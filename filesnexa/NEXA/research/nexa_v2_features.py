"""PHASE3_SIX_FAMILIES_V2 feature / signal builders for F1, F2, F3 (H3a, H3b) and F5.

Deterministic and causal. F4 and F6 are BLOCKED; nothing here touches ticks.

INPUT FRAME ("bars"): Pepperstone M1 BID bars, ascending, one row per bar, with
  time_utc (tz-aware UTC OPEN time), time_server (naive server OPEN time), open, high, low,
  close, spread (points), plus the merged calendar columns listed per builder.

INFORMATION BOUNDARY
  * Row i is decided at its CLOSE: decision_ts[i] = time_utc[i] + 1 min. A builder output at
    row i may depend on rows 0..i only (closed-bar convention; MQL5 start_pos=1). Orders built
    from row i execute at the next bar open >= decision_ts + latency (nexa_execution).
  * Higher timeframes: an M5/M15 bar opened at o is visible at row i only when
    o + len(tf) <= decision_ts[i].
  * Released VALUES (calendar actual) enter only at the release bar (attach_f1), whose close is
    after the release time.
  * SCHEDULED times of exact-time HIGH-importance events are public in advance. The +-30 min
    event filters therefore use them looking forward, by design. Tentative or date-only events are
    not schedulable and are ignored.
  * Rolling statistics are trailing; spread medians use strictly earlier UTC dates; the F2 width
    median uses strictly earlier days; the F5 range median uses strictly earlier sessions; D1
    regime uses the last COMPLETED server day.

SENSITIVITY: every signal-affecting configuration is enumerated from the frozen protocol
(protocols_phase3_v2.build()); no value is hard-coded here, so no undeclared configuration can
be produced. Execution-only parameters (targets, holds, stop variants, fill rules, entry point)
are applied by nexa_v2_trials.

Pre-registered operational choices (made before opening, pinned with this file):
  F1  currency sign map SIGN_MAP (explicit per event code; unknown or no-convention codes are
      excluded); events of the instrument's own currencies only; same-timestamp events form one
      release cluster whose score is the mean of g*c*S; a cluster is skipped when another exact
      HIGH event of the instrument's currencies falls within +-30 min at a DIFFERENT time; spread
      filter uses the median of the same UTC hour over the prior 20 dates; the stop follows design
      section 2.E.
  F2  the day's FIRST break decides; if that bar fails the event filter the day is skipped (no
      later break is taken); a day needs >= 50 % of the Asian-window minutes; width filter
      [0.3, 2.0] x median of the prior 60 valid days (>= 20 required).
  F3  HTF bars = UTC floor bins; ATR = SMA(14) of true range (MT5 iATR); displacement bar t-1 with
      |body| >= 1.2 ATR(t-1); if two HTF bars become visible on the same M1 row the later wins.
  F5  sigma_t = std of the prior 60 M1 close-to-close PRICE changes x sqrt(bars since session start); anchor
      "mean" = mean of session closes, "typical" = mean of (h+l+c)/3, both up to and including t;
      filters per design section 6 (rollover, 1.5x hour-median spread, +-30 min events of the
      instrument currencies plus JPY/AUD/CNY, D1 trend, session-range expansion > 2x the median of
      the prior 20 sessions); the London null session is [07:00, 14:00) UTC.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import protocols_phase3_v2 as pv

BAR = pd.Timedelta(minutes=1)
SYMBOL_CCY = {"EURUSD": ("EUR", "USD"), "GBPUSD": ("GBP", "USD"), "USDJPY": ("USD", "JPY"), "XAUUSD": ("XAU", "USD")}
F1_CURRENCIES = ("USD", "EUR", "GBP", "JPY")
F5_EXTRA_EVENT_CCY = ("JPY", "AUD", "CNY")
EVENT_WINDOW = pd.Timedelta(minutes=30)

# +1: a higher-than-forecast print is conventionally positive for the currency; -1: negative
# (unemployment-type); 0: no conventional currency sign -> excluded. Codes not listed -> excluded.
SIGN_MAP = {
    "consumer-price-expectations": 1, "consumer-price-index-yy": 1, "gdp-qq": 1, "cpi-yy": 1, "gdp-mm": 1,
    "gdp-yy": 1, "gross-domestic-product-qq": 1, "retail-sales-mm": 1,
    "tokyo-consumer-price-index-ex-food-energy-yy": 1, "adp-nonfarm-employment-change": 1,
    "average-hourly-earnings-mm": 1, "chicago-pmi": 1, "consumer-confidence-index": 1, "consumer-price-index": 1,
    "consumer-price-index-ex-food-energy-mm": 1, "consumer-price-index-mm": 1, "core-pce-price-index-mm": 1,
    "core-pce-price-index-yy": 1, "durable-goods-orders": 1, "existing-home-sales": 1, "gdp-sales-qq": 1,
    "ism-manufacturing-pmi": 1, "ism-non-manufacturing-pmi": 1, "ism-non-manufacturing-prices": 1,
    "ism-prices-paid": 1, "jolts-job-openings": 1, "markit-manufacturing-pmi": 1, "markit-services-pmi": 1,
    "new-home-sales": 1, "nonfarm-payrolls": 1, "philadelphia-fed-manufacturing-index": 1,
    "producer-price-index-mm": 1, "retail-sales-ex-autos-mm": 1,
    "initial-jobless-claims": -1, "unemployment-rate": -1,
    "eia-crude-oil-stocks-change": 0, "boj-l-money-stock-yy": 0,
}

F5_SESSIONS = {"22": (22 * 60, 6 * 60), "23": (23 * 60, 6 * 60), "0": (0, 6 * 60)}
F5_NULL_SESSIONS = {"LDN": (7 * 60, 14 * 60)}


# ---------------------------------------------------------------- declared configurations

def _protocol(exp: str) -> dict:
    return next(p for p in pv.build() if p["experiment"] == exp)


def declared(exp: str) -> dict:
    p = _protocol(exp)
    if p["status"] != "ACTIVE":
        raise ValueError(f"{exp} is {p['status']}")
    return {**p["grid"], **p["sensitivity"]}


def _fmt(v) -> str:
    return f"{v:g}" if isinstance(v, float) else str(v)


# ---------------------------------------------------------------- shared causal helpers

def utc(b: pd.DataFrame) -> pd.Series:
    t = pd.to_datetime(b["time_utc"], utc=True)
    return pd.Series(t.to_numpy(), index=b.index)


def ns(ts) -> np.ndarray:
    """int64 UTC nanoseconds of a tz-aware (or naive-UTC) datetime Series/array."""
    return np.asarray(pd.DatetimeIndex(pd.to_datetime(ts, utc=True)).as_unit("ns").asi8)


def day_key(b: pd.DataFrame) -> np.ndarray:
    """UTC calendar date of each row as int64 ns of its midnight."""
    d = ns(b["time_utc"])
    return d - d % int(pd.Timedelta(days=1).value)


def minute_of_day(b: pd.DataFrame) -> np.ndarray:
    d = ns(b["time_utc"])
    return (d % int(pd.Timedelta(days=1).value)) // int(BAR.value)


def atr_sma(high, low, close, n: int = 14) -> np.ndarray:
    """MT5 iATR convention: simple mean of the last n true ranges (trailing)."""
    h, lo, c = (np.asarray(x, float) for x in (high, low, close))
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.vstack([h - lo, np.abs(h - pc), np.abs(lo - pc)]), axis=0)
    return pd.Series(tr).rolling(n, min_periods=n).mean().to_numpy()


def prior_hour_median_spread(b: pd.DataFrame, days: int = 20, min_days: int = 5) -> np.ndarray:
    """For each row: median, over the prior `days` UTC dates (strictly earlier), of that date's
    median spread in the same UTC hour."""
    date, hour = day_key(b), minute_of_day(b) // 60
    per = pd.DataFrame({"d": date, "h": hour, "s": b["spread"].to_numpy(float)}).groupby(["d", "h"])["s"].median()
    wide = per.unstack("h").sort_index()
    prior = wide.shift(1).rolling(days, min_periods=min_days).median()
    stacked = prior.stack(future_stack=True)
    key = pd.MultiIndex.from_arrays([date, hour])
    return stacked.reindex(key).to_numpy(float)


def event_times(cal: pd.DataFrame, currencies) -> np.ndarray:
    """Exact-time HIGH-importance scheduled release times (UTC, sorted) for the given currencies."""
    m = cal["importance"].eq(3) & cal["timestamp_exact"].astype(bool) & cal["currency"].isin(list(currencies))
    return np.unique(ns(cal.loc[m, "time_utc"]))


def schedule_flag(b: pd.DataFrame, times_ns: np.ndarray, window: pd.Timedelta = EVENT_WINDOW) -> np.ndarray:
    """True where a scheduled event lies within +-window of the row's decision time."""
    dec = ns(b["time_utc"]) + int(BAR.value)
    w = int(window.value)
    lo = np.searchsorted(times_ns, dec - w, side="left")
    hi = np.searchsorted(times_ns, dec + w, side="right")
    return hi > lo


