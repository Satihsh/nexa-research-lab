"""Register (certify) every V2 builder into the FROZEN PHASE3_SIX_FAMILIES_V2 registry. Never opens.

Usage: python register_builders_v2.py <anchor> <seq> <entry_sha256> [registry_root]
  <seq>/<entry_sha256> = the ledger head as last PUBLISHED off-machine (R1 compare-and-swap).
Each registration appends one BUILDER_CERTIFIED event; the script prints a NEXA-CHECKPOINT line after
every event, and the final line must be published off-machine before any further ledger call.
Certification inputs are the deterministic SYNTHETIC generators in nexa_v2_features (no market data)."""
from __future__ import annotations

import os
import sys

import nexa_registry2 as r2
import nexa_v2_features as nf

HERE = os.path.dirname(os.path.abspath(__file__))


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    anchor, seq, head = argv[0], int(argv[1]), argv[2]
    root = argv[3] if len(argv) > 3 else os.path.join(HERE, "registry_v2")
    reg = r2.RegistryV2(root, nexa_root=os.path.dirname(HERE))
    cp = {"seq": seq, "entry_sha256": head}
    bars = nf.synthetic_bars()
    for name in sorted(nf.BUILDERS):
        fn, cols = nf.BUILDERS[name]
        e = reg.register_builder(anchor, fn, bars, checkpoint=cp, extra_cols=cols)
        cp = {"seq": e["seq"], "entry_sha256": e["entry_sha256"]}
        print(f"{name}: {reg.checkpoint_line(anchor, cp)}")
    e = reg.register_event_builder(anchor, nf.calendar_prior_baselines, nf.synthetic_calendar(), "time_utc",
                                   nf.CAL_PERTURB_COLS, nf.CAL_CHECK_COLS, checkpoint=cp)
    cp = {"seq": e["seq"], "entry_sha256": e["entry_sha256"]}
    print(f"calendar_prior_baselines: {reg.checkpoint_line(anchor, cp)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
