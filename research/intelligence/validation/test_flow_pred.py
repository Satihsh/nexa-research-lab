"""Synthetic G1 tests for qc_flow_pred/main.py (PREREG_FLOW_PRED.md s.8). No market data. Run with .venv-ml."""
import importlib.util
import json
import os
import sys
import types
from datetime import date, timedelta

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
stub = types.ModuleType('AlgorithmImports')
stub.QCAlgorithm = object
sys.modules.setdefault('AlgorithmImports', stub)
spec = importlib.util.spec_from_file_location('qc_flow_pred_main', os.path.join(HERE, 'qc_flow_pred', 'main.py'))
fp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fp)


def weekdays(start, n):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def synth_day(rng, p0=15000.0, sig_s=0.8, drift=0.0):
    return fp.finish_day(synth_store(rng, p0, sig_s, drift))


STORE_FIELDS = ('last', 'hi', 'lo', 'vol', 'buy', 'sell', 'bbuy', 'bsell', 'ntr', 'nq', 'bsz', 'asz')


def synth_store(rng, p0=15000.0, sig_s=0.8, drift=0.0):
    """Per-second store filled vectorially. Each minute has a flow imbalance x; if drift != 0 the price drifts
    by drift * x points per second for the next 300 s (a planted aggressive-flow signal)."""
    st = fp.DayStore()
    x = rng.uniform(-1, 1, fp.NMIN)
    step = rng.normal(0, sig_s, fp.NSEC)
    if drift:
        xs = np.repeat(x, 60)
        kern = np.concatenate([np.zeros(60), np.ones(300)])  # starts after the minute closes
        step += drift * np.convolve(xs, kern)[:fp.NSEC] / 60.0
    px = p0 + np.cumsum(step)
    st.last = px.copy()
    st.hi = px + np.abs(rng.normal(0, 0.2, fp.NSEC))
    st.lo = px - np.abs(rng.normal(0, 0.2, fp.NSEC))
    v = rng.integers(1, 20, fp.NSEC).astype(float)
    xs = np.repeat(x, 60)
    st.vol, st.buy, st.sell = v, v * (1 + xs) / 2, v * (1 - xs) / 2
    st.bbuy, st.bsell = np.where(v >= 10, st.buy, 0.0), np.where(v >= 10, st.sell, 0.0)
    st.ntr = np.ones(fp.NSEC)
    st.nq = rng.integers(1, 5, fp.NSEC).astype(float)
    st.bsz, st.asz = rng.integers(1, 30, fp.NSEC).astype(float), rng.integers(1, 30, fp.NSEC).astype(float)
    return st


def synth_days(n, seed, drift):
    rng = np.random.default_rng(seed)
    return [(dt, synth_day(rng, drift=drift)) for dt in weekdays(date(2024, 1, 2), n)]


_CACHE = {}


def dataset(drift):
    if drift not in _CACHE:
        _CACHE[drift] = fp.build_dataset(synth_days(360, 7 if drift else 8, drift))
    return _CACHE[drift]


# 1 ---------------------------------------------------------------- classification
def test_classify_quote_and_tick_rule():
    assert fp.classify(100.25, 100.0, 100.25, None, 0) == 1
    assert fp.classify(100.0, 100.0, 100.25, None, 0) == -1
    assert fp.classify(100.2, 100.0, 100.25, None, 0) == 1            # above mid
    assert fp.classify(100.125, 100.0, 100.25, 100.0, 0) == 1          # at mid -> tick rule up
    assert fp.classify(100.125, 100.0, 100.25, 100.5, 0) == -1
    assert fp.classify(100.0, None, None, 100.0, -1) == -1             # no quotes, same price -> last sign
    assert fp.classify(100.0, None, None, None, 0) == 0


def test_one_sided_quote_updates():
    st = fp.DayStore()
    st.quote(0, 100.0, 0.0, 5, None)
    st.quote(1, 0.0, 100.25, None, 7)
    assert st.bid == 100.0 and st.ask == 100.25 and st.bid_sz == 5 and st.ask_sz == 7
    st.trade(2, 100.25, 3, 10)
    st.trade(2, 100.0, 12, 10)
    assert st.buy[2] == 3 and st.sell[2] == 12 and st.bsell[2] == 12 and st.bbuy[2] == 0
    assert st.hi[2] == 100.25 and st.lo[2] == 100.0 and st.last[2] == 100.0 and st.ntr[2] == 2


