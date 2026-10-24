#!/usr/bin/env python3
"""H-IVB1-NQ: Fabio Valentini's IVB Model 1 on CME NQ (PREREG_HIVB1_NQ.md, sha 3ef68268...).

Range 09:30-09:59 ET -> fixed volume profile (0.25-pt bins, each bar's volume spread uniformly over its range;
POC + 70 % VA via of_common.va_greedy) -> first 5-min candle closing outside the range sets the direction ->
limit at the near VA edge (VAH long / VAL short, fill needs a 1-tick trade-through) -> exits: 5-min close beyond the
far VA edge (invalidation), hard stop at the range's opposite extreme, target 2R, time exit 15:59.
Interpretations fixed before the run: DEVIATIONS_HIVB1_HIM.md.

Usage:  python3 hivb1_nq.py [--data <csv with volume>]     (one stage; results file is never overwritten)
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import of_common as oc  # noqa: E402  (read-only: va_greedy, bootstrap, boot_summary, bh)
import horb1_orb as hb  # noqa: E402  (read-only: clock, calendar, eligible days, event days)

DATA = ('~/NEXA-Agent-Lab/research/intelligence/orderflow/databento/data/'
        'NQ_v0_ohlcv1m_2023-02-18_2026-10-10_volume.csv.gz')
W = 0.25                      # NQ tick = profile bin
TICK = 0.25
RANGE_START = 9 * 60 + 30
RANGE_LEN = 30
DEADLINE = 15 * 60            # breakout candle must close / limit must fill before 15:00
LAST = 15 * 60 + 59
TARGET_R = 2.0
VA_FRAC = 0.70
COST = {'S0': 1.0, 'S1': 2.0, 'S2': 3.0}   # NQ points per round trip (§4)
MIN_R = 10.0                  # cost floor: S1 cost 2.0 > 20 % of R  <=>  R < 10 points
SEED = 20261013
B_BOOT = 2000
N_TRIALS = 69
MIN_TRADES = 200
MNQ_USD_PER_POINT = 2.0


def placebo_anchors() -> list:
    """§5 N1: every 30 min 02:30-08:00 and 11:00-14:00 ET -> 19 anchors."""
    return list(range(2 * 60 + 30, 8 * 60 + 1, 30)) + list(range(11 * 60, 14 * 60 + 1, 30))


# ----------------------------------------------------------------------------- data with volume
@dataclass
class DV:
    utc: np.ndarray
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    v: np.ndarray
    audit: dict = field(default_factory=dict)

    def at(self, utc_minute: int) -> int:
        k = int(np.searchsorted(self.utc, utc_minute))
        return k if k < len(self.utc) and self.utc[k] == utc_minute else -1

    def days(self) -> list:
        ny = pd.to_datetime(self.utc, unit='m', utc=True).tz_convert('America/New_York')
        return [d for d in sorted(set(ny.date)) if d.weekday() < 5]


def from_frame(df: pd.DataFrame) -> DV:
    """time_server = New York + 7 h (as horb1_orb.from_frame), plus a `volume` column."""
    audit = {'rows_raw': int(len(df))}
    df = df.drop_duplicates('time_server', keep='first')
    ts = pd.to_datetime(df.time_server, format='%Y-%m-%d %H:%M:%S')
    ny = pd.DatetimeIndex(ts - pd.Timedelta(hours=7))
    utc = ny.tz_localize('America/New_York', ambiguous='NaT', nonexistent='NaT').tz_convert('UTC')
    keep = ~pd.isna(utc)
    df = df[keep]
    um = (utc[keep].as_unit('ns').asi8 // 60_000_000_000).astype(np.int64)
    order = np.argsort(um, kind='stable')
    um = um[order]
    uniq = np.r_[True, np.diff(um) > 0]
    sel = order[uniq]
    g = lambda col: df[col].to_numpy(float)[sel]  # noqa: E731
    audit.update({'rows_kept': int(uniq.sum()), 'rows_nat_clock': int((~keep).sum())})
    return DV(um[uniq], g('open'), g('high'), g('low'), g('close'), g('volume'), audit)


def load(path: str = DATA) -> DV:
    return from_frame(pd.read_csv(path, usecols=['time_server', 'open', 'high', 'low', 'close', 'volume']))


# ----------------------------------------------------------------------------- profile (§3.2)
def profile(h: np.ndarray, l: np.ndarray, v: np.ndarray):
    """Uniform spread of each bar's volume over its 0.25-pt bins. Returns (VAL, VAH, POC) or None."""
    if len(h) == 0 or float(np.sum(v)) <= 0:
        return None
    lo_k = np.floor(np.asarray(l) / W + 1e-9).astype(np.int64)
    hi_k = np.floor(np.asarray(h) / W + 1e-9).astype(np.int64)
    k0 = int(lo_k.min())
    vol = np.zeros(int(hi_k.max()) - k0 + 1)
    for a, b, x in zip(lo_k - k0, hi_k - k0, v):
        vol[a:b + 1] += x / (b - a + 1)
    poc, lo, hi = oc.va_greedy(vol, VA_FRAC)
    return (k0 + lo) * W, (k0 + hi + 1) * W, (k0 + poc) * W


