# CONCEPT CARDS

Each card: **consensus** (what most sources agree on) · **who says what** (source IDs, see `SOURCES.md`; claim IDs in `CLAIMS.md`) · **disagreements** · **NEXA measurability** · **linked hypotheses**. Append, never overwrite.

---

## K-01 Value area / POC / VAH / VAL
- **Consensus:** VA ≈ 70 % of session volume around the POC; POC = highest-volume price ("fair value"); prior-session VA edges are reference levels; inside value = rotation, outside = imbalance (DOC-001 example 70 %; YT-004; YT-006; YT-014; S42).
- **Who says what:** YT-004 VAH = premium/resistance, VAL = discount/support, rotate edge→POC→edge (CL-006); YT-005 opening location vs prior VA = daily bias (CL-005); YT-014 poor VA ⇒ rotation through value (CL-011); YT-007 prior VA after news acceptance shifts the auction (CL-014).
- **Disagreements:** session definition (RTH 9:30–16:00 ET for YT-004/005/006; YT-005 also uses overnight 18:00–09:29 ET profile for targets). For 24 h FX there is **no** RTH — a session choice must be pre-registered (GAP-K01).
- **NEXA:** CALC — spot tick-volume profile is a validated proxy for XAU/EUR/JPY (T1), **not GBP**; futures true volume 2 y. POC fragile on bimodal days.
- **Hypotheses:** OF-03, OF-16, OF-18, HYP-007.
- **Batch 2:** the NinjaTrader VP default value area is **68 %**, and its minute-resolution profiles spread bar volume evenly across the high–low range (CL-071). NEXA keeps its pre-registered α = 0.70 with typical-price assignment (validated in T1). 68 % and even-spread are robustness variants, not new hypotheses.

## K-02 HVN / LVN
- **Consensus:** HVN = acceptance; LVN = little time/volume, "rejection", fast traverse (YT-004 CL-017; YT-013 trend-day pockets CL-010; S42/S46).
- **Who says what:** YT-007 uses prior VAH→nearest LVN as a demand zone (CL-015); YT-004 says an LVN under VAL holds on a bullish day (CL-016); YT-013 says balance **fills** LVN "caves" (CL-010); YT-002 "empty profile" = regime change to clean moves (CL-018); SRC-NOTE-001: price goes down to LVN then up.
- **Disagreements:** LVN as *traverse zone* (K-02 consensus, YT-013) vs LVN as *reaction/support* (YT-004 conditional, YT-007 zone edge, NOTE-001). YT-013's "fill" is consistent with NOTE-001's first half (price reaches the LVN) but not with a deterministic bounce.
- **NEXA:** CALC (definition must be pre-registered: smoothed density minimum, depth, bandwidth).
- **Hypotheses:** OF-05 (H-A traverse vs H-B reaction), OF-05c (conditional on HTF trend), OF-05f (fill after trend day).

## K-03 Initial balance (IB) / opening range (OR) / IVB
- **Consensus:** the first period range frames the day; breaks out of a small range tend to travel (YT-006 CL-003; DOC-001 Deep-M IVB = ORB-based projection tool; YT-007 IVB protection as target CL-044; Zarattini & Aziz ORB literature).
- **Who says what:** YT-006: IB size **relative to recent IBs** is the key variable (small ⇒ directional on accepted break; large ⇒ stays inside). YT-009 (equities): the trigger is a **2-min close** above the pre-market high with RVOL ≥ 3 SD, behind a gate (open above prior high and close) (CL-040). YT-002: two positive-GEX strikes form an IVB-like "cage" (CL-034).
- **Disagreements:** what range defines the "opening" (60-min IB, 15/30/60-min OR, pre-market range); acceptance definition (close beyond vs hold for time).
- **NEXA:** CALC on M1 (9 y). FX has no single open: anchors must be pre-registered (London 07:00/08:00 UTC, NY 13:30 UTC; COMEX gold day session 13:20 UTC).
- **Hypotheses:** OF-01, OF-02, OF-07, OF-17, OF-19.

