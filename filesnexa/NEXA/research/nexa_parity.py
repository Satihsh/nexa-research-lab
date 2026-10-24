"""
nexa_parity.py -- Stage 3 of NEXA_IMPLEMENTATION_PLAN_V3.

PARITY ORACLE. Independently reconstructs the NEXA feature definitions in
Python and compares the result against the f00..f47 values MQL5 actually wrote.

WHY THIS EXISTS
---------------
If Python and MQL5 compute "ATR" or "displacement" even slightly differently, a
model gets trained on values the live engine never sees. That failure is silent:
it passes every unit test, produces a plausible backtest, and presents in
production as alpha decay. This module is the only place in the research tier
permitted to compute a feature, and it computes them solely to be compared --
never to be used.

WHAT THIS MODULE IS NOT
-----------------------
* NOT a second feature engine. Its output is never written into the canonical
  dataset, never fed to a model, never substituted for an MQL5 value.
* NOT a copy of the MQL5 code. It is a reconstruction from the documented
  definitions. Copying the implementation would make the comparison vacuous:
  two copies of the same bug agree perfectly.

AUTHORITY
---------
`PackFeatures()` in NEXA_Intelligence.mqh is the authoritative live
implementation. When Python and MQL5 disagree, that is a finding about the
RESEARCH side until investigation proves otherwise -- MQL5 is what trades.

CAUSALITY
---------
Reconstruction stands at `decision_ts`: the OPEN TIME OF THE CLOSED BAR whose
features produced the decision. The bar at decision_ts is index 0 of the
series (MQL5 copies with start_pos=1, so its index 0 IS the bar at decision_ts),
and only bars at or before it are visible. A reconstruction that can see one bar
further forward would produce a flattering match and a worthless oracle, so the
window is cut explicitly and a leakage self-test asserts it.

PARITY-EXEMPT FEATURES
----------------------
Some features cannot be reconstructed from bar data at all. They are declared
PARITY_EXEMPT_DATA_DEPENDENT, reported separately, and NEVER counted as
matching. `sole_basis_guard()` additionally refuses to let an exempt-only
feature set justify promotion.

FAIL-CLOSED
-----------
Any of: unsupported schema, missing feature, wrong feature order, categorical
mismatch, continuous value outside tolerance, or unestablishable causal
reconstruction -> overall status FAIL. `assert_parity_or_halt()` raises, and the
CLI exits non-zero, so a training stage that forgets to check still cannot run.

Self-contained: pandas + numpy.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import pandas as pd

import nexa_time

SUPPORTED_SCHEMA_VERSIONS = ("1.0",)
FEATURE_COUNT = 48
FEATURE_COLUMNS = [f"f{i:02d}" for i in range(FEATURE_COUNT)]

# V3 tolerance. abs_tol carries values near zero, where a relative test is
# meaningless (1e-9 vs 2e-9 is a 100% relative difference and no error at all).
DEFAULT_REL_TOL = 1e-6
DEFAULT_ABS_TOL = 1e-9

# B-PARITY-TOL (human decision 2026-10-03, option A). The Trade DNA journal packs
# each feature to float32 (PackFeatures) and prints it with DoubleToString(f, 6),
# so a journalled continuous value can differ from the engine's double by up to
# half a unit in the 6th decimal plus float32 rounding. The continuous contract
# therefore also accepts abs_diff <= 0.5e-6 + |mql5| * 2**-23 (twice the float32
# half-ulp bound, for margin). None restores the bare rel/abs rule.
DEFAULT_JOURNAL_DECIMALS = 6
FLOAT32_REL = 2.0 ** -23


class FeatureKind(str, Enum):
    CATEGORICAL = "CATEGORICAL"    # exact equality required
    CONTINUOUS = "CONTINUOUS"      # rel/abs tolerance
    EXEMPT = "PARITY_EXEMPT_DATA_DEPENDENT"


class ParityStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    EXEMPT = "EXEMPT"
    NOT_RECONSTRUCTED = "NOT_RECONSTRUCTED"


@dataclass(frozen=True)
class FeatureSpec:
    index: int
    name: str            # MQL5 NexaSignal member name
    kind: FeatureKind
    note: str = ""


# ---------------------------------------------------------------------------
# THE FROZEN SCHEMA -- order mirrors PackFeatures() exactly.
# Reordering here without reordering MQL5 (or vice versa) is itself a defect the
# oracle must catch, which is why verify_feature_order() reads the MQL5 source.
# ---------------------------------------------------------------------------
FEATURE_SPECS = (
    FeatureSpec(0,  "structureBreakUp",      FeatureKind.CATEGORICAL),
    FeatureSpec(1,  "structureBreakDown",    FeatureKind.CATEGORICAL),
    FeatureSpec(2,  "isBOS_up",              FeatureKind.CATEGORICAL),
    FeatureSpec(3,  "isBOS_down",            FeatureKind.CATEGORICAL),
    FeatureSpec(4,  "isCHoCH_up",            FeatureKind.CATEGORICAL),
    FeatureSpec(5,  "isCHoCH_down",          FeatureKind.CATEGORICAL),
    FeatureSpec(6,  "isMSS_up",              FeatureKind.CATEGORICAL),
    FeatureSpec(7,  "isMSS_down",            FeatureKind.CATEGORICAL),
    FeatureSpec(8,  "displacementUp",        FeatureKind.CATEGORICAL),
    FeatureSpec(9,  "displacementDown",      FeatureKind.CATEGORICAL),
    FeatureSpec(10, "displacementATR",       FeatureKind.CONTINUOUS),
    FeatureSpec(11, "sweepUp",               FeatureKind.CATEGORICAL),
    FeatureSpec(12, "sweepDown",             FeatureKind.CATEGORICAL),
    FeatureSpec(13, "fvgBullActive",         FeatureKind.CATEGORICAL),
    FeatureSpec(14, "fvgBearActive",         FeatureKind.CATEGORICAL),
    FeatureSpec(15, "obBullActive",          FeatureKind.CATEGORICAL),
    FeatureSpec(16, "obBearActive",          FeatureKind.CATEGORICAL),
    FeatureSpec(17, "inOTE_up",              FeatureKind.CATEGORICAL),
    FeatureSpec(18, "inOTE_down",            FeatureKind.CATEGORICAL),
    FeatureSpec(19, "bprActive",             FeatureKind.CATEGORICAL),
    FeatureSpec(20, "trendState",            FeatureKind.CATEGORICAL),
    FeatureSpec(21, "volState",              FeatureKind.CATEGORICAL),
    FeatureSpec(22, "breakoutState",         FeatureKind.CATEGORICAL),
    FeatureSpec(23, "regimeTransitioning",   FeatureKind.CATEGORICAL),
    FeatureSpec(24, "trendM5",               FeatureKind.CATEGORICAL),
    FeatureSpec(25, "trendM15",              FeatureKind.CATEGORICAL),
    FeatureSpec(26, "trendH1",               FeatureKind.CATEGORICAL),
    FeatureSpec(27, "htfAlignment",          FeatureKind.CATEGORICAL),
    FeatureSpec(28, "spreadATRRatio",        FeatureKind.CONTINUOUS),
    FeatureSpec(29, "usdCompositeDirection", FeatureKind.CATEGORICAL,
                "S13: compared when the basket symbols' bars are supplied (MarketData.basket); "
                "exempt for a run without them"),
    FeatureSpec(30, "obiProxy",              FeatureKind.EXEMPT,
                "tick-flow proxy; exact historical tick sequence unavailable"),
    FeatureSpec(31, "cvdProxy",              FeatureKind.EXEMPT,
                "tick-flow proxy; exact historical tick sequence unavailable"),
    FeatureSpec(32, "liqState",              FeatureKind.CATEGORICAL),
    FeatureSpec(33, "liqResolution",         FeatureKind.CATEGORICAL),
    FeatureSpec(34, "liqExcursionATR",       FeatureKind.CONTINUOUS),
    FeatureSpec(35, "liqWickBodyRatio",      FeatureKind.CONTINUOUS),
    FeatureSpec(36, "liqBarsBeyond",         FeatureKind.CATEGORICAL),
    FeatureSpec(37, "liqBarsSinceReclaim",   FeatureKind.CATEGORICAL),
    FeatureSpec(38, "liqSweepDirection",     FeatureKind.CATEGORICAL),
    FeatureSpec(39, "liqResponseDirection",  FeatureKind.CATEGORICAL),
    FeatureSpec(40, "liqMssAfter",           FeatureKind.CATEGORICAL),
    FeatureSpec(41, "liqDisplacementAfter",  FeatureKind.CATEGORICAL),
    FeatureSpec(42, "liqFvgAfter",           FeatureKind.CATEGORICAL),
    FeatureSpec(43, "liqEventActive",        FeatureKind.CATEGORICAL),
    FeatureSpec(44, "liqLevel",              FeatureKind.CATEGORICAL),
    FeatureSpec(45, "liqSetup",              FeatureKind.CATEGORICAL),
    FeatureSpec(46, "liqOrigin",             FeatureKind.EXEMPT,
                "LIVE vs RECONSTRUCTED depends on EA process history, not market data"),
    FeatureSpec(47, "newsRiskActive",        FeatureKind.EXEMPT,
                "economic calendar state at decision time is not reproducible offline"),
)

EXEMPT_INDICES = tuple(s.index for s in FEATURE_SPECS if s.kind is FeatureKind.EXEMPT)
RECONSTRUCTABLE_INDICES = tuple(s.index for s in FEATURE_SPECS if s.kind is not FeatureKind.EXEMPT)
# Features that need the OTHER basket symbols' bars. A run without them treats these as exempt
# (reported, never counted as passing) instead of failing on "never reconstructed".
BASKET_INDICES = (29,)
BASKET_SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY", "XAUUSD")
USDCOMP_LOOKBACK_BARS = 10
USDCOMP_STALE_BARS = 5
ONE_MINUTE = pd.Timedelta(minutes=1)

# enum encodings, mirroring NEXA_Common.mqh
TREND_UP, TREND_DOWN, TREND_RANGE, TREND_UNKNOWN = 0, 1, 2, 3
VOL_HIGH, VOL_NORMAL, VOL_LOW = 0, 1, 2
BRK_NONE, BRK_TRUE, BRK_FALSE = 0, 1, 2
LVL_PDH, LVL_PDL, LVL_ASIA_HIGH, LVL_ASIA_LOW, LVL_COUNT = 0, 1, 2, 3, 4
SWEEP_IDLE, SWEEP_BEYOND, SWEEP_RECLAIMED, SWEEP_CONFIRMED, SWEEP_EXPIRED = 0, 1, 2, 3, 4
RESOLVE_NONE, RESOLVE_REVERSAL, RESOLVE_CONTINUATION = 0, 1, 2
SETUP_NONE = 0
SETUP_BY_LEVEL = {   # (level, is_reversal) -> setup id
    (LVL_PDH, True): 1, (LVL_PDH, False): 2,
    (LVL_PDL, True): 3, (LVL_PDL, False): 4,
    (LVL_ASIA_HIGH, True): 5, (LVL_ASIA_HIGH, False): 6,
    (LVL_ASIA_LOW, True): 7, (LVL_ASIA_LOW, False): 8,
}


@dataclass
class ParityConfig:
    """Broker/session semantics needed to reproduce the live engine's view."""
    atr_period: int = 14
    swing_lookback: int = 2
    displacement_atr_min: float = 1.20
    sweep_lookback_bars: int = 20
    regime_atr_history: int = 100
    range_atr_ratio_max: float = 1.50
    breakout_fail_window: int = 5
    gmt_offset: int = 2                      # broker server hours ahead of GMT (standard time)
    server_follows_us_dst: bool = True       # +1 h inside US DST (Pepperstone = New York + 7 h; D-TZ)
    min_sweep_excursion_atr: float = 0.10
    max_sweep_excursion_atr: float = 2.50
    max_bars_beyond: int = 6
    response_window_bars: int = 8
    event_valid_bars: int = 12
    rel_tol: float = DEFAULT_REL_TOL
    abs_tol: float = DEFAULT_ABS_TOL
    journal_decimals: int | None = DEFAULT_JOURNAL_DECIMALS
    accepted_ties: tuple = ()               # AcceptedTie entries (see load_accepted_ties)


