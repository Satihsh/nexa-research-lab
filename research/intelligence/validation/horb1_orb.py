#!/usr/bin/env python3
"""H-ORB-1: 5-minute opening-range breakout on Pepperstone NAS100 (PREREG_HORB1_NAS100_ORB.md, sha af3b6169...).

Rule (Zarattini & Aziz 2023, §3 of the pre-registration): the 09:30-09:35 ET candle sets the direction (no trade on
a doji); enter at the 09:35 bar open (long pays the ask); stop at the first candle's low/high; target entry +/- 10R;
otherwise exit at the close of the 15:59 bar; a bar touching both stop and target counts as the stop.
Interpretations fixed before any NAS100 data was seen: DEVIATIONS_HORB1.md.

Usage:
  python3 horb1_orb.py --stage P      # replication period (first day -> 2023-02-17)
  python3 horb1_orb.py --stage H      # post-paper holdout (2023-02-18 -> last complete day); opened once
Research only: reads the frozen canonical NAS100 M1 export and the frozen IM1 US calendar; writes results here.
An existing results file is never overwritten (stages are opened once).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import of_common as oc  # noqa: E402  (read-only reuse: block bootstrap, BH)
import im1_intraday_momentum as im  # noqa: E402  (read-only reuse: frozen US calendar, NY->UTC clock)

DATA = ('~/NEXA-Agent-Lab/filesnexa/NEXA/data/pepperstone/m1_canonical/'
        'PEPPERSTONE_NAS100_M1_canonical.csv.gz')
POINT = 0.1                      # MT5 point of Pepperstone NAS100 (§2 spec probe 2026-10-01); spread column is in points
TICK = 0.1                       # price precision for the doji test (§3.2)
SPREAD_FLOOR = 1.0               # index points (§4 S0)
STRESS = {'S0': 0.0, 'S1': 0.5, 'S2': 1.0}   # extra index points per side (§4)
TARGET_R = 10.0
COST_FLOOR_FRAC = 0.20
OPEN_MIN = 9 * 60 + 30           # 09:30 ET
LAST_MIN = 15 * 60 + 59          # bar starting 15:59 ET
P_END = '2023-02-17'
H_START = '2023-02-18'
MIN_H_TRADES = 300
SEED = 20261012
B_BOOT = 2000
BLOCK = 20
USD_PER_POINT_PER_LOT = 1.0      # Pepperstone NAS100 (§2)
MIN_LOT = 0.1
MNQ_USD_PER_POINT = 2.0          # informational only (CME Micro E-mini Nasdaq-100)
EVENT_RE = re.compile(r'(fomc|fed interest rate decision|federal funds rate|consumer price index|\bcpi\b|'
                      r'nonfarm payrolls|non-farm payrolls)', re.I)


def placebo_times() -> list:
    """§5 N1: every 30 min 03:00-15:00 ET, excluding 08:30-10:30 inclusive -> 20 times."""
    return [t for t in range(3 * 60, 15 * 60 + 1, 30) if not (8 * 60 + 30 <= t <= 10 * 60 + 30)]


# ----------------------------------------------------------------------------- data
@dataclass
class Data:
    utc: np.ndarray       # UTC epoch minute of each bar's open (sorted, unique)
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    spr: np.ndarray       # recorded spread in price units
    audit: dict

    def at(self, utc_minute: int) -> int:
        k = int(np.searchsorted(self.utc, utc_minute))
        return k if k < len(self.utc) and self.utc[k] == utc_minute else -1

    def days(self) -> list:
        """NY calendar dates covered by the data (weekdays only)."""
        ny = pd.to_datetime(self.utc, unit='m', utc=True).tz_convert('America/New_York')
        ds = sorted({d for d in ny.date})
        return [d for d in ds if d.weekday() < 5]


def from_frame(df: pd.DataFrame, point: float = POINT) -> Data:
    """df: time_server ('%Y-%m-%d %H:%M:%S', server = New York + 7 h), open, high, low, close, spread (points)."""
    audit = {'rows_raw': int(len(df))}
    if 'time_status' in df.columns:
        ok = df.time_status.astype(str) == 'OK'
        audit['rows_status_not_ok'] = int((~ok).sum())
        df = df[ok]
    n0 = len(df)
    df = df.drop_duplicates('time_server', keep='first')
    audit['rows_duplicate_time_server'] = int(n0 - len(df))
    ts = pd.to_datetime(df.time_server, format='%Y-%m-%d %H:%M:%S')
    ny = pd.DatetimeIndex(ts - pd.Timedelta(hours=7))
    utc = ny.tz_localize('America/New_York', ambiguous='NaT', nonexistent='NaT').tz_convert('UTC')
    keep = ~pd.isna(utc)
    audit['rows_nat_clock'] = int((~keep).sum())
    df = df[keep]
    um = (utc[keep].as_unit('ns').asi8 // 60_000_000_000).astype(np.int64)
    order = np.argsort(um, kind='stable')
    um = um[order]
    uniq = np.r_[True, np.diff(um) > 0]
    audit['rows_duplicate_utc'] = int((~uniq).sum())
    sel = order[uniq]
    g = lambda col: df[col].to_numpy(float)[sel]  # noqa: E731
    return Data(um[uniq], g('open'), g('high'), g('low'), g('close'), g('spread') * point, audit)


def load(path: str = DATA) -> Data:
    df = pd.read_csv(path, usecols=lambda c: c in {'time_server', 'open', 'high', 'low', 'close', 'spread',
                                                    'time_status'}, dtype={'time_status': str})
    return from_frame(df)


# ----------------------------------------------------------------------------- one day
def utc_of(d: date, ny_min: int) -> int:
    return im.utc_min(d, ny_min)


def first_candle(D: Data, d: date, t0: int):
    """O1 = open(t0), C1 = close(t0+4), H1/L1 = extremes of t0..t0+4. None if any bar is missing (§3.1)."""
    ks = [D.at(utc_of(d, t0 + j)) for j in range(5)]
    if min(ks) < 0:
        return None
    return float(D.o[ks[0]]), float(D.c[ks[4]]), float(max(D.h[k] for k in ks)), float(min(D.l[k] for k in ks))


def direction(o1: float, c1: float, tick: float = TICK) -> int:
    a, b = round(o1 / tick), round(c1 / tick)
    return 1 if b > a else (-1 if b < a else 0)


def simulate(D: Data, d: date, t0: int = OPEN_MIN, *, stress: float = 0.0, spread_floor: float = SPREAD_FLOOR,
             target_r: float | None = TARGET_R, entry_mode: str = 'open', flip: bool = False,
             atr_stop: float | None = None) -> dict:
    """One trade of the rule anchored at t0 (minutes after NY midnight). Returns a dict with 'status'."""
    fc = first_candle(D, d, t0)
    if fc is None:
        return {'status': 'missing'}
    o1, c1, h1, l1 = fc
    dir0 = direction(o1, c1)
    if dir0 == 0:
        return {'status': 'doji'}
    ke = D.at(utc_of(d, t0 + 5))
    kx = D.at(utc_of(d, LAST_MIN))
    if ke < 0 or kx < 0 or kx <= ke:
        return {'status': 'missing'}
    spr = lambda k: max(float(D.spr[k]), spread_floor)  # noqa: E731
    if entry_mode == 'open':
        ref, start = float(D.o[ke]), ke
    else:                                                   # §8 robustness: entry at the 09:35 bar close
        ref, start = float(D.c[ke]), ke + 1
        if start > kx:
            return {'status': 'missing'}
    s_e = spr(ke)
    dirn = -dir0 if flip else dir0
    entry0 = ref + s_e if dirn == 1 else ref                # long pays the ask, short sells the bid (S0)
    if atr_stop is not None:
        r0 = atr_stop
    else:
        stop_orig = l1 if dir0 == 1 else h1
        entry_orig = ref + s_e if dir0 == 1 else ref
        r0 = (entry_orig - stop_orig) * dir0                # R of the original-direction rule (N2: same distance)
    if not (r0 > 0):
        return {'status': 'stop_breached_at_entry', 'dir': dirn}
    if s_e + 2 * stress > COST_FLOOR_FRAC * r0:
        return {'status': 'cost_floor', 'dir': dirn, 'R0': r0, 'spread_e': s_e}
    stop = entry0 - dirn * r0
    target = entry0 + dirn * target_r * r0 if target_r is not None else None
    entry = entry0 + dirn * stress
    exit_px, how = None, 'time'
    for k in range(start, kx + 1):
        sk = spr(k)
        gap_ok = k > start or entry_mode != 'open'
        if dirn == 1:
            hit_s = D.l[k] <= stop
            hit_t = target is not None and D.h[k] >= target
            if hit_s:
                exit_px = (float(D.o[k]) if gap_ok and D.o[k] <= stop else stop) - stress
                how = 'stop'
                break
            if hit_t:
                exit_px, how = target - stress, 'target'
                break
        else:
            hit_s = D.h[k] + sk >= stop
            hit_t = target is not None and D.l[k] + sk <= target
            if hit_s:
                exit_px = (float(D.o[k]) + sk if gap_ok and D.o[k] + sk >= stop else stop) + stress
                how = 'stop'
                break
            if hit_t:
                exit_px, how = target + stress, 'target'
                break
    if exit_px is None:
        exit_px = float(D.c[kx]) - stress if dirn == 1 else float(D.c[kx]) + spr(kx) + stress
    pnl = (exit_px - entry) * dirn
    return {'status': 'trade', 'dir': dirn, 'R0': r0, 'pnl_pts': pnl, 'R': pnl / r0, 'exit': how,
            'spread_e': s_e, 'ref': ref}


def buy_and_hold(D: Data, d: date, spread_floor: float = SPREAD_FLOOR) -> dict:
    """§5 N3: long 09:35 open (ask) -> 15:59 close (bid)."""
    ke, kx = D.at(utc_of(d, OPEN_MIN + 5)), D.at(utc_of(d, LAST_MIN))
    if ke < 0 or kx < 0:
        return {'status': 'missing'}
    entry = float(D.o[ke]) + max(float(D.spr[ke]), spread_floor)
    pnl = float(D.c[kx]) - entry
    return {'status': 'trade', 'pnl_pts': pnl, 'bp': pnl / entry * 1e4}


# ----------------------------------------------------------------------------- days
def eligible_days(D: Data, holidays: set, lo: str | None, hi: str | None, cal_lo: date, cal_hi: date) -> tuple:
    """US trading days in [lo, hi] inside the frozen calendar's coverage, not a holiday/early close (§2)."""
    out, audit = [], {'weekdays': 0, 'holiday_or_early_close': 0, 'outside_calendar': 0}
    for d in D.days():
        ds = d.isoformat()
        if (lo and ds < lo) or (hi and ds > hi):
            continue
        audit['weekdays'] += 1
        if d < cal_lo or d > cal_hi:
            audit['outside_calendar'] += 1
            continue
        if d in holidays:
            audit['holiday_or_early_close'] += 1
            continue
        out.append(d)
    return out, audit


