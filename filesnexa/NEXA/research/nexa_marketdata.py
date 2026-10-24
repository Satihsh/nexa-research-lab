"""
nexa_marketdata.py -- Stage 5 external historical market-data pipeline.

Turns third-party historical data into the canonical bars NEXA's research tier
consumes, behind a quality gate that fails closed.

    RAW (Dukascopy .bi5 ticks | HistData M1 csv)
        -> provider adapter (decode, scale, timezone)
        -> canonical tick or bar frame
        -> QUALITY GATE
        -> derived bars M1 -> M5 -> M15 -> H1 -> H4 -> D1
        -> manifest + checksums

WHAT THIS MODULE WILL NOT DO
----------------------------
It will not invent a price, fill a gap, smooth an anomaly, or substitute one
provider's bar for another's. Missing data stays missing and is reported. A
research dataset that quietly repairs itself produces backtests that cannot
happen live, which is the single most expensive failure mode available here.

EXTERNAL DATA IS NOT BROKER DATA
--------------------------------
Dukascopy and HistData describe *their* liquidity, not the execution broker's.
Spread, slippage, fill behaviour, the daily-bar rollover and therefore PDH/PDL
all differ. Every frame produced here carries `source`, and every downstream
claim built on it is a claim about that source. Broker-parity validation
remains a separate, later, unavoidable step.

PROVIDER CONTRACTS, EXTRACTED FROM THE TOOLS' SOURCE (not their READMEs)
------------------------------------------------------------------------
Dukascopy .bi5  (Praveens1234/dukascopy-downloader, keyhankamyar/TickVault)
  * URL: /datafeed/{SYMBOL}/{YYYY}/{MM}/{DD}/{HH}h_ticks.bi5
  * MONTHS ARE 0-INDEXED. January is "00". Both tools do `month - 1`.
    Off-by-one here silently fetches the wrong month's data.
  * LZMA-compressed, big-endian records of 20 bytes:
        >u4 ms-offset from the hour, >u4 ask, >u4 bid, >f4 ask_vol, >f4 bid_vol
  * Integer prices scale by a per-symbol pipet size.
  * Timestamps are UTC.

HistData M1  (philipperemy/FX-1-Minute-Data)
  * Semicolon-delimited: YYYYMMDD HHMMSS;open;high;low;close;volume
  * Timestamps are US EASTERN **WITHOUT DST** -- a fixed UTC-5 offset all year.
    Treating it as America/New_York shifts half the year by an hour and moves
    every session boundary and daily bar with it.
  * `volume` is a tick count, not traded size, and is frequently 0.

CROSS-SOURCE AGREEMENT FOUND
----------------------------
The two Dukascopy tools express price scaling differently -- TickVault as a
multiplier (EURUSD 1e-5, XAUUSD 1e-3), the downloader as a divisor (100000,
1000) -- and they agree exactly. That agreement is asserted in the tests, so a
future change to either registry is caught rather than assumed.

Self-contained: pandas + numpy. lzma is stdlib.
"""

from __future__ import annotations

import hashlib
import json
import lzma
import os
import struct
from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum

import numpy as np
import pandas as pd

CANONICAL_TICK_COLUMNS = (
    "timestamp", "symbol", "bid", "ask", "mid", "spread",
    "bid_volume", "ask_volume", "source", "source_file", "timezone",
)
CANONICAL_BAR_COLUMNS = (
    "time", "symbol", "timeframe", "open", "high", "low", "close",
    "tick_volume", "real_volume", "source", "source_file", "timezone", "quality_status",
)

