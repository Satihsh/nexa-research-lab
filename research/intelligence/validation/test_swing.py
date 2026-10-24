"""Synthetic G1 tests for qc_swing/main.py (PREREG_SWING_TREND.md s.7). No market data is read."""
from __future__ import annotations

import importlib.util
import math
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
spec = importlib.util.spec_from_file_location('qc_swing_main', os.path.join(HERE, 'qc_swing', 'main.py'))
sw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sw)


def bdays(n, start=date(2009, 1, 1)):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def trend(n, g=0.001, noise=0.0, seed=0):
    rng = np.random.default_rng(seed)
    r = g + noise * rng.standard_normal(n)
    return 100.0 * np.cumprod(1 + r)


# 1. sign / lookback
def test_tsmom_sign_follows_lookback():
    n = 400
    d = bdays(n)
    up = trend(n, 0.001, 0.005, 1)
    w = sw.decisions(d, up * 1.001, up * 0.999, up, 'P')
    v = w[~np.isnan(w)]
    assert len(v) > 0 and (v > 0).all()
    dn = trend(n, -0.001, 0.005, 2)
    w = sw.decisions(d, dn * 1.001, dn * 0.999, dn, 'P')
    assert (w[~np.isnan(w)] < 0).all()
    first = int(np.flatnonzero(~np.isnan(w))[0])
    assert first == sw.LOOKBACK + sw.WARM_EXTRA - 1


# 2. EWMA vol and cap
def test_ewma_vol_and_cap():
    c = 100 * np.cumprod(1 + np.tile([0.01, -0.01], 300))
    vol = sw.ewma_vol(c)
    assert vol[-1] == pytest.approx(math.sqrt(252) * 0.01, rel=0.02)
    assert sw.size(0.01) == sw.CAP
    assert sw.size(0.40) == pytest.approx(1.0)
    assert sw.size(float('nan')) == 0.0


# 3. month-end decision only, and one-day execution lag
def test_month_end_and_lag():
    n = 420
    d = bdays(n)
    c = trend(n, 0.001, 0.004, 3)
    w = sw.decisions(d, c * 1.001, c * 0.999, c, 'P')
    me = sw.month_end_flags(d)
    idx = np.flatnonzero(~np.isnan(w))
    for t in idx[1:]:
        if not me[t]:
            assert w[t] == w[t - 1]
    rolls = [False] * n
    pnl = sw.market_pnl(d, c, rolls, w, [0.0, 0.0, 0.0])
    t0 = idx[0]
    assert d[t0] not in pnl and d[t0 + 1] in pnl
    g, cs, dw, rc = pnl[d[t0 + 1]]
    assert g == 0.0 and dw == pytest.approx(abs(w[t0]))           # executed at close t0+1, no exposure yet
    g2, *_ = pnl[d[t0 + 2]]
    assert g2 == pytest.approx(w[t0] * (c[t0 + 2] / c[t0 + 1] - 1))


# 4. Donchian state machine
def test_donchian_entry_exit():
    n = 450
    d = bdays(n)
    c = np.full(n, 100.0)
    c[330:360] = np.linspace(101, 110, 30)                # breakout above 55-day high
    c[360:] = 90.0 - 0.5 * np.arange(n - 360)              # collapse below 20-day low -> exit, then keeps falling
    h, l = c + 0.1, c - 0.1
    w = sw.decisions(d, h, l, c, 'V-DON')
    assert np.isnan(w[300]) or w[300] == 0
    assert w[335] > 0
    assert w[360] == 0                                     # exit first, no same-bar flip
    assert w[380] < 0                                      # later close < 55-day low -> short


# 5. MA cross
def test_ma_cross_sign():
    n = 450
    d = bdays(n)
    up = trend(n, 0.001, 0.0, 0)
    w = sw.decisions(d, up, up, up, 'V-MA')
    assert (w[~np.isnan(w)] > 0).all()


# 6. cost at rebalance and roll
def test_costs_rebalance_and_roll():
    d = bdays(6)
    c = np.full(6, 100.0)
    w = np.array([np.nan, 1.0, 1.0, 0.5, 0.5, 0.5])
    rolls = [False, False, False, False, True, False]
    pnl = sw.market_pnl(d, c, rolls, w, [0.0, 2.0, 4.0])
    _, cs, dw, rc = pnl[d[2]]                               # entry executed at close 2: |1-0| * 1/100
    assert cs[1] == pytest.approx(0.01) and dw == pytest.approx(1.0)
    _, cs, dw, rc = pnl[d[4]]                               # 1 -> 0.5 executed at close 4 + roll with |1| held
    assert dw == pytest.approx(0.5)
    assert rc[1] == pytest.approx(1.0 * 2.0 / 100)
    assert cs[1] == pytest.approx(0.5 * 1.0 / 100 + 0.02)


# 7. portfolio averages over active markets
def test_portfolio_average():
    d1, d2 = date(2011, 1, 3), date(2011, 1, 4)
    pnl = {'A': {d1: (0.02, [0.0, 0.0, 0.0], 0.0, [0, 0, 0]), d2: (0.01, [0, 0, 0], 0, [0, 0, 0])},
           'B': {d2: (0.03, [0, 0.01, 0], 0, [0, 0, 0])}}
    days, R, G, sec, _ = sw.portfolio(pnl, {'A': 'x', 'B': 'y'})
    assert days == [d1, d2]
    assert R[1][0] == pytest.approx(0.02)
    assert R[1][1] == pytest.approx((0.01 + 0.02) / 2)


# 8. bootstrap / verdict
def test_bootstrap_and_verdict():
    x = np.full(800, 0.001) + np.random.default_rng(0).normal(0, 0.0001, 800)
    days = bdays(800, date(2011, 1, 3))
    st = sw.series_stats(days, x)
    assert st['S1']['ci95'][0] > 0 and sw.verdict(st) == 'VALIDATED (G4)'
    st2 = sw.series_stats(days, -x)
    assert sw.verdict(st2) == 'REJECTED'
    st3 = sw.series_stats(days[:300], x[:300])
    assert sw.verdict(st3) == 'INSUFFICIENT-N'


def test_run_all_smoke():
    n = 700
    d = bdays(n)
    data = {}
    for i, k in enumerate(('ES', 'NQ', 'GC')):
        c = trend(n, 0.0005 * (1 if i != 2 else -1), 0.01, i)
        data[k] = {'dates': d, 'o': list(c), 'h': list(c * 1.002), 'l': list(c * 0.998), 'c': list(c),
                   'rolls': [j % 63 == 0 for j in range(n)]}
    props = {'ES': (0.25, 50.0), 'NQ': (0.25, 20.0), 'GC': (0.1, 100.0)}
    res = sw.run_all(data, props)
    assert set(sw.VARIANTS) <= set(res) and res['P']['n_days'] > 0
    assert res['V-IDX']['n_days'] > 0