# ---------------------------------------------------------------------------
# Independent indicator reconstruction
# ---------------------------------------------------------------------------

def mt5_iatr(high, low, close, period: int) -> np.ndarray:
    """
    MT5 built-in iATR: a SIMPLE moving average of the true range over `period`.

    This is what NEXA_Features.mqh reads (iATR handles, CopyBuffer shift 1), so it
    is what the oracle must reproduce. Verified on real Pepperstone tester Trade
    DNA (GBPUSD M1, 2025-06-02 week): SMA(TR,14) reproduced f10 displacementATR
    on 400/400 sampled rows within 1e-6; Wilder smoothing did not (median abs
    error 1.8e-2). The first true range is high-low (no previous close), and the
    first `period` values (indices 0..period-1) are NaN.
    """
    h = np.asarray(high, dtype="float64")
    low_a = np.asarray(low, dtype="float64")
    c = np.asarray(close, dtype="float64")
    n = len(h)
    atr = np.full(n, np.nan)
    if n < period or period < 1:
        return atr
    tr = np.empty(n)
    tr[0] = h[0] - low_a[0]
    prev_close = c[:-1]
    tr[1:] = np.maximum.reduce([h[1:] - low_a[1:], np.abs(h[1:] - prev_close), np.abs(low_a[1:] - prev_close)])
    csum = np.concatenate(([0.0], np.cumsum(tr)))
    atr[period - 1:] = (csum[period:] - csum[:-period]) / period
    return atr


def wilder_atr(high, low, close, period: int) -> np.ndarray:
    """
    Wilder ATR (RMA of true range). NOT what MT5 iATR computes -- see mt5_iatr,
    which the parity reconstruction uses. Kept for research use and its tests.

    Warm-up is explicit: the first `period` values are NaN, then a simple mean
    of the first `period` true ranges seeds the recursion. MT5 does the same, and
    a reconstruction that instead started smoothing from bar 0 would drift for
    dozens of bars and produce mismatches that look like a formula error.
    """
    h = np.asarray(high, dtype="float64")
    low_a = np.asarray(low, dtype="float64")
    c = np.asarray(close, dtype="float64")
    n = len(h)
    atr = np.full(n, np.nan)
    if n < period + 1 or period < 1:
        return atr
    tr = np.empty(n)
    tr[0] = h[0] - low_a[0]
    prev_close = c[:-1]
    tr[1:] = np.maximum.reduce([
        h[1:] - low_a[1:],
        np.abs(h[1:] - prev_close),
        np.abs(low_a[1:] - prev_close),
    ])
    atr[period] = tr[1:period + 1].mean()
    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def is_swing_high(highs: np.ndarray, idx: int, lookback: int) -> bool:
    """Strict swing: every neighbour within `lookback` on BOTH sides is lower."""
    n = len(highs)
    if lookback < 1 or idx - lookback < 0 or idx + lookback >= n:
        return False
    h = highs[idx]
    for i in range(1, lookback + 1):
        if highs[idx - i] >= h or highs[idx + i] >= h:
            return False
    return True


def is_swing_low(lows: np.ndarray, idx: int, lookback: int) -> bool:
    n = len(lows)
    if lookback < 1 or idx - lookback < 0 or idx + lookback >= n:
        return False
    low_v = lows[idx]
    for i in range(1, lookback + 1):
        if lows[idx - i] <= low_v or lows[idx + i] <= low_v:
            return False
    return True


def last_swing_high(highs: np.ndarray, start: int, max_bars: int, lookback: int):
    """Series-indexed scan (0 = newest closed bar), walking back in time."""
    n = len(highs)
    limit = min(start + max_bars, n - lookback - 1)
    for s in range(start, max(limit, start)):
        if is_swing_high(highs, s, lookback):
            return highs[s], s
    return 0.0, -1


def last_swing_low(lows: np.ndarray, start: int, max_bars: int, lookback: int):
    n = len(lows)
    limit = min(start + max_bars, n - lookback - 1)
    for s in range(start, max(limit, start)):
        if is_swing_low(lows, s, lookback):
            return lows[s], s
    return 0.0, -1


