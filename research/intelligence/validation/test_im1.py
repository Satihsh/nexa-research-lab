"""Unit tests for im1_intraday_momentum.py (PREREG_IM1 §9). Synthetic data only; no market outcomes."""
import os
import sys
from datetime import date

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import im1_intraday_momentum as im  # noqa: E402


class FakeS:
    def __init__(self, days, sprd):
        self.days, self.sprd, self.sym = days, sprd, 'EURUSD'


class FakeB:
    """Bars at chosen UTC minutes with given OHLC."""
    def __init__(self, rows, days, sprd=0.00001):
        rows = sorted(rows)
        self.utc = np.array([r[0] for r in rows], np.int64)
        self.o = np.array([r[1] for r in rows]); self.h = np.array([r[2] for r in rows])
        self.l = np.array([r[3] for r in rows]); self.c = np.array([r[4] for r in rows])
        self.sday = np.zeros(len(rows), np.int64)
        self.S = FakeS(days, np.array([sprd]))

    def at(self, m):
        k = int(np.searchsorted(self.utc, m))
        return k if k < len(self.utc) and self.utc[k] == m else -1


def window(d, C, p0, p1, extra=None):
    """30 one-minute bars from C-30 to C-1 drifting p0 -> p1, plus the bar starting at C-31 closing at p0."""
    rows = [(im.utc_min(d, C - 31), p0, p0, p0, p0)]
    for j in range(30):
        px = p0 + (p1 - p0) * (j + 1) / 30
        rows.append((im.utc_min(d, C - 30 + j), p0 + (p1 - p0) * j / 30, max(px, p0), min(px, p0), px))
    return rows + (extra or [])


def test_close_mapping_est_edt():
    assert im.utc_min(date(2026, 1, 15), 15 * 60) % 1440 == 20 * 60      # EST: 15:00 ET = 20:00 UTC
    assert im.utc_min(date(2026, 7, 15), 15 * 60) % 1440 == 19 * 60      # EDT: 15:00 ET = 19:00 UTC
    assert im.utc_min(date(2026, 1, 15), 13 * 60 + 30) % 1440 == 18 * 60 + 30


def test_placebo_count_and_exclusion():
    for C in (15 * 60, 13 * 60 + 30):
        p = im.placebo_closes(C)
        assert len(p) == 33 and all(abs(t - C) > 75 for t in p) and min(p) == 360 and max(p) <= 16 * 60 + 45


def test_good_friday():
    assert im.easter(2024) == date(2024, 3, 31) and im.easter(2025) == date(2025, 4, 20)


def test_trade_long_costs_and_time_exit():
    d, C = date(2026, 1, 15), 15 * 60
    B = FakeB(window(d, C, 1.1000, 1.1010), [d.isoformat()])
    t = im.trade('EURUSD', B, d, C, +1, spread=0.00002, sig=0.001, stress_bp=0.25)
    # entry at open of C-30 bar (1.1000) + spread; exit at close of C-1 bar (1.1010)
    pnl = 1.1010 - (1.1000 + 0.00002)
    net = pnl - 0.00007 - 2 * 0.25e-4 * 1.1000
    assert abs(t['net_bp'] - net / 1.1000 * 1e4) < 1e-9 and t['exit'] == 'time'
    assert abs(t['gross_bp'] - (1.1010 - 1.1000) / 1.1000 * 1e4) < 1e-9


def test_trade_short_stop_fill():
    d, C = date(2026, 1, 15), 15 * 60
    rows = window(d, C, 1.1000, 1.1000)
    rows = [r for r in rows if r[0] != im.utc_min(d, C - 20)] + [(im.utc_min(d, C - 20), 1.1000, 1.1100, 1.1000, 1.1050)]
    B = FakeB(rows, [d.isoformat()])
    t = im.trade('EURUSD', B, d, C, -1, spread=0.00002, sig=0.001, stress_bp=0.0, stop_k=4.0)
    assert t['exit'] == 'stop' and t['R'] < -0.9          # stopped at 4 sigma (~44 pips) above entry


def test_cost_floor_skip():
    d, C = date(2026, 1, 15), 15 * 60
    B = FakeB(window(d, C, 1.1000, 1.1010), [d.isoformat()])
    assert im.trade('EURUSD', B, d, C, +1, spread=0.0002, sig=0.00001, stress_bp=0.0).get('skip')


def test_rod_anchor_across_weekend_and_sign():
    thu, fri, mon, C = date(2026, 1, 8), date(2026, 1, 9), date(2026, 1, 12), 15 * 60
    rows = window(thu, C, 1.1000, 1.1003) + window(fri, C, 1.1000, 1.0998)   # Friday close P(C) = 1.0998
    rows += window(mon, C, 1.0990, 1.1005)                                     # Monday P(C-30) = 1.0990 -> short
    B = FakeB(rows, [x.isoformat() for x in (thu, fri, mon)])
    orig = im.SIG_LOOKBACK
    im.SIG_LOOKBACK = 2                     # sigma for Monday from Thu + Fri windows (causal)
    try:
        df = im.run_symbol('EURUSD', B, [thu, fri, mon], C, 'S0')
    finally:
        im.SIG_LOOKBACK = orig
    assert len(df) == 1 and df.iloc[0].d == mon and df.iloc[0].dir == -1      # Thu: no prev; Fri: sigma warm-up
    assert abs(df.iloc[0].r_rod_bp - (1.0990 / 1.0998 - 1) * 1e4) < 1e-9


if __name__ == '__main__':
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for f in fns:
        f()
        print('PASS', f.__name__)
    print(f'{len(fns)}/{len(fns)} PASS')
