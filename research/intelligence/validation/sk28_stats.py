"""H-SK28-OOS statistics and verdict (PREREG_SK28_OOS.md s.3-5) from the saved QuantConnect chunk logs.

Usage: python sk28_stats.py <logs_dir> > sk28_results.json
<logs_dir> holds one log file per chunk (any name ending .txt) with the 'NEXA_SK28 i/n {json}' lines.
"""
import glob
import json
import math
import os
import sys
from datetime import date, datetime, timedelta

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'qc_sk28'))
import importlib.util
import types

if 'AlgorithmImports' not in sys.modules:
    _stub = types.ModuleType('AlgorithmImports')
    _stub.QCAlgorithm = object
    sys.modules['AlgorithmImports'] = _stub
_spec = importlib.util.spec_from_file_location('qc_sk28_main', os.path.join(HERE, 'qc_sk28', 'main.py'))
qm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(qm)

COSTS = (1.0, 2.0, 3.0)
SEED, B_BOOT, BLOCK, N_CTRL = 20261023, 2000, 20, 2000
P_LATE_FROM = date(2018, 1, 2)
GATE_MATCH, GATE_RATIO = 0.50, (0.80, 1.25)
MIN_TRADES, BAR = 300, 0.025
MLL, MNQ_USD = 2000.0, 2.0


def _f(x, nd=5):
    if x is None:
        return None
    x = float(x)
    return round(x, nd) if math.isfinite(x) else None


def block_indices(n, rng, L=BLOCK):
    if n <= L:
        return rng.integers(0, n, n)
    nb = int(math.ceil(n / L))
    st = rng.integers(0, n - L + 1, nb)
    return (st[:, None] + np.arange(L)[None, :]).ravel()[:n]


def read_logs(d):
    """{(year, half): chunk dict} from every log file in d (multi-part lines re-joined)."""
    chunks = {}
    for p in sorted(glob.glob(os.path.join(d, '*.txt'))):
        parts = {}
        for line in open(p, encoding='utf-8'):
            i = line.find('NEXA_SK28 ')
            if i < 0:
                continue
            head, body = line[i + 10:].split(' ', 1)
            k, n = head.split('/')
            parts[int(k)] = body.rstrip('\n')
            total = int(n)
        if parts:
            assert sorted(parts) == list(range(1, total + 1)), p
            c = json.loads(''.join(parts[k] for k in sorted(parts)))
            chunks[(c['year'], c['half'])] = c
    return chunks


def trades_of(c):
    y = c['year']
    s = c['tr']
    out = []
    for i in range(0, len(s), 11):
        r = qm.decode(s[i:i + 11])
        out.append({'date': date(y, 1, 1) + timedelta(days=r['doy']), 'minute': r['minute'],
                    'model': qm.MODELS[r['model']], 'dir': 1 if r['dir'] else -1, 'reason': qm.REASONS[r['reason']],
                    'r': (r['r'] - qm.R_LIM - 1) / 100.0, 'risk': r['risk_t'] * qm.TICK,
                    'mr': (r['mr'] - qm.R_LIM - 1) / 100.0 if r['mrisk_t'] else None,
                    'mrisk': r['mrisk_t'] * qm.TICK if r['mrisk_t'] else None})
    return out


def days_of(c):
    y = c['year']
    lo, hi = (date.fromisoformat(x) for x in c['window'])
    bits = ''.join(format(qm.B64.index(ch), '06b') for ch in c['rth_days'])
    return [date(y, 1, 1) + timedelta(days=k) for k, b in enumerate(bits) if b == '1'
            and lo <= date(y, 1, 1) + timedelta(days=k) <= hi]


def net(t, cost):
    return t['r'] - cost / t['risk']


def mnet(t, cost):
    return t['mr'] - cost / t['mrisk']


