"""
test_nexa_validate.py -- Stage 5 tests.

Synthetic fixtures only. No MT5 terminal, no network, no recorded dataset.

The fixtures build datasets with a KNOWN defect, then assert the gate catches
it. Several build a clean dataset and assert the gate stays quiet, because a
gate that fails everything is as useless as one that passes everything.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nexa_validate import (
    FEATURE_COLUMNS,
    GateStatus,
    Severity,
    ValidationConfig,
    ValidationGateError,
    assert_validation_or_halt,
    binary_target,
    episode_view,
    make_purged_walk_forward,
    validate_dataset,
    verify_no_leakage,
)

T0 = pd.Timestamp("2026-01-05 08:00:00")


def _episode(i, label="TP_WIN", *, start=None, span_min=30, symbol="EURUSD",
             timeframe="M1", seed=None, features=None, ambiguous=False):
    rng = np.random.default_rng(seed if seed is not None else i)
    start = start if start is not None else T0 + pd.Timedelta(hours=6 * i)
    end = start + pd.Timedelta(minutes=span_min)
    row = {
        "schema_version": "1.0",
        "row_id": f"{symbol}:{start}:{i}",
        "symbol": symbol, "timeframe": timeframe,
        "event": "OPEN", "episode_id": i,
        "decision_ts": start - pd.Timedelta(minutes=1),
        "decision_ts_effective": start - pd.Timedelta(minutes=1),
        "write_ts": start + pd.Timedelta(hours=2),
        "fill_ts": start,
        "label_start_ts": start, "label_end_ts": end,
        "label": label, "label_reason": "TEST",
        "ambiguous_bar": ambiguous, "bars_to_outcome": span_min,
        "mfe_r": 1.2, "mae_r": 0.4, "result_r": 1.5,
        "exec_model": "M1_OHLC_TEST",
    }
    if features is None:
        vals = rng.normal(size=len(FEATURE_COLUMNS))
        # Regime enums must span several buckets WITHOUT tracking the label
        # cycle. An earlier fixture used f21 = i % 2 while labels alternated on
        # i % 2, making f21 a perfect predictor -- the leakage detector caught
        # it, which is the detector working. Different moduli keep them
        # independent.
        vals[20] = i % 3
        vals[21] = (i // 7) % 2
    else:
        vals = features
    for j, col in enumerate(FEATURE_COLUMNS):
        row[col] = float(vals[j])
    return row


def _dataset(n=300, win_every=2, **over):
    rows = []
    for i in range(n):
        label = "TP_WIN" if i % win_every == 0 else "SL_LOSS"
        rows.append(_episode(i, label=label, **over))
    return pd.DataFrame(rows)


def _cfg(**over) -> ValidationConfig:
    base = {"min_resolved_episodes": 50, "walk_forward_folds": 3,
            "embargo_bars": 60, "bar_minutes": 1}
    base.update(over)
    return ValidationConfig(**base)


def codes(res) -> set:
    return {f.code for f in res.findings}


# ---------------------------------------------------------------------------
# clean dataset
# ---------------------------------------------------------------------------

def test_clean_dataset_passes():
    res = validate_dataset(_dataset(300), _cfg())
    assert res.status is GateStatus.PASS, res.report()
    assert res.passed


def test_clean_dataset_produces_folds():
    res = validate_dataset(_dataset(300), _cfg(walk_forward_folds=3))
    assert len(res.splits) == 3
    for sp in res.splits:
        assert len(sp.train_idx) > 0 and len(sp.test_idx) > 0


def test_gate_does_not_raise_on_pass():
    res = validate_dataset(_dataset(300), _cfg())
    assert_validation_or_halt(res)      # must not raise


# ---------------------------------------------------------------------------
# empty / schema
# ---------------------------------------------------------------------------

def test_empty_dataset_is_fail_not_pass():
    res = validate_dataset(pd.DataFrame(), _cfg())
    assert res.status is GateStatus.FAIL
    assert "EMPTY_DATASET" in codes(res)
    with pytest.raises(ValidationGateError):
        assert_validation_or_halt(res)


def test_unsupported_schema_fails():
    df = _dataset(100)
    df["schema_version"] = "2.0"
    res = validate_dataset(df, _cfg())
    assert "UNSUPPORTED_SCHEMA" in codes(res) and not res.passed


def test_mixed_schema_versions_fail():
    df = _dataset(100)
    df.loc[0, "schema_version"] = "1.1"
    res = validate_dataset(df, _cfg())
    assert "MIXED_SCHEMA_VERSIONS" in codes(res)


def test_missing_feature_column_fails():
    df = _dataset(100).drop(columns=["f33"])
    res = validate_dataset(df, _cfg())
    assert "MISSING_FEATURES" in codes(res) and not res.passed


def test_missing_label_column_fails():
    df = _dataset(100).drop(columns=["label"])
    res = validate_dataset(df, _cfg())
    assert "MISSING_REQUIRED_COLUMN" in codes(res)


# ---------------------------------------------------------------------------
# feature integrity
# ---------------------------------------------------------------------------

def test_nan_feature_is_an_error():
    df = _dataset(100)
    df.loc[3, "f07"] = np.nan
    res = validate_dataset(df, _cfg())
    assert "FEATURE_NAN" in codes(res) and not res.passed


def test_infinite_feature_is_an_error():
    df = _dataset(100)
    df.loc[5, "f11"] = np.inf
    res = validate_dataset(df, _cfg())
    assert "FEATURE_NONFINITE" in codes(res)


def test_constant_feature_is_warned_not_failed():
    """A zero-variance feature is useless, not corrupting."""
    df = _dataset(100)
    df["f44"] = 1.0
    res = validate_dataset(df, _cfg())
    assert "CONSTANT_FEATURES" in codes(res)
    assert all(f.severity is not Severity.ERROR
               for f in res.findings if f.code == "CONSTANT_FEATURES")


# ---------------------------------------------------------------------------
# labels and class balance
# ---------------------------------------------------------------------------

def test_no_trainable_labels_fails():
    df = _dataset(100)
    df["label"] = "AMBIGUOUS"
    res = validate_dataset(df, _cfg())
    assert "NO_TRAINABLE_LABELS" in codes(res)


def test_severe_class_imbalance_fails():
    df = _dataset(300, win_every=100)      # ~3% wins
    res = validate_dataset(df, _cfg())
    assert "CLASS_IMBALANCE" in codes(res) and not res.passed


def test_insufficient_sample_fails():
    res = validate_dataset(_dataset(40), _cfg(min_resolved_episodes=200))
    assert "INSUFFICIENT_SAMPLE" in codes(res)


def test_invalid_labels_fail():
    df = _dataset(100)
    df.loc[2, "label"] = "INVALID"
    res = validate_dataset(df, _cfg())
    assert "INVALID_LABELS" in codes(res)


def test_timeout_is_excluded_from_binary_target():
    """A trade that never resolved is not evidence either way."""
    labels = pd.Series(["TP_WIN", "SL_LOSS", "TIMEOUT", "AMBIGUOUS"])
    t = binary_target(labels)
    assert t.iloc[0] == 1.0 and t.iloc[1] == 0.0
    assert pd.isna(t.iloc[2]) and pd.isna(t.iloc[3])


def test_breakeven_and_time_exit_count_as_losses():
    t = binary_target(pd.Series(["BREAKEVEN_STOP", "TIME_EXIT"]))
    assert (t == 0.0).all()


def test_high_ambiguity_rate_is_warned():
    rows = [_episode(i, label="TP_WIN" if i % 2 == 0 else "SL_LOSS",
                     ambiguous=(i % 2 == 0)) for i in range(200)]
    res = validate_dataset(pd.DataFrame(rows), _cfg(max_ambiguous_fraction=0.2))
    assert "HIGH_AMBIGUITY_RATE" in codes(res)


# ---------------------------------------------------------------------------
# chronology
# ---------------------------------------------------------------------------

def test_label_starting_before_decision_fails():
    df = _dataset(100)
    df.loc[1, "label_start_ts"] = df.loc[1, "decision_ts_effective"] - pd.Timedelta(hours=1)
    res = validate_dataset(df, _cfg())
    assert "LABEL_BEFORE_DECISION" in codes(res) and not res.passed


def test_label_end_before_start_fails():
    df = _dataset(100)
    df.loc[4, "label_end_ts"] = df.loc[4, "label_start_ts"] - pd.Timedelta(minutes=5)
    res = validate_dataset(df, _cfg())
    assert "LABEL_END_BEFORE_START" in codes(res)


def test_write_ts_used_as_decision_anchor_is_flagged():
    df = _dataset(100)
    df["write_ts"] = df["decision_ts_effective"]
    res = validate_dataset(df, _cfg())
    assert "WRITE_TS_EQUALS_DECISION_TS" in codes(res)


# ---------------------------------------------------------------------------
# duplicates
# ---------------------------------------------------------------------------

def test_duplicate_row_id_fails():
    df = _dataset(100)
    df.loc[5, "row_id"] = df.loc[4, "row_id"]
    res = validate_dataset(df, _cfg())
    assert "DUPLICATE_ROW_ID" in codes(res)


def test_duplicate_episode_fails():
    df = _dataset(100)
    dup = df.iloc[[7]].copy()
    dup["row_id"] = "other"
    df = pd.concat([df, dup], ignore_index=True)
    res = validate_dataset(df, _cfg())
    assert "DUPLICATE_EPISODE" in codes(res) and not res.passed


def test_episode_view_collapses_multiple_rows_per_trade():
    rows = []
    for ev in ("OPEN", "FILL", "CLOSE"):
        r = _episode(0)
        r["event"] = ev
        r["row_id"] = f"r-{ev}"
        rows.append(r)
    ep = episode_view(pd.DataFrame(rows))
    assert len(ep) == 1 and ep.iloc[0]["event"] == "OPEN"


# ---------------------------------------------------------------------------
# coverage
# ---------------------------------------------------------------------------

def test_mixed_timeframes_fail():
    a = _dataset(60)
    b = _dataset(60, timeframe="M5")
    b["episode_id"] += 1000
    b["row_id"] = b["row_id"] + "-b"
    res = validate_dataset(pd.concat([a, b], ignore_index=True), _cfg())
    assert "MIXED_TIMEFRAMES" in codes(res) and not res.passed


def test_narrow_regime_coverage_is_warned():
    rows = [_episode(i, label="TP_WIN" if i % 2 == 0 else "SL_LOSS",
                     features=np.zeros(len(FEATURE_COLUMNS))) for i in range(120)]
    res = validate_dataset(pd.DataFrame(rows), _cfg())
    assert "NARROW_REGIME_COVERAGE" in codes(res)


def test_multiple_symbols_are_reported():
    a = _dataset(60)
    b = _dataset(60, symbol="GBPUSD")
    b["episode_id"] += 1000
    b["row_id"] = b["row_id"] + "-b"
    res = validate_dataset(pd.concat([a, b], ignore_index=True), _cfg())
    assert res.stats["symbols"] == ["EURUSD", "GBPUSD"]


# ---------------------------------------------------------------------------
# leakage
# ---------------------------------------------------------------------------

def test_feature_that_predicts_label_perfectly_is_caught():
    """No legitimate market feature correlates with the outcome at |r|>0.95."""
    df = _dataset(200)
    df["f30"] = binary_target(df["label"]).to_numpy() * 1.0
    res = validate_dataset(df, _cfg())
    assert "FEATURE_ALMOST_PERFECTLY_PREDICTS_LABEL" in codes(res)
    assert not res.passed


def test_clean_features_do_not_trigger_leakage_check():
    res = validate_dataset(_dataset(200), _cfg())
    assert "FEATURE_ALMOST_PERFECTLY_PREDICTS_LABEL" not in codes(res)


def test_purge_removes_overlapping_training_rows():
    """
    Every episode spans 10 days, so early episodes overlap later test windows
    and must be purged.
    """
    rows = [_episode(i, label="TP_WIN" if i % 2 == 0 else "SL_LOSS",
                     start=T0 + pd.Timedelta(days=i), span_min=60 * 24 * 10)
            for i in range(60)]
    ep = pd.DataFrame(rows)
    findings = []
    splits = make_purged_walk_forward(ep, _cfg(embargo_bars=60 * 24 * 12), findings)
    assert splits
    assert sum(s.purged for s in splits) > 0


def test_embargo_shorter_than_label_span_fails():
    rows = [_episode(i, start=T0 + pd.Timedelta(days=i), span_min=60 * 24 * 5)
            for i in range(40)]
    findings = []
    make_purged_walk_forward(pd.DataFrame(rows), _cfg(embargo_bars=10), findings)
    assert any(f.code == "EMBARGO_TOO_SHORT" for f in findings)


def test_independent_leakage_verifier_catches_injected_overlap():
    """
    The verifier is separate from the builder on purpose: a builder bug that
    kept an overlapping row must still be caught.
    """
    rows = [_episode(i, start=T0 + pd.Timedelta(days=i), span_min=60 * 24 * 10)
            for i in range(60)]
    ep = pd.DataFrame(rows).sort_values("label_start_ts").reset_index(drop=True)
    findings = []
    splits = make_purged_walk_forward(ep, _cfg(embargo_bars=60 * 24 * 12), findings)
    assert splits
    sp = splits[-1]
    sp.train_idx = np.append(sp.train_idx, sp.test_idx[0])   # inject the leak
    leak_findings = []
    verify_no_leakage(ep, [sp], leak_findings)
    assert any(f.code == "LEAKAGE_TRAIN_TEST_OVERLAP" for f in leak_findings)


def test_clean_splits_pass_the_leakage_verifier():
    rows = [_episode(i, start=T0 + pd.Timedelta(days=i), span_min=30)
            for i in range(60)]
    ep = pd.DataFrame(rows).sort_values("label_start_ts").reset_index(drop=True)
    findings = []
    splits = make_purged_walk_forward(ep, _cfg(embargo_bars=60), findings)
    leak_findings = []
    verify_no_leakage(ep, splits, leak_findings)
    assert not leak_findings


def test_high_label_overlap_is_reported():
    rows = [_episode(i, label="TP_WIN" if i % 2 == 0 else "SL_LOSS",
                     start=T0 + pd.Timedelta(minutes=i), span_min=600)
            for i in range(120)]
    res = validate_dataset(pd.DataFrame(rows), _cfg())
    assert "HIGH_LABEL_OVERLAP" in codes(res)
    assert res.stats["overlapping_label_fraction"] > 0.5


def test_cannot_split_tiny_dataset():
    res = validate_dataset(_dataset(4), _cfg(min_resolved_episodes=1,
                                             walk_forward_folds=5))
    assert "CANNOT_SPLIT" in codes(res)


# ---------------------------------------------------------------------------
# determinism / reporting
# ---------------------------------------------------------------------------

def test_validation_is_deterministic():
    df = _dataset(200)
    a = validate_dataset(df, _cfg())
    b = validate_dataset(df, _cfg())
    assert a.status == b.status
    assert [str(f) for f in a.findings] == [str(f) for f in b.findings]
    assert a.stats == b.stats
    assert [(s.fold, len(s.train_idx), len(s.test_idx)) for s in a.splits] == \
           [(s.fold, len(s.train_idx), len(s.test_idx)) for s in b.splits]


def test_report_is_stable_text():
    df = _dataset(200)
    assert validate_dataset(df, _cfg()).report() == validate_dataset(df, _cfg()).report()


def test_failure_report_names_the_error():
    df = _dataset(100)
    df.loc[3, "f07"] = np.nan
    res = validate_dataset(df, _cfg())
    assert "FEATURE_NAN" in res.report()
    assert "FAIL" in res.report()


def test_gate_error_message_contains_the_report():
    res = validate_dataset(pd.DataFrame(), _cfg())
    with pytest.raises(ValidationGateError, match="DATASET VALIDATION FAILED"):
        assert_validation_or_halt(res)
