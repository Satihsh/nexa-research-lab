#!/usr/bin/env python3
"""Joint BH across the 15 primary tests of OF-16/19/20 (+ OF-19-T), PREREG_OF_COMMON.md §C8. Reads the full-run JSONs."""
import json, os
import of_common as oc

a = json.load(open(os.path.join(oc.HERE, 'of16_results.json')))
b = json.load(open(os.path.join(oc.HERE, 'of19_results.json')))
c = json.load(open(os.path.join(oc.HERE, 'of20_results.json')))
tests = []
for s in ('XAUUSD', 'EURUSD', 'USDJPY'):
    R = a['symbols'][s]; tests.append((f'OF-16 {s}', R['cells'][R['primary_cell']]['per_split']['discovery']['p_one_sided']))
for s in oc.SYMBOLS:
    R = b['symbols'][s]
    for nm in ('theta19a', 'theta19b'):
        tests.append((f'OF-19 {nm} {s}', R['cells'][R['primary_cell']][nm]['per_split']['discovery']['p_one_sided']))
for s in oc.SYMBOLS:
    R = c['symbols'][s]; cc = R['cells'][R['primary_cell']]
    tests.append((f'OF-20 {s} (n_TD={cc["n_cond"]})', cc['per_split'].get('discovery', {}).get('p_one_sided')))
tests.append(('OF-19-T pooled (holdout, stress 0.05)', b['trade_OF19T']['holdout']['stress_0.05']['p_one_sided']))
adj = oc.bh([p for _, p in tests])
out = [{'test': t, 'disc_p_or_holdout_p': p, 'joint_BH': q} for (t, p), q in zip(tests, adj)]
json.dump({'note': 'discovery one-sided p for the 15 primary tests; OF-19-T uses its holdout p. OF-20 p-values with n_TD < 100 are degenerate (bootstrap of 0-2 events) and are gated by the n>=100 rule.',
           'tests': out, 'n_joint_BH_below_0.10': sum(1 for x in out if x['joint_BH'] is not None and x['joint_BH'] < 0.10)},
          open(os.path.join(oc.HERE, 'of_joint_bh.json'), 'w'), indent=1)
for x in out: print(x)
