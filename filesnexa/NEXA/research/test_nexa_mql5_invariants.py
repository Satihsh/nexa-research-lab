"""Static invariant checks on the live MQL5 sources.

These tests read the MQL5 files as text. They do not compile anything and they
do not prove runtime behaviour; they stop silent drift in contracts the research
tier depends on:

  * NEXA_Risk.mqh stays byte-identical (modulo line endings) to the immutable
    baseline except three human-approved blocks -- the fail-closed correlation cap
    (2026-09-29), the fail-closed currency-exposure cap (S11, 2026-10-03) and the
    pre-trade daily-loss budget (C4, 2026-10-03, appended) -- and keeps the hard-risk
    defaults recorded in the handover.
  * The FOMC fail-closed table is sorted, has no duplicates, covers today with
    headroom, and covers every year the research data spans.
  * PackFeatures() stays wired to exactly 48 slots.

Skipped (not failed) when the MQL5 sources are not one directory above research/.
"""
from __future__ import annotations

import datetime as dt
import os
import re

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BASELINE = os.path.join(ROOT, "NEXA_BASELINE_BACKUP_20260919-124052")


def _read(path: str) -> str:
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8").replace("\r\n", "\n")


def _need(path: str) -> str:
    if not os.path.isfile(path):
        pytest.skip(f"MQL5 source not present in this layout: {path}")
    return _read(path)


# ---------------------------------------------------------------- risk engine

# The ONLY human-authorised divergences from the baseline: the fail-closed correlation-cap safety fix
# (approved 2026-09-29) and the fail-closed currency-exposure cap (S11, approved 2026-10-03). Everything
# before the correlation block must stay byte-identical to the immutable baseline, and each block must
# equal its approved text (hashes below). Any other change to NEXA_Risk.mqh still requires a new explicit
# human authorisation.
CORR_BLOCK_START_BASE = "//==================== PEARSON CORRELATION ===================="
CORR_BLOCK_START_LIVE = "//==================== CORRELATION CAP (fail-closed, time-aligned) ===================="
CORR_BLOCK_END = "//==================== PORTFOLIO CURRENCY EXPOSURE ===================="
APPROVED_CORR_BLOCK_SHA256 = "97f28759e6c4853ddb3b7cba9b2e47c29599d4efd08e9ac0dfc71844f319c62e"
# The exposure block runs from CORR_BLOCK_END to the end of the file (S11: NetCurrencyExposure reports an
# unreadable position, ExposureCapOK blocks with EXPOSURE_POSITION_UNREADABLE / EXPOSURE_CAP_INVALID_SPEC).
APPROVED_EXPOSURE_BLOCK_SHA256 = "bb23581e9b9dd99449eff14eeb1e38ef2e59a52917a3b89c69254b252d4e4a73"
# C4 (approved 2026-10-03) is APPENDED before "#endif": the exposure text plus "#endif\n" must still hash to
# the S11-approved value, and the appended section must equal its approved text.
C4_BLOCK_START = "//==================== DAILY LOSS BUDGET (C4, pre-trade) ===================="
APPROVED_C4_BLOCK_SHA256 = "c6eabbb95e6acdc20f35b35789c2906de60877ad1bb71138fda03853e4605405"


def _split(src: str, start: str) -> tuple[str, str, str]:
    i, j = src.index(start), src.index(CORR_BLOCK_END)
    return src[:i], src[i:j], src[j:]


def test_risk_engine_identical_to_baseline_outside_the_approved_fixes():
    live = _need(os.path.join(ROOT, "NEXA_Risk.mqh"))
    base = _need(os.path.join(BASELINE, "NEXA_Risk.mqh"))
    lp, lblock, ls = _split(live, CORR_BLOCK_START_LIVE)
    bp, _, bs = _split(base, CORR_BLOCK_START_BASE)
    assert lp == bp, "NEXA_Risk.mqh diverged from baseline outside the approved fixes"
    import hashlib
    assert hashlib.sha256(lblock.encode("utf-8")).hexdigest() == APPROVED_CORR_BLOCK_SHA256, \
        "correlation block differs from the approved safety fix: requires explicit human authorisation"
    k = ls.index(C4_BLOCK_START)
    assert hashlib.sha256((ls[:k] + "#endif\n").encode("utf-8")).hexdigest() == APPROVED_EXPOSURE_BLOCK_SHA256, \
        "exposure block differs from the approved S11 fix: requires explicit human authorisation"
    assert hashlib.sha256(ls[k:].encode("utf-8")).hexdigest() == APPROVED_C4_BLOCK_SHA256, \
        "daily-loss budget block differs from the approved C4 change: requires explicit human authorisation"
    # S11 only changed NetCurrencyExposure / ExposureCapOK: the rest of the block is the baseline text.
    for sig in ("void GetSymbolCurrencies(", "#endif"):
        assert ls[ls.index(sig):ls.index(sig) + 200].split("\n  }\n")[0] == bs[bs.index(sig):bs.index(sig) + 200].split("\n  }\n")[0]


