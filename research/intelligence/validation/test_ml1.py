"""Synthetic G1 tests for qc_ml1/main.py (PREREG_ML1.md s.8). No market data. Run with .venv-ml (sklearn)."""
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
spec = importlib.util.spec_from_file_location('qc_ml1_main', os.path.join(HERE, 'qc_ml1', 'main.py'))
ml = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ml)


def weekdays(start, n):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def synth_day(rng, p0, sig=0.0004, signal=0.0):
    """390 one-minute bars; if signal != 0, after bar 30 the drift follows the sign of the first-30-minute move."""
    r = rng.normal(0, sig, ml.NBARS)
    first = r[:30].sum()
    r[30:] += signal * np.sign(first) * sig
    c = p0 * np.exp(np.cumsum(r))
    o = np.concatenate([[p0], c[:-1]])
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, sig / 3, ml.NBARS)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, sig / 3, ml.NBARS)))
    v = rng.integers(50, 500, ml.NBARS).astype(float)
    return {'o': o, 'h': h, 'l': l, 'c': c, 'v': v}


def synth_days(n, start=date(2019, 1, 2), signal=0.0, seed=0):
    rng = np.random.default_rng(seed)
    days, pn, pe = [], 10000.0, 3000.0
    for d in weekdays(start, n):
        nq = synth_day(rng, pn, signal=signal)
        es = synth_day(rng, pe, sig=0.0003, signal=signal)
        days.append({'date': d, 'NQ': nq, 'ES': es})
        pn, pe = float(nq['c'][-1]), float(es['c'][-1])
    return days


# 1. bracket: stop first, time exit, 15:59 cap
def test_bracket_rules():
    c = np.full(ml.NBARS, 100.0)
    h, l = c + 0.1, c - 0.1
    h2, l2 = h.copy(), l.copy()
    h2[50], l2[50] = 103, 97                      # both barriers in one bar
    assert ml.bracket(h2, l2, c, 40, 2.0, +1) == (-1.0, 50)
    assert ml.bracket(h2, l2, c, 40, 2.0, -1) == (-1.0, 50)
    h3 = h.copy(); h3[45] = 102.5
    assert ml.bracket(h3, l, c, 40, 2.0, +1) == (1.0, 45)
    c4 = c.copy(); c4[100] = 101.0               # no barrier: time exit at k+60
    assert ml.bracket(h, l, c4, 40, 2.0, +1) == (0.5, 100)
    assert ml.bracket(h, l, c, 329, 2.0, +1)[1] == 389     # 15:00 decision -> 15:59 exit
    assert ml.bracket(h, l, c, 350, 2.0, -1)[1] == 389     # capped at the last bar


# 2. sigma60 and other history values use previous days only
def test_history_uses_prior_days_only():
    days = synth_days(30, seed=1)
    st = [ml.day_stats(ml._f64(d['NQ'])) for d in days]
    h1 = ml.history(st, 25)
    st2 = list(st)
    st2[25] = ml.day_stats(ml._f64(synth_day(np.random.default_rng(99), 10000.0, sig=0.01)))
    h2 = ml.history(st2, 25)
    assert h1['sig60'] == h2['sig60'] and h1['sigd'] == h2['sigd'] and h1['rv'] == h2['rv']
    assert ml.history(st, 19) is None


# 3. no feature at decision bar k uses bars after k (perturbation test)
def test_no_lookahead_in_features():
    days = synth_days(25, seed=2)
    st_t = [ml.day_stats(ml._f64(d['NQ'])) for d in days]
    st_x = [ml.day_stats(ml._f64(d['ES'])) for d in days]
    ht, hx = ml.history(st_t, 24), ml.history(st_x, 24)
    ht['prev_ret'] = 0.001
    d, x = ml._f64(days[24]['NQ']), ml._f64(days[24]['ES'])
    base = ml.features(d, x, ht, hx, 1.0, 2)
    for j, k in enumerate(ml.DEC_K):
        d2 = {key: val.copy() for key, val in d.items()}
        x2 = {key: val.copy() for key, val in x.items()}
        for arr in (d2, x2):
            for key in ('o', 'h', 'l', 'c'):
                arr[key][k + 1:] *= 1.05
            arr['v'][k + 1:] *= 7
        pert = ml.features(d2, x2, ht, hx, 1.0, 2)
        assert np.allclose(np.nan_to_num(base[j], nan=-9), np.nan_to_num(pert[j], nan=-9)), k
    assert len(base[0]) == len(ml.FEATURES) == 20


# 4. at most 2 trades a day, no overlap
def test_trade_day_limits():
    rows = [{'date': date(2020, 1, 2), 'k': k, 'long': 1.0, 'short': -1.0, 'exit_long': k + 30, 'exit_short': k + 30,
             'stop': 10.0} for k in ml.DEC_K]
    p = np.full(len(rows), 0.9)
    tr = ml.trade_day(rows, p, 0.1, (1.0, 2.0, 3.0))
    assert len(tr) == 2 and tr[0]['k'] == 29 and tr[1]['k'] == 59       # 44 skipped (busy until 59)
    assert tr[0]['net'][1] == 1.0 - 0.2
    p2 = np.full(len(rows), 0.55)
    assert ml.trade_day(rows, p2, 0.1, (1.0, 2.0, 3.0)) == []
    p3 = np.full(len(rows), 0.1)
    t3 = ml.trade_day(rows, p3, 0.1, (1.0, 2.0, 3.0))
    assert t3[0]['dir'] == -1 and t3[0]['gross'] == -1.0


