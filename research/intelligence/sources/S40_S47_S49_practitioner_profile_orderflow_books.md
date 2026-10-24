# S40–S47, S49: practitioner books (Market Profile, Volume Profile, VPA, order flow, Renaissance)

**Evidence status for this whole group:** practitioner literature. Every quantitative claim below is **UNVERIFIED** unless stated otherwise. None of these sources has:
- an out-of-sample test;
- a cost model;
- a baseline comparison;
- a multiple-testing correction.

Example trades are selected illustrations. S44 and S49 state explicitly that **all trades are hypothetical, not live**.

**Provenance warnings (file content ≠ book title):**
- **S40** `Anna Coulling A complete Guide to Volume Price.pdf` is **not Coulling's book**. It is "Cliff-notes by @HowLn_", a third-party summary (75 pp.). Coulling's own wording cannot be cited from it.
- **S47** `The Man Who Solved the Market PDF.pdf` is **not Zuckerman's book**. It is a "Bookey" chapter summary (186 pp.).
  - The first extraction truncated at page 24 because of a NUL character; it was re-extracted in full (186 pp.).
- **Corpus items 16–17 are not PDFs.** They are 2 `.bibtex` *citation records* (Edet 2026, *Gamma Exposure (GEX) for 0DTE Traders*; Schwartz & Whitemore 2026, *Options Market Microstructure*).
  - **Neither book's content is in the corpus. Neither can be cited as read.**
  - Both are 2026 Amazon KDP self-published titles.

---

## S42: Dalton, Jones & Dalton (1993), *Mind over Markets*
**What was read:** TOC; Ch. 2 (auction, day types); the Ch. 4 openings section (open types); Special Situations (3-1 days, Neutral-Extreme, the Value-Area Rule); App. 1 (value-area calculation). The rest was keyword-scanned.

**Core definitions (SOURCE)**
- **Data:** pit-era futures (T-bonds, soybeans, S&P), with 30-minute TPO periods A, B, C, …
- **Initial balance (IB):** the range of the first two periods, i.e. the first hour ("slightly longer in the S&P").
- **Range extension:** trade beyond the IB. It is attributed to "other-timeframe" (OTF) participants.
- **Value area (VA):** "the area where 70 % of the day's business is conducted (roughly one standard deviation)".
  - **Volume VA algorithm (App. 1):**
    1. Start at the maximum-volume price.
    2. Compare the sum of the next two prices above with the next two below; add the larger pair.
    3. Repeat until ≥ 70 % of volume is included.
  - The TPO VA is the same with TPO counts.
- **Open types:** Open-Drive, Open-Test-Drive, Open-Rejection-Reverse, Open-Auction, in decreasing order of conviction.
  - "In the majority of cases the extreme left behind after an Open-Drive will hold for the entire day."
  - Open-Rejection-Reverse extremes "generally hold less than half of the time".
- **Day types:** Normal, Normal Variation, Trend, Double-Distribution Trend, Neutral, Nontrend.
- **"Markets trend only 20–30 % of the time"** (attributed to "knowledgeable professionals").

**The only quantified studies in the Market Profile literature found in the corpus (SOURCE, Ch. 4 "Special Situations")**
- **3-1 days** (initiative tail, TPO count and range extension all in the same direction):
  - **Sample:** T-bonds, 24 Jun 1986 – 29 May 1987.
  - **Next-day first 90 minutes better than the previous VA:** 94 % (2I-1R days: 71 %). Worse: 0 %.
  - **Next-day close better / within / worse:** 59 / 38 / 3 % (2I-1R: 46 / 36 / 18).
- **Neutral-Extreme days:**
  - **Sample:** T-bonds, 24 Jun 1986 – 12 Aug 1987.
  - **First 90 minutes better / within / worse:** 64 / 28 / 8 %.
  - **Next-day close:** 45 / 28 / 27 %.
- **The authors' own caveat:** "derived from one market studied over a limited period … other markets behave differently and all markets change over time."
- **Value-Area Rule:** if the market opens outside the prior VA and is accepted back inside it ("double TPO prints"), there is "a good possibility" it auctions through to the other side of the VA. It is more likely when:
  - the open is close to the VA;
  - the VA is narrow.
  - **No statistic is given.**

**Critical reading (INFERENCE)**
- **Sample size is not reported.** Roughly 230 trading days contain only a handful of 3-1 days. There is **no base rate**: how often does *any* next day trade beyond the previous VA in the first 90 minutes? With wide VAs and a gap-prone open, that base rate may be high.
- **Single market, about one year, 1986–87 floor era.** No costs, no test.
- **Status:** HYPOTHESIS. Testable on NEXA data (HYP-MP-01/02 in 14_HYPOTHESIS_REGISTRY).
- **"70 % ≈ one standard deviation" holds only under normality** (±1σ = 68.3 %; 70 % ≈ ±1.036σ). Intraday price-volume distributions are often bimodal (see the "Double-Distribution" day type), so the σ analogy is a heuristic, not a result.
- **The session concepts (open, IB, close) assume a pit session.** For 24-hour FX and gold they must be *defined* before they can be tested (see 06_LIQUIDITY_MODEL, session anchors).

