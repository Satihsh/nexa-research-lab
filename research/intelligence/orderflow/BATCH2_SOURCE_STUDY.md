# Batch 2 source study: Bookmap, MenthorQ, NinjaTrader, Doug Pless streams, Real Deal Futures playlist (2026-10-11)

**Purpose:** a narrative summary of what the batch-2 sources add. The atomic record is in `kb/`: SOURCES (SRC-DOC-002…005, SRC-YT-015…023, SRC-PL-001), CLAIMS (CL-048…071, section E), CONCEPTS (K-01/04–08 appended; new K-12), HYPOTHESIS_QUEUE (OF-24/25/26) and GAPS (K02, K09, K10, D08, Q-09…Q-11).

**Evidence classes** (`kb/README.md`): VERIFIED-DOC · VENDOR-CLAIM · PRESENTER-CLAIM · HYPOTHESIS · TOPIC-ONLY.

## 0. Coverage and what could not be done

| Input | Result |
|---|---|
| bookmap.com, features page, glossary | Read (SRC-DOC-002) |
| menthorq.com, futures/FX model pages, 6 Academy lessons | Read (SRC-DOC-003) |
| MenthorQ "Best GEX tools 2026" guide | Read (SRC-DOC-004). Vendor ranks itself first |
| NinjaTrader order-flow page plus 4 help-guide pages | Read (SRC-DOC-005) |
| 3 Doug Pless × Bookmap live streams | **Metadata + chapters only.** Transcripts refused (YouTube HTTP 429 IP rate limit, via the MCP and the in-app browser) |
| Real Deal Futures "Order Flow Series" playlist (6 videos) | Playlist resolved from a truncated link via the in-app browser. **Metadata + chapters only** (same 429) |
| `7WVX5Y5Mfjk` | Duplicate of SRC-YT-007. Not re-studied |

**Not done:** speech-level extraction from the 9 videos. Retry order is in GAPS Q-09. No presenter claims were invented from chapter titles; those topics are TOPIC-ONLY.

## 1. Verified facts (official documentation)

1. **Spot FX has no order-flow delta** (NinjaTrader, CL-050). Bid/ask delta is unsupported on spot forex because there is no traded "last"; UpDownTick runs on the bid series. Some FX feeds stamp every tick with a fixed volume (CL-070).
   - *Implication:* any "delta" from Pepperstone quotes is quote pressure, not aggressor flow. OF-11 / HYP-017 are downgraded (OF-26).
2. **Imbalance has documented defaults, but "stacked imbalance" has none** (CL-048/051). NinjaTrader uses a ratio of 1.5 with a minimum delta of 10 and a diagonal comparison. Other sources use 300 % or 3:1.
   - *Implication:* it is not a standard object, and is untestable as a source claim (GAP-K02).
3. **The value-area percentage is a convention.** NinjaTrader's default is 68 %, matching S46 (CL-071), while NEXA pre-registered 70 % (S42/S45). NinjaTrader minute profiles spread volume evenly across the bar range; NEXA uses typical price.
   - *Implication:* robustness variants only.
4. **Order-book vocabulary** (Bookmap glossary, CL-053/055): absorption (a fourth definition), sweeps, pulled liquidity, spoofing, MBO vs MBP.
   - *Implication:* NEXA has no exchange book for spot FX (K-12, NO).
5. **GEX tools update from daily open interest.** Futures and FX levels from MenthorQ are EOD-only; intraday models cover equities only (CL-058/063/069).

## 2. Vendor claims (unverified; some useful as definitions)

- **MenthorQ covers GC and currency futures** (6E/6B/6J …) from CME options-on-futures, plus "Key Levels on Forex" incl. XAU (CL-057/059).
  - This is the first source in the KB that claims GEX levels for NEXA's instruments.
  - Methodology is undisclosed, and the vendor's own FAQ still tells gold traders to watch GLD (CL-064).
  - No history and no backtest.
- **Level definitions:**
  - HVL = the inflection of the cumulative gamma curve (regime boundary);
  - Call Resistance / Put Support = the max net call / put gamma strike (CL-060/061/067).
  - This is the same mechanism as DeepCharts' zero gamma and SpotGamma's volatility trigger, under different names and different, undisclosed computations.
- **Expected-move containment of 85–87 % (SPX)** (CL-068) is what a calibrated ±1σ band gives (≈ 84 %) plus the variance risk premium. It is a calibration property, not an edge.
- **Bookmap:**
  - "100 %" native-iceberg detection on CME (CL-054);
  - the heatmap shows "true support and resistance" (CL-056).
  - No methods or evidence are given.
- **"Native vs converted" futures GEX** (CL-062): mechanically plausible (basis drift). It is partly corroborated by NEXA T1: the gold basis map failed; the EUR/GBP/JPY basis maps passed.

## 3. Contradictions recorded

- **CL-064:** MenthorQ "native GC levels" vs "monitor GLD for gold" (intra-vendor).
- **CL-061:** the MenthorQ Call Resistance lesson says dealers are both "mostly short" and "long gamma".
- **K-08:** three vendors (DeepCharts, SpotGamma, MenthorQ) name the regime boundary differently and compute it in undisclosed ways, so their levels are not interchangeable.

## 4. Hypotheses (all data-blocked; none to test now)

- **OF-24:** gold GEX regime → next-session XAUUSD range and mean reversion.
- **OF-25:** 6E/6B/6J gamma strikes as reaction levels for spot FX.
- Both need historical CME options-on-futures OI by strike (GAP-D08: paid data; needs your approval). Both have a low prior, because CME options gamma is a small share of gold/FX flow compared with SPX.
- **OF-26** is a reclassification (proxy delta ≠ order flow), not a test.

## 5. What this changes for NEXA

- **Strengthens existing blocks:** no signed order flow, no book, no stacked imbalance on spot FX.
- **Opens one data question for later:** CME options-on-futures OI history for GC/6E/6B/6J would allow an *independent* GEX test (OF-24/25). Vendor levels cannot be back-tested and should not be used directly.
- **No production, data-collection or test action is proposed.**
