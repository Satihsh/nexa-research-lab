"""Tests for nexa_time. Known conversions + an hour-by-hour cross-check of the explicit
US DST rules against the IANA database over 2000-2030."""
from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

import nexa_time as nt


def test_known_conversions():
    s = pd.Series(pd.to_datetime([
        "2024-01-15 10:00",   # winter: server UTC+2
        "2024-07-15 10:00",   # summer: server UTC+3
        "2024-03-18 00:01",   # US DST already on, EU not yet: UTC+3 (the evidence week)
        "2024-10-28 00:01",   # EU DST already off, US still on: UTC+3
        "2024-11-04 00:01",   # both off: UTC+2
    ]))
    utc = nt.server_to_utc(s).dt.tz_localize(None)
    assert list(utc.dt.strftime("%Y-%m-%d %H:%M")) == [
        "2024-01-15 08:00", "2024-07-15 07:00", "2024-03-17 21:01", "2024-10-27 21:01", "2024-11-03 22:01"]


def test_weekly_open_is_17_ny_all_year():
    opens = pd.Series(pd.to_datetime(["2024-03-11 00:01", "2024-03-18 00:01", "2024-11-04 00:01"]))
    ny = nt.server_to_utc(opens).dt.tz_convert("America/New_York")
    assert set(ny.dt.strftime("%a %H:%M")) == {"Sun 17:01"}


def test_round_trip_is_identity_for_valid_times():
    rng = pd.date_range("2005-01-03", "2026-09-25", freq="37min")
    srv = pd.Series(rng)
    ok = nt.classify_server_times(srv).eq("OK")
    back = nt.utc_to_server(nt.server_to_utc(srv[ok]))
    assert (back.to_numpy() == srv[ok].to_numpy()).all()


def test_explicit_rules_match_iana_every_hour_2000_2030():
    ny = ZoneInfo("America/New_York")
    utc = pd.date_range("2000-01-01", "2030-12-31 23:00", freq="h", tz="UTC")
    srv = nt.utc_to_server(pd.Series(utc))
    ref = pd.Series(utc).dt.tz_convert(ny).dt.tz_localize(None) + pd.Timedelta(hours=7)
    assert (srv.to_numpy() == ref.to_numpy()).all()


def test_pre_2007_rule():
    s, e = nt.us_dst_bounds_local(2005)
    assert s == dt.datetime(2005, 4, 3, 2) and e == dt.datetime(2005, 10, 30, 2)  # noqa: DTZ001 - naive NY wall-clock time by design
    s, e = nt.us_dst_bounds_local(2024)
    assert s == dt.datetime(2024, 3, 10, 2) and e == dt.datetime(2024, 11, 3, 2)  # noqa: DTZ001 - naive NY wall-clock time by design


def test_nonexistent_and_ambiguous_are_flagged_not_guessed():
    s = pd.Series(pd.to_datetime(["2024-03-10 09:30", "2024-11-03 08:30", "2024-11-03 09:30"]))
    assert list(nt.classify_server_times(s)) == ["NONEXISTENT", "AMBIGUOUS", "OK"]
    with pytest.raises(ValueError):
        nt.server_to_utc(s)
    got = nt.server_to_utc(s, on_invalid="nat")
    assert got.isna().tolist() == [True, True, False]


def test_tz_aware_server_input_rejected():
    with pytest.raises(ValueError):
        nt.server_to_utc(pd.Series(pd.to_datetime(["2024-01-01 10:00"]).tz_localize("UTC")))


def test_offsets_and_canonicalize_keep_original_column():
    df = pd.DataFrame({"time": ["2024.01.15 10:00:00", "2024.07.15 10:00:00"], "x": [1, 2]})
    c = nt.canonicalize(df, fmt="%Y.%m.%d %H:%M:%S")
    assert list(c["time"]) == list(df["time"])                     # original untouched
    assert c["utc_offset_h"].tolist() == [2.0, 3.0]
    assert (c["time_status"] == "OK").all() and (c["time_clock"] == "PEPPERSTONE_NY_CLOSE").all()


def test_weekly_open_evidence_reports_clock():
    t = pd.Series(pd.to_datetime(["2024-03-15 23:58", "2024-03-18 00:01", "2024-03-18 00:02"]))
    ev = nt.weekly_open_evidence(t)
    assert ev["server_clock"].tolist() == ["Mon 00:01"]
    assert np.isfinite(ev["utc"].astype("int64")).all()