def stats(days, trades, control=False):
    """days: chronological dates of the set; trades: list of trade dicts inside the set."""
    days = sorted(set(days) | {t['date'] for t in trades})
    ix = {d: i for i, d in enumerate(days)}
    n, nt = len(days), len(trades)
    out = {'days': n, 'trades': nt}
    if nt == 0:
        out['S1'] = {'mean': None}
        return out
    dsum, dcnt = np.zeros(n), np.zeros(n)
    for t in trades:
        dsum[ix[t['date']]] += net(t, COSTS[1])
        dcnt[ix[t['date']]] += 1
    rng = np.random.default_rng(SEED)
    reps = np.empty(B_BOOT)
    for b in range(B_BOOT):
        k = block_indices(n, rng)
        cc = dcnt[k].sum()
        reps[b] = dsum[k].sum() / cc if cc > 0 else np.nan
    r = reps[np.isfinite(reps)]
    out['S1'] = {'mean': _f(dsum.sum() / nt), 'ci': [_f(np.percentile(r, 2.5)), _f(np.percentile(r, 97.5))],
                 'p': _f((1 + np.sum(r <= 0)) / (len(r) + 1), 4)}
    out['S0'] = _f(np.mean([net(t, COSTS[0]) for t in trades]))
    out['S2'] = _f(np.mean([net(t, COSTS[2]) for t in trades]))
    out['gross'] = _f(np.mean([t['r'] for t in trades]))
    rs = np.array([net(t, COSTS[1]) for t in trades])
    out['win'] = _f(np.mean(rs > 0), 4)
    out['avg_win'] = _f(rs[rs > 0].mean() if (rs > 0).any() else None, 3)
    out['avg_loss'] = _f(rs[rs <= 0].mean() if (rs <= 0).any() else None, 3)
    out['max_win'] = _f(rs.max(), 2)
    out['median_risk_pts'] = _f(np.median([t['risk'] for t in trades]), 2)
    q = np.array_split(np.arange(n), 4)
    out['blocks'] = [_f(dsum[k].sum() / dcnt[k].sum(), 4) if dcnt[k].sum() > 0 else None for k in q]
    out['blocks_pos'] = int(sum(1 for v in out['blocks'] if (v or 0) > 0))
    td = dsum[dcnt > 0]
    out['green'] = _f(np.mean(td > 0), 4)
    eq = np.concatenate([[0.0], np.cumsum(dsum)])
    out['max_dd_R'] = _f(np.max(np.maximum.accumulate(eq) - eq), 2)
    run = best = 0
    for x in rs:
        run = run + 1 if x < 0 else 0
        best = max(best, run)
    out['lose_streak'] = best
    grp = lambda key: {k: [len(v), _f(np.mean(v), 3)] for k, v in sorted(_group(trades, key).items())}
    out['per_year'] = grp(lambda t: str(t['date'].year))
    out['per_model'] = grp(lambda t: t['model'])
    out['long_short'] = grp(lambda t: 'long' if t['dir'] > 0 else 'short')
    out['exit_reasons'] = {k: v[0] for k, v in grp(lambda t: t['reason']).items()}
    out['topstep50k_1mnq'] = topstep(days, trades)
    if control:
        out['control'] = control_test(trades, out['S1']['mean'])
    return out


def _group(trades, key):
    g = {}
    for t in trades:
        g.setdefault(key(t), []).append(net(t, COSTS[1]))
    return g


def control_test(trades, real_mean):
    """Each trade takes its real or mirror outcome with p = 1/2; refused mirrors are left out of that replicate."""
    real = np.array([net(t, COSTS[1]) for t in trades])
    mir = np.array([mnet(t, COSTS[1]) if t['mr'] is not None else np.nan for t in trades])
    rng = np.random.default_rng(SEED)
    pm = np.empty(N_CTRL)
    for i in range(N_CTRL):
        pick = np.where(rng.random(len(real)) < 0.5, real, mir)
        ok = np.isfinite(pick)
        pm[i] = pick[ok].mean() if ok.any() else np.nan
    pv = pm[np.isfinite(pm)]
    pct = float(np.mean(pv < real_mean)) if (real_mean is not None and len(pv)) else None
    return {'n': N_CTRL, 'mirror_refused': int(np.sum(~np.isfinite(mir))), 'mean': _f(pv.mean()),
            'p95': _f(np.percentile(pv, 95)), 'real_pct': _f(pct, 4)}


def topstep(days, trades):
    """Illustrative: 1 MNQ per trade at S1, $2,000 trailing end-of-day loss limit locking at the start balance."""
    by = {}
    for t in trades:
        by[t['date']] = by.get(t['date'], 0.0) + (t['r'] * t['risk'] - COSTS[1]) * MNQ_USD
    bal = hi = 0.0
    breach = None
    for d in sorted(by):
        bal += by[d]
        if breach is None and bal <= min(hi - MLL, 0.0):
            breach = str(d)
        hi = max(hi, bal)
    return {'final_usd': _f(bal, 0), 'first_breach': breach}


