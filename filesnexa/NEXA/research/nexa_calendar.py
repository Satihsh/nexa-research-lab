"""Canonical MT5 economic calendar for research. Ingest + provenance + validation only.

Input: the four files written by NEXA_CalendarExport.mq5 (Common\\Files). Output: one
canonical table, one row per calendar VALUE. No feature (surprise, z-score, ...) is
computed here: that is Phase-3 work under a frozen protocol.

CALENDAR TIME BASIS (empirical, 2026-09-27; see calendar_manifest.json)
  CalendarValueHistory stamps EVERY historical value with the trade server's UTC offset
  AT EXPORT TIME, not the offset valid on the event date. Evidence: US Nonfarm Payrolls
  (08:30 New York, all year) appears at 15:30 in US-DST months and 16:30 in winter months
  of an export taken in summer (offset +3). Therefore:
      time_utc    = time_calendar_text - export_offset   (export_offset from provenance:
                                                          export_time_trade_server - export_time_gmt)
      time_server = nexa_time.utc_to_server(time_utc)    (bar-clock aligned, for joins with bars)
  Using the bar clock (nexa_time.server_to_utc) on calendar text would shift every
  opposite-season event by one hour. Validation: each recurring event's release clock is
  checked in its OWN country's local time; rows off the event's modal local clock are
  flagged (local_clock_off_mode), never corrected.

Semantics carried into the table (never silently dropped)
  time_mode      0 DATETIME (exact) | 1 DATE (all day) | 2 NOTIME | 3 TENTATIVE
                 -> timestamp_exact is True only for DATETIME
  importance     0 NONE | 1 LOW | 2 MODERATE | 3 HIGH
  actual/forecast/prev/revised_prev: NaN when MT5 had no value (never 0)
  revision_caveat: the export reflects the calendar state at export time. The forecast
                 and prev values AS KNOWN BEFORE the release are not reconstructable;
                 any feature built on them must carry this caveat.
Look-ahead rule for Phase 3: `actual` may be used only at or after time_utc.
"""
from __future__ import annotations

import hashlib
import json
import os

import numpy as np
import pandas as pd

import nexa_time as nt

ENCODING = "cp1252"   # MQL5 FILE_ANSI writes the Windows ANSI code page (e.g. 0x80 = EUR sign), not UTF-8
FILES = ("NEXA_Cal_countries.csv", "NEXA_Cal_events.csv", "NEXA_Cal_values.csv", "NEXA_Cal_provenance.txt")
TIME_MODES = {0: "DATETIME", 1: "DATE", 2: "NOTIME", 3: "TENTATIVE"}
IMPORTANCE = {0: "NONE", 1: "LOW", 2: "MODERATE", 3: "HIGH"}


class CalendarError(ValueError):
    pass


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_provenance(path: str) -> dict:
    out = {}
    with open(path, encoding=ENCODING) as fh:
        for line in fh:
            if "=" in line:
                k, v = line.rstrip("\r\n").split("=", 1)
                out[k.strip()] = v.strip()
    return out


COUNTRY_TZ = {"US": "America/New_York", "EU": "Europe/Berlin", "DE": "Europe/Berlin", "FR": "Europe/Paris",
              "IT": "Europe/Rome", "ES": "Europe/Madrid", "GB": "Europe/London", "JP": "Asia/Tokyo",
              "CA": "America/Toronto", "AU": "Australia/Sydney", "NZ": "Pacific/Auckland", "CH": "Europe/Zurich",
              "CN": "Asia/Shanghai", "HK": "Asia/Hong_Kong", "SG": "Asia/Singapore", "NO": "Europe/Oslo",
              "SE": "Europe/Stockholm", "KR": "Asia/Seoul", "IN": "Asia/Kolkata", "BR": "America/Sao_Paulo",
              "MX": "America/Mexico_City", "ZA": "Africa/Johannesburg"}


def export_offset(prov: dict) -> pd.Timedelta:
    """Trade-server minus GMT at export, rounded to 15 min (the basis of every calendar stamp)."""
    srv = pd.to_datetime(prov["export_time_trade_server"], format="%Y.%m.%d %H:%M:%S")
    gmt = pd.to_datetime(prov["export_time_gmt"], format="%Y.%m.%d %H:%M:%S")
    return pd.Timedelta(minutes=15 * round((srv - gmt) / pd.Timedelta(minutes=15)))


