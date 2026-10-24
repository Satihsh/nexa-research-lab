# DeepCharts: official documentation study, connected to the handwritten notes and the Vishaal Fx video

**Date:** 2026-10-11.
**Status:** RESEARCH ONLY.
- Public web pages, free YouTube storyboard previews and the YouTube MCP transcript only.
- No market data collected, nothing downloaded except preview images (to the scratchpad), nothing installed, no credits, no MT5, no trades, no production change.
- **Parent documents:** `NEXA_ORDERFLOW_FRAMEWORK_REPORT.md` and `ADDENDUM_A_VISHAAL_FX_VIDEO.md` (this study supersedes Addendum A §A0 provenance; see §0.3).

## 0. Sources and provenance labels

| Label | Meaning | Sources used |
|---|---|---|
| **OFFICIAL-DOC** | DeepCharts help center or changelog | Help center index; articles: Deep Print (Footprint®), Big Trades, Deep Trades, Deep Profile Values, Deep V-Tracker, Deep Delta, Different Types of Input, Deep-M IVB, Speed of Tape, ADR Target, Option Summary GEX; Changelog v15.6 (links in §8) |
| **OFFICIAL-BLOG** | DeepCharts marketing/education blog | "Deep Trades & Big Trades Explained" |
| **PARTNER** | Broker / data-vendor pages describing DeepCharts | Optimus Futures product page; dxFeed DeepCharts page |
| **PRESENTER** | What the video shows or says | YouTube MCP transcript (timestamps) and metadata; YouTube storyboard previews (free, 10-second frames; up to 320×180 px) |
| **3P** | Other vendors and practitioners (not DeepCharts) | LuxAlgo, TradingView scripts, ATAS feedback, S44 Trader Dale |
| **INTERP** | My interpretation | Marked inline |

### 0.1 General caveats
- **The official documentation is descriptive, not quantitative.** Almost no article gives default values or formulas (verified per article; see each concept). Several articles are internally inconsistent (§1.6).
- **DeepCharts is a futures order-flow platform.** Its data connections are Rithmic, CQG and dxFeed (help center "Connection" section). Its order-flow tools depend on exchange trade data, several on **MBO (market-by-order)** data.

### 0.2 Video facts established (YouTube MCP `get_video_info` / `get_transcript`, storyboard)
- **Title:** "The Trading Truth No one Talks About (PART 2) - LIVE TRADE WITH DEEP CHARTS (ORDER FLOW) Vishaal Fx".
- **Duration 19:00. Uploaded 2026-10-04.**
- **The English auto-transcript is sparse** (mostly "Okay"); the substance is visual.
- **Structure, from storyboard frames at 10-second resolution (approximate ±10 s):**

| Time | What is on screen (PRESENTER, observed) |
|---|---|
| 0:00–0:30 | Intro, disclaimer, podcast shot |
| **0:40–1:00, 1:30–2:20** | **Whiteboard (yellow):** volume profile, **VAH / VAL**, oscillation inside value, a mark near VAL, **LVN** below |
| **3:00–3:50** | **Whiteboard:** "**ORB**" → "**IVB**", then an IVB sketch with oscillation, an upward break, "**E**" (entry) and "**SL**" |
| 4:10–4:50 | Podcast shot |
| 5:00–10:20 | **Live trade on a laptop filmed by camera**, split-screen with the presenters. Chart: orange volume profile on the left, price, a yellow curve, coloured levels |
| **10:30–18:20** | **Direct screen recording** (presenters in a picture-in-picture inset). DeepCharts chart: orange profile (left); a purple/green histogram (right); several **labelled horizontal levels** (green and red labels); an olive horizontal band; candles falling through the band. **From about 17:10 a green risk/reward box extends *below* the entry, i.e. the trade is a SHORT** (INTERP from 320×180 frames; labels unreadable at that size) |
| 18:30–19:00 | Podcast shot, end card |