def attach_schedule(bars: pd.DataFrame, cal: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Adds sched_inst (instrument currencies) and sched_f5 (instrument + JPY/AUD/CNY)."""
    ccy = [c for c in SYMBOL_CCY[symbol] if c != "XAU"]
    out = bars.copy()
    out["sched_inst"] = schedule_flag(out, event_times(cal, ccy))
    out["sched_f5"] = schedule_flag(out, event_times(cal, sorted(set(ccy) | set(F5_EXTRA_EVENT_CCY))))
    return out


# ---------------------------------------------------------------- F1: macro event direction

def f1_event_table(cal: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Release clusters for one symbol. Uses only nexa_calendar V2 columns that are causal
    (prior-only baselines) plus the first-print PROVENANCE filter (f1_eligible)."""
    base, quote = SYMBOL_CCY[symbol]
    ccy = [c for c in (base, quote) if c in F1_CURRENCIES]
    e = cal[cal["f1_eligible"].astype(bool) & cal["currency"].isin(ccy)].copy()
    e["c"] = e["event_code"].map(SIGN_MAP).fillna(0).astype(int)
    e = e[e["c"] != 0]
    e["g"] = np.where(e["currency"].eq(base), 1, -1)
    e["S"] = (e["actual"].astype(float) - e["forecast"].astype(float)) / e["prior_surprise_sd"].astype(float)
    e["gcs"] = e["g"] * e["c"] * e["S"]
    e["time_utc"] = pd.to_datetime(e["time_utc"], utc=True)
    cl = e.groupby("time_utc").agg(score=("gcs", "mean"), n_events=("gcs", "size"),
                                   codes=("event_code", lambda s: "|".join(sorted(s)))).reset_index()
    sched = event_times(cal, [c for c in (base, quote) if c != "XAU"])
    t_ns = ns(cl["time_utc"])
    w = int(EVENT_WINDOW.value)
    lo = np.searchsorted(sched, t_ns - w, side="left")
    hi = np.searchsorted(sched, t_ns + w, side="right")
    same_lo = np.searchsorted(sched, t_ns, side="left")
    same_hi = np.searchsorted(sched, t_ns, side="right")
    cl["isolated"] = (hi - lo) == (same_hi - same_lo)          # nothing within +-30 min at another time
    cl = cl[cl["isolated"] & np.isfinite(cl["score"]) & (cl["score"] != 0)]
    return cl.sort_values("time_utc").reset_index(drop=True)


def attach_f1(bars: pd.DataFrame, events: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Put each cluster score on the bar whose OPEN equals the release time (decided at its close,
    i.e. after the release). Clusters without an exact bar are dropped and counted."""
    out = bars.copy()
    out["f1_score"] = np.nan
    t = utc(out)
    pos = pd.Series(np.arange(len(out)), index=pd.DatetimeIndex(t))
    pos = pos[~pos.index.duplicated()]
    idx = pos.reindex(pd.DatetimeIndex(events["time_utc"]))
    ok = idx.notna().to_numpy()
    out.loc[out.index[idx[ok].astype(int).to_numpy()], "f1_score"] = events.loc[ok, "score"].to_numpy()
    return out, {"clusters": len(events), "attached": int(ok.sum()), "no_exact_bar": int((~ok).sum())}


def f1_features(b: pd.DataFrame) -> pd.DataFrame:
    """Signal at the row whose close = release + delta_min: direction = sign(score) when
    |score| >= z_star. Stop per design 2.E: distance max(1.5 x ATR(M1,14) at release - 1 min,
    post-release range), beyond the post-release extreme. Needs contiguous minutes."""
    cfg = declared("F1_MACRO_EVENT")
    t = ns(b["time_utc"])
    n = len(b)
    hi, lo, cl = (b[c].to_numpy(float) for c in ("high", "low", "close"))
    sp = b["spread"].to_numpy(float)
    atr = atr_sma(hi, lo, cl)
    hmed = prior_hour_median_spread(b)
    score = b["f1_score"].to_numpy(float)
    out = {}
    for d in cfg["delta_min"]:
        out[f"f1_dir_d{d}"] = np.zeros(n)
        out[f"f1_sl_d{d}"] = np.full(n, np.nan)
        out[f"f1_absz_d{d}"] = np.full(n, np.nan)
    m = int(BAR.value)
    for r in np.flatnonzero(np.isfinite(score)):
        s_val = score[r]
        if r == 0 or t[r - 1] != t[r] - m or not np.isfinite(atr[r - 1]) or s_val == 0:
            continue
        direction = 1.0 if s_val > 0 else -1.0
        for d in cfg["delta_min"]:
            s = r + d - 1
            if s >= n or t[s] != t[r] + (d - 1) * m:
                continue
            if not (np.isfinite(hmed[s]) and sp[s] <= 3.0 * hmed[s]):
                continue
            ph, pl = hi[r:s + 1].max(), lo[r:s + 1].min()
            dist = max(1.5 * atr[r - 1], ph - pl)
            sl = min(cl[s] - dist, pl) if direction > 0 else max(cl[s] + dist, ph)
            out[f"f1_dir_d{d}"][s] = direction
            out[f"f1_sl_d{d}"][s] = sl
            out[f"f1_absz_d{d}"][s] = abs(s_val)
    for d in cfg["delta_min"]:
        for z in cfg["z_star"]:
            ok = np.nan_to_num(out[f"f1_absz_d{d}"], nan=-1.0) >= z
            out[f"sig_f1_z{_fmt(z)}_d{d}"] = np.where(ok, out[f"f1_dir_d{d}"], 0.0)
    return pd.DataFrame(out, index=b.index)


# ---------------------------------------------------------------- F2: XAU Asian-range breakout

def _f2_core(b: pd.DataFrame, jitter_seed: int | None) -> pd.DataFrame:
    cfg = declared("F2_XAU_SESSION_BREAKOUT")
    date = day_key(b)
    mod = minute_of_day(b)
    hi, lo, cl = (b[c].to_numpy(float) for c in ("high", "low", "close"))
    sched = b["sched_inst"].to_numpy(bool)
    n = len(b)
    out = {"f2_atr": atr_sma(hi, lo, cl)}
    for h in cfg["asian_end_utc_hour"]:
        asia = mod < h * 60
        g = pd.DataFrame({"d": date[asia], "h": hi[asia], "l": lo[asia]}).groupby("d")
        rng = pd.DataFrame({"H": g["h"].max(), "L": g["l"].min(), "cnt": g["h"].size()})
        rng = rng[rng["cnt"] >= 0.5 * 60 * h]
        rng["W"] = rng["H"] - rng["L"]
        rng["medW"] = rng["W"].shift(1).rolling(60, min_periods=20).median()
        rng["ok"] = (rng["W"] >= 0.3 * rng["medW"]) & (rng["W"] <= 2.0 * rng["medW"])
        if jitter_seed is not None:                # random-range null: same width, random centre
            u = np.random.default_rng(jitter_seed + h).uniform(-0.5, 0.5, len(rng))
            mid = (rng["H"] + rng["L"]) / 2 + u * rng["W"]
            rng["H"], rng["L"] = mid + rng["W"] / 2, mid - rng["W"] / 2
        per = rng.reindex(date)
        H, L, W, ok = (per[c].to_numpy() for c in ("H", "L", "W", "ok"))
        ok = np.asarray(pd.Series(ok).fillna(False), bool)
        window = (mod >= h * 60) & (mod < 10 * 60)
        mid_col = np.full(n, np.nan)
        for bb in cfg["buffer_b"]:
            up = cl > H + bb * W
            dn = cl < L - bb * W
            brk = window & ok & (up | dn)
            first = brk & ~pd.Series(brk).groupby(date).cumsum().gt(1).to_numpy()
            take = first & ~sched
            sig = np.where(take & up, 1.0, np.where(take & dn, -1.0, 0.0))
            out[f"sig_f2_b{_fmt(bb)}_ae{h}"] = sig
            mid_col = np.where(sig != 0, (H + L) / 2, mid_col)
        out[f"f2_mid_ae{h}"] = mid_col
    return pd.DataFrame(out, index=b.index)


def f2_features(b: pd.DataFrame) -> pd.DataFrame:
    return _f2_core(b, None)


def f2_null_random_range(b: pd.DataFrame) -> pd.DataFrame:
    """Null: a range of the SAME width with its centre moved uniformly within +-W/2 (seeded)."""
    return _f2_core(b, 20260929)


# ---------------------------------------------------------------- F3: FVG zones

def _htf(b: pd.DataFrame, minutes: int) -> tuple[pd.DataFrame, np.ndarray]:
    t_ns = ns(b["time_utc"])
    step = int(pd.Timedelta(minutes=minutes).value)
    key = t_ns - t_ns % step
    g = pd.DataFrame({"k": key, "o": b["open"].to_numpy(float), "h": b["high"].to_numpy(float),
                      "l": b["low"].to_numpy(float), "c": b["close"].to_numpy(float)}).groupby("k", sort=True)
    htf = pd.DataFrame({"o": g["o"].first(), "h": g["h"].max(), "l": g["l"].min(), "c": g["c"].last()})
    done = htf.index.to_numpy() + step - int(BAR.value)
    vis = np.searchsorted(t_ns, done, side="left")          # first M1 row whose close >= HTF close
    return htf.reset_index(drop=True), vis


def f3_features(b: pd.DataFrame) -> pd.DataFrame:
    cfg = declared("F3_FVG_RETRACEMENT")
    n = len(b)
    out = {}
    for tf in cfg["timeframe"]:
        minutes = {"M5": 5, "M15": 15}[tf]
        htf, vis = _htf(b, minutes)
        h, lo, c, o = (htf[k].to_numpy() for k in ("h", "l", "c", "o"))
        atr = atr_sma(h, lo, c)
        h2, l2 = np.r_[np.nan, np.nan, h[:-2]], np.r_[np.nan, np.nan, lo[:-2]]
        body1 = np.abs(np.r_[np.nan, c[:-1]] - np.r_[np.nan, o[:-1]])
        atr1 = np.r_[np.nan, atr[:-1]]
        disp = body1 >= 1.2 * atr1
        bull = (lo > h2) & disp
        bear = (h < l2) & disp
        top = np.where(bull, lo, np.where(bear, l2, np.nan))
        bot = np.where(bull, h2, np.where(bear, h, np.nan))
        size_atr = (top - bot) / atr
        dirn = np.where(bull, 1.0, np.where(bear, -1.0, 0.0))
        cols = {k: np.full(n, np.nan) for k in ("top", "bot", "szatr", "atr")}
        dcol = np.zeros(n)
        keep = (dirn != 0) & np.isfinite(size_atr) & (vis < n)
        for j in np.flatnonzero(keep):                        # ascending j: a later HTF bar overwrites
            i = vis[j]
            dcol[i] = dirn[j]
            cols["top"][i], cols["bot"][i], cols["szatr"][i], cols["atr"][i] = top[j], bot[j], size_atr[j], atr[j]
        out[f"f3_dir_{tf}"] = dcol
        for k, v in cols.items():
            out[f"f3_{k}_{tf}"] = v
        for m in cfg["min_size_atr"]:
            out[f"sig_f3_{tf}_m{_fmt(m)}"] = np.where(np.nan_to_num(cols["szatr"], nan=-1.0) >= m, dcol, 0.0)
    return pd.DataFrame(out, index=b.index)


# ---------------------------------------------------------------- F5: Asian-session mean reversion

def _session(mod: np.ndarray, start: int, end: int) -> np.ndarray:
    return (mod >= start) | (mod < end) if start > end else (mod >= start) & (mod < end)


def _f5_block(b: pd.DataFrame, name: str, start: int, end: int, z_list, anchors) -> dict:
    mod = minute_of_day(b)
    date = day_key(b)
    hi, lo, cl = (b[c].to_numpy(float) for c in ("high", "low", "close"))
    n = len(b)
    ins = _session(mod, start, end)
    sid = date + np.where((start > end) & (mod >= start), int(pd.Timedelta(days=1).value), 0)
    sid = np.where(ins, sid, -1)
    grp = pd.Series(sid)
    ret = pd.Series(cl).diff()                               # price units, same as close - mu
    sig60 = ret.rolling(60, min_periods=60).std().shift(1).to_numpy()
    cnt = pd.Series(np.ones(n)).groupby(grp).cumsum().to_numpy()
    sigma = sig60 * np.sqrt(cnt)
    rng_td = (pd.Series(hi).groupby(grp).cummax() - pd.Series(lo).groupby(grp).cummin()).to_numpy()
    fin = pd.DataFrame({"sid": sid[ins], "h": hi[ins], "l": lo[ins]}).groupby("sid").agg(h=("h", "max"), l=("l", "min"))
    fin["rng"] = fin["h"] - fin["l"]
    fin["med"] = fin["rng"].shift(1).rolling(20, min_periods=10).median()
    med = pd.Series(fin["med"]).reindex(sid).to_numpy()
    srv = pd.to_datetime(b["time_server"])
    ent = srv + BAR
    ent_mod = (ent.dt.hour * 60 + ent.dt.minute).to_numpy()
    rollover = (ent_mod >= 23 * 60 + 55) | (ent_mod <= 65)
    # D1 regime from the last COMPLETED server day
    sday = srv.dt.floor("D")
    d1 = pd.DataFrame({"d": sday, "h": hi, "l": lo, "c": cl}).groupby("d").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    d1["atr"] = atr_sma(d1["h"], d1["l"], d1["c"])
    d1["trend"] = (d1["c"].diff().abs() > 1.5 * d1["atr"]).astype(float).where(d1["atr"].notna())
    prior_trend = d1["trend"].shift(1).reindex(sday.to_numpy()).to_numpy()
    hmed = prior_hour_median_spread(b)
    sp = b["spread"].to_numpy(float)
    next_in = np.r_[ins[1:], False] & (np.r_[sid[1:], -2] == sid)          # next bar still in this session
    base_ok = (ins & next_in & ~rollover & np.isfinite(sigma) & (sigma > 0) & np.isfinite(hmed) & (sp <= 1.5 * hmed)
               & ~b["sched_f5"].to_numpy(bool) & (prior_trend == 0.0) & np.isfinite(med) & (rng_td <= 2.0 * med))
    out = {f"f5_sigma_s{name}": np.where(ins, sigma, np.nan)}
    for a in anchors:
        price = cl if a == "mean" else (hi + lo + cl) / 3.0
        mu = (pd.Series(price).groupby(grp).cumsum() / cnt).to_numpy()
        z = (cl - mu) / sigma
        out[f"f5_mu_a{a}_s{name}"] = np.where(ins, mu, np.nan)
        for zs in z_list:
            sig = np.where(base_ok & (z <= -zs), 1.0, np.where(base_ok & (z >= zs), -1.0, 0.0))
            out[f"sig_f5_z{_fmt(zs)}_a{a}_s{name}"] = sig
    return out


def f5_features(b: pd.DataFrame) -> pd.DataFrame:
    cfg = declared("F5_ASIAN_MEAN_REVERSION")
    out = {}
    for s in cfg["session_start_utc_hour"]:
        start, end = F5_SESSIONS[str(s)]
        out.update(_f5_block(b, str(s), start, end, cfg["z_star"], cfg["anchor"]))
    for name, (start, end) in F5_NULL_SESSIONS.items():
        out.update(_f5_block(b, name, start, end, cfg["z_star"], cfg["anchor"]))
    return pd.DataFrame(out, index=b.index)


BUILDERS = {"F1_MACRO_EVENT": (f1_features, ("f1_score", "spread")),
            "F2_XAU_SESSION_BREAKOUT": (f2_features, ("spread",)),
            "F2_NULL_RANDOM_RANGE": (f2_null_random_range, ("spread",)),
            "F3_FVG_RETRACEMENT": (f3_features, ("spread",)),
            "F5_ASIAN_MEAN_REVERSION": (f5_features, ("spread",))}


# ---------------------------------------------------------------- synthetic certification data

def synthetic_bars(days: int = 70, seed: int = 20260929, start: str = "2024-01-01") -> pd.DataFrame:
    """Deterministic SYNTHETIC M1 bars (weekdays, 24 h) for causality certification only. Not market
    data; never used for any result. Includes a synthetic release-score column and schedule flags."""
    rng = np.random.default_rng(seed)
    t = pd.date_range(start, periods=days * 1440, freq="1min", tz="UTC")
    t = t[t.dayofweek < 5]
    n = len(t)
    c = 100.0 + np.cumsum(rng.normal(0, 0.03, n))
    o = np.r_[100.0, c[:-1]] + rng.normal(0, 0.005, n)
    h = np.maximum(o, c) + rng.uniform(0, 0.03, n)
    lo = np.minimum(o, c) - rng.uniform(0, 0.03, n)
    import nexa_time
    b = pd.DataFrame({"time_utc": t, "time_server": nexa_time.utc_to_server(pd.Series(t)).to_numpy(),
                      "open": o, "high": h, "low": lo, "close": c, "spread": rng.integers(1, 12, n).astype(float)})
    score = np.full(n, np.nan)
    rel = rng.choice(np.arange(200, n - 200), size=max(10, n // 900), replace=False)
    score[rel] = rng.normal(0, 1.5, len(rel))
    b["f1_score"] = score
    ev = np.zeros(n, bool)
    for r in rel:
        ev[max(0, r - 30):r + 31] = True
    b["sched_inst"] = ev
    b["sched_f5"] = ev
    return b


# ---------------------------------------------------------------- calendar baselines (event builder)

CAL_CHECK_COLS = ("prior_n", "prior_modal_clock", "prior_surprise_sd", "local_clock_off_prior")
CAL_PERTURB_COLS = ("actual", "forecast", "prev", "revised_prev")


def calendar_prior_baselines(table: pd.DataFrame) -> pd.DataFrame:
    """The causal F1 baseline columns (strictly earlier releases only). Certified with
    nexa_causality.certify_events: changing any release at/after a cut must leave these columns of
    every earlier release unchanged. NOTE: first_print (a provenance label) uses the NEXT release's
    prev by construction and is deliberately NOT among the certified causal columns."""
    import nexa_calendar
    t = table.drop(columns=[c for c in ("first_print",) if c in table.columns])
    return nexa_calendar.prior_only_baselines(t)[list(CAL_CHECK_COLS)]


def synthetic_calendar(n_per_event: int = 120, seed: int = 20260929) -> pd.DataFrame:
    """Deterministic SYNTHETIC release table for event-builder certification only (not market data)."""
    rng = np.random.default_rng(seed)
    rows = []
    for ev in range(3):
        t0 = pd.Timestamp("2018-01-05 13:30", tz="UTC") + pd.Timedelta(days=ev)
        prev_actual = np.nan
        for k in range(n_per_event):
            f = rng.normal(0, 1)
            a = f + rng.normal(0, 1)
            revised = prev_actual + (rng.normal(0, 0.1) if rng.random() < 0.2 else 0.0)
            rows.append({"id": ev * 10_000 + k, "event_id": ev, "time_utc": t0 + pd.Timedelta(days=7 * k),
                         "local_clock": "08:30" if rng.random() > 0.05 else "07:30", "timestamp_exact": True,
                         "actual": a, "forecast": f, "prev": prev_actual, "revised_prev": revised})
            prev_actual = a
    return pd.DataFrame(rows)