def calendar() -> tuple:
    with open(im.CAL_PATH) as f:
        cal = json.load(f)
    years = sorted({int(x[:4]) for x in cal['dates']})
    return {date.fromisoformat(x) for x in cal['dates']}, date(years[0], 1, 1), date(years[-1], 12, 31)


def event_days() -> set:
    """§8: US FOMC / CPI / NFP release dates from the MT5 calendar (server date, converted to NY date)."""
    cal = pd.read_csv(im.MT5_CAL, usecols=['country_code', 'time_server_text', 'event_name'])
    us = cal[(cal.country_code == 'US') & cal.event_name.astype(str).str.contains(EVENT_RE)]
    ts = pd.to_datetime(us.time_server_text, format='%Y.%m.%d %H:%M:%S') - pd.Timedelta(hours=7)
    return set(ts.dt.date)


# ----------------------------------------------------------------------------- statistics
def boot(values: np.ndarray) -> dict:
    v = np.asarray(values, float)
    if len(v) < 2:
        return {'theta': float(v.mean()) if len(v) else None, 'ci95': [None, None], 'p_one_sided': None, 'n': len(v)}
    reps = oc.bootstrap(lambda idx: float(v[idx].mean()), len(v), B=B_BOOT, seed=SEED)
    return oc.boot_summary(float(v.mean()), reps) | {'n': int(len(v))}


