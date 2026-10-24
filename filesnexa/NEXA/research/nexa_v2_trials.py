"""PHASE3_SIX_FAMILIES_V2: trial -> orders/labels, nulls, costs and the pre-registered selection
and verdict logic. Pure functions of certified builder outputs (nexa_v2_features); no data access,
no evaluation is run by importing or testing this module.

Conventions (pre-registered before opening, pinned with this file)
  * Times are naive UTC for the execution engine; a signal at row i has signal_time =
    time_utc[i] + 1 min (bar close) and fills at the next bar open (nexa_execution bar mode).
  * Targets are set from the SIGNAL bar close and the pre-computed stop: tp = close + d*k*|close-sl|.
    Realised R is measured from the actual fill, so spread/slippage make realised targets < k R.
  * Costs: protocol COSTS. Event slippage multiplier x3 applies to F1. Swaps: contracts.json
    swap_long/short in POINTS per lot per server rollover (x3 on Wednesday); only charges are
    applied, never credits, because the snapshot (2026-09) is not the historical swap.
  * One position at a time per (trial, symbol) (nexa_execution.run_one_at_a_time).
  * Bootstrap: stationary (Politis-Romano) on the trade sequence, mean block length = mean trades
    per active UTC day (>= 1), 5000 draws, seed 20260928; lower bound = one-sided 95 %.
  * Nulls (protocol "nulls"): timing (random direction, same times), direction (same directions,
    times re-drawn from the same UTC hour-of-week within the same year), circular shift (>= 1
    week, wrapping within the data's extent in each year); family nulls: F1 surprise shuffle within event_id; F2 random range
    (certified builder); F3 matched zone (same size, side and distance from price at a non-FVG
    HTF close in the same UTC hour-of-week and year); F5 same rule in London hours.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

import nexa_execution as ex
import nexa_robust as rb
import nexa_v2_features as nf
import protocols_phase3_v2 as pv

SEED = 20260928
N_DRAWS = pv.TESTS["null_permutations"]
N_BOOT = 5000
MIN_TRADES_REPORT = pv.TESTS["min_trades_report"]
TF_MIN = {"M5": 5, "M15": 15}
FILL_THROUGH = {"touch": 0.0, "through_1pt": 1.0, "through_2pt": 2.0}
EVENT_SLIP_X = pv.COSTS["slippage"]["event_multiplier"]


def instrument(symbol: str, contracts: dict) -> ex.Instrument:
    c = contracts[symbol]
    base, quote = nf.SYMBOL_CCY[symbol]
    return ex.Instrument(symbol, float(c["point"]), float(c["trade_contract_size"]),
                         account_is_quote=(quote == "USD"), account_is_base=(base == "USD"))


def exec_config(exp: str, cfg: dict) -> ex.ExecConfig:
    c = pv.COSTS
    frac = c["slippage"]["spread_frac"] * (EVENT_SLIP_X if exp == "F1_MACRO_EVENT" else 1.0)
    through = FILL_THROUGH[cfg["fill_rule"]] if "fill_rule" in cfg else 1.0
    return ex.ExecConfig(latency_ms=c["latency_ms"], commission_per_lot_side=c["commission_per_lot_side_usd"],
                         slip_points=c["slippage"]["points"], slip_spread_frac=frac, through_points=through)


def load_contracts(path: str) -> dict:
    with open(path) as fh:
        return json.load(fh)


# ---------------------------------------------------------------- planned orders

@dataclass(frozen=True)
class Planned:
    order: ex.Order
    row: int
    ref: float                  # signal-bar close: the price every level is expressed against


def _naive(t) -> pd.Series:
    return pd.Series(pd.to_datetime(t, utc=True)).dt.tz_convert("UTC").dt.tz_localize(None)


def quotes(bars: pd.DataFrame, symbol: str, contracts: dict):
    q = pd.DataFrame({"time": _naive(bars["time_utc"]).to_numpy(), "open": bars["open"].to_numpy(float),
                      "high": bars["high"].to_numpy(float), "low": bars["low"].to_numpy(float),
                      "close": bars["close"].to_numpy(float), "spread": bars["spread"].to_numpy(float)})
    return ex.quotes_from_bars(q, float(contracts[symbol]["point"]))


def _session_end(sig_time: pd.Timestamp, end_min: int) -> pd.Timestamp:
    day = sig_time.normalize()
    end = day + pd.Timedelta(minutes=end_min)
    return end if end > sig_time else end + pd.Timedelta(days=1)


def plan_orders(exp: str, claim: str, cfg: dict, bars: pd.DataFrame, feats: pd.DataFrame) -> list[Planned]:
    """Orders for one ACTIVE trial configuration (H3a has no orders; see h3a_events)."""
    t = _naive(bars["time_utc"])
    cl = bars["close"].to_numpy(float)
    out: list[Planned] = []
    fmt = nf._fmt
    if exp == "F1_MACRO_EVENT":
        col = f"sig_f1_z{fmt(cfg['z_star'])}_d{cfg['delta_min']}"
        sl_col = feats[f"f1_sl_d{cfg['delta_min']}"].to_numpy(float)
        for i in np.flatnonzero(feats[col].to_numpy() != 0):
            d = int(feats[col].iat[i])
            st = t.iat[i] + nf.BAR
            sl = sl_col[i]
            out.append(Planned(ex.Order(st, d, "MARKET", sl=sl, tp=cl[i] + d * cfg["target_r"] * abs(cl[i] - sl),
                                        exit_time=st + pd.Timedelta(minutes=cfg["hold_min"]), tag=f"r{i}"), i, cl[i]))
    elif exp == "F2_XAU_SESSION_BREAKOUT":
        h = cfg["asian_end_utc_hour"]
        col = f"sig_f2_b{fmt(cfg['buffer_b'])}_ae{h}"
        for i in np.flatnonzero(feats[col].to_numpy() != 0):
            d = int(feats[col].iat[i])
            st = t.iat[i] + nf.BAR
            sl = feats[f"f2_mid_ae{h}"].iat[i] if cfg["stop"] == "range_mid" else cl[i] - d * 10.0 * feats["f2_atr"].iat[i]
            if not np.isfinite(sl) or d * (cl[i] - sl) <= 0:
                continue
            out.append(Planned(ex.Order(st, d, "MARKET", sl=sl, tp=cl[i] + d * cfg["target_r"] * abs(cl[i] - sl),
                                        exit_time=st.normalize() + pd.Timedelta(hours=16), tag=f"r{i}"), i, cl[i]))
    elif exp == "F3_FVG_RETRACEMENT" and claim == "H3b_limit_expectancy":
        tf, m = cfg["timeframe"], cfg["min_size_atr"]
        step = pd.Timedelta(minutes=TF_MIN[tf])
        sig = feats[f"sig_f3_{tf}_m{fmt(m)}"].to_numpy()
        top, bot, atr = (feats[f"f3_{k}_{tf}"].to_numpy(float) for k in ("top", "bot", "atr"))
        sched = np.r_[0, np.cumsum(bars["sched_inst"].to_numpy(bool))]
        rows = np.flatnonzero(sig != 0)
        by_dir = {1: np.flatnonzero(sig > 0), -1: np.flatnonzero(sig < 0)}
        for i in rows:
            d = int(sig[i])
            st = t.iat[i] + nf.BAR
            expiry = st + cfg["validity_bars"] * step
            opp_list = by_dir[-d]
            k_ = int(np.searchsorted(opp_list, i, side="right"))
            if k_ < opp_list.size:                               # a new opposite zone cancels the order
                expiry = min(expiry, t.iat[int(opp_list[k_])] + nf.BAR)
            j_end = int(np.searchsorted(t.to_numpy(), expiry.to_datetime64(), side="left"))
            if sched[j_end] - sched[i] > 0:                   # scheduled HIGH event inside the validity window
                continue
            edge = top[i] if d > 0 else bot[i]
            level = edge if cfg["entry"] == "edge" else (top[i] + bot[i]) / 2
            sl = bot[i] - 0.25 * atr[i] if d > 0 else top[i] + 0.25 * atr[i]
            far = bot[i] if d > 0 else top[i]
            out.append(Planned(ex.Order(st, d, "LIMIT", sl=sl, tp=level + d * cfg["target_r"] * abs(level - sl), level=level,
                                        expiry=expiry, cancel_level=far, max_hold=48 * step, tag=f"r{i}"), i, cl[i]))
    elif exp == "F5_ASIAN_MEAN_REVERSION":
        s = str(cfg["session_start_utc_hour"])
        out = _f5_plan(cfg, s, nf.F5_SESSIONS[s][1], t, cl, feats)
    else:
        raise ValueError(f"no orders for {exp}/{claim}")
    return out


def _f5_plan(cfg: dict, s: str, end_min: int, t: pd.Series, cl: np.ndarray, feats: pd.DataFrame) -> list[Planned]:
    fmt = nf._fmt
    col = f"sig_f5_z{fmt(cfg['z_star'])}_a{cfg['anchor']}_s{s}"
    mu = feats[f"f5_mu_a{cfg['anchor']}_s{s}"].to_numpy(float)
    sg = feats[f"f5_sigma_s{s}"].to_numpy(float)
    out = []
    for i in np.flatnonzero(feats[col].to_numpy() != 0):
        d = int(feats[col].iat[i])
        st = t.iat[i] + nf.BAR
        ex_t = min(st + pd.Timedelta(minutes=cfg["hold_bars"]), _session_end(st, end_min))
        out.append(Planned(ex.Order(st, d, "MARKET", sl=cl[i] - d * cfg["stop_k"] * sg[i], tp=mu[i], exit_time=ex_t,
                                    tag=f"r{i}"), i, cl[i]))
    return out


def f5_london_null(cfg: dict, bars: pd.DataFrame, feats: pd.DataFrame) -> list[Planned]:
    return _f5_plan(cfg, "LDN", nf.F5_NULL_SESSIONS["LDN"][1], _naive(bars["time_utc"]), bars["close"].to_numpy(float), feats)


# ---------------------------------------------------------------- simulation + swap

def rollovers(entry: pd.Timestamp, exit_: pd.Timestamp) -> int:
    """Server-midnight rollovers in (entry, exit], Wednesday counted 3x (swap_rollover3days=3)."""
    import nexa_time
    a, b = nexa_time.utc_to_server(pd.Series([entry, exit_])).tolist()
    n = 0
    day = a.normalize() + pd.Timedelta(days=1)
    while day <= b:
        n += 3 if day.dayofweek == 3 else 1          # the rollover INTO Thursday is Wednesday's
        day += pd.Timedelta(days=1)
    return n


def simulate(planned: list[Planned], bars: pd.DataFrame, symbol: str, contracts: dict, cfg_exec: ex.ExecConfig) -> pd.DataFrame:
    q = quotes(bars, symbol, contracts)
    inst = instrument(symbol, contracts)
    tr = ex.run_one_at_a_time(q, [p.order for p in planned], inst, cfg_exec)
    if tr.empty:
        return tr
    c = contracts[symbol]
    swap_cost = []
    for _, r in tr.iterrows():
        if r["status"] not in ("FILLED_CLOSED", "OPEN_AT_END"):
            swap_cost.append(0.0)
            continue
        side = c["swap_long"] if r["direction"] > 0 else c["swap_short"]
        pts = -min(float(side), 0.0) * rollovers(pd.Timestamp(r["entry_time"]), pd.Timestamp(r["exit_time"]))
        swap_cost.append(pts * float(c["point"]))
    tr["swap_price"] = swap_cost
    tr["r_net_swap"] = tr["r_net"] - tr["swap_price"] / tr["risk"]
    return tr


def filled_r(trades: pd.DataFrame) -> np.ndarray:
    if trades.empty:
        return np.array([])
    f = trades[trades["status"].isin(["FILLED_CLOSED", "OPEN_AT_END"])]
    return f["r_net_swap"].to_numpy(float)


# ---------------------------------------------------------------- F3 H3a

def h3a_events(cfg: dict, bars: pd.DataFrame, feats: pd.DataFrame, sig_override: pd.DataFrame | None = None) -> pd.DataFrame:
    """One row per qualifying zone: touched within validity_bars HTF bars after it became visible.
    Bullish zone (below price) touched when bid low <= top; bearish when bid high >= bot."""
    tf, m = cfg["timeframe"], cfg["min_size_atr"]
    f = feats if sig_override is None else sig_override
    sig = f[f"sig_f3_{tf}_m{nf._fmt(m)}"].to_numpy()
    top, bot = (f[f"f3_{k}_{tf}"].to_numpy(float) for k in ("top", "bot"))
    t = nf.ns(bars["time_utc"])
    hi, lo = bars["high"].to_numpy(float), bars["low"].to_numpy(float)
    span = cfg["validity_bars"] * TF_MIN[tf] * int(nf.BAR.value)
    rows = []
    for i in np.flatnonzero(sig != 0):
        start = i + 1
        stop = int(np.searchsorted(t, t[i] + int(nf.BAR.value) + span, side="left"))
        if stop <= start:
            continue
        touched = lo[start:stop].min() <= top[i] if sig[i] > 0 else hi[start:stop].max() >= bot[i]
        complete = t[-1] >= t[i] + int(nf.BAR.value) + span
        rows.append({"row": int(i), "dir": int(sig[i]), "touched": bool(touched), "complete": bool(complete)})
    return pd.DataFrame(rows, columns=["row", "dir", "touched", "complete"])


def matched_zones(cfg: dict, bars: pd.DataFrame, feats: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Null zones: for each real zone, same size / side / distance from the close, placed at a
    random non-FVG HTF-close row of the same UTC hour-of-week and year."""
    tf, m = cfg["timeframe"], cfg["min_size_atr"]
    col = f"sig_f3_{tf}_m{nf._fmt(m)}"
    sig = feats[col].to_numpy()
    top, bot = (feats[f"f3_{k}_{tf}"].to_numpy(float) for k in ("top", "bot"))
    cl = bars["close"].to_numpy(float)
    mod = nf.minute_of_day(bars)
    t = pd.to_datetime(bars["time_utc"], utc=True)
    how = (t.dt.dayofweek * 24 + t.dt.hour).to_numpy()
    yr = t.dt.year.to_numpy()
    cand = (mod % TF_MIN[tf] == TF_MIN[tf] - 1) & (feats[f"f3_dir_{tf}"].to_numpy() == 0)
    rng = np.random.default_rng(seed)
    n = len(bars)
    out = {col: np.zeros(n), f"f3_top_{tf}": np.full(n, np.nan), f"f3_bot_{tf}": np.full(n, np.nan)}
    pool: dict = {}
    for i in np.flatnonzero(sig != 0):
        key = (how[i], yr[i])
        if key not in pool:
            pool[key] = np.flatnonzero(cand & (how == how[i]) & (yr == yr[i]))
        p = pool[key]
        if p.size == 0:
            continue
        j = int(p[rng.integers(0, p.size)])
        size = top[i] - bot[i]
        if sig[i] > 0:
            nt = cl[j] - (cl[i] - top[i])
            nb = nt - size
        else:
            nb = cl[j] + (bot[i] - cl[i])
            nt = nb + size
        out[col][j], out[f"f3_top_{tf}"][j], out[f"f3_bot_{tf}"][j] = sig[i], nt, nb
    return pd.DataFrame(out, index=bars.index)


