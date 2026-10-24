# S07: "Beat The Market Maker (BTMM) Strategy" (HowToTrade promotional PDF)
**File:** `Beat-The-Market-Maker-BTMM-Strategy.pdf`. 7 pp. Header "HowToTrade". The chart is GBP/USD 15-minute data from a **Pepperstone** feed (seen in the rendered p. 4).

| Field | Value |
|---|---|
| **Source type** | Industry / practitioner (retail education marketing). The method is attributed to Steve Mauro. |
| **Evidence status** | **Unverified claim.** No data, no test, no statistics. |
| **Processing** | All 7 pages read. Chart pages 4–5 inspected visually. Page 1 is a cover. |

## 1. Claims (SOURCE, all unverified)
**Market-maker premise**
- Market makers (MMs) "manipulate" price: they induce retail traders into positions and then reverse.
- BTMM = "follow the money"; it is likened to "Smart Money Concepts".

**Three-day cycle**
- **Level I:** an MM-driven fast move.
- **Level II:** retail-emotion-driven, without MM support.
- **Level III:** MMs return for profit-taking and continuation in the technical-trend direction.

**Tools**
- Candlestick patterns: spike, spinning top, hammer, doji, morning/evening star, railroad tracks.
- EMAs 5/13/50/200, with the 5/13 cross as entry/exit.
- Colour-coded sessions (Asia, NY).
- Previous-day high and low (HOD/LOD); pivot points.
- Average Daily Range (ADR).
- Traders Dynamic Index (RSI + MAs + volatility bands; "shark fins").

**Profitability:** "not a one-size-fits-all guarantee… depends on skill". No numbers are given.

## 2. Critical assessment
**The "market maker manipulation" mechanism is asserted, not shown.**
- Academic sources in the corpus *do* document MM strategic behaviour:
  - S06 (Cartea, Chang & Graumans): MMs signal to each other with large limit orders and snipe retail limit orders. This is identified with trader-level IDs on the AFM data.
  - S11 (FX last look): brokers reject trades.
  - S24 (algorithmic supracompetitive spreads).
- **But** none of these supports a predictable *3-day directional cycle*. That claim is **UNVERIFIED**.
- The academic MM literature is about **spreads, queue position and adverse selection**, not multi-day directional manipulation (INFERENCE).

**Testable components**
- The 3-day cycle (a day-of-week / run-length test).
- HOD/LOD and pivot levels as support/resistance.
- ADR-based range exhaustion.
- Session ranges.

All can be tested with NEXA's M1 data. None has evidence here.

**Redundancy:** EMA 5/13 is similar to the 8E MACD(5,13,4) momentum engine. NEXA's DEV evidence: momentum improves on the base but is not net-positive.

## 3. NEXA relevance
- Candidate hypotheses (low prior):
  - previous-day high/low and session-range levels;
  - an ADR-exhaustion filter;
  - "3-day cycle" serial dependence of daily ranges and directions.
- **Do not adopt the narrative.** The phrase "market makers trap retail" is not a measurable state with Pepperstone quote-only data. NEXA cannot observe MM identity, inventory or order flow.

**Cross-references:** S06, S11, S24 (real MM behaviour); S01 Forex Essentials (sessions, levels); S09 Bollinger (bands); S08.