#: Dukascopy integer-price scaling. Multiply the raw integer by this.
#: EURUSD 1e-5 == divide by 100000; XAUUSD 1e-3 == divide by 1000.
PIPET_SCALE = {
    "EURUSD": 1e-5, "GBPUSD": 1e-5, "AUDUSD": 1e-5, "NZDUSD": 1e-5,
    "USDCHF": 1e-5, "USDCAD": 1e-5, "EURGBP": 1e-5, "EURCHF": 1e-5,
    "USDJPY": 1e-3, "EURJPY": 1e-3, "GBPJPY": 1e-3, "AUDJPY": 1e-3,
    "XAUUSD": 1e-3, "XAGUSD": 1e-3,
}

DUKASCOPY_TICK_STRUCT = ">IIIff"          # ms, ask, bid, ask_vol, bid_vol
DUKASCOPY_RECORD_BYTES = 20

#: HistData is US Eastern with NO daylight saving: a constant offset year-round.
HISTDATA_FIXED_UTC_OFFSET_HOURS = -5

TIMEFRAME_MINUTES = {"M1": 1, "M5": 5, "M15": 15, "H1": 60, "H4": 240, "D1": 1440}


class Severity(str, Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"


class QualityStatus(str, Enum):
    OK = "OK"
    SUSPECT = "SUSPECT"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class Finding:
    severity: Severity
    code: str
    message: str
    count: int = 0
    detail: tuple = field(default_factory=tuple)

    def __str__(self) -> str:
        d = f" (e.g. {list(self.detail)})" if self.detail else ""
        return f"[{self.severity.value}] {self.code}: {self.message} n={self.count}{d}"


@dataclass
class DataQualityResult:
    status: QualityStatus
    findings: list
    stats: dict

    @property
    def ok(self) -> bool:
        return not any(f.severity is Severity.ERROR for f in self.findings)

    def report(self) -> str:
        lines = [f"data quality: {self.status.value}"]
        for k, v in sorted(self.stats.items()):
            lines.append(f"  {k:<26}: {v}")
        lines += ["  " + str(f) for f in self.findings] or ["  (no findings)"]
        return "\n".join(lines)


class MarketDataError(RuntimeError):
    """Raised when data cannot be admitted to the research tier."""


# ---------------------------------------------------------------------------
# provider adapters
# ---------------------------------------------------------------------------

def dukascopy_url(symbol: str, ts: pd.Timestamp) -> str:
    """
    Build a Dukascopy hourly tick URL.

    The month is ZERO-INDEXED in Dukascopy's path scheme: January is "00".
    This is the single most common way to silently download the wrong month.
    """
    return (f"https://datafeed.dukascopy.com/datafeed/{symbol.upper()}/"
            f"{ts.year:04d}/{ts.month - 1:02d}/{ts.day:02d}/{ts.hour:02d}h_ticks.bi5")


def decode_bi5(raw: bytes, symbol: str, hour_start: pd.Timestamp,
               source_file: str = "") -> pd.DataFrame:
    """
    Decode one LZMA-compressed Dukascopy hourly tick file.

    An empty payload is legitimate and common: a market-closed hour genuinely
    contains no ticks. It returns an empty frame rather than raising, because
    treating "closed" as "corrupt" would flag every weekend.
    """
    sym = symbol.upper()
    if sym not in PIPET_SCALE:
        raise MarketDataError(
            f"no pipet scale registered for {sym}; refusing to guess a price "
            f"scale -- a wrong scale silently produces plausible but false prices")
    scale = PIPET_SCALE[sym]

    if not raw:
        return _empty_ticks()
    try:
        payload = lzma.LZMADecompressor(format=lzma.FORMAT_AUTO).decompress(raw)
    except lzma.LZMAError as exc:
        raise MarketDataError(f"{source_file}: not valid LZMA ({exc})") from exc

    if len(payload) == 0:
        return _empty_ticks()
    if len(payload) % DUKASCOPY_RECORD_BYTES != 0:
        raise MarketDataError(
            f"{source_file}: {len(payload)} bytes is not a multiple of "
            f"{DUKASCOPY_RECORD_BYTES}; the file is truncated or corrupt")

    n = len(payload) // DUKASCOPY_RECORD_BYTES
    ms = np.empty(n, dtype="int64")
    ask = np.empty(n, dtype="float64")
    bid = np.empty(n, dtype="float64")
    av = np.empty(n, dtype="float64")
    bv = np.empty(n, dtype="float64")
    for i in range(n):
        off = i * DUKASCOPY_RECORD_BYTES
        m, a, b, avol, bvol = struct.unpack(
            DUKASCOPY_TICK_STRUCT, payload[off:off + DUKASCOPY_RECORD_BYTES])
        ms[i] = m
        ask[i] = a * scale
        bid[i] = b * scale
        av[i] = avol
        bv[i] = bvol

    hour_start = pd.Timestamp(hour_start)
    if hour_start.tzinfo is None:
        hour_start = hour_start.tz_localize("UTC")
    frame = pd.DataFrame({
        "timestamp": hour_start + pd.to_timedelta(ms, unit="ms"),
        "symbol": sym, "bid": bid, "ask": ask,
        "mid": (bid + ask) / 2.0, "spread": ask - bid,
        "bid_volume": bv, "ask_volume": av,
        "source": "dukascopy", "source_file": source_file, "timezone": "UTC",
    })
    return frame[list(CANONICAL_TICK_COLUMNS)]


def _empty_ticks() -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype="object") for c in CANONICAL_TICK_COLUMNS})