def swing_trend(highs: np.ndarray, lows: np.ndarray, lookback: int) -> int:
    """Higher-highs + higher-lows = UP; lower both = DOWN; else RANGE."""
    h1, hi1 = last_swing_high(highs, lookback, 80, lookback)
    l1, lo1 = last_swing_low(lows, lookback, 80, lookback)
    if hi1 < 0 or lo1 < 0:
        return TREND_UNKNOWN
    h2, hi2 = last_swing_high(highs, hi1 + 1, 80, lookback)
    l2, lo2 = last_swing_low(lows, lo1 + 1, 80, lookback)
    if hi2 < 0 or lo2 < 0:
        return TREND_UNKNOWN
    if h1 > h2 and l1 > l2:
        return TREND_UP
    if h1 < h2 and l1 < l2:
        return TREND_DOWN
    return TREND_RANGE


def vol_regime(atr_series: np.ndarray, atr_now: float, history: int) -> int:
    """ATR vs its own trailing mean. Thresholds 1.30 / 0.70.

    `atr_series` is SERIES order (index 0 = newest closed bar = atr_now). Mirrors
    NEXA_Features.mqh VolRegime(): CopyBuffer(handle, 0, 1, history) takes the
    `history` most recent values FROM SHIFT 1 -- i.e. INCLUDING atr_now -- and skips
    non-finite / non-positive entries inside that span. The previous oracle passed
    atr_series[1:] (excluding atr_now) and took hist[-history:] (the OLDEST values of
    a newest-first array); both diverged from MQL5 (volState ~4% mismatch on real
    Pepperstone Trade DNA, 2026-09-27).
    """
    if atr_now is None or not np.isfinite(atr_now) or atr_now <= 0:
        return VOL_NORMAL
    span = np.asarray(atr_series, dtype="float64")[:history]
    hist = span[np.isfinite(span) & (span > 0)]
    if len(hist) == 0:
        return VOL_NORMAL
    avg = float(hist.mean())
    if avg <= 0:
        return VOL_NORMAL
    ratio = atr_now / avg
    if ratio > 1.30:
        return VOL_HIGH
    if ratio < 0.70:
        return VOL_LOW
    return VOL_NORMAL


def range_vs_trend(highs, lows, closes, atr_now: float, bars: int, max_ratio: float) -> int:
    if atr_now <= 0 or bars < 2 or len(highs) < bars:
        return TREND_UNKNOWN
    hh = float(np.max(highs[:bars]))
    ll = float(np.min(lows[:bars]))
    if (hh - ll) / atr_now <= max_ratio:
        return TREND_RANGE
    return TREND_UP if closes[0] > closes[bars - 1] else TREND_DOWN


def detect_fvg(highs, lows):
    """Three-candle imbalance between bar[2] and bar[0]."""
    if len(highs) < 3:
        return False, False
    bull = bool(highs[2] < lows[0])
    bear = bool(lows[2] > highs[0])
    return bull, bear


def detect_order_block(opens, closes, highs, lows, brk_up: bool, brk_dn: bool):
    """Last opposite-coloured candle within the 10 bars before the break."""
    n = len(opens)
    lim = min(10, n)
    ob_bull = ob_bear = False
    if brk_up:
        for s in range(1, lim):
            if closes[s] < opens[s]:
                ob_bull = True
                break
    if brk_dn:
        for s in range(1, lim):
            if closes[s] > opens[s]:
                ob_bear = True
                break
    return ob_bull, ob_bear


def detect_ote(highs, lows, closes, disp_up: bool, disp_dn: bool, lookback: int):
    """0.618-0.79 retracement band of the displacement leg."""
    ote_up = ote_dn = False
    if len(closes) == 0:
        return False, False
    cur = closes[0]
    if disp_up:
        leg_start, idx = last_swing_low(lows, lookback, 40, lookback)
        leg_end = highs[0]
        if idx >= 0 and leg_start > 0 and leg_end > leg_start:
            f618 = leg_end - (leg_end - leg_start) * 0.618
            f79 = leg_end - (leg_end - leg_start) * 0.79
            ote_up = bool(cur <= f618 and cur >= f79)
    if disp_dn:
        leg_start, idx = last_swing_high(highs, lookback, 40, lookback)
        leg_end = lows[0]
        if idx >= 0 and leg_start > 0 and leg_start > leg_end:
            f618 = leg_end + (leg_start - leg_end) * 0.618
            f79 = leg_end + (leg_start - leg_end) * 0.79
            ote_dn = bool(cur >= f618 and cur <= f79)
    return ote_up, ote_dn


# ---------------------------------------------------------------------------
# Stateful reconstructions (breakout memory, liquidity machine)
# ---------------------------------------------------------------------------

class BreakoutMemory:
    """
    Two-stage breakout classifier.

    A false breakout is break-THEN-rejection, so it cannot be read off one bar.
    This mirrors the documented state contract, not the MQL5 source text.
    """

    def __init__(self, fail_window: int):
        self.level = 0.0
        self.direction = 0
        self.bars_ago = 0
        self.fail_window = fail_window

    def classify(self, brk_up: bool, brk_dn: bool,
                 swing_high: float, swing_low: float, close_now: float) -> int:
        if brk_up and swing_high > 0:
            self.level, self.direction, self.bars_ago = swing_high, 1, 0
            return BRK_TRUE
        if brk_dn and swing_low > 0:
            self.level, self.direction, self.bars_ago = swing_low, -1, 0
            return BRK_TRUE
        if self.direction != 0 and self.level > 0:
            self.bars_ago += 1
            failed = (close_now < self.level) if self.direction > 0 else (close_now > self.level)
            if failed:
                self.level, self.direction, self.bars_ago = 0.0, 0, 0
                return BRK_FALSE
            if self.bars_ago > self.fail_window:
                self.level, self.direction, self.bars_ago = 0.0, 0, 0
            else:
                return BRK_TRUE
        return BRK_NONE


class LiquidityEvent:
    __slots__ = ("bars_beyond", "bars_since_reclaim", "displacement_after",
                 "excursion_atr", "extreme_beyond", "fvg_after", "level_id",
                 "level_price", "mss_after", "resolution", "response_direction",
                 "setup", "state", "sweep_direction", "wick_body_ratio")

    def __init__(self, level_id: int):
        self.level_id = level_id
        self.reset(0.0)

    def reset(self, level_price: float) -> None:
        self.state = SWEEP_IDLE
        self.resolution = RESOLVE_NONE
        self.level_price = level_price
        self.extreme_beyond = 0.0
        self.excursion_atr = 0.0
        self.wick_body_ratio = 0.0
        self.bars_beyond = 0
        self.bars_since_reclaim = 0
        self.sweep_direction = 0
        self.response_direction = 0
        self.displacement_after = False
        self.mss_after = False
        self.fvg_after = False
        self.setup = SETUP_NONE


def level_polarity(level_id: int) -> int:
    return 1 if level_id in (LVL_PDH, LVL_ASIA_HIGH) else -1


