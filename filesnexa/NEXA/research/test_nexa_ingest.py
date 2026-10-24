"""
test_nexa_ingest.py -- Stage 2 tests.

Every fixture is synthetic. No MT5 terminal, no network, no real journal file
is required to run these. The fixtures are built from the same column list the
loader enforces, so a schema change breaks the tests loudly rather than letting
the loader drift away from nexa_schema_v1.json unnoticed.

Run:  python -m pytest test_nexa_ingest.py -v
"""

from __future__ import annotations

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nexa_ingest import (
    FEATURE_COLUMNS,
    SchemaVersionError,
    load_many,
    load_trade_dna,
    write_canonical,
)

MT5_COLUMNS = [
    "schema_version", "row_id", "write_ts", "decision_ts", "dispatch_ts", "fill_ts",
    "symbol", "timeframe", "event", "strategy_id", "direction", "decision_source",
    "bid", "ask", "spread", "spread_atr_ratio", "atr", "atr_m15", "session_tag",
    "regime_trend", "regime_vol", "regime_transitioning",
    "pdh", "pdl", "pdc", "pd_src_bar", "liq_setup", "liq_origin", "liq_level", "liq_state",
    "composite_score", "quality_score",
    "entry_intended", "entry_actual", "sl_price", "tp_price", "target_r", "risk_dist",
    "lots", "slippage_points", "commission", "swap", "result_r",
    "model_id", "model_schema_version", "calibration_id", "ai_raw_p",
] + FEATURE_COLUMNS + ["reason"]


def _row(**over) -> dict:
    """A valid DECISION row; override any field to construct a defect."""
    r = {c: "" for c in MT5_COLUMNS}
    r.update({
        "schema_version": "1.0",
        "row_id": "EURUSD:2026.09.18 08:00:00:1",
        "write_ts": "2026.09.18 08:00:01",
        "decision_ts": "2026.09.18 08:00:00",
        "symbol": "EURUSD", "timeframe": "M1",
        "event": "DECISION", "strategy_id": "1", "direction": "0",
        "decision_source": "RULE_ONLY",
        "bid": "1.10000", "ask": "1.10012", "spread": "0.00012",
        "spread_atr_ratio": "0.0800", "atr": "0.00150", "atr_m15": "0.00220",
        "session_tag": "LONDON",
        "regime_trend": "0", "regime_vol": "1", "regime_transitioning": "0",
        "pdh": "1.10500", "pdl": "1.09500", "pdc": "1.10100",
        "pd_src_bar": "2026.09.17",
        "liq_setup": "0", "liq_origin": "0", "liq_level": "0", "liq_state": "0",
        "composite_score": "0", "quality_score": "3",
        "entry_intended": "0.00000", "entry_actual": "0.00000",
        "sl_price": "0.00000", "tp_price": "0.00000",
        "target_r": "0.000", "risk_dist": "0.00000", "lots": "0.00",
        "slippage_points": "0.0", "commission": "0.00", "swap": "0.00",
        "result_r": "0.0000",
        "model_id": "NONE", "model_schema_version": "1.0",
        "calibration_id": "NONE", "ai_raw_p": "-1.000000",
        "reason": "NO_TRADE_NO_QUALIFIED_LIQUIDITY_EVENT_state0",
    })
    for i, c in enumerate(FEATURE_COLUMNS):
        r[c] = f"{i * 0.01:.6f}"
    r.update(over)
    return r


def _open_row(**over) -> dict:
    return _row(**{
        "row_id": "EURUSD:2026.09.18 08:05:00:2",
        "decision_ts": "2026.09.18 08:05:00",
        "dispatch_ts": "2026.09.18 08:05:00",
        "event": "OPEN", "direction": "1",
        "entry_intended": "1.10012", "sl_price": "1.09900", "tp_price": "1.10180",
        "target_r": "1.500", "risk_dist": "0.00112", "lots": "0.01",
        "composite_score": "2", "quality_score": "6",
        "reason": "DISPATCHED", **over})


def _fill_row(**over) -> dict:
    # Mirrors reality: written from a blank signal, so decision_ts renders as epoch.
    return _row(**{
        "row_id": "EURUSD:1970.01.01 00:00:00:3",
        "decision_ts": "1970.01.01 00:00:00",
        "dispatch_ts": "2026.09.18 08:05:00",
        "fill_ts": "2026.09.18 08:05:01",
        "event": "FILL", "direction": "1",
        "entry_intended": "1.10012", "entry_actual": "1.10014",
        "sl_price": "1.09900", "tp_price": "1.10180",
        "lots": "0.01", "slippage_points": "2.0", "commission": "-0.07",
        "reason": "SLIPPAGE_PTS_2.0", **over})


