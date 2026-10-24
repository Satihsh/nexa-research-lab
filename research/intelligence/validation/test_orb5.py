"""Synthetic G1 tests for qc_orb5/main.py (PREREG_ORB5.md s.6). No market data is read."""
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
spec = importlib.util.spec_from_file_location('qc_orb5_main', os.path.join(HERE, 'qc_orb5', 'main.py'))
ob = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ob)


def flat(price=100.0, w=0.25):
    n = 390
    return [np.full(n, price), np.full(n, price + w), np.full(n, price - w), np.full(n, price)]


def up_candle(d):
    d[0][0], d[3][4] = 100.0, 101.0           # O = 100, C = 101 -> long
    d[1][2], d[2][1] = 101.5, 99.0            # H = 101.5, L = 99.0
    d[0][5] = 101.0                           # entry 101.0 -> R = 2.0, target 121.0


# 1. candle, direction, doji
def test_candle_and_direction():
    d = flat()
    up_candle(d)
    assert ob.candle(*d) == (100.0, 101.5, 99.0, 101.0)
    assert ob.real_dir(*d) == 1
    d[3][4] = 100.0
    assert ob.real_dir(*d) == 0
    d[3][4] = 99.5
    assert ob.real_dir(*d) == -1


# 2. stop side, R and 10R target
def test_stop_side_and_target():
    d = flat()
    up_candle(d)
    for k in range(5, 390):
        d[1][k], d[2][k], d[3][k] = 101.25, 100.75, 101.0
    d[1][200] = 121.0                         # target touched
    t = ob.orb_trade(*d, 1)
    assert t['R_pts'] == 2.0 and t['kind'] == 'target' and t['exit'] == 121.0 and t['k_exit'] == 200
    s = ob.orb_trade(*d, -1)                  # short: stop at H = 101.5, R = 0.5 < 1.0 floor -> None
    assert s is None


# 3. stop-first tie and time exit
def test_tie_and_time_exit():
    d = flat()
    up_candle(d)
    for k in range(5, 390):
        d[1][k], d[2][k], d[3][k] = 101.25, 100.75, 101.0
    d[1][50], d[2][50] = 121.0, 98.0          # both in one minute -> stop
    t = ob.orb_trade(*d, 1)
    assert t['kind'] == 'stop' and t['exit'] == 99.0
    d[1][50], d[2][50] = 101.25, 100.75
    d[3][389] = 101.5
    t = ob.orb_trade(*d, 1)
    assert t['kind'] == 'time' and t['exit'] == 101.5


# 4. R floor and entry beyond stop
def test_r_floor():
    d = flat()
    up_candle(d)
    d[0][5] = 99.0                            # entry at the stop -> R = 0 -> None
    assert ob.orb_trade(*d, 1) is None
    d[0][5] = 99.75                           # R = 0.75 < 1.0 -> None
    assert ob.orb_trade(*d, 1) is None


# 5. set P / IN split
def test_sets():
    assert ob.in_primary(date(2012, 5, 1)) and ob.in_primary(date(2024, 5, 1))
    assert not ob.in_primary(date(2018, 5, 1)) and not ob.in_primary(date(2023, 2, 27))
    assert not ob.in_primary(date(2009, 12, 15))


# 6. run_all smoke: placebo and verdict keys, doji counting
def test_run_all_smoke():
    rng = np.random.default_rng(5)
    days, dd = [], date(2010, 1, 4)
    while dd < date(2026, 1, 1):
        if dd.weekday() < 5:
            d = flat()
            d[0][0] = 100.0
            d[3][4] = 100.0 + rng.choice([-1.0, 0.0, 1.0])
            d[1][:5], d[2][:5] = 102.0, 98.0
            d[0][5] = d[3][4]
            d[3][389] = 100.0 + rng.normal(0, 3)
            days.append({'date': dd, 'o': d[0], 'h': d[1], 'l': d[2], 'c': d[3]})
        dd += timedelta(days=7)
    res = ob.run_all(days, 'NQ')
    assert res['skipped']['doji'] > 0
    assert set(['P', 'IN', 'PRE', 'POST', 'placebo', 'verdict']) <= set(res)
    assert res['P']['days'] + res['IN']['days'] <= res['n_days']