# 2 ---------------------------------------------------------------- barriers
def flat_day(price=100.0):
    d = {'hi': np.full(fp.NSEC, price), 'lo': np.full(fp.NSEC, price), 'last': np.full(fp.NSEC, price)}
    d['c'] = d['last'][59::60].copy()
    return d


def test_barrier_stop_first_target_time_exit():
    d = flat_day()
    k, s0 = 100, 60 * 101
    d['hi'][s0 + 10], d['lo'][s0 + 10] = 102.0, 98.0               # both in one second -> stop first
    assert fp.barrier(d, k, 300, 1.0, 1) == (-1.0, s0 + 10)
    assert fp.barrier(d, k, 300, 1.0, -1) == (-1.0, s0 + 10)
    d = flat_day()
    d['hi'][s0 + 5] = 101.5
    assert fp.barrier(d, k, 300, 1.0, 1) == (1.0, s0 + 5)
    assert fp.barrier(d, k, 300, 1.0, -1) == (-1.0, s0 + 5)
    d = flat_day()
    d['last'][s0 + 29] = 100.5                                       # 30-s horizon time exit
    r, e = fp.barrier(d, k, 30, 1.0, 1)
    assert abs(r - 0.5) < 1e-12 and e == s0 + 29
    d['hi'][s0 + 30] = 105.0                                         # outside the 30-s window: ignored
    assert fp.barrier(d, k, 30, 1.0, 1)[0] == 0.5


def test_unit_floor():
    assert fp.unit(0.1, 30) == 4 * 0.25
    assert abs(fp.unit(6.0, 900) - 6.0 * np.sqrt(15)) < 1e-12


# 3 ---------------------------------------------------------------- no look-ahead
def test_features_use_no_future_data():
    st = synth_store(np.random.default_rng(1))
    d = fp.finish_day(st)
    hist = {'sig1': 6.0, 'vbar': 600.0, 'rbar': 80.0, 'prev': d['stats']}
    X0 = fp.day_features(d, hist)
    assert X0.shape == (331, 29)
    for k in (29, 100, 300):
        cut = 60 * (k + 1)
        st2 = fp.DayStore()
        for name in STORE_FIELDS:
            a = getattr(st, name).copy()
            a[cut:] = a[cut:][::-1] * 1.7 + 3                          # a different future after T
            setattr(st2, name, a)
        X1 = fp.day_features(fp.finish_day(st2), hist)
        j = int(np.nonzero(fp.DEC_K == k)[0][0])
        assert np.allclose(X0[:j + 1], X1[:j + 1]), k
        assert not np.allclose(X0[j + 1:], X1[j + 1:])


# 4 ---------------------------------------------------------------- profile
def test_value_area_known_profile():
    bins = np.arange(10)
    vols = np.array([1, 1, 2, 5, 10, 6, 3, 1, 1, 0], float)          # total 30, 70 % = 21
    poc, vah, val = fp.value_area(bins, vols)
    assert poc == 4 * 0.25
    # from POC 10: add 6 (16), then 5 vs 3 -> 5 (21) -> stop: area bins 3..5
    assert (vah, val) == (5 * 0.25, 3 * 0.25)


# 5 ---------------------------------------------------------------- walk-forward
def test_folds_never_train_on_test_quarter():
    dates = weekdays(date(2024, 1, 2), 420)
    fl = fp.folds(dates)
    assert len(fl) >= 2
    for tr, te, tq in fl:
        assert max(tr) < min(te)
        assert all(fp.quarter(dates[i]) == tq for i in te)
        assert len({fp.quarter(dates[i]) for i in tr}) >= 4


def test_delta_uses_training_only():
    ds = dataset(0.0)
    fl = fp.folds(ds['dates'])
    tr, te, _ = fl[0]
    Y = fp.labels_y(ds['lab'][300]['gl'])
    cols = list(range(29))
    m1, d1 = fp.train_with_delta(ds['X'], Y, tr, ds['dates'], cols)
    Y2 = Y.copy()
    Y2[te] = 1 - np.clip(Y2[te], 0, 1)                                 # scramble the test quarter
    m2, d2 = fp.train_with_delta(ds['X'], Y2, tr, ds['dates'], cols)
    assert d1 == d2 and np.allclose(m1[1].coef_, m2[1].coef_)