def read_histdata_m1(path: str, symbol: str) -> pd.DataFrame:
    """
    Read one HistData ASCII M1 file into canonical bars, converted to UTC.

    HistData timestamps are US Eastern WITHOUT daylight saving -- a fixed
    UTC-5 all year. Localising them to America/New_York would shift roughly
    half the year by an hour, moving every session boundary and every daily
    bar, which in turn moves PDH/PDL and the whole liquidity engine.
    """
    frame = pd.read_csv(path, sep=";", header=None, dtype=str,
                        names=["ts", "open", "high", "low", "close", "volume"])
    if not len(frame):
        return _empty_bars()

    ts = pd.to_datetime(frame["ts"], format="%Y%m%d %H%M%S", errors="coerce")
    bad = ts.isna()
    if bad.any():
        raise MarketDataError(
            f"{os.path.basename(path)}: {int(bad.sum())} unparseable timestamps; "
            f"expected 'YYYYMMDD HHMMSS'")
    utc = ts + timedelta(hours=-HISTDATA_FIXED_UTC_OFFSET_HOURS)

    out = pd.DataFrame({
        "time": utc.dt.tz_localize("UTC"),
        "symbol": symbol.upper(), "timeframe": "M1",
        "open": pd.to_numeric(frame["open"], errors="coerce"),
        "high": pd.to_numeric(frame["high"], errors="coerce"),
        "low": pd.to_numeric(frame["low"], errors="coerce"),
        "close": pd.to_numeric(frame["close"], errors="coerce"),
        # HistData's volume is a tick count, not traded size, and is often 0.
        # real_volume stays NaN: the field is unavailable, not zero.
        "tick_volume": pd.to_numeric(frame["volume"], errors="coerce"),
        "real_volume": np.nan,
        "source": "histdata", "source_file": os.path.basename(path),
        "timezone": "UTC (converted from fixed EST, no DST)",
        "quality_status": QualityStatus.OK.value,
    })
    return out[list(CANONICAL_BAR_COLUMNS)].sort_values("time").reset_index(drop=True)


def _empty_bars() -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype="object") for c in CANONICAL_BAR_COLUMNS})


# ---------------------------------------------------------------------------
# tick -> bar derivation
# ---------------------------------------------------------------------------

