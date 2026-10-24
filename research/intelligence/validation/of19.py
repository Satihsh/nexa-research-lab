#!/usr/bin/env python3
"""OF-19: relative initial-balance width vs outcome of an accepted break
(PREREG_OF19_RELATIVE_IB.md; inherits PREREG_OF_COMMON.md).

Usage: python of19.py --stage disc|val|full
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import date

import numpy as np
import pandas as pd
from scipy.stats import norm

import of_common as oc

NS = (10, 20, 60)
MS = (15, 30, 60)
END_MIN = 1440
N2_REPS = 1000
NULL_DRAWS = 50
NULL_REPS = 1000
MFE_NULL = math.sqrt(2.0 / math.pi)


def find_break(sm, o, h, l, c, a, IBH, IBL, m, end_min=END_MIN):
    """First bar t >= a+60 (with t+m <= last minute) whose close is beyond the IB; acceptance over (t, t+m]."""
    elig = np.where((sm >= a + 60) & (sm + m <= end_min - 1))[0]
    if len(elig) == 0:
        return None
    cc = c[elig]
    hit = np.where((cc > IBH) | (cc < IBL))[0]
    if len(hit) == 0:
        return None
    k = int(elig[hit[0]])
    beta = 1 if c[k] > IBH else -1
    t = int(sm[k])
    win = np.where((sm > t) & (sm <= t + m))[0]
    if beta == 1:
        acc = bool((l[win] >= IBH).all())
    else:
        acc = bool((h[win] <= IBL).all())
    t_a_pos = int(np.where(sm <= t + m)[0][-1])
    return {'t_pos': k, 'beta': beta, 'accepted': acc, 't_a_pos': t_a_pos, 't_a_min': t + m}


def trade_outcome(sm, o, h, l, c, entry_pos, beta, level, spread, comm):
    """Long buys at bid+spread, sells at bid; short sells at bid, buys at bid+spread. Stop when price trades back
    inside the IB (long: low < level; short: high > level); exit at the level or the gapping open; else last close."""
    if beta == 1:
        entry = o[entry_pos] + spread
    else:
        entry = o[entry_pos]
    D = beta * (entry - level)
    if not D > 0:
        return None
    exit_px, how = None, 'E'
    for k in range(entry_pos, len(sm)):
        if beta == 1 and l[k] < level:
            exit_px = o[k] if (k > entry_pos and o[k] < level) else level
            how = 'stop'; break
        if beta == -1 and h[k] > level:
            exit_px = o[k] if (k > entry_pos and o[k] > level) else level
            how = 'stop'; break
    if exit_px is None:
        exit_px = c[-1]
    if beta == 1:
        pnl = exit_px - entry - comm
    else:
        pnl = entry - (exit_px + spread) - comm
    return {'D': D, 'R': pnl / D, 'exit': how, 'entry': entry}


def variance_share(S: oc.Sym) -> np.ndarray:
    acc = np.zeros(1440); nd = 0
    for i in range(len(S.days)):
        if S.split[i] != 0 or not S.valid[i] or not oc.is_eval_day(S, i):
            continue
        sl = S.bars(i)
        c = S.c[sl]; sm = S.smin[sl]
        r = np.diff(np.log(c))
        tot = float((r ** 2).sum())
        if tot <= 0:
            continue
        np.add.at(acc, sm[1:], r ** 2 / tot)
        nd += 1
    share = acc / nd
    tail = np.cumsum(share[::-1])[::-1]               # tail[k] = sum_{j>=k} share[j]
    tail_after = np.r_[tail[1:], 0.0]                  # sum_{j>k}
    return tail_after


# ----------------------------------------------------------------------------- per-session records
def build(S: oc.Sym, anchor: str, max_split: int, tail_after: np.ndarray):
    sym = S.sym
    sess = []          # all valid sessions (for RIB history), incl. those without sigma
    for i in range(1, len(S.days)):
        if not S.valid[i] or S.split[i] > max_split:
            continue
        d = date.fromisoformat(S.days[i])
        a = oc.anchor_smin(sym, anchor, d)
        idx, a_bar = oc.session(S, i, a)
        if a_bar is None:
            continue
        ib = oc.ib_window(S, idx, a)
        if ib is None:
            continue
        IBH, IBL, _ = ib
        rec = {'i': i, 'day': S.days[i], 'split': int(S.split[i]), 'year': d.year, 'wd': d.weekday(),
               'IB': IBH - IBL, 'IBH': IBH, 'IBL': IBL, 'sig': float(S.sig[i]), 'sprd': float(S.sprd[i]),
               'eval': bool(oc.is_eval_day(S, i) and np.isfinite(S.sig[i]) and S.sig[i] > 0)}
        sm, o, h, l, c = S.smin[idx], S.o[idx], S.h[idx], S.l[idx], S.c[idx]
        for m in MS:
            ev = find_break(sm, o, h, l, c, a, IBH, IBL, m)
            if ev is None:
                rec[f'acc{m}'] = 0; rec[f'brk{m}'] = 0
                continue
            rec[f'brk{m}'] = 1
            rec[f'acc{m}'] = int(ev['accepted'])
            rec[f'beta{m}'] = ev['beta']
            if not ev['accepted'] or not rec['eval']:
                continue
            beta = ev['beta']; level = IBH if beta == 1 else IBL
            Pa = float(c[ev['t_a_pos']]); CE = float(c[-1])
            sh = float(tail_after[int(sm[ev['t_a_pos']])])
            srem = rec['sig'] * math.sqrt(max(sh, 0.0))
            dist = beta * (Pa - level)
            p0 = float(norm.cdf(dist / srem)) if srem > 0 else (1.0 if dist > 0 else 0.5)
            y1 = int(beta * (CE - level) > 0)
            rec[f'y1{m}'] = y1; rec[f'p0{m}'] = p0; rec[f'e{m}'] = y1 - p0
            after = slice(ev['t_a_pos'] + 1, len(sm))
            if srem > 0 and ev['t_a_pos'] + 1 < len(sm):
                ext = h[after].max() if beta == 1 else l[after].min()
                rec[f'mfe{m}'] = beta * (ext - Pa) / srem
            if m == 30:
                ep = ev['t_a_pos'] + 1
                if ep < len(sm):
                    rec['entry_min'] = int(sm[ep])
                    tr = trade_outcome(sm, o, h, l, c, ep, beta, level, rec['sprd'], oc.commission(sym, float(o[ep])))
                    if tr is None:
                        rec['trade_skip'] = 'entry_inside_IB'
                    else:
                        cost = oc.commission(sym, tr['entry']) + rec['sprd']
                        if cost > 0.20 * tr['D']:
                            rec['trade_skip'] = 'cost_floor'
                        else:
                            rec['tradeR'] = tr['R']; rec['tradeD'] = tr['D']; rec['trade_exit'] = tr['exit']
        sess.append(rec)
    df = pd.DataFrame(sess)
    for N in NS:
        med = df.IB.rolling(N, min_periods=N).median().shift(1)
        df[f'RIB{N}'] = df.IB / med
    df['IBR'] = df.IB / df.sig
    return df


def classes(df: pd.DataFrame, col: str) -> tuple[np.ndarray, list]:
    disc = df[(df.split == 0) & df['eval']][col].dropna()
    cuts = list(np.percentile(disc, [100 / 3, 200 / 3]))
    v = df[col].to_numpy()
    k = np.digitize(v, cuts).astype(float)
    k[~np.isfinite(v)] = np.nan
    return k, cuts


def th_a(e, cls, acc, idx=None):
    if idx is not None:
        e, cls, acc = e[idx], cls[idx], acc[idx]
    s = acc & (cls == 0); L = acc & (cls == 2)
    if s.sum() == 0 or L.sum() == 0:
        return np.nan
    return e[s].mean() - e[L].mean()


def th_b(e, cls, acc, idx=None):
    if idx is not None:
        e, cls, acc = e[idx], cls[idx], acc[idx]
    s = acc & (cls == 0)
    return e[s].mean() if s.sum() else np.nan


def cell(df: pd.DataFrame, N: int, m: int, max_split: int, perm: bool, rng) -> dict:
    ev = df[df['eval']].reset_index(drop=True)
    cls, cuts = classes(df, f'RIB{N}')
    cls = cls[df['eval'].to_numpy()]
    e = ev.get(f'e{m}', pd.Series(np.nan, index=ev.index)).to_numpy(float)
    acc = np.isfinite(e) & np.isfinite(cls)
    e = np.nan_to_num(e)
    sp = ev.split.to_numpy()
    out = {'N': N, 'm': m, 'tercile_cuts_RIB': cuts, 'n_sessions': int(len(ev)),
           'n_accepted_by_class': {nm: int((acc & (cls == k)).sum()) for k, nm in enumerate(('SMALL', 'MID', 'LARGE'))},
           'E1_by_class_pooled': {nm: oc._f(e[acc & (cls == k)].mean()) if (acc & (cls == k)).any() else None
                                  for k, nm in enumerate(('SMALL', 'MID', 'LARGE'))}}
    for nm, fn in (('theta19a', th_a), ('theta19b', th_b)):
        per = {}
        for s in range(max_split + 1):
            pos = np.where(sp == s)[0]
            if len(pos) == 0:
                continue
            ee, cc, aa = e[pos], cls[pos], acc[pos]
            reps = oc.bootstrap(lambda ix: fn(ee, cc, aa, ix), len(pos))
            per[oc.SPLIT_NAMES[s]] = oc.boot_summary(fn(ee, cc, aa), reps)
        reps = oc.bootstrap(lambda ix: fn(e, cls, acc, ix), len(ev))
        out[nm] = {'per_split': per, 'pooled': oc.boot_summary(fn(e, cls, acc), reps)}
    if perm:
        th = th_a(e, cls, acc)
        cnt = 0
        for _ in range(N2_REPS):
            c2 = cls.copy()
            for s in np.unique(sp):
                ix = np.where((sp == s) & acc)[0]
                c2[ix] = c2[ix][rng.permutation(len(ix))]
            cnt += th_a(e, c2, acc) >= th
        out['p_N2_permutation'] = (1 + cnt) / (N2_REPS + 1)
    out['_arrays'] = (e, cls, acc, sp, ev)
    return out


def trade_block(all_trades: pd.DataFrame, split: int) -> dict:
    """Pooled across symbols; day-block bootstrap over dates."""
    t = all_trades[(all_trades.split == split) & (all_trades.cls == 0)]
    if len(t) == 0:
        return {'n': 0}
    g = t.groupby('day').agg(sR=('R', 'sum'), n=('R', 'size')).sort_index()
    sR, n = g.sR.to_numpy(), g.n.to_numpy()
    res = {'n': int(len(t))}
    for nm, st in (('net', 0.0), ('stress_0.05', 0.05), ('stress_0.10', 0.10)):
        f = lambda ix=None: ((sR if ix is None else sR[ix]).sum() - st * (n if ix is None else n[ix]).sum()) / (n if ix is None else n[ix]).sum()
        res[nm] = oc.boot_summary(f(), oc.bootstrap(lambda ix: f(ix), len(g)))
    res['per_symbol_stress_0.05'] = {s: oc._f(x.R.mean() - 0.05) for s, x in t.groupby('sym')}
    res['exit_stop_share'] = oc._f((t.exit == 'stop').mean())
    return res


def geometry_null(S: oc.Sym, trades: pd.DataFrame, anchor_sessions: pd.DataFrame, rng) -> np.ndarray:
    """For each trade: NULL_DRAWS sessions from the same symbol/split, same entry minute, random direction,
    same D in sigma units, same stop/exit rules and costs. Returns array (n_trades, NULL_DRAWS) of R."""
    out = np.full((len(trades), NULL_DRAWS), np.nan)
    for k, tr in enumerate(trades.itertuples()):
        pool = anchor_sessions[(anchor_sessions.split == tr.split) & anchor_sessions['eval'] & np.isfinite(anchor_sessions.sprd)]
        ii = pool.i.to_numpy()
        got = 0; tries = 0
        while got < NULL_DRAWS and tries < NULL_DRAWS * 20:
            tries += 1
            r = pool.iloc[int(rng.integers(0, len(pool)))]
            sl = S.bars(int(r.i))
            sm = S.smin[sl]
            p = int(np.searchsorted(sm, tr.entry_min))
            if p >= len(sm) or sm[p] >= tr.entry_min + 5:
                continue
            beta = 1 if rng.random() < 0.5 else -1
            o, h, l, c = S.o[sl], S.h[sl], S.l[sl], S.c[sl]
            D = tr.Dsig * r.sig
            entry = o[p] + (r.sprd if beta == 1 else 0.0)
            level = entry - beta * D
            res = trade_outcome(sm, o, h, l, c, p, beta, level, r.sprd, oc.commission(S.sym, float(o[p])))
            if res is None:
                continue
            out[k, got] = res['R']; got += 1
    return out


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', choices=['disc', 'val', 'full'], required=True)
    args = ap.parse_args()
    ms_ = oc.stage_max_split(args.stage)
    full = args.stage == 'full'
    rng = np.random.default_rng(oc.SEED)
    out = {'hypothesis': 'OF-19', 'prereg': ['PREREG_OF_COMMON.md', 'PREREG_OF19_RELATIVE_IB.md'], 'stage': args.stage,
           'splits_opened': oc.SPLIT_NAMES[:ms_ + 1], 'symbols': {},
           'implementation_notes': ['Break eligibility uses t + m <= 16:59 NY (last bar minute) so that P_a exists.',
                                    'Geometry null applies no cost floor (D matched in sigma units).']}
    trades_all, pA, pB = [], {}, {}
    Ssyms = {}
    for sym in oc.SYMBOLS:
        S = oc.load(sym); Ssyms[sym] = S
        tail = variance_share(S)
        R = {'cells': {}}
        for role, anchor in (('primary', oc.PRIMARY_ANCHOR[sym]), ('secondary', oc.secondary_anchor(sym))):
            df = build(S, anchor, ms_, tail)
            R[f'n_valid_sessions_{role}'] = int(len(df))
            for N in NS:
                for m in MS:
                    prim = role == 'primary' and N == 20 and m == 30
                    key = f'{role}:{anchor}|N{N}|m{m}'
                    c = cell(df, N, m, ms_, perm=prim and full, rng=rng)
                    e, cls, acc, sp, ev = c.pop('_arrays')
                    R['cells'][key] = c
                    if not prim:
                        continue
                    R['primary_cell'] = key
                    pA[sym] = c['theta19a']['per_split'].get('discovery', {}).get('p_one_sided')
                    pB[sym] = c['theta19b']['per_split'].get('discovery', {}).get('p_one_sided')
                    # Y2 extension
                    mfe = ev.get('mfe30', pd.Series(np.nan, index=ev.index)).to_numpy(float)
                    okm = acc & np.isfinite(mfe)
                    mf = np.nan_to_num(mfe)
                    def d_mfe(ix=None):
                        a_, c_, k_ = (mf, cls, okm) if ix is None else (mf[ix], cls[ix], okm[ix])
                        s_, L_ = k_ & (c_ == 0), k_ & (c_ == 2)
                        return a_[s_].mean() - a_[L_].mean() if s_.any() and L_.any() else np.nan
                    R['Y2_extension'] = {
                        'MFE_sigma_rem_by_class': {nm: oc._f(mf[okm & (cls == k)].mean()) for k, nm in enumerate(('SMALL', 'MID', 'LARGE'))},
                        'driftless_benchmark': MFE_NULL,
                        'SMALL_minus_LARGE': oc.boot_summary(d_mfe(), oc.bootstrap(lambda ix: d_mfe(ix), len(ev))),
                        'SMALL_minus_benchmark': oc._f(mf[okm & (cls == 0)].mean() - MFE_NULL) if (okm & (cls == 0)).any() else None}
                    # Y3 stays inside
                    acc30 = ev.acc30.to_numpy()
                    ibr, ibr_cuts = classes(df, 'IBR'); ibr = ibr[df['eval'].to_numpy()]
                    R['Y3_no_accepted_break'] = {
                        'by_RIB_class': {nm: oc._f(1 - acc30[cls == k].mean()) for k, nm in enumerate(('SMALL', 'MID', 'LARGE'))},
                        'by_IBR_class': {nm: oc._f(1 - acc30[ibr == k].mean()) for k, nm in enumerate(('SMALL', 'MID', 'LARGE'))},
                        'IBR_cuts': ibr_cuts,
                        'failed_break_share_of_breaks': oc._f(1 - ev.acc30[ev.brk30 == 1].mean())}
                    # robustness
                    rob = {}
                    beta30 = ev.get('beta30', pd.Series(np.nan, index=ev.index)).to_numpy(float)
                    for nm, msk in (('up_only', beta30 == 1), ('down_only', beta30 == -1)):
                        a2 = acc & msk
                        rob[nm] = {'theta19a': oc._f(th_a(e, cls, a2)), 'theta19b': oc._f(th_b(e, cls, a2)),
                                   'n_small': int((a2 & (cls == 0)).sum())}
                    fri = ev.wd.to_numpy() == 4
                    rob['friday_only'] = {'theta19a': oc._f(th_a(e, cls, acc & fri)), 'theta19b': oc._f(th_b(e, cls, acc & fri))}
                    rob['excl_friday'] = {'theta19a': oc._f(th_a(e, cls, acc & ~fri)), 'theta19b': oc._f(th_b(e, cls, acc & ~fri))}
                    yrs = ev.year.to_numpy()
                    rob['per_year_theta19a'] = {str(y): oc._f(th_a(e, cls, acc & (yrs == y))) for y in sorted(set(yrs))}
                    rob['per_year_theta19b'] = {str(y): oc._f(th_b(e, cls, acc & (yrs == y))) for y in sorted(set(yrs))}
                    w = np.array([(acc & (cls == 0) & (yrs == y)).sum() for y in sorted(set(yrs))])
                    tb = np.array([th_b(e, cls, acc & (yrs == y)) for y in sorted(set(yrs))])
                    rob['year_share_theta19b'] = oc.year_shares(np.array(sorted(set(yrs))), np.nan_to_num(w * tb))
                    R['robustness'] = rob
                    # trades
                    t = ev[np.isfinite(ev.get('tradeR', pd.Series(np.nan, index=ev.index)))].copy()
                    t['cls'] = cls[np.isfinite(ev.get('tradeR', pd.Series(np.nan, index=ev.index)).to_numpy())]
                    t['sym'] = sym
                    t = t.rename(columns={'tradeR': 'R', 'trade_exit': 'exit'})
                    t['Dsig'] = t.tradeD / t.sig
                    pip = {'EURUSD': 1e-4, 'GBPUSD': 1e-4, 'USDJPY': 1e-2, 'XAUUSD': 0.1}[sym]
                    t['Dpips'] = t.tradeD / pip
                    skips = ev.get('trade_skip', pd.Series(dtype=object)).value_counts().to_dict()
                    R['trade_skips'] = {k: int(v) for k, v in skips.items()}
                    R['trade_D_distribution_SMALL'] = {
                        'pips_p10_p50_p90': [oc._f(x) for x in np.percentile(t.Dpips[t.cls == 0], [10, 50, 90])] if (t.cls == 0).any() else None,
                        'sigma_p10_p50_p90': [oc._f(x) for x in np.percentile(t.Dsig[t.cls == 0], [10, 50, 90])] if (t.cls == 0).any() else None}
                    R['trade_by_class_per_split'] = {
                        oc.SPLIT_NAMES[s]: {nm: {'n': int(((t.split == s) & (t.cls == k)).sum()),
                                                 'meanR_net': oc._f(t.R[(t.split == s) & (t.cls == k)].mean())}
                                            for k, nm in enumerate(('SMALL', 'MID', 'LARGE'))} for s in range(ms_ + 1)}
                    trades_all.append(t[['sym', 'day', 'split', 'year', 'cls', 'R', 'exit', 'entry_min', 'Dsig', 'sig']])
                    R['_sessions_primary'] = df
        out['symbols'][sym] = R
        print(sym, 'done', flush=True)

    # BH within primary families
    for nm, P in (('theta19a', pA), ('theta19b', pB)):
        adj = oc.bh([P[s] for s in oc.SYMBOLS])
        for s, a in zip(oc.SYMBOLS, adj):
            out['symbols'][s][f'{nm}_disc_p_BH'] = a
    for nm in ('theta19a', 'theta19b'):
        sec = [(s, k) for s in oc.SYMBOLS for k in out['symbols'][s]['cells'] if k != out['symbols'][s]['primary_cell']]
        sp_ = [out['symbols'][s]['cells'][k][nm]['per_split'].get('discovery', {}).get('p_one_sided') for s, k in sec]
        for (s, k), a in zip(sec, oc.bh(sp_)):
            out['symbols'][s]['cells'][k][f'{nm}_disc_p_BH_secondary_family'] = a

    T = pd.concat(trades_all, ignore_index=True)
    out['trade_OF19T'] = {oc.SPLIT_NAMES[s]: trade_block(T, s) for s in range(ms_ + 1)}
    out['trade_OF19T']['LARGE_class_comparison'] = {
        oc.SPLIT_NAMES[s]: {'n': int(((T.split == s) & (T.cls == 2)).sum()),
                            'meanR_net': oc._f(T.R[(T.split == s) & (T.cls == 2)].mean())} for s in range(ms_ + 1)}

    if full:
        n_sup = n_rej = 0
        for s in oc.SYMBOLS:
            R = out['symbols'][s]
            c = R['cells'][R['primary_cell']]
            vs = {}
            for nm in ('theta19a', 'theta19b'):
                ps = c[nm]['per_split']
                vs[nm] = oc.verdict(ps['discovery']['theta'], R[f'{nm}_disc_p_BH'], ps['validation']['theta'],
                                    ps['holdout']['theta'], c[nm]['pooled']['ci95'][0], c[nm]['pooled']['theta'])
            pn2 = c.get('p_N2_permutation')
            if vs['theta19a'] == 'REJECTED' or vs['theta19b'] == 'REJECTED':
                v = 'REJECTED'
            elif vs['theta19a'] == 'SUPPORTED' and vs['theta19b'] == 'SUPPORTED' and pn2 is not None and pn2 < 0.10:
                v = 'SUPPORTED'
            else:
                v = 'INCONCLUSIVE'
            R['effect_verdicts'] = vs; R['verdict'] = v
            n_sup += v == 'SUPPORTED'; n_rej += v == 'REJECTED'
        out['overall_OF19P'] = {'supported': n_sup, 'rejected': n_rej,
                                'verdict': 'SUPPORTED' if n_sup >= 3 else 'REJECTED' if n_rej >= 3 else 'INCONCLUSIVE'}
        # OF-19-T decision with geometry null on holdout SMALL trades
        th = T[(T.split == 2) & (T.cls == 0)].reset_index(drop=True)
        nulls = []
        for sym in oc.SYMBOLS:
            tt = th[th.sym == sym]
            if len(tt):
                nulls.append(geometry_null(Ssyms[sym], tt, out['symbols'][sym]['_sessions_primary'], rng))
        NUL = np.vstack(nulls) if nulls else np.zeros((0, NULL_DRAWS))
        obs = th.R.mean() if len(th) else np.nan
        reps = []
        for _ in range(NULL_REPS):
            pick = rng.integers(0, NULL_DRAWS, len(NUL))
            vals = NUL[np.arange(len(NUL)), pick]
            reps.append(np.nanmean(vals))
        reps = np.array(reps)
        p_null = float((np.sum(reps >= obs)) / NULL_REPS) if len(th) else None
        hb = out['trade_OF19T']['holdout']; db = out['trade_OF19T']['discovery']
        per = hb.get('per_symbol_stress_0.05', {})
        npos = sum(1 for v in per.values() if v is not None and v > 0)
        if hb.get('n', 0) < 200:
            tv = 'INSUFFICIENT-N'
        elif hb['stress_0.05']['theta'] is not None and hb['stress_0.05']['theta'] <= 0:
            tv = 'REJECTED-T'
        elif hb['stress_0.05']['ci95'][0] > 0 and npos >= 3 and db['stress_0.05']['theta'] > 0 and p_null < 0.10:
            tv = 'SUPPORTED-T'
        else:
            tv = 'INCONCLUSIVE-T'
        out['trade_OF19T']['geometry_null'] = {'observed_holdout_meanR_net': oc._f(obs), 'null_mean': oc._f(np.nanmean(reps)),
                                               'null_p95': oc._f(np.nanpercentile(reps, 95)), 'p_null': p_null,
                                               'n_null_missing': int(np.isnan(NUL).sum())}
        out['trade_OF19T']['symbols_positive_stress'] = npos
        out['trade_OF19T']['verdict'] = tv
    for s in oc.SYMBOLS:
        out['symbols'][s].pop('_sessions_primary', None)
    T.to_csv(os.path.join(oc.HERE, f'of19_trades_{args.stage}.csv'), index=False)
    fn = os.path.join(oc.HERE, f'of19_results_{args.stage}.json' if not full else 'of19_results.json')
    with open(fn, 'w') as f:
        json.dump(out, f, indent=1, default=lambda x: oc._f(x) if isinstance(x, (np.floating, float)) else int(x) if isinstance(x, np.integer) else str(x))
    print('wrote', fn)
    return 0


if __name__ == '__main__':
    sys.exit(main())
