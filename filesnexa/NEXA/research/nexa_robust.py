"""NEXA Gates 10/12 - selection-bias and robustness controls.

Every tool here exists to make it HARDER to promote a strategy:

  benjamini_hochberg    false-discovery control across every hypothesis tested
  probabilistic_sharpe  P(true Sharpe > benchmark) given sample length, skew, kurtosis
  deflated_sharpe       the same, with the benchmark raised to the expected maximum
                        Sharpe of `n_trials` unskilled strategies (Bailey & Lopez de Prado)
  pbo_cscv              probability of backtest overfitting via combinatorially
                        symmetric cross-validation (Bailey, Borwein, Lopez de Prado, Zhu)
  walk_forward_windows  chronological train/test windows with an embargo gap

Sharpe ratios here are PER OBSERVATION (per trade or per period); no annualisation
is applied, because trade spacing is irregular.
"""
from __future__ import annotations

import itertools
import math

import numpy as np
from scipy import stats

EULER_GAMMA = 0.5772156649015329


def benjamini_hochberg(pvalues, q: float = 0.10) -> np.ndarray:
    """Boolean mask of hypotheses rejected at FDR level q (step-up procedure)."""
    p = np.asarray(pvalues, dtype=float)
    if p.size == 0:
        return np.zeros(0, dtype=bool)
    if np.any((p < 0) | (p > 1) | ~np.isfinite(p)):
        raise ValueError("p-values must be finite and in [0, 1]")
    order = np.argsort(p)
    thresh = q * np.arange(1, p.size + 1) / p.size
    passed = p[order] <= thresh
    k = np.max(np.nonzero(passed)[0]) + 1 if passed.any() else 0
    mask = np.zeros(p.size, dtype=bool)
    mask[order[:k]] = True
    return mask


def expectancy_pvalue(r) -> float:
    """One-sided t-test p-value for mean(r) > 0. NaN when undefined."""
    a = np.asarray(r, dtype=float)
    if a.size < 3 or np.std(a, ddof=1) == 0:
        return float("nan")
    t = a.mean() / (a.std(ddof=1) / math.sqrt(a.size))
    return float(stats.t.sf(t, df=a.size - 1))


def sharpe(r) -> float:
    a = np.asarray(r, dtype=float)
    if a.size < 2:
        return float("nan")
    sd = a.std(ddof=1)
    return float(a.mean() / sd) if sd > 0 else float("nan")


def probabilistic_sharpe(r, sr_benchmark: float = 0.0) -> float:
    a = np.asarray(r, dtype=float)
    n = a.size
    sr = sharpe(a)
    if n < 3 or not np.isfinite(sr):
        return float("nan")
    g3 = float(stats.skew(a, bias=False))
    g4 = float(stats.kurtosis(a, fisher=False, bias=False))
    denom = 1.0 - g3 * sr + (g4 - 1.0) / 4.0 * sr * sr
    if denom <= 0:
        return float("nan")
    z = (sr - sr_benchmark) * math.sqrt(n - 1) / math.sqrt(denom)
    return float(stats.norm.cdf(z))


def expected_max_sharpe(n_trials: int, var_sr: float) -> float:
    """E[max SR] across n_trials independent zero-skill strategies with SR variance var_sr."""
    if n_trials <= 1 or var_sr <= 0:
        return 0.0
    z1 = stats.norm.ppf(1.0 - 1.0 / n_trials)
    z2 = stats.norm.ppf(1.0 - 1.0 / (n_trials * math.e))
    return math.sqrt(var_sr) * ((1.0 - EULER_GAMMA) * z1 + EULER_GAMMA * z2)


def deflated_sharpe(r, n_trials: int, var_sr_trials: float) -> float:
    """PSR against the expected max Sharpe of `n_trials` unskilled tries.

    `var_sr_trials` is the variance of the Sharpe ratios of ALL configurations
    tried (not just the winner). An honest trial count is the whole point:
    under-reporting it inflates this number.
    """
    return probabilistic_sharpe(r, expected_max_sharpe(n_trials, var_sr_trials))


def pbo_cscv(perf: np.ndarray, n_splits: int = 16, metric=None) -> dict:
    """Probability of backtest overfitting.

    perf: T x N matrix, row t = period t, column j = configuration j's return.
    The rows are cut into `n_splits` contiguous blocks; for every half/half
    combination, pick the in-sample best configuration and record its OOS rank.
    PBO = fraction of combinations where that pick lands below the OOS median.
    """
    m = np.asarray(perf, dtype=float)
    if m.ndim != 2 or m.shape[1] < 2:
        raise ValueError("perf must be T x N with N >= 2 configurations")
    if n_splits % 2 or n_splits < 2:
        raise ValueError("n_splits must be even")
    if m.shape[0] < n_splits:
        raise ValueError("need at least one row per split")
    metric = metric or (lambda x: np.nanmean(x, axis=0) / (np.nanstd(x, axis=0, ddof=1) + 1e-12))
    blocks = np.array_split(np.arange(m.shape[0]), n_splits)
    logits = []
    for combo in itertools.combinations(range(n_splits), n_splits // 2):
        is_idx = np.concatenate([blocks[i] for i in combo])
        oos_idx = np.concatenate([blocks[i] for i in range(n_splits) if i not in combo])
        best = int(np.nanargmax(metric(m[is_idx])))
        oos = metric(m[oos_idx])
        rank = (np.sum(oos < oos[best]) + 0.5 * (np.sum(oos == oos[best]) - 1)) + 1
        w = rank / (m.shape[1] + 1)
        logits.append(math.log(w / (1.0 - w)))
    lg = np.array(logits)
    return {"pbo": float(np.mean(lg <= 0)), "n_combinations": int(lg.size),
            "median_logit": float(np.median(lg)), "n_configs": int(m.shape[1])}


def walk_forward_windows(n: int, train: int, test: int, embargo: int = 0,
                         step: int | None = None, anchored: bool = False) -> list:
    """Index windows [(train_idx, test_idx), ...] in time order.

    Test windows never overlap each other; `embargo` rows between train end and
    test start are dropped so labels spanning the boundary cannot leak.
    """
    if min(train, test) <= 0 or embargo < 0:
        raise ValueError("train/test must be positive, embargo >= 0")
    step = step or test
    out = []
    start = 0
    while True:
        tr_lo = 0 if anchored else start
        tr_hi = start + train
        te_lo = tr_hi + embargo
        te_hi = te_lo + test
        if te_hi > n:
            break
        out.append((np.arange(tr_lo, tr_hi), np.arange(te_lo, te_hi)))
        start += step
    return out
