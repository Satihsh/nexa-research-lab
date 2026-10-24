"""Synthetic tests for forward_horb30l.py (no market data, no connector)."""
from __future__ import annotations

import csv
import json
import os
import sys
from datetime import date

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forward_horb30l as fw  # noqa: E402

DAY = date(2026, 10, 15)          # EDT: NY 09:30 = 13:30 UTC


def candles(day: date, bars: dict, base: float = 29600.0, spread: float = 1.4) -> list:
    out = []
    for m in range(9 * 60, 16 * 60 + 30):
        o = h = l = c = base
        if m in bars:
            o, h, l, c = bars[m]
        t = (pd.Timestamp(day) + pd.Timedelta(minutes=m)).tz_localize('America/New_York').tz_convert('UTC')
        ts = t.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        out.append({'time': ts, 'open': o + spread / 2, 'high': h + spread / 2, 'low': l + spread / 2,
                    'close': c + spread / 2, 'volume': 0.1, 'side': 'ask'})
        out.append({'time': ts, 'open': o - spread / 2, 'high': h - spread / 2, 'low': l - spread / 2,
                    'close': c - spread / 2, 'volume': 0.1, 'side': 'bid'})
    return out


def breakout_day() -> dict:
    b = {m: (29600.0, 29620.0, 29580.0, 29600.0) for m in range(570, 600)}          # A 29620, B 29580 (mid)
    b |= {m: (29622.0, 29626.0, 29621.0, 29625.0) for m in range(600, 605)}           # close 29625 > A
    b[605] = (29625.0, 29626.0, 29624.0, 29625.0)                                       # entry (mid open 29625)
    b[620] = (29660.0, 29671.0, 29659.0, 29670.0)                                       # 1R target = 29670
    return b


def run(tmp_path, monkeypatch, cand, name='fetch.json', wrap=False):
    monkeypatch.setattr(fw, 'DIR', str(tmp_path))
    monkeypatch.setattr(fw, 'LOG', str(tmp_path / 'log.csv'))
    monkeypatch.setattr(fw, 'START', DAY)
    p = tmp_path / name
    payload = {'instrument': 'USATECH.IDX/USD', 'period': 'M1', 'candles': cand}
    p.write_text(json.dumps({'result': json.dumps(payload)}) if wrap else json.dumps(payload))
    fw.main(str(p))
    with open(tmp_path / 'log.csv') as f:
        return list(csv.DictReader(f))


def test_forward_trade_mid_and_exec(tmp_path, monkeypatch):
    rows = run(tmp_path, monkeypatch, candles(DAY, breakout_day(), base=29625.0))
    r = rows[0]
    assert r['ny_date'] == '2026-10-15' and r['status'] == 'trade' and r['exit_kind'] == 'target'
    assert float(r['R_pts']) == pytest.approx(45.0) and float(r['net_R_S1']) == pytest.approx(43.0 / 45.0)
    assert r['exec_status'] == 'trade' and float(r['exec_R']) < float(r['gross_pts']) / 45.0   # pays the spread


def test_forward_idempotent_and_wrapped_json(tmp_path, monkeypatch):
    c = candles(DAY, breakout_day(), base=29625.0)
    run(tmp_path, monkeypatch, c, wrap=True)
    rows = run(tmp_path, monkeypatch, c, name='again.json')
    assert len(rows) == 1


def test_forward_not_observed_gap(tmp_path, monkeypatch):
    nxt = date(2026, 10, 19)                                                             # Monday; 16th Fri missed
    rows = run(tmp_path, monkeypatch, candles(nxt, {}, base=29600.0))
    st = {r['ny_date']: r['status'] for r in rows}
    assert st['2026-10-15'] == 'not_observed' and st['2026-10-16'] == 'not_observed'
    assert st['2026-10-19'] in ('no_breakout', 'missing')
