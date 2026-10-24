#!/usr/bin/env python3
"""OF-16: opening location vs prior-session value (PREREG_OF16_OPEN_LOCATION.md; inherits PREREG_OF_COMMON.md).

Usage: python of16.py --stage disc|val|full
Stage gating implements the pre-registered opening order (discovery -> validation -> holdout, once).
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

import of_common as oc

N3_REPS = 200


def bias(O: float, val: float, vah: float) -> int:
    if O > vah:
        return 1
    if O < val:
        return -1
    return 0


def barrier(h: np.ndarray, l: np.ndarray, O: float, b: int, dist: float) -> tuple[int, bool]:
    """Y2: favourable barrier O + b*dist before adverse O - b*dist. Same-bar double touch = 0. Returns (Y, resolved)."""
    fav, adv = O + b * dist, O - b * dist
    for hh, ll in zip(h, l):
        if b == 1:
            f, a = hh >= fav, ll <= adv
        else:
            f, a = ll <= fav, hh >= adv
        if f and a:
            return 0, True
        if f:
            return 1, True
        if a:
            return 0, True
    return 0, False


# ----------------------------------------------------------------------------- per-day records
def build(S: oc.Sym, anchor: str, max_split: int) -> pd.DataFrame:
    sym = S.sym
    w = oc.BINW[sym]
    rows = []
    excl = {'prev_not_valid': 0, 'sigma_undefined': 0, 'no_anchor_bar': 0, 'no_prev_anchored_profile': 0}
    for i in range(1, len(S.days)):
        day = S.days[i]
        if not oc.is_eval_day(S, i) or S.split[i] > max_split:
            continue
        if not oc.prev_ok(S, i):
            excl['prev_not_valid'] += 1
            continue
        sig = S.sig[i]
        if not np.isfinite(sig) or sig <= 0:
            excl['sigma_undefined'] += 1
            continue
        d = date.fromisoformat(day)
        a = oc.anchor_smin(sym, anchor, d)
        idx, a_bar = oc.session(S, i, a)
        if a_bar is None:
            excl['no_anchor_bar'] += 1
            continue
        O = float(S.o[a_bar]); C = float(S.c[S.end[i] - 1])
        # prior profiles
        pv = S.bars(i - 1)
        h0, l0, c0, v0 = S.h[pv], S.l[pv], S.c[pv], S.tv[pv]
        va_a0 = oc.value_area(h0, l0, c0, v0, w)
        H0, L0 = float(h0.max()), float(l0.min())
        dprev = date.fromisoformat(S.days[i - 1])
        ap = oc.anchor_smin(sym, anchor, dprev)
        sm0 = S.smin[pv]
        ms = sm0 >= ap
        if ms.sum() < 30:
            excl['no_prev_anchored_profile'] += 1
            va_s = None
        else:
            va_s = oc.value_area(h0[ms], l0[ms], c0[ms], v0[ms], w)
            Hs, Ls = float(h0[ms].max()), float(l0[ms].min())
        va_sig = oc.value_area(h0, l0, c0, v0, sig / 50.0)
        # outcomes path from anchor bar to E
        hh, ll = S.h[idx], S.l[idx]
        y2p, r2p = barrier(hh, ll, O, 1, 0.5 * sig)
        y2m, r2m = barrier(hh, ll, O, -1, 0.5 * sig)
        R0 = H0 - L0
        rec = {'i': i, 'day': day, 'split': int(S.split[i]), 'year': d.year, 'wd': d.weekday(), 'O': O, 'C': C,
               'Cprev': float(S.C[i - 1]), 'sig': float(sig), 'sprd': float(S.sprd[i]) if np.isfinite(S.sprd[i]) else np.nan,
               'VAL_A0': va_a0[0] if va_a0 else np.nan, 'VAH_A0': va_a0[1] if va_a0 else np.nan,
               'PVAL_A0': L0 + 0.15 * R0, 'PVAH_A0': H0 - 0.15 * R0,
               'VAL_S': va_s[0] if va_s else np.nan, 'VAH_S': va_s[1] if va_s else np.nan,
               'PVAL_S': (Ls + 0.15 * (Hs - Ls)) if va_s else np.nan, 'PVAH_S': (Hs - 0.15 * (Hs - Ls)) if va_s else np.nan,
               'VAL_SIG': va_sig[0] if va_sig else np.nan, 'VAH_SIG': va_sig[1] if va_sig else np.nan,
               'Y2p': y2p, 'R2p': r2p, 'Y2m': y2m, 'R2m': r2m}
        rows.append(rec)
    df = pd.DataFrame(rows)
    df.attrs['excluded'] = excl
    return df


# ----------------------------------------------------------------------------- statistics
def arrays(df: pd.DataFrame, VAL: np.ndarray, VAH: np.ndarray) -> dict:
    O, C = df.O.to_numpy(), df.C.to_numpy()
    b = np.where(O > VAH, 1, np.where(O < VAL, -1, 0))
    b[~(np.isfinite(VAL) & np.isfinite(VAH))] = 0
    ok = np.isfinite(VAL) & np.isfinite(VAH)
    return {'b': b, 'up': (C > O).astype(float), 'dn': (C < O).astype(float), 'split': df.split.to_numpy(),
            'ok': ok.astype(float)}


def theta16(A: dict, idx: np.ndarray | None = None) -> float:
    b, up, dn, sp, ok = A['b'], A['up'], A['dn'], A['split'], A['ok']
    if idx is not None:
        b, up, dn, sp, ok = b[idx], up[idx], dn[idx], sp[idx], ok[idx]
    num = den = 0.0
    for s in np.unique(sp):
        m = (sp == s) & (ok > 0)
        n = m.sum()
        if n == 0:
            continue
        pi = up[m].mean()
        ab, be = m & (b == 1), m & (b == -1)
        num += up[ab].sum() + dn[be].sum() - ab.sum() * pi - be.sum() * (1 - pi)
        den += ab.sum() + be.sum()
    return num / den if den > 0 else np.nan


def hitrate(A: dict, idx=None) -> float:
    b, up, dn = A['b'], A['up'], A['dn']
    if idx is not None:
        b, up, dn = b[idx], up[idx], dn[idx]
    out = b != 0
    return float((up[b == 1].sum() + dn[b == -1].sum()) / out.sum()) if out.sum() else np.nan


def contrib(A: dict) -> np.ndarray:
    """Per-day numerator contribution (Y - p0) on outside days, using per-split pi."""
    b, up, dn, sp, ok = A['b'], A['up'], A['dn'], A['split'], A['ok']
    c = np.zeros(len(b))
    for s in np.unique(sp):
        m = (sp == s) & (ok > 0)
        pi = up[m].mean() if m.sum() else np.nan
        c[m & (b == 1)] = up[m & (b == 1)] - pi
        c[m & (b == -1)] = dn[m & (b == -1)] - (1 - pi)
    return c


def boot(A: dict, fn, positions: np.ndarray) -> dict:
    sub = {k: v[positions] for k, v in A.items()}
    th = fn(sub)
    reps = oc.bootstrap(lambda ix: fn(sub, ix), len(positions))
    return oc.boot_summary(th, reps)


def n3_placebo(df: pd.DataFrame, VALc: str, VAHc: str, A_real: dict, theta_real: float, rng) -> dict:
    """Geometry-preserving placebo value: donor offsets relative to the donor's prior close, scaled by sigma."""
    VAL, VAH = df[VALc].to_numpy(), df[VAHc].to_numpy()
    offL = (VAL - df.Cprev.to_numpy()) / df.sig.to_numpy()
    offH = (VAH - df.Cprev.to_numpy()) / df.sig.to_numpy()
    ok = np.isfinite(offL) & np.isfinite(offH)
    sp = df.split.to_numpy(); ii = df.i.to_numpy()
    nxt_of = {v: k for k, v in enumerate(ii)}                     # position by day index
    pos_next = np.array([nxt_of.get(v + 1, -1) for v in ii])       # row whose prior day is this row's day
    Cp, sg, O, C = df.Cprev.to_numpy(), df.sig.to_numpy(), df.O.to_numpy(), df.C.to_numpy()
    thetas, ins_rates = [], []
    real_inside = (A_real['b'] == 0) & (A_real['ok'] > 0)
    real_rate = float(((C >= VAL) & (C <= VAH))[real_inside].mean()) if real_inside.sum() else np.nan
    pools = {s: np.where((sp == s) & ok)[0] for s in np.unique(sp)}
    for _ in range(N3_REPS):
        donor = np.full(len(df), -1)
        for s, pool in pools.items():
            tgt = np.where(sp == s)[0]
            dsel = pool[rng.integers(0, len(pool), len(tgt))]
            bad = (dsel == tgt) | (dsel == pos_next[tgt])
            while bad.any():
                dsel[bad] = pool[rng.integers(0, len(pool), bad.sum())]
                bad = (dsel == tgt) | (dsel == pos_next[tgt])
            donor[tgt] = dsel
        pVAL = Cp + offL[donor] * sg
        pVAH = Cp + offH[donor] * sg
        A = arrays(df, pVAL, pVAH)
        A['ok'] = A_real['ok']                                    # same evaluation days as the real cell
        thetas.append(theta16(A))
        ins = (A['b'] == 0) & (A['ok'] > 0)
        ins_rates.append(float(((C >= pVAL) & (C <= pVAH))[ins].mean()) if ins.sum() else np.nan)
    thetas = np.array(thetas); ins_rates = np.array(ins_rates)
    return {'theta_placebo_mean': oc._f(np.nanmean(thetas)), 'theta_placebo_p95': oc._f(np.nanpercentile(thetas, 95)),
            'p_N3': oc._f((1 + np.sum(thetas >= theta_real)) / (N3_REPS + 1)),
            'Y3_inside_close_in_VA_real': oc._f(real_rate), 'Y3_placebo_mean': oc._f(np.nanmean(ins_rates)),
            'Y3_p_N3': oc._f((1 + np.sum(ins_rates >= real_rate)) / (N3_REPS + 1)) if np.isfinite(real_rate) else None}


