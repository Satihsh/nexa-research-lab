"""CAP-NEUTRAL RESEARCH — NOT PRODUCTION CONFIGURATION.

A4 analysis of the 48 verified cap-neutral tester runs, exactly as pre-registered in
research/capneutral/CAPNEUTRAL_RESEARCH_PLAN.md (amendments 1-2, recorded before results).

    python research/capneutral/capn_analysis.py            # writes research/capneutral/results/

Read-only with respect to every input: Trade DNA, run folders, bar exports, the EA, the
risk file and both registries are only read. Nothing here fits, tunes or selects.

Definitions (plan §7A, amendment 1):
  realised_pnl_usd = sum over exit legs of dir * (exit - actual fill) * lots * contract value
                     + CLOSE commission + CLOSE swap        (CLOSE carries the full round trip)
  initial_risk_usd = OPEN lots * risk_dist * contract value (USDJPY at the intended entry)
  net_R            = realised_pnl_usd / initial_risk_usd     (the only R that reaches Gate 8)
  gross_R          = DNA result_r: price-only, from the INTENDED entry (excludes entry
                     slippage, commission and swap) -- reported, never used for a verdict.
"""
from __future__ import annotations

import csv
import glob
import hashlib
import json
import math
import os
import re
import sys

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = os.path.dirname(HERE)
ROOT = os.path.dirname(RESEARCH)
if RESEARCH not in sys.path:
    sys.path.insert(0, RESEARCH)

import nexa_8e_capital as CV
import nexa_8e_costs as C
import nexa_robust as RB
import nexa_stats as NS
import nexa_time

LABEL = "CAP-NEUTRAL RESEARCH — NOT PRODUCTION CONFIGURATION"
RUNS = os.path.join(ROOT, "research", "tester_runs_capneutral")
DNA_DIR = os.path.join(ROOT, "data", "pepperstone", "tester_capneutral")
BARS_DIR = os.path.join(ROOT, "data", "pepperstone", "tester")
OUT = os.path.join(HERE, "results")
TS = "%Y.%m.%d %H:%M:%S"

SYMBOLS = ("GBPUSD", "EURUSD", "USDJPY", "XAUUSD")
WINDOWS = {  # window -> (from, to) exactly as the batch ran them (to is exclusive)
    "A2024Q1": ("2024.01.01", "2024.04.01"), "A2024Q2": ("2024.04.01", "2024.07.01"),
    "A2024Q3": ("2024.07.01", "2024.10.01"), "A2024Q4": ("2024.10.01", "2025.01.01"),
    "A2025Q1": ("2025.01.01", "2025.04.01"), "A2025Q2": ("2025.04.01", "2025.07.01"),
    "A2025Q3": ("2025.07.01", "2025.10.01"), "A2025Q4": ("2025.10.01", "2026.01.01"),
    "A2026Q1": ("2026.01.01", "2026.04.01"), "A2026Q2": ("2026.04.01", "2026.07.01"),
    "A2026Q3": ("2026.07.01", "2026.08.28"), "B": ("2026.08.28", "2026.09.26"),
}
START_BALANCE = 50_000.0
RISK, CEILING, MAX_TRADES, DAILY_LOSS, MAX_DD = 0.003, 0.01, 10, 0.02, 0.10
MAX_TP_R, SPEC_BEST_R = 4.0, 0.5 * 1.5 + 0.5 * 4.0        # implemented vs intended best exit
TARGET, CYCLE_DAYS = 0.245, 20
GATE8 = NS.StatsConfig(min_trades=200, block=10)            # pre-registered primary
GATE8_IID = NS.StatsConfig(min_trades=200, block=1)         # pre-registered secondary
BH_Q = 0.10                                                 # library default (amendment 2)
EXIT_TOL_R = 0.05                                           # exit classification tolerance
BE_R, PARTIAL_R, TIME_EXIT_BARS, TIME_EXIT_R = 1.0, 1.5, 48, 0.3
VAR_SR_8E = 0.022528317280615343   # 8E VAL Sharpe variance (exploratory DSR sensitivity only)

# frozen / production identities checked by integrity()
PINNED = {
    "NEXA_Risk.mqh": "7fd5692a2bd3aec7443185f914be320158cfe55bcddcf370db059a6da0d908d1",
    "NEXA_EA.mq5": "d65090cca1654814b1be6e6b50cb6c2570c2ba4a3a9c7790bae5ba7121716c62",
    "build/NEXA_EA.ex5": "91ee5e20b0a21b75d72b169bfc1f7d079dd6542c7239bc280e05c6724609e5fb",
}
REGISTRY_HEADS = {  # (dir, seq, entry_sha256) recorded off-machine 2026-10-02
    "registry_v2": (6, "bbd9a28ed6bc7e0b20f3fca9f9ba1fe437f4bd39dc9c1e99ed73fb7505be5b2b"),
    "registry_8e": (2170, "9f7249a235b41c2452703c2e7baf3b2617cb1fe32b2a66e5d8655067e505d575"),
}


# ----------------------------------------------------------------- arithmetic
def daily_ceiling(risk: float, best_r: float, max_trades: int) -> float:
    """Largest possible one-day return before costs: every trade a best-exit win, each sized
    on current equity (compounding), at most max_trades trades."""
    return (1.0 + risk * best_r) ** max_trades - 1.0


def wins_needed(target: float, risk: float, best_r: float) -> float:
    return math.log(1.0 + target) / math.log(1.0 + risk * best_r)


def contract_value(symbol: str, price: float) -> float:
    """USD value of a 1.0 price move on 1.0 lot."""
    if symbol in ("EURUSD", "GBPUSD"):
        return 100_000.0
    if symbol == "XAUUSD":
        return 100.0
    if symbol == "USDJPY":
        return 100_000.0 / price
    raise ValueError(f"unsupported symbol {symbol}")


