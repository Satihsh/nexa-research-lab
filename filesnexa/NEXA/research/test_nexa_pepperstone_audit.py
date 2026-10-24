"""Tests for the gap classifier and offset evidence (constructed timestamps, not market data)."""
from __future__ import annotations

import pandas as pd

from nexa_pepperstone_audit import classify_gaps, infer_server_offset


def test_weekend_gap_is_not_an_intra_week_gap():
    t = pd.Series(pd.to_datetime(["2024-01-05 23:58", "2024-01-05 23:59", "2024-01-08 00:00", "2024-01-08 00:01"]))
    g = classify_gaps(t, pd.Timedelta(minutes=1))
    assert g == {**g, "gaps_total": 1, "weekend_closures": 1, "intra_week_gaps": 0}


def test_midweek_hole_is_reported_with_its_length():
    t = pd.Series(pd.to_datetime(["2024-01-10 10:00", "2024-01-10 13:00", "2024-01-10 13:01"]))
    g = classify_gaps(t, pd.Timedelta(minutes=1))
    assert g["intra_week_gaps"] == 1
    assert g["largest_intra_week_gaps_h"][0][2] == 3.0


def test_offset_evidence_reports_weekly_first_bar():
    m1 = pd.DataFrame({"time": ["2024-01-05 23:59", "2024-01-08 00:00", "2024-01-08 00:01"]})
    ev = infer_server_offset(m1)
    assert ev["n_weeks"] == 1 and ev["weekly_first_bar_server_time"] == ["Monday 00:00"]