def ticks_to_bars(ticks: pd.DataFrame, timeframe: str = "M1",
                  price: str = "bid") -> pd.DataFrame:
    """
    Aggregate canonical ticks into bars, deterministically.

    Conventions, fixed and stated because they change every downstream number:
      * left-labelled, left-closed: a bar stamped 10:00 covers [10:00, 10:01).
        This matches MT5, where iTime() returns a bar's OPEN time.
      * built from BID by default, as MT5 charts are. Ask bars are available
        via price="ask" for spread work, never mixed into one series.
      * empty intervals produce NO bar. A market-closed minute has no bar in
        MT5 either, and inventing a flat one would fabricate liquidity.
    """
    if timeframe not in TIMEFRAME_MINUTES:
        raise MarketDataError(f"unknown timeframe {timeframe}")
    if price not in ("bid", "ask", "mid"):
        raise MarketDataError(f"price must be bid/ask/mid, got {price}")
    if not len(ticks):
        return _empty_bars()

    work = ticks.copy()
    work["timestamp"] = pd.to_datetime(work["timestamp"], utc=True)
    work = work.sort_values("timestamp", kind="mergesort").set_index("timestamp")

    rule = f"{TIMEFRAME_MINUTES[timeframe]}min"
    grouped = work[price].resample(rule, label="left", closed="left")
    bars = grouped.ohlc()
    bars = bars[bars["open"].notna()]           # no ticks -> no bar
    if not len(bars):
        return _empty_bars()

    counts = work[price].resample(rule, label="left", closed="left").count()
    bars["tick_volume"] = counts.reindex(bars.index).astype("int64")

    sym = str(work["symbol"].iloc[0])
    src = str(work["source"].iloc[0])
    out = bars.reset_index().rename(columns={"timestamp": "time"})
    out["symbol"] = sym
    out["timeframe"] = timeframe
    out["real_volume"] = np.nan
    out["source"] = src
    out["source_file"] = f"derived:{price}"
    out["timezone"] = "UTC"
    out["quality_status"] = QualityStatus.OK.value
    return out[list(CANONICAL_BAR_COLUMNS)].reset_index(drop=True)


def resample_bars(bars: pd.DataFrame, target: str) -> pd.DataFrame:
    """
    Derive a higher timeframe from M1 bars.

    Only ever aggregates upward. Deriving M1 from H1 would require inventing
    intrabar structure, and that structure is exactly what NEXA's features read.
    """
    if target not in TIMEFRAME_MINUTES:
        raise MarketDataError(f"unknown timeframe {target}")
    if not len(bars):
        return _empty_bars()
    src_tf = str(bars["timeframe"].iloc[0])
    if TIMEFRAME_MINUTES[target] < TIMEFRAME_MINUTES.get(src_tf, 1):
        raise MarketDataError(
            f"refusing to derive {target} from {src_tf}: downward resampling "
            f"would fabricate intrabar structure")

    work = bars.copy()
    work["time"] = pd.to_datetime(work["time"], utc=True)
    work = work.sort_values("time", kind="mergesort").set_index("time")
    rule = f"{TIMEFRAME_MINUTES[target]}min"
    agg = work.resample(rule, label="left", closed="left").agg(
        open=("open", "first"), high=("high", "max"),
        low=("low", "min"), close=("close", "last"),
        tick_volume=("tick_volume", "sum"))
    agg = agg[agg["open"].notna()]
    if not len(agg):
        return _empty_bars()

    out = agg.reset_index()
    out["symbol"] = str(bars["symbol"].iloc[0])
    out["timeframe"] = target
    out["real_volume"] = np.nan
    out["source"] = str(bars["source"].iloc[0])
    out["source_file"] = f"derived:{src_tf}->{target}"
    out["timezone"] = "UTC"
    out["quality_status"] = QualityStatus.OK.value
    return out[list(CANONICAL_BAR_COLUMNS)].reset_index(drop=True)


# ---------------------------------------------------------------------------
# quality gate
# ---------------------------------------------------------------------------