def clopper_pearson_upper(k: int, n: int, conf: float = 0.95) -> float:
    """One-sided upper confidence bound for a binomial proportion."""
    if n <= 0:
        return float("nan")
    return 1.0 if k >= n else float(stats.beta.ppf(conf, k + 1, n - k))


# ----------------------------------------------------------------- Trade DNA
def read_events(path: str) -> tuple[list[dict], int, int]:
    """Non-DECISION rows (file order), number of DECISION rows, and DECISION rows that carry
    the exposure-cap reason. Streams the file; never loads the decisions into memory.
    Also notes the EA's survival pause (first SURVIVAL_PAUSED decision, opens after it) in
    read_events.last_pause for the calling run."""
    rows, n_dec, n_cap = [], 0, 0
    pause = {"first_pause": None, "paused_decisions": 0, "opens_after_first_pause": 0}
    with open(path, newline="") as fh:
        rd = csv.reader(fh)
        header = next(rd)
        ev_i = header.index("event")
        for rec in rd:
            if len(rec) > ev_i and rec[ev_i] == "DECISION":
                n_dec += 1
                if rec[-1].endswith("PORTFOLIO_CURRENCY_EXPOSURE_CAP"):
                    n_cap += 1
                if "SURVIVAL_PAUSED" in rec[-1]:
                    pause["paused_decisions"] += 1
                    if pause["first_pause"] is None:
                        pause["first_pause"] = rec[header.index("decision_ts")]
                continue
            if rec[ev_i] == "OPEN" and pause["first_pause"] is not None:
                pause["opens_after_first_pause"] += 1
            rows.append(dict(zip(header, rec)))
    read_events.last_pause = pause
    return rows, n_dec, n_cap


def _f(row: dict, k: str) -> float:
    return float(row[k])


def pair_trades(rows: list[dict], symbol: str, window: str) -> pd.DataFrame:
    """Pair OPEN -> FILL -> (PARTIAL_CLOSE ...) -> CLOSE rows into trades.

    Positions can briefly overlap (a new order is dispatched while the previous position is
    still open; observed in the campaign), so rows are matched by EXACT volume and direction:
    a FILL attaches to the earliest unfilled OPEN with the same lots and direction, a CLOSE to
    the filled open trade with the same lots and direction. A PARTIAL_CLOSE attaches only when
    exactly one filled trade of that direction is open. Any ambiguity, orphan or leftover
    raises: rows are never guessed onto a trade."""
    def same(a: dict, b: dict) -> bool:
        return abs(_f(a, "lots") - _f(b, "lots")) < 1e-9 and _f(a, "direction") == _f(b, "direction")

    pending, live, done, overlaps = [], [], [], 0
    for r in rows:
        ev = r["event"]
        if ev == "OPEN":
            if live or pending:
                overlaps += 1
            pending.append({"open": r, "fill": None, "legs": [], "order": len(done) + len(live) + len(pending)})
        elif ev == "FILL":
            m = [t for t in pending if same(t["open"], r)]
            if not m:
                raise ValueError(f"{symbol} {window}: FILL without a matching OPEN")
            m[0]["fill"] = r
            pending.remove(m[0])
            live.append(m[0])
        elif ev in ("PARTIAL_CLOSE", "CLOSE"):
            if ev == "CLOSE":
                m = [t for t in live if not t["legs"] and same(t["open"], r)] or \
                    [t for t in live if t["legs"] and _f(r, "direction") == _f(t["open"], "direction")]
            else:
                m = [t for t in live if _f(r, "direction") == _f(t["open"], "direction")]
            if not m:
                raise ValueError(f"{symbol} {window}: {ev} without OPEN+FILL")
            if len(m) > 1:
                raise ValueError(f"{symbol} {window}: ambiguous {ev} ({len(m)} candidate trades)")
            m[0]["legs"].append(r)
            if ev == "CLOSE":
                live.remove(m[0])
                done.append(m[0])
        else:
            raise ValueError(f"{symbol} {window}: unknown event {ev}")
    if pending or live:
        raise ValueError(f"{symbol} {window}: trade left open at end of file")
    done.sort(key=lambda t: t["order"])
    out = pd.DataFrame([_trade_record(t, symbol, window, k) for k, t in enumerate(done)])
    out.attrs["overlapping_opens"] = overlaps
    return out


def _trade_record(t: dict, symbol: str, window: str, idx: int) -> dict:
    o, f, legs = t["open"], t["fill"], t["legs"]
    close = legs[-1]
    d = _f(o, "direction")
    intended, fill = _f(o, "entry_intended"), _f(f, "entry_actual")
    risk_dist, lots = _f(o, "risk_dist"), _f(o, "lots")
    if abs(_f(f, "lots") - lots) > 1e-9 or abs(sum(_f(x, "lots") for x in legs) - lots) > 1e-6:
        raise ValueError(f"{symbol} {window} trade {idx}: OPEN/FILL/exit-leg volumes differ")
    price_pnl = sum(d * (_f(x, "entry_actual") - fill) * _f(x, "lots") * contract_value(symbol, _f(x, "entry_actual"))
                    for x in legs)
    comm, swap = _f(close, "commission"), _f(close, "swap")
    risk_usd = lots * risk_dist * contract_value(symbol, intended)
    exit_px = _f(close, "entry_actual")
    sl, tp = _f(o, "sl_price"), _f(o, "tp_price")
    return {
        "symbol": symbol, "window": window, "trade": idx,
        "decision_time": pd.Timestamp(pd.to_datetime(o["decision_ts"], format=TS)),
        "entry_time": pd.Timestamp(pd.to_datetime(f["fill_ts"], format=TS)),
        "exit_time": pd.Timestamp(pd.to_datetime(close["fill_ts"], format=TS)),
        "direction": int(d), "entry_intended": intended, "fill": fill, "exit": exit_px,
        "sl": sl, "tp": tp, "target_r": _f(o, "target_r"), "risk_dist": risk_dist, "lots": lots,
        "spread_at_decision": _f(o, "spread"), "legs": len(legs),
        "commission_usd": comm, "swap_usd": swap, "fill_commission_usd": _f(f, "commission"),
        "price_pnl_usd": price_pnl, "realised_pnl_usd": price_pnl + comm + swap,
        "initial_risk_usd": risk_usd,
        "net_r": (price_pnl + comm + swap) / risk_usd,
        "gross_r": _f(close, "result_r"),
        "price_r_from_fill": price_pnl / risk_usd,
        "entry_slip_r": d * (intended - fill) / risk_dist,
        "commission_r": comm / risk_usd, "swap_r": swap / risk_usd,
        "spread_r_est": _f(o, "spread") / risk_dist,
        "exit_type": classify_exit(d, fill, exit_px, sl, tp, risk_dist),
    }


