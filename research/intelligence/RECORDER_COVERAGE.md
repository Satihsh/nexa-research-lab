# NEXA Market Recorder: coverage of the user's 22 requested ATAS indicators (2026-10-18)

- **Recorder:** NEXA Monitor v4 (`atas/NexaMonitor/NexaRecorder.cs`, commit f271ad4).
- **Output folder:** `~/Documents/NEXA_ATAS/recorder/<instrument>_<timeframe>/`, one file set per Topstep session.
- **Principle:** record the raw inputs, not 22 indicator outputs.
  - Every indicator below is a function of these inputs.
  - ATAS publishes most formulas at github.com/AtasPlatform/Indicators (folder `Technical/`), so each can be rebuilt **exactly**, with any setting, after the fact.
- **Rule:** nothing in this file is a prediction. Any pattern found in the recording becomes a pre-registered hypothesis, tested on later data (NEXA law L2).

| Requested indicator | Rebuilt from | ATAS formula public? | Status |
|---|---|---|---|
| Big Trades | tape (aggregated trades, side, size) | Other.dll (closed); aggregation = ATAS cumulative trades | ✅ recorded |
| Cluster Search | levels (footprint per price: volume, bid, ask, ticks) | `ClusterSearch.cs` | ✅ |
| Cluster Statistics | bars (volume, bid/ask, ticks, delta, max/min delta, duration, height) | `ClusterStatistic.cs` | ✅ |
| DOM Levels / Heatmap | dom (top 20 levels per side, every 5 s) | `DOM.cs`, `Heatmap/`; DomLevels in Other.dll | ✅ (5 s resolution, not every change) |
| Volume Profile & TPO | levels (profile); bars (TPO = 30-min brackets) | profile = footprint sums | ✅ |
| Absorption | tape + levels + dom | Other.dll (closed) | ⚠️ inputs recorded; ATAS's exact rule unknown |
| Order Flow Indicator | tape | `OrderFlow.cs` | ✅ |
| Order Flow Rhythm | tape | Other.dll (closed) | ⚠️ inputs recorded; exact rule unknown |
| Spread Volume | tape (prev bid/ask + side) | `SpreadVolume.cs` (volume grouped by the bid/ask pair at trade time) | ✅ |
| VWAP / TWAP | bars (+ levels for exact VWAP) | `VWAP.cs` | ✅ |
| Options Chain: Expected Move / GEX / Key Levels | **options chain data** | — | ❌ NEXA has no options feed; GEX was already data-blocked (paid third party) |
| OHLC Plus | bars | `OHLCPlus.cs` | ✅ (weekly/monthly need ≥ 1 week recorded) |
| VSA – WSD Histogram | bars | `VsaWsd.cs` (range in ticks, wicks, EMA100 of range; buy/sell dots when close vs prior open and range shrinks) | ✅ |
| CVD | bars (delta) | `CumulativeDelta.cs` | ✅ |
| CVD Pro / Market Power | tape (delta filtered by trade size) | `MarketPower.cs` | ✅ |
| OI Analyzer | bars (OI field) + tape | `OIAnalyzer.cs` | ⚠️ needs per-trade OI; CME OI is daily, so likely mostly empty |
| Maximum Levels | levels | `MaxLevels.cs` | ✅ |
| Dynamic Levels | levels | `DynamicLevels.cs` | ✅ |
| MBO DOM | market-by-order data | — | ❌ MBO comes only through the Rithmic connector; the ATAS demo uses dxFeed |
| Speed of Tape | bars (ticks, time) / tape | `SpeedOfTape.cs` (ticks in the last 15 s, auto-filter = SMA × 1.5) | ✅ |
| Margin Zones | bars + exchange margin setting | `MarginZones.cs` | ✅ (margin entered manually) |

**Already computed live at each entry/exit (v2–v3):**
- context, levels, VWAP, value area, EMA 5/9/13, MACD 5/13/4, Bollinger, squeeze, RSI, CVD, footprint stacks, big trades.

## Limits stated up front
- **14 days ≈ 10 RTH sessions.** NEXA's tests used 10–16 years and still found no intraday edge. Ten sessions can describe the market. They cannot validate a predictor: any pattern found in 10 days is far more likely luck than edge.
- **Coverage gaps:** the recorder only runs while ATAS X is open, the chart is loaded and the Mac is awake. Gaps show as missing minutes.
- **Data quality:** real-time data is needed for clean tape/DOM. On the free plan the data is 15 minutes delayed.

## Update v5 (2026-10-18)
- **All timeframes:** the recorder keeps 1-minute bars with full footprint. M5, M10, M15, M30, H1, H4 and D are **exact** aggregations of them:
  - OHLC, volume, delta and bid/ask volumes add up;
  - max/min delta follow the running delta;
  - footprint levels add up.
  - So one M1 chart per instrument is enough; no separate charts per timeframe.
- **Live multi-timeframe view:** the panel shows EMA 5/9/13 stack, RSI14 and last-bar direction for M1, M5, M10, M15, M30, H1, H4 and D. The same values go to `mtf.csv` at every entry and exit.
  - H4 is aligned to the 17:00 CT session start; D = Topstep session.
  - D needs about 20+ sessions of chart history; with less it is computed on fewer bars.
- **"Best timeframe":** comparing 8 timeframes and keeping the best is another multiple-testing trap. Any comparison is report-only, and the chosen timeframe must then be confirmed on later data.
- **Data quality (history):** historical dxFeed bars have max/min delta = bar delta and duration 0. True intra-bar values exist only for bars recorded live.
- **DOM:** an unchanged book (e.g. market closed) is no longer written repeatedly.
