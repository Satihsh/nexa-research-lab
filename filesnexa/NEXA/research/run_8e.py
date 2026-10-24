"""RESEARCH_8E_V1 orchestration (pinned with the campaign; no free parameters).

  python run_8e.py tables            build + cache per-base signal tables (all variant masks attached)
  python run_8e.py dev               DEV metrics for every trial -> runs_8e/dev_metrics.csv (exploration)
  python run_8e.py val <seq> <head>  ONE VAL record per trial into registry_8e (compare-and-swap chain)
  python run_8e.py select <seq> <head>   pinned selection rule per group, sealed before the OOS start
  python run_8e.py analysis          information / redundancy / stress / capital-velocity / DSR / PBO
Every number comes from nexa_8e_research (pinned); this file only loops over the pinned universe.
"""
from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

import nexa_8e_engines as E
import nexa_8e_research as R
import nexa_registry2 as r2
import protocols_8e as P

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs_8e")
CACHE = os.path.join(RUNS, "cache")
REG = os.path.join(HERE, "registry_8e")
VARIANTS = R.STACK + R.SINGLE + R.THRESH
EMBARGO = pd.Timedelta(minutes=P.COMMON["purge_embargo"]["embargo_minutes"])
MAX_LABEL = pd.Timedelta(minutes=P.COMMON["purge_embargo"]["max_label_minutes"])


def base_key(sym, tf, n, mode, k, spread_mult=1.0):
    return f"{sym}_{tf}_dc{n}_{mode}_k{k}" + ("" if spread_mult == 1.0 else f"_sx{spread_mult:g}")


def _build_one(args):
    sym, tf, n, mode, k, spread_mult = args
    path = os.path.join(CACHE, base_key(sym, tf, n, mode, k, spread_mult) + ".pkl.gz")
    if os.path.exists(path):
        return path
    m1 = R.load_m1(sym)
    bars = E.resample_m1(m1, tf)
    feats = E.all_features(bars, n)
    sig = R.signal_outcomes(bars, feats, R.BaseCfg(sym, tf, n, mode, k), spread_mult=spread_mult)
    for v in VARIANTS:
        sig[f"m_{v}"] = R.variant_mask(v, feats, sig) if len(sig) else []
    eng = feats.iloc[sig["row"].to_numpy(int)] if len(sig) else feats.iloc[:0]
    for c in ("sq_bars_since_fire", "vei", "above_ema200", "mom_long_score", "mom_short_score", "ofi_ratio_up",
              "ofi_ratio_dn", "qb_pct", "td_bull_exhaust", "td_bear_exhaust"):
        sig[f"f_{c}"] = eng[c].to_numpy() if len(sig) else []
    os.makedirs(CACHE, exist_ok=True)
    sig.to_pickle(path, compression="gzip")
    return path


def bases(spread_mult=1.0):
    g = P.GRID
    return [(s, tf, n, mode, k, spread_mult) for s in P.SYMBOLS for tf in g["tf"] for n in g["dc_n"]
            for mode in g["entry_mode"] for k in g["target_r"]]


def load_table(sym, tf, n, mode, k, spread_mult=1.0) -> pd.DataFrame:
    return pd.read_pickle(os.path.join(CACHE, base_key(sym, tf, n, mode, k, spread_mult) + ".pkl.gz"), compression="gzip")


def trades_for(sig: pd.DataFrame, variant: str, period: str) -> pd.DataFrame:
    s, e = P.PERIODS[period]
    w = R.in_window(sig[sig[f"m_{variant}"]], s, e, EMBARGO, MAX_LABEL, first_period=(period == "DEV"))
    return R.take_non_overlapping(w)


def trial_rows():
    u = r2.derive_universe(P.build())
    return [t for t in u if t["experiment"] in ("E8_STACK", "E8_THRESH")]


def cmd_tables():
    with ProcessPoolExecutor(max_workers=6) as ex:
        for p in ex.map(_build_one, bases()):
            print("built", os.path.basename(p), flush=True)


