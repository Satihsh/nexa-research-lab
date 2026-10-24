"""Synthetic tests for horb30l_duka_oos.py (PREREG_HORB30L_REPL_DUKA.md). No market data is read."""
from __future__ import annotations

import json
import os
import sys
from datetime import date

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import horb30l_duka_oos as dk  # noqa: E402
import hivb1_nq as iv  # noqa: E402

PAR_DAYS = [date(2023, 3, 1), date(2023, 3, 2), date(2023, 3, 3), date(2023, 3, 6)]
OOS_DAYS = [date(2016, 3, 1), date(2016, 3, 2), date(2016, 3, 3)]
HALF_SPREAD = 0.7


def day_bars(width: float, win: bool, base: float = 15000.0) -> dict:
    """Mid OHLC per NY minute 09:00-16:29: range 09:30-09:59 = [base-width/2, base+width/2], breakout at 10:04,
    entry 10:05, then target (win) or stop."""
    A, B = base + width / 2, base - width / 2
    bars = {}
    for m in range(540, 990):
        o = base + 0.25 * (m % 2)
        bars[m] = (o, o + 0.5, o - 0.5, o)
    for m in range(570, 600):
        bars[m] = (base, A, B, base + 0.25 * (m % 2))
    for m in range(600, 605):
        bars[m] = (A + 1, A + 3, A + 0.5, A + 2)
    bars[605] = (A + 2, A + 2.5, A + 1.5, A + 2)
    R = (A + 2) - B
    for m in range(606, 990):
        o = A + 2 + 0.25 * (m % 2)
        bars[m] = (o, o + 0.5, o - 0.5, o)
    if win:
        bars[620] = (A + 2, A + 2 + R + 1, A + 2, A + 2 + R)
    else:
        bars[620] = (A + 2, A + 2, B - 1, B - 0.5)
    return bars


def write_raw(raw, days_spec) -> pd.DataFrame:
    rows = []
    for d, width, win in days_spec:
        for m, (o, h, l, c) in day_bars(width, win).items():
            t = (pd.Timestamp(d) + pd.Timedelta(minutes=m)).tz_localize('America/New_York').tz_convert('UTC')
            rows.append((t, o, h, l, c))
    mid = pd.DataFrame(rows, columns=['t', 'open', 'high', 'low', 'close'])
    bid = mid.copy()
    ask = mid.copy()
    for k in ('open', 'high', 'low', 'close'):
        bid[k] -= HALF_SPREAD
        ask[k] += HALF_SPREAD
    os.makedirs(raw, exist_ok=True)
    pd.DataFrame({'Gmt time': bid.t.dt.strftime('%d.%m.%Y %H:%M:%S.000'), 'Open': bid.open, 'High': bid.high,
                  'Low': bid.low, 'Close': bid.close, 'Volume': 1.0}).to_csv(
        os.path.join(raw, 'USATECH.IDX-USD_Candlestick_1_M_BID.csv'), index=False)
    pd.DataFrame({'Time (UTC)': ask.t.dt.strftime('%Y.%m.%d %H:%M:%S'), 'Open': ask.open, 'High': ask.high,
                  'Low': ask.low, 'Close': ask.close, 'Volume': 1.0}).to_csv(
        os.path.join(raw, 'USATECH.IDX-USD_Candlestick_1_M_ASK.csv'), index=False)
    return mid


def nq_dv(mid: pd.DataFrame):
    ny = mid.t.dt.tz_convert('America/New_York').dt.tz_localize(None)
    f = mid.drop(columns='t').assign(volume=1.0, time_server=(ny + pd.Timedelta(hours=7)).dt.strftime(
        '%Y-%m-%d %H:%M:%S'))
    return iv.from_frame(f)


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(dk, 'PARITY_OUT', str(tmp_path / 'parity.json'))
    monkeypatch.setattr(dk, 'OOS_OUT', str(tmp_path / 'oos.json'))
    return tmp_path


def spec():
    par = [(d, w, win) for d, w, win in zip(PAR_DAYS, (40, 60, 80, 50), (True, False, True, True))]
    oos = [(d, w, win) for d, w, win in zip(OOS_DAYS, (40, 30, 70), (True, True, False))]
    return par + oos


