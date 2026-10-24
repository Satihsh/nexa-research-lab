"""C4 (human-approved 2026-10-03, option B): the 2 % daily loss is a pre-trade BUDGET, not only a halt trigger.

Before: DailyLossLimitBreached() only stopped NEW entries once equity was already >= 2 % below the day's start,
so a trade opened just above the line plus positions still open could take the day past 2 % (research
campaign: 12 of 732 traded days beyond -2 %, worst -2.29 %). Now ExecuteSignal() also requires, inside the
portfolio lock, E_now - OpenRisk(all open positions to their stops) - NewRisk >= 0.98 * DailyStartEquity.
The halt trigger stays as the second line. Fail-closed on any unreadable state.

Evidence: research/engfix/c4/regression_evidence.json (c4_regression.py).
"""
from __future__ import annotations

import difflib
import hashlib
import json
import os
import re

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PRE = os.path.join(ROOT, "build", "c4_pre_source")
EVIDENCE = os.path.join(os.path.dirname(__file__), "engfix", "c4", "regression_evidence.json")
MARK = "//==================== DAILY LOSS BUDGET (C4, pre-trade) ===================="
# The sources the C4 build and its evidence came from (later changes, e.g. S14, edit NEXA_EA.mq5 again).
C4_SRC = os.path.join(ROOT, "build", "c4_src")
C4_SNAP = {"NEXA_EA.mq5": "NEXA_EA_C4.mq5", "NEXA_Risk.mqh": "NEXA_Risk.mqh", "NEXA_Common.mqh": "NEXA_Common.mqh"}


