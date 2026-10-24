#!/usr/bin/env python3
"""C2 daily FX/XAU time-series momentum (PREREG_C2_TSMOM.md).

Usage: python c2_tsmom.py --stage disc|val|full
Research only: reads local Pepperstone D1 + contracts.json; writes results in this folder.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np
import pandas as pd

import of_common as oc

sys.path.insert(0, '~/NEXA-Agent-Lab/filesnexa/NEXA/research')
from nexa_robust import deflated_sharpe   # noqa: E402  (read-only import)

DATA = '~/NEXA-Agent-Lab/filesnexa/NEXA/data/pepperstone'
U8 = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'NZDUSD', 'USDCAD', 'USDCHF', 'XAUUSD']
NEXA4 = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
USD_BASE = {'USDJPY', 'USDCAD', 'USDCHF'}
SPREAD = {'EURUSD': 0.00004, 'GBPUSD': 0.00008, 'USDJPY': 0.005, 'AUDUSD': 0.00006, 'NZDUSD': 0.00009,
          'USDCAD': 0.00009, 'USDCHF': 0.00009, 'XAUUSD': 0.30}                              # §4 (price units)
SLIP_BP = {'S0': 0.0, 'S1': 0.5, 'S2': 1.0}
TARGET_VOL, LEV_CAP, COM, STOP_K = 0.10, 3.0, 60, 3.0
ROLL_W = {0: 1, 1: 1, 2: 3, 3: 1, 4: 1}                                                     # Mon..Fri (Wed x3)
SPLIT_END = {0: '2012-12-31', 1: '2019-12-31', 2: '2026-09-25'}
SEED, NREP, BLOCK_M = 20261011, 1000, 12


# ----------------------------------------------------------------------------- data
def load_panel(symbols: list, cutoff: str) -> dict:
    frames = {}
    for s in symbols:
        d = pd.read_csv(os.path.join(DATA, f'PEPPERSTONE_{s}_D1.csv'), parse_dates=['time'])
        d = d[d.time.dt.dayofweek < 5]
        d = d[d.time <= pd.Timestamp(cutoff)].drop_duplicates('time').set_index('time').sort_index()
        frames[s] = d
    dates = sorted(set().union(*[set(f.index) for f in frames.values()]))
    idx = pd.DatetimeIndex(dates)
    P = {k: np.full((len(idx), len(symbols)), np.nan) for k in ('O', 'H', 'L', 'C')}
    for j, s in enumerate(symbols):
        f = frames[s].reindex(idx)
        for k, col in (('O', 'open'), ('H', 'high'), ('L', 'low'), ('C', 'close')):
            P[k][:, j] = f[col].to_numpy(float)
    P['dates'] = idx
    P['symbols'] = symbols
    P['valid'] = np.isfinite(P['C'])
    return P


def ewma_sigma(close: np.ndarray, com: int = COM) -> np.ndarray:
    """Annualised EWMA sigma of daily log returns, using data <= t; NaN until 60 returns exist."""
    out = np.full(len(close), np.nan)
    ok = np.isfinite(close)
    c = close[ok]
    r = np.diff(np.log(c))
    v = pd.Series(r ** 2).ewm(com=com, adjust=True).mean().to_numpy()
    sig = np.sqrt(261.0 * v)
    sig[:59] = np.nan
    pos = np.where(ok)[0]
    out[pos[1:]] = sig
    return out


def own_positions(valid_col: np.ndarray) -> np.ndarray:
    """For each union-date index, the count of valid bars up to and including it minus 1 (own-series position)."""
    return np.cumsum(valid_col) - 1


def signals_at(P: dict, dec_idx: np.ndarray, L: int | str) -> np.ndarray:
    """K x N signal matrix in {-1,0,+1}, NaN if invalid; uses only the instrument's bars <= decision date."""
    C = P['C']; T, N = C.shape
    out = np.full((len(dec_idx), N), np.nan)
    for j in range(N):
        vc = P['valid'][:, j]
        cc = C[vc, j]
        pos = own_positions(vc)
        lags = [21, 63, 252] if L == 'COMBO' else [L]
        need = (252 if L == 'COMBO' else L) + 60
        for k, t in enumerate(dec_idx):
            p = pos[t]
            if p < need:
                continue
            ss = [np.sign(math.log(cc[p]) - math.log(cc[p - lg])) for lg in lags]
            out[k, j] = np.sign(np.mean(ss)) if L == 'COMBO' else ss[0]
    return out