def default_deadline(t0: int) -> int:
    """Primary deadline 15:00; earlier anchors keep the primary's 5.5 h window, capped at 15:00 (I-1)."""
    return min(t0 + (DEADLINE - RANGE_START), DEADLINE)


def setup(D: DV, d, t0: int = RANGE_START, rlen: int = RANGE_LEN, deadline: int | None = None):
    deadline = default_deadline(t0) if deadline is None else deadline
    ks = [D.at(hb.utc_of(d, t0 + j)) for j in range(rlen)]
    if min(ks) < 0:
        return {'status': 'missing'}
    A, Bv = float(D.h[ks].max()), float(D.l[ks].min())
    prof = profile(D.h[ks], D.l[ks], D.v[ks])
    if prof is None:
        return {'status': 'missing'}
    val, vah, poc = prof
    grid0 = t0 + rlen
    m = grid0
    while m + 5 <= deadline:
        kc = D.at(hb.utc_of(d, m + 4))
        if kc >= 0:
            cl = float(D.c[kc])
            if cl > A:
                return {'status': 'ok', 'dir': 1, 'A': A, 'B': Bv, 'VAL': val, 'VAH': vah, 'POC': poc,
                        'scan_from': m + 5, 'grid0': grid0, 'deadline': deadline}
            if cl < Bv:
                return {'status': 'ok', 'dir': -1, 'A': A, 'B': Bv, 'VAL': val, 'VAH': vah, 'POC': poc,
                        'scan_from': m + 5, 'grid0': grid0, 'deadline': deadline}
        m += 5
    return {'status': 'no_breakout'}


# ----------------------------------------------------------------------------- one day (§3.4-3.8)
def simulate(D: DV, d, t0: int = RANGE_START, *, rlen: int = RANGE_LEN, cost: float = COST['S1'],
             target_r: float = TARGET_R, entry_mode: str = 'edge', inval_tf: int = 5, hard_stop: bool = True,
             max_trades: int = 1, fade: bool = False, deadline: int | None = None) -> dict:
    if D.at(hb.utc_of(d, LAST)) < 0:
        return {'status': 'missing'}
    S = setup(D, d, t0, rlen, deadline)
    if S['status'] != 'ok':
        return S
    dir0 = S['dir']
    if entry_mode == 'edge':
        level = S['VAH'] if dir0 == 1 else S['VAL']
    else:                                                   # §8 robustness: entry at the POC
        level = S['POC']
    inval = S['VAL'] if dir0 == 1 else S['VAH']
    R = (level - inval) * dir0
    if not (R >= MIN_R):
        return {'status': 'cost_floor', 'R': R}
    dirn = -dir0 if fade else dir0
    if fade:                                                # N2: same level, same R, same target multiple
        stop, use_inval = level - dirn * R, False
    else:
        stop, use_inval = (S['B'] if dirn == 1 else S['A']), True
    target = level + dirn * target_r * R
    trades, state, entry, fill_m = [], 'wait', None, None
    for m in range(S['scan_from'], LAST + 1):
        k = D.at(hb.utc_of(d, m))
        if k < 0:
            continue
        o_, h_, l_, c_ = float(D.o[k]), float(D.h[k]), float(D.l[k]), float(D.c[k])
        candle_end = ((m - S['grid0']) % 5 == 4) if inval_tf == 5 else True
        exit_px, how = None, None
        if state == 'wait':
            if m >= S['deadline']:
                break
            hit = (l_ <= level - TICK) if dir0 == 1 else (h_ >= level + TICK)   # the retrace touch (also for N2)
            if not hit:
                if use_inval and candle_end and ((c_ < inval) if dir0 == 1 else (c_ > inval)):
                    break                                   # setup invalidated before a fill
                continue
            state, entry, fill_m = 'in', level, m
            if hard_stop and ((l_ <= stop) if dirn == 1 else (h_ >= stop)):
                exit_px, how = stop, 'stop'                 # fill bar: stop only, never the target
            elif use_inval and candle_end and ((c_ < inval) if dir0 == 1 else (c_ > inval)):
                exit_px, how = c_, 'invalidation'
        else:
            hit_s = hard_stop and ((l_ <= stop) if dirn == 1 else (h_ >= stop))
            hit_t = (h_ >= target + TICK) if dirn == 1 else (l_ <= target - TICK)
            if hit_s:
                gap = (o_ <= stop) if dirn == 1 else (o_ >= stop)
                exit_px, how = (o_ if gap else stop), 'stop'
            elif hit_t:
                exit_px, how = target, 'target'
            elif use_inval and candle_end and ((c_ < inval) if dir0 == 1 else (c_ > inval)):
                exit_px, how = c_, 'invalidation'
        if state == 'in' and exit_px is None and m == LAST:
            exit_px, how = c_, 'time'
        if exit_px is not None:
            pnl = (exit_px - entry) * dirn - cost
            trades.append({'dir': dirn, 'R_pts': R, 'pnl_pts': pnl, 'R': pnl / R, 'exit': how,
                           'fill_min': fill_m})
            state = 'wait'
            if len(trades) >= max_trades or how != 'target':
                break
    if not trades:
        return {'status': 'no_fill'}
    return {'status': 'trade', 'trades': trades}


