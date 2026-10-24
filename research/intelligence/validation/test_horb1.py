"""Unit tests for horb1_orb.py on synthetic M1 bars (PREREG_HORB1_NAS100_ORB.md §9). No market data is read."""
from __future__ import annotations

import os
import sys
from datetime import date

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import horb1_orb as h  # noqa: E402


def frame(d: date, bars: dict, base: float = 20000.0, spread_pts: float = 10.0) -> pd.DataFrame:
    """Flat day 09:30-15:59 ET at `base` (spread 1.0 index point = 10 MT5 points), overridden by
    bars[ny_minute] = (o, h, l, c) or (o, h, l, c, spread_points). Server time = New York + 7 h."""
    rows = []
    for m in range(9 * 60 + 30, 16 * 60):
        o = hh = ll = c = base
        sp = spread_pts
        if m in bars:
            v = bars[m]
            o, hh, ll, c = v[:4]
            sp = v[4] if len(v) > 4 else spread_pts
        ts = pd.Timestamp(d) + pd.Timedelta(minutes=m) + pd.Timedelta(hours=7)
        rows.append({'time_server': ts.strftime('%Y-%m-%d %H:%M:%S'), 'open': o, 'high': hh, 'low': ll, 'close': c,
                     'spread': sp, 'time_status': 'OK'})
    return pd.DataFrame(rows)


def up_candle(lo=19990.0, hi=20012.0, o1=20000.0, c1=20010.0) -> dict:
    """First candle 09:30-09:34 rising from o1 to c1 with extremes lo/hi."""
    b = {570: (o1, o1 + 1, lo, o1 + 1)}
    for m in (571, 572, 573):
        b[m] = (o1 + 1, o1 + 2, o1, o1 + 2)
    b[574] = (o1 + 2, hi, o1 + 2, c1)
    return b


D0 = date(2024, 7, 1)   # summer (EDT)


def test_placebo_times_are_twenty_and_exclude_open_window():
    t = h.placebo_times()
    assert len(t) == 20
    assert all(not (510 <= x <= 630) for x in t)
    assert t[0] == 180 and t[-1] == 900


@pytest.mark.parametrize('d,utc_hhmm', [(date(2024, 7, 1), '13:30'), (date(2024, 1, 2), '14:30'),
                                        (date(2024, 3, 12), '13:30'),    # US already EDT, EU still winter
                                        (date(2024, 10, 29), '13:30'),   # EU back to winter, US still EDT
                                        (date(2024, 11, 4), '14:30')])
def test_ny_clock_maps_to_utc_across_dst(d, utc_hhmm):
    u = h.utc_of(d, h.OPEN_MIN)
    assert pd.Timestamp(u, unit='m').strftime('%H:%M') == utc_hhmm
    D = h.from_frame(frame(d, {}))
    assert D.at(u) >= 0                        # server = NY + 7 h lands on the same bar


def test_doji_is_no_trade():
    b = up_candle(c1=20000.0)                  # C1 == O1 at 0.1 precision
    D = h.from_frame(frame(D0, b))
    assert h.simulate(D, D0)['status'] == 'doji'


def test_long_target_hit_and_r_definition():
    b = up_candle(lo=19990.0)
    b[575] = (20010.0, 20011.0, 20009.0, 20010.0)          # entry bar open 20010, ask = 20011
    b[600] = (20010.0, 20300.0, 20010.0, 20250.0)          # rally through the target
    D = h.from_frame(frame(D0, b))
    r = h.simulate(D, D0)
    assert r['status'] == 'trade' and r['dir'] == 1
    assert r['R0'] == pytest.approx(20011.0 - 19990.0)     # entry ask - L1
    assert r['exit'] == 'target'
    assert r['R'] == pytest.approx(10.0)                   # S0: target fill exactly 10R


def test_stress_is_applied_per_side():
    b = up_candle(lo=19990.0)
    b[575] = (20010.0, 20011.0, 20009.0, 20010.0)
    b[600] = (20010.0, 20300.0, 20010.0, 20250.0)
    D = h.from_frame(frame(D0, b))
    r = h.simulate(D, D0, stress=0.5)
    assert r['pnl_pts'] == pytest.approx(10 * 21.0 - 1.0)  # 0.5 in + 0.5 out


def test_long_stop_gap_fills_at_open():
    b = up_candle(lo=19990.0)
    b[575] = (20010.0, 20011.0, 20005.0, 20006.0)
    b[576] = (19980.0, 19981.0, 19970.0, 19975.0)          # gaps below the 19990 stop
    D = h.from_frame(frame(D0, b))
    r = h.simulate(D, D0)
    assert r['exit'] == 'stop'
    assert r['pnl_pts'] == pytest.approx(19980.0 - 20011.0)


