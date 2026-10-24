"""S13 (human-approved 2026-10-03, option B): usdCompositeDirection (f29) reads the basket symbols by TIME.

Before: iClose(sym, tf, 1) / iClose(sym, tf, 11) -- bar POSITIONS on each basket symbol, so a tick gap or a
different trading break mixed different moments (~15 % of window-B rows; the value was not reproducible
offline and f29 was parity-exempt). Now each symbol uses its last bar at or before the decision bar's time and
its last bar at or before 10 bars earlier (CopyRates by time), skipping stale or degenerate symbols. f29 is
never scored and feeds no model, so trading must be unchanged; the parity oracle now compares f29.

Evidence: engfix/s13/regression_evidence.json; reports/pepperstone/B_PARITY_S13_VERIFY_WINDOW_B.json.
"""
from __future__ import annotations

import hashlib
import json
import os
import re

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PRE = os.path.join(ROOT, "build", "s13_pre_source", "NEXA_Intelligence.mqh")
PRE_SHA_PREFIX = "18e3b30c7de52234"
EVIDENCE = os.path.join(os.path.dirname(__file__), "engfix", "s13", "regression_evidence.json")
PARITY = os.path.join(os.path.dirname(__file__), "reports", "pepperstone", "B_PARITY_S13_VERIFY_WINDOW_B.json")


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


def test_basket_read_by_time_not_position():
    f = _func(_read(os.path.join(ROOT, "NEXA_Intelligence.mqh")), "int UsdCompositeDirection()")
    assert not re.search(r"iClose\s*\(", f), "positional iClose must not remain"
    assert "datetime t   = iTime(_Symbol, PERIOD_CURRENT, 1);" in f                 # the decision bar
    assert "int n = CopyRates(basket[i], PERIOD_CURRENT, t10 - (datetime)stale, t, r);" in f   # bars <= t only
    assert "for(int k = i0; k >= 0; k--) if(r[k].time <= t10) { i10 = k; break; }" in f
    assert "if(i10 < 0 || i10 >= i0) continue;" in f
    assert "if((long)(t - r[i0].time) > stale || (long)(t10 - r[i10].time) > stale) continue;" in f
    src = _read(os.path.join(ROOT, "NEXA_Intelligence.mqh"))
    assert "const int NEXA_USDCOMP_LOOKBACK_BARS = 10;" in src and "const int NEXA_USDCOMP_STALE_BARS    = 5;" in src


def test_vote_rule_unchanged_and_change_confined():
    pre, cur = _read(PRE), _read(os.path.join(ROOT, "NEXA_Intelligence.mqh"))
    assert _sha(PRE).startswith(PRE_SHA_PREFIX)
    tail = "      bool up = c0 > c10;"
    assert _func(pre, "int UsdCompositeDirection()").split(tail)[1] == _func(cur, "int UsdCompositeDirection()").split(tail)[1]
    head = "//==================== SYNTHETIC USD COMPOSITE (INFERRED) ===================="
    assert pre[:pre.index(head)] == cur[:cur.index(head)], "anything before the composite changed"
    assert _func(pre, "bool PackFeatures(") == _func(cur, "bool PackFeatures(")       # f00-f47 wiring unchanged
    assert pre.rstrip().endswith("#endif") and cur.rstrip().endswith("#endif")


def test_ea_still_does_not_score_f29():
    ea = _read(os.path.join(ROOT, "NEXA_EA.mq5"))
    score = _func(ea, "int ComputeCompositeScore(")
    assert "usdCompositeDirection" not in score.replace("// usdCompositeDirection deliberately NOT scored", "")


def test_tester_regression_evidence():
    if not os.path.exists(EVIDENCE):
        pytest.skip("S13 regression evidence not present")
    with open(EVIDENCE) as fh:
        ev = json.load(fh)
    snap = os.path.join(ROOT, "build", "s13_src")                                  # pinned to the S13 sources
    for name, f in (("NEXA_EA.mq5", "NEXA_EA_S13.mq5"), ("NEXA_Intelligence.mqh", "NEXA_Intelligence.mqh"),
                    ("NEXA_Risk.mqh", "NEXA_Risk.mqh"), ("NEXA_Common.mqh", "NEXA_Common.mqh")):
        assert ev["sources"][name] == _sha(os.path.join(snap, f)), f"evidence/source mismatch ({name})"
    cur = _read(os.path.join(ROOT, "NEXA_Intelligence.mqh"))
    assert _func(cur, "int UsdCompositeDirection()") == _func(_read(os.path.join(snap, "NEXA_Intelligence.mqh")),
                                                               "int UsdCompositeDirection()"), "f29 code changed: rerun"
    assert ev["s13_ex5"] == _sha(os.path.join(ROOT, "build", "NEXA_EA_S13.ex5"))
    s = ev["summary"]
    assert s["runs"] == 12 and s["all_test_passed"] and s["all_comparable"]
    assert s["rows_differing_outside_f29"] == 0          # trading and every other feature byte-identical
    assert s["f29_changed_rows"] > 0                      # the defect was real and is gone


def test_window_b_parity_compares_f29():
    if not os.path.exists(PARITY):
        pytest.skip("S13 parity evidence not present")
    with open(PARITY) as fh:
        p = json.load(fh)
    assert set(p) == {"GBPUSD_B", "EURUSD_B", "USDJPY_B", "XAUUSD_B"}
    for tag, v in p.items():
        assert v["contract_status"] == "PASS", tag
        assert v["features_compared"] == 44 and "usdCompositeDirection" not in v["features_exempt"], tag
        assert v["mismatch_rate_by_feature"] == {}, tag
