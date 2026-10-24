"""Build the V2 canonical calendar: V1 canonical rows + first_print + prior-only baselines + f1_eligible.
Deterministic; reads only the pinned raw export. Usage: python build_calendar_v2.py <export_folder> --out <dir>"""
from __future__ import annotations

import argparse
import json
import os

import nexa_calendar as nc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    t, manifest = nc.load_export(a.folder)
    t["first_print"] = nc.first_print_status(t)
    t = nc.prior_only_baselines(t)
    t["f1_eligible"] = nc.f1_eligible(t)
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "PEPPERSTONE_MT5_CALENDAR_canonical_v2.csv.gz")
    t.to_csv(path, index=False, compression={"method": "gzip", "mtime": 0})
    high = t[t["importance"].eq(3)]
    manifest.update({
        "version": 2, "canonical_v2_sha256": nc.sha256_file(path), "rows_total": len(t),
        "first_print_all": {k: int(v) for k, v in t["first_print"].value_counts().items()},
        "first_print_high": {k: int(v) for k, v in high["first_print"].value_counts().items()},
        "high_local_clock_off_prior": int(high["local_clock_off_prior"].sum()),
        "f1_eligible_rows": int(t["f1_eligible"].sum()),
        "f1_eligible_by_currency": {k: int(v) for k, v in t[t["f1_eligible"]]["currency"].value_counts().items()},
        "rules": "first_print from next release prev/revised_prev; baselines from strictly earlier releases only",
    })
    with open(os.path.join(a.out, "calendar_manifest_v2.json"), "w") as fh:
        json.dump(manifest, fh, indent=1, default=str)
    print(json.dumps({k: manifest[k] for k in ("rows_total", "first_print_high", "high_local_clock_off_prior",
                                               "f1_eligible_rows", "f1_eligible_by_currency")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
