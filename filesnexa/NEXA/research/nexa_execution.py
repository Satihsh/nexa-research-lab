"""NEXA research execution & fill simulator. Deterministic; no RNG anywhere.

One order -> one trade record. Two data modes with ONE set of rules:

  TICK mode : quotes (time, bid, ask). Everything happens at the first quote whose time
              is >= the moment the action becomes possible (signal time + latency).
  BAR mode  : BID OHLC bars (time = bar OPEN, broker server or UTC - caller's choice) with a
              per-bar spread in POINTS. Intrabar order is unknown, so the rules are
              conservative and explicit:
                * an action decided on bar i's close executes at bar i+1's OPEN
                  (latency < 1 bar is assumed and asserted);
                * when one bar reaches both the stop and the target, the STOP wins;
                * a bar that GAPS through a level fills at the bar's open, not the level.

Fill rules (both modes)
  MARKET  buy at ask + slip, sell at bid - slip.
  LIMIT   buy fills only when ask <= limit - through*point (a TOUCH IS NOT A FILL);
          fill price = min(limit, ask) (price improvement on a gap, never worse than limit).
          Sell mirrors on bid. No slippage on the limit fill itself.
  STOP-ENTRY buy triggers when ask >= level; fills at max(level, ask) + slip.
  STOP-LOSS  long closes when bid <= sl at min(sl, bid) - slip; short when ask >= sl at max(sl, ask) + slip.
  TAKE-PROFIT is a resting limit: long exits when bid >= tp + through*point at max(tp, bid).
  TIME EXIT  market close at the first quote/bar open >= exit time; with max_hold, the exit
             time is min(exit_time, entry_time + max_hold).
  CANCEL     a pending LIMIT/STOP is cancelled (status CANCELLED_INVALIDATED) at the first bar/quote
             that CLOSES beyond cancel_level (long: close < level, short: close > level) before a fill.
  SAME-BAR   (bar mode) after an INTRABAR fill (LIMIT/STOP) the path inside the fill bar is unknown:
             the stop is still checked on that bar (conservative) but the TARGET is not, and the
             fill bar's favourable excursion is not counted in MFE. A MARKET fill at the bar open
             owns the whole bar, so its fill bar is checked normally.

Costs (reported separately and in R)
  spread_cost      : half-spread paid at entry and at exit relative to the bid/ask mid, in price
  commission       : commission_per_lot_side (account ccy) x 2, converted to quote-currency price
                     units per unit of base: account_to_quote(price) / contract_size
  slippage         : slip_points*point + slip_spread_frac*spread, adverse, on market/stop fills
R = direction x (exit - entry) - commission, divided by the INITIAL stop distance from the
ACTUAL entry (entry - sl for longs).
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Instrument:
    symbol: str
    point: float
    contract_size: float
    account_is_quote: bool = True        # EURUSD, XAUUSD (USD account): commission already in quote ccy
    account_is_base: bool = False        # USDJPY: quote(JPY) per account(USD) = price

    def commission_price(self, commission_account: float, price: float) -> float:
        """Commission (account ccy, whole order) -> quote-currency price units per 1 unit of base."""
        if self.account_is_quote:
            q = commission_account
        elif self.account_is_base:
            q = commission_account * price
        else:
            raise ValueError("cross-currency account conversion needs an explicit rate; not supported")
        return q / self.contract_size


@dataclass(frozen=True)
class ExecConfig:
    latency_ms: int = 250
    commission_per_lot_side: float = 3.50
    slip_points: float = 0.0
    slip_spread_frac: float = 0.5
    through_points: float = 1.0
    bar_seconds: int = 60


@dataclass(frozen=True)
class Order:
    signal_time: pd.Timestamp        # when the decision was made (tick time, or bar CLOSE in bar mode)
    direction: int                   # +1 long, -1 short
    kind: str                        # MARKET | LIMIT | STOP
    sl: float                        # absolute price
    tp: float | None = None          # absolute price or None
    level: float | None = None       # LIMIT/STOP entry price
    expiry: pd.Timestamp | None = None
    exit_time: pd.Timestamp | None = None
    tag: str = ""
    max_hold: pd.Timedelta | None = None     # time exit at entry_time + max_hold (min with exit_time)
    cancel_level: float | None = None        # pending order cancelled when a close is beyond this level


@dataclass
class TradeRecord:
    tag: str
    status: str                      # FILLED_CLOSED | EXPIRED | CANCELLED_INVALID | OPEN_AT_END
    direction: int
    signal_time: object
    entry_time: object = None
    entry: float = float("nan")
    exit_time: object = None
    exit: float = float("nan")
    exit_reason: str = ""
    sl: float = float("nan")
    tp: float = float("nan")
    risk: float = float("nan")
    r_gross: float = float("nan")
    r_net: float = float("nan")
    commission_price: float = 0.0
    spread_cost_price: float = 0.0
    slippage_price: float = 0.0
    mfe_r: float = float("nan")
    mae_r: float = float("nan")
    ambiguous_bar: bool = False
    latency_ms: int = 0

    def as_dict(self) -> dict:
        return asdict(self)


def _slip(cfg: ExecConfig, inst: Instrument, spread_price: float) -> float:
    return cfg.slip_points * inst.point + cfg.slip_spread_frac * spread_price


# ---------------------------------------------------------------- quote stream abstraction

class _Quotes:
    """Uniform access to 'events' (tick quotes or bars) as arrays."""

    def __init__(self, t, bid_open, ask_open, bid_hi=None, bid_lo=None, spread=None, is_bars=False,
                 bid_close=None):
        self.t = np.asarray(pd.to_datetime(t).values)
        self.bo = np.asarray(bid_open, float)
        self.ao = np.asarray(ask_open, float)
        self.bh = self.bo if bid_hi is None else np.asarray(bid_hi, float)
        self.bl = self.bo if bid_lo is None else np.asarray(bid_lo, float)
        self.sp = self.ao - self.bo if spread is None else np.asarray(spread, float)
        self.is_bars = is_bars
        self.cl = None if bid_close is None else np.asarray(bid_close, float)

    def ask_hi(self, i):
        return self.bh[i] + self.sp[i]

    def ask_lo(self, i):
        return self.bl[i] + self.sp[i]

    def first_at_or_after(self, when) -> int:
        return int(np.searchsorted(self.t, np.datetime64(pd.Timestamp(when).to_datetime64()), side="left"))


def quotes_from_ticks(ticks: pd.DataFrame) -> _Quotes:
    """ticks: columns time (datetime-like, ascending), bid, ask."""
    return _Quotes(ticks["time"], ticks["bid"], ticks["ask"], bid_close=ticks["bid"])


def quotes_from_bars(bars: pd.DataFrame, point: float) -> _Quotes:
    """bars: time (OPEN time), open, high, low, close (BID), spread (points)."""
    sp = bars["spread"].to_numpy(float) * point
    return _Quotes(bars["time"], bars["open"], bars["open"].to_numpy(float) + sp,
                   bars["high"], bars["low"], sp, is_bars=True, bid_close=bars["close"])


# ---------------------------------------------------------------- engine

def simulate_order(q: _Quotes, order: Order, inst: Instrument, cfg: ExecConfig,
                   end_index: int | None = None) -> TradeRecord:
    d = order.direction
    if d not in (1, -1):
        raise ValueError("direction must be +1 or -1")
    rec = TradeRecord(order.tag, "EXPIRED", d, order.signal_time, sl=order.sl,
                      tp=order.tp if order.tp is not None else float("nan"), latency_ms=cfg.latency_ms)
    n = len(q.t) if end_index is None else end_index
    if q.is_bars:
        if cfg.latency_ms >= cfg.bar_seconds * 1000:
            raise ValueError("bar mode assumes latency < one bar")
        start = q.first_at_or_after(pd.Timestamp(order.signal_time))      # the next bar OPEN
    else:
        start = q.first_at_or_after(pd.Timestamp(order.signal_time) + pd.Timedelta(milliseconds=cfg.latency_ms))
    exp_i = n if order.expiry is None else min(n, q.first_at_or_after(order.expiry))

    # ---- entry
    entry_i, entry, slip_in = None, float("nan"), 0.0
    for i in range(start, exp_i):
        ask_o, bid_o, sp = q.ao[i], q.bo[i], q.sp[i]
        if order.kind == "MARKET":
            s = _slip(cfg, inst, sp)
            entry, slip_in = (ask_o + s, s) if d > 0 else (bid_o - s, s)
            entry_i = i
            break
        if order.kind == "LIMIT":
            thr = cfg.through_points * inst.point
            if d > 0 and q.ask_lo(i) <= order.level - thr:
                entry, entry_i = min(order.level, ask_o), i
                break
            if d < 0 and q.bh[i] >= order.level + thr:
                entry, entry_i = max(order.level, bid_o), i
                break
        elif order.kind == "STOP":
            s = _slip(cfg, inst, sp)
            if d > 0 and q.ask_hi(i) >= order.level:
                entry, entry_i, slip_in = max(order.level, ask_o) + s, i, s
                break
            if d < 0 and q.bl[i] <= order.level:
                entry, entry_i, slip_in = min(order.level, bid_o) - s, i, s
                break
        else:
            raise ValueError(f"unknown order kind {order.kind}")
        if order.cancel_level is not None and q.cl is not None and (
                (d > 0 and q.cl[i] < order.cancel_level) or (d < 0 and q.cl[i] > order.cancel_level)):
            rec.status = "CANCELLED_INVALIDATED"
            return rec
    if entry_i is None:
        return rec
    risk = (entry - order.sl) * d
    if not np.isfinite(risk) or risk <= 0:
        rec.status = "CANCELLED_INVALID"
        rec.entry, rec.entry_time = entry, q.t[entry_i]
        return rec
    rec.entry, rec.entry_time, rec.risk = entry, q.t[entry_i], risk
    comm = inst.commission_price(cfg.commission_per_lot_side * 2, entry)
    spread_cost = q.sp[entry_i] / 2

    # ---- exits: from the entry event itself (bars: the whole entry bar is after the fill
    # only for MARKET fills at the open; limit/stop fills intrabar -> the rest of that bar
    # is checked too, conservatively)
    tp = order.tp
    thr = cfg.through_points * inst.point
    exit_i = n - 1
    exit_px, reason, slip_out, amb = float("nan"), "", 0.0, False
    exit_when = order.exit_time
    if order.max_hold is not None:
        hold_end = pd.Timestamp(q.t[entry_i]) + pd.Timedelta(order.max_hold)
        exit_when = hold_end if exit_when is None else min(pd.Timestamp(exit_when), hold_end)
    exit_t_i = n if exit_when is None else q.first_at_or_after(exit_when)
    intrabar_fill = q.is_bars and order.kind in ("LIMIT", "STOP")
    mfe = mae = 0.0
    for i in range(entry_i, n):
        if i >= exit_t_i and i > entry_i:
            s = _slip(cfg, inst, q.sp[i])
            exit_px = q.bo[i] - s if d > 0 else q.ao[i] + s
            exit_i, reason, slip_out = i, "TIME_EXIT", s
            break
        if d > 0:
            fav, adv = q.bh[i] - entry, entry - q.bl[i]
            hit_sl = q.bl[i] <= order.sl
            hit_tp = tp is not None and q.bh[i] >= tp + thr
        else:
            fav, adv = entry - q.ask_lo(i), q.ask_hi(i) - entry
            hit_sl = q.ask_hi(i) >= order.sl
            hit_tp = tp is not None and q.ask_lo(i) <= tp - thr
        if intrabar_fill and i == entry_i:
            fav, hit_tp = 0.0, False          # path inside the fill bar is unknown: no target, no MFE
        mfe, mae = max(mfe, fav), max(mae, adv)
        if hit_sl:
            s = _slip(cfg, inst, q.sp[i])
            amb = bool(hit_tp)
            exit_px = (min(order.sl, q.bo[i]) - s) if d > 0 else (max(order.sl, q.ao[i]) + s)
            exit_i, reason, slip_out = i, "SL", s
            break
        if hit_tp:
            exit_px = max(tp, q.bo[i]) if d > 0 else min(tp, q.ao[i])
            exit_i, reason = i, "TP"
            break
    else:
        rec.status = "OPEN_AT_END"
        s = _slip(cfg, inst, q.sp[n - 1])
        exit_px = q.bo[n - 1] - s if d > 0 else q.ao[n - 1] + s
        reason, slip_out = "END_OF_DATA", s
    gross = d * (exit_px - entry)
    rec.status = rec.status if rec.status == "OPEN_AT_END" else "FILLED_CLOSED"
    rec.exit, rec.exit_time, rec.exit_reason, rec.ambiguous_bar = exit_px, q.t[exit_i], reason, amb
    rec.r_gross = (gross + slip_in + slip_out) / risk
    rec.r_net = (gross - comm) / risk
    rec.commission_price, rec.spread_cost_price = comm, spread_cost + q.sp[exit_i] / 2
    rec.slippage_price = slip_in + slip_out
    rec.mfe_r, rec.mae_r = mfe / risk, mae / risk
    return rec


def run_one_at_a_time(q: _Quotes, orders: list[Order], inst: Instrument, cfg: ExecConfig) -> pd.DataFrame:
    """Simulate orders in signal-time order, skipping any whose signal arrives while a
    previous trade is still open (one position per strategy)."""
    busy_until = None
    rows = []
    for o in sorted(orders, key=lambda x: pd.Timestamp(x.signal_time)):
        if busy_until is not None and pd.Timestamp(o.signal_time) <= pd.Timestamp(busy_until):
            rows.append(TradeRecord(o.tag, "SKIPPED_POSITION_OPEN", o.direction, o.signal_time).as_dict())
            continue
        r = simulate_order(q, o, inst, cfg)
        if r.status in ("FILLED_CLOSED", "OPEN_AT_END"):
            busy_until = r.exit_time
        rows.append(r.as_dict())
    return pd.DataFrame(rows)


def fill_summary(trades: pd.DataFrame) -> dict:
    """Fill probability and E[R] over ALL placed orders (unfilled = 0R), so a high
    filled-trade win rate cannot hide a low fill rate."""
    placed = trades[~trades["status"].eq("SKIPPED_POSITION_OPEN")]
    filled = placed[placed["status"].isin(["FILLED_CLOSED", "OPEN_AT_END"])]
    return {"placed": len(placed), "filled": len(filled),
            "fill_probability": len(filled) / len(placed) if len(placed) else float("nan"),
            "expectancy_filled_r": float(filled["r_net"].mean()) if len(filled) else float("nan"),
            "expectancy_per_order_r": float(filled["r_net"].sum() / len(placed)) if len(placed) else float("nan")}


AccountToQuote = Callable[[float], float]