def rebalance_days(dates: pd.DatetimeIndex, freq: str) -> np.ndarray:
    key = dates.to_period('M') if freq == 'M' else dates.to_period('W-FRI')
    s = pd.Series(np.arange(len(dates)), index=dates)
    last = s.groupby(key).max().to_numpy()
    return last[last < len(dates) - 1]                          # need a next day to execute


# ----------------------------------------------------------------------------- costs
def side_cost_frac(sym: str, price: np.ndarray, slip_bp: float, cost_mult: float = 1.0) -> np.ndarray:
    if sym in USD_BASE:
        comm_bp = 0.35 * np.ones_like(price)
    elif sym == 'XAUUSD':
        comm_bp = 0.035 / price * 1e4
    else:
        comm_bp = 0.35 / price
    half_spread_bp = SPREAD[sym] / 2.0 / price * 1e4
    return ((comm_bp + half_spread_bp) * cost_mult + slip_bp) / 1e4


def swap_charge_frac(swap_pts: float, point: float, price: np.ndarray, mode: str) -> np.ndarray:
    """Per unit notional per rollover. mode: charges (option a) | none | sym | x2. Positive = cost."""
    if mode == 'none':
        return np.zeros_like(price)
    if mode == 'sym':
        return -swap_pts * point / price
    c = max(0.0, -swap_pts) * point / price
    return 2 * c if mode == 'x2' else c


# ----------------------------------------------------------------------------- simulator
def simulate(P: dict, specs: dict, dec_idx: np.ndarray, S: np.ndarray, slip: str = 'S1', swap: str = 'charges',
             cost_mult: float = 1.0, track: bool = False) -> dict:
    """S: R x K x N signals (NaN = invalid). Returns daily portfolio returns R x T (+ per-instrument for row 0)."""
    O, H, Lo, C, V = P['O'], P['H'], P['L'], P['C'], P['valid']
    T, N = C.shape
    Rn = S.shape[0]
    syms = P['symbols']
    sig = np.column_stack([ewma_sigma(C[:, j]) for j in range(N)])
    exec_idx = dec_idx + 1
    k_of_day = {int(e): k for k, e in enumerate(exec_idx)}
    w = np.zeros((Rn, N)); entry = np.full((Rn, N), np.nan); dist = np.zeros((Rn, N))
    nact = np.zeros(Rn)
    out = np.zeros((Rn, T))
    inst = np.zeros((N, T)) if track else None
    stops = 0; turnover = np.zeros(Rn)
    slipbp = SLIP_BP[slip]
    spr = np.array([SPREAD[s] for s in syms])
    lastC = np.full(N, np.nan)
    for t in range(T):
        v = V[t]
        contrib = np.zeros((Rn, N)); cost = np.zeros((Rn, N))
        if t in k_of_day:
            k = k_of_day[t]
            d = dec_idx[k]
            s_k = S[:, k, :]
            sg = sig[d]
            scale = np.where(np.isfinite(sg) & (sg > 0), np.minimum(LEV_CAP, TARGET_VOL / np.where(sg > 0, sg, 1)), np.nan)
            wn = np.where(np.isfinite(s_k) & np.isfinite(scale), s_k * scale, 0.0)
            nact = np.sum(np.isfinite(s_k) & np.isfinite(scale)[None, :], axis=1).astype(float)
            # overnight part with old weights, then trade at the open
            for j in range(N):
                if not v[j]:
                    wn[:, j] = w[:, j]                            # no bar: cannot trade; keep
                    continue
                if np.isfinite(lastC[j]):
                    contrib[:, j] += w[:, j] * (O[t, j] / lastC[j] - 1)
                sc = side_cost_frac(syms[j], np.array([O[t, j]]), slipbp, cost_mult)[0]
                dw = np.abs(wn[:, j] - w[:, j])
                cost[:, j] += dw * sc; turnover += dw
                entry[:, j] = O[t, j]
                sd = sig[d, j] / math.sqrt(261) if np.isfinite(sig[d, j]) else np.nan
                dist[:, j] = STOP_K * sd * math.sqrt(21) * O[t, j] if np.isfinite(sd) else np.inf
            w = wn
            ref = np.where(v, O[t], np.nan)                       # intraday reference = open
            from_open = True
        else:
            ref = lastC
            from_open = False
        for j in range(N):
            if not v[j]:
                continue
            wj = w[:, j]
            if not from_open and not np.isfinite(ref[j]):
                continue
            base = ref[j]
            stop_long = entry[:, j] - dist[:, j]
            stop_short = entry[:, j] + dist[:, j]
            longm = wj > 0; shortm = wj < 0
            fill = np.full(Rn, np.nan)
            if not from_open:
                gl = longm & (O[t, j] <= stop_long)
                gs = shortm & (O[t, j] + spr[j] >= stop_short)
                fill[gl] = O[t, j]; fill[gs] = O[t, j] + spr[j]
            hl = longm & np.isnan(fill) & (Lo[t, j] <= stop_long)
            hs = shortm & np.isnan(fill) & (H[t, j] + spr[j] >= stop_short)
            fill[hl] = stop_long[hl]; fill[hs] = stop_short[hs]
            hit = np.isfinite(fill)
            contrib[:, j] += np.where(hit, wj * (fill / base - 1), wj * (C[t, j] / base - 1))
            if hit.any():
                sc = side_cost_frac(syms[j], np.array([C[t, j]]), slipbp, cost_mult)[0]
                cost[hit, j] += np.abs(wj[hit]) * sc
                turnover[hit] += np.abs(wj[hit])
                stops += int(hit[0]) if Rn else 0
                w[hit, j] = 0.0
            # swap for positions held over this server day's rollover
            if t < T - 1:
                dow = P['dates'][t].dayofweek
                sp = specs[syms[j]]
                cl = swap_charge_frac(sp['swap_long'], sp['point'], np.array([C[t, j]]), swap)[0]
                cs = swap_charge_frac(sp['swap_short'], sp['point'], np.array([C[t, j]]), swap)[0]
                ch = np.where(w[:, j] > 0, cl, np.where(w[:, j] < 0, cs, 0.0)) * np.abs(w[:, j]) * ROLL_W.get(dow, 0)
                cost[:, j] += ch
        denom = np.where(nact > 0, nact, np.nan)
        net = (contrib - cost)
        out[:, t] = np.nan_to_num(net.sum(axis=1) / denom)
        if track:
            inst[:, t] = np.nan_to_num(net[0] / denom[0]) if np.isfinite(denom[0]) else 0.0
        lastC = np.where(v, C[t], lastC)
    return {'daily': out, 'inst': inst, 'stops': stops, 'turnover': turnover, 'dates': P['dates']}


