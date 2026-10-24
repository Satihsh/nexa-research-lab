#!/usr/bin/env python3
"""IM1 market intraday momentum (PREREG_IM1_INTRADAY_MOMENTUM.md, sha aee2e870...; inherits PREREG_OF_COMMON.md).

Rule (Baltussen et al. 2021, timing strategy eta(r_ROD)): 30 min before the close C, go long if the return from the
previous valid day's close to C-30 is positive, short if negative; exit at C. Deviations: DEVIATIONS_IM1.md.

Usage:
  python3 im1_intraday_momentum.py build-calendar      # writes IM1_US_CALENDAR.json (frozen before discovery)
  python3 im1_intraday_momentum.py --stage disc|val|full
Research only: reads local Pepperstone M1 and the frozen calendar; writes results in this folder.
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

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import of_common as oc  # noqa: E402

sys.path.insert(0, '~/NEXA-Agent-Lab/filesnexa/NEXA/research')

SYMS = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
CLOSE = {'EURUSD': 15 * 60, 'GBPUSD': 15 * 60, 'USDJPY': 15 * 60, 'XAUUSD': 13 * 60 + 30}   # minutes NY (§2)
FX_CLOSE_ROBUST = 14 * 60
OPEN_ONFH = 8 * 60 + 20                                           # §8 robustness (r_ONFH to open + 30)
SPREAD_FLOOR = {'EURUSD': 0.00002, 'GBPUSD': 0.00002, 'USDJPY': 0.002, 'XAUUSD': 0.0}         # 0.2 pip FX (§4)
STRESS_BP = {'S0': 0.0, 'S1': 0.25, 'S2': 0.50}                   # per side
STOP_K = 4.0
SIG_LOOKBACK = 60
COST_FLOOR_FRAC = 0.20
WIN = 30
CAL_PATH = os.path.join(HERE, 'IM1_US_CALENDAR.json')
MT5_CAL = '~/NEXA-Agent-Lab/filesnexa/NEXA/data/pepperstone/calendar/canonical_v2/PEPPERSTONE_MT5_CALENDAR_canonical_v2.csv.gz'


def placebo_closes(C: int) -> list:
    """Every 15 min 06:00-16:45 NY excluding |t - C| <= 75 (§5; D2: 33 times)."""
    return [t for t in range(6 * 60, 16 * 60 + 46, 15) if abs(t - C) > 75]


# ----------------------------------------------------------------------------- calendar (§2, D1)
def easter(y: int) -> date:
    a, b, c = y % 19, y // 100, y % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    month = (h + l_ - 7 * m + 114) // 31
    day = ((h + l_ - 7 * m + 114) % 31) + 1
    return date(y, month, day)


def build_calendar() -> dict:
    cal = pd.read_csv(MT5_CAL, usecols=['country_code', 'type', 'time_server_text', 'event_name'])
    us = cal[(cal.country_code == 'US') & (cal.type == 2)]
    mt5 = sorted({pd.to_datetime(s, format='%Y.%m.%d %H:%M:%S').date().isoformat() for s in us.time_server_text})
    mt5 = [d for d in mt5 if '2017-01-01' <= d <= '2026-12-31']
    good_friday = [(easter(y) - timedelta(days=2)).isoformat() for y in range(2017, 2027)]
    early = []
    for y in range(2017, 2027):
        nov = [date(y, 11, d) for d in range(1, 31) if date(y, 11, d).weekday() == 3]
        early.append((nov[3] + timedelta(days=1)).isoformat())           # day after Thanksgiving
        for md in ((12, 24), (12, 31), (7, 3)):
            dd = date(y, *md)
            if dd.weekday() < 5:
                early.append(dd.isoformat())
    dates = sorted(set(mt5) | set(good_friday) | set(early))
    return {'source': 'MT5 calendar US type 2 + Good Friday (D1) + CME early closes (Fri after Thanksgiving, '
                      'Dec 24, Dec 31, Jul 3 if weekday)', 'mt5_us_holidays': mt5, 'good_friday': good_friday,
            'early_close': sorted(set(early)), 'dates': dates}


def load_calendar() -> set:
    with open(CAL_PATH) as f:
        return {date.fromisoformat(d) for d in json.load(f)['dates']}


# ----------------------------------------------------------------------------- bars / clock
class Bars:
    def __init__(self, S: oc.Sym):
        day_per_bar = np.empty(len(S.smin), dtype=object)
        sday_idx = np.empty(len(S.smin), dtype=np.int64)
        for i, (s, e) in enumerate(zip(S.start, S.end)):
            day_per_bar[s:e] = S.days[i]
            sday_idx[s:e] = i
        srv = pd.to_datetime(day_per_bar) + pd.to_timedelta(S.smin, unit='m')
        ny = pd.DatetimeIndex(srv - pd.Timedelta(hours=7))
        utc = ny.tz_localize('America/New_York', ambiguous='NaT', nonexistent='NaT').tz_convert('UTC')
        self.utc = (utc.as_unit('ns').asi8 // 60_000_000_000).astype(np.int64)
        self.o, self.h, self.l, self.c = S.o, S.h, S.l, S.c
        self.sday = sday_idx
        self.S = S

    def at(self, utc_minute: int) -> int:
        k = int(np.searchsorted(self.utc, utc_minute))
        return k if k < len(self.utc) and self.utc[k] == utc_minute else -1


def utc_min(d: date, ny_min: int) -> int:
    """UTC epoch minute of New York local time ny_min (minutes after midnight) on date d (DST-aware)."""
    t = pd.Timestamp(d.year, d.month, d.day) + pd.Timedelta(minutes=ny_min)
    return int(t.tz_localize('America/New_York').tz_convert('UTC').value // 60_000_000_000)


def price_at(B: Bars, d: date, ny_min: int) -> float:
    """P(T): bid close of the M1 bar whose open time is T - 1 min (§3)."""
    k = B.at(utc_min(d, ny_min) - 1)
    return float(B.c[k]) if k >= 0 else np.nan


# ----------------------------------------------------------------------------- one trade
def trade(sym: str, B: Bars, d: date, C: int, direction: int, spread: float, sig: float, stress_bp: float,
          stop_k: float = STOP_K, entry_mode: str = 'open') -> dict:
    i0 = B.at(utc_min(d, C - WIN)) if entry_mode == 'open' else B.at(utc_min(d, C - WIN) - 1)
    i1 = B.at(utc_min(d, C) - 1)
    if i0 < 0 or i1 < 0:
        return {'missing': True}
    ref = float(B.o[i0]) if entry_mode == 'open' else float(B.c[i0])
    start = i0 if entry_mode == 'open' else i0 + 1
    entry_px = ref + spread if direction == 1 else ref
    stop_dist = stop_k * sig * ref
    comm = oc.commission(sym, ref)
    if not (stop_dist > 0):
        return {'missing': True}
    if comm + spread > COST_FLOOR_FRAC * stop_dist:
        return {'skip': True}
    stop = entry_px - stop_dist if direction == 1 else entry_px + stop_dist
    exit_px, how = None, 'time'
    for k in range(start, i1 + 1):
        if direction == 1 and B.l[k] <= stop:
            exit_px = B.o[k] if (k > start and B.o[k] <= stop) else stop
            how = 'stop'
            break
        if direction == -1 and B.h[k] + spread >= stop:
            exit_px = (B.o[k] + spread) if (k > start and B.o[k] + spread >= stop) else stop
            how = 'stop'
            break
    if exit_px is None:
        exit_px = B.c[i1] if direction == 1 else B.c[i1] + spread
    pnl = (exit_px - entry_px) if direction == 1 else (entry_px - exit_px)
    net = pnl - comm - 2 * stress_bp * 1e-4 * ref
    return {'net_bp': net / ref * 1e4, 'gross_bp': (pnl + spread) / ref * 1e4, 'R': net / stop_dist,
            'exit': how, 'soc': stop_dist / (comm + spread)}


# ----------------------------------------------------------------------------- per-symbol event table
def eligible_days(S: oc.Sym, holidays: set) -> list:
    out = []
    for i, ds in enumerate(S.days):
        d = date.fromisoformat(ds)
        if ds >= oc.FIRST_DAY[S.sym] and d.weekday() < 5 and d not in holidays and bool(S.valid[i]):
            out.append(d)
    return out


def run_symbol(sym: str, B: Bars, days: list, C: int, stress: str, *, stop_k=STOP_K, entry_mode='open',
               spread_floor=None, predictor='ROD', max_day: str = oc.LAST_DAY) -> pd.DataFrame:
    """One row per eligible day with a signal; r_ROD anchored at the previous eligible day's close (§3)."""
    S = B.S
    pday = {d: i for i, d in enumerate(S.days)}
    floor = SPREAD_FLOOR[sym] if spread_floor is None else spread_floor
    # sigma of the [C-30, C) window log return over the previous 60 eligible days (causal)
    wr = {}
    for d in days:
        a, b = B.at(utc_min(d, C - WIN)), B.at(utc_min(d, C) - 1)
        if a >= 0 and b >= 0:
            wr[d] = math.log(B.c[b] / B.o[a])
    sig = pd.Series(wr).rolling(SIG_LOOKBACK, min_periods=SIG_LOOKBACK).std(ddof=1).shift(1)
    rows, miss, skip = [], 0, 0
    prev = None
    for d in days:
        if d.isoformat() > max_day:
            break
        p_prev_close = price_at(B, prev, C) if prev is not None else np.nan
        prev_was = prev
        prev = d
        if prev_was is None or (d - prev_was).days > 4:          # no valid previous close day (§2)
            miss += 1
            continue
        if predictor == 'ROD':
            p_sig = price_at(B, d, C - WIN)
        else:                                                    # r_ONFH: previous close -> open + 30 (§8)
            p_sig = price_at(B, d, OPEN_ONFH + WIN)
        p_lh0, p_lh1 = price_at(B, d, C - WIN), price_at(B, d, C)
        sg = sig.get(d, np.nan)
        if not (np.isfinite(p_prev_close) and np.isfinite(p_sig) and np.isfinite(p_lh0) and np.isfinite(p_lh1)
                and np.isfinite(sg)):
            miss += 1
            continue
        r = p_sig / p_prev_close - 1.0
        if r == 0:
            continue
        direction = 1 if r > 0 else -1
        k = B.at(utc_min(d, C - WIN))
        sp = S.sprd[B.sday[k]] if k >= 0 else np.nan
        if not np.isfinite(sp):
            miss += 1
            continue
        t = trade(sym, B, d, C, direction, max(floor, float(sp)), float(sg), STRESS_BP[stress], stop_k, entry_mode)
        if t.get('missing'):
            miss += 1
            continue
        if t.get('skip'):
            skip += 1
            continue
        rows.append({'d': d, 'sym': sym, 'split': oc.split_of(d.isoformat()), 'year': d.year, 'dir': direction,
                     'r_rod_bp': r * 1e4, 'r_lh_bp': (p_lh1 / p_lh0 - 1.0) * 1e4, 'net': t['net_bp'],
                     'gross': t['gross_bp'], 'R': t['R'], 'stop': t['exit'] == 'stop', 'soc': t['soc']})
    df = pd.DataFrame(rows)
    df.attrs.update({'missing': miss, 'skipped_cost_floor': skip})
    return df