class LiquidityMachine:
    """
    IDLE -> BEYOND -> RECLAIMED -> CONFIRMED -> EXPIRED, one tracker per pool.

    Direction is never inferred from the sweep itself: a taken high may precede a
    reversal or a continuation, and only the structural response after the
    reclaim distinguishes them.
    """

    def __init__(self, cfg: ParityConfig):
        self.cfg = cfg
        self.events = [LiquidityEvent(i) for i in range(LVL_COUNT)]
        self.last_bar_fed = None

    def advance(self, level_id: int, level_price: float, atr: float,
                bar_high: float, bar_low: float, bar_open: float, bar_close: float,
                disp_up: bool, disp_dn: bool, mss_up: bool, mss_dn: bool,
                fvg_bull: bool, fvg_bear: bool, point: float) -> None:
        ev = self.events[level_id]
        if level_price <= 0 or atr <= 0 or not np.isfinite(level_price) or not np.isfinite(atr):
            return
        if ev.level_price > 0 and abs(ev.level_price - level_price) > point:
            ev.reset(level_price)           # level moved: old pool no longer exists
            return
        ev.level_price = level_price

        pol = level_polarity(level_id)
        beyond = (bar_high > level_price) if pol > 0 else (bar_low < level_price)
        closed_back = (bar_close < level_price) if pol > 0 else (bar_close > level_price)

        if ev.state == SWEEP_IDLE:
            if not beyond:
                return
            excursion = (bar_high - level_price) if pol > 0 else (level_price - bar_low)
            exc_atr = excursion / atr
            if exc_atr < self.cfg.min_sweep_excursion_atr:
                return
            if exc_atr > self.cfg.max_sweep_excursion_atr:
                ev.reset(level_price)
                return
            ev.state = SWEEP_BEYOND
            ev.sweep_direction = pol
            ev.extreme_beyond = bar_high if pol > 0 else bar_low
            ev.excursion_atr = exc_atr
            ev.bars_beyond = 1
            body = abs(bar_close - bar_open)
            wick = (bar_high - max(bar_open, bar_close)) if pol > 0 \
                else (min(bar_open, bar_close) - bar_low)
            ev.wick_body_ratio = (wick / body) if body > 0 else 99.0
            if closed_back:
                ev.state = SWEEP_RECLAIMED
            return

        if ev.state == SWEEP_BEYOND:
            if beyond:
                ev.bars_beyond += 1
                ev.extreme_beyond = max(ev.extreme_beyond, bar_high) if pol > 0 \
                    else min(ev.extreme_beyond, bar_low)
                excursion = (ev.extreme_beyond - level_price) if pol > 0 \
                    else (level_price - ev.extreme_beyond)
                ev.excursion_atr = excursion / atr
                if ev.bars_beyond > self.cfg.max_bars_beyond or \
                        ev.excursion_atr > self.cfg.max_sweep_excursion_atr:
                    ev.reset(level_price)   # acceptance, not a grab
                return
            if closed_back:
                ev.state = SWEEP_RECLAIMED
            return

        if ev.state == SWEEP_RECLAIMED:
            ev.bars_since_reclaim += 1
            rev_disp = disp_dn if pol > 0 else disp_up
            rev_mss = mss_dn if pol > 0 else mss_up
            rev_fvg = fvg_bear if pol > 0 else fvg_bull
            cont_disp = disp_up if pol > 0 else disp_dn
            cont_mss = mss_up if pol > 0 else mss_dn
            cont_fvg = fvg_bull if pol > 0 else fvg_bear
            if rev_mss or rev_disp:
                ev.state = SWEEP_CONFIRMED
                ev.resolution = RESOLVE_REVERSAL
                ev.response_direction = -pol
                ev.displacement_after, ev.mss_after, ev.fvg_after = rev_disp, rev_mss, rev_fvg
                ev.setup = SETUP_BY_LEVEL[(level_id, True)]
                ev.bars_since_reclaim = 0
                return
            if cont_mss or cont_disp:
                ev.state = SWEEP_CONFIRMED
                ev.resolution = RESOLVE_CONTINUATION
                ev.response_direction = pol
                ev.displacement_after, ev.mss_after, ev.fvg_after = cont_disp, cont_mss, cont_fvg
                ev.setup = SETUP_BY_LEVEL[(level_id, False)]
                ev.bars_since_reclaim = 0
                return
            if ev.bars_since_reclaim > self.cfg.response_window_bars:
                ev.state = SWEEP_EXPIRED
            return

        if ev.state == SWEEP_CONFIRMED:
            ev.bars_since_reclaim += 1
            if ev.bars_since_reclaim > self.cfg.event_valid_bars:
                ev.state = SWEEP_EXPIRED
            return

        if ev.state == SWEEP_EXPIRED and not beyond:
            ev.reset(level_price)

    def primary(self):
        """CONFIRMED outranks RECLAIMED; ties broken by recency."""
        best, best_rank = None, -1
        for ev in self.events:
            rank = 2 if ev.state == SWEEP_CONFIRMED else (1 if ev.state == SWEEP_RECLAIMED else -1)
            if rank < 0:
                continue
            if rank > best_rank or (best is not None and rank == best_rank
                                    and ev.bars_since_reclaim < best.bars_since_reclaim):
                best, best_rank = ev, rank
        return best


# ---------------------------------------------------------------------------
# Market data container
# ---------------------------------------------------------------------------

TF_LENGTH = {"M1": pd.Timedelta(minutes=1), "M5": pd.Timedelta(minutes=5), "M15": pd.Timedelta(minutes=15),
             "M30": pd.Timedelta(minutes=30), "H1": pd.Timedelta(hours=1), "H4": pd.Timedelta(hours=4),
             "D1": pd.Timedelta(days=1)}


@dataclass
class MarketData:
    """
    Bar history keyed by timeframe label ('M1','M5','M15','H1','D1').

    Each frame needs columns time, open, high, low, close and must be sorted
    ascending by time. `point` is the symbol's price increment.
    """
    bars: dict
    point: float = 1e-5
    basket: dict = field(default_factory=dict)       # symbol -> entry-timeframe bars (time, close), for f29
    _gmt_hours: dict = field(default_factory=dict, repr=False, compare=False)

    def gmt_hours(self, tf: str, gmt_offset: int, us_dst: bool) -> np.ndarray:
        """GMT hour of every bar of `tf` under the EA's clock (cached per frame and clock)."""
        frame = self.bars[tf]
        key = (tf, gmt_offset, us_dst, len(frame))
        if key not in self._gmt_hours:
            off = server_gmt_offset_hours(frame["time"], gmt_offset, us_dst)
            self._gmt_hours[key] = (frame["time"] - pd.to_timedelta(off, unit="h")).dt.hour.to_numpy()
        return self._gmt_hours[key]

    def window(self, tf: str, decision_ts: pd.Timestamp, count: int, entry_tf: str = "M1"):
        """
        Series-indexed window of CLOSED bars at decision time, newest first.

        The decision is taken when the entry bar opened at decision_ts closes, i.e.
        at decision_ts + len(entry_tf). A `tf` bar is visible only if it has closed
        by then: open + len(tf) <= decision_ts + len(entry_tf). This is exactly what
        MQL5's CopyRates(tf, start_pos=1) returns at that moment.

        For the entry timeframe this reduces to open <= decision_ts (the bar AT
        decision_ts is index 0). For M5/M15/H1 it EXCLUDES the forming bar: the
        previous `open <= decision_ts` cut admitted e.g. the 10:00 M5 bar at a 10:02
        M1 decision, whose exported OHLC contains prices up to 10:05 -- a look-ahead
        in the oracle found on real Pepperstone Trade DNA (2026-09-27).

        The decision clock is the FIRST TICK of the next entry bar, because that is
        when MQL5 runs its new-bar logic. After a tick gap (daily break, weekend,
        quiet minutes) the next entry bar opens later than decision_ts + len(entry_tf),
        and CopyRates(tf, 1) then already returns the higher-timeframe bars that
        closed during the gap (B-PARITY-EDGE-1, 2026-10-03). The entry-timeframe
        window is unaffected: no entry bar exists inside the gap.
        """
        frame = self.bars.get(tf)
        if frame is None or not len(frame):
            return None
        clock = decision_ts + TF_LENGTH[entry_tf]
        if tf != entry_tf:
            entry = self.bars.get(entry_tf)
            if entry is not None and len(entry):
                et = entry["time"].to_numpy()
                i = et.searchsorted(np.datetime64(decision_ts), side="right")
                if i < len(et):
                    clock = max(clock, pd.Timestamp(et[i]))
        cut = clock - TF_LENGTH[tf]
        visible = frame[frame["time"] <= cut]
        if not len(visible):
            return None
        tail = visible.tail(count)
        return {
            "time": tail["time"].to_numpy()[::-1],
            "open": tail["open"].to_numpy(dtype="float64")[::-1],
            "high": tail["high"].to_numpy(dtype="float64")[::-1],
            "low": tail["low"].to_numpy(dtype="float64")[::-1],
            "close": tail["close"].to_numpy(dtype="float64")[::-1],
        }

    def prev_day_levels(self, decision_ts: pd.Timestamp):
        """
        PDH/PDL/PDC from the D1 bar COMPLETED before decision_ts's own day.

        Broker-relative by construction: the D1 series supplied here must come
        from the execution broker, because a different daily rollover produces
        different levels for the same calendar date.
        """
        d1 = self.bars.get("D1")
        if d1 is None or not len(d1):
            return None
        # The latest D1 bar of an EARLIER day (MQL5 GetPreviousDayLevelsAsOf: the bar
        # before the one containing asOf). Selecting by date, not by position, keeps this
        # correct when the series lacks the current forming day, as the tester D1
        # exports do (B-PARITY-LIQ RC2, 2026-10-03).
        before = d1[d1["time"] < decision_ts.normalize()]
        if not len(before):
            return None
        prev = before.iloc[-1]
        if prev["high"] <= 0 or prev["low"] <= 0 or prev["high"] < prev["low"]:
            return None
        return float(prev["high"]), float(prev["low"]), float(prev["close"]), prev["time"]


