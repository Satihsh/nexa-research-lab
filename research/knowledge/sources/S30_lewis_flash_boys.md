# S30: Michael Lewis, *Flash Boys: A Wall Street Revolt* (W. W. Norton, 2014; first edition)

**File:** `Flash-Boys.pdf`. 211 pp.

| Field | Value |
|---|---|
| **Source type** | **External: popular / investigative journalism (trade non-fiction).** Not academic, not peer-reviewed. Narrative built from interviews (Brad Katsuyama / RBC → IEX; Ronan Ryan; John Schwall; Sergey Aleynikov; Spread Networks; Rich Gates / TFS Capital), plus a few cited studies (UC Berkeley 2013 SIP-vs-direct-feed paper; CFTC / Clark-Joseph; Nanex; Themis Trading). |
| **Evidence status** | **Unverified claims / anecdotal evidence**, with some **supported** elements: the existence of co-location, maker-taker rebates, flash orders, Reg NMS/SIP latency, Spread Networks and payment for order flow are documented facts. The magnitudes (HFT profit estimates, "$160M/day tax", "$1bn/yr dark-pool arbitrage") are **single-source estimates without methods**. The framing is explicitly advocacy (pro-IEX); counter-arguments (HFT narrows spreads) are summarised but dismissed. **Contested**: academic HFT literature is mixed (see S24, S26). |
| **Processing** | **All 211 pp. read in full text** (493k characters, ≈ 395 compacted blocks): Introduction, Chapters 1–8, Epilogue, Acknowledgments, back matter. Low-text pages: p. 1 (cover, rendered: title art only), pp. 2–5 (title, dedication, epigraph, contents: text present), p. 9 (intro end, text present), pp. 206–210 (also-by / blurbs), p. 211 (rendered: copyright page, ISBN 978-0-393-24466-3). No figures or tables. The IEX "obelisk" charts are described in the text only. No equations. |

## 1. Factual and claimed content (SOURCE; numbers as reported, mostly unverified)

### Latency infrastructure
- **Spread Networks** (Ch. 1):
  - 827-mile straight fibre Chicago (CME) ↔ Carteret (Nasdaq);
  - round trip **13 ms**, against ≈ 14.65–17 ms on carrier routes;
  - about $300M build;
  - leased at **$10.6M / 5 years** up front (≈ $14M all-in) to ~200 slots;
  - Tabb estimated **$20bn/yr** futures–cash arbitrage contested by ~400 firms.
- **Microwave towers** (Epilogue) later cut the round trip to ≈ **8 ms** (4.5 ms less than fibre).
- Speed of light in fibre ≈ ⅔ c (≈ 124 miles/ms).
- **Co-location / "proximity services"** (Ch. 3, Ronan Ryan):
  - moving a Kansas City fund to Nutley cut 43 ms → 3.8 ms;
  - switch latency fell from 150 µs to 1.2 µs;
  - Radianz billed HFT ≈ $80M (2005–08) for co-location;
  - exchanges sold bigger pipes: $25k → $40k/month for a **2 µs** gain.

### Market fragmentation and the "illusory" quote (Ch. 2)
- 13 public US exchanges (four sites in NJ) plus ~40–45 dark pools by 2013.
- **Displayed liquidity vanished when Katsuyama's orders were sprayed across venues.**
  - Fill % fell as more venues were targeted. BATS (nearest, Weehawken) always filled 100 %.
  - Hypothesis: **arrival-time differences (≈ 2–4 ms) allowed cross-venue front-running.**
  - **"Thor"** delayed orders so they reached all venues within ≈ 350 µs (the fastest HFT inter-exchange hop ≈ 465 µs). Fills became complete.
  - Example: 10M Citigroup shares saved $29k (< 0.1 %), extrapolated to ≈ $160M/day across $225bn ADV. The **extrapolation is the author's**, not a measurement.

### Maker-taker / inverted fees
- Rebates paid to liquidity makers, fees charged to takers; some venues invert.
- Brokers' "sequential cost-effective routers" chase rebates, which exposes client intent.
- CBSX inverted its fees right after Spread went live (Sep 2010), drawing broker flow that HFT front-ran to NJ.

### Reg NMS (2005/2007) and the SIP
- The **order-protection rule** (route to the NBBO venue first) made routing predictable.
- The **public SIP is slower than private direct feeds**. Gaps up to ~25 ms are cited.
- Berkeley 2013 study: SIP vs direct price for AAPL differed **55,000 times/day**.
- This creates **"slow market arbitrage"**: picking off stale quotes.

### Flash orders (2009)
- Exchanges showed orders to paying HFT firms for fractions of a second (Schumer letter).