- **Transcript anchors:**
  - 1:14 "number of transactions"; 1:36–1:41 "Stop loss … target … type of entry"; 2:05–2:08 "low volume";
  - 2:53 "open range breakout … world famous"; 3:03 "initial volume";
  - 6:03 "Delta profile"; 6:20–6:34 "$3,000 … $960 … $3,000"; 6:50 "this trade is purely based on P and Delta and big confirmations";
  - 8:46 "purple band"; 8:53–9:05 "stacked imbalance … if it's breaks here, it will be super target";
  - 10:36 "I'll shift to one minute"; 10:50 "more confirmation"; 11:24–11:27 "entry … stop"; 12:48 "extra contract";
  - 13:41 "around 1 to 2"; 15:24 "We can close"; 16:00 "170 pips"; 17:43–17:51 "particip(ants) heavy … buyers"; 18:12 "transaction".

### 0.3 Correction to Addendum A
- The PDF's "1:20:00+" timeline is **fabricated**; the real video is 19:00.
- The pasted decopy summary's 18:34 outline is consistent with the actual video.
- **Most important:** your handwritten notes (VAH/VAL oscillation, bubble near VAL, SL/TP, LVN, ORB → IVB) **closely match the presenter's whiteboard at 0:40–3:50.** They appear to be notes taken from this lesson. **Verify by screenshot** (§7).

---

## 1. The seven concepts

### 1.1 Big Trades (and Deep Trades)

**Official mechanics (OFFICIAL-DOC)**
- **Big Trades** "visualize large, aggressive market orders in real time" as **bubbles**.
- **Filtering:**
  - *Manual*: Min/Max trade size. Example: "If Min = 30, only trades with 30 contracts or more will be plotted".
  - *Automatic*: the "Big Trades Analysis" algorithm sets thresholds from the symbol's "price behavior and volatility", with Intensity Low/Medium/Strong.
- **Colour encodes the aggressor side:** **Ask Color = aggressive buyers; Bid Color = aggressive sellers.**
- **Size** scales between Min and Max Size via a "Standard Deviation" setting. Opacity has min/max settings.
- **Optional "Zones"** settings (Biggest Only; Shadow/Body Mode: All / Reverse Only / Trend Only / None).
- **No defaults are stated.**

**Deep Trades** (OFFICIAL-DOC) uses **MBO** data to link each aggressive order to "the passive liquidity it interacted with". Markers:
- **hollow circle:** a large trade built from many smaller quantities;
- **filled circle:** large size in one or a few executions;
- **square:** an execution hitting a big resting passive order;
- **diamond:** a large aggressive order hitting a large resting order, which the article calls "the most significant".
- **Requires** Rithmic L1/L2 or dxFeed L2 with DOM Type = MBO.
- "**Historical MBO data cannot be backfilled from the provider**"; it is stored locally only while collected live.

**Naming conflict (OFFICIAL-DOC vs OFFICIAL-DOC):** Changelog v15.6 (dated June 24, 2026) states "The existing Deep Trades indicator has been renamed to Big Trades … name change only", yet still describes Deep Trades as the MBO variant. **The help center keeps both articles.** Which indicator the presenter used cannot be determined from the docs.

**Input data (OFFICIAL-DOC, "Different Types of Input")**
- *Volume:* raw exchange transactions, so a 30-lot market order filling three 10-lot resting orders appears as three 10-lot prints and is **missed** by a Min = 30 filter.
- *Order:* MBO only; shows the passive orders consumed.
- *Aggregate:* computed by DeepCharts. It infers parent orders from a shared **aggressor ID** (example: 100 × 5-lot child trades → one 500-lot parent).
- The article states Aggregate "did not require … MBO". INTERP: an aggressor ID is an order-level field, so that statement is unexplained.

**Interpretation (OFFICIAL-BLOG)**
- "unusually large executed orders" when "a participant sends a significant amount of contracts".
- **Breakout continuation** is claimed more likely with "large buyers above resistance or large sellers below support".
- **Failed breakouts:** aggressive opposite-side activity after a break.
- "most useful when interpreted within a structured trading framework rather than as isolated signals".
- **No threshold is defined** for "unusually large".

**Data required:** exchange trade prints with **aggressor side** and size (Volume); MBO for Deep Trades/Order; a stable trade feed for Aggregate.

**Limitations**
- **(1) Doc-level:** no defaults or formulas; "institutional" is asserted, not defined.
- **(2) Mechanism (EMP, parent report §2.2):** informed traders split orders (Barclay & Warner 1993), so "big" ≠ "informed". Aggregation by aggressor ID partly addresses splitting within one order, but not across orders or time.
- **(3) Futures only:** spot FX/XAU have no central tape.
- **(4) No historical MBO backfill**, so any MBO-based study must be prospective.