def classify_exit(d: float, fill: float, exit_px: float, sl: float, tp: float, risk_dist: float,
                  tol_r: float = EXIT_TOL_R) -> str:
    """By price only (the DNA records no exit reason): TP, SL, BREAKEVEN (stop moved to the
    actual open price), else OTHER (time exit, Friday close or tester chunk end)."""
    tol = tol_r * risk_dist
    if tp > 0 and d * (exit_px - tp) >= -tol:
        return "TP"
    if d * (exit_px - sl) <= tol:
        return "SL"
    if abs(exit_px - fill) <= tol:
        return "BREAKEVEN"
    return "OTHER"


# ----------------------------------------------------------------- run evidence
def read_text(path: str) -> str:
    with open(path, errors="replace") as fh:
        return fh.read()


def read_lines(path: str) -> list[str]:
    with open(path, errors="replace") as fh:
        return fh.readlines()


def run_window(run_dir: str) -> tuple[str, str]:
    t = read_text(os.path.join(run_dir, "RUN.txt"))
    return re.search(r"start=\S+ (\S+)", t).group(1), re.search(r"end=\S+ (\S+)", t).group(1)


def run_log_lines(run_dir: str):
    s, e = run_window(run_dir)
    for f in sorted(glob.glob(os.path.join(run_dir, "*.log"))):
        for ln in read_lines(f):
            p = ln.rstrip("\n").split("\t")
            if len(p) >= 4 and s <= p[2][:8] <= e:
                yield p[-1]


def tester_evidence(run_dir: str, symbol: str) -> dict:
    deals, finals, passed, inputs = {}, [], False, {}
    for msg in run_log_lines(run_dir):
        m = re.search(rf"deal #(\d+) (buy|sell) ([\d.]+) {symbol} at ([\d.]+) done", msg)
        if m:
            deals[int(m.group(1))] = (m.group(2), float(m.group(3)), float(m.group(4)))
        m = re.search(r"final balance ([\d.\-]+) USD", msg)
        if m:
            finals.append(float(m.group(1)))
        if "Test passed" in msg and f"{symbol}," in msg:
            passed = True
        m = re.match(r"^\s*(Inp\w+)=(.*)$", msg)
        if m:
            inputs[m.group(1)] = m.group(2).strip()
    return {"deals": deals, "final_balance": finals[0] if len(set(finals)) == 1 else None,
            "final_balance_lines": len(finals), "test_passed": passed, "inputs": inputs}


def rebuild_balance(symbol: str, deals: dict, close_costs: float, start: float = START_BALANCE) -> tuple[float, float]:
    """Average-cost netting of the tester's own deals + DNA CLOSE commission/swap."""
    pos = avg = pnl = 0.0
    for _, (side, vol, px) in sorted(deals.items()):
        sg = 1.0 if side == "buy" else -1.0
        if pos == 0 or (pos > 0) == (sg > 0):
            avg = (avg * abs(pos) + px * vol) / (abs(pos) + vol)
            pos += sg * vol
        else:
            q = min(vol, abs(pos))
            pnl += (px - avg) * q * (1 if pos > 0 else -1) * contract_value(symbol, px)
            pos += sg * q
            if abs(pos) < 1e-9:
                pos = avg = 0.0
            if vol - q > 1e-9:
                pos, avg = sg * (vol - q), px
    return start + pnl + close_costs, pos


def expected_inputs() -> dict:
    src = read_text(os.path.join(ROOT, "NEXA_EA.mq5"))
    exp = {}
    for f in ["NEXA_EA.mq5"] + re.findall(r'^#include "([^"]+)"', src, re.MULTILINE):
        txt = read_text(os.path.join(ROOT, f))
        for m in re.finditer(r"^\s*s?input\s+\w+\s+(\w+)\s*=\s*([^;]+);", txt, re.MULTILINE):
            exp[m.group(1)] = m.group(2).strip().strip('"')
    exp["InpMaxSameCurrencyNet"] = "10000"
    return exp


def _same(a: str, b: str) -> bool:
    try:
        return abs(float(a) - float(b)) < 1e-9
    except ValueError:
        return a.strip().lower() == b.strip().lower()


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ----------------------------------------------------------------- bars / defect
def load_bars(symbol: str, window: str) -> pd.DataFrame:
    b = pd.read_csv(os.path.join(BARS_DIR, f"PEPPERSTONE_{symbol}_M1_tester_{window}.csv"),
                    usecols=["time", "high", "low", "close"])
    b["time"] = pd.to_datetime(b["time"], format=TS)
    return b.set_index("time").sort_index()