def load_export(folder: str, expect_server: str = "Pepperstone-Demo") -> tuple[pd.DataFrame, dict]:
    paths = {f: os.path.join(folder, f) for f in FILES}
    missing = [f for f, p in paths.items() if not os.path.exists(p)]
    if missing:
        raise CalendarError(f"calendar export incomplete, missing {missing}")
    prov = read_provenance(paths["NEXA_Cal_provenance.txt"])
    if prov.get("server") != expect_server:
        raise CalendarError(f"export came from server {prov.get('server')!r}, expected {expect_server!r}")
    c = pd.read_csv(paths["NEXA_Cal_countries.csv"], encoding=ENCODING)
    e = pd.read_csv(paths["NEXA_Cal_events.csv"], encoding=ENCODING)
    v = pd.read_csv(paths["NEXA_Cal_values.csv"], encoding=ENCODING)
    for name, df, n_key in (("countries", c, "countries"), ("events", e, "events"), ("values", v, "values")):
        if n_key in prov and int(prov[n_key]) != len(df):
            raise CalendarError(f"{name}: provenance says {prov[n_key]} rows, file has {len(df)}")
    off = export_offset(prov)
    manifest = {"provenance": prov, "sha256": {f: sha256_file(p) for f, p in paths.items()},
                "rows": {"countries": len(c), "events": len(e), "values": len(v)},
                "calendar_time_basis": f"FIXED_EXPORT_OFFSET {off}"}
    return canonical_table(c, e, v, off), manifest


def canonical_table(c: pd.DataFrame, e: pd.DataFrame, v: pd.DataFrame, offset: pd.Timedelta) -> pd.DataFrame:
    if v["id"].duplicated().any():
        raise CalendarError(f"{int(v['id'].duplicated().sum())} duplicate value ids")
    orphan = ~v["event_id"].isin(e["id"])
    if orphan.any():
        raise CalendarError(f"{int(orphan.sum())} values reference unknown events")
    ev = e.rename(columns={"id": "event_id", "name": "event_name"})
    co = c.rename(columns={"id": "country_id", "name": "country_name", "code": "country_code"})
    t = v.merge(ev, on="event_id", how="left").merge(co[["country_id", "country_name", "country_code", "currency"]],
                                                     on="country_id", how="left")
    t = t.rename(columns={"time_server": "time_server_text"})           # verbatim MT5 text kept
    cal_naive = pd.to_datetime(t["time_server_text"], format="%Y.%m.%d %H:%M:%S")
    t["time_utc"] = (cal_naive - offset).dt.tz_localize("UTC")
    t["time_server"] = nt.utc_to_server(t["time_utc"]).to_numpy()      # bar clock, for joins with bars
    t["time_status"] = "OK"
    t["calendar_time_basis"] = f"FIXED_EXPORT_OFFSET {offset}"
    t["time_mode_name"] = t["time_mode"].map(TIME_MODES).fillna("UNKNOWN")
    t["importance_name"] = t["importance"].map(IMPORTANCE).fillna("UNKNOWN")
    t["timestamp_exact"] = t["time_mode"].eq(0) & t["time_status"].eq("OK")
    for col in ("actual", "prev", "revised_prev", "forecast"):
        t[col] = pd.to_numeric(t[col], errors="coerce")
    t["revision_caveat"] = "calendar state at export time; pre-release forecast/prev not reconstructable"
    t = t.sort_values(["time_utc", "event_id", "id"], kind="mergesort").reset_index(drop=True)
    return flag_local_clock(t)