@pytest.mark.parametrize(
    "name,value",
    [
        ("InpRiskPercent", "0.30"),
        ("InpHardRiskCeiling", "1.00"),
        ("InpMaxDailyLossPct", "2.00"),
        ("InpMaxDrawdownPct", "10.00"),
        ("InpMaxTradesPerDay", "10"),
        ("InpMaxSpreadATRRatio", "0.15"),
        ("InpMaxMarginUsagePct", "50.0"),
        ("InpMaxSameCurrencyNet", "2"),
        ("InpMaxCorrelation", "0.75"),
        ("InpCorrelationBars", "100"),
    ],
)
def test_hard_risk_defaults_unchanged(name, value):
    src = _need(os.path.join(ROOT, "NEXA_Risk.mqh"))
    m = re.search(rf"input\s+\w+\s+{name}\s*=\s*([0-9.]+)\s*;", src)
    assert m, f"{name} not found in NEXA_Risk.mqh"
    assert float(m.group(1)) == float(value)


# ---------------------------------------------------------------- FOMC gate

def _fomc_rows() -> list[tuple[dt.date, bool]]:
    src = _need(os.path.join(ROOT, "NEXA_FOMC.mqh"))
    body = re.search(r"FOMCEvent\s+g_fomc\[\]\s*=\s*\{(.*?)\};", src, re.DOTALL)
    assert body, "g_fomc[] table not found"
    rows = re.findall(r"\{\s*(\d{4})\s*,\s*(\d{1,2})\s*,\s*(\d{1,2})\s*,\s*(true|false)\s*\}", body.group(1))
    return [(dt.date(int(y), int(m), int(d)), s == "true") for y, m, d, s in rows]


def test_fomc_table_sorted_and_unique():
    rows = _fomc_rows()
    dates = [d for d, _ in rows]
    assert len(dates) >= 8
    assert dates == sorted(dates), "FOMC_Init reads the LAST row as the table end: keep it sorted"
    assert len(set(dates)) == len(dates)


def test_fomc_decision_days_are_weekdays():
    for d, _ in _fomc_rows():
        assert d.weekday() < 5, f"{d} is a weekend: transcription error"


def test_fomc_table_covers_today_with_headroom():
    """The gate fails CLOSED when exhausted. Fail this test 60 days before that happens."""
    last = _fomc_rows()[-1][0]
    assert last >= dt.datetime.now(dt.UTC).date() + dt.timedelta(days=60), (
        f"FOMC table ends {last}: add the next year's schedule before NEXA stops trading"
    )


@pytest.mark.parametrize("year", [2024, 2025, 2026])
def test_fomc_table_covers_backtest_years(year):
    """Tester runs over these years must apply the same gate live policy would."""
    per_year = [d for d, _ in _fomc_rows() if d.year == year]
    assert len(per_year) == 8, f"{year}: expected 8 scheduled meetings, found {len(per_year)}"
    assert sum(1 for d, s in _fomc_rows() if d.year == year and s) == 4, "4 SEP meetings per year"


# ---------------------------------------------------------------- feature contract

def test_packfeatures_width_is_48():
    """Order is checked by nexa_parity.verify_feature_order; this pins the width."""
    src = _need(os.path.join(ROOT, "NEXA_Intelligence.mqh"))
    m = re.search(r"#define\s+NEXA_AI_FEATURE_COUNT\s+(\d+)", src)
    assert m and int(m.group(1)) == 48
    body = re.search(r"bool\s+PackFeatures\s*\(.*?\n  \}", src, re.DOTALL)
    assert body, "PackFeatures() not found"
    assert len(re.findall(r"out\[k\+\+\]\s*=", body.group(0))) == 48


def test_fomc_veto_row_anchored_to_closed_bar():
    """decision_ts must be the CLOSED bar (shift 1) even on pre-feature vetoes."""
    src = _need(os.path.join(ROOT, "NEXA_EA.mq5"))
    m = re.search(r"FOMC_InBlockedWindow\(fomcReason\)\)\s*\{(.*?)return;", src, re.DOTALL)
    assert m, "FOMC veto block not found"
    assert "iTime(_Symbol, PERIOD_CURRENT, 1)" in m.group(1)
    assert "decisionBarTime = bt;" not in m.group(1)


def test_risk_dist_not_journaled_for_rows_without_a_stop():
    """CLOSE rows have sl=0; |entry - 0| is a price, not a risk distance."""
    src = _need(os.path.join(ROOT, "NEXA_EA.mq5"))
    assert "(r.sl > 0 && r.entryIntended > 0) ? MathAbs(r.entryIntended - r.sl) : 0.0" in src