# ----------------------------------------------------------------------------- statistics
def boot(x) -> dict:
    v = np.asarray(x, float)
    if len(v) < 2:
        return {'theta': float(v.mean()) if len(v) else None, 'ci95': [None, None], 'p_one_sided': None, 'n': len(v)}
    reps = oc.bootstrap(lambda idx: float(v[idx].mean()), len(v), B=B_BOOT, seed=SEED)
    return oc.boot_summary(float(v.mean()), reps) | {'n': int(len(v))}


def frame(D: DV, days: list, **kw) -> tuple:
    rows, counts = [], {}
    for d in days:
        r = simulate(D, d, **kw)
        counts[r['status']] = counts.get(r['status'], 0) + 1
        for t in r.get('trades', []):
            rows.append({'day': d.isoformat(), 'year': d.year, **t})
    return pd.DataFrame(rows), counts


def year_check(df: pd.DataFrame, col: str = 'R') -> dict:
    if df.empty:
        return {'years': {}, 'max_year_share': None, 'share_years_positive': None}
    by = df.groupby('year')[col].sum()
    tot = float(by.sum())
    return {'years': {int(k): float(x) for k, x in by.items()},
            'max_year_share': float(by.max() / tot) if tot > 0 else None,
            'share_years_positive': float((by > 0).mean())}


def sharpe(x) -> float:
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1)) if len(x) > 2 and x.std(ddof=1) > 0 else float('nan')