# ----------------------------------------------------------------------------- statistics
def pooled_stat(df: pd.DataFrame, col: str = 'net') -> dict:
    """Equal weight per trade; day-block bootstrap over calendar days (block 20)."""
    if df.empty:
        return {'n': 0, 'mean': None}
    g = df.groupby('d')[col].agg(['sum', 'count']).sort_index()
    s, n = g['sum'].to_numpy(), g['count'].to_numpy()
    theta = s.sum() / n.sum()
    reps = oc.bootstrap(lambda ix: s[ix].sum() / n[ix].sum(), len(s))
    sd = float(df[col].std(ddof=1)) if len(df) > 1 else None
    return {'n': int(len(df)), 'days': int(len(g))} | oc.boot_summary(float(theta), reps) | {
        'sd_bp': sd, 'mde80_bp': (2.5 * sd / math.sqrt(len(df))) if sd else None}


def beta_stat(df: pd.DataFrame) -> dict:
    """Gross predictive regression r_LH = a + b r_ROD (bp), day-block bootstrap CI (N2)."""
    if len(df) < 10:
        return {'n': int(len(df))}
    days = np.array(sorted(df.d.unique()))
    by = {d: g for d, g in df.groupby('d')}
    x, y = df.r_rod_bp.to_numpy(), df.r_lh_bp.to_numpy()
    b = float(np.cov(x, y, ddof=1)[0, 1] / np.var(x, ddof=1))
    xs = [by[d].r_rod_bp.to_numpy() for d in days]
    ys = [by[d].r_lh_bp.to_numpy() for d in days]

    def stat(ix):
        xx = np.concatenate([xs[i] for i in ix])
        yy = np.concatenate([ys[i] for i in ix])
        v = np.var(xx, ddof=1)
        return np.cov(xx, yy, ddof=1)[0, 1] / v if v > 0 else np.nan
    reps = oc.bootstrap(stat, len(days))
    r2 = float(np.corrcoef(x, y)[0, 1] ** 2)
    return {'n': int(len(df)), 'beta': b, 'R2': r2} | {k: v for k, v in oc.boot_summary(b, reps).items() if k != 'theta'}


