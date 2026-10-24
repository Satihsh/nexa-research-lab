"""Unit tests for fx1_fix_reversals.py (PREREG_FX1 §9). Synthetic data and calendar arithmetic only; no market outcomes."""
import os
import sys
from datetime import date

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fx1_fix_reversals as fx  # noqa: E402


def hm(u):
    return (u % 1440) // 60, u % 60


def test_fix_clocks_dst():
    # Tokyo has no DST: 09:55 JST = 00:55 UTC all year
    assert hm(fx.window('W1', date(2026, 1, 15))[0]) == (0, 55) and hm(fx.window('W1', date(2026, 7, 15))[0]) == (0, 55)
    # W1 end / W2 start 08:00 Berlin: 07:00 UTC winter, 06:00 UTC summer
    assert hm(fx.window('W1', date(2026, 1, 15))[1]) == (7, 0) and hm(fx.window('W2', date(2026, 7, 15))[0]) == (6, 0)
    # ECB 14:15 Berlin: 13:15 UTC winter, 12:15 UTC summer
    assert hm(fx.window('W2', date(2026, 1, 15))[1]) == (13, 15) and hm(fx.window('W2', date(2026, 7, 15))[1]) == (12, 15)
    # London 16:00 -> NY 16:55: winter 16:00 -> 21:55 UTC, summer 15:00 -> 20:55 UTC (355 min both)
    for d in (date(2026, 1, 15), date(2026, 7, 15)):
        a, b = fx.window('W3', d)
        assert b - a == 355
    assert hm(fx.window('W3', date(2026, 1, 15))[0]) == (16, 0) and hm(fx.window('W3', date(2026, 7, 15))[1]) == (20, 55)


def test_dst_mismatch_weeks():
    # 2026-03-10: US on EDT, UK/EU still on standard time -> W3 = 16:00 UTC -> 20:55 UTC (295 min)
    a, b = fx.window('W3', date(2026, 3, 10))
    assert hm(a) == (16, 0) and hm(b) == (20, 55) and b - a == 295
    # 2026-10-28: UK/EU back on GMT/CET, US still EDT (ends Nov 1) -> 295 min again; W2 08:00 CET = 07:00 UTC
    a, b = fx.window('W3', date(2026, 10, 28))
    assert b - a == 295 and hm(fx.window('W2', date(2026, 10, 28))[0]) == (7, 0)


def test_all_windows_inside_server_day():
    for d in (date(2026, 1, 12), date(2026, 3, 10), date(2026, 7, 15), date(2026, 10, 28), date(2025, 11, 3)):
        for w in fx.WINS:
            a, b = fx.window(w, d)
            assert fx.server_day_of_utc(a) == d and fx.server_day_of_utc(b - 1) == d, (w, d)


def test_directions_follow_paper_sign():
    for (w, s), p in fx.PAPER.items():
        foreign_up = 1 if p > 0 else -1
        expected = -foreign_up if s == 'USDJPY' else foreign_up          # USDJPY up = yen down
        assert fx.DIRECTION[(w, s)] == expected, (w, s)


def test_calendars():
    t = {x for y in (2024, 2025) for x in fx.target_closed(y)}
    assert {date(2024, 3, 29), date(2024, 4, 1), date(2024, 5, 1), date(2024, 12, 26), date(2025, 4, 18)} <= t
    c = fx.build_calendars()
    assert '2026-09-22' in c['tokyo_closed'] and '2025-01-02' in c['tokyo_closed']
    assert set(c['wmr_closed']) >= {'2025-12-25', '2026-01-01'} and '2025-12-26' not in c['wmr_closed']


def test_placebo_offsets_and_rollover():
    o = fx.placebo_offsets()
    assert len(o) == 41 and min(o) == -720 and max(o) == 690 and all(abs(x) > 90 for x in o)
    a, b = fx.window('W3', date(2026, 1, 15))
    assert fx.touches_rollover(a + 120, b + 120) and not fx.touches_rollover(a - 120, b - 120)
    a, b = fx.window('W1', date(2026, 1, 15))                    # 19:55 ET -> 02:00 ET
    assert fx.touches_rollover(a - 180, b - 180)                  # 16:55 ET start touches
    assert not fx.touches_rollover(a, b)


class FakeS:
    def __init__(self):
        self.sprd = np.array([0.00001])


class FakeB:
    def __init__(self, o, h, l, c):
        self.o, self.h, self.l, self.c = map(np.asarray, (o, h, l, c))
        self.S = FakeS()


def test_trade_costs_stop_floor():
    n = 10
    o = np.linspace(1.1000, 1.1009, n); c = o + 0.0001
    B = FakeB(o, np.maximum(o, c), np.minimum(o, c), c)
    t = fx.trade('EURUSD', B, 0, n - 1, +1, spread=0.00002, sig=0.001)
    pnl = c[-1] - (1.1000 + 0.00002)
    assert t['exit'] == 'time' and abs(t['pnl'] - pnl) < 1e-12
    assert abs(fx.net_bp(t, 'S1') - (pnl - 0.00007 - 2 * 0.25e-4 * 1.1) / 1.1 * 1e4) < 1e-9
    assert abs(t['gross_bp'] - (c[-1] - 1.1) / 1.1 * 1e4) < 1e-9
    h = np.maximum(o, c).copy(); h[4] = 1.1100                    # short stopped (4 sigma ~ 44 pips)
    t2 = fx.trade('EURUSD', FakeB(o, h, np.minimum(o, c), c), 0, n - 1, -1, spread=0.00002, sig=0.001)
    assert t2['exit'] == 'stop' and abs(t2['pnl'] + 4 * 0.001 * 1.1) < 1e-9
    assert fx.trade('EURUSD', B, 0, n - 1, +1, spread=0.0002, sig=0.00001).get('skip')


if __name__ == '__main__':
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for f in fns:
        f()
        print('PASS', f.__name__)
    print(f'{len(fns)}/{len(fns)} PASS')
