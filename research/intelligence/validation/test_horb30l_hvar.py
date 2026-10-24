"""Unit tests for horb30l_nq.py and hvar_nq.py on synthetic 1-min bars (PREREG_HORB30L_NQ §9, PREREG_HVAR_NQ §9).
No market data is read."""
from __future__ import annotations

import os
import sys
from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import horb30l_nq as orb  # noqa: E402
import hvar_nq as hv  # noqa: E402
import hivb1_nq as iv  # noqa: E402

D0 = date(2024, 7, 1)


def rows(d: date, bars: dict, base: float = 20000.0, vol: float = 10.0, start=9 * 60 + 30, end=16 * 60,
         drop=()) -> list:
    out = []
    for m in range(start, end):
        if m in drop:
            continue
        o = h = l = c = base
        v = vol
        if m in bars:
            x = bars[m]
            o, h, l, c = x[:4]
            v = x[4] if len(x) > 4 else vol
        ts = pd.Timestamp(d) + pd.Timedelta(minutes=m) + pd.Timedelta(hours=7)
        out.append({'time_server': ts.strftime('%Y-%m-%d %H:%M:%S'), 'open': o, 'high': h, 'low': l, 'close': c,
                    'volume': v})
    return out


def dv(r: list):
    return iv.from_frame(pd.DataFrame(r))


def orb_range() -> dict:
    return {m: (20000.0, 20010.0, 19990.0, 20000.0) for m in range(570, 600)}       # A = 20010, B = 19990


# ----------------------------------------------------------------------------- H-ORB30L-NQ
def test_orb_placebos_and_deadline():
    a = orb.placebo_anchors()
    assert len(a) == 19 and 570 not in a
    assert orb.placebo_deadline(150) == 270 and orb.placebo_deadline(840) == 900


def test_orb_long_breakout_hits_1R_target():
    b = orb_range()
    b |= {m: (20012.0, 20016.0, 20011.0, 20015.0) for m in range(600, 605)}          # 5-min close 20015 > A
    b[605] = (20015.0, 20016.0, 20014.0, 20015.0)                                        # entry bar (open 20015)
    b[610] = (20030.0, 20041.0, 20029.0, 20040.0)                                        # 1R target 20040 + tick
    t = orb.simulate(dv(rows(D0, b, base=20015.0)), D0, cost=2.0)
    assert t['status'] == 'trade' and t['entry_min'] == 605 and t['exit_kind'] == 'target'
    assert t['R_pts'] == pytest.approx(25.0) and t['R'] == pytest.approx(23.0 / 25.0)


def test_orb_deadline_1130_inclusive():
    b = orb_range() | {m: (20000.0, 20009.0, 19995.0, 20000.0) for m in range(600, 685)}
    b |= {m: (20012.0, 20016.0, 20011.0, 20015.0) for m in range(685, 690)}            # candle 11:25-11:29
    assert orb.setup(dv(rows(D0, b)), D0)['entry_min'] == 690
    b2 = orb_range() | {m: (20000.0, 20009.0, 19995.0, 20000.0) for m in range(600, 690)}
    b2 |= {m: (20012.0, 20016.0, 20011.0, 20015.0) for m in range(690, 695)}           # candle 11:30-11:34
    assert orb.setup(dv(rows(D0, b2)), D0)['status'] == 'no_breakout'


def test_orb_gap_stop_and_same_bar_priority():
    b = orb_range() | {m: (20012.0, 20016.0, 20011.0, 20015.0) for m in range(600, 606)}
    b[606] = (19980.0, 19981.0, 19979.0, 19980.0)                                        # opens below B
    t = orb.simulate(dv(rows(D0, b, base=20015.0)), D0, cost=0.0)
    assert t['exit_kind'] == 'stop' and t['exit'] == pytest.approx(19980.0)
    b[606] = (20015.0, 20045.0, 19985.0, 20015.0)                                        # stop and target same bar
    t = orb.simulate(dv(rows(D0, b, base=20015.0)), D0, cost=0.0)
    assert t['exit_kind'] == 'stop' and t['exit'] == pytest.approx(19990.0)


def test_orb_entry_bar_checks_stop_only_and_time_exit():
    b = orb_range() | {m: (20012.0, 20016.0, 20011.0, 20015.0) for m in range(600, 605)}
    b[605] = (20015.0, 20060.0, 20014.0, 20015.0)                                        # target touched on entry bar
    t = orb.simulate(dv(rows(D0, b, base=20015.0)), D0, cost=0.0)
    assert t['exit_kind'] == 'time' and t['exit'] == pytest.approx(20015.0)


def test_orb_cost_floor_missing_and_n2():
    b = {m: (20000.0, 20002.0, 19998.0, 20000.0) for m in range(570, 600)}
    b |= {m: (20003.0, 20004.0, 20002.0, 20003.0) for m in range(600, 606)}
    assert orb.simulate(dv(rows(D0, b, base=20003.0)), D0)['status'] == 'cost_floor'
    assert orb.simulate(dv(rows(D0, orb_range(), drop=(580,))), D0)['status'] == 'missing'
    assert orb.simulate(dv(rows(D0, orb_range(), drop=(929,))), D0)['status'] == 'missing'
    n2 = orb.simulate(dv(rows(D0, orb_range(), base=20005.0)), D0, n2=True, cost=0.0)
    assert n2['status'] == 'trade' and n2['entry_min'] == 600 and n2['R_pts'] == pytest.approx(15.0)