def year_check(df: pd.DataFrame) -> dict:
    tot = float(df.net.sum())
    yrs = sorted(df.year.unique())
    share = {int(y): (float(df[df.year == y].net.sum()) / tot if tot else None) for y in yrs}
    pos = {int(y): bool(df[df.year == y].net.mean() > 0) for y in yrs}
    return {'share': share, 'positive': pos, 'n_positive': int(sum(pos.values())), 'n_years': len(yrs),
            'max_share': max((abs(v) for v in share.values() if v is not None), default=None)}


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', nargs='?', default='run')
    ap.add_argument('--stage', choices=['disc', 'val', 'full'])
    a = ap.parse_args()
    if a.cmd == 'build-calendar':
        cal = build_calendar()
        with open(CAL_PATH, 'w') as f:
            json.dump(cal, f, indent=1)
        print(f"wrote {CAL_PATH}: {len(cal['dates'])} dates ({len(cal['mt5_us_holidays'])} MT5, "
              f"{len(cal['good_friday'])} Good Friday, {len(cal['early_close'])} early close)")
        return 0
    ms = oc.stage_max_split(a.stage)
    max_day = {0: '2022-12-31', 1: '2024-12-31', 2: oc.LAST_DAY}[ms]
    opened = oc.SPLIT_NAMES[:ms + 1]
    holidays = load_calendar()
    out = {'prereg_sha256': 'aee2e8705d45c954ffb6481c8fdde129bf12611f3110e25145d7944c32f31fba',
           'stage': a.stage, 'splits_opened': opened, 'symbols': {}, 'placebo_counts': {}}
    frames = {st: [] for st in STRESS_BP}
    plac = {}                                     # sym -> list of (C', mean S1 net)
    plac_frames = {}                              # rank -> list of frames for pooled placebo
    robust = {}
    for sym in SYMS:
        S = oc.load(sym)
        B = Bars(S)
        days = eligible_days(S, holidays)
        C = CLOSE[sym]
        for st in STRESS_BP:
            df = run_symbol(sym, B, days, C, st, max_day=max_day)
            frames[st].append(df)
            if st == 'S1':
                out['symbols'][sym] = {'eligible_days': len(days), 'trades': int(len(df)),
                                       'missing': df.attrs['missing'], 'skipped_cost_floor': df.attrs['skipped_cost_floor'],
                                       'stop_rate': float(df.stop.mean()) if len(df) else None,
                                       'median_stop_over_cost': float(df.soc.median()) if len(df) else None}
        pcs = placebo_closes(C)
        out['placebo_counts'][sym] = len(pcs)
        plac[sym] = []
        for rank, Cp in enumerate(pcs):
            dfp = run_symbol(sym, B, days, Cp, 'S1', max_day=max_day)
            plac[sym].append((Cp, float(dfp.net.mean()) if len(dfp) else np.nan))
            plac_frames.setdefault(rank, []).append(dfp)
        if a.stage == 'full':
            rb = {}
            if sym != 'XAUUSD':
                rb['fx_close_14'] = run_symbol(sym, B, days, FX_CLOSE_ROBUST, 'S1', max_day=max_day)
            rb['onfh_predictor'] = run_symbol(sym, B, days, C, 'S1', predictor='ONFH', max_day=max_day)
            rb['entry_close_C31'] = run_symbol(sym, B, days, C, 'S1', entry_mode='close', max_day=max_day)
            if sym != 'XAUUSD':
                rb['spread_floor_0.1pip'] = run_symbol(sym, B, days, C, 'S1', spread_floor=SPREAD_FLOOR[sym] / 2, max_day=max_day)
                rb['spread_floor_0.3pip'] = run_symbol(sym, B, days, C, 'S1', spread_floor=SPREAD_FLOOR[sym] * 1.5, max_day=max_day)
            rb['stop_3sigma'] = run_symbol(sym, B, days, C, 'S1', stop_k=3.0, max_day=max_day)
            rb['stop_6sigma'] = run_symbol(sym, B, days, C, 'S1', stop_k=6.0, max_day=max_day)
            for k, v in rb.items():
                robust.setdefault(k, []).append(v)
        del B, S
        print(sym, out['symbols'][sym], flush=True)

    P = {st: pd.concat(frames[st], ignore_index=True) for st in STRESS_BP}
    res = {}
    for st in STRESS_BP:
        res[st] = {'pooled': pooled_stat(P[st]),
                   'by_split': {oc.SPLIT_NAMES[s]: pooled_stat(P[st][P[st].split == s]) for s in range(ms + 1)}}
    out['primary_P'] = res
    out['gross_pooled'] = pooled_stat(P['S1'], 'gross')
    out['secondary'] = {s: {'pooled': pooled_stat(P['S1'][P['S1'].sym == s]),
                            'by_split': {oc.SPLIT_NAMES[k]: pooled_stat(P['S1'][(P['S1'].sym == s) & (P['S1'].split == k)])
                                         for k in range(ms + 1)},
                            'gross_mean_bp': float(P['S1'][P['S1'].sym == s].gross.mean())} for s in SYMS}
    pv = [out['secondary'][s]['pooled'].get('p_one_sided') for s in SYMS]
    out['BH_secondaries'] = dict(zip(SYMS, oc.bh(pv)))
    out['N2_beta'] = {'pooled': beta_stat(P['S1']), **{s: beta_stat(P['S1'][P['S1'].sym == s]) for s in SYMS},
                      'baltussen_reference': {'FX_pooled': 0.72, 'gold': 1.09}}
    # N1 placebo (S1 net): per symbol and pooled by rank
    obs = {s: float(P['S1'][P['S1'].sym == s].net.mean()) for s in SYMS}
    out['N1_placebo'] = {}
    for s in SYMS:
        means = np.array([m for _, m in plac[s]])
        out['N1_placebo'][s] = {'observed': obs[s], 'placebo_means': [(int(c), oc._f(m)) for c, m in plac[s]],
                                'p_tod': float((1 + np.sum(means >= obs[s])) / (len(means) + 1))}
    pooled_obs = float(P['S1'].net.mean())
    pooled_means = np.array([float(pd.concat(plac_frames[r], ignore_index=True).net.mean()) for r in sorted(plac_frames)])
    out['N1_placebo']['pooled'] = {'observed': pooled_obs, 'p_tod': float((1 + np.sum(pooled_means >= pooled_obs)) / (len(pooled_means) + 1)),
                                   'n_placebos': int(len(pooled_means))}
    # DSR (n_trials = 1 + 4 + 33 = 38, D2)
    try:
        from nexa_robust import deflated_sharpe
        srs = []
        for x in [P['S1'].net] + [P['S1'][P['S1'].sym == s].net for s in SYMS] + \
                 [pd.concat(plac_frames[r], ignore_index=True).net for r in sorted(plac_frames)]:
            x = np.asarray(x, float)
            if len(x) > 2 and x.std(ddof=1) > 0:
                srs.append(x.mean() / x.std(ddof=1))
        var_sr = float(np.var(srs, ddof=1))
        n_trials = 1 + len(SYMS) + len(plac_frames)
        out['DSR'] = {'P_S1': float(deflated_sharpe(P['S1'].net.to_numpy(), n_trials, var_sr)), 'n_trials': n_trials,
                      'var_sr_trials': var_sr}
    except Exception as e:  # noqa: BLE001
        out['DSR'] = {'error': repr(e)}
    out['years'] = year_check(P['S1'])
    if a.stage == 'full':
        out['robustness'] = {k: pooled_stat(pd.concat(v, ignore_index=True)) for k, v in robust.items()}
        big = P['S1'][P['S1'].r_rod_bp.abs() >= P['S1'].groupby('sym').r_rod_bp.transform(lambda z: z.abs().quantile(0.8))]
        out['robustness']['large_rod_days_top20pct'] = pooled_stat(big)
        out['robustness']['per_year'] = {int(y): pooled_stat(P['S1'][P['S1'].year == y]) for y in sorted(P['S1'].year.unique())}
        out['acceptance'] = acceptance(out)
    fn = os.path.join(HERE, 'im1_results.json' if a.stage == 'full' else f'im1_results_{a.stage}.json')
    with open(fn, 'w') as f:
        json.dump(out, f, indent=1, default=lambda x: oc._f(x) if isinstance(x, (np.floating, float)) else int(x)
                  if isinstance(x, (np.integer,)) else str(x))
    print('wrote', fn)
    print(json.dumps({'stage': a.stage, 'P_S1': res['S1'], 'gross': out['gross_pooled'],
                      'N2_beta_pooled': out['N2_beta']['pooled'], 'placebo_pooled': out['N1_placebo']['pooled'],
                      'DSR': out['DSR']}, indent=1, default=str))
    return 0


