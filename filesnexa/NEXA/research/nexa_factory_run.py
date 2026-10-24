"""Run the Strategy Factory under a protocol frozen BEFORE any result is seen.

    python nexa_factory_run.py --bars ../../"NEXA 2"/data/XAUUSD_H1.csv --symbol XAUUSD --tf H1

PROTOCOL (the sha256 of this dict is written into the report; changing it after
seeing results is exactly the selection bias this file exists to prevent):

  DEV      2018-01-01 .. 2022-12-31   configs are ranked here
  VAL      2023-01-01 .. 2024-12-31   walk-forward continues through here
  HOLDOUT  2025-01-01 .. end          evaluated ONCE per family, with the config
                                      frozen on DEV+VAL; never used to choose

  Walk-forward: for each year Y in WF_YEARS, pick the family config with the best
  expectancy over all years < Y (min MIN_TRADES_SELECT trades), trade it in Y.
  The stitched year-by-year trades are the family's walk-forward OOS record.

  A family becomes a CANDIDATE (for MT5 Strategy Tester + shadow, NOT for live)
  only if ALL hold on its walk-forward OOS record:
    * nexa_stats verdict EDGE_SUPPORTED_IN_SAMPLE at BASE cost
    * expectancy > 0 at STRESS cost
    * Benjamini-Hochberg pass at q = FDR_Q across all non-null families
    * deflated Sharpe >= DSR_MIN with n_trials = every config in the registry
    * PBO < PBO_MAX (families with >= 2 configs)
    * expectancy above the NULL_RANDOM baseline
  Holdout results are reported for every family whether or not it passes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict

import numpy as np
import pandas as pd

import nexa_factory as fct
import nexa_robust as rob
import nexa_stats as st

PROTOCOL = {
    "periods": {"DEV": ["2018-01-01", "2022-12-31"], "VAL": ["2023-01-01", "2024-12-31"],
                "HOLDOUT": ["2025-01-01", "2099-12-31"]},
    "wf_years": [2020, 2021, 2022, 2023, 2024],
    "min_trades_select": 30,
    # ASSUMED costs, fractions of price (XAUUSD source has no bid/ask). 1 bp at $2000 = $0.20.
    "costs": {"BASE": {"spread": 1.5e-4, "slippage": 0.25e-4},
              "STRESS": {"spread": 3.0e-4, "slippage": 0.5e-4},
              "SEVERE": {"spread": 5.0e-4, "slippage": 1.0e-4}},
    "fdr_q": 0.10,
    "dsr_min": 0.95,
    "pbo_max": 0.50,
    "stats": {"min_trades": 30, "n_boot": 4000, "n_mc": 3000, "cost_shock_r": 0.05, "block": 1},
}


def protocol_hash() -> str:
    return hashlib.sha256(json.dumps(PROTOCOL, sort_keys=True).encode()).hexdigest()[:16]


def _cost(name: str) -> fct.CostModel:
    c = PROTOCOL["costs"][name]
    return fct.CostModel(name, c["spread"], c["slippage"], assumed=True, relative=True)


def _period(tr: pd.DataFrame, name: str) -> pd.DataFrame:
    lo, hi = PROTOCOL["periods"][name]
    ts = pd.to_datetime(tr.entry_ts)
    return tr[(ts >= lo) & (ts <= pd.Timestamp(hi) + pd.Timedelta(days=1))]


def _year(tr: pd.DataFrame) -> np.ndarray:
    return pd.to_datetime(tr.entry_ts).dt.year.values if len(tr) else np.zeros(0, int)


def _exp(tr: pd.DataFrame) -> float:
    return float(tr.r_net.mean()) if len(tr) else float("nan")


def walk_forward(runs: dict, names: list) -> tuple[pd.DataFrame, list]:
    """Stitch year-by-year OOS trades of the config chosen on all prior years."""
    parts, picks = [], []
    for y in PROTOCOL["wf_years"]:
        best, best_e = None, -np.inf
        for n in names:
            tr = runs[n]
            past = tr[_year(tr) < y]
            if len(past) >= PROTOCOL["min_trades_select"] and _exp(past) > best_e:
                best, best_e = n, _exp(past)
        picks.append({"year": y, "config": best, "trailing_expectancy_r": None if best is None else best_e})
        if best is not None:
            tr = runs[best]
            parts.append(tr[_year(tr) == y].assign(wf_config=best))
    return (pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()), picks


def monthly_matrix(runs: dict, names: list, period=("DEV", "VAL")) -> np.ndarray:
    lo, hi = PROTOCOL["periods"][period[0]][0], PROTOCOL["periods"][period[-1]][1]
    months = pd.period_range(lo, hi, freq="M")
    cols = []
    for n in names:
        tr = runs[n]
        s = tr.groupby(pd.to_datetime(tr.entry_ts).dt.to_period("M")).r_net.sum() if len(tr) else pd.Series(dtype=float)
        cols.append(s.reindex(months, fill_value=0.0).values)
    return np.column_stack(cols)


def _session(ts: pd.Series) -> np.ndarray:
    h = pd.to_datetime(ts).dt.hour.values           # broker server time (EET/EEST)
    return np.where(h < 9, "ASIA", np.where(h < 15, "LONDON", np.where(h < 20, "NEWYORK", "LATE")))


def _sha256(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def run(bars_path: str, symbol: str, tf: str, out_dir: str) -> dict:
    b = fct.load_bars(bars_path)
    reg = fct.registry()
    scfg = st.StatsConfig(**PROTOCOL["stats"])
    runs = {s.name: s.run(b, _cost("BASE")).frame for s in reg}
    fam = {}
    for s in reg:
        fam.setdefault(s.family, []).append(s.name)

    dev_sr = [rob.sharpe(_period(runs[s.name], "DEV").r_net.values) for s in reg]
    var_sr = float(np.nanvar(dev_sr, ddof=1))
    n_trials = len(reg)

    report = {"symbol": symbol, "timeframe": tf, "bars_file": os.path.basename(bars_path),
              "bars_sha256": _sha256(bars_path),
              "bars": {"rows": len(b), "first": str(b.time.iloc[0]), "last": str(b.time.iloc[-1])},
              "protocol": PROTOCOL, "protocol_sha": protocol_hash(),
              "costs_are_assumed": True, "n_trials": n_trials, "var_sharpe_dev": var_sr,
              "configs": {}, "families": {}}

    for s in reg:
        tr = runs[s.name]
        report["configs"][s.name] = {
            "family": s.family, "params": s.params,
            **{p: {"n": len(_period(tr, p)), "expectancy_r": _exp(_period(tr, p))} for p in ("DEV", "VAL", "HOLDOUT")}}

    null_wf, _ = walk_forward(runs, fam["null"])
    null_exp = _exp(null_wf)

    pvals = {}
    for family, names in fam.items():
        wf, picks = walk_forward(runs, names)
        r = wf.r_net.values if len(wf) else np.zeros(0)
        ev = st.evaluate(r, scfg)
        fr = {"configs": names, "wf_picks": picks, "wf_oos": ev.to_dict()}
        # cost stress: rerun the SAME picked configs under harsher costs
        for cname in ("STRESS", "SEVERE"):
            parts = []
            for pk in picks:
                if pk["config"]:
                    strat = next(x for x in reg if x.name == pk["config"])
                    t2 = strat.run(b, _cost(cname)).frame
                    parts.append(t2[_year(t2) == pk["year"]])
            rs = pd.concat(parts).r_net.values if parts else np.zeros(0)
            fr[f"wf_oos_{cname.lower()}"] = st.trade_metrics(rs)
        fr["pvalue"] = rob.expectancy_pvalue(r)
        fr["psr"] = rob.probabilistic_sharpe(r)
        fr["dsr"] = rob.deflated_sharpe(r, n_trials, var_sr)
        if len(names) >= 2:
            fr["pbo"] = rob.pbo_cscv(monthly_matrix(runs, names), n_splits=10)
        if len(wf):
            fr["by_direction"] = st.segment_metrics(r, np.where(wf.direction > 0, "LONG", "SHORT"))
            fr["by_session"] = st.segment_metrics(r, _session(wf.entry_ts))
            fr["by_year"] = st.segment_metrics(r, _year(wf).astype(str))
            fr["ambiguous_rate"] = float(wf.ambiguous.mean())
            fr["mfe_r_median"] = float(wf.mfe_r.median())
            fr["mae_r_median"] = float(wf.mae_r.median())
        # HOLDOUT: config frozen on DEV+VAL, evaluated once
        best, best_e = None, -np.inf
        for n in names:
            pre = pd.concat([_period(runs[n], "DEV"), _period(runs[n], "VAL")])
            if len(pre) >= PROTOCOL["min_trades_select"] and _exp(pre) > best_e:
                best, best_e = n, _exp(pre)
        if best:
            ho = _period(runs[best], "HOLDOUT").r_net.values
            fr["holdout"] = {"frozen_config": best, "dev_val_expectancy_r": best_e,
                             **st.evaluate(ho, scfg).to_dict()}
        report["families"][family] = fr
        if family != "null" and np.isfinite(fr["pvalue"]):
            pvals[family] = fr["pvalue"]

    fams = list(pvals)
    mask = rob.benjamini_hochberg([pvals[f] for f in fams], PROTOCOL["fdr_q"]) if fams else []
    for f, ok in zip(fams, mask, strict=True):
        report["families"][f]["bh_fdr_pass"] = bool(ok)

    for family, fr in report["families"].items():
        if family == "null":
            fr["candidate"] = False
            fr["gate_failures"] = ["baseline"]
            continue
        fails = []
        if fr["wf_oos"]["verdict"] != st.Verdict.EDGE_SUPPORTED_IN_SAMPLE.value:
            fails.append(f"stats verdict {fr['wf_oos']['verdict']}")
        if not fr["wf_oos_stress"].get("expectancy_r", -1) > 0:
            fails.append("expectancy <= 0 at STRESS cost")
        if not fr.get("bh_fdr_pass", False):
            fails.append("fails Benjamini-Hochberg FDR")
        if not (np.isfinite(fr["dsr"]) and fr["dsr"] >= PROTOCOL["dsr_min"]):
            fails.append(f"deflated Sharpe {fr['dsr']:.3f} < {PROTOCOL['dsr_min']}")
        if "pbo" in fr and fr["pbo"]["pbo"] >= PROTOCOL["pbo_max"]:
            fails.append(f"PBO {fr['pbo']['pbo']:.2f} >= {PROTOCOL['pbo_max']}")
        if not fr["wf_oos"]["metrics"].get("expectancy_r", -np.inf) > null_exp:
            fails.append("does not beat NULL_RANDOM")
        fr["candidate"] = not fails
        fr["gate_failures"] = fails

    report["null_wf_expectancy_r"] = null_exp
    report["candidates"] = [f for f, fr in report["families"].items() if fr["candidate"]]
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.join(out_dir, f"factory_{symbol}_{tf}")
    with open(stem + ".json", "w") as fh:
        json.dump(report, fh, indent=1, default=_json_default)
    with open(stem + "_spec.json", "w") as fh:
        fh.write(fct.spec_json(reg))
    return report


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (pd.Timestamp, np.datetime64)):
        return str(o)
    if hasattr(o, "__dataclass_fields__"):
        return asdict(o)
    return str(o)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--bars", required=True)
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--tf", required=True)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "reports"))
    a = ap.parse_args(argv)
    rep = run(a.bars, a.symbol, a.tf, a.out)
    print(json.dumps({"protocol_sha": rep["protocol_sha"], "candidates": rep["candidates"],
                      "families": {f: {"verdict": fr["wf_oos"]["verdict"], "n": fr["wf_oos"]["metrics"].get("n"),
                                       "E[R]": fr["wf_oos"]["metrics"].get("expectancy_r"),
                                       "fails": fr["gate_failures"]}
                                   for f, fr in rep["families"].items()}}, indent=1, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