# ---------------------------------------------------------------------------
# Reconstruction
# ---------------------------------------------------------------------------

@dataclass
class Reconstruction:
    values: dict                     # feature index -> float
    exempt: tuple = EXEMPT_INDICES
    causal_ok: bool = True
    reason: str = ""


def reconstruct_features(decision_ts: pd.Timestamp, data: MarketData,
                         cfg: ParityConfig, *, quote=None,
                         machine: LiquidityMachine | None = None,
                         breakout: BreakoutMemory | None = None,
                         prev_trend_state: int | None = None) -> Reconstruction:
    """
    Reconstruct every non-exempt feature as of decision_ts.

    `quote` is (bid, ask) recorded at decision time. A recorded quote is market
    DATA, not a feature -- using it is legitimate in the same way OHLC is. The
    ATR it is divided by is computed independently here, so f28 still tests a
    real disagreement.

    Stateful features (breakout memory, liquidity machine, regimeTransitioning)
    require the caller to carry state across rows in chronological order, which
    is what `run_parity` does.
    """
    need = max(cfg.regime_atr_history + cfg.atr_period + 5,
               cfg.sweep_lookback_bars + cfg.swing_lookback * 2 + 10, 120)
    entry = data.window("M1", decision_ts, need)
    if entry is None or len(entry["close"]) < cfg.atr_period + cfg.swing_lookback * 2 + 5:
        return Reconstruction({}, causal_ok=False,
                              reason="insufficient entry-timeframe history for warm-up")

    # chronological order for ATR, then flip to series order (0 = newest closed)
    chron_h = entry["high"][::-1]
    chron_l = entry["low"][::-1]
    chron_c = entry["close"][::-1]
    atr_chron = mt5_iatr(chron_h, chron_l, chron_c, cfg.atr_period)
    atr_series = atr_chron[::-1]
    atr_now = atr_series[0]
    if not np.isfinite(atr_now) or atr_now <= 0:
        return Reconstruction({}, causal_ok=False, reason="ATR warm-up incomplete at decision_ts")

    h, low_a, c, o = entry["high"], entry["low"], entry["close"], entry["open"]
    lb = cfg.swing_lookback
    v: dict = {}

    sh, _sh_idx = last_swing_high(h, lb, 60, lb)
    sl, _sl_idx = last_swing_low(low_a, lb, 60, lb)
    last_close = c[0]

    brk_up = bool(sh > 0 and last_close > sh)
    brk_dn = bool(sl > 0 and last_close < sl)
    v[0], v[1] = float(brk_up), float(brk_dn)

    prior_trend = swing_trend(h, low_a, lb)
    v[2] = float(brk_up and prior_trend == TREND_UP)
    v[3] = float(brk_dn and prior_trend == TREND_DOWN)
    choch_up = brk_up and prior_trend != TREND_UP
    choch_dn = brk_dn and prior_trend != TREND_DOWN
    v[4], v[5] = float(choch_up), float(choch_dn)

    body = abs(c[0] - o[0])
    disp_ratio = body / atr_now
    bull = c[0] > o[0]
    disp_up = bool(disp_ratio >= cfg.displacement_atr_min and bull)
    disp_dn = bool(disp_ratio >= cfg.displacement_atr_min and not bull)
    v[8], v[9], v[10] = float(disp_up), float(disp_dn), float(disp_ratio)

    mss_up = choch_up and disp_up
    mss_dn = choch_dn and disp_dn
    v[6], v[7] = float(mss_up), float(mss_dn)

    sweep_hi, _ = last_swing_high(h, lb, cfg.sweep_lookback_bars, lb)
    sweep_lo, _ = last_swing_low(low_a, lb, cfg.sweep_lookback_bars, lb)
    v[12] = float(sweep_hi > 0 and h[0] > sweep_hi and last_close < sweep_hi)   # sweepDown
    v[11] = float(sweep_lo > 0 and low_a[0] < sweep_lo and last_close > sweep_lo)  # sweepUp

    fvg_bull, fvg_bear = detect_fvg(h, low_a)
    v[13], v[14] = float(fvg_bull), float(fvg_bear)

    ob_bull, ob_bear = detect_order_block(o, c, h, low_a, brk_up, brk_dn)
    v[15], v[16] = float(ob_bull), float(ob_bear)

    ote_up, ote_dn = detect_ote(h, low_a, c, disp_up, disp_dn, lb)
    v[17], v[18] = float(ote_up), float(ote_dn)

    # BPR requires both gaps present and overlapping
    if fvg_bull and fvg_bear:
        bull_b, bull_t = h[2], low_a[0]
        bear_t, bear_b = low_a[2], h[0]
        bpr = not (bull_t < bear_b or bear_t < bull_b)
    else:
        bpr = False
    v[19] = float(bpr)

    v[20] = float(prior_trend if prior_trend != TREND_UNKNOWN
                  else range_vs_trend(h, low_a, c, atr_now, 30, cfg.range_atr_ratio_max))
    v[21] = float(vol_regime(atr_series, atr_now, cfg.regime_atr_history))

    bmem = breakout if breakout is not None else BreakoutMemory(cfg.breakout_fail_window)
    v[22] = float(bmem.classify(brk_up, brk_dn, sh, sl, last_close))

    v[23] = float(prev_trend_state is not None and int(v[20]) != int(prev_trend_state))

    tf_trend = {}
    for idx, tf in ((24, "M5"), (25, "M15"), (26, "H1")):
        w = data.window(tf, decision_ts, 200)
        if w is None or len(w["close"]) < lb * 2 + 5:
            tf_trend[tf] = TREND_UNKNOWN
        else:
            tf_trend[tf] = swing_trend(w["high"], w["low"], lb)
        v[idx] = float(tf_trend[tf])
    if tf_trend.get("H1") == TREND_UP and tf_trend.get("M15") == TREND_UP:
        v[27] = 1.0
    elif tf_trend.get("H1") == TREND_DOWN and tf_trend.get("M15") == TREND_DOWN:
        v[27] = -1.0
    else:
        v[27] = 0.0

    if quote is not None and quote[0] > 0 and quote[1] > 0:
        v[28] = float((quote[1] - quote[0]) / atr_now)

    # ---- liquidity machine -------------------------------------------------
    mach = machine if machine is not None else LiquidityMachine(cfg)
    pd_levels = data.prev_day_levels(decision_ts)
    asia_h, asia_l = _asia_range_as_of(data, decision_ts, cfg.gmt_offset, cfg.server_follows_us_dst)
    if pd_levels is not None:
        pdh, pdl, _pdc, _src = pd_levels
        prices = {LVL_PDH: pdh, LVL_PDL: pdl, LVL_ASIA_HIGH: asia_h, LVL_ASIA_LOW: asia_l}
        bar_t = entry["time"][0]
        if mach.last_bar_fed is None or bar_t > mach.last_bar_fed:
            mach.last_bar_fed = bar_t
            for lvl_id in range(LVL_COUNT):
                mach.advance(lvl_id, prices[lvl_id], atr_now,
                             h[0], low_a[0], o[0], c[0],
                             disp_up, disp_dn, mss_up, mss_dn, fvg_bull, fvg_bear,
                             data.point)

    ev = mach.primary()
    if ev is None:
        v[32] = float(SWEEP_IDLE); v[33] = float(RESOLVE_NONE)
        v[34] = 0.0; v[35] = 0.0; v[36] = 0.0; v[37] = 0.0
        v[38] = 0.0; v[39] = 0.0; v[40] = 0.0; v[41] = 0.0; v[42] = 0.0
        v[43] = 0.0; v[44] = float(LVL_PDH); v[45] = float(SETUP_NONE)
    else:
        v[32] = float(ev.state); v[33] = float(ev.resolution)
        v[34] = float(ev.excursion_atr); v[35] = float(ev.wick_body_ratio)
        v[36] = float(ev.bars_beyond); v[37] = float(ev.bars_since_reclaim)
        v[38] = float(ev.sweep_direction); v[39] = float(ev.response_direction)
        v[40] = float(ev.mss_after); v[41] = float(ev.displacement_after)
        v[42] = float(ev.fvg_after)
        v[43] = float(ev.state == SWEEP_CONFIRMED)
        v[44] = float(ev.level_id); v[45] = float(ev.setup)

    if data.basket:
        v[29] = float(usd_composite_direction(data.basket, decision_ts))

    return Reconstruction(v)