### 1.2 Absorption

**Official mechanics**
- **Deep V-Tracker** (OFFICIAL-DOC), "Absorption & Pressure" module:
  - **Absorption** = "Zones where aggressive orders are blocked by passive orders (limit orders)".
  - **Pressure** = "active zones where one counterparty pushes price with force".
  - Labels: **AC** (Absorption Control, "key buying absorption level"), **AE** (Absorption Extreme, "invalidation level"), **PC** (Pressure Control, "key selling level"), **PE** (Pressure Extreme, invalidation).
  - Intensity Strong/Medium/Weak; Level Mode Conservative/Medium/Aggressive.
  - **Detection method, input data and defaults are not stated.**
- **Patterns** module: Acceleration ("sudden 'jerk'"), Exhaustion ("aggressive participants run out of energy or orders"), Slowdown.
- **Deep Delta** (OFFICIAL-DOC) mentions absorption only as "a push in one side that is absorbed by leaving a shadow out of the indicator".

**Interpretation (OFFICIAL-BLOG):** "Absorption when large trades appear but price fails to move … often indicates that a large seller is absorbing liquidity, a situation that can precede a reversal" (hedged "often", "can").

**Data required:** aggressor-signed volume plus price progress. A true "passive order" view needs MBO/DOM.

**Limitations**
- The detection algorithm is proprietary and undocumented.
- Absorption is identified with **hindsight** if the level holds. The AE/PE "invalidation" levels define failure, but no base rates are published.
- NEXA can only compute **unsigned** effort-vs-result (OF-09), not absorption as DeepCharts defines it.

### 1.3 Stacked imbalances

**Official mechanics**
- Deep Print colour mode "Imbalance" plus a threshold "Min. Vol. Diff. For Imbalance" (the minimum volume difference to count an imbalance; **no default, no ratio stated**).
- Changelog v15.6 adds an "**Imbalance Tracker**" that "functions similarly to Imbalance Diagonal but performs calculations horizontally", and "calculates delta percentage relationships horizontally".
- **"Stacked imbalance" is NOT defined anywhere in the official documentation reviewed.** The partner page mentions "Delta and imbalance coloring with auto-threshold" (PARTNER).

**3P definitions (not DeepCharts):** diagonal Ask(p) vs Bid(p−1 tick) at a ratio "around 3:1" (LuxAlgo; S44 uses 300 %). "Stacked" = ≥ 3 consecutive same-side levels (LuxAlgo; MQL5 article). An ATAS user note says stacked-imbalance displays can **lag** (drawn after the bar closes).

**PRESENTER:** 8:53–9:05, "stacked imbalance … if it's breaks here, it will be super target". **No threshold or definition is given in the audio.**

**Data required:** per-price bid/ask aggressor volume (footprint).

**Limitations:** the DeepCharts definition and its defaults are unknown. 3P thresholds are display conventions, not evidence. **Do not assume 300 %/3-stack for DeepCharts.**

### 1.4 Footprint charts (Deep Print)

**Official mechanics (OFFICIAL-DOC)**
- "combines **price, volume, and order flow** into a single candle".
- **Cell types:** Volume ("Total traded volume"), Ask/Bid Split ("Buy vs Sell volume"), **Delta ("Difference between Ask and Bid")**, Delta + Total Volume.
- **Modes:** Profile (histogram) or Box.
- **Input:** Volume, Aggregate Volume, Order ("Order book volume"), Num Trades ("Number of executions per price").
- **Tick grouping:** Auto (Auto Group Factor) or Manual; Group Mode Fixed or "Based on Open/Close".
- **Per-bar POCs:** Volume POC (highest volume in the bar); **Delta POC** ("largest net difference between buy and sell"; Minimum Delta threshold).
- **Colouring:** None/Fixed/Fading/More Colors; by Volume, Delta, Imbalance, Dominant Volume, Dominant Volume Delta.
- **v15.6:** up to four footprint columns side by side.
- **The overview names** "buyer and seller acceleration", "absorption and depletion", "bid/ask dominance", **without definitions.**

**Interpretation (PARTNER):** "Reveals absorption, exhaustion, and trapped traders in real time".

