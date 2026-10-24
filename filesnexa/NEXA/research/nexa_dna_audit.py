"""Phase 7 Trade DNA audit across tester chunks. Read-only.

    python nexa_dna_audit.py ../data/pepperstone/tester --glob 'PEPPERSTONE_NEXA_TradeDNA_*_A20*.csv' --out reports/x.json

Checks, per file and aggregated:
  * decisions / trades (OPEN, FILL, CLOSE) / NO_TRADE by reason family
  * causality: decision_ts is the open time of the CLOSED bar, i.e. strictly before
    write_ts, and on M1 exactly one bar earlier (write_ts - decision_ts == 60 s for
    DECISION rows, allowing weekend/session gaps as > 60 s but never <= 0)
  * f00..f47 present, finite, and not constant (a constant feature carries nothing)
  * execution rows carry entry/SL/TP/lots/slippage/commission; CLOSE rows carry result_r
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re

import numpy as np
import pandas as pd

FEATURES = [f"f{i:02d}" for i in range(48)]


def reason_family(reason: str) -> str:
    r = str(reason)
    if not r or r == "nan":
        return "EMPTY"
    r = re.sub(r"_-?\d+(\.\d+)?(PCT)?$", "", r)          # strip trailing numeric payload
    r = re.sub(r"_\d{8}_.*$", "", r)                      # FOMC_WINDOW_YYYYMMDD_KIND
    parts = r.split("_")
    return "_".join(parts[:4])


def audit_frame(df: pd.DataFrame) -> dict:
    dt = pd.to_datetime(df["decision_ts"], format="%Y.%m.%d %H:%M:%S", errors="coerce")
    wt = pd.to_datetime(df["write_ts"], format="%Y.%m.%d %H:%M:%S", errors="coerce")
    dec = df["event"].eq("DECISION")
    lag = (wt - dt)[dec & dt.notna() & wt.notna()]
    feats = df.loc[dec, FEATURES].apply(pd.to_numeric, errors="coerce")
    out = {
        "rows": len(df),
        "events": df["event"].value_counts().to_dict(),
        "decision_ts_range": [str(dt[dec].min()), str(dt[dec].max())],
        "causality": {
            "decision_rows_checked": len(lag),
            "lag_not_positive": int((lag <= pd.Timedelta(0)).sum()),
            "lag_exactly_one_bar": int((lag == pd.Timedelta(minutes=1)).sum()),
            "lag_over_one_bar": int((lag > pd.Timedelta(minutes=1)).sum()),
            "epoch_decision_ts_rows": int((dt.dt.year == 1970).sum()),
        },
        "features": {
            "missing_columns": [f for f in FEATURES if f not in df.columns],
            "non_finite_values": int((~np.isfinite(feats.to_numpy(dtype=float))).sum()),
            "constant_features": [f for f in FEATURES if feats[f].nunique(dropna=True) <= 1],
        },
        "no_trade_reasons": (df.loc[dec, "reason"].map(reason_family).value_counts().head(25).to_dict()),
    }
    ex = df[df["event"].isin(["OPEN", "FILL", "CLOSE", "PARTIAL_CLOSE"])]
    if len(ex):
        cols = ["entry_intended", "entry_actual", "sl_price", "tp_price", "lots", "slippage_points", "commission", "result_r"]
        out["execution_rows_missing"] = {c: int(pd.to_numeric(ex[c], errors="coerce").isna().sum()) for c in cols if c in ex}
        closes = pd.to_numeric(df.loc[df["event"].eq("CLOSE"), "result_r"], errors="coerce").dropna()
        out["closed_trades"] = len(closes)
        out["result_r_sum"] = float(closes.sum())
    else:
        out["closed_trades"] = 0
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir")
    ap.add_argument("--glob", default="PEPPERSTONE_NEXA_TradeDNA_*.csv")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    files = sorted(glob.glob(os.path.join(a.data_dir, a.glob)))
    rep = {"files": {}, "totals": {}}
    tot_dec = tot_trades = tot_rows = 0
    fam_tot: dict = {}
    for p in files:
        df = pd.read_csv(p, dtype=str, keep_default_na=False)
        r = audit_frame(df)
        rep["files"][os.path.basename(p)] = r
        tot_rows += r["rows"]
        tot_dec += r["events"].get("DECISION", 0)
        tot_trades += r["closed_trades"]
        for k, v in r["no_trade_reasons"].items():
            fam_tot[k] = fam_tot.get(k, 0) + v
    rep["totals"] = {"files": len(files), "rows": tot_rows, "decisions": tot_dec, "closed_trades": tot_trades,
                     "no_trade_reason_families": dict(sorted(fam_tot.items(), key=lambda x: -x[1]))}
    with open(a.out, "w") as fh:
        json.dump(rep, fh, indent=1, default=str)
    print(json.dumps(rep["totals"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
