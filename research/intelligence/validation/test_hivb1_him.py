"""Unit tests for hivb1_nq.py and him_nq.py on synthetic 1-min bars (PREREG_HIVB1_NQ §9, PREREG_HIM_NQ §9).
No market data is read."""
from __future__ import annotations

import os
import sys
from datetime import date

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hivb1_nq as iv  # noqa: E402
import him_nq as im  # noqa: E402
import of_common as oc  # noqa: E402

D0 = date(2024, 7, 1)


def rows(d: date, bars: dict, base: float = 20000.0, vol: float = 10.0, start=9 * 60 + 30, end=16 * 60) -> list:
    out = []
    for m in range(start, end):
        o = h = l = c = base
        v = vol
        if m in bars:
            x = bars[m]
            o, h, l, c = x[:4]
            v = x[4] if len(x) > 4 else vol
        ts = pd.Timestamp(d) + pd.Timedelta(minutes=m) + pd.Timedelta(hours=7)
        out.append({'time_server': ts.strftime('%Y-%m-%d %H:%M:%S'), 'open': o, 'high': h, 'low': l, 'close': c,
                    'volume': v, 'spread': 0, 'time_status': 'OK'})
    return out


def range_bars() -> dict:
    """09:30-09:59: wide uniform bars 19980-20020 plus a heavy bar at 20000 (POC)."""
    b = {m: (20000.0, 20020.0, 19980.0, 20000.0, 161.0) for m in range(570, 600)}
    b[585] = (20000.0, 20000.0, 20000.0, 20000.0, 3000.0)
    return b


def levels():
    b = range_bars()
    ms = sorted(b)
    return iv.profile(np.array([b[m][1] for m in ms]), np.array([b[m][2] for m in ms]), np.array([b[m][4] for m in ms]))


# ----------------------------------------------------------------------------- H-IVB1-NQ
def test_placebo_anchor_count():
    a = iv.placebo_anchors()
    assert len(a) == 19 and a[0] == 150 and a[-1] == 840 and not any(510 <= x <= 630 for x in a)


def test_profile_uniform_spread_against_hand_calc():
    val, vah, poc = iv.profile(np.array([100.5, 100.5]), np.array([100.0, 100.5]), np.array([30.0, 20.0]))
    assert poc == pytest.approx(100.5)        # 10 + 20 = 30 at 100.5; 10 each at 100.0, 100.25
    assert val == pytest.approx(100.0) and vah == pytest.approx(100.75)


def test_profile_matches_va_greedy_indices():
    val, vah, poc = levels()
    assert poc == pytest.approx(20000.0)
    assert val < poc < vah and (vah - val) >= iv.MIN_R


def _day(post: dict):
    b = range_bars() | post
    return iv.from_frame(pd.DataFrame(rows(D0, b)))


def test_long_breakout_fill_target():
    val, vah, poc = levels()
    R = vah - val
    post = {m: (20025.0, 20026.0, 20024.0, 20025.0) for m in range(600, 605)}          # 5-min close > A = 20020
    post |= {m: (20025.0, 20026.0, 20024.0, 20025.0) for m in range(605, 610)}
    post[610] = (20020.0, 20021.0, vah - 0.5, vah)                                      # retrace fills at VAH
    post |= {m: (vah + 1, vah + 2, vah + 0.5, vah + 1.5) for m in range(611, 620)}
    post[620] = (vah + 2, vah + 2 * R + 1, vah + 1, vah + 2 * R)                         # target hit
    D = _day(post)
    r = iv.simulate(D, D0, cost=2.0)
    assert r['status'] == 'trade' and len(r['trades']) == 1
    t = r['trades'][0]
    assert t['dir'] == 1 and t['exit'] == 'target'
    assert t['R'] == pytest.approx((2 * R - 2.0) / R)


def test_invalidation_on_5min_close():
    val, vah, poc = levels()
    R = vah - val
    post = {m: (20025.0, 20026.0, 20024.0, 20025.0) for m in range(600, 610)}
    post[610] = (20020.0, 20021.0, vah - 0.5, vah)
    post |= {m: (val - 1, val, val - 2, val - 1) for m in range(611, 615)}               # candle 10:10-10:14 closes < VAL
    D = _day(post)
    t = iv.simulate(D, D0, cost=0.0)['trades'][0]
    assert t['exit'] == 'invalidation' and t['pnl_pts'] == pytest.approx((val - 1) - vah)


def test_hard_stop_and_same_bar_priority():
    val, vah, poc = levels()
    R = vah - val
    post = {m: (20025.0, 20026.0, 20024.0, 20025.0) for m in range(600, 610)}
    post[610] = (20020.0, 20021.0, vah - 0.5, vah)
    post[611] = (vah, vah + 2 * R + 5, 19970.0, vah)                                     # touches stop (B=19980) and target
    D = _day(post)
    t = iv.simulate(D, D0, cost=0.0)['trades'][0]
    assert t['exit'] == 'stop' and t['pnl_pts'] == pytest.approx(19980.0 - vah)


def test_no_breakout_and_no_fill():
    D = _day({})
    assert iv.simulate(D, D0)['status'] == 'no_breakout'
    post = {m: (20030.0, 20031.0, 20029.0, 20030.0) for m in range(600, 960)}             # breaks out, never retraces
    D = _day(post)
    assert iv.simulate(D, D0)['status'] == 'no_fill'


