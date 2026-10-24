"""Synthetic G1 tests for qc_swing_fwd/main.py (PREREG_SWING_FWD.md s.7). No market data is read."""
from __future__ import annotations

import importlib.util
import inspect
import os
import sys
import types
from datetime import date, timedelta

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
stub = types.ModuleType('AlgorithmImports')
stub.QCAlgorithm = object
sys.modules.setdefault('AlgorithmImports', stub)


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, rel))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


sw = load('qc_swing_main', 'qc_swing/main.py')
fw = load('qc_swing_fwd_main', 'qc_swing_fwd/main.py')

SHARED = ('block_indices', '_f', 'boot_mean', 'ewma_vol', 'month_end_flags', 'size', 'decisions',
          'market_pnl', 'portfolio', 'series_stats', 'verdict', 'run_all')
CONSTS = ('SEED', 'B_BOOT', 'BLOCK', 'EVAL_FROM', 'LOOKBACK', 'WARM_EXTRA', 'COM', 'TARGET_VOL', 'CAP',
          'COMMISSION_RT', 'TICKS', 'MARKETS', 'VARIANTS')


def bdays(n, start=date(2009, 1, 1)):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def bdays_until(end, start=date(2009, 1, 1)):
    out, d = [], start
    while d <= end:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def mkdata(dates, keys=('ES', 'NQ', 'GC')):
    n = len(dates)
    data = {}
    for i, k in enumerate(keys):
        rng = np.random.default_rng(i)
        c = 100.0 * np.cumprod(1 + 0.0004 * (1 if i != 2 else -1) + 0.01 * rng.standard_normal(n))
        data[k] = {'dates': dates, 'o': list(c), 'h': list(c * 1.002), 'l': list(c * 0.998), 'c': list(c),
                   'rolls': [j % 63 == 0 for j in range(n)]}
    return data


PROPS = {'ES': (0.25, 50.0), 'NQ': (0.25, 20.0), 'GC': (0.1, 100.0)}


# 1. shared engine identical to H-SWING (source text and constants)
def test_engine_identical():
    for name in SHARED:
        assert inspect.getsource(getattr(fw, name)) == inspect.getsource(getattr(sw, name)), name
    for name in CONSTS:
        assert getattr(fw, name) == getattr(sw, name), name


# 2. LONG-IDX / BH-IDX weights
def test_control_weights():
    d = bdays(500)
    c = 100 * np.cumprod(1 + 0.01 * np.random.default_rng(5).standard_normal(500))
    lg = sw.decisions(d, c, c, c, 'LONG')
    li = fw.decisions_fwd(d, c, c, c, 'LONG-IDX')
    bh = fw.decisions_fwd(d, c, c, c, 'BH-IDX')
    assert np.array_equal(np.isnan(lg), np.isnan(li)) and np.allclose(lg[~np.isnan(lg)], li[~np.isnan(li)])
    assert np.array_equal(np.isnan(lg), np.isnan(bh)) and (bh[~np.isnan(bh)] == 1.0).all()
    p = fw.decisions_fwd(d, c, c, c, 'P')
    assert np.allclose(np.nan_to_num(p, nan=9), np.nan_to_num(sw.decisions(d, c, c, c, 'P'), nan=9))


# 3. window boundaries
def test_windows():
    assert fw.WINDOWS['HIST'] == (date(2011, 1, 3), date(2026, 7, 21))
    assert fw.WINDOWS['FWD'] == (date(2026, 7, 22), date(2027, 12, 31))
    assert fw.WINDOWS['POOLED'] == (date(2011, 1, 3), date(2027, 12, 31))
    days = [date(2026, 7, 20), date(2026, 7, 21), date(2026, 7, 22), date(2027, 12, 31), date(2028, 1, 3)]
    x = [1, 2, 3, 4, 5]
    dh, xh = fw.windowed(days, x, *fw.WINDOWS['HIST'])
    df, xf = fw.windowed(days, x, *fw.WINDOWS['FWD'])
    assert list(xh) == [1, 2] and list(xf) == [3, 4] and dh[-1] == date(2026, 7, 21) and df[0] == date(2026, 7, 22)


# 4. HIST statistics equal H-SWING run_all when data ends before HIST_END
def test_hist_matches_run_all():
    d = bdays(1300)                          # 2009 -> ~2013, ends before HIST_END
    data = mkdata(d)
    a = sw.run_all(data, PROPS)
    b = fw.run_fwd(data, PROPS)
    for v in ('P', 'V-IDX', 'LONG'):
        assert b[v]['HIST']['S1'] == a[v]['S1'], v
        for key in ('ann_return', 'ann_vol', 'max_dd', 'pos_day_share', 'pos_month_share', 'per_year'):
            assert b[v]['HIST'][key] == a[v][key], (v, key)
        assert b[v]['HIST']['S0_mean'] == a[v]['S0_mean'] and b[v]['HIST']['S2_mean'] == a[v]['S2_mean']
    assert b['controls']['P_minus_LONG_HIST']['theta'] == a['P_minus_LONG']['theta']
    assert b['controls']['P_minus_LONG_HIST']['ci95'] == a['P_minus_LONG']['ci95']
    assert b['P']['FWD'] == {'n_days': 0}
    assert b['fwd_verdict']['P'] == 'INSUFFICIENT-N' and b['binding'] is False


