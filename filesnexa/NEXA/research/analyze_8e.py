"""RESEARCH_8E_V1 analysis (pinned; descriptive outputs, never feeds selection).

  python analyze_8e.py info        engine information / redundancy / mutual information (DEV and VAL)
  python analyze_8e.py stack       incremental stack L0..L7 (DEV and VAL, non-overlapping trades)
  python analyze_8e.py selected    selected trials: stress x2/x3 spread, DSR, PBO, capital-velocity replay
  python analyze_8e.py sizing      day-by-day broker sizing tables (real spec probe) for the ideal path
Outputs: research/runs_8e/*.json|csv
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

import nexa_8e_capital as CV
import nexa_8e_costs as C
import nexa_8e_engines as E
import nexa_8e_feasibility as F
import nexa_8e_research as R
import nexa_registry2 as r2
import nexa_robust as rb
import protocols_8e as P
import run_8e as RUN

ENG = ["sq", "vei", "ema200", "mom", "ofi", "quoteburst", "td"]


def _window(sig: pd.DataFrame, period: str) -> pd.DataFrame:
    s, e = P.PERIODS[period]
    return R.in_window(sig, s, e, RUN.EMBARGO, RUN.MAX_LABEL, first_period=(period == "DEV"))


def mutual_info_bits(x: np.ndarray, y: np.ndarray) -> float:
    x, y = x.astype(bool), y.astype(bool)
    mi = 0.0
    for a in (False, True):
        for b in (False, True):
            pxy = np.mean((x == a) & (y == b))
            px, py = np.mean(x == a), np.mean(y == b)
            if pxy > 0:
                mi += pxy * np.log2(pxy / (px * py))
    return float(mi)


def cmd_info():
    rows, corr = [], {}
    for sym, tf, n, mode, k, _ in RUN.bases():
        sig = RUN.load_table(sym, tf, n, mode, k)
        for period in ("DEV", "VAL"):
            w = _window(sig, period)
            if len(w) < 30:
                continue
            r = w["r_net"].to_numpy(float)
            win = r > 0
            for v in R.SINGLE + R.THRESH:
                m = w[f"m_{v}"].to_numpy(bool)
                rows.append({"symbol": sym, "tf": tf, "dc_n": n, "mode": mode, "k": k, "period": period, "variant": v,
                             "n_base": len(r), "n_kept": int(m.sum()), "mean_base": float(r.mean()),
                             "mean_kept": float(r[m].mean()) if m.any() else np.nan,
                             "delta": float(r[m].mean() - r.mean()) if m.any() else np.nan,
                             "p_random_subset": R.random_subset_p(r, m, draws=1000),
                             "mi_bits_win": mutual_info_bits(m, win), "win_base": float(win.mean()),
                             "win_kept": float(win[m].mean()) if m.any() else np.nan})
            if period == "DEV" and mode == "close_next_open" and k == 3:
                flags = pd.DataFrame({e: w[f"m_A_{e}"].astype(float) for e in ENG})
                corr[f"{sym}_{tf}_dc{n}"] = flags.corr().round(3).to_dict()
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(RUN.RUNS, "info_signal_level.csv"), index=False)
    with open(os.path.join(RUN.RUNS, "redundancy_corr.json"), "w") as fh:
        json.dump(corr, fh, indent=1)
    agg = (df.groupby(["period", "symbol", "variant"])
             .agg(bases=("delta", "size"), mean_delta=("delta", "mean"), share_improves=("delta", lambda x: float((x > 0).mean())),
                  share_sig=("p_random_subset", lambda x: float((x < 0.05).mean())), mean_kept_frac=("n_kept", "mean"),
                  mi_bits=("mi_bits_win", "mean")).reset_index())
    agg.to_csv(os.path.join(RUN.RUNS, "info_summary.csv"), index=False)
    print(agg[agg.period == "VAL"].to_string())


def cmd_stack():
    rows = []
    for sym, tf, n, mode, k, _ in RUN.bases():
        sig = RUN.load_table(sym, tf, n, mode, k)
        for period in ("DEV", "VAL"):
            for v in R.STACK:
                tr = RUN.trades_for(sig, v, period)
                m = R.metrics(tr)
                rows.append({"symbol": sym, "tf": tf, "dc_n": n, "mode": mode, "k": k, "period": period, "variant": v,
                             "n": m.get("n", 0), "exp_net_r": m.get("exp_net_r", np.nan),
                             "win_rate": m.get("win_rate", np.nan), "cost_r": m.get("cost_r_mean", np.nan),
                             "trades_per_active_day": m.get("trades_per_active_day", np.nan)})
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(RUN.RUNS, "stack.csv"), index=False)
    print(df.groupby(["period", "symbol", "variant"])[["n", "exp_net_r", "win_rate"]].mean().round(3).to_string())


def _sharpe_all_val(reg, anchor):
    out = []
    for r in reg._results():
        m = r["metrics"]
        if r["period"] == "VAL" and m.get("n", 0) >= 30 and m.get("sharpe_per_trade") is not None:
            out.append(m["sharpe_per_trade"])
    return np.array(out, float)


def cmd_selected(anchor):
    reg = r2.RegistryV2(RUN.REG)
    v = reg.verify(anchor)
    with open(os.path.join(RUN.RUNS, "selection.json")) as fh:
        picks = json.load(fh)["picks"]
    specs = C.load_specs()
    sr_all = _sharpe_all_val(reg, anchor)
    n_trials = v["campaign"]["trial_counts"]["dsr_trial_count"]
    out = {}
    # PBO per group from monthly VAL net R of all trials in the group
    for g, pick in picks.items():
        if not pick:
            out[g] = None
            continue
        c = pick["config"]
        sym = g.split("|")[2]
        res = {"config": c, "val": pick["val"]}
        for sx in (2.0, 3.0):
            RUN._build_one((sym, c["tf"], c["dc_n"], c["entry_mode"], c["target_r"], sx))
            tr = RUN.trades_for(RUN.load_table(sym, c["tf"], c["dc_n"], c["entry_mode"], c["target_r"], sx), c["variant"], "VAL")
            res[f"stress_spread_x{sx:g}"] = R.metrics(tr)
        tr = RUN.trades_for(RUN.load_table(sym, c["tf"], c["dc_n"], c["entry_mode"], c["target_r"]), c["variant"], "VAL")
        r = tr["r_net"].to_numpy(float)
        res["dsr"] = float(rb.deflated_sharpe(r, n_trials, float(np.var(sr_all)))) if len(r) > 3 else None
        res["dsr_inputs"] = {"n_trials": n_trials, "var_sr_trials": float(np.var(sr_all)), "n_val_trials_used": int(sr_all.size)}
        # PBO across the group's configs (monthly net R, VAL)
        exp, claim, _ = g.split("|")
        mats = {}
        for t in RUN.trial_rows():
            if (t["experiment"], t["claim"], t["symbol"]) != (exp, claim, sym):
                continue
            cc = t["config"]
            tt = RUN.trades_for(RUN.load_table(sym, cc["tf"], cc["dc_n"], cc["entry_mode"], cc["target_r"]), cc["variant"], "VAL")
            if len(tt):
                mats[t["trial_id"]] = tt.groupby(pd.to_datetime(tt["exit_time"]).dt.to_period("M"))["r_net"].sum()
        mat = pd.DataFrame(mats).fillna(0.0).sort_index()
        res["pbo"] = rb.pbo_cscv(mat.to_numpy(), n_splits=8) if mat.shape[0] >= 8 and mat.shape[1] >= 2 else None
        # capital velocity replay from $200 with the real broker spec
        if sym in specs:
            days = CV.simulate(tr[["entry_time", "risk", "r_net", "cost_r"]], specs[sym], start_equity=200.0)
            res["capital_velocity"] = CV.summary(days)
            res["capital_velocity"]["p_20_of_20_bootstrap"] = CV.p_all_targets_bootstrap(days["net_return"].to_numpy()) if len(days) else None
            days.head(20).to_csv(os.path.join(RUN.RUNS, f"capital_velocity_first20_{g.replace('|', '_')}.csv"), index=False)
            big = CV.simulate(tr[["entry_time", "risk", "r_net", "cost_r"]], specs[sym], start_equity=10000.0)
            res["capital_velocity_10k_reference"] = CV.summary(big)
        out[g] = res
    with open(os.path.join(RUN.RUNS, "selected_analysis.json"), "w") as fh:
        json.dump(out, fh, indent=1, default=str)
    print(json.dumps({g: (None if x is None else {"val_n": x["val"].get("n"), "val_exp": x["val"].get("exp_net_r"),
                                                    "dsr": x["dsr"], "pbo": (x["pbo"] or {}).get("pbo")}) for g, x in out.items()},
                     indent=1, default=str))


def _atr_median(sym: str, tf: str, since: str = "2025-09-25") -> float:
    b = E.resample_m1(R.load_m1(sym, since), tf)
    return float(E.atr(b, 14).median())


def cmd_sizing():
    specs = C.load_specs()
    spread_med = {"XAUUSD": 0.12, "EURUSD": 0.00002 * 1.0, "GBPUSD": 0.00003, "NAS100": 1.0}
    stops = {("XAUUSD", "M15 ATR14 median"): _atr_median("XAUUSD", "M15"),
             ("EURUSD", "M15 ATR14 median"): _atr_median("EURUSD", "M15"),
             ("GBPUSD", "M15 ATR14 median"): _atr_median("GBPUSD", "M15"),
             ("NAS100", "ASSUMED 20 pts"): 20.0, ("NAS100", "ASSUMED 40 pts"): 40.0}
    rows = []
    for (sym, label), stop in stops.items():
        sp = specs[sym]
        costs = C.CostInputs(spread_price=spread_med[sym], slippage_price=0.5 * spread_med[sym])
        for d in F.compounding_path():
            s = C.size_trade(sp, d["start_equity"], 0.01, stop, costs)
            row = {"symbol": sym, "stop_basis": label, "stop_price": stop, "day": d["day"],
                   "start_equity": d["start_equity"], "profit_objective": d["profit_objective"],
                   "risk_cash": s["risk_cash"], "raw_lots": s["raw_lots"], "lots": s["lots"], "tradable": s["tradable"]}
            if s["tradable"]:
                for k in (3, 5):
                    o = C.net_outcome(sp, s["lots"], stop, k, costs, d["start_equity"])
                    row[f"net_win_{k}R"] = o["net_win"]
                    row[f"coverage_{k}R"] = o["net_win"] / d["profit_objective"]
                row.update({"gross_win_3R": C.net_outcome(sp, s["lots"], stop, 3, costs, d["start_equity"])["gross_win"],
                            "costs_cash": C.trade_costs(sp, s["lots"], costs)["total_cost"],
                            "required_R_single_trade": (d["profit_objective"] + C.trade_costs(sp, s["lots"], costs)["total_cost"])
                            / (stop * sp.value_per_price_per_lot * s["lots"])})
            else:
                row["equity_needed_for_min_lot"] = s["equity_needed_for_min_lot"]
            row["verdict"] = ("TARGET NOT MATHEMATICALLY REACHABLE WITH THIS SINGLE TRADE" if not s["tradable"]
                              or row.get("coverage_5R", 0) < 1 else "single 5R trade covers the objective")
            rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(RUN.RUNS, "sizing_tables.csv"), index=False)
    print(df[["symbol", "stop_basis", "day", "start_equity", "raw_lots", "lots", "tradable", "verdict"]].iloc[::5].to_string())


if __name__ == "__main__":
    c = sys.argv[1]
    {"info": cmd_info, "stack": cmd_stack, "sizing": cmd_sizing}.get(c, lambda: cmd_selected(sys.argv[2]))()
