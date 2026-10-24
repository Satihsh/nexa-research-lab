"""PHASE3_SIX_FAMILIES_V2: seal OOS selections (one per experiment/claim/symbol) with the PINNED rule
nexa_v2_trials.select on the recorded VAL rows. Orchestration only, not pinned. User approval 2026-10-12: "Option A".
Usage: python seal_v2_oos.py <seq> <head>   (checkpoint as PUBLISHED off-machine)"""
import collections
import json
import os
import sys

import nexa_registry2 as r2
import nexa_v2_trials as tr

A = "6090be68184af7643f82b680d144a1b9e1622b3bbceebfb872729b97b9d9324c"
HERE = os.path.dirname(os.path.abspath(__file__))
reg = r2.RegistryV2(os.path.join(HERE, "registry_v2"), nexa_root=os.path.dirname(HERE))
cp = {"seq": int(sys.argv[1]), "entry_sha256": sys.argv[2]}
v = reg.verify(A, checkpoint=cp)
U = v["universe"]
val = collections.defaultdict(list)
for r in reg._results():
    if r["period"] != "VAL":
        continue
    t = U[r["trial_id"]]
    m = r["metrics"]
    val[(t["experiment"], t["claim"], t["symbol"])].append(
        {"trial_id": r["trial_id"], "n": m.get("n") or 0,
         "lower": m["lower"] if m.get("lower") is not None else float("nan"), "n_params": m.get("n_params")})
out = []
for g in sorted(val):
    tid = tr.select(val[g])
    if tid is None:
        print("NO SELECTABLE TRIAL (n<30 or no finite VAL lower bound):", g)
        continue
    rationale = ("pinned rule nexa_v2_trials.select on recorded VAL rows: highest VAL lower bound among trials with "
                 f"n >= {tr.MIN_TRADES_REPORT}; ties -> fewer params, then trial_id. User approval 2026-10-12 'Option A'.")
    e = reg.select_for_oos(A, tid, rationale, checkpoint=cp)
    cp = {"seq": e["seq"], "entry_sha256": e["entry_sha256"]}
    out.append({"group": list(g), "trial_id": tid, "seq": e["seq"]})
    print(f"SEALED {' '.join(g):55s} {tid}  seq {e['seq']}")
print(reg.checkpoint_line(A, cp))
with open(os.path.join(HERE, "reports", "V2_OOS_SELECTIONS.json"), "w") as fh:
    json.dump({"sealed_utc": r2._utcnow().isoformat(), "selections": out, "head": cp}, fh, indent=1)