def _close_row(**over) -> dict:
    return _row(**{
        "row_id": "EURUSD:1970.01.01 00:00:00:4",
        "decision_ts": "1970.01.01 00:00:00",
        "fill_ts": "2026.09.18 09:20:00",
        "event": "CLOSE", "direction": "1",
        "entry_intended": "1.10012", "entry_actual": "1.10180",
        "lots": "0.01", "commission": "-0.14", "swap": "-0.02",
        "result_r": "1.5000", "reason": "R_RESULT_1.500", **over})


def _write(tmp_path, rows, name="NEXA_TradeDNA_EURUSD.csv") -> str:
    p = tmp_path / name
    pd.DataFrame(rows, columns=MT5_COLUMNS).to_csv(p, index=False, lineterminator="\n")
    return str(p)


def codes(result) -> set:
    return {f.code for f in result.findings}


# --------------------------------------------------------------------------
# happy path
# --------------------------------------------------------------------------

def test_clean_file_loads_without_errors(tmp_path):
    path = _write(tmp_path, [_row(), _open_row(), _fill_row(), _close_row()])
    res = load_trade_dna(path)
    assert res.ok, res.report()
    assert len(res.frame) == 4
    assert res.stats["symbols"] == ["EURUSD"]
    assert res.stats["event_counts"]["OPEN"] == 1


def test_features_are_passed_through_unmodified(tmp_path):
    """The central rule: Python must not alter an MQL5-produced feature."""
    path = _write(tmp_path, [_open_row()])
    res = load_trade_dna(path)
    for i, col in enumerate(FEATURE_COLUMNS):
        assert res.frame[col].iloc[0] == pytest.approx(i * 0.01, abs=1e-12)


def test_numeric_precision_is_preserved(tmp_path):
    path = _write(tmp_path, [_open_row(entry_intended="1.23456", f07="0.123457")])
    res = load_trade_dna(path)
    assert res.frame["entry_intended"].iloc[0] == pytest.approx(1.23456, abs=1e-12)
    assert res.frame["f07"].iloc[0] == pytest.approx(0.123457, abs=1e-12)


# --------------------------------------------------------------------------
# schema version
# --------------------------------------------------------------------------

def test_unsupported_schema_version_raises(tmp_path):
    path = _write(tmp_path, [_row(schema_version="0.9")])
    with pytest.raises(SchemaVersionError):
        load_trade_dna(path)


def test_unsupported_schema_can_be_inspected_without_raising(tmp_path):
    path = _write(tmp_path, [_row(schema_version="2.0")])
    res = load_trade_dna(path, strict_schema=False)
    assert "UNSUPPORTED_SCHEMA" in codes(res)
    assert not res.ok


def test_missing_schema_column_raises(tmp_path):
    p = tmp_path / "legacy.csv"
    pd.DataFrame([{"time": "x", "symbol": "EURUSD"}]).to_csv(p, index=False)
    with pytest.raises(SchemaVersionError):
        load_trade_dna(str(p))


def test_mixed_schema_versions_flagged(tmp_path):
    path = _write(tmp_path, [_row(), _row(row_id="r2", schema_version="1.1")])
    res = load_trade_dna(path, strict_schema=False)
    assert "MIXED_SCHEMA_VERSIONS" in codes(res)


# --------------------------------------------------------------------------
# timestamps
# --------------------------------------------------------------------------

def test_timestamp_kinds_are_not_conflated(tmp_path):
    path = _write(tmp_path, [_fill_row()])
    row = load_trade_dna(path).frame.iloc[0]
    assert row["write_ts"] != row["fill_ts"]
    assert row["dispatch_ts"] == pd.Timestamp("2026-09-18 08:05:00")
    assert row["fill_ts"] == pd.Timestamp("2026-09-18 08:05:01")


def test_empty_timestamp_becomes_nat_not_epoch(tmp_path):
    path = _write(tmp_path, [_row(dispatch_ts="", fill_ts="")])
    row = load_trade_dna(path).frame.iloc[0]
    assert pd.isna(row["dispatch_ts"]) and pd.isna(row["fill_ts"])


def test_epoch_decision_ts_is_treated_as_missing(tmp_path):
    path = _write(tmp_path, [_open_row(), _fill_row()])
    res = load_trade_dna(path)
    assert "EPOCH_DECISION_TS" in codes(res)
    fill = res.frame[res.frame["event"] == "FILL"].iloc[0]
    assert pd.isna(fill["decision_ts"])          # never 1970


def test_malformed_timestamp_is_an_error(tmp_path):
    path = _write(tmp_path, [_row(decision_ts="18/09/2026 08:00")])
    res = load_trade_dna(path)
    assert "MALFORMED_TIMESTAMP" in codes(res)
    assert not res.ok


