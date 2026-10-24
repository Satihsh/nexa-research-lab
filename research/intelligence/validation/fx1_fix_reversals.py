#!/usr/bin/env python3
"""FX1 daily FX fix reversals (PREREG_FX1_FIX_REVERSALS.md, sha 18207319...; inherits PREREG_OF_COMMON.md and the
IM1 cost / stop / placebo conventions). Source: Krohn, Mueller & Whelan (2024 JF), Table I signs.

Windows (each fix by its own local clock, DST-aware), traded in the paper's per-currency direction:
  W1 post-Tokyo  09:55 Asia/Tokyo  -> 08:00 Europe/Berlin
  W2 pre-ECB     08:00 Europe/Berlin -> 14:15 Europe/Berlin
  W3 post-London 16:00 Europe/London -> 16:55 America/New_York
Deviations / implementation notes: DEVIATIONS_FX1.md.

Usage:
  python3 fx1_fix_reversals.py build-calendars        # writes FX1_CALENDARS.json (frozen before discovery)
  python3 fx1_fix_reversals.py smoke                  # counts only (no P&L), D10
  python3 fx1_fix_reversals.py --stage disc|val|full
Research only: reads local Pepperstone M1 and frozen calendars; writes results in this folder.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import of_common as oc  # noqa: E402
import im1_intraday_momentum as im  # noqa: E402  (read-only reuse: Bars, easter, pooled_stat, year_check)

PREREG_SHA = '182073199c56a09f5ffaadaf5c07b33140ca3e4fbec3d735863f6ea038769928'
SYMS = ['EURUSD', 'GBPUSD', 'USDJPY']
WINS = ['W1', 'W2', 'W3']
TOKYO, BERLIN, LONDON, NY = (ZoneInfo('Asia/Tokyo'), ZoneInfo('Europe/Berlin'), ZoneInfo('Europe/London'),
                             ZoneInfo('America/New_York'))
UTC = ZoneInfo('UTC')
# §2: direction of the PAIR trade (+1 long pair, -1 short pair) from the paper's Table I sign
DIRECTION = {('W1', 'EURUSD'): +1, ('W1', 'GBPUSD'): +1, ('W1', 'USDJPY'): -1,
             ('W2', 'EURUSD'): -1, ('W2', 'GBPUSD'): -1, ('W2', 'USDJPY'): +1,
             ('W3', 'EURUSD'): +1, ('W3', 'GBPUSD'): +1, ('W3', 'USDJPY'): +1}
# paper Table I (bp/day, + = foreign currency up vs USD), for N2
PAPER = {('W1', 'EURUSD'): 2.34, ('W1', 'GBPUSD'): 1.27, ('W1', 'USDJPY'): 3.15,
         ('W2', 'EURUSD'): -3.52, ('W2', 'GBPUSD'): -2.29, ('W2', 'USDJPY'): -1.03,
         ('W3', 'EURUSD'): 2.73, ('W3', 'GBPUSD'): 2.65, ('W3', 'USDJPY'): -1.16}
FIX_OF = {'W1': 'tokyo', 'W2': 'ecb', 'W3': 'wmr'}
SPREAD_FLOOR = {'EURUSD': 0.00002, 'GBPUSD': 0.00002, 'USDJPY': 0.002}      # 0.2 pip (§4)
STRESS_BP = {'S0': 0.0, 'S1': 0.25, 'S2': 0.50}                               # per side
STOP_K = 4.0
SIG_LOOKBACK = 60
COST_FLOOR_FRAC = 0.20
POST_PAPER = '2020-01-01'
CAL_PATH = os.path.join(HERE, 'FX1_CALENDARS.json')
JP_PATH = os.path.join(HERE, 'C1_JP_HOLIDAYS.json')


# ----------------------------------------------------------------------------- clock
def utc_minute(d: date, hh: int, mm: int, tz: ZoneInfo) -> int:
    """UTC epoch minute of local wall time hh:mm on date d in tz (DST-aware)."""
    t = datetime(d.year, d.month, d.day, hh, mm, tzinfo=tz).astimezone(UTC)
    return int(t.timestamp() // 60)


def window(w: str, d: date, mode: str = 'fix', w3_end_ny: tuple = (16, 55)) -> tuple:
    """(start, end) UTC minutes of window w on day d. Exit bar is the one starting at end - 1 (§3).
    mode 'fix': local fix clocks (primary); 'paper_et': the paper's fixed ET boundaries (§8 robustness)."""
    if mode == 'fix':
        if w == 'W1':
            return utc_minute(d, 9, 55, TOKYO), utc_minute(d, 8, 0, BERLIN)
        if w == 'W2':
            return utc_minute(d, 8, 0, BERLIN), utc_minute(d, 14, 15, BERLIN)
        return utc_minute(d, 16, 0, LONDON), utc_minute(d, *w3_end_ny, NY)
    if w == 'W1':                                    # 20:55 ET on the previous NY calendar date (D13)
        return utc_minute(d - timedelta(days=1), 20, 55, NY), utc_minute(d, 2, 0, NY)
    if w == 'W2':
        return utc_minute(d, 2, 0, NY), utc_minute(d, 8, 15, NY)
    return utc_minute(d, 11, 0, NY), utc_minute(d, *w3_end_ny, NY)