# ---------------------------------------------------------------- generic nulls

def _mirror(o: ex.Order, ref: float) -> ex.Order:
    f = lambda x: None if x is None else 2 * ref - x
    return replace(o, direction=-o.direction, sl=f(o.sl), tp=f(o.tp), level=f(o.level), cancel_level=f(o.cancel_level))


def _relocate(p: Planned, j: int, t: pd.Series, cl: np.ndarray) -> Planned:
    """Same geometry relative to the close, moved to row j (all times shifted by the same amount)."""
    dp, dt = cl[j] - p.ref, (t.iat[j] + nf.BAR) - pd.Timestamp(p.order.signal_time)
    o = p.order
    g = lambda x: None if x is None else x + dp
    h = lambda x: None if x is None else pd.Timestamp(x) + dt
    return Planned(replace(o, signal_time=o.signal_time + dt, sl=g(o.sl), tp=g(o.tp), level=g(o.level),
                           cancel_level=g(o.cancel_level), expiry=h(o.expiry), exit_time=h(o.exit_time)), j, cl[j])


def null_timing(planned: list[Planned], seed: int) -> list[Planned]:
    rng = np.random.default_rng(seed)
    flip = rng.integers(0, 2, len(planned)).astype(bool)
    return [Planned(_mirror(p.order, p.ref), p.row, p.ref) if f else p for p, f in zip(planned, flip, strict=True)]


