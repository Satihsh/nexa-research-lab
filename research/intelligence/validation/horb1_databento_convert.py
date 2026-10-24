#!/usr/bin/env python3
"""Convert a Databento GLBX.MDP3 ohlcv-1m DBN file into the canonical M1 CSV that horb1_orb.load() reads
(DEVIATIONS_HORB1 D-1, D-3, D-4). Run with the Databento venv (needs the `databento` package):

  .../orderflow/databento/.venv/bin/python -I horb1_databento_convert.py <in.dbn.zst> <out.csv.gz>

Columns written: time_server (bar open in New York time + 7 h, '%Y-%m-%d %H:%M:%S'), open, high, low, close,
spread (0 points: the 1.0-point S0 floor applies to every bar, D-3), time_status ('OK'), time_utc, symbol.
Never repairs data: rows are written as received; duplicates are left for the loader to count.
"""
from __future__ import annotations

import hashlib
import json
import sys

import databento as db
import pandas as pd


def convert(src: str, dst: str) -> dict:
    store = db.DBNStore.from_file(src)
    df = store.to_df(price_type='float', pretty_ts=True)          # index ts_event (UTC, bar open)
    df = df.reset_index()
    ts = pd.DatetimeIndex(df['ts_event'])
    ny = ts.tz_convert('America/New_York').tz_localize(None)
    out = pd.DataFrame({
        'time_server': (ny + pd.Timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S'),
        'open': df['open'].astype(float), 'high': df['high'].astype(float),
        'low': df['low'].astype(float), 'close': df['close'].astype(float),
        'spread': 0, 'time_status': 'OK', 'time_utc': ts.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'symbol': df['symbol'].astype(str) if 'symbol' in df.columns else '',
        'instrument_id': df['instrument_id'] if 'instrument_id' in df.columns else -1,
    })
    out.to_csv(dst, index=False, compression='gzip')
    sha = hashlib.sha256(open(dst, 'rb').read()).hexdigest()
    return {'src': src, 'dst': dst, 'rows': int(len(out)), 'first_utc': str(ts.min()), 'last_utc': str(ts.max()),
            'symbols': sorted(set(out['symbol'])), 'n_instrument_ids': int(out['instrument_id'].nunique()),
            'sha256': sha}


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    print(json.dumps(convert(sys.argv[1], sys.argv[2]), indent=1))
