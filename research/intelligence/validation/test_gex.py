"""Synthetic tests for qc_gex/main.py and gex_stats.py (PREREG_GEX_RANGE.md s.7). No market data."""
import base64
import importlib.util
import math
import os
import random
import sys
import types
from datetime import date, datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
stub = types.ModuleType('AlgorithmImports')
stub.QCAlgorithm = object
sys.modules.setdefault('AlgorithmImports', stub)
spec = importlib.util.spec_from_file_location('gex_stats', os.path.join(HERE, 'gex_stats.py'))
gs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gs)
qm = gs.qm


def test_gex_formula_and_signs():
    net, ab, n = qm.gex_from_rows([(True, 100, 0.002), (False, 50, 0.004), (True, 0, 1.0), (False, 10, float('nan'))], 4000.0)
    k = 100 * 4000.0 ** 2 * 0.01
    assert n == 2 and abs(net - (100 * 0.002 - 50 * 0.004) * k) < 1e-6 and abs(ab - (100 * 0.002 + 50 * 0.004) * k) < 1e-6
    assert qm.gex_from_rows([], 4000.0) == (None, None, 0) and qm.gex_from_rows([(True, 1, 1)], 0)[0] is None


def test_log_code_roundtrip():
    for x in (3.2e9, -7.5e8, 12.0, -1.0e10):
        v = qm.dec_log(qm.enc_log(x, True), True)
        assert abs(v - x) / abs(x) < 0.0013
    assert qm.enc_log(None, True) == 0 and qm.enc_log(0.0, False) == 0 and qm.dec_log(0, True) is None


def test_record_pack_unpack_and_budget():
    b = qm.pack(364, 1234, 456, -2.5e9, 9e9, 1e8, 3e8, 17.25, qm.flags_of(390, 389, 5000, 0, 17.25))
    assert len(b) == 17
    r = qm.unpack(b)
    assert r['day'] == 364 and r['nq_ticks'] == 1234 and r['es_ticks'] == 456 and r['vix'] == 17.25
    assert r['nq_ok'] and r['es_ok'] and r['spx_ok'] and not r['ndx_ok'] and r['vix_ok']
    assert r['spx_gex'] < 0 and abs(r['spx_abs'] - 9e9) / 9e9 < 0.002
    assert len(base64.b64encode(b * 253)) + 600 < 9500        # a full year of records + summary fits 10 KB


def test_rth_window():
    assert not qm.rth_index(datetime(2020, 1, 2, 9, 30)) and qm.rth_index(datetime(2020, 1, 2, 9, 31))
    assert qm.rth_index(datetime(2020, 1, 2, 16, 0)) and not qm.rth_index(datetime(2020, 1, 2, 16, 1))


def test_base_is_previous_ten_complete_sessions():
    rng = list(range(1, 16))
    ok = [True] * 15
    ok[3] = False                          # day with value 4 is incomplete: skipped, as RangeGuide skips it
    b = gs.base_ranges(rng, ok)
    assert b[:11] == [None] * 11
    assert b[11] == sum([1, 2, 3, 5, 6, 7, 8, 9, 10, 11]) / 10     # day 12 sees only prior days
    assert b[14] == sum(range(5, 15)) / 10


def test_trailing_rank_no_lookahead():
    x = list(range(300))
    r = gs.trailing_rank(x)
    assert r[250] is None and r[251] == 1.0 and r[299] == 1.0
    x2 = x[:]
    x2[299] = -1
    assert gs.trailing_rank(x2)[298] == r[298]                # changing a later value never moves an earlier rank


def test_newey_west_and_normal():
    d = [1.0] * 50 + [-1.0] * 50
    assert gs.nw_se(d) > 0
    assert abs(gs.norm_sf(1.959964) - 0.025) < 1e-4


