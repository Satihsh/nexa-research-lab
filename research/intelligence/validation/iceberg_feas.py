"""H-ICE-FEAS (PREREG_ICEBERG_FEAS.md): can the NEXA recorder tape see iceberg-like refills? Feasibility only.

Usage: python iceberg_feas.py <recorder_dir>   (folder holding ES_M1/ and NQ_M1/ with tape_<session>.csv files)
Prints one JSON result. No price-direction statistic is computed.
"""
from __future__ import annotations

import csv
import json
import os
import statistics
import sys
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo('America/New_York')
FIRST_SESSION = date(2026, 10, 21)
N_NEED, MIN_COVER, MIN_VALID, MIN_CAND, REPEAT_S = 10, 0.95, 0.99, 20, 10.0


def parse_ts(s):
    s = s.strip()
    fmt = '%Y-%m-%d %H:%M:%S.%f' if '.' in s else '%Y-%m-%d %H:%M:%S'
    return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)


def rth_minute(dt_utc):
    """Minute index 0..389 within 09:30-15:59 ET, or None outside RTH (DST-aware)."""
    et = dt_utc.astimezone(ET)
    if et.weekday() >= 5:
        return None
    m = et.hour * 60 + et.minute - 570
    return m if 0 <= m < 390 else None


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def quote_valid(r):
    b, a, bs, az = fnum(r['prev_bid']), fnum(r['prev_ask']), fnum(r['prev_bid_size']), fnum(r['prev_ask_size'])
    return None not in (b, a, bs, az) and b > 0 and a > b and bs > 0 and az > 0


def is_candidate(r):
    if not quote_valid(r):
        return False
    v, fp, lp = fnum(r['volume']), fnum(r['first_price']), fnum(r['last_price'])
    if None in (v, fp, lp) or fp != lp:
        return False
    if r['side'] == 'BUY':
        return lp == fnum(r['prev_ask']) and v > fnum(r['prev_ask_size'])
    if r['side'] == 'SELL':
        return lp == fnum(r['prev_bid']) and v > fnum(r['prev_bid_size'])
    return False


def session_stats(rows):
    """rows: dicts with the tape header fields. Returns per-session measures over RTH rows."""
    minutes, rth, cands, delays, back = set(), [], [], [], 0
    last_recv = None
    for r in rows:
        try:
            tt, rv = parse_ts(r['trade_time']), parse_ts(r['received_utc'])
        except (ValueError, KeyError):
            continue
        m = rth_minute(tt)
        if m is None:
            continue
        minutes.add(m)
        rth.append(r)
        delays.append((rv - tt).total_seconds())
        if last_recv is not None and rv < last_recv:
            back += 1
        last_recv = rv
        if is_candidate(r):
            cands.append((tt, r['side'], fnum(r['last_price']),
                          fnum(r['volume']) - fnum(r['prev_ask_size'] if r['side'] == 'BUY' else r['prev_bid_size'])))
    aggr = [r for r in rth if r['side'] in ('BUY', 'SELL')]
    rep = sum(1 for i in range(1, len(cands))
              if cands[i][1] == cands[i - 1][1] and cands[i][2] == cands[i - 1][2]
              and (cands[i][0] - cands[i - 1][0]).total_seconds() <= REPEAT_S)
    return {
        'rows': len(rth), 'coverage': len(minutes) / 390.0,
        'aggressor_share': len(aggr) / len(rth) if rth else None,
        'quote_valid_share': (sum(1 for r in aggr if quote_valid(r)) / len(aggr)) if aggr else None,
        'received_backwards': back,
        'delay_median_s': statistics.median(delays) if delays else None,
        'delay_p95_s': sorted(delays)[int(0.95 * (len(delays) - 1))] if delays else None,
        'candidates': len(cands), 'candidate_share': len(cands) / len(aggr) if aggr else None,
        'median_excess': statistics.median([c[3] for c in cands]) if cands else None,
        'repeat_refill_share': rep / len(cands) if cands else None,
    }


def verdict(sessions):
    q = [s for s in sessions if s['coverage'] >= MIN_COVER][:N_NEED]
    if len(q) < N_NEED:
        return 'INSUFFICIENT', q
    valid = sum(s['quote_valid_share'] * s['rows'] * (s['aggressor_share'] or 0) for s in q) / \
        max(1e-9, sum(s['rows'] * (s['aggressor_share'] or 0) for s in q))
    med = statistics.median(s['candidates'] for s in q)
    return ('FEASIBLE' if valid >= MIN_VALID and med >= MIN_CAND else 'NOT FEASIBLE'), q


def run(recorder_dir):
    out = {}
    for inst in ('ES_M1', 'NQ_M1'):
        folder = os.path.join(recorder_dir, inst)
        sessions = []
        for name in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
            if not (name.startswith('tape_') and name.endswith('.csv')):
                continue
            key = date.fromisoformat(name[5:15])
            if key < FIRST_SESSION:
                continue
            with open(os.path.join(folder, name), newline='') as fh:
                st = session_stats(list(csv.DictReader(fh)))
            sessions.append(dict(st, session=key.isoformat()))
        v, q = verdict(sessions)
        out[inst] = {'verdict': v, 'qualifying_used': [s['session'] for s in q], 'sessions': sessions}
    return out


if __name__ == '__main__':
    print(json.dumps(run(sys.argv[1]), indent=1, default=str))
