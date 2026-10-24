# S32: Larry Harris, *Trading and Exchanges: Market Microstructure for Practitioners*, **draft copy** (5 March 2002; published by Oxford University Press, 2003)

**File:** `Trading-Exchanges-Market-Microstructure-Practitioners Draft Copy.pdf`. 113 pp.

| Field | Value |
|---|---|
| **Source type** | **Oxford / university.** University textbook by a USC Marshall professor (former SEC chief economist), published by Oxford University Press. The material is a pre-publication draft. |
| **Evidence status** | **Established** (textbook consensus of market-microstructure theory: adverse selection, spread components, order exposure, the zero-sum game). Mostly conceptual prose with stylised examples; no new empirical results. |
| **Processing** | **All 113 pp. read in full** (332k characters). Low-text pages pp. 2, 4 and 88 were rendered and pixel-tested: **blank (0 dark pixels)**. p. 20 (Fig. 2-1 Bridge quote montage) was read from the text layer. Equations: the information-aggregation box (Ch. 10) and the transaction-cost benchmark formula (Ch. 21) were extracted. |
| **⚠ Content completeness of the FILE** | **This PDF is a sampler, not the whole book.** It holds:<br>• front matter and table of contents;<br>• **Chapter 1 in full** (8 pp.);<br>• then **only the opening ≈ 2–4 pages of each of Chapters 2–29**. Each chapter stops mid-sentence (e.g. Ch. 10's algebra box stops before its result; Ch. 12's bluff example stops before the "failed ending"; Ch. 14 stops at the adverse-selection component);<br>• part openers;<br>• a partial bibliography (General, Ch. 3–5 only, ends mid-entry).<br>**The file was processed completely, but the book is only partly represented.** Anything beyond these openings (e.g. Ch. 14's full equilibrium spread model, Ch. 19's liquidity measures, Ch. 21's econometric cost methods, Ch. 28's circuit-breaker analysis) is **NOT in the corpus**. It must not be cited as read. |

## 1. Core framework (SOURCE: Ch. 1, 8, 10, 13–14, 16, 18–22)
- **Trading is a zero-sum game** relative to the market average (Ch. 1, 8, credited to J. Treynor).
  - Profit-motivated traders (informed speculators, dealers, order anticipators, bluffers) win, on average, at the expense of utilitarian traders (investors, hedgers, gamblers) and **futile traders** ("believe they are profit-motivated… expectations are not rational").
  - "Traders who do not expect to win should refrain from trading."
- **Key recurrent themes (Ch. 1.5):**
  - information asymmetry;
  - **the option value of standing orders** (a limit order is a free option to the market);
  - the order-flow externality;
  - market structure determines power;
  - free entry and exit equalises net profits;
  - principal–agent problems (brokers);
  - credit and trust;
  - the zero-sum game.
- **Fundamental vs market value (Ch. 10):**
  - fundamental value is the expected PV given current information; it is not perfect foresight;
  - changes in fundamental value are unpredictable, so in efficient markets prices ≈ random walk;
  - Fischer Black's "noise": prices are informative if within ½× to 2× of value.
- **Information aggregation (Ch. 10 box, partly in file):**
  - f_i = V + e_i (unbiased forecasts); demand D_i = a(f_i − P);
  - market clearing ΣD_i = 0 gives P = mean(f_i), whose error (1/N)Σe_i shrinks with N under independent errors;
  - *the derivation is truncated in the file; the result is standard (INFERENCE)*.
- **Dealers (Ch. 13):**
  - dealers sell immediacy;
  - **realized spread < quoted spread** because quotes are adjusted after informed flow. Worked example: quoted 0.3, realized −0.1 after adverse news;
  - "position traders" vs "spread traders": in competitive markets dealers must speculate to survive;
  - retail limit-order users are acting as dealers, often without realising the risk.
- **Spread components (Ch. 14):**
  - **transaction-cost (transitory) component** gives bid/ask bounce (negative serial correlation of price changes);
  - **adverse-selection (permanent) component** is how dealers recover losses to informed traders from the uninformed;
  - "the most important lesson… uninformed traders lose to well-informed traders whether they submit limit orders or market orders. **Uninformed traders lose simply because they trade.** … minimize your trading."
- **Order anticipators (Ch. 11):**
  - front runners, sentiment-oriented technical traders and squeezers are "parasitic traders" who do not make prices more informative;
  - quote-matchers extract the option value of displayed limit orders;
  - the tick size governs the cost of stepping ahead (time precedence).
- **Bluffers / manipulation (Ch. 12):**
  - rumour-mongering and price manipulation exploit **momentum traders, who "are particularly susceptible to bluffs"**;
  - a stylised long-side bluff (BNB example: accumulate, use a non-fundamental news trigger, aggressive buying, message-board promotion, distribute to momentum buyers).
- **Block traders (Ch. 15):** four problems:
  - latent demand;
  - **order exposure**;
  - price discrimination;
  - asymmetric information.
  - Front runners accelerate impact by demanding liquidity ahead or withholding it.
- **Value traders (Ch. 16):**
  - the **ultimate liquidity suppliers**; they make markets *resilient*;
  - their "outside spread"; risks are adverse selection and the **winner's curse**.
- **Arbitrage (Ch. 17):**
  - definitions: basis, fair value, arbitrage spread = basis − fair value, **arbitrage bounds**, **basis/residual risk**, carrying costs;
  - hedge ratios chosen to minimise portfolio risk.
- **Buy-side order choice (Ch. 18):**
  - market vs limit depends on spread *and* on value knowledge;
  - **execution probability vs price trade-off**;
  - the cost of non-execution when the market moves away;
  - order display is "the most important trading decision" for large traders.
