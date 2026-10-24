"""S11 exposure-cap fail-closed (2026-10-03, approved option A): ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE.

Compares the Trade DNA of the S11 build (s11/REG_S11_GBPUSD_<W>) row by row with the D46 baseline
(staleguard/REG_STALE_GBPUSD_<W>), same windows, inputs and tester setup.

In the Strategy Tester every open position is readable, so the fail-closed path can never fire there:
the expected result is that EVERY row is byte-identical (including every PORTFOLIO_CURRENCY_EXPOSURE_CAP
block and every trade row), with zero EXPOSURE_POSITION_UNREADABLE / EXPOSURE_CAP_INVALID_SPEC rows.
The unreadable path itself is covered statically (test_nexa_risk_s11_exposure.py).

    python research/engfix/s11_regression.py   -> s11/regression_evidence.json
"""
from __future__ import annotations

import hashlib
import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BASE = os.path.join(HERE, "staleguard")
NEW = os.path.join(HERE, "s11")
WINDOWS = ["A2024Q1", "A2024Q2", "A2024Q3", "A2024Q4", "A2025Q1", "A2025Q2", "A2025Q3", "A2025Q4",
           "A2026Q1", "A2026Q2", "A2026Q3", "B"]
NEW_REASONS = ("EXPOSURE_POSITION_UNREADABLE", "EXPOSURE_CAP_INVALID_SPEC")


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
    b_dir = os.path.join(BASE, f"REG_STALE_GBPUSD_{w}")
    n_dir = os.path.join(NEW, f"REG_S11_GBPUSD_{w}")
    b, n = _dna(b_dir), _dna(n_dir)
    out = {"base_rows": len(b), "new_rows": len(n), "columns_equal": list(b.columns) == list(n.columns),
           "test_passed": _passed(n_dir)}
    out["comparable"] = len(b) == len(n) and out["columns_equal"]
    if not out["comparable"]:
        return out
    cap = "NO_TRADE_PORTFOLIO_CURRENCY_EXPOSURE_CAP"
    out.update({
        "rows_differing": int(b.ne(n).any(axis=1).sum()),
        "exposure_cap_blocks_base": int((b["reason"] == cap).sum()),
        "exposure_cap_blocks_new": int((n["reason"] == cap).sum()),
        "new_fail_closed_rows": int(n["reason"].str.contains("|".join(NEW_REASONS), regex=True).sum()),
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
        "rows_differing_total": sum(v["rows_differing"] for v in ok),
        "exposure_cap_blocks_total": sum(v["exposure_cap_blocks_new"] for v in ok),
        "exposure_cap_blocks_identical": all(v["exposure_cap_blocks_base"] == v["exposure_cap_blocks_new"] for v in ok),
        "new_fail_closed_rows_total": sum(v["new_fail_closed_rows"] for v in ok),
        "opens_total": sum(v["opens"] for v in ok),
    }
    ev = {"label": "ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE",
          "sources": {"NEXA_EA.mq5": _sha(os.path.join(ROOT, "NEXA_EA.mq5")),
                      "NEXA_Risk.mqh": _sha(os.path.join(ROOT, "NEXA_Risk.mqh"))},
          "s11_ex5": _sha(os.path.join(ROOT, "build", "NEXA_EA_S11.ex5")),
          "baseline": "staleguard/REG_STALE_GBPUSD_<W> (D46 build fd2fe06e, NEXA_Risk 7fd5692a)",
          "windows": wins, "summary": summary}
    with open(os.path.join(NEW, "regression_evidence.json"), "w") as fh:
        json.dump(ev, fh, indent=1)
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