def cell_stats(df: pd.DataFrame, VALc: str, VAHc: str, max_split: int, full: bool, rng=None, n3: bool = False) -> dict:
    VAL, VAH = df[VALc].to_numpy(), df[VAHc].to_numpy()
    A = arrays(df, VAL, VAH)
    sp = A['split']
    res = {'n_days': int((A['ok'] > 0).sum()), 'n_above': int((A['b'] == 1).sum()), 'n_below': int((A['b'] == -1).sum()),
           'n_inside': int(((A['b'] == 0) & (A['ok'] > 0)).sum())}
    res['share_outside'] = oc._f((res['n_above'] + res['n_below']) / res['n_days']) if res['n_days'] else None
    per = {}
    for s in range(max_split + 1):
        pos = np.where(sp == s)[0]
        if len(pos) == 0:
            continue
        sub = {k: v[pos] for k, v in A.items()}
        per[oc.SPLIT_NAMES[s]] = boot(A, lambda X, ix=None: theta16(X, ix), pos) | {
            'n_outside': int((sub['b'] != 0).sum()), 'hit_rate_H': oc._f(hitrate(sub)),
            'pi_up': oc._f(sub['up'][sub['ok'] > 0].mean())}
    res['per_split'] = per
    allpos = np.arange(len(df))
    res['pooled'] = boot(A, lambda X, ix=None: theta16(X, ix), allpos)
    res['pooled_hit_rate_H'] = boot(A, lambda X, ix=None: hitrate(X, ix) - 0.0, allpos)
    if n3:
        res['N3'] = n3_placebo(df, VALc, VAHc, A, res['pooled']['theta'], rng)
    res['_A'] = A
    return res