### Payment for order flow
- TD Ameritrade sold retail flow (hundreds of millions per year) to Citadel and others, on "handshake deals".
- Schwab sold its flow to UBS for 8 years at $285M ("left ≥ $1bn on the table", per Chris Nagy).
- Retail flow is the most valuable because it is **uninformed and slow**.

### Dark pools (Ch. 4, 7)
- Banks internalised **15–60 % of client orders** in their own pools while those pools were < 1–2 % of the market (Goldman: ~50 % of routed orders filled in a pool that was < 2 % of the market).
- **Rich Gates's test:**
  - rest a mid-point buy in a dark pool, then sell at a lower price on a lit venue;
  - he was picked off (bought at 100.05, sold at 100.01);
  - positive at Goldman Sigma X (≈ 50 % of tests, H1 2010), later at Credit Suisse Crossfinder and BATS.
- Selling HFT access to pools; pinging with 100-share orders.
- **"Dark pool arbitrage"** (Ch. 7): HFT intermediates between an IEX mid-peg seller and a bank's dark-pool buyer resting at the offer. Estimated > $1bn/yr, from 15 days of observations. HFT took ≈ 85 % of the gains, the bank ≈ 15 %.

### Order types (Ch. 6)
- About 150 exotic types, e.g. **Post-Only, Hide-Not-Slide** (queue-jumping for rebates).
- Sub-penny pricing ($30.0001).
- HFT ≈ 50 % of trades but **> 99 % of orders** (orders as information probes).

### Taxonomy of predation (IEX "Puzzle Masters")
1. **Electronic front-running** (see the order on one venue, race to others).
2. **Rebate arbitrage.**
3. **Slow market arbitrage** (stale quotes; "probably by far the most widespread").
4. (Later) **dark pool arbitrage.**

### IEX design (Ch. 6–7)
- **350 µs speed bump** (38 miles of coiled fibre in a "shoebox").
- No co-location; no rebates; flat 9 mils per side.
- Only market, limit and **mid-point peg** orders.
- Owners cannot be direct traders.
- Own fast market view to re-price pegs before stale-quote snipes.
- Launched **25 Oct 2013**: day 1 traded 568,524 shares.
- **Goldman's 19 Dec 2013 flow:** 92 % filled at the mid vs 17 % in dark pools; average trade size ≈ 2× market.