def _metrics_row(t, period):
    c = t["config"]
    sig = load_table(t["symbol"], c["tf"], c["dc_n"], c["entry_mode"], c["target_r"])
    tr = trades_for(sig, c["variant"], period)
    m = R.metrics(tr)
    m["lower"] = R.stationary_lower(tr["r_net"].to_numpy(float), tr["entry_time"]) if m["n"] >= 2 else float("nan")
    return m, tr


def cmd_dev():
    rows = []
    for t in trial_rows():
        m, _ = _metrics_row(t, "DEV")
        rows.append({"trial_id": t["trial_id"], "experiment": t["experiment"], "symbol": t["symbol"], **t["config"], **m})
    pd.DataFrame(rows).to_csv(os.path.join(RUNS, "dev_metrics.csv"), index=False)
    print("dev rows", len(rows))


def _zs(ts: pd.Timestamp) -> str:
    return pd.Timestamp(ts).strftime("%Y-%m-%dT%H:%M:%SZ")


def cmd_val(anchor, seq, head):
    reg = r2.RegistryV2(REG)
    cp = {"seq": int(seq), "entry_sha256": head}
    c0 = reg.verify(anchor, checkpoint=cp)["campaign"]
    data, code = reg.digest(c0["pins"]["data"]), reg.digest(c0["pins"]["code"])
    vs, ve = P.PERIODS["VAL"]
    done = {r["trial_id"] for r in reg._results() if r["period"] == "VAL"}
    out = []
    for t in trial_rows():
        if t["trial_id"] in done:
            continue
        m, tr = _metrics_row(t, "VAL")
        first = _zs(tr["entry_time"].min()) if m["n"] else _zs(pd.Timestamp(vs.rstrip("Z")) + EMBARGO)
        last = _zs(tr["exit_time"].max()) if m["n"] else first
        builder = E.features_dc20 if t["config"]["dc_n"] == 20 else E.features_dc55
        metrics = {k: (None if isinstance(v, float) and not np.isfinite(v) else v) for k, v in m.items()}
        e = reg.record(anchor, t["trial_id"], "VAL", [vs, ve], first, last, data, code, [builder], metrics, checkpoint=cp)
        cp = {"seq": e["seq"], "entry_sha256": e["entry_sha256"]}
        out.append(cp)
    print(json.dumps({"records": len(out), "head": cp}))


def cmd_select(anchor, seq, head):
    reg = r2.RegistryV2(REG)
    cp = {"seq": int(seq), "entry_sha256": head}
    v = reg.verify(anchor, checkpoint=cp)
    res = [r for r in reg._results() if r["period"] == "VAL"]
    groups: dict = {}
    for r in res:
        t = v["universe"][r["trial_id"]]
        groups.setdefault((t["experiment"], t["claim"], t["symbol"]), []).append(r)
    picks = {}
    for g, rows in sorted(groups.items()):
        ok = [r for r in rows if (r["metrics"].get("n") or 0) >= P.COMMON["tests"]["min_trades_report"]
              and r["metrics"].get("lower") is not None]
        if not ok:
            picks["|".join(g)] = None
            continue
        best = min(ok, key=lambda r: (-r["metrics"]["lower"], r["trial_id"]))
        e = reg.select_for_oos(anchor, best["trial_id"], "pinned rule: highest VAL lower bound, >= 30 trades", checkpoint=cp)
        cp = {"seq": e["seq"], "entry_sha256": e["entry_sha256"]}
        picks["|".join(g)] = {"trial_id": best["trial_id"], "config": v["universe"][best["trial_id"]]["config"],
                              "val": best["metrics"]}
    with open(os.path.join(RUNS, "selection.json"), "w") as fh:
        json.dump({"picks": picks, "head": cp}, fh, indent=1, default=str)
    print(json.dumps({"head": cp, "groups": len(picks)}))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "tables":
        cmd_tables()
    elif cmd == "dev":
        cmd_dev()
    elif cmd == "val":
        cmd_val(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "select":
        cmd_select(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        raise SystemExit(f"unknown command {cmd}")

