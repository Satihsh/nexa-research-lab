"""Gate 4 on the Pepperstone batch: sampled parity across every tester chunk. Read-only.

For each chunk: ingest the Trade DNA (Stage 2), draw a SEEDED sample of DECISION rows,
and run the parity oracle against the broker's own M1/M5/M15/H1/D1 bars exported by
NEXA_BarExport under the identical tester configuration.

Reported two ways, never blended:
  * CONTRACT: nexa_parity's own tolerance (rel<=1e-6 or abs<=1e-9), unchanged.
  * PRECISION-AWARE (diagnostic only): a continuous mismatch is "within journal
    precision" when |diff| <= 5e-7 + |mql5| * 2^-23, i.e. explained by the Trade DNA's
    6-decimal text and float32 packing. This does NOT redefine the contract.
Pre-feature veto rows (FOMC window) carry a reset signal by construction and are
excluded from the sample and counted separately.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re

import numpy as np
import pandas as pd

import nexa_ingest as ing
import nexa_parity as p

PRE_FEATURE_VETO = re.compile(r"^NO_TRADE_FOMC")


def load_bars(path: str) -> str:
    """MT5 writes 'YYYY.MM.DD HH:MM:SS'; write an ISO copy next to it (original untouched)."""
    iso = path[:-4] + ".iso.csv"
    if not os.path.exists(iso):
        b = pd.read_csv(path)
        b["time"] = pd.to_datetime(b["time"], format="%Y.%m.%d %H:%M:%S").dt.strftime("%Y-%m-%d %H:%M:%S")
        b.to_csv(iso, index=False)
    return iso


def chunk_parity(dna: str, bars: dict, point: float, n: int, seed: int, schema: str) -> dict:
    frame = ing.load_many([dna], schema_path=schema).frame
    dec = frame[frame["event"].eq("DECISION")]
    veto = dec["reason"].astype(str).str.match(PRE_FEATURE_VETO)
    pool = dec[~veto]
    sample = pool.sample(min(n, len(pool)), random_state=seed)
    for c in ("decision_ts", "decision_ts_effective"):
        if c in sample.columns:
            sample[c] = pd.to_datetime(sample[c], errors="coerce")
    data = p.load_market_data({tf: load_bars(pth) for tf, pth in bars.items()}, point=point)
    r = p.run_parity(sample, data, p.ParityConfig(gmt_offset=2), events=("DECISION",))
    mm = r.mismatch_frame() if r.mismatches else pd.DataFrame()
    out = {"decisions": len(dec), "pre_feature_veto_excluded": int(veto.sum()), "sampled": len(sample),
           "contract_status": "PASS" if r.passed else "FAIL", "contract_mismatches": len(mm)}
    if len(mm):
        cont = mm[mm["kind"].astype(str).str.contains("CONTINUOUS")]
        q = 5e-7 + cont["mql5_value"].astype(float).abs() * 2 ** -23
        within = cont["abs_diff"] <= q
        out["by_feature"] = mm.groupby("feature_name").size().to_dict()
        out["continuous_within_journal_precision"] = int(within.sum())
        out["continuous_beyond_precision_by_feature"] = cont[~within].groupby("feature_name").size().to_dict()
        out["categorical_by_feature"] = mm[~mm["kind"].astype(str).str.contains("CONTINUOUS")].groupby("feature_name").size().to_dict()
    out["_report"] = r.report()
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tester_dir")
    ap.add_argument("--contracts", required=True)
    ap.add_argument("--schema", required=True)
    ap.add_argument("--per-chunk", type=int, default=500)
    ap.add_argument("--seed", type=int, default=20260927)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    with open(a.contracts) as fh:
        contracts = json.load(fh)
    rep = {"method": __doc__, "seed": a.seed, "per_chunk": a.per_chunk, "chunks": {}}
    for dna in sorted(glob.glob(os.path.join(a.tester_dir, "PEPPERSTONE_NEXA_TradeDNA_*_[AB]*.csv"))):
        tag = os.path.basename(dna)[len("PEPPERSTONE_NEXA_TradeDNA_"):-4]
        sym, w = tag.split("_", 1)
        bars = {tf: os.path.join(a.tester_dir, f"PEPPERSTONE_{sym}_{tf}_tester_{w}.csv") for tf in ("M1", "M5", "M15", "H1", "D1")}
        if not all(os.path.exists(v) for v in bars.values()):
            rep["chunks"][tag] = {"error": "bars missing"}
            continue
        r = chunk_parity(dna, bars, contracts[sym]["point"], a.per_chunk, a.seed, a.schema)
        rep["chunks"][tag] = {k: v for k, v in r.items() if k != "_report"}
        print(tag, r["contract_status"], r["sampled"], r.get("by_feature", {}), flush=True)
    agg: dict = {}
    for v in rep["chunks"].values():
        for k, c in v.get("by_feature", {}).items():
            agg[k] = agg.get(k, 0) + c
    rep["total_sampled"] = sum(v.get("sampled", 0) for v in rep["chunks"].values())
    rep["mismatches_by_feature_total"] = dict(sorted(agg.items(), key=lambda x: -x[1]))
    rep["continuous_within_journal_precision_total"] = sum(v.get("continuous_within_journal_precision", 0) for v in rep["chunks"].values())
    with open(a.out, "w") as fh:
        json.dump(rep, fh, indent=1, default=lambda o: o.item() if isinstance(o, np.generic) else str(o))
    print(json.dumps({k: rep[k] for k in ("total_sampled", "mismatches_by_feature_total",
                                          "continuous_within_journal_precision_total")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