def monthly(daily_row: np.ndarray, dates: pd.DatetimeIndex) -> pd.Series:
    s = pd.Series(daily_row, index=dates)
    return s.groupby(dates.to_period('M')).apply(lambda x: float(np.prod(1 + x) - 1))


# ----------------------------------------------------------------------------- statistics
def mboot(x: np.ndarray, B: int = 2000) -> dict:
    x = np.asarray(x, float)
    if len(x) < 6:
        return {'n': int(len(x)), 'theta': oc._f(x.mean()) if len(x) else None}
    rng = np.random.default_rng(SEED)
    reps = np.array([x[oc.block_indices(len(x), rng, BLOCK_M)].mean() for _ in range(B)])
    sd = x.std(ddof=1)
    return {'n': int(len(x))} | oc.boot_summary(float(x.mean()), reps) | {
        'sharpe_ann': oc._f(x.mean() / sd * math.sqrt(12)) if sd > 0 else None}


def split_of_month(p: pd.Period) -> int:
    s = str(p)
    return 0 if s <= '2012-12' else 1 if s <= '2019-12' else 2


def circular_shift(S0: np.ndarray, rng, nrep: int) -> np.ndarray:
    """Rotate each instrument's VALID signal months by an independent offset in [24, K_valid - 24] (wrap-around);
    warm-up (NaN) months stay NaN, so the active universe is unchanged."""
    K, N = S0.shape
    out = np.full((nrep, K, N), np.nan)
    for j in range(N):
        idx = np.where(np.isfinite(S0[:, j]))[0]
        vals = S0[idx, j]
        kv = len(idx)
        for r in range(nrep):
            off = int(rng.integers(24, max(25, kv - 24)))
            out[r, idx, j] = np.roll(vals, off)
    return out