def excursion(tr: pd.Series, bars: pd.DataFrame) -> dict:
    """Approximate path facts from BID M1 bars (generated-tick model): best favourable move in
    initial-risk units, bar index at which 1.0R was first touched, bars held, and r at the close
    of bar 48. Initial risk = |actual fill - initial stop| (what the EA's r uses before BE)."""
    seg = bars.loc[tr.entry_time.floor("min"): tr.exit_time.floor("min")]
    risk = abs(tr.fill - tr.sl)
    if seg.empty or risk <= 0:
        return {"mfe_r": float("nan"), "be_bar": -1, "bars_held": 0, "r_at_48": float("nan")}
    fav = (seg["high"] - tr.fill) if tr.direction > 0 else (tr.fill - seg["low"])
    fav_r = (fav / risk).to_numpy()
    hit = np.nonzero(fav_r >= BE_R)[0]
    r48 = float("nan")
    if len(seg) > TIME_EXIT_BARS:
        c = seg["close"].iloc[TIME_EXIT_BARS]
        r48 = float(((c - tr.fill) if tr.direction > 0 else (tr.fill - c)) / risk)
    return {"mfe_r": float(np.nanmax(fav_r)), "be_bar": int(hit[0]) if hit.size else -1,
            "bars_held": len(seg), "r_at_48": r48}


def defect_impact(tr: pd.DataFrame) -> dict:
    """Counts from existing records + an arithmetic magnitude bound (INFERENCE, not evidence)."""
    reached_be = tr["mfe_r"] >= BE_R
    reached_15 = tr["mfe_r"] >= PARTIAL_R
    blocked_time = reached_be & (tr["be_bar"] < TIME_EXIT_BARS) & (tr["bars_held"] > TIME_EXIT_BARS) & (tr["r_at_48"] < TIME_EXIT_R)
    # bound: half the position banked at +1.5R instead of the implemented exit of that half
    half_diff = np.where(reached_15, 0.5 * (PARTIAL_R - tr["price_r_from_fill"]), 0.0)
    return {
        "trades": len(tr), "bars_missing": int(tr["mfe_r"].isna().sum()),
        "reached_breakeven_1R": int(reached_be.sum()), "reached_1_5R": int(reached_15.sum()),
        "reached_1_5R_by_exit": tr.loc[reached_15, "exit_type"].value_counts().to_dict(),
        "breakeven_exits": int((tr["exit_type"] == "BREAKEVEN").sum()),
        "held_over_48_bars": int((tr["bars_held"] > TIME_EXIT_BARS).sum()),
        "time_exit_blocked_after_breakeven": int(blocked_time.sum()),
        "partial_close_rows": int((tr["legs"] > 1).sum()),
        "inference_partial_half_bound_r": {
            "sum_r": float(half_diff.sum()), "per_trade_r": float(half_diff.sum() / len(tr)) if len(tr) else float("nan"),
            "gain_r_on_be_or_other_exits": float(half_diff[half_diff > 0].sum()),
            "loss_r_on_tp_exits": float(half_diff[half_diff < 0].sum()),
            "note": ("INFERENCE: price-path arithmetic for the half that the specification would have closed at "
                     "+1.5R; ignores lot rounding, the time exit and any change in later decisions. Not campaign "
                     "evidence; no alternative EA was simulated or run."),
        },
    }


# ----------------------------------------------------------------- daily / capital
def trading_days(bars: pd.DataFrame) -> pd.DatetimeIndex:
    d = pd.DatetimeIndex(bars.index.normalize().unique())
    return d[d.weekday < 5]


def daily_returns(tr: pd.DataFrame, days: pd.DatetimeIndex, start: float = START_BALANCE) -> pd.DataFrame:
    """Realised closed balance by server day for one chunk (days without a trade = 0 %)."""
    if len(tr):
        pnl = tr.groupby(tr["exit_time"].dt.normalize())["realised_pnl_usd"].sum()
        n_open = tr.groupby(tr["entry_time"].dt.normalize()).size()
    else:
        pnl, n_open = pd.Series(dtype=float), pd.Series(dtype=int)
    alld = days.union(pd.DatetimeIndex(pnl.index)).sort_values()
    rows, bal = [], start
    for d in alld:
        p = float(pnl.get(d, 0.0))
        rows.append({"day": d, "start_balance": bal, "pnl": p, "ret": p / bal,
                     "trades_entered": int(n_open.get(d, 0))})
        bal += p
    df = pd.DataFrame(rows)
    peak = np.maximum.accumulate(np.r_[start, (df["start_balance"] + df["pnl"]).to_numpy()])[1:]
    df["drawdown"] = 1 - (df["start_balance"] + df["pnl"]) / peak
    return df


