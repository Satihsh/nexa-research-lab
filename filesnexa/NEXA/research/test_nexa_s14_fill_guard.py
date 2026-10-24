"""S14 (human-approved 2026-10-04, option C): post-fill hard-ceiling guard + signed slippage in the journal.

Pepperstone runs every symbol on MARKET execution (contracts.json trade_exemode = 2), where the order's
deviation (SetDeviationInPoints(20)) is ignored, so a fill can be worse than the quote the lots were sized on.
After each entry fill the EA now re-computes the ACTUAL risk (fill price to stop, OrderCalcProfit) and closes
the position when it exceeds InpHardRiskCeiling or cannot be determined (fail-closed). The FILL row's reason
also carries the signed slippage (+ = adverse). No new limit, no input, no schema change.

Evidence: tester_runs/fillguard_s14_20261004 (harness), engfix/s14/regression_evidence.json (regression).
"""
from __future__ import annotations

import csv
import difflib
import hashlib
import json
import os

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PRE = os.path.join(ROOT, "build", "s14_pre_source", "NEXA_EA.mq5")
PRE_SHA_PREFIX = "4ef7de88b80e2dc9"
RUN = os.path.join(os.path.dirname(__file__), "tester_runs", "fillguard_s14_20261004")
EVIDENCE = os.path.join(os.path.dirname(__file__), "engfix", "s14", "regression_evidence.json")


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


def test_broker_uses_market_execution_where_deviation_is_ignored():
    p = os.path.join(ROOT, "data", "pepperstone", "contracts.json")
    if not os.path.exists(p):
        pytest.skip("contracts.json not present")
    with open(p) as fh:
        c = json.load(fh)
    assert all(c[s]["trade_exemode"] == 2 for s in ("EURUSD", "GBPUSD", "USDJPY", "XAUUSD"))   # SYMBOL_TRADE_EXECUTION_MARKET


def test_guard_logic():
    src = _read(os.path.join(ROOT, "NEXA_FillGuard.mqh"))
    r = _func(src, "double NexaPositionRiskPct(")
    assert "if(!PositionSelectByTicket(ticket)) return -1.0;" in r and "if(sl <= 0) return -2.0;" in r
    assert "if(!OrderCalcProfit(ty, sym, vol, open, sl, pnl)" in r and "return loss / eq * 100.0;" in r
    d = _func(src, "bool NexaFillRiskExceeds(")
    assert "if(riskPct < 0 || !NexaFinite(riskPct)) return true;" in d and "return riskPct > ceilingPct + 1e-9;" in d


def test_ea_runs_the_guard_on_every_entry_fill_and_journals_signed_slippage():
    tt = _func(_read(os.path.join(ROOT, "NEXA_EA.mq5")), "void OnTradeTransaction(")
    assert 'row.reason = StringFormat("SLIPPAGE_PTS_%.1f_ADVERSE_%+.1f", slipPts, slipAdv);' in tt
    assert "double slipAdv = (pt > 0 && dir != 0) ? (dealPrice - intended) * dir / pt : 0;" in tt
    g = tt.index("double fillRiskPct = NexaPositionRiskPct(posId);")
    assert tt.index("LogRow(blank, row);") < g < tt.index("if(entryType != DEAL_ENTRY_OUT")   # entry-fill branch only
    assert "if(NexaFillRiskExceeds(fillRiskPct, InpHardRiskCeiling))" in tt
    assert 'CloseNexaPositionIfAny("fill risk above hard ceiling");' in tt
    assert 'FILL_RISK_ABOVE_HARD_CEILING_%.2fPCT' in tt


def test_change_is_additive_and_confined():
    pre, cur = _read(PRE), _read(os.path.join(ROOT, "NEXA_EA.mq5"))
    assert _sha(PRE).startswith(PRE_SHA_PREFIX)
    diff = [ln for ln in difflib.ndiff(pre.splitlines(), cur.splitlines()) if ln[:2] in ("- ", "+ ")]
    removed = [ln[2:] for ln in diff if ln.startswith("- ")]
    # only two lines replaced: the deviation line (comment added, value unchanged) and the FILL reason format
    assert removed == ["   trade.SetDeviationInPoints(20);",
                       '      row.reason = StringFormat("SLIPPAGE_PTS_%.1f", slipPts);'], removed
    for sig in ("void ExecuteSignal(", "void ManageOpenPosition()", "void OnTick()"):
        assert _func(pre, sig) == _func(cur, sig), sig
    assert "trade.SetDeviationInPoints(20);" in cur                       # the value itself is unchanged


def test_compiled_harness_cases():
    p = os.path.join(RUN, "mql5_results.csv")
    if not os.path.exists(p):
        pytest.skip("fill-guard harness evidence not present")
    with open(os.path.join(RUN, "PROVENANCE.txt")) as fh:
        prov = dict(line.strip().split("=", 1) for line in fh if "=" in line)
    assert prov["fillguard_mqh_sha256"] == _sha(os.path.join(ROOT, "NEXA_FillGuard.mqh")), "stale evidence: rerun"
    with open(p, newline="") as fh:
        rows = {r["case"]: r for r in csv.DictReader(fh)}
    assert len(rows) == 7 and all(r["expected"] == r["actual"] for r in rows.values()), rows
    for c in ("risk_below_ceiling", "risk_above_ceiling"):                 # compiled risk == independent calculation
        assert abs(float(rows[c]["risk_pct"]) - float(rows[c]["independent_pct"])) < 1e-6
    assert float(rows["risk_below_ceiling"]["risk_pct"]) < 1.0 < float(rows["risk_above_ceiling"]["risk_pct"])


def test_tester_regression_evidence():
    if not os.path.exists(EVIDENCE):
        pytest.skip("S14 regression evidence not present")
    with open(EVIDENCE) as fh:
        ev = json.load(fh)
    for name in ("NEXA_EA.mq5", "NEXA_FillGuard.mqh", "NEXA_Risk.mqh", "NEXA_Common.mqh", "NEXA_Intelligence.mqh"):
        assert ev["sources"][name] == _sha(os.path.join(ROOT, name)), f"stale evidence ({name}): rerun"
    assert ev["s14_ex5"] == _sha(os.path.join(ROOT, "build", "NEXA_EA_S14.ex5"))
    s = ev["summary"]
    assert s["runs"] == 12 and s["all_test_passed"] and s["all_comparable"]
    assert s["rows_differing_outside_reason"] == 0 and s["reason_changes_outside_fill_rows"] == 0
    assert s["fill_rows"] > 0 and s["fill_reasons_parsed"] == s["fill_abs_part_unchanged"] == s["fill_rows"]
    assert s["fill_signed_part_matches_prices"] == s["fill_rows"]
    assert s["guard_firings"] == 0
