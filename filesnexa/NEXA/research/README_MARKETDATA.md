# NEXA External Market Data (Stage 5)

`nexa_marketdata.py` turns third-party historical data into the canonical bars
NEXA's research tier consumes, behind a fail-closed quality gate.

```
RAW (Dukascopy .bi5 ticks | HistData M1 csv)
  -> provider adapter (decode, scale, timezone)
  -> canonical tick/bar frame
  -> QUALITY GATE
  -> M1 -> M5 -> M15 -> H1 -> H4 -> D1
  -> manifest + checksums
```

## Forensic findings on the three supplied repositories

All three were cloned and read at source level. **None contains market data.**
All three are downloaders or libraries; the single CSV in FX-1-Minute-Data is a
symbol list.

| Repo | What it is | Data in repo | Target host | Licence |
|---|---|---|---|---|
| `philipperemy/FX-1-Minute-Data` | HistData scraper (`histdata` pkg) | none | `histdata.com`, `drive.google.com` | present |
| `Praveens1234/dukascopy-downloader` | Dukascopy tick + candle fetcher, Flask UI | none | `datafeed.dukascopy.com` | **NONE** |
| `keyhankamyar/TickVault` | Dukascopy tick library, parquet store | none | `datafeed.dukascopy.com` | present |

`dukascopy-downloader` ships **no licence file** — default copyright applies, so
its code may be read but not copied. The format facts below were re-derived and
re-implemented independently.

### Contracts extracted from source (not READMEs)

**Dukascopy `.bi5`**
- `/datafeed/{SYMBOL}/{YYYY}/{MM}/{DD}/{HH}h_ticks.bi5`
- **Months are ZERO-INDEXED.** January is `00`. Both tools do `month - 1`.
  This is the easiest way to silently download the wrong month.
- LZMA, big-endian, 20-byte records: `>u4` ms-from-hour, `>u4` ask, `>u4` bid,
  `>f4` ask_vol, `>f4` bid_vol
- Integer prices scale per symbol. Timestamps UTC.

**HistData ASCII M1**
- `YYYYMMDD HHMMSS;open;high;low;close;volume`, semicolon-delimited
- **US Eastern WITHOUT DST** — a fixed UTC-5 all year. Localising to
  `America/New_York` shifts half the year by an hour, moving every session
  boundary, every daily bar, and therefore PDH/PDL.
- `volume` is a tick count, frequently 0. `real_volume` stays unavailable.

### Cross-source agreement found

TickVault stores price scaling as multipliers (`EURUSD 1e-5`, `XAUUSD 1e-3`);
dukascopy-downloader stores divisors (`100000`, `1000`). **They agree exactly.**
That agreement is asserted in `test_pipet_registries_from_both_tools_agree`, so
a future drift in either registry is caught rather than assumed.

## Design rules

**Nothing is repaired.** No gap is filled, no anomaly smoothed, no provider
substituted for another. Missing data stays missing and is reported. A research
dataset that quietly repairs itself produces backtests that cannot happen live.

**Providers are never merged.** `cross_source_compare()` compares and reports;
it does not blend. Two feeds differ because their liquidity differs, and
averaging them yields a series nobody could have traded.

**Bars are left-labelled, left-closed** — a bar stamped 10:00 covers
`[10:00, 10:01)`, matching MT5's `iTime()`. Built from **bid** by default, as
MT5 charts are. An empty interval produces **no bar**, because a closed minute
has no bar in MT5 either.

**Resampling only aggregates upward.** Deriving M1 from H1 is refused: it would
invent the intrabar structure NEXA's features actually read.

## External data is not broker data

Dukascopy and HistData describe *their* liquidity. Spread, slippage, fill
behaviour and the daily-bar rollover all differ from the execution broker — and
the D1 boundary determines PDH/PDL, which anchors the entire liquidity engine.
Every frame carries `source`; every manifest carries the same warning. Broker
parity remains a separate, later, unavoidable step.

## Quality gate

Ticks: chronological order, duplicates, invalid/zero prices, crossed quotes,
extreme spread. Bars: order, duplicate timestamps, missing OHLC, non-positive
prices, impossible OHLC, timeframe and symbol consistency, gaps.

Weekend and holiday gaps are **INFO, not errors** — a gate that errors every
Saturday teaches its operator to ignore it. Intraday gaps are WARN: those are
missing data, not a market closure.

`assert_quality_or_halt()` raises on `REJECTED`.

## Status

The pipeline is built and tested (48 tests). **It has processed no real data**:
`datafeed.dukascopy.com`, `histdata.com` and `drive.google.com` are all outside
this environment's network allowlist (`host_not_allowed`, verified by attempted
fetch). Downloading must happen where network access exists.
