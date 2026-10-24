"""T2 volatility-forecast validation (PREREG_T2_VOLATILITY.md, hash in PREREG_HASHES.txt).

Research only. Reads Pepperstone M1 canonical bars, builds server-day OHLC and 5-minute realised variance,
produces walk-forward calibrated variance forecasts (ATR, close-to-close, Parkinson, GK, RS, Yang-Zhang, RV means,
EWMA, HAR) and evaluates QLIKE / MSE-log, Diebold-Mariano (Newey-West), directional usefulness, regime stability and
parameter sensitivity per split. Output: t2_results.json + t2_tables.md
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

M1 = '~/NEXA-Agent-Lab/filesnexa/NEXA/data/pepperstone/m1_canonical/PEPPERSTONE_{}_M1_canonical.csv.gz'
OUT = os.path.dirname(os.path.abspath(__file__))
SYMBOLS = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
SPLITS = {'discovery': ('2017-01-01', '2022-12-31'), 'validation': ('2023-01-01', '2024-12-31'),
          'holdout': ('2025-01-01', '2026-09-30')}
MIN_TRAIN = 250


def daily_frame(sym: str) -> pd.DataFrame:
    d = pd.read_csv(M1.format(sym), usecols=['time_server', 'open', 'high', 'low', 'close'])
    d['ts'] = pd.to_datetime(d.time_server)
    d['day'] = d.ts.dt.normalize()
    d = d[d.day.dt.dayofweek < 5]
    # 5-minute closes within each server day (last close of each 5-min bucket)
    d['b5'] = d.ts.dt.floor('5min')
    c5 = d.groupby(['day', 'b5'], sort=True)['close'].last().reset_index()
    lc = np.log(c5.close.to_numpy())
    r = np.diff(lc, prepend=np.nan)          # first return of each day = vs previous day's last 5-min close
    c5['r2'] = r ** 2
    rv = c5.groupby('day').r2.sum(min_count=1)
    g = d.groupby('day')
    out = pd.DataFrame({'O': g.open.first(), 'H': g.high.max(), 'L': g.low.min(), 'C': g.close.last(),
                        'bars': g.close.size(), 'RV': rv})
    out = out.iloc[1:]                         # first day has no previous close
    med = out.bars.median()
    out['thin'] = out.bars < 0.8 * med
    return out


def forecasts(df: pd.DataFrame) -> pd.DataFrame:
    O, H, L, C = (np.log(df[k]) for k in 'OHLC')
    Cp = C.shift(1)
    f = pd.DataFrame(index=df.index)
    tr = pd.concat([df.H - df.L, (df.H - df.C.shift(1)).abs(), (df.L - df.C.shift(1)).abs()], axis=1).max(axis=1)

    def wilder(x, n):
        return x.ewm(alpha=1.0 / n, adjust=False).mean()
    for n in (7, 14, 28):
        f[f'ATR{n}'] = wilder(tr / df.C, n) ** 2          # ATR as a fraction of price, squared
    rcc = C - Cp
    f['CC20'] = (rcc ** 2).rolling(20).mean()
    hl = (H - L) ** 2
    f['PK20'] = hl.rolling(20).mean() / (4 * math.log(2))
    gk = 0.5 * (H - L) ** 2 - (2 * math.log(2) - 1) * (C - O) ** 2
    f['GK20'] = gk.rolling(20).mean()
    rs = (H - C) * (H - O) + (L - C) * (L - O)
    f['RS20'] = rs.rolling(20).mean()
    ro = O - Cp                                        # overnight (open vs prior close)
    rc = C - O
    for n in (5, 10, 20, 60):
        k = 0.34 / (1.34 + (n + 1) / (n - 1))
        so = ro.rolling(n).var()
        sc = rc.rolling(n).var()
        srs = rs.rolling(n).mean()
        f[f'YZ{n}'] = so + k * sc + (1 - k) * srs
    f['RVM20'] = df.RV.rolling(20).mean()
    f['RV1'] = df.RV
    f['EWMA'] = df.RV.ewm(alpha=1 - 0.94, adjust=False).mean()
    return f


def walk_forward(df: pd.DataFrame, f: pd.DataFrame, h: int) -> pd.DataFrame:
    """Calibrated variance forecasts for target mean(RV[d+1..d+h]); monthly refit, expanding window."""
    tgt = pd.concat([df.RV.shift(-k) for k in range(1, h + 1)], axis=1).mean(axis=1)
    if h == 1:                                   # thin days excluded as targets (prereg §1)
        nxt_thin = df.thin.shift(-1).astype('boolean').fillna(True).astype(bool)
        tgt[nxt_thin] = np.nan
    lt = np.log(tgt)
    lrv = np.log(df.RV)
    har = pd.DataFrame({'d': lrv, 'w': np.log(df.RV.rolling(5).mean()), 'm': np.log(df.RV.rolling(22).mean())})
    out = pd.DataFrame(index=df.index)
    out['target'] = tgt
    months = df.index.to_period('M')
    cols = list(f.columns)
    for m in months.unique():
        start = m.to_timestamp()
        test_idx = df.index[months == m]
        # training pairs whose target is fully known before the month starts
        train_end_pos = df.index.searchsorted(start) - h
        if train_end_pos < MIN_TRAIN:
            continue
        tr_idx = df.index[:train_end_pos]
        y = lt.loc[tr_idx]
        for c in cols + ['HAR']:
            if c == 'HAR':
                X = har.loc[tr_idx]
                Xt = har.loc[test_idx]
            else:
                X = np.log(f.loc[tr_idx, [c]])
                Xt = np.log(f.loc[test_idx, [c]])
            ok = y.notna() & np.isfinite(X).all(axis=1)
            if ok.sum() < MIN_TRAIN:
                continue
            A = np.column_stack([np.ones(ok.sum()), X[ok].to_numpy()])
            beta, *_ = np.linalg.lstsq(A, y[ok].to_numpy(), rcond=None)
            res = y[ok].to_numpy() - A @ beta
            s2 = res.var()
            At = np.column_stack([np.ones(len(Xt)), Xt.to_numpy()])
            out.loc[test_idx, c] = np.exp(At @ beta + 0.5 * s2)
    return out


def qlike(rv, f):
    x = rv / f
    return x - np.log(x) - 1


def nw_se(d: np.ndarray, lags: int = 5) -> float:
    d = d - d.mean()
    n = len(d)
    g0 = (d @ d) / n
    s = g0
    for l in range(1, lags + 1):
        w = 1 - l / (lags + 1)
        s += 2 * w * (d[l:] @ d[:-l]) / n
    return math.sqrt(max(s, 1e-300) / n)


def dm(la: pd.Series, lb: pd.Series) -> tuple[float, float]:
    d = (la - lb).dropna().to_numpy()
    if len(d) < 30:
        return float('nan'), float('nan')
    t = d.mean() / nw_se(d)
    return float(t), float(2 * (1 - stats.norm.cdf(abs(t))))


def bh(p: list[float]) -> list[float]:
    p = np.asarray(p, float)
    n = np.isfinite(p).sum()
    order = np.argsort(np.where(np.isfinite(p), p, np.inf))
    q = np.full(len(p), np.nan)
    prev = 1.0
    for rank in range(n, 0, -1):
        i = order[rank - 1]
        prev = min(prev, p[i] * n / rank)
        q[i] = prev
    return q.tolist()


def block_boot_hit(hits: np.ndarray, block: int = 20, B: int = 2000, seed: int = 7) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    n = len(hits)
    nb = int(np.ceil(n / block))
    means = []
    for _ in range(B):
        starts = rng.integers(0, max(n - block, 1), nb)
        s = np.concatenate([hits[a:a + block] for a in starts])[:n]
        means.append(s.mean())
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def main() -> int:
    results = {'prereg': 'PREREG_T2_VOLATILITY.md', 'symbols': {}}
    dm_rows = []
    for sym in SYMBOLS:
        df = daily_frame(sym)
        f = forecasts(df)
        sres = {'days': int(len(df)), 'thin_days': int(df.thin.sum()), 'first': str(df.index[0].date()),
                'last': str(df.index[-1].date())}
        for h in (1, 5):
            wf = walk_forward(df, f, h)
            names = [c for c in wf.columns if c != 'target']
            hres = {}
            disc = wf.loc[SPLITS['discovery'][0]:SPLITS['discovery'][1], 'target']
            cuts = np.nanpercentile(disc, [100 / 3, 200 / 3])
            for split, (a, b) in SPLITS.items():
                w = wf.loc[a:b].dropna(subset=['target'])
                w = w.dropna(subset=['ATR14', 'HAR', 'YZ20'])
                if len(w) < 50:
                    continue
                rv = w.target
                L = {c: qlike(rv, w[c]) for c in names}
                M = {c: (np.log(rv) - np.log(w[c])) ** 2 for c in names}
                tab = {}
                for c in names:
                    t_atr, p_atr = dm(L[c], L['ATR14'])
                    t_har, p_har = dm(L[c], L['HAR'])
                    tab[c] = {'n': int(L[c].notna().sum()), 'qlike': float(L[c].mean()), 'mse_log': float(M[c].mean()),
                              'dm_t_vs_ATR14': t_atr, 'p_vs_ATR14': p_atr, 'dm_t_vs_HAR': t_har, 'p_vs_HAR': p_har}
                    if h == 1:
                        dm_rows.append({'sym': sym, 'split': split, 'model': c, 'p_vs_ATR14': p_atr, 'p_vs_HAR': p_har,
                                        't_vs_ATR14': t_atr, 't_vs_HAR': t_har})
                # directional usefulness (h=1 meaningful; reported for both)
                med60 = df.RV.rolling(60).median().reindex(w.index)
                up = (rv > med60)
                for c in ('ATR14', 'YZ20', 'HAR', 'RVM20', 'EWMA', 'CC20', 'PK20'):
                    pred = w[c] > med60
                    hits = (pred == up)[med60.notna()].to_numpy().astype(float)
                    lo, hi = block_boot_hit(hits)
                    nxt_range = np.log(df.H / df.L).shift(-1).reindex(w.index)
                    rho = stats.spearmanr(w[c], nxt_range, nan_policy='omit').statistic
                    tab[c].update({'hit_rate_above_median': float(hits.mean()), 'hit_ci95': [lo, hi],
                                   'spearman_next_range': float(rho)})
                # regime stability
                terc = np.digitize(rv, cuts)
                for c in ('ATR14', 'YZ20', 'HAR', 'RVM20', 'EWMA'):
                    tab[c]['qlike_by_rv_tercile'] = [float(L[c][terc == k].mean()) for k in range(3)]
                    tab[c]['qlike_by_year'] = {str(y): float(v) for y, v in L[c].groupby(L[c].index.year).mean().items()}
                hres[split] = tab
            sres[f'h{h}'] = hres
        results['symbols'][sym] = sres
        print(sym, 'done', flush=True)
    # BH across symbols x models for the holdout, h=1
    for key in ('p_vs_ATR14', 'p_vs_HAR'):
        for split in SPLITS:
            rows = [r for r in dm_rows if r['split'] == split and r['model'] not in (('ATR14',) if key == 'p_vs_ATR14' else ('HAR',))]
            qs = bh([r[key] for r in rows])
            for r, q in zip(rows, qs):
                r[key.replace('p_', 'q_')] = q
    results['dm_h1'] = dm_rows
    with open(os.path.join(OUT, 't2_results.json'), 'w') as fh:
        json.dump(results, fh, indent=1, default=float)
    return 0


if __name__ == '__main__':
    sys.exit(main())