**Data required:** trade-by-trade prints with aggressor side (MBO for the Order input).

**Limitations**
- Tick grouping and colour thresholds change what the trader "sees". No defaults are documented.
- Visual footprint reading is discretionary, and largely **contemporaneous** with price (parent report §2.2).

### 1.5 Volume Profile and Delta Profile

**Volume profile (OFFICIAL-DOC, Deep Profile Values / Volume By Price)**
- POC = "the price level with the highest volume".
- The Value Area line "delimits the extremes of the Value Area High and Low". **VA % is user-set; the example uses 70 %, no default stated.**
- **Peaks and Valleys** ("highest and lowest volume traded"; Sensitivity, Minimum Volume, Exclude High/Low). These are the documented analogues of **HVN/LVN**; the terms HVN/LVN themselves are not used.
- **Period:** Composite / Multiples / Visible / Personalized; length in minutes/days/weeks/months/volume.
- **Session filter** in **U.S. time**. Developing POC/VA; optional VWAP and bands.
- **Input:** Volume / Order / Aggregate Trades / Number of Trades.

**Delta profile**
- **Not defined in the official help articles reviewed.**
- Partner: "Delta profile showing directional conviction at each level" (Optimus); "automatic tick grouping of delta profiles" (dxFeed).
- 3P (LuxAlgo): per-price accumulation of ask-volume − bid-volume. "Strong positive delta at a level where price stalls" is read as passive sellers absorbing.

**PRESENTER:** 6:03 "Delta profile"; 6:50 "purely based on P and Delta". INTERP: "P" most likely means **Profile**. The right-hand purple/green histogram in the 10:30+ recordings is plausibly a delta or bid/ask profile; it is **unconfirmed**.

**Data required:** volume profile = traded volume at price (NEXA has a TRUE version from CME futures 1-minute bars and a PROXY version from tick volume). Delta profile = aggressor-signed volume at price (**NEXA has none**).

**Limitations:**
- VA % and the profile period are free parameters, so the same chart can show different VAH/VAL.
- Peaks/Valleys "Sensitivity" is undocumented.

### 1.6 Order flow and aggressive buying/selling

**Official mechanics**
- **Aggressive buying** = "large orders lift the ask price"; **aggressive selling** = "large orders hit the bid" (OFFICIAL-BLOG).
- Delta = "Difference between Ask and Bid" (OFFICIAL-DOC, Deep Print).
- **Speed of Tape** (OFFICIAL-DOC) "measures the instantaneous speed at which trades are executed". **Defaults are documented:** Number of seconds = 10, Bars to show = 3, Input = Volume, Display = Total. Colours by delta sign. "Sudden spikes in tape speed … often precede or confirm significant price movements".

**Documentation inconsistencies (OFFICIAL-DOC):** the input-type definitions differ between articles.
- "Aggregate" in the Input article is aggressor-ID parent-order reconstruction.
- "Aggregate Trade" in the Volume article "Tracks the number of trades executed".
- "Aggregate Trades" in the Deep Delta article "combin[es] trades executed at the same price level".
- "Aggregate Trades" in the DeepDOM Deep Trades article groups small trades "within a short time window at the same price".

**PRESENTER:** 1:14 "number of transactions"; 10:25 "[tr]aders are engaging more and more"; 17:43 "participants heavy … buyers".

**Data required:** aggressor-flagged trades (exchange). DeepCharts **Order/MBO views need an MBO feed**.

**Limitations:**
- Aggressor classification is exact only from exchange data.
- Order-flow association with price is mostly **contemporaneous**; predictive power at the minutes-to-hours horizon is the open question (HYP-022).

### 1.7 Expansion and breakout confirmation

**Official mechanics (OFFICIAL-DOC, Deep-M IVB)**
- "an algorithmic indicator … to simplify trading the **Opening Range Breakout (ORB)** structure".
- "analyzes years of historical data" and plots "high-probability **projection, protection, and exit** levels" based on "statistical probability calculations" / "historical probability models".
- **RTH Opening Range (Min): 15 / 30 (recommended) / 60** → High, Mid and Low levels.
- After the break, if Enable Protection is on:
  - **Protection** ("highest-probability target of the day");
  - **"Ext. Avg"** (second target);
  - **"Ext. Std-1"** (third/final target).
