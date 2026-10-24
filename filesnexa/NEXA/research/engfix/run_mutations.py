"""Mutation tests for the D-PARTIAL-AFTER-BE fix (engineering regression, not research evidence).

Each mutant is a COPY of NEXA_PositionMgmt.mqh with one deliberate regression, compiled together with
a copy of NEXA_PositionMgmtTest.mq5 under its own unit name in build/mut/<id>/ and run in the Strategy
Tester through run_pmgmt_harness.sh. A mutant is KILLED when the harness reports at least one FAIL.
The real sources are never edited.

    python research/engfix/run_mutations.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def read(path: str) -> str:
    with open(path) as fh:
        return fh.read()


def write(path: str, text: str) -> None:
    with open(path, "w") as fh:
        fh.write(text)
MQH = "NEXA_PositionMgmt.mqh"
MUTANTS = {
    "M1_current_stop_denominator": (   # the original root cause
        "   if(hasCtx && ctxRisk > 0 && NexaFinite(ctxRisk)) return ctxRisk;\n",
        "   if(sl > 0) return MathAbs(open - sl);\n"),
    "M2_ignore_deal_history": (
        "   if(historyHasExit) return true;\n",
        ""),
    "M3_ignore_inflight_window": (
        "   if(lastAttemptAt > 0 && (double)now - lastAttemptAt <= (double)inflightTimeoutSec) return true;\n",
        ""),
    "M4_no_time_exit_after_breakeven": (
        "   if(in.timeExitBars > 0 && in.barsHeld >= in.timeExitBars && a.r < in.timeExitR) a.timeExit = true;\n",
        "   if(in.timeExitBars > 0 && in.barsHeld >= in.timeExitBars && a.r < in.timeExitR && slBelowEntry) a.timeExit = true;\n"),
    "M6_ignore_pending_close_order": (
        "   if(closeOrderPending) return true;\n",
        ""),
    "M5_partial_closes_whole_position": (
        "   if(closeV >= vmin && closeV < vol && (vol - closeV) >= vmin) return closeV;\n",
        "   if(vol >= vmin) return vol;\n"),
}


def main() -> int:
    src = read(os.path.join(ROOT, MQH))
    harness = read(os.path.join(ROOT, "NEXA_PositionMgmtTest.mq5"))
    only = set(sys.argv[1:])
    summary = os.path.join(ROOT, "research", "engfix", "runs", "mutation_summary.json")
    out = json.loads(read(summary)) if only and os.path.exists(summary) else {}
    for k, (a, b) in MUTANTS.items():
        if only and k not in only:
            continue
        assert src.count(a) == 1, f"{k}: mutation anchor not found exactly once"
        unit = "NEXA_PMMut" + k.split("_")[0][1:]
        d = os.path.join(ROOT, "build", "mut", k)
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
        write(os.path.join(d, MQH), src.replace(a, b))
        shutil.copy(os.path.join(ROOT, "NEXA_Common.mqh"), d)
        write(os.path.join(d, unit + ".mq5"), harness)
        comp = subprocess.run(["sh", "tools/compile_mql5.sh", f"build/mut/{k}/{unit}.mq5"], cwd=ROOT,
                              capture_output=True, text=True, check=False)
        if comp.returncode != 0:
            out[k] = {"compiled": False}
            continue
        res = os.path.join(ROOT, "research", "engfix", "runs", f"mut_{k}", "mql5_results.csv")
        for _attempt in range(3):          # the tester dies early at random on this machine: retry, never count as survived
            run = subprocess.run(["sh", "research/engfix/run_pmgmt_harness.sh", unit, f"mut_{k}", f"build/mut/{k}/{MQH}"],
                                 cwd=ROOT, capture_output=True, text=True, check=False,
                                 env={**os.environ, "WAIT_AGENT": "0"})
            if os.path.exists(res):
                break
        fails = []
        if os.path.exists(res):
            fails = [ln.split(",")[0] for ln in read(res).replace("\r", "").splitlines() if ln.endswith(",FAIL")]
        ran = os.path.exists(res)
        out[k] = {"compiled": True, "ran": ran, "failing_checks": fails, "killed": bool(fails),
                  "runner": run.stdout.strip()}
        print(k, "KILLED" if fails else ("SURVIVED" if ran else "NOT RUN"), fails[:6])
    with open(summary, "w") as fh:
        json.dump(out, fh, indent=1)
    return 0 if all(v.get("killed") for v in out.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
