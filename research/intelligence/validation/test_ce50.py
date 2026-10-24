"""Synthetic G1 tests for qc_ce50/main.py (PREREG_CE50.md s.7). No market data."""
import importlib.util
import json
import os
import sys
import types
from datetime import date, timedelta

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
stub = types.ModuleType('AlgorithmImports')
stub.QCAlgorithm = object
sys.modules.setdefault('AlgorithmImports', stub)
spec = importlib.util.spec_from_file_location('qc_ce50_main', os.path.join(HERE, 'qc_ce50', 'main.py'))
ce = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ce)


def day(p=100.0):
    """450 flat bars at p; range bar 0 makes H = p+10, L = p-10, midline p."""
    o, h, l, c = (np.full(ce.NB, p) for _ in range(4))
    h[0], l[0] = p + 10, p - 10
    return o, h, l, c


def k15(j, i=0):
    """1-minute index of minute i inside 15-minute block j."""
    return ce.K_OPEN + ce.BLK * j + i


def test_range_midline_and_signal():
    o, h, l, c = day()
    h[59], l[30] = 112.0, 95.0
    h[60] = 500.0                                 # 09:30 bar is not in the range
    assert ce.rng_mid(h, l) == (112.0, 90.0, 101.0)   # bar 0 still holds the low 90
    c[ce.K_SIG] = 100.5
    assert ce.signal(h, l, c) == -1
    c[ce.K_SIG] = 101.5
    assert ce.signal(h, l, c) == 1
    c[ce.K_SIG] = 101.0
    assert ce.signal(h, l, c) == 0


def test_entry_open_initial_stop_and_time_exit():
    o, h, l, c = day()
    o[ce.K_ENTRY] = 99.0
    c[ce.K_LAST] = 95.0
    t = ce.trade(o, h, l, c, -1)
    assert t['R_pts'] == 110.25 - 99.0 and t['kind'] == 'time' and t['gross'] == 4.0


def test_r_floor_and_beyond():
    o, h, l, c = day()
    o[ce.K_ENTRY] = 110.0                         # short 0.25 below the stop -> 1 tick < 4 ticks
    assert ce.trade(o, h, l, c, -1) == 'r_floor'
    o[ce.K_ENTRY] = 111.0                         # already beyond the short stop
    assert ce.trade(o, h, l, c, -1) == 'beyond'


def test_stop_and_gap_fill():
    o, h, l, c = day()
    h[100] = 110.25
    t = ce.trade(o, h, l, c, -1)
    assert t['kind'] == 'stop' and t['gross'] == -10.25
    o, h, l, c = day()
    o[100], h[100] = 115.0, 116.0                 # gaps through the stop: fill at the open
    t = ce.trade(o, h, l, c, -1)
    assert t['gross'] == -15.0


def test_swing_trailing_timing_and_tighten_only():
    o, h, l, c = day()
    # 15-min block highs: block 1 = 105 is a swing high (blocks 0 and 2 lower) -> applies from block 3
    h[k15(1, 5)] = 105.0
    h[k15(2, 0) + 3] = 101.0
    h[k15(3, 0)] = 105.1                          # first bar of block 3: above the new stop 105.25? no -> safe
    h[k15(3, 1)] = 105.25                         # touches the trailed stop (105 + 1 tick)
    t = ce.trade(o, h, l, c, -1)
    assert t['kind'] == 'stop' and t['gross'] == 100.0 - 105.25 and t['trail'] == 1


def test_swing_not_used_before_confirmation():
    o, h, l, c = day()
    h[k15(1, 5)] = 105.0
    h[k15(2, 7)] = 105.25                         # inside block 2: swing at block 1 not yet confirmed
    t = ce.trade(o, h, l, c, -1)
    # not stopped at 105.25 inside block 2 (block 1's swing is unconfirmed and in fact never forms);
    # block 2 itself becomes the swing (105.25 > 105 and > block 3) and trails the stop to 105.5 from block 4
    assert t['kind'] == 'time' and t['trail'] == 1


