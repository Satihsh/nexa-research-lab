#!/usr/bin/env python3
"""OFC1R: final replication of frozen OFC1 rules on 6E 2023-2025 (PREREG_OFC1R_REPLICATION.md). Thin wrapper.

Imports ofc1_core unchanged; overrides only splits, data file, degraded-date file and instrument list.
DSR is computed afterwards with the NEXA research venv (D11): ofc1r_dsr.py-equivalent inline step in the report.
Usage: python ofc1r_run.py
"""
import json
import os
import sys
from datetime import datetime

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ofc1_core as of  # noqa: E402  (frozen, read-only)

FILE = os.path.join(of.DBDIR, 'data', 'GLBX.MDP3_trades_6E.v.0_2022-10-01_2025-09-01.dbn.zst')
COND = os.path.join(of.DBDIR, 'dataset_condition_2022-10_2025-08.json')
of.SPLITS = [('replication', '2023-01-01', '2025-08-31')]
END = '2025-08-31'


def degraded_touch():
    with open(COND) as f:
        deg = {d for d, _ in json.load(f)}
    out = set(deg)
    for d in deg:
        out.add(datetime.fromordinal(datetime.strptime(d, '%Y-%m-%d').toordinal() + 1).strftime('%Y-%m-%d'))
    return out


of.degraded_touch = degraded_touch


def main():
    C = of.prepare('6E', of.load('6E', [FILE]))
    trs, sk, plac, cnt = of.run_pass(C, END, of.Params(), True)
    n2, sk2, _, _ = of.run_pass(C, END, of.Params(confirm=False), False)
    rob = {}
    for name, prm in {'cost_floor_off': of.Params(cost_floor=False), 'imbalance_nt_form': of.Params(nt_form=True),
                      'e2_5pct': of.Params(e2=0.05), 'e2_20pct': of.Params(e2=0.20), 'first_bubble': of.Params(first_bubble=True),
                      'stack_ge2': of.Params(min_stack=2), 'exits_on_close': of.Params(exit_on_close=True)}.items():
        rob[name] = of.boot_mean(of.run_pass(C, END, prm, False)[0])
    all_days = sorted({t['day'] for t in trs} | {t['day'] for t in n2})
    P = of.boot_mean(trs, 'R0')
    S1 = of.boot_mean(trs, 'R1')
    pl = of.placebo_p(trs, plac) if trs else {'p': None}
    dl = of.boot_delta(trs, n2, all_days) if trs and n2 else {'delta': None}
    years = sorted({t['day'][:4] for t in trs})
    by_year = {y: of.boot_mean([t for t in trs if t['day'][:4] == y]) for y in years}
    tot = sum(t['R0'] for t in trs)
    year_share = {y: (sum(t['R0'] for t in trs if t['day'][:4] == y) / tot if tot else None) for y in years}
    crit = {
        '1_mean>0_p<0.05': bool(P['mean'] is not None and P['mean'] > 0 and P['p_one_sided'] < 0.05),
        '2_S1_mean>0': bool((S1['mean'] or -1) > 0),
        '3_placebo_p<=0.05': bool((pl.get('p') or 1) <= 0.05),
        '4_N2_delta>0': bool((dl.get('delta') or -1) > 0),
        '5_years': bool(sum(1 for y in years if (by_year[y]['mean'] or -1) > 0) >= 2 and tot > 0
                        and all((v or 0) <= 0.5 for v in year_share.values())),
        '6_DSR>=0.95': None,   # computed afterwards (D11)
    }
    if P['mean'] is None or P['mean'] <= 0:
        verdict = 'REJECTED'
    elif P['n'] < 150:
        verdict = 'INSUFFICIENT-N'
    elif all(v for k, v in crit.items() if k != '6_DSR>=0.95'):
        verdict = 'REPLICATED pending DSR'
    else:
        verdict = 'INCONCLUSIVE'
    out = {'prereg': 'PREREG_OFC1R_REPLICATION.md', 'counts': cnt, 'skips': sk, 'n2_skips': sk2,
           'P1': P, 'P1_S1': S1, 'by_setup': {s: of.boot_mean([t for t in trs if t['setup'] == s]) for s in of.SETUPS},
           'by_year': by_year, 'year_share': year_share,
           'by_block': {b: of.boot_mean([t for t in trs if t['blk'] == i]) for i, b in enumerate(('Asia', 'London', 'NY'))},
           'N1_placebo': pl, 'N2_no_confirmation': of.boot_mean(n2), 'N2_delta': dl, 'robustness': rob,
           'criteria': crit, 'verdict': verdict, 'trades': trs,
           'sr_inputs_for_DSR': {'P1': [P['mean'], P['sd_R']], 'N2': [of.boot_mean(n2)['mean'], of.boot_mean(n2)['sd_R']]}}
    with open(os.path.join(HERE, 'ofc1r_results.json'), 'w') as f:
        json.dump(out, f, indent=1, default=lambda x: float(x) if isinstance(x, np.floating) else int(x) if isinstance(x, np.integer) else str(x))
    print(json.dumps({k: out[k] for k in ('counts', 'P1', 'P1_S1', 'by_year', 'N1_placebo', 'N2_delta', 'criteria', 'verdict')},
                     indent=1, default=str))


if __name__ == '__main__':
    main()