def flag_local_clock(t: pd.DataFrame, min_releases: int = 12) -> pd.DataFrame:
    """For every exact-timestamp event with >= min_releases, compute the release clock in the
    event's own country time zone; flag rows whose local clock differs from that event's mode."""
    t = t.copy()
    t["local_clock"] = pd.Series(None, index=t.index, dtype="object")
    t["local_clock_off_mode"] = False
    for code, tz in COUNTRY_TZ.items():
        m = t["country_code"].eq(code) & t["timestamp_exact"]
        if m.any():
            t.loc[m, "local_clock"] = pd.to_datetime(t.loc[m, "time_utc"]).dt.tz_convert(tz).dt.strftime("%H:%M").to_numpy()
    ok = t["local_clock"].notna()
    counts = t[ok].groupby("event_id")["local_clock"].agg(["size", lambda x: x.mode().iloc[0]])
    counts.columns = ["n", "mode"]
    big = counts[counts["n"] >= min_releases]
    mode = t["event_id"].map(big["mode"])
    t["local_clock_off_mode"] = (ok & mode.notna() & t["local_clock"].fillna("").ne(mode.fillna(""))).astype(bool)
    return t


def release_clock_check(t: pd.DataFrame, event_code: str, currency: str) -> dict:
    """Server-time and New-York-time clock of every release of one event, split by US DST.
    For a New-York-scheduled release (e.g. US NFP 08:30 ET) the NY clock must be constant
    all year; under the NY+7 server convention the SERVER clock must be constant too."""
    m = t["event_code"].astype(str).str.strip('"').eq(event_code) & t["currency"].eq(currency) & t["timestamp_exact"]
    x = t[m]
    if not len(x):
        return {"event_code": event_code, "releases": 0}
    ny = pd.to_datetime(x["time_utc"]).dt.tz_convert("America/New_York")
    dst = ny.map(lambda z: bool(z.dst()))
    srv = pd.to_datetime(x["time_server"]).dt.strftime("%H:%M")
    off = x[x["local_clock_off_mode"]]
    return {"event_code": event_code, "releases": len(x),
            "server_clock_by_us_dst": {str(k): {a: int(b) for a, b in srv[dst == k].value_counts().items()} for k in (True, False)},
            "new_york_clock": {a: int(b) for a, b in ny.dt.strftime("%H:%M").value_counts().items()},
            "off_mode_rows": off["time_server_text"].tolist(),
            "first": str(x["time_server"].min()), "last": str(x["time_server"].max())}


