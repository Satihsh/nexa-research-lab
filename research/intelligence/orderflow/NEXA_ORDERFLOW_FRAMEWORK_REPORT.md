# NEXA: Order Flow, Options Flow and Market Intelligence. Research Report

**Date:** 2026-10-11.
**Status:** RESEARCH ONLY. No data collected, no MT5 launched, no code or configuration changed, no trades.

**Inputs**
- Four handwritten pages (IMG_6395–6398).
- The NEXA repository: `research/intelligence/` 01–20, the T1/T2 validation results and `filesnexa/NEXA` sources.
- Corpus notes S40–S54.
- A short literature check (sources at the end).

**Evidence labels used throughout**

| Label | Meaning |
|---|---|
| **MECH** | Established mechanics (exchange rules, definitions, accounting identities) |
| **EMP** | Peer-reviewed or well-documented empirical evidence |
| **PRAC** | Practitioner claim (books, courses, indicator vendors). Not evidence of profitability |
| **NEXA-EV** | NEXA's own measured results |
| **HYP** | My hypothesis or interpretation; untested |

---

## 0. Summary for the reader

1. **Your notes describe two different trades that share one drawing.**
   - **A rotation trade:** buy *inside* value near VAL after price clears a high-volume cluster, and target the opposite edge (VAH).
   - **A breakout trade:** sell when price breaks the cluster *and* VAL, and target the next LVN below value.
   - They belong to opposite market states, **balance** and **imbalance**. Your question 1 ("What is the context?") must decide which state applies before either is allowed. That is the single most important formalisation in this report.
2. **The "bubble" / big-trade concept cannot be measured as you drew it with NEXA's current data.**
   - The drawing implies individual large prints with an aggressor side ("big trade for sellers").
   - NEXA has **no trade-level data and no aggressor side** for any instrument. Massive futures trades and quotes are NOT_ENTITLED; Pepperstone ticks are quotes only.
   - We *can* measure **unsigned volume anomalies** at 1-minute resolution on CME futures (true volume plus transaction count, about 2 years), and tick-volume anomalies on spot (9 years).
   - So a "volume-cluster" version of your idea is testable. The "sellers were trapped" interpretation is not.
3. **Your LVN rule contradicts the mainstream auction-theory reading.**
   - You wrote: "market go down will reach LVN, once reach LVN, market will go up".
   - The usual Market Profile / Volume Profile reading is that LVNs are **low-acceptance** prices that price tends to move *through* quickly, while high-volume areas slow price down.
   - Both readings exist in practitioner literature. **No peer-reviewed evidence supports either at NEXA's horizon.** This is a clean, cheap, competing-hypothesis test (H-05).
4. **"Unfinished auction" in your notes is linked to LVNs, but in Market Profile it means something else.**
   - It refers to a **poor high or poor low**: a session extreme with no single-print tail, which practitioners expect to be revisited.
   - That is measurable *exactly* from M1 bars as a TPO profile, over 9 years, and is one of the cheapest tests available (H-04).
5. **Options flow and GEX** are, for NEXA's instruments (XAUUSD, EURUSD, GBPUSD, USDJPY), **mostly unmeasurable and of uncertain relevance.**
   - Gold and FX option markets that matter are COMEX/CME options on futures and, above all, the OTC FX options market. NEXA sees neither.
   - The only options data in reach is US-listed ETF options: GLD, FXE, FXB, FXY.
     - Through Massive: unsigned volume, **no open interest**.
     - Through a second connector in this session (Alpha Vantage-style tools): it advertises historical chains with IV and Greeks, but **the entitlement is unverified and was not called** (§4.3).
   - Even with full data, dealer-gamma sign identification is an unsolved inference problem (S54).
6. **NEXA's own evidence base forces a cost-first lens.**
   - NEXA's existing rule set lost −0.318R per trade over 1,902 tester trades.
   - Commission alone was −0.245R, because stops were tiny (median 2.4 pips on EURUSD).
   - Any intraday setup with structural stops a few pips wide starts deep in the hole. **Every hypothesis below is evaluated net of costs, in R, against a geometry-matched random-entry null.**
7. **Ranked first** (cheapest, cleanest data, most informative):
   - **H-01** opening-range breakout and **H-02** volume-confirmed ORB (your "IVB");
   - **H-03** your core value-area rotation/breakout family;
   - **H-04** unfinished auctions;
   - **H-05** LVN behaviour.
   - Order-flow-confirmation and GEX hypotheses rank last because their data does not exist for us yet.

---

## 1. Faithful transcription of the handwritten notes

Spelling as written; `[?]` marks an uncertain reading; `[sic]` marks an apparent slip. My interpretation is kept separate (§1.5).

### 1.1 Page 1 (IMG_6395): checklist and value area

> **Checklist for intraday Trading (market profile + Volume profile + Order flow)**
> ① What is the context ?
> ② Where is the location ?
> ③ What is the price response ?
> ④ What does order flow show ?
> ⑤ Do I have a valid trade idea ?
>
> **Volume Profile ↓**
> *[Diagram: a vertical price axis with a volume-profile curve. Two horizontal lines are labelled* VALUE AREA HIGH (VAH) *(upper) and* VALUE AREA LOW (VAL) *(lower). The profile has a large bulge between them, a small bulge above VAH and a bulge below VAL. A zig-zag "ʌʌʌ" line oscillates between VAH and VAL.]*
> The middle part where the market runs ʌʌʌ

### 1.2 Page 2 (IMG_6396): big trades

