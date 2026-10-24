"""Known-answer tests for nexa_stats. Vectors are hand-built to check the maths;
they are not market data and say nothing about NEXA's performance."""
from __future__ import annotations

import math

import numpy as np
import pytest

from nexa_stats import (
    StatsConfig,
    Verdict,
    bootstrap_ci,
    cost_shock,
    cost_shock_price,
    evaluate,
    max_drawdown_r,
    monte_carlo,
    segment_metrics,
    trade_metrics,
)

FAST = StatsConfig(n_boot=800, n_mc=400)


def test_metrics_known_values():
    r = [2.0, -1.0, -1.0, 2.0, -1.0]
    m = trade_metrics(r)
    assert m["n"] == 5
    assert m["win_rate"] == pytest.approx(0.4)
    assert m["expectancy_r"] == pytest.approx(0.2)
    assert m["profit_factor"] == pytest.approx(4.0 / 3.0)
    assert m["payoff_ratio"] == pytest.approx(2.0)
    assert m["max_consecutive_losses"] == 2
    assert m["worst_r"] == -1.0


def test_max_drawdown_includes_initial_peak_of_zero():
    assert max_drawdown_r([-1, -1, 3, -2]) == pytest.approx(2.0)
    assert max_drawdown_r([1, 1, 1]) == 0.0
    assert max_drawdown_r([]) == 0.0


def test_profit_factor_edge_cases():
    assert math.isinf(trade_metrics([1.0, 2.0])["profit_factor"])
    assert trade_metrics([-1.0, -2.0])["profit_factor"] == 0.0


def test_nan_is_rejected_not_imputed():
    with pytest.raises(ValueError):
        trade_metrics([1.0, float("nan")])


def test_bootstrap_is_deterministic_and_brackets_mean():
    r = np.tile([1.5, -1.0], 40)
    a, b = bootstrap_ci(r, cfg=FAST), bootstrap_ci(r, cfg=FAST)
    assert a == b
    assert a["lo"] <= a["point"] <= a["hi"]
    assert a["point"] == pytest.approx(0.25)


def test_block_bootstrap_runs_and_brackets():
    r = np.tile([1.5, -1.0, -1.0, 2.0], 20)
    ci = bootstrap_ci(r, cfg=StatsConfig(n_boot=500, block=5))
    assert ci["lo"] <= ci["point"] <= ci["hi"]


def test_cost_shock_r_and_price():
    np.testing.assert_allclose(cost_shock([1.0, -1.0], 0.1), [0.9, -1.1])
    np.testing.assert_allclose(cost_shock_price([1.0, -1.0], [0.0020, 0.0010], 0.0002), [0.9, -1.2])
    with pytest.raises(ValueError):
        cost_shock_price([1.0], [0.0], 0.1)


def test_insufficient_sample_verdict():
    assert evaluate([1.0] * 10, FAST).verdict is Verdict.INSUFFICIENT_SAMPLE


def test_coin_flip_is_not_an_edge():
    r = np.tile([1.0, -1.0], 50)          # expectancy exactly zero
    assert evaluate(r, FAST).verdict is Verdict.EDGE_NOT_DEMONSTRATED


def test_negative_expectancy_detected():
    r = np.tile([1.0, -1.0, -1.0], 40)
    assert evaluate(r, FAST).verdict is Verdict.NEGATIVE_EXPECTANCY


def test_thin_edge_fails_cost_shock():
    r = np.tile([0.14, -0.06], 400)       # +0.04R/trade, CI excludes 0, dies at 0.05R shock
    rep = evaluate(r, FAST)
    assert rep.verdict is Verdict.EDGE_NOT_DEMONSTRATED
    assert any("cost shock" in x for x in rep.reasons)


def test_robust_edge_supported_but_labelled_in_sample():
    r = np.tile([2.0, -1.0], 100)         # +0.5R/trade
    rep = evaluate(r, FAST)
    assert rep.verdict is Verdict.EDGE_SUPPORTED_IN_SAMPLE
    assert "OOS" in rep.reasons[-1]


def test_monte_carlo_ruin_probability_bounds():
    losing = monte_carlo(np.tile([1.0, -1.0, -1.0], 50), StatsConfig(n_mc=300, risk_per_trade=0.01))
    winning = monte_carlo(np.tile([3.0, -1.0], 50), StatsConfig(n_mc=300, risk_per_trade=0.003))
    assert losing["p_hit_max_drawdown"] > winning["p_hit_max_drawdown"]
    assert 0.0 <= winning["p_hit_max_drawdown"] <= 1.0
    assert losing["max_dd_r"]["p5"] <= losing["max_dd_r"]["p95"]


def test_segment_metrics():
    seg = segment_metrics([1.0, -1.0, 2.0], ["LONDON", "ASIA", "LONDON"])
    assert seg["LONDON"]["n"] == 2 and seg["LONDON"]["expectancy_r"] == pytest.approx(1.5)
    with pytest.raises(ValueError):
        segment_metrics([1.0], ["A", "B"])