def acceptance(out: dict) -> dict:
    R = out['primary_P']
    d, v, h = (R['S1']['by_split'].get(s, {}) for s in ('discovery', 'validation', 'holdout'))
    pooled = R['S1']['pooled']
    sec = out['secondary']
    yrs = out['years']
    crit = {
        '1_discovery_p<0.05': bool((d.get('theta') or -1) > 0 and (d.get('p_one_sided') or 1) < 0.05),
        '2_val_holdout_>0': bool((v.get('theta') or -1) > 0 and (h.get('theta') or -1) > 0),
        '3_pooled_ci_lo>0': bool((pooled.get('ci95') or [None])[0] is not None and pooled['ci95'][0] > 0),
        '4_placebo_p<=0.05': bool(out['N1_placebo']['pooled']['p_tod'] <= 0.05),
        '5_mechanism_beta_ci_lo>0': bool((out['N2_beta']['pooled'].get('ci95') or [None])[0] is not None
                                         and out['N2_beta']['pooled']['ci95'][0] > 0),
        '6_stability': bool((yrs['max_share'] or 1) <= 0.5 and yrs['n_positive'] >= 6
                            and sum(1 for s in SYMS if (sec[s]['pooled'].get('theta') or -1) > 0) >= 3),
        '7_DSR>=0.95': bool((out['DSR'].get('P_S1') or 0) >= 0.95),
        '8_stop_over_cost>=5': bool(all((out['symbols'][s]['median_stop_over_cost'] or 0) >= 5 for s in SYMS)),
    }
    n_hold = (h.get('n') or 0)
    s0 = R['S0']['pooled'].get('theta')
    s0d = R['S0']['by_split'].get('discovery', {}).get('theta')
    s0h = R['S0']['by_split'].get('holdout', {}).get('theta')
    if s0 is None or s0 <= 0 or (s0d is not None and s0h is not None and np.sign(s0d) * np.sign(s0h) < 0):
        verdict = 'REJECTED'
    elif n_hold < 800:
        verdict = 'INSUFFICIENT-N'
    elif all(crit.values()):
        verdict = 'RESEARCH CANDIDATE (G4)'
    else:
        verdict = 'INCONCLUSIVE'
    return {'criteria': crit, 'verdict': verdict, 'gross_confirmed': crit['5_mechanism_beta_ci_lo>0']}


if __name__ == '__main__':
    sys.exit(main())
