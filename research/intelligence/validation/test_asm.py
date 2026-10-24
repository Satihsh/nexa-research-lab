"""Synthetic tests for qc_asm/main.py (PREREG_T1_STATE.md, PREREG_T2A_VAR.md). No market data is read."""
from __future__ import annotations

import importlib.util
import math
import os
import sys
import types

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
stub = types.ModuleType('AlgorithmImports')
stub.QCAlgorithm = object
sys.modules.setdefault('AlgorithmImports', stub)
spec = importlib.util.spec_from_file_location('qc_asm_main', os.path.join(HERE, 'qc_asm', 'main.py'))
asm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asm)


def flat_day(price=100.0, wiggle=0.25):
    o, h, l, c = [], [], [], []
    for k in range(390):
        o.append(price); c.append(price); h.append(price + wiggle); l.append(price - wiggle)
    return {'o': o, 'h': h, 'l': l, 'c': c, 'v': [100.0] * 390}


def set_bar(day, k, o, h, l, c):
    day['o'][k], day['h'][k], day['l'][k], day['c'][k] = o, h, l, c


def test_volume_spread_uniform():
    base, vol = asm.volume_at_price([(101.0, 100.0, 50.0), (100.5, 100.5, 10.0)])
    assert base == 400 and len(vol) == 5
    assert vol == pytest.approx([10.0, 10.0, 20.0, 10.0, 10.0])


def test_value_area_dalton_pairs():
    # ticks 100.00 .. 102.00; POC at 101.00; heavier side above
    prof = [(100.0, 100.0, 1.0), (100.25, 100.25, 2.0), (100.5, 100.5, 3.0), (100.75, 100.75, 4.0),
            (101.0, 101.0, 20.0), (101.25, 101.25, 6.0), (101.5, 101.5, 6.0), (101.75, 101.75, 1.0), (102.0, 102.0, 1.0)]
    poc, val, vah = asm.value_area(prof)
    assert poc == 101.0
    # total 44, 70 % = 30.8: POC 20 -> +above pair (12) = 32 >= 30.8
    assert (val, vah) == (101.0, 101.5)


def test_value_area_tie_goes_up_and_poc_tie_to_middle():
    prof = [(100.0, 100.0, 5.0), (100.25, 100.25, 5.0), (100.5, 100.5, 10.0), (100.75, 100.75, 5.0), (101.0, 101.0, 5.0)]
    poc, val, vah = asm.value_area(prof)
    assert poc == 100.5 and (val, vah) == (100.0, 101.0)       # equal pairs -> above first (20/30 < 70 %), then below
    poc2, _, _ = asm.value_area([(100.0, 100.0, 5.0), (100.25, 100.25, 1.0), (100.5, 100.5, 5.0)])
    assert poc2 == 100.0                                        # tie, equidistant from middle -> lower


def test_t1_states_and_scores():
    d = flat_day(100.0)
    d['c'][asm.K11] = 103.0                                     # above VAH at 11:00
    d['c'][asm.K_LAST] = 104.0
    r = asm.t1_day(d, 99.0, 101.0)
    assert r['state'] == 'I+' and r['D'] == 1 and r['sub'] == 'I-breakout' and r['Y'] > 0
    d2 = flat_day(102.0)
    d2['c'][asm.K11] = 100.5                                    # opened above, back inside -> failed auction
    d2['c'][asm.K_LAST] = 101.5
    r2 = asm.t1_day(d2, 99.0, 101.0)
    assert r2['state'] == 'R' and r2['sub'] == 'R-failed' and r2['Dm'] == -1 and r2['Y'] < 0   # reverts up = Y<0
    assert r2['Y'] == pytest.approx(-math.log(101.5 / 100.5) * 1e4)


def test_t2a_long_reentry_hits_2r():
    d = flat_day(100.0)                                          # VA 99..101
    for k in range(15, 30):                                      # 09:45 bar: closes below VAL
        set_bar(d, k, 98.5, 98.75, 98.0, 98.5)
    for k in range(30, 45):                                      # 10:00 bar: closes back inside
        set_bar(d, k, 99.5, 99.75, 99.25, 99.5)
    set_bar(d, 45, 99.5, 99.6, 99.4, 99.5)                       # entry at 99.5; stop 97.75 -> R 1.75; target 103.0
    for k in range(46, 390):
        set_bar(d, k, 103.5, 103.75, 103.25, 103.5)
    tr, sr, sv = asm.t2a_day(d, 99.0, 101.0)
    assert len(tr) == 1 and tr[0]['dir'] == 1 and tr[0]['kind'] == 'target'
    assert tr[0]['stop'] == pytest.approx(97.75) and tr[0]['tgt'] == pytest.approx(103.0)
    assert asm.net_r(tr[0], 0.0) == pytest.approx(2.0)


def test_t2a_stop_first_when_both_touched():
    d = flat_day(100.0)
    for k in range(15, 30):
        set_bar(d, k, 98.5, 98.75, 98.0, 98.5)
    for k in range(30, 45):
        set_bar(d, k, 99.5, 99.75, 99.25, 99.5)
    set_bar(d, 45, 99.5, 104.0, 97.0, 99.5)                      # both stop and target inside one minute
    tr, _, _ = asm.t2a_day(d, 99.0, 101.0)
    assert tr[0]['kind'] == 'stop' and asm.net_r(tr[0], 0.0) == pytest.approx(-1.0)