def analyse(D: DV, days: list, ev: set) -> dict:
    out = {'n_days': len(days)}
    fr = {}
    for lvl, cst in COST.items():
        df, counts = frame(D, days, cost=cst)
        fr[lvl] = df
        out[lvl] = {'counts': counts, 'mean_R': boot(df.R) if len(df) else None,
                    'mean_pts': float(df.pnl_pts.mean()) if len(df) else None,
                    'win_rate': float((df.R > 0).mean()) if len(df) else None,
                    'exits': df.exit.value_counts().to_dict() if len(df) else {}}
    s1 = fr['S1']
    if len(s1):
        sec = {'long': s1[s1.dir == 1].R.to_numpy(), 'short': s1[s1.dir == -1].R.to_numpy()}
        sec |= {f'year_{y}': g.R.to_numpy() for y, g in s1.groupby('year')}
        b = {k: boot(v) for k, v in sec.items()}
        adj = oc.bh([x.get('p_one_sided') for x in b.values()])
        out['secondaries_S1'] = {k: v | {'p_bh': a} for (k, v), a in zip(b.items(), adj)}
        out['year_check_S1'] = year_check(s1)
        out['cost_check'] = {'median_R_pts': float(s1.R_pts.median()), 'ok': bool(s1.R_pts.median() >= 10 * COST['S1'])}
        out['sizing'] = {'account_for_1pct_at_median_R_usd_mnq': float(MNQ_USD_PER_POINT * s1.R_pts.median() / 0.01)}
    obs = float(s1.R.mean()) if len(s1) else float('nan')
    pl = {}
    for t in placebo_anchors():
        df, _ = frame(D, days, t0=t, cost=COST['S1'])
        pl[t] = df.R.to_numpy() if len(df) else np.array([])
    pm = {t: float(x.mean()) if len(x) else float('nan') for t, x in pl.items()}
    fin = [x for x in pm.values() if np.isfinite(x)]
    out['N1_placebo'] = {'observed': obs, 'n_anchors': len(pl),
                         'p_tod': float((1 + sum(x >= obs for x in fin)) / (1 + len(fin))) if fin else None,
                         'by_anchor': {f'{t // 60:02d}:{t % 60:02d}': {'mean_R': pm[t], 'n': int(len(pl[t]))} for t in pl}}
    n2, _ = frame(D, days, cost=COST['S1'], fade=True)
    out['N2_fade_S1'] = boot(n2.R) if len(n2) else None
    try:
        sys.path.insert(0, '~/NEXA-Agent-Lab/filesnexa/NEXA/research')
        from nexa_robust import deflated_sharpe
        series = [s1.R.to_numpy(), s1[s1.dir == 1].R.to_numpy(), s1[s1.dir == -1].R.to_numpy()] + list(pl.values())
        srs = [x for x in (sharpe(s) for s in series) if np.isfinite(x)]
        var_sr = float(np.var(srs, ddof=1)) if len(srs) > 1 else float('nan')
        out['DSR'] = {'S1': float(deflated_sharpe(s1.R.to_numpy(), N_TRIALS, var_sr)), 'n_trials': N_TRIALS,
                      'var_sr_own_series': var_sr}
    except Exception as e:  # noqa: BLE001
        out['DSR'] = {'error': repr(e)}
    rob = {}
    for name, kw in {'range_15min': {'rlen': 15}, 'target_2.5R': {'target_r': 2.5}, 'entry_at_POC': {'entry_mode': 'poc'},
                     'invalidation_1min_close': {'inval_tf': 1}, 'no_hard_stop': {'hard_stop': False},
                     'reentries_up_to_3': {'max_trades': 3}}.items():
        df, _ = frame(D, days, cost=COST['S1'], **kw)
        rob[name] = boot(df.R) if len(df) else None
    df, _ = frame(D, [d for d in days if d not in ev], cost=COST['S1'])
    rob['excl_fomc_cpi_nfp'] = boot(df.R) if len(df) else None
    out['robustness_S1'] = rob
    return out


def acceptance(H: dict) -> dict:
    n = H['S1']['counts'].get('trade', 0)
    m1, m0 = H['S1']['mean_R'] or {}, H['S0']['mean_R'] or {}
    yc, sec = H.get('year_check_S1', {}), H.get('secondaries_S1', {})
    checks = {
        '1_mean>0_ci_lo>0': bool((m1.get('theta') or 0) > 0 and (m1.get('ci95') or [None])[0] is not None
                                 and m1['ci95'][0] > 0),
        '2_p_tod<=0.05': bool((H['N1_placebo'].get('p_tod') or 1) <= 0.05),
        '3a_no_year>40%': bool(yc.get('max_year_share') is not None and yc['max_year_share'] <= 0.40),
        '3b_years_positive>=60%': bool((yc.get('share_years_positive') or 0) >= 0.60),
        '3c_long_and_short>=0': bool(all((sec.get(k, {}).get('theta') or -1) >= 0 for k in ('long', 'short'))),
        '4_DSR>=0.95': bool((H.get('DSR', {}).get('S1') or 0) >= 0.95),
        '5_median_R>=20pts': bool(H.get('cost_check', {}).get('ok', False)),
    }
    if n < MIN_TRADES:
        verdict = 'INSUFFICIENT-N'
    elif (m0.get('theta') or 0) <= 0:
        verdict = 'REJECTED'
    elif all(checks.values()):
        verdict = 'RESEARCH_CANDIDATE (G4)'
    else:
        verdict = 'INCONCLUSIVE'
    return {'checks': checks, 'verdict': verdict, 'n_trades_S1': n}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default=DATA)
    a = ap.parse_args()
    outp = os.path.join(HERE, 'hivb1_results.json')
    if os.path.exists(outp):
        sys.exit('REFUSED: hivb1_results.json exists (opened once)')
    D = load(a.data)
    hol, lo, hi = hb.calendar()
    all_days = D.days()
    days, aud = hb.eligible_days(D, hol, None, None, lo, hi)
    days = [d for d in days if d < all_days[-1]]
    H = {'data_path': a.data, 'data_audit': D.audit, 'day_audit': aud, 'first_day': days[0].isoformat(),
         'last_day': days[-1].isoformat()} | analyse(D, days, hb.event_days())
    H['acceptance'] = acceptance(H)
    with open(outp, 'w') as f:
        json.dump(H, f, indent=1, default=str)
    print(json.dumps(H['acceptance'], indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