def test_decision_ts_required_on_decision_and_open(tmp_path):
    path = _write(tmp_path, [_open_row(decision_ts="")])
    res = load_trade_dna(path)
    assert "MISSING_DECISION_TS" in codes(res)
    assert not res.ok


# --------------------------------------------------------------------------
# structural validation
# --------------------------------------------------------------------------

def test_duplicate_row_id_is_an_error(tmp_path):
    path = _write(tmp_path, [_row(), _row()])
    res = load_trade_dna(path)
    assert "DUPLICATE_ROW_ID" in codes(res)
    assert not res.ok


def test_invalid_event_is_an_error(tmp_path):
    path = _write(tmp_path, [_row(event="MAYBE")])
    res = load_trade_dna(path)
    assert "INVALID_EVENT" in codes(res)


def test_non_numeric_feature_is_an_error(tmp_path):
    path = _write(tmp_path, [_open_row(f12="abc")])
    res = load_trade_dna(path)
    assert "NON_NUMERIC_FEATURE" in codes(res)
    assert not res.ok


def test_missing_required_column_reported(tmp_path):
    p = tmp_path / "short.csv"
    df = pd.DataFrame([_row()], columns=MT5_COLUMNS).drop(columns=["f47"])
    df.to_csv(p, index=False)
    res = load_trade_dna(str(p))
    assert "MISSING_COLUMNS" in codes(res)
    assert len(res.frame) == 0        # refuses to emit a frame without the feature block


def test_inconsistent_symbol_is_flagged(tmp_path):
    path = _write(tmp_path, [_row(), _row(row_id="r2", symbol="GBPUSD")])
    res = load_trade_dna(path)
    assert "INCONSISTENT_SYMBOL" in codes(res)


def test_invalid_direction_on_trade_row(tmp_path):
    path = _write(tmp_path, [_open_row(direction="0")])
    res = load_trade_dna(path)
    assert "INVALID_DIRECTION" in codes(res)


# --------------------------------------------------------------------------
# numeric sanity
# --------------------------------------------------------------------------

def test_inverted_quote_is_an_error(tmp_path):
    path = _write(tmp_path, [_row(bid="1.10012", ask="1.10000", spread="-0.00012")])
    res = load_trade_dna(path)
    assert "INVERTED_QUOTE" in codes(res)


def test_ai_raw_p_minus_one_is_valid_sentinel(tmp_path):
    """-1 means 'no model participated'. It is not an out-of-range probability."""
    path = _write(tmp_path, [_row(ai_raw_p="-1.000000")])
    res = load_trade_dna(path)
    assert "AI_P_OUT_OF_RANGE" not in codes(res)
    assert res.frame["ai_raw_p"].iloc[0] == -1.0


def test_ai_raw_p_out_of_range_flagged(tmp_path):
    path = _write(tmp_path, [_row(ai_raw_p="1.400000")])
    res = load_trade_dna(path)
    assert "AI_P_OUT_OF_RANGE" in codes(res)


def test_ai_raw_p_is_never_renamed_to_calibrated(tmp_path):
    path = _write(tmp_path, [_row(ai_raw_p="0.700000")])
    frame = load_trade_dna(path).frame
    assert "ai_raw_p" in frame.columns
    assert not any("calibrated_p" in c for c in frame.columns)
    assert frame["calibration_id"].iloc[0] == "NONE"


def test_barriers_on_wrong_side_flagged(tmp_path):
    path = _write(tmp_path, [_open_row(sl_price="1.10500", tp_price="1.09000")])
    res = load_trade_dna(path)
    assert "BARRIERS_WRONG_SIDE_LONG" in codes(res)


def test_nonpositive_lots_on_executed_row(tmp_path):
    path = _write(tmp_path, [_open_row(lots="0.00")])
    res = load_trade_dna(path)
    assert "NONPOSITIVE_LOTS" in codes(res)


# --------------------------------------------------------------------------
# episode linking
# --------------------------------------------------------------------------

def test_episode_links_open_fill_close(tmp_path):
    path = _write(tmp_path, [_row(), _open_row(), _fill_row(), _close_row()])
    frame = load_trade_dna(path).frame
    trade = frame[frame["event"].isin(("OPEN", "FILL", "CLOSE"))]
    assert trade["episode_id"].nunique() == 1
    assert (frame[frame["event"] == "DECISION"]["episode_id"] == -1).all()