def null_direction(planned: list[Planned], bars: pd.DataFrame, seed: int) -> list[Planned]:
    t = _naive(bars["time_utc"])
    cl = bars["close"].to_numpy(float)
    tt = pd.to_datetime(bars["time_utc"], utc=True)
    how = (tt.dt.dayofweek * 24 + tt.dt.hour).to_numpy()
    yr = tt.dt.year.to_numpy()
    rng = np.random.default_rng(seed)
    out, pool = [], {}
    for p in planned:
        key = (how[p.row], yr[p.row])
        if key not in pool:
            pool[key] = np.flatnonzero((how == key[0]) & (yr == key[1]))
        j = int(pool[key][rng.integers(0, pool[key].size)])
        out.append(_relocate(p, j, t, cl))
    return out


def null_circular(planned: list[Planned], bars: pd.DataFrame, seed: int) -> list[Planned]:
    t = _naive(bars["time_utc"])
    tv = t.to_numpy()
    cl = bars["close"].to_numpy(float)
    rng = np.random.default_rng(seed)
    years = t.dt.year.to_numpy()
    offsets: dict = {}
    out = []
    for p in planned:
        st = pd.Timestamp(p.order.signal_time)
        in_y = np.flatnonzero(years == st.year)
        if in_y.size == 0:
            continue
        y0, y1 = t.iat[int(in_y[0])], t.iat[int(in_y[-1])] + nf.BAR      # the data's extent in that year
        span = (y1 - y0).total_seconds()
        if span <= 14 * 86400:
            continue
        if st.year not in offsets:
            offsets[st.year] = rng.uniform(7 * 86400, span - 7 * 86400)
        new = y0 + pd.Timedelta(seconds=((st - y0).total_seconds() + offsets[st.year]) % span)
        j = int(np.searchsorted(tv, (new - nf.BAR).to_datetime64(), side="left"))
        if j >= len(t) or t.iat[j].year != st.year:
            continue
        out.append(_relocate(p, j, t, cl))
    return out


