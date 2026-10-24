#!/usr/bin/env python3
"""H-ORB30L-NQ: 30-minute opening-range breakout, long only, on CME NQ (PREREG_HORB30L_NQ.md, sha 75fd92dd...).

Range 09:30-09:59 -> first 5-min candle closing above the range high by 11:30 -> long at the next 1-min open,
stop = range low, target 1R (2R secondary), time exit at the 15:29 bar close. N2 = the same bracket entered at the
10:00 open on every day (beta control). Interpretations fixed before the run: DEVIATIONS_HORB30L_HVAR.md.

Usage:  python3 horb30l_nq.py [--data <csv with volume>]      (one stage; results file is never overwritten)
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import of_common as oc  # noqa: E402  (read-only: bootstrap, boot_summary, bh)
import horb1_orb as hb  # noqa: E402  (read-only: clock, calendar, eligible days, event days)
import hivb1_nq as iv  # noqa: E402  (read-only: DV loader with volume)

DATA = iv.DATA
TICK = 0.25
RANGE_START = 9 * 60 + 30
RANGE_LEN = 30
DEADLINE = 11 * 60 + 30          # breakout candle must close by 11:30 (user constraint)
EXIT_MIN = 15 * 60 + 29          # time exit = close of the 15:29 bar
COST = {'S0': 1.0, 'S1': 2.0, 'S2': 3.0}
MIN_R = 10.0
SEED = 20261014
B_BOOT = 2000
N_TRIALS = 116
MIN_TRADES = 200
MNQ_USD_PER_POINT = 2.0
RISK_USD = 100.0


def placebo_anchors() -> list:
    """§5 N1: every 30 min 02:30-08:00 and 11:00-14:00 ET -> 19 anchors."""
    return list(range(2 * 60 + 30, 8 * 60 + 1, 30)) + list(range(11 * 60, 14 * 60 + 1, 30))


def placebo_deadline(t0: int) -> int:
    return min(t0 + 120, 15 * 60)


# ----------------------------------------------------------------------------- shared trade engine
def run_trade(D, d, entry_min: int, exit_min: int, dirn: int, stop: float, *, target: float | None = None,
              target_r: float = 1.0, cost: float = COST['S1']) -> dict:
    """Enter at the open of the first existing 1-min bar >= entry_min; stop touch / gap at open; target needs a
    1-tick trade-through; same bar -> stop; entry bar checks the stop only; time exit at the exit_min bar close."""
    em, ke = None, -1
    for m in range(entry_min, exit_min):
        ke = D.at(hb.utc_of(d, m))
        if ke >= 0:
            em = m
            break
    if em is None:
        return {'status': 'no_entry_bar'}
    entry = float(D.o[ke])
    R = (entry - stop) * dirn
    if R <= 0:
        return {'status': 'invalid', 'R': R}
    if R < MIN_R:
        return {'status': 'cost_floor', 'R': R}
    tgt = entry + dirn * target_r * R if target is None else target
    if (tgt - entry) * dirn <= 0:
        return {'status': 'target_passed'}
    exit_px = how = None
    for m in range(em, exit_min + 1):
        k = D.at(hb.utc_of(d, m))
        if k < 0:
            continue
        o_, h_, l_, c_ = float(D.o[k]), float(D.h[k]), float(D.l[k]), float(D.c[k])
        first = m == em
        if (l_ <= stop) if dirn == 1 else (h_ >= stop):
            gap = (not first) and ((o_ <= stop) if dirn == 1 else (o_ >= stop))
            exit_px, how = (o_ if gap else stop), 'stop'
        elif (not first) and ((h_ >= tgt + TICK) if dirn == 1 else (l_ <= tgt - TICK)):
            exit_px, how = tgt, 'target'
        elif m == exit_min:
            exit_px, how = c_, 'time'
        if exit_px is not None:
            break
    if exit_px is None:
        return {'status': 'missing'}
    pnl = (exit_px - entry) * dirn - cost
    return {'status': 'trade', 'dir': dirn, 'entry': entry, 'exit': exit_px, 'R_pts': R, 'pnl_pts': pnl,
            'R': pnl / R, 'exit_kind': how, 'entry_min': em}


# ----------------------------------------------------------------------------- the rule (§3)
def setup(D, d, t0: int = RANGE_START, *, deadline: int = DEADLINE, tf: int = 5, side: int = 1) -> dict:
    ks = [D.at(hb.utc_of(d, t0 + j)) for j in range(RANGE_LEN)]
    if min(ks) < 0:
        return {'status': 'missing'}
    A, B = float(D.h[ks].max()), float(D.l[ks].min())
    m = t0 + RANGE_LEN
    while m + tf <= deadline:
        kc = D.at(hb.utc_of(d, m + tf - 1))
        if kc >= 0:
            cl = float(D.c[kc])
            if (cl > A) if side == 1 else (cl < B):
                return {'status': 'ok', 'A': A, 'B': B, 'entry_min': m + tf}
        m += tf
    return {'status': 'no_breakout', 'A': A, 'B': B}


def simulate(D, d, t0: int = RANGE_START, *, deadline: int | None = None, tf: int = 5, target_r: float = 1.0,
             exit_min: int = EXIT_MIN, cost: float = COST['S1'], side: int = 1, n2: bool = False) -> dict:
    if D.at(hb.utc_of(d, exit_min)) < 0:
        return {'status': 'missing'}
    deadline = (DEADLINE if t0 == RANGE_START else placebo_deadline(t0)) if deadline is None else deadline
    S = setup(D, d, t0, deadline=deadline, tf=tf, side=side)
    if S['status'] == 'missing':
        return S
    if n2:                                   # beta control: same bracket at the 10:00 open, no condition
        return run_trade(D, d, t0 + RANGE_LEN, exit_min, 1, S['B'], target_r=target_r, cost=cost)
    if S['status'] != 'ok':
        return S
    stop = S['B'] if side == 1 else S['A']
    return run_trade(D, d, S['entry_min'], exit_min, side, stop, target_r=target_r, cost=cost)


# ----------------------------------------------------------------------------- statistics
def boot(x) -> dict:
    v = np.asarray(x, float)
    if len(v) < 2:
        return {'theta': float(v.mean()) if len(v) else None, 'ci95': [None, None], 'p_one_sided': None, 'n': len(v)}
    reps = oc.bootstrap(lambda idx: float(v[idx].mean()), len(v), B=B_BOOT, seed=SEED)
    return oc.boot_summary(float(v.mean()), reps) | {'n': int(len(v))}


def frame(D, days: list, fn=None, **kw) -> tuple:
    fn = fn or simulate
    rows, counts = [], {}
    for d in days:
        r = fn(D, d, **kw)
        counts[r['status']] = counts.get(r['status'], 0) + 1
        if r['status'] == 'trade':
            rows.append({'day': d.isoformat(), 'year': d.year, 'month': d.strftime('%Y-%m'),
                         **{k: r[k] for k in ('dir', 'R_pts', 'pnl_pts', 'R', 'exit_kind')}})
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


def dsr(primary, series: list) -> dict:
    try:
        sys.path.insert(0, '~/NEXA-Agent-Lab/filesnexa/NEXA/research')
        from nexa_robust import deflated_sharpe
        srs = [x for x in (sharpe(s) for s in series) if np.isfinite(x)]
        var_sr = float(np.var(srs, ddof=1)) if len(srs) > 1 else float('nan')
        return {'S1': float(deflated_sharpe(np.asarray(primary, float), N_TRIALS, var_sr)), 'n_trials': N_TRIALS,
                'var_sr_own_series': var_sr, 'n_series': len(series)}
    except Exception as e:  # noqa: BLE001
        return {'error': repr(e)}


def user_goal(df: pd.DataFrame, n_days: int) -> dict:
    """Descriptive only (§8): winning days / months, losing streak, $ per MNQ at a fixed $100 risk."""
    if df.empty:
        return {}
    win = df.pnl_pts > 0
    streak = best = 0
    for w in win:
        streak = 0 if w else streak + 1
        best = max(best, streak)
    contracts = np.maximum(1, np.floor(RISK_USD / (df.R_pts * MNQ_USD_PER_POINT)))
    usd = contracts * df.pnl_pts * MNQ_USD_PER_POINT
    risk = contracts * df.R_pts * MNQ_USD_PER_POINT
    by_m = pd.Series(usd.values, index=df.month).groupby(level=0).sum()
    return {'trade_days': int(len(df)), 'eligible_days': n_days, 'share_trade_days_won': float(win.mean()),
            'share_months_positive': float((by_m > 0).mean()), 'n_months': int(len(by_m)),
            'longest_losing_streak_trades': int(best), 'usd_per_trade_mean': float(usd.mean()),
            'usd_per_month_mean': float(by_m.mean()), 'usd_per_month_median': float(by_m.median()),
            'usd_worst_month': float(by_m.min()), 'usd_best_month': float(by_m.max()),
            'actual_risk_usd_median': float(np.median(risk)), 'share_trades_risk_above_100': float((risk > RISK_USD).mean())}


def analyse(D, days: list, ev: set) -> dict:
    out = {'n_days': len(days)}
    fr = {}
    for lvl, cst in COST.items():
        df, counts = frame(D, days, cost=cst)
        fr[lvl] = df
        out[lvl] = {'counts': counts, 'mean_R': boot(df.R) if len(df) else None,
                    'mean_pts': float(df.pnl_pts.mean()) if len(df) else None,
                    'win_rate': float((df.R > 0).mean()) if len(df) else None,
                    'exits': df.exit_kind.value_counts().to_dict() if len(df) else {}}
    s1 = fr['S1']
    r2, _ = frame(D, days, cost=COST['S1'], target_r=2.0)
    sec = {'target_2R': r2.R.to_numpy()} | {f'year_{y}': g.R.to_numpy() for y, g in s1.groupby('year')}
    b = {k: boot(v) for k, v in sec.items()}
    adj = oc.bh([x.get('p_one_sided') for x in b.values()])
    out['secondaries_S1'] = {k: v | {'p_bh': a} for (k, v), a in zip(b.items(), adj)}
    out['year_check_S1'] = year_check(s1)
    out['cost_check'] = {'median_R_pts': float(s1.R_pts.median()) if len(s1) else None,
                         'ok': bool(len(s1) and s1.R_pts.median() >= 10 * COST['S1'])}
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
    n2, n2c = frame(D, days, cost=COST['S1'], n2=True)
    out['N2_beta_control'] = (boot(n2.R) if len(n2) else {}) | {'counts': n2c,
                             'primary_minus_N2': (obs - float(n2.R.mean())) if len(n2) and len(s1) else None}
    n3 = []
    for d in days:
        ke, kx = D.at(hb.utc_of(d, RANGE_START + RANGE_LEN)), D.at(hb.utc_of(d, EXIT_MIN))
        if ke >= 0 and kx >= 0:
            n3.append(float(D.c[kx]) - float(D.o[ke]))
    out['N3_buy_hold_1000_1530_pts'] = {'mean': float(np.mean(n3)) if n3 else None, 'n': len(n3)}
    out['DSR'] = dsr(s1.R.to_numpy(), [s1.R.to_numpy(), r2.R.to_numpy()] + list(pl.values()) + [n2.R.to_numpy()])
    rob = {}
    for name, kw in {'no_deadline': {'deadline': 15 * 60 + 25}, 'breakout_1min_close': {'tf': 1},
                     'exit_1559': {'exit_min': 15 * 60 + 59}, 'short_mirror': {'side': -1}}.items():
        df, _ = frame(D, days, cost=COST['S1'], **kw)
        rob[name] = boot(df.R) if len(df) else None
    df, _ = frame(D, [d for d in days if d not in ev], cost=COST['S1'])
    rob['excl_fomc_cpi_nfp'] = boot(df.R) if len(df) else None
    out['robustness_S1'] = rob
    out['user_goal_S1'] = user_goal(s1, len(days))
    return out


def acceptance(H: dict) -> dict:
    n = H['S1']['counts'].get('trade', 0)
    m1, m0 = H['S1']['mean_R'] or {}, H['S0']['mean_R'] or {}
    yc = H.get('year_check_S1', {})
    diff = H.get('N2_beta_control', {}).get('primary_minus_N2')
    checks = {
        '1_mean>0_ci_lo>0': bool((m1.get('theta') or 0) > 0 and (m1.get('ci95') or [None])[0] is not None
                                 and m1['ci95'][0] > 0),
        '2_p_tod<=0.05': bool((H['N1_placebo'].get('p_tod') or 1) <= 0.05),
        '3a_no_year>40%': bool(yc.get('max_year_share') is not None and yc['max_year_share'] <= 0.40),
        '3b_years_positive>=60%': bool((yc.get('share_years_positive') or 0) >= 0.60),
        '4_DSR>=0.95': bool((H.get('DSR', {}).get('S1') or 0) >= 0.95),
        '5_median_R>=20pts': bool(H.get('cost_check', {}).get('ok', False)),
        '6_primary_minus_N2>0': bool(diff is not None and diff > 0),
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


def eligible(D) -> tuple:
    hol, lo, hi = hb.calendar()
    all_days = D.days()
    days, aud = hb.eligible_days(D, hol, None, None, lo, hi)
    return [d for d in days if d < all_days[-1]], aud


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default=DATA)
    a = ap.parse_args()
    outp = os.path.join(HERE, 'horb30l_results.json')
    if os.path.exists(outp):
        sys.exit('REFUSED: horb30l_results.json exists (opened once)')
    D = iv.load(a.data)
    days, aud = eligible(D)
    H = {'data_path': a.data, 'data_audit': D.audit, 'day_audit': aud, 'first_day': days[0].isoformat(),
         'last_day': days[-1].isoformat()} | analyse(D, days, hb.event_days())
    H['acceptance'] = acceptance(H)
    with open(outp, 'w') as f:
        json.dump(H, f, indent=1, default=str)
    print(json.dumps(H['acceptance'], indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