def test_same_bar_stop_and_target_counts_as_stop():
    b = up_candle(lo=19990.0)
    b[575] = (20010.0, 20011.0, 20009.0, 20010.0)
    b[577] = (20010.0, 20300.0, 19900.0, 20000.0)          # touches both
    D = h.from_frame(frame(D0, b))
    r = h.simulate(D, D0)
    assert r['exit'] == 'stop' and r['R'] == pytest.approx(-1.0)


def test_short_uses_ask_for_stop_and_time_exit():
    b = {570: (20000.0, 20001.0, 19998.0, 19999.0), 571: (19999.0, 20002.0, 19997.0, 19998.0),
         572: (19998.0, 19999.0, 19996.0, 19997.0), 573: (19997.0, 19998.0, 19994.0, 19995.0),
         574: (19995.0, 19996.0, 19990.0, 19991.0)}       # down candle, H1 = 20002
    b[575] = (19991.0, 19992.0, 19989.0, 19990.0)          # short entry at bid 19991
    b[600] = (19990.0, 20001.5, 19985.0, 19990.0)          # ask high 20002.5 >= stop 20002 -> stop
    D = h.from_frame(frame(D0, b, base=19990.0))
    r = h.simulate(D, D0)
    assert r['dir'] == -1 and r['exit'] == 'stop'
    assert r['R0'] == pytest.approx(20002.0 - 19991.0)
    b[600] = (19990.0, 20000.0, 19985.0, 19990.0)          # ask high 20001 < stop -> held to 15:59
    D = h.from_frame(frame(D0, b, base=19990.0))
    r = h.simulate(D, D0)
    assert r['exit'] == 'time'
    assert r['pnl_pts'] == pytest.approx(19991.0 - (19990.0 + 1.0))   # buy back at the ask


def test_cost_floor_skip():
    b = {570: (20009.0, 20010.0, 20008.0, 20010.0), 571: (20010.0, 20011.0, 20009.0, 20011.0),
         572: (20010.0, 20011.0, 20009.0, 20011.0), 573: (20010.0, 20011.0, 20009.0, 20011.0),
         574: (20011.0, 20012.0, 20010.0, 20012.0)}       # L1 = 20008; entry ask 20011 -> R0 = 3 pts
    b[575] = (20010.0, 20011.0, 20009.0, 20010.0)
    D = h.from_frame(frame(D0, b))
    assert h.simulate(D, D0)['status'] == 'cost_floor'     # 1.0 > 0.2 * 3


def test_missing_required_bar():
    f = frame(D0, up_candle())
    f = f[~f.time_server.str.endswith('16:32:00')]          # 09:32 ET bar removed
    D = h.from_frame(f)
    assert h.simulate(D, D0)['status'] == 'missing'


def test_flip_keeps_distance_and_reverses_direction():
    b = up_candle(lo=19990.0)
    b[575] = (20010.0, 20011.0, 20009.0, 20010.0)
    D = h.from_frame(frame(D0, b))
    r = h.simulate(D, D0, flip=True)
    assert r['dir'] == -1 and r['R0'] == pytest.approx(21.0)


def test_calendar_excludes_holidays_and_outside_coverage():
    f = pd.concat([frame(date(2024, 7, 3), {}), frame(date(2024, 7, 4), {}), frame(date(2024, 7, 5), {})])
    D = h.from_frame(f)
    days, aud = h.eligible_days(D, {date(2024, 7, 3), date(2024, 7, 4)}, None, None,
                                date(2017, 1, 1), date(2026, 12, 31))
    assert days == [date(2024, 7, 5)] and aud['holiday_or_early_close'] == 2
    days, aud = h.eligible_days(D, set(), None, None, date(2025, 1, 1), date(2026, 12, 31))
    assert days == [] and aud['outside_calendar'] == 3


def test_frozen_calendar_marks_known_closures():
    hol, lo, hi = h.calendar()
    assert date(2024, 7, 4) in hol and date(2024, 3, 29) in hol      # Independence Day, Good Friday
    assert date(2024, 11, 29) in hol                                  # early close after Thanksgiving


def test_acceptance_insufficient_and_rejected():
    def H(n, m0, m1):
        return {'S1': {'counts': {'trade': n}, 'mean_R': {'theta': m1, 'ci95': [m1 - 0.1, m1 + 0.1],
                                                           'p_one_sided': 0.5}},
                'S0': {'counts': {'trade': n}, 'mean_R': {'theta': m0}}, 'N1_placebo': {'p_tod': 0.5},
                'year_check_S1': {}, 'secondaries_S1': {}, 'DSR': {}, 'cost_check': {}}
    assert h.acceptance(None, H(100, 0.2, 0.2))['verdict'] == 'INSUFFICIENT-N'
    assert h.acceptance(None, H(400, -0.1, -0.1))['verdict'] == 'REJECTED'
    assert h.acceptance(None, H(400, 0.1, 0.05))['verdict'] == 'INCONCLUSIVE'
