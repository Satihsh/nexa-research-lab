"""Pepperstone cost / sizing engine against the probed broker specification (no market data)."""
from __future__ import annotations

import pytest

import nexa_8e_costs as C


@pytest.fixture(scope="module")
def specs():
    return C.load_specs()


def test_probe_specs_are_the_broker_values(specs):
    x, n = specs["XAUUSD"], specs["NAS100"]
    assert (x.contract_size, x.tick_size, x.tick_value, x.vmin, x.vstep) == (100.0, 0.01, 1.0, 0.01, 0.01)
    assert x.value_per_price_per_lot == pytest.approx(100.0) and x.commission_per_side_minlot == pytest.approx(0.04)
    assert (n.contract_size, n.tick_size, n.tick_value, n.vmin, n.vstep) == (1.0, 0.1, 0.1, 0.1, 0.1)
    assert n.value_per_price_per_lot == pytest.approx(1.0) and n.commission_per_side_minlot == 0.0
    assert x.vmin != n.vmin                         # never assume identical volume specs
    assert "US100" not in specs and "USTEC" not in specs


@pytest.mark.parametrize("raw,step,exp", [(0.0188, 0.01, 0.01), (0.0099, 0.01, 0.0), (0.29, 0.1, 0.2),
                                          (0.3, 0.1, 0.3), (-1, 0.01, 0.0), (float("nan"), 0.01, 0.0)])
def test_round_down_never_up(raw, step, exp):
    assert C.round_down_to_step(raw, step) == pytest.approx(exp)


def test_sizing_never_exceeds_risk_and_rejects_below_min_lot(specs):
    x = specs["XAUUSD"]
    costs = C.CostInputs(spread_price=0.12, slippage_price=0.06)
    s = C.size_trade(x, 200, 0.01, 5.0, costs)
    assert not s["tradable"] and s["equity_needed_for_min_lot"] == pytest.approx(532.0)
    for eq in (600, 1000, 5000, 12345.67):
        s = C.size_trade(x, eq, 0.01, 5.0, costs)
        assert s["tradable"] and s["loss_at_stop_cash"] <= eq * 0.01 + 1e-9
    n = specs["NAS100"]
    s = C.size_trade(n, 200, 0.01, 19.0, C.CostInputs(spread_price=1.0))
    assert s["tradable"] and s["lots"] == pytest.approx(0.1) and s["loss_at_stop_cash"] <= 2.0 + 1e-9


def test_cost_and_net_outcome_arithmetic(specs):
    x = specs["XAUUSD"]
    c = C.CostInputs(spread_price=0.12, slippage_price=0.06)
    o = C.net_outcome(x, 0.01, 5.0, 3, c, 1000.0)
    assert o["spread_cost"] == pytest.approx(0.12) and o["slippage_cost"] == pytest.approx(0.12)
    assert o["commission_cost"] == pytest.approx(0.08) and o["total_cost"] == pytest.approx(0.32)
    assert o["gross_win"] == pytest.approx(15.0) and o["net_win"] == pytest.approx(14.68)
    assert o["net_R_win"] == pytest.approx(2.936) and o["net_R_loss"] == pytest.approx(-1.064)
    stressed = C.net_outcome(x, 0.01, 5.0, 3, C.CostInputs(0.36, 0.18), 1000.0)
    assert stressed["total_cost"] == pytest.approx(0.36 + 0.36 + 0.08)          # 3x spread + 3x slippage


def test_breakeven_and_edge_score():
    assert C.breakeven_win_rate(2, 0.0) == pytest.approx(1 / 3)
    assert C.breakeven_win_rate(3, 0.2) == pytest.approx(0.3)
    assert C.expected_net_r(0.3, 3, 0.2) == pytest.approx(0.3 * 2.8 - 0.7 * 1.2)
    assert C.net_edge_score(2.0, 0.5) == 4.0 and C.net_edge_score(1.0, 0.0) != C.net_edge_score(1.0, 0.0)
