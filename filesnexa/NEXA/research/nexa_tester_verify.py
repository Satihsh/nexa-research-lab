"""Classify every tester run as PASSED / FAILED from its OWN evidence. Read-only.

A copied tester log holds the whole day's runs, so a bare grep for "Test passed" can
match a different run. A run PASSES only when:
  * the tester log has a "Test passed" line timestamped at/after this run's start,
    for this run's symbol, and
  * for NEXA runs, the Trade DNA's last decision_ts is within 4 days of the window
    end (weekends and NEXA's Friday cut-off allowed), i.e. the EA saw the whole window.

    python nexa_tester_verify.py tester_runs ../data/pepperstone/tester --out reports/x.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re

import pandas as pd


def run_meta(run_dir: str) -> dict:
    with open(os.path.join(run_dir, "RUN.txt")) as fh:
        txt = fh.read()
    m = dict(re.findall(r"(\w+)=(\S+)", txt))
    m["start_clock"] = re.search(r"start=\S+ (\S+)", txt).group(1)
    return m


def passed_line(run_dir: str, symbol: str, start_clock: str) -> str | None:
    p = os.path.join(run_dir, "tester.log")
    if not os.path.exists(p):
        return None
    with open(p, errors="replace") as fh:
        for line in fh:
            parts = line.split("\t")
            if len(parts) < 4 or parts[2][:8] < start_clock:
                continue
            if "Test passed" in line and f"{symbol}," in line:
                return line.strip().split("\t", 3)[-1]
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_dir")
    ap.add_argument("dna_dir")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    rep = {}
    for rd in sorted(glob.glob(os.path.join(a.runs_dir, "PS_*"))):
        name = os.path.basename(rd)
        if not os.path.exists(os.path.join(rd, "RUN.txt")):
            continue
        m = run_meta(rd)
        line = passed_line(rd, m["symbol"], m["start_clock"])
        r = {"symbol": m["symbol"], "from": m["from"], "to": m["to"], "model": m["model"],
             "tester_passed": bool(line), "evidence": line}
        if name.startswith("PS_NEXA_"):
            tag = name[len("PS_NEXA_"):]
            dna = os.path.join(a.dna_dir, f"PEPPERSTONE_NEXA_TradeDNA_{tag}.csv")
            if os.path.exists(dna):
                d = pd.read_csv(dna, usecols=["decision_ts", "event"], dtype=str)
                ts = pd.to_datetime(d.decision_ts, format="%Y.%m.%d %H:%M:%S", errors="coerce")
                last = ts.max()
                end = pd.to_datetime(m["to"], format="%Y.%m.%d")
                r.update(dna_rows=len(d), last_decision=str(last),
                         covers_window=bool(pd.notna(last) and last >= end - pd.Timedelta(days=4)))
            else:
                r.update(dna_rows=None, covers_window=False)
            r["status"] = "PASSED" if r["tester_passed"] and r["covers_window"] else "FAILED"
        else:
            r["status"] = "PASSED" if r["tester_passed"] else "FAILED"
        rep[name] = r
    with open(a.out, "w") as fh:
        json.dump(rep, fh, indent=1)
    for k, v in rep.items():
        print(f"{v['status']:6s} {k:28s} rows={v.get('dna_rows')} last={v.get('last_decision')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
