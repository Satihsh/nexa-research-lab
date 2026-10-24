"""D-TZ DST-aware server clock (2026-10-03, approved option A): ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE.

Compares the Trade DNA of the D-TZ build (dtz/REG_DTZ_GBPUSD_<W>) with the S11 baseline
(s11/REG_S11_GBPUSD_<W>, fixed GMT+2 clock), same windows, inputs and tester setup.

Runtime proof of the clock: SessionTag() is computed from the EA's clock at EVALUATION time (write_ts).
For every journalled tag, the D-TZ build must agree with the true clock (research/nexa_time.py rule via
nexa_parity.server_gmt_offset_hours) and the S11 baseline with the old fixed +2 clock.

Behaviour change is EXPECTED (US-DST months): reported, not asserted away -- decisions differing, trades,
the first divergence, and trades that the corrected LATE veto (21-24 GMT) now blocks.

    python research/engfix/dtz_regression.py   -> dtz/regression_evidence.json
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "research"))
from nexa_parity import server_gmt_offset_hours

BASE = os.path.join(HERE, "s11")
NEW = os.path.join(HERE, "dtz")
WINDOWS = ["A2024Q1", "A2024Q2", "A2024Q3", "A2024Q4", "A2025Q1", "A2025Q2", "A2025Q3", "A2025Q4",
           "A2026Q1", "A2026Q2", "A2026Q3", "B"]
FMT = "%Y.%m.%d %H:%M:%S"


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


def _tag(hour: np.ndarray) -> np.ndarray:
    return np.select([hour < 7, hour < 12, hour < 16, hour < 21], ["ASIA", "LONDON", "OVERLAP", "NY"], "LATE")


def _tags_check(d: pd.DataFrame, us_dst: bool) -> dict:
    rows = d[(d["event"] == "DECISION") & (d["session_tag"] != "")]
    w = pd.to_datetime(rows["write_ts"], format=FMT)
    off = server_gmt_offset_hours(w, 2, us_dst)
    expect = _tag((w - pd.to_timedelta(off, unit="h")).dt.hour.to_numpy())
    return {"rows": len(rows), "mismatches": int((rows["session_tag"].to_numpy() != expect).sum()),
            "rows_in_us_dst": int((server_gmt_offset_hours(w, 2, True) == 3).sum())}


def _true_tag_of(d: pd.DataFrame) -> np.ndarray:
    w = pd.to_datetime(d["write_ts"], format=FMT)
    return _tag((w - pd.to_timedelta(server_gmt_offset_hours(w, 2, True), unit="h")).dt.hour.to_numpy())


def window(w: str) -> dict:
    b_dir = os.path.join(BASE, f"REG_S11_GBPUSD_{w}")
    n_dir = os.path.join(NEW, f"REG_DTZ_GBPUSD_{w}")
    b, n = _dna(b_dir), _dna(n_dir)
    out = {"base_rows": len(b), "new_rows": len(n), "test_passed": _passed(n_dir),
           "new_tags_vs_true_clock": _tags_check(n, True),
           "base_tags_vs_fixed_clock": _tags_check(b, False)}
    key = ["decision_ts", "event", "write_ts"]
    bk = b.assign(_k=b[key].agg("|".join, axis=1)).set_index("_k")
    nk = n.assign(_k=n[key].agg("|".join, axis=1)).set_index("_k")
    common = bk.index.intersection(nk.index)
    cols = [c for c in b.columns if c not in ("row_id",)]
    differs = bk.loc[common, cols].ne(nk.loc[common, cols]).any(axis=1)
    only_b, only_n = bk.index.difference(nk.index), nk.index.difference(bk.index)
    diff_keys = list(differs[differs].index) + list(only_b) + list(only_n)
    first = min((k.split("|")[2] for k in diff_keys), default=None)
    fw = pd.to_datetime(pd.Series([first]), format=FMT) if first else None
    bo, no = b[b["event"] == "OPEN"], n[n["event"] == "OPEN"]
    out.update({
        "rows_identical_keyed": int((~differs).sum()), "rows_differing_keyed": int(differs.sum()),
        "rows_only_base": len(only_b), "rows_only_new": len(only_n),
        "first_divergence_write_ts": first,
        "first_divergence_in_us_dst": bool(server_gmt_offset_hours(fw, 2, True)[0] == 3) if first else None,
        "opens_base": len(bo), "opens_new": len(no),
        "opens_base_true_tag_late": int((_true_tag_of(bo) == "LATE").sum()) if len(bo) else 0,
        "opens_new_true_tag_late": int((_true_tag_of(no) == "LATE").sum()) if len(no) else 0,
    })
    return out


def main() -> int:
    wins = {w: window(w) for w in WINDOWS}
    summary = {
        "runs": len(wins), "all_test_passed": all(v["test_passed"] for v in wins.values()),
        "tag_rows_checked": sum(v["new_tags_vs_true_clock"]["rows"] for v in wins.values()),
        "tag_rows_in_us_dst": sum(v["new_tags_vs_true_clock"]["rows_in_us_dst"] for v in wins.values()),
        "new_tag_mismatches_vs_true_clock": sum(v["new_tags_vs_true_clock"]["mismatches"] for v in wins.values()),
        "base_tag_mismatches_vs_fixed_clock": sum(v["base_tags_vs_fixed_clock"]["mismatches"] for v in wins.values()),
        "rows_differing_keyed": sum(v["rows_differing_keyed"] for v in wins.values()),
        "rows_only_base": sum(v["rows_only_base"] for v in wins.values()),
        "rows_only_new": sum(v["rows_only_new"] for v in wins.values()),
        "first_divergence_always_in_us_dst": all(v["first_divergence_in_us_dst"] in (True, None) for v in wins.values()),
        "opens_base": sum(v["opens_base"] for v in wins.values()), "opens_new": sum(v["opens_new"] for v in wins.values()),
        "opens_new_true_tag_late": sum(v["opens_new_true_tag_late"] for v in wins.values()),
        "opens_base_true_tag_late": sum(v["opens_base_true_tag_late"] for v in wins.values()),
    }
    ev = {"label": "ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE",
          "sources": {"NEXA_EA.mq5": _sha(os.path.join(ROOT, "NEXA_EA.mq5")),
                      "NEXA_Common.mqh": _sha(os.path.join(ROOT, "NEXA_Common.mqh")),
                      "NEXA_Risk.mqh": _sha(os.path.join(ROOT, "NEXA_Risk.mqh"))},
          "dtz_ex5": _sha(os.path.join(ROOT, "build", "NEXA_EA_DTZ.ex5")),
          "baseline": "s11/REG_S11_GBPUSD_<W> (S11 build 7d37dc7d, fixed GMT+2 clock)",
          "windows": wins, "summary": summary}
    with open(os.path.join(NEW, "regression_evidence.json"), "w") as fh:
        json.dump(ev, fh, indent=1, default=lambda o: o.item() if isinstance(o, np.generic) else str(o))
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
