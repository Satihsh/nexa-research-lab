"""8-engine research harness (research only; independent of V2; never touches the live EA).

Pipeline (all pre-registered in protocols_8e.py):
  1. M1 canonical -> completed TF bars (nexa_8e_engines.resample_m1) -> causal engine features.
  2. BASELINE signals: Donchian breakout (E3) in one of two entry modes
       close_next_open : close beyond the prior-N channel -> MARKET at the next bar open;
       stop_at_channel : STOP order at the channel level valid for the next bar only (intrabar
                         touch = trade-through of the stop; both sides placed when both allowed).
  3. Every baseline signal is simulated ONCE and INDEPENDENTLY with nexa_execution (bar mode: next-bar
     fills, bid/ask via recorded spread, stop wins ambiguous bars, gaps fill at the open, commission
     from the observed Pepperstone schedule, slippage 0.5 x spread) plus swap charges (charges only).
     Stop = 1.0 x ATR14 (at the signal bar) from the fill, target = k x stop, time stop 48 bars.
  4. Engine add-ons are FILTERS evaluated at the signal bar (information available at decision time).
  5. Trading performance per trial = filtered signals taken greedily one-at-a-time (no overlap).
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np
import pandas as pd

import nexa_execution as ex
import nexa_time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
M1_PATH = os.path.join(ROOT, "data", "pepperstone", "m1_canonical", "PEPPERSTONE_{}_M1_canonical.csv.gz")
TF_MIN = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60}
HOLD_BARS = 48
STOP_ATR = 1.0
COMMISSION_PER_LOT_SIDE = 4.0          # observed: $0.04 per 0.01 lot per side (spec probe 2026-10-01)
SLIP_SPREAD_FRAC = 0.5
SPEC = {"XAUUSD": {"point": 0.01, "contract": 100.0, "swap_long": -84.33, "swap_short": 32.63},
        "EURUSD": {"point": 1e-5, "contract": 100000.0, "swap_long": -7.29, "swap_short": 1.54},
        "GBPUSD": {"point": 1e-5, "contract": 100000.0, "swap_long": -3.35, "swap_short": -1.72}}


def load_m1(symbol: str, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    b = pd.read_csv(M1_PATH.format(symbol), usecols=["time_utc", "open", "high", "low", "close", "tick_volume",
                                                     "spread", "time_status"])
    b = b[b["time_status"].eq("OK")].drop(columns=["time_status"])
    if start:
        b = b[b["time_utc"] >= start]
    if end:
        b = b[b["time_utc"] < end]
    return b.reset_index(drop=True)


@dataclass(frozen=True)
class BaseCfg:
    symbol: str
    tf: str
    dc_n: int
    entry_mode: str        # close_next_open | stop_at_channel
    target_r: float


def _quotes(bars: pd.DataFrame, point: float):
    q = pd.DataFrame({"time": pd.to_datetime(bars["time_utc"], utc=True).dt.tz_localize(None).to_numpy(),
                      "open": bars["open"].to_numpy(float), "high": bars["high"].to_numpy(float),
                      "low": bars["low"].to_numpy(float), "close": bars["close"].to_numpy(float),
                      "spread": bars["spread"].fillna(0).to_numpy(float)})
    return ex.quotes_from_bars(q, point)


def _rollovers(entry, exit_) -> int:
    a, b = nexa_time.utc_to_server(pd.Series([pd.Timestamp(entry), pd.Timestamp(exit_)])).tolist()
    n, day = 0, a.normalize() + pd.Timedelta(days=1)
    while day <= b:
        n += 3 if day.dayofweek == 3 else 1
        day += pd.Timedelta(days=1)
    return n


def signal_outcomes(bars: pd.DataFrame, feats: pd.DataFrame, cfg: BaseCfg, spread_mult: float = 1.0) -> pd.DataFrame:
    """One row per baseline signal (decision bar i, direction d), simulated independently."""
    sp = SPEC[cfg.symbol]
    b = bars.copy()
    b["spread"] = b["spread"].fillna(0) * spread_mult
    q = _quotes(b, sp["point"])
    inst = ex.Instrument(cfg.symbol, sp["point"], sp["contract"])
    xc = ex.ExecConfig(latency_ms=250, commission_per_lot_side=COMMISSION_PER_LOT_SIDE, slip_points=0.0,
                       slip_spread_frac=SLIP_SPREAD_FRAC, through_points=1.0, bar_seconds=TF_MIN[cfg.tf] * 60)
    t = pd.to_datetime(b["time_utc"], utc=True).dt.tz_localize(None)
    step = pd.Timedelta(minutes=TF_MIN[cfg.tf])
    cl = b["close"].to_numpy(float)
    a = feats["atr14"].to_numpy(float)
    rows = []
    if cfg.entry_mode == "close_next_open":
        cand = [(i, 1) for i in np.flatnonzero(feats["brk_close_up"].to_numpy() == 1)] + \
               [(i, -1) for i in np.flatnonzero(feats["brk_close_dn"].to_numpy() == 1)]
    else:   # stop at the channel that will apply to bar i+1 = max/min of bars i-N+1..i (known at close i)
        up_next = b["high"].rolling(cfg.dc_n, min_periods=cfg.dc_n).max().to_numpy(float)
        lo_next = b["low"].rolling(cfg.dc_n, min_periods=cfg.dc_n).min().to_numpy(float)
        cand = [(i, 1) for i in range(len(b)) if np.isfinite(up_next[i])] + \
               [(i, -1) for i in range(len(b)) if np.isfinite(lo_next[i])]
    for i, d in sorted(cand):
        if i + 1 >= len(b) or not np.isfinite(a[i]) or a[i] <= 0:
            continue
        st = t.iat[i] + step                                    # decision at bar close
        dist = STOP_ATR * a[i]
        if cfg.entry_mode == "close_next_open":
            ref = cl[i] + (sp["point"] * b["spread"].iat[i] if d > 0 else 0.0)   # approx fill for geometry
            o = ex.Order(st, d, "MARKET", sl=ref - d * dist, tp=ref + d * cfg.target_r * dist,
                         max_hold=HOLD_BARS * step, tag=str(i))
        else:
            lvl = up_next[i] if d > 0 else lo_next[i]
            o = ex.Order(st, d, "STOP", sl=lvl - d * dist, tp=lvl + d * cfg.target_r * dist, level=lvl,
                         expiry=st + step, max_hold=HOLD_BARS * step, tag=str(i))
        r = ex.simulate_order(q, o, inst, xc)
        if r.status not in ("FILLED_CLOSED", "OPEN_AT_END"):
            continue
        swap_pts = sp["swap_long"] if d > 0 else sp["swap_short"]
        swap_cost = -min(swap_pts, 0.0) * sp["point"] * _rollovers(r.entry_time, r.exit_time)
        rows.append({"row": i, "dir": d, "signal_time": st, "entry_time": pd.Timestamp(r.entry_time),
                     "exit_time": pd.Timestamp(r.exit_time), "exit_reason": r.exit_reason, "risk": r.risk,
                     "r_gross": r.r_gross, "r_net": r.r_net - swap_cost / r.risk,
                     "cost_r": (r.commission_price + r.spread_cost_price + r.slippage_price + swap_cost) / r.risk,
                     "spread_r": r.spread_cost_price / r.risk, "comm_r": r.commission_price / r.risk,
                     "slip_r": r.slippage_price / r.risk, "swap_r": swap_cost / r.risk,
                     "mfe_r": r.mfe_r, "mae_r": r.mae_r, "status": r.status})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- engine filters (decision-time features)

STACK = ["L0_baseline", "L1_sq", "L2_vei", "L3_ema200", "L4_mom", "L5_ofi", "L6_quoteburst", "L7_td"]
SINGLE = ["A_sq", "A_vei", "A_ema200", "A_mom", "A_ofi", "A_quoteburst", "A_td"]
THRESH = [f"vei_{x}" for x in ("1.0", "1.1", "1.2", "1.3", "1.5")] + \
         [f"ofi_{x}" for x in ("1.25", "1.5", "2", "3", "4", "5")] + \
         [f"qb_{x}" for x in ("0.95", "0.975", "0.99", "0.995")]
STACK_DEFAULTS = {"vei": 1.2, "ofi": 3.0, "qb": 0.975, "sq_window": 5}


def _engine_pass(name: str, f: pd.DataFrame, rows: np.ndarray, dirs: np.ndarray, thr: float | None = None) -> np.ndarray:
    g = f.iloc[rows]
    if name == "sq":
        return (g["sq_bars_since_fire"].to_numpy(float) <= STACK_DEFAULTS["sq_window"])
    if name == "vei":
        return g["vei"].to_numpy(float) >= (thr if thr is not None else STACK_DEFAULTS["vei"])
    if name == "ema200":
        ab = g["above_ema200"].to_numpy(float)
        return np.where(dirs > 0, ab == 1, ab == 0)
    if name == "mom":
        return np.where(dirs > 0, g["mom_long_score"].to_numpy(float) >= 4, g["mom_short_score"].to_numpy(float) >= 4)
    if name == "ofi":
        t = thr if thr is not None else STACK_DEFAULTS["ofi"]
        return np.where(dirs > 0, g["ofi_ratio_up"].to_numpy(float) >= t, g["ofi_ratio_dn"].to_numpy(float) >= t)
    if name == "quoteburst":
        return g["qb_pct"].to_numpy(float) >= (thr if thr is not None else STACK_DEFAULTS["qb"])
    if name == "td":
        return np.where(dirs > 0, g["td_bull_exhaust"].to_numpy(float) != 1, g["td_bear_exhaust"].to_numpy(float) != 1)
    raise ValueError(name)


ORDER = ["sq", "vei", "ema200", "mom", "ofi", "quoteburst", "td"]


def variant_mask(variant: str, f: pd.DataFrame, sig: pd.DataFrame) -> np.ndarray:
    rows, dirs = sig["row"].to_numpy(int), sig["dir"].to_numpy(int)
    keep = np.ones(len(sig), bool)
    if variant.startswith("L"):
        level = int(variant[1])
        for eng in ORDER[:level]:
            keep &= _engine_pass(eng, f, rows, dirs)
    elif variant.startswith("A_"):
        keep &= _engine_pass(variant[2:], f, rows, dirs)
    else:
        eng, thr = variant.split("_")
        keep &= _engine_pass({"vei": "vei", "ofi": "ofi", "qb": "quoteburst"}[eng], f, rows, dirs, float(thr))
    return keep


def take_non_overlapping(sig: pd.DataFrame) -> pd.DataFrame:
    """One position at a time: signals in decision order, skipped while a previous trade is open."""
    if sig.empty:
        return sig
    s = sig.sort_values(["signal_time", "dir"], kind="mergesort")
    keep, busy = [], pd.Timestamp.min
    for idx, r in s.iterrows():
        if r["signal_time"] <= busy:
            continue
        keep.append(idx)
        busy = r["exit_time"]
    return s.loc[keep]


def in_window(sig: pd.DataFrame, start: str, end: str, embargo: pd.Timedelta, max_label: pd.Timedelta,
              first_period: bool) -> pd.DataFrame:
    """Purge/embargo: entries >= start (+embargo unless first period), exits < end."""
    s0 = pd.Timestamp(start.rstrip("Z")) + (pd.Timedelta(0) if first_period else embargo)
    e0 = pd.Timestamp(end.rstrip("Z"))
    m = (sig["signal_time"] >= s0) & (sig["signal_time"] + max_label <= e0) & (sig["exit_time"] < e0)
    return sig[m]


# ---------------------------------------------------------------- metrics

def metrics(tr: pd.DataFrame) -> dict:
    if tr.empty:
        return {"n": 0}
    r = tr["r_net"].to_numpy(float)
    w, lo = r[r > 0], r[r <= 0]
    eq = np.cumsum(r)
    dd = float(np.max(np.maximum.accumulate(np.r_[0.0, eq]) - np.r_[0.0, eq]))
    out = {"n": int(r.size), "exp_net_r": float(r.mean()), "exp_gross_r": float(tr["r_gross"].mean()),
           "win_rate": float((r > 0).mean()), "avg_win_r": float(w.mean()) if w.size else 0.0,
           "avg_loss_r": float(lo.mean()) if lo.size else 0.0, "median_r": float(np.median(r)),
           "profit_factor": float(w.sum() / -lo.sum()) if lo.size and lo.sum() < 0 else float("inf"),
           "max_dd_r": dd, "cost_r_mean": float(tr["cost_r"].mean()), "spread_r_mean": float(tr["spread_r"].mean()),
           "comm_r_mean": float(tr["comm_r"].mean()), "slip_r_mean": float(tr["slip_r"].mean()),
           "swap_r_mean": float(tr["swap_r"].mean()), "mfe_r_mean": float(tr["mfe_r"].mean()),
           "mae_r_mean": float(tr["mae_r"].mean()),
           "sharpe_per_trade": float(r.mean() / r.std(ddof=1)) if r.size > 1 and r.std(ddof=1) > 0 else float("nan"),
           "cost_share_of_gross": float(tr["cost_r"].sum() / tr["r_gross"].clip(lower=0).sum()) if tr["r_gross"].clip(lower=0).sum() > 0 else float("nan")}
    days = pd.to_datetime(tr["entry_time"]).dt.normalize()
    out["trades_per_active_day"] = float(days.value_counts().mean())
    return out


def stationary_lower(r: np.ndarray, days, n_boot: int = 2000, alpha: float = 0.05, seed: int = 20261001) -> float:
    """One-sided lower bound of mean R (stationary bootstrap, mean block = trades per active day)."""
    if len(r) < 2:
        return float("nan")
    d = pd.Series(pd.to_datetime(days)).dt.normalize()
    mb = max(1.0, float(d.value_counts().mean()))
    rng = np.random.default_rng(seed)
    n, k, p = len(r), np.arange(len(r)), 1.0 / mb
    reps = np.empty(n_boot)
    for i in range(n_boot):
        new = rng.random(n) < p
        new[0] = True
        starts = rng.integers(0, n, n)
        first = np.maximum.accumulate(np.where(new, k, 0))
        reps[i] = r[(starts[first] + (k - first)) % n].mean()
    return float(np.quantile(reps, alpha))


def random_subset_p(base_r: np.ndarray, kept_mask: np.ndarray, draws: int = 2000, seed: int = 20261001) -> float:
    """Does an engine filter select better-than-random signals? p = P(random subset mean >= kept mean)."""
    k = int(kept_mask.sum())
    if k < 5 or k == len(base_r):
        return float("nan")
    obs = base_r[kept_mask].mean()
    rng = np.random.default_rng(seed)
    sims = np.array([base_r[rng.choice(len(base_r), k, replace=False)].mean() for _ in range(draws)])
    return float((1 + np.sum(sims >= obs)) / (1 + draws))
