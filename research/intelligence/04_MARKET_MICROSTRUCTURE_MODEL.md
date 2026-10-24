# 04: MARKET MICROSTRUCTURE MODEL (Tier 1)

**Scope:** what NEXA trades against, what it can observe, and how microstructure enters the decision through cost c, fill quality and short-horizon state. It cannot enter as a directional oracle.

## 1. The venue NEXA actually trades on (facts)

| Fact | Evidence |
|---|---|
| Pepperstone CFDs, **market execution** (`trade_exemode = 2`), IOC filling, deviation ignored | Broker specs (S14 work, 2026-10-04) |
| An OTC dealer/internaliser counterparty, not a central limit order book | Original S32, S30, S11 (structure) |
| **Ticks are quote updates only: bid/ask, no size, no last price, no BUY/SELL flags** | MEASURED: 2.46M EURUSD and 10.84M XAUUSD ticks; flags ∈ {2, 4, 128, 1024} |
| Spreads are raw (Razor-like): EURUSD 0.2, GBPUSD 0.6, USDJPY 0.9 pips; XAU 17 points (on a Sunday) | Live symbol info, 2026-10-04 |
| Commission $7 per lot round trip (research assumption; to be confirmed at the first demo fill) | Cap-neutral plan |
| XAUUSD advertises `ticks_bookdepth = 10` (broker DOM) | Live symbol info |

**Implication (INFERENCE):**
- NEXA is a *liquidity taker* at a dealer. Its microstructure problem is **adverse selection of its own fills and the cost of crossing**, not reading a book.
- The original corpus's strongest T1 finding stands: **slow resting orders are picked off** (S06: 62.58 % sniped within about 91 µs), **and last-look rejections cluster after favourable moves** (S11, S31).
- Under market execution with IOC, NEXA's exposure is **slippage**: S14 found XAU fills up to 55 points worse than the quote.

## 2. Observable microstructure state for NEXA

| Variable | Definition | Data | Status |
|---|---|---|---|
| Spread s_t | ask − bid (points); spread/σ̂ (f28 uses spread/ATR) | MT5 ticks, M1 spread | AVAILABLE |
| Quote intensity λ_q | quote updates per second, over a trailing window | MT5 ticks (live) / M1 tick_volume (bar) | AVAILABLE (tick_volume = count per minute) |
| Quote-direction imbalance (f30) | EQ-008 | live ticks | PROXY; not reproducible offline |
| Quote-burst endogeneity | Hawkes branching ratio (EQ-035) | ticks | research-later |
| Micro-volatility | RV from 1-minute or tick mids (noise-robust: two-scale RV, EXTERNAL) | ticks | AVAILABLE (28 days plus forward) |
| Own fill quality | signed slippage (S14 `SLIPPAGE_PTS_…_ADVERSE_±x`), latency, requotes, rejections | Trade DNA (S14 demo from 2026-10-05) | AVAILABLE prospectively |
| Exchange activity | futures volume and transactions, V/N | Massive 1 min | AVAILABLE (2 y) |
| Broker book (XAU only) | depth-10 DOM, if logged | MT5 live | **NOT LOGGED.** Would need a separate approval (a logger change) |

## 3. Microstructure enters through cost and fill, formally

From EQ-025 the decision needs c/D (cost in R). Decompose the realised cost of one trade:

    c = s_entry/2 + s_exit/2 + slip_entry + slip_exit + commission + swap·(holding)

**Expected cost, conditioned on state:**

    E[c | x^E_t] = f(s_t, λ_q,t, σ̂_t, news_t, session_t, size)

**Hypotheses already in the backlog:**
- **H-NEWS-SLIP:** slippage tails grow near news.
- **H-STOP-SLIP:** stop fills worsen with short-horizon σ.
- **H-LASTLOOK-REJECT.**
- **H-DEVIATION-OPT:** now partly moot, because deviation is ignored under market execution (S14).
- **H-SPREAD-REGIME:** XAU spread takes a few discrete states.

The S14 forward check is the first dataset that can test them (2026-10-05 onward).

**Decision use (once tested):**
- abstain when E[c | x^E]/D exceeds a fixed share of the predicted gross edge;
- choose D to keep c/D bounded (HYP-024).

## 4. What microstructure *cannot* give NEXA

| Claim from the corpus | Why it does not transfer |
|---|---|
| Order-book imbalance predicts the next mid move (S13, S26, S34: AUC ≈ 0.72 at event horizon) | No depth. The horizon is seconds/events, below NEXA's 1-minute decision clock |
| Market + limit order flow explain returns (S51) | Contemporaneous, inter-dealer, needs signs and sizes |
| Iceberg detection (S27–S29) | No book |
| Client-type flow heterogeneity (S52) | Needs agent IDs |
| Footprint / imbalance / unfinished business (S44) | Needs trade side at each price |

## 5. The microstructure model NEXA can use

**A. Cost model (deterministic, per trade):** c from spec plus measured s_t, plus expected slippage, conditioned on x^E. It feeds EQ-025 directly.

**B. Execution-risk state (probabilistic):** P(adverse slip > k·σ̂ | x^E). It is trained on demo fills. The variables are:
- spread state;
- λ_q;
- σ̂;
- news window;
- session;
- XAU vs FX.

**C. Activity state (from bars, reproducible):**
- RVOL (EQ-005);
- EVR (EQ-006);
- Amihud (EQ-007);
- V/N for futures.

These describe *how* price is trading: thick vs thin, absorbing vs gapping. Their value is tested for:
- volatility (HYP-002);
- reaction near levels (HYP-003);
- execution cost (H-SPREAD-REGIME).

**D. Cross-venue anchor:** futures volume and price (Massive) as the price-forming reference for spot gold and FX. **Lead–lag at 1-minute granularity only.** The original S14 found lead–lag Sharpe decays to 0 at about 7 bp of cost, so it is a *context* variable, not a signal (H-LEADLAG-FX retained, low priority).

## 6. Falsification summary (Tier 1)

| Statement | Falsified if |
|---|---|
| Spread/quote-intensity state predicts slippage | Logistic or quantile regression on S14 fills shows no out-of-sample gain over an unconditional model (log score, BH-corrected) |
| Activity state (RVOL/EVR/Amihud) carries information beyond volatility | Nested models with HAR σ̂ show ΔQLIKE ≈ 0, and level-reaction tests show no gain over placebo |
| Tick-volume is a usable activity proxy | Hourly de-seasonalised correlation with exchange volume < 0.3 over the full 2 years (currently 0.57–0.70 on one month) |