def server_day_of_utc(u: int) -> date:
    """Server day (NY + 7 h) containing UTC minute u."""
    t = datetime.fromtimestamp(u * 60, UTC).astimezone(NY) + timedelta(hours=7)
    return t.date()


def touches_rollover(u0: int, u1: int) -> bool:
    """True if [u0, u1] (closed) intersects 16:55-17:05 NY of any date (§5 placebo exclusion)."""
    d0 = datetime.fromtimestamp(u0 * 60, UTC).astimezone(NY).date()
    for k in range(-1, 3):
        dd = d0 + timedelta(days=k)
        a, b = utc_minute(dd, 16, 55, NY), utc_minute(dd, 17, 5, NY)
        if u0 <= b and u1 >= a:
            return True
    return False


def placebo_offsets() -> list:
    """delta every 30 min from -12 h to +11.5 h, excluding |delta| <= 90 min (§5; 41 offsets)."""
    return [m for m in range(-720, 691, 30) if abs(m) > 90]


# ----------------------------------------------------------------------------- calendars (§2, D3)
def target_closed(y: int) -> list:
    e = im.easter(y)
    return [date(y, 1, 1), e - timedelta(days=2), e + timedelta(days=1), date(y, 5, 1), date(y, 12, 25), date(y, 12, 26)]


def build_calendars() -> dict:
    with open(JP_PATH) as f:
        jp = sorted(json.load(f)['dates'].keys())
    years = range(2017, 2027)
    tgt = sorted({x.isoformat() for y in years for x in target_closed(y)})
    wmr = sorted({x.isoformat() for y in years for x in (date(y, 1, 1), date(y, 12, 25))})
    return {'source': {'tokyo': 'C1_JP_HOLIDAYS.json dates (MT5 JP type-2 + Dec 31-Jan 3 + NEXA public-record additions)',
                       'ecb': 'TARGET closing days: Jan 1, Good Friday, Easter Monday, May 1, Dec 25, Dec 26',
                       'wmr': 'WMR London: weekdays except Dec 25 and Jan 1'},
            'tokyo_closed': jp, 'ecb_closed': tgt, 'wmr_closed': wmr}


def load_calendars() -> dict:
    with open(CAL_PATH) as f:
        c = json.load(f)
    return {'tokyo': {date.fromisoformat(x) for x in c['tokyo_closed']},
            'ecb': {date.fromisoformat(x) for x in c['ecb_closed']},
            'wmr': {date.fromisoformat(x) for x in c['wmr_closed']}}


def eligible_days(S: oc.Sym, max_day: str) -> list:
    """Server day d: weekday, >= FIRST_DAY, <= max_day, COMMON §C4 valid (fix calendars applied per window)."""
    return [date.fromisoformat(ds) for i, ds in enumerate(S.days)
            if oc.FIRST_DAY[S.sym] <= ds <= max_day and date.fromisoformat(ds).weekday() < 5 and bool(S.valid[i])]