# 6 ---------------------------------------------------------------- trading rule
def test_trade_day_cap_and_no_overlap():
    p = np.full(331, 0.9)
    lab = {'gl': np.ones(331), 'gs': -np.ones(331), 'u': 4.0,
           'el': 60 * (fp.DEC_K + 1) + 299.0, 'es': 60 * (fp.DEC_K + 1) + 299.0}
    tr = fp.trade_day(p, lab, 0.1, fp.COST['NQ'])
    assert len(tr) == 3
    assert [t['j'] for t in tr] == [0, 5, 10]                          # each 5-min trade blocks the next 4 minutes
    assert all(t['dir'] == 1 and abs(t['net'][1] - (1 - 2 / 4.0)) < 1e-12 for t in tr)
    assert fp.trade_day(np.full(331, 0.5), lab, 0.1, fp.COST['NQ']) == []


# 7 ---------------------------------------------------------------- placebo
def test_day_shift_moves_day_keeps_minute():
    Y = np.arange(10)[:, None] * 1000 + np.arange(331)[None, :]
    tr = np.arange(8)
    Ys = fp.day_shift(Y, tr, 3)
    assert (Ys[8:] == Y[8:]).all()
    assert (Ys[tr] % 1000 == Y[tr] % 1000).all()                       # same minute
    assert not (Ys[tr] == Y[tr]).all()                                 # different day
    assert sorted((Ys[tr] // 1000)[:, 0]) == list(range(8))


# 8 ---------------------------------------------------------------- end to end
def test_planted_flow_signal_found():
    res = fp.run_all(dataset(0.023), 'NQ', n_placebo=2)
    h5 = res['H']['300']
    assert h5['verdict'] == 'VALIDATED', json.dumps(h5)[:600]
    assert h5['abl']['B']['adds'] is True
    assert h5['bss'] > 0
    json.dumps(res)


def test_noise_market_not_validated():
    res = fp.run_all(dataset(0.0), 'NQ', n_placebo=2)
    assert res['overall'] != 'VALIDATED', res['overall']
    assert all(r['verdict'] != 'VALIDATED' for r in res['H'].values())


# 9 ---------------------------------------------------------------- verdict and log budget
def test_verdict_logic():
    st = {'S1': {'n': 500, 'mean': 0.03, 'ci': [0.01, 0.05], 'p': 0.004}, 'q_pos': 4, 'n_q': 6}
    assert fp.verdict(st, 0.0) == 'VALIDATED'
    assert fp.verdict(dict(st, q_pos=3), 0.0) == 'INCONCLUSIVE'       # needs ceil(2*6/3) = 4
    assert fp.verdict(st, 0.1) == 'INCONCLUSIVE'
    assert fp.verdict(dict(st, S1=dict(st['S1'], p=0.02)), 0.0) == 'INCONCLUSIVE'
    assert fp.verdict(dict(st, S1=dict(st['S1'], mean=0.02)), 0.0) == 'INCONCLUSIVE'
    assert fp.verdict(dict(st, S1=dict(st['S1'], mean=-0.01)), 0.0) == 'REJECTED'
    assert fp.verdict(dict(st, S1=dict(st['S1'], n=99)), 0.0) == 'INSUFFICIENT-N'
    assert fp.overall(['REJECTED', 'INSUFFICIENT-N']) == 'REJECTED'
    assert fp.overall(['REJECTED', 'INCONCLUSIVE']) == 'INCONCLUSIVE'
    assert fp.overall(['INCONCLUSIVE', 'VALIDATED']) == 'VALIDATED'


def test_log_budget_and_chunks():
    ds = dataset(0.023)
    res = fp.run_all(ds, 'NQ', n_placebo=2)
    for h, r in res['H'].items():                                       # worst case: coefficients for all 4 H
        r.setdefault('coef', fp.final_coefs(ds, int(h), list(range(29))))
    res.update({'skipped': {'incomplete': 12, 'roll': 8}, 'rung': 1, 'wall_s': 99999})
    text = json.dumps(res, separators=(',', ':'))
    lines = ['NEXA_FP_PART %d/%d %s' % c for c in fp.log_chunks(text)]
    assert sum(len(x) for x in lines) < 9500, sum(len(x) for x in lines)
    assert ''.join(p for _, _, p in fp.log_chunks(text)) == text