def _read(path: str) -> str:
    if not os.path.isfile(path):
        pytest.skip(f"not present: {path}")
    with open(path, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def _sha(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _func(src: str, signature: str) -> str:
    i = src.index(signature)
    return src[i:src.index("\n  }\n", i)]


def test_budget_formula_and_fail_closed_paths():
    f = _func(_read(os.path.join(ROOT, "NEXA_Risk.mqh")), "bool DailyLossBudgetOK(")
    assert "double floorEq = startEq * (1.0 - InpMaxDailyLossPct / 100.0);" in f
    assert "if(eq - openRisk - newRisk < floorEq)" in f
    assert not re.search(r"\bcontinue\s*;", f), "an open position must never be skipped"
    for reason in ("DAILY_LOSS_BUDGET_INVALID_CONFIG", "DAILY_LOSS_BUDGET_NO_START_EQUITY",
                   "DAILY_LOSS_BUDGET_INVALID_EQUITY", "DAILY_LOSS_BUDGET_POSITION_UNREADABLE",
                   "DAILY_LOSS_BUDGET_POSITION_WITHOUT_STOP", "DAILY_LOSS_BUDGET_NEW_RISK_UNREADABLE"):
        assert f'reason = "{reason}"; return false;' in f, reason
    assert 'GlobalVariableGet(GV("DailyStartEquity"))' in f            # same start equity as the halt trigger
    assert "PositionGetDouble(POSITION_PRICE_CURRENT), sl, ok)" in f    # open risk measured from the current price
    g = _func(_read(os.path.join(ROOT, "NEXA_Risk.mqh")), "double NexaLossToStop(")
    assert "if(!OrderCalcProfit(otype, sym, lots, fromPrice, stopPrice, pnl) || !NexaFinite(pnl)) return 0;" in g
    assert "return (pnl < 0) ? -pnl : 0.0;" in g


def test_gate_sits_inside_the_lock_before_any_order():
    f = _func(_read(os.path.join(ROOT, "NEXA_EA.mq5")), "void ExecuteSignal(")
    call = ('if(!DailyLossBudgetOK(_Symbol, dir, entry, stopPrice, lots, dlReason)) '
            '{ ReleasePortfolioLock(); LogDecision(s, dir, "NO_TRADE_" + dlReason); return; }')
    assert f.count(call) == 1
    g = f.index(call)
    assert f.index("AcquirePortfolioLock()") < f.index("CorrelationCapOK(_Symbol, corrReason)") < g
    for later in ("PreflightExecutionCheck(", "ReserveTradeSlot()", "trade.Buy", "trade.Sell"):
        assert g < f.index(later), later


def test_change_is_an_append_and_the_trigger_is_untouched():
    pre_r, cur_r = _read(os.path.join(PRE, "NEXA_Risk.mqh")), _read(os.path.join(ROOT, "NEXA_Risk.mqh"))
    k = cur_r.index(MARK)
    assert pre_r == cur_r[:k] + pre_r[pre_r.rindex("#endif"):], "C4 must only append a section before #endif"
    for sig in ("bool DailyLossLimitBreached()", "void RollDailyStateIfNewDay()", "double CalcLotSizeHardened("):
        assert _func(pre_r, sig) == _func(cur_r, sig), sig
    assert re.findall(r"^input.*$", pre_r, re.MULTILINE) == re.findall(r"^input.*$", cur_r, re.MULTILINE)
    pre_e, cur_e = _read(os.path.join(PRE, "NEXA_EA.mq5")), _read(os.path.join(C4_SRC, "NEXA_EA_C4.mq5"))  # C4's own change
    diff = [ln for ln in difflib.ndiff(pre_e.splitlines(), cur_e.splitlines()) if ln[:2] in ("- ", "+ ")]
    assert not [ln for ln in diff if ln.startswith("- ")] and len(diff) == 2
    assert "DailyLossBudgetOK" in diff[1] and "dlReason" in diff[0]


def test_tester_regression_evidence():
    if not os.path.exists(EVIDENCE):
        pytest.skip("C4 regression evidence not present")
    with open(EVIDENCE) as fh:
        ev = json.load(fh)
    for name in ("NEXA_EA.mq5", "NEXA_Risk.mqh", "NEXA_Common.mqh"):              # pinned to the C4 sources
        assert ev["sources"][name] == _sha(os.path.join(C4_SRC, C4_SNAP[name])), f"evidence/source mismatch ({name})"
    assert ev["c4_ex5"] == _sha(os.path.join(ROOT, "build", "NEXA_EA_C4.ex5"))
    s = ev["summary"]
    assert s["runs"] == 12 and s["all_test_passed"]
    assert s["refusals_justified"] == s["budget_refusals"]           # every refusal is arithmetically justified
    assert s["fail_closed_rows"] == 0                                 # nothing unreadable in the tester
    assert s["first_divergence_always_a_budget_refusal"]              # behaviour changes only through the gate
    assert s["new_days_beyond_2pct"] <= s["base_days_beyond_2pct"]


def test_compiled_budget_harness_boundaries_and_fail_closed():
    import csv
    run = os.path.join(os.path.dirname(__file__), "tester_runs", "dailybudget_c4_20261003")
    if not os.path.exists(os.path.join(run, "mql5_results.csv")):
        pytest.skip("budget harness evidence not present")
    with open(os.path.join(run, "PROVENANCE.txt")) as fh:
        prov = dict(line.strip().split("=", 1) for line in fh if "=" in line)
    assert prov["nexa_risk_sha256"] == _sha(os.path.join(ROOT, "NEXA_Risk.mqh")), "stale evidence: rerun the harness"
    with open(os.path.join(run, "mql5_results.csv"), newline="") as fh:
        rows = {r["case"]: r for r in csv.DictReader(fh)}
    expected = {"no_start_equity", "fresh_day_no_positions", "direction_zero", "no_positions_floor_above",
                "no_positions_floor_below", "one_open_position_floor_above", "one_open_position_floor_below",
                "open_position_without_stop", "after_close_fresh_day"}
    assert set(rows) == expected
    assert all(r["expected"] == r["actual"] for r in rows.values()), rows
    assert rows["no_start_equity"]["reason"] == "DAILY_LOSS_BUDGET_NO_START_EQUITY"
    assert rows["direction_zero"]["reason"] == "DAILY_LOSS_BUDGET_NEW_RISK_UNREADABLE"
    assert rows["open_position_without_stop"]["reason"] == "DAILY_LOSS_BUDGET_POSITION_WITHOUT_STOP"
    assert float(rows["one_open_position_floor_above"]["open_risk"]) > 0          # the open position's risk counted
    assert rows["one_open_position_floor_above"]["reason"].startswith("DAILY_LOSS_BUDGET_eq")


def test_research_configuration_pairs_exercise_the_gate():
    p = os.path.join(os.path.dirname(__file__), "engfix", "c4", "capn_evidence.json")
    if not os.path.exists(p):
        pytest.skip("research-configuration pair evidence not present")
    with open(p) as fh:
        ev = json.load(fh)
    for name in ("NEXA_EA.mq5", "NEXA_Risk.mqh", "NEXA_Common.mqh"):              # pinned to the C4 sources
        assert ev["sources"][name] == _sha(os.path.join(C4_SRC, C4_SNAP[name])), f"evidence/source mismatch ({name})"
    s = ev["summary"]
    assert s["pairs"] == 6 and s["all_passed"]
    assert s["budget_refusals"] > 0 and s["refusals_justified"] == s["budget_refusals"]
    assert s["fail_closed_rows"] == 0 and s["first_divergence_always_a_budget_refusal"]
    assert s["new_days_beyond_2pct"] <= s["base_days_beyond_2pct"]