# ----------------------------------------------------------------------------- one trade (IM1 mechanics, generic window)
def trade(sym: str, B, i0: int, i1: int, direction: int, spread: float, sig: float, stop_k: float = STOP_K) -> dict:
    """Entry at open of bar i0, exit at close of bar i1 (bid; longs pay the spread at entry, shorts at exit).
    Returns path-dependent pieces; net for a stress level = pnl - comm - 2 * stress * 1e-4 * ref."""
    ref = float(B.o[i0])
    entry_px = ref + spread if direction == 1 else ref
    stop_dist = stop_k * sig * ref
    comm = oc.commission(sym, ref)
    if not (stop_dist > 0):
        return {'missing': True}
    if comm + spread > COST_FLOOR_FRAC * stop_dist:
        return {'skip': True}
    stop = entry_px - stop_dist if direction == 1 else entry_px + stop_dist
    if direction == 1:
        hit = np.flatnonzero(B.l[i0:i1 + 1] <= stop)
    else:
        hit = np.flatnonzero(B.h[i0:i1 + 1] + spread >= stop)
    if hit.size:
        k = i0 + int(hit[0])
        if direction == 1:
            exit_px = B.o[k] if (k > i0 and B.o[k] <= stop) else stop
        else:
            exit_px = (B.o[k] + spread) if (k > i0 and B.o[k] + spread >= stop) else stop
        how = 'stop'
    else:
        exit_px = B.c[i1] if direction == 1 else B.c[i1] + spread
        how = 'time'
    pnl = float((exit_px - entry_px) if direction == 1 else (entry_px - exit_px))
    return {'pnl': pnl, 'comm': comm, 'ref': ref, 'spread': spread, 'stop_dist': stop_dist, 'exit': how,
            'gross_bp': (pnl + spread) / ref * 1e4, 'soc': stop_dist / (comm + spread)}


def net_bp(t: dict, stress: str) -> float:
    return (t['pnl'] - t['comm'] - 2 * STRESS_BP[stress] * 1e-4 * t['ref']) / t['ref'] * 1e4


# ----------------------------------------------------------------------------- per-cell event table
def run_cell(sym: str, B, days: list, w: str, cal: dict, *, delta: int = 0, mode: str = 'fix',
             w3_end_ny=(16, 55), stop_k: float = STOP_K, spread_floor=None, placebo: bool = False) -> pd.DataFrame:
    """One row per eligible day for (window w, pair sym), optionally shifted by delta minutes (placebo)."""
    S = B.S
    closed = cal[FIX_OF[w]]
    floor = SPREAD_FLOOR[sym] if spread_floor is None else spread_floor
    direction = DIRECTION[(w, sym)]
    cand, miss_cal, miss_roll = [], 0, 0
    for d in days:
        if d in closed:
            miss_cal += 1
            continue
        u0, u1 = window(w, d, mode, w3_end_ny)
        u0, u1 = u0 + delta, u1 + delta
        if placebo and touches_rollover(u0, u1):
            miss_roll += 1
            continue
        cand.append((d, u0, u1))
    if not cand:
        df = pd.DataFrame()
        df.attrs.update({'missing': 0, 'skipped_cost_floor': 0, 'closed_fix': miss_cal, 'rollover_excluded': miss_roll})
        return df
    U0 = np.array([c[1] for c in cand], np.int64)
    U1 = np.array([c[2] for c in cand], np.int64) - 1
    k0 = np.searchsorted(B.utc, U0)
    k1 = np.searchsorted(B.utc, U1)
    n = len(B.utc)
    ok0 = (k0 < n) & (B.utc[np.minimum(k0, n - 1)] == U0)
    ok1 = (k1 < n) & (B.utc[np.minimum(k1, n - 1)] == U1)
    have = ok0 & ok1 & (k1 >= k0)
    # sigma of the window log return over the previous 60 eligible days with bars (causal, §3)
    lr = np.full(len(cand), np.nan)
    hv = np.flatnonzero(have)
    lr[hv] = np.log(B.c[k1[hv]] / B.o[k0[hv]])
    sig = pd.Series(lr[hv]).rolling(SIG_LOOKBACK, min_periods=SIG_LOOKBACK).std(ddof=1).shift(1).to_numpy()
    sig_all = np.full(len(cand), np.nan)
    sig_all[hv] = sig
    rows, miss, skip = [], 0, 0
    for j, (d, u0, u1) in enumerate(cand):
        if not have[j] or not np.isfinite(sig_all[j]):
            miss += 1
            continue
        i0, i1 = int(k0[j]), int(k1[j])
        sp = S.sprd[B.sday[i0]]
        if not np.isfinite(sp):
            miss += 1
            continue
        t = trade(sym, B, i0, i1, direction, max(floor, float(sp)), float(sig_all[j]), stop_k)
        if t.get('missing'):
            miss += 1
            continue
        if t.get('skip'):
            skip += 1
            continue
        rows.append({'d': d, 'sym': sym, 'win': w, 'split': oc.split_of(d.isoformat()), 'year': d.year,
                     'dir': direction, 'net': net_bp(t, 'S1'), 'net_S0': net_bp(t, 'S0'), 'net_S2': net_bp(t, 'S2'),
                     'gross': t['gross_bp'], 'stop': t['exit'] == 'stop', 'soc': t['soc']})
    df = pd.DataFrame(rows)
    df.attrs.update({'missing': miss, 'skipped_cost_floor': skip, 'closed_fix': miss_cal, 'rollover_excluded': miss_roll})
    return df


