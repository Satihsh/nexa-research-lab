"""PHASE3_SIX_FAMILIES_V2 in-sample driver (DEV, WF 2020-2024, VAL) - orchestration only, NOT pinned.

All results are produced by the PINNED runner (nexa_v2_runner.run_group) and written only through
nexa_v2_runner.record_all (registry compare-and-swap). This file just loads the pinned data files and
loops over periods; it has no parameters that affect any result.

Usage
  python run_v2_inSample.py --group N --anchor A --seq S --head H          # record group N (DEV + WF + VAL)
  python run_v2_inSample.py --group N --dry-run-dev                        # time DEV only, records nothing
  python run_v2_inSample.py --list
<seq>/<head> = the ledger head as last PUBLISHED off-machine. The printed NEXA-CHECKPOINT line must be
published off-machine before the next --group call. VAL/WF are never computed in --dry-run-dev.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import pickle
import sys
import time

import pandas as pd

import nexa_registry2 as r2
import nexa_v2_runner as rn
import nexa_v2_trials as tr

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
M1 = os.path.join(ROOT, "data", "pepperstone", "m1_canonical", "PEPPERSTONE_{}_M1_canonical.csv.gz")
CAL = os.path.join(ROOT, "data", "pepperstone", "calendar", "canonical_v2", "PEPPERSTONE_MT5_CALENDAR_canonical_v2.csv.gz")
CONTRACTS = os.path.join(ROOT, "data", "pepperstone", "contracts.json")
LOG = os.path.join(HERE, "reports", "V2_INSAMPLE_RUN_LOG.jsonl")


def groups(reg: r2.RegistryV2, anchor: str) -> tuple[dict, list]:
    v = reg.verify(anchor)
    g = collections.defaultdict(list)
    for t in v["universe"].values():
        g[(t["experiment"], t["claim"], t["symbol"])].append(t)
    return v, sorted(g.items())


def load_calendar() -> pd.DataFrame:
    c = pd.read_csv(CAL)
    c["time_utc"] = pd.to_datetime(c["time_utc"], utc=True)
    return c


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", type=int)
    ap.add_argument("--anchor", default="6090be68184af7643f82b680d144a1b9e1622b3bbceebfb872729b97b9d9324c")
    ap.add_argument("--seq", type=int)
    ap.add_argument("--head")
    ap.add_argument("--dry-run-dev", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--compute-only", help="run the pinned run_group for all periods and pickle the records here")
    ap.add_argument("--record-from", help="record a pickle written by --compute-only (same group) via record_all")
    a = ap.parse_args(argv)
    reg = r2.RegistryV2(os.path.join(HERE, "registry_v2"), nexa_root=ROOT)
    v, gl = groups(reg, a.anchor)
    if a.list:
        for i, (k, ts) in enumerate(gl):
            print(i, k, len(ts))
        return 0
    (exp, claim, sym), trials = gl[a.group]
    proto = v["protocols"][exp]
    t0 = time.time()
    if a.record_from:
        with open(a.record_from, "rb") as fh:
            saved = pickle.load(fh)
        if saved["group"] != a.group or saved["key"] != [exp, claim, sym]:
            raise SystemExit("pickle does not belong to this group")
        return _record(reg, a, exp, claim, sym, saved["recs"], t0)
    bars = rn.load_m1(M1.format(sym))
    bars, info = rn.prepare(bars, load_calendar(), sym, exp)
    contracts = tr.load_contracts(CONTRACTS)
    print(f"[{a.group}] {exp} {claim} {sym}: {len(trials)} trials; bars {len(bars):,}; prepare {info}; "
          f"load {time.time() - t0:.0f}s", flush=True)
    plan = [("DEV", None)] if a.dry_run_dev else \
        [("DEV", None)] + [("WF", y) for y in proto["periods_utc"]["WF_YEARS"]] + [("VAL", None)]
    recs = []
    for period, y in plan:
        t1 = time.time()
        out = rn.run_group(proto, claim, sym, period, bars, contracts, trials, wf_year=y)
        n_tr = [r["metrics"].get("n", 0) for r in out]
        print(f"  {period}{'' if y is None else ' ' + str(y)}: {len(out)} records, trades median "
              f"{int(pd.Series(n_tr).median())}, max {max(n_tr)}; {time.time() - t1:.0f}s", flush=True)
        recs += out
    if a.dry_run_dev:
        print(f"DRY RUN (DEV only, nothing recorded); total {time.time() - t0:.0f}s")
        return 0
    if a.compute_only:
        with open(a.compute_only, "wb") as fh:
            pickle.dump({"group": a.group, "key": [exp, claim, sym], "recs": recs}, fh)
        print(f"COMPUTED {len(recs)} records (not recorded) -> {a.compute_only}; total {time.time() - t0:.0f}s")
        return 0
    return _record(reg, a, exp, claim, sym, recs, t0)


def _record(reg, a, exp, claim, sym, recs, t0) -> int:
    if a.seq is None or not a.head:
        raise SystemExit("--seq/--head (published off-machine) are required to record")
    t2 = time.time()
    cp = rn.record_all(reg, a.anchor, {"seq": a.seq, "entry_sha256": a.head}, recs)
    line = reg.checkpoint_line(a.anchor, cp)
    with open(LOG, "a") as fh:
        fh.write(json.dumps({"group": a.group, "key": [exp, claim, sym], "records": len(recs),
                             "seq": cp["seq"], "head": cp["entry_sha256"], "utc": r2._utcnow().isoformat(),
                             "seconds": round(time.time() - t0)}) + "\n")
    print(f"RECORDED {len(recs)} in {time.time() - t2:.0f}s; total {time.time() - t0:.0f}s")
    print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
