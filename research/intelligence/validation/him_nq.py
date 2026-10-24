#!/usr/bin/env python3
"""H-IM-NQ: market intraday momentum on CME NQ (PREREG_HIM_NQ.md, sha 1113e2ee...).

Primary (Baltussen et al. 2021): r = close(15:29 bar) / close(15:59 bar, previous eligible day) - 1; trade sign(r)
from the 15:30 bar open to the 15:59 bar close; no stop, no target. Secondary (Gao et al. 2018): signal from the
previous close to the 09:59 bar close, same trade. Interpretations fixed before the run: DEVIATIONS_HIVB1_HIM.md.

Usage:  python3 him_nq.py [--data <canonical csv>]      (one stage; results file is never overwritten)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timedelta

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import of_common as oc  # noqa: E402
import horb1_orb as hb  # noqa: E402

DATA = ('~/NEXA-Agent-Lab/research/intelligence/orderflow/databento/data/'
        'NQ_v0_ohlcv1m_2023-02-18_2026-10-10_canonical.csv.gz')
T_END = 16 * 60                # trade window [T_END - 30, T_END)
LAST = 15 * 60 + 59
FH_MIN = 9 * 60 + 59           # Gao: close of the 09:59 bar
COST = {'S0': 1.0, 'S1': 2.0, 'S2': 3.0}
SEED = 20261013
B_BOOT = 2000
N_TRIALS = 69
MIN_TRADES = 600


def placebo_ends() -> list:
    """§5 N1: window ends every 15 min 10:30-15:15 ET -> 20 placebos."""
    return list(range(10 * 60 + 30, 15 * 60 + 16, 15))


def prev_weekday(d: date) -> date:
    p = d - timedelta(days=1)
    while p.weekday() >= 5:
        p -= timedelta(days=1)
    return p


def close_at(D, d: date, m: int):
    k = D.at(hb.utc_of(d, m))
    return float(D.c[k]) if k >= 0 else None


def trade(D, d: date, prev: date, *, t_end: int = T_END, signal: str = 'rod', cost: float = COST['S1'],
          entry_mode: str = 'open') -> dict:
    pc = close_at(D, prev, LAST)
    sig_px = close_at(D, d, t_end - 31) if signal == 'rod' else close_at(D, d, FH_MIN)
    ke, kx = D.at(hb.utc_of(d, t_end - 30)), D.at(hb.utc_of(d, t_end - 1))
    if pc is None or sig_px is None or ke < 0 or kx < 0 or (entry_mode == 'close' and kx <= ke):
        return {'status': 'missing'}
    r = sig_px / pc - 1.0
    if r == 0:
        return {'status': 'zero_signal'}
    dirn = 1 if r > 0 else -1
    entry = float(D.o[ke]) if entry_mode == 'open' else float(D.c[ke])
    gross = (float(D.c[kx]) - entry) * dirn
    net = gross - cost
    return {'status': 'trade', 'dir': dirn, 'r': r, 'gross_pts': gross, 'net_pts': net, 'bp': net / entry * 1e4}


def pairs(days: list) -> list:
    """(day, previous weekday) where both are eligible (prev not eligible -> signal undefined, I-4)."""
    s = set(days)
    return [(d, prev_weekday(d)) for d in days if prev_weekday(d) in s]


def boot(x) -> dict:
    v = np.asarray(x, float)
    if len(v) < 2:
        return {'theta': float(v.mean()) if len(v) else None, 'ci95': [None, None], 'p_one_sided': None, 'n': len(v)}
    reps = oc.bootstrap(lambda idx: float(v[idx].mean()), len(v), B=B_BOOT, seed=SEED)
    return oc.boot_summary(float(v.mean()), reps) | {'n': int(len(v))}


def frame(D, prs: list, **kw) -> tuple:
    rows, counts = [], {}
    for d, p in prs:
        t = trade(D, d, p, **kw)
        counts[t['status']] = counts.get(t['status'], 0) + 1
        if t['status'] == 'trade':
            rows.append({'day': d.isoformat(), 'year': d.year, **{k: t[k] for k in ('dir', 'r', 'gross_pts',
                                                                                   'net_pts', 'bp')}})
    return pd.DataFrame(rows), counts


def year_check(df: pd.DataFrame) -> dict:
    if df.empty:
        return {'years': {}, 'max_year_share': None, 'share_years_positive': None}
    by = df.groupby('year').bp.sum()
    tot = float(by.sum())
    return {'years': {int(k): float(x) for k, x in by.items()},
            'max_year_share': float(by.max() / tot) if tot > 0 else None,
            'share_years_positive': float((by > 0).mean())}


def sharpe(x) -> float:
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1)) if len(x) > 2 and x.std(ddof=1) > 0 else float('nan')


def analyse(D, prs: list, ev: set) -> dict:
    out = {'n_pairs': len(prs)}
    fr = {}
    for lvl, cst in COST.items():
        df, counts = frame(D, prs, cost=cst)
        fr[lvl] = df
        out[lvl] = {'counts': counts, 'mean_bp': boot(df.bp) if len(df) else None,
                    'mean_net_pts': float(df.net_pts.mean()) if len(df) else None,
                    'mean_gross_pts': float(df.gross_pts.mean()) if len(df) else None,
                    'hit_rate': float((df.net_pts > 0).mean()) if len(df) else None}
    s1 = fr['S1']
    fh, _ = frame(D, prs, cost=COST['S1'], signal='fh')
    sec = {'gao_fh': fh.bp.to_numpy(), 'long': s1[s1.dir == 1].bp.to_numpy(), 'short': s1[s1.dir == -1].bp.to_numpy()}
    sec |= {f'year_{y}': g.bp.to_numpy() for y, g in s1.groupby('year')}
    b = {k: boot(v) for k, v in sec.items()}
    adj = oc.bh([x.get('p_one_sided') for x in b.values()])
    out['secondaries_S1'] = {k: v | {'p_bh': a} for (k, v), a in zip(b.items(), adj)}
    out['year_check_S1'] = year_check(s1)
    obs = float(s1.bp.mean()) if len(s1) else float('nan')
    pl = {}
    for t in placebo_ends():
        df, _ = frame(D, prs, t_end=t, cost=COST['S1'])
        pl[t] = df.bp.to_numpy() if len(df) else np.array([])
    pm = {t: float(x.mean()) if len(x) else float('nan') for t, x in pl.items()}
    fin = [x for x in pm.values() if np.isfinite(x)]
    out['N1_placebo'] = {'observed': obs, 'n_placebos': len(pl),
                         'p_tod': float((1 + sum(x >= obs for x in fin)) / (1 + len(fin))) if fin else None,
                         'by_end': {f'{t // 60:02d}:{t % 60:02d}': {'mean_bp': pm[t], 'n': int(len(pl[t]))} for t in pl}}
    lo_, _ = frame(D, prs, cost=COST['S1'])
    out['N3_uncond_long_last30'] = {'mean_gross_pts': float((lo_.gross_pts * lo_.dir).mean()) if len(lo_) else None}
    try:
        sys.path.insert(0, '~/NEXA-Agent-Lab/filesnexa/NEXA/research')
        from nexa_robust import deflated_sharpe
        series = [s1.bp.to_numpy(), fh.bp.to_numpy(), sec['long'], sec['short']] + list(pl.values())
        srs = [x for x in (sharpe(s) for s in series) if np.isfinite(x)]
        var_sr = float(np.var(srs, ddof=1)) if len(srs) > 1 else float('nan')
        out['DSR'] = {'S1': float(deflated_sharpe(s1.bp.to_numpy(), N_TRIALS, var_sr)), 'n_trials': N_TRIALS,
                      'var_sr_own_series': var_sr}
    except Exception as e:  # noqa: BLE001
        out['DSR'] = {'error': repr(e)}
    rob = {}
    df, _ = frame(D, [(d, p) for d, p in prs if d not in ev], cost=COST['S1'])
    rob['excl_fomc_cpi_nfp'] = boot(df.bp) if len(df) else None
    if len(s1):
        med = float(s1.r.abs().median())
        strong = s1[s1.r.abs() > med]
        rob['strong_move_|r|>median'] = boot(strong.bp) | {'median_abs_r': med}
    df, _ = frame(D, prs, cost=COST['S1'], entry_mode='close')
    rob['entry_at_1530_close'] = boot(df.bp) if len(df) else None
    out['robustness_S1'] = rob
    return out


def acceptance(H: dict) -> dict:
    n = H['S1']['counts'].get('trade', 0)
    m1, m0 = H['S1']['mean_bp'] or {}, H['S0']['mean_bp'] or {}
    yc, sec = H['year_check_S1'], H['secondaries_S1']
    checks = {
        '1_mean>0_ci_lo>0': bool((m1.get('theta') or 0) > 0 and (m1.get('ci95') or [None])[0] is not None
                                 and m1['ci95'][0] > 0),
        '2_p_tod<=0.05': bool((H['N1_placebo'].get('p_tod') or 1) <= 0.05),
        '3a_no_year>40%': bool(yc.get('max_year_share') is not None and yc['max_year_share'] <= 0.40),
        '3b_years_positive>=60%': bool((yc.get('share_years_positive') or 0) >= 0.60),
        '3c_long_and_short>=0': bool(all((sec.get(k, {}).get('theta') or -1) >= 0 for k in ('long', 'short'))),
        '4_DSR>=0.95': bool((H.get('DSR', {}).get('S1') or 0) >= 0.95),
        '5_gross>=2x_S1_cost': bool((H['S1'].get('mean_gross_pts') or 0) >= 2 * COST['S1']),
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
    outp = os.path.join(HERE, 'him_results.json')
    if os.path.exists(outp):
        sys.exit('REFUSED: him_results.json exists (opened once)')
    D = hb.load(a.data)
    hol, lo, hi = hb.calendar()
    all_days = D.days()
    days, aud = hb.eligible_days(D, hol, None, None, lo, hi)
    days = [d for d in days if d < all_days[-1]]
    prs = pairs(days)
    H = {'data_path': a.data, 'day_audit': aud, 'first_day': prs[0][0].isoformat(),
         'last_day': prs[-1][0].isoformat()} | analyse(D, prs, hb.event_days())
    H['acceptance'] = acceptance(H)
    with open(outp, 'w') as f:
        json.dump(H, f, indent=1, default=str)
    print(json.dumps(H['acceptance'], indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