def raw_window_returns(sym: str, B, days: list, w: str, cal: dict) -> pd.DataFrame:
    """N2: unconditional window return in foreign-currency terms (bp, + = foreign up vs USD), no stop, no costs."""
    rows = []
    for d in days:
        if d in cal[FIX_OF[w]]:
            continue
        u0, u1 = window(w, d)
        i0, i1 = B.at(u0), B.at(u1 - 1)
        if i0 < 0 or i1 < 0:
            continue
        r = (B.c[i1] / B.o[i0] - 1.0) * 1e4
        rows.append({'d': d, 'r': -r if sym == 'USDJPY' else r})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- statistics
def stat(df: pd.DataFrame, col: str = 'net') -> dict:
    return im.pooled_stat(df, col) if len(df) else {'n': 0, 'theta': None}


def day_weight_stat(df: pd.DataFrame) -> dict:
    """Equal weight per day (§8): mean of day means, day-block bootstrap."""
    g = df.groupby('d').net.mean().sort_index().to_numpy()
    reps = oc.bootstrap(lambda ix: g[ix].mean(), len(g))
    return {'days': int(len(g))} | oc.boot_summary(float(g.mean()), reps)


def years(df: pd.DataFrame) -> dict:
    tot = float(df.net.sum())
    ys = sorted(int(y) for y in df.year.unique())
    share = {y: (float(df[df.year == y].net.sum()) / tot if tot else None) for y in ys}
    pos = {y: bool(df[df.year == y].net.mean() > 0) for y in ys}
    return {'total_net_bp': tot, 'share': share, 'positive': pos, 'n_positive': int(sum(pos.values())),
            'n_years': len(ys), 'max_share': max((v for v in share.values() if v is not None), default=None)}


