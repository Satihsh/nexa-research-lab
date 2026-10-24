"""Capital-velocity mathematics and simulator (research only). No market data."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

import nexa_8e_capital as CV
import nexa_8e_costs as C
import nexa_8e_feasibility as F

SPEC = C.SymbolSpec("XAUUSD", 0.01, 0.01, 1.0, 100.0, 0.01, 50.0, 0.01, 0, 0, 0.04, 17, "FOREX")


def test_ideal_compounding_path_exact():
    p = F.compounding_path()
    assert p[0]["target_equity"] == pytest.approx(249.0) and p[1]["target_equity"] == pytest.approx(310.005)
    assert p[-1]["target_equity"] == pytest.approx(200 * 1.245 ** 20) == pytest.approx(16010.95, abs=0.01)


def test_winners_needed_and_r_floor():
    assert F.winners_needed(2) == 12 and F.winners_needed(3) == 8 and F.winners_needed(24.5) == 1
    assert F.winners_needed(1, cost_r=1.0) == math.inf
    assert F.r_needed_all_win(10) == pytest.approx(2.2156, abs=1e-4)
    assert F.equity_after(10, 0, 2) - 1 < 0.245 < F.equity_after(10, 0, 2.3) - 1


def test_dp_probabilities_sum_to_one_and_match_monte_carlo():
    for p, r, c in [(0.5, 3, 0.15), (0.3, 10, 0.0), (0.7, 4, 0.1)]:
        d = F.day_distribution(p, r, cost_r=c)
        assert d.p_target + d.p_halt + d.p_cap == pytest.approx(1.0, abs=1e-12)
        rng = np.random.default_rng(1)
        hits = 0
        for _ in range(20000):
            eq, n = 1.0, 0
            while n < 10:
                eq *= (1 + 0.01 * (r - c)) if rng.random() < p else (1 - 0.01 * (1 + c))
                n += 1
                if eq >= 1.245 - 1e-12 or eq <= 0.98 + 1e-12:
                    break
            hits += eq >= 1.245 - 1e-12
        assert hits / 20000 == pytest.approx(d.p_target, abs=0.012)


def test_unreachable_when_ten_winners_are_not_enough():
    assert F.day_distribution(0.99, 2.0).p_target == 0.0


def test_zero_edge_bound_holds_for_every_tabled_scenario():
    bound = F.zero_edge_target_bound()
    assert bound == pytest.approx(0.1084, abs=1e-4)
    for r in (2, 3, 4, 5, 10, 24.5, 40):
        p = 1 / (1 + r)                                    # zero edge before costs
        d = F.day_distribution(p, r)
        assert d.p_target <= bound + 1e-12
        assert d.exp_return == pytest.approx(0.0, abs=1e-12)


def test_required_edge_inequality():
    assert F.min_expected_daily_return(0.5) == pytest.approx(0.5 * 0.245 - 0.5 * (1 - 0.9702), abs=1e-12)
    for p, r in [(0.6, 5), (0.7, 4)]:
        d = F.day_distribution(p, r)
        assert d.exp_return >= F.min_expected_daily_return(d.p_target) - 1e-12


def test_single_trade_requirements_on_real_xau_spec():
    s = F.single_trade_requirements(200, 0.01, 5.0, 100.0, 0.01, 0.01, 0.25)
    assert not s["tradable"] and s["lots"] == 0.0                 # $5 stop at min lot risks > $2
    s = F.single_trade_requirements(200, 0.01, 1.5, 100.0, 0.01, 0.01, 0.25)
    assert s["tradable"] and s["required_r"] > 24 and s["p_driftless"] < 0.05


def _tr(day, rets, risk=1.0, cost=0.1):
    t0 = pd.Timestamp(day)
    return pd.DataFrame({"entry_time": [t0 + pd.Timedelta(hours=i) for i in range(len(rets))],
                         "risk": risk, "r_net": rets, "cost_r": cost})


def test_simulator_locks_after_target_and_halts_at_daily_loss():
    t = pd.concat([_tr("2024-03-04 10:00", [30.0, 5.0]),            # first trade exceeds target -> lock
                   _tr("2024-03-05 10:00", [-1.1, -1.1, -1.1, 5.0])])
    d = CV.simulate(t, SPEC, start_equity=1000.0)
    # round-down sizing makes each loss slightly < 1 %: 2 losses = -1.9 % (no halt), the 3rd crosses -2 %
    assert list(d["status"]) == ["TARGET_HIT", "DAILY_LOSS_HALT"] and list(d["trades"]) == [1, 3]
    assert d["ending_equity"].iloc[0] >= 1000 * 1.245
    day2 = d.iloc[1]
    assert day2["net_return"] <= -0.02 and day2["net_return"] > -0.03          # the 5R trade after the halt is never taken


def test_simulator_never_rounds_up_and_respects_trade_cap():
    d = CV.simulate(_tr("2024-03-04 10:00", [1.0] * 3, risk=5.0), SPEC, start_equity=200.0)
    assert d["trades"].iloc[0] == 0 and d["skipped_below_min_lot"].iloc[0] == 3
    d = CV.simulate(_tr("2024-03-04 00:00", [0.1] * 15, risk=1.0, cost=0.0), SPEC, start_equity=10000.0)
    assert d["trades"].iloc[0] == 10


def test_bootstrap_all_targets():
    assert CV.p_all_targets_bootstrap(np.array([0.3] * 10)) == 1.0
    assert CV.p_all_targets_bootstrap(np.array([0.0] * 10)) == 0.0
    p = CV.p_all_targets_bootstrap(np.array([0.3, 0.0]), horizon=2, draws=40000)
    assert p == pytest.approx(0.25, abs=0.01)