def validate_ticks(ticks: pd.DataFrame) -> DataQualityResult:
    findings: list = []
    stats: dict = {"rows": len(ticks)}
    if not len(ticks):
        findings.append(Finding(Severity.ERROR, "EMPTY_TICKS", "no tick rows"))
        return DataQualityResult(QualityStatus.REJECTED, findings, stats)

    ts = pd.to_datetime(ticks["timestamp"], utc=True)
    stats["range"] = f"{ts.min()} .. {ts.max()}"
    stats["symbols"] = sorted(set(ticks["symbol"].astype(str)))
    stats["sources"] = sorted(set(ticks["source"].astype(str)))

    if not ts.is_monotonic_increasing:
        findings.append(Finding(Severity.ERROR, "TICKS_OUT_OF_ORDER",
                                "tick timestamps are not chronological",
                                count=int((ts.diff() < pd.Timedelta(0)).sum())))
    exact_dup = ticks.duplicated(subset=["timestamp", "bid", "ask"], keep=False)
    if exact_dup.any():
        findings.append(Finding(Severity.WARN, "DUPLICATE_TICKS",
                                "identical (timestamp, bid, ask) rows",
                                count=int(exact_dup.sum())))

    bid = pd.to_numeric(ticks["bid"], errors="coerce")
    ask = pd.to_numeric(ticks["ask"], errors="coerce")
    bad_price = (bid <= 0) | (ask <= 0) | bid.isna() | ask.isna()
    if bad_price.any():
        findings.append(Finding(Severity.ERROR, "INVALID_PRICE",
                                "zero, negative or missing bid/ask",
                                count=int(bad_price.sum())))
    crossed = (ask < bid) & ~bad_price
    if crossed.any():
        findings.append(Finding(Severity.ERROR, "CROSSED_QUOTE",
                                "ask below bid", count=int(crossed.sum())))

    spread = (ask - bid)[~bad_price & ~crossed]
    if len(spread):
        med = float(spread.median())
        stats["median_spread"] = round(med, 8)
        if med > 0:
            extreme = spread > med * 50
            if extreme.any():
                findings.append(Finding(
                    Severity.WARN, "EXTREME_SPREAD",
                    "spread above 50x the median -- real at rollover and news, "
                    "but flagged so it is never mistaken for normal liquidity",
                    count=int(extreme.sum())))
    status = QualityStatus.OK
    if any(f.severity is Severity.ERROR for f in findings):
        status = QualityStatus.REJECTED
    elif findings:
        status = QualityStatus.SUSPECT
    return DataQualityResult(status, findings, stats)


