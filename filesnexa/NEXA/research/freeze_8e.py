"""Freeze RESEARCH_8E_V1 (its own registry; never V2). Prints the anchor (publish it off-machine).
Usage: python freeze_8e.py [registry_root]   (default research/registry_8e)"""
from __future__ import annotations

import os
import sys

import nexa_registry2 as r2
import protocols_8e as P

HERE = os.path.dirname(os.path.abspath(__file__))
NEXA = os.path.dirname(HERE)
DATA = {**{f"m1_{s}": f"data/pepperstone/m1_canonical/PEPPERSTONE_{s}_M1_canonical.csv.gz" for s in P.SYMBOLS},
        **{f"m1_manifest_{s}": f"data/pepperstone/m1_canonical/manifest_{s}.json" for s in P.SYMBOLS},
        "spec_probe": "data/pepperstone/spec_probe/spec_probe_20261001.csv",
        "spec_probe_provenance": "data/pepperstone/spec_probe/PROVENANCE.txt"}
CODE = {m: f"research/{m}.py" for m in ["nexa_8e_engines", "nexa_8e_research", "nexa_8e_costs", "nexa_8e_capital",
                                         "nexa_8e_feasibility", "protocols_8e", "freeze_8e", "nexa_execution",
                                         "nexa_causality", "nexa_registry2", "nexa_time", "nexa_robust",
                                         "run_8e", "analyze_8e", "test_nexa_8_engines",
                                         "test_nexa_capital_velocity", "test_nexa_pepperstone_costs"]}
DESIGN = {"feasibility_audit": "research/reports/NEXA_24_5_DAILY_FEASIBILITY_AUDIT.md",
          "engine_specification": "research/reports/NEXA_8_ENGINE_SPECIFICATION.md",
          "mql5_spec_probe_source": "NEXA_SpecProbe.mq5"}


def pin(group: dict) -> dict:
    return {k: {"path": p, "sha256": r2.sha256_file(os.path.join(NEXA, p))} for k, p in sorted(group.items())}


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    root = argv[0] if argv else os.path.join(HERE, "registry_8e")
    os.makedirs(root, exist_ok=True)
    reg = r2.RegistryV2(root, nexa_root=NEXA)
    pins = {"data": pin(DATA), "code": pin(CODE), "design_artifacts": pin(DESIGN)}
    correction = {"primary": "BH-FDR q=0.10 over the 3 primary groups; DSR with N = 2160 + legacy",
                  "information": "random-subset null per engine (2000 draws), reported, not used for promotion"}
    notes = {"not_v2": "independent research campaign; V2 (6090be68...) untouched and NOT opened",
             "val_is_seen": "VAL 2023-2026 data was used by earlier NEXA work; VAL evidence is not OOS evidence",
             "pre_freeze_exploration": "XAUUSD M15 2021 (DEV) run once as a harness smoke test before freezing",
             "nas100": "BLOCKED: no local NAS100 price history",
             "superseded": {"834473f094d668c28f0ca960d891747e2b38d010a3dafd3fbade5d1d7952c673":
                            "orchestration (run_8e.py) and analysis (analyze_8e.py) pinned before opening; never opened"},
             "pre_freeze_dev_smoke": "XAUUSD H1 dc20 close_next_open k3 DEV run once (runner smoke test)"}
    anchor = reg.create_and_freeze("RESEARCH_8E_V1", P.build(), pins, P.LEGACY_TRIALS, correction, notes)
    print(anchor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