def cycles(daily: pd.DataFrame, n: int = CYCLE_DAYS) -> pd.DataFrame:
    rows = []
    for k in range(len(daily) // n):
        blk = daily.iloc[k * n:(k + 1) * n]
        rows.append({"cycle_start": blk["day"].iloc[0], "cycle_end": blk["day"].iloc[-1],
                     "return": float(np.prod(1 + blk["ret"].to_numpy()) - 1)})
    return pd.DataFrame(rows)


def dist(x) -> dict:
    a = np.asarray(x, float)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return {"n": 0}
    q = {f"q{int(p * 100):02d}": float(np.quantile(a, p)) for p in (0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99)}
    return {"n": int(a.size), "mean": float(a.mean()), "std": float(a.std(ddof=1)) if a.size > 1 else float("nan"),
            "min": float(a.min()), "max": float(a.max()),
            "skew": float(stats.skew(a, bias=False)) if a.size > 2 else float("nan"),
            "excess_kurtosis": float(stats.kurtosis(a, bias=False)) if a.size > 3 else float("nan"), **q}


def nexa_rule_replay(tr: pd.DataFrame, spec: C.SymbolSpec, start: float = 200.0, risk: float = RISK,
                     ceiling: float = CEILING, fractional: bool = False) -> dict:
    """Replay a symbol's tested trades on a small account with NEXA's own sizing
    (NEXA_Risk.mqh CalcLotSizeHardened): round DOWN to the step; below the minimum lot the
    minimum lot is used ONLY if its risk is within the 1 % hard ceiling, else NO TRADE; the
    drawdown throttle (x0.5 at 5 %, x0.25 at 7.5 %, stop at 10 %) only reduces; daily-loss halt
    at -2 % of the day's start; <= 10 trades per server day. fractional=True drops the lot grid
    (THEORETICAL compounding, not broker-executable). P/L = net_R x executed risk."""
    eq, peak = start, start
    taken = skip_min = skip_ceiling = skip_halt = skip_dd = 0
    for _, g in tr.sort_values("entry_time").groupby(tr["entry_time"].dt.normalize(), sort=True):
        day_start, n_day = eq, 0
        for _, t in g.iterrows():
            if (day_start - eq) / day_start >= DAILY_LOSS or n_day >= MAX_TRADES:
                skip_halt += 1
                continue
            dd = (peak - eq) / peak if peak > 0 else 1.0
            mult = 0.0 if dd >= MAX_DD else 0.25 if dd >= 0.75 * MAX_DD else 0.5 if dd >= 0.5 * MAX_DD else 1.0
            if mult == 0.0:
                skip_dd += 1
                continue
            risk_per_lot = t.initial_risk_usd / t.lots
            if fractional:
                lots = eq * risk / risk_per_lot * mult
            else:
                lots = C.round_down_to_step(eq * risk / risk_per_lot, spec.vstep)
                if lots < spec.vmin - 1e-12:
                    if spec.vmin * risk_per_lot / eq <= ceiling:
                        lots = spec.vmin
                    else:
                        skip_ceiling += 1
                        continue
                lots = min(lots, spec.vmax)
                lots = C.round_down_to_step(lots * mult, spec.vstep)
                if lots < spec.vmin - 1e-12:
                    skip_min += 1
                    continue
            eq += t.net_r * risk_per_lot * lots
            peak = max(peak, eq)
            taken += 1
            n_day += 1
    return {"start": start, "end": eq, "return": eq / start - 1, "trades_taken": taken,
            "skipped_min_lot_exceeds_ceiling": skip_ceiling, "skipped_below_min_after_throttle": skip_min,
            "skipped_daily_halt_or_cap": skip_halt, "skipped_drawdown_stop": skip_dd}


def load_symbol_specs() -> tuple[dict, dict]:
    """Broker volume grid per symbol. EURUSD/GBPUSD/XAUUSD from the pre-registered spec probe
    (nexa_8e_costs.load_specs); USDJPY, absent from that probe, from the broker's own contract
    export data/pepperstone/contracts.json. The USDJPY commission field (unused by the replays'
    P/L, which takes costs from net R) is the campaign's observed $7.00 per lot round trip."""
    specs, source = dict(C.load_specs()), {}
    for s in specs:
        source[s] = "spec_probe_20261001.csv"
    if "USDJPY" not in specs:
        with open(os.path.join(ROOT, "data", "pepperstone", "contracts.json")) as fh:
            j = json.load(fh)["USDJPY"]
        specs["USDJPY"] = C.SymbolSpec("USDJPY", j["point"], j["trade_tick_size"], j["trade_tick_value"],
                                       j["trade_contract_size"], j["volume_min"], j["volume_max"], j["volume_step"],
                                       j["trade_stops_level"], j["trade_freeze_level"], 3.5 * j["volume_min"], 0,
                                       "SYMBOL_CALC_MODE_FOREX")
        source["USDJPY"] = "contracts.json (broker export)"
    return specs, source


def weekday_blocks(first: pd.Timestamp, last: pd.Timestamp, n: int = CYCLE_DAYS) -> list:
    days = pd.bdate_range(first.normalize(), last.normalize())
    return [(days[k * n], days[(k + 1) * n - 1]) for k in range(len(days) // n)]


# ----------------------------------------------------------------- main
def integrity(evidence: dict, counts: dict) -> dict:
    exp = expected_inputs()
    res = {"runs": len(evidence), "verified_markers": 0, "gate_failures": []}
    for tag, ev in evidence.items():
        rd = os.path.join(RUNS, f"CAPN_NEXA_{tag}")
        res["verified_markers"] += os.path.exists(os.path.join(rd, "VERIFIED_PASS"))
        bad = [k for k in exp if k in ev["inputs"] and not _same(ev["inputs"][k], exp[k])]
        miss = [k for k in exp if k not in ev["inputs"]]
        extra = [k for k in ev["inputs"] if k not in exp]
        g = {"test_passed": ev["test_passed"], "inputs_exact": not (bad or miss or extra),
             "zero_cap_blocks": counts[tag]["cap_blocks"] == 0, "window_covered": counts[tag]["covers_window"]}
        if not all(g.values()):
            res["gate_failures"].append({tag: g, "bad": bad, "missing": miss, "extra": extra})
    sums = {}
    for ln in read_lines(os.path.join(DNA_DIR, "SHA256SUMS")):
        h, f = ln.split()
        sums[f] = h == sha256(os.path.join(DNA_DIR, f))
    res["sha256sums"] = {"files": len(sums), "ok": int(sum(sums.values()))}
    res["pinned"] = {k: sha256(os.path.join(ROOT, k)) == v for k, v in PINNED.items()}
    mt5 = os.path.expanduser("~/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5/Experts")
    res["research_ea_sha256_ok"] = sha256(os.path.join(mt5, "NEXA_Research", "NEXA_EA_CAPN.ex5")) == PINNED["build/NEXA_EA.ex5"]
    res["deployed_ea_sha256"] = sha256(os.path.join(mt5, "Advisors", "NEXA_EA.ex5"))
    res["registries"] = {}
    for reg, (seq, head) in REGISTRY_HEADS.items():
        led = [json.loads(x) for x in read_lines(os.path.join(RESEARCH, reg, "ledger.jsonl"))]
        res["registries"][reg] = {"entries": len(led), "head_seq": led[-1]["seq"],
                                  "head_matches_offmachine_record": led[-1]["seq"] == seq and led[-1]["entry_sha256"] == head}
    smoke = os.path.join(RUNS, "CAPN_NEXA_USDJPY_A2026Q1")
    res["smoke_reused"] = {"run": os.path.basename(smoke), "run_started": read_text(os.path.join(smoke, "RUN.txt")).split("start=")[1].split("\n")[0],
                           "smoke_marker": read_text(os.path.join(RUNS, "SMOKE_PASSED")).strip()}
    res["failed_attempts"] = sorted(os.path.basename(p) for p in glob.glob(os.path.join(RUNS, "FAILEDRUN_*")))
    return res


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    specs, spec_source = load_symbol_specs()
    evidence, counts, trades, daily, cyc = {}, {}, [], [], []
    for sym in SYMBOLS:
        for w, (frm, to) in WINDOWS.items():
            tag = f"{sym}_{w}"
            rd = os.path.join(RUNS, f"CAPN_NEXA_{tag}")
            rows, n_dec, n_cap = read_events(os.path.join(DNA_DIR, f"CAPNEUTRAL_NEXA_TradeDNA_{tag}.csv"))
            tr = pair_trades(rows, sym, w)
            ev = tester_evidence(rd, sym)
            close_costs = float(tr["commission_usd"].sum() + tr["swap_usd"].sum()) if len(tr) else 0.0
            rebuilt, left = rebuild_balance(sym, ev["deals"], close_costs)
            dna_rebuilt = START_BALANCE + (float(tr["realised_pnl_usd"].sum()) if len(tr) else 0.0)
            bars = load_bars(sym, w)
            dec_last = pd.read_csv(os.path.join(DNA_DIR, f"CAPNEUTRAL_NEXA_TradeDNA_{tag}.csv"), usecols=["decision_ts"],
                                   dtype=str)["decision_ts"]
            last_dec = pd.to_datetime(dec_last, format=TS, errors="coerce").max()
            counts[tag] = {"decisions": n_dec, "cap_blocks": n_cap, "trades": len(tr), "deals": len(ev["deals"]),
                           "overlapping_opens": tr.attrs.get("overlapping_opens", 0),
                           **read_events.last_pause,
                           "final_balance": ev["final_balance"], "rebuilt_from_deals": rebuilt,
                           "rebuilt_from_dna_net_r": dna_rebuilt, "open_position_left": left,
                           "reconciles": ev["final_balance"] is not None and abs(rebuilt - ev["final_balance"]) <= 0.01 * max(1, len(ev["deals"]))
                           and abs(dna_rebuilt - ev["final_balance"]) <= 0.01 * max(1, len(tr)),
                           "covers_window": bool(pd.notna(last_dec) and last_dec >= pd.to_datetime(to, format="%Y.%m.%d") - pd.Timedelta(days=4))}
            evidence[tag] = ev
            if len(tr):
                ex = pd.DataFrame([excursion(t, bars) for t in tr.itertuples()], index=tr.index)
                tr = pd.concat([tr, ex], axis=1)
                trades.append(tr)
            dd = daily_returns(tr, trading_days(bars))
            dd["symbol"], dd["window"] = sym, w
            daily.append(dd)
            c = cycles(dd)
            c["symbol"], c["window"] = sym, w
            cyc.append(c)
    T = pd.concat(trades, ignore_index=True).sort_values(["entry_time", "symbol"]).reset_index(drop=True)
    T["balance_before"] = START_BALANCE + T.groupby(["symbol", "window"])["realised_pnl_usd"].transform(lambda x: x.cumsum().shift(1).fillna(0.0))
    T["risk_pct_of_balance"] = T["initial_risk_usd"] / T["balance_before"]
    D = pd.concat(daily, ignore_index=True)
    Y = pd.concat(cyc, ignore_index=True)

    res = {"label": LABEL, "ea_behaviour": "implemented EA (D-PARTIAL-AFTER-BE present)"}
    res["integrity"] = integrity(evidence, counts)
    res["integrity"]["reconciliation"] = {"runs_reconciled": int(sum(v["reconciles"] for v in counts.values())),
                                          "max_abs_diff_deals": max(abs(v["rebuilt_from_deals"] - v["final_balance"]) for v in counts.values()),
                                          "max_abs_diff_dna": max(abs(v["rebuilt_from_dna_net_r"] - v["final_balance"]) for v in counts.values()),
                                          "partial_close_rows": int((T["legs"] > 1).sum()),
                                          "overlapping_opens": int(sum(v["overlapping_opens"] for v in counts.values())),
                                          "deals_equal_2x_trades_every_run": all(v["deals"] == 2 * v["trades"] for v in counts.values())}
    res["arithmetic"] = {"implemented_ceiling": daily_ceiling(RISK, MAX_TP_R, MAX_TRADES),
                         "specification_ceiling": daily_ceiling(RISK, SPEC_BEST_R, MAX_TRADES),
                         "formal_bound_1pct_path": daily_ceiling(CEILING, MAX_TP_R, MAX_TRADES),
                         "wins_needed_for_target": wins_needed(TARGET, RISK, MAX_TP_R)}

    # ---- edge (formal: Gate 8 on net R, entry-time order)
    net = T["net_r"].to_numpy()
    g8 = NS.evaluate(net, GATE8).to_dict()
    g8_iid = NS.evaluate(net, GATE8_IID).to_dict()
    stress = NS.bootstrap_ci(NS.cost_shock(net, 0.15), cfg=GATE8)
    per_sym, pvals = {}, []
    for s in SYMBOLS:
        r = T.loc[T.symbol == s, "net_r"].to_numpy()
        e = NS.evaluate(r, GATE8)
        p = RB.expectancy_pvalue(r)
        pvals.append(p if np.isfinite(p) else 1.0)
        per_sym[s] = {"gate8": e.verdict.value, "metrics": e.metrics, "ci": e.expectancy_ci, "p_one_sided": p}
    for s, rej in zip(SYMBOLS, RB.benjamini_hochberg(pvals, BH_Q)):
        per_sym[s]["bh_reject_q10"] = bool(rej)
    res["edge"] = {"pooled_gate8_block10": g8, "pooled_gate8_iid": g8_iid, "stress_0_15r_ci": stress,
                   "per_symbol": per_sym,
                   "psr_dsr_1_trial": RB.probabilistic_sharpe(net),
                   "exploratory_dsr_sensitivity": {str(n): RB.deflated_sharpe(net, n, VAR_SR_8E) for n in (25, 1000, 4008)}}
    # ---- descriptive (observed)
    comp = {k: float(T[k].mean()) for k in ("gross_r", "entry_slip_r", "price_r_from_fill", "commission_r", "swap_r", "net_r", "spread_r_est")}
    comp["residual_price_r_minus_gross_plus_slip"] = float((T["price_r_from_fill"] - T["gross_r"] - T["entry_slip_r"]).abs().max())
    res["costs"] = {"mean_r": comp, "commission_usd": float(T["commission_usd"].sum()), "swap_usd": float(T["swap_usd"].sum()),
                    "price_pnl_usd": float(T["price_pnl_usd"].sum()), "realised_pnl_usd": float(T["realised_pnl_usd"].sum()),
                    "commission_per_lot_rt": float(-T["commission_usd"].sum() / T["lots"].sum()),
                    "fills_differing_from_intended": int((T["fill"] != T["entry_intended"]).sum()),
                    "entry_slip_r_dist": dist(T["entry_slip_r"]),
                    "gross_r_dist": dist(T["gross_r"]), "net_r_dist": dist(T["net_r"])}
    res["frequency"] = {"trades": len(T), "per_symbol": T.symbol.value_counts().to_dict(),
                        "per_year": T.entry_time.dt.year.value_counts().sort_index().to_dict(),
                        "trading_days": len(D), "days_with_entry": int((D.trades_entered > 0).sum()),
                        "max_entries_one_day": int(D.trades_entered.max()),
                        "lots": dist(T["lots"]), "risk_pct_of_balance_at_entry": dist(T["risk_pct_of_balance"])}
    T["exit_r_bucket"] = pd.cut(T["net_r"], [-np.inf, -1.5, -1.0, -0.5, 0, 0.5, 1, 2, 3, np.inf])
    res["exits"] = {"by_type": T.exit_type.value_counts().to_dict(),
                    "net_r_by_type": T.groupby("exit_type")["net_r"].mean().to_dict(),
                    "net_r_buckets": {str(k): int(v) for k, v in T["exit_r_bucket"].value_counts().sort_index().items()}}
    res["by_quarter"] = {f"{s}|{w}": {"n": len(g), "net_exp": float(g.net_r.mean()), "gross_exp": float(g.gross_r.mean()),
                                       "sum_net_r": float(g.net_r.sum())}
                         for (s, w), g in T.groupby(["symbol", "window"])}
    q = pd.DataFrame(res["by_quarter"]).T
    res["stability"] = {"quarters": len(q), "quarters_net_positive": int((q.net_exp > 0).sum()),
                        "quarters_gross_positive": int((q.gross_exp > 0).sum()),
                        "by_year_net_exp": T.groupby(T.entry_time.dt.year)["net_r"].mean().to_dict()}
    # ---- capital (observed, per symbol; each run its own account)
    halt_days = D[D.ret <= -DAILY_LOSS]
    res["capital"] = {
        "daily_returns_all_symbol_days": dist(D["ret"]),
        "daily_by_symbol": {s: dist(D.loc[D.symbol == s, "ret"]) for s in SYMBOLS},
        "best_10_days": D.nlargest(10, "ret")[["symbol", "day", "ret"]].astype(str).to_dict("records"),
        "losing_days": int((D.ret < 0).sum()), "flat_days": int((D.ret == 0).sum()), "winning_days": int((D.ret > 0).sum()),
        "days_at_or_below_minus_2pct": len(halt_days), "worst_day": float(D.ret.min()),
        "max_drawdown_within_chunk": float(D.drawdown.max()),
        "chunk_returns": {f"{s}|{w}": float(np.prod(1 + g.ret) - 1) for (s, w), g in D.groupby(["symbol", "window"])},
        "days_at_target": int((D.ret >= TARGET).sum()),
        "days_at_target_cp95_upper": clopper_pearson_upper(int((D.ret >= TARGET).sum()), len(D)),
        "cycles": {"n": len(Y), "dist": dist(Y["return"]), "reaching_80x": int((Y["return"] >= (1 + TARGET) ** CYCLE_DAYS - 1).sum()),
                   "ending_below_start": int((Y["return"] < 0).sum())},
        "max_consecutive_losses_by_symbol": {s: NS.trade_metrics(T.loc[T.symbol == s, "net_r"].to_numpy())["max_consecutive_losses"] for s in SYMBOLS},
    }
    # ---- $200 replays (theoretical sizing of the TESTED trades; not broker-executed)
    rep = {}
    for s in SYMBOLS:
        ts = T[T.symbol == s].sort_values("entry_time")
        blocks = weekday_blocks(ts.entry_time.min(), ts.entry_time.max())
        out = {"nexa_rule": [], "theoretical_fractional": [], "preregistered_8e_sim": []}
        for a, b in blocks:
            sub = ts[(ts.entry_time.dt.normalize() >= a) & (ts.entry_time.dt.normalize() <= b)]
            out["nexa_rule"].append(nexa_rule_replay(sub, specs[s]))
            out["theoretical_fractional"].append(nexa_rule_replay(sub, specs[s], fractional=True))
            utc = nexa_time.server_to_utc(sub["entry_time"].reset_index(drop=True), on_invalid="nat").dt.tz_localize(None)
            utc = utc.fillna(sub["entry_time"].reset_index(drop=True) - pd.Timedelta(hours=2))   # DST-ambiguous hour only
            sim_in = pd.DataFrame({"entry_time": utc.to_numpy(),
                                   "risk": sub["risk_dist"].to_numpy(), "r_net": sub["net_r"].to_numpy(),
                                   "cost_r": (-(sub["commission_r"] + sub["swap_r"])).clip(lower=0).to_numpy()})
            sd = CV.simulate(sim_in, specs[s], start_equity=200.0, risk=RISK) if len(sim_in) else pd.DataFrame()
            out["preregistered_8e_sim"].append({"end": float(sd["ending_equity"].iloc[-1]) if len(sd) else 200.0,
                                                "trades_taken": int(sd["trades"].sum()) if len(sd) else 0,
                                                "skipped_below_min_lot": int(sd["skipped_below_min_lot"].sum()) if len(sd) else 0})
        summ = {}
        for k, v in out.items():
            ends = np.array([x["end"] for x in v])
            summ[k] = {"cycles": len(v), "mean_end": float(ends.mean()) if len(ends) else float("nan"),
                       "median_end": float(np.median(ends)) if len(ends) else float("nan"),
                       "cycles_profitable": int((ends > 200).sum()), "cycles_reaching_80x": int((ends >= 200 * (1 + TARGET) ** CYCLE_DAYS).sum()),
                       "trades_taken": int(sum(x["trades_taken"] for x in v)),
                       "extracted_profit_sum": float(np.clip(ends - 200, 0, None).sum()),
                       "losses_realised_sum": float(np.clip(ends - 200, None, 0).sum())}
            for kk in ("skipped_min_lot_exceeds_ceiling", "skipped_below_min_after_throttle", "skipped_daily_halt_or_cap", "skipped_below_min_lot"):
                if v and kk in v[0]:
                    summ[k][kk] = int(sum(x[kk] for x in v))
        rep[s] = summ
    res["replay_200"] = rep
    res["replay_200_spec_source"] = {k: {"source": spec_source[k], "vmin": specs[k].vmin, "vstep": specs[k].vstep, "vmax": specs[k].vmax} for k in SYMBOLS}
    # ---- defect impact (counts from existing records)
    res["defect_impact"] = defect_impact(T)
    # ---- EA survival pause (OBSERVED) and exploratory split
    M = pd.DataFrame(counts).T
    never = {k for k, v in counts.items() if v["first_pause"] is None}
    run_of = T["symbol"] + "_" + T["window"]
    cvp = np.where(T.symbol == "XAUUSD", 100.0, np.where(T.symbol == "USDJPY", 100_000.0 / T.entry_intended, 100_000.0))
    res["survival_pause"] = {
        "runs_paused": int(M["first_pause"].notna().sum()), "runs_never_paused": len(never),
        "opens_after_first_pause": int(M["opens_after_first_pause"].sum()),
        "trades_in_paused_runs": int((~run_of.isin(never)).sum()), "trades_in_never_paused_runs": int(run_of.isin(never).sum()),
        "exploratory_net_exp_paused_runs": float(T.loc[~run_of.isin(never), "net_r"].mean()),
        "exploratory_net_exp_never_paused_runs": float(T.loc[run_of.isin(never), "net_r"].mean()),
        "never_paused": sorted(never)}
    res["frequency"]["max_risk_pct_at_placed_stop"] = float((T.lots * (T.entry_intended - T.sl).abs() * cvp / T.balance_before).max())
    res["frequency"]["trades_below_0_25pct_risk"] = int((T.risk_pct_of_balance < 0.0025).sum())
    res["defect_impact_by_symbol"] = {s: defect_impact(T[T.symbol == s]) for s in SYMBOLS}

    T.drop(columns=["exit_r_bucket"]).to_csv(os.path.join(OUT, "capn_trades.csv"), index=False)
    D.to_csv(os.path.join(OUT, "capn_daily.csv"), index=False)
    Y.to_csv(os.path.join(OUT, "capn_cycles.csv"), index=False)
    pd.DataFrame(counts).T.to_csv(os.path.join(OUT, "capn_run_manifest.csv"))
    with open(os.path.join(OUT, "capn_results.json"), "w") as fh:
        json.dump(res, fh, indent=1, default=str)
    print(json.dumps({"trades": len(T), "gate8": g8["verdict"], "net_exp": g8["metrics"]["expectancy_r"],
                      "reconciled": res["integrity"]["reconciliation"]["runs_reconciled"]}, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
