"""T1 tick-volume <-> real futures volume validation (PREREG_T1_TICKVOL_PROXY.md; hash in PREREG_HASHES.txt).

Research only. Inputs:
  data/<PAIR>_fut_hourly.csv   from Massive (front contract per server day, prereg section 2):
       utc_hour (epoch s), vol, tx, close
  data/<PAIR>_fut_profile.csv  from Massive: server_day, bin0 (int), vols (';'-joined volumes from bin0 upward)
  Pepperstone M1 canonical (spot).
Outputs: t1_results.json, t1_daily.csv, t1_hourly_summary.csv
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats
from scipy.ndimage import gaussian_filter1d
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import roc_auc_score

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
M1 = '~/NEXA-Agent-Lab/filesnexa/NEXA/data/pepperstone/m1_canonical/PEPPERSTONE_{}_M1_canonical.csv.gz'
PAIRS = {'XAUUSD': ('GC', 1.0, False), 'EURUSD': ('6E', 0.0001, False), 'GBPUSD': ('6B', 0.0001, False),
         'USDJPY': ('6J', 0.000001, True)}
START, END = '2024-10-07', '2026-09-25'
DISC_END = '2025-09-30'
EXCLUDE_DAYS = {'XAUUSD': {'2026-03-30'}, 'EURUSD': {'2026-03-30'}}   # deviation D1: front-selection anomaly (missing 2026-03-27 sessions)
SESS = [('ASIA', list(range(23, 24)) + list(range(0, 7))), ('LONDON', list(range(7, 12))),
        ('OVERLAP', list(range(12, 16))), ('NY', list(range(16, 21))), ('LATE', [21, 22])]


def sess_of(h: int) -> str:
    for n, hs in SESS:
        if h in hs:
            return n
    return 'NA'


# ----------------------------------------------------------------- spot
def load_spot(sym: str) -> pd.DataFrame:
    d = pd.read_csv(M1.format(sym), usecols=['time_utc', 'time_server', 'open', 'high', 'low', 'close', 'tick_volume',
                                             'spread'])
    d['tu'] = pd.to_datetime(d.time_utc, utc=True)
    d = d[(d.tu >= pd.Timestamp(START, tz='UTC') - pd.Timedelta(days=70)) & (d.tu < pd.Timestamp(END, tz='UTC') + pd.Timedelta(days=1))]
    d['sday'] = pd.to_datetime(d.time_server).dt.strftime('%Y-%m-%d')
    d['hour'] = (d.tu - pd.Timestamp(0, tz='UTC')) // pd.Timedelta('1h') * 3600
    d['lr'] = np.log(d.close).diff()
    return d.reset_index(drop=True)


def spot_hourly(d: pd.DataFrame) -> pd.DataFrame:
    g = d.groupby('hour')
    h = pd.DataFrame({'VT': g.tick_volume.sum(), 'bars': g.close.size(), 'closeS': g.close.last(),
                      'openS': g.open.first(), 'rv': g.lr.apply(lambda x: float((x ** 2).sum())),
                      'spread': g.spread.median(), 'sday': g.sday.last()})
    h['absret'] = np.abs(np.log(h.closeS / h.openS))
    return h


def server_days(d: pd.DataFrame) -> pd.DataFrame:
    g = d.groupby('sday')
    out = pd.DataFrame({'O': g.open.first(), 'H': g.high.max(), 'L': g.low.min(), 'C': g.close.last(),
                        'bars': g.close.size(), 'TV': g.tick_volume.sum(), 'spr': g.spread.median(),
                        'rv': g.lr.apply(lambda x: float((x ** 2).sum())),
                        'path': g.close.apply(lambda x: float(np.abs(np.diff(np.log(x.to_numpy()))).sum()))})
    out = out[pd.to_datetime(out.index).dayofweek < 5]
    out['ret'] = np.log(out.C / out.C.shift(1))
    out['sig_r'] = out.ret.rolling(20).std().shift(1)            # causal: previous 20 days
    out['er'] = np.abs(np.log(out.C / out.O)) / out.path.replace(0, np.nan)
    out['thin'] = out.bars < 0.8 * out.bars.median()
    out['wd'] = pd.to_datetime(out.index).dayofweek
    out['tv_rel'] = np.log(out.TV / out.groupby('wd').TV.transform(lambda s: s.rolling(8, min_periods=4).median().shift(1)))
    out['spr_rel'] = np.log(out.spr / out.spr.rolling(20, min_periods=10).median().shift(1))
    return out


# ----------------------------------------------------------------- profiles
def va_greedy(v: np.ndarray, alpha: float = 0.70) -> tuple[int, int, int]:
    poc = int(np.argmax(v))
    lo = hi = poc
    tot = v.sum()
    acc = v[poc]
    n = len(v)
    while acc < alpha * tot and (lo > 0 or hi < n - 1):
        up = v[hi + 1:hi + 3].sum() if hi < n - 1 else -1
        dn = v[max(lo - 2, 0):lo].sum() if lo > 0 else -1
        if up >= dn:                                      # ties: upper side first (prereg)
            k = min(2, n - 1 - hi); acc += v[hi + 1:hi + 1 + k].sum(); hi += k
        else:
            k = min(2, lo); acc += v[lo - k:lo].sum(); lo -= k
    return poc, lo, hi


def bimodal(v: np.ndarray) -> tuple[bool, float]:
    s = gaussian_filter1d(v.astype(float), 3)
    if s.max() <= 0:
        return False, 0.0
    pk = [i for i in range(1, len(s) - 1) if s[i] >= s[i - 1] and s[i] > s[i + 1]]
    if len(pk) < 2:
        return False, 0.0
    pk.sort(key=lambda i: -s[i])
    p1, p2 = pk[0], pk[1]
    ratio = s[p2] / s[p1]
    a, b = sorted((p1, p2))
    dip = s[a:b + 1].min()
    return bool(ratio >= 0.6 and dip <= 0.8 * s[p2]), float(ratio)


def jsd(p: np.ndarray, q: np.ndarray) -> float:
    p = p / p.sum(); q = q / q.sum(); m = 0.5 * (p + q)
    def kl(a, b):
        mask = a > 0
        return float((a[mask] * np.log2(a[mask] / b[mask])).sum())
    return 0.5 * kl(p, m) + 0.5 * kl(q, m)


def wasserstein_bins(p: np.ndarray, q: np.ndarray) -> float:
    return float(np.abs(np.cumsum(p / p.sum()) - np.cumsum(q / q.sum())).sum())   # in bins


def block_boot_diff(a: np.ndarray, b: np.ndarray, B: int = 2000, seed: int = 11) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    obs = float(np.nanmean(a) - np.nanmean(b))
    ds = []
    for _ in range(B):
        ds.append(np.nanmean(rng.choice(a, len(a))) - np.nanmean(rng.choice(b, len(b))))
    return obs, float(np.percentile(ds, 2.5)), float(np.percentile(ds, 97.5))


def corr_pack(x: pd.Series, y: pd.Series) -> dict:
    ok = x.notna() & y.notna() & np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 30:
        return {'n': int(ok.sum()), 'pearson': None}
    return {'n': int(ok.sum()), 'pearson': float(np.corrcoef(x[ok], y[ok])[0, 1])}


def analyse(pair: str) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    fut_code, binw, invert = PAIRS[pair]
    fh = pd.read_csv(os.path.join(DATA, f'{pair}_fut_hourly.csv')).drop_duplicates('utc_hour').set_index('utc_hour')
    fp = pd.read_csv(os.path.join(DATA, f'{pair}_fut_profile.csv'), dtype={'server_day': str}).drop_duplicates('server_day').set_index('server_day')
    spot = load_spot(pair)
    sh = spot_hourly(spot)
    sd = server_days(spot)
    res: dict = {'pair': pair, 'futures': fut_code}

    # ---------------- hourly activity
    H = sh.join(fh, how='inner')
    H = H[(H.index >= pd.Timestamp(START).timestamp()) & (H.index < (pd.Timestamp(END) + pd.Timedelta(days=1)).timestamp())]
    H = H[~H.sday.isin(EXCLUDE_DAYS.get(pair, set()))]
    n_all = len(H)
    H = H[(H.bars >= 30) & (H.vol > 0)].copy()
    res['hours'] = {'joined': int(n_all), 'kept': int(len(H))}
    H['lt'], H['lf'] = np.log(H.VT), np.log(H.vol)
    ts = pd.to_datetime(H.index, unit='s', utc=True)
    H['how'] = ts.dayofweek * 24 + ts.hour
    H['uh'] = ts.hour
    H['date'] = ts.strftime('%Y-%m-%d')
    H['wk'] = (ts - pd.Timestamp('2024-01-01', tz='UTC')).days // 7
    for c in ('lt', 'lf'):                                   # M3a causal trailing 8-week median per hour-of-week
        H[c + '_base'] = H.groupby('how')[c].transform(lambda s: s.rolling(8, min_periods=4).median().shift(1))
        H[c + '_res'] = H[c] - H[c + '_base']
        H[c + '_res_b'] = H[c] - H.groupby('how')[c].transform('mean')   # M3b
    disc = H.date <= DISC_END
    act = {'M1_pearson_log': corr_pack(H['lt'], H['lf'])['pearson'],
           'M2_spearman': float(stats.spearmanr(H.VT, H.vol).statistic),
           'M3a_deseason_causal': corr_pack(H.lt_res, H.lf_res),
           'M3b_deseason_fullsample': corr_pack(H.lt_res_b, H.lf_res_b)['pearson'],
           'M3a_discovery': corr_pack(H.lt_res[disc], H.lf_res[disc])['pearson'],
           'M3a_holdout': corr_pack(H.lt_res[~disc], H.lf_res[~disc])['pearson']}
    # M4 rolling 20-trading-day windows step 5
    dates = sorted(H.date.unique())
    roll = []
    for i in range(0, len(dates) - 19, 5):
        w = H[H.date.isin(dates[i:i + 20])]
        cp = corr_pack(w.lt_res, w.lf_res)
        if cp['pearson'] is not None:
            roll.append((dates[i], cp['pearson']))
    rv = np.array([r for _, r in roll])
    act['M4_rolling'] = {'windows': len(rv), 'min': float(rv.min()), 'p05': float(np.percentile(rv, 5)),
                         'median': float(np.median(rv)), 'max': float(rv.max()), 'share_below_0.30': float((rv < 0.30).mean()),
                         'worst_window_start': roll[int(rv.argmin())][0]}
    # M5 regime: daily spot RV tercile and ER tercile (server day; discovery cut-points)
    H = H.join(sd[['rv', 'er']].rename(columns={'rv': 'day_rv', 'er': 'day_er'}), on='sday')
    def tercile_corr(col: str, src: pd.DataFrame) -> dict:
        cuts = np.nanpercentile(src.loc[src.date <= DISC_END, col], [100 / 3, 200 / 3])
        k = np.digitize(src[col], cuts)
        return {f'T{j + 1}': corr_pack(src.lt_res[k == j], src.lf_res[k == j]) for j in range(3)}
    act['M5_by_daily_vol_tercile'] = tercile_corr('day_rv', H)
    act['M5_by_daily_ER_tercile'] = tercile_corr('day_er', H)
    act['M6_by_session'] = {s: corr_pack(H.lt_res[H.uh.map(sess_of) == s], H.lf_res[H.uh.map(sess_of) == s]) for s, _ in SESS}
    act['M7_by_hourly_vol_tercile'] = tercile_corr('rv', H)
    # M8a distributional similarity of seasonal ratios
    a, b = H.lt_res.dropna(), H.lf_res.dropna()
    act['M8a_KS'] = float(stats.ks_2samp(a, b).statistic)
    act['M8a_W1_log'] = float(stats.wasserstein_distance(a, b))
    act['M8a_sd_ratio_T_over_F'] = float(a.std() / b.std())
    # M8b intraday shape JS per UTC date
    js = []
    for dt, g in H.groupby('date'):
        if len(g) >= 20:
            js.append(jsd(g.VT.to_numpy(float), g.vol.to_numpy(float)))
    act['M8b_JS_daily_shape'] = {'days': len(js), 'median': float(np.median(js)), 'p90': float(np.percentile(js, 90))}
    res['activity'] = act

    # ---------------- basis (hourly closes) and HYP-034
    Sp = 1.0 / H.closeS if invert else H.closeS
    H['b'] = np.log(H.close) - np.log(Sp)
    bday = H.groupby('sday').b.median()
    H['b_causal'] = H.sday.map(bday.shift(1))
    sig_r = sd.sig_r
    H['map_err'] = np.abs(H.b - H.b_causal) / H.sday.map(sig_r)
    roll_days = set()
    if 'front' in fp.columns:
        fr = fp.front
        chg = fr[fr != fr.shift(1)].index[1:]
        for d0 in chg:
            roll_days.add(d0)
            nxt = fr.index[fr.index.get_loc(d0) + 1] if fr.index.get_loc(d0) + 1 < len(fr) else None
            if nxt: roll_days.add(nxt)
    me = H.loc[~H.sday.isin(roll_days), 'map_err'].dropna()
    res['basis'] = {'hours': int(len(me)), 'share_le_0.1sig': float((me <= 0.1).mean()), 'median_err_sig': float(me.median()),
                    'p95_err_sig': float(np.percentile(me, 95)), 'roll_days_excluded': len(roll_days),
                    'basis_start_bp': float(bday.iloc[0] * 1e4), 'basis_end_bp': float(bday.iloc[-1] * 1e4)}

    # ---------------- daily profiles
    rows = []
    for day, fr_ in fp.iterrows():
        if day < START or day > END or day in EXCLUDE_DAYS.get(pair, set()) or day not in sd.index or day not in bday.index:
            continue
        vf = np.array([float(x) for x in str(fr_.vols).split(';')])
        b0 = int(fr_.bin0)
        g = spot[spot.sday == day]
        if len(g) < 100 or vf.sum() <= 0:
            continue
        typ = (g.high + g.low + g.close) / 3.0
        sp_ = 1.0 / typ if invert else typ
        out = {}
        for bname, bval in (('align', bday[day]), ('causal', bday.shift(1).get(day, np.nan))):
            if not np.isfinite(bval):
                continue
            fprice = np.exp(np.log(sp_) + bval)
            bins = np.round(fprice / binw).astype(int)
            lo_b, hi_b = min(bins.min(), b0), max(bins.max(), b0 + len(vf) - 1)
            n = hi_b - lo_b + 1
            if n > 5000:
                continue
            VT = np.zeros(n); VF = np.zeros(n)
            np.add.at(VT, bins - lo_b, g.tick_volume.to_numpy(float))
            VF[b0 - lo_b:b0 - lo_b + len(vf)] = vf
            pT, loT, hiT = va_greedy(VT); pF, loF, hiF = va_greedy(VF)
            price = lambda i: (lo_b + i) * binw
            sr = sd.loc[day, 'sig_r']
            e = lambda i, j: abs(math.log(price(i) / price(j))) / sr if sr and sr > 0 else np.nan
            inter = max(0, min(hiT, hiF) - max(loT, loF) + 1); union = max(hiT, hiF) - min(loT, loF) + 1
            out[bname] = {'P1': e(pT, pF), 'P2': e(hiT, hiF), 'P3': e(loT, loF), 'P4': inter / union,
                          'P5': jsd(VT + 1e-12, VF + 1e-12), 'P6': wasserstein_bins(VT, VF) * binw / price(pF) / sr,
                          'P7': float(VT @ VF / (np.linalg.norm(VT) * np.linalg.norm(VF))),
                          'vah_T': price(hiT), 'val_T': price(loT), 'vah_F': price(hiF), 'val_F': price(loF)}
            if bname == 'align':
                bmF, rF = bimodal(VF); bmT, rT = bimodal(VT)
                VTn = VT[VT > 0] / VT.sum()
                Hn = -(VTn * np.log(VTn)).sum() / math.log(max(len(VTn), 2))
                out['bim_F'], out['bim_T'], out['ratio_T'], out['ratio_F'], out['conc_T'] = bmF, bmT, rT, rF, 1 - Hn
        if 'align' not in out:
            continue
        r = {'day': day, **{f'{k}_{b}': v for b in ('align', 'causal') if b in out for k, v in out[b].items()},
             'bim_F': out['bim_F'], 'bim_T': out['bim_T'], 'z1': out['ratio_T'] if out['bim_T'] or out['ratio_T'] > 0 else 0.0,
             'z2': out['conc_T'], 'z3': sd.loc[day, 'tv_rel'], 'z4': sd.loc[day, 'bars'] / sd.bars.median(),
             'z5': sd.loc[day, 'spr_rel'], 'z6': (sd.loc[day, 'H'] - sd.loc[day, 'L']) / sd.loc[day, 'C'] / sd.loc[day, 'sig_r'],
             'thin': bool(sd.loc[day, 'thin']), 'b_causal': bday.shift(1).get(day, np.nan)}
        rows.append(r)
    D = pd.DataFrame(rows).set_index('day')
    D['reliable'] = ((D.P1_align <= 0.25) & (D.P4_align >= 0.70)).astype(int)
    prof = {'days': int(len(D)), 'thin_days': int(D.thin.sum())}
    for b in ('align', 'causal'):
        if f'P1_{b}' not in D:
            continue
        x = D.dropna(subset=[f'P1_{b}'])
        prof[b] = {k: {'median': float(x[f'{k}_{b}'].median()), 'p90': float(x[f'{k}_{b}'].quantile(0.9))}
                   for k in ('P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7')}
        prof[b]['share_P1_le_0.25'] = float((x[f'P1_{b}'] <= 0.25).mean())
        prof[b]['share_reliable'] = float(((x[f'P1_{b}'] <= 0.25) & (x[f'P4_{b}'] >= 0.70)).mean())
    bm = D.bim_F
    prof['P8_bimodal'] = {'share_bimodal_F': float(bm.mean()),
                          'fail_rate_bimodal': float((D.P1_align[bm] > 0.25).mean()) if bm.any() else None,
                          'fail_rate_unimodal': float((D.P1_align[~bm] > 0.25).mean()),
                          'spot_detects_futures_bimodal': {'tp': int((D.bim_T & bm).sum()), 'fp': int((D.bim_T & ~bm).sum()),
                                                           'fn': int((~D.bim_T & bm).sum()), 'tn': int((~D.bim_T & ~bm).sum())}}
    res['profile'] = prof
    res['prereg_verdict'] = {
        'HYP001_activity_M3a_ge_0.50': bool(act['M3a_deseason_causal']['pearson'] >= 0.50),
        'HYP001_profile_medianP4_ge_0.70': bool(prof['align']['P4']['median'] >= 0.70),
        'HYP001_profile_P1_le_0.25_on_ge_60pct': bool(prof['align']['share_P1_le_0.25'] >= 0.60),
        'HYP034_basis_95pct_le_0.1sig': bool(res['basis']['share_le_0.1sig'] >= 0.95)}
    D['pair'] = pair
    H['pair'] = pair
    return res, D, H


def tvpc_models(D: pd.DataFrame, H: pd.DataFrame, results: dict) -> pd.DataFrame:
    D = D.copy()
    D['disc'] = D.index <= DISC_END
    Z = ['z1', 'z2', 'z3', 'z4', 'z5', 'z6']
    fin = np.isfinite(D[Z].astype(float))
    ok = fin.all(axis=1)
    out_nonfinite = {z: int((~fin[z]).sum()) for z in Z}
    X = D.loc[ok, Z].copy()
    mu, sdv = X[D.disc[ok]].mean(), X[D.disc[ok]].std()
    Xs = (X - mu) / sdv
    Xs = pd.concat([Xs, pd.get_dummies(D.loc[ok, 'pair'], drop_first=True).astype(float)], axis=1)
    y = D.loc[ok, 'reliable']
    tr, te = D.disc[ok].to_numpy(), ~D.disc[ok].to_numpy()
    out = {'rows_excluded_nonfinite_z': out_nonfinite, 'rows_used': int(ok.sum()), 'rows_total': int(len(D))}
    if y[tr].nunique() == 2 and y[te].nunique() == 2:
        lr = LogisticRegression(C=1.0, max_iter=1000).fit(Xs[tr], y[tr])
        p = lr.predict_proba(Xs[te])[:, 1]
        clim = y[tr].mean()
        brier = float(((p - y[te]) ** 2).mean()); brier_c = float(((clim - y[te]) ** 2).mean())
        lp = np.log(np.clip(p, 1e-6, 1 - 1e-6) / np.clip(1 - p, 1e-6, 1))
        cal = LogisticRegression(C=1e6, max_iter=1000).fit(lp.reshape(-1, 1), y[te])
        out['TVPC_fitted'] = {'n_train': int(tr.sum()), 'n_test': int(te.sum()), 'base_rate_train': float(clim),
                              'base_rate_test': float(y[te].mean()), 'auc': float(roc_auc_score(y[te], p)),
                              'brier': brier, 'brier_climatology': brier_c, 'calibration_slope': float(cal.coef_[0, 0]),
                              'calibration_intercept': float(cal.intercept_[0]),
                              'coef': dict(zip(Xs.columns, map(float, lr.coef_[0])))}
        D.loc[ok, 'TVPC'] = lr.predict_proba(Xs)[:, 1]
        out['TVPC0'] = {'auc_test': float(roc_auc_score(y[te], 1 - D.loc[ok, 'z1'][te])),
                        'auc_train': float(roc_auc_score(y[tr], 1 - D.loc[ok, 'z1'][tr]))}
    out['acceptance_failure_detectable'] = bool(out.get('TVPC_fitted', {}).get('auc', 0) >= 0.65 and
                                                out['TVPC_fitted']['brier'] < out['TVPC_fitted']['brier_climatology'])
    D['TVPC0'] = 1 - D.z1
    # ---------------- TVPC_activity (hour level)
    H = H.dropna(subset=['lt_res', 'lf_res']).copy()
    H['abs_e'] = np.abs(H.lt_res - H.lf_res)
    H['sess'] = H.uh.map(sess_of)
    H['disc'] = H.date <= DISC_END
    H['rv_t'] = H.groupby('pair').rv.transform(lambda s: pd.qcut(s.rank(method='first'), 3, labels=False))
    H['spr_t'] = H.groupby('pair').spread.transform(lambda s: pd.qcut(s.rank(method='first'), 3, labels=False))
    H['sig_h'] = H.groupby(['pair', 'uh']).absret.transform('median')
    H['ar'] = H.absret / H.sig_h
    XA = pd.concat([pd.get_dummies(H[['sess', 'pair']].astype(str), drop_first=True).astype(float),
                    pd.get_dummies(H.rv_t.astype(int).astype(str), prefix='rvt', drop_first=True).astype(float),
                    pd.get_dummies(H.spr_t.astype(int).astype(str), prefix='sprt', drop_first=True).astype(float),
                    H[['ar', 'lt_res']]], axis=1)
    m = LinearRegression().fit(XA[H.disc], H.abs_e[H.disc])
    pred = m.predict(XA[~H.disc])
    resid = H.abs_e[~H.disc] - pred
    out['TVPC_activity'] = {'n_train': int(H.disc.sum()), 'n_test': int((~H.disc).sum()),
                            'r2_test': float(1 - (resid ** 2).sum() / ((H.abs_e[~H.disc] - H.abs_e[H.disc].mean()) ** 2).sum()),
                            'spearman_pred_vs_realised_test': float(stats.spearmanr(pred, H.abs_e[~H.disc]).statistic),
                            'coef': dict(zip(XA.columns, map(float, m.coef_)))}
    results['tvpc'] = out
    return D


def downstream(D: pd.DataFrame, spot_by_pair: dict, results: dict) -> None:
    """Holdout: agreement of VA-based features computed from spot (T) vs futures (F) profiles, vs TVPC of the profile day."""
    recs = []
    for pair, sp in spot_by_pair.items():
        inv = PAIRS[pair][2]
        Dp = D[D.pair == pair]
        days = list(Dp.index)
        for i in range(len(days) - 1):
            d0, d1 = days[i], days[i + 1]
            if d0 <= DISC_END:
                continue
            r0 = Dp.loc[d0]
            if not np.isfinite(r0.get('vah_T_align', np.nan)) or not np.isfinite(r0.get('b_causal', np.nan)):
                continue
            g = sp[sp.sday == d1]
            sr = r0.get('sig_r', np.nan)
            if not (np.isfinite(sr) and sr > 0):
                continue
            for hh in (8, 14):
                x = g[g.tu.dt.hour == hh]
                if x.empty:
                    continue
                s = float(x.close.iloc[0]); s = 1 / s if inv else s
                f = math.exp(math.log(s) + Dp.loc[d1, 'b_causal']) if np.isfinite(Dp.loc[d1, 'b_causal']) else np.nan
                if not np.isfinite(f):
                    continue
                inT = r0.val_T_align <= f <= r0.vah_T_align
                inF = r0.val_F_align <= f <= r0.vah_F_align
                # F-a (08:00 only): per-edge |distance_T - distance_F| in sigma_day units, averaged over VAH and VAL
                dis = (abs(math.log(f / r0.vah_T_align) - math.log(f / r0.vah_F_align)) +
                       abs(math.log(f / r0.val_T_align) - math.log(f / r0.val_F_align))) / 2 / sr if hh == 8 else np.nan
                recs.append({'pair': pair, 'day': d0, 'hh': hh, 'flag_agree': int(inT == inF),
                             'dist_dis': dis, 'TVPC': r0.get('TVPC', np.nan), 'TVPC0': r0.TVPC0})
    R = pd.DataFrame(recs)
    # day-block unit: one row per (pair, day); flag agreement averaged over 08:00 and 14:00
    Rd = R.groupby(['pair', 'day']).agg(flag_agree=('flag_agree', 'mean'), dist_dis=('dist_dis', 'mean'),
                                         TVPC=('TVPC', 'first'), TVPC0=('TVPC0', 'first')).reset_index()
    out = {'n_records': int(len(R)), 'n_days': int(len(Rd))}
    for sc in ('TVPC', 'TVPC0'):
        x = Rd.dropna(subset=[sc])
        if len(x) < 30:
            continue
        cuts = x[sc].quantile([1 / 3, 2 / 3]).to_numpy()
        top, bot = x[x[sc] >= cuts[1]], x[x[sc] <= cuts[0]]
        xd = x.dropna(subset=['dist_dis'])
        out[sc] = {'spearman_score_vs_neg_flag_disagree': float(stats.spearmanr(x[sc], x.flag_agree).statistic),
                   'spearman_score_vs_neg_dist_disagree': float(stats.spearmanr(xd[sc], -xd.dist_dis).statistic),
                   'flag_disagree_top_minus_bottom': block_boot_diff(1 - top.flag_agree.to_numpy(float), 1 - bot.flag_agree.to_numpy(float)),
                   'dist_disagree_top_minus_bottom': block_boot_diff(top.dist_dis.dropna().to_numpy(float), bot.dist_dis.dropna().to_numpy(float)),
                   'flag_agree_top': float(top.flag_agree.mean()), 'flag_agree_bottom': float(bot.flag_agree.mean()),
                   'pass_rule': 'expected direction = top-minus-bottom disagreement < 0 with 95% CI excluding 0'}
        for k in ('flag_disagree_top_minus_bottom', 'dist_disagree_top_minus_bottom'):
            out[sc][k.replace('top_minus_bottom', 'PASS')] = bool(out[sc][k][2] < 0)
    results['downstream_holdout'] = out


def main() -> int:
    results = {'prereg': 'PREREG_T1_TICKVOL_PROXY.md', 'deviations': [
        'D1: 2026-03-30 excluded for XAUUSD and EURUSD (Massive lacks 2026-03-27 session bars for the main contracts; the prior-session rule picked GCZ6 / 6EU6, thin back months).',
        'D2: the Massive workspace expired mid-export (2026-10-05); later pulls (GC 2026-07-01..10-02, all 6E/6B/6J) use the front schedule '
        'already computed by the section-2 rule from 1session bars on 2026-10-04 (hard-coded, identical rule output), instead of re-deriving it in SQL.',
        'D4: rows with a non-finite TVPC input (z5 = ln(spread/trailing median) is +-inf when a median spread is 0) are excluded from the TVPC fit; counts in tvpc.rows_excluded_nonfinite_z.',
        'D3: downstream test fixed before any downstream output was seen: F-a uses per-edge |d_T - d_F| / sigma_day at 08:00 only '
        '(the draft averaged signed distances); bootstrap resamples days (prereg: day-block), not hour records.'],
        'pairs': {}}
    Ds, Hs, spots = [], [], {}
    only = sys.argv[1:]                      # debug: restrict pairs; output gets a suffix so the final run stays clean
    sfx = '_' + '_'.join(only) if only else ''
    for pair in (only or PAIRS):
        if not os.path.exists(os.path.join(DATA, f'{pair}_fut_hourly.csv')):
            print('missing', pair); continue
        r, D, H = analyse(pair)
        D = D.join(server_days(load_spot(pair))[['sig_r']], how='left')
        results['pairs'][pair] = r
        Ds.append(D); Hs.append(H); spots[pair] = load_spot(pair)
        print(pair, json.dumps(r['prereg_verdict']), flush=True)
    D = pd.concat(Ds); H = pd.concat(Hs)
    D = tvpc_models(D, H, results)
    downstream(D, spots, results)
    D.to_csv(os.path.join(HERE, f't1_daily{sfx}.csv'))
    with open(os.path.join(HERE, f't1_results{sfx}.json'), 'w') as fh:
        json.dump(results, fh, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    return 0


if __name__ == '__main__':
    sys.exit(main())
