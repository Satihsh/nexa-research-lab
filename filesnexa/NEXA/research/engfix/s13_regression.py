"""S13 time-aligned USD composite (2026-10-03, approved option B): ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE.

Compares the Trade DNA of the S13 build (s13/REG_S13_GBPUSD_<W>) with the C4 baseline (c4/REG_C4_GBPUSD_<W>),
same windows, inputs and tester setup. usdCompositeDirection (f29) is journalled but never scored, so the
expected result is: EVERY column of EVERY row identical except f29 (trading provably unchanged), with f29
changing on the rows where positional and time-aligned reads disagree.

    python research/engfix/s13_regression.py   -> s13/regression_evidence.json
"""
from __future__ import annotations

import hashlib
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BASE = os.path.join(HERE, "c4")
NEW = os.path.join(HERE, "s13")
WINDOWS = ["A2024Q1", "A2024Q2", "A2024Q3", "A2024Q4", "A2025Q1", "A2025Q2", "A2025Q3", "A2025Q4",
           "A2026Q1", "A2026Q2", "A2026Q3", "B"]


def _sha(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _dna(run_dir: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(run_dir, "dna.csv.gz"), dtype=str, keep_default_na=False)


def _passed(run_dir: str) -> bool:
    p = os.path.join(run_dir, "tester.log")
    if not os.path.exists(p):
        return False
    with open(p, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-16", errors="replace") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode(errors="replace")
    return "Test passed" in text


def window(w: str) -> dict:
    b_dir, n_dir = os.path.join(BASE, f"REG_C4_GBPUSD_{w}"), os.path.join(NEW, f"REG_S13_GBPUSD_{w}")
    b, n = _dna(b_dir), _dna(n_dir)
    out = {"base_rows": len(b), "new_rows": len(n), "test_passed": _passed(n_dir),
           "columns_equal": list(b.columns) == list(n.columns)}
    if len(b) != len(n) or not out["columns_equal"]:
        out["comparable"] = False
        return out
    others = [c for c in b.columns if c != "f29"]
    dec = n["event"] == "DECISION"
    out.update({
        "comparable": True,
        "rows_differing_outside_f29": int(b[others].ne(n[others]).any(axis=1).sum()),
        "f29_changed_rows": int((b["f29"] != n["f29"]).sum()),
        "decision_rows": int(dec.sum()),
        "f29_changed_share": round(float((b["f29"] != n["f29"])[dec].mean()), 4),
        "new_f29_values": n.loc[dec, "f29"].value_counts().to_dict(),
        "opens": int((n["event"] == "OPEN").sum()),
    })
    return out


def main() -> int:
    wins = {w: window(w) for w in WINDOWS}
    ok = [v for v in wins.values() if v.get("comparable")]
    summary = {
        "runs": len(wins), "all_test_passed": all(v["test_passed"] for v in wins.values()),
        "all_comparable": len(ok) == len(wins),
        "rows_compared": sum(v["new_rows"] for v in ok),
        "rows_differing_outside_f29": sum(v["rows_differing_outside_f29"] for v in ok),
        "f29_changed_rows": sum(v["f29_changed_rows"] for v in ok),
        "decision_rows": sum(v["decision_rows"] for v in ok),
        "opens_total": sum(v["opens"] for v in ok),
    }
    summary["f29_changed_share"] = round(summary["f29_changed_rows"] / max(summary["decision_rows"], 1), 4)
    ev = {"label": "ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE",
          "sources": {n: _sha(os.path.join(ROOT, n)) for n in
                      ("NEXA_EA.mq5", "NEXA_Intelligence.mqh", "NEXA_Risk.mqh", "NEXA_Common.mqh")},
          "s13_ex5": _sha(os.path.join(ROOT, "build", "NEXA_EA_S13.ex5")),
          "baseline": "c4/REG_C4_GBPUSD_<W> (C4 build 149aa0b1, positional f29)",
          "windows": wins, "summary": summary}
    with open(os.path.join(NEW, "regression_evidence.json"), "w") as fh:
        json.dump(ev, fh, indent=1, default=lambda o: o.item() if isinstance(o, np.generic) else str(o))
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