## K-04 Absorption / exhaustion / "behind the elephant"
- **Consensus (operational, practitioner):** heavy aggressive volume at a price **without** price progress, followed by the opposite side taking control (DOC-001 blog; YT-005 CL-022/023; YT-007 CL-024; YT-006 CL-021).
- **Who says what:** YT-006 narrows absorption to **repeated reloading** of passive orders; a single large order hit is *not* absorption (CL-020) — and describes the "behind the elephant" break-and-reclaim (CL-021). YT-005 reads absorption from where aggressors sit within the candle (wick vs body). YT-007: no candle closes below the sellers' cluster.
- **Disagreements:** exact definition (single large print vs repeated reload vs candle-position heuristic); all require aggressor/passive data.
- **NEXA:** NO for the signed concept. **PROXY:** unsigned effort-vs-result (high volume, small range, wick at extreme, close back inside) on futures 1-min or tick volume.
- **Link to NOTE-001:** the "bubble near VAL, buy when price moves back above it" ≈ YT-006 behind-the-elephant / YT-005 "inversion" pattern.
- **Hypotheses:** OF-09, OF-22, OF-03a.
- **Batch 2 (2026-10-11):** the Bookmap glossary (CL-053) adds a fourth definition: large *limit* orders absorbing heavy aggressive volume. This is closest to Axia's "reloading" (CL-020) but has no repetition requirement. Bookmap's native-iceberg detection is claimed at "100 %" on CME (CL-054); synthetic icebergs are heuristic. Neither method is disclosed. **NEXA remains NO for any signed absorption.**

## K-05 Big trades / large-trader activity
- **Consensus:** large executed orders displayed as bubbles; side by colour (DOC-001 Big Trades: Ask = aggressive buyers, Bid = aggressive sellers); thresholds user-set (YT-005 uses manual filter 45 on MNQ, CL in YT-005 14:02).
- **Caveats:** large prints ≠ informed (Barclay & Warner 1993); aggregation by aggressor ID partly addresses splitting (DOC-001).
- **NEXA:** NO (no trades); PROXY via futures V/N per minute (OF-08).
- **Batch 2:** NinjaTrader Trade Detector (size or accumulation based; parameters not yet read) and Bookmap Large Lot Tracker / Market Pulse (undocumented) are further display tools. None documents a threshold that would make "big" objective.

## K-06 Delta / CVD / divergence
- **Consensus:** delta = ask-aggressor − bid-aggressor volume; CVD cumulative; divergence at extremes = warning, not a signal on its own (YT-006 CL-026); CVD continuing = hold.
- **NEXA:** NO (true); weak proxies only. **Hypotheses:** OF-11 (low priority).
- **Batch 2: VERIFIED-DOC facts (CL-049, CL-050).**
  - The industry classification rule is: at or above the ask = buy; at or below the bid = sell; inside the spread = the previous tick's side.
  - The fallback is the tick test (UpDownTick).
  - **NinjaTrader does not support bid/ask delta on spot forex at all** (no "last").
  - **Consequence for NEXA:** any delta built from Pepperstone bid/ask quotes measures *quote movement*, not aggressor flow. This weakens OF-11 and HYP-017 further. Only CME futures trades with an aggressor flag (GAP-D01) would give real delta.

## K-07 Footprint / imbalance / stacked imbalance
- **Consensus:** per-price bid×ask volume; imbalance thresholds are display conventions (S44 300 %; LuxAlgo ≈3:1); DeepCharts documents no default (DOC-001). YT-006: footprint is history; needs ladder for context (CL-025). YT-001: stacked imbalance as target (CL-029).
- **NEXA:** NO.
- **Batch 2:** the first documented defaults come from NinjaTrader:
  - imbalance ratio **1.5** (150 %) with a minimum delta of **10**, diagonal comparison by default (CL-048);
  - **no stacked-imbalance definition** (CL-051).
