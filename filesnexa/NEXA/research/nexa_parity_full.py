"""Gate 4: FULL chronological parity on complete tester chunks. Read-only.

Stateful features (breakout memory, liquidity state machine, regimeTransitioning) are
only testable when EVERY decision row is replayed in order - a random sample breaks the
state chain and manufactures mismatches (see nexa_parity_sampled.py, stateless-only).

Pre-feature veto rows (FOMC window) carry a reset signal and a forming-bar timestamp
in the pre-fix EA; they are counted and excluded from comparison, but kept in the replay
order check.

    python nexa_parity_full.py ../data/pepperstone/tester --tags GBPUSD_B XAUUSD_B --out r.json
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
import pandas as pd

import nexa_ingest as ing
import nexa_parity as p
from nexa_parity_sampled import PRE_FEATURE_VETO, load_bars


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tester_dir")
    ap.add_argument("--tags", nargs="+", required=True)
    ap.add_argument("--contracts", required=True)
    ap.add_argument("--schema", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--accepted-ties", help="reviewed tie register (parity_accepted_ties.json)")
    a = ap.parse_args(argv)
    ties = p.load_accepted_ties(a.accepted_ties) if a.accepted_ties else ()
    with open(a.contracts) as fh:
        contracts = json.load(fh)
    rep = {}
    for tag in a.tags:
        sym, w = tag.split("_", 1)
        dna = os.path.join(a.tester_dir, f"PEPPERSTONE_NEXA_TradeDNA_{tag}.csv")
        frame = ing.load_many([dna], schema_path=a.schema).frame
        dec = frame[frame["event"].eq("DECISION")]
        veto = dec["reason"].astype(str).str.match(PRE_FEATURE_VETO)
        rows = dec[~veto].copy()
        for c in ("decision_ts", "decision_ts_effective"):
            if c in rows.columns:
                rows[c] = pd.to_datetime(rows[c], errors="coerce")
        bars = {tf: load_bars(os.path.join(a.tester_dir, f"PEPPERSTONE_{sym}_{tf}_tester_{w}.csv"))
                for tf in ("M1", "M5", "M15", "H1", "D1")}
        basket = {s: load_bars(os.path.join(a.tester_dir, f"PEPPERSTONE_{s}_M1_tester_{w}.csv"))
                  for s in p.BASKET_SYMBOLS
                  if os.path.exists(os.path.join(a.tester_dir, f"PEPPERSTONE_{s}_M1_tester_{w}.csv"))}
        if len(basket) != len(p.BASKET_SYMBOLS):
            basket = {}                                   # all four or none: f29 is then reported exempt
        r = p.run_parity(rows, p.load_market_data(bars, point=contracts[sym]["point"], basket_paths=basket),
                         p.ParityConfig(gmt_offset=2, accepted_ties=ties), events=("DECISION",))
        mm = r.mismatch_frame() if r.mismatches else pd.DataFrame(columns=["feature_name", "kind", "abs_diff", "mql5_value"])
        cont = mm[mm["kind"].astype(str).str.contains("CONTINUOUS")]
        within = cont["abs_diff"] <= 5e-7 + cont["mql5_value"].astype(float).abs() * 2 ** -23
        rep[tag] = {"decisions": len(dec), "pre_feature_veto_excluded": int(veto.sum()), "compared_rows": len(rows),
                    "contract_status": "PASS" if r.passed else "FAIL",
                    "mismatch_rate_by_feature": {k: round(v / max(len(rows), 1), 5)
                                                 for k, v in mm.groupby("feature_name").size().items()},
                    "continuous_within_journal_precision": int(within.sum()),
                    "continuous_beyond_precision": cont[~within].groupby("feature_name").size().to_dict(),
                    "accepted_ties": len(r.accepted),
                    "accepted_ties_by_feature": pd.Series([m.feature_name for m in r.accepted], dtype=object)
                                                .value_counts().to_dict(),
                    "ties_unused_in_range": r.stats.get("ties_unused_in_range", 0),
                    "features_compared": r.stats.get("features_compared"),
                    "features_exempt": r.stats.get("exempt_names")}
        with open(os.path.join(os.path.dirname(a.out), f"parity_full_{tag}.log"), "w") as fh:
            fh.write(r.report())
        if len(mm):
            mm.to_csv(os.path.join(os.path.dirname(a.out), f"parity_full_{tag}_mismatches.csv.gz"), index=False)
        print(tag, json.dumps(rep[tag]), flush=True)
    with open(a.out, "w") as fh:
        json.dump(rep, fh, indent=1, default=lambda o: o.item() if isinstance(o, np.generic) else str(o))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
