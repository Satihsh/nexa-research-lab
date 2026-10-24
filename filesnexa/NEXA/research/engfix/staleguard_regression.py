"""Stale-bar guard (2026-10-03, approved option C): ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE.

Compares the Trade DNA of the stale-guard build (staleguard/REG_STALE_GBPUSD_<W>) row by row with the
D45 baseline (regression/REG_PMFIX_GBPUSD_<W>), same windows, inputs and tester setup.

Expected: every row identical, except the decisions evaluated more than NEXA_STALE_BAR_MAX_SEC after their
bar closed, which must now read NO_TRADE_STALE_BAR (and only those). Every other row -- including every
OPEN / FILL / PARTIAL_CLOSE / CLOSE row, with its prices, P&L and R -- must be byte-identical. (The copied
tester.log holds the whole day's runs, so its "final balance" lines are not used.)

    python research/engfix/staleguard_regression.py   -> staleguard/regression_evidence.json
"""
from __future__ import annotations

import hashlib
import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BASE = os.path.join(HERE, "regression")
NEW = os.path.join(HERE, "staleguard")
WINDOWS = ["A2024Q1", "A2024Q2", "A2024Q3", "A2024Q4", "A2025Q1", "A2025Q2", "A2025Q3", "A2025Q4",
           "A2026Q1", "A2026Q2", "A2026Q3", "B"]
STALE_MAX_SEC = 6 * 3600
BAR_SEC = 60                                    # M1 entry timeframe
REASON = "NO_TRADE_STALE_BAR"


def _sha(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _dna(run_dir: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(run_dir, "dna.csv.gz"), dtype=str, keep_default_na=False)


def _is_utf16(path: str) -> bool:
    with open(path, "rb") as fh:
        return fh.read(2) in (b"\xff\xfe", b"\xfe\xff")


def _passed(run_dir: str) -> bool:
    p = os.path.join(run_dir, "tester.log")
    if not os.path.exists(p):
        return False
    with open(p, encoding="utf-16", errors="replace") if _is_utf16(p) else open(p, errors="replace") as fh:
        return "Test passed" in fh.read()


def window(w: str) -> dict:
    b_dir = os.path.join(BASE, f"REG_PMFIX_GBPUSD_{w}")
    n_dir = os.path.join(NEW, f"REG_STALE_GBPUSD_{w}")
    b, n = _dna(b_dir), _dna(n_dir)
    out = {"base_rows": len(b), "new_rows": len(n), "columns_equal": list(b.columns) == list(n.columns),
           "test_passed": _passed(n_dir)}
    if len(b) != len(n) or not out["columns_equal"]:
        out["comparable"] = False
        return out
    out["comparable"] = True
    wts = pd.to_datetime(b["write_ts"], format="%Y.%m.%d %H:%M:%S", errors="coerce")
    dts = pd.to_datetime(b["decision_ts"], format="%Y.%m.%d %H:%M:%S", errors="coerce")
    lag = (wts - dts).dt.total_seconds() - BAR_SEC
    expected = (b["event"] == "DECISION") & (lag > STALE_MAX_SEC)
    flagged = n["reason"] == REASON
    diff = b.ne(n)
    row_diff = diff.any(axis=1)
    out.update({
        "expected_stale": int(expected.sum()),
        "flagged_stale": int(flagged.sum()),
        "flagged_equals_expected": bool((flagged == expected).all()),
        "base_reasons_on_stale_rows": b.loc[expected, "reason"].str.replace(r"_state\d+|_\d+(\.\d+)?PCT", "", regex=True)
                                        .value_counts().to_dict(),
        "rows_differing_outside_stale": int((row_diff & ~expected).sum()),
        "columns_differing_on_stale_rows": sorted(c for c in b.columns if diff.loc[expected, c].any()),
        "opens_base": int((b["event"] == "OPEN").sum()), "opens_new": int((n["event"] == "OPEN").sum()),
        "stale_lag_hours_min": round(float(lag[expected].min()) / 3600, 2) if expected.any() else None,
        "max_lag_hours_not_stale": round(float(lag[(b["event"] == "DECISION") & ~expected].max()) / 3600, 2),
    })
    return out


def main() -> int:
    wins = {w: window(w) for w in WINDOWS}
    ok = [v for v in wins.values() if v.get("comparable")]
    summary = {
        "runs": len(wins), "all_test_passed": all(v["test_passed"] for v in wins.values()),
        "all_comparable": len(ok) == len(wins),
        "all_flagged_equals_expected": all(v["flagged_equals_expected"] for v in ok),
        "expected_stale_total": sum(v["expected_stale"] for v in ok),
        "flagged_stale_total": sum(v["flagged_stale"] for v in ok),
        "rows_differing_outside_stale_total": sum(v["rows_differing_outside_stale"] for v in ok),
        "columns_differing_on_stale_rows": sorted({c for v in ok for c in v["columns_differing_on_stale_rows"]}),
        "opens_identical": all(v["opens_base"] == v["opens_new"] for v in ok),
        "trade_rows_identical": all(v["rows_differing_outside_stale"] == 0 for v in ok),
    }
    ev = {"label": "ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE",
          "sources": {"NEXA_EA.mq5": _sha(os.path.join(ROOT, "NEXA_EA.mq5")),
                      "NEXA_Risk.mqh": _sha(os.path.join(ROOT, "NEXA_Risk.mqh"))},
          "stale_ex5": _sha(os.path.join(ROOT, "build", "NEXA_EA_STALE.ex5")),
          "baseline": "regression/REG_PMFIX_GBPUSD_<W> (D45 build 28e8d925, source 10b62623)",
          "stale_max_sec": STALE_MAX_SEC, "windows": wins, "summary": summary}
    with open(os.path.join(NEW, "regression_evidence.json"), "w") as fh:
        json.dump(ev, fh, indent=1)
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
