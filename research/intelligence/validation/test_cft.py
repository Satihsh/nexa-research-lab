"""Synthetic tests for qc_cft/main.py (PREREG_CFT.md). No market data is read."""
from __future__ import annotations

import importlib.util
import os
import sys
import types
from datetime import date

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
stub = types.ModuleType('AlgorithmImports')
stub.QCAlgorithm = object
sys.modules.setdefault('AlgorithmImports', stub)
spec = importlib.util.spec_from_file_location('qc_cft_main', os.path.join(HERE, 'qc_cft', 'main.py'))
cft = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cft)


def flat_day(base=5000.0, step=0.0, wiggle=0.25, vol=100.0, x=None):
    o, h, l, c, v = [], [], [], [], []
    p = base
    for k in range(390):
        op = p
        p = base + step * (k + 1)
        cl = p + (wiggle if k % 2 else -wiggle)
        o.append(op); c.append(cl); h.append(max(op, cl) + 0.25); l.append(min(op, cl) - 0.25); v.append(vol)
    d = {'o': o, 'h': h, 'l': l, 'c': c, 'v': v}
    d['x'] = x if x is not None else [0.0] * 390
    return d


def prev_days(n=14, base=5000.0):
    return [{'o': flat_day(base)['o'], 'c': flat_day(base)['c']} for _ in range(n)]


def test_classify_quote_mid_and_tick_rule():
    assert cft.classify(100.5, 100.0, 100.5, None, 0) == 1
    assert cft.classify(100.0, 100.0, 100.5, None, 0) == -1
    assert cft.classify(100.4, 100.0, 100.5, None, 0) == 1           # above mid
    assert cft.classify(100.1, 100.0, 100.5, None, 0) == -1          # below mid
    assert cft.classify(100.25, 100.0, 100.5, 100.0, 0) == 1         # at mid -> tick rule up
    assert cft.classify(100.25, 100.0, 100.5, 100.25, -1) == -1      # unchanged -> previous sign
    assert cft.classify(100.25, None, None, 100.5, 0) == -1          # no quotes -> tick rule


def test_sigma_band_and_trend_long_time_exit():
    prev = prev_days()
    s = cft.sigma_at(prev, 29)
    assert 0 < s < 0.001
    day = flat_day(step=0.5)                       # steady rise: above UB by 10:00, VWAP below price
    tr = cft.simulate(day, prev)
    assert len(tr) == 1 and tr[0]['dir'] == 1 and tr[0]['tau'] == 600 and tr[0]['kind'] == 'time'
    assert tr[0]['entry'] == day['o'][30] and tr[0]['exit'] == day['c'][389] and tr[0]['pts'] > 0


def test_gate_blocks_noise_and_passes_persistent_flow():
    prev = prev_days()
    persistent = flat_day(step=0.5, x=[50.0] * 390)
    noisy = flat_day(step=0.5, x=[50.0 if k % 2 else -50.0 for k in range(390)])
    assert len(cft.simulate(persistent, prev, gate=True)) == 1
    assert cft.simulate(noisy, prev, gate=True) == []
    against = flat_day(step=0.5, x=[-50.0] * 390)   # flow opposite to the price trend
    assert cft.simulate(against, prev, gate=True) == []


def test_vwap_trailing_stop_and_reversal():
    prev = prev_days()
    day = flat_day(step=0.5)
    for k in range(150, 390):                       # 12:00 onward: collapse far below the lower band
        p = day['c'][149] - 3.0 * (k - 149)
        day['o'][k] = p + 1.0; day['c'][k] = p; day['h'][k] = p + 1.25; day['l'][k] = p - 0.25
    tr = cft.simulate(day, prev)
    assert tr[0]['dir'] == 1 and tr[0]['kind'] == 'stop'
    assert any(t['dir'] == -1 for t in tr[1:])      # reversal into a short at the same decision time
    rev = [t for t in tr if t['dir'] == -1][0]
    assert rev['tau'] == tr[0]['exit_tau']


def test_no_same_direction_reentry_and_evening_exit():
    prev = prev_days()
    day = flat_day(step=0.5)
    tr = cft.simulate(day, prev, eve=True)
    assert len(tr) == 1 and tr[0]['exit'] == day['c'][cft.EVE_EXIT_K]


def test_roll_day_uses_open_only_bands():
    prev = prev_days(base=4000.0)                   # yesterday's close far below today's open
    day = flat_day(base=5000.0, step=0.5)
    assert len(cft.simulate(day, prev, roll=True)) == 1      # gap term dropped on roll days


def test_overlay_and_combine_and_green_month():
    tr = [{'pts': 5.0, 'R': 3.0, 'mae': -1.0}, {'pts': -3.0, 'R': 2.0, 'mae': -3.0}, {'pts': 4.0, 'R': 2.0, 'mae': 0.0}]
    assert cft.overlay(tr, 0, 0.0)[0] == pytest.approx(6.0)
    assert cft.overlay(tr, 1, 0.0)[0] == pytest.approx(5.0)
    tr2 = [{'pts': -4.0, 'R': 3.0, 'mae': -4.0}, {'pts': 9.0, 'R': 3.0, 'mae': 0.0}]
    assert cft.overlay(tr2, 2, 0.0)[0] == pytest.approx(-4.0)          # stop at -1R
    assert cft.overlay(tr2, 0, 0.0)[1] == pytest.approx(-4.0)          # worst mark
    pp, pb = cft.combine_sim(np.full(40, 200.0), np.zeros(40), n_paths=200)
    assert pp == 1.0 and pb == 0.0
    pp, pb = cft.combine_sim(np.full(40, -150.0), np.full(40, -150.0), n_paths=200)
    assert pp == 0.0 and pb == 1.0
    assert cft.green_month(np.full(30, 1.0), n_paths=50) == 1.0
    assert cft.green_month(np.array([1.0, -1.0] * 20), n_paths=50) == 0.0


def test_summarise_verdict_and_cftp_shapes():
    prev = prev_days()
    up = flat_day(step=0.5, x=[50.0] * 390)
    days = []
    for i in range(400):
        tt = {'A': cft.simulate(up, prev), 'B': cft.simulate(up, prev, gate=True), 'BEVE': []}
        days.append((date(2024, 6, 3), up['o'][0], tt))
    st = cft.summarise(days, ['A', 'B', 'BEVE'], 'ES')
    assert st['B']['trades'] == 400 and st['B']['S1']['theta'] > 0 and st['B']['green_share'] == 1.0
    diff = cft.boot(st['B']['series'] - st['A']['series'])
    assert cft.verdict(st['A'], st['B'], diff) in ('TREND-ONLY', 'CFT VALIDATED (G4)', 'INCONCLUSIVE')
    out = cft.cftp([tt['B'] for _, _, tt in days[:60]], 'ES')
    assert set(out['grid']) == {f'V{o}_k{k}' for o in range(4) for k in (2, 4, 8)} and out['choice'] is not None