def usd_composite_direction(basket: dict, decision_ts: pd.Timestamp,
                            bar: pd.Timedelta = ONE_MINUTE) -> int:
    """
    Mirror of MQL5 UsdCompositeDirection (NEXA_Intelligence.mqh, S13 2026-10-03): each basket symbol
    is read by TIME -- its last bar at or before the decision bar's open time and its last bar at or
    before 10 bars earlier; a symbol is not counted when either bar is more than 5 bars stale or both
    are the same bar. Votes: USDJPY up = USD strong, the others up = USD weak. +1 strong / -1 weak
    when at most one counted symbol disagrees, else 0; fewer than 2 counted symbols -> 0.
    """
    t10 = decision_ts - USDCOMP_LOOKBACK_BARS * bar
    stale = USDCOMP_STALE_BARS * bar
    strong = weak = counted = 0
    for sym in BASKET_SYMBOLS:
        f = basket.get(sym)
        if f is None or not len(f):
            continue
        tt = f["time"].to_numpy()
        i0 = int(tt.searchsorted(np.datetime64(decision_ts), side="right")) - 1
        i10 = int(tt.searchsorted(np.datetime64(t10), side="right")) - 1
        if i0 < 0 or i10 < 0 or i10 >= i0:
            continue
        if decision_ts - pd.Timestamp(tt[i0]) > stale or t10 - pd.Timestamp(tt[i10]) > stale:
            continue
        c = f["close"].to_numpy()
        c0, c10 = float(c[i0]), float(c[i10])
        if c0 <= 0 or c10 <= 0:
            continue
        up = c0 > c10
        counted += 1
        if sym == "USDJPY":
            strong, weak = strong + up, weak + (not up)
        else:
            strong, weak = strong + (not up), weak + up
    if counted < 2:
        return 0
    if strong >= counted - 1:
        return 1
    if weak >= counted - 1:
        return -1
    return 0


def server_gmt_offset_hours(server_times, gmt_offset: int, us_dst: bool = True) -> np.ndarray:
    """
    Mirror of MQL5 NexaServerGMTOffsetHours (NEXA_Common.mqh, D-TZ 2026-10-03): the
    standard-time offset, plus 1 h while New York (= server - 7 h) is inside US DST,
    using nexa_time's explicit US rule. Server hours that nexa_time flags as
    NONEXISTENT / AMBIGUOUS (Sunday switch hours; markets closed) fall inside the
    [start, end) interval and therefore get the DST offset, exactly as in MQL5.
    """
    t = pd.Series(pd.to_datetime(server_times)).reset_index(drop=True)
    off = np.full(len(t), int(gmt_offset), dtype=np.int64)
    if not us_dst or not len(t):
        return off
    ny = t - pd.Timedelta(hours=7)
    for y in sorted(set(ny.dt.year.dropna().astype(int))):
        if y < 1987:
            continue
        start, end = nexa_time.us_dst_bounds_local(y)
        off[((ny.dt.year == y) & (ny >= start) & (ny < end)).to_numpy()] += 1
    return off


def _asia_range_as_of(data: MarketData, decision_ts: pd.Timestamp, gmt_offset: int, us_dst: bool = True):
    """
    Asia high/low accumulated INCREMENTALLY up to decision_ts.

    The session's final range must never leak backwards onto an earlier bar:
    a bar at 02:00 GMT sees the range as of 02:00, not the completed 00:00-09:00
    range known only at 09:00.

    Mirrors MQL5 UpdateSessionLevels: the range restarts at the first bar of GMT
    hour 0 and only bars in GMT hours 0-8 extend it; until the next such bar it is
    CARRIED FORWARD across days and weekends. On a Monday before the first GMT
    hour-0 bar the level is therefore Friday's Asia range, not 0
    (B-PARITY-LIQ RC1, 2026-10-03).
    """
    m1 = data.bars.get("M1")
    if m1 is None or not len(m1):
        return 0.0, 0.0
    n = int(m1["time"].searchsorted(decision_ts, side="right"))       # bars up to decision_ts
    if not n:
        return 0.0, 0.0
    g = data.gmt_hours("M1", gmt_offset, us_dst)[:n]
    starts = np.flatnonzero((g == 0) & (np.r_[-1, g[:-1]] != 0))
    if not len(starts):
        return 0.0, 0.0
    s = starts[-1]
    keep = g[s:] < 9
    return float(m1["high"].to_numpy()[s:n][keep].max()), float(m1["low"].to_numpy()[s:n][keep].min())


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

@dataclass
class Mismatch:
    row_id: str
    symbol: str
    timeframe: str
    decision_ts: str
    feature_index: int
    feature_name: str
    kind: str
    mql5_value: float
    python_value: float
    abs_diff: float
    rel_diff: float
    tolerance: str
    status: str

    def as_dict(self) -> dict:
        return dict(self.__dict__)


@dataclass
class ParityResult:
    status: ParityStatus
    mismatches: list
    per_feature: dict
    stats: dict
    notes: list = field(default_factory=list)
    accepted: list = field(default_factory=list)     # mismatches matched to an AcceptedTie

    @property
    def passed(self) -> bool:
        return self.status is ParityStatus.PASS

    def mismatch_frame(self) -> pd.DataFrame:
        return pd.DataFrame([m.as_dict() for m in self.mismatches])

    def report(self) -> str:
        lines = [
            "NEXA parity oracle report",
            "=" * 72,
            f"rows compared      : {self.stats.get('rows_compared')}",
            (f"rows skipped       : {self.stats.get('rows_skipped')} "
             f"(causal reconstruction unavailable)"),
            f"features compared  : {self.stats.get('features_compared')} of {FEATURE_COUNT}",
            (f"parity-exempt      : {self.stats.get('features_exempt')} "
             f"-> {sorted(self.stats.get('exempt_names', []))}"),
            (f"tolerance          : rel<={self.stats.get('rel_tol')} abs<={self.stats.get('abs_tol')}"
             f" journal_decimals={self.stats.get('journal_decimals')}"),
            f"mismatches         : {len(self.mismatches)}",
            f"accepted ties      : {len(self.accepted)} (register entries: {self.stats.get('ties_listed', 0)})",
            f"STATUS             : {self.status.value}",
            "-" * 72,
        ]
        if self.per_feature:
            worst = sorted(self.per_feature.items(),
                           key=lambda kv: kv[1]["mismatches"], reverse=True)[:12]
            lines.append("per-feature (worst first):")
            for name, s in worst:
                lines.append(
                    f"  {name:<24} {s['status']:<18} n={s['compared']:<5} "
                    f"bad={s['mismatches']:<5} max_abs={s['max_abs']:.3e} "
                    f"max_rel={s['max_rel']:.3e}")
        for n in self.notes:
            lines.append(f"NOTE: {n}")
        if self.mismatches:
            lines.append("-" * 72)
            lines.append("first mismatches:")
            for m in self.mismatches[:10]:
                lines.append(
                    f"  {m.decision_ts} {m.symbol}/{m.timeframe} {m.feature_name}"
                    f"[{m.feature_index}] mql5={m.mql5_value!r} py={m.python_value!r} "
                    f"abs={m.abs_diff:.3e} rel={m.rel_diff:.3e} tol={m.tolerance} -> {m.status}")
        return "\n".join(lines)


def journal_quantum(journal_value: float, journal_decimals: int | None) -> float:
    """Largest representation error of a journalled value: 6-decimal print of a float32."""
    if journal_decimals is None:
        return 0.0
    return 0.5 * 10.0 ** (-journal_decimals) + abs(journal_value) * FLOAT32_REL