def trades_frame(D: Data, days: list, **kw) -> tuple:
    rows, counts = [], {}
    for d in days:
        r = simulate(D, d, **kw)
        counts[r['status']] = counts.get(r['status'], 0) + 1
        if r['status'] == 'trade':
            rows.append({'day': d.isoformat(), 'year': d.year, **{k: r[k] for k in ('dir', 'R0', 'pnl_pts', 'R',
                                                                                  'exit', 'spread_e')}})
    return pd.DataFrame(rows), counts


def year_check(df: pd.DataFrame) -> dict:
    if df.empty:
        return {'years': {}, 'max_year_share': None, 'share_years_positive': None}
    by = df.groupby('year').R.sum()
    tot = float(by.sum())
    share = float(by.max() / tot) if tot > 0 else None
    return {'years': {int(k): float(v) for k, v in by.items()}, 'max_year_share': share,
            'share_years_positive': float((by > 0).mean())}


def sharpe(x) -> float:
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1)) if len(x) > 2 and x.std(ddof=1) > 0 else float('nan')


def analyse(D: Data, days: list, label: str, extra_days: set | None = None) -> dict:
    """Everything §5-§8 asks for, on one period."""
    out = {'period': label, 'n_days': len(days)}
    frames = {}
    for lvl, st in STRESS.items():
        df, counts = trades_frame(D, days, stress=st)
        frames[lvl] = df
        out[lvl] = {'counts': counts, 'mean_R': boot(df.R.to_numpy()) if len(df) else None,
                    'mean_pts': float(df.pnl_pts.mean()) if len(df) else None,
                    'win_rate': float((df.R > 0).mean()) if len(df) else None,
                    'exits': df.exit.value_counts().to_dict() if len(df) else {}}
    s1 = frames['S1']
    if len(s1):
        sec = {'long': s1[s1.dir == 1].R.to_numpy(), 'short': s1[s1.dir == -1].R.to_numpy()}
        sec |= {f'year_{y}': g.R.to_numpy() for y, g in s1.groupby('year')}
        b = {k: boot(v) for k, v in sec.items()}
        adj = oc.bh([x.get('p_one_sided') for x in b.values()])
        out['secondaries_S1'] = {k: v | {'p_bh': a} for (k, v), a in zip(b.items(), adj)}
        out['year_check_S1'] = year_check(s1)
        out['cost_check'] = {'median_R0_pts': float(s1.R0.median()), 'median_spread_e': float(s1.spread_e.median()),
                             'ok': bool(s1.R0.median() >= 10 * (s1.spread_e.median() + 2 * STRESS['S1']))}
        out['sizing'] = {'share_R0_le_20pts': float((s1.R0 <= 20).mean()),
                         'account_for_1pct_at_median_R0_usd_nas100': float(MIN_LOT * USD_PER_POINT_PER_LOT *
                                                                           s1.R0.median() / 0.01),
                         'account_for_1pct_at_median_R0_usd_mnq': float(MNQ_USD_PER_POINT * s1.R0.median() / 0.01)}
    # N1 timing placebo (S1, identical rule at other anchors)
    obs = float(s1.R.mean()) if len(s1) else float('nan')
    pl = {}
    for t in placebo_times():
        df, _ = trades_frame(D, days, t0=t, stress=STRESS['S1'])
        pl[t] = df.R.to_numpy()
    pm = {t: float(v.mean()) if len(v) else float('nan') for t, v in pl.items()}
    finite = [m for m in pm.values() if np.isfinite(m)]
    out['N1_placebo'] = {'observed': obs, 'n_placebos': len(pl),
                         'p_tod': float((1 + sum(m >= obs for m in finite)) / (1 + len(finite))) if finite else None,
                         'by_time': {f'{t // 60:02d}:{t % 60:02d}': {'mean_R': pm[t], 'n': int(len(pl[t]))}
                                     for t in pl}}
    # N2 direction placebo, N3 buy-and-hold
    n2, _ = trades_frame(D, days, stress=STRESS['S1'], flip=True)
    out['N2_opposite_S1'] = boot(n2.R.to_numpy()) if len(n2) else None
    bh_ = [buy_and_hold(D, d) for d in days]
    bh_ = [x for x in bh_ if x['status'] == 'trade']
    out['N3_buy_hold'] = {'n': len(bh_), 'mean_pts': float(np.mean([x['pnl_pts'] for x in bh_])) if bh_ else None,
                          'mean_bp': float(np.mean([x['bp'] for x in bh_])) if bh_ else None}
    # DSR: n_trials = 1 (primary) + 2 (long-only, short-only) + placebo times (DEVIATIONS_HORB1 I-5)
    try:
        sys.path.insert(0, '~/NEXA-Agent-Lab/filesnexa/NEXA/research')
        from nexa_robust import deflated_sharpe
        series = [s1.R.to_numpy(), s1[s1.dir == 1].R.to_numpy(), s1[s1.dir == -1].R.to_numpy()] + list(pl.values())
        srs = [sharpe(x) for x in series]
        srs = [x for x in srs if np.isfinite(x)]
        var_sr = float(np.var(srs, ddof=1)) if len(srs) > 1 else float('nan')
        out['DSR'] = {'S1': float(deflated_sharpe(s1.R.to_numpy(), len(series), var_sr)),
                      'n_trials': len(series), 'var_sr_trials': var_sr}
    except Exception as e:  # noqa: BLE001
        out['DSR'] = {'error': repr(e)}
    # §8 robustness (reported only)
    rob = {}
    variants = {'atr_stop_no_target': None, 'target_5R': {'target_r': 5.0}, 'no_target': {'target_r': None},
                'entry_bar_close': {'entry_mode': 'close'}, 'spread_floor_0.5': {'spread_floor': 0.5},
                'spread_floor_2.0': {'spread_floor': 2.0}}
    for name, kw in variants.items():
        if kw is None:
            df = atr_variant(D, days)
        else:
            df, _ = trades_frame(D, days, stress=STRESS['S1'], **kw)
        rob[name] = boot(df.R.to_numpy()) if len(df) else None
    if extra_days is not None:
        df, _ = trades_frame(D, [d for d in days if d not in extra_days], stress=STRESS['S1'])
        rob['excl_fomc_cpi_nfp'] = boot(df.R.to_numpy()) if len(df) else None
    df, _ = trades_frame(D, [d for d in days if d.year != 2020], stress=STRESS['S1'])
    rob['excl_2020'] = boot(df.R.to_numpy()) if len(df) else None
    out['robustness_S1'] = rob
    return out