## S46: Steidlmayer & Hawkins (2003), *Steidlmayer on Markets: Trading with Market Profile*, 2nd edition
**What was read:** TOC; Ch. 6 day structure; Ch. 10–11 strategy passages (keyword scan of the rest).

**Day structure, defined by the first hour's range (IB) (SOURCE)**

| Day type | Range extension beyond IB | Long-term (OTF) share of activity |
|---|---|---|
| Nontrend | ≈ none | — |
| Normal | ≈ 50 % | 10–20 % |
| Normal Variation | ≈ 100 % (about 2× IB) | 20–40 % |
| Trend | — | 40–60 % |

- **Trend day criteria:**
  - small IB;
  - close within 10 % of the extreme;
  - non-rotational (successive half-hour highs and lows in one direction, broken at most once or twice).
- **The first standard deviation is 68 %** of volume (Steidlmayer). Dalton and Keppler use **70 %**.
- **"Trending activity occurs approximately 10–20 % of the time"; development 80–90 %.** Dalton says 20–30 %.
- **After a trend day: "some 90 percent chance the market will trade sideways or reverse that day's price activity the next day."**
- **Anecdotes:**
  - a Bund open-drive strategy "worked over 70 percent of the time" for one trader before 2002;
  - fading Richard Dennis's breakouts on the CBOT floor.

**Critical reading:**
- The 68/70 %, 10–20 vs 20–30 % and post-trend 90 % numbers are **unsourced**.
- The OTF participation shares (10–60 %) are **not observable**. There is no data behind them.
- The day-type thresholds, however, are **mechanically codifiable**: IB, extension ratio, close location, rotation count.

**Tension with S42:**
- Dalton reports *continuation* after 3-1 and neutral-extreme structure.
- Hawkins says that after a *trend day* the next day is sideways or reverses 90 % of the time.
- The two concern different structures, but both are testable on the same data (HYP-MP-03).

## S45: J. Keppler (2010), *Profit with the Market Profile*
- **Practitioner text** (MarketDelta charts).
- **VA = 70 %** of TPOs or activity. A normal-distribution explanation (68–95–99.7) is used as the rationale.
- **Topics:** participants, the auction, analysing the open, profile patterns.
- **No quantified tests.** Keyword-scanned; TOC and core chapters on value area and the open skimmed.
- **Status:** UNVERIFIED.

## S41: "Dean Market Profile" (A. Kulkarni?) (2019), *Anyone Can Learn Market Profile* (Notion Press)
- **Indian-market (Nifty/BankNifty) AMT/MP primer.** Autobiographical and motivational.
- **"LCTR framework":** **L**ogic → **C**ontext → **T**iming → **R**isk.
  - This is structurally the same layering as the directive's §10 (level/setup → context → execution → risk).
  - It is offered **as a discretionary mindset, not a rule set**.
- **It explicitly advises to "stop relying on statistical patterns as they are not applicable to real markets".** This is the opposite of NEXA's evidence standard.
- **Risk rules stated:** 2 % per trade, 6 % open risk, 10 % per month.
- **VA = 70 %.**
- **Status:** UNVERIFIED / OPINION.

## S43: EarnForex, *MarketProfile v1.15* indicator manual (2020)
- **Documentation for a free MT4/MT5 TPO Market Profile indicator** (GitHub). It covers:
  - daily, weekly, monthly, intraday and rectangle sessions;
  - VAH, VAL and median (POC);
  - single prints; "prominent median" (PPOC).
- **Changelog (relevant to NEXA):** v1.14 "**Fixed a rounding error in MT5 version, which resulted in value areas being biased towards higher prices**". This is a reminder that VA implementations carry subtle bias. Any NEXA implementation needs a parity test against a reference.
- **Claim:** "Traders tend to return to those areas if the volume of the breakout movement is not too high." **Unsupported.**
- **Status:** TOOL DOCUMENTATION. TPO profiles are computable from MT5 M1 bars.