def markov_signs(S0: np.ndarray, rng, nrep: int) -> np.ndarray:
    K, N = S0.shape
    out = np.full((nrep, K, N), np.nan)
    for j in range(N):
        col = S0[:, j]; ok = np.isfinite(col)
        vals = col[ok]
        pflip = np.mean(vals[1:] != vals[:-1]) if len(vals) > 1 else 0.5
        idx = np.where(ok)[0]
        for r in range(nrep):
            s = np.empty(len(idx)); s[0] = rng.choice([-1, 1])
            fl = rng.random(len(idx)) < pflip
            for i in range(1, len(idx)):
                s[i] = -s[i - 1] if fl[i] else s[i - 1]
            out[r, idx, j] = s
    return out


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', choices=['disc', 'val', 'full'], required=True)
    args = ap.parse_args()
    ms = oc.stage_max_split(args.stage)
    full = args.stage == 'full'
    cutoff = SPLIT_END[ms]
    specs = json.load(open(os.path.join(DATA, 'contracts.json')))
    rng = np.random.default_rng(SEED)
    out = {'hypothesis': 'C2 TSMOM', 'prereg': ['PREREG_C2_TSMOM.md'], 'stage': args.stage,
           'splits_opened': oc.SPLIT_NAMES[:ms + 1], 'cells': {}}

    def run_cell(univ, L, freq, slip='S1', swap='charges', cost_mult=1.0, S_override=None, track=False):
        P = load_panel(univ, cutoff)
        dec = rebalance_days(P['dates'], freq)
        S0 = signals_at(P, dec, L) if S_override is None else S_override
        Sx = S0[None] if S0.ndim == 2 else S0
        sim = simulate(P, specs, dec, Sx, slip, swap, cost_mult, track)
        return P, dec, S0, sim

    # common evaluation start: first month after the primary cell's first valid execution
    Pp, decp, S_prim, sim_p = run_cell(U8, 252, 'M', track=True)
    first_exec = decp[np.where(np.isfinite(S_prim).any(axis=1))[0][0]] + 1
    eval_start = Pp['dates'][first_exec].to_period('M') + 1
    out['eval_start_month'] = str(eval_start)

    def eval_series(sim, row=0):
        m = monthly(sim['daily'][row], sim['dates'])
        return m[m.index >= eval_start]

    def report(m: pd.Series) -> dict:
        rep = {}
        sp = np.array([split_of_month(p) for p in m.index])
        for s in range(ms + 1):
            rep[oc.SPLIT_NAMES[s]] = mboot(m.to_numpy()[sp == s])
        rep['pooled'] = mboot(m.to_numpy())
        return rep

    m_prim = eval_series(sim_p)
    out['primary'] = {'cell': 'L252|M|U8|S1|swap=charges', 'monthly': report(m_prim)}
    # variants of the primary
    var = {}
    for nm, kw in (('S0', dict(slip='S0')), ('S2', dict(slip='S2')), ('cost_x2', dict(cost_mult=2.0)),
                   ('ex_swap', dict(swap='none')), ('swap_sym', dict(swap='sym')), ('swap_x2', dict(swap='x2'))):
        _, _, _, sv = run_cell(U8, 252, 'M', **kw)
        var[nm] = report(eval_series(sv))
    out['primary_variants'] = var
    # long-only N1
    S_lo = np.where(np.isfinite(S_prim), 1.0, np.nan)
    _, _, _, slo = run_cell(U8, 252, 'M', S_override=S_lo)
    m_lo = eval_series(slo)
    out['N1_long_only'] = report(m_lo)
    # placebo N2 and N3 (batched)
    S_eval = S_prim
    plc = circular_shift(S_eval, rng, NREP)
    _, _, _, sp2 = run_cell(U8, 252, 'M', S_override=plc)
    pm = np.array([eval_series(sp2, r).mean() for r in range(NREP)])
    obs = m_prim.mean()
    out['N2_placebo'] = {'observed_mean': oc._f(obs), 'placebo_mean': oc._f(pm.mean()), 'placebo_p95': oc._f(np.percentile(pm, 95)),
                         'p_N2': oc._f((1 + np.sum(pm >= obs)) / (NREP + 1))}
    mk = markov_signs(S_eval, rng, NREP)
    _, _, _, sp3 = run_cell(U8, 252, 'M', S_override=mk)
    p3 = np.array([eval_series(sp3, r).mean() for r in range(NREP)])
    out['N3_markov'] = {'placebo_mean': oc._f(p3.mean()), 'p_N3': oc._f((1 + np.sum(p3 >= obs)) / (NREP + 1))}
    # per-instrument and per-year contributions (primary)
    inst = sim_p['inst']
    dates = sim_p['dates']
    keep = dates.to_period('M') >= eval_start
    contrib = {s: float(inst[j, keep].sum()) for j, s in enumerate(U8)}
    tot = sum(contrib.values())
    out['instruments'] = {'sum_daily_contrib': contrib, 'share': {s: oc._f(v / tot) if tot else None for s, v in contrib.items()},
                          'n_positive': int(sum(v > 0 for v in contrib.values()))}
    yrs = np.array([p.year for p in m_prim.index])
    out['years'] = oc.year_shares(yrs, m_prim.to_numpy()) | {
        'mean_by_year': {str(y): oc._f(m_prim[yrs == y].mean()) for y in sorted(set(yrs))}}
    # risk descriptors
    eq = (1 + m_prim).cumprod(); dd = (eq / eq.cummax() - 1).min()
    ann = (1 + m_prim.mean()) ** 12 - 1
    out['descriptors'] = {'ann_return': oc._f(ann), 'max_drawdown': oc._f(dd), 'calmar': oc._f(ann / abs(dd)) if dd < 0 else None,
                          'stops_primary': int(sim_p['stops']),
                          'turnover_per_year': oc._f(float(sim_p['turnover'][0]) / max(1, len(m_prim) / 12) / len(U8)),
                          'rolling36_sharpe_min_median': [oc._f(x) for x in np.nanpercentile(
                              (m_prim.rolling(36).mean() / m_prim.rolling(36).std() * math.sqrt(12)).dropna(), [0, 50])] if len(m_prim) > 40 else None}
    # 16-cell grid
    srs = []
    for univ_nm, univ in (('U8', U8), ('NEXA4', NEXA4)):
        for L in (21, 63, 252, 'COMBO'):
            for freq in ('M', 'W'):
                key = f'L{L}|{freq}|{univ_nm}'
                _, _, _, sc = run_cell(univ, L, freq)
                mc = eval_series(sc)
                out['cells'][key] = report(mc)
                srs.append(mc.mean() / mc.std(ddof=1))
    var_sr = float(np.var(srs, ddof=1))
    out['DSR'] = {'primary': oc._f(deflated_sharpe(m_prim.to_numpy(), 16, var_sr)), 'var_sr_trials': var_sr,
                  'sr_primary_monthly': oc._f(m_prim.mean() / m_prim.std(ddof=1))}
    sec = [k for k in out['cells'] if k != 'L252|M|U8']
    for k, a in zip(sec, oc.bh([out['cells'][k].get('discovery', {}).get('p_one_sided') for k in sec])):
        out['cells'][k]['disc_p_BH_secondary'] = a
    if full:
        r = out['primary']['monthly']; v = out['primary_variants']
        lo_sh = out['N1_long_only']['pooled'].get('sharpe_ann') or -9
        inst_sh = out['instruments']['share']
        crit = {
            '1_disc_p_lt_0.05_and_pos': bool((r['discovery'].get('theta') or -1) > 0 and (r['discovery'].get('p_one_sided') or 1) < 0.05),
            '2_val_hold_pos': bool((r['validation'].get('theta') or -1) > 0 and (r['holdout'].get('theta') or -1) > 0),
            '3_pooled_ci_lo_gt_0': bool((r['pooled']['ci95'][0] or -1) > 0),
            '4_placebo_and_beats_long_only': bool(out['N2_placebo']['p_N2'] < 0.05 and (r['pooled'].get('sharpe_ann') or -9) > lo_sh),
            '5_ex_swap_and_swap_x2_pos': bool((v['ex_swap']['pooled'].get('theta') or -1) > 0 and (v['swap_x2']['pooled'].get('theta') or -1) > 0),
            '6_breadth': bool(out['instruments']['n_positive'] >= 5 and max(x for x in inst_sh.values() if x is not None) <= 0.5),
            '7_stability': bool(not out['years']['flag_year_gt_50pct'] and (v['cost_x2']['holdout'].get('theta') or -1) > 0),
            '8_dsr': bool((out['DSR']['primary'] or 0) >= 0.95)}
        out['acceptance'] = crit
        nh = r['holdout']['n']; npool = r['pooled']['n']
        if nh < 60 or npool < 250:
            vd = 'INSUFFICIENT-N'
        elif (v['S0']['pooled'].get('theta') or 0) <= 0 or np.sign(r['discovery'].get('theta') or 0) * np.sign(r['holdout'].get('theta') or 0) < 0:
            vd = 'REJECTED'
        elif all(crit.values()):
            vd = 'SUPPORTED (research candidate, G4)'
        else:
            vd = 'INCONCLUSIVE'
        out['verdict'] = vd
    fn = os.path.join(oc.HERE, 'c2_results.json' if full else f'c2_results_{args.stage}.json')
    with open(fn, 'w') as f:
        json.dump(out, f, indent=1, default=lambda x: oc._f(x) if isinstance(x, (np.floating, float)) else int(x) if isinstance(x, np.integer) else str(x))
    print('wrote', fn)
    return 0


if __name__ == '__main__':
    sys.exit(main())