# 5 + 6. delta calibration and walk-forward never use test-year rows
def test_walk_forward_and_calibration_isolation(monkeypatch=None):
    seen = []
    orig_fit = ml.fit

    def spy_fit(X, y, seed=ml.SEED):
        seen.append(len(y))
        return orig_fit(X, y, seed)

    rows = ml.build_rows(synth_days(4 * 252, start=date(2018, 1, 2), seed=3), 'NQ')
    years = sorted({r['date'].year for r in rows})
    calls = []
    orig_twd = ml.train_with_delta

    def spy_twd(train, placebo_seed=None):
        calls.append(max(r['date'] for r in train))
        return orig_twd(train, placebo_seed)

    ml.fit, ml.train_with_delta = spy_fit, spy_twd
    old = (ml.VAL_YEARS, ml.HOLD_FROM)
    try:
        ml.VAL_YEARS, ml.HOLD_FROM = [2021], date(2021, 7, 1)
        days = synth_days(4 * 252, start=date(2018, 1, 2), seed=3)
        res = ml.run_target(days, 'NQ', n_placebo=1)
    finally:
        ml.fit, ml.train_with_delta = orig_fit, orig_twd
        ml.VAL_YEARS, ml.HOLD_FROM = old
    assert calls[0] < date(2021, 1, 1)                     # fold 2021 trained on < 2021 only
    assert all(c < date(2021, 7, 1) for c in calls[1:])    # hold-out and placebo models: < HOLD_FROM only
    keep, X, y = ml.labelled([r for r in rows if r['date'].year < 2021])
    yr = np.array([r['date'].year for r in keep])
    assert seen[0] == int((yr <= years[-3 - (years[-1] - 2020)]).sum()) or seen[0] < len(y)
    assert 'verdict' in res and res['folds']['2021']['n_train_rows'] > 0


# 7. placebo: circular day-shift (DEVIATIONS_ML1 D-1) keeps label structure, breaks the feature link
def test_placebo_day_shift():
    rows = []
    for i in range(50):
        for k in ml.DEC_K:
            rows.append({'date': date(2020, 1, 1) + timedelta(days=i), 'k': k, 'x': [i, k], 'long': (1.0 if (i % 2) else -1.0)})
    keep, X, y = ml.day_shift_labels(rows, 3)
    days = sorted({r['date'] for r in rows})
    m = int(np.random.default_rng(3).integers(5, 45))
    for r, yy in zip(keep, y):
        src = (days.index(r['date']) + m) % 50
        assert yy == (1 if src % 2 else 0)
    assert len(keep) == len(rows)
    keep2, X2, y2 = ml.day_shift_labels(rows, 3)
    assert np.array_equal(y, y2)                                  # deterministic per seed


def test_permute_within_day_helper():
    rows = [{'date': date(2020, 1, 2 + (i // 21))} for i in range(63)]
    y = np.random.default_rng(0).integers(0, 2, 63)
    yp = ml.permute_within_day(rows, y, 5)
    for d in range(3):
        assert sorted(y[d * 21:(d + 1) * 21]) == sorted(yp[d * 21:(d + 1) * 21])
    assert not np.array_equal(y, yp)


# 8. bootstrap and verdict
def test_bootstrap_and_verdict():
    x = np.full(600, 0.15) + np.random.default_rng(1).normal(0, 0.05, 600)
    s = {'S1': ml.boot_mean(x), 'blocks_pos': 4}
    assert s['S1']['ci95'][0] > 0
    assert ml.verdict(s, s, 0.0) == 'PROP-READY'
    s2 = {'S1': ml.boot_mean(x - 0.1), 'blocks_pos': 4}
    assert ml.verdict(s2, s2, 0.0) == 'VALIDATED (G4)'
    assert ml.verdict(s2, s2, 0.10) == 'INCONCLUSIVE'
    neg = {'S1': ml.boot_mean(-x), 'blocks_pos': 0}
    assert ml.verdict(s, neg, 0.0) == 'REJECTED'
    assert ml.verdict(s, {'n_trades': 0}, 0.0) == 'INSUFFICIENT-N'


# 9. log chunking lossless
def test_log_chunks():
    text = json.dumps({'a': list(range(5000))})
    parts = ml.log_chunks(text)
    assert ''.join(p for _, _, p in parts) == text and all(len(p) <= ml.LOG_CHUNK for _, _, p in parts)


# end-to-end sanity: a planted momentum signal is found; pure noise is not
def test_end_to_end_signal_and_noise():
    old = (ml.VAL_YEARS, ml.HOLD_FROM)
    try:
        ml.VAL_YEARS, ml.HOLD_FROM = [2022], date(2023, 1, 1)
        sig = ml.run_target(synth_days(6 * 260, start=date(2018, 1, 2), signal=0.08, seed=4), 'NQ', n_placebo=2)
        noise = ml.run_target(synth_days(6 * 260, start=date(2018, 1, 2), signal=0.0, seed=5), 'NQ', n_placebo=2)
    finally:
        ml.VAL_YEARS, ml.HOLD_FROM = old
    assert sig['H']['S1']['mean'] > 0.05 and sig['H']['trades_per_day'] > 0.5
    assert abs(noise['H']['S1']['mean']) < 0.15
    assert noise['H']['S1']['mean'] < sig['H']['S1']['mean']
    assert max(sig['placebo_H_means']) < sig['H']['S1']['mean']   # day-shift placebo cannot reproduce a real signal