def within_tolerance(a: float, b: float, rel_tol: float, abs_tol: float,
                     journal_decimals: int | None = None):
    """
    Absolute OR relative OR (when `journal_decimals` is set) within the journal's
    own quantisation of `a`, the MQL5 journal value. Returns (ok, abs_diff, rel_diff).
    """
    if not np.isfinite(a) or not np.isfinite(b):
        return False, float("inf"), float("inf")
    abs_diff = abs(a - b)
    denom = max(abs(a), abs(b))
    rel_diff = abs_diff / denom if denom > 0 else 0.0
    ok = abs_diff <= abs_tol or rel_diff <= rel_tol or abs_diff <= journal_quantum(a, journal_decimals)
    return bool(ok), abs_diff, rel_diff


@dataclass(frozen=True)
class AcceptedTie:
    """
    One human-accepted mismatch: an exact floating-point tie at a decision
    threshold (or a value that follows from one), documented with its root cause.
    It is accepted only on the SAME symbol, decision bar and feature with the SAME
    values on both sides; any other difference on that row still fails.
    """
    symbol: str
    decision_ts: str
    feature_name: str
    mql5_value: float
    python_value: float
    cause: str

    def key(self) -> tuple:
        return (self.symbol, pd.Timestamp(self.decision_ts), self.feature_name)

    def matches(self, mql5_value: float, python_value: float) -> bool:
        return (abs(mql5_value - self.mql5_value) <= 1e-9
                and abs(python_value - self.python_value) <= 1e-9 * max(1.0, abs(self.python_value)))


def load_accepted_ties(path: str) -> tuple:
    """Load the reviewed tie register (parity_accepted_ties.json). Every entry needs a cause."""
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    ties = []
    for t in doc["ties"]:
        tie = AcceptedTie(str(t["symbol"]), str(t["decision_ts"]), str(t["feature_name"]),
                          float(t["mql5_value"]), float(t["python_value"]), str(t["cause"]))
        if not tie.cause.strip():
            raise ValueError(f"accepted tie without a cause: {tie}")
        ties.append(tie)
    keys = [t.key() for t in ties]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate entries in the accepted-tie register")
    return tuple(ties)


def verify_feature_order(mql5_intelligence_path: str) -> tuple:
    """
    Cross-check FEATURE_SPECS order against PackFeatures() in the MQL5 source.

    This reads the ORDER (a schema contract), never the VALUES. A silent reorder
    on either side would make every later comparison meaningless while still
    reporting a clean pass, so it is checked structurally.
    """
    if not os.path.exists(mql5_intelligence_path):
        return False, [f"MQL5 source not found: {mql5_intelligence_path}"]
    with open(mql5_intelligence_path, "r", encoding="utf-8", errors="replace") as fh:
        src = fh.read()
    names = re.findall(r"out\[k\+\+\]\s*=\s*\(float\)\s*sig\.([A-Za-z_0-9]+)", src)
    names += re.findall(r"out\[k\+\+\]\s*=\s*\(float\)\((?:sig\.)?([A-Za-z_0-9]+)\s*\?", src)
    problems = []
    if len(names) != FEATURE_COUNT:
        problems.append(f"MQL5 packs {len(names)} features, schema declares {FEATURE_COUNT}")
    for spec, mql_name in zip(FEATURE_SPECS, names):
        if spec.name != mql_name:
            problems.append(
                f"order mismatch at index {spec.index}: schema '{spec.name}' vs MQL5 '{mql_name}'")
    return (not problems), problems


def run_parity(frame: pd.DataFrame, data: MarketData, cfg: ParityConfig | None = None,
               *, mql5_source: str | None = None,
               events=("OPEN", "FILL")) -> ParityResult:
    """
    Compare MQL5 feature values in `frame` against an independent reconstruction.

    `frame` is a Stage 2 canonical frame. Rows are processed in chronological
    order because breakout memory, the liquidity machine and regimeTransitioning
    are stateful -- evaluating them out of order would produce wrong state and a
    misleading mismatch list.
    """
    cfg = cfg or ParityConfig()
    notes: list = []
    mismatches: list = []
    accepted: list = []
    ties = {t.key(): t for t in cfg.accepted_ties}
    ties_seen: set = set()

    if "schema_version" in frame.columns and len(frame):
        versions = sorted(set(frame["schema_version"].astype(str)))
        bad = [v for v in versions if v not in SUPPORTED_SCHEMA_VERSIONS]
        if bad:
            return ParityResult(
                ParityStatus.FAIL, [], {},
                {"rows_compared": 0, "rows_skipped": len(frame), "reason": "schema"},
                [(f"unsupported schema_version {bad}; "
                  "parity cannot be established")])

    missing = [c for c in FEATURE_COLUMNS if c not in frame.columns]
    if missing:
        return ParityResult(
            ParityStatus.FAIL, [], {},
            {"rows_compared": 0, "rows_skipped": len(frame), "reason": "missing_features"},
            [(f"feature columns absent from dataset: {missing[:8]} "
              f"({len(missing)} total) -- parity FAIL")])

    if mql5_source:
        ok, problems = verify_feature_order(mql5_source)
        if not ok:
            return ParityResult(
                ParityStatus.FAIL, [], {},
                {"rows_compared": 0, "rows_skipped": len(frame), "reason": "feature_order"},
                [("feature ORDER disagrees with MQL5 PackFeatures(): "
                  + "; ".join(problems))])
        notes.append(f"feature order verified against {os.path.basename(mql5_source)}")

    anchor_col = "decision_ts_effective" if "decision_ts_effective" in frame.columns else "decision_ts"
    work = frame[frame["event"].isin(events)] if "event" in frame.columns else frame
    work = work[work[anchor_col].notna()].sort_values(anchor_col, kind="mergesort")

    exempt_now = set(EXEMPT_INDICES) | (set() if data.basket else set(BASKET_INDICES))
    if not data.basket:
        notes.append("usdCompositeDirection not compared: no basket bars supplied (MarketData.basket)")
    per_feature = {
        s.name: {"compared": 0, "mismatches": 0, "max_abs": 0.0, "max_rel": 0.0,
                 "status": (ParityStatus.EXEMPT.value if s.index in exempt_now
                            else ParityStatus.NOT_RECONSTRUCTED.value),
                 "kind": s.kind.value}
        for s in FEATURE_SPECS
    }

    machine = LiquidityMachine(cfg)
    breakout = BreakoutMemory(cfg.breakout_fail_window)
    prev_trend = None
    rows_compared = rows_skipped = 0

    for _, row in work.iterrows():
        ts = pd.Timestamp(row[anchor_col])
        if pd.isna(ts) or ts.year < 1990:
            rows_skipped += 1
            continue
        quote = None
        if "bid" in row and "ask" in row and pd.notna(row["bid"]) and pd.notna(row["ask"]):
            quote = (float(row["bid"]), float(row["ask"]))

        rec = reconstruct_features(ts, data, cfg, quote=quote, machine=machine,
                                   breakout=breakout, prev_trend_state=prev_trend)
        if not rec.causal_ok:
            rows_skipped += 1
            notes.append(f"{ts}: {rec.reason}") if len(notes) < 20 else None
            continue
        if 20 in rec.values:
            prev_trend = int(rec.values[20])
        rows_compared += 1

        for spec in FEATURE_SPECS:
            col = f"f{spec.index:02d}"
            stat = per_feature[spec.name]
            if spec.index in exempt_now:
                continue
            if spec.index not in rec.values:
                continue
            mql_v = float(row[col]) if pd.notna(row[col]) else float("nan")
            py_v = float(rec.values[spec.index])
            stat["compared"] += 1

            if spec.kind is FeatureKind.CATEGORICAL:
                ok = bool(np.isfinite(mql_v) and np.isfinite(py_v)
                          and round(mql_v) == round(py_v))
                abs_d = abs(mql_v - py_v) if np.isfinite(mql_v) and np.isfinite(py_v) else float("inf")
                rel_d = 0.0 if ok else 1.0
                tol = "exact"
            else:
                ok, abs_d, rel_d = within_tolerance(mql_v, py_v, cfg.rel_tol, cfg.abs_tol,
                                                    cfg.journal_decimals)
                tol = (f"rel<={cfg.rel_tol:g} or abs<={cfg.abs_tol:g}"
                       + (f" or journal({cfg.journal_decimals}dp,f32)" if cfg.journal_decimals is not None else ""))

            stat["max_abs"] = max(stat["max_abs"], abs_d if np.isfinite(abs_d) else stat["max_abs"])
            stat["max_rel"] = max(stat["max_rel"], rel_d if np.isfinite(rel_d) else stat["max_rel"])
            if not ok:
                sym = str(row.get("symbol", ""))
                tie = ties.get((sym, ts, spec.name))
                accept = tie is not None and tie.matches(mql_v, py_v)
                if tie is not None:
                    ties_seen.add(tie.key())
                    if not accept:
                        notes.append(f"{ts} {sym} {spec.name}: listed tie does not match "
                                     f"(mql5={mql_v!r} py={py_v!r}) -- counted as FAIL")
                rec_m = Mismatch(
                    row_id=str(row.get("row_id", "")),
                    symbol=sym,
                    timeframe=str(row.get("timeframe", "")),
                    decision_ts=str(ts),
                    feature_index=spec.index, feature_name=spec.name,
                    kind=spec.kind.value,
                    mql5_value=mql_v, python_value=py_v,
                    abs_diff=abs_d, rel_diff=rel_d, tolerance=tol,
                    status=("ACCEPTED_TIE: " + tie.cause) if accept else "FAIL")
                if accept:
                    stat["accepted_ties"] = stat.get("accepted_ties", 0) + 1
                    accepted.append(rec_m)
                else:
                    stat["mismatches"] += 1
                    mismatches.append(rec_m)

    for spec in FEATURE_SPECS:
        stat = per_feature[spec.name]
        if spec.index in exempt_now:
            stat["status"] = ParityStatus.EXEMPT.value
        elif stat["compared"] == 0:
            stat["status"] = ParityStatus.NOT_RECONSTRUCTED.value
        else:
            stat["status"] = (ParityStatus.PASS.value if stat["mismatches"] == 0
                              else ParityStatus.FAIL.value)

    exempt_names = [s.name for s in FEATURE_SPECS if s.index in exempt_now]
    never_reconstructed = [s.name for s in FEATURE_SPECS
                           if s.index not in exempt_now
                           and per_feature[s.name]["compared"] == 0]
    if never_reconstructed:
        notes.append(
            "features never reconstructed (no usable row or missing history): "
             + ", ".join(never_reconstructed)
             + " -- these are NOT passes")

    run_symbols = set(work["symbol"].astype(str)) if "symbol" in work.columns else set()
    unused = [t for t in cfg.accepted_ties if t.symbol in run_symbols and t.key() not in ties_seen
              and work[anchor_col].min() <= t.key()[1] <= work[anchor_col].max()]
    for t in unused[:20]:
        notes.append(f"listed tie not observed in this run: {t.symbol} {t.decision_ts} {t.feature_name}")

    status = ParityStatus.PASS
    if mismatches or rows_compared == 0 or never_reconstructed:
        status = ParityStatus.FAIL
    if rows_compared == 0:
        notes.append("no row could be causally reconstructed; parity cannot be established")

    stats = {
        "rows_compared": rows_compared,
        "rows_skipped": rows_skipped,
        "features_compared": FEATURE_COUNT - len(exempt_now) - len(never_reconstructed),
        "features_exempt": len(exempt_now),
        "exempt_names": exempt_names,
        "rel_tol": cfg.rel_tol,
        "abs_tol": cfg.abs_tol,
        "journal_decimals": cfg.journal_decimals,
        "ties_listed": len(cfg.accepted_ties),
        "ties_accepted": len(accepted),
        "ties_unused_in_range": len(unused),
    }
    return ParityResult(status, mismatches, per_feature, stats, notes, accepted)


