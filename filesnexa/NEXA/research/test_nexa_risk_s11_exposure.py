"""S11 (human-approved 2026-10-03, option A): the portfolio currency-exposure cap fails CLOSED.

Before: NetCurrencyExposure() `continue`d past a position whose symbol could not be read, so the cap
under-counted and could let an entry through (fail-open). Volume or currency spec that read as empty
were likewise silently counted as zero. Now any such position makes ExposureCapOK() block with
EXPOSURE_POSITION_UNREADABLE, and a candidate symbol without readable currencies blocks with
EXPOSURE_CAP_INVALID_SPEC -- the same rule as the approved correlation cap (2026-09-29).

The unreadable path cannot occur in the single-symbol Strategy Tester, so it is checked statically
here; the tester regression (research/engfix/s11/regression_evidence.json) proves nothing else moved.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PRE_S11 = os.path.join(ROOT, "build", "s11_pre_source", "NEXA_Risk.mqh")
PRE_S11_SHA = "7fd5692a2bd3aec7443185f914be320158cfe55bcddcf370db059a6da0d908d1"
APPROVED_SHA = "1f684cdef889757ae1b5cbf6c6d72378891d8e9f65bf951f964658ff9fa5897b"   # NEXA_Risk.mqh as approved for S11 (C4 later appended a section)
S11_SNAPSHOT = os.path.join(ROOT, "build", "s11_src", "NEXA_Risk.mqh")
EVIDENCE = os.path.join(os.path.dirname(__file__), "engfix", "s11", "regression_evidence.json")


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


def _fail_open_paths(net_body: str) -> list:
    """Every way the summation loop can skip or zero a position without reporting it."""
    problems = []
    if re.search(r"\bcontinue\s*;", net_body):
        problems.append("loop skips a position with `continue`")
    for guard in ('if(psym == "") { ok = false; return 0; }',
                  "if(!MathIsValidNumber(vol) || vol <= 0) { ok = false; return 0; }",
                  'if(base == "" || quote == "") { ok = false; return 0; }'):
        if guard not in net_body:
            problems.append(f"missing fail-closed guard: {guard}")
    if "ok = true;" not in net_body:
        problems.append("ok not initialised")
    return problems


def test_every_unreadable_position_is_reported():
    src = _read(os.path.join(ROOT, "NEXA_Risk.mqh"))
    assert "double NetCurrencyExposure(string currency, bool &ok)" in src
    assert _fail_open_paths(_func(src, "double NetCurrencyExposure(")) == []


def test_the_check_detects_the_original_fail_open_code():
    """The rule above must flag the pre-S11 source; otherwise it would prove nothing."""
    pre = _read(PRE_S11)
    assert _sha(PRE_S11) == PRE_S11_SHA
    found = _fail_open_paths(_func(pre, "double NetCurrencyExposure("))
    assert "loop skips a position with `continue`" in found


def test_cap_blocks_before_comparing_and_on_missing_spec():
    f = _func(_read(os.path.join(ROOT, "NEXA_Risk.mqh")), "bool ExposureCapOK(")
    assert ('if(base == "" || quote == "" || volMin <= 0 || InpMaxSameCurrencyNet <= 0) '
            '{ reason = "EXPOSURE_CAP_INVALID_SPEC"; return false; }') in f
    block = 'if(!okBase || !okQuote) { reason = "EXPOSURE_POSITION_UNREADABLE"; return false; }'
    assert block in f
    assert f.index("NetCurrencyExposure(base, okBase)") < f.index(block) < f.index("MathAbs(baseAfter) > capLots")
    assert "double capLots = InpMaxSameCurrencyNet * volMin;" in f              # the limit itself is unchanged
    assert 'reason = "PORTFOLIO_CURRENCY_EXPOSURE_CAP"; return false;' in f


def test_change_confined_to_the_two_exposure_functions():
    pre, cur = _read(PRE_S11), _read(S11_SNAPSHOT)               # S11's own change, not later ones
    assert _sha(S11_SNAPSHOT) == APPROVED_SHA
    cut = "// Net exposure in lots for a currency across ALL open positions on the account,"
    assert pre[:pre.index(cut)] == cur[:cur.index(cut)], "anything before the exposure functions changed"
    assert pre.rstrip().endswith("#endif") and cur.rstrip().endswith("#endif")
    for name in re.findall(r"^input\s+\w+\s+(\w+)\s*=", pre, re.MULTILINE):
        assert re.search(rf"^input\s+\w+\s+{name}\s*=", cur, re.MULTILINE), name
    assert re.findall(r"^input.*$", pre, re.MULTILINE) == re.findall(r"^input.*$", cur, re.MULTILINE)   # no input added or changed


def test_no_other_caller_of_the_changed_signature():
    callers = []
    for path in glob.glob(os.path.join(ROOT, "*.mq5")) + glob.glob(os.path.join(ROOT, "*.mqh")):
        with open(path, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                if "NetCurrencyExposure(" in ln and "double NetCurrencyExposure(" not in ln:
                    callers.append((os.path.basename(path), ln.strip()))
    assert {c[0] for c in callers} == {"NEXA_Risk.mqh"}, callers
    assert all(", okBase)" in c[1] or ", okQuote)" in c[1] for c in callers), callers


def test_tester_regression_evidence():
    if not os.path.exists(EVIDENCE):
        pytest.skip("S11 regression evidence not present")
    with open(EVIDENCE) as fh:
        ev = json.load(fh)
    assert ev["sources"]["NEXA_Risk.mqh"] == APPROVED_SHA == _sha(S11_SNAPSHOT)    # pinned to the S11 source
    cur = _read(os.path.join(ROOT, "NEXA_Risk.mqh"))
    for sig in ("double NetCurrencyExposure(", "bool ExposureCapOK("):                # unchanged since the evidence
        assert _func(cur, sig) == _func(_read(S11_SNAPSHOT), sig), sig
    assert ev["s11_ex5"] == _sha(os.path.join(ROOT, "build", "NEXA_EA_S11.ex5"))
    s = ev["summary"]
    assert s["runs"] == 12 and s["all_test_passed"] and s["all_comparable"]
    assert s["rows_differing_total"] == 0                     # every row, incl. every trade row, identical
    assert s["exposure_cap_blocks_identical"] and s["exposure_cap_blocks_total"] > 0
    assert s["new_fail_closed_rows_total"] == 0               # no position is unreadable in the tester
