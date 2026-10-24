"""Synthetic tests for qc_sk28/main.py and sk28_stats.py (PREREG_SK28_OOS.md s.8). No market data.
The end-to-end smoke test runs the frozen pipeline on their own generate_synthetic_data (needs pandas)."""
import hashlib
import importlib.util
import os
import sys
import types
from datetime import date, datetime, timedelta

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN = os.path.join(HERE, 'qc_sk28', 'frozen')
stub = types.ModuleType('AlgorithmImports')
stub.QCAlgorithm = object
sys.modules.setdefault('AlgorithmImports', stub)
spec = importlib.util.spec_from_file_location('sk28_stats', os.path.join(HERE, 'sk28_stats.py'))
st = importlib.util.module_from_spec(spec)
spec.loader.exec_module(st)
qm = st.qm
if FROZEN not in sys.path:
    sys.path.insert(0, FROZEN)


def test_frozen_hashes_match_prereg_appendix():
    pre = open(os.path.join(HERE, 'PREREG_SK28_OOS.md')).read()
    n = 0
    for line in open(os.path.join(FROZEN, 'FROZEN_SHA256.txt')):
        h, p = line.split()
        assert f'{h}  {p}' in pre, p
        assert hashlib.sha256(open(os.path.join(FROZEN, p), 'rb').read()).hexdigest() == h, p
        n += 1
    assert n == 25


def test_windows_and_data_range():
    assert qm.window(2010, 1) == (date(2010, 1, 4), date(2010, 6, 30))
    assert qm.window(2010, 2) == (date(2010, 7, 1), date(2010, 12, 31))
    assert qm.window(2022, 2) == (date(2022, 7, 1), date(2022, 12, 23))
    assert qm.window(2023, 1) == (date(2023, 1, 3), date(2023, 6, 30))
    assert qm.window(2025, 2) == (date(2025, 7, 1), date(2025, 11, 28))
    assert qm.data_range(2010, 1) == (date(2009, 9, 3), date(2010, 6, 30))
    assert qm.data_range(2010, 2) == (date(2010, 3, 3), date(2010, 12, 31))


def test_encode_decode_roundtrip_and_clamp():
    rec = {'doy': 365, 'minute': 1439, 'model': 11, 'dir': 1, 'reason': 7, 'r': 4095, 'risk_t': 127, 'mr': 0,
           'mrisk_t': 0}
    s = qm.encode(rec)
    assert len(s) == 11 and qm.decode(s) == rec
    rec2 = {'doy': 3, 'minute': 600, 'model': 2, 'dir': 0, 'reason': 1, 'r': qm.enc_r(-1.0, [0]), 'risk_t': 48,
            'mr': qm.enc_r(2.37, [0]), 'mrisk_t': 52}
    assert qm.decode(qm.encode(rec2)) == rec2
    cl = [0]
    assert qm.enc_r(25.0, cl) == 4095 and qm.enc_r(-25.0, cl) == 1 and cl[0] == 2


def test_bars_to_csv_read_by_their_loader():
    import io
    from data.loader import load_csv
    rows = [(datetime(2023, 1, 3, 18, 1), 100.0, 101.25, 99.5, 100.75, 0),
            (datetime(2023, 1, 3, 18, 2), 100.75, 101.0, 100.5, 101.0, 7)]
    df = load_csv(io.StringIO(qm.bars_to_csv(rows)), 'NQ')
    assert list(df['datetime'].dt.strftime('%H:%M')) == ['18:01', '18:02']     # end-labelled ET kept as is
    assert list(df['volume']) == [1, 7]                                         # their 0 -> 1 rule
    assert df['high'].iloc[0] == 101.25


class _Sig:
    pass


def test_mirror_signal_reflects_around_entry():
    from strategy.models.base import Signal, ModelRiskProfile
    import pandas as pd
    s = Signal(idx=5, ts=pd.Timestamp('2023-01-03 10:00'), model='ou_rev', direction='long', entry=100.0, stop=88.0,
               target=124.0, risk_ticks=48, reward_ticks=96, rr=2.0, priority=15, risk_profile=ModelRiskProfile())
    m = qm.mirror_signal(s)
    assert (m.direction, m.stop, m.target, m.entry) == ('short', 112.0, 76.0, 100.0)
    assert s.direction == 'long' and m.risk_profile is s.risk_profile
    assert qm.mirror_signal(m).stop == 88.0