- Defaults across sources now span 150 % (NinjaTrader), 300 % (S44) and ≈ 3:1 (LuxAlgo); DeepCharts documents none.
- **Conclusion:** "stacked imbalance" is not a standard object. Any NEXA use must pre-register its own ratio, minimum and stack count, and it is BLOCKED anyway on spot FX.

## K-08 Gamma exposure (GEX) regime
- **Consensus (vendor/practitioner):** positive dealer gamma ⇒ pinning/mean reversion; negative ⇒ acceleration; zero-gamma as balance point (YT-002, YT-003, YT-005, YT-007; EMP mechanism Baltussen 2021, pinning Ni-Pearson-Poteshman 2005).
- **Disagreements / caveats:** dealer sign not identified from OI (S54); vendors use proprietary flips (SpotGamma "volatility trigger", MenthorQ "HVL", DeepCharts zero gamma from CBOE market-maker data); **all for SPX/NDX**.
- **NEXA:** NO for XAU/FX. **Hypotheses:** OF-12 (blocked).
- **Batch 2 (MenthorQ, CL-057–CL-066).**
  - **HVL:** the inflection of the cumulative-gamma curve = regime boundary. Above it: mean-reverting / pinning; below it: momentum. This is the same mechanism as CL-032/033 (DeepCharts zero gamma) and SpotGamma's "volatility trigger" (YT-003). **Three vendors, three names, undisclosed computations**, so levels from different vendors are not interchangeable.
  - **Call Resistance:** the max net-call-gamma strike.
  - **New coverage claim:** MenthorQ says it computes levels from CME options-on-futures for **GC and currency futures (6E/6B/6J)** and publishes "Key Levels on Forex" incl. XAU. This weakens the earlier statement "all GEX content is SPX/NDX-only".
  - **Caveats:**
    - futures levels update once daily (EOD);
    - methodology is undisclosed (OI vs volume, dealer sign, spot mapping);
    - the vendor's own FAQ still points gold traders to GLD (CL-064);
    - there is no history or backtest.
  - **Market-structure caution (NEXA analysis, not a source claim):** gold and FX options-on-futures open interest is small relative to spot/OTC FX turnover. Dealer hedging of CME options is a much smaller share of total flow than for SPX, so the prior for a GEX effect on XAUUSD/EURUSD is lower than for SPX.
- **NEXA status:** still BLOCKED@G1 for XAU/FX. Historical CME options-on-futures OI by strike (GAP-D08) would be needed to compute and test levels independently; vendor levels cannot be back-tested.
- **Batch 2, expected-move bands:** MenthorQ's "1D Min/Max" (CL-068) claims 85–87 % containment on SPX. That matches a calibrated ±1σ band (≈ 84 % one-sided) plus the variance risk premium, so it says the band is *calibrated*, not that touches are tradable. Put Support (CL-067) is the max net-put-gamma strike, the mirror of Call Resistance.
- **Batch 3: mathematics and the first controlled evidence.**
  - **Reference formula (CL-072):** Γ·OI·mult·S²·0.01 per 1 % move. Signs are a positioning *model*. The flow-signed alternative (CL-076) infers dealer side from classified trades.
  - **Implementations differ materially:**
    - GammaGEX uses S (not S²), contradicts its own sign comment and silently defaults the flip to spot (CL-077);
    - Scorsone uses flow-signed trades with Black–Scholes on futures options (CL-078);
    - FlashAlpha's flip is cumulative by strike (CL-073).
  - **Evidence (CL-075, FlashAlpha 8 y SPY):** GEX strongly tracks next-day realised vol raw (ρ −0.36), but the effect **vanishes after VIX + ATM IV** (ρ −0.03, p 0.18). DEX predicts no returns.
  - **Read-across to NEXA:** this matches T2 (volatility forecasts are dominated by persistence/IV). For XAU/FX any GEX test (OF-24) must beat implied vol (e.g. CBOE GVZ / CME CVOL, if obtainable) and lagged RV/HAR, not just a no-information baseline. Prior lowered.

