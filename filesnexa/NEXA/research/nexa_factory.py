"""NEXA Gate 10 - Strategy Factory: GENERATE -> TEST -> CHALLENGE -> VALIDATE -> SELECT.

Research-tier only. Nothing here trades, and nothing here is wired into the EA.
A strategy that survives this file is a CANDIDATE for the MT5 Strategy Tester
and shadow mode, never a live promotion.

Conventions (normative)
  * Bars are BID OHLC in broker server time, ascending, one row per closed bar.
  * A decision on bar i uses only bars 0..i (bar i is closed). Entry is at the
    OPEN of bar i+1. `decision_ts` = open time of bar i, as in NEXA Trade DNA.
  * Long entry pays the ask (bid open + spread) plus slippage; long exits are
    triggered by and filled at bid. Short entry fills at bid minus slippage;
    short exits are triggered when ask (bid + spread) reaches the level.
  * If one bar spans both stop and target, the STOP is taken (conservative) and
    the trade is flagged `ambiguous`.
  * One open position per strategy; signals while in a position are ignored.
  * R = realised P/L / initial stop distance measured from the ACTUAL entry.
  * Costs are explicit inputs. When the data has no bid/ask (Axiory XAUUSD),
    costs are ASSUMPTIONS and every result must be read across cost scenarios.
"""
from __future__ import annotations

import itertools
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

# ----------------------------------------------------------------- data


def load_bars(path: str) -> pd.DataFrame:
    """Load OHLC bars. Timestamps are kept as naive server time; any '+0000'
    suffix on the Axiory ladder is a known mislabel (values are server time)."""
    df = pd.read_csv(path)
    cols = {c.lower(): c for c in df.columns}
    out = pd.DataFrame({
        "time": pd.to_datetime(df[cols["time"]].astype(str).str.replace(r"[+-]\d{4}$", "", regex=True)),
        "open": df[cols["open"]].astype(float),
        "high": df[cols["high"]].astype(float),
        "low": df[cols["low"]].astype(float),
        "close": df[cols["close"]].astype(float),
    })
    if "spread" in cols:
        out["spread_pts"] = df[cols["spread"]].astype(float)
    out = out.sort_values("time").drop_duplicates("time").reset_index(drop=True)
    bad = (out.high < out[["open", "close"]].max(axis=1)) | (out.low > out[["open", "close"]].min(axis=1))
    if bad.any():
        raise ValueError(f"{int(bad.sum())} bars violate OHLC geometry; fix upstream")
    return out


# ----------------------------------------------------------------- causal indicators
# Every function returns an array aligned to bars where element i uses bars <= i only.


def true_range(h, lo, c) -> np.ndarray:
    pc = np.concatenate(([np.nan], c[:-1]))
    tr = np.fmax(h - lo, np.fmax(np.abs(h - pc), np.abs(lo - pc)))
    tr[0] = h[0] - lo[0]
    return tr


def wilder(x: np.ndarray, n: int) -> np.ndarray:
    """Wilder RMA seeded with the SMA of the first n values; NaN before that."""
    out = np.full(x.size, np.nan)
    if x.size < n:
        return out
    out[n - 1] = np.nanmean(x[:n])
    for i in range(n, x.size):
        out[i] = (out[i - 1] * (n - 1) + x[i]) / n
    return out


def atr(b: pd.DataFrame, n: int = 14) -> np.ndarray:
    return wilder(true_range(b.high.values, b.low.values, b.close.values), n)


