"""Tests for the CAP-NEUTRAL RESEARCH A4 analysis (synthetic data only; no campaign file is read)."""
from __future__ import annotations

import math
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capn_analysis as A

import nexa_8e_costs as C

HEADER = ["event", "decision_ts", "fill_ts", "direction", "entry_intended", "entry_actual", "sl_price", "tp_price",
          "target_r", "risk_dist", "lots", "spread", "commission", "swap", "result_r", "reason"]


def row(event, **kw):
    base = {"decision_ts": "2025.01.06 10:00:00", "fill_ts": "2025.01.06 10:01:00", "direction": "1",
            "entry_intended": "1.10000", "entry_actual": "1.10010", "sl_price": "1.09900", "tp_price": "1.10400",
            "target_r": "4.0", "risk_dist": "0.00100", "lots": "1.00", "spread": "0.00001", "commission": "0.00",
            "swap": "0.00", "result_r": "0.0000", "reason": ""}
    base.update({k: str(v) for k, v in kw.items()})
    base["event"] = event
    return base


def one_trade(exit_px="1.10200", comm="-7.00", gross="2.0", lots="1.00", **open_kw):
    close_kw = {**open_kw, "entry_actual": exit_px, "lots": lots, "commission": comm, "result_r": gross,
                "fill_ts": "2025.01.06 12:00:00"}
    return [row("OPEN", lots=lots, **open_kw), row("FILL", lots=lots, commission="-3.50", **open_kw),
            row("CLOSE", **close_kw)]


# ---------------------------------------------------------------- arithmetic
def test_ceiling_derivation_matches_plan_amendment():
    assert A.daily_ceiling(0.003, 4.0, 10) == pytest.approx(0.126692, abs=1e-6)
    assert A.daily_ceiling(0.003, 2.75, 10) == pytest.approx(0.085631, abs=1e-6)
    assert A.daily_ceiling(0.01, 4.0, 10) == pytest.approx(0.480244, abs=1e-6)
    assert A.wins_needed(0.245, 0.003, 4.0) == pytest.approx(18.37, abs=0.01)
    assert A.wins_needed(0.245, 0.003, 4.0) > 10        # unreachable under the 10-trade cap


def test_contract_value():
    assert A.contract_value("EURUSD", 1.1) == 100_000
    assert A.contract_value("XAUUSD", 4000) == 100
    assert A.contract_value("USDJPY", 150.0) == pytest.approx(100_000 / 150.0)
    with pytest.raises(ValueError):
        A.contract_value("NAS100", 1.0)


def test_clopper_pearson_zero_successes():
    n = 1000
    assert A.clopper_pearson_upper(0, n) == pytest.approx(1 - 0.05 ** (1 / n), rel=1e-6)
    assert math.isnan(A.clopper_pearson_upper(0, 0))


# ---------------------------------------------------------------- trade pairing / net R
def test_net_r_uses_actual_fill_close_commission_and_swap():
    t = A.pair_trades(one_trade(), "EURUSD", "A2025Q1").iloc[0]
    assert t.price_pnl_usd == pytest.approx((1.10200 - 1.10010) * 100_000)        # 190
    assert t.realised_pnl_usd == pytest.approx(183.0)                              # FILL commission NOT added
    assert t.initial_risk_usd == pytest.approx(100.0)
    assert t.net_r == pytest.approx(1.83)
    assert t.entry_slip_r == pytest.approx(-0.1)                                    # filled 1 pip worse
    assert t.price_r_from_fill == pytest.approx(t.gross_r + t.entry_slip_r)         # 1.9 = 2.0 - 0.1
    assert t.commission_r == pytest.approx(-0.07)


def test_usdjpy_pnl_converted_at_exit_and_risk_at_intended_entry():
    kw = {"entry_intended": "150.000", "entry_actual": "150.000", "sl_price": "149.900", "tp_price": "150.400",
          "risk_dist": "0.100"}
    t = A.pair_trades(one_trade(exit_px="150.200", comm="0.00", **kw), "USDJPY", "B").iloc[0]
    assert t.price_pnl_usd == pytest.approx(0.2 * 100_000 / 150.2)
    assert t.initial_risk_usd == pytest.approx(0.1 * 100_000 / 150.0)


def test_partial_close_legs_are_summed():
    rows = [row("OPEN"), row("FILL"),
            row("PARTIAL_CLOSE", entry_actual="1.10160", lots="0.50"),
            row("CLOSE", entry_actual="1.10010", lots="0.50", commission="-7.00")]
    t = A.pair_trades(rows, "EURUSD", "A2025Q1").iloc[0]
    assert t.legs == 2
    assert t.price_pnl_usd == pytest.approx((1.10160 - 1.10010) * 0.5 * 100_000)


