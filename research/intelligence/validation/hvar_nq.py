#!/usr/bin/env python3
"""H-VAR-NQ: Dalton's Value-Area Rule on CME NQ (PREREG_HVAR_NQ.md, sha 687dbf38...).

Previous eligible RTH session's 70 % volume value area -> today opens outside it -> two consecutive 30-min periods
trade inside it (signal by 11:30) -> enter at the next 1-min open toward the opposite VA edge; stop = the session
extreme made so far; time exit at the 15:59 bar close. Null: the same rule on the value area of session d-k,
k = 2..20. Interpretations fixed before the run: DEVIATIONS_HORB30L_HVAR.md.

Usage:  python3 hvar_nq.py [--data <csv with volume>]      (one stage; results file is never overwritten)
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
import of_common as oc  # noqa: E402
import horb1_orb as hb  # noqa: E402
import hivb1_nq as iv  # noqa: E402  (read-only: DV loader, profile)
import horb30l_nq as orb  # noqa: E402  (read-only: trade engine, statistics helpers)

DATA = iv.DATA
TICK = orb.TICK
RTH0, RTH_LAST = 9 * 60 + 30, 15 * 60 + 59
PERIOD = 30
DEADLINE = 11 * 60 + 30          # signal (end of the 2nd inside period) by 11:30 (user constraint)
COST = orb.COST
N_TRIALS = orb.N_TRIALS
MIN_TRADES = 150
STALE_LAGS = list(range(2, 21))  # 19 placebos


# ----------------------------------------------------------------------------- previous-session value area
def session_stats(D, d):
    ks = [D.at(hb.utc_of(d, m)) for m in range(RTH0, RTH_LAST + 1)]
    if min(ks) < 0:
        return None
    prof = iv.profile(D.h[ks], D.l[ks], D.v[ks])
    if prof is None:
        return None
    val, vah, poc = prof
    return {'VAL': val, 'VAH': vah, 'POC': poc, 'width': vah - val, 'close': float(D.c[ks[-1]])}


def build_sessions(D, days: list) -> dict:
    return {d: session_stats(D, d) for d in days}


# ----------------------------------------------------------------------------- one day (§3)
def setup(D, days: list, i: int, sess: dict, *, lag: int = 1, deadline: int = DEADLINE, n_inside: int = 2) -> dict:
    d = days[i]
    if i - lag < 0:
        return {'status': 'no_prev'}
    va = sess.get(days[i - lag])
    if va is None:
        return {'status': 'missing'}
    k0, kx = D.at(hb.utc_of(d, RTH0)), D.at(hb.utc_of(d, RTH_LAST))
    if k0 < 0 or kx < 0:
        return {'status': 'missing'}
    op = float(D.o[k0])
    if va['VAL'] <= op <= va['VAH']:
        return {'status': 'inside_open'}
    dirn = 1 if op < va['VAL'] else -1
    run = 0
    p = 0
    while RTH0 + (p + 1) * PERIOD <= deadline:
        s = RTH0 + p * PERIOD
        ks = [k for k in (D.at(hb.utc_of(d, s + j)) for j in range(PERIOD)) if k >= 0]
        if not ks:
            return {'status': 'missing'}
        hi, lo = float(D.h[ks].max()), float(D.l[ks].min())
        inside = hi >= va['VAL'] + TICK and lo <= va['VAH'] - TICK
        run = run + 1 if inside else 0
        if run >= n_inside:
            sig = s + PERIOD
            kk = [k for k in (D.at(hb.utc_of(d, m)) for m in range(RTH0, sig)) if k >= 0]
            stop = float(D.l[kk].min()) if dirn == 1 else float(D.h[kk].max())
            return {'status': 'ok', 'dir': dirn, 'signal': sig, 'stop': stop, 'open': op, **va}
        p += 1
    return {'status': 'no_acceptance', 'dir': dirn, 'open': op, **va}


def simulate(D, days: list, i: int, sess: dict, *, lag: int = 1, deadline: int = DEADLINE, n_inside: int = 2,
             cost: float = COST['S1'], stop_mode: str = 'extreme', target_mode: str = 'edge') -> dict:
    S = setup(D, days, i, sess, lag=lag, deadline=deadline, n_inside=n_inside)
    if S['status'] != 'ok':
        return S
    dirn = S['dir']
    stop = S['stop'] if stop_mode == 'extreme' else (
        S['VAL'] - 0.25 * S['width'] if dirn == 1 else S['VAH'] + 0.25 * S['width'])
    target = (S['VAH'] if dirn == 1 else S['VAL']) if target_mode == 'edge' else S['POC']
    r = orb.run_trade(D, days[i], S['signal'], RTH_LAST, dirn, stop, target=target, cost=cost)
    return r | {'open': S['open'], 'VAL': S['VAL'], 'VAH': S['VAH'], 'width': S['width']}


# ----------------------------------------------------------------------------- Dalton conditions (no lookahead)
def dalton_conditions(D, days: list, sess: dict) -> dict:
    """Per day index i -> (cond1 distance, cond2 narrow value, cond3 direction); None if undefined (§6, I-n)."""
    dist = {}
    for i in range(1, len(days)):
        va = sess.get(days[i - 1])
        k0 = D.at(hb.utc_of(days[i], RTH0))
        if va is None or k0 < 0 or va['width'] <= 0:
            continue
        op = float(D.o[k0])
        if op < va['VAL'] or op > va['VAH']:
            dist[i] = min(abs(op - va['VAL']), abs(op - va['VAH'])) / va['width']
    out = {}
    for i in range(1, len(days)):
        prev = [dist[j] for j in range(max(0, i - 60), i) if j in dist]
        c1 = (dist[i] <= float(np.median(prev))) if (i in dist and len(prev) >= 10) else None
        w_prev = [sess[days[j]]['width'] for j in range(max(0, i - 21), i - 1) if sess.get(days[j])]
        va1 = sess.get(days[i - 1])
        c2 = (va1['width'] < float(np.median(w_prev))) if (va1 and len(w_prev) >= 10) else None
        c3 = None
        if i - 21 >= 0 and va1 and sess.get(days[i - 21]):
            c3 = float(np.sign(va1['close'] - sess[days[i - 21]]['close']))
        out[i] = (c1, c2, c3)
    return out


# ----------------------------------------------------------------------------- statistics
def frame(D, days: list, sess: dict, conds: dict | None = None, idx: list | None = None, **kw) -> tuple:
    rows, counts = [], {}
    for i in (range(len(days)) if idx is None else idx):
        r = simulate(D, days, i, sess, **kw)
        counts[r['status']] = counts.get(r['status'], 0) + 1
        if r['status'] == 'trade':
            d = days[i]
            c = (conds or {}).get(i, (None, None, None))
            rows.append({'day': d.isoformat(), 'year': d.year, 'month': d.strftime('%Y-%m'),
                         **{k: r[k] for k in ('dir', 'R_pts', 'pnl_pts', 'R', 'exit_kind')},
                         'c1': c[0], 'c2': c[1], 'c3_agree': (None if c[2] is None else bool(c[2] == r['dir']))})
    return pd.DataFrame(rows), counts


def analyse(D, days: list, ev: set) -> dict:
    sess = build_sessions(D, days)
    conds = dalton_conditions(D, days, sess)
    out = {'n_days': len(days), 'sessions_complete': int(sum(v is not None for v in sess.values()))}
    fr = {}
    for lvl, cst in COST.items():
        df, counts = frame(D, days, sess, conds, cost=cst)
        fr[lvl] = df
        out[lvl] = {'counts': counts, 'mean_R': orb.boot(df.R) if len(df) else None,
                    'mean_pts': float(df.pnl_pts.mean()) if len(df) else None,
                    'win_rate': float((df.R > 0).mean()) if len(df) else None,
                    'exits': df.exit_kind.value_counts().to_dict() if len(df) else {}}
    s1 = fr['S1']
    def pick(mask) -> np.ndarray:
        return s1[mask].R.to_numpy() if len(s1) else np.array([])

    has = len(s1) > 0
    sec = {'long': pick(s1.dir == 1) if has else np.array([]), 'short': pick(s1.dir == -1) if has else np.array([]),
           'dalton1_distance': pick(s1.c1.eq(True)) if has else np.array([]),
           'dalton2_narrow_value': pick(s1.c2.eq(True)) if has else np.array([]),
           'dalton3_direction': pick(s1.c3_agree.eq(True)) if has else np.array([])}
    dsr_keys = list(sec)                       # the 5 counted secondaries (§6 DSR family)
    sec |= {f'year_{y}': g.R.to_numpy() for y, g in s1.groupby('year')} if has else {}
    b = {k: orb.boot(v) for k, v in sec.items()}
    adj = oc.bh([x.get('p_one_sided') for x in b.values()])
    out['secondaries_S1'] = {k: v | {'p_bh': a} for (k, v), a in zip(b.items(), adj)}
    out['year_check_S1'] = orb.year_check(s1)
    out['cost_check'] = {'median_R_pts': float(s1.R_pts.median()) if len(s1) else None,
                         'ok': bool(len(s1) and s1.R_pts.median() >= 10 * COST['S1'])}
    out['N2_traverse_rate'] = {'share_target_exits': float((s1.exit_kind == 'target').mean()) if len(s1) else None,
                               'dalton_coin_flip': 0.5, 'popular_claim': 0.8}
    obs = float(s1.R.mean()) if len(s1) else float('nan')
    pl = {}
    for k in STALE_LAGS:
        df, _ = frame(D, days, sess, lag=k, cost=COST['S1'])
        pl[k] = df.R.to_numpy() if len(df) else np.array([])
    pm = {k: float(x.mean()) if len(x) else float('nan') for k, x in pl.items()}
    fin = [x for x in pm.values() if np.isfinite(x)]
    out['N1_stale_value'] = {'observed': obs, 'n_placebos': len(pl),
                             'p_stale': float((1 + sum(x >= obs for x in fin)) / (1 + len(fin))) if fin else None,
                             'by_lag': {f'd-{k}': {'mean_R': pm[k], 'n': int(len(pl[k]))} for k in pl}}
    out['DSR'] = orb.dsr(s1.R.to_numpy(), [s1.R.to_numpy()] + [sec[k] for k in dsr_keys] + list(pl.values()))
    rob = {}
    for name, kw in {'no_deadline': {'deadline': 15 * 60 + 30}, 'one_inside_period': {'n_inside': 1},
                     'stop_quarter_width': {'stop_mode': 'quarter'}, 'target_prev_POC': {'target_mode': 'poc'}}.items():
        df, _ = frame(D, days, sess, cost=COST['S1'], **kw)
        rob[name] = orb.boot(df.R) if len(df) else None
    df, _ = frame(D, days, sess, idx=[i for i, d in enumerate(days) if d not in ev], cost=COST['S1'])
    rob['excl_fomc_cpi_nfp'] = orb.boot(df.R) if len(df) else None
    out['robustness_S1'] = rob
    out['user_goal_S1'] = orb.user_goal(s1, len(days))
    return out


def acceptance(H: dict) -> dict:
    n = H['S1']['counts'].get('trade', 0)
    m1, m0 = H['S1']['mean_R'] or {}, H['S0']['mean_R'] or {}
    yc, sec = H.get('year_check_S1', {}), H.get('secondaries_S1', {})
    checks = {
        '1_mean>0_ci_lo>0': bool((m1.get('theta') or 0) > 0 and (m1.get('ci95') or [None])[0] is not None
                                 and m1['ci95'][0] > 0),
        '2_p_stale<=0.05': bool((H['N1_stale_value'].get('p_stale') or 1) <= 0.05),
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
    outp = os.path.join(HERE, 'hvar_results.json')
    if os.path.exists(outp):
        sys.exit('REFUSED: hvar_results.json exists (opened once)')
    D = iv.load(a.data)
    days, aud = orb.eligible(D)
    H = {'data_path': a.data, 'data_audit': D.audit, 'day_audit': aud, 'first_day': days[0].isoformat(),
         'last_day': days[-1].isoformat()} | analyse(D, days, hb.event_days())
    H['acceptance'] = acceptance(H)
    with open(outp, 'w') as f:
        json.dump(H, f, indent=1, default=str)
    print(json.dumps(H['acceptance'], indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