- **Liquidity (Ch. 19):**
  - "the ability to trade large size quickly at low cost when you want to trade";
  - the object of **bilateral search**; optimal unilateral search stops when expected benefit < cost (camera example);
  - exchanges are search engines.
- **Volatility (Ch. 20):**
  - **fundamental volatility** (unanticipated value changes; unpredictable) vs **transitory volatility** (uninformed liquidity demand; reverses);
  - storage costs, inelastic demand and perishability raise commodity volatility;
  - predictable carrying-cost drift does not count as volatility.
- **Transaction-cost measurement (Ch. 21, V):**
  - **Estimated Cost = TradeSize × TradeSign × (TradePrice − BenchmarkPrice)**. Costs sum to zero across counterparties;
  - components: explicit; implicit (spread and impact); **missed-trade opportunity cost**. Example: an unfilled cotton limit order cost $137.5k of opportunity;
  - implicit costs need a counterfactual benchmark, so measurement is "difficult and imprecise".
- **Performance evaluation (Ch. 22 opener):**
  - "most active traders lose because they trade too much and pay too much to trade";
  - **skill vs luck** discrimination is very hard (Sizzler E. coli example);
  - past performance predicts poorly;
  - **sample-selection bias** "probably accounts for more trading losses than any other mistakes".
- **Market structure (Ch. 5–6, 23–29 openers):**
  - continuous vs call markets; order precedence (price, then time/public/display); leapfrogging; tick-size trade-offs;
  - **price clustering on round numbers** (strongest with small ticks, high volatility, thin trading). Clever traders place limits just inside round numbers;
  - specialists' affirmative and negative obligations; internalisation and payment for order flow (helps small market orders, hurts limit orders);
  - fragmentation vs consolidation; floor vs automated (audit trails);
  - bubble/crash dynamics: momentum traders, margin calls and stop-loss cascades, order anticipators front-running stops;
  - insider trading.

## 2. Critical assessment (INFERENCE)
- Authoritative, textbook-level consensus, but **equity / US-centric (2001–02)**. Many institutional facts are dated (pre-Reg NMS, pre-HFT). The economic principles are durable, as the author himself notes.
- Arguments are largely verbal and stylised. Numbers in boxes are illustrations, not data.
- The **sampler limitation** (see the table) means the corpus contains the *statements of principle* that open each chapter, not their derivations or empirical support.

## 3. Principles for NEXA (tagged)
- **SOURCE (established):** costs, not signal quality, decide most active traders' outcomes. Cost measurement needs an explicit benchmark and must include opportunity cost of misses. (Corroborated by S22, S10, S25 and S31.)
- **SOURCE:** a resting limit order is a **free option** given to better-informed / faster traders, so fills are adversely selected. (Corroborates S06, S10, S11, S27, S29, S31.)
- **SOURCE:** momentum traders are structurally the counterparties bluffers and order anticipators exploit. **INFERENCE:** a momentum/breakout engine should expect a fat tail of failed breakouts around news-like triggers and round numbers. Hypothesis only.
- **SOURCE:** stop-loss orders and margin calls cluster and can be anticipated, so crashes accelerate through stop levels.
  - **INFERENCE:** NEXA's stops placed at obvious levels (round numbers, recent swing extremes) may suffer worse slippage. Links to H-ROUND-NUM.
- **SOURCE:** transitory volatility (bid/ask bounce, liquidity-demand pressure) reverses; fundamental volatility does not.
  - **INFERENCE:** short-horizon reversal at M1–M5 partly reflects spread bounce on bid-based bars. NEXA backtests on bid-only OHLC must not count bounce as signal (cf. S13, S38).
- **SOURCE:** skill vs luck and sample-selection bias dominate evaluation errors. (Corroborates S14, S22, S33, S01's selection of examples.)
- **SOURCE:** price clustering at round numbers. **HYPOTHESIS H-ROUND-NUM:** XAU/FX quotes and swing extremes cluster at round levels (e.g. XAU x00/x50; FX 00/50 pips); stop/limit liquidity there changes fill quality and short-horizon reversal probability. Data: broker ticks/M1, available. Evidence: hypothesis (Harris states clustering for exchange prices; FX clustering is cited via Goodhart–Curcio in the bibliography only).

## 4. NEXA relevance
- **High conceptual value; no direct signals.**
- It reinforces NEXA's governance stance:
  - trade less;
  - measure costs with benchmarks;
  - treat backtest P&L winners with selection-bias suspicion;
  - treat passive fills as adversely selected.
- **Data-limited items:** order exposure, block trading, specialist, internalisation and front-running dynamics need order-level data that Pepperstone does not provide.
- **Retail CFD context:** the broker acts as dealer/internaliser (Ch. 25 logic). NEXA is a small uninformed-by-default liquidity demander. Harris predicts it pays the spread plus adverse-selection component on every trade. An edge must exceed this.

**Cross-references:**
- S06, S10, S11 (adverse selection of limit orders);
- S27, S29 (order exposure/icebergs; Harris 1996 is cited by S29 for parasitic traders);
- S34 (order-flow information);
- S13 (microprice, spread bounce);
- S25 (implementation shortfall);
- S31 (TCA benchmarks; FX market practice);
- S30 Flash Boys (order anticipation by HFT, a modern instance of Ch. 11);
- S14, S22, S33 (selection bias / multiple testing);
- S21 (Thorp, arbitrage bounds and basis);
- S39 (FX value drivers, Ch. 20.1.1).