def test_effective_decision_ts_inherited_by_fill(tmp_path):
    path = _write(tmp_path, [_open_row(), _fill_row()])
    frame = load_trade_dna(path).frame
    fill = frame[frame["event"] == "FILL"].iloc[0]
    assert fill["decision_ts_effective"] == pd.Timestamp("2026-09-18 08:05:00")
    assert bool(fill["decision_ts_inherited"]) is True


def test_original_decision_ts_not_overwritten(tmp_path):
    """A consumer must be able to tell an inherited anchor from a native one."""
    path = _write(tmp_path, [_open_row(), _fill_row()])
    frame = load_trade_dna(path).frame
    opened = frame[frame["event"] == "OPEN"].iloc[0]
    assert bool(opened["decision_ts_inherited"]) is False
    assert opened["decision_ts"] == opened["decision_ts_effective"]


def test_orphan_execution_row_flagged(tmp_path):
    path = _write(tmp_path, [_fill_row()])
    res = load_trade_dna(path)
    assert "ORPHAN_EXECUTION_ROW" in codes(res)


def test_rejected_row_closes_episode(tmp_path):
    rej = _fill_row(row_id="r-rej", event="REJECTED", reason="ASYNC_RC_10016")
    path = _write(tmp_path, [_open_row(), rej, _open_row(row_id="r-open2"),
                             _fill_row(row_id="r-fill2")])
    frame = load_trade_dna(path).frame
    assert frame[frame["event"] != "DECISION"]["episode_id"].nunique() == 2


# --------------------------------------------------------------------------
# determinism and output
# --------------------------------------------------------------------------

def test_ingestion_is_deterministic(tmp_path):
    path = _write(tmp_path, [_row(), _open_row(), _fill_row(), _close_row()])
    a = load_trade_dna(path).frame
    b = load_trade_dna(path).frame
    pd.testing.assert_frame_equal(a, b)


def test_write_canonical_refuses_on_errors(tmp_path):
    path = _write(tmp_path, [_row(), _row()])          # duplicate row_id
    res = load_trade_dna(path)
    with pytest.raises(ValueError, match="refusing to write"):
        write_canonical(res, str(tmp_path / "out.csv"))


def test_write_canonical_roundtrip(tmp_path):
    path = _write(tmp_path, [_row(), _open_row(), _fill_row(), _close_row()])
    res = load_trade_dna(path)
    out = write_canonical(res, str(tmp_path / "canonical.csv"))
    back = pd.read_csv(out)
    assert len(back) == 4
    assert all(c in back.columns for c in FEATURE_COLUMNS)


def test_output_sorted_by_causal_anchor_not_write_ts(tmp_path):
    early = _row(row_id="a", decision_ts="2026.09.18 08:00:00", write_ts="2026.09.18 23:59:59")
    later = _row(row_id="b", decision_ts="2026.09.18 09:00:00", write_ts="2026.09.18 09:00:01")
    path = _write(tmp_path, [later, early])
    frame = load_trade_dna(path).frame
    assert frame["row_id"].tolist() == ["a", "b"]


# --------------------------------------------------------------------------
# multi-file
# --------------------------------------------------------------------------

def test_load_many_combines_and_tags_source(tmp_path):
    p1 = _write(tmp_path, [_row(), _open_row()], "NEXA_TradeDNA_EURUSD.csv")
    p2 = _write(tmp_path, [_row(row_id="g1", symbol="GBPUSD"),
                           _open_row(row_id="g2", symbol="GBPUSD")],
                "NEXA_TradeDNA_GBPUSD.csv")
    res = load_many([p1, p2])
    assert set(res.frame["symbol"]) == {"EURUSD", "GBPUSD"}
    assert set(res.frame["source_file"]) == {"NEXA_TradeDNA_EURUSD.csv",
                                             "NEXA_TradeDNA_GBPUSD.csv"}


def test_load_many_detects_cross_file_duplicate_ids(tmp_path):
    p1 = _write(tmp_path, [_row()], "a.csv")
    p2 = _write(tmp_path, [_row()], "b.csv")
    res = load_many([p1, p2])
    assert "DUPLICATE_ROW_ID_ACROSS_FILES" in codes(res)
    assert not res.ok


def test_findings_carry_example_row_numbers(tmp_path):
    path = _write(tmp_path, [_row(), _row(row_id="r2", event="NOPE")])
    res = load_trade_dna(path)
    finding = next(f for f in res.findings if f.code == "INVALID_EVENT")
    assert finding.count == 1 and len(finding.rows) == 1


def test_empty_file_with_header_only(tmp_path):
    p = tmp_path / "empty.csv"
    pd.DataFrame(columns=MT5_COLUMNS).to_csv(p, index=False)
    res = load_trade_dna(str(p))
    assert len(res.frame) == 0
    assert res.stats["rows_in"] == 0
