"""Stale-bar guard (2026-10-03, approved option C): static checks of the MQL5 source, plus the
Strategy Tester regression evidence, pinned to the source hash it was produced from.

The EA evaluates a closed bar at the first tick of the next bar. After a weekend or holiday closure
that tick is the reopening, so Friday's last bar was evaluated (and could have been traded) at
Monday's price. In 96 tester runs this happened 588-589 times and never opened a trade only because
of wide spreads or no qualified event. The guard withholds the trade decision for a closed bar that
ended more than 6 h ago; features (and the liquidity state) are still built exactly as before.

Evidence: research/engfix/staleguard/regression_evidence.json (staleguard_regression.py).
"""
from __future__ import annotations

import difflib
import hashlib
import json
import os

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EVIDENCE = os.path.join(os.path.dirname(__file__), "engfix", "staleguard", "regression_evidence.json")
D45_SNAPSHOT = os.path.join(ROOT, "build", "pmfix_src", "NEXA_EA_PMFIX.mq5")
D45_SOURCE = "10b62623dde6cb7644b05ad58f92c308a2d45ea8d88e7301217122fb661011ac"
RISK_AT_EVIDENCE = "7fd5692a2bd3aec7443185f914be320158cfe55bcddcf370db059a6da0d908d1"   # NEXA_Risk.mqh when the D46 regression ran
D46_SNAPSHOT = os.path.join(ROOT, "build", "stale_src", "NEXA_EA_STALE.mq5")   # the source D46 was built and run from
D46_SOURCE = "3edcec11a6eabbfbcba3625369c4de205bc114fdfe0cfb144c4d55e123027488"


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


def test_guard_rule_and_limit():
    src = _read(os.path.join(ROOT, "NEXA_EA.mq5"))
    assert "const int NEXA_STALE_BAR_MAX_SEC = 6 * 3600;" in src
    f = _func(src, "bool NexaClosedBarStale(")
    assert "if(closedBarOpen <= 0 || periodSec <= 0 || now <= 0) return false;" in f
    assert "return ((long)now - ((long)closedBarOpen + periodSec)) > maxSec;" in f    # measured from bar CLOSE


def test_guard_sits_after_features_and_before_any_trade_path():
    tick = _func(_read(os.path.join(ROOT, "NEXA_EA.mq5")), "void OnTick()")
    call = ("if(NexaClosedBarStale(g_sig.decisionBarTime, PeriodSeconds(PERIOD_CURRENT), TimeCurrent(), "
            "NEXA_STALE_BAR_MAX_SEC))\n     { LogDecision(g_sig, 0, \"NO_TRADE_STALE_BAR\"); return; }")
    assert tick.count(call) == 1
    g = tick.index(call)
    assert tick.index("g_sigValid = BuildFeatures(g_sig);") < g          # liquidity state advances as before
    assert tick.index("g_sig.usdCompositeDirection = UsdCompositeDirection();") < g
    for later in ("NO_TRADE_SPREAD_TAX", "ComputeCompositeScore(", "ExecuteSignal("):
        assert g < tick.index(later), later


def test_change_is_additive_and_confined():
    """Against the D45 source: lines are only ADDED, and only the guard block (no logic removed)."""
    d45 = _read(D45_SNAPSHOT)
    assert _sha(D45_SNAPSHOT) == D45_SOURCE
    cur = _read(D46_SNAPSHOT)                                    # D46's own change, not later ones
    assert _sha(D46_SNAPSHOT) == D46_SOURCE
    diff = [ln for ln in difflib.ndiff(d45.splitlines(), cur.splitlines()) if ln[:2] in ("- ", "+ ")]
    assert not [ln for ln in diff if ln.startswith("- ")], "existing lines removed or edited"
    added = [ln[2:] for ln in diff]
    assert len(added) == 17
    assert all(("NexaClosedBarStale" in a or "NEXA_STALE_BAR_MAX_SEC" in a or a.strip().startswith(("//", "{", "}"))
                or a.strip() == "" or "return" in a or "NO_TRADE_STALE_BAR" in a) for a in added)
    for sig in ("void ExecuteSignal(", "void ManageOpenPosition()", "int OnInit()", "bool IsWeekendCloseWindow()",
                "void CloseNexaPositionIfAny(", "bool ValidateInputs("):
        assert _func(d45, sig) == _func(cur, sig), sig


def test_tester_regression_evidence():
    if not os.path.exists(EVIDENCE):
        pytest.skip("stale-guard regression evidence not present")
    with open(EVIDENCE) as fh:
        ev = json.load(fh)
    assert ev["sources"]["NEXA_EA.mq5"] == _sha(D46_SNAPSHOT), "evidence must stay pinned to the D46 source"
    tick = _func(_read(os.path.join(ROOT, "NEXA_EA.mq5")), "void OnTick()")
    assert tick == _func(_read(D46_SNAPSHOT), "void OnTick()"), "OnTick changed since the D46 evidence: rerun"
    assert ev["sources"]["NEXA_Risk.mqh"] == RISK_AT_EVIDENCE
    assert ev["stale_ex5"] == _sha(os.path.join(ROOT, "build", "NEXA_EA_STALE.ex5"))
    s = ev["summary"]
    assert s["runs"] == 12 and s["all_test_passed"] and s["all_comparable"]
    assert s["all_flagged_equals_expected"] and s["flagged_stale_total"] == s["expected_stale_total"] > 0
    assert s["rows_differing_outside_stale_total"] == 0 and s["trade_rows_identical"] and s["opens_identical"]
    assert set(s["columns_differing_on_stale_rows"]) <= {"reason", "composite_score", "quality_score"}
    for w, v in ev["windows"].items():
        assert v["max_lag_hours_not_stale"] <= 6, w                      # every unflagged decision is fresh