## S49: "Trader Dale", *Volume Profile: The Insider's Guide to Trading* (≈ 2018–20)
- **Retail FX/futures educator. All trades are hypothetical** (the book's own disclosure). It also advertises a paid signal service ("strike rate in excess of 70 % over the past 10 months").
- **Profile shapes (SOURCE):**
  - **D:** balance; POC near the middle; trade from the edges to the POC.
  - **P:** aggressive buyers, then rotation at the high.
  - **b:** the mirror of P.
  - **thin:** trend.
- **Setup #1 "volume accumulation":** a sideways "rotation" followed by a strong move. The heaviest-volume price inside the rotation (from a "Flexible Volume Profile") is traded **on the first return, with no confirmation**.
  - **Rationale given:** institutions "defend their positions"; counterparties avoid "a fight".
  - **Unfalsifiable as stated.** The *mechanical* version is testable (HYP-VP-02).
- **Look-ahead caution (INFERENCE):** the zone is labelled "buyers' accumulation" *because* price later rose.
  - This is legitimate only if the level is used **after** the breakout is complete, i.e. causally at the time of the retest.
  - Any test must define the breakout and the zone using data available at the retest time only.
- **"Only 3.5 % of daily FX volume is retail" (BIS)** is used to argue for following institutions.

## S44: "Trader Dale", *Order Flow Trading Setups* (≈ 2020)
- **Futures footprint charts** (NinjaTrader, CQG data). **All trades hypothetical.**
- **Definitions (SOURCE):**
  - **Footprint:** bid × ask volume per price, per bar.
  - **"Delta shows a sum of Bid and Ask"**. **This is a definitional error:** delta is a *difference*, ask-volume − bid-volume. The book later uses it correctly as a difference.
  - **Imbalance:** diagonal comparison where Ask(p) ≥ 300 % of Bid(p − 1 tick), or the reverse. **This is the origin of the "300 %" threshold quoted in the directive §13.**
    - No justification is given for 300 %. It is a display default.
  - **Stacked imbalances:** ≥ 3 adjacent imbalance cells, claimed to be "strong S/R".
  - **Unfinished business (failed auction):** a bar high with bid volume ≠ 0 (or a low with ask volume ≠ 0). Claimed to act as a "magnet". The author also says it is "not a Holy Grail".
  - **Trades filter:** prints of ≥ 25 contracts on 6E (EUR futures).
  - **Cumulative-delta divergence** on 1-minute bars.
- **Setups:** combine a pre-defined S/R zone (from volume profile) with an order-flow "confirmation": a limit-order absorption or aggressive orders with delta in the trade direction. This is **exactly the directive's WHERE (level) + WHEN (order flow) split**, offered here as practice with no evidence.
- **FX vs futures:** FX volume is decentralised and "Forex providers are unable to distinguish Bid and Ask". The author analyses currency futures and executes in spot FX, transferring levels "visually".
  - **For JPY, CHF and CAD the futures quote is inverse.**
  - **Our measured basis** (6EZ6 − EURUSD ≈ +0.0047, GCZ6 − XAUUSD ≈ +$35–50 in September 2026, drifting daily) shows that "visual" transfer is imprecise and the mapping must be explicit.
- **Data reality for NEXA:**
  - Every bid×ask feature here needs **trade-initiator classification**, which NEXA does not have.
  - MT5/Pepperstone has none.
  - Massive's plan has futures 1-minute aggregates (volume, transactions) but **no trades and no quotes** (NOT_ENTITLED, 2026-10-04).
  - **True footprint, delta, imbalance and unfinished business are UNAVAILABLE.** Only proxy delta (tick rule or bulk-volume classification on 1-minute bars) is derivable, with the caveats in 07/08.

## S40: cliff-notes of A. Coulling, *A Complete Guide to Volume Price Analysis*
- **Wyckoff's laws as framed:** supply/demand, cause and effect, **effort vs result** ("the price action should reflect the volume").
- **"Validation or anomaly":** a wide-spread candle on low volume, or high volume on a narrow spread, is an anomaly. Also "tests", "no demand" / "no supply", "climaxes".
- **Terminology conflict:** the notes call a high-volume sell-off at the bottom a "buying climax" and the top a "selling climax", named from the insider's side. Standard Wyckoff usage is the reverse (selling climax at the bottom).
- **Mathematical content (INFERENCE):** effort vs result is a statement about the joint distribution of |return| and volume over a bar. It formalises as the residual of log|r| regressed on log(volume), conditioned on session and volatility. This is a price-impact measure in the Kyle-λ / Amihud family (EQ-EVR in 11).
- **Status:** UNVERIFIED. Also a secondary source (a summary, not the book).

## S47: Bookey summary of G. Zuckerman (2019), *The Man Who Solved the Market*
- **Journalistic history of Renaissance Technologies / Medallion**, summarised.
- **Method-relevant statements (as summarised; second-hand journalism):**
  - Leonard Baum (hidden Markov models) worked with Simons on **currency** patterns.
  - There was an early emphasis on **clean, comprehensive price data** (Sandor Straus).
  - A **single unified model** across assets.
  - Many **weak, non-intuitive signals**.
  - Kelly-style sizing influence (via Elwyn Berlekamp and John Kelly).
  - "Medallion ≈ 66 % average annual return since 1988" (gross of fees; **unverifiable**, survivorship).
- **Status:** NARRATIVE. Useful only as a *process* reference:
  - data hygiene;
  - many small edges;
  - cost obsession;
  - statistical rather than discretionary rules.
- **Gives no tradable or testable claim.** The HMM mention supports regime-switching state models as a *method family* (09), not any parameterisation.
