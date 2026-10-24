"""D-TZ (human-approved 2026-10-03, option A): the EA's server clock follows US DST.

Pepperstone server time = New York + 7 h, i.e. GMT+2 on US standard time and GMT+3 during US DST
(research/reports/TIME_CONVENTION_EVIDENCE.json). The EA used a fixed InpGMTOffset = 2, so for ~2/3 of
the year every "GMT" hour (Asia range, session tag and its LATE veto, optional session filter / hard
close, FOMC clock) was real GMT + 1. NEXA_Common.mqh now adds the US-DST hour with the same explicit
rule as research/nexa_time.py; the parity oracle mirrors it (nexa_parity.server_gmt_offset_hours).

Evidence:
  * tester_runs/clock_dtz_20261003  -- compiled clock, every hour 2000-2030 (test_nexa_parity.py)
  * engfix/dtz/regression_evidence.json -- journalled session tags vs the true clock, behaviour diff
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PRE = os.path.join(ROOT, "build", "dtz_pre_source", "NEXA_Common.mqh")
PRE_SHA = "f4d0a7de036adf46"                       # prefix of the pre-D-TZ NEXA_Common.mqh
EVIDENCE = os.path.join(os.path.dirname(__file__), "engfix", "dtz", "regression_evidence.json")


def _read(path: str) -> str:
    if not os.path.isfile(path):
        pytest.skip(f"not present: {path}")
    with open(path, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def _sha(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def test_clock_follows_us_dst_through_one_helper():
    src = _read(os.path.join(ROOT, "NEXA_Common.mqh"))
    assert "input int InpGMTOffset = 2;" in src
    assert "const bool NEXA_SERVER_FOLLOWS_US_DST = true;" in src
    assert "const int  NEXA_SERVER_NY_PLUS_HOURS  = 7;" in src
    assert "return InpGMTOffset + ((NEXA_SERVER_FOLLOWS_US_DST && NexaUSDSTAtServer(srv)) ? 1 : 0);" in src
    assert "datetime NexaToGMT(datetime srv)   { return srv - (datetime)(NexaServerGMTOffsetHours(srv) * 3600); }" in src
    assert "datetime NexaGMTNow()              { return NexaToGMT(TimeCurrent()); }" in src
    # the US rule, as in nexa_time.us_dst_bounds_local
    assert "if(t.year >= 2007)      { start = NexaNthSunday(t.year, 3, 2); end = NexaNthSunday(t.year, 11, 1); }" in src
    assert "else if(t.year >= 1987) { start = NexaNthSunday(t.year, 4, 1); end = NexaLastSunday(t.year, 10); }" in src
    assert "start += 2 * 3600; end += 2 * 3600;" in src and "return (ny >= start && ny < end);" in src


def test_no_fixed_offset_conversion_left_anywhere():
    for path in glob.glob(os.path.join(ROOT, "*.mq5")) + glob.glob(os.path.join(ROOT, "*.mqh")):
        with open(path, encoding="utf-8", errors="replace") as fh:
            code = "\n".join(ln.split("//", 1)[0] for ln in fh)
        assert not re.search(r"InpGMTOffset\s*\*\s*3600", code), os.path.basename(path)


def test_change_confined_to_the_clock_block():
    pre, cur = _read(PRE), _read(os.path.join(ROOT, "NEXA_Common.mqh"))
    assert _sha(PRE).startswith(PRE_SHA)
    a, b = "//--- Broker server clock offset from GMT, in hours.", "int      NexaGMTHourOf(datetime srv)"
    assert pre[:pre.index(a)] == cur[:cur.index(a)], "anything before the clock block changed"
    assert pre[pre.index(b):] == cur[cur.index(b):], "anything after the clock helpers changed"
    assert re.findall(r"^input.*$", pre, re.MULTILINE) == re.findall(r"^input.*$", cur, re.MULTILINE)


def test_tester_regression_evidence():
    if not os.path.exists(EVIDENCE):
        pytest.skip("D-TZ regression evidence not present")
    with open(EVIDENCE) as fh:
        ev = json.load(fh)
    # pinned to the sources the D-TZ regression ran with (C4 later changed NEXA_EA.mq5 / NEXA_Risk.mqh)
    assert ev["sources"]["NEXA_Common.mqh"] == _sha(os.path.join(ROOT, "NEXA_Common.mqh")), "stale evidence: rerun"
    assert ev["sources"]["NEXA_EA.mq5"] == _sha(os.path.join(ROOT, "build", "dtz_src", "NEXA_EA_DTZ.mq5"))
    assert ev["sources"]["NEXA_Risk.mqh"] == _sha(os.path.join(ROOT, "build", "dtz_src", "NEXA_Risk.mqh"))
    assert ev["dtz_ex5"] == _sha(os.path.join(ROOT, "build", "NEXA_EA_DTZ.ex5"))
    s = ev["summary"]
    assert s["runs"] == 12 and s["all_test_passed"]
    assert s["tag_rows_checked"] > 500_000 and s["tag_rows_in_us_dst"] > 0
    assert s["new_tag_mismatches_vs_true_clock"] == 0          # the compiled EA now runs on the true clock
    assert s["base_tag_mismatches_vs_fixed_clock"] == 0        # ... and the baseline ran on the old fixed one
    assert s["first_divergence_always_in_us_dst"]              # behaviour changes only where the clocks differ
    assert s["opens_new_true_tag_late"] == 0                   # the LATE veto now holds on real GMT