def test_match_ref_greedy_one_to_one():
    t = datetime(2023, 3, 1, 10, 0)
    ref = [(t, 0, 'L'), (t + timedelta(minutes=1), 0, 'L'), (t, 1, 'S'), (t + timedelta(hours=1), 2, 'L')]
    qc = [(t + timedelta(minutes=2), 0, 'L'), (t, 1, 'L'), (t + timedelta(hours=1, minutes=3), 2, 'L')]
    matched, per = qm.match_ref(ref, qc)
    assert matched == 1 and per == {0: [2, 1], 1: [1, 0], 2: [1, 0]}   # side, model and +-2 min all required
    s = '202303011000,0,L;202512011000,3,S'
    assert qm.parse_ref(s, date(2023, 1, 3), date(2025, 11, 28)) == [(t, 0, 'L')]


def test_first_eth_and_rth_bitmap():
    rows = [(datetime(2023, 1, 2, 18, 1), 0, 0, 0, 0, 1), (datetime(2023, 1, 2, 18, 2), 0, 0, 0, 0, 1),
            (datetime(2023, 1, 3, 18, 0), 0, 0, 0, 0, 1), (datetime(2023, 1, 4, 9, 31), 0, 0, 0, 0, 1),
            (datetime(2023, 1, 5, 9, 30), 0, 0, 0, 0, 1)]
    assert qm.first_eth_check(rows) == (1, 1)
    c = {'year': 2023, 'half': 1, 'window': ['2023-01-03', '2023-06-30'], 'rth_days': qm.rth_bitmap(rows, 2023)}
    assert st.days_of(c) == [date(2023, 1, 4)]           # 09:30 end-label = pre-open bar, not RTH


def _chunk(year, half, trades, days, gate=None):
    clamps = [0]
    recs = []
    lo, hi = qm.window(year, half)
    for d, model, dr, r, risk, mr, mrisk in trades:
        if not lo <= d <= hi:
            continue
        recs.append(qm.encode({'doy': (d - date(year, 1, 1)).days, 'minute': 600, 'model': qm.MODELS.index(model),
                               'dir': dr, 'reason': 1, 'r': qm.enc_r(r, clamps), 'risk_t': int(risk / 0.25),
                               'mr': qm.enc_r(mr if mr is not None else 0, clamps),
                               'mrisk_t': int(mrisk / 0.25) if mr is not None else 0}))
    rows = [(datetime.combine(d, datetime.min.time()) + timedelta(hours=10), 0, 0, 0, 0, 1) for d in days]
    days = [d for d in days if lo <= d <= hi]
    c = {'year': year, 'half': half, 'window': [str(lo), str(hi)], 'rth_days': qm.rth_bitmap(rows, year), 'tr': ''.join(recs),
         'eth_1801': [5, 0]}
    if gate:
        c['gate'] = gate
    return c


def test_trades_roundtrip_costs_and_refused_mirror():
    d = date(2015, 3, 2)
    c = _chunk(2015, 1, [(d, 'trend', 1, 1.5, 10.0, -0.8, 12.0), (d, 'sweep', 0, -1.0, 20.0, None, None)], [d])
    tr = st.trades_of(c)
    assert tr[0]['model'] == 'trend' and tr[0]['dir'] == 1 and tr[1]['dir'] == -1
    assert abs(st.net(tr[0], 2.0) - 1.3) < 1e-9 and abs(st.net(tr[1], 2.0) + 1.1) < 1e-9
    assert tr[1]['mr'] is None and abs(st.mnet(tr[0], 2.0) - (-0.8 - 2 / 12)) < 1e-9


def _year(y, mean_r, n_days=240, seed=1, mirror=-1.0):
    rng = np.random.default_rng(seed + y)
    days, trades = [], []
    d = date(y, 1, 5)
    while len(days) < n_days:
        if d.weekday() < 5:
            days.append(d)
            for _ in range(2):
                r = mean_r + rng.normal(0, 1.0)
                trades.append((d, 'ou_rev', 1, float(np.clip(r, -3, 6)), 12.0, mirror, 12.0))
        d += timedelta(days=1)
    return days, trades