def atr_variant(D: Data, days: list) -> pd.DataFrame:
    """§8: stop = 5 % of the 14-day ATR of the RTH session (09:30-15:59), no target, EoD exit; S1."""
    rth = {}
    for d in days:
        ks = [D.at(utc_of(d, m)) for m in (OPEN_MIN, LAST_MIN)]
        if min(ks) < 0:
            continue
        sl = slice(ks[0], ks[1] + 1)
        rth[d] = (float(D.h[sl].max()), float(D.l[sl].min()), float(D.c[ks[1]]))
    ds = sorted(rth)
    rows = []
    for i, d in enumerate(ds):
        if i < 15:
            continue
        trs = []
        for j in range(i - 14, i):
            h, l_, _ = rth[ds[j]]
            pc = rth[ds[j - 1]][2]
            trs.append(max(h - l_, abs(h - pc), abs(l_ - pc)))
        r = simulate(D, d, stress=STRESS['S1'], target_r=None, atr_stop=0.05 * float(np.mean(trs)))
        if r['status'] == 'trade':
            rows.append({'day': d.isoformat(), 'year': d.year, 'R': r['R'], 'dir': r['dir']})
    return pd.DataFrame(rows)


def acceptance(P: dict | None, H: dict) -> dict:
    nH = H['S1']['counts'].get('trade', 0)
    h1 = H['S1']['mean_R'] or {}
    h0 = H['S0']['mean_R'] or {}
    p_ok = P is not None and P.get('sufficient', False)
    p1 = (P or {}).get('S1', {}).get('mean_R') or {}
    yc = H.get('year_check_S1', {})
    sec = H.get('secondaries_S1', {})
    checks = {
        '1_P_mean>0_p<0.05': (bool((p1.get('theta') or 0) > 0 and (p1.get('p_one_sided') or 1) < 0.05)
                              if p_ok else 'P_INSUFFICIENT'),
        '2_H_mean>0_ci_lo>0': bool((h1.get('theta') or 0) > 0 and (h1.get('ci95') or [None])[0] is not None
                                   and h1['ci95'][0] > 0),
        '3_p_tod<=0.05': bool((H['N1_placebo'].get('p_tod') or 1) <= 0.05),
        '4a_no_year>40%': bool(yc.get('max_year_share') is not None and yc['max_year_share'] <= 0.40),
        '4b_years_positive>=60%': bool((yc.get('share_years_positive') or 0) >= 0.60),
        '4c_long_and_short>=0': bool(all((sec.get(k, {}).get('theta') or -1) >= 0 for k in ('long', 'short'))),
        '5_DSR>=0.95': bool((H.get('DSR', {}).get('S1') or 0) >= 0.95),
        '6_cost_check': bool(H.get('cost_check', {}).get('ok', False)),
    }
    sign = lambda x: (x > 0) - (x < 0)  # noqa: E731
    if nH < MIN_H_TRADES:
        verdict = 'INSUFFICIENT-N'
    elif (h0.get('theta') or 0) <= 0 or (p_ok and sign(p1.get('theta') or 0) != sign(h1.get('theta') or 0)):
        verdict = 'REJECTED'
    elif all(v is True or v == 'P_INSUFFICIENT' for v in checks.values()):
        verdict = 'RESEARCH_CANDIDATE (G4)'
    else:
        verdict = 'INCONCLUSIVE'
    return {'checks': checks, 'verdict': verdict, 'n_H_trades_S1': nH}