### Market events cited
- **Flash crash** 6 May 2010: −600 Dow points in minutes; P&G printed at $0.01 and $100,000; SEC report kept time to the second, not the microsecond.
- Facebook IPO glitch (2012); Knight Capital −$440M (Aug 2012); Goldman Aug 2013 errant trades; BATS trading outside the NBBO since 2008.
- Intraday volatility 2010–13 ≈ 40 % higher than 2004–06 (author's figure).
- Mini flash crashes, e.g. GOOG $796 → $775 → $793 within ~1.75 s.

### HFT characteristics claimed
- Flat overnight.
- **Virtu: one losing day in ~5.5 years; Tradebot: 4 years without a losing day.** This implies an informational / structural edge, not risk-taking.
- Chicago futures lead NJ equities. HFT uses that lead to **withdraw quotes before broad moves**, so liquidity disappears exactly when it is needed.

### The Aleynikov case (Ch. 5, 8)
- Narrative on Goldman's HFT stack:
  - ~60M lines of legacy code (Hull Trading);
  - three stages: ticker plant → strategy → order entry;
  - hub-and-spoke latency of 5 ms across a street.
- **"all their algorithms are premised on some sort of prediction — predicting something one second into the future"** (quoted from Aleynikov). The predictions failed in Sep 2008.
- Not about market mechanics per se.

## 2. Critical assessment (INFERENCE)
1. **Journalism with an advocacy arc.**
   - Protagonist-centred; opponents are paraphrased; banks' views are second-hand.
   - Key numbers come from interested parties (IEX founders, Tabb, Nagy) without methods.
   - Anonymous sources.
2. **Selective evidence on HFT welfare.**
   - The book concedes spreads narrowed (≈ 1/16 → 1¢) but argues the narrowing is "illusory".
   - Academic work (S24 Cartea et al.; S26; wider literature) finds mixed effects:
     - HFT market-making narrows spreads in normal times;
     - latency arbitrage imposes a tax (cf. Budish–Cramton–Shim, not in corpus);
     - liquidity withdraws in stress.
   - The book's core mechanism (**stale-quote sniping from latency differentials**) is consistent with that literature. Its magnitudes are not established.
3. **Small-sample and anecdotal tests.**
   - Gates's tests: "hundreds", in illiquid names.
   - Thor's savings: single trades extrapolated.
   - The "obelisk" chart: one stock, one second.
   - IEX day-one statistics: weeks of data, selection effects (only the honest brokers routed to IEX).
4. **US equity specific (2007–2013).** FX is OTC with last look, no NBBO/SIP and different fee structures.
   - The **general mechanisms transfer to FX**: latency arbitrage between ECNs and stale quotes; last-look option to reject; internalisation by dealers / payment for flow at retail brokers (S31 and S32 corroborate).
5. **Post-publication events (outside corpus, UNKNOWN here):** IEX became a public exchange (2016). The book's claims were debated. The corpus does not contain those rebuttals or follow-ups, so they are **not used as evidence**.

## 3. Principles (tagged)
- **SOURCE + S32 + S31:**
  - a displayed or submitted order is information;
  - venues and intermediaries can monetise it (front-running, pinging, last look, payment for order flow);
  - the slowest participant trades at stale prices.
- **SOURCE (supported mechanism) + S24/S26:** latency differentials create **stale-quote sniping**. A resting order is picked off when the reference price moves elsewhere first (Harris's "free option", S32).
- **SOURCE:** "trading activity" ≠ "liquidity". Volume can be manufactured by intermediaries who take no risk. Displayed depth can vanish at the moment of need ("liquidity mirage", also S31 HSBC).
- **SOURCE:** in stress, fast liquidity providers **withdraw first**, leading to gaps and mini flash crashes.
  - **INFERENCE for NEXA:** stop-loss orders at a retail CFD broker may fill far through the stop in fast markets. Backtests that assume stop fills at the stop price understate tail loss (links S10, S15, S22 cost fragility).
- **SOURCE:** fragmented markets + slow consolidated data mean the price you see is not the price you can trade.
  - **INFERENCE:** NEXA's broker feed is one dealer's view. Fills, requotes and slippage depend on the broker's internalisation and LP hedging.
  - The tick timestamps in NEXA's data are broker-server times, not a consolidated tape.
- **SOURCE:** complexity itself is a risk. "Normal accidents" (Perrow), glitches and outages show that complex systems fail without a single culprit (Zoran Perkov; Cook, "How Complex Systems Fail").
  - **INFERENCE:** this supports NEXA's design philosophy: simple, auditable engine logic, fail-closed safety (NEXA_Safety.mqh, correlation cap fix), kill switches, and an operational envelope (S31).
- **SOURCE (quote):** HFT algos predict ~1 s ahead and failed in the 2008 regime break.
  - **INFERENCE:** prediction edges are regime-fragile (S22, S33, S35).

## 4. NEXA relevance
- **No tradable signal; DATA-LIMITED.** NEXA cannot observe multi-venue order books, SIP vs direct feeds, or broker internalisation.
- **Execution-risk awareness (actionable for research design, not strategy):**
  1. **H-STOP-SLIP:** realised slippage on NEXA stop-loss and market fills grows non-linearly with short-horizon volatility and around news/opening gaps. Measure from NEXA's own deal history (requested vs filled price, by volatility bucket and session).
     - Data: available (MT5 deal history; tester has no real slippage, so live/demo history is needed).
     - Look-ahead risk: none if the volatility bucket uses pre-fill data.
     - Evidence: hypothesis.
  2. **H-LASTLOOK-REJECT:** requotes/rejections cluster when price moves in the trader's favour during the latency window (last-look asymmetry; S31 Cürex).
     - Data: partial (MT5 retcodes / requote logs if retained).
     - Evidence: hypothesis.
  3. Treat backtest fills at the bar's bid/ask as **optimistic**. Add stress-scenario slippage (k × spread, k × ATR_1m) in validation, especially for stops.
- **Governance:** simplicity, explicit rules, audit trails and refusing opaque intermediaries' incentives mirror NEXA's frozen-protocol / fail-closed philosophy.

**Cross-references:**
- S32 Harris (order anticipators Ch. 11; free option of limit orders; internalisation / payment for order flow Ch. 25; flash-crash dynamics Ch. 28);
- S31 FX handbook (last look, liquidity mirage, independent TCA benchmarks, segregated desks);
- S24 (Cartea et al.: algorithms and tick size);
- S26 (algorithms predicting order flow);
- S34 (imbalance → next trade sign);
- S13 (microprice);
- S06, S10, S11 (adverse selection of resting orders);
- S27, S29 (order exposure);
- S25 (execution cost);
- S15 (FX scaling / volatility bursts);
- S38 (sampling-interval effects on measured volatility).
