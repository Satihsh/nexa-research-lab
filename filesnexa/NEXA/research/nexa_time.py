"""Canonical time normalisation for NEXA research. Pure, deterministic, no I/O.

Every research timestamp is converted to UTC through ONE declared server-clock
convention. Nothing in research may use a fixed GMT offset.

PEPPERSTONE_NY_CLOSE (evidence, not assumption)
  Pepperstone-Demo server time = New York local time + 7 h ("New York close": server
  midnight = 17:00 New York, all year). So server = UTC+2 while New York is on EST and
  UTC+3 while it is on EDT, switching on the US DST dates, NOT the EU dates.
  Evidence (2026-09-27, research/reports/TIME_CONVENTION_EVIDENCE.json): the FX weekly
  open is the Monday 00:01 server-time bar in EVERY week of 2024-2025, including the
  weeks between the US and EU switches (2024-03-11/18/25, 2024-10-28, 2025-03-10/17/24,
  2025-10-27), where an EU-DST server would show 23:00 Sunday or 01:00 Monday.
  Consequence for the EA: NEXA's fixed InpGMTOffset=2 is 1 h wrong from the second
  Sunday of March to the first Sunday of November (defect D-TZ; EA untouched here).

US DST rules implemented explicitly (so results do not depend on the host's tzdata):
  2007+     : second Sunday of March 02:00 local -> first Sunday of November 02:00 local
  1987-2006 : first Sunday of April 02:00 local  -> last Sunday of October 02:00 local
Cross-checked hour by hour against IANA America/New_York in test_nexa_time.py.

Server times that do not map to exactly one instant are FLAGGED, never guessed:
  NONEXISTENT : spring-forward hour (NY 02:00-03:00 -> server 09:00-10:00, a Sunday)
  AMBIGUOUS   : fall-back hour      (NY 01:00-02:00 -> server 08:00-09:00, a Sunday)
FX and metals are closed then, so market data never falls there; calendar rows might.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import numpy as np
import pandas as pd

NY_TO_SERVER = pd.Timedelta(hours=7)


@dataclass(frozen=True)
class ServerClock:
    name: str
    ny_plus_hours: int
    evidence: str


PEPPERSTONE_NY_CLOSE = ServerClock(
    "PEPPERSTONE_NY_CLOSE", 7,
    "weekly FX open = Monday 00:01 server in all 2024-2025 weeks incl. US/EU DST gap weeks")
CLOCKS = {PEPPERSTONE_NY_CLOSE.name: PEPPERSTONE_NY_CLOSE}


def _nth_sunday(year: int, month: int, n: int) -> dt.date:
    d = dt.date(year, month, 1)
    first = d + dt.timedelta(days=(6 - d.weekday()) % 7)
    return first + dt.timedelta(weeks=n - 1)


def _last_sunday(year: int, month: int) -> dt.date:
    nxt = dt.date(year + (month == 12), month % 12 + 1, 1)
    last = nxt - dt.timedelta(days=1)
    return last - dt.timedelta(days=(last.weekday() - 6) % 7)


def us_dst_bounds_local(year: int) -> tuple[dt.datetime, dt.datetime]:
    """[start, end) of US DST in NEW YORK LOCAL wall time (02:00 on both switch days)."""
    if year >= 2007:
        s, e = _nth_sunday(year, 3, 2), _nth_sunday(year, 11, 1)
    elif year >= 1987:
        s, e = _nth_sunday(year, 4, 1), _last_sunday(year, 10)
    else:
        raise ValueError("US DST rules before 1987 are not implemented")
    return dt.datetime.combine(s, dt.time(2)), dt.datetime.combine(e, dt.time(2))


def _as_series(ts) -> pd.Series:
    s = pd.Series(pd.to_datetime(ts))
    if s.dt.tz is not None:
        raise ValueError("server timestamps must be naive (broker wall-clock time)")
    return s


def classify_server_times(server_ts, clock: ServerClock = PEPPERSTONE_NY_CLOSE) -> pd.Series:
    """'OK', 'NONEXISTENT' or 'AMBIGUOUS' for each naive server timestamp."""
    s = _as_series(server_ts)
    ny = s - pd.Timedelta(hours=clock.ny_plus_hours)
    out = np.full(len(s), "OK", dtype=object)
    for y in sorted(set(ny.dt.year.dropna().astype(int))):
        start, end = us_dst_bounds_local(y)
        in_y = (ny.dt.year == y).to_numpy()
        gap = ((ny >= start) & (ny < start + pd.Timedelta(hours=1))).to_numpy()
        fold = ((ny >= end - pd.Timedelta(hours=1)) & (ny < end)).to_numpy()
        out[in_y & gap] = "NONEXISTENT"
        out[in_y & fold] = "AMBIGUOUS"
    return pd.Series(out, index=s.index)


def server_to_utc(server_ts, clock: ServerClock = PEPPERSTONE_NY_CLOSE,
                  on_invalid: str = "raise") -> pd.Series:
    """Naive server wall time -> tz-aware UTC.

    on_invalid: 'raise' (default) | 'nat' (NONEXISTENT/AMBIGUOUS -> NaT).
    """
    s = _as_series(server_ts)
    ny = s - pd.Timedelta(hours=clock.ny_plus_hours)
    offset_h = np.full(len(s), 5.0)                      # EST = UTC-5
    for y in sorted(set(ny.dt.year.dropna().astype(int))):
        start, end = us_dst_bounds_local(y)
        m = ((ny.dt.year == y) & (ny >= start) & (ny < end)).to_numpy()
        offset_h[m] = 4.0                                 # EDT = UTC-4
    utc = (ny + pd.to_timedelta(offset_h, unit="h")).dt.tz_localize("UTC")
    status = classify_server_times(s, clock)
    bad = status.ne("OK") & s.notna()
    if bad.any():
        if on_invalid == "raise":
            raise ValueError(f"{int(bad.sum())} server timestamps are NONEXISTENT/AMBIGUOUS, "
                             f"e.g. {s[bad].iloc[0]} ({status[bad].iloc[0]})")
        utc[bad] = pd.NaT
    return utc


def utc_to_server(utc_ts, clock: ServerClock = PEPPERSTONE_NY_CLOSE) -> pd.Series:
    """tz-aware (or naive-as-UTC) UTC -> naive server wall time. Always unambiguous."""
    s = pd.Series(pd.to_datetime(utc_ts))
    if s.dt.tz is None:
        s = s.dt.tz_localize("UTC")
    utc_naive = s.dt.tz_convert("UTC").dt.tz_localize(None)
    offset_h = np.full(len(s), 5.0)
    # DST in UTC: starts 07:00 UTC (02:00 EST), ends 06:00 UTC (02:00 EDT)
    for y in sorted(set(utc_naive.dt.year.dropna().astype(int))):
        start, end = us_dst_bounds_local(y)
        su, eu = start + dt.timedelta(hours=5), end + dt.timedelta(hours=4)
        m = ((utc_naive >= su) & (utc_naive < eu)).to_numpy()
        offset_h[m] = 4.0
    return utc_naive - pd.to_timedelta(offset_h, unit="h") + pd.Timedelta(hours=clock.ny_plus_hours)


def utc_offset_hours(server_ts, clock: ServerClock = PEPPERSTONE_NY_CLOSE) -> pd.Series:
    """Server-minus-UTC in hours (2 or 3 for Pepperstone) for each server timestamp."""
    s = _as_series(server_ts)
    utc = server_to_utc(s, clock, on_invalid="nat").dt.tz_localize(None)
    return ((s - utc) / pd.Timedelta(hours=1)).round(6)


WEEKEND_GAP = pd.Timedelta(hours=24)


def weekly_open_evidence(server_times, min_gap: pd.Timedelta = WEEKEND_GAP) -> pd.DataFrame:
    """First bar after each weekend gap, with the implied UTC time under the clock.
    Used to (re)verify the convention on any new dataset."""
    t = pd.Series(pd.to_datetime(server_times)).drop_duplicates().sort_values().reset_index(drop=True)
    first = t[t.diff() > min_gap].reset_index(drop=True)
    return pd.DataFrame({"server_time": first,
                         "server_clock": first.dt.strftime("%a %H:%M"),
                         "utc": server_to_utc(first, on_invalid="nat")})


def canonicalize(df: pd.DataFrame, col: str = "time", clock: ServerClock = PEPPERSTONE_NY_CLOSE,
                 fmt: str | None = None) -> pd.DataFrame:
    """Return a copy with the original server column kept verbatim plus:
       time_server (naive), time_utc (tz-aware), utc_offset_h, time_status, time_clock."""
    out = df.copy()
    srv = pd.to_datetime(out[col], format=fmt) if fmt else pd.to_datetime(out[col])
    out["time_server"] = srv
    out["time_status"] = classify_server_times(srv, clock).to_numpy()
    out["time_utc"] = server_to_utc(srv, clock, on_invalid="nat").to_numpy()
    out["utc_offset_h"] = ((srv - pd.to_datetime(out["time_utc"]).dt.tz_localize(None)) / pd.Timedelta(hours=1)).to_numpy()
    out["time_clock"] = clock.name
    return out
