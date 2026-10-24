"""Fail-closed correlation cap (human-approved NEXA_Risk.mqh safety fix, 2026-09-29).

* Python oracle cases: aligned, missing history, unreadable symbol (wrapper, via MQL5 evidence),
  shifted bars, sparse missing bars, insufficient alignment (79/80 boundary), zero variance,
  NaN / non-finite, high correlation blocks, low correlation passes.
* Regression: the REMOVED shift-aligned function passed (returned ~0) where the fix blocks.
* Parity: the COMPILED MQL5 core, run in the Strategy Tester on the same fixtures, must equal the
  oracle; the evidence is pinned to the current NEXA_Risk.mqh hash (stale evidence fails).
* Static fail-closed checks on the MQL5 source. Synthetic data only."""
from __future__ import annotations

import csv
import hashlib
import os
import re

import numpy as np
import pytest

import nexa_corr_oracle as o

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Re-run 2026-10-03 after each approved change to NEXA_Risk.mqh (S11, then C4); results identical to the
# 2026-09-29 run corrcap_parity_20260929_t2 (kept). The evidence must match the CURRENT Risk source.
EVIDENCE = os.path.join(os.path.dirname(__file__), "tester_runs", "corrcap_parity_20261003_c4")
FIX = o.fixtures()


@pytest.mark.parametrize("name", sorted(FIX))
def test_oracle_state_matches_fail_closed_expectation(name):
    c = FIX[name]
    state, _, _, _ = o.correlation_from_bars(c["tA"], c["cA"], c["tB"], c["cB"])
    assert state == c["expect"], (name, o.STATE_NAME[state])


def test_every_non_ok_state_blocks_the_cap():
    assert o.cap_ok([o.OK, o.OK])
    assert not o.cap_ok([o.OK, o.INSUFFICIENT_DATA])
    assert not o.cap_ok([o.BLOCK])
    assert not o.cap_ok([o.OK, 99])                      # any unexpected state blocks too


def test_correlation_value_is_the_pearson_of_time_aligned_returns():
    c = FIX["gap_15_bars_B_time_aligned"]
    state, r, aligned, _ = o.correlation_from_bars(c["tA"], c["cA"], c["tB"], c["cB"])
    tb = {t: x for t, x in zip(c["tB"], c["cB"], strict=True)}
    ra, rb = [], []
    for k in range(1, len(c["tA"])):
        t0, t1 = c["tA"][k - 1], c["tA"][k]
        if t0 in tb and t1 in tb:
            ra.append(c["cA"][k] / c["cA"][k - 1] - 1)
            rb.append(tb[t1] / tb[t0] - 1)
    assert aligned == len(ra) == 84
    assert r == pytest.approx(np.corrcoef(ra, rb)[0, 1], abs=1e-12) and state == o.BLOCK


def test_threshold_boundary_and_sign():
    c = FIX["valid_aligned_high_corr"]
    _, r, _, _ = o.correlation_from_bars(c["tA"], c["cA"], c["tB"], c["cB"])
    assert o.correlation_from_bars(c["tA"], c["cA"], c["tB"], c["cB"], threshold=abs(r))[0] == o.BLOCK   # >= blocks
    assert o.correlation_from_bars(c["tA"], c["cA"], c["tB"], c["cB"], threshold=abs(r) + 1e-9)[0] == o.OK
    assert o.correlation_from_bars(*(FIX["negative_high_corr_block"][k] for k in ("tA", "cA", "tB", "cB")))[0] == o.BLOCK


def test_invalid_configuration_fails_closed():
    c = FIX["valid_aligned_high_corr"]
    for kw in ({"bars_back": 2}, {"threshold": float("nan")}, {"threshold": 0.0}, {"min_aligned_frac": 0.0}):
        assert o.correlation_from_bars(c["tA"], c["cA"], c["tB"], c["cB"], **kw)[0] == o.INSUFFICIENT_DATA
    assert o.correlation_from_bars(c["tA"], c["cA"][:-1], c["tB"], c["cB"])[0] == o.INSUFFICIENT_DATA


