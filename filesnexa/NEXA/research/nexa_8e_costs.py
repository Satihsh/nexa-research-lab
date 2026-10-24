"""Pepperstone broker-cost and position-sizing engine for the 8-engine research (research only).

Every number comes from the broker's own specification captured by NEXA_SpecProbe.mq5
(data/pepperstone/spec_probe/spec_probe_20261001.csv): contract size, tick size/value, volume grid,
stops/freeze levels and the commission actually charged on a simulated min-lot round trip.
No generic internet lot formula is used. Sizing ROUNDS DOWN to the volume step and never exceeds the
risk ceiling; if the rounded size is below the broker minimum the trade is NOT tradable (it is never
rounded up to make a table look feasible).

Money per 1.0 price unit per 1.0 lot = tick_value / tick_size (USD account; the probe's
OrderCalcProfit confirms +/- one tick per lot equals tick_value for every probed symbol).
"""
from __future__ import annotations

import csv
import math
import os
from dataclasses import dataclass

PROBE = os.path.join(os.path.dirname(__file__), "..", "data", "pepperstone", "spec_probe", "spec_probe_20261001.csv")


@dataclass(frozen=True)
class SymbolSpec:
    symbol: str
    point: float
    tick_size: float
    tick_value: float
    contract_size: float
    vmin: float
    vmax: float
    vstep: float
    stops_level: int
    freeze_level: int
    commission_per_side_minlot: float      # USD, observed (positive number)
    probe_spread_points: int
    calc_mode: str

    @property
    def value_per_price_per_lot(self) -> float:
        return self.tick_value / self.tick_size

    def commission_round_trip(self, lots: float) -> float:
        return 2.0 * self.commission_per_side_minlot * (lots / self.vmin)


def load_specs(path: str = PROBE) -> dict[str, SymbolSpec]:
    with open(path, newline="") as fh:
        rows = list(csv.reader(fh))
    header = rows[0]
    specs, comm = {}, {}
    for r in rows[1:]:
        if len(r) > 2 and r[0] == "ROUND_TRIP" and r[1] != "symbol":
            comm[r[1]] = (abs(float(r[5])) + abs(float(r[6]))) / 2.0       # per side, at the probed (min) volume
    for r in rows[1:]:
        if len(r) != len(header) or r[0] in ("ROUND_TRIP", "symbol"):
            continue
        d = dict(zip(header, r, strict=True))
        s = d["symbol"]
        specs[s] = SymbolSpec(s, float(d["point"]), float(d["tick_size"]), float(d["tick_value"]),
                              float(d["contract_size"]), float(d["volume_min"]), float(d["volume_max"]),
                              float(d["volume_step"]), int(d["stops_level"]), int(d["freeze_level"]),
                              comm.get(s, float("nan")), int(d["spread_pts"]), d["calc_mode"])
    return specs


def round_down_to_step(raw: float, step: float) -> float:
    if not (math.isfinite(raw) and raw > 0 and step > 0):
        return 0.0
    n = math.floor(raw / step + 1e-9)
    return round(n * step, 10)


@dataclass(frozen=True)
class CostInputs:
    spread_price: float            # full spread in PRICE units paid on the round trip (entry at ask, exit at bid)
    slippage_price: float = 0.0    # adverse slippage per side, price units
    financing_cash: float = 0.0    # swap/financing for the holding period, USD (charges only)


def size_trade(spec: SymbolSpec, equity: float, risk_pct: float, stop_price: float, costs: CostInputs) -> dict:
    """Largest broker-valid volume whose TOTAL loss at the stop (price loss + spread + 2x slippage +
    commission + financing) does not exceed equity * risk_pct."""
    out = {"equity": equity, "risk_cash": equity * risk_pct, "stop_price": stop_price}
    vpp = spec.value_per_price_per_lot
    per_lot_loss = (stop_price + costs.spread_price + 2 * costs.slippage_price) * vpp + 2 * spec.commission_per_side_minlot / spec.vmin
    raw = (out["risk_cash"] - costs.financing_cash) / per_lot_loss if per_lot_loss > 0 else 0.0
    lots = min(round_down_to_step(raw, spec.vstep), spec.vmax)
    out.update(raw_lots=raw, lots=lots, tradable=lots >= spec.vmin - 1e-12 and stop_price > spec.stops_level * spec.point)
    if out["tradable"]:
        out["loss_at_stop_cash"] = lots * per_lot_loss + costs.financing_cash
        out["actual_risk_pct"] = out["loss_at_stop_cash"] / equity
    else:
        out["min_lot_loss_at_stop_cash"] = spec.vmin * per_lot_loss + costs.financing_cash
        out["min_lot_risk_pct"] = out["min_lot_loss_at_stop_cash"] / equity
        out["equity_needed_for_min_lot"] = out["min_lot_loss_at_stop_cash"] / risk_pct
    return out


def trade_costs(spec: SymbolSpec, lots: float, costs: CostInputs) -> dict:
    vpp = spec.value_per_price_per_lot
    spread_cash = costs.spread_price * vpp * lots
    slip_cash = 2 * costs.slippage_price * vpp * lots
    comm_cash = spec.commission_round_trip(lots)
    total = spread_cash + slip_cash + comm_cash + costs.financing_cash
    return {"spread_cost": spread_cash, "slippage_cost": slip_cash, "commission_cost": comm_cash,
            "financing_cost": costs.financing_cash, "total_cost": total}


def net_outcome(spec: SymbolSpec, lots: float, stop_price: float, r_multiple: float, costs: CostInputs,
                equity: float) -> dict:
    """Gross and net P/L of a full winner at r_multiple x stop, and of a full loser."""
    vpp = spec.value_per_price_per_lot
    c = trade_costs(spec, lots, costs)
    gross_win = r_multiple * stop_price * vpp * lots
    gross_loss = -stop_price * vpp * lots
    risk_cash = stop_price * vpp * lots
    out = {**c, "gross_win": gross_win, "net_win": gross_win - c["total_cost"],
           "gross_loss": gross_loss, "net_loss": gross_loss - c["total_cost"],
           "gross_R": r_multiple, "net_R_win": (gross_win - c["total_cost"]) / risk_cash if risk_cash else float("nan"),
           "net_R_loss": (gross_loss - c["total_cost"]) / risk_cash if risk_cash else float("nan"),
           "cost_R": c["total_cost"] / risk_cash if risk_cash else float("nan"),
           "cost_pct_of_gross_win": c["total_cost"] / gross_win if gross_win else float("nan"),
           "cost_pct_of_equity": c["total_cost"] / equity}
    return out


def net_edge_score(net_expectancy_cash: float, total_cost_cash: float) -> float:
    """NET_EDGE_SCORE = net expectancy per trade / total execution cost per trade (NaN if no cost)."""
    return net_expectancy_cash / total_cost_cash if total_cost_cash > 0 else float("nan")


def expected_net_r(p_win: float, r_multiple: float, cost_r: float) -> float:
    return p_win * (r_multiple - cost_r) - (1 - p_win) * (1 + cost_r)


def breakeven_win_rate(r_multiple: float, cost_r: float) -> float:
    return (1 + cost_r) / (r_multiple + 1)