def summarize(t: pd.DataFrame) -> dict:
    hi = t["importance"].eq(3)
    return {"values": len(t), "events": int(t["event_id"].nunique()),
            "range_utc": [str(t["time_utc"].min()), str(t["time_utc"].max())],
            "time_status": t["time_status"].value_counts().to_dict(),
            "time_mode": t["time_mode_name"].value_counts().to_dict(),
            "high_importance_values": int(hi.sum()),
            "high_importance_exact_by_currency": t[hi & t["timestamp_exact"]]["currency"].value_counts().head(12).to_dict(),
            "actual_missing_frac_high": float(t.loc[hi, "actual"].isna().mean()) if hi.any() else np.nan,
            "forecast_missing_frac_high": float(t.loc[hi, "forecast"].isna().mean()) if hi.any() else np.nan,
            "local_clock_checked_rows": int(t["local_clock"].notna().sum()),
            "local_clock_off_mode_rows": int(t["local_clock_off_mode"].sum()),
            "local_clock_off_mode_high": int((t["local_clock_off_mode"] & hi).sum())}


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--out", required=True, help="output folder")
    a = ap.parse_args(argv)
    t, manifest = load_export(a.folder)
    os.makedirs(a.out, exist_ok=True)
    t.to_csv(os.path.join(a.out, "PEPPERSTONE_MT5_CALENDAR_canonical.csv.gz"), index=False)
    manifest["summary"] = summarize(t)
    manifest["nfp_clock_check"] = release_clock_check(t, "nonfarm-payrolls", "USD")
    manifest["canonical_sha256"] = sha256_file(os.path.join(a.out, "PEPPERSTONE_MT5_CALENDAR_canonical.csv.gz"))
    with open(os.path.join(a.out, "calendar_manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=1, default=str)
    print(json.dumps({k: manifest[k] for k in ("rows", "summary", "nfp_clock_check")}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# ---------------------------------------------------------------- V2: provenance + prior-only baselines

FIRST_PRINT = ("CONFIRMED", "REVISED_VALUE", "UNDETERMINED")


def first_print_status(t: pd.DataFrame, rtol: float = 1e-9, atol: float = 1e-9) -> pd.Series:
    """CONFIRMED     actual == the NEXT release's `prev` (the first print was kept);
       REVISED_VALUE actual == the NEXT release's `revised_prev` while that differs from its `prev`;
       UNDETERMINED  anything else, incl. the latest release of an event (no successor yet) or
                     missing actual. Only CONFIRMED rows are eligible for surprise features.
    This is a data-PROVENANCE filter decided by the release sequence, never by prices."""
    x = t.sort_values(["event_id", "time_utc", "id"], kind="mergesort")
    nxt_prev = x.groupby("event_id")["prev"].shift(-1)
    nxt_rev = x.groupby("event_id")["revised_prev"].shift(-1)
    a = x["actual"]
    conf = a.notna() & nxt_prev.notna() & np.isclose(a, nxt_prev, rtol=rtol, atol=atol)
    diff_rev = nxt_rev.notna() & ~np.isclose(nxt_rev, nxt_prev.fillna(np.inf), rtol=rtol, atol=atol)
    rev = ~conf & a.notna() & diff_rev & np.isclose(a, nxt_rev, rtol=rtol, atol=atol)
    out = pd.Series("UNDETERMINED", index=x.index, dtype=object)
    out[conf] = "CONFIRMED"
    out[rev] = "REVISED_VALUE"
    return out.reindex(t.index)


def prior_only_baselines(t: pd.DataFrame, min_prior: int = 12) -> pd.DataFrame:
    """Per event, using ONLY releases strictly before each row (causal):
      prior_n                 number of earlier exact releases
      prior_modal_clock       modal local release clock of earlier releases (None if < min_prior)
      local_clock_off_prior   row's local clock differs from prior_modal_clock
      prior_surprise_sd       std of (actual - forecast) over earlier CONFIRMED releases (NaN if < min_prior)
    Replaces V1's full-sample mode (which used information after the event)."""
    t = t.copy()
    if "first_print" not in t.columns:
        t["first_print"] = first_print_status(t)
    t["prior_n"] = 0
    t["prior_modal_clock"] = pd.Series(None, index=t.index, dtype=object)
    t["prior_surprise_sd"] = np.nan
    order = t.sort_values(["event_id", "time_utc", "id"], kind="mergesort").index
    import collections
    cur_event, counts, n, surprises = None, collections.Counter(), 0, []
    pn, pm, psd = {}, {}, {}
    for i in order:
        ev = t.at[i, "event_id"]
        if ev != cur_event:
            cur_event, counts, n, surprises = ev, collections.Counter(), 0, []
        pn[i] = n
        pm[i] = counts.most_common(1)[0][0] if n >= min_prior and counts else None
        psd[i] = float(np.std(surprises, ddof=1)) if len(surprises) >= min_prior else np.nan
        clk = t.at[i, "local_clock"]
        if t.at[i, "timestamp_exact"] and isinstance(clk, str):
            counts[clk] += 1
            n += 1
        if t.at[i, "first_print"] == "CONFIRMED" and pd.notna(t.at[i, "forecast"]):
            surprises.append(float(t.at[i, "actual"]) - float(t.at[i, "forecast"]))
    t["prior_n"] = pd.Series(pn)
    t["prior_modal_clock"] = pd.Series(pm)
    t["prior_surprise_sd"] = pd.Series(psd)
    t["local_clock_off_prior"] = t["prior_modal_clock"].notna() & t["local_clock"].notna() & \
        t["local_clock"].astype(str).ne(t["prior_modal_clock"].astype(str))
    return t


def f1_eligible(t: pd.DataFrame, min_prior: int = 12) -> pd.Series:
    """The frozen F1 event filter (V2): HIGH importance, MT5 type INDICATOR (1), exact DATETIME,
    first print CONFIRMED, forecast present, >= min_prior earlier releases, local clock equal to
    the PRIOR-ONLY modal clock, and a prior-only surprise sd available."""
    return (t["importance"].eq(3) & t["type"].eq(1) & t["timestamp_exact"] & t["first_print"].eq("CONFIRMED")
            & t["forecast"].notna() & t["prior_n"].ge(min_prior) & ~t["local_clock_off_prior"]
            & t["prior_surprise_sd"].notna() & t["prior_surprise_sd"].gt(0))