class ParityGateError(RuntimeError):
    """Raised when parity fails. Downstream training must not proceed."""


def assert_parity_or_halt(result: ParityResult) -> None:
    """
    Fail-closed gate. Call this before any training or promotion step.

    Raising rather than returning a flag is deliberate: a caller that forgets to
    check a boolean proceeds silently on a failed oracle, which is the exact
    outcome this stage exists to prevent.
    """
    if result.status is not ParityStatus.PASS:
        raise ParityGateError(
            "PARITY FAILED -- model training and promotion are not valid.\n"
            + result.report())


def sole_basis_guard(feature_indices) -> None:
    """
    Refuse a feature set made only of parity-exempt features.

    Exempt features are unverifiable offline. A model resting solely on them
    could never have its inputs checked against the live engine, so it must not
    reach promotion however good its backtest looks.
    """
    idx = {int(i) for i in feature_indices}
    if idx and idx.issubset(set(EXEMPT_INDICES)):
        names = [s.name for s in FEATURE_SPECS if s.index in idx]
        raise ParityGateError(
            "feature set consists only of parity-exempt features "
            f"({names}); these cannot be verified against the live engine and "
            "must never be the sole basis for promotion")


def load_market_data(paths: dict, point: float = 1e-5, basket_paths: dict | None = None) -> MarketData:
    """Load OHLC CSVs per timeframe: {'M1': 'm1.csv', 'D1': 'd1.csv', ...}; optionally the basket
    symbols' entry-timeframe bars {'EURUSD': 'eurusd_m1.csv', ...} for f29."""
    basket = {}
    for sym, path in (basket_paths or {}).items():
        b = pd.read_csv(path)
        b["time"] = pd.to_datetime(b["time"])
        basket[sym] = b[["time", "close"]].sort_values("time").reset_index(drop=True)
    bars = {}
    for tf, path in paths.items():
        df = pd.read_csv(path)
        cols = {c.lower(): c for c in df.columns}
        df = df.rename(columns={cols.get("time", "time"): "time"})
        df["time"] = pd.to_datetime(df["time"])
        for c in ("open", "high", "low", "close"):
            if c in cols:
                df[c] = pd.to_numeric(df[cols[c]], errors="coerce")
        bars[tf] = df[["time", "open", "high", "low", "close"]].sort_values("time").reset_index(drop=True)
    return MarketData(bars=bars, point=point, basket=basket)


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(
        description="NEXA parity oracle: independent reconstruction vs MQL5 f00..f47.")
    ap.add_argument("canonical", help="Stage 2 canonical dataset (.csv/.parquet)")
    ap.add_argument("--m1", required=True, help="M1 OHLC csv")
    ap.add_argument("--m5"); ap.add_argument("--m15"); ap.add_argument("--h1")
    ap.add_argument("--d1", required=True, help="D1 OHLC csv (broker's own daily bars)")
    ap.add_argument("--point", type=float, default=1e-5)
    ap.add_argument("--gmt-offset", type=int, default=2, help="standard-time (US winter) server offset")
    ap.add_argument("--fixed-gmt-offset", action="store_true", help="disable the US-DST hour (pre-D-TZ clock)")
    ap.add_argument("--mql5-source", help="NEXA_Intelligence.mqh, to verify feature ORDER")
    ap.add_argument("--rel-tol", type=float, default=DEFAULT_REL_TOL)
    ap.add_argument("--abs-tol", type=float, default=DEFAULT_ABS_TOL)
    ap.add_argument("--journal-decimals", type=int, default=DEFAULT_JOURNAL_DECIMALS)
    ap.add_argument("--accepted-ties", help="reviewed tie register (parity_accepted_ties.json)")
    ap.add_argument("--out", help="write mismatch table here")
    args = ap.parse_args(argv)

    frame = (pd.read_parquet(args.canonical) if args.canonical.endswith(".parquet")
             else pd.read_csv(args.canonical))
    for c in ("decision_ts", "decision_ts_effective"):
        if c in frame.columns:
            frame[c] = pd.to_datetime(frame[c], errors="coerce")

    paths = {"M1": args.m1, "D1": args.d1}
    for tf, p in (("M5", args.m5), ("M15", args.m15), ("H1", args.h1)):
        if p:
            paths[tf] = p
    data = load_market_data(paths, point=args.point)

    cfg = ParityConfig(gmt_offset=args.gmt_offset, server_follows_us_dst=not args.fixed_gmt_offset,
                       rel_tol=args.rel_tol, abs_tol=args.abs_tol,
                       journal_decimals=args.journal_decimals,
                       accepted_ties=load_accepted_ties(args.accepted_ties) if args.accepted_ties else ())
    result = run_parity(frame, data, cfg, mql5_source=args.mql5_source)
    print(result.report())
    if args.out and result.mismatches:
        result.mismatch_frame().to_csv(args.out, index=False)
        print(f"\nmismatch table: {args.out}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