- **Zones** = "strongest reaction zones during a breakout", where partial exits "may be considered".
- A summary panel shows a Neutral / Positive / Negative bias.
- **The IVB acronym is not expanded. No formulas, instruments, years or entry rules are given.**

**Other expansion-related tools:**
- **ADR Target** (OFFICIAL-DOC): average daily high–low over Length days (example 10), to "Identify realistic daily expansion targets". No formula for the targets.
- **Speed of Tape** (§1.6).
- **There is no DeepCharts indicator named "Expansion"** in the help center. The thumbnail's "Expansion" menu item is promotional artwork; INTERP: it may refer to the IVB extension levels ("Ext. Avg / Ext. Std-1").

**Breakout confirmation (OFFICIAL-BLOG):** large buyers above resistance or large sellers below support "increases the probability that the breakout will continue". This is a claim; no evidence is published.

**PRESENTER:** 2:53 "OB or B open range breakout … world famous"; 3:03 "initial volume"; the whiteboard "ORB → IVB" with E/SL at 3:00–3:50.

**Data required:** OHLC (opening range) for the levels. The "historical probability models" are proprietary. Volume/order-flow confirmation needs trade data.

**Limitations:**
- Deep-M IVB is a **black box**. Its levels cannot be reproduced or validated from the documentation.
- "Recommended 30 min" and "high-probability" are vendor statements without published statistics.

---

## 2. What this means for NEXA's data (no change to the parent capability matrix)

| DeepCharts concept | Minimum data | NEXA status |
|---|---|---|
| Big Trades (Volume/Aggregate input) | Exchange prints with aggressor side and size | **NO** (Massive futures trades NOT_ENTITLED; Pepperstone quotes only). Unsigned per-minute proxy: OF-08 |
| Deep Trades / Order input | **MBO**, collected live (no historical backfill) | **NO.** Only possible prospectively with an MBO feed (Rithmic/dxFeed L2) |
| Absorption (V-Tracker) | Aggressor volume + passive book | **NO** (proprietary). Unsigned effort–result: OF-09 |
| Footprint / imbalances / stacked imbalances | Per-price bid/ask aggressor volume | **NO** |
| Volume profile, VA, POC, peaks/valleys | Traded volume at price | **YES** (futures 1-min TRUE, 2 y; spot tick-volume PROXY, validated for XAU/EUR/JPY in T1) |
| Delta profile | Signed volume at price | **NO** (proxy only) |
| Deep-M IVB levels | Proprietary models | **Not reproducible.** NEXA can test its *own* pre-registered ORB definitions (OF-01/02) |
| Speed of Tape | Trade timestamps | Futures **transactions per minute** (TRUE, 1-min resolution) is the closest available measure |
| DeepGamma GEX | **SPX only**, CBOE-reported market-maker positioning (OFFICIAL-DOC "Option Summary GEX") | **Irrelevant to XAU/FX.** It confirms the parent report's view that a credible GEX needs positioning data that does not exist for gold/FX |

---

## 3. Connection to your handwritten notes (N1–N9 from the parent report §1)

| Note | Resolved by documentation or video? | Status |
|---|---|---|
| N1 checklist (context / location / response / order flow / valid idea) | Not in the DeepCharts docs. The blog says tools are "most useful … within a structured trading framework" | Your framework; consistent with vendor guidance |
| N2 oscillation inside VAH/VAL | The whiteboard at about 1:30 shows the same drawing (storyboard) | **Matches presenter** (confirm with screenshot) |
| **N3/N4 "bubble" and "Big trade for Sellers"** | **Big Trades bubbles; Bid Color = aggressive sellers** (OFFICIAL-DOC). So "big trade for sellers" most plausibly means a **bid-coloured bubble, i.e. large aggressive selling near VAL** | **Partly resolved.** The data requirement is now explicit: aggressor-side trades |
| N4 "buy when price moves above the bubble" | The blog's failed-breakout / absorption logic is the closest documented idea. Large selling that fails to push price lower ("price fails to move") can precede a reversal | **Presenter/your rule;** the docs give no entry rule |
| N5 SL below bubble / around VAL, TP at VAH | Not in the docs; the whiteboard shows SL marks (3:40–3:50 for IVB) | Presenter method; parameters not established |
| N6 break of bubble + VAL → short, TP below VAL at LVN | Not in the docs. INTERP: the live trade (10:30+) is a **short** with a large downside target, *possibly* this variant | **Unconfirmed**, needs screenshots |
| N7 "unfinished auction" | Not in the DeepCharts docs reviewed | Unresolved |
| N8 LVN → market will go up | DeepCharts documents Peaks/Valleys only as volume extremes, with no behavioural claim | Unresolved; still the parent report's competing hypotheses (OF-05) |
| **N9 ORB → IVB** | **DeepCharts' Deep-M IVB is an ORB-based indicator** (OFFICIAL-DOC); the presenter says "open range breakout … initial volume" (2:53–3:03) | **Resolved in substance:** IVB = DeepCharts' ORB-based level-projection tool. **The acronym expansion "Initial Volume Breakout" is not confirmed by DeepCharts** (3P vendors use "Initial Volume" and "Initial Value") |

