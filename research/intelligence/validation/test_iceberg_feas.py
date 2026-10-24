"""Synthetic tests for iceberg_feas.py (PREREG_ICEBERG_FEAS.md s.5). No recorder data is read."""
from __future__ import annotations

import importlib.util
import os
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('iceberg_feas', os.path.join(HERE, 'iceberg_feas.py'))
ic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ic)


def row(tt, side='BUY', vol=5, fp=100.0, lp=100.0, bid=99.75, bs=3, ask=100.0, az=2, recv=None):
    f = '%Y-%m-%d %H:%M:%S.%f'
    return {'received_utc': (recv or tt + timedelta(minutes=15)).strftime(f), 'trade_time': tt.strftime(f),
            'side': side, 'volume': str(vol), 'first_price': str(fp), 'last_price': str(lp), 'prev_bid': str(bid),
            'prev_bid_size': str(bs), 'prev_ask': str(ask), 'prev_ask_size': str(az), 'prints': '1'}


# 1. RTH filter in ET, DST-aware (summer: 13:30 UTC = 09:30 ET; winter: 14:30 UTC = 09:30 ET)
def test_rth_minute_dst():
    assert ic.rth_minute(datetime(2026, 10, 21, 13, 30, tzinfo=timezone.utc)) == 0
    assert ic.rth_minute(datetime(2026, 10, 21, 13, 29, tzinfo=timezone.utc)) is None
    assert ic.rth_minute(datetime(2026, 11, 3, 14, 30, tzinfo=timezone.utc)) == 0
    assert ic.rth_minute(datetime(2026, 11, 3, 20, 59, tzinfo=timezone.utc)) == 389
    assert ic.rth_minute(datetime(2026, 11, 3, 21, 0, tzinfo=timezone.utc)) is None
    assert ic.rth_minute(datetime(2026, 10, 24, 15, 0, tzinfo=timezone.utc)) is None   # Saturday


# 2. quote validity
def test_quote_valid():
    t = datetime(2026, 10, 21, 14, 0, tzinfo=timezone.utc)
    assert ic.quote_valid(row(t))
    assert not ic.quote_valid(row(t, bid=100.0, ask=100.0))
    assert not ic.quote_valid(row(t, az=0))


# 3. candidate definition, both sides
def test_candidates():
    t = datetime(2026, 10, 21, 14, 0, tzinfo=timezone.utc)
    assert ic.is_candidate(row(t, 'BUY', vol=5, lp=100.0, ask=100.0, az=2))
    assert not ic.is_candidate(row(t, 'BUY', vol=2, lp=100.0, ask=100.0, az=2))      # not more than shown
    assert not ic.is_candidate(row(t, 'BUY', vol=5, fp=100.0, lp=100.25))            # moved through
    assert ic.is_candidate(row(t, 'SELL', vol=9, fp=99.75, lp=99.75, bid=99.75, bs=3))
    assert not ic.is_candidate(row(t, 'SELL', vol=9, fp=99.75, lp=99.75, bid=99.5, bs=3))


# 4. session stats: coverage, repeat refills, backwards receive time
def test_session_stats():
    base = datetime(2026, 10, 21, 13, 30, tzinfo=timezone.utc)
    rows = [row(base + timedelta(minutes=m)) for m in range(390)]
    rows.insert(5, row(base + timedelta(minutes=4, seconds=5)))                       # repeat within 10 s
    rows.append(row(base + timedelta(minutes=389, seconds=30), recv=base))           # receive time goes back
    s = ic.session_stats(rows)
    assert s['coverage'] == 1.0 and s['candidates'] == len(rows) and s['received_backwards'] == 1
    assert s['repeat_refill_share'] > 0 and abs(s['delay_median_s'] - 900) < 1e-6


# 5. verdict thresholds and qualifying-session rule
def test_verdict():
    good = {'coverage': 1.0, 'rows': 1000, 'aggressor_share': 1.0, 'quote_valid_share': 1.0, 'candidates': 25}
    thin = dict(good, coverage=0.5)
    assert ic.verdict([good] * 9 + [thin] * 5)[0] == 'INSUFFICIENT'
    assert ic.verdict([good] * 10)[0] == 'FEASIBLE'
    assert ic.verdict([dict(good, candidates=10)] * 10)[0] == 'NOT FEASIBLE'
    assert ic.verdict([dict(good, quote_valid_share=0.9)] * 10)[0] == 'NOT FEASIBLE'