def validate_bars(bars: pd.DataFrame, *, expect_timeframe: str | None = None,
                  max_gap_bars: int = 60) -> DataQualityResult:
    """
    Quality gate for bar data.

    Weekend and holiday gaps are expected in FX and are reported as INFO, not
    errors. A gate that errors on every Saturday teaches its operator to ignore
    it, which is worse than having no gate.
    """
    findings: list = []
    stats: dict = {"rows": len(bars)}
    if not len(bars):
        findings.append(Finding(Severity.ERROR, "EMPTY_BARS", "no bar rows"))
        return DataQualityResult(QualityStatus.REJECTED, findings, stats)

    t = pd.to_datetime(bars["time"], utc=True)
    stats["range"] = f"{t.min()} .. {t.max()}"
    stats["symbols"] = sorted(set(bars["symbol"].astype(str)))
    stats["timeframes"] = sorted(set(bars["timeframe"].astype(str)))
    stats["sources"] = sorted(set(bars["source"].astype(str)))

    if expect_timeframe and stats["timeframes"] != [expect_timeframe]:
        findings.append(Finding(Severity.ERROR, "TIMEFRAME_MISMATCH",
                                f"expected {expect_timeframe}, found {stats['timeframes']}"))
    if len(stats["symbols"]) > 1:
        findings.append(Finding(Severity.ERROR, "MIXED_SYMBOLS",
                                f"one frame must hold one symbol, found {stats['symbols']}"))
    if not t.is_monotonic_increasing:
        findings.append(Finding(Severity.ERROR, "BARS_OUT_OF_ORDER",
                                "bar times are not chronological"))
    dup = t.duplicated(keep=False)
    if dup.any():
        findings.append(Finding(Severity.ERROR, "DUPLICATE_BAR_TIME",
                                "repeated bar timestamps", count=int(dup.sum())))

    o = pd.to_numeric(bars["open"], errors="coerce")
    h = pd.to_numeric(bars["high"], errors="coerce")
    low = pd.to_numeric(bars["low"], errors="coerce")
    c = pd.to_numeric(bars["close"], errors="coerce")
    missing = o.isna() | h.isna() | low.isna() | c.isna()
    if missing.any():
        findings.append(Finding(Severity.ERROR, "MISSING_OHLC", "missing OHLC values",
                                count=int(missing.sum())))
    nonpos = ((o <= 0) | (h <= 0) | (low <= 0) | (c <= 0)) & ~missing
    if nonpos.any():
        findings.append(Finding(Severity.ERROR, "NONPOSITIVE_PRICE",
                                "zero or negative prices", count=int(nonpos.sum())))
    impossible = (~missing) & ((h < low) | (h < o) | (h < c) | (low > o) | (low > c))
    if impossible.any():
        findings.append(Finding(
            Severity.ERROR, "IMPOSSIBLE_OHLC",
            "high below low, or high/low not enclosing open/close",
            count=int(impossible.sum())))

    tf = stats["timeframes"][0] if len(stats["timeframes"]) == 1 else None
    if tf in TIMEFRAME_MINUTES and len(t) > 1:
        step = pd.Timedelta(minutes=TIMEFRAME_MINUTES[tf])
        gaps = t.diff().dropna()
        big = gaps[gaps > step * max_gap_bars]
        weekend = sum(1 for g in big if g >= pd.Timedelta(days=1))
        stats["gaps_over_threshold"] = len(big)
        stats["weekend_or_holiday_gaps"] = int(weekend)
        intraday = len(big) - weekend
        if intraday:
            findings.append(Finding(
                Severity.WARN, "INTRADAY_GAP",
                f"gaps over {max_gap_bars} bars inside a trading day -- missing "
                f"data, not a market closure", count=int(intraday)))
        if weekend:
            findings.append(Finding(Severity.INFO, "SESSION_GAPS",
                                    "weekend/holiday gaps (expected in FX)",
                                    count=int(weekend)))

    status = QualityStatus.OK
    if any(f.severity is Severity.ERROR for f in findings):
        status = QualityStatus.REJECTED
    elif any(f.severity is Severity.WARN for f in findings):
        status = QualityStatus.SUSPECT
    return DataQualityResult(status, findings, stats)


def assert_quality_or_halt(result: DataQualityResult) -> None:
    """Fail-closed. Data that fails the gate must not enter the research tier."""
    if result.status is QualityStatus.REJECTED:
        raise MarketDataError("MARKET DATA REJECTED\n" + result.report())


# ---------------------------------------------------------------------------
# cross-source consistency
# ---------------------------------------------------------------------------