# ----------------------------------------------------------------------------- H-VAR-NQ
PREV = date(2024, 6, 28)


def prev_bars() -> dict:
    return {m: (20000.0, 20010.0, 19990.0, 20000.0, 100.0) for m in range(570, 960)}


def va():
    b = prev_bars()
    ms = sorted(b)
    return iv.profile(np.array([b[m][1] for m in ms]), np.array([b[m][2] for m in ms]), np.array([b[m][4] for m in ms]))


def two_days(today: dict, base: float):
    r = rows(PREV, prev_bars()) + rows(D0, today, base=base)
    D = dv(r)
    days = [PREV, D0]
    return D, days, hv.build_sessions(D, days)


def test_var_long_acceptance_target():
    val, vah, poc = va()
    entry = val + 2.0
    today = {570: (val - 20, val + 1, val - 30, val + 1)}                                # opens below value
    today[640] = (entry, vah + 1.0, entry - 1, vah)                                      # traverses to VAH
    D, days, sess = two_days(today, entry)
    S = hv.setup(D, days, 1, sess)
    assert S['status'] == 'ok' and S['dir'] == 1 and S['signal'] == 630 and S['stop'] == pytest.approx(val - 30)
    t = hv.simulate(D, days, 1, sess, cost=2.0)
    assert t['exit_kind'] == 'target' and t['R_pts'] == pytest.approx(32.0)
    assert t['pnl_pts'] == pytest.approx(vah - entry - 2.0)


def test_var_short_inside_open_and_no_acceptance():
    val, vah, poc = va()
    D, days, sess = two_days({570: (vah + 20, vah + 30, vah - 1, vah - 1)}, vah - 2.0)
    assert hv.setup(D, days, 1, sess)['dir'] == -1
    D, days, sess = two_days({}, (val + vah) / 2)
    assert hv.setup(D, days, 1, sess)['status'] == 'inside_open'
    D, days, sess = two_days({}, val - 40.0)                                              # never back inside
    assert hv.setup(D, days, 1, sess)['status'] == 'no_acceptance'


def test_var_deadline_and_one_period_variant():
    val, vah, poc = va()
    today = {m: (val - 40, val - 39, val - 41, val - 40) for m in range(570, 660)}        # outside until 11:00
    D, days, sess = two_days(today, val + 2.0)                                            # inside 11:00-11:59
    assert hv.setup(D, days, 1, sess)['status'] == 'no_acceptance'                       # 12:00 > 11:30
    assert hv.setup(D, days, 1, sess, deadline=15 * 60 + 30)['signal'] == 720
    assert hv.setup(D, days, 1, sess, n_inside=1)['signal'] == 690


def test_var_stale_lag_uses_older_session():
    d3 = [date(2024, 6, 27), PREV, D0]
    other = {m: (20100.0, 20110.0, 20090.0, 20100.0, 100.0) for m in range(570, 960)}
    r = rows(d3[0], other) + rows(PREV, prev_bars()) + rows(D0, {}, base=20050.0)
    D = dv(r)
    sess = hv.build_sessions(D, d3)
    assert hv.setup(D, d3, 2, sess, lag=2)['status'] in ('ok', 'no_acceptance')
    assert hv.setup(D, d3, 2, sess, lag=2)['VAL'] > 20080
    assert hv.setup(D, d3, 2, sess, lag=1)['VAL'] < 20000


def test_dalton_conditions_need_history():
    days, r, d = [], [], date(2024, 1, 2)
    while len(days) < 23:
        if d.weekday() < 5:
            px = 20000.0 + 10 * len(days)
            r += rows(d, {m: (px, px + 10, px - 10, px, 100.0) for m in range(570, 960)}, base=px)
            days.append(d)
        d += timedelta(days=1)
    D = dv(r)
    sess = hv.build_sessions(D, days)
    c = hv.dalton_conditions(D, days, sess)
    assert c[5] == (None, None, None)                                                     # too little history
    assert c[22][2] == 1.0 and c[22][1] is False                                         # rising closes, equal widths


# ----------------------------------------------------------------------------- pipeline smoke (synthetic only)
def _walk(n: int, start: int):
    rng = np.random.default_rng(11)
    out, days, d = [], [], date(2024, 1, 2)
    while len(days) < n:
        if d.weekday() < 5:
            px, bars = 20000.0, {}
            for m in range(start, 16 * 60):
                c = px + float(rng.normal(0, 4))
                bars[m] = (px, max(px, c) + 1.0, min(px, c) - 1.0, c, float(rng.integers(50, 500)))
                px = c
            out += rows(d, bars, start=start)
            days.append(d)
        d += timedelta(days=1)
    return dv(out), days


def test_orb_analyse_end_to_end():
    D, days = _walk(25, 2 * 60 + 30)
    H = orb.analyse(D, days, set())
    H['acceptance'] = orb.acceptance(H)
    assert H['N1_placebo']['n_anchors'] == 19 and H['DSR'].get('n_series') == 22
    assert H['acceptance']['verdict'] == 'INSUFFICIENT-N'


def test_var_analyse_end_to_end():
    D, days = _walk(30, 9 * 60 + 30)
    H = hv.analyse(D, days, set())
    H['acceptance'] = hv.acceptance(H)
    assert H['N1_stale_value']['n_placebos'] == 19 and H['DSR'].get('n_series') == 25
    assert H['acceptance']['verdict'] == 'INSUFFICIENT-N'
