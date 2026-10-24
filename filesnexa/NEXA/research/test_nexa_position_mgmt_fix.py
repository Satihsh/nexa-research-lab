"""Engineering fix D-PARTIAL-AFTER-BE (2026-10-03): static checks of the MQL5 source, plus the runtime
evidence produced in the Strategy Tester, each pinned to the source hashes it was produced from.

Root cause: ManageOpenPosition() measured R against the CURRENT stop (|open - sl|). Breakeven sets
sl == open, so risk became 0 and the routine returned before the 1.5R partial close and the 48-bar
time exit. Evidence files (research/engfix/):
  * runs/pmgmt_harness/mql5_results.csv   -- NEXA_PositionMgmtTest.mq5 scenario checks (requirements 1-8, 11, 12)
  * runs/mutation_summary.json             -- deliberate regressions of NEXA_PositionMgmt.mqh, all must be killed
  * regression/regression_evidence.json    -- pre-fix vs fixed EA end to end (requirements 9, 10)
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENG = os.path.join(os.path.dirname(__file__), "engfix")
PRE_FIX_SOURCE = "d65090cca1654814b1be6e6b50cb6c2570c2ba4a3a9c7790bae5ba7121716c62"
# The D45 evidence was produced from this source (kept byte-identical as the staged compile copy).
# Later EA changes (stale-bar guard, 2026-10-03) leave ManageOpenPosition untouched; that is checked
# below, so the D45 evidence stays valid for the management logic of the current source.
D45_SOURCE = "10b62623dde6cb7644b05ad58f92c308a2d45ea8d88e7301217122fb661011ac"
D45_SNAPSHOT = os.path.join(ROOT, "build", "pmfix_src", "NEXA_EA_PMFIX.mq5")


def _src(name: str) -> str:
    path = os.path.join(ROOT, name)
    if not os.path.isfile(path):
        pytest.skip(f"MQL5 source not present: {name}")
    with open(path, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def _sha(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _func(src: str, signature: str) -> str:
    i = src.index(signature)
    return src[i:src.index("\n  }\n", i)]


def _evidence(rel: str) -> str:
    p = os.path.join(ENG, rel)
    if not os.path.exists(p):
        pytest.skip(f"evidence not present: {rel}")
    return p


# ---------------------------------------------------------------- static: the fix itself
def test_root_cause_removed_r_no_longer_from_current_stop():
    s = _func(_src("NEXA_EA.mq5"), "void ManageOpenPosition()")
    tail = s[s.index("// D-PARTIAL-AFTER-BE fix (2026-10-03)"):]
    assert "MathAbs(open - sl)" not in tail                     # no current-stop denominator
    assert "NexaMgmtAction act = NexaManageStep(in);" in tail
    assert 'GV("RiskDist_" + IntegerToString(posId))' in tail   # authoritative initial risk, same key as writers
    assert 'GV("PartialDone_" + IntegerToString(posId))' in tail
    assert "ulong  posId  = (ulong)PositionGetInteger(POSITION_IDENTIFIER);" in tail


def test_time_exit_and_breakeven_paths_driven_by_decision_and_keep_guards():
    s = _func(_src("NEXA_EA.mq5"), "void ManageOpenPosition()")
    assert 'if(act.timeExit) CloseNexaPositionIfAny("time exit");' in s
    assert "StopDistanceAllowed(type, open) && FreezeLevelAllowsChange(type, sl, tp) && !ModifyThrottled(ticket)" in s
    assert "in.timeExitR = 0.3;" in s                            # the literal threshold is unchanged


def test_partial_exactly_once_uses_history_and_pending_orders():
    s = _src("NEXA_EA.mq5")
    m = _func(s, "void ManageOpenPosition()")
    assert "PositionExitDealState(posId)" in m and "PositionHasPendingCloseOrder(posId)" in m
    assert "GlobalVariableSet(pk, (double)TimeCurrent());" in m
    assert "DEAL_ENTRY_OUT || e == DEAL_ENTRY_OUT_BY) return 1;" in _func(s, "int PositionExitDealState(")
    h = _src("NEXA_PositionMgmt.mqh")
    f = _func(h, "bool NexaPartialHandled(")
    assert "if(historyHasExit) return true;" in f and "if(closeOrderPending) return true;" in f


def test_initial_risk_reference_never_uses_a_stop_at_or_beyond_entry():
    f = _func(_src("NEXA_PositionMgmt.mqh"), "double NexaInitialRiskRef(")
    assert "if(hasCtx && ctxRisk > 0 && NexaFinite(ctxRisk)) return ctxRisk;" in f
    assert "bool lossSide = (dir > 0) ? (sl < open) : (sl > open);" in f
    assert "return lossSide ? MathAbs(open - sl) : 0.0;" in f


def test_no_input_added_or_changed_and_risk_file_untouched():
    src = _src("NEXA_EA.mq5")
    names = {}
    for f in ["NEXA_EA.mq5"] + re.findall(r'^#include "([^"]+)"', src, re.MULTILINE):
        for m in re.finditer(r"^\s*s?input\s+\w+\s+(\w+)\s*=\s*([^;]+);", _src(f), re.MULTILINE):
            names[m.group(1)] = m.group(2).strip().strip('"')
    assert len(names) == 64                                     # same 64 inputs the A3 runs logged
    for k, v in {"InpPartialCloseAtR": "1.50", "InpPartialClosePct": "50.0", "InpBreakevenAtR": "1.00",
                 "InpTimeExitBars": "48", "InpMaxSameCurrencyNet": "2", "InpRiskPercent": "0.30",
                 "InpHardRiskCeiling": "1.00", "InpMaxTradesPerDay": "10", "InpMinSampleForSurvival": "20",
                 "InpExpectancyPauseR": "-0.1", "InpMinTP_R": "1.50", "InpMaxTP_R": "4.00"}.items():
        assert float(names[k]) == float(v), k
    assert "NEXA_PositionMgmt.mqh" not in _src("NEXA_Risk.mqh")
    assert _sha(os.path.join(ROOT, "NEXA_Risk.mqh")) == "a43d8328178550657fe3af51717896d71accbd28fb43f5e0b0df825483e3a244"   # approved C4 (D45 ran on 7fd5692a)


def test_entry_logic_untouched_outside_management():
    """Every function of the pre-fix source except ManageOpenPosition is byte-identical."""
    pre = os.path.join(ROOT, "build", "pmfix_pre_source", "NEXA_EA.mq5")
    if not os.path.exists(pre):
        pytest.skip("pre-fix source snapshot not present")
    with open(pre, encoding="utf-8") as fh:
        old = fh.read().replace("\r\n", "\n")
    assert _sha(pre) == PRE_FIX_SOURCE
    if not os.path.exists(D45_SNAPSHOT):
        pytest.skip("D45 source snapshot not present")
    assert _sha(D45_SNAPSHOT) == D45_SOURCE
    with open(D45_SNAPSHOT, encoding="utf-8") as fh:
        new = fh.read().replace("\r\n", "\n")
    for sig in ("void ExecuteSignal(", "void OnTradeTransaction(", "int OnInit()", "double ComputeTP(",
                "void OnTick()", "bool SafeModifySL(", "void CloseNexaPositionIfAny(", "bool ValidateInputs("):
        if sig in old:
            assert _func(old, sig) == _func(new, sig), sig


# ---------------------------------------------------------------- runtime evidence (Strategy Tester)
def test_harness_all_pass_for_current_include():
    ev = _evidence(os.path.join("runs", "pmgmt_harness", "PROVENANCE.txt"))
    with open(ev) as fh:
        prov = dict(line.strip().split("=", 1) for line in fh if "=" in line)
    assert prov["mqh_sha256"] == _sha(os.path.join(ROOT, "NEXA_PositionMgmt.mqh")), "stale evidence: rerun the harness"
    with open(_evidence(os.path.join("runs", "pmgmt_harness", "mql5_results.csv")), newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 47 and all(r["result"].strip() == "PASS" for r in rows)
    names = {r["check"] for r in rows}
    for req in ("T01_", "T02_", "T03_", "T04_", "T05_", "T06_", "T07_", "T08_", "T11_", "T12_", "T12b_"):
        assert any(n.startswith(req) for n in names), req


def test_every_mutant_killed():
    with open(_evidence(os.path.join("runs", "mutation_summary.json"))) as fh:
        mut = json.load(fh)
    assert len(mut) == 6
    assert all(v["compiled"] and v["ran"] and v["killed"] for v in mut.values()), mut


def test_end_to_end_regression_pre_vs_post():
    with open(_evidence(os.path.join("regression", "regression_evidence.json"))) as fh:
        ev = json.load(fh)
    assert ev["post_sources"]["NEXA_EA.mq5"] == D45_SOURCE, "evidence must stay pinned to the D45 source"
    if not os.path.exists(D45_SNAPSHOT):
        pytest.skip("D45 source snapshot not present")
    assert _sha(D45_SNAPSHOT) == D45_SOURCE
    with open(D45_SNAPSHOT, encoding="utf-8") as fh:
        d45 = fh.read().replace("\r\n", "\n")
    sig = "void ManageOpenPosition()"
    assert _func(d45, sig) == _func(_src("NEXA_EA.mq5"), sig), "management logic changed since the D45 evidence: rerun"
    assert ev["post_sources"]["NEXA_PositionMgmt.mqh"] == _sha(os.path.join(ROOT, "NEXA_PositionMgmt.mqh"))
    s = ev["summary"]
    assert s["runs"] == 24 and s["all_test_passed"] and s["all_inputs_exact_production"]
    assert s["all_reconcile"] and s["all_deals_match_legs"] and s["all_ingest_ok"] and s["all_episodes_linked"]
    assert s["pre_partials"] == 0 and s["post_partials"] > 0                # the defect, then the fix
    assert s["post_max_one_partial_per_trade"] and s["post_all_partial_triggers_at_or_after_1_5R"]
    assert s["post_partials_sent_logged"] == s["post_partials"]              # every send executed once, no duplicate send
    for w, v in ev["windows"].items():
        assert v["post"]["partials_sent_logged"] == v["post"]["partials"], w
    assert s["post_partial_send_failures"] == 0 and s["post_no_risk_reference_warnings"] == 0
    assert s["post_history_unreadable_warnings"] == 0
    assert s["post_close_result_r_max_rel_err"] < 0.03                      # 5-dp journal rounding only
    for w, d in s["windows_diverging"].items():                             # divergence only at an exit row
        assert d["post_event"] in ("PARTIAL_CLOSE", "CLOSE") or d["pre_event"] in ("PARTIAL_CLOSE", "CLOSE"), (w, d)
