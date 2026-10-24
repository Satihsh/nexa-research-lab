"""H-GEX-RANGE statistics and verdict (PREREG_GEX_RANGE.md s.2-4) from the saved QuantConnect year logs.

Usage: python gex_stats.py <logs_dir> > gex_results.json
"""
import base64
import glob
import importlib.util
import json
import math
import os
import sys
import types
from datetime import date, timedelta

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if 'AlgorithmImports' not in sys.modules:
    _stub = types.ModuleType('AlgorithmImports')
    _stub.QCAlgorithm = object
    sys.modules['AlgorithmImports'] = _stub
_spec = importlib.util.spec_from_file_location('qc_gex_main', os.path.join(HERE, 'qc_gex', 'main.py'))
qm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(qm)

BASE_N, RANK_N, NW_LAGS = 10, 252, 5
FIRST_FIT, OOS_FROM, OOS_TO = 2013, 2015, 2025
ALPHA, MIN_RED, MIN_YEARS = 0.025, 0.02, 7


def read_logs(d):
    years = {}
    for p in sorted(glob.glob(os.path.join(d, '*.txt'))):
        parts, total = {}, 0
        for line in open(p, encoding='utf-8'):
            i = line.find('NEXA_GEX ')
            if i < 0:
                continue
            head, body = line[i + 9:].split(' ', 1)
            k, n = head.split('/')
            parts[int(k)] = body.rstrip('\n')
            total = int(n)
        if parts:
            assert sorted(parts) == list(range(1, total + 1)), p
            c = json.loads(''.join(parts[k] for k in sorted(parts)))
            if c['year'] != 0:
                years[c['year']] = c
    return years


def days_of(years):
    """Chronological list of day dicts across all year chunks."""
    out = []
    for y in sorted(years):
        c = years[y]
        raw = base64.b64decode(c['rec'])
        for i in range(0, len(raw), qm.REC.size):
            r = qm.unpack(raw[i:i + qm.REC.size])
            r['date'] = date(c['year0'], 1, 1) + timedelta(days=r['day'])
            out.append(r)
    out.sort(key=lambda r: r['date'])
    return out


def trailing_rank(x):
    """Percentile of x[t] within x[t-RANK_N+1 .. t] (needs a full window); None otherwise."""
    out = [None] * len(x)
    for t in range(len(x)):
        if t + 1 < RANK_N or x[t] is None:
            continue
        w = [v for v in x[t - RANK_N + 1:t + 1] if v is not None]
        if len(w) < RANK_N * 0.9:
            continue
        out[t] = sum(1 for v in w if v <= x[t]) / len(w)
    return out


def base_ranges(rng, ok):
    """Mean range of the previous BASE_N complete sessions (the v6 RangeGuide rule); None until BASE_N exist."""
    out, hist = [], []
    for r, k in zip(rng, ok):
        out.append(sum(hist[-BASE_N:]) / BASE_N if len(hist) >= BASE_N else None)
        if k:
            hist.append(r)
    return out


def ols(X, y):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta


def nw_se(d, lags=NW_LAGS):
    d = np.asarray(d, float)
    n = len(d)
    e = d - d.mean()
    s = e @ e / n
    for L in range(1, lags + 1):
        w = 1 - L / (lags + 1)
        s += 2 * w * (e[L:] @ e[:-L]) / n
    return math.sqrt(max(s, 0) / n)


def norm_sf(z):
    return 0.5 * math.erfc(z / math.sqrt(2))


def frame(days, inst, source='spx_gex'):
    """Rows usable for instrument inst ('nq' or 'es'): date, y, ln base, rank, ln vix."""
    rng = [d[inst + '_ticks'] * qm.TICK for d in days]
    ok = [d[inst + '_ok'] and d[inst + '_ticks'] > 0 for d in days]
    base = base_ranges(rng, ok)
    if source == 'sign':
        feat = [None if d['spx_gex'] is None else (1.0 if d['spx_gex'] > 0 else 0.0) for d in days]
        rank = feat
    else:
        rank = trailing_rank([d[source] for d in days])
    rows = []
    for d, r, k, b, g in zip(days, rng, ok, base, rank):
        if not k or b is None or b <= 0 or g is None:
            continue
        rows.append({'date': d['date'], 'y': math.log(r), 'lb': math.log(b), 'g': g,
                     'lv': math.log(d['vix']) if d['vix'] else None})
    return rows


def walk_forward(rows, use_g, use_v):
    """Yearly refits; returns (dates, losses B, losses M) for OOS years, with B = same model without g."""
    out = []
    for Y in range(OOS_FROM, OOS_TO + 1):
        tr = [r for r in rows if FIRST_FIT <= r['date'].year < Y and (not use_v or r['lv'] is not None)]
        te = [r for r in rows if r['date'].year == Y and (not use_v or r['lv'] is not None)]
        if len(tr) < 100 or not te:
            continue

        def X(rs, with_g):
            cols = [np.ones(len(rs)), [r['lb'] for r in rs]]
            if use_v:
                cols.append([r['lv'] for r in rs])
            if with_g:
                cols.append([r['g'] for r in rs])
            return np.column_stack(cols)
        yt = np.array([r['y'] for r in tr])
        ye = np.array([r['y'] for r in te])
        bB = ols(X(tr, False), yt)
        bM = ols(X(tr, True), yt)
        lB = (ye - X(te, False) @ bB) ** 2
        lM = (ye - X(te, True) @ bM) ** 2
        for r, a, b in zip(te, lB, lM):
            out.append((r['date'], float(a), float(b), r))
    return out