# ----------------------------------------------------------------------------- main
def run_stage(stage: str) -> dict:
    ms = oc.stage_max_split(stage)
    max_day = {0: '2022-12-31', 1: '2024-12-31', 2: oc.LAST_DAY}[ms]
    cal = load_calendars()
    offs = placebo_offsets()
    out = {'prereg_sha256': PREREG_SHA, 'stage': stage, 'max_day': max_day,
           'splits_opened': oc.SPLIT_NAMES[:ms + 1], 'cells': {}, 'n_placebo_offsets': len(offs)}
    frames, plac, rob, n2 = [], {o: [] for o in offs}, {}, {}
    for sym in SYMS:
        S = oc.load(sym)
        B = im.Bars(S)
        days = eligible_days(S, max_day)
        for w in WINS:
            df = run_cell(sym, B, days, w, cal)
            frames.append(df)
            out['cells'][f'{w}_{sym}'] = {'eligible_server_days': len(days), 'trades': int(len(df)), **df.attrs,
                                          'stop_rate': float(df.stop.mean()) if len(df) else None,
                                          'median_stop_over_cost': float(df.soc.median()) if len(df) else None}
            raw = raw_window_returns(sym, B, days, w, cal)
            n2[f'{w}_{sym}'] = {'paper_bp': PAPER[(w, sym)], 'n': int(len(raw))} | stat(raw, 'r')
            for o in offs:
                plac[o].append(run_cell(sym, B, days, w, cal, delta=o, placebo=True))
            if stage == 'full':
                v = {'W3_to_1700': run_cell(sym, B, days, w, cal, w3_end_ny=(17, 0)) if w == 'W3' else df,
                     'paper_fixed_ET': run_cell(sym, B, days, w, cal, mode='paper_et'),
                     'spread_floor_0.1pip': run_cell(sym, B, days, w, cal, spread_floor=SPREAD_FLOOR[sym] / 2),
                     'spread_floor_0.3pip': run_cell(sym, B, days, w, cal, spread_floor=SPREAD_FLOOR[sym] * 1.5),
                     'stop_3sigma': run_cell(sym, B, days, w, cal, stop_k=3.0),
                     'stop_6sigma': run_cell(sym, B, days, w, cal, stop_k=6.0)}
                for k, x in v.items():
                    rob.setdefault(k, []).append(x)
            print(stage, w, sym, out['cells'][f'{w}_{sym}'], flush=True)
        del B, S
    P = pd.concat(frames, ignore_index=True)
    res = {}
    for st, col in (('S0', 'net_S0'), ('S1', 'net'), ('S2', 'net_S2')):
        res[st] = {'pooled': stat(P, col), 'by_split': {oc.SPLIT_NAMES[s]: stat(P[P.split == s], col) for s in range(ms + 1)}}
    out['primary_P'] = res
    out['gross_pooled'] = stat(P, 'gross')
    out['post_paper_2020+'] = stat(P[P.d >= date.fromisoformat(POST_PAPER)])
    sec = {}
    for w in WINS:
        x = P[P.win == w]
        sec[w] = {'pooled': stat(x), 'gross_mean_bp': float(x.gross.mean()),
                  'by_split': {oc.SPLIT_NAMES[s]: stat(x[x.split == s]) for s in range(ms + 1)}}
    for s in SYMS:
        x = P[P.sym == s]
        sec[s] = {'pooled': stat(x), 'gross_mean_bp': float(x.gross.mean()),
                  'by_split': {oc.SPLIT_NAMES[k]: stat(x[x.split == k]) for k in range(ms + 1)}}
    out['secondary'] = sec
    keys = WINS + SYMS
    out['BH_secondaries'] = dict(zip(keys, oc.bh([sec[k]['pooled'].get('p_one_sided') for k in keys])))
    out['cell_stats'] = {f'{w}_{s}': {'net_S1': stat(P[(P.win == w) & (P.sym == s)]),
                                      'gross_mean_bp': float(P[(P.win == w) & (P.sym == s)].gross.mean())}
                         for w in WINS for s in SYMS}
    out['N2_gross_replication'] = n2
    # N1 placebo (S1 net), pooled over all cells per offset
    obs = float(P.net.mean())
    pm, pn = {}, {}
    for o in offs:
        x = pd.concat([f for f in plac[o] if len(f)], ignore_index=True)
        pm[o], pn[o] = float(x.net.mean()), int(len(x))
    means = np.array([pm[o] for o in offs])
    out['N1_placebo'] = {'observed': obs, 'p_tod': float((1 + np.sum(means >= obs)) / (len(offs) + 1)),
                         'n_offsets': len(offs), 'by_offset_min': {int(o): {'mean': pm[o], 'n': pn[o]} for o in offs},
                         'rollover_excluded': {int(o): int(sum(f.attrs.get('rollover_excluded', 0) for f in plac[o]))
                                               for o in offs}}
    # DSR (n_trials = 1 + 6 + 41 = 48)
    try:
        sys.path.insert(0, '~/NEXA-Agent-Lab/filesnexa/NEXA/research')
        from nexa_robust import deflated_sharpe
        series = [P.net] + [P[P.win == w].net for w in WINS] + [P[P.sym == s].net for s in SYMS] + \
                 [pd.concat([f for f in plac[o] if len(f)], ignore_index=True).net for o in offs]
        srs = [float(np.mean(x) / np.std(x, ddof=1)) for x in map(lambda z: np.asarray(z, float), series)
               if len(x) > 2 and np.std(x, ddof=1) > 0]
        var_sr = float(np.var(srs, ddof=1))
        out['DSR'] = {'P_S1': float(deflated_sharpe(P.net.to_numpy(), len(series), var_sr)),
                      'n_trials': len(series), 'var_sr_trials': var_sr}
    except Exception as e:  # noqa: BLE001
        out['DSR'] = {'error': repr(e)}
    out['years'] = years(P)
    if stage == 'full':
        R = {k: stat(pd.concat(v, ignore_index=True)) for k, v in rob.items()}
        R['W2_W3_only'] = stat(P[P.win != 'W1'])
        R['equal_weight_per_day'] = day_weight_stat(P)
        R['per_year'] = {int(y): stat(P[P.year == y]) for y in sorted(P.year.unique())}
        out['robustness'] = R
        out['acceptance'] = acceptance(out)
    return out