def f1_shuffled_calendar(cal: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Surprise-shuffled null: permute S = (actual - forecast)/prior_sd within each event_id among
    f1-eligible rows, by rewriting actual = forecast + S_perm * prior_sd."""
    c = cal.copy()
    m = c["f1_eligible"].astype(bool)
    s = (c.loc[m, "actual"].astype(float) - c.loc[m, "forecast"].astype(float)) / c.loc[m, "prior_surprise_sd"].astype(float)
    rng = np.random.default_rng(seed)
    perm = s.groupby(c.loc[m, "event_id"]).transform(lambda x: x.to_numpy()[rng.permutation(len(x))])
    c.loc[m, "actual"] = c.loc[m, "forecast"].astype(float) + perm * c.loc[m, "prior_surprise_sd"].astype(float)
    return c


# ---------------------------------------------------------------- statistics / selection / verdict

def stationary_bootstrap_mean(r: np.ndarray, mean_block: float, n_boot: int = N_BOOT, seed: int = SEED) -> np.ndarray:
    """Politis-Romano stationary bootstrap of the mean (geometric blocks, circular wrap)."""
    a = np.asarray(r, float)
    n = a.size
    rng = np.random.default_rng(seed)
    p = 1.0 / max(1.0, mean_block)
    reps = np.empty(n_boot)
    k = np.arange(n)
    for b in range(n_boot):
        new = rng.random(n) < p
        new[0] = True
        starts = rng.integers(0, n, n)
        first = np.maximum.accumulate(np.where(new, k, 0))          # index where the current block began
        idx = (starts[first] + (k - first)) % n
        reps[b] = a[idx].mean()
    return reps


def mean_block_length(entry_times) -> float:
    d = pd.to_datetime(pd.Series(entry_times)).dt.normalize()
    return max(1.0, float(d.value_counts().mean())) if len(d) else 1.0


def lower_bound(r: np.ndarray, entry_times, alpha: float = pv.TESTS["alpha"]) -> dict:
    if len(r) < 2:
        return {"n": len(r), "mean": float("nan"), "lower": float("nan"), "p_le_zero": float("nan")}
    reps = stationary_bootstrap_mean(r, mean_block_length(entry_times))
    return {"n": len(r), "mean": float(np.mean(r)), "lower": float(np.quantile(reps, alpha)),
            "p_le_zero": float(np.mean(reps <= 0.0))}


def permutation_p(observed: float, null_stats: np.ndarray) -> float:
    ns = np.asarray(null_stats, float)
    ns = ns[np.isfinite(ns)]
    return float((1 + np.sum(ns >= observed)) / (1 + ns.size))


def select(val_rows: list[dict]) -> str | None:
    """Pre-registered selection per (experiment, claim, symbol): highest VAL lower bound among trials
    with >= min_trades_report VAL observations; ties -> fewer parameters, then trial_id."""
    ok = [r for r in val_rows if r["n"] >= MIN_TRADES_REPORT and np.isfinite(r["lower"])]
    if not ok:
        return None
    ok.sort(key=lambda r: (-r["lower"], r["n_params"], r["trial_id"]))
    return ok[0]["trial_id"]


def primary_verdicts(groups: list[dict], dsr_trials: int, var_sr_trials: float) -> list[dict]:
    """groups: one dict per primary test with OOS r (or H3a diff draws), null p-values, pbo, n.
    PASS requires ALL: n >= min_trades_promote, bootstrap p <= alpha, every null p <= alpha
    (intersection-union), BH-FDR rejection across ALL primary tests at q, DSR >= dsr_min
    (bar families), PBO <= pbo_max. Anything else is NOT_DEMONSTRATED; there is no other verdict."""
    T = pv.TESTS
    pvals = [max([g["p_boot"], *g["null_p"].values()]) if np.isfinite(g["p_boot"]) else 1.0 for g in groups]
    bh = rb.benjamini_hochberg(np.clip(pvals, 0, 1), q=T["fdr_q"])
    out = []
    for g, p, rej in zip(groups, pvals, bh, strict=True):
        dsr = rb.deflated_sharpe(g["r"], dsr_trials, var_sr_trials) if len(g["r"]) >= 3 else float("nan")
        checks = {"n": g["n"] >= T["min_trades_promote"], "p_iut": p <= T["alpha"], "bh": bool(rej),
                  "dsr": (np.isfinite(dsr) and dsr >= T["dsr_min"]) if g.get("uses_dsr", True) else True,
                  "pbo": np.isfinite(g["pbo"]) and g["pbo"] <= T["pbo_max"]}
        out.append({**{k: g[k] for k in ("group",)}, "p_iut": p, "dsr": dsr, "checks": checks,
                    "verdict": "PASS_CANDIDATE" if all(checks.values()) else "NOT_DEMONSTRATED"})
    return out


def n_params(cfg: dict) -> int:
    return len(cfg)
