# S01: John M. Bland, Jay M. Meisler, Michael D. Archer, *Forex Essentials in 15 Trades: The Global-View.com Guide to Successful Currency Trading* (Wiley Trading, 2009)

**File:** `(Wiley Trading) … Forex Essentials in 15 Trades … (2009).pdf`. 335 PDF pages; 10,526 extracted lines.

| Field | Value |
|---|---|
| **Source type** | Industry/practitioner book (Wiley Trading series). Bland and Meisler are co-founders of Global-View.com and ex-bank FX dealers. Archer is CEO of FXPraxis.com, a futures/FX trader since the 1970s. Not peer-reviewed. Contains commercial self-promotion (Global-View, FXPraxis, Archer's software and books, broker "spotlight"). |
| **Evidence status** | Mostly **practitioner opinion and anecdote; unverified claims**. The 15 showcased trades are **illustrative, selected examples**, not a performance record (see §4). Arithmetic in examples was checked: mostly correct, but **4 source errors** were found (§6). Some claims coincide with established findings elsewhere (disposition effect, stop clustering at round numbers, news-time liquidity withdrawal, CIRP, carry crash risk). |
| **Processing** | **Full text read: lines 1–10,526**, covering front matter, Part One (Ch. 1–7), Part Two (Ch. 8–23, all 15 trades), Part Three (Ch. 24–28, including Visual Basic code), App. A–D, glossary, About the Authors and the index (index read in compacted one-line form). **38 low-text pages:** all rendered as thumbnails and classified by pixel density. 25 are blank; 13 are content, viewed on a contact sheet (cover, titles, dedication, part title, H&S/P&F figures, broker screenshots, screen setup, Mundo charts, back-cover blurb). **Rendered at full size and checked:** pp. 72 (Fig 3.8 RSI), 77 (Fig 3.11 Nofri), 108 (Fig 6.1 trading record table), 166 (Fig 13.1 Three Chart System), 245–246 (Mundo equilibrium formula, Fig 26.6, FOREX beta), 278–279 (directional movement/volatility (DM/V) example), 306 (Fig D.1 banking hours). The other trade charts (Figs 9.1–23.2) were interpreted from captions and the trade statistics stated in the text, not individually inspected. |

## 1. Structure
- **Part One, Basics (Ch. 1–7):** terms and calculations; money management; technical analysis (TA) survey; fundamentals; trading the news; trader profiles; brokers.
- **Part Two (Ch. 8–23):** Archer's "Snowflake" heuristic plus 15 trades, each themed (money management, psychology, TA, FA).
- **Part Three (Ch. 24–28):**
  - currency futures/forwards;
  - "Shanghai BC" forum posts;
  - the "Mundo" synthetic currency and "FOREX beta";
  - the Goodman Swing Count System (GSCS);
  - Market Environment (ME) analysis with Visual Basic 6 code.

## 2. Mathematics and calculations (SOURCE, with our checks)

| Item | Source formula/example | Check |
|---|---|---|
| Leverage | Leverage = 100/Margin %; USD 148,000/USD 500 = 296:1 | ✓ |
| Pip value | 1 % of EUR/USD at 1.4800 = 148 pips ≈ $1,480 per 100k | ✓ |
| Position sizing (p. 28) | units = $risk / stop distance; $500 / 0.0148 = EUR 33,783 | ✓ (USD-quoted pair) |
| Rollover/forward | Carry = short-rate differential (5.5 % − 0.5 % = 5 %); forward points = S·Δr (105.00 × −0.0575 = −6.038) | Direction ✓. **INFERENCE:** S·Δr is a linear approximation. Exact covered interest parity (CIRP) gives F = 105 × 1.005/1.0625 = 99.32, i.e. −5.68 points; the source overstates by about 6 %. |
| Expectancy (Ch. 9) | R:R 3:1 with win-rate 1/3 → +$100 per 3 trades. Campaign: 30 units of $100, 3 wins × $300 − 7 losses × $100 = +$200 | ✓. **INFERENCE:** break-even p* = 1/(1 + R) = 25 % before costs; spread and slippage lower the effective R. |
| RSI (p. 71) | "RSI = 100 − (100/1 + RS)"; RS described as average of up-close days / average of down-close days | Standard form: 100 − 100/(1 + RS), with RS = average gain / average loss in magnitudes. The source description is imprecise. Equivalent to S22's ν+/(ν+ + ν−) ×100. |
| Trade-record table (Fig 6.1, rendered) | 10 EUR/USD trades: −43 pips as traded; +67 pips had one stop not been pulled (−160 → −50) | ✓ both totals |
| Mundo (Ch. 23/26) | Average of EUR/USD, GBP/USD, 1/USDCHF, 1/USDJPY in pips: 12,753 + 18,872 + 8,069 + 8,530 = 48,224; ÷4 = 12,056 → 1.2056 | ✓. **INFERENCE (limitations):** an arithmetic mean of price *levels* weights components by price level (GBP ≈ 2.3 × CHF), with arbitrary JPY scaling. Every component is X/USD, so it is effectively an inverse-USD basket, not a "global" currency (contrast the geometric-weighted DXY). |
| FOREX beta (Table 26.1) | β = SD(pair)/SD(Mundo) in pips: EUR 802.61/352.70 = 2.28 … SEK 94.43/352.70 = 0.27 | Ratios ✓. **INFERENCE:** the SD of price *levels* in pips depends on scale (low-priced SEK/USD automatically scores low) and is trend-contaminated (non-stationary). It is not a volatility beta; the proper version uses log-return SDs or Cov/Var. |
| Rhythm (p. 255) | Average down price-rhythm 5.33; time-rhythm 2.33; crest average 25 | ✓ |
| DM/V (pp. 278–279, rendered) | Prices 117.5, 116.9, 117.7, 118.0, 117.4, 117.5, 117.0, 118.1 → printed **DM = .9, V = 4.3** | **SOURCE ERROR:** DM = 0.6 and V = Σ\|Δ\| = 4.0. Also, ~117 price levels labelled "EUR/USD" look like USD/JPY. |
| Triangular / five-currency equilibrium (p. 245, rendered) | Printed "EUR/USD = (EUR/GBP **÷** GBP/CHF) × (CHF/JPY ÷ USD/JPY)" | **SOURCE ERROR:** must be (EUR/GBP **×** GBP/CHF) × (CHF/JPY ÷ USD/JPY) = EUR/CHF × CHF/USD. The triangle EUR/USD = EUR/GBP × GBP/USD ✓. |
| Thickness (p. 281) | "(H1 − L1) ÷ (H2 − L2); lower ratio → thicker" | **INCONSISTENT** with the book's own verbal definition (overlap of consecutive bar ranges, >50 % = thick; Ch. 11/15). A ratio of consecutive ranges does not measure overlap. |
| VB6 code (pp. 291–292) | `CalculateDM`: DM(i) = C(i) − C(i − N) ✓. `CalculateVolatility`: inner loop sums `Abs(Q(i).C − mean)` | **CODE BUG:** uses `i` instead of `j`, so the result is \|C_i − SMA_N\| (distance from the moving average), not mean absolute deviation, and not the text's "aggregate movement" (path length). **INFERENCE:** \|price − MA\| is exactly the quantity S15 shows has built-in pseudo-mean-reversion. |
| 2008 crisis (p. 60) | EUR/USD 1.6040 → 1.3882 = −13.45 %; → 1.2331 = a further 9.7 % of the high | ✓ |

**INFERENCE:** DM/V maps directly to Kaufman's efficiency ratio ER = \|DM\|/V (path efficiency, i.e. trend vs chop). The book's "thickness" (by its verbal definition) is a bar-overlap/choppiness measure. Both can be computed causally from closed bars.

## 3. Methods described (SOURCE; none statistically validated in the book)
- **KIS system (Ch. 8):**
  - Trend from 1d (+1h subtrend); measure the average primary and secondary swing ("price rhythm").
  - Wait for an average-size pullback, then enter on the first move back in the trend direction ("**Dagger**" = pullback-continuation entry).
  - Stop ≈ 50 % of the average secondary swing; target ≈ 75 % of the average primary swing.
  - Trail by half of each 10–20 pip favourable move.
  - Day-trade rule: at +20–25 pips take partial profit and move the stop to near breakeven.
- **Major trend:** "draw a line from the first closing price on a chart to the last". Archer asks whether a moving average adds information and answers "Not really".
  - **INFERENCE:** this is the sign of the N-bar return, i.e. time-series momentum (TSMOM) sign (S22 §10.4). Practitioner and academic definitions converge.
- **Hartnagle "Simple System" (Ch. 21):** MA for trend/entry/exit plus an oscillator filter (take an MA buy only when the oscillator is falling or ≤0; exit on the MA signal unconditionally). This is a trend-plus-pullback filter.
  - Claimed 2004 test "over a wide range of filters, parameters, and rule sets": "results seldom varied by more than 5 percent… the simplest setups worked… as well as the most complex".
  - No metric, period, costs or out-of-sample (OOS) design is given: an **unverified claim**, though it is consistent in spirit with parsimony and S04's noisy-objective lesson.
- **Three Chart System (Fig 13.1, rendered), timing / watch / perspective:**
  - Guerrilla 1m/5m/30m; Scalper 5m/30m/1h; Day 30m/3h/1d; Position 3h/1d/1w.
  - The Day-trader set differs between Ch. 6 (5m/15m/4h), Ch. 8 (5m/1h/1d) and Fig 13.1 (internal inconsistency).
- **Trader profiles (Ch. 6):** targets of 10–25 / 25–50 / 50–100 / 200–500 pips, with stops at the stated "1:3" (5–10 / 15–20 / 25–30 / 40–50).
  - The implied R:R ratios are not 1:3 (Scalper about 1:1.7–2.5; Position about 1:4–1:10).
  - SOURCE: Guerrilla trading is professional-only because costs dominate (cost fragility).
- **GSCS (Ch. 27):** nine rules.
  - 50 % retracement S/R; measured move; buyer–seller equilibrium; recursion (self-similarity across time frames); wave propagation (all waves are three-swing matrices); the Return (the 4th wave retraces ~50 % of the whole 1-2-3 matrix and ends near the end of wave 2); Compensation-Carryover-Cancellation (3C); Intersection; Points.
  - **INFERENCE:**
    - The 3C rule lets "misses" carry over until cancelled, in either direction, so it is effectively unfalsifiable.
    - The 50 % rule ("support or resistance of some kind for some period") is weak.
    - A 15,000-example computer test is announced ("Stay tuned!"), but **no results are reported**.
    - Archer's claim that "GSCS is predictive whereas Elliott is descriptive" is unsupported.
- **ME (Ch. 28):** DM × V grid (4×4 ×up/down = 32 environments; 10×10 profile matrix); secondary elements thickness, price/time rhythm; tertiary "shape" and "triangulation".
  - "Shape" = a semaphore channel (MAs of highs and lows *displaced back half the period*, i.e. **centred**). **INFERENCE: look-ahead** if used at the right edge.
  - Claim: high-DM/low-V tends to evolve into low-DM/high-V at tops and bottoms, as a "leading indicator" (unverified).
- **News (Ch. 5, 22):**
  - Consensus vs actual surprise drives the reaction; whisper numbers are unreliable.
  - A "shockwave" is followed by "price-trace-dispersement (PTD)", a slower opposite drift that often erases the shock. This is claimed from Archer/Bickford research; no statistics are shown.
  - The OCO straddle around news is defeated by brokers and spread ballooning.
  - Recommendation: be **flat** during news.
- **Shanghai BC (Ch. 25):**
  - Pyramid into medium-term trends; initial stop 1 % of equity; wide stops; scale in and out; exit by trailing stops.
  - 20-MA on 8h/1d/1w/1M charts. Rule: "never buy below falling daily 20 MA / never sell above rising daily 20 MA". RSI(10) only on weekly/monthly charts.
  - **Lead–lag claims:** EUR/GBP and GBP/CHF lead EUR/USD and USD/CHF by "a day or two"; EUR/JPY, GBP/JPY and CHF/JPY lead USD/JPY.
  - "Gold is the mirror of Dollar… correlation is excellent."
  - Tokyo fix (10:00 JST) and importer settlement days (5th/10th/15th…) produce USD/JPY demand into the fix.
  - Session opens (first hour of Tokyo/London/NY) hold most liquidity, and moves start there, especially at the London open. A Yen jump at the Tokyo open "continues throughout the day and a few more days".
  - All anecdotal; "Never lost money on a medium-term bet relying on those guide dogs" is survivorship-prone.

## 4. Evidence quality: the 15 trades are a selected sample
- Tally of the stated results (17 executions across 15 chapters; Ch. 17 has 3), **arithmetic verified for every trade with stated prices**:
  - −75, −23, +131, +315, +263, +535, +362, −118, +45, +44, +485, +58, +318 (no prices), +636 (no prices), +144, +59, +84;
  - **= +3,263 pips; 14/17 winners (82 %).**
- This contradicts the authors' own statements:
  - Archer "makes more bad trades than good trades" (p. 95);
  - "the new trader should assume he or she will lose 70 percent of the time" (p. 112).
- **INFERENCE: strong selection bias.** The trades were chosen to illustrate lessons, with no denominator, costs or full record. Trades #11 and #12 give no prices and are unverifiable.
- Other unverifiable performance claims:
  - Jonathan's Wave "48 % annual returns with a zero expectation of a 50 % drawdown (Managed Account Reports)", an ill-defined statistic;
  - "breaking even… puts you ahead of 90 percent of your peers";
  - ">95 % of traders are failures";
  - "at least 75 % of markets exhibit time rhythm in at least one time frame". **INFERENCE:** "at least one of many time frames" guarantees a high rate by chance.

## 5. Principles (tagged)
1. **SOURCE (consistent with S10/S11):** around news, liquidity thins, spreads balloon, gaps occur, and stop/market orders fill far away. The example is the NFP of 1 Feb 2008: an order placed at 1.4910 filled at 1.4955, the day high (45 pips). Brokers do not provide "gap insurance".
2. **SOURCE + INFERENCE:** stops placed at obvious levels or round numbers ("Jubbs") get run.
   - This coincides with Osler (2000, 2003; cited in S22's bibliography) on stop-loss clustering at round numbers.
   - The book adds: "legitimate whipsawing is almost certainly many times more common than stop harvesting". Its test for harvesting is to compare platforms; a gap of ≥10 pips raises suspicion.
3. **SOURCE:** money management and attitude matter more than the entry method; a single large loss is the usual way traders fail (Fig 6.1, the "bounce" anecdote).
   - **INFERENCE:** no-stop/averaging-down behaviour is a short-gamma, negatively skewed payoff ("nine out of 10 times the bounce will save you; one out of 10… devastating").
4. **SOURCE:** correlations between FX pairs change over time, and "diversification" across correlated pairs is a myth (relevant to NEXA's correlation cap).
5. **SOURCE:** the drivers of FX rotate (yield differentials in a growth/low-volatility regime vs growth expectations in risk-off; the money-supply era came and went). This is non-stationarity, consistent with S14 and S22 on edge decay.
6. **SOURCE:** classic chart patterns are "not particularly reliable anymore because too many traders are aware of them". This is reflexive edge decay (cf S21 on rediscovery).
7. **SOURCE (good methodology):** split any system's results by DM/V regime and prefer methods that "do not collapse in the weaker" regime. Bathtub analysis: test "as many examples as possible" and "avoid adding too many ad hoc rules".
   - **INFERENCE:** these are the right instincts, but the book has no out-of-sample split, no multiple-testing control and no cost modelling. "Bathtub" mining ("what happens on the 5th hour after 2 up + 2 down hours?") is uncontrolled data-snooping.
8. **SOURCE:** the FX/equity correlation is regime-dependent (high in 2008). The carry trade earns the rate differential but unwinds violently in crises (2008), consistent with S22 §8.2.
9. **SOURCE (App D, rendered):** time of day strongly affects volume, liquidity and volatility. The banking-hours chart uses fixed GMT offsets with no DST.
   - **INFERENCE:** static offsets misalign half the year. This is relevant to NEXA's server = NY+7 convention and the D-TZ open item.
10. **SOURCE:** the Sunday open is "treacherous: very illiquid, pip spreads outrageous" (relevant to H-GAP-VOL in S15).

## 6. Source errors and inconsistencies found
1. DM/V example arithmetic: DM 0.9 and V 4.3 printed vs 0.6 and 4.0 correct, plus the price-level label.
2. Five-currency equilibrium uses ÷ GBP/CHF where × is needed.
3. "FOREX beta": first defined as a ratio of OLS trend slopes vs time (12 %/10 % = 1.2), which is not beta (Cov/Var of returns), and "low beta = moving laterally" is wrong. Then redefined as a ratio of price-level SDs, which is scale- and trend-dependent.
4. VB volatility code uses index i instead of j, so it computes distance from the MA.
5. Thickness formula is inconsistent with the verbal definition.
6. Trader-profile R:R ratios are inconsistent with the stated 1:3; chart sets differ across chapters; target pips differ between Ch. 6 and Ch. 9.
7. Contradiction (preserved): "Good traders do not pyramid… pyramiding losses is suicide" (authors, glossary) vs scaling in (Ch. 11) and Shanghai BC's pyramiding as "no other way to make big money".
8. Trade #14 text says "50 pips" while the stats say +59.
9. Linear forward-points approximation (§2).
10. "All econometric models use linear tools" (an incorrect generalisation even in 2009).

## 7. NEXA relevance and hypotheses
- **H-THICKNESS-ER** (data available: NEXA M1–D1 closed bars):
  - Compute Kaufman ER = \|C_t − C_{t−N}\| / Σ\|ΔC\| and a bar-overlap ratio (overlap of [L_{t−1}, H_{t−1}] and [L_t, H_t] divided by the union range) per symbol and time frame.
  - Test as *descriptive regime variables* whether 8E trend vs band/mean-reversion engine outcomes differ by ER/overlap tercile.
  - Use in-sample only, then prospective; no retuning of frozen V2/8E.
  - Risks: multiple N choices; overlap with H-HURST-GATE (S15) and H-TSMOM-TANH (S22).
  - Evidence level: hypothesis; practitioner origin.
- **H-NEWS-PTD:** does the post-release drift reverse the initial shock (PTD) or continue it?
  - Measure on NEXA symbols using event windows from the MT5 calendar. **Caveat:** the calendar timestamp offset (memory: MT5 calendar is stamped with the export-time offset) must be corrected first.
  - Look-ahead risk: use the release time, not bar-close detection.
  - Links S10 news slippage. For NEXA it is primarily a **risk / no-trade-window** question, not an entry signal.
- **H-CROSS-LEAD:** do EUR/GBP, GBP/CHF and EUR/JPY lead EUR/USD? Do JPY crosses lead USD/JPY? Does XAU co-move with USD inversely?
  - Lagged cross-correlation on closed bars at H1/H4/D1 with a strict lag ≥1 bar; compare against S14's Lévy-area method.
  - Data: partially available. Cross symbols must exist in the Pepperstone tester; no broad downloads.
  - Evidence: anecdotal claim. Linked to S14 H-LEADLAG-FX (data-limited).
- **H-OPEN-CONT / H-GOTOBI:**
  - Session-open continuation (Tokyo/London) and Tokyo-fix/gotobi USD/JPY drift.
  - Needs exact server-time (NY+7) to JST/UTC mapping with DST handling.
  - Gotobi is documented in the academic literature (not cited here). It is USD/JPY-only and not XAU.
  - Evidence: practitioner claim. Links S14 H-SESSION-SPLIT.
- **H-RETURN-50 (GSCS):**
  - Whether 4th swings after a 1-2-3 swing matrix end near 50 % of the matrix more often than a random-walk swing-null predicts.
  - Requires a deterministic, causal (zig-zag on closed bars, with confirmation lag) swing definition. A swing algorithm's confirmation delay is a classic **look-ahead trap**.
  - **The evidence prior is weak**, since GSCS is unfalsifiable as stated. Low priority.
- **Execution hygiene for NEXA:**
  1. No stops at round numbers (offset from them), consistent with Osler.
  2. Treat news windows as risk regimes (S10).
  3. Account for Sunday-open spread and gap.
  4. Measure performance per regime.
  - Cost-only, no-edge assumptions apply.
- **Do not use:**
  - the showcased trade results as evidence;
  - Mundo/FOREX-beta as defined;
  - "shape" with centred MAs;
  - GSCS 3C carryover calculations;
  - Fibonacci/DiNapoli/Gann claims;
  - Archer's ME code without fixing the bug.

**Cross-references:**
- S22 (TSMOM sign; Osler citation; carry/CIRP; triangular arbitrage);
- S15 (MA-distance artefact; scaling ≠ exact self-similarity; weekend gaps);
- S10 (news slippage, discretion);
- S11 (last look / stop-running suspicion);
- S14 (lead–lag, session split);
- S21 (edge decay through rediscovery);
- S17 (TD), S09/S19 (bands);
- S04 (noisy objective vs "results seldom varied by 5 %").
