"""T1 EXPLORATORY follow-ups (NOT pre-registered; written after t1_results.json was seen).

Why: the pre-registered TVPC input z5 = ln(median spread / trailing median) is undefined on 72-100% of FX days because
Pepperstone records a 0-point raw spread on most FX M1 bars, so the pre-registered fitted TVPC was estimated on a biased
603-of-2019-day subsample (no GBPUSD rows). These variants use every day. They do NOT replace the pre-registered verdict.

  E1: z5 -> z5m = ln(mean spread / trailing 20-day median of daily mean spread)
  E2: z5 dropped
  E0: TVPC0 = 1 - z1 evaluated on all days (pre-registered form, full sample)
Same procedure as tvpc_models(): standardise on discovery, logistic with pair fixed effects, fit discovery, test holdout.
Downstream test re-run with the E1 score in place of the fitted TVPC.
Output: t1_exploratory.json
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

import t1_tickvol_proxy as t1

HERE = os.path.dirname(os.path.abspath(__file__))


def fit_eval(D: pd.DataFrame, Z: list[str]) -> tuple[dict, pd.Series]:
    fin = np.isfinite(D[Z].astype(float)).all(axis=1)
    X = D.loc[fin, Z].astype(float)
    disc = (D.index <= t1.DISC_END)[fin.to_numpy()]
    Xs = (X - X[disc].mean()) / X[disc].std()
    Xs = pd.concat([Xs, pd.get_dummies(D.loc[fin, 'pair'], drop_first=True).astype(float)], axis=1)
    y = D.loc[fin, 'reliable'].astype(int)
    tr, te = disc, ~disc
    lr = LogisticRegression(C=1.0, max_iter=1000).fit(Xs[tr], y[tr])
    p = lr.predict_proba(Xs[te])[:, 1]
    clim = y[tr].mean()
    lp = np.log(np.clip(p, 1e-6, 1 - 1e-6) / np.clip(1 - p, 1e-6, 1))
    cal = LogisticRegression(C=1e6, max_iter=1000).fit(lp.reshape(-1, 1), y[te])
    pair_te = D.loc[fin, 'pair'][te]
    out = {'rows_used': int(fin.sum()), 'n_train': int(tr.sum()), 'n_test': int(te.sum()),
           'auc': float(roc_auc_score(y[te], p)), 'brier': float(((p - y[te]) ** 2).mean()),
           'brier_climatology': float(((clim - y[te]) ** 2).mean()),
           'calibration_slope': float(cal.coef_[0, 0]), 'calibration_intercept': float(cal.intercept_[0]),
           'auc_by_pair': {k: float(roc_auc_score(y[te][pair_te == k], p[(pair_te == k).to_numpy()]))
                           for k in sorted(pair_te.unique()) if y[te][pair_te == k].nunique() == 2},
           'coef': dict(zip(Xs.columns, map(float, lr.coef_[0]))), 'intercept': float(lr.intercept_[0]),
           'standardise_mu_discovery': X[disc].mean().round(6).to_dict(), 'standardise_sd_discovery': X[disc].std().round(6).to_dict()}
    out['meets_prereg_bar_auc_ge_0.65_and_brier_lt_clim'] = bool(out['auc'] >= 0.65 and out['brier'] < out['brier_climatology'])
    score = pd.Series(np.nan, index=D.index)
    score[fin.to_numpy()] = lr.predict_proba(Xs)[:, 1]
    return out, score


def main() -> int:
    D = pd.read_csv(os.path.join(HERE, 't1_daily.csv'), index_col=0)
    D.index = D.index.astype(str)
    spots, z5m = {}, []
    for pair in t1.PAIRS:
        sp = t1.load_spot(pair)
        spots[pair] = sp
        g = sp.groupby('sday').spread.mean()
        g = g[pd.to_datetime(g.index).dayofweek < 5]
        z = np.log(g / g.rolling(20, min_periods=10).median().shift(1))
        z5m.append(pd.DataFrame({'pair': pair, 'z5m': z}))
    Z5 = pd.concat(z5m)
    D = D.reset_index().rename(columns={'index': 'day'}) if 'day' not in D.reset_index().columns else D.reset_index()
    D = D.merge(Z5.reset_index().rename(columns={'sday': 'day'}), on=['day', 'pair'], how='left').set_index('day')
    res: dict = {'label': 'EXPLORATORY (not pre-registered)', 'reason': __doc__.split('\n\n')[1].strip()}
    res['E1_z5_mean_spread'], s1 = fit_eval(D, ['z1', 'z2', 'z3', 'z4', 'z5m', 'z6'])
    res['E2_no_z5'], _ = fit_eval(D, ['z1', 'z2', 'z3', 'z4', 'z6'])
    te = D.index > t1.DISC_END
    res['E0_TVPC0_all_days'] = {'n_test': int(te.sum()), 'auc_test': float(roc_auc_score(D.reliable[te], 1 - D.z1[te])),
                                'auc_by_pair': {k: float(roc_auc_score(D.reliable[te & (D.pair == k)], 1 - D.z1[te & (D.pair == k)]))
                                                for k in t1.PAIRS}}
    # reliability base rates (what "reliable day" means per pair, holdout)
    res['reliable_rate_holdout_by_pair'] = D[te].groupby('pair').reliable.mean().round(3).to_dict()
    # downstream with E1 in place of the fitted TVPC
    Dd = D.copy()
    Dd['TVPC'] = s1
    dres: dict = {}
    t1.downstream(Dd, spots, dres)
    res['downstream_holdout_E1'] = dres['downstream_holdout']
    # E3: activity correlation (M3a) excluding hours within +-2 server days of a front-contract change. Worst M4 windows
    # all straddle a roll; the causal front rule follows a contract whose volume is collapsing (futures-side artefact).
    e3 = {}
    for pair in t1.PAIRS:
        _, _, H = t1.analyse(pair)
        fp = pd.read_csv(os.path.join(t1.DATA, f'{pair}_fut_profile.csv'), dtype={'server_day': str}).set_index('server_day')
        days = list(fp.index)
        chg = [i for i in range(1, len(days)) if fp.front.iloc[i] != fp.front.iloc[i - 1]]
        near = {days[j] for i in chg for j in range(max(0, i - 2), min(len(days), i + 3))}
        k = ~H.sday.isin(near)
        e3[pair] = {'roll_window_days': len(near),
                    'M3a_all': t1.corr_pack(H.lt_res, H.lf_res)['pearson'],
                    'M3a_ex_roll': t1.corr_pack(H.lt_res[k], H.lf_res[k])['pearson'],
                    'M3a_roll_only': t1.corr_pack(H.lt_res[~k], H.lf_res[~k])['pearson'],
                    'M3a_holdout_ex_roll': t1.corr_pack(H.lt_res[k & (H.date > t1.DISC_END)], H.lf_res[k & (H.date > t1.DISC_END)])['pearson']}
    res['E3_activity_ex_roll'] = e3
    with open(os.path.join(HERE, 't1_exploratory.json'), 'w') as fh:
        json.dump(res, fh, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    print(json.dumps({k: v for k, v in res.items() if k != 'reason'}, indent=1, default=str))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