def test_overlapping_positions_pair_by_volume_and_direction():
    # observed pattern: a new order is dispatched before the previous position's CLOSE row
    rows = [row("OPEN", lots="0.99"), row("FILL", lots="0.99", entry_actual="1.10010"),
            row("OPEN", lots="3.88"),
            row("CLOSE", lots="0.99", entry_actual="1.09980"),
            row("FILL", lots="3.88", entry_actual="1.10020"),
            row("CLOSE", lots="3.88", entry_actual="1.10120")]
    t = A.pair_trades(rows, "EURUSD", "A2025Q2")
    assert list(t.lots) == [0.99, 3.88]
    assert t.price_pnl_usd.tolist() == pytest.approx([(1.09980 - 1.10010) * 0.99 * 1e5, (1.10120 - 1.10020) * 3.88 * 1e5])
    assert t.attrs["overlapping_opens"] == 1


@pytest.mark.parametrize("rows,msg", [
    ([row("OPEN"), row("FILL"), row("OPEN"), row("FILL"), row("CLOSE")], "ambiguous"),
    ([row("CLOSE")], "without OPEN"),
    ([row("OPEN"), row("FILL")], "left open"),
    ([row("OPEN", lots="1.00"), row("FILL", lots="0.50")], "FILL without a matching OPEN"),
    ([row("OPEN"), row("FILL"), row("CLOSE", lots="2.00")], "without OPEN"),
    ([row("OPEN"), row("FILL"), row("MODIFY")], "unknown event"),
])
def test_pairing_refuses_to_guess(rows, msg):
    with pytest.raises(ValueError, match=msg):
        A.pair_trades(rows, "EURUSD", "A2025Q1")


@pytest.mark.parametrize("exit_px,expected", [
    (1.10400, "TP"), (1.10450, "TP"), (1.09900, "SL"), (1.09880, "SL"), (1.10010, "BREAKEVEN"), (1.10150, "OTHER"),
])
def test_exit_classification_long(exit_px, expected):
    assert A.classify_exit(1, 1.10010, exit_px, 1.09900, 1.10400, 0.00100) == expected


def test_exit_classification_short():
    assert A.classify_exit(-1, 1.1000, 1.0960, 1.1010, 1.0960, 0.0010) == "TP"
    assert A.classify_exit(-1, 1.1000, 1.1012, 1.1010, 1.0960, 0.0010) == "SL"


# ---------------------------------------------------------------- deals / files
def test_rebuild_balance_from_deals():
    deals = {1: ("buy", 1.0, 1.10010), 2: ("sell", 0.5, 1.10160), 3: ("sell", 0.5, 1.10010)}
    bal, left = A.rebuild_balance("EURUSD", deals, close_costs=-7.0)
    assert left == 0
    assert bal == pytest.approx(50_000 + 75.0 - 7.0)


def test_read_events_counts_cap_blocks(tmp_path):
    p = tmp_path / "dna.csv"
    dec = ["DECISION"] + [""] * (len(HEADER) - 2)
    lines = [",".join(HEADER),
             ",".join(dec + ["NO_TRADE_PORTFOLIO_CURRENCY_EXPOSURE_CAP"]),
             ",".join(dec + ["NO_QUALIFIED_LIQUIDITY_EVENT_state0"]),
             ",".join(row("OPEN")[h] for h in HEADER)]
    p.write_text("\n".join(lines) + "\n")
    rows, n_dec, n_cap = A.read_events(str(p))
    assert (n_dec, n_cap, len(rows), rows[0]["event"]) == (2, 1, 1, "OPEN")


# ---------------------------------------------------------------- daily / cycles
def _trades(days_pnl):
    return pd.DataFrame({"entry_time": [pd.Timestamp(d) + pd.Timedelta(hours=9) for d, _ in days_pnl],
                         "exit_time": [pd.Timestamp(d) + pd.Timedelta(hours=10) for d, _ in days_pnl],
                         "realised_pnl_usd": [p for _, p in days_pnl]})


def test_daily_returns_compound_and_include_flat_days():
    days = pd.bdate_range("2025-01-06", periods=5)
    d = A.daily_returns(_trades([("2025-01-06", 500.0), ("2025-01-08", -1010.0)]), days)
    assert len(d) == 5 and (d.ret == 0).sum() == 3
    assert d.ret.iloc[0] == pytest.approx(0.01)
    assert d.ret.iloc[2] == pytest.approx(-1010.0 / 50_500.0)
    assert d.drawdown.max() == pytest.approx(1010.0 / 50_500.0)


def test_daily_returns_empty_chunk():
    d = A.daily_returns(pd.DataFrame(columns=["entry_time", "exit_time", "realised_pnl_usd"]),
                        pd.bdate_range("2025-01-06", periods=3))
    assert len(d) == 3 and (d.ret == 0).all()


def test_cycles_use_full_blocks_only():
    d = pd.DataFrame({"day": pd.bdate_range("2025-01-06", periods=45), "ret": [0.01] * 45})
    c = A.cycles(d, 20)
    assert len(c) == 2
    assert c["return"].iloc[0] == pytest.approx(1.01 ** 20 - 1)


# ---------------------------------------------------------------- $200 replay
SPEC = C.SymbolSpec("EURUSD", 0.00001, 0.00001, 1.0, 100000.0, 0.01, 50.0, 0.01, 0, 0, 0.035, 10, "FOREX")