def gate_counts(c, ref):
    """Per-chunk gate counts from the QC per-trade records vs the reference (same rule as qm.match_ref)."""
    lo, hi = (date.fromisoformat(x) for x in c['window'])
    qc_rows = [(datetime.combine(t['date'], datetime.min.time()) + timedelta(minutes=t['minute']),
                qm.MODELS.index(t['model']), 'L' if t['dir'] > 0 else 'S') for t in trades_of(c)]
    ref_rows = qm.parse_ref(ref, lo, hi)
    matched, per = qm.match_ref(ref_rows, qc_rows)
    return {'ref_n': len(ref_rows), 'qc_n': len(qc_rows), 'matched': matched,
            'per_model': {qm.MODELS[k]: v for k, v in sorted(per.items())}}


def gate(chunks, ref=None):
    if ref is not None:
        for k, c in chunks.items():
            if k[0] > qm.P_TO.year and 'tr' in c:
                c['gate'] = gate_counts(c, ref)
    g = [c['gate'] for y, c in sorted(chunks.items()) if 'gate' in c]
    if len(g) < 6:
        return {'status': 'INCOMPLETE', 'chunks': len(g)}
    ref_n = sum(x['ref_n'] for x in g)
    qc_n = sum(x['qc_n'] for x in g)
    matched = sum(x['matched'] for x in g)
    per = {}
    for x in g:
        for m, (a, b) in x['per_model'].items():
            per.setdefault(m, [0, 0])
            per[m][0] += a
            per[m][1] += b
    rate = matched / ref_n if ref_n else 0.0
    ratio = qc_n / ref_n if ref_n else 0.0
    ok = rate >= GATE_MATCH and GATE_RATIO[0] <= ratio <= GATE_RATIO[1]
    return {'status': 'PASS' if ok else 'FAIL', 'ref_n': ref_n, 'qc_n': qc_n, 'matched': matched,
            'match_rate': _f(rate, 4), 'count_ratio': _f(ratio, 4),
            'per_model': {m: [a, b, _f(b / a if a else None, 3)] for m, (a, b) in sorted(per.items())},
            'eth_1801': [sum(chunks[y]['eth_1801'][0] for y in chunks if 'gate' in chunks[y]),
                         sum(chunks[y]['eth_1801'][1] for y in chunks if 'gate' in chunks[y])]}


def verdict(gate_status, p, inn):
    if gate_status != 'PASS':
        return 'NOT RUN (gate)'
    if p['trades'] < MIN_TRADES:
        return 'INSUFFICIENT-N'
    m = p['S1']['mean']
    if m is None or m <= 0:
        return 'REJECTED'
    c = p.get('control', {})
    ok = (m >= BAR and (p['S1']['ci'][0] or -1) > 0 and p['S1']['p'] <= 0.05 and p['blocks_pos'] >= 3
          and (inn.get('S1', {}).get('mean') or -1) > 0 and c.get('p95') is not None and m > c['p95'])
    return 'VALIDATED' if ok else 'INCONCLUSIVE'


def run(chunks, ref=None):
    out = {'chunks': ['%d-H%d' % k for k in sorted(chunks)], 'gate': gate(chunks, ref)}
    pd_, pt, idd, it = [], [], [], []
    for (y, h), c in sorted(chunks.items()):
        (pd_ if y <= qm.P_TO.year else idd).extend(days_of(c))
        (pt if y <= qm.P_TO.year else it).extend(trades_of(c))
    out['chunk_info'] = {'%d-H%d' % y: {k: c.get(k) for k in ('bars', 'first_bar', 'last_bar', 'signals', 'trades_all', 'trades',
                                                     'mirror_refused', 'r_clamped', 'eth_1801', 'seconds')}
                         for y, c in sorted(chunks.items())}
    if it:
        out['IN'] = stats(idd, it)
    p_keys = sorted(k for k in chunks if k[0] <= qm.P_TO.year)
    if p_keys:
        out['P_chunks_present'] = ['%d-H%d' % k for k in p_keys]
        out['P'] = stats(pd_, pt, control=True)
        out['P_late'] = stats([d for d in pd_ if d >= P_LATE_FROM], [t for t in pt if t['date'] >= P_LATE_FROM])
        complete = p_keys == [(y, h) for y in range(qm.P_FROM.year, qm.P_TO.year + 1) for h in (1, 2)]
        out['verdict'] = verdict(out['gate']['status'], out['P'], out.get('IN', {})) if complete else 'P INCOMPLETE'
    return out


if __name__ == '__main__':
    from ref_trades import REF
    print(json.dumps(run(read_logs(sys.argv[1]), REF), indent=1, default=str))
