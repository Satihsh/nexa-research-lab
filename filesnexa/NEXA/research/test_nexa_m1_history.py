"""Tests for nexa_m1_history on constructed files (not market data)."""
from __future__ import annotations

import pandas as pd
import pytest

import nexa_m1_history as mh


def _write(path, times, px=1.1, spread=1):
    t = pd.to_datetime(times)
    df = pd.DataFrame({"time": t.strftime("%Y.%m.%d %H:%M:%S"), "open": px, "high": px + 1e-4,
                       "low": px - 1e-4, "close": px, "tick_volume": 1, "spread": spread})
    df.to_csv(path, index=False)
    return str(path)


def test_overlap_identical_is_merged_once(tmp_path):
    a = _write(tmp_path / "a.csv", pd.date_range("2024-01-02 10:00", periods=5, freq="1min"))
    b = _write(tmp_path / "b.csv", pd.date_range("2024-01-02 10:03", periods=5, freq="1min"))
    out, info = mh.assemble([a, b])
    assert len(out) == 8 and info["overlap_bars"] == 2 and info["overlap_conflicts"] == 0


def test_overlap_conflict_aborts(tmp_path):
    a = _write(tmp_path / "a.csv", pd.date_range("2024-01-02 10:00", periods=5, freq="1min"))
    b = _write(tmp_path / "b.csv", pd.date_range("2024-01-02 10:03", periods=5, freq="1min"), px=1.2)
    with pytest.raises(mh.HistoryError):
        mh.assemble([a, b])


def test_gap_report_separates_weekend_and_intraweek():
    t = pd.Series(pd.to_datetime(["2024-01-05 23:58", "2024-01-08 00:01", "2024-01-08 00:02",
                                  "2024-01-08 10:00", "2024-01-08 10:01"]))
    g = mh.gap_report(t, pd.Timedelta(minutes=1))
    assert g["weekend"] == 1 and g["intra_week_ge_6h"] == 1 and g["intra_week_lt_6h"] == 0


def test_resample_check_detects_equal_and_unequal():
    m1 = pd.DataFrame({"time": pd.date_range("2024-01-02 10:00", periods=10, freq="1min"),
                       "open": range(10), "high": [x + 0.5 for x in range(10)],
                       "low": [x - 0.5 for x in range(10)], "close": range(10)}).astype({"open": float, "close": float})
    broker = pd.DataFrame({"time": pd.to_datetime(["2024-01-02 10:00", "2024-01-02 10:05"]),
                           "open": [0.0, 5.0], "high": [4.5, 9.5], "low": [-0.5, 4.5], "close": [4.0, 9.0]})
    assert mh.resample_check(m1, broker, "M5")["mismatch_frac"] == 0.0
    broker.loc[1, "high"] = 9.7
    assert mh.resample_check(m1, broker, "M5")["mismatching_bars_by_field"]["high"] == 1