def _json(path: str, obj: dict) -> None:
    if os.path.exists(path):
        sys.exit(f'REFUSED: {os.path.basename(path)} exists (stages are opened once)')
    with open(path, 'w') as f:
        json.dump(obj, f, indent=1, default=str)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', choices=['P', 'H'], required=True)
    ap.add_argument('--data', default=DATA, help='canonical M1 CSV (DEVIATIONS_HORB1 D-4)')
    a = ap.parse_args()
    D = load(a.data)
    D.audit['data_path'] = a.data
    hol, cal_lo, cal_hi = calendar()
    ev = event_days()
    all_days = D.days()
    first, last = all_days[0].isoformat(), all_days[-1].isoformat()
    if a.stage == 'P':
        days, aud = eligible_days(D, hol, None, P_END, cal_lo, cal_hi)
        sufficient = bool(days) and (date.fromisoformat('2023-02-18') - days[0]).days >= 730
        res = {'data_audit': D.audit, 'data_first_ny_day': first, 'data_last_ny_day': last, 'day_audit': aud,
               'sufficient': sufficient}
        if sufficient:
            res |= analyse(D, days, 'P', ev)
        _json(os.path.join(HERE, 'horb1_results_P.json'), res)
    else:
        pth = os.path.join(HERE, 'horb1_results_P.json')
        if not os.path.exists(pth):
            sys.exit('REFUSED: run --stage P first')
        with open(pth) as f:
            P = json.load(f)
        days, aud = eligible_days(D, hol, H_START, None, cal_lo, cal_hi)
        days = [d for d in days if d < all_days[-1]]          # last complete day only
        H = {'day_audit': aud} | analyse(D, days, 'H', ev)
        H['acceptance'] = acceptance(P, H)
        _json(os.path.join(HERE, 'horb1_results_H.json'), H)
        print(json.dumps(H['acceptance'], indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
