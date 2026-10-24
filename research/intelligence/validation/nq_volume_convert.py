#!/usr/bin/env python3
"""Write the frozen Databento NQ ohlcv-1m DBN (sha bf5b20b4...) as CSV *with volume* for H-IVB1-NQ
(PREREG_HIVB1_NQ.md §3.2 needs volume per bar). Same rows as horb1_databento_convert.py, plus `volume`.
Run with the Databento venv:  .../orderflow/databento/.venv/bin/python -I nq_volume_convert.py <in.dbn.zst> <out.csv.gz>
"""
from __future__ import annotations

import hashlib
import json
import sys

import databento as db
import pandas as pd


def convert(src: str, dst: str) -> dict:
    df = db.DBNStore.from_file(src).to_df(price_type='float', pretty_ts=True).reset_index()
    ts = pd.DatetimeIndex(df['ts_event'])
    ny = ts.tz_convert('America/New_York').tz_localize(None)
    out = pd.DataFrame({'time_server': (ny + pd.Timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S'),
                        'open': df['open'].astype(float), 'high': df['high'].astype(float),
                        'low': df['low'].astype(float), 'close': df['close'].astype(float),
                        'volume': df['volume'].astype(float), 'time_status': 'OK'})
    out.to_csv(dst, index=False, compression='gzip')
    return {'rows': int(len(out)), 'volume_sum': float(out.volume.sum()), 'zero_volume_rows': int((out.volume <= 0).sum()),
            'sha256': hashlib.sha256(open(dst, 'rb').read()).hexdigest()}


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    print(json.dumps(convert(sys.argv[1], sys.argv[2]), indent=1))
