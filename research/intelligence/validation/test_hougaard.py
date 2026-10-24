"""Synthetic G1 tests for qc_hougaard/main.py (PREREG_HOUGAARD.md s.7). No market data."""
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
spec = importlib.util.spec_from_file_location('qc_hougaard_main', os.path.join(HERE, 'qc_hougaard', 'main.py'))
hg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hg)


def flat(p=35000.0):
    """180 bars, all at p, window high p+10, low p-10 (bar 0)."""
    o, h, l, c = (np.full(hg.NB, p) for _ in range(4))
    h[0], l[0] = p + 10, p - 10
    return o, h, l, c


def hold(arrs, k, price):
    """Bars after k sit at price (so later bars neither stop nor target unless a test sets them)."""
    for a in arrs:
        a[k + 1:] = price


def test_window_high_low_uses_59_bars_only():
    o, h, l, c = flat()
    h[58], l[30] = 35020.0, 34985.0
    h[59] = 36000.0                          # first active bar, not part of the window
    assert hg.window(h, l) == (35020.0, 34985.0)


def test_distances_percentage_and_floors():
    assert hg.distances(35000.0, 1.0, 'A') == (9.0, 6.0)
    assert hg.distances(35000.0, 1.0, 'B') == (9.0, 9.0)
    s, t = hg.distances(21000.0, 0.25, 'A')
    assert abs(s - 5.5) < 1e-9 and abs(t - 3.5) < 1e-9     # 5.4 -> 5.5, 3.6 -> 3.5 (nearest tick)
    assert hg.distances(100.0, 0.25, 'A') == (0.5, 0.25)  # floors: 2 ticks / 1 tick
    assert hg.distances(35000.0, 1.0, 'A', fixed=(9.0, 6.0)) == (9.0, 6.0)


def test_no_trigger_no_trade_and_cancel_after_1029():
    o, h, l, c = flat()
    assert hg.real_trade(o, h, l, c, 1.0, 'A') is None
    h[120] = 35020.0                          # 10:30 bar: orders already cancelled
    assert hg.real_trade(o, h, l, c, 1.0, 'A') is None
    h[119] = 35010.0                          # 10:29 bar: still active
    t = hg.real_trade(o, h, l, c, 1.0, 'A')
    assert t['dir'] == 1 and t['k'] == 119


def test_long_target_and_gap_fill():
    o, h, l, c = flat()
    o[60], h[60], l[60], c[60] = 35012.0, 35013.0, 35012.0, 35013.0   # gaps above the high: fill at the open
    hold((o, h, l, c), 60, 35012.0)
    h[61] = 35012.0 + 6.0
    t = hg.real_trade(o, h, l, c, 1.0, 'A')
    assert t['dir'] == 1 and t['kind'] == 'target' and abs(t['gross'] - 6 / 9) < 1e-12


def test_short_stop_first_in_entry_bar():
    o, h, l, c = flat()
    h[70], l[70] = 34990.0 + 9.0, 34990.0 - 6.0   # entry bar reaches stop and target: stop first
    t = hg.real_trade(o, h, l, c, 1.0, 'A')
    assert t['dir'] == -1 and t['kind'] == 'stop' and t['gross'] == -1.0


def test_both_levels_in_one_bar_is_minus_one():
    o, h, l, c = flat()
    h[65], l[65] = 35011.0, 34989.0
    t = hg.real_trade(o, h, l, c, 1.0, 'B')
    assert t['kind'] == 'both' and t['gross'] == -1.0 and t['dir'] == 0


def test_oco_first_fill_cancels_other():
    o, h, l, c = flat()
    h[62] = 35010.0                           # long fills first
    l[90] = 34900.0                           # later break of the low: no second trade, it is the long's stop
    t = hg.real_trade(o, h, l, c, 1.0, 'A')
    assert t['dir'] == 1 and t['k'] == 62 and t['kind'] == 'stop'


def test_time_exit_at_1129_close():
    o, h, l, c = flat()
    h[62], l[62] = 35010.0, 35010.0
    hold((o, h, l, c), 62, 35010.0)
    c[hg.K_LAST] = 35013.0
    t = hg.real_trade(o, h, l, c, 1.0, 'A')
    assert t['kind'] == 'time' and abs(t['gross'] - 3 / 9) < 1e-12