def test_trailing_never_loosens():
    o, h, l, c = day()
    h[k15(1, 5)] = 108.0                          # swing at 108 -> stop 108.25
    h[k15(5, 5)] = 109.0                          # later swing higher than the current stop: ignored
    t = ce.trade(o, h, l, c, -1)
    assert t['trail'] == 1


def test_long_mirror():
    o, h, l, c = day()
    c[ce.K_SIG] = 101.0
    assert ce.signal(h, l, c) == 1
    l[k15(1, 5)] = 95.0
    l[k15(3, 2)] = 94.75
    t = ce.trade(o, h, l, c, 1)
    assert t['kind'] == 'stop' and t['gross'] == 94.75 - 100.0 and t['R_pts'] == 10.25


def synth_days(n, rng, drift, start=date(2012, 1, 2)):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            o, h, l, c = day()
            up = rng.random() < 0.5
            c[ce.K_SIG] = 101.0 if up else 99.0
            sgn = 1 if up else -1
            path = 100.0 + np.cumsum(rng.normal(drift * sgn, 0.4, ce.NB - ce.K_ENTRY))
            o[ce.K_ENTRY:] = np.concatenate([[100.0], path[:-1]])
            c[ce.K_ENTRY:] = path
            h[ce.K_ENTRY:] = np.maximum(o[ce.K_ENTRY:], c[ce.K_ENTRY:]) + 0.1
            l[ce.K_ENTRY:] = np.minimum(o[ce.K_ENTRY:], c[ce.K_ENTRY:]) - 0.1
            out.append({'date': d, 'o': o, 'h': h, 'l': l, 'c': c})
        d += timedelta(days=1)
    return out


def test_end_to_end_planted_and_noise():
    res = ce.run_all(synth_days(1200, np.random.default_rng(1), 0.03), 'NQ')
    assert res['P']['trades'] > 300 and res['IN']['trades'] > 0
    assert res['P']['S1']['mean'] > 0.025 and res['P']['S1']['ci'][0] > 0
    assert res['control']['real_pct'] >= 0.95 and res['verdict'] == 'VALIDATED', json.dumps(res)[:400]
    res = ce.run_all(synth_days(1200, np.random.default_rng(2), 0.0), 'NQ')
    assert res['verdict'] != 'VALIDATED'


def test_split_p_in():
    days = synth_days(1200, np.random.default_rng(3), 0.0, start=date(2014, 6, 2))
    res = ce.run_all(days, 'ES')
    assert res['P']['days'] + res['IN']['days'] == res['FULL']['days'] and res['P']['days'] > 0 and res['IN']['days'] > 0


def test_verdict_rules():
    p = {'trades': 400, 'S1': {'mean': 0.05, 'ci': [0.01, 0.1], 'p': 0.01}, 'blocks_pos': 4}
    inn = {'S1': {'mean': 0.03}}
    assert ce.verdict(p, inn, 0.99) == 'VALIDATED'
    assert ce.verdict(dict(p, S1=dict(p['S1'], p=0.03)), inn, 0.99) == 'INCONCLUSIVE'   # > 0.05/2
    assert ce.verdict(p, {'S1': {'mean': -0.1}}, 0.99) == 'INCONCLUSIVE'
    assert ce.verdict(p, inn, 0.9) == 'INCONCLUSIVE'
    assert ce.verdict(dict(p, S1=dict(p['S1'], mean=0.0)), inn, 0.99) == 'REJECTED'
    assert ce.verdict(dict(p, trades=299), inn, 0.99) == 'INSUFFICIENT-N'


def test_log_budget():
    res = ce.run_all(synth_days(4200, np.random.default_rng(4), 0.0, start=date(2010, 1, 4)), 'NQ')
    res['skipped_days'] = {'incomplete': 999, 'roll': 99}
    assert len(json.dumps(res, separators=(',', ':'))) < 9000