def acceptance(out: dict) -> dict:
    R = out['primary_P']
    d, v, h = (R['S1']['by_split'].get(s, {}) for s in ('discovery', 'validation', 'holdout'))
    pooled, pp, sec, yrs = R['S1']['pooled'], out['post_paper_2020+'], out['secondary'], out['years']

    def lo(x):
        c = (x.get('ci95') or [None])[0]
        return c is not None and c > 0
    crit = {
        '1_discovery_p<0.05': bool((d.get('theta') or -1) > 0 and (d.get('p_one_sided') or 1) < 0.05),
        '2_val_holdout_>0': bool((v.get('theta') or -1) > 0 and (h.get('theta') or -1) > 0),
        '3_pooled_ci_lo>0': lo(pooled),
        '4_placebo_p<=0.05': bool(out['N1_placebo']['p_tod'] <= 0.05),
        '5_post_paper_>0_ci_lo>0': bool((pp.get('theta') or -1) > 0 and lo(pp)),
        '6_stability': bool(yrs['total_net_bp'] > 0 and (yrs['max_share'] or 1) <= 0.40 and yrs['n_positive'] >= 6
                            and sum((sec[w]['pooled'].get('theta') or -1) > 0 for w in WINS) >= 2
                            and sum((sec[s]['pooled'].get('theta') or -1) > 0 for s in SYMS) >= 2),
        '7_DSR>=0.95': bool((out['DSR'].get('P_S1') or 0) >= 0.95),
        '8_stop_over_cost>=5': bool(all((c['median_stop_over_cost'] or 0) >= 5 for c in out['cells'].values())),
    }
    s0 = R['S0']['pooled'].get('theta')
    s0d = R['S0']['by_split'].get('discovery', {}).get('theta')
    s0h = R['S0']['by_split'].get('holdout', {}).get('theta')
    if s0 is None or s0 <= 0 or (s0d is not None and s0h is not None and np.sign(s0d) * np.sign(s0h) < 0):
        verdict = 'REJECTED'
    elif (h.get('n') or 0) < 1000:
        verdict = 'INSUFFICIENT-N'
    elif all(crit.values()):
        verdict = 'RESEARCH CANDIDATE (G4)'
    else:
        verdict = 'INCONCLUSIVE'
    n2 = out['N2_gross_replication']
    sign_match = {k: (x.get('theta') is not None and np.sign(x['theta']) == np.sign(x['paper_bp'])) for k, x in n2.items()}
    return {'criteria': crit, 'verdict': verdict, 'N2_sign_matches': int(sum(sign_match.values())),
            'N2_sign_match_by_cell': sign_match}


def smoke() -> None:
    """D10: counts / missing / stop rate only on a discovery slice; no P&L printed."""
    cal = load_calendars()
    for sym in ('EURUSD', 'USDJPY'):
        S = oc.load(sym)
        B = im.Bars(S)
        days = [d for d in eligible_days(S, '2017-12-31')]
        for w in WINS:
            df = run_cell(sym, B, days, w, cal)
            print(sym, w, 'days', len(days), 'trades', len(df), dict(df.attrs),
                  'stop_rate', round(float(df.stop.mean()), 4) if len(df) else None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', nargs='?', default='run')
    ap.add_argument('--stage', choices=['disc', 'val', 'full'])
    a = ap.parse_args()
    if a.cmd == 'build-calendars':
        c = build_calendars()
        with open(CAL_PATH, 'w') as f:
            json.dump(c, f, indent=1)
        print('wrote', CAL_PATH, {k: len(v) for k, v in c.items() if k != 'source'})
        return 0
    if a.cmd == 'smoke':
        smoke()
        return 0
    out = run_stage(a.stage)
    fn = os.path.join(HERE, 'fx1_results.json' if a.stage == 'full' else f'fx1_results_{a.stage}.json')
    with open(fn, 'w') as f:
        json.dump(out, f, indent=1, default=lambda x: oc._f(x) if isinstance(x, (np.floating, float)) else int(x)
                  if isinstance(x, (np.integer,)) else str(x))
    print('wrote', fn)
    print(json.dumps({'stage': a.stage, 'P': out['primary_P'], 'gross': out['gross_pooled'],
                      'post_paper': out['post_paper_2020+'], 'placebo_p': out['N1_placebo']['p_tod'],
                      'DSR': out['DSR'], 'acceptance': out.get('acceptance')}, indent=1, default=str))
    return 0


if __name__ == '__main__':
    sys.exit(main())
