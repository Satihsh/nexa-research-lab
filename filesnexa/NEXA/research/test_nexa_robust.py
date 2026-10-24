"""Known-answer and property tests for nexa_robust. Inputs are constructed to
exercise the maths; they are not market data."""
from __future__ import annotations

import numpy as np
import pytest

from nexa_robust import (
    benjamini_hochberg,
    deflated_sharpe,
    expectancy_pvalue,
    expected_max_sharpe,
    pbo_cscv,
    probabilistic_sharpe,
    walk_forward_windows,
)


def test_bh_textbook_example():
    # Benjamini & Hochberg (1995) style: 3 of these survive at q=0.05
    p = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216]
    mask = benjamini_hochberg(p, q=0.05)
    assert mask.tolist() == [True, True] + [False] * 8


def test_bh_step_up_rescues_earlier_ranks():
    mask = benjamini_hochberg([0.04, 0.04, 0.04], q=0.05)   # 0.04 <= 0.05*3/3
    assert mask.all()


def test_bh_rejects_bad_input_and_handles_empty():
    assert benjamini_hochberg([]).size == 0
    with pytest.raises(ValueError):
        benjamini_hochberg([0.1, 1.5])


def test_expectancy_pvalue_direction():
    rng = np.random.default_rng(1)
    good = rng.normal(0.5, 1.0, 200)
    bad = rng.normal(-0.5, 1.0, 200)
    assert expectancy_pvalue(good) < 0.01
    assert expectancy_pvalue(bad) > 0.99
    assert np.isnan(expectancy_pvalue([1.0, 1.0, 1.0]))


def test_psr_monotone_in_sample_size():
    rng = np.random.default_rng(2)
    base = rng.normal(0.1, 1.0, 2000)
    assert probabilistic_sharpe(base[:100]) < probabilistic_sharpe(base)


def test_expected_max_sharpe_grows_with_trials():
    assert expected_max_sharpe(1, 0.01) == 0.0
    assert 0 < expected_max_sharpe(10, 0.01) < expected_max_sharpe(1000, 0.01)


def test_deflated_below_undeflated():
    rng = np.random.default_rng(3)
    r = rng.normal(0.08, 1.0, 500)
    assert deflated_sharpe(r, n_trials=200, var_sr_trials=0.005) < probabilistic_sharpe(r)


def test_pbo_is_calibrated_on_pure_noise():
    """One noise matrix can give any PBO (CSCV combos are dependent), so check the
    average over many independent matrices: it must sit near 0.5."""
    v = [pbo_cscv(np.random.default_rng(s).normal(0, 1, (240, 20)), n_splits=8)["pbo"]
         for s in range(30)]
    assert 0.38 < float(np.mean(v)) < 0.62


def test_pbo_low_when_one_config_is_genuinely_better():
    rng = np.random.default_rng(5)
    m = rng.normal(0, 1, (480, 30))
    m[:, 7] += 0.6
    assert pbo_cscv(m, n_splits=10)["pbo"] < 0.1


def test_pbo_input_validation():
    with pytest.raises(ValueError):
        pbo_cscv(np.zeros((20, 1)))
    with pytest.raises(ValueError):
        pbo_cscv(np.zeros((20, 3)), n_splits=5)


def test_walk_forward_windows_ordered_embargoed_non_overlapping():
    w = walk_forward_windows(100, train=40, test=10, embargo=5)
    assert len(w) == 5
    for tr, te in w:
        assert tr.max() + 5 < te.min()
    tests = np.concatenate([te for _, te in w])
    assert len(tests) == len(set(tests.tolist()))
    anchored = walk_forward_windows(100, train=40, test=10, anchored=True)
    assert all(tr.min() == 0 for tr, _ in anchored)
    with pytest.raises(ValueError):
        walk_forward_windows(10, 0, 5)
