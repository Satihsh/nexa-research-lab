"""Phase 3 data-quality audit of Pepperstone exports. Read-only: never rewrites data.

    python nexa_pepperstone_audit.py ../data/pepperstone --out reports/PEPPERSTONE_DATA_AUDIT.json

Checks per file: coverage, duplicates, non-monotonic time, OHLC geometry, weekday gap
classification (weekend closures are expected; intra-week gaps are findings),
spread realism by server hour, tick bid/ask presence and crossed quotes, and the
broker's server-time offset inferred from the weekly FX open.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os

import pandas as pd


def classify_gaps(times: pd.Series, step: pd.Timedelta) -> dict:
    """Split gaps > step into weekend closures vs intra-week gaps.

    A gap is a weekend closure when it starts on Friday or Saturday and ends on
    Sunday or Monday (server time). Everything else is an intra-week gap.
    """
    t = pd.to_datetime(times).sort_values().reset_index(drop=True)
    d = t.diff()
    idx = d[d > step].index
    starts, ends = t[idx - 1], t[idx]
    weekend = (starts.dt.dayofweek.isin([4, 5]).values & ends.dt.dayofweek.isin([6, 0]).values)
    intra = [(str(s), str(e), float((e - s) / pd.Timedelta(hours=1)))
             for s, e, w in zip(starts, ends, weekend, strict=True) if not w]
    return {"gaps_total": len(idx), "weekend_closures": int(weekend.sum()),
            "intra_week_gaps": len(intra),
            "largest_intra_week_gaps_h": sorted(intra, key=lambda x: -x[2])[:5]}


def infer_server_offset(m1: pd.DataFrame) -> dict:
    """FX reopens Sunday ~21:00-22:00 UTC. The first bar of each week in server time
    therefore reveals the server offset (GMT+2 winter / GMT+3 summer for EET/EEST)."""
    t = pd.to_datetime(m1["time"])
    gap = t.diff() > pd.Timedelta(hours=24)
    first = t[gap]
    return {"weekly_first_bar_server_time": sorted({f"{x.day_name()} {x:%H:%M}" for x in first})[:6],
            "n_weeks": int(gap.sum())}


def audit_rates(path: str, step: pd.Timedelta, point: float | None) -> dict:
    b = pd.read_csv(path)
    t = pd.to_datetime(b["time"])
    r = {"file": os.path.basename(path), "rows": len(b), "first": str(t.min()), "last": str(t.max()),
         "duplicate_times": int(t.duplicated().sum()), "non_monotonic": int((t.diff() < pd.Timedelta(0)).sum()),
         "ohlc_geometry_violations": int(((b.high < b[["open", "close"]].max(axis=1)) |
                                          (b.low > b[["open", "close"]].min(axis=1))).sum()),
         "non_positive_prices": int((b[["open", "high", "low", "close"]] <= 0).any(axis=1).sum()),
         "spread_points": {"median": float(b.spread.median()), "p95": float(b.spread.quantile(.95)),
                           "p99": float(b.spread.quantile(.99)), "max": float(b.spread.max()),
                           "zero_frac": float((b.spread == 0).mean())},
         "gaps": classify_gaps(t, step)}
    if step <= pd.Timedelta(minutes=1):
        by_h = b.groupby(t.dt.hour).spread.median()
        r["spread_points_median_by_server_hour"] = {int(k): float(v) for k, v in by_h.items()}
        r["server_time_offset_evidence"] = infer_server_offset(b)
    if point:
        r["spread_price_median"] = float(b.spread.median() * point)
    return r


def audit_ticks(path: str) -> dict:
    with gzip.open(path, "rt") as fh:
        k = pd.read_csv(fh, usecols=["time_msc", "bid", "ask", "flags"])
    t = pd.to_datetime(k.time_msc, unit="ms")
    both = (k.bid > 0) & (k.ask > 0)
    spread = (k.ask - k.bid)[both]
    return {"file": os.path.basename(path), "ticks": len(k), "first": str(t.min()), "last": str(t.max()),
            "bid_ask_both_present_frac": float(both.mean()), "crossed_quotes": int((spread < 0).sum()),
            "zero_spread_frac": float((spread == 0).mean()),
            "spread_price": {"median": float(spread.median()), "p95": float(spread.quantile(.95)),
                             "p99": float(spread.quantile(.99))},
            "non_monotonic_time": int((t.diff() < pd.Timedelta(0)).sum()),
            "duplicate_time_msc": int(k.time_msc.duplicated().sum()),
            "gaps": classify_gaps(t, pd.Timedelta(minutes=30))}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    contracts = {}
    cpath = os.path.join(a.data_dir, "contracts.json")
    if os.path.exists(cpath):
        with open(cpath) as fh:
            contracts = json.load(fh)
    rep = {"broker": "Pepperstone", "server": "Pepperstone-Demo", "data_dir": os.path.abspath(a.data_dir),
           "transformations": "none: files are read, never rewritten", "d1": {}, "m1_recent": {}, "ticks_recent": {}}
    for p in sorted(glob.glob(os.path.join(a.data_dir, "PEPPERSTONE_*_D1.csv"))):
        s = os.path.basename(p).split("_")[1]
        rep["d1"][s] = audit_rates(p, pd.Timedelta(days=1), None)
    for p in sorted(glob.glob(os.path.join(a.data_dir, "PEPPERSTONE_*_M1_recent.csv"))):
        s = os.path.basename(p).split("_")[1]
        pt = (contracts.get(s) or {}).get("point")
        rep["m1_recent"][s] = audit_rates(p, pd.Timedelta(minutes=1), pt)
    for p in sorted(glob.glob(os.path.join(a.data_dir, "PEPPERSTONE_*_ticks_recent.csv.gz"))):
        s = os.path.basename(p).split("_")[1]
        rep["ticks_recent"][s] = audit_ticks(p)
    rep["contracts"] = {s: contracts[s] for s in ("EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "XAGUSD") if s in contracts}
    with open(a.out, "w") as fh:
        json.dump(rep, fh, indent=1, default=str)
    print(json.dumps({"d1": len(rep["d1"]), "m1": list(rep["m1_recent"]), "ticks": list(rep["ticks_recent"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
