"""Tests for nexa_dna_audit on constructed rows (not market data)."""
from __future__ import annotations

import pandas as pd

from nexa_dna_audit import FEATURES, audit_frame, reason_family


def _rows(decision, write, reason="NO_TRADE_SPREAD_TAX_476.2PCT"):
    base = {f: "0.5" for f in FEATURES}
    base["f01"] = "1"
    return {**base, "event": "DECISION", "decision_ts": decision, "write_ts": write, "reason": reason}


def test_reason_family_strips_numeric_payloads():
    assert reason_family("NO_TRADE_SPREAD_TAX_476.2PCT") == "NO_TRADE_SPREAD_TAX"
    assert reason_family("FOMC_WINDOW_20250618_SEP_DOTPLOT") == "FOMC_WINDOW"
    assert reason_family("") == "EMPTY"


def test_causality_flags_same_bar_or_future_decision():
    df = pd.DataFrame([
        _rows("2025.06.02 00:01:00", "2025.06.02 00:02:00"),
        _rows("2025.06.02 00:05:00", "2025.06.02 00:05:00"),   # same timestamp: forming-bar leak
        _rows("2025.06.02 00:09:00", "2025.06.02 00:08:00"),   # decision after write: leak
    ])
    df.loc[1, "f00"] = "0.7"
    c = audit_frame(df)["causality"]
    assert c["lag_exactly_one_bar"] == 1 and c["lag_not_positive"] == 2


def test_constant_and_non_finite_features_reported():
    df = pd.DataFrame([_rows("2025.06.02 00:01:00", "2025.06.02 00:02:00"),
                       _rows("2025.06.02 00:02:00", "2025.06.02 00:03:00")])
    df.loc[0, "f02"] = "inf"
    f = audit_frame(df)["features"]
    assert f["non_finite_values"] == 1
    assert "f00" in f["constant_features"] and "f02" not in f["constant_features"]
