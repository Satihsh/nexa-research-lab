"""Synthetic G1 tests for qc_fpt/main.py (PREREG_FPT_REV.md s.7). No market data is read."""
from __future__ import annotations

import importlib.util
import os
import sys
import types
from datetime import date, timedelta

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
stub = types.ModuleType('AlgorithmImports')
stub.QCAlgorithm = object
sys.modules.setdefault('AlgorithmImports', stub)
spec = importlib.util.spec_from_file_location('qc_fpt_main', os.path.join(HERE, 'qc_fpt', 'main.py'))
fpt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fpt)


def flat(price=100.0, w=0.25):
    n = 390
    return (np.full(n, price), np.full(n, price + w), np.full(n, price - w), np.full(n, price))


def setb(arr, k, o, h, l, c):
    O, H, L, C = arr
    O[k], H[k], L[k], C[k] = o, h, l, c


# 1. displacement definition
def test_displacement_definition():
    d = flat()
    setb(d, 4, 100, 101, 99.9, 100.8)      # green
    setb(d, 5, 100.8, 100.9, 99.0, 99.5)   # red, bigger body (1.3 > 0.8), closes below prior low 99.9
    assert fpt.is_disp(*d, 5, -1)
    assert not fpt.is_disp(*d, 5, +1)
    setb(d, 5, 100.8, 100.9, 99.95, 100.0)  # red but close 100.0 not below prior low 99.9
    assert not fpt.is_disp(*d, 5, -1)
    setb(d, 5, 100.8, 100.9, 99.0, 100.5)   # red, smaller body
    assert not fpt.is_disp(*d, 5, -1)


# 2. fractal confirm / break / consume
def test_fractal_bos_and_consumption():
    o, h, l, c = flat(110.0)                # all above fair 100 -> only shorts
    fp = 100.0
    l[3] = 109.0                             # fractal low at j=3 (lower than bars 2 and 4)
    setb((o, h, l, c), 6, 110, 110.1, 108.5, 108.8)   # close 108.8 < 109 -> BOS short at bar 6
    tr = fpt.fpt_day(o, h, l, c, fp, s=1.0, t=1.52, cost=0.0, use80=True)
    assert len(tr) >= 1 and tr[0]['k'] == 7 and tr[0]['dir'] == -1 and tr[0]['trig'] in ('bos', 'both')
    # consumed: a second close below 109 later, with no new fractal, gives no new BOS signal
    o2, h2, l2, c2 = flat(110.0)
    l2[3] = 109.0
    setb((o2, h2, l2, c2), 6, 110, 110.1, 108.5, 108.8)
    # make the first trade end quickly: price jumps up to stop at bar 7
    h2[7] = 115.0
    setb((o2, h2, l2, c2), 20, 110, 110.1, 108.5, 108.7)  # another close below 109; fractal consumed
    tr2 = fpt.fpt_day(o2, h2, l2, c2, fp, s=1.0, t=1.52, cost=0.0, use80=True)
    assert all(t['k'] != 21 or t['trig'] == 'disp' for t in tr2)


# 3. direction toward fair price and the 80 % filter
def test_direction_and_distance_filter():
    o, h, l, c = flat(100.0)
    setb((o, h, l, c), 4, 100, 101, 99.9, 100.8)
    setb((o, h, l, c), 5, 100.8, 100.9, 99.0, 99.5)       # bearish displacement, close 99.5
    tr = fpt.fpt_day(o, h, l, c, fp=101.0, s=1.0, t=1.52)  # close below fair -> only longs -> no short
    assert tr == []
    tr = fpt.fpt_day(o, h, l, c, fp=98.0, s=1.0, t=1.52)   # distance 1.5 >= 0.8*1.52=1.216 -> short
    assert tr and tr[0]['dir'] == -1
    tr = fpt.fpt_day(o, h, l, c, fp=98.5, s=1.0, t=1.52)   # distance 1.0 < 1.216 -> filtered
    assert tr == []
    tr = fpt.fpt_day(o, h, l, c, fp=98.5, s=1.0, t=1.52, use80=False)
    assert tr and tr[0]['dir'] == -1