def test_verdicts_end_to_end():
    gate = {'ref_n': 100, 'qc_n': 100, 'matched': 80, 'per_model': {'ou_rev': [100, 80]}}
    good = {}
    for y in range(2010, 2026):
        days, trades = _year(y, 0.6)
        for h in (1, 2):
            good[(y, h)] = _chunk(y, h, trades, days, gate if y >= 2023 else None)
    res = st.run(good)
    assert res['gate']['status'] == 'PASS' and res['verdict'] == 'VALIDATED', res['verdict']
    assert res['P']['control']['real_pct'] > 0.95 and res['P']['blocks_pos'] == 4
    bad = {}
    for y in range(2010, 2026):
        days, trades = _year(y, 0.0, mirror=0.2)
        for h in (1, 2):
            bad[(y, h)] = _chunk(y, h, trades, days, gate if y >= 2023 else None)
    assert st.run(bad)['verdict'] in ('REJECTED', 'INCONCLUSIVE')
    neg = {(y, h): _chunk(y, h, [(t[0], t[1], t[2], -0.5, 12.0, 0.0, 12.0) for t in _year(y, 0)[1]], _year(y, 0)[0],
                          gate if y >= 2023 else None) for y in range(2010, 2026) for h in (1, 2)}
    assert st.run(neg)['verdict'] == 'REJECTED'
    del good[(2014, 2)]
    assert st.run(good)['verdict'] == 'P INCOMPLETE'


def test_gate_counts_from_records():
    d = date(2024, 2, 5)
    c = _chunk(2024, 1, [(d, 'trend', 1, 1.0, 10.0, -1.0, 10.0), (d, 'sweep', 0, 1.0, 10.0, -1.0, 10.0)], [d])
    ref = '202402051001,7,L;202402051000,11,L;202402051000,0,S;202407011000,7,L'   # records sit at 10:00
    g = st.gate_counts(c, ref)
    assert g['ref_n'] == 3 and g['qc_n'] == 2 and g['matched'] == 1
    assert g['per_model'] == {'ou_rev': [1, 0], 'trend': [1, 1], 'sweep': [1, 0]}


def test_gate_thresholds():
    mk = lambda ref, qc, m: {(y, _h): {'gate': {'ref_n': ref, 'qc_n': qc, 'matched': m, 'per_model': {}}, 'eth_1801': [1, 0]}
                             for y in (2023, 2024, 2025) for _h in (1, 2)}
    assert st.gate(mk(100, 100, 50))['status'] == 'PASS' and st.gate(mk(100, 100, 50))['ref_n'] == 600
    assert st.gate(mk(100, 100, 49))['status'] == 'FAIL'
    assert st.gate(mk(100, 126, 90))['status'] == 'FAIL'
    assert st.gate(mk(100, 79, 60))['status'] == 'FAIL'
    assert st.verdict('FAIL', {}, {}) == 'NOT RUN (gate)'


def test_log_budget():
    # 800 trades in a half year (the reference's busiest year had 906 in 12 months) + summary must stay under QuantConnect's 10 KB per backtest (with the log prefixes)
    c = {'year': 2024, 'half': 2, 'window': ['2024-07-01', '2024-12-31'], 'bars': 470000, 'first_bar': '2023-09-03 18:01:00',
         'last_bar': '2024-12-31 16:59:00', 'signals': 5000, 'trades_all': 1200, 'trades': 900, 'mirror_refused': 30,
         'r_clamped': 0, 'eth_1801': [300, 0], 'rth_days': 'A' * 62, 'gross_mean': 0.1234, 'S1_mean': 0.0123,
         'tr': 'A' * 11 * 800, 'seconds': 300.0,
         'gate': {'ref_n': 800, 'qc_n': 800, 'matched': 600, 'per_model': {m: [70, 60] for m in qm.MODELS}}}
    import json
    s = json.dumps(c, separators=(',', ':'))
    parts = -(-len(s) // 7000)
    assert len(s) + parts * 60 < 10000, len(s)


def test_smoke_frozen_pipeline_on_their_synthetic_data():
    from data.loader import generate_synthetic_data
    df = generate_synthetic_data(days=200)
    rows = [(t.to_pydatetime(), o, h, l, c, v) for t, o, h, l, c, v in
            zip(df['datetime'], df['open'], df['high'], df['low'], df['close'], df['volume'])]
    year, half = 2024, 1
    res = qm.chunk_result([r for r in rows if r[0].date() >= date(2024, 1, 2)], year, half)
    assert res['bars'] > 0 and res['trades'] == len(res['tr']) // 11
    tr = st.trades_of(res)
    assert all(qm.window(year, half)[0] <= t['date'] <= qm.window(year, half)[1] for t in tr)
    assert all(t['risk'] >= 10.0 for t in tr)                      # their 40-tick floor survives the adapter
