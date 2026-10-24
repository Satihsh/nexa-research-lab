"""+24.5 %/day feasibility mathematics under NEXA's hard risk rules (research only).

Model of one trading day (all quantities relative to the day's starting equity = 1):
  * every trade risks f = 1 % of CURRENT equity (NEXA sizes on live equity -> compounding in-day);
  * a winner returns +R risk units, a loser -1 risk unit; execution cost c (in risk units) is paid
    on every trade: win multiplier 1 + f(R - c), loss multiplier 1 - f(1 + c);
  * the day stops at the TARGET (equity >= 1 + target), at the DAILY LOSS halt (NEXA: halt when
    (start - equity)/start >= 2 %, i.e. equity <= 0.98), or after max_trades (NEXA hard cap 10);
  * trades are independent Bernoulli(p) in the exact DP below (dependence is discussed in the report).

General bound (no distributional assumption). If no trade has positive expected value, equity is a
supermartingale and, by optional stopping at a bounded stopping time, E[W_stop] <= 1. Every stopped
day ends with W >= W_min (the lowest equity reachable when the halt triggers), so
    P(target) * (1 + target) + (1 - P(target)) * W_min <= 1
    =>  P(target) <= (1 - W_min) / (1 + target - W_min).
The same inequality, read the other way, gives the MINIMUM expected daily return any strategy needs
to reach the target with probability h: E[W_stop] - 1 >= h*target - (1 - h)*(1 - W_min).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

TARGET = 0.245
RISK = 0.01
DAILY_LOSS = 0.02
MAX_TRADES = 10


def compounding_path(start: float = 200.0, rate: float = TARGET, days: int = 20) -> list[dict]:
    """Ideal compounding table; no rounding inside (display rounding is the caller's job)."""
    out, eq = [], start
    for d in range(1, days + 1):
        out.append({"day": d, "start_equity": eq, "profit_objective": eq * rate, "target_equity": eq * (1 + rate)})
        eq *= 1 + rate
    return out


def winners_needed(r_multiple: float, risk: float = RISK, target: float = TARGET, cost_r: float = 0.0) -> int:
    """Minimum number of consecutive full winners (in-day compounding) to reach the target."""
    g = 1 + risk * (r_multiple - cost_r)
    if g <= 1:
        return math.inf
    return math.ceil(math.log(1 + target) / math.log(g) - 1e-12)


def r_needed_all_win(n_trades: int, risk: float = RISK, target: float = TARGET) -> float:
    """R every trade must deliver if ALL n trades win (no costs)."""
    return ((1 + target) ** (1 / n_trades) - 1) / risk


def equity_after(wins: int, losses: int, r_multiple: float, risk: float = RISK, cost_r: float = 0.0) -> float:
    return (1 + risk * (r_multiple - cost_r)) ** wins * (1 - risk * (1 + cost_r)) ** losses


@dataclass(frozen=True)
class DayOutcome:
    p_target: float
    p_halt: float
    p_cap: float
    exp_return: float
    exp_trades: float


def day_distribution(p: float, r_multiple: float, risk: float = RISK, cost_r: float = 0.0, target: float = TARGET,
                     daily_loss: float = DAILY_LOSS, max_trades: int = MAX_TRADES) -> DayOutcome:
    """Exact DP over (wins, losses) for i.i.d. Bernoulli(p) trades with the NEXA stopping rules."""
    up, dn = 1 + risk * (r_multiple - cost_r), 1 - risk * (1 + cost_r)
    hi, lo = 1 + target, 1 - daily_loss
    alive = {(0, 0): 1.0}
    p_t = p_h = p_c = er = et = 0.0
    for n in range(max_trades):
        nxt: dict = {}
        for (w, l), pr in alive.items():
            for dw, dl, q in ((1, 0, p), (0, 1, 1 - p)):
                if q == 0:
                    continue
                w2, l2, pr2 = w + dw, l + dl, pr * q
                eq = up ** w2 * dn ** l2
                if eq >= hi - 1e-12:
                    p_t += pr2
                    er += pr2 * (eq - 1)
                    et += pr2 * (n + 1)
                elif eq <= lo + 1e-12:
                    p_h += pr2
                    er += pr2 * (eq - 1)
                    et += pr2 * (n + 1)
                else:
                    nxt[(w2, l2)] = nxt.get((w2, l2), 0.0) + pr2
        alive = nxt
    for (w, l), pr in alive.items():
        p_c += pr
        er += pr * (up ** w * dn ** l - 1)
        et += pr * max_trades
    return DayOutcome(p_t, p_h, p_c, er, et)


def w_min(risk: float = RISK, cost_r: float = 0.0, daily_loss: float = DAILY_LOSS) -> float:
    """Lowest equity at which a day can end via the loss halt: just above the halt line, one more
    full loss. (Ends at the trade cap are above the halt line, so this bounds every outcome.)"""
    return (1 - daily_loss) * (1 - risk * (1 + cost_r))


def zero_edge_target_bound(risk: float = RISK, cost_r: float = 0.0, target: float = TARGET,
                           daily_loss: float = DAILY_LOSS) -> float:
    wm = w_min(risk, cost_r, daily_loss)
    return (1 - wm) / (1 + target - wm)


def min_expected_daily_return(hit_rate: float, risk: float = RISK, cost_r: float = 0.0, target: float = TARGET,
                              daily_loss: float = DAILY_LOSS) -> float:
    """Necessary (not sufficient) expected daily return for a target hit-rate h."""
    wm = w_min(risk, cost_r, daily_loss)
    return hit_rate * target - (1 - hit_rate) * (1 - wm)


def p_barrier_driftless(target_dist: float, stop_dist: float) -> float:
    """P(price reaches +target_dist before -stop_dist) for a driftless continuous martingale."""
    return stop_dist / (stop_dist + target_dist)


def single_trade_requirements(equity: float, risk: float, stop_price: float, value_per_price_per_lot: float,
                              vmin: float, vstep: float, cost_cash_per_minlot: float, target: float = TARGET) -> dict:
    """Can ONE trade at <= risk reach the daily target? (broker volume grid respected)."""
    risk_cash = equity * risk
    loss_per_lot = stop_price * value_per_price_per_lot
    raw = risk_cash / loss_per_lot if loss_per_lot > 0 else 0.0
    lots = math.floor(raw / vstep + 1e-9) * vstep
    cost = cost_cash_per_minlot * (lots / vmin) if vmin > 0 else float("nan")
    out = {"risk_cash": risk_cash, "raw_lots": raw, "lots": lots, "tradable": lots >= vmin - 1e-12,
           "actual_risk_cash": lots * loss_per_lot + cost}
    if out["tradable"]:
        need_profit = equity * target + cost
        out["target_price_move"] = need_profit / (lots * value_per_price_per_lot)
        out["required_r"] = out["target_price_move"] / stop_price
        out["p_driftless"] = p_barrier_driftless(out["target_price_move"], stop_price)
    return out
