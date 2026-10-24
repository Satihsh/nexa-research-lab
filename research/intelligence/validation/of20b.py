#!/usr/bin/env python3
"""OF-20b: trend day -> balance day with a session-length-normalised day-type rule
(PREREG_OF20b_TREND_BALANCE_NORMALISED.md; inherits PREREG_OF_COMMON.md).

Usage: python of20b.py --stage disc|val|full
Diagnostics (ROT13 distribution, component shares, validity counts) are logged before any outcome is tabulated.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date

import numpy as np
import pandas as pd

import of_common as oc
from of20 import cell, rd, rot_count

NPER = 13
END_MIN = 1440


# ----------------------------------------------------------------------------- definitions (§3)
def partition13(sm: np.ndarray, a: int, T: int) -> np.ndarray:
    """Period index j = floor((t - a) * 13 / T) in {0..12} (exact integer arithmetic)."""
    return ((sm - a) * NPER) // T


def usable_periods(j: np.ndarray, T: int) -> np.ndarray:
    cnt = np.bincount(j, minlength=NPER)[:NPER]
    return cnt >= 0.5 * T / NPER


def ib_b(sm: np.ndarray, h: np.ndarray, l: np.ndarray, a: int, T: int):
    m = (sm - a) * NPER < 2 * T
    if m.sum() < 0.9 * 2 * T / NPER:
        return None
    return float(h[m].max()), float(l[m].min())


def theta_A(P30: int) -> int:
    return max(0, (2 * (P30 - 2)) // 11)


def classify_b(O, H, L, C, IBH, IBL, ROT, thr) -> dict:
    R = H - L
    IB = IBH - IBL
    CL = (C - L) / R
    REX = (R - IB) / IB if IB > 0 else np.nan
    up = CL >= 0.90 and H > IBH and L >= IBL and REX >= 1.0 and ROT <= thr
    dn = CL <= 0.10 and L < IBL and H <= IBH and REX >= 1.0 and ROT <= thr
    return {'TD': int(up or dn), 'dir': 1 if up else (-1 if dn else 0),
            'BAL1': int(ROT >= thr + 1 and 0.25 <= CL <= 0.75),
            'c_CL': int(CL >= 0.9 or CL <= 0.1), 'c_onesided': int((H > IBH and L >= IBL) or (L < IBL and H <= IBH)),
            'c_REX': int(REX >= 1.0), 'c_ROT': int(ROT <= thr)}


def session_b(S: oc.Sym, i: int, a: int):
    idx, a_bar = oc.session(S, i, a)
    if a_bar is None:
        return None
    T = END_MIN - a
    sm, o, h, l, c = S.smin[idx], S.o[idx], S.h[idx], S.l[idx], S.c[idx]
    ib = ib_b(sm, h, l, a, T)
    if ib is None:
        return None
    IBH, IBL = ib
    H, L = float(h.max()), float(l.min())
    if H <= L:
        return None
    O, C = float(o[0]), float(c[-1])
    # 13-period codification
    j = partition13(sm, a, T)
    use = usable_periods(j, T)
    Hs = [h[j == k].max() for k in range(NPER) if use[k]]
    Ls = [l[j == k].min() for k in range(NPER) if use[k]]
    rot13 = rot_count(np.array(Hs), np.array(Ls))
    st13 = classify_b(O, H, L, C, IBH, IBL, rot13, 2)
    # variant A: 30-min periods (OF-20 convention), scaled threshold
    per = (sm - a) // 30
    last = int(per.max())
    H30, L30 = [], []
    for k in range(last + 1):
        m = per == k
        if not m.any() or (k == last and m.sum() < 15):
            continue
        H30.append(h[m].max()); L30.append(l[m].min())
    P30 = len(H30)
    thA = theta_A(P30)
    rot30 = rot_count(np.array(H30), np.array(L30))
    stA = classify_b(O, H, L, C, IBH, IBL, rot30, thA)
    va = oc.value_area(h, l, c, S.tv[idx], oc.BINW[S.sym])
    return {'O': O, 'C': C, 'H': H, 'L': L, 'T': T, 'n_usable13': int(use.sum()), 'valid13': bool(use.sum() >= 11),
            'ROT13': rot13, 'P30': P30, 'thA': thA, 'ROT30': rot30,
            'TDb': st13['TD'], 'dirb': st13['dir'], 'BAL1b': st13['BAL1'],
            'cb_CL': st13['c_CL'], 'cb_onesided': st13['c_onesided'], 'cb_REX': st13['c_REX'], 'cb_ROT': st13['c_ROT'],
            'TDa': stA['TD'], 'dira': stA['dir'], 'BAL1a': stA['BAL1'],
            'VAL': va[0] if va else np.nan, 'VAH': va[1] if va else np.nan}


def build(S: oc.Sym, anchor: str, max_split: int) -> tuple[pd.DataFrame, dict]:
    rows, cnt = [], {'no_anchor_bar_or_IB_b_invalid': 0}
    for i in range(1, len(S.days)):
        if not S.valid[i] or not oc.is_eval_day(S, i) or S.split[i] > max_split:
            continue
        d = date.fromisoformat(S.days[i])
        st = session_b(S, i, oc.anchor_smin(S.sym, anchor, d))
        if st is None:
            cnt['no_anchor_bar_or_IB_b_invalid'] += 1
            continue
        sig = S.sig[i]
        st.update({'i': i, 'day': S.days[i], 'split': int(S.split[i]), 'year': d.year, 'wd': d.weekday(),
                   'relsig': sig / S.C[i - 1] if np.isfinite(sig) else np.nan})
        rows.append(st)
    return pd.DataFrame(rows), cnt


def pairs(df: pd.DataFrame, code: str) -> pd.DataFrame:
    """code 'b' (13-period; both sessions valid13) or 'a' (variant A; IB_b-valid sessions)."""
    D = df[df.valid13] if code == 'b' else df
    nxt = D.set_index('i')
    TD, dirc, BAL = f'TD{code}', f'dir{code}', f'BAL1{code}'
    rows = []
    for r in D.itertuples():
        if r.i + 1 not in nxt.index:
            continue
        n = nxt.loc[r.i + 1]
        tdir = getattr(r, dirc) if getattr(r, dirc) != 0 else int(np.sign(r.C - r.O))
        bal2 = int((np.isfinite(r.VAL) and r.VAL <= n.C <= r.VAH) or (tdir != 0 and np.sign(n.C - n.O) == -tdir))
        rows.append({'day': r.day, 'split': r.split, 'year': r.year, 'wd': r.wd, 'relsig': r.relsig,
                     'TD': getattr(r, TD), 'dir': getattr(r, dirc), 'BAL1n': n[BAL], 'BAL2n': bal2, 'TDn': n[TD],
                     'typ': 'T' if getattr(r, TD) else ('B' if getattr(r, BAL) else 'O'),
                     'typn': 'T' if n[TD] else ('B' if n[BAL] else 'O'), 'va_ok': bool(np.isfinite(r.VAL))})
    return pd.DataFrame(rows)


def diagnostics(df: pd.DataFrame) -> dict:
    v = df[df.valid13]
    return {'sessions_IB_b_valid': int(len(df)), 'sessions_valid13': int(len(v)),
            'usable13_distribution': {int(k): int(x) for k, x in df.n_usable13.value_counts().sort_index().items()},
            'ROT13_p5_p25_p50_p75_p95': [float(x) for x in np.percentile(v.ROT13, [5, 25, 50, 75, 95])] if len(v) else None,
            'share_ROT13_le_2': oc._f((v.ROT13 <= 2).mean()), 'share_CL_extreme': oc._f(v.cb_CL.mean()),
            'share_onesided_ext': oc._f(v.cb_onesided.mean()), 'share_REXb_ge_1': oc._f(v.cb_REX.mean()),
            'P30_values': {int(k): int(x) for k, x in df.P30.value_counts().sort_index().items()},
            'thetaA_values': {int(k): int(x) for k, x in df.thA.value_counts().sort_index().items()},
            'share_ROT30_le_thetaA': oc._f((df.ROT30 <= df.thA).mean())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', choices=['disc', 'val', 'full'], required=True)
    args = ap.parse_args()
    ms = oc.stage_max_split(args.stage)
    full = args.stage == 'full'
    rng = np.random.default_rng(oc.SEED)
    out = {'hypothesis': 'OF-20b', 'prereg': ['PREREG_OF_COMMON.md', 'PREREG_OF20b_TREND_BALANCE_NORMALISED.md'],
           'stage': args.stage, 'splits_opened': oc.SPLIT_NAMES[:ms + 1], 'label': 'RETROSPECTIVE (semi-blind)', 'symbols': {}}
    built = {}
    # ---- diagnostics first (§4), before any outcome is tabulated
    for sym in oc.SYMBOLS:
        S = oc.load(sym)
        for role, anchor in (('primary', oc.PRIMARY_ANCHOR[sym]), ('secondary', oc.secondary_anchor(sym))):
            df, cnt = build(S, anchor, ms)
            built[(sym, role)] = (anchor, df)
            dg = diagnostics(df) | cnt
            out['symbols'].setdefault(sym, {'diagnostics': {}, 'cells': {}})['diagnostics'][role] = dg
            print('DIAG', sym, role, anchor, json.dumps(dg), flush=True)
    # ---- outcomes
    pdisc = {}
    for sym in oc.SYMBOLS:
        R = out['symbols'][sym]
        for role in ('primary', 'secondary'):
            anchor, df = built[(sym, role)]
            for code, cname in (('b', '13p'), ('a', 'varA')):
                P = pairs(df, code)
                sess = df[df.valid13] if code == 'b' else df
                tdcol = f'TD{code}'
                pt = sess[tdcol].to_numpy(float)
                R[f'P_TD_{cname}_{role}'] = {oc.SPLIT_NAMES[s]: oc._f(sess[tdcol][sess.split == s].mean()) for s in range(ms + 1)}
                R[f'P_TD_{cname}_{role}_pooled'] = oc.boot_summary(pt.mean(), oc.bootstrap(lambda ix: pt[ix].mean(), len(pt)))
                R[f'n_pairs_{cname}_{role}'] = int(len(P))
                for on in ('BAL1n', 'BAL2n'):
                    prim = role == 'primary' and code == 'b' and on == 'BAL1n'
                    key = f'{role}:{anchor}|{cname}|{on[:-1]}'
                    ov = P[on].to_numpy(float)
                    if on == 'BAL2n':
                        ov = np.where(P.va_ok, ov, np.nan)
                    R['cells'][key] = cell(P, P.TD.to_numpy(float), ov, ms, rng, perm=prim and full)
                    if prim:
                        R['primary_cell'] = key
                        pdisc[sym] = R['cells'][key]['per_split'].get('discovery', {}).get('p_one_sided')
                if role == 'primary' and code == 'b':
                    pers = cell(P, P.TD.to_numpy(float), P.TDn.to_numpy(float), ms, rng, perm=False)
                    R['persistence'] = {'P_TDnext_given_TD': pers['P_out_given_cond'], 'P_TD': pers['P_cond'],
                                        'rd': pers['pooled'], 'n_TD': pers['n_cond']}
                    R['transition_matrix_row_normalised'] = {r: {c: oc._f(v) for c, v in row.items()}
                                                             for r, row in pd.crosstab(P.typ, P.typn, normalize='index').iterrows()}
                    R['transition_counts'] = {r: {c: int(v) for c, v in row.items()} for r, row in pd.crosstab(P.typ, P.typn).iterrows()}
                    rob = {}
                    nf = P.wd.to_numpy() != 4
                    rob['excl_friday_to_monday'] = cell(P[nf], P.TD[nf].to_numpy(float), P.BAL1n[nf].to_numpy(float), ms, rng, False)['pooled']
                    for nm, dv in (('up_trend_days', 1), ('down_trend_days', -1)):
                        msk = ((P.TD == 0) | (P.dir == dv)).to_numpy()
                        cnd = ((P.TD == 1) & (P.dir == dv)).to_numpy(float)
                        rob[nm] = cell(P[msk], cnd[msk], P.BAL1n[msk].to_numpy(float), ms, rng, False)['pooled'] | {'n': int(cnd.sum())}
                    yrs = P.year.to_numpy(); ys = sorted(set(yrs))
                    tdv, b1 = P.TD.to_numpy(float), P.BAL1n.to_numpy(float)
                    rob['per_year_rd'] = {str(y): oc._f(rd(tdv[yrs == y], b1[yrs == y])) for y in ys}
                    w = np.array([((tdv > 0) & (yrs == y)).sum() for y in ys])
                    th = np.array([rd(tdv[yrs == y], b1[yrs == y]) for y in ys])
                    rob['year_share'] = oc.year_shares(np.array(ys), np.nan_to_num(w * th))
                    cuts = np.nanpercentile(P.relsig[P.split == 0], [100 / 3, 200 / 3])
                    ter = np.digitize(P.relsig, cuts)
                    rob['by_prior_sigma_tercile'] = {f'T{k + 1}': cell(P[ter == k], tdv[ter == k], b1[ter == k], ms, rng, False)['pooled']
                                                     | {'n_TD': int(tdv[ter == k].sum())} for k in range(3)}
                    R['robustness'] = rob
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
            R['verdict_CL009_retro'] = v
            n_sup += v == 'SUPPORTED'; n_rej += v == 'REJECTED'
            # HYP-013
            lo, hi = R['P_TD_13p_primary_pooled']['ci95']
            R['HYP013'] = {'P_TDb': R['P_TD_13p_primary_pooled']['theta'], 'ci95': [lo, hi],
                           'consistent_S46_10_20': bool(lo is not None and hi >= 0.10 and lo <= 0.20),
                           'consistent_S42_20_30': bool(lo is not None and hi >= 0.20 and lo <= 0.30)}
            # HYP-010
            anc = oc.PRIMARY_ANCHOR[s]
            c2 = R['cells'][f'primary:{anc}|13p|BAL2']
            lo, hi = c2['pooled_P_out_given_cond']['ci95']
            if c2['n_cond'] < 100:
                res = 'UNDETERMINED (n < 100)'
            elif hi is not None and hi < 0.85:
                res = 'REFUTED for the analogue'
            elif lo is not None and lo > 0.95:
                res = 'ABOVE RANGE'
            else:
                res = 'CONSISTENT'
            R['HYP010'] = {'P_BAL2_given_TD': c2['pooled_P_out_given_cond']['theta'], 'ci95': [lo, hi],
                           'P_BAL2_given_not_TD': c2['P_out_given_not'], 'n_TD': c2['n_cond'], 'result': res,
                           'counted': oc.PROFILE_PROXY_VALID[s]}
        ov = 'SUPPORTED-RETRO' if n_sup >= 3 else 'REJECTED' if n_rej >= 3 else 'INCONCLUSIVE'
        persist = sum(1 for s in oc.SYMBOLS if (out['symbols'][s]['persistence']['rd']['ci95'][0] or -1) > 0)
        if ov == 'SUPPORTED-RETRO' and persist < 3:
            reading = "Axia's sequence holds retrospectively for XAU/FX (DeepCharts' ~10 % already refuted in OF-20) - pending prospective confirmation (§6)"
        elif ov == 'REJECTED' and persist >= 3:
            reading = "Continuation (DeepCharts-style) reading holds; Axia's does not transfer"
        elif ov == 'REJECTED':
            reading = 'Day types ~independent; neither claim adds information'
        else:
            reading = 'Unresolved; GAP-K04 stays open'
        out['overall_CL009_retro'] = {'supported': n_sup, 'rejected': n_rej, 'verdict': ov}
        out['resolution'] = {'persistence_ci_above_0_symbols': persist, 'reading': reading}
    fn = os.path.join(oc.HERE, f'of20b_results_{args.stage}.json' if not full else 'of20b_results.json')
    with open(fn, 'w') as f:
        json.dump(out, f, indent=1, default=lambda x: oc._f(x) if isinstance(x, (np.floating, float)) else int(x) if isinstance(x, np.integer) else str(x))
    print('wrote', fn)
    return 0


if __name__ == '__main__':
    sys.exit(main())
