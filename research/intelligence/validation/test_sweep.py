"""Synthetic G1 tests for qc_sweep/main.py (PREREG_SWEEP.md s.9). No market data is read."""
from __future__ import annotations

import importlib.util
import os
import sys
import types
from datetime import date, timedelta

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
stub = types.ModuleType('AlgorithmImports')
stub.QCAlgorithm = object
sys.modules.setdefault('AlgorithmImports', stub)
spec = importlib.util.spec_from_file_location('qc_sweep_main', os.path.join(HERE, 'qc_sweep', 'main.py'))
sw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sw)


def flat(price=100.0, w=0.25):
    n = 390
    return [np.full(n, price), np.full(n, price + w), np.full(n, price - w), np.full(n, price)]


def setb(arr, k, o, h, l, c):
    arr[0][k], arr[1][k], arr[2][k], arr[3][k] = o, h, l, c


# 1. levels, gap rule and first-sweep window
def test_first_sweep_and_gap():
    o, h, l, c = flat()
    h[50] = 101.5                                     # level 101 + 2 ticks = 101.5 -> sweep at 50
    assert sw.first_sweep(h, l, o[0], 101.0, 1) == 50
    h[50] = 101.25                                    # only 1 tick beyond -> no sweep
    assert sw.first_sweep(h, l, o[0], 101.0, 1) is None
    h[0] = 105.0                                      # bar 0 is never a signal bar
    assert sw.first_sweep(h, l, o[0], 101.0, 1) is None
    h[340] = 110.0                                    # after 14:59 -> outside window
    assert sw.first_sweep(h, l, o[0], 101.0, 1) is None
    assert sw.first_sweep(h, l, 101.0, 101.0, 1) is None   # gapped at/above the level
    l[20] = 98.5
    assert sw.first_sweep(h, l, o[0], 99.0, -1) == 20


# 2. Arm A bracket, next-bar entry, stop-first tie
def test_arm_a_bracket_and_tie():
    d = flat()
    setb(d, 30, 100, 101.6, 99.9, 101.2)              # sweep of 101 at bar 30
    setb(d, 31, 101.2, 101.3, 101.0, 101.2)           # entry at o[31] = 101.2
    setb(d, 32, 101.2, 103.3, 99.0, 102.0)            # touches both stop (99.2) and target (103.2) -> stop
    tr, so, sr = sw.sweep_day(*d, {1: 101.0, -1: None}, 2.0, 'A')
    assert len(tr) == 1 and tr[0]['k'] == 31 and tr[0]['dir'] == 1
    assert tr[0]['kind'] == 'stop' and abs(tr[0]['exit'] - 99.2) < 1e-9 and tr[0]['R_pts'] == 2.0


# 3. Arm B reclaim window, stop and R floor
def test_arm_b_reclaim_and_floor():
    d = flat()
    setb(d, 40, 100, 101.75, 100, 101.5)              # sweep at 40, close still above 101
    for k in range(41, 45):
        setb(d, k, 101.4, 101.5, 101.2, 101.3)        # stays above 101
    setb(d, 45, 101.5, 101.6, 100.5, 100.8)           # closes back below 101 at bar 45 (within 15)
    setb(d, 46, 100.8, 100.9, 100.7, 100.8)           # entry o[46] = 100.8; stop = 101.75 + 0.25 = 102.0; R = 1.2
    tr, so, sr = sw.sweep_day(*d, {1: 101.0, -1: None}, 2.0, 'B')
    assert len(tr) == 1 and tr[0]['dir'] == -1 and tr[0]['k'] == 46
    assert abs(tr[0]['R_pts'] - 1.2) < 1e-9
    d2 = flat()
    setb(d2, 40, 100, 101.75, 100, 101.5)
    for k in range(41, 56):
        setb(d2, k, 101.4, 101.5, 101.2, 101.3)
    setb(d2, 56, 101.5, 101.6, 100.5, 100.8)          # reclaim after 16 bars -> outside window
    tr2, _, _ = sw.sweep_day(*d2, {1: 101.0, -1: None}, 2.0, 'B')
    assert tr2 == []
    d3 = flat()
    setb(d3, 40, 100, 101.5, 100, 100.9)              # sweep and same-bar reclaim; stop 101.75
    setb(d3, 41, 101.2, 101.3, 101.0, 101.2)          # entry 101.2 -> R = 0.55 < 1.0 -> skipped
    tr3, _, sr3 = sw.sweep_day(*d3, {1: 101.0, -1: None}, 2.0, 'B')
    assert tr3 == [] and sr3 == 1


# 4. one position at a time
def test_one_position():
    d = flat()
    setb(d, 30, 100, 101.6, 99.9, 101.2)              # high-side sweep at 30 -> long from 31, never exits -> time
    setb(d, 60, 100, 100.1, 98.4, 99.0)               # low-side sweep at 60 while long is open -> skipped
    tr, so, _ = sw.sweep_day(*d, {1: 101.0, -1: 99.0}, 5.0, 'A')
    assert len(tr) == 1 and so == 1 and tr[0]['kind'] == 'time'


# 5. placebo levels: distance-matched, excluded band, skipped side
def test_placebo_levels():
    rng = np.random.default_rng(1)
    for _ in range(500):
        lv = sw.placebo_levels(100.0, 110.0, 95.0, rng)
        mh = (lv[1] - 100.0) / 10.0
        ml = (100.0 - lv[-1]) / 5.0
        for m in (mh, ml):
            assert 0.7 <= m <= 1.3 and not (0.95 <= m <= 1.05)
    lv = sw.placebo_levels(111.0, 110.0, 95.0, rng)
    assert lv[1] is None and lv[-1] is not None


# 6. prepare: RNG20 warm-up, adjacency and gap rules
def _day(i, dd, rngw=4.0, base=100.0):
    o, h, l, c = flat(base)
    h[10] = base + rngw / 2
    l[20] = base - rngw / 2
    return {'seq': i + 1, 'date': dd, 'o': o, 'h': h, 'l': l, 'c': c}


def test_prepare():
    days, dd = [], date(2010, 1, 4)
    for i in range(30):
        days.append(_day(i, dd, rngw=20.0))
        dd += timedelta(days=1 if dd.weekday() < 4 else 3)
    use = sw.prepare(days)
    assert len(use) == 10                             # first 20 are warm-up
    assert abs(use[0]['s'] - 2.0) < 1e-9 and use[0]['pdh'] == 110.0 and use[0]['pdl'] == 90.0
    days[0]['h'][10] = 104.0                          # a narrow-range day pulls s toward the 1.0 floor rule
    assert sw.prepare(days[:21])[0]['s'] >= 1.0
    for x in days[25:]:
        x['seq'] += 5                                 # skipped (roll / incomplete) sessions before day 25
    use2 = sw.prepare(days)
    assert len(use2) == 9 and all(u['date'] != days[25]['date'] for u in use2)


# 7. stats / verdict smoke
def test_run_all_smoke():
    days, dd = [], date(2009, 12, 1)
    rng = np.random.default_rng(3)
    for i in range(80):
        x = _day(i, dd)
        x['h'][100:110] += rng.uniform(0, 4)
        x['l'][200:210] -= rng.uniform(0, 4)
        days.append(x)
        dd += timedelta(days=1 if dd.weekday() < 4 else 3)
    res = sw.run_all(days, 'NQ')
    for arm in ('arm_A', 'arm_B'):
        assert arm in res and 'verdict' in res[arm]
        assert len(res[arm].get('placebo', {}).get('means', [None] * 20)) == 20 or res[arm]['trades'] == 0
