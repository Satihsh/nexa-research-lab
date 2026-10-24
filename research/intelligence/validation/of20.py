#!/usr/bin/env python3
"""OF-20: trend day -> balance day vs base rate (PREREG_OF20_TREND_BALANCE.md; inherits PREREG_OF_COMMON.md).

Usage: python of20.py --stage disc|val|full
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

import of_common as oc

PERM_REPS = 1000


def rot_count(Hs: np.ndarray, Ls: np.ndarray) -> int:
    """EQ-018: a_j = +1 up-auction, -1 down-auction, 0 otherwise; ROT = sign changes among non-zero a_j."""
    a = []
    for j in range(1, len(Hs)):
        if Hs[j] > Hs[j - 1] and Ls[j] >= Ls[j - 1]:
            a.append(1)
        elif Ls[j] < Ls[j - 1] and Hs[j] <= Hs[j - 1]:
            a.append(-1)
    return int(sum(1 for x, y in zip(a, a[1:]) if x != y))


def classify(O, H, L, C, IBH, IBL, ROT) -> dict:
    R = H - L
    IB = IBH - IBL
    CL = (C - L) / R
    REX = (R - IB) / IB if IB > 0 else np.nan
    up = CL >= 0.90 and H > IBH and L >= IBL and REX >= 1.0 and ROT <= 2
    dn = CL <= 0.10 and L < IBL and H <= IBH and REX >= 1.0 and ROT <= 2
    lite_up = CL >= 0.90 and ROT <= 2
    lite_dn = CL <= 0.10 and ROT <= 2
    return {'TD': int(up or dn), 'TDdir': 1 if up else (-1 if dn else 0),
            'TDlite': int(lite_up or lite_dn), 'TDlitedir': 1 if lite_up else (-1 if lite_dn else 0),
            'BAL1': int(ROT >= 3 and 0.25 <= CL <= 0.75), 'BAL1third': int(ROT >= 3 and 1 / 3 <= CL <= 2 / 3),
            'CL': CL, 'REX': REX, 'ROT': ROT, 'R': R}


def session_stats(S: oc.Sym, i: int, a: int, full_day: bool = False):
    sl = S.bars(i)
    sm = S.smin[sl]
    if full_day:
        idx = np.arange(sl.start, sl.stop)
        if len(idx) == 0 or sm[0] >= 180:
            return None
        a = int(sm[0])                      # deviation OF-D1: A0 IB starts at the day's first bar (gold opens 18:00 NY)
    else:
        idx, a_bar = oc.session(S, i, a)
        if a_bar is None:
            return None
    ib = oc.ib_window(S, idx, a)
    if ib is None:
        return None
    IBH, IBL, _ = ib
    h, l, c, o, smi = S.h[idx], S.l[idx], S.c[idx], S.o[idx], S.smin[idx]
    H, L = float(h.max()), float(l.min())
    if H <= L:
        return None
    per = (smi - a) // 30
    Hs, Ls = [], []
    last = int(per.max())
    for j in range(0, last + 1):
        m = per == j
        if not m.any():
            continue
        if j == last and m.sum() < 15:
            continue
        Hs.append(h[m].max()); Ls.append(l[m].min())
    ROT = rot_count(np.array(Hs), np.array(Ls))
    O, C = float(o[0]), float(c[-1])
    st = classify(O, H, L, C, IBH, IBL, ROT)
    va = oc.value_area(h, l, c, S.tv[idx], oc.BINW[S.sym])
    st.update({'O': O, 'C': C, 'H': H, 'L': L, 'VAL': va[0] if va else np.nan, 'VAH': va[1] if va else np.nan})
    return st


def build(S: oc.Sym, anchor: str | None, max_split: int) -> pd.DataFrame:
    rows = []
    for i in range(1, len(S.days)):
        if not S.valid[i] or not oc.is_eval_day(S, i) or S.split[i] > max_split:
            continue
        d = date.fromisoformat(S.days[i])
        if anchor is None:
            st = session_stats(S, i, 0, full_day=True)
        else:
            st = session_stats(S, i, oc.anchor_smin(S.sym, anchor, d))
        if st is None:
            continue
        sig = S.sig[i]
        st.update({'i': i, 'day': S.days[i], 'split': int(S.split[i]), 'year': d.year, 'wd': d.weekday(),
                   'sig': float(sig), 'Rsig': st['R'] / sig if np.isfinite(sig) and sig > 0 else np.nan,
                   'relsig': sig / S.C[i - 1] if np.isfinite(sig) else np.nan})
        rows.append(st)
    return pd.DataFrame(rows)


def pairs(df: pd.DataFrame) -> pd.DataFrame:
    """Consecutive (d, d+1): d+1 = next weekday server day present (index i+1), both valid sessions."""
    nxt = df.set_index('i')
    rows = []
    for r in df.itertuples():
        if r.i + 1 not in nxt.index:
            continue
        n = nxt.loc[r.i + 1]
        tdir = r.TDdir if r.TDdir != 0 else int(np.sign(r.C - r.O))
        bal2 = int((np.isfinite(r.VAL) and r.VAL <= n.C <= r.VAH) or (tdir != 0 and np.sign(n.C - n.O) == -tdir))
        rows.append({'day': r.day, 'split': r.split, 'year': r.year, 'wd': r.wd, 'TD': r.TD, 'TDdir': r.TDdir,
                     'TDlite': r.TDlite, 'Rsig': r.Rsig, 'relsig': r.relsig,
                     'BAL1n': n.BAL1, 'BAL1thirdn': n.BAL1third, 'BAL2n': bal2, 'TDn': n.TD,
                     'typ': 'T' if r.TD else ('B' if r.BAL1 else 'O'), 'typn': 'T' if n.TD else ('B' if n.BAL1 else 'O'),
                     'va_ok': bool(np.isfinite(r.VAL))})
    return pd.DataFrame(rows)


def rd(cond, out, idx=None):
    if idx is not None:
        cond, out = cond[idx], out[idx]
    c = cond > 0
    if c.sum() == 0 or (~c).sum() == 0:
        return np.nan
    return out[c].mean() - out[~c].mean()


def condp(cond, out, idx=None):
    if idx is not None:
        cond, out = cond[idx], out[idx]
    c = cond > 0
    return out[c].mean() if c.sum() else np.nan


def cell(P: pd.DataFrame, cond: np.ndarray, out: np.ndarray, max_split: int, rng, perm: bool) -> dict:
    sp = P.split.to_numpy()
    ok = np.isfinite(cond) & np.isfinite(out)
    cond = np.where(ok, cond, 0); out = np.where(ok, out, 0)
    keep = np.where(ok)[0]
    cond, out, sp = cond[keep], out[keep], sp[keep]
    res = {'n_pairs': int(len(keep)), 'n_cond': int(cond.sum()), 'P_cond': oc._f(cond.mean()),
           'P_out_given_cond': oc._f(condp(cond, out)), 'P_out_given_not': oc._f(condp(1 - cond, out)),
           'P_out': oc._f(out.mean())}
    per = {}
    for s in range(max_split + 1):
        pos = np.where(sp == s)[0]
        if len(pos) == 0:
            continue
        cc, oo = cond[pos], out[pos]
        per[oc.SPLIT_NAMES[s]] = oc.boot_summary(rd(cc, oo), oc.bootstrap(lambda ix: rd(cc, oo, ix), len(pos))) | {
            'n_cond': int(cc.sum()), 'P_cond': oc._f(cc.mean()), 'P_out_given_cond': oc._f(condp(cc, oo)),
            'P_out_given_not': oc._f(condp(1 - cc, oo))}
    res['per_split'] = per
    res['pooled'] = oc.boot_summary(rd(cond, out), oc.bootstrap(lambda ix: rd(cond, out, ix), len(cond)))
    res['pooled_P_out_given_cond'] = oc.boot_summary(condp(cond, out), oc.bootstrap(lambda ix: condp(cond, out, ix), len(cond)))
    a = int(((cond > 0) & (out > 0)).sum()); b = int(((cond > 0) & (out == 0)).sum())
    c = int(((cond == 0) & (out > 0)).sum()); d = int(((cond == 0) & (out == 0)).sum())
    res['fisher_p_greater'] = oc._f(fisher_exact([[a, b], [c, d]], alternative='greater')[1]) if a + b > 0 else None
    if perm:
        th = rd(cond, out); cnt = 0
        for _ in range(PERM_REPS):
            o2 = out.copy()
            for s in np.unique(sp):
                ix = np.where(sp == s)[0]
                o2[ix] = o2[ix][rng.permutation(len(ix))]
            cnt += rd(cond, o2) >= th
        res['p_perm'] = (1 + cnt) / (PERM_REPS + 1)
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', choices=['disc', 'val', 'full'], required=True)
    args = ap.parse_args()
    ms = oc.stage_max_split(args.stage)
    full = args.stage == 'full'
    rng = np.random.default_rng(oc.SEED)
    out = {'hypothesis': 'OF-20', 'prereg': ['PREREG_OF_COMMON.md', 'PREREG_OF20_TREND_BALANCE.md'], 'stage': args.stage,
           'splits_opened': oc.SPLIT_NAMES[:ms + 1], 'symbols': {},
           'implementation_notes': ['BAL2 for a non-trend day d uses direction sign(C_d - O_d) of session d '
                                    '(the prereg names "trend direction of d", undefined on non-trend days).',
                                    'XD cells exclude pairs whose sigma-hat is undefined.',
                                    'OF-D1 (robustness-only path): A0 full-day IB = first 60 min after the server day\'s first bar '
                                    '(XAUUSD opens 18:00 NY, so "17:00 NY" has no bars); fixed after a crash in the disc run, '
                                    'before any OF-20 output was written.']}
    pdisc = {}
    for sym in oc.SYMBOLS:
        S = oc.load(sym)
        R = {'cells': {}}
        for role, anchor in (('primary', oc.PRIMARY_ANCHOR[sym]), ('secondary', oc.secondary_anchor(sym))):
            df = build(S, anchor, ms)
            P = pairs(df)
            xd_cut = float(np.nanpercentile(df.Rsig[df.split == 0], 80))
            P['XD'] = np.where(np.isfinite(P.Rsig), (P.Rsig >= xd_cut).astype(float), np.nan)
            R[f'n_sessions_{role}'] = int(len(df)); R[f'n_pairs_{role}'] = int(len(P))
            R[f'XD_cut_Rsig_{role}'] = xd_cut
            # HYP-013 base rate
            R[f'P_TD_by_split_{role}'] = {oc.SPLIT_NAMES[s]: oc._f(df.TD[df.split == s].mean()) for s in range(ms + 1)}
            R[f'P_TD_pooled_{role}'] = oc._f(df.TD.mean())
            R[f'P_TDlite_pooled_{role}'] = oc._f(df.TDlite.mean())
            R[f'P_BAL1_pooled_{role}'] = oc._f(df.BAL1.mean())
            for cn in ('TD', 'TDlite', 'XD'):
                for on in ('BAL1n', 'BAL1thirdn', 'BAL2n'):
                    prim = role == 'primary' and cn == 'TD' and on == 'BAL1n'
                    key = f'{role}:{anchor}|{cn}|{on[:-1]}'
                    outv = P[on].to_numpy(float)
                    if on == 'BAL2n':
                        outv = np.where(P.va_ok, outv, np.nan)
                    R['cells'][key] = cell(P, P[cn].to_numpy(float), outv, ms, rng, perm=prim and full)
                    if prim:
                        R['primary_cell'] = key
                        pdisc[sym] = R['cells'][key]['per_split'].get('discovery', {}).get('p_one_sided')
            if role == 'primary':
                # persistence and transition matrix
                R['persistence'] = {'P_TDnext_given_TD': oc._f(P.TDn[P.TD == 1].mean()) if (P.TD == 1).any() else None,
                                    'P_TD': oc._f(P.TD.mean()),
                                    'rd': cell(P, P.TD.to_numpy(float), P.TDn.to_numpy(float), ms, rng, perm=False)['pooled']}
                tm = pd.crosstab(P.typ, P.typn, normalize='index')
                R['transition_matrix_row_normalised'] = {r: {c: oc._f(tm.loc[r, c]) for c in tm.columns} for r in tm.index}
                R['transition_counts'] = {r: {c: int(v) for c, v in row.items()} for r, row in pd.crosstab(P.typ, P.typn).iterrows()}
                # robustness
                rob = {}
                nf = P.wd.to_numpy() != 4
                rob['excl_friday_to_monday'] = cell(P[nf], P.TD[nf].to_numpy(float), P.BAL1n[nf].to_numpy(float), ms, rng, False)['pooled']
                for nm, dirv in (('up_trend_days', 1), ('down_trend_days', -1)):
                    cnd = ((P.TD == 1) & (P.TDdir == dirv)).to_numpy(float)
                    msk = (P.TD == 0) | (P.TDdir == dirv)
                    rob[nm] = cell(P[msk], cnd[msk.to_numpy()], P.BAL1n[msk].to_numpy(float), ms, rng, False)['pooled'] | {
                        'n': int(cnd.sum())}
                yrs = P.year.to_numpy()
                rob['per_year_rd'] = {str(y): oc._f(rd(P.TD.to_numpy(float)[yrs == y], P.BAL1n.to_numpy(float)[yrs == y]))
                                      for y in sorted(set(yrs))}
                w = np.array([((P.TD == 1) & (yrs == y)).sum() for y in sorted(set(yrs))])
                th = np.array([rd(P.TD.to_numpy(float)[yrs == y], P.BAL1n.to_numpy(float)[yrs == y]) for y in sorted(set(yrs))])
                rob['year_share'] = oc.year_shares(np.array(sorted(set(yrs))), np.nan_to_num(w * th))
                cuts = np.nanpercentile(P.relsig[P.split == 0], [100 / 3, 200 / 3])
                ter = np.digitize(P.relsig, cuts)
                rob['by_prior_sigma_tercile'] = {f'T{k + 1}': cell(P[ter == k], P.TD[ter == k].to_numpy(float),
                                                                   P.BAL1n[ter == k].to_numpy(float), ms, rng, False)['pooled'] | {
                    'n_TD': int(P.TD[ter == k].sum())} for k in range(3)}
                R['robustness'] = rob
        # A0 full-day session (reported only)
        dfa = build(S, None, ms)
        Pa = pairs(dfa)
        R['robustness']['A0_full_day_session'] = {'P_TD': oc._f(dfa.TD.mean()),
                                                  'rd_TD_BAL1': cell(Pa, Pa.TD.to_numpy(float), Pa.BAL1n.to_numpy(float), ms, rng, False)['pooled']}
        out['symbols'][sym] = R
        print(sym, 'done', flush=True)

    adj = oc.bh([pdisc[s] for s in oc.SYMBOLS])
    for s, a in zip(oc.SYMBOLS, adj):
        out['symbols'][s]['primary_disc_p_BH'] = a
    sec = [(s, k) for s in oc.SYMBOLS for k in out['symbols'][s]['cells'] if k != out['symbols'][s]['primary_cell']]
    for (s, k), a in zip(sec, oc.bh([out['symbols'][s]['cells'][k]['per_split'].get('discovery', {}).get('p_one_sided') for s, k in sec])):
        out['symbols'][s]['cells'][k]['disc_p_BH_secondary_family'] = a

    if full:
        n_sup = n_rej = 0
        for s in oc.SYMBOLS:
            R = out['symbols'][s]
            c = R['cells'][R['primary_cell']]
            ps = c['per_split']
            if c['n_cond'] < 100:
                v = 'INSUFFICIENT-N'
            else:
                v = oc.verdict(ps['discovery']['theta'], R['primary_disc_p_BH'], ps['validation']['theta'],
                               ps['holdout']['theta'], c['pooled']['ci95'][0], c['pooled']['theta'],
                               extra_ok=c.get('p_perm') is not None and c['p_perm'] < 0.10)
            R['verdict_CL009'] = v
            n_sup += v == 'SUPPORTED'; n_rej += v == 'REJECTED'
            anc = oc.PRIMARY_ANCHOR[s]
            q = {}
            for on in ('BAL1', 'BAL2'):
                cc = R['cells'][f'primary:{anc}|XD|{on}']
                lo, hi = cc['pooled_P_out_given_cond']['ci95']
                q[on] = {'q': cc['pooled_P_out_given_cond']['theta'], 'ci95': [lo, hi],
                         'P_out_given_not_XD': cc['P_out_given_not'],
                         'result': 'CONSISTENT' if (lo is not None and hi is not None and hi >= 0.05 and lo <= 0.15) else 'REFUTED for the analogue'}
            R['CL031_q'] = q
            c2 = R['cells'][f'primary:{anc}|TD|BAL2']
            lo, hi = c2['pooled_P_out_given_cond']['ci95']
            R['HYP010'] = {'P_BAL2_given_TD': c2['pooled_P_out_given_cond']['theta'], 'ci95': [lo, hi],
                           'P_BAL2_given_not_TD': c2['P_out_given_not'],
                           'result': 'REFUTED for the analogue' if hi is not None and hi < 0.85 else
                           'CONSISTENT' if hi is not None and lo is not None and hi >= 0.85 and lo <= 0.95 else 'ABOVE RANGE',
                           'counted_in_verdicts': oc.PROFILE_PROXY_VALID[s]}
        ov = 'SUPPORTED' if n_sup >= 3 else 'REJECTED' if n_rej >= 3 else 'INCONCLUSIVE'
        q_above = sum(1 for s in oc.SYMBOLS if out['symbols'][s]['CL031_q']['BAL1']['ci95'][0] is not None
                      and out['symbols'][s]['CL031_q']['BAL1']['ci95'][0] > 0.15)
        q_cons = sum(1 for s in oc.SYMBOLS if out['symbols'][s]['CL031_q']['BAL1']['result'] == 'CONSISTENT')
        persist = sum(1 for s in oc.SYMBOLS if (out['symbols'][s]['persistence']['rd']['ci95'][0] or -1) > 0)
        if ov == 'SUPPORTED' and q_above >= 3:
            reading = "Axia's sequence holds for XAU/FX under these definitions; DeepCharts' 10 % does not transfer"
        elif ov == 'REJECTED' and persist >= 3 and q_cons >= 3:
            reading = "DeepCharts' continuation reading holds; Axia's does not transfer"
        elif ov == 'REJECTED' and persist < 3:
            reading = 'Neither: day types are roughly independent; neither claim adds information'
        else:
            reading = 'Unresolved; stays CONTRADICTED-BY-SOURCE in the KB'
        out['overall_CL009'] = {'supported': n_sup, 'rejected': n_rej, 'verdict': ov}
        out['resolution'] = {'CL031_q_above_0.15_symbols': q_above, 'CL031_consistent_symbols': q_cons,
                             'persistence_ci_above_0_symbols': persist, 'reading': reading}
    fn = os.path.join(oc.HERE, f'of20_results_{args.stage}.json' if not full else 'of20_results.json')
    with open(fn, 'w') as f:
        json.dump(out, f, indent=1, default=lambda x: oc._f(x) if isinstance(x, (np.floating, float)) else int(x) if isinstance(x, np.integer) else str(x))
    print('wrote', fn)
    return 0


if __name__ == '__main__':
    sys.exit(main())