## K-09 Market sequence (trend ↔ balance)
- **Who says what:** YT-013: trend days typically followed by balance days (CL-009). YT-002: expansion followed by rebalance only ≈10 % of the time (CL-031). **Direct contradiction.** S46/HYP-010 also discuss post-trend-day behaviour.
- **NEXA:** CALC (day-type classification from M1 profiles). **Hypotheses:** OF-20 (resolves CL-009 vs CL-031).

## K-10 Positioning / liquidation breaks / stop runs
- **Who says what:** YT-012: balance builds two-sided positioning; the break liquidates the losers ⇒ fast move, weak next-day follow-through (CL-013). YT-011: fast breaks of obvious lows after long holds are exit-driven and fade (CL-028). EMP: Osler 2003 (stop clustering, cascades).
- **NEXA:** CALC. **Hypotheses:** OF-06, OF-13, OF-21.

## K-11 Process: context → location → trigger
- **Consensus across all sources:** context/profile first, order flow only for timing (YT-006 CL-001; YT-002 order flow = timing; YT-003 planning then execution; YT-005 bias → levels → execution). Matches the user's five-question checklist (NOTE-001) and the report's decision pipeline.

## K-12 Order book / heatmap / icebergs / MBO vs MBP (added 2026-10-11, batch 2)
- **Definitions (Bookmap glossary, VERIFIED-DOC):**
  - liquidity = the sum of resting limit orders;
  - a sweep clears all liquidity at a price;
  - pulled liquidity = cancellations near the BBO;
  - spoofing = placing or cancelling orders to create artificial moves (illegal);
  - MBO = per-order queue data; MBP = per-price aggregate (CL-055).
- **Who says what:**
  - Bookmap: the heatmap shows "true support and resistance" (CL-056, vendor claim).
  - NinjaTrader: the Market Depth Map is a "historic and real-time visualization of the limit order book" and pairs with the Trade Detector.
  - SRC-YT-020 covers DOM and heatmap use (transcript pending).
- **Disagreements and caveats:**
  - Displayed liquidity can be pulled or spoofed. Vendors offer filters (Bookmap Tradermap Pro "filter out market maker bots") without disclosed methods.
  - Academic work (e.g. Cont, Kukanov & Stoikov 2014, order-flow imbalance) finds short-horizon predictability that decays within seconds to minutes. That is well below NEXA's M1 horizon, and its costs dominate.
- **NEXA:** **NO.** Spot FX at Pepperstone has no central limit order book: depth is LP-aggregated and broker-specific. CME depth history (MBO/MBP) is not in NEXA's data (GAP-D02).
- **Hypotheses:** none feasible. Recorded so future sources mapping to "heatmap" setups are classified quickly as BLOCKED.

## K-13 Trading-bot and MCP tooling (added 2026-10-11, batch 3; details in `TOOLING_EVALUATIONS.md`)
- **Pattern across bot videos** (YT-024/025/028, titles and chapters only):
  - LLM-assisted code generation → backtest → parameter optimisation → "incubation"/forward test → broker/webhook automation.
  - Profitability claims are unsupported (YT-025 title). Trial counts are large (CL-085).
- **NEXA already enforces stronger controls:** pre-registration, frozen hashes, holdout-once, BH/DSR, cost stress, the Risk Engine as final authority, and no trading without approval.
- **MCP servers:**
  - Trading-capable servers are a safety surface (CL-080, CL-084).
  - Data-only servers are only as good as their upstream (Yahoo is unofficial, CL-082; unnamed providers, CL-081).
- **NEXA:** no new integration is recommended. The existing `meta-trader-mcp` (trading/exec disabled, risk interceptor) remains the only MT5 bridge.