def evaluate(rows, use_v=False):
    wf = walk_forward(rows, True, use_v)
    if not wf:
        return {'n': 0}
    lB = np.array([x[1] for x in wf])
    lM = np.array([x[2] for x in wf])
    red = 1 - lM.mean() / lB.mean()
    d = lB - lM
    se = nw_se(d)
    z = d.mean() / se if se > 0 else 0.0
    per = {}
    for x in wf:
        per.setdefault(x[0].year, [[], []])
        per[x[0].year][0].append(x[1])
        per[x[0].year][1].append(x[2])
    per_year = {str(y): round(1 - np.mean(v[1]) / np.mean(v[0]), 4) for y, v in sorted(per.items())}
    pool = [r for r in rows if r['date'].year >= FIRST_FIT and (not use_v or r['lv'] is not None)]
    cols = [np.ones(len(pool)), [r['lb'] for r in pool]] + ([[r['lv'] for r in pool]] if use_v else []) + [[r['g'] for r in pool]]
    c = float(ols(np.column_stack(cols), np.array([r['y'] for r in pool]))[-1])
    return {'n': len(wf), 'loss_B': round(float(lB.mean()), 5), 'loss_M': round(float(lM.mean()), 5),
            'reduction': round(float(red), 4), 'dm_z': round(float(z), 3), 'p': round(norm_sf(z), 5),
            'years_positive': sum(1 for v in per_year.values() if v > 0), 'years': len(per_year),
            'per_year': per_year, 'coef_g_pooled': round(c, 4)}


def b0_vs_b1(rows):
    """Is the raw 10-day mean (B0: forecast = ln base) already calibrated vs the fitted B1?"""
    wf = walk_forward(rows, False, False)
    if not wf:
        return {}
    l0 = np.mean([(x[3]['y'] - x[3]['lb']) ** 2 for x in wf])
    l1 = np.mean([x[1] for x in wf])
    return {'loss_B0': round(float(l0), 5), 'loss_B1': round(float(l1), 5), 'B1_vs_B0_reduction': round(float(1 - l1 / l0), 4)}


def quintiles(rows):
    """Actual / forecast range (B1 fitted on everything 2013+) by gamma-rank quintile, plus mean points."""
    pool = [r for r in rows if r['date'].year >= FIRST_FIT]
    if len(pool) < 50:
        return {}
    X = np.column_stack([np.ones(len(pool)), [r['lb'] for r in pool]])
    b = ols(X, np.array([r['y'] for r in pool]))
    out = {}
    for q in range(5):
        sel = [r for r in pool if q / 5 <= r['g'] < (q + 1) / 5 or (q == 4 and r['g'] == 1.0)]
        if not sel:
            continue
        ratio = [math.exp(r['y'] - (b[0] + b[1] * r['lb'])) for r in sel]
        out['Q%d' % (q + 1)] = {'n': len(sel), 'actual_over_forecast': round(float(np.mean(ratio)), 4),
                                'mean_range_pts': round(float(np.mean([math.exp(r['y']) for r in sel])), 2)}
    return out


def verdict(e):
    if not e.get('n'):
        return 'NO DATA'
    if e['reduction'] <= 0:
        return 'REJECTED'
    ok = (e['reduction'] >= MIN_RED and e['p'] <= ALPHA and e['years_positive'] >= MIN_YEARS and e['coef_g_pooled'] < 0)
    return 'VALIDATED' if ok else 'INCONCLUSIVE'


def run(years):
    days = days_of(years)
    out = {'years': sorted(years), 'days': len(days),
           'chunk_info': {str(y): {k: c.get(k) for k in ('days', 'spx_contracts_mean', 'spx_contracts_min', 'opt_seconds', 'errors')}
                          for y, c in sorted(years.items())}}
    for inst in ('nq', 'es'):
        rows = frame(days, inst)
        e = evaluate(rows)
        res = {'rows': len(rows), 'primary_M1_vs_B1': e, 'verdict': verdict(e), 'B0_vs_B1': b0_vs_b1(rows),
               'quintiles': quintiles(rows), 'secondary_vix_M2_vs_B2': evaluate(rows, use_v=True),
               'secondary_abs_gamma': evaluate(frame(days, inst, 'spx_abs')),
               'secondary_sign': evaluate(frame(days, inst, 'sign'))}
        if inst == 'nq':
            res['secondary_ndx_gex'] = evaluate(frame(days, inst, 'ndx_gex'))
        out[inst.upper()] = res
    complete = sorted(years) == list(range(2012, 2026))
    out['H_GEX_RANGE'] = out['NQ']['verdict'] if complete else 'INCOMPLETE'
    return out


if __name__ == '__main__':
    print(json.dumps(run(read_logs(sys.argv[1])), indent=1, default=str))