# 4. next-bar entry, stop first on ties
def test_next_bar_entry_and_stop_first():
    o, h, l, c = flat(100.0)
    setb((o, h, l, c), 4, 100, 101, 99.9, 100.8)
    setb((o, h, l, c), 5, 100.8, 100.9, 99.0, 99.5)
    o[6] = 99.6
    h[6], l[6] = 99.6 + 1.0, 99.6 - 1.52        # both stop and target touched in bar 6
    tr = fpt.fpt_day(o, h, l, c, fp=98.0, s=1.0, t=1.52)
    assert tr[0]['k'] == 6 and tr[0]['entry'] == 99.6
    assert tr[0]['kind'] == 'stop' and tr[0]['gross'] == pytest.approx(-1.0)


def _short_setup(o, h, l, c, k):
    """Bearish displacement at bar k (prior bar green), close ~ c[k-1]-1."""
    base = c[k - 1]
    setb((o, h, l, c), k - 1, base, base + 1.0, base - 0.05, base + 0.8)
    setb((o, h, l, c), k, base + 0.8, base + 0.9, base - 1.0, base - 0.5)


# 5. three-consecutive-loss session stop and 6. one position at a time
def test_session_stop_and_one_position():
    o, h, l, c = flat(110.0)
    for k in (5, 15, 25, 35):
        _short_setup(o, h, l, c, k)
        h[k + 1] = 120.0                          # stop hit on the entry bar
    tr = fpt.fpt_day(o, h, l, c, fp=100.0, s=1.0, t=1.52)
    assert len(tr) == 3 and all(t['kind'] == 'stop' for t in tr)
    assert [t['k'] for t in tr] == [6, 16, 26]


def test_one_position_signals_ignored_while_open():
    o, h, l, c = flat(110.0)
    _short_setup(o, h, l, c, 5)                   # entry bar 6, no exit until close (flat path)
    _short_setup(o, h, l, c, 20)                  # signal while position open -> ignored
    tr = fpt.fpt_day(o, h, l, c, fp=100.0, s=5.0, t=7.6, use80=False)
    assert len(tr) == 1 and tr[0]['kind'] == 'time' and tr[0]['k_exit'] == 389


# 7. V-OPEN structure / HTF filter / doubled distances
def test_open_variant():
    o, h, l, c = flat(100.0)
    setb((o, h, l, c), 0, 100.0, 100.6, 99.9, 100.5)    # green opening bar, range 0.7
    assert fpt.open_day(o, h, l, c, pre_hi=100.4, pre_lo=99.5, eve_ref=101.0, s=1.0, t=1.52)[0]['dir'] == 1
    assert fpt.open_day(o, h, l, c, pre_hi=100.6, pre_lo=99.5, eve_ref=101.0, s=1.0, t=1.52) == []  # no structure break
    assert fpt.open_day(o, h, l, c, pre_hi=100.4, pre_lo=99.5, eve_ref=99.0, s=1.0, t=1.52) == []   # HTF up -> no long
    assert fpt.open_day(o, h, l, c, pre_hi=None, pre_lo=None, eve_ref=101.0, s=1.0, t=1.52) == []
    tr = fpt.open_day(o, h, l, c, pre_hi=100.4, pre_lo=99.5, eve_ref=101.0, s=0.5, t=0.76)          # range 0.7 > 0.5
    assert tr[0]['R_pts'] == pytest.approx(1.0)


# 8. scale F and RNG20 warm-up
def test_scale_series():
    d0 = date(2025, 3, 1)
    dates = [d0 + timedelta(days=i) for i in range(60)]
    rngs = [50.0] * 60
    f, s = fpt.scale_series(rngs, dates)
    assert f == pytest.approx(25.0 / 50.0)
    assert s[:20] == [None] * 20 and s[20] == pytest.approx(25.0)
    f2, s2 = fpt.scale_series([1.0] * 30, dates[:30], f=0.5)
    assert f2 == 0.5 and s2[25] == pytest.approx(fpt.MIN_STOP)


def test_run_all_smoke():
    days = []
    d0 = date(2025, 3, 3)
    for i in range(40):
        o, h, l, c = flat(100.0 + i)
        days.append({'date': d0 + timedelta(days=i), 'o': o, 'h': h, 'l': l, 'c': c, 'rng': 2.0,
                     'pre_hi': None, 'pre_lo': None, 'eve': None})
    res = fpt.run_all(days, 'NQ')
    assert res['n_days'] == 20 and res['P']['trades'] == 0 and res['P']['verdict'] == 'INSUFFICIENT-N'