# 5. difference statistics on common dates only
def test_diff_stats_common_dates():
    d1, d2, d3 = date(2012, 1, 3), date(2012, 1, 4), date(2012, 1, 5)
    sa = {d1: 0.03, d2: 0.01, d3: 0.02}
    sb = {d2: 0.005, d3: 0.03}
    r = fw.diff_stats(sa, sb, date(2011, 1, 3), date(2026, 7, 21))
    assert r['n_days'] == 2 and r['theta'] == pytest.approx((0.005 - 0.01) / 2)
    r2 = fw.diff_stats(sa, sb, date(2012, 1, 5), date(2012, 1, 5))
    assert r2['n_days'] == 1 and r2['theta'] == pytest.approx(-0.01)


# 6. A1 control verdict
def test_control_verdict():
    assert fw.control_verdict({'theta': -1e-5, 'ci95': [-2e-5, 1e-5]}) == 'DRIFT ONLY'
    assert fw.control_verdict({'theta': 0.0, 'ci95': [-2e-5, 1e-5]}) == 'DRIFT ONLY'
    assert fw.control_verdict({'theta': 1e-5, 'ci95': [1e-6, 2e-5]}) == 'TIMING VALUE'
    assert fw.control_verdict({'theta': 1e-5, 'ci95': [-1e-6, 2e-5]}) == 'UNRESOLVED'
    assert fw.control_verdict({'theta': None, 'ci95': [None, None]}) is None


# 7. forward verdict
def _r(fn, f_theta, f_hi, p_theta, p_lo, blocks_pos=4, months=200):
    return {'FWD': {'n_days': fn, 'S1': {'theta': f_theta, 'ci95': [f_theta - 1, f_hi]}},
            'POOLED': {'n_days': 4300, 'n_months': months, 'blocks_pos': blocks_pos,
                       'S1': {'theta': p_theta, 'ci95': [p_lo, p_theta + 1]}}}


def test_fwd_verdict():
    mu = 2e-4
    assert fw.fwd_verdict(_r(249, 1e-3, 1e-2, 3e-4, 1e-5), mu) == 'INSUFFICIENT-N'
    assert fw.fwd_verdict(_r(300, 1e-3, 1e-2, 3e-4, 1e-5), mu) == 'CONFIRMED'
    assert fw.fwd_verdict(_r(300, 1e-3, 1e-2, 3e-4, 1e-5, blocks_pos=2), mu) == 'INCONCLUSIVE'
    assert fw.fwd_verdict(_r(300, -1e-4, 1e-2, 3e-4, 1e-5), mu) == 'INCONCLUSIVE'      # fwd mean <= 0
    assert fw.fwd_verdict(_r(300, 1e-4, 1e-2, 3e-4, -1e-6), mu) == 'INCONCLUSIVE'      # pooled CI touches 0
    assert fw.fwd_verdict(_r(300, -5e-4, 1.5e-4, 3e-4, 1e-5), mu) == 'FAILED'          # fwd CI upper < mu_H
    assert fw.fwd_verdict(_r(300, 1e-3, 1e-2, 0.0, -1e-5), mu) == 'FAILED'              # pooled mean <= 0


# 8. end-to-end smoke across the HIST / FWD boundary
def test_run_fwd_smoke_boundary():
    d = bdays_until(date(2027, 3, 31))
    res = fw.run_fwd(mkdata(d), PROPS)
    assert res['data_end'] == '2027-03-31' and res['binding'] is False
    for v in fw.FWD_VARIANTS:
        h, f, p = res[v]['HIST'], res[v]['FWD'], res[v]['POOLED']
        assert h['n_days'] + f['n_days'] == p['n_days'], v
        assert f['n_days'] > 0
    assert res['fwd_verdict']['P'] == 'INSUFFICIENT-N'                       # < 250 forward days
    assert res['A1_verdict'] in ('DRIFT ONLY', 'TIMING VALUE', 'UNRESOLVED')
    assert set(res['A0']) == {'P', 'V-IDX', 'P_minus_LONG'}
    assert res['controls']['V-IDX_minus_BH-IDX_FWD']['n_days'] == res['V-IDX']['FWD']['n_days']


# 9. v2 (DEVIATIONS_SWING_FWD D-1): every function except the logging is source-identical to the v1 file that ran Part A
def test_v2_statistics_identical_to_v1():
    v1 = load('qc_swing_fwd_v1', 'qc_swing_fwd/main_v1_be25c85c.py')
    names = [n for n, o in vars(v1).items() if inspect.isfunction(o) and o.__module__ == v1.__name__]
    assert 'run_fwd' in names and 'fwd_verdict' in names
    for n in names:
        assert inspect.getsource(getattr(fw, n)) == inspect.getsource(getattr(v1, n)), n
    for n in ('HIST_END', 'FWD_START', 'FWD_END', 'WINDOWS', 'FWD_VARIANTS', 'IDX', 'REF', 'MIN_FWD_DAYS', 'CONTROLS'):
        assert getattr(fw, n) == getattr(v1, n), n


# 10. chunked logging is lossless and every line fits under QC's ~8,192-char cut
def test_log_chunks_roundtrip():
    d = bdays_until(date(2027, 3, 31))
    import json
    text = json.dumps(fw.run_fwd(mkdata(d), PROPS), separators=(',', ':'))
    parts = fw.log_chunks(text)
    assert len(parts) >= 2 and ''.join(p for _, _, p in parts) == text
    assert all(n == len(parts) for _, n, _ in parts) and [i for i, _, _ in parts] == list(range(1, len(parts) + 1))
    assert max(len('NEXA_SWING_FWD_PART %d/%d %s' % t) for t in parts) < 8000
    assert fw.log_chunks('') == [(1, 1, '')]