def test_t2a_short_and_window_and_small_r():
    d = flat_day(100.0)
    for k in range(15, 30):
        set_bar(d, k, 101.5, 102.0, 101.25, 101.5)               # up excursion
    for k in range(30, 45):
        set_bar(d, k, 100.5, 100.75, 100.25, 100.5)              # back inside -> short
    tr, _, _ = asm.t2a_day(d, 99.0, 101.0)
    assert tr and tr[0]['dir'] == -1 and tr[0]['stop'] == pytest.approx(102.25)
    late = flat_day(100.0)
    for k in range(330, 345):                                    # 15:00 bar closes outside, re-entry after 15:00
        set_bar(late, k, 98.5, 98.75, 98.0, 98.5)
    for k in range(345, 360):
        set_bar(late, k, 99.5, 99.75, 99.25, 99.5)
    assert asm.t2a_day(late, 99.0, 101.0)[0] == []
    tiny = flat_day(100.0)
    for k in range(15, 30):
        set_bar(tiny, k, 98.6, 98.7, 98.5, 98.6)                 # close below VAL, extreme 98.5 -> stop 98.25
    for k in range(30, 45):
        set_bar(tiny, k, 99.0, 99.1, 98.95, 99.05)
    set_bar(tiny, 45, 98.95, 99.0, 98.9, 98.95)                  # entry 98.95 -> R 0.70 >= 2 ticks (0.50)
    tr_t, sr, _ = asm.t2a_day(tiny, 99.0, 101.0)
    assert len(tr_t) == 1 and sr == 0
    set_bar(tiny, 45, 98.6, 98.7, 98.55, 98.6)                   # entry 98.6 -> R 0.35 < 2 ticks -> skipped
    tr_s, sr2, _ = asm.t2a_day(tiny, 99.0, 101.0)
    assert sr2 == 1 and all(t['k'] != 45 for t in tr_s)


def test_t2a_needs_new_excursion_after_exit():
    d = flat_day(100.0)
    for k in range(15, 30):
        set_bar(d, k, 98.5, 98.75, 98.0, 98.5)
    for k in range(30, 45):
        set_bar(d, k, 99.5, 99.75, 99.25, 99.5)
    set_bar(d, 45, 99.5, 99.6, 97.0, 99.5)                       # stopped out at minute 45
    for k in range(46, 75):                                      # rest of the 10:15 bar and the 10:30 bar inside
        set_bar(d, k, 99.5, 99.75, 99.25, 99.5)
    tr, _, _ = asm.t2a_day(d, 99.0, 101.0)
    assert len(tr) == 1                                          # no re-signal without a new close outside
    for k in range(75, 90):
        set_bar(d, k, 98.5, 98.75, 98.25, 98.5)                  # new excursion
    for k in range(90, 105):
        set_bar(d, k, 99.5, 99.75, 99.25, 99.5)
    tr2, _, _ = asm.t2a_day(d, 99.0, 101.0)
    assert len(tr2) == 2 and tr2[1]['k'] == 105


def test_t2a_va_target_variant_and_eve_window():
    d = flat_day(100.0)
    for k in range(15, 30):
        set_bar(d, k, 98.5, 98.75, 98.0, 98.5)
    for k in range(30, 45):
        set_bar(d, k, 99.5, 99.75, 99.25, 99.5)
    set_bar(d, 45, 99.5, 99.75, 99.4, 99.6)                      # entry 99.5, opposite VA edge 101.0 above it
    for k in range(46, 390):
        set_bar(d, k, 101.5, 101.75, 101.25, 101.5)
    tr, _, _ = asm.t2a_day(d, 99.0, 101.0, target='VA')
    assert tr[0]['tgt'] == 101.0 and tr[0]['kind'] == 'target'
    assert asm.t2a_day(d, 99.0, 101.0, last_end=600)[0] == []    # signal bar ends 10:15 > 10:00 window


def test_stats_and_verdicts():
    rows = []
    for i in range(1200):
        st = 'I+' if i % 2 == 0 else 'R'
        rows.append({'state': st, 'sub': 'I-migration' if st != 'R' else 'R-failed', 'Y': 5.0 if st != 'R' else -5.0,
                     'Yb': 1.0, 'Rr': 5.0, 'ibpct': (i % 10) / 10})
    s = asm.t1_stats(rows)
    assert s['H1_I_cont']['theta'] == 5.0 and s['H2_R_cont']['theta'] == -5.0 and s['H3_delta']['theta'] == 10.0
    assert asm.t1_verdict(s) == 'STATE PREDICTABLE'
    t = {'dir': 1, 'R_pts': 1.0, 'gross': 2.0, 'kind': 'target'}
    days = [[t] if i % 3 == 0 else [] for i in range(1200)]
    st2 = asm.t2a_stats(days, (0.0, 0.5, 1.0), [2010 + i // 100 for i in range(1200)])
    assert st2['trades'] == 400 and st2['S1']['theta'] == pytest.approx(1.5)
    assert asm.t2a_verdict(st2) == 'VALIDATED (G4)'
    lose = {'dir': -1, 'R_pts': 1.0, 'gross': -1.0, 'kind': 'stop'}
    st3 = asm.t2a_stats([[lose] if i % 3 == 0 else [] for i in range(1200)], (0.0, 0.5, 1.0), [2010] * 1200)
    assert asm.t2a_verdict(st3) == 'REJECTED'
