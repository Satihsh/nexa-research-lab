"""PHASE3_SIX_FAMILIES_V2 evaluation DRIVER: universe x period -> registry records.

Pinned before opening so that every result recorded after opening is produced by pinned code with no
free parameters. It never opens the campaign, never selects, and never runs by itself; importing or
testing it touches no market data (tests inject synthetic bars).

Pre-registered rules
  * Window = the full declared period (DEV/VAL/OOS) or the WF calendar year, in UTC.
  * Signals are eligible only when decision_ts >= window start + embargo (DEV: window start) and
    decision_ts + max_label <= window end; bars after the window end are never passed to the engine,
    so no label can use data beyond the period (purge).
  * Warm-up: builders receive up to WARMUP_DAYS of bars BEFORE the window as trailing inputs only
    (no signal, order or result is taken from them). For OOS this reads the end of the EXCLUDED period
    as trailing input at OOS evaluation time, i.e. after the OOS period has ended.
  * Every trial of the group is run; zero-trade trials are recorded (n = 0), never dropped.
  * H3a statistic: mean(touched | FVG) - mean(touched | matched zone); lower bound = alpha-quantile of
    the difference of independent stationary-bootstrap replicates (seeds SEED, SEED + 1).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import nexa_registry2 as r2
import nexa_stats as st
import nexa_v2_features as nf
import nexa_v2_trials as tr

WARMUP_DAYS = 100


def zstr(ts: pd.Timestamp) -> str:
    ts = pd.Timestamp(ts)
    ts = ts.tz_convert("UTC").tz_localize(None) if ts.tzinfo is not None else ts
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


M1_COLS = ["time_utc", "time_server", "open", "high", "low", "close", "spread"]


def load_m1(path: str) -> pd.DataFrame:
    """Canonical Pepperstone M1 (nexa_m1_history output). Rows whose server time is NONEXISTENT or
    AMBIGUOUS under the clock (no UTC time) are dropped; they are counted in the manifest."""
    b = pd.read_csv(path, usecols=M1_COLS + ["time_status"])
    b = b[b["time_status"].eq("OK")].drop(columns=["time_status"])
    b["time_utc"] = pd.to_datetime(b["time_utc"], utc=True)
    b["time_server"] = pd.to_datetime(b["time_server"])
    return b.sort_values("time_utc").reset_index(drop=True)


def prepare(bars: pd.DataFrame, cal: pd.DataFrame, symbol: str, experiment: str) -> tuple[pd.DataFrame, dict]:
    """Attach the scheduled-event flags and, for F1, the release scores (certified paths only)."""
    b = nf.attach_schedule(bars, cal, symbol)
    info: dict = {}
    if experiment == "F1_MACRO_EVENT":
        b, info = nf.attach_f1(b, nf.f1_event_table(cal, symbol))
    return b, info


def window(protocol: dict, period: str, wf_year: int | None = None) -> tuple[pd.Timestamp, pd.Timestamp]:
    per = protocol["periods_utc"]
    if period == "WF":
        if wf_year not in per["WF_YEARS"]:
            raise ValueError(f"wf_year {wf_year} not declared")
        return pd.Timestamp(f"{wf_year}-01-01"), pd.Timestamp(f"{wf_year + 1}-01-01")
    return (pd.Timestamp(r2.parse_utc(per[period][0])).tz_localize(None),
            pd.Timestamp(r2.parse_utc(per[period][1])).tz_localize(None))


def slice_bars(bars: pd.DataFrame, ws: pd.Timestamp, we: pd.Timestamp) -> pd.DataFrame:
    t = pd.to_datetime(bars["time_utc"], utc=True).dt.tz_localize(None)
    m = (t >= ws - pd.Timedelta(days=WARMUP_DAYS)) & (t < we)
    return bars.loc[m].reset_index(drop=True)


def _eligible(planned: list, ws_entry: pd.Timestamp, we: pd.Timestamp, max_label: pd.Timedelta) -> list:
    return [p for p in planned if pd.Timestamp(p.order.signal_time) >= ws_entry
            and pd.Timestamp(p.order.signal_time) + max_label <= we]


def _trade_metrics(trades: pd.DataFrame) -> dict:
    r = tr.filled_r(trades)
    filled = trades[trades["status"].isin(["FILLED_CLOSED", "OPEN_AT_END"])] if len(trades) else trades
    lb = tr.lower_bound(r, filled["entry_time"] if len(filled) else [])
    m = {"n": int(r.size), "lower": lb["lower"], "mean": lb["mean"], "p_le_zero": lb["p_le_zero"],
         "open_at_end": int((trades["status"] == "OPEN_AT_END").sum()) if len(trades) else 0}
    if r.size:
        m.update({k: v for k, v in st.trade_metrics(r).items() if isinstance(v, (int, float))})
    if len(trades):
        m["fill"] = tr.ex.fill_summary(trades)
    return m


def _h3a_metrics(cfg: dict, bars: pd.DataFrame, feats: pd.DataFrame, ws_entry, we, max_label) -> dict:
    t = pd.to_datetime(bars["time_utc"], utc=True).dt.tz_localize(None)

    def keep(ev):
        if ev.empty:
            return ev
        dec = t.iloc[ev["row"].to_numpy()].to_numpy() + np.timedelta64(1, "m")
        ok = (dec >= np.datetime64(ws_entry)) & (dec + np.timedelta64(int(max_label.total_seconds()), "s") <= np.datetime64(we))
        return ev[ok & ev["complete"].to_numpy()]
    real = keep(tr.h3a_events(cfg, bars, feats))
    null = keep(tr.h3a_events(cfg, bars, feats, tr.matched_zones(cfg, bars, feats, tr.SEED)))
    if len(real) < 2 or len(null) < 2:
        return {"n": len(real), "n_matched": len(null), "lower": float("nan"), "diff": float("nan")}
    a, b = real["touched"].to_numpy(float), null["touched"].to_numpy(float)
    ra = tr.stationary_bootstrap_mean(a, tr.mean_block_length(t.iloc[real["row"]]), seed=tr.SEED)
    rb_ = tr.stationary_bootstrap_mean(b, tr.mean_block_length(t.iloc[null["row"]]), seed=tr.SEED + 1)
    d = ra - rb_
    return {"n": len(real), "n_matched": len(null), "touch_rate": float(a.mean()),
            "touch_rate_matched": float(b.mean()), "diff": float(a.mean() - b.mean()),
            "lower": float(np.quantile(d, tr.pv.TESTS["alpha"])), "p_le_zero": float(np.mean(d <= 0))}


def run_group(protocol: dict, claim: str, symbol: str, period: str, bars: pd.DataFrame, contracts: dict,
              trials: list[dict], wf_year: int | None = None, cal: pd.DataFrame | None = None) -> list[dict]:
    """bars: canonical M1 for `symbol` with schedule columns attached (nf.attach_schedule) and, for F1,
    the release scores attached (nf.attach_f1). Returns one registry-ready record per trial."""
    exp = protocol["experiment"]
    if protocol["status"] != "ACTIVE":
        raise ValueError(f"{exp} is {protocol['status']}")
    ws, we = window(protocol, period, wf_year)
    emb = pd.Timedelta(minutes=protocol["purge_embargo"]["embargo_minutes"])
    max_label = pd.Timedelta(minutes=protocol["purge_embargo"]["max_label_minutes"])
    ws_entry = ws if period == "DEV" else ws + emb
    b = slice_bars(bars, ws, we)
    feats = nf.BUILDERS[exp][0](b)
    out = []
    for trial in sorted(trials, key=lambda x: x["trial_id"]):
        if (trial["experiment"], trial["claim"], trial["symbol"]) != (exp, claim, symbol):
            raise ValueError("trial does not belong to this group")
        cfg = trial["config"]
        if claim == "H3a_revisit":
            metrics = _h3a_metrics(cfg, b, feats, ws_entry, we, max_label)
            first, last = ws_entry, ws_entry
        else:
            planned = _eligible(tr.plan_orders(exp, claim, cfg, b, feats), ws_entry, we, max_label)
            trades = tr.simulate(planned, b, symbol, contracts, tr.exec_config(exp, cfg)) if planned else pd.DataFrame()
            metrics = _trade_metrics(trades) if len(trades) else {"n": 0, "lower": float("nan")}
            filled = trades[trades["status"].isin(["FILLED_CLOSED", "OPEN_AT_END"])] if len(trades) else trades
            first = pd.Timestamp(filled["entry_time"].min()) if len(filled) else ws_entry
            last = pd.Timestamp(filled["exit_time"].max()) if len(filled) else ws_entry
        metrics.update({"n_params": tr.n_params(cfg), "trial_id": trial["trial_id"]})
        out.append({"trial_id": trial["trial_id"], "period": period, "wf_year": wf_year,
                    "window_utc": [zstr(ws), zstr(we)], "first_entry_utc": zstr(max(first, ws_entry)),
                    "max_label_end_utc": zstr(min(max(last, max(first, ws_entry)), we)), "metrics": metrics})
    return out


def record_all(reg: r2.RegistryV2, anchor: str, checkpoint: dict, records: list[dict]) -> dict:
    """Records every row through the registry (compare-and-swap per call). Returns the new head, which
    must be published off-machine before any further call."""
    v = reg.verify(anchor, checkpoint=checkpoint)
    c, universe = v["campaign"], v["universe"]
    data, code = reg.digest(c["pins"]["data"]), reg.digest(c["pins"]["code"])
    cp = checkpoint
    for rec in records:
        if rec["trial_id"] not in universe:
            raise r2.RegistryError("trial not in the pinned universe")
        builders = [nf.BUILDERS[universe[rec["trial_id"]]["experiment"]][0]]
        e = reg.record(anchor, rec["trial_id"], rec["period"], rec["window_utc"], rec["first_entry_utc"],
                       rec["max_label_end_utc"], data, code, builders, _json_safe(rec["metrics"]),
                       wf_year=rec["wf_year"], checkpoint=cp)
        cp = {"seq": e["seq"], "entry_sha256": e["entry_sha256"]}
    return cp


def _json_safe(x):
    if isinstance(x, dict):
        return {str(k): _json_safe(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_json_safe(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        return None if not np.isfinite(x) else float(x)
    return x
