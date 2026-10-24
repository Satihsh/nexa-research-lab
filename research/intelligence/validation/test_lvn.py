"""Synthetic G1 tests for qc_lvn/main.py (PREREG_LVN_SPEED.md s.7). No market data is read."""
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
spec = importlib.util.spec_from_file_location('qc_lvn_main', os.path.join(HERE, 'qc_lvn', 'main.py'))
lv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lv)


# 1. bin width: 2 % of RNG20, whole ticks, at least one tick
def test_bin_width():
    assert lv.bin_width(100.0) == 2.0
    assert lv.bin_width(30.0) == 0.5          # 0.6 -> 0.5 (floor to ticks)
    assert lv.bin_width(5.0) == 0.25          # 0.1 -> 1 tick minimum


# 2. uniform spreading by overlap; zero-range bar; total volume preserved
def test_profile_spreading():
    p = lv.profile([102.0], [100.0], [100.0], 100.0, 104.0, 1.0)   # bins [100,101) [101,102) [102,103) [103,104) [104]
    assert len(p) == 5
    assert abs(p[0] - 50) < 1e-9 and abs(p[1] - 50) < 1e-9 and p[2] == 0
    p = lv.profile([101.5], [101.5], [30.0], 100.0, 104.0, 1.0)
    assert p[1] == 30.0
    p = lv.profile([104.0, 103.0], [100.0, 100.5], [80.0, 25.0], 100.0, 104.0, 1.0)
    assert abs(p.sum() - 105.0) < 1e-9


# 3. thin / thick selection and ties
def test_tags():
    prof = np.array([5, 1, 1, 9, 7, 3, 8, 2, 6, 4], float)      # n = 10 -> k = 2
    t = lv.tags(prof)
    assert list(np.nonzero(t == -1)[0]) == [1, 2]               # tie at 1: both lowest, lower price first
    assert list(np.nonzero(t == 1)[0]) == [3, 6]
    assert (t == 0).sum() == 6


# 4. minutes outside [PDL, PDH] are ignored; groups by bin tag
def test_day_sums():
    tag = np.array([-1, 0, 1])
    c = np.array([100.5, 101.5, 102.5, 110.0, 99.0, 100.2])
    r = lv.day_sums(c, 100.0, 103.0, 1.0, tag, 1.0)
    assert r['thin'][1] == 1 and r['mid'][1] == 1 and r['thick'][1] == 1   # k=3 (110) and k=4 (99) are outside
    assert abs(r['thick'][0] - 7.5) < 1e-9 and abs(r['thin'][0] - 1.0) < 1e-9


# 5. sigma warm-up / adjacency in prepare; mirror flip
def _day(i, dd, rng):
    c = 100 + np.cumsum(rng.normal(0, 0.5, 390))
    h = c + 0.5
    l = c - 0.5
    v = rng.uniform(10, 100, 390)
    return {'seq': i + 1, 'date': dd, 'h': h, 'l': l, 'c': c, 'v': v}


def test_prepare_and_mirror():
    rng = np.random.default_rng(2)
    days, dd = [], date(2010, 1, 4)
    for i in range(40):
        days.append(_day(i, dd, rng))
        dd += timedelta(days=1 if dd.weekday() < 4 else 3)
    rows, sk = lv.prepare(days)
    assert len(rows) == 20 and sk['gap'] == 0
    for x in days[30:]:
        x['seq'] += 3                         # three skipped (roll / incomplete) sessions before day 30
    rows2, sk2 = lv.prepare(days)
    assert sk2['gap'] == 1 and len(rows2) == 19
    t = lv.tags(np.arange(10, dtype=float))
    assert list(np.nonzero(t[::-1] == -1)[0]) == [8, 9]


# 6. run_all smoke and verdict keys
def test_run_all_smoke():
    rng = np.random.default_rng(4)
    days, dd = [], date(2010, 1, 4)
    for i in range(120):
        days.append(_day(i, dd, rng))
        dd += timedelta(days=1 if dd.weekday() < 4 else 3)
    res = lv.run_all(days, 'NQ')
    assert res['verdict'] in ('CONFIRMED', 'REFUTED', 'INCONCLUSIVE')
    assert len(res['S_ci95']) == 2 and len(res['blocks']) == 4
