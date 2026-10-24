#!/usr/bin/env python3
"""H-ORB30L-REPL Part B: prospective forward log of the FROZEN H-ORB30L-NQ rule on Dukascopy USATECH.IDX/USD M1
(PREREG_HORB30L_REPL.md §3). Read-only data; this script never trades.

Input: one raw JSON file saved from the Dukascopy connector's get_candles (instrument USATECH.IDX/USD, period M1,
side both). The file may be the tool result itself ({"candles": [...]}) or a wrapper containing that JSON as text.

For every NY weekday from START up to the latest complete session in the file that is not yet in the log:
  - session fully covered (09:30-09:59 and the 15:29 bar present) -> apply the rule on MID prices (S1 cost 2.0),
    plus the executable variant (entry at ask, exits on bid, no extra cost);
  - otherwise -> 'not_observed' (never back-filled later; a holiday also shows here).
Usage:  python3 forward_horb30l.py <raw.json>        (appends to forward_horb30l/log.csv; idempotent)
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import horb30l_nq as orb  # noqa: E402  (frozen engine, sha 7d4095bc)
import hivb1_nq as iv  # noqa: E402

START = date(2026, 10, 15)
DIR = os.path.join(HERE, 'forward_horb30l')
LOG = os.path.join(DIR, 'log.csv')
COLS = ['ny_date', 'status', 'entry_min', 'R_pts', 'gross_pts', 'net_R_S1', 'exit_kind', 'exec_status',
        'exec_gross_pts', 'exec_R', 'raw_file', 'raw_sha256', 'logged_utc']


def read_candles(path: str) -> list:
    txt = open(path, encoding='utf-8').read()
    try:
        obj = json.loads(txt)
    except json.JSONDecodeError:
        obj = None
    def find(o):
        if isinstance(o, dict):
            if isinstance(o.get('candles'), list):
                return o['candles']
            for v in o.values():
                r = find(v)
                if r is not None:
                    return r
        if isinstance(o, list):
            for v in o:
                r = find(v)
                if r is not None:
                    return r
        if isinstance(o, str) and '"candles"' in o:
            try:
                return find(json.loads(o))
            except json.JSONDecodeError:
                return None
        return None
    c = find(obj) if obj is not None else None
    if c is None:
        m = re.search(r'\{.*"candles".*\}', txt, re.S)
        c = find(json.loads(m.group(0))) if m else None
    if not c:
        raise SystemExit(f'no candles found in {path}')
    return c


def to_frames(candles: list) -> tuple:
    """-> (mid, bid, ask) DataFrames in the canonical time_server = NY + 7 h format, one row per minute."""
    df = pd.DataFrame(candles)
    df['t'] = pd.to_datetime(df['time'], utc=True)
    ny = df['t'].dt.tz_convert('America/New_York').dt.tz_localize(None)
    df['time_server'] = (ny + pd.Timedelta(hours=7)).dt.strftime('%Y-%m-%d %H:%M:%S')
    side = {s: g.drop_duplicates('time_server').set_index('time_server')[['open', 'high', 'low', 'close', 'volume']]
            for s, g in df.groupby('side')}
    if 'bid' not in side or 'ask' not in side:
        raise SystemExit('need both bid and ask candles (side=both)')
    common = side['bid'].index.intersection(side['ask'].index)
    bid, ask = side['bid'].loc[common], side['ask'].loc[common]
    mid = (bid + ask) / 2.0
    return tuple(x.reset_index().rename(columns={'index': 'time_server'}) for x in (mid, bid, ask))


def exec_trade(Db, Da, d, entry_min: int, stop: float, cost: float = 0.0) -> dict:
    """Executable variant: same rule/semantics as orb.run_trade, but entry = ask open, exits judged on bid."""
    em = ka = None
    for m in range(entry_min, orb.EXIT_MIN):
        ka = Da.at(orb.hb.utc_of(d, m))
        if ka >= 0 and Db.at(orb.hb.utc_of(d, m)) >= 0:
            em = m
            break
    if em is None:
        return {'status': 'no_entry_bar'}
    entry = float(Da.o[ka])
    R = entry - stop
    if R <= 0:
        return {'status': 'invalid'}
    if R < orb.MIN_R:
        return {'status': 'cost_floor'}
    tgt = entry + R
    for m in range(em, orb.EXIT_MIN + 1):
        k = Db.at(orb.hb.utc_of(d, m))
        if k < 0:
            continue
        o_, h_, l_, c_ = float(Db.o[k]), float(Db.h[k]), float(Db.l[k]), float(Db.c[k])
        first = m == em
        px = how = None
        if l_ <= stop:
            px, how = (o_ if (not first and o_ <= stop) else stop), 'stop'
        elif not first and h_ >= tgt + orb.TICK:
            px, how = tgt, 'target'
        elif m == orb.EXIT_MIN:
            px, how = c_, 'time'
        if px is not None:
            g = px - entry - cost
            return {'status': 'trade', 'gross_pts': px - entry, 'R': g / R}
    return {'status': 'missing'}


def evaluate_day(Dm, Db, Da, d) -> dict:
    r = orb.simulate(Dm, d, cost=orb.COST['S1'])
    row = {'ny_date': d.isoformat(), 'status': r['status']}
    if r['status'] == 'trade':
        row |= {'entry_min': r['entry_min'], 'R_pts': round(r['R_pts'], 4),
                'gross_pts': round(r['pnl_pts'] + orb.COST['S1'], 4), 'net_R_S1': round(r['R'], 6),
                'exit_kind': r['exit_kind']}
        S = orb.setup(Dm, d)
        x = exec_trade(Db, Da, d, S['entry_min'], S['B'])
        row |= {'exec_status': x['status']}
        if x['status'] == 'trade':
            row |= {'exec_gross_pts': round(x['gross_pts'], 4), 'exec_R': round(x['R'], 6)}
    return row


def covered(D, d) -> bool:
    return all(D.at(orb.hb.utc_of(d, m)) >= 0 for m in list(range(570, 600)) + [orb.EXIT_MIN])


def logged_dates() -> set:
    if not os.path.exists(LOG):
        return set()
    with open(LOG) as f:
        return {r['ny_date'] for r in csv.DictReader(f)}


def main(path: str) -> int:
    os.makedirs(DIR, exist_ok=True)
    sha = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    mid, bid, ask = to_frames(read_candles(path))
    Dm, Db, Da = (iv.from_frame(x) for x in (mid, bid, ask))
    days_in_file = [d for d in Dm.days() if covered(Dm, d)]
    last = max(days_in_file) if days_in_file else None
    done = logged_dates()
    new_rows = []
    if last is not None:
        d = START
        while d <= last:
            if d.weekday() < 5 and d.isoformat() not in done:
                row = evaluate_day(Dm, Db, Da, d) if d in days_in_file else {'ny_date': d.isoformat(),
                                                                              'status': 'not_observed'}
                new_rows.append(row | {'raw_file': os.path.basename(path), 'raw_sha256': sha,
                                       'logged_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')})
            d += timedelta(days=1)
    exists = os.path.exists(LOG)
    with open(LOG, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        if not exists:
            w.writeheader()
        for r in new_rows:
            w.writerow({c: r.get(c, '') for c in COLS})
    with open(LOG) as f:
        allr = list(csv.DictReader(f))
    tr = [float(r['net_R_S1']) for r in allr if r['status'] == 'trade']
    summary = {'appended': [(r['ny_date'], r['status'], r.get('exit_kind', ''), r.get('net_R_S1', '')) for r in new_rows],
               'last_complete_session_in_file': last.isoformat() if last else None,
               'forward_trades': len(tr), 'forward_mean_R_S1': round(sum(tr) / len(tr), 4) if tr else None,
               'days_logged': len(allr), 'not_observed': sum(r['status'] == 'not_observed' for r in allr)}
    print(json.dumps(summary))
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
