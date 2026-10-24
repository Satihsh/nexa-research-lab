"""C4 daily-loss budget (2026-10-03, approved option B): ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE.

Compares the Trade DNA of the C4 build (c4/REG_C4_GBPUSD_<W>) with the D-TZ baseline
(dtz/REG_DTZ_GBPUSD_<W>), same windows, inputs and tester setup ($200, production inputs).

Checks per window:
  * every NO_TRADE_DAILY_LOSS_BUDGET_eq.._open.._new.._floor.. refusal is arithmetically justified
    (eq - open - new < floor) and no fail-closed reason (unreadable / no stop / no start) occurred;
  * the journals are identical up to the first budget refusal (behaviour changes only through the gate);
  * realised loss per server day (CLOSE + PARTIAL_CLOSE legs, net of commission and swap, GBPUSD USD P&L)
    in the baseline vs C4: days beyond -2 % and the worst day. Realised basis, against the balance at the
    start of the day (the EA's own basis is equity, which also counts open P&L).

    python research/engfix/c4_regression.py   -> c4/regression_evidence.json
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
BASE = os.path.join(HERE, "dtz")
NEW = os.path.join(HERE, "c4")
WINDOWS = ["A2024Q1", "A2024Q2", "A2024Q3", "A2024Q4", "A2025Q1", "A2025Q2", "A2025Q3", "A2025Q4",
           "A2026Q1", "A2026Q2", "A2026Q3", "B"]
DEPOSIT = 200.0
CONTRACT = 100_000.0                       # GBPUSD: USD P&L = direction * (exit - entry) * lots * contract
REFUSAL = re.compile(r"^NO_TRADE_DAILY_LOSS_BUDGET_eq(-?[\d.]+)_open(-?[\d.]+)_new(-?[\d.]+)_floor(-?[\d.]+)$")
FAIL_CLOSED = ("DAILY_LOSS_BUDGET_POSITION_UNREADABLE", "DAILY_LOSS_BUDGET_POSITION_WITHOUT_STOP",
               "DAILY_LOSS_BUDGET_NO_START_EQUITY", "DAILY_LOSS_BUDGET_INVALID", "DAILY_LOSS_BUDGET_NEW_RISK_UNREADABLE")
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


def daily_realised(d: pd.DataFrame) -> pd.DataFrame:
    legs = d[d["event"].isin(["CLOSE", "PARTIAL_CLOSE"])].copy()
    if not len(legs):
        return pd.DataFrame(columns=["day", "pnl", "start_balance", "ret"])
    f = lambda c: pd.to_numeric(legs[c], errors="coerce").fillna(0.0)
    legs["pnl"] = (f("direction") * (f("entry_actual") - f("entry_intended")) * f("lots") * CONTRACT
                   + f("commission") + f("swap"))
    legs["day"] = pd.to_datetime(legs["write_ts"], format=FMT).dt.date
    day = legs.groupby("day", sort=True)["pnl"].sum().reset_index()
    day["start_balance"] = DEPOSIT + day["pnl"].cumsum().shift(fill_value=0.0)
    day["ret"] = day["pnl"] / day["start_balance"]
    return day


def window(w: str) -> dict:
    b_dir, n_dir = os.path.join(BASE, f"REG_DTZ_GBPUSD_{w}"), os.path.join(NEW, f"REG_C4_GBPUSD_{w}")
    b, n = _dna(b_dir), _dna(n_dir)
    reasons = n["reason"].astype(str)
    ref = reasons[reasons.str.startswith("NO_TRADE_DAILY_LOSS_BUDGET")]
    parsed = [REFUSAL.match(r) for r in ref]
    justified = [bool(m) and float(m[1]) - float(m[2]) - float(m[3]) < float(m[4]) + 0.005 for m in parsed]
    fail_closed = int(sum(any(k in r for k in FAIL_CLOSED) for r in reasons))
    # first divergence (positional, both journals are written in time order)
    m = min(len(b), len(n))
    cols = [c for c in b.columns if c != "row_id"]
    neq = np.flatnonzero(b.iloc[:m][cols].to_numpy() != n.iloc[:m][cols].to_numpy())
    first_row = int(neq[0] // len(cols)) if len(neq) else (m if len(b) != len(n) else None)
    first_is_refusal = (first_row is None) or (first_row < len(n) and str(n.iloc[first_row]["reason"]).startswith(
        "NO_TRADE_DAILY_LOSS_BUDGET"))
    db, dn = daily_realised(b), daily_realised(n)
    return {
        "base_rows": len(b), "new_rows": len(n), "test_passed": _passed(n_dir),
        "budget_refusals": len(ref), "refusals_justified": int(sum(justified)), "fail_closed_rows": fail_closed,
        "first_divergence_row": first_row,
        "first_divergence_ts": None if first_row is None or first_row >= len(n) else n.iloc[first_row]["write_ts"],
        "first_divergence_is_budget_refusal": bool(first_is_refusal),
        "opens_base": int((b["event"] == "OPEN").sum()), "opens_new": int((n["event"] == "OPEN").sum()),
        "base_days_beyond_2pct": int((db["ret"] <= -0.02).sum()), "new_days_beyond_2pct": int((dn["ret"] <= -0.02).sum()),
        "base_worst_day_ret": float(db["ret"].min()) if len(db) else 0.0,
        "new_worst_day_ret": float(dn["ret"].min()) if len(dn) else 0.0,
    }


def main() -> int:
    wins = {w: window(w) for w in WINDOWS}
    v = list(wins.values())
    summary = {
        "runs": len(v), "all_test_passed": all(x["test_passed"] for x in v),
        "budget_refusals": sum(x["budget_refusals"] for x in v),
        "refusals_justified": sum(x["refusals_justified"] for x in v),
        "fail_closed_rows": sum(x["fail_closed_rows"] for x in v),
        "first_divergence_always_a_budget_refusal": all(x["first_divergence_is_budget_refusal"] for x in v),
        "windows_identical": sum(x["first_divergence_row"] is None for x in v),
        "opens_base": sum(x["opens_base"] for x in v), "opens_new": sum(x["opens_new"] for x in v),
        "base_days_beyond_2pct": sum(x["base_days_beyond_2pct"] for x in v),
        "new_days_beyond_2pct": sum(x["new_days_beyond_2pct"] for x in v),
        "base_worst_day_ret": min(x["base_worst_day_ret"] for x in v),
        "new_worst_day_ret": min(x["new_worst_day_ret"] for x in v),
    }
    ev = {"label": "ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE",
          "sources": {n: _sha(os.path.join(ROOT, n)) for n in ("NEXA_EA.mq5", "NEXA_Risk.mqh", "NEXA_Common.mqh")},
          "c4_ex5": _sha(os.path.join(ROOT, "build", "NEXA_EA_C4.ex5")),
          "baseline": "dtz/REG_DTZ_GBPUSD_<W> (D-TZ build 53439394, 2 % halt trigger only)",
          "windows": wins, "summary": summary}
    with open(os.path.join(NEW, "regression_evidence.json"), "w") as fh:
        json.dump(ev, fh, indent=1, default=lambda o: o.item() if isinstance(o, np.generic) else str(o))
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
