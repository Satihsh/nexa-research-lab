"""NEXA 8-engine research features (research only; NOT part of V2, NOT in the live EA).

INPUT: a completed-bar frame produced by `resample_m1` from Pepperstone canonical M1 BID bars:
  time_utc (bar OPEN, tz-aware), open, high, low, close, spread (points, of the bar's FIRST minute,
  the minute a next-bar-open fill happens in), spread_max, tick_volume (sum of M1 quote counts),
  up_tv / dn_tv (quote counts of M1 bars that closed above / below their open), max_m1_tv.
DECISION CONVENTION: a row is decided at its CLOSE and may use rows 0..i only (closed-bar rule).
Every builder is certified with nexa_causality.certify (tests include deliberately leaky variants).

DATA TRUTH (Pepperstone MT5, measured): ticks are QUOTE updates (bid/ask only; volume=0, last=0,
no aggressor flags; DOM unavailable). M1 `tick_volume` = number of quote updates, NOT traded volume.
Therefore:
  * Engine 6 is an ORDER-FLOW **PROXY**: a 1-minute tick-rule split of quote activity
    (`ofi_proxy`), not aggressor order flow, not institutional flow.
  * Engine 7 detects ABNORMAL QUOTE ACTIVITY (`quote_burst`), not trade size / block trades.

Engine definitions (version 1, frozen with the 8E protocol):
  E1 Squeeze   BB(20, 2.0 population sd, SMA mid) inside KC(EMA20 mid +/- 1.5 x Wilder ATR20).
  E2 VEI       Wilder ATR(14) / Wilder ATR(50).
  E3 Donchian  upper/lower = max high / min low of the N bars BEFORE the current bar.
  E4 Trend     EMA(200) of close; slope over 10 bars and distance, both in ATR(14) units.
  E5 Momentum  EMA(9); MACD = EMA5 - EMA13, signal = EMA4(MACD), histogram and its 1-bar slope.
  E6 OFI proxy buy_q = sum of quote counts of up-closing M1 bars in the bar, sell_q likewise;
               ratio = (buy_q + 1) / (sell_q + 1) (Laplace-smoothed), z = (buy_q - sell_q)/(buy_q + sell_q).
  E7 Quote burst  bar quote count / median of the PRIOR 100 bars; trailing percentile rank (prior 500).
  E8 TD Sequential (DeMark classic, v1): buy setup = consecutive closes < close[4] begun by a bearish
               price flip (close[t-1] > close[t-5] and close[t] < close[t-4]); completes at 9 (count
               resets after 9). Sell setup mirrors (closes > close[4]). Buy countdown starts after a
               completed buy setup: counts (not necessarily consecutive) bars with close <= low[2],
               completes at 13; cancelled when a sell setup completes (and vice versa). No TDST,
               perfection or recycling qualifiers in v1 (documented simplification).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TF_RULE = {"M1": "1min", "M5": "5min", "M15": "15min", "M30": "30min", "H1": "1h"}


# ---------------------------------------------------------------- resampling (completed bars only)

def resample_m1(m1: pd.DataFrame, tf: str) -> pd.DataFrame:
    """M1 canonical -> completed TF bars in UTC. A TF bar uses only M1 bars inside its interval, so its
    values are known at its close (the M1 rows after it are never read)."""
    b = m1.copy()
    b["time_utc"] = pd.to_datetime(b["time_utc"], utc=True)
    b = b.sort_values("time_utc")
    up = (b["close"] > b["open"]).astype(float) * b["tick_volume"]
    dn = (b["close"] < b["open"]).astype(float) * b["tick_volume"]
    g = b.assign(up_tv=up, dn_tv=dn).groupby(pd.Grouper(key="time_utc", freq=TF_RULE[tf], label="left", closed="left"))
    out = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                        "close": g["close"].last(), "spread": g["spread"].first(), "spread_max": g["spread"].max(),
                        "tick_volume": g["tick_volume"].sum(), "up_tv": g["up_tv"].sum(), "dn_tv": g["dn_tv"].sum(),
                        "max_m1_tv": g["tick_volume"].max(), "m1_count": g["close"].count()})
    out = out[out["m1_count"] > 0].reset_index()
    return out


# ---------------------------------------------------------------- shared causal primitives

def true_range(b: pd.DataFrame) -> pd.Series:
    pc = b["close"].shift(1)
    return pd.concat([b["high"] - b["low"], (b["high"] - pc).abs(), (b["low"] - pc).abs()], axis=1).max(axis=1)


def wilder(x: pd.Series, n: int) -> pd.Series:
    """Wilder smoothing (alpha = 1/n), seeded after n observations (NaN before)."""
    out = x.ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()
    return out


def atr(b: pd.DataFrame, n: int) -> pd.Series:
    return wilder(true_range(b), n)


def ema(x: pd.Series, n: int) -> pd.Series:
    return x.ewm(span=n, adjust=False, min_periods=n).mean()


def trailing_pct_rank(x: pd.Series, window: int, min_periods: int | None = None) -> pd.Series:
    """Rank of x[t] within x[t-window..t-1] (strictly prior values), in [0, 1]."""
    mp = min_periods or max(20, window // 5)
    arr = x.to_numpy(float)
    out = np.full(len(arr), np.nan)
    for i in range(len(arr)):
        lo = max(0, i - window)
        prev = arr[lo:i]
        prev = prev[np.isfinite(prev)]
        if prev.size >= mp and np.isfinite(arr[i]):
            out[i] = (prev < arr[i]).mean()
    return pd.Series(out, index=x.index)


# ---------------------------------------------------------------- E1 squeeze

def squeeze(b: pd.DataFrame, bb_n: int = 20, bb_k: float = 2.0, kc_n: int = 20, kc_atr_n: int = 20,
            kc_mult: float = 1.5, rank_window: int = 252) -> pd.DataFrame:
    c = b["close"]
    mid = c.rolling(bb_n, min_periods=bb_n).mean()
    sd = c.rolling(bb_n, min_periods=bb_n).std(ddof=0)
    bbu, bbl = mid + bb_k * sd, mid - bb_k * sd
    kmid = ema(c, kc_n)
    a = atr(b, kc_atr_n)
    kcu, kcl = kmid + kc_mult * a, kmid - kc_mult * a
    on = ((bbu < kcu) & (bbl > kcl)).astype(float).where(bbu.notna() & kcu.notna())
    on_b = on.fillna(0).astype(bool)
    run_id = (~on_b).cumsum()
    dur = on_b.groupby(run_id).cumsum().where(on_b, 0).astype(float)
    fire = (on_b.shift(1, fill_value=False) & ~on_b) & on.notna()
    fire_id = fire.cumsum()
    since_fire = pd.Series(np.arange(len(b)), index=b.index).groupby(fire_id).cumcount().astype(float).where(fire_id > 0)
    bw = (bbu - bbl) / mid
    kw = (kcu - kcl) / kmid
    return pd.DataFrame({"sq_on": on, "sq_dur": dur.where(on.notna()), "sq_depth": ((kcu - kcl) - (bbu - bbl)) / (kcu - kcl),
                         "bb_bandwidth": bw, "kc_width": kw, "sq_compression_pct": trailing_pct_rank(bw, rank_window),
                         "sq_fire": fire.astype(float).where(on.notna()), "sq_bars_since_fire": since_fire,
                         "sq_fire_dir": np.sign(c - mid).where(fire)}, index=b.index)


# ---------------------------------------------------------------- E2 VEI

def vei(b: pd.DataFrame, fast: int = 14, slow: int = 50, rank_window: int = 252, slope_n: int = 3) -> pd.DataFrame:
    v = atr(b, fast) / atr(b, slow)
    slope = v - v.shift(slope_n)
    tv = b["tick_volume"].astype(float)
    m = tv.shift(1).rolling(100, min_periods=50).mean()
    s = tv.shift(1).rolling(100, min_periods=50).std()
    return pd.DataFrame({"vei": v, "vei_slope": slope, "vei_accel": slope - slope.shift(slope_n),
                         "vei_pct": trailing_pct_rank(v, rank_window), "tickvol_z": (tv - m) / s}, index=b.index)


# ---------------------------------------------------------------- E3 Donchian

def donchian(b: pd.DataFrame, n: int = 20, atr_n: int = 14) -> pd.DataFrame:
    up = b["high"].shift(1).rolling(n, min_periods=n).max()
    lo = b["low"].shift(1).rolling(n, min_periods=n).min()
    a = atr(b, atr_n)
    rng = b["high"] - b["low"]
    return pd.DataFrame({"dc_upper": up, "dc_lower": lo, "atr14": a,
                         "brk_close_up": (b["close"] > up).astype(float).where(up.notna()),
                         "brk_close_dn": (b["close"] < lo).astype(float).where(lo.notna()),
                         "brk_touch_up": (b["high"] >= up).astype(float).where(up.notna()),
                         "brk_touch_dn": (b["low"] <= lo).astype(float).where(lo.notna()),
                         "brk_mag_atr_up": (b["close"] - up) / a, "brk_mag_atr_dn": (lo - b["close"]) / a,
                         "close_location": ((b["close"] - b["low"]) / rng).where(rng > 0),
                         "range_exp": rng / a}, index=b.index)


# ---------------------------------------------------------------- E4 trend

def trend(b: pd.DataFrame, n: int = 200, slope_n: int = 10) -> pd.DataFrame:
    e = ema(b["close"], n)
    a = atr(b, 14)
    return pd.DataFrame({"ema200": e, "above_ema200": (b["close"] > e).astype(float).where(e.notna()),
                         "ema200_slope_atr": (e - e.shift(slope_n)) / a, "ema200_dist_atr": (b["close"] - e) / a}, index=b.index)


# ---------------------------------------------------------------- E5 momentum

def momentum(b: pd.DataFrame) -> pd.DataFrame:
    c = b["close"]
    e9 = ema(c, 9)
    macd = ema(c, 5) - ema(c, 13)
    sig = ema(macd, 4)
    hist = macd - sig
    hs = hist - hist.shift(1)
    long_parts = pd.concat([c > e9, macd > sig, hist > 0, hs > 0], axis=1)
    short_parts = pd.concat([c < e9, macd < sig, hist < 0, hs < 0], axis=1)
    valid = e9.notna() & sig.notna() & hs.notna()
    return pd.DataFrame({"ema9": e9, "macd": macd, "macd_signal": sig, "macd_hist": hist, "macd_hist_slope": hs,
                         "ema9_slope": e9 - e9.shift(1),
                         "mom_long_score": long_parts.sum(axis=1).astype(float).where(valid),
                         "mom_short_score": short_parts.sum(axis=1).astype(float).where(valid)}, index=b.index)


# ---------------------------------------------------------------- E6 order-flow PROXY (quote activity, tick rule)

def ofi_proxy(b: pd.DataFrame) -> pd.DataFrame:
    bq, sq = b["up_tv"].astype(float), b["dn_tv"].astype(float)
    tot = bq + sq
    return pd.DataFrame({"ofi_buy_q": bq, "ofi_sell_q": sq, "ofi_ratio_up": (bq + 1) / (sq + 1),
                         "ofi_ratio_dn": (sq + 1) / (bq + 1), "ofi_z": ((bq - sq) / tot).where(tot > 0)}, index=b.index)


# ---------------------------------------------------------------- E7 abnormal quote activity

def quote_burst(b: pd.DataFrame, med_window: int = 100, rank_window: int = 500) -> pd.DataFrame:
    tv = b["tick_volume"].astype(float)
    med = tv.shift(1).rolling(med_window, min_periods=med_window // 2).median()
    score = tv / med
    m1med = b["max_m1_tv"].astype(float).shift(1).rolling(med_window, min_periods=med_window // 2).median()
    return pd.DataFrame({"qb_score": score, "qb_pct": trailing_pct_rank(tv, rank_window),
                         "qb_m1_burst": b["max_m1_tv"] / m1med}, index=b.index)


# ---------------------------------------------------------------- E8 TD Sequential

def td_sequential(b: pd.DataFrame) -> pd.DataFrame:
    c, hi, lo = b["close"].to_numpy(float), b["high"].to_numpy(float), b["low"].to_numpy(float)
    n = len(c)
    bs = np.zeros(n)        # buy setup count (bearish run: close < close[4])
    ss = np.zeros(n)        # sell setup count (bullish run: close > close[4])
    bcd = np.zeros(n)       # buy countdown
    scd = np.zeros(n)
    b9 = np.zeros(n)
    s9 = np.zeros(n)
    b13 = np.zeros(n)
    s13 = np.zeros(n)
    buy_count = sell_count = 0
    buy_cd_active = sell_cd_active = False
    buy_cd = sell_cd = 0
    for t in range(n):
        if t >= 5:
            down = c[t] < c[t - 4]
            up = c[t] > c[t - 4]
            # buy setup: start requires a bearish flip
            if down and (buy_count > 0 or c[t - 1] > c[t - 5]):
                buy_count += 1
            else:
                buy_count = 0
            if up and (sell_count > 0 or c[t - 1] < c[t - 5]):
                sell_count += 1
            else:
                sell_count = 0
            if buy_count == 9:
                b9[t] = 1
                buy_cd_active, buy_cd = True, 0
                sell_cd_active, sell_cd = False, 0           # opposite setup cancels countdown
            if sell_count == 9:
                s9[t] = 1
                sell_cd_active, sell_cd = True, 0
                buy_cd_active, buy_cd = False, 0
            if buy_cd_active and buy_count != 9 and c[t] <= lo[t - 2]:
                buy_cd += 1
                if buy_cd == 13:
                    b13[t] = 1
                    buy_cd_active = False
            if sell_cd_active and sell_count != 9 and c[t] >= hi[t - 2]:
                sell_cd += 1
                if sell_cd == 13:
                    s13[t] = 1
                    sell_cd_active = False
            bs[t], ss[t] = buy_count, sell_count
            bcd[t] = buy_cd if buy_cd_active or b13[t] else 0
            scd[t] = sell_cd if sell_cd_active or s13[t] else 0
            if buy_count == 9:
                buy_count = 0
            if sell_count == 9:
                sell_count = 0
        else:
            bs[t] = ss[t] = np.nan
    return pd.DataFrame({"td_buy_setup": bs, "td_sell_setup": ss, "td_buy_countdown": bcd, "td_sell_countdown": scd,
                         "td_buy9": b9, "td_sell9": s9, "td_buy13": b13, "td_sell13": s13}, index=b.index)


def td_exhaustion(td: pd.DataFrame, lookback: int = 3) -> pd.DataFrame:
    """Bullish exhaustion (vetoes LONG): sell setup count >= 8, or a sell 9 / sell 13 within the last
    `lookback` bars. Bearish exhaustion (vetoes SHORT) mirrors on the buy side."""
    s9 = td["td_sell9"].rolling(lookback, min_periods=1).max()
    s13 = td["td_sell13"].rolling(lookback, min_periods=1).max()
    b9 = td["td_buy9"].rolling(lookback, min_periods=1).max()
    b13 = td["td_buy13"].rolling(lookback, min_periods=1).max()
    bull = ((td["td_sell_setup"] >= 8) | (s9 > 0) | (s13 > 0)).astype(float)
    bear = ((td["td_buy_setup"] >= 8) | (b9 > 0) | (b13 > 0)).astype(float)
    score_bull = (td["td_sell_setup"].fillna(0) / 9 + 2 * s13.fillna(0)).clip(upper=3)
    score_bear = (td["td_buy_setup"].fillna(0) / 9 + 2 * b13.fillna(0)).clip(upper=3)
    return pd.DataFrame({"td_bull_exhaust": bull, "td_bear_exhaust": bear, "td_bull_score": score_bull,
                         "td_bear_score": score_bear}, index=td.index)


# ---------------------------------------------------------------- all features

def all_features(b: pd.DataFrame, dc_n: int = 20) -> pd.DataFrame:
    td = td_sequential(b)
    return pd.concat([squeeze(b), vei(b), donchian(b, dc_n), trend(b), momentum(b), ofi_proxy(b), quote_burst(b),
                      td, td_exhaustion(td)], axis=1)


def features_dc20(b: pd.DataFrame) -> pd.DataFrame:
    return all_features(b, 20)


def features_dc55(b: pd.DataFrame) -> pd.DataFrame:
    return all_features(b, 55)


BUILDERS = {"features_dc20": features_dc20, "features_dc55": features_dc55}
EXTRA_PERTURB = ("spread", "tick_volume", "up_tv", "dn_tv", "max_m1_tv")


def synthetic_m1(n: int = 30000, start: str = "2024-03-04", price: float = 2000.0, vol: float = 0.3,
                 seed: int = 20261001) -> pd.DataFrame:
    """Deterministic SYNTHETIC M1 bars for causality certification only (not market data)."""
    rng = np.random.default_rng(seed)
    t = pd.date_range(start, periods=n, freq="1min", tz="UTC")
    c = price + np.cumsum(rng.normal(0, vol, n))
    o = np.r_[price, c[:-1]]
    return pd.DataFrame({"time_utc": t, "open": o, "high": np.maximum(o, c) + rng.uniform(0, vol, n),
                         "low": np.minimum(o, c) - rng.uniform(0, vol, n), "close": c,
                         "tick_volume": rng.integers(5, 200, n).astype(float), "spread": rng.integers(8, 25, n).astype(float)})