def proxy_swap(sym: str, df: pd.DataFrame) -> dict:
    """Robustness: futures A0 VA (cached CME profiles) mapped to spot with the causal basis; EUR/GBP/JPY only."""
    import t1_tickvol_proxy as t1
    fut_code, binw, invert = t1.PAIRS[sym]
    fh = pd.read_csv(os.path.join(t1.DATA, f'{sym}_fut_hourly.csv')).drop_duplicates('utc_hour').set_index('utc_hour')
    fp = pd.read_csv(os.path.join(t1.DATA, f'{sym}_fut_profile.csv'), dtype={'server_day': str}).drop_duplicates('server_day').set_index('server_day')
    spot = t1.load_spot(sym)
    sh = t1.spot_hourly(spot)
    H = sh.join(fh, how='inner')
    H = H[(H.bars >= 30) & (H.vol > 0)]
    Sp = 1.0 / H.closeS if invert else H.closeS
    bday = (np.log(H.close) - np.log(Sp)).groupby(H.sday).median()
    out_val, out_vah = np.full(len(df), np.nan), np.full(len(df), np.nan)
    for k, r in enumerate(df.itertuples()):
        pdays = r.prevday
        if pdays not in fp.index or pdays not in bday.index:
            continue
        fr = fp.loc[pdays]
        vf = np.array([float(x) for x in str(fr.vols).split(';')])
        if vf.sum() <= 0:
            continue
        _, lo, hi = oc.va_greedy(vf)
        b0 = int(fr.bin0)
        FL, FH = (b0 + lo - 0.5) * binw, (b0 + hi + 0.5) * binw
        bb = float(bday[pdays])
        sL, sH = FL / math.exp(bb), FH / math.exp(bb)
        if invert:
            sL, sH = 1.0 / sH, 1.0 / sL
        out_val[k], out_vah[k] = sL, sH
    m = np.isfinite(out_val)
    sub = df[m].copy()
    sub['FVAL'], sub['FVAH'] = out_val[m], out_vah[m]
    if len(sub) < 50:
        return {'n_days': int(len(sub)), 'note': 'too few days'}
    Af = arrays(sub, sub.FVAL.to_numpy(), sub.FVAH.to_numpy())
    At = arrays(sub, sub.VAL_A0.to_numpy(), sub.VAH_A0.to_numpy())
    pos = np.arange(len(sub))
    rf = boot(Af, lambda X, ix=None: theta16(X, ix), pos)
    rt = boot(At, lambda X, ix=None: theta16(X, ix), pos)
    agree = (Af['b'] == At['b']).mean()
    return {'period': [sub.day.iloc[0], sub.day.iloc[-1]], 'n_days': int(len(sub)),
            'theta16_futures_VA': rf, 'theta16_tickvol_VA_same_days': rt,
            'location_label_agreement': oc._f(agree),
            'same_sign': bool(rf['theta'] is not None and rt['theta'] is not None and np.sign(rf['theta']) == np.sign(rt['theta']))}


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', choices=['disc', 'val', 'full'], required=True)
    args = ap.parse_args()
    ms = oc.stage_max_split(args.stage)
    full = args.stage == 'full'
    rng = np.random.default_rng(oc.SEED)
    out = {'hypothesis': 'OF-16', 'prereg': ['PREREG_OF_COMMON.md', 'PREREG_OF16_OPEN_LOCATION.md'], 'stage': args.stage,
           'splits_opened': oc.SPLIT_NAMES[:ms + 1], 'symbols': {}}
    primary_disc_p = {}
    for sym in oc.SYMBOLS:
        S = oc.load(sym)
        R = {'audit': S.audit, 'profile_proxy_valid': oc.PROFILE_PROXY_VALID[sym], 'cells': {}}
        for anc_role, anchor in (('primary', oc.PRIMARY_ANCHOR[sym]), ('secondary', oc.secondary_anchor(sym))):
            df = build(S, anchor, ms)
            df['prevday'] = [S.days[i - 1] for i in df.i]
            R[f'excluded_{anc_role}_anchor'] = df.attrs['excluded']
            for prof, (cl, ch) in (('A0', ('VAL_A0', 'VAH_A0')), ('anchored', ('VAL_S', 'VAH_S'))):
                key = f'{anc_role}:{anchor}|profile:{prof}'
                is_primary = anc_role == 'primary' and prof == 'A0'
                cs = cell_stats(df, cl, ch, ms, full, rng, n3=is_primary and full)
                A = cs.pop('_A')
                R['cells'][key] = cs
                if is_primary:
                    R['primary_cell'] = key
                    primary_disc_p[sym] = cs['per_split'].get('discovery', {}).get('p_one_sided')
                    # secondary outcome Y2 (barrier) and magnitude
                    b = A['b']; out_ = b != 0
                    y2 = np.where(b == 1, df.Y2p, np.where(b == -1, df.Y2m, 0)).astype(float)
                    res2 = np.where(b == 1, df.R2p, np.where(b == -1, df.R2m, False)).astype(bool)
                    sp = df.split.to_numpy()
                    pi = np.array([A['up'][(sp == s)].mean() for s in sp])
                    p0 = np.where(b == 1, pi, 1 - pi)
                    mag = (b * (df.C - df.O) / df.sig).to_numpy()
                    cost_sig = ((np.array([oc.commission(sym, x) for x in df.C]) + df.sprd) / df.sig).to_numpy()
                    R['primary_secondary'] = {
                        'Y2_barrier_rate': oc._f(y2[out_].mean()), 'Y2_minus_0.5': oc._f(y2[out_].mean() - 0.5),
                        'Y2_minus_drift_base': oc._f((y2 - p0)[out_].mean()),
                        'Y2_unresolved_share': oc._f((~res2[out_]).mean()),
                        'Y2_rate_among_resolved': oc._f(y2[out_ & res2].mean()) if (out_ & res2).any() else None,
                        'magnitude_mean_signed_move_sigma': oc._f(np.nanmean(mag[out_])),
                        'median_roundtrip_cost_sigma': oc._f(np.nanmedian(cost_sig))}
                    # 70-80 % figure
                    if full:
                        H = cs['pooled_hit_rate_H']
                        lo, hi = H['ci95']
                        R['claim_70_80'] = {'H': H['theta'], 'ci95': H['ci95'],
                                            'result': ('REFUTED for the analogue' if hi is not None and hi < 0.70 else
                                                       'EXCEEDED' if lo is not None and lo > 0.80 else
                                                       'CONSISTENT' if lo is not None and hi is not None and hi >= 0.70 and lo <= 0.80 else 'UNDETERMINED')}
                    # N2 volume-free pseudo-VA and difference
                    An2 = arrays(df, df.PVAL_A0.to_numpy(), df.PVAH_A0.to_numpy())
                    An2['ok'] = A['ok']
                    pos = np.arange(len(df))
                    th_n2 = theta16(An2)
                    reps = oc.bootstrap(lambda ix: theta16(A, ix) - theta16(An2, ix), len(df))
                    R['N2_volume_free'] = {'theta16_N2': oc._f(th_n2),
                                           'diff_VA_minus_N2': oc.boot_summary(theta16(A) - th_n2, reps)}
                    R['N2_volume_free']['volume_adds_information'] = bool(
                        R['N2_volume_free']['diff_VA_minus_N2']['ci95'][0] is not None and R['N2_volume_free']['diff_VA_minus_N2']['ci95'][0] > 0)
                    # robustness
                    rob = {}
                    for nm, msk in (('above_only', b == 1), ('below_only', b == -1)):
                        A2 = dict(A); A2['b'] = np.where(msk, b, 0)
                        rob[nm] = boot(A2, lambda X, ix=None: theta16(X, ix), pos)
                    nomon = np.where(df.wd.to_numpy() != 0)[0]
                    rob['excl_friday_to_monday'] = boot(A, lambda X, ix=None: theta16(X, ix), nomon)
                    As = arrays(df, df.VAL_SIG.to_numpy(), df.VAH_SIG.to_numpy())
                    rob['sigma_scaled_bins'] = boot(As, lambda X, ix=None: theta16(X, ix), pos)
                    rob['per_year'] = oc.year_shares(df.year.to_numpy(), contrib(A))
                    rob['per_year_theta'] = {str(y): oc._f(theta16({k: v[df.year.to_numpy() == y] for k, v in A.items()}))
                                             for y in sorted(df.year.unique())}
                    if full and sym in ('EURUSD', 'GBPUSD', 'USDJPY'):
                        try:
                            rob['proxy_swap_futures'] = proxy_swap(sym, df)
                        except Exception as e:                   # reported, never silent
                            rob['proxy_swap_futures'] = {'error': repr(e)}
                    R['robustness'] = rob
        out['symbols'][sym] = R
        print(sym, 'done', flush=True)

    # BH: primary family = 3 proxy-valid symbols
    fam = [s for s in oc.SYMBOLS if oc.PROFILE_PROXY_VALID[s]]
    adj = oc.bh([primary_disc_p[s] for s in fam])
    for s, a in zip(fam, adj):
        out['symbols'][s]['primary_disc_p_BH'] = a
    out['symbols']['GBPUSD']['primary_disc_p_BH'] = None
    # secondary family BH
    sec = [(s, k) for s in oc.SYMBOLS for k in out['symbols'][s]['cells'] if k != out['symbols'][s]['primary_cell']]
    sec_p = [out['symbols'][s]['cells'][k]['per_split'].get('discovery', {}).get('p_one_sided') for s, k in sec]
    for (s, k), a in zip(sec, oc.bh(sec_p)):
        out['symbols'][s]['cells'][k]['disc_p_BH_secondary_family'] = a

    if full:
        n_sup = n_rej = 0
        for s in oc.SYMBOLS:
            R = out['symbols'][s]
            c = R['cells'][R['primary_cell']]
            ps = c['per_split']
            extra = R.get('cells')[R['primary_cell']].get('N3', {}).get('p_N3')
            v = oc.verdict(ps['discovery']['theta'], R['primary_disc_p_BH'] if s != 'GBPUSD' else ps['discovery']['p_one_sided'],
                           ps['validation']['theta'], ps['holdout']['theta'], c['pooled']['ci95'][0], c['pooled']['theta'],
                           extra_ok=extra is not None and extra < 0.10)
            R['verdict'] = v if oc.PROFILE_PROXY_VALID[s] else f'{v} (proxy-invalid; not counted)'
            if oc.PROFILE_PROXY_VALID[s]:
                n_sup += v == 'SUPPORTED'; n_rej += v == 'REJECTED'
        out['overall'] = {'supported': n_sup, 'rejected': n_rej,
                          'verdict': 'SUPPORTED' if n_sup >= 2 else 'REJECTED' if n_rej >= 2 else 'INCONCLUSIVE',
                          'rule': '>=2 of {XAUUSD, EURUSD, USDJPY}'}
    fn = os.path.join(oc.HERE, f'of16_results_{args.stage}.json' if not full else 'of16_results.json')
    with open(fn, 'w') as f:
        json.dump(out, f, indent=1, default=lambda x: oc._f(x) if isinstance(x, (np.floating, float)) else int(x) if isinstance(x, np.integer) else str(x))
    print('wrote', fn)
    return 0


if __name__ == '__main__':
    sys.exit(main())