def test_cost_floor_on_narrow_value_area():
    b = {m: (20000.0, 20001.0, 19999.0, 20000.0, 10.0) for m in range(570, 600)}
    b[585] = (20000.0, 20000.0, 20000.0, 20000.0, 5000.0)
    post = {m: (20005.0, 20006.0, 20004.0, 20005.0) for m in range(600, 605)}
    D = iv.from_frame(pd.DataFrame(rows(D0, b | post)))
    assert iv.simulate(D, D0)['status'] == 'cost_floor'


def test_short_mirror_and_fade_trigger():
    val, vah, poc = levels()
    R = vah - val
    post = {m: (19975.0, 19976.0, 19974.0, 19975.0) for m in range(600, 610)}           # close < B = 19980 -> short
    post[610] = (19980.0, val + 0.5, 19979.0, val)                                        # retrace up, fills at VAL
    D = _day(post)
    t = iv.simulate(D, D0, cost=0.0)['trades'][0]
    assert t['dir'] == -1 and t['exit'] == 'time'
    f = iv.simulate(D, D0, cost=0.0, fade=True)['trades'][0]
    assert f['dir'] == 1 and f['fill_min'] == 610                                         # same retrace touch


def test_missing_range_bar():
    r = rows(D0, range_bars())
    r = [x for x in r if not x['time_server'].endswith('16:40:00')]                       # 09:40 ET removed
    assert iv.simulate(iv.from_frame(pd.DataFrame(r)), D0)['status'] == 'missing'


# ----------------------------------------------------------------------------- H-IM-NQ
def test_im_placebo_count():
    p = im.placebo_ends()
    assert len(p) == 20 and p[0] == 630 and p[-1] == 915


def test_im_long_signal_trade_and_prev_weekday():
    fri, mon = date(2024, 6, 28), date(2024, 7, 1)
    assert im.prev_weekday(mon) == fri
    r = rows(fri, {959: (19990.0, 19991.0, 19989.0, 20000.0)})                           # previous close 20000
    r += rows(mon, {929: (20100.0, 20101.0, 20099.0, 20100.0),                           # r > 0 -> long
                    930: (20101.0, 20102.0, 20100.0, 20101.0),
                    959: (20110.0, 20111.0, 20109.0, 20120.0)}, base=20105.0)
    D = im.hb.from_frame(pd.DataFrame(r))
    t = im.trade(D, mon, fri, cost=2.0)
    assert t['dir'] == 1 and t['gross_pts'] == pytest.approx(20120.0 - 20101.0)
    assert t['net_pts'] == pytest.approx(17.0)


def test_im_short_and_zero_signal_and_dst():
    a, b = date(2024, 3, 8), date(2024, 3, 11)                                           # US DST starts 2024-03-10
    r = rows(a, {959: (100.0, 100.0, 100.0, 100.0)}, base=100.0)
    r += rows(b, {929: (99.0, 99.0, 99.0, 99.0), 930: (99.0, 99.0, 99.0, 99.0),
                  959: (98.0, 98.0, 98.0, 98.0)}, base=99.0)
    D = im.hb.from_frame(pd.DataFrame(r))
    t = im.trade(D, b, a, cost=0.0)
    assert t['dir'] == -1 and t['gross_pts'] == pytest.approx(1.0)
    r2 = rows(a, {959: (100.0, 100.0, 100.0, 100.0)}, base=100.0) + rows(b, {929: (100.0, 100.0, 100.0, 100.0)},
                                                                         base=100.0)
    assert im.trade(im.hb.from_frame(pd.DataFrame(r2)), b, a)['status'] == 'zero_signal'


def test_im_pairs_need_eligible_previous_day():
    days = [date(2024, 7, 1), date(2024, 7, 2), date(2024, 7, 5)]                       # 07-03/04 not eligible
    assert im.pairs(days) == [(date(2024, 7, 2), date(2024, 7, 1))]


# ----------------------------------------------------------------------------- pipeline smoke (synthetic only)
def _walk_days(n: int = 30, start=2 * 60 + 30):
    rng = np.random.default_rng(7)
    out, days, d = [], [], date(2024, 1, 2)
    while len(days) < n:
        if d.weekday() < 5:
            px, bars = 20000.0, {}
            for m in range(start, 16 * 60):
                step = float(rng.normal(0, 4))
                o, c = px, px + step
                bars[m] = (o, max(o, c) + 1.0, min(o, c) - 1.0, c, float(rng.integers(50, 500)))
                px = c
            out += rows(d, bars, start=start)
            days.append(d)
        d = date.fromordinal(d.toordinal() + 1)
    return pd.DataFrame(out), days


def test_ivb_analyse_and_acceptance_run_end_to_end():
    df, days = _walk_days()
    H = iv.analyse(iv.from_frame(df), days, set())
    H['acceptance'] = iv.acceptance(H)
    assert H['N1_placebo']['n_anchors'] == 19 and 'error' not in H['DSR']
    assert H['acceptance']['verdict'] == 'INSUFFICIENT-N'


def test_im_analyse_and_acceptance_run_end_to_end():
    df, days = _walk_days(start=9 * 60 + 30)
    H = im.analyse(im.hb.from_frame(df), im.pairs(days), set())
    H['acceptance'] = im.acceptance(H)
    assert H['N1_placebo']['n_placebos'] == 20 and 'error' not in H['DSR']
    assert H['acceptance']['verdict'] == 'INSUFFICIENT-N'
