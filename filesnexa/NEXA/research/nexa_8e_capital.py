"""NEXA Capital Velocity Engine (research-only simulator; subordinate to the deterministic risk rules).

Per server trading day (Pepperstone server day = New York close; nexa_time):
  start_equity E0, target_equity = E0 * 1.245, profit objective = E0 * 0.245 (no internal rounding).
  Trades of the day are taken in entry order (already non-overlapping), each sized at <= 1 % of CURRENT
  equity with the broker's real volume grid (round DOWN; below the minimum lot -> SKIPPED, never rounded up).
  The session LOCKS (no new entries) when: equity >= target (target hit), equity <= 0.98 * E0 (NEXA
  daily-loss halt), or 10 trades were taken (NEXA cap). Nothing is ever re-sized after a miss: no
  doubling, no martingale, no averaging, no re-entry logic, no target chasing.
A trade's cash P/L = r_net x risk_price x value_per_price_per_lot x lots, where r_net already contains
spread, commission, slippage and swap (nexa_8e_research), so costs scale with the traded volume.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import nexa_8e_costs as C
import nexa_time

TARGET, RISK, DAILY_LOSS, MAX_TRADES = 0.245, 0.01, 0.02, 10


def server_day(ts: pd.Series) -> pd.Series:
    return nexa_time.utc_to_server(pd.Series(pd.to_datetime(ts))).dt.normalize()


def simulate(trades: pd.DataFrame, spec: C.SymbolSpec, start_equity: float = 200.0, risk: float = RISK,
             target: float = TARGET, daily_loss: float = DAILY_LOSS, max_trades: int = MAX_TRADES,
             days: int | None = None) -> pd.DataFrame:
    """trades: columns entry_time (naive UTC), risk (price distance entry->stop), r_net, cost_r.
    Returns one row per trading day that had at least one signal (days with no signal are not
    trading days for this strategy)."""
    if trades.empty:
        return pd.DataFrame()
    t = trades.sort_values("entry_time").copy()
    t["day"] = server_day(t["entry_time"]).to_numpy()
    vpp = spec.value_per_price_per_lot
    eq = start_equity
    rows = []
    for day, g in t.groupby("day", sort=True):
        e0, tgt, halt = eq, eq * (1 + target), eq * (1 - daily_loss)
        taken = skipped = 0
        gross = cost = 0.0
        status = "OPEN"
        for _, r in g.iterrows():
            if status != "OPEN":
                break
            if taken >= max_trades:
                status = "TRADE_CAP"
                break
            per_lot_loss = r["risk"] * vpp * (1 + r["cost_r"])          # stop distance + all costs, per lot
            lots = C.round_down_to_step(eq * risk / per_lot_loss, spec.vstep) if per_lot_loss > 0 else 0.0
            lots = min(lots, spec.vmax)
            if lots < spec.vmin - 1e-12:
                skipped += 1
                continue
            pnl = r["r_net"] * r["risk"] * vpp * lots
            gross += (r["r_net"] + r["cost_r"]) * r["risk"] * vpp * lots
            cost += r["cost_r"] * r["risk"] * vpp * lots
            eq += pnl
            taken += 1
            if eq >= tgt - 1e-9:
                status = "TARGET_HIT"
            elif eq <= halt + 1e-9:
                status = "DAILY_LOSS_HALT"
        rows.append({"day": pd.Timestamp(day), "start_equity": e0, "target_equity": tgt, "ending_equity": eq,
                     "net_pnl": eq - e0, "net_return": eq / e0 - 1, "trades": taken, "skipped_below_min_lot": skipped,
                     "gross_pnl": gross, "costs": cost, "status": status, "target_hit": eq >= tgt - 1e-9})
        if days is not None and len(rows) >= days:
            break
    out = pd.DataFrame(rows)
    peak = out["ending_equity"].cummax().clip(lower=start_equity)
    out["drawdown"] = 1 - out["ending_equity"] / peak
    return out


def summary(days: pd.DataFrame) -> dict:
    if days.empty:
        return {"days": 0}
    traded = days[days["trades"] > 0]
    return {"days": len(days), "days_with_trades": len(traded),
            "target_hit_rate": float(days["target_hit"].mean()),
            "daily_loss_halt_rate": float((days["status"] == "DAILY_LOSS_HALT").mean()),
            "mean_daily_return": float(days["net_return"].mean()),
            "median_daily_return": float(days["net_return"].median()),
            "final_equity": float(days["ending_equity"].iloc[-1]), "max_drawdown": float(days["drawdown"].max()),
            "skipped_below_min_lot": int(days["skipped_below_min_lot"].sum()),
            "trades": int(days["trades"].sum()), "cost_share_of_gross": float(days["costs"].sum() / days["gross_pnl"].clip(lower=0).sum())
            if days["gross_pnl"].clip(lower=0).sum() > 0 else float("nan")}


def p_all_targets_bootstrap(daily_returns: np.ndarray, target: float = TARGET, horizon: int = 20, draws: int = 20000,
                            seed: int = 20261001) -> float:
    """Empirical probability that `horizon` consecutive resampled trading days ALL reach the target
    (i.i.d. day bootstrap; a descriptive statistic, not a forecast)."""
    r = np.asarray(daily_returns, float)
    if r.size == 0:
        return float("nan")
    rng = np.random.default_rng(seed)
    hits = (r >= target - 1e-12)
    sims = hits[rng.integers(0, r.size, (draws, horizon))].all(axis=1)
    return float(sims.mean())
