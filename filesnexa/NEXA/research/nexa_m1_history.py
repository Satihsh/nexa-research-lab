"""Canonical Pepperstone M1 history for research. Assembly + validation; never repairs data.

Sources (all Pepperstone-Demo, exported by NEXA_BarExport in the MT5 Strategy Tester):
  data/pepperstone/m1_history/PEPPERSTONE_<SYM>_<YYYYMMDD>_<TF>.csv.gz   2017-07 -> 2023-12
  data/pepperstone/tester/PEPPERSTONE_<SYM>_<TF>_tester_<A20..|B>.csv     2024-01 -> 2026-09
Rules
  * overlapping bars from different chunks must be IDENTICAL (open/high/low/close/spread);
    any conflict aborts the build (a mismatch means the sources disagree - never pick one)
  * time kept verbatim in server time; time_utc added only via nexa_time
  * derived higher timeframes are checked against the broker's own bars (determinism check)
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re

import pandas as pd

import nexa_time as nt

COLS = ["time", "open", "high", "low", "close", "tick_volume", "spread"]
TF_RULE = {"M5": "5min", "M15": "15min", "H1": "1h"}


class HistoryError(ValueError):
    pass


def _read(path: str) -> pd.DataFrame:
    b = pd.read_csv(path, usecols=lambda c: c in COLS)
    b["time"] = pd.to_datetime(b["time"], format="%Y.%m.%d %H:%M:%S")
    return b


def source_files(data_root: str, symbol: str, tf: str) -> list[str]:
    a = sorted(glob.glob(os.path.join(data_root, "m1_history", f"PEPPERSTONE_{symbol}_20*_{tf}.csv.gz")))
    b = [p for p in sorted(glob.glob(os.path.join(data_root, "tester", f"PEPPERSTONE_{symbol}_{tf}_tester_*.csv")))
         if re.search(r"_tester_(A20\d\dQ\d|B)\.csv$", p)]
    return a + b


def assemble(paths: list[str]) -> tuple[pd.DataFrame, dict]:
    if not paths:
        raise HistoryError("no source files")
    frames = [_read(p).assign(_src=os.path.basename(p)) for p in paths]
    allb = pd.concat(frames, ignore_index=True)
    dup = allb[allb.duplicated("time", keep=False)]
    conflicts = 0
    if len(dup):
        g = dup.groupby("time")[["open", "high", "low", "close", "spread"]].nunique()
        conflicts = int((g > 1).any(axis=1).sum())
    if conflicts:
        raise HistoryError(f"{conflicts} overlapping bars disagree between chunks")
    out = allb.drop_duplicates("time").sort_values("time").drop(columns="_src").reset_index(drop=True)
    geo = int(((out.high < out[["open", "close"]].max(axis=1)) | (out.low > out[["open", "close"]].min(axis=1))).sum())
    if geo:
        raise HistoryError(f"{geo} bars violate OHLC geometry")
    return out, {"sources": [os.path.basename(p) for p in paths], "overlap_bars": int(dup["time"].nunique()),
                 "overlap_conflicts": conflicts}


def gap_report(times: pd.Series, step: pd.Timedelta) -> dict:
    t = pd.Series(times).reset_index(drop=True)
    d = t.diff()
    idx = d[d > step].index
    s, e = t[idx - 1].reset_index(drop=True), t[idx].reset_index(drop=True)
    gh = ((e - s) / pd.Timedelta(hours=1)).round(3)
    weekend = s.dt.dayofweek.isin([4, 5]) & e.dt.dayofweek.isin([6, 0])
    long_mid = (~weekend) & (gh >= 6)                        # holidays / outages (>= 6 h inside a week)
    short_mid = (~weekend) & (gh < 6)
    return {"gaps": len(idx), "weekend": int(weekend.sum()), "intra_week_ge_6h": int(long_mid.sum()),
            "intra_week_lt_6h": int(short_mid.sum()),
            "largest_intra_week": [(str(a), str(b), float(h)) for a, b, h in
                                   sorted(zip(s[~weekend], e[~weekend], gh[~weekend], strict=True),
                                          key=lambda x: -x[2])[:5]]}


def resample_check(m1: pd.DataFrame, broker: pd.DataFrame, tf: str) -> dict:
    """Aggregate M1 in SERVER time (broker bars are server-aligned) and compare with the
    broker's own bars on their common timestamps."""
    g = m1.set_index("time").resample(TF_RULE[tf], label="left", closed="left")
    agg = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(),
                        "close": g.close.last()}).dropna().reset_index()
    j = agg.merge(broker[["time", "open", "high", "low", "close"]], on="time", suffixes=("_m1", "_broker"))
    diff = {c: int((j[f"{c}_m1"] - j[f"{c}_broker"]).abs().gt(1e-9).sum()) for c in ("open", "high", "low", "close")}
    return {"compared_bars": len(j), "mismatching_bars_by_field": diff,
            "mismatch_frac": float(max(diff.values()) / len(j)) if len(j) else float("nan")}


def build(data_root: str, symbol: str, out_dir: str) -> dict:
    m1, info = assemble(source_files(data_root, symbol, "M1"))
    c = nt.canonicalize(m1.assign(time=m1["time"].dt.strftime("%Y-%m-%d %H:%M:%S")), col="time")
    bad = c["time_status"].ne("OK")
    if bad.any():
        raise HistoryError(f"{int(bad.sum())} M1 bars fall on NONEXISTENT/AMBIGUOUS server times")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"PEPPERSTONE_{symbol}_M1_canonical.csv.gz")
    c.to_csv(path, index=False)
    with open(path, "rb") as fh:
        sha = hashlib.sha256(fh.read()).hexdigest()
    rep = {"symbol": symbol, "broker": "Pepperstone", "server": "Pepperstone-Demo", "clock": nt.PEPPERSTONE_NY_CLOSE.name,
           "rows": len(c), "first_server": str(m1.time.iloc[0]), "last_server": str(m1.time.iloc[-1]),
           "first_utc": str(c.time_utc.iloc[0]), "last_utc": str(c.time_utc.iloc[-1]),
           "canonical_file": os.path.basename(path), "canonical_sha256": sha, **info,
           "gaps": gap_report(m1["time"], pd.Timedelta(minutes=1)),
           "spread_points": {"median": float(m1.spread.median()), "p95": float(m1.spread.quantile(.95)),
                             "zero_frac": float((m1.spread == 0).mean())},
           "resample_vs_broker": {}}
    for tf in ("M5", "M15", "H1"):
        paths = source_files(data_root, symbol, tf)
        if paths:
            broker, _ = assemble(paths)
            rep["resample_vs_broker"][tf] = resample_check(m1, broker, tf)
    return rep


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("data_root")
    ap.add_argument("--symbols", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    reps = {s: build(a.data_root, s, a.out) for s in a.symbols}
    with open(os.path.join(a.out, "m1_canonical_manifest.json"), "w") as fh:
        json.dump(reps, fh, indent=1)
    for s, r in reps.items():
        print(s, r["rows"], r["first_server"], "->", r["last_server"], "overlap conflicts", r["overlap_conflicts"],
              "gaps", r["gaps"]["intra_week_ge_6h"], "resample mismatch", {k: v["mismatch_frac"] for k, v in r["resample_vs_broker"].items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