---

## 4. The presenter's method: what is and is not established

**Established (PRESENTER, from audio and frames):**
- The method combines **volume profile** context, **ORB/IVB**, **delta profile** and "big confirmations" (6:50).
- A **stacked imbalance** was treated as a potential "super target" (8:53).
- The presenter **switched to the 1-minute chart** for confirmation (10:36).
- An **extra contract** was added (12:48).
- The trade was **closed** (15:24), the risk/target framing was **$960 vs $3,000** (6:30–6:34; ≈ 3.1R if both are per-trade dollar figures, INTERP), and the result was described as **"170 pips"** (16:00).
- The live trade appears to be a **short** (green box below entry, about 17:10+).

**Not established:**
- the instrument (the thumbnail shows "NG" artwork with levels at about 20,400; not reliable);
- the timeframe before the switch;
- the exact entry trigger, stop placement and target rule;
- which IVB levels were used;
- whether Big Trades or Deep Trades was on;
- Deep Print settings, VA % and profile period;
- what "170 pips" means for the instrument.

**No entry rules, thresholds or parameters are inferred in this document.**

---

## 5. Unanswered questions

1. What does IVB stand for in DeepCharts' own usage? (The docs never expand it.)
2. How are the Deep-M IVB Protection / Ext. Avg / Ext. Std-1 levels computed (instruments, years, statistic)?
3. Is "Big Trades" today the old Deep Trades (v15.6 rename) or the size-filter tool? Which did the presenter use?
4. The default and definition of the imbalance threshold ("Min. Vol. Diff. For Imbalance"); whether DeepCharts defines *stacked* imbalances, and with what count and ratio.
5. The V-Tracker absorption/pressure detection method and its input data.
6. The default VA % and profile period in Deep Profile Values; the Peaks/Valleys sensitivity.
7. How "Aggregate" input infers aggressor IDs without MBO (the docs contradict themselves).
8. Video: instrument, contract, timeframe, entry/stop/target prices, which levels triggered entry, the role of the "purple band" and of the olive band.
9. Does your note "Big trade for Sellers" denote a bid-coloured bubble (as INTERP suggests)? Was it copied from the whiteboard?

---

## 6. Implications for the NEXA research plan (no implementation)

- **OF-02 (IVB):** redefine the target of the test as "**NEXA's own pre-registered ORB extension levels**", explicitly **not** a replication of Deep-M IVB (proprietary).
  - Any level rule (e.g. range multiples) must be pre-registered and justified in NEXA's documents; it is not taken from DeepCharts.
- **OF-03/OF-08:** the "bubble" is now precisely a **Big Trades bubble with aggressor colour**. NEXA's measurable substitute remains the **unsigned** volume / transaction anomaly on futures 1-minute bars. Results must be labelled as not testing the bid/ask-coloured concept.
- **New data fact:** MBO-based features (Deep Trades, Order input) **cannot be backfilled**. Any future evaluation of them must be prospective, from a live MBO feed. Rank unchanged (last).
- **GEX:** DeepCharts' GEX is SPX-only and uses CBOE-reported market-maker data. It does not change the gold/FX verdict.

---

## 7. Screenshots needed to decode the trading method

**Capture method:**
- YouTube in a normal browser window.
- **Settings → Quality → 1080p.**
- Pause, press **F** for full screen, hide the controls (move the mouse away), take a screenshot.
- Times are ±10 s (storyboard resolution); take 2–3 frames around each.

