"""NEXA Gate 8 - quantitative validation of realised trade outcomes.

Input is a vector of per-trade outcomes in R (net of costs, as the broker
realised them), ordered by entry time. Nothing here fits, tunes or selects
anything: it measures a fixed set of trades and says how much that evidence
supports, and does not support.

Contract
  * All randomness takes an explicit seed; the same input gives the same output.
  * Every statistic reports the sample size it rests on.
  * The verdict is EDGE_NOT_DEMONSTRATED unless the bootstrap lower bound of
    expectancy is above zero on a sample of at least `min_trades`, and it stays
    so under the configured cost shock. Statistical significance is reported
    separately from tradability and never substitutes for it.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from enum import Enum

import numpy as np


class Verdict(str, Enum):
    INSUFFICIENT_SAMPLE = "INSUFFICIENT_SAMPLE"
    EDGE_NOT_DEMONSTRATED = "EDGE_NOT_DEMONSTRATED"
    NEGATIVE_EXPECTANCY = "NEGATIVE_EXPECTANCY"
    EDGE_SUPPORTED_IN_SAMPLE = "EDGE_SUPPORTED_IN_SAMPLE"   # never "profitable": OOS decides


@dataclass(frozen=True)
class StatsConfig:
    min_trades: int = 30
    n_boot: int = 5000
    n_mc: int = 5000
    ci: float = 0.95
    block: int = 1                  # 1 = iid bootstrap; >1 = moving-block (serial dependence)
    cost_shock_r: float = 0.05      # extra cost per trade, in R, for the stress verdict
    risk_per_trade: float = 0.003   # fraction of equity per 1R (NEXA target 0.30%)
    ruin_drawdown: float = 0.10     # NEXA hard max drawdown
    seed: int = 20260927


DEFAULT = StatsConfig()


def _clean(r) -> np.ndarray:
    a = np.asarray(r, dtype=float).ravel()
    if a.size and not np.all(np.isfinite(a)):
        raise ValueError("outcomes contain NaN/inf; resolve upstream, never impute")
    return a


def max_drawdown_r(r) -> float:
    """Largest peak-to-trough fall of cumulative R (>= 0). Peak starts at 0."""
    a = _clean(r)
    if a.size == 0:
        return 0.0
    eq = np.concatenate(([0.0], np.cumsum(a)))
    return float(np.max(np.maximum.accumulate(eq) - eq))


def trade_metrics(r) -> dict:
    a = _clean(r)
    n = int(a.size)
    out: dict = {"n": n}
    if n == 0:
        return out
    wins, losses = a[a > 0], a[a < 0]
    gross_win, gross_loss = float(wins.sum()), float(-losses.sum())
    sd = float(a.std(ddof=1)) if n > 1 else float("nan")
    downside = a[a < 0]
    dsd = float(np.sqrt(np.mean(np.minimum(a, 0.0) ** 2))) if n else float("nan")
    k = max(1, math.floor(0.05 * n))
    tail = np.sort(a)[:k]
    out.update(
        win_rate=float(wins.size / n),
        loss_rate=float(losses.size / n),
        expectancy_r=float(a.mean()),
        median_r=float(np.median(a)),
        total_r=float(a.sum()),
        avg_win_r=float(wins.mean()) if wins.size else 0.0,
        avg_loss_r=float(losses.mean()) if losses.size else 0.0,
        profit_factor=(gross_win / gross_loss) if gross_loss > 0 else (math.inf if gross_win > 0 else float("nan")),
        payoff_ratio=(float(wins.mean()) / float(-losses.mean())) if wins.size and losses.size else float("nan"),
        std_r=sd,
        sharpe_per_trade=(float(a.mean()) / sd) if n > 1 and sd > 0 else float("nan"),
        sortino_per_trade=(float(a.mean()) / dsd) if downside.size and dsd > 0 else float("nan"),
        max_drawdown_r=max_drawdown_r(a),
        worst_r=float(a.min()),
        cvar5_r=float(tail.mean()),
        max_consecutive_losses=_max_run(a < 0),
    )
    return out


def _max_run(mask: np.ndarray) -> int:
    best = cur = 0
    for m in mask:
        cur = cur + 1 if m else 0
        best = max(best, cur)
    return int(best)


def _resample_idx(n: int, block: int, rng: np.random.Generator) -> np.ndarray:
    if block <= 1 or n <= block:
        return rng.integers(0, n, n)
    starts = rng.integers(0, n - block + 1, math.ceil(n / block))
    return (starts[:, None] + np.arange(block)[None, :]).ravel()[:n]


def bootstrap_ci(r, stat=np.mean, cfg: StatsConfig | None = None) -> dict:
    """Percentile bootstrap CI of `stat`, iid or moving-block."""
    cfg = cfg or DEFAULT
    a = _clean(r)
    if a.size < 2:
        return {"n": int(a.size), "point": float("nan"), "lo": float("nan"), "hi": float("nan")}
    rng = np.random.default_rng(cfg.seed)
    reps = np.array([stat(a[_resample_idx(a.size, cfg.block, rng)]) for _ in range(cfg.n_boot)])
    alpha = (1.0 - cfg.ci) / 2.0
    return {
        "n": int(a.size),
        "point": float(stat(a)),
        "lo": float(np.quantile(reps, alpha)),
        "hi": float(np.quantile(reps, 1.0 - alpha)),
        "p_le_zero": float(np.mean(reps <= 0.0)),
    }


def monte_carlo(r, cfg: StatsConfig | None = None) -> dict:
    """Resample the trade sequence (with replacement) to size the drawdown and ruin
    distribution. Ruin = equity drawdown reaching `ruin_drawdown` at `risk_per_trade`
    per R, compounded, which is how NEXA's percentage sizing behaves."""
    cfg = cfg or DEFAULT
    a = _clean(r)
    if a.size < 2:
        return {"n": int(a.size)}
    rng = np.random.default_rng(cfg.seed + 1)
    dd_r = np.empty(cfg.n_mc)
    final_r = np.empty(cfg.n_mc)
    ruined = 0
    for i in range(cfg.n_mc):
        s = a[_resample_idx(a.size, cfg.block, rng)]
        dd_r[i] = max_drawdown_r(s)
        final_r[i] = s.sum()
        eq = np.cumprod(1.0 + cfg.risk_per_trade * s)
        if np.any(1.0 - eq / np.maximum.accumulate(np.concatenate(([1.0], eq)))[1:] >= cfg.ruin_drawdown):
            ruined += 1
    q = (0.05, 0.25, 0.5, 0.75, 0.95)
    return {
        "n": int(a.size),
        "sims": cfg.n_mc,
        "max_dd_r": {f"p{int(x * 100)}": float(np.quantile(dd_r, x)) for x in q},
        "final_r": {f"p{int(x * 100)}": float(np.quantile(final_r, x)) for x in q},
        "p_hit_max_drawdown": ruined / cfg.n_mc,
    }