def test_read_raw_formats_and_refusals(tmp_path):
    raw = str(tmp_path / 'raw')
    write_raw(raw, spec()[:1])
    files = dk.raw_files(raw)
    assert sorted(files.values()) == ['ask', 'bid']
    for p in files:
        df = dk.read_raw(p)
        assert str(df.t.dt.tz) == 'UTC' and df.t.iloc[0] == pd.Timestamp('2023-03-01 14:00', tz='UTC')
    bad = tmp_path / 'b'
    bad.mkdir()
    pd.DataFrame({'Time (EET)': ['2023.03.01 00:00:00'], 'Open': [1], 'High': [1], 'Low': [1], 'Close': [1]}).to_csv(
        bad / 'x_BID.csv', index=False)
    with pytest.raises(SystemExit):
        dk.read_raw(str(bad / 'x_BID.csv'))
    with pytest.raises(SystemExit):
        dk.raw_files(str(bad))                                                    # BID without ASK


def test_rule_calendar():
    c15 = dk.rule_calendar(2015)
    for x in ('2015-01-01', '2015-01-19', '2015-02-16', '2015-04-03', '2015-05-25', '2015-07-03', '2015-09-07',
              '2015-10-12', '2015-11-11', '2015-11-26', '2015-11-27', '2015-12-24', '2015-12-25', '2015-12-31'):
        assert date.fromisoformat(x) in c15, x
    assert date(2012, 10, 29) in dk.rule_calendar(2012) and date(2012, 10, 30) in dk.rule_calendar(2012)
    assert date(2011, 12, 26) in dk.rule_calendar(2011)                          # Christmas Sunday -> Monday
    assert dk.easter(2016) == date(2016, 3, 27) and dk.easter(2010) == date(2010, 4, 4)
    cal = dk.oos_calendar([2015, 2016, 2017])
    assert date(2015, 11, 26) in cal and date(2017, 1, 2) in cal                  # frozen file from 2017


def test_stale_day(tmp_path):
    raw = str(tmp_path / 'raw')
    write_raw(raw, spec()[:1])
    Dm, _, _, _ = dk.load(raw)
    assert not dk.stale(Dm, PAR_DAYS[0])
    flat = pd.DataFrame([{'time_server': (pd.Timestamp(PAR_DAYS[0]) + pd.Timedelta(minutes=m, hours=7)).strftime(
        '%Y-%m-%d %H:%M:%S'), 'open': 1.0, 'high': 1.0, 'low': 1.0, 'close': 1.0, 'volume': 0.0}
        for m in range(560, 960)])
    assert dk.stale(iv.from_frame(flat), PAR_DAYS[0])


def test_pipeline_manifest_parity_oos(env):
    raw = str(env / 'raw')
    mid = write_raw(raw, spec())
    m = dk.write_manifest(raw)
    assert len(m['files']) == 2
    with pytest.raises(SystemExit):
        dk.write_manifest(raw)                                                    # frozen
    p = dk.parity(raw, nq=nq_dv(mid))
    assert p['load_audit']['first_utc'] >= dk.CUTOFF_NY.tz_convert('UTC').isoformat()   # no pre-cutoff row loaded
    assert p['n_days'] == 4 and p['n_both_trade'] == 4 and p['PASS']
    with pytest.raises(SystemExit):
        dk.parity(raw, nq=nq_dv(mid))                                             # opened once
    o = dk.oos(raw, battery=False)
    assert o['load_audit']['last_utc'] < dk.CUTOFF_NY.tz_convert('UTC').isoformat()     # no in-sample row loaded
    assert o['first_day'] == '2016-03-01' and o['last_day'] == '2016-03-03'
    assert o['counts_S1'] == {'trade': 3} and o['acceptance']['verdict'] == 'INSUFFICIENT-N'
    assert o['executable_variant_ask_entry_bid_exit']['n'] == 3
    with pytest.raises(SystemExit):
        dk.oos(raw, battery=False)                                                # opened once


def test_oos_refused_without_parity_pass(env):
    raw = str(env / 'raw')
    write_raw(raw, spec())
    dk.write_manifest(raw)
    with pytest.raises(SystemExit):
        dk.oos(raw, battery=False)                                                # no parity file
    json.dump({'PASS': False}, open(dk.PARITY_OUT, 'w'))
    with pytest.raises(SystemExit):
        dk.oos(raw, battery=False)                                                # parity failed


def test_manifest_tamper_detected(env):
    raw = str(env / 'raw')
    write_raw(raw, spec())
    dk.write_manifest(raw)
    with open(os.path.join(raw, 'USATECH.IDX-USD_Candlestick_1_M_ASK.csv'), 'a') as f:
        f.write('2023.12.29 20:00:00,1,1,1,1,1\n')
    with pytest.raises(SystemExit):
        dk.verify_manifest(raw)
