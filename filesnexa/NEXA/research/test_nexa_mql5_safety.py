"""Pre-live safety audit (2026-09-29): static checks that each deterministic fix stays in the MQL5
source, plus the runtime evidence produced in the Strategy Tester (pinned to source hashes).

These tests read MQL5 as text; the runtime behaviour is covered by the tester evidence files:
  * tester_runs/safety_primitives_20260929: NEXA_Safety.mqh primitives (29 checks, all PASS);
  * tester_runs/safetyaudit_evidence/dna_regression.json: pre-audit vs fixed EA, identical Trade DNA
    except the intended CLOSE result_r correction when partial closes occur.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RUNS = os.path.join(os.path.dirname(__file__), "tester_runs")


def _src(name: str) -> str:
    path = os.path.join(ROOT, name)
    if not os.path.isfile(path):
        pytest.skip(f"MQL5 source not present: {name}")
    with open(path, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def _sha(name: str) -> str:
    with open(os.path.join(ROOT, name), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _func(src: str, signature: str) -> str:
    i = src.index(signature)
    j = src.index("\n  }\n", i)
    return src[i:j]


def test_restart_keeps_guard_while_broker_order_pending():
    s = _func(_src("NEXA_EA.mq5"), "int OnInit()")
    assert "SetInFlight(_Symbol, false);" not in s
    assert "bool pendingAtBroker = NexaOrderPending();" in s and "SetInFlight(_Symbol, pendingAtBroker);" in s
    assert re.search(r"else if\(!pendingAtBroker\)\s*ClearPendingContext", s)


def test_every_exit_after_portfolio_lock_releases_it():
    s = _func(_src("NEXA_EA.mq5"), "void ExecuteSignal(")
    i, j = s.index("AcquirePortfolioLock()"), s.index("SetInFlight(_Symbol, true);")
    region = s[s.index("\n", i):j]
    returns = region.count("return;")
    assert returns >= 4
    assert region.count("ReleasePortfolioLock(); LogDecision") == returns
    tail = s[s.index("else\n     {\n      ReleaseTradeSlot();"):]
    assert "ReleasePortfolioLock();" in tail and "SetInFlight(_Symbol, false);" in tail


def test_trade_slot_is_reserved_atomically_before_dispatch():
    s = _func(_src("NEXA_EA.mq5"), "void ExecuteSignal(")
    assert "IncrementTradeCount()" not in s
    assert s.index("ReserveTradeSlot()") < s.index("SetInFlight(_Symbol, true);") < s.index("trade.Buy")
    safety = _src("NEXA_Safety.mqh")
    assert "GlobalVariableSetOnCondition(key, c + 1, c)" in safety


def test_retries_revalidate_and_never_raise_risk():
    s = _func(_src("NEXA_EA.mq5"), "void ExecuteSignal(")
    loop = s[s.index("for(int attempt = 0;"):s.index("trade.Buy")]
    assert "riskNow > sizedRiskDist * (1.0 + 1e-9)" in loop and "stopSide" in loop and "roomOK" in loop
    assert "revalFail = true;" in loop and "break;" in loop


def test_missing_stop_recovery_exits_when_intended_stop_breached():
    s = _func(_src("NEXA_EA.mq5"), "void ManageOpenPosition()")
    block = s[s.index("if(sl <= 0)"):s.index("// D-PARTIAL-AFTER-BE fix (2026-10-03)")]
    assert "StopDistanceAllowed(type, reSL)" in block
    assert 'CloseNexaPositionIfAny("stop missing and intended stop already breached")' in block
    assert "ModifyThrottled(ticket)" in block


def test_breakeven_and_time_exit_are_throttled_and_distance_checked():
    s = _func(_src("NEXA_EA.mq5"), "void ManageOpenPosition()")
    assert "StopDistanceAllowed(type, open) && FreezeLevelAllowsChange(type, sl, tp) && !ModifyThrottled(ticket)" in s
    assert "trade.PositionClose(ticket)" not in s
    assert 'CloseNexaPositionIfAny("time exit")' in s


def test_close_by_and_whole_position_r():
    s = _src("NEXA_EA.mq5")
    full = _func(s, "bool PositionFullyClosedByHistory(")
    assert "DEAL_ENTRY_OUT_BY" in full
    tt = _func(s, "void OnTradeTransaction(")
    assert "entryType != DEAL_ENTRY_OUT && entryType != DEAL_ENTRY_OUT_BY" in tt
    assert "UpdateExpectancyStats(rTotal" in tt and "rowC.resultR = rTotal;" in tt


def test_row_id_is_unique_across_restarts():
    s = _src("NEXA_EA.mq5")
    assert "g_rowSeq = (long)TimeLocal() * 1000000;" in _func(s, "int OnInit()")
    assert '"%s:%s:%I64d"' in s and "(int)g_rowSeq" not in s


def test_news_filter_fails_closed_on_unresolvable_event():
    s = _func(_src("NEXA_Intelligence.mqh"), "bool IsNewsRiskWindow(")
    assert not re.search(r"CalendarEventById\([^)]*\)\)\s*continue;", s)
    assert not re.search(r"CalendarCountryById\([^)]*\)\)\s*continue;", s)
    assert s.count("treating as RISK WINDOW (fail-closed)") >= 3


def test_frozen_parts_untouched():
    """PackFeatures (f00-f47) and NEXA_Risk.mqh are not part of this audit's changes. NEXA_Risk.mqh was
    7fd5692a at the audit; it has since changed only by the human-approved S11 and C4 changes (2026-10-03),
    whose exact text is pinned in test_nexa_mql5_invariants.py."""
    live = _func(_src("NEXA_Intelligence.mqh"), "bool PackFeatures(")
    base = os.path.join(ROOT, "NEXA_BASELINE_BACKUP_20260919-124052", "NEXA_Intelligence.mqh")
    if not os.path.isfile(base):
        pytest.skip("baseline not present")
    with open(base, encoding="utf-8") as fh:
        assert live == _func(fh.read().replace("\r\n", "\n"), "bool PackFeatures(")
    assert _sha("NEXA_Risk.mqh") == "a43d8328178550657fe3af51717896d71accbd28fb43f5e0b0df825483e3a244"   # approved C4 (S11 1f684cde, audit 7fd5692a)
    s = _src("NEXA_EA.mq5")
    assert "trade.SetDeviationInPoints(20);" in s                       # broker parameter unchanged


# ---------------------------------------------------------------- runtime evidence (Strategy Tester)

def test_safety_primitives_runtime_evidence_all_pass_for_current_source():
    ev = os.path.join(RUNS, "safety_primitives_20260929")
    with open(os.path.join(ev, "PROVENANCE.txt")) as fh:
        prov = dict(line.strip().split("=", 1) for line in fh if "=" in line)
    assert prov["nexa_safety_mqh_sha256"] == _sha("NEXA_Safety.mqh"), "stale evidence: rerun NEXA_SafetyTest"
    with open(os.path.join(ev, "mql5_results.csv"), newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 29 and all(r["result"] == "PASS" for r in rows)


# The 2026-09-29 audit evidence belongs to the source it was produced from. The EA has since received the
# separately evidenced D-PARTIAL-AFTER-BE fix (test_nexa_position_mgmt_fix.py), so this evidence is pinned
# to its own post-audit source rather than to the current file.
SAFETY_AUDIT_POST_SOURCE = "d65090cca1654814b1be6e6b50cb6c2570c2ba4a3a9c7790bae5ba7121716c62"


def test_dna_regression_pre_vs_post_audit():
    with open(os.path.join(RUNS, "safetyaudit_evidence", "dna_regression.json")) as fh:
        ev = json.load(fh)
    assert ev["post_sources"]["NEXA_EA.mq5"] == SAFETY_AUDIT_POST_SOURCE, "audit evidence must stay pinned to its source"
    c = ev["comparisons"]
    for k in ("deposit_50000", "deposit_1000"):
        assert c[k]["rows"][0] == c[k]["rows"][1] and c[k]["rows_differing_excl_rowid_writets"] == 0
    p = c["deposit_1000_forced_partials_InpPartialCloseAtR_0.5"]
    assert p["differing_columns"] == {"result_r": 2, "reason": 2} and p["differing_events"] == {"CLOSE": 2}
    assert all(v["post_row_id_unique"] for v in c.values())