def cost_shock(r, shock_r: float) -> np.ndarray:
    """Charge every trade an extra `shock_r` R (e.g. wider spread / slippage)."""
    return _clean(r) - float(shock_r)


def cost_shock_price(r, risk_dist, extra_price) -> np.ndarray:
    """Per-trade shock in price units converted through each trade's own stop distance."""
    a, d = _clean(r), _clean(risk_dist)
    if a.shape != d.shape or np.any(d <= 0):
        raise ValueError("risk_dist must be positive and aligned with outcomes")
    return a - float(extra_price) / d


def breakeven_cost_r(r) -> float:
    """Extra per-trade cost (R) that drives expectancy to zero. <= 0 means already negative."""
    a = _clean(r)
    return float(a.mean()) if a.size else float("nan")


def segment_metrics(r, keys) -> dict:
    """Expectancy by segment (regime / session / setup / symbol / direction)."""
    a = _clean(r)
    k = np.asarray(keys)
    if k.shape != a.shape:
        raise ValueError("keys must align with outcomes")
    out = {}
    for key in sorted({str(x) for x in k}):
        sub = a[k.astype(str) == key]
        out[key] = {"n": int(sub.size), "expectancy_r": float(sub.mean()) if sub.size else float("nan"),
                    "win_rate": float((sub > 0).mean()) if sub.size else float("nan")}
    return out


@dataclass
class Gate8Report:
    verdict: Verdict
    reasons: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    expectancy_ci: dict = field(default_factory=dict)
    shocked_expectancy_ci: dict = field(default_factory=dict)
    monte_carlo: dict = field(default_factory=dict)
    breakeven_cost_r: float = float("nan")
    config: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        return d


def evaluate(r, cfg: StatsConfig | None = None) -> Gate8Report:
    cfg = cfg or DEFAULT
    a = _clean(r)
    rep = Gate8Report(verdict=Verdict.EDGE_NOT_DEMONSTRATED, config=asdict(cfg))
    rep.metrics = trade_metrics(a)
    if a.size < cfg.min_trades:
        rep.verdict = Verdict.INSUFFICIENT_SAMPLE
        rep.reasons.append(f"n={a.size} < min_trades={cfg.min_trades}")
        if a.size >= 2:
            rep.expectancy_ci = bootstrap_ci(a, cfg=cfg)
        return rep
    rep.expectancy_ci = bootstrap_ci(a, cfg=cfg)
    rep.shocked_expectancy_ci = bootstrap_ci(cost_shock(a, cfg.cost_shock_r), cfg=cfg)
    rep.monte_carlo = monte_carlo(a, cfg)
    rep.breakeven_cost_r = breakeven_cost_r(a)
    if rep.expectancy_ci["hi"] < 0:
        rep.verdict = Verdict.NEGATIVE_EXPECTANCY
        rep.reasons.append("whole bootstrap CI of expectancy is below zero")
    elif rep.expectancy_ci["lo"] <= 0:
        rep.reasons.append("bootstrap CI of expectancy includes zero")
    elif rep.shocked_expectancy_ci["lo"] <= 0:
        rep.reasons.append(f"edge does not survive a {cfg.cost_shock_r}R per-trade cost shock")
    else:
        rep.verdict = Verdict.EDGE_SUPPORTED_IN_SAMPLE
        rep.reasons.append("expectancy CI > 0 and survives cost shock; in-sample only, OOS still required")
    return rep
