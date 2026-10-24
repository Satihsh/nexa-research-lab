"""C4 daily-loss budget -- research-configuration check (ENGINEERING REGRESSION, NOT RESEARCH EVIDENCE).

The production-input regression (c4_regression.py, $200) never came near -2 %, so the gate never bound.
This pairs the D-TZ build (halt trigger only) and the C4 build (budget + trigger) under the cap-neutral
research configuration ($50k, InpMaxSameCurrencyNet=10000, other inputs at defaults) on the six windows that
had days beyond -2 % in the campaign, so the gate is exercised on real tester data:
  * every budget refusal is arithmetically justified, no fail-closed reason occurs;
  * journals are identical up to the first budget refusal;
  * realised daily loss (net of commission and swap; JPY P&L converted at the exit price) before vs after.

    python research/engfix/c4_capn_check.py   -> c4/capn_evidence.json
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
from c4_regression import FAIL_CLOSED, FMT, REFUSAL, _dna, _passed, _sha

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "c4")
PAIRS = [("GBPUSD", "A2024Q1"), ("GBPUSD", "A2024Q2"), ("GBPUSD", "A2026Q1"),
         ("EURUSD", "A2025Q1"), ("USDJPY", "A2024Q1"), ("USDJPY", "A2025Q1")]
DEPOSIT = 50_000.0


def daily(d: pd.DataFrame, sym: str) -> pd.DataFrame:
    legs = d[d["event"].isin(["CLOSE", "PARTIAL_CLOSE"])].copy()
    if not len(legs):
        return pd.DataFrame(columns=["day", "pnl", "start_balance", "ret"])

    def f(c):
        return pd.to_numeric(legs[c], errors="coerce").fillna(0.0)
    quote = f("direction") * (f("entry_actual") - f("entry_intended")) * f("lots") * 100_000.0
    usd = quote / f("entry_actual") if sym.endswith("JPY") else quote
    legs["pnl"] = usd + f("commission") + f("swap")
    legs["day"] = pd.to_datetime(legs["write_ts"], format=FMT).dt.date
    day = legs.groupby("day", sort=True)["pnl"].sum().reset_index()
    day["start_balance"] = DEPOSIT + day["pnl"].cumsum().shift(fill_value=0.0)
    day["ret"] = day["pnl"] / day["start_balance"]
    return day


def pair(sym: str, w: str) -> dict:
    b_dir, n_dir = os.path.join(OUT, f"capn_DTZ_{sym}_{w}"), os.path.join(OUT, f"capn_C4_{sym}_{w}")
    b, n = _dna(b_dir), _dna(n_dir)
    reasons = n["reason"].astype(str)
    ref = reasons[reasons.str.startswith("NO_TRADE_DAILY_LOSS_BUDGET")]
    parsed = [REFUSAL.match(r) for r in ref]
    justified = [bool(m) and float(m[1]) - float(m[2]) - float(m[3]) < float(m[4]) + 0.005 for m in parsed]
    m = min(len(b), len(n))
    cols = [c for c in b.columns if c != "row_id"]
    neq = np.flatnonzero(b.iloc[:m][cols].to_numpy() != n.iloc[:m][cols].to_numpy())
    first = int(neq[0] // len(cols)) if len(neq) else (m if len(b) != len(n) else None)
    first_ok = first is None or (first < len(n) and str(n.iloc[first]["reason"]).startswith("NO_TRADE_DAILY_LOSS_BUDGET"))
    db, dn = daily(b, sym), daily(n, sym)
    return {
        "base_passed": _passed(b_dir), "new_passed": _passed(n_dir),
        "budget_refusals": len(ref), "refusals_justified": int(sum(justified)),
        "fail_closed_rows": int(sum(any(k in r for k in FAIL_CLOSED) for r in reasons)),
        "first_divergence_ts": None if first is None or first >= len(n) else n.iloc[first]["write_ts"],
        "first_divergence_is_budget_refusal": bool(first_ok),
        "opens_base": int((b["event"] == "OPEN").sum()), "opens_new": int((n["event"] == "OPEN").sum()),
        "base_days_beyond_2pct": int((db["ret"] <= -0.02).sum()), "new_days_beyond_2pct": int((dn["ret"] <= -0.02).sum()),
        "base_worst_day_ret": float(db["ret"].min()) if len(db) else 0.0,
        "new_worst_day_ret": float(dn["ret"].min()) if len(dn) else 0.0,
        "base_net_pnl": float(db["pnl"].sum()), "new_net_pnl": float(dn["pnl"].sum()),
    }


def main() -> int:
    pairs = {f"{s}_{w}": pair(s, w) for s, w in PAIRS}
    v = list(pairs.values())
    summary = {
        "pairs": len(v), "all_passed": all(x["base_passed"] and x["new_passed"] for x in v),
        "budget_refusals": sum(x["budget_refusals"] for x in v),
        "refusals_justified": sum(x["refusals_justified"] for x in v),
        "fail_closed_rows": sum(x["fail_closed_rows"] for x in v),
        "first_divergence_always_a_budget_refusal": all(x["first_divergence_is_budget_refusal"] for x in v),
        "opens_base": sum(x["opens_base"] for x in v), "opens_new": sum(x["opens_new"] for x in v),
        "base_days_beyond_2pct": sum(x["base_days_beyond_2pct"] for x in v),
        "new_days_beyond_2pct": sum(x["new_days_beyond_2pct"] for x in v),
        "base_worst_day_ret": min(x["base_worst_day_ret"] for x in v),
        "new_worst_day_ret": min(x["new_worst_day_ret"] for x in v),
    }
    ev = {"label": "ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE (research configuration, not production inputs)",
          "sources": {n: _sha(os.path.join(ROOT, n)) for n in ("NEXA_EA.mq5", "NEXA_Risk.mqh", "NEXA_Common.mqh")},
          "builds": {"DTZ": _sha(os.path.join(ROOT, "build", "NEXA_EA_DTZ.ex5")),
                     "C4": _sha(os.path.join(ROOT, "build", "NEXA_EA_C4.ex5"))},
          "pairs": pairs, "summary": summary}
    with open(os.path.join(OUT, "capn_evidence.json"), "w") as fh:
        json.dump(ev, fh, indent=1, default=lambda o: o.item() if isinstance(o, np.generic) else str(o))
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