| Priority | Time | What is on screen | What I need visible |
|---|---|---|---|
| **1** | **10:30–10:50** | First screen-recorded frame of the live chart | **Chart header** (symbol/contract, timeframe, platform panel names); **right price axis**; **every label** on the horizontal levels (likely IVB High/Mid/Low or Protection/Ext levels: INTERP, confirm); the summary panel (top-left, IVB bias, if present) |
| **2** | **11:20–12:00** | Entry and stop | Order/position lines with **prices**; any **bubbles** (colour = side) and their location relative to the levels and the olive band; footprint/imbalance cells if visible |
| **3** | **17:10–18:20** | Green risk/reward box | Entry, stop and target **prices** and any R / $ readout on the box |
| **4** | **3:00–3:50** | Whiteboard: ORB → IVB sketch with **E** and **SL** | The full drawing and all handwriting (where E and SL sit relative to the range and the break) |
| **5** | **1:30–2:20** | Whiteboard: VAH/VAL oscillation, bubble, LVN | All labels, especially the text next to the bubble (to compare with "Big trade for Sellers") and where SL/TP are drawn |
| 6 | 12:40–13:00 | "extra contract" | Position size before and after; the price at the add |
| 7 | 15:20–16:05 | Close and "170 pips" | Exit price, P&L readout, position summary |
| 8 | 8:40–9:20 (filmed laptop) | "purple band", "stacked imbalance … super target" | The band's position vs price and levels; the footprint cells marked as a stacked imbalance (may be illegible: camera-filmed) |
| 9 | 6:15–6:55 (filmed laptop) | "$960 … $3,000", "P and Delta" | Risk/target panel and the delta-profile view (may be illegible) |
| 10 | 10:36 | "I'll shift to one minute" | Timeframe selector before and after |

**Most valuable single set:** priorities 1–3 (screen-recorded, legible). Together they give the instrument, the level system and the trade geometry. Then 4–5 to reconcile your notes with the whiteboard.

---

## 8. Sources

**Official DeepCharts documentation (OFFICIAL-DOC)**
- Help center index: https://www.deepcharts.com/helpcenter
- Deep Print (Footprint®): https://www.deepcharts.com/helpcenter/article/deep-print-(footprint%C2%AE)
- Big Trades: https://www.deepcharts.com/helpcenter/article/big-trades
- Deep Trades: https://www.deepcharts.com/helpcenter/article/deep-trades-deepchart
- Different Types of Input: https://www.deepcharts.com/helpcenter/article/different-types-of-input
- Deep Profile Values: https://www.deepcharts.com/helpcenter/article/deep-profile-values
- Deep V-Tracker: https://www.deepcharts.com/helpcenter/article/deep-v-tracker
- Deep Delta: https://www.deepcharts.com/helpcenter/article/deep-delta
- Deep-M IVB: https://www.deepcharts.com/helpcenter/article/deep-m-ivb
- Speed of Tape (Instant): https://www.deepcharts.com/helpcenter/article/speed-of-tape-(instant)
- ADR Target: https://www.deepcharts.com/helpcenter/article/average-daily-range-target-(adr-target)
- Option Summary GEX: https://www.deepcharts.com/helpcenter/article/option-summary-gex
- Changelog v15.6: https://www.deepcharts.com/changelog/v15.6

**Other sources**
- Official blog: https://www.deepcharts.com/blog/deep-trades-big-trades-orderflow
- Partner pages: https://optimusfutures.com/deepcharts-futures-trading-platform.php ; https://dxfeed.com/platforms/dxfeed-deepcharts/
- Third-party definitions (not DeepCharts):
  - https://www.luxalgo.com/library/concept/bid-ask-imbalance/
  - https://www.luxalgo.com/library/concept/delta-profile.md
  - https://feedback.atas.net/p/imbalance-aggression-and-imbalance-absorption
  - https://www.mql5.com/de/blogs/post/772518
  - https://mmt.gg/indicators/fourblock-ivb-52a5310b
  - https://www.tradingview.com/script/e3ZnxPpk-Initial-Value-Breakout-OmegaTools/
- Video: https://www.youtube.com/watch?v=eLGVyu3utXE (metadata and transcript via YouTube MCP; storyboard previews at i.ytimg.com, saved to scratchpad only).
