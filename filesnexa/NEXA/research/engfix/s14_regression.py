"""S14 post-fill hard-ceiling guard (2026-10-04, approved option C): ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE.

Compares the Trade DNA of the S14 build (s14/REG_S14_GBPUSD_<W>) with the S13 baseline (s13/REG_S13_GBPUSD_<W>).
Expected: every row identical except the FILL rows' reason, which now also carries the SIGNED slippage
("SLIPPAGE_PTS_<abs>_ADVERSE_<+/-x>"); the absolute part is unchanged and the sign agrees with the fill prices;
the guard never fires in the tester (no fill exceeded the hard ceiling).

    python research/engfix/s14_regression.py   -> s14/regression_evidence.json
"""
from __future__ import annotations

import hashlib
import json
import os
import re

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BASE = os.path.join(HERE, "s13")
NEW = os.path.join(HERE, "s14")
WINDOWS = ["A2024Q1", "A2024Q2", "A2024Q3", "A2024Q4", "A2025Q1", "A2025Q2", "A2025Q3", "A2025Q4",
           "A2026Q1", "A2026Q2", "A2026Q3", "B"]
FILL_REASON = re.compile(r"^SLIPPAGE_PTS_([\d.]+)_ADVERSE_([+-][\d.]+)$")
POINT = 1e-5                                   # GBPUSD


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
    b_dir, n_dir = os.path.join(BASE, f"REG_S13_GBPUSD_{w}"), os.path.join(NEW, f"REG_S14_GBPUSD_{w}")
    b, n = _dna(b_dir), _dna(n_dir)
    out = {"base_rows": len(b), "new_rows": len(n), "test_passed": _passed(n_dir)}
    if len(b) != len(n) or list(b.columns) != list(n.columns):
        out["comparable"] = False
        return out
    fill = n["event"] == "FILL"
    other = [c for c in b.columns if c != "reason"]
    differs_other = b[other].ne(n[other]).any(axis=1)
    differs_reason = b["reason"] != n["reason"]
    parsed = n.loc[fill, "reason"].str.extract(FILL_REASON)
    abs_same = (parsed[0].astype(float).round(1).values
                == b.loc[fill, "reason"].str.replace("SLIPPAGE_PTS_", "", regex=False).astype(float).round(1).values)
    nf = n[fill]
    calc = ((pd.to_numeric(nf["entry_actual"]) - pd.to_numeric(nf["entry_intended"]))
            * pd.to_numeric(nf["direction"]) / POINT).round(1)
    sign_ok = np.isclose(parsed[1].astype(float).values, calc.values, atol=0.051)
    out.update({
        "comparable": True,
        "rows_differing_outside_reason": int(differs_other.sum()),
        "reason_changes_outside_fill_rows": int((differs_reason & ~fill).sum()),
        "fill_rows": int(fill.sum()), "fill_reasons_parsed": int(parsed[0].notna().sum()),
        "fill_abs_part_unchanged": int(abs_same.sum()), "fill_signed_part_matches_prices": int(sign_ok.sum()),
        "adverse_fills": int((parsed[1].astype(float) > 0).sum()), "favourable_fills": int((parsed[1].astype(float) < 0).sum()),
        "guard_firings": int(n["reason"].str.startswith("FILL_RISK_ABOVE_HARD_CEILING").sum()),
    })
    return out


def main() -> int:
    wins = {w: window(w) for w in WINDOWS}
    ok = [v for v in wins.values() if v.get("comparable")]
    keys = ("rows_differing_outside_reason", "reason_changes_outside_fill_rows", "fill_rows", "fill_reasons_parsed",
            "fill_abs_part_unchanged", "fill_signed_part_matches_prices", "adverse_fills", "favourable_fills",
            "guard_firings")
    summary = {"runs": len(wins), "all_test_passed": all(v["test_passed"] for v in wins.values()),
               "all_comparable": len(ok) == len(wins), **{k: sum(v[k] for v in ok) for k in keys}}
    ev = {"label": "ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE",
          "sources": {n: _sha(os.path.join(ROOT, n)) for n in
                      ("NEXA_EA.mq5", "NEXA_FillGuard.mqh", "NEXA_Risk.mqh", "NEXA_Common.mqh", "NEXA_Intelligence.mqh")},
          "s14_ex5": _sha(os.path.join(ROOT, "build", "NEXA_EA_S14.ex5")),
          "baseline": "s13/REG_S13_GBPUSD_<W> (S13 build dec57013, no post-fill guard)",
          "windows": wins, "summary": summary}
    with open(os.path.join(NEW, "regression_evidence.json"), "w") as fh:
        json.dump(ev, fh, indent=1, default=lambda o: o.item() if isinstance(o, np.generic) else str(o))
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
