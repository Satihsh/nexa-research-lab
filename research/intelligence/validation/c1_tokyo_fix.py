#!/usr/bin/env python3
"""C1 Tokyo-fix (gotobi) USDJPY flow strategy (PREREG_C1_TOKYO_FIX.md; inherits PREREG_OF_COMMON.md).

Usage: python c1_tokyo_fix.py --stage disc|val|full
Research only: reads local Pepperstone M1 + the frozen C1_JP_HOLIDAYS.json; writes results in this folder.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import date, timedelta

import numpy as np
import pandas as pd

import of_common as oc

sys.path.insert(0, '~/NEXA-Agent-Lab/filesnexa/NEXA/research')
from nexa_robust import deflated_sharpe   # noqa: E402  (read-only import)

SYM = 'USDJPY'
FIX_UTC_MIN = 55                  # 00:55 UTC = 09:55 JST
SPREAD_FLOOR = 0.002              # 0.2 pip in JPY price units (§4)
COMM_BP = 0.70                    # USD 7 per 100k USD notional per round trip
STRESS_BP = {'S0': 0.0, 'S1': 0.25, 'S2': 0.50}   # per side
STOP_K = 4.0
SIG_LOOKBACK = 60
COST_FLOOR_FRAC = 0.20
PLACEBO_OFFSETS = [k * 5 for k in range(-23, 26) if abs(k) > 2]   # 44 switch times 23:00-03:00 excl. 00:45-01:05
assert len(PLACEBO_OFFSETS) == 44
BLOCK = 20


# ----------------------------------------------------------------------------- calendar
def load_holidays(path: str = os.path.join(oc.HERE, 'C1_JP_HOLIDAYS.json')) -> set:
    with open(path) as f:
        return {date.fromisoformat(d) for d in json.load(f)['dates']}


def business_days(start: date, end: date, holidays: set) -> list:
    out, d = [], start
    while d <= end:
        if d.weekday() < 5 and d not in holidays:
            out.append(d)
        d += timedelta(days=1)
    return out


def gotobi_days(bdays: list, roll: bool = True) -> tuple[set, set]:
    """Returns (gotobi set, month-end set). Targets 5,10,15,20,25,30 (+ last business day of month).
    roll=True: a non-business target maps to the previous business day; roll=False: dropped."""
    bset = set(bdays)
    lo, hi = min(bdays), max(bdays)
    out, me = set(), set()
    y, m = lo.year, lo.month
    while (y, m) <= (hi.year, hi.month):
        for k in (5, 10, 15, 20, 25, 30):
            try:
                t = date(y, m, k)
            except ValueError:
                continue
            if t in bset:
                out.add(t)
            elif roll:
                p = t - timedelta(days=1)
                while p not in bset and p >= lo:
                    p -= timedelta(days=1)
                if p in bset:
                    out.add(p)
        mdays = [d for d in bdays if d.year == y and d.month == m]
        if mdays:
            out.add(mdays[-1]); me.add(mdays[-1])
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out, me


# ----------------------------------------------------------------------------- clock
def server_to_utc_min(day_str_per_bar: np.ndarray, smin: np.ndarray) -> np.ndarray:
    """UTC minutes since epoch: server = NY local + 7 h (COMMON §C3)."""
    srv = pd.to_datetime(day_str_per_bar) + pd.to_timedelta(smin, unit='m')
    ny = pd.DatetimeIndex(srv - pd.Timedelta(hours=7))
    utc = ny.tz_localize('America/New_York', ambiguous='NaT', nonexistent='NaT').tz_convert('UTC')
    return (utc.as_unit('ns').asi8 // 60_000_000_000).astype(np.int64)


def utc_min_of(d: date, offset_min_from_0055: int) -> int:
    base = int(pd.Timestamp(d).value // 60_000_000_000)      # 00:00 UTC of D
    return base + FIX_UTC_MIN + offset_min_from_0055


# ----------------------------------------------------------------------------- legs
def leg(direction: int, o, h, l, c, i0: int, i1: int, spread: float, sig: float, stress_bp: float,
        stop_k: float = STOP_K) -> dict | None:
    """Trade from the open of bar i0 to the close of bar i1 (inclusive), bid data.
    Long: buy at ask (bid+spread), sell at bid; short: sell at bid, buy at ask. Catastrophe stop at stop_k*sig."""
    if direction == 1:
        entry_px = o[i0] + spread
        ref = o[i0]
    else:
        entry_px = o[i0]
        ref = o[i0]
    stop_dist = stop_k * sig * ref
    if not stop_dist > 0:
        return None
    comm_px = 0.00007 * ref
    if comm_px + spread > COST_FLOOR_FRAC * stop_dist:
        return {'skip': 'cost_floor'}
    stop = entry_px - stop_dist if direction == 1 else entry_px + stop_dist
    exit_px, how = None, 'time'
    for k in range(i0, i1 + 1):
        if direction == 1 and l[k] <= stop:
            exit_px = o[k] if (k > i0 and o[k] <= stop) else stop
            how = 'stop'; break
        if direction == -1 and h[k] + spread >= stop:
            exit_px = (o[k] + spread) if (k > i0 and o[k] + spread >= stop) else stop
            how = 'stop'; break
    if exit_px is None:
        exit_px = c[i1] if direction == 1 else c[i1] + spread
    pnl_px = (exit_px - entry_px) if direction == 1 else (entry_px - exit_px)
    gross_bp = (pnl_px + spread) / ref * 1e4          # before spread/commission/stress (mid-ish move)
    net_px = pnl_px - comm_px - 2 * stress_bp * 1e-4 * ref
    return {'net_bp': net_px / ref * 1e4, 'gross_bp': gross_bp, 'R': net_px / stop_dist, 'exit': how,
            'stop_over_cost': stop_dist / (comm_px + spread)}


# ----------------------------------------------------------------------------- data
class Bars:
    def __init__(self, S: oc.Sym):
        day_per_bar = np.empty(len(S.smin), dtype=object)
        sday_idx = np.empty(len(S.smin), dtype=np.int64)
        for i, (s, e) in enumerate(zip(S.start, S.end)):
            day_per_bar[s:e] = S.days[i]; sday_idx[s:e] = i
        self.utc = server_to_utc_min(day_per_bar, S.smin)
        self.o, self.h, self.l, self.c = S.o, S.h, S.l, S.c
        self.sday = sday_idx
        self.S = S

    def at(self, utc_minute: int) -> int:
        k = int(np.searchsorted(self.utc, utc_minute))
        return k if k < len(self.utc) and self.utc[k] == utc_minute else -1

    def spread(self, bar: int, floor: float = SPREAD_FLOOR) -> float:
        s = self.S.sprd[self.sday[bar]]
        return max(floor, float(s)) if np.isfinite(s) else np.nan


def window_returns(B: Bars, days: list, off: int, pre: int = 5, post: int = 5) -> pd.Series:
    vals = {}
    for d in days:
        T = utc_min_of(d, off)
        a, b = B.at(T - pre), B.at(T + post - 1)
        if a >= 0 and b >= 0:
            vals[d] = math.log(B.c[b] / B.o[a])
    return pd.Series(vals)


def sigma_series(rets: pd.Series) -> pd.Series:
    return rets.rolling(SIG_LOOKBACK, min_periods=SIG_LOOKBACK).std(ddof=1).shift(1)


def event(B: Bars, d: date, off: int, sig: float, stress_bp: float, legs: str, pre: int = 5, post: int = 5,
          spread_floor: float = None, stop_k: float = STOP_K) -> dict | None:
    T = utc_min_of(d, off)
    e0, sw, ex = B.at(T - pre), B.at(T - 1), B.at(T + post - 1)
    if e0 < 0 or sw < 0 or (legs != 'long' and ex < 0):
        return {'missing': True}
    s = B.spread(sw, SPREAD_FLOOR if spread_floor is None else spread_floor)
    if not (np.isfinite(sig) and sig > 0 and np.isfinite(s)):
        return {'missing': True}
    out = {'net_bp': 0.0, 'gross_bp': 0.0, 'R': 0.0, 'legs': 0, 'stops': 0, 'skips': 0, 'soc': []}
    todo = [(1, e0, sw)] + ([(-1, sw + 1, ex)] if legs == 'both' else [])
    for direction, i0, i1 in todo:
        if direction == -1 and B.utc[i0] != T:          # short leg must start at the 00:55 bar
            i0b = B.at(T)
            if i0b < 0:
                continue
            i0 = i0b
        r = leg(direction, B.o, B.h, B.l, B.c, i0, i1, s, sig, stress_bp, stop_k)
        if r is None:
            continue
        if 'skip' in r:
            out['skips'] += 1; continue
        out['net_bp'] += r['net_bp']; out['gross_bp'] += r['gross_bp']; out['R'] += r['R']
        out['legs'] += 1; out['stops'] += r['exit'] == 'stop'; out['soc'].append(r['stop_over_cost'])
    return out if out['legs'] > 0 else {'skipped_all': True, 'skips': out['skips']}


# ----------------------------------------------------------------------------- statistics
def summary(x: np.ndarray) -> dict:
    x = np.asarray(x, float)
    if len(x) < 5:
        return {'n': int(len(x)), 'mean': oc._f(x.mean()) if len(x) else None}
    reps = oc.bootstrap(lambda ix: x[ix].mean(), len(x))
    return {'n': int(len(x))} | oc.boot_summary(float(x.mean()), reps)


def run_claim(B, days, sig_by_off, off, legs, stress, pre=5, post=5, spread_floor=None, stop_k=STOP_K, sig_off=None):
    rows = []
    miss = skip = 0
    sig_s = sig_by_off[off if sig_off is None else sig_off]
    for d in days:
        sg = sig_s.get(d, np.nan)
        ev = event(B, d, off, sg, STRESS_BP[stress], legs, pre, post, spread_floor, stop_k)
        if ev is None or ev.get('missing'):
            miss += 1; continue
        if ev.get('skipped_all'):
            skip += 1; continue
        rows.append({'d': d, 'split': oc.split_of(d.isoformat()), 'net': ev['net_bp'], 'gross': ev['gross_bp'],
                     'R': ev['R'], 'legs': ev['legs'], 'stops': ev['stops'], 'soc': float(np.median(ev['soc']))})
    df = pd.DataFrame(rows)
    df.attrs.update({'missing': miss, 'skipped_cost_floor': skip})
    return df


def claim_report(df: pd.DataFrame, max_split: int) -> dict:
    rep = {'missing_events': df.attrs.get('missing'), 'skipped_cost_floor': df.attrs.get('skipped_cost_floor')}
    if df.empty:
        return rep | {'n': 0}
    for s in range(max_split + 1):
        x = df[df.split == s]
        rep[oc.SPLIT_NAMES[s]] = summary(x.net.to_numpy()) | {'gross_mean_bp': oc._f(x.gross.mean()),
                                                              'mean_R': oc._f(x.R.mean()),
                                                              'stop_rate_per_leg': oc._f(x.stops.sum() / max(1, x.legs.sum()))}
    rep['pooled'] = summary(df.net.to_numpy()) | {'gross_mean_bp': oc._f(df.gross.mean()), 'mean_R': oc._f(df.R.mean()),
                                                  'median_stop_over_cost': oc._f(df.soc.median())}
    return rep


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', choices=['disc', 'val', 'full'], required=True)
    args = ap.parse_args()
    ms = oc.stage_max_split(args.stage)
    full = args.stage == 'full'
    S = oc.load(SYM)
    B = Bars(S)
    hol = load_holidays()
    first = date.fromisoformat(oc.FIRST_DAY[SYM]) - timedelta(days=120)       # warm-up for sigma (not evaluated)
    last = date.fromisoformat(oc.LAST_DAY)
    bd_all = business_days(first, last, hol)
    got, me = gotobi_days(bd_all, roll=True)
    got_nr, _ = gotobi_days(bd_all, roll=False)
    eval_from = date.fromisoformat(oc.FIRST_DAY[SYM])
    cutoff = {0: date(2022, 12, 31), 1: date(2024, 12, 31), 2: last}[ms]
    in_scope = lambda d: eval_from <= d <= cutoff
    days_all = [d for d in bd_all if in_scope(d)]
    days_g = [d for d in days_all if d in got]
    days_g_nr = [d for d in days_all if d in got_nr]
    days_o = [d for d in days_all if d not in got]
    # sigma per switch offset (causal; uses all business days incl. warm-up)
    bd_hist = [d for d in bd_all if d <= cutoff]
    offs = sorted(set(PLACEBO_OFFSETS + [0, 1]))
    sig_by_off = {o: sigma_series(window_returns(B, bd_hist, o)) for o in offs}
    out = {'hypothesis': 'C1 Tokyo fix', 'prereg': ['PREREG_OF_COMMON.md', 'PREREG_C1_TOKYO_FIX.md', 'C1_JP_HOLIDAYS.json'],
           'stage': args.stage, 'splits_opened': oc.SPLIT_NAMES[:ms + 1],
           'counts': {'business_days': len(days_all), 'gotobi_roll': len(days_g), 'gotobi_noroll': len(days_g_nr),
                      'other': len(days_o), 'month_end': len([d for d in days_all if d in me])}}
    claims = {}
    for st in ('S0', 'S1', 'S2'):
        claims[f'A_{st}'] = run_claim(B, days_g, sig_by_off, 0, 'both', st)
    claims['B_S1'] = run_claim(B, days_g, sig_by_off, 0, 'long', 'S1')
    claims['C_S1'] = run_claim(B, days_all, sig_by_off, 0, 'both', 'S1')
    claims['D_S1'] = run_claim(B, days_g, sig_by_off, 0, 'long', 'S1', pre=30, sig_off=0)
    claims['AnoRoll_S1'] = run_claim(B, days_g_nr, sig_by_off, 0, 'both', 'S1')
    out['claims'] = {k: claim_report(v, ms) for k, v in claims.items()}
    A = claims['A_S1']
    # power (discovery sigma)
    sd = A[A.split == 0].net.std(ddof=1)
    out['power'] = {'disc_sd_bp': oc._f(sd), 'MDE80_bp': {oc.SPLIT_NAMES[s]: oc._f(2.486 * sd / math.sqrt(max(1, (A.split == s).sum())))
                                                         for s in range(ms + 1)}}
    # placebo (time of day), A rule, GOTOBI, S1
    plc = {}
    for off in PLACEBO_OFFSETS:
        dfp = run_claim(B, days_g, sig_by_off, off, 'both', 'S1')
        plc[off] = dfp
    obs_pool = A.net.mean()
    pmeans = np.array([plc[o].net.mean() for o in PLACEBO_OFFSETS])
    out['placebo'] = {'observed_pooled_S1': oc._f(obs_pool), 'placebo_means': {str(o): oc._f(m) for o, m in zip(PLACEBO_OFFSETS, pmeans)},
                      'p_tod_pooled': oc._f((1 + np.sum(pmeans >= obs_pool)) / 45)}
    for s in range(ms + 1):
        obs_s = A[A.split == s].net.mean()
        pm_s = np.array([plc[o][plc[o].split == s].net.mean() for o in PLACEBO_OFFSETS])
        out['placebo'][f'n_placebos_ge_obs_{oc.SPLIT_NAMES[s]}'] = int(np.sum(pm_s >= obs_s))
    # delta GOTOBI - OTHER (gross, A rule) over all business days in date order
    Call = run_claim(B, days_all, sig_by_off, 0, 'both', 'S1').sort_values('d').reset_index(drop=True)
    isg = Call.d.isin(got).to_numpy(); gr = Call.gross.to_numpy()
    def dlt(ix=None):
        g, x = (isg, gr) if ix is None else (isg[ix], gr[ix])
        return x[g].mean() - x[~g].mean() if g.any() and (~g).any() else np.nan
    out['delta_gotobi_minus_other_gross'] = oc.boot_summary(dlt(), oc.bootstrap(lambda ix: dlt(ix), len(Call)))
    out['delta_gotobi_minus_other_gross'] |= {'mean_gotobi': oc._f(gr[isg].mean()), 'mean_other': oc._f(gr[~isg].mean())}
    # years
    A2 = A.assign(year=[d.year for d in A.d])
    ys = sorted(A2.year.unique())
    out['years'] = {'net_S1_mean_by_year': {str(y): oc._f(A2[A2.year == y].net.mean()) for y in ys},
                    'n_by_year': {str(y): int((A2.year == y).sum()) for y in ys},
                    'positive_years': int(sum(A2[A2.year == y].net.mean() > 0 for y in ys)), 'years': len(ys)}
    out['years'] |= oc.year_shares(A2.year.to_numpy(), A2.net.to_numpy())
    # DSR over 49 trials (5 claims + 44 placebos), S1
    srs = [claims[k].net.mean() / claims[k].net.std(ddof=1) for k in ('A_S1', 'B_S1', 'C_S1', 'D_S1', 'AnoRoll_S1')]
    srs += [plc[o].net.mean() / plc[o].net.std(ddof=1) for o in PLACEBO_OFFSETS]
    var_sr = float(np.var(srs, ddof=1))
    out['DSR'] = {'A_S1': oc._f(deflated_sharpe(A.net.to_numpy(), 49, var_sr)), 'var_sr_trials': var_sr,
                  'sr_A_per_event': oc._f(srs[0])}
    # BH secondaries (discovery p)
    sec = ['B_S1', 'C_S1', 'D_S1', 'AnoRoll_S1']
    ps = [out['claims'][k].get('discovery', {}).get('p_one_sided') for k in sec]
    for k, a in zip(sec, oc.bh(ps)):
        out['claims'][k]['disc_p_BH_secondary'] = a
    # robustness (reported only)
    rob = {}
    me_mask = A.d.isin(me)
    rob['gotobi_5_10_only'] = summary(A[~me_mask].net.to_numpy())
    rob['month_end_only'] = summary(A[me_mask].net.to_numpy())
    rob['fridays'] = summary(A[[d.weekday() == 4 for d in A.d]].net.to_numpy())
    for fl in (0.001, 0.003):
        rob[f'spread_floor_{fl}'] = summary(run_claim(B, days_g, sig_by_off, 0, 'both', 'S1', spread_floor=fl).net.to_numpy())
    for k in (3.0, 6.0):
        rob[f'stop_k_{k}'] = summary(run_claim(B, days_g, sig_by_off, 0, 'both', 'S1', stop_k=k).net.to_numpy())
    rob['switch_at_0056'] = summary(run_claim(B, days_g, sig_by_off, 1, 'both', 'S1', sig_off=1).net.to_numpy())
    out['robustness'] = rob
    if full:
        r = out['claims']['A_S1']; r0 = out['claims']['A_S0']
        nh = r.get('holdout', {}).get('n', 0); npool = r['pooled']['n']
        crit = {
            '1_disc_p_lt_0.05_and_pos': bool((r['discovery'].get('theta') or -1) > 0 and (r['discovery'].get('p_one_sided') or 1) < 0.05),
            '2_val_hold_pos': bool((r['validation'].get('theta') or -1) > 0 and (r['holdout'].get('theta') or -1) > 0),
            '3_pooled_ci_lo_gt_0': bool((r['pooled']['ci95'][0] or -1) > 0),
            '4_placebo': bool(out['placebo']['p_tod_pooled'] <= 0.05 and out['placebo']['n_placebos_ge_obs_holdout'] <= 8),
            '5_delta_ci_lo_gt_0': bool((out['delta_gotobi_minus_other_gross']['ci95'][0] or -1) > 0),
            '6_stability': bool(not out['years']['flag_year_gt_50pct'] and out['years']['positive_years'] >= 6),
            '7_dsr_ge_0.95': bool((out['DSR']['A_S1'] or 0) >= 0.95),
            '8_stop_ge_5x_cost': bool((r['pooled'].get('median_stop_over_cost') or 0) >= 5)}
        out['acceptance'] = crit
        if nh < 100 or npool < 500:
            v = 'INSUFFICIENT-N'
        elif (r0['pooled'].get('theta') or 0) <= 0 or np.sign(r['discovery'].get('theta') or 0) * np.sign(r['holdout'].get('theta') or 0) < 0:
            v = 'REJECTED'
        elif all(crit.values()):
            v = 'SUPPORTED (research candidate, G4)'
        else:
            v = 'INCONCLUSIVE'
        out['verdict'] = v
    fn = os.path.join(oc.HERE, 'c1_results.json' if full else f'c1_results_{args.stage}.json')
    with open(fn, 'w') as f:
        json.dump(out, f, indent=1, default=lambda x: oc._f(x) if isinstance(x, (np.floating, float)) else int(x) if isinstance(x, np.integer) else str(x))
    print('wrote', fn)
    return 0


if __name__ == '__main__':
    sys.exit(main())