def _replay_trades(net_rs, risk_per_lot, day="2025-01-06", same_day=True):
    n = len(net_rs)
    t0 = pd.Timestamp(day)
    times = [t0 + pd.Timedelta(minutes=i) if same_day else t0 + pd.Timedelta(days=i) for i in range(n)]
    return pd.DataFrame({"entry_time": times, "net_r": net_rs, "lots": [1.0] * n,
                         "initial_risk_usd": [risk_per_lot] * n})


def test_replay_min_lot_executed_only_within_hard_ceiling():
    # risk per 0.01 lot = $1.50 -> 0.75 % of $200 (<= 1 %): minimum lot executed
    r = A.nexa_rule_replay(_replay_trades([1.0], 150.0), SPEC, start=200.0)
    assert r["trades_taken"] == 1 and r["end"] == pytest.approx(201.5)
    # risk per 0.01 lot = $2.50 -> 1.25 % of $200 (> 1 %): NO TRADE
    r = A.nexa_rule_replay(_replay_trades([1.0], 250.0), SPEC, start=200.0)
    assert r["trades_taken"] == 0 and r["skipped_min_lot_exceeds_ceiling"] == 1


def test_replay_daily_loss_halt_and_trade_cap():
    # each loss is -1R at the minimum lot ($1.50 = 0.75 %): third entry happens at -1.5 %, fourth is halted
    r = A.nexa_rule_replay(_replay_trades([-1.0] * 5, 150.0), SPEC, start=200.0)
    assert r["trades_taken"] == 3 and r["skipped_daily_halt_or_cap"] == 2
    r = A.nexa_rule_replay(_replay_trades([0.0] * 12, 150.0), SPEC, start=200.0)
    assert r["trades_taken"] == 10 and r["skipped_daily_halt_or_cap"] == 2


def test_replay_fractional_is_theoretical_and_never_skips():
    r = A.nexa_rule_replay(_replay_trades([1.0], 250.0), SPEC, start=200.0, fractional=True)
    assert r["trades_taken"] == 1 and r["end"] == pytest.approx(200.0 * 1.003)


def test_replay_drawdown_stop():
    # fractional: -1R costs 0.3 % (x0.5 past 5 % drawdown, x0.25 past 7.5 %); one loss per day so the
    # daily halt never binds. 60 losses only reach ~9.5 % (throttle); 200 reach the 10 % stop.
    r60 = A.nexa_rule_replay(_replay_trades([-1.0] * 60, 1.0, same_day=False), SPEC, start=200.0, fractional=True)
    assert r60["skipped_drawdown_stop"] == 0 and 0.90 < r60["end"] / 200.0 < 0.95
    r = A.nexa_rule_replay(_replay_trades([-1.0] * 200, 1.0, same_day=False), SPEC, start=200.0, fractional=True)
    assert r["skipped_drawdown_stop"] > 0
    assert r["end"] / 200.0 == pytest.approx(0.90, abs=0.001)   # stops at the 10 % drawdown limit


# ---------------------------------------------------------------- defect evidence
def test_excursion_and_time_exit_territory():
    idx = pd.date_range("2025-01-06 10:00", periods=60, freq="1min")
    high = np.full(60, 1.10020)
    high[5] = 1.10120                       # +1.1R touched at bar 5
    bars = pd.DataFrame({"high": high, "low": np.full(60, 1.10000), "close": np.full(60, 1.10015)}, index=idx)
    tr = pd.Series({"entry_time": idx[0], "exit_time": idx[-1], "fill": 1.10010, "sl": 1.09910, "direction": 1})
    ex = A.excursion(tr, bars)
    assert ex["be_bar"] == 5 and ex["bars_held"] == 60
    assert ex["mfe_r"] == pytest.approx(1.1)
    assert ex["r_at_48"] == pytest.approx(0.05)
    T = pd.DataFrame([{**ex, "exit_type": "BREAKEVEN", "legs": 1, "price_r_from_fill": 0.0}])
    d = A.defect_impact(T)
    assert d["reached_breakeven_1R"] == 1 and d["reached_1_5R"] == 0
    assert d["time_exit_blocked_after_breakeven"] == 1


def test_defect_bound_signs():
    T = pd.DataFrame([
        {"mfe_r": 1.6, "be_bar": 3, "bars_held": 10, "r_at_48": np.nan, "exit_type": "BREAKEVEN", "legs": 1, "price_r_from_fill": 0.0},
        {"mfe_r": 4.0, "be_bar": 3, "bars_held": 30, "r_at_48": np.nan, "exit_type": "TP", "legs": 1, "price_r_from_fill": 4.0},
    ])
    b = A.defect_impact(T)["inference_partial_half_bound_r"]
    assert b["gain_r_on_be_or_other_exits"] == pytest.approx(0.75)
    assert b["loss_r_on_tp_exits"] == pytest.approx(-1.25)


def test_symbol_specs_cover_all_four_symbols():
    specs, source = A.load_symbol_specs()
    for s in A.SYMBOLS:
        assert specs[s].vmin == 0.01 and specs[s].vstep == 0.01
    assert source["USDJPY"].startswith("contracts.json")
