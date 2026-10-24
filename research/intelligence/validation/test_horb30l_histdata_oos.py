"""Synthetic tests for horb30l_histdata_oos.py (PREREG_HORB30L_REPL_HISTDATA.md). No market data is read."""
from __future__ import annotations

import json
import os
import sys
import zipfile

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import horb30l_histdata_oos as hd  # noqa: E402
import test_horb30l_duka_oos as td  # noqa: E402  (shared synthetic day generator)


def write_zips(raw, days_spec) -> pd.DataFrame:
    rows = []
    for d, width, win in days_spec:
        for m, (o, h, l, c) in td.day_bars(width, win).items():
            t = (pd.Timestamp(d) + pd.Timedelta(minutes=m)).tz_localize('America/New_York').tz_convert('UTC')
            rows.append((t, o, h, l, c))
    bid = pd.DataFrame(rows, columns=['t', 'open', 'high', 'low', 'close'])
    est = (bid.t.dt.tz_convert('UTC').dt.tz_localize(None) - pd.Timedelta(hours=5))
    os.makedirs(raw, exist_ok=True)
    for y, g in bid.groupby(est.dt.year):
        txt = '\n'.join(f'{e:%Y%m%d %H%M%S};{r.open:.3f};{r.high:.3f};{r.low:.3f};{r.close:.3f};0'
                        for e, r in zip(est[g.index], g.itertuples())) + '\n'
        with zipfile.ZipFile(os.path.join(raw, f'HISTDATA_COM_ASCII_NSXUSD_M1_{y}.zip'), 'w') as zf:
            zf.writestr(f'DAT_ASCII_NSXUSD_M1_{y}.csv', txt)
            zf.writestr(f'DAT_ASCII_NSXUSD_M1_{y}.txt', 'status report')
    return bid


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(hd, 'PARITY_OUT', str(tmp_path / 'parity.json'))
    monkeypatch.setattr(hd, 'OOS_OUT', str(tmp_path / 'oos.json'))
    return tmp_path


def test_reader_est_clock(tmp_path):
    raw = str(tmp_path / 'raw')
    write_zips(raw, td.spec()[:1])                                  # 2023-03-01 (EST): 09:00 NY = 14:00 UTC
    df, name, _ = hd.read_zip(hd.raw_zips(raw)[0])
    assert name == 'DAT_ASCII_NSXUSD_M1_2023.csv'
    assert df.t.iloc[0] == pd.Timestamp('2023-03-01 14:00', tz='UTC')


def test_reader_summer_fixed_offset(tmp_path):
    """EST without DST: a summer row stamped 08:00 EST is 13:00 UTC = 09:00 New York (EDT)."""
    raw = tmp_path / 'raw'
    raw.mkdir()
    with zipfile.ZipFile(raw / 'HISTDATA_COM_ASCII_NSXUSD_M1_2015.zip', 'w') as zf:
        zf.writestr('DAT_ASCII_NSXUSD_M1_2015.csv', '20150701 080000;4400;4401;4399;4400.5;0\n')
    df, _, _ = hd.read_zip(str(raw / 'HISTDATA_COM_ASCII_NSXUSD_M1_2015.zip'))
    assert df.t.iloc[0] == pd.Timestamp('2015-07-01 13:00', tz='UTC')
    assert df.t.iloc[0].tz_convert('America/New_York').hour == 9


def test_pipeline_manifest_parity_oos(env):
    raw = str(env / 'raw')
    bid = write_zips(raw, td.spec())
    assert len(hd.write_manifest(raw)['files']) == 2
    with pytest.raises(SystemExit):
        hd.write_manifest(raw)
    p = hd.parity(raw, nq=td.nq_dv(bid))
    assert p['load_audit']['first_utc'] >= hd.dk.CUTOFF_NY.tz_convert('UTC').isoformat()
    assert p['n_days'] == 4 and p['n_both_trade'] == 4 and p['PASS']
    with pytest.raises(SystemExit):
        hd.parity(raw, nq=td.nq_dv(bid))
    o = hd.oos(raw, battery=False)
    assert o['load_audit']['last_utc'] < hd.dk.CUTOFF_NY.tz_convert('UTC').isoformat()
    assert o['first_day'] == '2016-03-01' and o['counts_S1'] == {'trade': 3}
    assert o['acceptance']['verdict'] == 'INSUFFICIENT-N'
    with pytest.raises(SystemExit):
        hd.oos(raw, battery=False)


def test_oos_refused_and_tamper(env):
    raw = str(env / 'raw')
    write_zips(raw, td.spec())
    hd.write_manifest(raw)
    with pytest.raises(SystemExit):
        hd.oos(raw, battery=False)
    json.dump({'PASS': False}, open(hd.PARITY_OUT, 'w'))
    with pytest.raises(SystemExit):
        hd.oos(raw, battery=False)
    with open(os.path.join(raw, 'HISTDATA_COM_ASCII_NSXUSD_M1_2016.zip'), 'ab') as f:
        f.write(b'x')
    with pytest.raises(SystemExit):
        hd.verify_manifest(raw)