def _days(effect, seed=7, start=date(2012, 1, 2), n=3500):
    """Synthetic days: true range follows a vol process; with effect, high SPX gamma shrinks the range."""
    rng = random.Random(seed)
    out, vol, d = [], 100.0, start
    gam = 0.0
    while len(out) < n:
        if d.weekday() < 5:
            vol = max(20.0, vol * math.exp(rng.gauss(0, 0.05)) * (100.0 / vol) ** 0.02)
            gam = 0.95 * gam + rng.gauss(0, 1)
            mult = math.exp(-0.25 * math.tanh(gam / 3)) if effect else 1.0
            r_nq = vol * mult * math.exp(rng.gauss(0, 0.25))
            r_es = r_nq / 3.5
            out.append({'date': d, 'nq_ticks': int(r_nq / 0.25), 'es_ticks': int(r_es / 0.25), 'nq_ok': True, 'es_ok': True,
                        'spx_gex': gam * 1e9 + 1, 'spx_abs': abs(gam) * 1e9 + 5e9, 'ndx_gex': gam * 1e8 + 1,
                        'ndx_abs': 1e8, 'vix': vol / 6.0, 'spx_ok': True, 'ndx_ok': True, 'vix_ok': True})
        d += timedelta(days=1)
    return out


def _years(days):
    years = {}
    by = {}
    for d in days:
        by.setdefault(d['date'].year, []).append(d)
    for y, ds in by.items():
        raw = b''.join(qm.pack((d['date'] - date(y, 1, 1)).days, d['nq_ticks'], d['es_ticks'], d['spx_gex'], d['spx_abs'],
                               d['ndx_gex'], d['ndx_abs'], d['vix'], qm.flags_of(390, 390, 1, 1, d['vix'])) for d in ds)
        years[y] = {'year': y, 'year0': y, 'days': len(ds), 'rec': base64.b64encode(raw).decode()}
    return years


def test_planted_effect_validates_and_noise_does_not():
    yrs = {y: v for y, v in _years(_days(True)).items() if 2012 <= y <= 2025}
    res = gs.run(yrs)
    assert res['NQ']['verdict'] == 'VALIDATED', res['NQ']['primary_M1_vs_B1']
    assert res['NQ']['primary_M1_vs_B1']['coef_g_pooled'] < 0
    q = res['NQ']['quintiles']
    assert q['Q1']['actual_over_forecast'] > q['Q5']['actual_over_forecast']
    yrs0 = {y: v for y, v in _years(_days(False, seed=11)).items() if 2012 <= y <= 2025}
    v0 = gs.run(yrs0)['NQ']['verdict']
    assert v0 in ('REJECTED', 'INCONCLUSIVE'), v0


def test_verdict_rules():
    base = {'n': 2000, 'reduction': 0.03, 'p': 0.01, 'years_positive': 8, 'coef_g_pooled': -0.1}
    assert gs.verdict(base) == 'VALIDATED'
    assert gs.verdict({**base, 'coef_g_pooled': 0.1}) == 'INCONCLUSIVE'
    assert gs.verdict({**base, 'reduction': 0.019}) == 'INCONCLUSIVE'
    assert gs.verdict({**base, 'p': 0.03}) == 'INCONCLUSIVE'
    assert gs.verdict({**base, 'years_positive': 6}) == 'INCONCLUSIVE'
    assert gs.verdict({**base, 'reduction': -0.001}) == 'REJECTED'
    assert gs.verdict({'n': 0}) == 'NO DATA'


def test_walk_forward_uses_only_past_years():
    days = _days(True, n=2600)
    rows = gs.frame(days, 'nq')
    wf = gs.walk_forward(rows, True, False)
    assert wf and min(x[0].year for x in wf) == 2015
    # the 2015 forecasts must not change when 2016+ data is altered
    days2 = [dict(d) for d in days]
    for d in days2:
        if d['date'].year >= 2016:
            d['nq_ticks'] = 1
    wf2 = gs.walk_forward(gs.frame(days2, 'nq'), True, False)
    a = [x[2] for x in wf if x[0].year == 2015]
    b = [x[2] for x in wf2 if x[0].year == 2015]
    assert a == b