> **BIG TRADES**
> *[Diagram: profile with VAH and VAL lines. Price zig-zags "MMMM" inside the value area. At the end of the last downswing, near VAL, a **circle** is drawn. From it an **arrow points up** (price rising), and an arrow points right to the label:]* **"Big trade for Sellers"** `[?: "Big trad. for Sellers"; the "for" is overwritten]`
> Wait until we get big trades !!!
> What is big trades ?
> — A particular point (a lot of transaction happened → it will represent like bubble.
> !!! When the market move above the bubble (means the market go up broke the bubble) we should buy !!!

### 1.3 Page 3 (IMG_6397): stops, targets, LVN, unfinished auction

> Stop loss → Below the bubble and also around VAL
> Take Profit → at VAH.
> ————
> If market breaks the bubble and break the VAL, from here we can put SL at the top, TP at below VAL.
> ↓
> at below got LVN
> **[boxed]** LOW Volume NOTE `[sic: Node]`
> \* Unfinish Auction
> \* Automatically market go down will reach LVN, once reach LVN, market will go up

### 1.4 Page 4 (IMG_6398): ORB → IVB

> **[boxed] ORB**
> Open Range Breakout
> ↓
> Initial Volume Breakout

### 1.5 Interpretation (mine, labelled HYP)

| # | What you wrote | What I think it means | Open ambiguities you should resolve |
|---|---|---|---|
| N1 | Five-question checklist | A sequential filter: each question must be answered before the next | Is the sequence strict (any "no" ⇒ NO TRADE) or a score? This report assumes **strict gating** |
| N2 | "The middle part where the market runs ʌʌʌ" | Price is **balancing** inside value: rotations between VAH and VAL | Which profile defines value: the prior session, the developing session, or a composite of several days? |
| N3 | Bubble = "a particular point where a lot of transactions happened" | A **volume cluster** at a narrow price × time location, drawn as a bubble on "big trades" charts (ATAS, Bookmap, Quantower-style; Trader Dale S44 uses a ≥ 25-contract print filter on 6E) | Is it **one large print**, **many prints at one price**, or **a high-volume bar**? The three need different data (§4) |
| N4 | "Big trade for Sellers" at the low of the rotation | Aggressive **selling** occurred near VAL. When price then rises above the bubble, those sellers are offside ("trapped"), and their exits (buy-to-cover) plus responsive buyers push price up | An equally consistent reading: a **passive buyer absorbed** the selling there. Both predict "up", but they differ on what failure looks like. **Neither is distinguishable without aggressor-side data** |
| N5 | Buy when price breaks above the bubble; SL below the bubble / around VAL; TP at VAH | A **responsive long** from the bottom of value to the top. "Breakout" refers to the micro-cluster, **not** to value | Stop = bubble low, or VAL, or the lower of the two? Entry on touch, on bar close, or on retest? |
| N6 | If price breaks the bubble **and** VAL → SL "at the top", TP below VAL at the LVN | An **initiative short**: value is rejected downward; target the next low-volume node below value | "The top" = bubble high? VAL? VAH? This changes risk by multiples |
| N7 | "Unfinish Auction" next to LVN | You link the LVN below value to an incomplete auction | In Market Profile, "unfinished auction" = **poor high/low** (no tail). An LVN is an internal thin area. Different structures |
| N8 | "Automatically market go down will reach LVN, once reach LVN, market will go up" | LVN as **magnet, then support** | Deterministic wording; contradicts the "LVN = fast traverse" reading (§2.1) |
| N9 | ORB → IVB | IVB refines ORB, probably by adding a **volume condition** to the breakout | "IVB" has **no standard definition**. TradingView indicators use it for "Initial *Value* Breakout" (the initial-session value area) or as an ORB projection tool. You need to pin down which you mean |

---

## 2. The trading framework: an explanation connecting the disciplines

### 2.1 Auction theory, Market Profile and Volume Profile

- **Market as auction (PRAC, from Steidlmayer S46 and Dalton S42).** Price moves to *advertise* for counterparties.
  - When price finds two-sided trade, time and volume accumulate. This is **acceptance**, forming **value**.
  - When it does not, price moves away quickly. This is **rejection**, leaving **tails** or **single prints**.
- **Balance vs imbalance:**
  - *Balance:* rotation inside a range. Responsive traders fade the edges.
  - *Imbalance:* initiative traders move price to a new area, and value migrates.
  - Your two trades (N5, N6) are respectively a balance trade and an imbalance trade.
- **Value Area:** the price range holding about 70 % of volume (or of TPOs) around the POC (MECH as a definition, EQ-014; the 70 % convention is PRAC, S42/S45; S46 uses 68 %).
  - The "one standard deviation" analogy is a heuristic. Real profiles are often bimodal (T1: 23–43 % of futures daily profiles).
- **POC:** the price with maximum volume. It is an argmax, so it is **unstable** and jumps between modes (NEXA-EV: proxy POC fails on 47–62 % of bimodal days, T1).
- **HVN / LVN:** local maxima and minima of the smoothed volume-at-price density (EQ-012/013).
  - **Reading A (PRAC, Dalton/Steidlmayer):** HVNs are areas of agreement that slow price. LVNs are areas of disagreement that price traverses quickly. Mid-profile single prints mean "rapid directional movement".
  - **Reading B (PRAC, Trader Dale S49 and others):** LVNs (or HVNs) are support/resistance where price reacts. **Your note N8 is Reading B.**
  - **EMP context:** Kavajecz & Odders-White (2004) find that support/resistance levels coincide with **peaks in limit-order-book depth**, which gives a mechanism by which *some* levels attract liquidity. That is about the order book, not about traded-volume nodes. **There is no peer-reviewed test of LVN behaviour in FX or gold that I am aware of.**
- **Initial Balance (IB):** the first-hour range (pit-era convention). **Range extension:** trading beyond the IB.
  - Day types (normal, normal-variation, trend, neutral, double-distribution) are defined from IB and extension (PRAC, S42/S46). NEXA has already codified them (EQ-016–018).
- **Unfinished auction / poor extremes (PRAC):**
  - A high or low with multiple TPOs at the extreme and no single-print tail is "unfinished"; practitioners expect a revisit.
  - "Excess" (a tail) marks a completed auction.
  - The footprint analogue (S44 "unfinished business": non-zero bid volume at a bar's high) needs trade-side data.

### 2.2 Order flow

| Concept | Definition | Measurement needed | Evidence status |
|---|---|---|---|
| Aggressor volume | Volume executed by market orders hitting the bid (sell) or lifting the offer (buy) | **Trade-by-trade prints with aggressor flag** (exchange MBO/trades) or Lee–Ready classification against quotes | MECH |
| Delta / CVD | Ask-volume − bid-volume per bar / cumulated | As above | MECH. S44 even mis-defines it as a *sum* |
| Delta profile | Delta per price level | As above | MECH |
| Footprint | Bid × ask volume per price per bar | As above | MECH display |
| Imbalance / stacked imbalances | Diagonal Ask(p) ≥ k·Bid(p−1 tick); k = 300 % by convention; ≥ 3 stacked | As above | **PRAC: the 300 % is a display default** (S44), with no justification |
| Absorption | Large aggressive volume with little price progress (passive liquidity absorbs it) | Volume + range (unsigned version computable); signed version needs aggressor data | Unsigned version = "effort vs result" (Wyckoff, S40; EQ-006/039) |
| Exhaustion | Diminishing aggressive volume at an extreme | Signed or unsigned volume series | PRAC |
| Trapped traders | Aggressors at an extreme who end up offside after reversal | Signed volume at the extreme + subsequent price | PRAC; mechanism plausible (forced exits) |
| Big trades | Unusually large individual prints | Trade sizes (prints) | **EMP caution:** informed traders tend to **split** orders. Barclay & Warner (1993) find most cumulative price change comes from **medium-size** trades ("stealth trading"); Chakravarty (2001) traces it to institutions. Large prints are often hedges, blocks, spreads or **roll** trades |
| Liquidity sweep / stop run | Price pushes beyond an obvious level, triggers stops, reverses | Price only (definable from bars); stop clustering is the mechanism | **EMP mechanism:** Osler (2003, JF) — FX take-profit orders cluster *at* round numbers; stop-loss orders cluster *just beyond* them, producing reversals and accelerations (price cascades, NY Fed SR 150) |
| Order-flow impact | Signed flow moves prices (linear at short horizons) | Signed flow | **EMP:** Evans & Lyons (2002), FX interdealer order flow explains a large share of daily exchange-rate changes; Cont, Kukanov & Stoikov (2014), order-flow imbalance at the best quotes explains short-horizon price changes almost linearly; Kozhan, Moore & Payne (2018, S51), limit-order flow carries information too. **This is mostly contemporaneous explanation, not forecasting** |
| Depth / order book | Resting limit orders by price | Market-by-price (MBP) or market-by-order (MBO) feeds | MECH. Pepperstone broker DOM (XAU depth 10) is the *broker's* LP book, not an exchange book |

**Critical point (EMP + NEXA-EV):** the academic order-flow literature shows **contemporaneous** association (flow and price move together) much more robustly than **predictive** power at the minutes-to-hours horizon of a retail EA after costs. A footprint signal that "confirms" a breakout is largely *describing* the breakout.

The honest research question is narrower: **does flow measured up to the decision bar's close add predictive information about the next N bars, beyond price alone, net of costs?** That is HYP-022's WHERE/WHEN decomposition (EQ-032).

### 2.3 Options flow and gamma

- **Definitions (MECH):** delta, gamma, theta, vega; open interest (OI); implied volatility (IV).
- **Dealer gamma exposure (GEX)** = Σ over strikes of OI × Γ × contract multiplier × S², with a **sign assumption** about who is long or short each option (EQ-027).
- **Mechanism (EMP):**
  - If dealers are net **short gamma**, delta-hedging *amplifies* moves; if **long gamma**, hedging *dampens* them.
  - Baltussen, Da, Lammers & Martens (2021, JFE) link **market intraday momentum** (the rest-of-day return predicts the last-30-minute return, across 60+ futures) to gamma-hedging demand.
  - Ni, Pearson & Poteshman (2005, JFE) document **pinning**: stock prices cluster at strikes on expiration dates for stocks with heavily traded options.
- **Practitioner constructs (PRAC):** call wall, put wall, gamma flip, "max pain". These are derived from OI with a dealer-sign assumption. S53 rebuilds GEX from public data; **S54 shows the sign of dealer gamma is not identified from OI alone**: customer and dealer sides cannot be separated without signed transaction data.
- **Relevance to NEXA (HYP, critical):**
  - **Gold:** spot XAU is driven by an OTC market plus COMEX futures. GLD options are a *derivative of a derivative*, with a share-of-market too small to plausibly move spot gold. S53 itself rejects ETF proxies.
  - **FX majors:** the options market is overwhelmingly **OTC** (interbank). CME FX options and FXE/FXB/FXY ETF options are a small sliver.
    - FX practitioners do watch large OTC **expiries at the 10:00 New York cut** as potential pins/magnets (PRAC). Public US-reported swap data (DTCC SDR) is a *candidate* source to investigate later. It is not available now.
  - **Conclusion:** options/GEX can at best be a **context variable for gold**, and only if COMEX OG options OI is acquired. For FX it is close to irrelevant with any data we could plausibly get. Priority: **last**.

### 2.4 Volatility and breakouts

- **Realised vs implied volatility (MECH).** NEXA can measure realised volatility well (T2).
  - HAR is the best-measured daily forecaster but does **not** significantly beat ATR(7) (NEXA-EV, T2).
  - Implied volatility for gold/FX is available only as a weak ETF-option proxy.
- **Volatility clustering and mean reversion (EMP, well-established):**
  - Compression tends to be followed by expansion in *magnitude* (HYP-019). That says nothing about *direction*.
  - **A breakout strategy's edge must come from direction, not from the fact that ranges expand.**
- **ORB literature:**
  - Crabel (1990) is the classic practitioner source (PRAC).
  - Zarattini & Aziz (2023, SSRN): 5-minute ORB on QQQ, 2016–2023, profitable in backtest, mainly with leverage.
  - Zarattini, Barbon & Aziz (2024, SSRN): "Stocks in Play" (high relative volume) ORB, reported Sharpe 2.81 in backtest.
  - **Caveats:** single-author-group, non-peer-reviewed backtests on **US equities with a true exchange open**. FX has no single open, and gold's "open" is ambiguous (Globex vs COMEX day session). **Transfer to NEXA's instruments is an open question**, not an assumption.
  - The "Stocks in Play" relative-volume filter is the closest literature analogue to your **IVB** idea: breakouts filtered by abnormal volume.
- **Intraday momentum (EMP):** Gao, Han, Li & Zhou (2018, JFE), "Market intraday momentum": the first half-hour return predicts the last half-hour (SPY). Baltussen et al. (2021) generalise to futures (§2.3).
- **Volatility-adjusted stops (NEXA-EV):** stops expressed in σ units make outcomes comparable across days. Commission-in-R falls as D grows (HYP-024). **Structural stops (bubble/VAL) must be checked against σ:** a stop at 0.1σ is noise-dominated and cost-dominated.
- **Barrier mathematics (MECH, EQ-024/034):** with driftless price, the probability of hitting target U before stop D is **D/(U+D)**.
  - Your VAL→VAH long with a tight stop just below VAL has a *low* hit-rate requirement and a *high* payoff.
  - **Its zero-skill baseline is not 50 %; it is D/(U+D).** Any claimed win-rate must be compared with that, not with 50 %.

### 2.5 Trade validation logic

- **Independent confirmations, not double counting.** VA edges, LVNs, POC and HVNs are all functionals of **the same** volume-at-price density. "Price at VAL *and* at an LVN *and* below POC" is often **one** observation, not three.
  - Delta proxies (tick-rule f30, BVC) are functions of the **same bar's return**, so their same-bar correlation with that return is mechanical (03 §4.3).
  - Only **lagged** or structurally independent measures (time-of-day, a higher-timeframe value relationship, futures true volume vs spot price) count as additional evidence.
- **NO TRADE must be the default output.** Every stage below lists its own NO TRADE conditions. The system acts only if every stage passes **and** the pre-registered, validated expectancy after costs is positive (EQ-025/033).

---

## 3. Structured decision framework (your five questions, made measurable)

Pipeline: **Context → Location → Price response → Order-flow evidence → Trade hypothesis → Confirmation → Risk/reward → Risk approval → Execute or NO TRADE.**

**Conventions**
- Every input is causal: computed only from bars closed by `decision_ts` + Δ (NEXA decision clock, 03 §3).
- σ_d is the prior-20-day daily return SD, the unit for distances.
- "Profile" means volume at price:
  - spot tick volume (PROXY; validated for XAU/EUR/JPY, **not GBP**, T1);
  - or CME futures volume mapped by the causal basis (TRUE; FX only for the price map, since the gold map failed HYP-034).

### Stage 1: CONTEXT. "Is the market balancing or trending, and is today normal?"

| Item | Specification |
|---|---|
| Question | Which regime holds: **balance** (rotational), **imbalance** (directional), or **abnormal** (event/illiquid)? |
| Inputs | Prior 1–5 session profiles; today's developing profile; M1 bars; calendar (news); session clock (DST-aware) |
| Features | **Value relationship:** today's developing value vs yesterday's (overlapping / higher / lower; S42). **Rotation count** (EQ-018). Efficiency ratio and variance ratio (EQ-020/021). **Compression ratio** (EQ-019). σ̂ (HAR/ATR7). **IB width percentile** (EQ-016). News window. Spread state. **TVPC** (proxy-profile confidence, T1) |
| Interpretations | Overlapping value + low efficiency ratio + rotations ⇒ balance. Value migrating + high efficiency ratio + IB extension ⇒ imbalance |
| Supports a trade | The regime label matches the setup family: a **rotation** setup (H-03a) only in balance; a **breakout** setup (H-03c, H-01) only when imbalance is emerging or the volatility state allows expansion |
| Invalidates | News window (existing NEXA news gate); thin/abnormal session; **TVPC low** (the proxy profile is unreliable that day: wide range / bimodal); GBPUSD profile-based setups (proxy rejected) |
| False signals | Regime labels from the *same* bars used for the entry (circular); a regime "change" at the open caused by the overnight gap |
| Confidence limits | Regime classification is noisy. HMM / Markov persistence (HYP-020) is **untested** |
| Test | Regime persistence and conditioning test HYP-020; conditional outcome tables by regime; never selected post hoc |

### Stage 2: LOCATION. "Where is price relative to value and structure?"

| Item | Specification |
|---|---|
| Question | Is price at a **pre-defined** reference location: VAH, VAL, POC, an LVN/HVN, the IB high/low, the opening-range high/low, a prior poor high/low? |
| Inputs | Causal profiles (prior session / developing / composite), TPO profile, opening range, IB |
| Features | Signed distance to each reference level in σ_d units. **Which** profile produced the level. Level "age". Level confluence count, **de-duplicated** (levels from one density count once) |
| Supports | Price within a pre-registered band (e.g. ±0.1σ_d; to be justified by noise-scale sensitivity, see §6) of a level that belongs to the setup |
| Invalidates | No reference level within band (⇒ NO TRADE); level computed from an unreliable proxy profile (low TVPC); for gold, futures-derived levels without an intraday basis update (HYP-034 failed for XAU) |
| False signals | "Confluence" made of correlated levels; levels redrawn after the fact (developing profiles change; freeze the level at decision time) |
| Confidence limits | Proxy VA bounds are good (median Jaccard 0.71–0.82). **Proxy POC is fragile** |
| Test | Placebo levels (same-distribution levels from a different day's profile) vs real levels: does outcome differ? (15 §2) |

### Stage 3: PRICE RESPONSE. "What did price do at the location?"

| Item | Specification |
|---|---|
| Question | **Acceptance** (time and volume building beyond the level), **rejection** (a fast move away), or **unresolved**? |
| Inputs | M1 bars after the first touch |
| Features | Time beyond the level (minutes, or TPO periods: Dalton's "two 30-min periods" acceptance convention, PRAC). Closes beyond. Excursion beyond, in σ. Speed of return. Tail formation (single prints). **Breakout bar range / σ_h** |
| Supports | The response matches the setup: a rotation long needs **rejection of VAL** (a quick return above VAL / above the cluster); a breakout short needs **acceptance below VAL** |
| Invalidates | Response contradicts the setup; response ambiguous within the pre-registered window (⇒ NO TRADE) |
| False signals | One wick through a level (a stop run, Osler 2003); acceptance judged with hindsight |
| Confidence limits | Acceptance thresholds are conventions. They must be pre-registered and sensitivity-tested |
| Test | Conditional continuation/reversal rates by response class vs unconditional base rates (HYP-007/009/012-style) |

### Stage 4: ORDER-FLOW EVIDENCE. "Did volume or flow behave as the hypothesis requires?"

| Item | Specification |
|---|---|
| Question | Is there **independent** evidence of participation: a volume anomaly, absorption, delta? |
| Inputs | Futures 1-min volume and transactions (TRUE, unsigned, about 2 y); spot tick volume (PROXY, 9 y); f30/f31 quote-direction proxies (live only); **no aggressor data** |
| Features | **Relative volume** RVOL = V / hour-of-week baseline (EQ-005). **Average trade size** V/N z-score (futures). **Effort–result residual** (EQ-006/039; absorption, unsigned). **Lagged** BVC delta proxy (EQ-009; exploratory only) |
| Supports | Volume anomaly at the location (the "bubble" proxy); absorption signature (high volume, low range) at a VA edge; RVOL elevated on the breakout bar (IVB) |
| Invalidates | Required evidence absent; activity proxy unreliable (TVPC_activity is *not* predictable, T1) |
| False signals | **Roll-date volume** (T1: roll windows drop the tick↔futures correlation to 0.16–0.37); spread/calendar trades; block trades; same-bar delta proxies (circular) |
| Confidence limits | **No true delta, footprint, imbalance or "big trade" prints exist in NEXA's data.** Everything here is unsigned or proxy |
| Test | Nested tests: does the flow feature add to a location+response model? (HYP-022, EQ-032) Proxy-swap test (futures vs tick volume) |

### Stage 5: TRADE HYPOTHESIS. "Which pre-registered setup is this?"

- Map the stage 1–4 outputs to **exactly one** registered setup ID (H-01…H-12 in §5). If none matches ⇒ NO TRADE.
- **Invalidation:** two setups imply opposite directions ⇒ NO TRADE.

### Stage 6: CONFIRMATION. "Has the trigger fired, by its exact rule?"

- **Trigger:** e.g. "M1 close above the cluster high". Defined in §5 per setup. Fired on the first tick after the decision bar closes (NEXA convention).
- **Invalidation:** the trigger did not fire within the pre-registered window ⇒ NO TRADE (no chasing).

### Stage 7: RISK/REWARD. "Is the geometry worth it after costs?"

| Item | Specification |
|---|---|
| Inputs | Stop D and target U per setup rule; σ̂; cost c = commission + spread + expected slippage (S14 fills when available) |
| Features | **U/D**; D/σ_d; **c/D (cost in R)**; driftless baseline P = D/(U+D); validated hit rate p̂ and its CI |
| Supports | E[R_net] = p̂·U/D − (1 − p̂) − c/D > κ (a pre-registered margin), using the **validated** p̂ for this setup, not a guess |
| Invalidates | D below a minimum in σ units (noise-dominated); c/D above a limit (cost-dominated, cf. the 0.245R finding); target beyond the next opposing level |
| Test | HYP-024 (cost-in-R vs stop width); barrier-law test of realised vs D/(U+D) |

### Stage 8: RISK APPROVAL

**The deterministic NEXA Risk Engine decides, unchanged** (fail-closed): risk ceiling, C4 daily budget, exposure and correlation caps, drawdown, survival pause, news gate. The AI or Judge cannot override it.

### Stage 9: EXECUTE or NO TRADE

- Execution follows existing S14 behaviour (market/IOC, post-fill hard-ceiling guard, signed slippage logging).
- Everything is journalled in Trade DNA, **including NO TRADE decisions and the stage that blocked them**. Today that requires schema v1.1 (not approved).

---

## 4. Technical capability matrix (from NEXA's existing data only)

### 4.1 Concept-by-concept

**Status codes**
- **CALC:** computable now from data on hand.
- **PROXY:** only an approximation; error measured where noted.
- **NO:** not measurable with current data.

| Concept | Status | Source | Notes / evidence |
|---|---|---|---|
| OHLC, sessions, opening range, IB | **CALC** | MT5 M1 2017→2026 (4 symbols + XAG); Massive futures 1-min (2 y) | Session anchors must be pre-registered (FX has no single open) |
| TPO profile, poor highs/lows, single prints, excess | **CALC (exact at 1-min resolution)** | M1 bars | Unfinished auctions fully testable |
| Volume profile, VAH/VAL/POC, HVN/LVN (spot) | **PROXY** | Pepperstone tick volume | T1: VA reliable for XAU/EUR/JPY (POC within 0.25σ on 67–75 % of days); **GBP rejected**; POC fails on bimodal days |
| Volume profile (futures, true volume) | **CALC** (2 y, 1-min) | Massive GC/6E/6B/6J aggregates; data cached in `validation/data/` (daily profiles + hourly) | Intra-bar volume distribution assumed (typical price); roll handling required |
| Mapping futures levels to spot | **CALC (FX) / FAILS (gold)** | Causal basis map | T1 HYP-034: ≤ 0.1σ on 97–99.9 % of FX hours; gold 88 % (p95 0.24σ) |
| Relative volume (RVOL), volume anomalies | **CALC (futures) / PROXY (spot)** | Futures volume; tick volume | De-seasonalised tick↔futures r ≈ 0.55–0.67 ex-roll; tick volume compresses surges |
| Average trade size (V/N) | **CALC** (futures, 1-min) | Massive `transactions` | The closest available proxy to "big trades", but per minute, not per print |
| Individual big prints ("bubbles") | **NO** | Needs trades | Massive futures trades NOT_ENTITLED |
| Aggressor side / delta / CVD / delta profile | **NO** (true); **PROXY** (BVC on futures bars, tick rule on spot quotes) | — | Proxies are unvalidated, partly circular, and f30/f31 are non-reproducible offline |
| Footprint, imbalances, stacked imbalances, unfinished business (footprint) | **NO** | — | — |
| Absorption (unsigned) | **PROXY** | Volume + range | Signed absorption: NO |
| Order book / depth / iceberg detection | **NO** historically; broker DOM for XAU could be logged forward (not exchange data) | — | — |
| Liquidity sweeps / stop runs | **CALC** (price-defined) | M1 + existing f32–f46 liquidity features | Existing NEXA liquidity features exist; their rule set is part of the negative cap-neutral result |
| Realised volatility, HAR, ATR | **CALC** | M1 | T2 done |
| Implied volatility (gold/FX) | **PROXY (weak)** | GLD/FXE options aggregates (Massive) + local Black–Scholes inversion | Stale prints, American exercise, ETF not OTC |
| Options volume by strike | **CALC (ETF only, unsigned)** | Massive options aggregates | No OI |
| Open interest, Greeks from the provider, call/put walls, GEX, gamma flip | **NO** (Massive: NOT_ENTITLED). **UNVERIFIED** via the second connector (§4.3) | — | Even with OI, the dealer sign is not identified (S54) |
| COMEX gold options (OG), CME FX options | **NO** | — | Not offered by Massive's futures API |
| Cross-asset (USD basket, ES, Treasuries) | **CALC** | MT5, Massive | — |
| Own execution (slippage, latency) | **CALC prospectively** | S14 demo Trade DNA, tick logger | **The demo has been stopped since 2026-10-05 06:59 MYT**: about 2 h of data, 0 fills |

### 4.2 Integrations actually configured (inspected, not called)

- **Massive (connector `8d797fad…`):** entitlements were **measured on 2026-10-04** (03_DATA_AVAILABILITY_MATRIX):
  - aggregates only, about 2-year rolling window;
  - trades, quotes, options snapshot/OI/Greeks and indices are NOT_ENTITLED.
  - **Rate limit about 5 calls/min.**
- **meta-trader-mcp:** the only MCP server in `~/.claude.json` for this project path. It is read-only market data and account access to the local MT5.
  - **Trap:** querying it while the terminal is down **auto-launches MT5** and can restart the live EAs (2026-10-05 incident).
  - It gives broker quotes, not exchange trades.
- **Second financial-data connector (`191d8dde…`), tool names matching the Alpha Vantage API:**
  - Advertises `HISTORICAL_OPTIONS`: "full historical options chain … Implied volatility (IV) and common Greeks"; `REALTIME_OPTIONS`; `HISTORICAL_PUT_CALL_RATIO` (from 2008); FX intraday; and more.
  - **US-listed equities/ETFs only** (GLD, SPY, FXE…), not COMEX or CME options.
  - **Entitlement UNVERIFIED and NOT CALLED** (your instruction). Premium options endpoints often need a paid key.
  - **Whether OI is included per contract is not stated in the tool description.** A single entitlement probe, after your approval, would settle it.

### 4.3 What that connector could and could not change

| If it delivers… | It enables | It still does not enable |
|---|---|---|
| Daily historical GLD chains with OI, IV, Greeks | A GLD-only GEX/wall reconstruction (S53 method) as a **context variable for gold**; IV term structure / skew for gold | The dealer sign (S54); COMEX OG positioning; any FX options intelligence; intraday option flow |
| Put/call ratios | Sentiment context (GLD, FXE) | Positioning; strike-level information |

---

## 5. Ranked catalogue of testable hypotheses

**Ranking score** = feasibility (data on hand?) × expected information value × testability (clean null?).

**Rules for every hypothesis**
- Registered under a new family prefix **OF-** (to be added to `14_HYPOTHESIS_REGISTRY.md` only after your review).
- Cross-referenced to existing HYP IDs where they overlap.
- **No parameter is fixed here.** Where a number appears, it is a *default to pre-register with a sensitivity grid*, counted as trials in the multiple-testing budget (15 §4).
- **Common methodology** (§6) applies to all.

| Rank | ID | Hypothesis (short) | Data | Feasibility | Value | Overlap |
|---|---|---|---|---|---|---|
| 1 | **OF-01** | Opening-range breakout continues more often than a geometry-matched null, net of costs | M1 9 y + futures 2 y | High | High (literature prior exists; cheap) | new (ORB) |
| 2 | **OF-02** | Volume-confirmed ORB ("IVB") beats plain ORB (nested) | Futures volume (TRUE) / tick volume (PROXY) | High | High | HYP-002 |
| 3 | **OF-03** | **Your core family:** value-area rotation / cluster-break / VAL-break trades (3 sub-setups) | Profiles (PROXY spot; TRUE futures for FX) | Medium–High | **Highest relevance to you** | HYP-007, HYP-015 |
| 4 | **OF-04** | Poor highs/lows (unfinished auctions) are revisited more often than tailed extremes | M1 TPO (exact) 9 y | Very high | Medium | HYP-012 adjacent |
| 5 | **OF-05** | LVN behaviour: fast traverse (A) vs reaction/support (B), your N8 | Profiles | High | High (resolves a direct conflict) | HYP-004/005/006 |
| 6 | **OF-06** | Failed breakouts beyond VA / OR edges (stop runs) revert to value | M1 | High | Medium–High | Osler mechanism |
| 7 | **OF-07** | IB width predicts range extension / day type | M1 | High | Medium (context feature) | HYP-011, HYP-013 |
| 8 | **OF-08** | "Large-trader activity" proxy: anomalous futures volume / trade size at a price acts as a level | Futures 1-min V, N (2 y) | Medium | Medium | new |
| 9 | **OF-09** | Unsigned absorption at VA edges precedes reversal | Volume + range | Medium | Medium | HYP-003 |
| 10 | **OF-10** | Higher-timeframe value relationship (migration) improves OF-01/03 | Profiles | High | Medium (filter) | S42 |
| 11 | **OF-11** | Proxy delta confirmation adds information to breakouts | BVC / tick rule (PROXY) | Low | Low (proxy-only) | HYP-017/018/022 |
| 12 | **OF-12** | Options/GEX context (gold only) changes breakout continuation | Needs OI | **Blocked** | Unknown | HYP-025–029 |

### OF-01: Opening-range breakout (ORB)

- **Rationale:**
  - **PRAC:** Crabel's ORB; Dalton's IB.
  - **EMP-adjacent:** ORB backtests on US equities (Zarattini & Aziz 2023; with Barbon 2024); intraday momentum (Gao et al. 2018; Baltussen et al. 2021).
  - **Mechanism:** early-session order imbalance persists, and stop orders beyond the range accelerate the move (Osler 2003).
- **Data:** M1 spot (9 y, all 4 symbols); futures M1 for robustness (2 y).
- **Setup:**
  - **Session anchors, pre-registered:** London open (07:00 or 08:00 UTC: choose one, test the other as a robustness variant); New York (13:30 UTC FX / 13:20 UTC COMEX-gold day-session open); Tokyo (00:00 UTC) as exploratory.
  - **OR length** ∈ {5, 15, 30, 60} min, a pre-registered grid with the family size counted.
- **Entry:** first M1 close beyond OR high (long) / low (short) within a pre-registered window (e.g. the first 2 h after the anchor). One trade per anchor per day.
- **Invalidation:** close back inside the OR (option A: exit) or the opposite OR side (option B: the stop). Pre-register A or B.
- **Stop / target:** stop at the opposite side of the OR or at the OR midpoint, expressed and capped in σ units; target as a fixed R multiple, **or** a time exit at a session close (Zarattini-style). Grid counted.
- **Expected regimes:** trend/imbalance days. Fails in balance days and around news spikes.
- **Failure conditions:** OR width tiny relative to σ (noise); news at the anchor; FX's lack of a true open.
- **Testing:** §6 protocol.
  - **Null 1:** same geometry anchored at random intraday times.
  - **Null 2:** driftless barrier law.
  - Report hit rate vs D/(U+D).
- **Costs:** spread at the anchor time (London open spreads are tight; Tokyo wide). Commission per lot converted to R at each trade's D. Slippage from S14 fills when available; until then a stress of +0.05R and +0.10R.
- **Minimum evidence:** §6.6.

### OF-02: Volume-confirmed ORB ("IVB", your note N9)

- **Rationale:** breakouts with abnormal participation are more likely to be initiative (imbalance) than noise. The analogue is the Stocks-in-Play filter (Zarattini, Barbon & Aziz 2024).
- **Data:** futures 1-min volume (TRUE, 2 y, FX + gold); tick volume (PROXY, 9 y) as a second test (proxy swap).
- **Setup:** OF-01 plus an extra condition: **RVOL of the OR window and/or the breakout bar ≥ q-th percentile of its causal hour-of-week baseline** (EQ-005). Pre-register q (e.g. 70th/80th/90th as a counted grid).
- **Test design:** **nested.** Does adding the volume condition change net E[R] relative to OF-01 *on the same anchors*? Use a permutation test (shuffle the volume labels across days).
- **Specific risks:**
  - Roll-week volume contamination (exclude ±2 days around rolls, as T1 found).
  - Tick volume understates surges (dispersion ratio ≈ 0.6), which may blunt the filter.
- **Status of the term "IVB":** not standard. If you meant "Initial *Value* Breakout" (breakout of the *opening-period value area*), that is a separate variant (OF-02b): use the opening-window profile VAH/VAL instead of the high/low.

### OF-03: Value-area family (your core notes N2–N6)

**Common definitions (pre-register):**
- **Value:** the prior completed session profile (primary). Developing-profile and 3-day-composite as counted variants. α = 0.70 (EQ-014).
- **Balance condition:** ≥ k rotations between the inner thirds of value in the current session before the setup (EQ-018). k pre-registered with sensitivity. Plus the context gate (Stage 1).
- **"Bubble" proxy (cluster):** a 1-min futures bar, or a contiguous 3–5-bar window, whose volume is ≥ the q-th percentile of its hour-of-week baseline. Its price span is that window's [low, high]. **Unsigned.** Your "for sellers" label cannot be measured, so it is not part of the rule.

**OF-03a: rotation long ("buy above the bubble near VAL") — your N5**
- **Location:** cluster midpoint in the lower third of value (within band of VAL).
- **Trigger:** first M1 close above the cluster high.
- **Stop:** below the cluster low (variant 1) or below VAL (variant 2), whichever rule is pre-registered, plus a buffer of b·σ_h.
- **Target:** VAH (as written); POC as a counted variant (closer target, higher baseline hit rate).
- **Mirror short (OF-03a′):** cluster in the upper third near VAH, break below it, target VAL. Your notes do not mention it; **testing only one side would be a selection bias.**

**OF-03b: cluster-break plus VAL-break short — your N6**
- **Trigger:** M1 close below the cluster low **and** below VAL, with **acceptance**: ≥ m consecutive M1 closes below VAL, or the 30-min TPO convention as a variant.
- **Stop:** "at the top". Pre-register as the cluster high (variant 1) or back inside value by d·σ (variant 2).
- **Target:** the nearest causal LVN below VAL (defined in OF-05), else a fixed R.
- **Mirror long (OF-03b′):** above VAH.

**OF-03c: Value-Area Rule (S42, HYP-007).** Open outside prior value, then re-entry and acceptance inside ⇒ traverse to the other side. Included because it shares the infrastructure and is the best-known profile rule.

**For all of OF-03:**
- **Expected regimes:** 03a in balance; 03b in imbalance onset.
- **Failure conditions:**
  - low TVPC days (wide range, bimodal; T1);
  - GBPUSD (proxy rejected);
  - gold futures-derived levels (basis map failed): **use the spot tick-volume profile for gold**.
- **Costs (critical):**
  - A VAL-to-cluster-low stop on EURUSD may be only a few pips.
  - At 2.4 pips, commission alone was 0.245R in NEXA's campaign.
  - **Report the distribution of D in pips and σ, and E[R] by D bucket.** Setups with D below a pre-registered σ floor are excluded *ex ante*, not after seeing results.
- **Nulls:**
  - **(i) Placebo cluster:** a random high-volume bar elsewhere in value, same geometry.
  - **(ii) Placebo value:** the profile from a different day, shifted to today's price.
  - **(iii)** Driftless barrier law.
- **Minimum evidence:** §6.6, per sub-setup **and** mirror.

### OF-04: Unfinished auctions (poor highs/lows) — your N7, properly defined

- **Rationale (PRAC, S42/S46):** a poor extreme (≥ 2 TPO periods at the session high or low, no single-print tail) signals an incomplete auction; the market tends to "repair" it.
- **Data:** M1 → 30-min TPO (exact). 9 years, 4 symbols. Very cheap.
- **Setup:** classify every session extreme as poor or excess (tail ≥ t single-print ticks; t pre-registered with sensitivity).
- **Measurement (a base-rate study first, not a trade):** P(revisit within N sessions | poor) vs P(revisit | excess), with distance-to-extreme in σ controlled. The controls matter: poor highs are often *closer* to the close, so naive revisit rates are confounded.
- **Trade version (only if the base rate differs):** a target or magnet for other setups (e.g. extend OF-03 targets to a poor extreme), not a standalone entry.
- **Null:** distance-matched random prior-session prices.

### OF-05: LVN behaviour — competing hypotheses (your N8 vs auction theory)

- **Definition (pre-register):** LVN = a local minimum of the Gaussian-smoothed volume-at-price density (EQ-012/013; bandwidth h in σ units, pre-registered grid), between two HVNs, with depth ratio ≤ r. Built from the causal prior-session or composite profile.
- **H-A (auction reading):** price **traverses** LVNs faster than HVNs. Measure time-to-cross per σ (survival model, HYP-004).
- **H-B (your reading):** price that falls *to* an LVN below value **reverses up**. Measure P(+x·σ before −x·σ | first touch of the LVN from above) vs the placebo level and vs the barrier law at symmetric barriers (50 %).
- **Why this matters:** OF-03b *targets* the LVN (it assumes price reaches it, consistent with H-A), while your N8 *buys* there (H-B). **If H-A holds, buying at LVNs is fading a low-friction zone.** The test resolves which of your two notes to keep.
- **Data caveat:** LVN location is less reliable on the tick-volume proxy than VA bounds. Gate by TVPC and repeat on futures profiles (FX).

### OF-06: Failed breakout / stop-run reversal

- **Rationale (EMP mechanism):** stop-loss orders cluster beyond obvious levels (Osler 2003). A brief excursion that triggers them and then fails leaves trapped breakout traders.
- **Setup:** excursion beyond VAH/VAL, the OR high/low, or the prior-day high/low by ≤ e·σ, then an M1 close back inside within w minutes.
- **Entry:** on re-entry. **Stop:** beyond the excursion extreme. **Target:** POC / the opposite edge.
- **Note:** NEXA's existing liquidity-sweep features (f32–f46) implement a related concept inside the rule set that tested negative (−0.318R). OF-06 must be defined **independently** and compared with that existing implementation, not assumed new.

### OF-07: Initial balance width → range extension (context feature)

- **Existing:** HYP-011 and HYP-013.
- **Purpose here:** a **Stage-1 context variable** for OF-01/03 (narrow IB ⇒ higher extension probability, PRAC). Test as a conditioning variable; report the base rates first.

### OF-08: "Large-trader activity" proxy (the measurable part of your BIG TRADES page)

- **Definition:** a futures 1-min bar with **average trade size V/N** and/or **volume** in the top q-th percentile of the causal hour-of-week baseline. It records an *activity anomaly at a price*, unsigned.
- **Hypotheses:**
  - **(a)** These prices act as reaction levels on first retest (S49 "volume accumulation", made causal: the level is defined only from data before the retest).
  - **(b)** A break away from the anomaly level continues (your N5 logic) more than placebo.
- **Hard limits:**
  - No individual prints, no side.
  - **Rolls, spread trades and block trades contaminate V/N.** Exclude roll windows; CME block trades are reported separately, and Massive aggregates may include them (unverified).
  - Barclay & Warner (1993): informed flow is often medium-sized and split, so "big" ≠ "informed".

### OF-09: Unsigned absorption at value edges

- **Definition:** effort–result residual (EQ-006/039). High volume relative to baseline with small |return| / range relative to σ_h, at a VA edge.
- **Hypothesis:** absorption at VAL (VAH) precedes up (down) moves more than at placebo locations (HYP-003).
- **Note:** this is the only "order-flow" concept testable now without aggressor data. The signed version must wait for trade data.

### OF-10: Higher-timeframe value relationship (filter)

- **Definition:** today's developing value vs the prior day's value: higher, lower, overlapping, inside or outside (S42). The weekly composite as a variant.
- **Use:** a Stage-1 filter for OF-01/03. Test as an **interaction** (does the setup's net E[R] differ by relationship?), with the multiple-testing count.

### OF-11: Proxy delta confirmation (low priority)

- **Definition:** the **lagged** BVC delta on futures 1-min bars (EQ-009) over the K bars before the trigger.
- **Hypothesis:** adds to OF-01/03.
- **Expectation:** weak. The proxy is a transformation of returns (03 §4.3), so mostly redundant with price.
- **When it becomes worthwhile:** only with true aggressor data (§7).

### OF-12: Options/GEX context (blocked)

- **Hypothesis:** gold breakout continuation (OF-01/03b) differs when GLD-derived (or, better, COMEX-OG-derived) dealer gamma is negative vs positive (Baltussen et al. mechanism).
- **Blockers:** OI (Massive NOT_ENTITLED; second connector unverified); sign identification (S54); ETF-to-spot relevance.
- **Status:** register as BLOCKED. Run a feasibility probe only after your approval.

---

## 6. Validation methodology (applies to every OF hypothesis)

This is built on `15_VALIDATION_FRAMEWORK.md` and the T1/T2 practice already used.

1. **Pre-registration before any outcome is computed.**
   - One document per hypothesis family, recording:
     - definitions, parameter grid (each cell counted as a trial), session anchors, instruments, data splits;
     - nulls, primary metric, decision rule, and the minimum σ floor for D.
   - SHA-256 recorded in `PREREG_HASHES.txt`. Deviations disclosed, never silent.
2. **Splits.**
   - **Spot M1 (9 y):** discovery 2017–2022 → validation 2023–2024 → holdout 2025-01 → 2026-09.
     - Disclosure: the V2 campaign *excludes* 2025–2026 for V2 only. These OF tests are a separate programme, but the overlap must be stated.
     - **2027 data needs your approval** (reserved as V2 OOS).
   - **Futures (2 y):** discovery 2024-10 → 2025-09; holdout 2025-10 → 2026-09.
     - Disclosure: profile *proxy* quality was already measured on this holdout in T1. Trade outcomes were not.
   - **Prospective holdout:** 2026-10 onward, accumulated without looking.
3. **Primary metric:** net expectancy in R per trade, E[R_net] (EQ-025):
   - commission at the account's actual rate (verify from the first S14 CLOSE row);
   - spread at entry/exit time;
   - slippage stress +0.05R / +0.10R until S14 fills exist;
   - swap where positions cross rollover.
4. **Nulls (mandatory):**
   - **(i)** Driftless barrier law: realised P(U before D) vs D/(U+D).
   - **(ii)** Geometry-matched random entries: same instrument, time-of-day, D and U.
   - **(iii)** Placebo levels: another day's profile, or random high-volume bars.
   - **(iv)** For nested claims (volume or flow adds value): a permutation of the added feature.
5. **Statistics:**
   - Day-block bootstrap CIs.
   - Benjamini–Hochberg q = 0.10 within each family.
   - Deflated Sharpe ratio counting all trials (Bailey & López de Prado 2014).
   - Per-symbol results; no pooling that hides a symbol's sign.
6. **Minimum evidence to accept (the existing Gate 8 conventions):**
   - ≥ 200 trades in the evaluated split;
   - 95 % CI lower bound of net E[R] > 0 after the +0.05R stress;
   - beats every null (i–iii);
   - same sign in discovery and holdout;
   - consistent across years (no single year > 50 % of total);
   - survives ±25 % parameter perturbation;
   - for proxy-based features: a **proxy swap** (futures vs tick volume) with the same sign.
7. **Promotion:** passing makes a setup a *research candidate* (RESEARCH_GATE G4→G5). Production requires walk-forward, a robustness battery, the S14 forward-check evidence, a written proposal and **your explicit approval**. Nothing auto-promotes.

---

## 7. Missing data requirements (identified, not collected)

| # | Data | Unblocks | Candidate source (UNVERIFIED unless noted) | Priority |
|---|---|---|---|---|
| 1 | **CME trade prints with aggressor side** for GC, 6E, 6B, 6J (tick or MBO) | True delta/CVD, delta profile, footprint, imbalances, individual big prints, signed absorption | CME DataMine / MDP 3.0 market-by-order; third-party vendors (e.g. Databento). **Massive futures trades: NOT_ENTITLED (measured)** | High (only if OF-01/03/09 show promise first) |
| 2 | **CME top-of-book / depth (MBP)** | Order-book imbalance (Cont et al. OFI), iceberg/absorption with depth, liquidity at levels (Kavajecz & Odders-White mechanism) | Same vendors | Medium |
| 3 | **Futures history beyond 2 years** (1-min aggregates) | Longer samples for OF-02/03/08 on true volume | Massive keeps a rolling 2 y only. **Cache before months drop out** | Medium–High (time-sensitive) |
| 4 | **COMEX OG options OI, volume, IV** (daily) | Gold GEX/walls (OF-12) | CME DataMine | Low |
| 5 | **GLD option chains with OI/Greeks** | ETF-based gold gamma proxy | Second connector advertises chains + IV + Greeks (**unverified**); Massive has no OI | Low |
| 6 | **OTC FX option expiries / notional by strike** | FX "expiry magnet" context | DTCC SDR public dissemination (US-reported only) | Low |
| 7 | **Spot tick history (forward)** | Microstructure, quote-intensity features | NEXA TickLogger: **needs the S14 demo running again** | Medium (free; blocked by the runtime outage) |
| 8 | **Own fills** (slippage, latency) | Realistic costs for every OF test | S14 demo forward check: **stopped since 2026-10-05** | **High** (free) |
| 9 | Broker DOM (XAU depth 10), logged forward | Broker-book imbalance (not exchange) | MT5 `MarketBookGet`; would need a new logger (approval) | Low |

---

## 8. Integration map (proposed; nothing implemented)

| NEXA component | Responsibility in this framework | What must NOT change |
|---|---|---|
| **Market Intelligence** (research tier now; later live feature modules) | Compute causal state:<br>• **Stage 1:** regime, value relationship, rotations, IB, σ̂, TVPC.<br>• **Stage 2:** levels (VA, POC, LVN/HVN, OR, IB, poor extremes, clusters) with source tags (TRUE / PROXY) and confidence.<br>• **Stage 3–4:** response class, RVOL, V/N anomaly, absorption residual. | Frozen f00–f47 / schema v1.0 / `PackFeatures()`. New features enter only via an approved append-only schema v1.1 |
| **Research Engine** (`research/`, registries) | Pre-registration, data splits, nulls, statistics (Gate 8/12), the OF-family registry, promotion status (RESEARCH_GATE G0–G7) | V2 / 8E registries (V2 frozen; 8E closed). Never pass flags to `freeze_*.py` |
| **NEXA Judge** | Maps the state to **one** validated setup, checks the trigger, computes E[R_net] from **validated** p̂ and current costs. Default output NO TRADE. AI may *propose* hypotheses and *explain* evidence; it **cannot authorise** | Judge outputs are advisory to the Risk Engine. No unvalidated setup is ever eligible |
| **Deterministic Risk Engine** (`NEXA_Risk.mqh` a43d8328) | Final authority: risk ceiling, C4 daily budget, exposure and correlation caps, drawdown, survival pause, news gate. **Unchanged** | No risk limit or semantics change |
| **Execution Engine** (S14 build ff30ac38) | Market/IOC execution, post-fill hard-ceiling guard, signed slippage logging. **Unchanged** | No execution change |
| **Trade DNA + learning/validation** | Journal every decision, **including NO TRADE and the blocking stage**, the setup ID and the state features (needs v1.1); outcome labels from fill time; feeds Gate 8, calibration and the prospective holdout | Schema v1.0 contract until v1.1 is approved |

---

## 9. Prioritised research roadmap

| Step | Work | Data | Cost | Why first |
|---|---|---|---|---|
| **0 (operational, prerequisite)** | **Restart the S14 demo yourself** (or migrate to the VPS) so the free data streams (fills, slippage, ticks) accumulate | — | — | Every cost assumption below needs real fills; stopped since 2026-10-05 |
| **1** | Pre-register **OF-04** (unfinished auctions) and **OF-07** (IB base rates) as **base-rate studies** | M1 (exact TPO) | Low | Cheapest; exact data; builds the session/anchor infrastructure everything else reuses |
| **2** | Pre-register and run **OF-01** (ORB) with full nulls and costs | M1 9 y | Low–Medium | Strongest external prior; clean null; answers whether *any* breakout logic survives NEXA's costs |
| **3** | **OF-02** (volume-confirmed ORB / IVB), nested on OF-01 | Futures volume (cached) + tick volume | Low | Direct test of your IVB idea; reuses OF-01 |
| **4** | **OF-05** (LVN competing hypotheses) | Profiles (TVPC-gated) | Medium | Decides which of your two LVN notes is consistent with data **before** building OF-03b on it |
| **5** | **OF-03** (your value-area family, both directions, all variants counted) | Profiles + futures clusters | Medium | Your core idea, now with the definitions, nulls and level behaviour established in steps 1–4 |
| **6** | **OF-06 / OF-09 / OF-10** as conditional extensions | As above | Medium | Only meaningful once a base setup shows something |
| **7** | **Data decision:** buy CME trade/aggressor data **only if** steps 2–5 find conditional structure that signed flow could sharpen | Purchase | $ | Avoids paying for order-flow data to confirm a setup with no edge |
| **8** | **OF-11 / OF-12** (true delta, GEX) | Needs §7 data | High | Last, and only with the evidence of steps 2–7 |

**What I recommend you decide after reading this:**
1. Which interpretation of the bubble (N3/N4) and stops (N5/N6) you intended.
2. Whether "IVB" means volume-confirmed ORB or Initial *Value* Breakout.
3. Approval to write the OF-04/OF-07/OF-01 pre-registrations (step 1–2). No data download is needed for those: M1 data is already on disk.

---

## 10. Weaknesses and conflicts in the framework, stated plainly

1. **Two trades in one drawing** (rotation vs breakout). Without a mechanical context gate, the same picture will be read as "buy" or "sell" after the fact.
2. **The "big trade for sellers" claim needs aggressor data that NEXA does not have.** Even with it, large prints are an ambiguous signal (EMP: stealth trading). The tradable content must survive as an *unsigned volume-cluster* rule.
3. **The LVN-reversal claim (N8) conflicts with mainstream auction theory**, and is written deterministically ("automatically", "will"). Treat it as a hypothesis with a stated competitor (OF-05).
4. **"Unfinished auction" is mislabelled** onto LVNs. In Market Profile it is a property of extremes.
5. **Stops "around VAL" sit exactly where stop orders cluster** (Osler 2003). That is the level most exposed to stop runs, which may favour OF-06 (fading the run) over OF-03a's stop placement.
6. **Hindsight bias in profile/bubble charts:** levels and bubbles look decisive after the move (S49 look-ahead caution). Every level must be frozen at decision time.
7. **Transfer risk:** the strongest ORB evidence is on US equities with a real open and "stocks in play". FX is a 24-hour, dealer-quoted market. Technical-rule profitability in FX has decayed over decades (Neely, Weller & Ulrich 2009, adaptive-markets evidence).
8. **Costs dominate small structures.** NEXA already measured a rule set whose gross was only −0.072R and whose commission turned it into −0.318R. Intraday structural trades with few-pip stops face the same arithmetic.
9. **No promise of profitability is implied anywhere in this report.** The purpose is to make your ideas *falsifiable*, so the data can decide which survive.

---

## Sources

**Repository**
- `research/intelligence/03_DATA_AVAILABILITY_MATRIX.md`, `05_OPTIONS_GEX_MODEL.md`, `11_NEW_MATHEMATICAL_CONSTRUCTS.md`, `14_HYPOTHESIS_REGISTRY.md`, `15_VALIDATION_FRAMEWORK.md`, `16_NEXA_INTELLIGENCE_ARCHITECTURE.md`.
- `validation/T1_REPORT.md`, `T2_REPORT.md`.
- `filesnexa/NEXA/research/capneutral/CAPNEUTRAL_RESEARCH_RESULTS.md`.
- Corpus notes `sources/S40_S47_S49…`, `S48_S50…`, `S51_S52…`, `S53_S54…` (S42 Dalton et al. 1993; S44/S49 Trader Dale; S46 Steidlmayer & Hawkins 2003; S51 Kozhan, Moore & Payne 2018; S53 Sen 2026; S54 Chilingarian 2026).

**Literature (checked 2026-10-11 where linked)**
- Zarattini & Aziz (2023), "Can Day Trading Really Be Profitable?", SSRN 4416622. https://papers.ssrn.com/abstract=4416622
- Zarattini, Barbon & Aziz (2024), "A Profitable Day Trading Strategy for the U.S. Equity Market", SSRN. https://ideas.repec.org/p/chf/rpseri/rp2498.html
- Baltussen, Da, Lammers & Martens (2021), "Hedging Demand and Market Intraday Momentum", *JFE* 142, 377–403. https://ideas.repec.org/a/eee/jfinec/v142y2021i1p377-403.html
- Osler (2003), "Currency Orders and Exchange Rate Dynamics", *JF* 58, 1791–1819; and "Stop-Loss Orders and Price Cascades in Currency Markets", NY Fed SR 150. https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf
- Barclay & Warner (1993), "Stealth Trading and Volatility: Which Trades Move Prices?", *JFE* 34, 281–305; Chakravarty (2001), *JFE*. https://academicnewsletter.sufe.edu.cn/info/358241
- Kavajecz & Odders-White (2004), "Technical Analysis and Liquidity Provision", *RFS* 17(4), 1043–1071. https://ideas.repec.org/a/oup/rfinst/v17y2004i4p1043-1071.html
- IVB variants (practitioner indicators, no evidence): https://mmt.gg/indicators/fourblock-ivb-52a5310b ; https://www.tradingview.com/script/e3ZnxPpk-Initial-Value-Breakout-OmegaTools/
- Poor highs/lows / unfinished auction (practitioner definitions): https://nexusfi.com/a/market-structure/single-prints-poor-highs-poor-lows-market-profile ; https://www.luxalgo.com/library/concept/poor-high-poor-low/

**Cited from established literature (not re-checked in this session):**
- Evans & Lyons (2002), *JPE*;
- Cont, Kukanov & Stoikov (2014), *J. Financial Econometrics*;
- Easley, López de Prado & O'Hara (2012), *RFS* (BVC);
- Lee & Ready (1991), *JF*;
- Kyle (1985), *Econometrica*;
- Ni, Pearson & Poteshman (2005), *JFE*;
- Gao, Han, Li & Zhou (2018), *JFE*;
- Neely, Weller & Ulrich (2009), *JFQA*;
- Bailey & López de Prado (2014), *J. Portfolio Management*;
- Crabel (1990), *Day Trading with Short Term Price Patterns and Opening Range Breakout*.

---

## Addenda

- **A (2026-10-11):** `ADDENDUM_A_VISHAAL_FX_VIDEO.md`, "Trading Truth (Part 2) – Live Trade with Deep Charts" (Vishaal Fx).
  - Based on two AI summaries that contradict each other on the video's length; the video itself was not watched.
  - Adds OF-13 (equal-highs/lows sweep and reversal), OF-14 (trade-management alternatives) and OF-15 (scaling in; policy-blocked).