def test_control_uses_real_bar_open_when_side_never_traded():
    o, h, l, c = flat()
    h[62] = 35010.0
    o[62] = 35001.0
    g, s = hg.control_trade(o, h, l, c, 1.0, 'A', -1, 62)
    assert s == 9.0 and g == -1.0            # short from 35001 at bar 62: high 35010 >= stop 35010 -> stop


def test_net_r_and_breakeven_logic():
    t = {'gross': 6 / 9, 'stop_pts': 9.0}
    assert abs(hg.net_r(t, 3.0) - (6 / 9 - 1 / 3)) < 1e-12


def synth_days(n, rng, p_win, start=date(2010, 1, 4)):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            o, h, l, c = flat()
            k = 60 + int(rng.integers(0, 50))
            up = rng.random() < 0.5
            if up:
                h[k] = 35010.0
            else:
                l[k] = 34990.0
            sgn = 1 if up else -1
            ent = 35010.0 if up else 34990.0
            hold((o, h, l, c), k, ent)
            if up:
                l[k] = ent
            else:
                h[k] = ent
            win = rng.random() < p_win
            j = min(k + 5, hg.K_LAST)
            if win:
                (h if up else l)[j] = ent + sgn * 6.0
            else:
                (l if up else h)[j] = ent - sgn * 9.0
            out.append({'date': d, 'o': o, 'h': h, 'l': l, 'c': c})
        d += timedelta(days=1)
    return out


def test_end_to_end_verdicts_and_splits():
    rng = np.random.default_rng(1)
    days = synth_days(800, rng, 0.62, start=date(2019, 6, 3))   # spans PRE and POST; 62 % wins at +6/-9: gross > 0 but YM S1 costs kill it
    res = hg.run_all(days, 'YM')
    assert res['A']['FULL']['trades'] == 800
    assert res['A']['FULL']['S1']['mean'] < 0 and res['A']['verdict'] == 'REJECTED'
    assert res['A']['FULL']['gross'] > 0
    assert res['A']['POST']['days'] > 0 and res['A']['PRE']['days'] > 0
    assert res['A']['POST']['days'] + res['A']['PRE']['days'] == res['A']['FULL']['days']
    assert all(d >= hg.POST_FROM for d in [x['date'] for x in days][-res['A']['POST']['days']:])
    assert 'YM_literal_9_6' in res and res['overall'] == res['A']['verdict']
    days = synth_days(800, np.random.default_rng(2), 0.97)  # near-certain winner passes (except Bonferroni/control)
    res = hg.run_all(days, 'YM')
    assert res['A']['FULL']['S1']['mean'] > 0.025 and res['A']['FULL']['S1']['ci'][0] > 0


def test_verdict_rules():
    full = {'trades': 400, 'S1': {'mean': 0.05, 'ci': [0.01, 0.09], 'p': 0.001}, 'blocks_pos': 4}
    post = {'S1': {'mean': 0.02}}
    assert hg.verdict(full, post, 0.99) == 'VALIDATED'
    assert hg.verdict(full, post, 0.90) == 'INCONCLUSIVE'
    assert hg.verdict(dict(full, S1=dict(full['S1'], p=0.02)), post, 0.99) == 'INCONCLUSIVE'   # > 0.05/6
    assert hg.verdict(full, {'S1': {'mean': -0.01}}, 0.99) == 'INCONCLUSIVE'
    assert hg.verdict(dict(full, S1=dict(full['S1'], mean=-0.001)), post, 0.99) == 'REJECTED'
    assert hg.verdict(dict(full, trades=299), post, 0.99) == 'INSUFFICIENT-N'


def test_log_budget():
    rng = np.random.default_rng(3)
    res = hg.run_all(synth_days(4300, rng, 0.6), 'YM')
    res['skipped'] = {'incomplete': 999, 'roll': 99}
    n = len(json.dumps(res, separators=(',', ':')))
    assert n < 9000, n
