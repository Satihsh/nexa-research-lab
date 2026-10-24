"""Freeze PHASE3_SIX_FAMILIES_V2 (FROZEN only; never opens). Prints the anchor, which must be held externally.
Usage: python freeze_phase3_v2.py [registry_root]   (default research/registry_v2)"""
from __future__ import annotations

import os
import sys

import nexa_registry2 as r2
import protocols_phase3_v2 as pv

HERE = os.path.dirname(os.path.abspath(__file__))
NEXA = os.path.dirname(HERE)

DATA = {**{f"m1_{s}": f"data/pepperstone/m1_canonical/PEPPERSTONE_{s}_M1_canonical.csv.gz" for s in pv.CORE4},
        **{f"m1_manifest_{s}": f"data/pepperstone/m1_canonical/manifest_{s}.json" for s in pv.CORE4},
        "calendar_canonical_v2": "data/pepperstone/calendar/canonical_v2/PEPPERSTONE_MT5_CALENDAR_canonical_v2.csv.gz",
        "calendar_manifest_v2": "data/pepperstone/calendar/canonical_v2/calendar_manifest_v2.json",
        "calendar_raw_values": "data/pepperstone/calendar/20260927T153535Z/NEXA_Cal_values.csv",
        "calendar_raw_events": "data/pepperstone/calendar/20260927T153535Z/NEXA_Cal_events.csv",
        "calendar_raw_provenance": "data/pepperstone/calendar/20260927T153535Z/NEXA_Cal_provenance.txt",
        "contracts_spec": "data/pepperstone/contracts.json"}
CODE_MODULES = ["nexa_time", "nexa_calendar", "nexa_execution", "nexa_m1_history", "nexa_causality", "nexa_registry2",
                "protocols_phase3_v2", "nexa_stats", "nexa_robust", "build_calendar_v2", "freeze_phase3_v2",
                "nexa_v2_features", "nexa_v2_trials", "nexa_v2_runner", "register_builders_v2",
                "test_nexa_registry2", "test_nexa_causality", "test_nexa_calendar", "test_nexa_execution",
                "test_nexa_v2_features", "test_nexa_v2_trials", "test_nexa_v2_runner", "test_nexa_time"]
CODE = {m: f"research/{m}.py" for m in CODE_MODULES}
DESIGN = {"research_design": "research/reports/RESEARCH_DESIGN_SIX_FAMILIES.md",
          "audit_v1": "research/reports/AUDIT_PHASE3_CAMPAIGN_V1.md",
          "time_convention_evidence": "research/reports/TIME_CONVENTION_EVIDENCE.json",
          "oos_determination_v2": "research/reports/OOS_DETERMINATION_V2.md",
          "external_checkpoint_procedure": "research/reports/V2_EXTERNAL_CHECKPOINT_PROCEDURE.md"}


def pin(group: dict) -> dict:
    return {k: {"path": p, "sha256": r2.sha256_file(os.path.join(NEXA, p))} for k, p in sorted(group.items())}


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    root = argv[0] if argv else os.path.join(HERE, "registry_v2")
    os.makedirs(root, exist_ok=True)
    reg = r2.RegistryV2(root, nexa_root=NEXA)
    pins = {"data": pin(DATA), "code": pin(CODE), "design_artifacts": pin(DESIGN)}
    correction = {"family_wise": "Benjamini-Hochberg FDR q=0.10 over ALL primary tests (experiment x claim x symbol)",
                  "dsr": "Deflated Sharpe with N = active trials + legacy trials (incl. every sensitivity config)",
                  "pbo": "CSCV PBO <= 0.5 on DEV/VAL trial matrix per (experiment, claim, symbol)",
                  "nulls": "intersection-union: every declared null must reject at alpha=0.05",
                  "legacy_trials_note": "108 = earlier factory/NEXA tester configurations counted against the same data"}
    notes = {"v1": "PHASE3_SIX_FAMILIES_V1 permanently REJECTED (research/registry); never opened",
             "oos": "prospective; see research/reports/OOS_DETERMINATION_V2.md",
             "blocked": "F4_CROSS_FEED_LATENCY, F6_TICK_QUOTE_IMBALANCE",
             "state_after_freeze": "FROZEN; opening requires explicit human approval",
             "superseded_pre_opening_freezes": {
                 "27b3463f5b2aa7f913701ba485946298bb128322321446631ddb406387b8485b":
                     "registry defects found by adversarial tests (A6d, A10b, X1); archive registry_v2_superseded_27b3463f",
                 "f2dc4ffb4aafe02254547811f5430f2e3b202e2ede59589282dfbe7b142b105e":
                     "feature builders, trial layer, execution hardening, sensitive-cut certification and R1 external "
                     "checkpoint added before opening; archive registry_v2_superseded_f2dc4ffb",
                 "faac4c8656ceed42c97849049cd3e8379936ed33a340844772e01849346033c0":
                     "final adversarial audit found raw (non-RegistryError) exceptions on a missing protocol file; "
                     "registry file/argument handling hardened; archive registry_v2_superseded_faac4c86",
                 "88b7688b2af5317878f9d29b81b5094cf3e5d3c788edf39639043622e4aa7197":
                     "evaluation driver (nexa_v2_runner) pinned before opening so every future result is produced by "
                     "pinned code; archive registry_v2_superseded_88b7688b"},
             "r1_control": "every mutating registry call requires the externally published ledger head "
                           "(research/reports/V2_EXTERNAL_CHECKPOINT_PROCEDURE.md)"}
    anchor = reg.create_and_freeze("PHASE3_SIX_FAMILIES_V2", pv.build(), pins, pv.LEGACY_TRIALS, correction, notes)
    print(anchor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
