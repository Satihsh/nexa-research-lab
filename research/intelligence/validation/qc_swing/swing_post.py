"""H-SWING post-processing (descriptive only; the verdict comes from the frozen run).
Reads the QC log, writes swing_results.json, prints the descriptive DSR (PREREG_SWING_TREND s.6)
and the micro-contract feasibility table (s.5). No market data is read here."""
from __future__ import annotations

import json
import math
import os
import sys
from statistics import NormalDist

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, 'logs_virtual_red_parrot.txt')
OUT = os.path.join(HERE, 'swing_results.json')
N = NormalDist()
EULER = 0.5772156649

# Smallest CME contract per market: (symbol, multiplier, verified?). Full-size used where no same-underlying micro is known.
MICRO = {
    'ES': ('MES', 5.0, True), 'NQ': ('MNQ', 2.0, True), 'YM': ('MYM', 0.5, True), 'RTY': ('M2K', 5.0, True),
    'GC': ('MGC', 10.0, True), 'SI': ('SIL', 1000.0, True), 'HG': ('MHG', 2500.0, True),
    'CL': ('MCL', 100.0, True), 'NG': ('MNG', 1000.0, False),
    '6E': ('M6E', 12500.0, True), '6J': ('MJY', 1250000.0, False), '6B': ('M6B', 6250.0, True),
    '6A': ('M6A', 10000.0, True), '6C': ('MCD', 10000.0, False),
    'ZN': ('ZN', 1000.0, True), 'ZB': ('ZB', 1000.0, True), 'ZF': ('ZF', 1000.0, True),
    'ZC': ('ZC', 5000.0, True), 'ZS': ('ZS', 5000.0, True), 'ZW': ('ZW', 5000.0, True),
}


def load():
    with open(LOG) as f:
        for line in f:
            i = line.find('NEXA_SWING_RESULT ')
            if i >= 0:
                return json.loads(line[i + len('NEXA_SWING_RESULT '):])
    sys.exit('NEXA_SWING_RESULT not found')


def dsr(sr, n_obs, skew, sr_trials, n_trials, kurt=3.0):
    """Bailey & Lopez de Prado (2014) deflated Sharpe on per-period Sharpe ratios. Kurtosis not logged: normal (3) assumed."""
    m = sum(sr_trials) / len(sr_trials)
    var = sum((s - m) ** 2 for s in sr_trials) / (len(sr_trials) - 1)
    sr0 = math.sqrt(var) * ((1 - EULER) * N.inv_cdf(1 - 1 / n_trials) + EULER * N.inv_cdf(1 - 1 / (n_trials * math.e)))
    z = (sr - sr0) * math.sqrt(n_obs - 1) / math.sqrt(1 - skew * sr + (kurt - 1) / 4 * sr * sr)
    return N.cdf(z), sr0


def main():
    r = load()
    with open(OUT, 'w') as f:
        json.dump(r, f, indent=1, sort_keys=True)
    trials = ['P', 'V-DON', 'V-MA', 'V-IDX']
    d_sr = {v: r[v]['sharpe_ann'] / math.sqrt(252) for v in trials}
    print('daily Sharpe:', {k: round(v, 5) for k, v in d_sr.items()})
    for v in ('P', 'V-IDX'):
        for nt in (4, 161):
            p, sr0 = dsr(d_sr[v], r[v]['n_days'], r[v]['skew'], list(d_sr.values()), nt)
            print(f'DSR {v} @ {nt} trials: {p:.3f} (SR0 daily {sr0:.5f})')
    print('\nfeasibility: account at which 1 smallest contract = rule weight (w = min(3, 0.40/vol), equal-weight over N)')
    rows = []
    for k, m in r['markets'].items():
        sym, mult, ok = MICRO[k]
        notional = m['last_close'] * mult
        w = min(3.0, 0.40 / m['last_vol'])
        rows.append((k, sym, ok, notional, w, notional * 20 / w, notional * 2 / w if k in ('ES', 'NQ') else None))
    for k, sym, ok, notional, w, a20, a2 in rows:
        extra = f'  V-IDX(N=2): ${a2:,.0f}' if a2 else ''
        print(f'{k:4s} {sym:4s}{"" if ok else "?"}  notional ${notional:>10,.0f}  w {w:4.2f}  P(N=20): ${a20:>12,.0f}{extra}')
    print(f'\nP needs every market at >= 1 contract: ${max(a for *_, a, _ in rows):,.0f}')


if __name__ == '__main__':
    main()