def test_removed_shift_aligned_function_failed_open_where_the_fix_blocks():
    """Documents the defect: the legacy function (shift-indexed, newest first) passed these cases."""
    for name in ("gap_15_bars_B_time_aligned", "missing_history_empty_B", "sparse_missing_8_bars_B"):
        c = FIX[name]
        a_shift = [0.0] + list(reversed(c["cA"]))                      # index 0 = forming bar
        b_shift = [0.0] + list(reversed(c["cB"])) + [0.0] * (102 - len(c["cB"]))
        legacy = o.legacy_pearson(a_shift, b_shift)
        new_state = o.correlation_from_bars(c["tA"], c["cA"], c["tB"], c["cB"])[0]
        assert abs(legacy) < o.THRESHOLD, (name, legacy)                # legacy: PASS
        assert new_state != o.OK, name                                  # fix: BLOCK / INSUFFICIENT_DATA


# ---------------------------------------------------------------- MQL5 parity (compiled core, Strategy Tester)

def _evidence():
    with open(os.path.join(EVIDENCE, "PROVENANCE.txt")) as fh:
        prov = dict(line.strip().split("=", 1) for line in fh if "=" in line)
    with open(os.path.join(EVIDENCE, "mql5_results.csv"), newline="") as fh:
        rows = {r["case"]: r for r in csv.DictReader(fh)}
    return prov, rows


def test_mql5_evidence_is_for_the_current_risk_source_and_fixtures(tmp_path):
    prov, _ = _evidence()
    with open(os.path.join(ROOT, "NEXA_Risk.mqh"), "rb") as fh:
        live = hashlib.sha256(fh.read()).hexdigest()
    assert prov["nexa_risk_sha256"] == live, "MQL5 evidence is stale: rerun NEXA_CorrCapTest in the tester"
    p = tmp_path / "fx.csv"
    o.write_fixtures(str(p))
    assert hashlib.sha256(p.read_bytes()).hexdigest() == prov["fixtures_sha256"]


@pytest.mark.parametrize("name", sorted(FIX))
def test_compiled_mql5_core_equals_oracle(name):
    _, rows = _evidence()
    c = FIX[name]
    state, r, aligned, detail = o.correlation_from_bars(c["tA"], c["cA"], c["tB"], c["cB"])
    m = rows[name]
    assert m["state"] == o.STATE_NAME[state]
    assert int(m["aligned"]) == aligned and m["detail"] == detail
    assert float(m["corr"]) == pytest.approx(r, abs=1e-12)


def test_mql5_wrapper_fails_closed_on_unreadable_symbol():
    _, rows = _evidence()
    assert rows["wrapper_unreadable_symbol"]["state"] == "INSUFFICIENT_DATA"
    assert rows["wrapper_unreadable_symbol"]["detail"] == "SYMBOL_UNAVAILABLE"
    assert rows["wrapper_empty_symbol"]["state"] == "INSUFFICIENT_DATA"
    assert rows["cap_no_positions"]["state"] == "OK"                    # nothing to correlate against


# ---------------------------------------------------------------- static checks on the MQL5 source

def _risk_src() -> str:
    with open(os.path.join(ROOT, "NEXA_Risk.mqh"), encoding="utf-8") as fh:
        return fh.read()


def _code_only(src: str) -> str:
    return "\n".join(line.split("//", 1)[0] for line in src.splitlines())


def test_mql5_source_is_fail_closed_and_time_aligned():
    s = _risk_src()
    block = s[s.index("CORRELATION CAP (fail-closed"):s.index("PORTFOLIO CURRENCY EXPOSURE")]
    assert "iClose(" not in _code_only(block) and "PearsonCorrelation" not in _code_only(s)
    cap = block[block.index("bool CorrelationCapOK"):]
    assert re.search(r'if\(psym == ""\)\s*\{[^}]*return false;', cap)
    assert re.search(r"NEXA_CORR_INSUFFICIENT_DATA\)\s*\{[^}]*return false;", cap)
    assert re.search(r"st != NEXA_CORR_OK\)\s*\{[^}]*return false;", cap)
    assert "SERIES_SYNCHRONIZED" in block and "CopyRates(symA, PERIOD_CURRENT, 1," in block
    assert re.search(r"#define NEXA_CORR_MIN_ALIGNED_FRAC\s+0\.80", block)
    assert o.MIN_ALIGNED_FRAC == 0.80 and o.THRESHOLD == 0.75 and o.BARS_BACK == 100