def cross_source_compare(a: pd.DataFrame, b: pd.DataFrame, *,
                         tolerance_pips: float = 2.0,
                         pip: float = 1e-4) -> DataQualityResult:
    """
    Compare two providers' M1 bars on their overlapping timestamps.

    Providers are never merged. Disagreement is information: two feeds differ
    because their liquidity pools differ, and silently averaging them would
    produce a price series no one could have traded.
    """
    findings: list = []
    stats: dict = {}
    if not len(a) or not len(b):
        findings.append(Finding(Severity.ERROR, "CROSS_SOURCE_EMPTY",
                                "one or both sources are empty"))
        return DataQualityResult(QualityStatus.REJECTED, findings, stats)

    left = a.copy(); right = b.copy()
    left["time"] = pd.to_datetime(left["time"], utc=True)
    right["time"] = pd.to_datetime(right["time"], utc=True)
    merged = left.merge(right, on="time", suffixes=("_a", "_b"))
    stats["overlapping_bars"] = len(merged)
    stats["source_a"] = str(a["source"].iloc[0])
    stats["source_b"] = str(b["source"].iloc[0])
    if not len(merged):
        findings.append(Finding(
            Severity.ERROR, "NO_OVERLAP",
            "no shared timestamps -- the two sources cannot be compared, which "
            "usually means a timezone conversion differs"))
        return DataQualityResult(QualityStatus.REJECTED, findings, stats)

    diff = (pd.to_numeric(merged["close_a"]) - pd.to_numeric(merged["close_b"])).abs() / pip
    stats["median_close_diff_pips"] = round(float(diff.median()), 3)
    stats["p99_close_diff_pips"] = round(float(diff.quantile(0.99)), 3)
    beyond = diff > tolerance_pips
    if beyond.any():
        findings.append(Finding(
            Severity.WARN, "CROSS_SOURCE_DIVERGENCE",
            f"bars differing by more than {tolerance_pips} pips on close",
            count=int(beyond.sum())))
    if float(diff.median()) > tolerance_pips * 5:
        findings.append(Finding(
            Severity.ERROR, "CROSS_SOURCE_SYSTEMATIC_OFFSET",
            f"median close difference {diff.median():.1f} pips suggests a "
            f"timezone or scaling error, not normal feed variation"))
    status = (QualityStatus.REJECTED if any(f.severity is Severity.ERROR for f in findings)
              else QualityStatus.SUSPECT if findings else QualityStatus.OK)
    return DataQualityResult(status, findings, stats)


# ---------------------------------------------------------------------------
# manifest / versioning
# ---------------------------------------------------------------------------

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_dataset(bars: pd.DataFrame, out_dir: str, *, symbol: str,
                  timeframe: str, dataset_version: str = "1.0") -> dict:
    """Write one symbol/timeframe frame with a checksummed manifest entry."""
    os.makedirs(out_dir, exist_ok=True)
    name = f"{symbol.upper()}_{timeframe}.csv"
    path = os.path.join(out_dir, name)
    frame = bars.copy()
    frame["time"] = pd.to_datetime(frame["time"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    frame.to_csv(path, index=False, lineterminator="\n")
    t = pd.to_datetime(bars["time"], utc=True)
    return {
        "file": name, "sha256": sha256_file(path), "bytes": os.path.getsize(path),
        "symbol": symbol.upper(), "timeframe": timeframe, "rows": len(bars),
        "first_bar": str(t.min()), "last_bar": str(t.max()),
        "sources": sorted(set(bars["source"].astype(str))),
        "timezone": "UTC", "dataset_version": dataset_version,
    }


def write_manifest(entries: list, out_dir: str, *, dataset_version: str = "1.0",
                   notes: str = "") -> str:
    manifest = {
        "dataset_version": dataset_version,
        "generated_utc": pd.Timestamp.now("UTC").isoformat(),
        "canonical_bar_columns": list(CANONICAL_BAR_COLUMNS),
        "canonical_tick_columns": list(CANONICAL_TICK_COLUMNS),
        "timezone": "UTC",
        "provenance_note":
            "External historical data. NOT broker execution data: spread, "
            "slippage, fill behaviour and the daily-bar boundary differ from "
            "the execution broker. Broker-parity validation remains required.",
        "notes": notes,
        "files": entries,
    }
    path = os.path.join(out_dir, "NEXA_DATASET_MANIFEST.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    return path


def build_timeframe_set(m1: pd.DataFrame,
                        timeframes=("M5", "M15", "H1", "H4", "D1")) -> dict:
    """Derive the full timeframe ladder from validated M1 bars."""
    out = {"M1": m1}
    for tf in timeframes:
        out[tf] = resample_bars(m1, tf)
    return out