def ema(x: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(x).ewm(span=n, adjust=False, min_periods=n).mean().values


def sma(x: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(x).rolling(n, min_periods=n).mean().values


def donchian_prior(b: pd.DataFrame, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Highest high / lowest low of the n bars BEFORE bar i (bar i excluded)."""
    hi = pd.Series(b.high.values).rolling(n, min_periods=n).max().shift(1).values
    lo = pd.Series(b.low.values).rolling(n, min_periods=n).min().shift(1).values
    return hi, lo


def adx(b: pd.DataFrame, n: int = 14) -> np.ndarray:
    h, lo, c = b.high.values, b.low.values, b.close.values
    up = np.concatenate(([0.0], h[1:] - h[:-1]))
    dn = np.concatenate(([0.0], lo[:-1] - lo[1:]))
    pdm = np.where((up > dn) & (up > 0), up, 0.0)
    ndm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = wilder(true_range(h, lo, c), n)
    with np.errstate(invalid="ignore", divide="ignore"):
        pdi = 100 * wilder(pdm, n) / tr
        ndi = 100 * wilder(ndm, n) / tr
        dx = 100 * np.abs(pdi - ndi) / (pdi + ndi)
    out = np.full(h.size, np.nan)
    ok = np.where(np.isfinite(dx))[0]
    if ok.size >= n:
        out[ok[0]:] = wilder(np.nan_to_num(dx[ok[0]:]), n)
    return out


def supertrend_dir(b: pd.DataFrame, factor: float = 3.0, n: int = 10) -> np.ndarray:
    """+1 uptrend / -1 downtrend / 0 undefined (TrendLock semantics, sign flipped
    to NEXA's +1 = long convention)."""
    h, lo, c = b.high.values, b.low.values, b.close.values
    a = atr(b, n)
    out = np.zeros(c.size, dtype=int)
    ub = lb = np.nan
    d = -1   # Pine starts in "downtrend" (direction := 1)
    for i in range(c.size):
        if not np.isfinite(a[i]):
            continue
        src = (h[i] + lo[i]) / 2
        u, low_b = src + factor * a[i], src - factor * a[i]
        if np.isfinite(lb):
            if not (low_b > lb or c[i - 1] < lb):
                low_b = lb
            if not (u < ub or c[i - 1] > ub):
                u = ub
            d = (1 if c[i] > u else -1) if d == -1 else (-1 if c[i] < low_b else 1)
        ub, lb = u, low_b
        out[i] = d
    return out


def resample_last_closed(b: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Higher-TF bars built from `b`. Each HTF bar carries `known_at`: the open
    time of the LAST base bar of its period (period end minus one base step).
    A base bar at time t may use an HTF bar only when known_at <= t, i.e. the
    whole HTF period has elapsed at t's close. A missing final base bar (gap)
    therefore delays availability; it never makes an HTF bar available early."""
    s = b.set_index("time")
    step = pd.Series(b.time).diff().median()
    g = s.resample(rule, label="left", closed="left")
    htf = pd.DataFrame({"open": g.open.first(), "high": g.high.max(),
                        "low": g.low.min(), "close": g.close.last()}).dropna()
    htf["known_at"] = htf.index + pd.Timedelta(rule) - step
    return htf.reset_index().rename(columns={"time": "htf_open"})


def htf_value_asof(b: pd.DataFrame, htf: pd.DataFrame, values: np.ndarray) -> np.ndarray:
    """Map an HTF series onto base bars: bar i sees the latest HTF bar whose last
    constituent is <= bar i (i.e. the HTF bar is fully closed at bar i's close)."""
    s = pd.DataFrame({"known_at": pd.to_datetime(htf.known_at.values), "v": values}).sort_values("known_at")
    m = pd.merge_asof(pd.DataFrame({"time": b.time.values}), s, left_on="time", right_on="known_at",
                      direction="backward")
    return m.v.values


def prev_day_hlc(b: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Previous SERVER day's high/low/close for each bar (no current-day info)."""
    day = b.time.dt.floor("D")
    agg = b.groupby(day).agg(h=("high", "max"), lo=("low", "min"), c=("close", "last")).shift(1)
    m = agg.reindex(day.values)
    return m.h.values, m.lo.values, m.c.values


# ----------------------------------------------------------------- simulator


@dataclass(frozen=True)
class CostModel:
    name: str
    spread: float          # price units, round trip is paid once via the ask side
    slippage: float        # price units per side, always adverse
    assumed: bool = True   # True when not measured from the execution broker
    relative: bool = False  # True: spread/slippage are FRACTIONS of the entry-bar open price


@dataclass
class Trades:
    frame: pd.DataFrame

    @property
    def r(self) -> np.ndarray:
        return self.frame.r_net.values if len(self.frame) else np.zeros(0)


def simulate(b: pd.DataFrame, signal: np.ndarray, stop_dist: np.ndarray, target_r: float,
             max_hold: int, cost: CostModel, spread_series: np.ndarray | None = None) -> Trades:
    o, h, lo, c, t = b.open.values, b.high.values, b.low.values, b.close.values, b.time.values
    n = len(b)
    rows = []
    i = 0
    while i < n - 1:
        d = int(signal[i])
        sd = stop_dist[i]
        if d == 0 or not np.isfinite(sd) or sd <= 0:
            i += 1
            continue
        e = i + 1
        scale = o[e] if cost.relative else 1.0
        spr = cost.spread * scale if spread_series is None else float(spread_series[e])
        slip = cost.slippage * scale
        entry = o[e] + spr + slip if d > 0 else o[e] - slip
        sl = entry - d * sd
        tp = entry + d * sd * target_r
        exit_px = np.nan
        reason = "TIME_EXIT"
        amb = False
        mfe = mae = 0.0
        last = min(n - 1, e + max_hold - 1)
        j = e
        for j in range(e, last + 1):
            if d > 0:
                fav, adv = h[j] - entry, entry - lo[j]
                hit_sl, hit_tp = lo[j] <= sl, h[j] >= tp
            else:
                fav, adv = entry - (lo[j] + spr), (h[j] + spr) - entry
                hit_sl, hit_tp = h[j] + spr >= sl, lo[j] + spr <= tp
            mfe, mae = max(mfe, fav), max(mae, adv)
            if hit_sl:
                amb = bool(hit_tp)
                gap = (o[j] < sl) if d > 0 else (o[j] + spr > sl)   # opened through the stop
                exit_px = (o[j] if gap else sl) - d * slip if d > 0 else \
                          ((o[j] + spr) if gap else sl) + slip
                reason = "SL_LOSS"
                break
            if hit_tp:
                exit_px = tp - slip if d > 0 else tp + slip
                reason = "TP_WIN"
                break
        if reason == "TIME_EXIT":
            j = last
            exit_px = c[j] - slip if d > 0 else c[j] + spr + slip
        pnl = (exit_px - entry) * d
        gross = pnl + (spr + 2 * slip)
        rows.append({"decision_ts": t[i], "entry_ts": t[e], "exit_ts": t[j], "direction": d,
                     "entry": entry, "sl": sl, "tp": tp, "exit": exit_px, "risk_dist": sd,
                     "r_net": pnl / sd, "r_gross": gross / sd, "exit_reason": reason,
                     "ambiguous": amb, "bars_held": j - e + 1, "mfe_r": mfe / sd, "mae_r": mae / sd})
        i = j + 1   # flat after exit bar; next decision on the exit bar's close at the earliest
    return Trades(pd.DataFrame(rows))


# ----------------------------------------------------------------- strategy registry


@dataclass(frozen=True)
class Strategy:
    name: str
    family: str
    hypothesis: str
    invalidation: str
    regime_assumption: str
    failure_conditions: str
    source: str
    params: dict
    build: Callable = field(repr=False, compare=False)   # (bars, **params) -> (signal, stop_dist)
    target_r: float = 2.0
    max_hold: int = 48

    def run(self, b: pd.DataFrame, cost: CostModel, spread_series=None) -> Trades:
        sig, sd = self.build(b, **self.params)
        return simulate(b, sig, sd, self.target_r, self.max_hold, cost, spread_series)

    def spec(self) -> dict:
        d = asdict(self)
        d.pop("build", None)
        return d


def _stdb(b, st_factor=3.0, st_len=10, don=20, ema_len=34, adx_len=14, adx_min=18.0,
          body_min=0.35, sl_atr=2.0, htf="4h"):
    """TrendLock synthesis: chart + HTF Supertrend agree, close breaks the prior
    Donchian band, EMA rising, not chop, body filter. Tick-volume filter omitted:
    Axiory tick counts are broker-specific and not comparable to the MT5 feed."""
    c, o = b.close.values, b.open.values
    st = supertrend_dir(b, st_factor, st_len)
    htf_b = resample_last_closed(b, htf)
    htf_dir = htf_value_asof(b, htf_b, supertrend_dir(htf_b, st_factor, st_len))
    dh, dl = donchian_prior(b, don)
    e = ema(c, ema_len)
    e_prev = np.concatenate(([np.nan], e[:-1]))
    ax = adx(b, adx_len)
    a = atr(b, 14)
    rng = b.high.values - b.low.values
    body = np.divide(np.abs(c - o), rng, out=np.zeros_like(c), where=rng > 0)
    trend_ok = ax > adx_min
    long_ = (st == 1) & (htf_dir == 1) & (c > dh) & (c > e) & (e > e_prev) & trend_ok & (c > o) & (body >= body_min)
    short = (st == -1) & (htf_dir == -1) & (c < dl) & (c < e) & (e < e_prev) & trend_ok & (c < o) & (body >= body_min)
    return np.where(long_, 1, np.where(short, -1, 0)), a * sl_atr


def _donchian(b, don=20, sl_atr=2.0):
    c = b.close.values
    dh, dl = donchian_prior(b, don)
    return np.where(c > dh, 1, np.where(c < dl, -1, 0)), atr(b, 14) * sl_atr


def _tsmom(b, look=120, sl_atr=2.0):
    """Enter on the bar where the sign of the `look`-bar return flips."""
    c = b.close.values
    ret = c - np.concatenate((np.full(look, np.nan), c[:-look]))
    s = np.sign(np.nan_to_num(ret)).astype(int)
    prev = np.concatenate(([0], s[:-1]))
    return np.where(s != prev, s, 0), atr(b, 14) * sl_atr


def _mr_z(b, look=48, z_in=2.0, adx_max=20.0, sl_atr=1.5):
    """Fade stretched closes only when ADX says the market is not trending."""
    c = b.close.values
    m, sd = sma(c, look), pd.Series(c).rolling(look, min_periods=look).std().values
    z = np.divide(c - m, sd, out=np.full_like(c, np.nan), where=sd > 0)
    calm = adx(b, 14) < adx_max
    return np.where((z < -z_in) & calm, 1, np.where((z > z_in) & calm, -1, 0)), atr(b, 14) * sl_atr


def _camarilla_rev(b, level=3, sl_atr=1.0):
    """Close back inside H3/L3 after the bar traded beyond it -> fade toward the pivot."""
    ph, pl, pc = prev_day_hlc(b)
    k = {3: 1.1 / 4, 4: 1.1 / 2}[level]
    H, L = pc + (ph - pl) * k, pc - (ph - pl) * k
    hi, lo, c = b.high.values, b.low.values, b.close.values
    short = (hi > H) & (c < H)
    long_ = (lo < L) & (c > L)
    return np.where(long_, 1, np.where(short, -1, 0)), atr(b, 14) * sl_atr


def _null_random(b, rate=0.02, seed=7, sl_atr=2.0):
    """Coin-flip entries: the cost-drag baseline every real strategy must beat."""
    rng = np.random.default_rng(seed)
    fire = rng.random(len(b)) < rate
    return np.where(fire, rng.choice([-1, 1], len(b)), 0), atr(b, 14) * sl_atr


def _grid(base: dict, **axes) -> list[dict]:
    out = []
    for vals in itertools.product(*axes.values()):
        p = dict(base)
        p.update(dict(zip(axes, vals, strict=True)))
        out.append(p)
    return out


def registry() -> list[Strategy]:
    """Every configuration tried. The COUNT of this list is the honest trial count
    for deflated-Sharpe and FDR: do not prune it after seeing results."""
    S = []
    for p in _grid({}, don=[20, 55], sl_atr=[2.0, 3.0]):
        S.append(Strategy(f"TL_STDB_d{p['don']}_s{p['sl_atr']}", "trend_breakout",
                          "Trend regime + HTF agreement + Donchian breakout continues for >=2R more often than cost-adjusted chance",
                          "close back through the Supertrend band / stop hit", "trending, ADX > 18",
                          "chop, spread > 0.1 ATR, news spikes", "NEXA-Agent-Lab TrendLock_Quantum_Synthesis.mq5",
                          p, _stdb, target_r=2.0, max_hold=72))
    for p in _grid({}, don=[20, 55], sl_atr=[2.0, 3.0]):
        S.append(Strategy(f"DONCHIAN_d{p['don']}_s{p['sl_atr']}", "breakout",
                          "Plain channel breakout (control for TL_STDB's filters)", "stop hit",
                          "any", "range regimes", "Research master section 20 (breakout)", p, _donchian, 2.0, 72))
    for p in _grid({}, look=[48, 120, 240]):
        S.append(Strategy(f"TSMOM_l{p['look']}", "momentum",
                          "Sign of trailing return persists", "stop hit", "persistent trends",
                          "V-reversals", "Research master section 12 (momentum)", p, _tsmom, 2.0, 120))
    for p in _grid({}, look=[24, 48], z_in=[2.0, 2.5]):
        S.append(Strategy(f"MR_Z_l{p['look']}_z{p['z_in']}", "mean_reversion",
                          "Stretched closes revert in non-trending regimes", "stop hit", "ADX < 20",
                          "trend onset", "Research master section 12 (mean reversion)", p, _mr_z, 1.0, 24))
    for p in _grid({}, level=[3, 4]):
        S.append(Strategy(f"CAM_REV_L{p['level']}", "camarilla",
                          "Failed excursion beyond H/L level reverts", "stop hit", "range days",
                          "trend days", "Research master section 11 (Camarilla)", p, _camarilla_rev, 1.5, 24))
    S.append(Strategy("NULL_RANDOM", "null", "No edge by construction", "-", "-", "-", "baseline",
                      {"rate": 0.02, "seed": 7, "sl_atr": 2.0}, _null_random, 2.0, 72))
    return S


def spec_json(strategies: list[Strategy]) -> str:
    return json.dumps([s.spec() for s in strategies], indent=1, default=str)
