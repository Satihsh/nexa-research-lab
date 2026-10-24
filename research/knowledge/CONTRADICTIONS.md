# CONTRADICTIONS: preserved, not resolved by fiat

Corpus: 39 files, 38 distinct works (S37 duplicates S06). Built 2026-10-02.

**Rule for this file:** every contradiction keeps **both sides** with references.
- A "Reading" line gives our INFERENCE about why the sides differ (different data, target, regime or definition).
- Where one side is simply an error, it is marked and also listed in FAILED_IDEAS.md.
- Nothing here is resolved by preferring the more prestigious source.

**Tags:**
- SOURCE = stated in a source.
- INFERENCE = our reasoning.
- ✗ = one side is a demonstrable error.

---

## A. Cross-source contradictions (substantive)

### A1. Is HFT/market-maker activity liquidity or a tax?

| Side | Claim | Sources |
|---|---|---|
| "Tax / mirage" | Spread narrowing is "illusory"; displayed liquidity vanishes when you trade; HFT front-runs, snipes stale quotes, withdraws in stress; "Scalpers Inc." adds volume without liquidity | S30 Ch. 2, 4, 6; S31 HSBC ("liquidity mirage", last look), Cürex; S06 (MMs snipe retail limit orders 62.58 % vs 0.08 %, collude on whom to trade with) |
| "Liquidity / competition" | Dealers and liquidity suppliers sell immediacy; competition and free entry drive spreads to cost; value traders make markets resilient | S32 Ch. 13–16; S24 (smaller ticks → competitive prices for convergent learners); S30 itself reports the SEC staff and HFT argument (spreads 1/16 → 1¢) |
| Mixed | Only ≈ 1/3 of registered liquidity providers behave as market makers; others are directional/opportunistic | S26 |

**Reading (INFERENCE).** Both mechanisms coexist.
- Market making narrows quoted spreads in normal conditions.
- Latency arbitrage and stale-quote sniping impose a cost on slow resting orders.
- Liquidity provision is conditional and withdraws in stress.

The quantitative split is **UNKNOWN** from the corpus:
- S30's magnitudes are unverified;
- S06 is one market and one month;
- S24 is theory.

For NEXA (a slow retail taker at an OTC dealer), the relevant consequence is **the same on both readings**: quoted spread is a lower bound on cost in fast markets.

### A2. Do last-look and rejection practices help or hurt the slow trader?

| Side | Claim | Sources |
|---|---|---|
| Helps (in equilibrium) | Last look lets the broker quote a **tighter** spread for a given share of toxic flow (Δ*/σ 0.065 vs 0.12 in the example) | S11 Props 5–12 |
| Hurts | Rejections are disproportionately the trades that moved in the trader's favour. Rejected orders leak information and are re-traded worse; last look "creates an illusion of liquidity" | S11 itself (rejection asymmetry); S31 (Cürex, HSBC); S30 (stale quotes, "phantom" liquidity) |
| Paradox | The last-look venue can quote **wider** spreads in a two-venue equilibrium | S11 multi-venue section |

**Reading.** S11 is a theoretical net-of-everything statement; S31 and S30 describe the cost borne at the moment of rejection. Both can hold. The net effect for a particular retail broker is **UNKNOWN** without fill/reject logs (H-LASTLOOK-REJECT).

### A3. Limit orders: "planned and cheaper" or adversely selected?

| Side | Claim | Sources |
|---|---|---|
| Use limits | "Limit orders = planned; market orders = impulse" | S19 p. 37 |
| Use limits | Icebergs "reduce slippage" and "maintain liquidity" | S28 |
| Adverse selection | Limit orders are free options. Fills come when price moves through you; misses when it runs away. Uninformed traders lose "whether they submit limit orders or market orders" | S32 Ch. 1, 14, 18; S06; S10 (misses adversely selected; retry costs 2.3–3.3 ticks); S27/S29 (hiding costs priority; exposure invites front-running); S31 (passive-algo P&L asymmetric) |

**Reading.** The practitioner side ignores fill-conditional drift. The academic side quantifies it. For NEXA any LIMIT-entry family must be evaluated **including the opportunity cost of misses** (S10 δ* = α; S29 Prop 5; S32 Ch. 21).

### A4. Does mean reversion around a moving average exist?

| Side | Claim | Sources |
|---|---|---|
| Yes (practitioner and backtest) | Band/%b reversals (Method III); z-score/RSI reversion with MA240 filter (Sharpe 1.39); countertrend exhaustion; OPS mean-reversion wealth (CWMR 1590×); MA rules | S09, S16, S17, S12, S01 (MA distance, ME) |
| Artefact | Subtracting an MA from **any** random walk creates OU-like reversion with α̂ ∝ 1/window. FX evidence of reversion to a constant level is "inconclusive" | S15 Ch. 4, 6 (+ our analytic check) |
| Scale-dependent | Minute-scale anti-persistence (H ≈ 0.44–0.48, Commerzbank quotes) vs daily mild persistence (H ≈ 0.50–0.59) | S15 Part 3 |
| Bounce | Short-horizon reversal is partly bid/ask bounce (transitory spread component) | S32 Ch. 14; S38 (intervalling); S14 Ch. 5 (EW overnight inflated by bounce); S12 (OPS exploits negative autocorrelation) |

**Reading.**
- The practitioner and backtest claims have no costs, OOS or nulls (FAILED_IDEAS).
- S15 does not prove reversion absent. It shows the MA construction cannot detect it.
- Real short-horizon reversal exists but is largely microstructure (bounce) and is untradeable after spread.

This is the basis of H-HURST-GATE and H-VR-SCALE.

### A5. Is trend following alive?

| Side | Claim | Sources |
|---|---|---|
| Alive | Vol-scaled TSMOM Sharpe 1.19 (sign), 2.8 (LSTM, cost-free) on 88 futures 1995–2015; a 12-month trend term even in 1960s warrant prices | S02; S21 (Kassouf ln X/X̄) |
| Dead in FX recently | FX Long and Sign(R) negative 2011–2019; only RL agents positive | S03 |
| Mostly ranging | "Markets trend 25–30 % of the time" (no citation) | S17 |
| Mildly persistent at all scales | Mean-absolute-return exponent E ≈ 0.56–0.58 > 0.5 | S15 |
| Decayed by awareness | Chart patterns "not reliable anymore because too many traders are aware" | S01 |

**Reading.**
- Different periods, assets and definitions.
- S15's E > 0.5 is compatible with weak, non-exploitable persistence once costs are counted.
- S02's period is a favourable trend regime.
- **Regime dependence is the only consistent conclusion** (STAT KB §7).

### A6. Does public order-book data predict the next move?

| Side | Claim | Sources |
|---|---|---|
| Yes | Best-level imbalance predicts next market-order sign up to ≈ 0.8; LASSO AUC ≈ 0.72 for jumps (CAC40); imbalance predicts 3–30 s price changes of spread size (INET); microprice improves forecasts | S34; S29; S13 |
| Barely | Using only public features, an algorithm's next order direction is predicted at 54 % (vs 70 % with member/algo IDs) | S26 |

**Reading.** Different targets:
- the next **aggregate market-order sign/jump** (S34);
- the next **individual algorithm's limit order** (S26).

Both agree that predictability decays within seconds or events (S13, S29, S34) and that the information lives in depth/flow data.

**NEXA has neither** (DATA-LIMITED). No contradiction for NEXA's purposes.

### A7. Long memory or roughness in volatility?

| Side | Claim | Sources |
|---|---|---|
| Rough, apparent long memory | Log-volatility increments behave like fBm with H ≈ 0.1. RFSV *appears* long-memory under classical tests while having none by construction | S04 Ch. 5–6 (GJR) |
| Long memory as modelling device | HAR (daily, weekly, monthly components) captures long memory parsimoniously and is a hard baseline; persistence β ≈ 0.99 in EGARCH | S23; S39 |
| Persistent level | "Volatility is rough but persistent in level (long memory in log-volatility)" | S18 §3 |

**Reading.** This is a dispute about **mechanism**, not about forecastability. All sides agree volatility is highly forecastable and that power-law/HAR-type kernels work. For NEXA the forecasting hypotheses (H-VOL-1, H-ROUGH-1) are unaffected.

### A8. ACF of fBm increments: power law vs exponential (✗ on one side)

| Side | Claim | Source |
|---|---|---|
| Power law ✓ | ρ_n ~ H(2H − 1)n^{2H−2} | S04 Ch. 4 (verified) |
| Exponential ✗ | H < ½ means a "mean-reverting process" with an "exponentially decaying" ACF | S18 §3 |

**Reading.** S18 is wrong (FAILED_IDEAS §C). Anti-persistent increments ≠ OU level mean reversion.

### A9. Cost tolerance of learned momentum strategies

| Side | Claim | Source |
|---|---|---|
| Fragile | Most ML edges vanish at 2–4 bps per unit turnover; at 10 bps the LSTM's Sharpe is −5.3 | S02 Exhibits 6–8 |
| Robust | DQN/A2C remain positive at 25 bp | S03 Fig. 2 |

**Reading.** The cost bases differ:
- S02 charges c on the change in vol-scaled position;
- S03 charges bp × price × change in scaled position, with additive P&L and a 20 bp training penalty.

**The numbers are not comparable as "bp".** Neither transfers to NEXA's CFD cost structure.

### A10. Is speed valuable?

| Side | Claim | Sources |
|---|---|---|
| Very | Firms pay $10.6M for 5 years of a 13 ms line and $40k/month for 2 µs; "one microsecond slower = second place" | S30 Ch. 1, 3 |
| For a patient CLOB trader, modestly | RLOS gain $5.14/€M at 10 ms vs $2.65 at 90 ms; ≈ 0.4 bp | S10 Ch. 5 |
| For an investor, not at all | 98.22 % of milliseconds are empty even in BAC; a 350 µs delay costs investors nothing measurable | S30 Ch. 7 (IEX analysis) |
| For execution choice | Slower execution beats the risk-transfer price on average (with more variance) | S31 BofA |

**Reading.** Speed is valuable to whoever competes for the **same stale quote** (latency arbitrageurs). For the slow side, the remedy is not speed but **not being the stale quote** (IEX design; avoid resting orders).

For NEXA (taker, M15+ horizons) speed is irrelevant to edge but **relevant to fill quality around news** (S10 news flicker law).

### A11. Market-maker "manipulation" of retail

| Side | Claim | Sources |
|---|---|---|
| Directional 3-day cycle | MMs trap retail, then reverse; Level I/II/III cycle | S07 (no data) |
| Microstructure only | MM strategic behaviour concerns spreads, queue, inventory, sniping and signalling, not multi-day direction | S06, S24, S26, S11, S32 |
| Stop running | Stops at round numbers "get run", but "legitimate whipsawing is many times more common than stop harvesting" | S01 (citing Osler via S22's bibliography) |
| Stop cascades | Order anticipators front-run anticipated stop-loss orders and margin calls in crashes | S32 Ch. 28 |

**Reading.** The corpus supports **stop clustering and stop-cascade dynamics** (S01, S32, Osler), but **not** a predictable multi-day manipulation cycle (UNVERIFIED).

### A12. What a squeeze is (definitional divergence)

| Definition | Source |
|---|---|
| BandWidth at its lowest level over ≈ 6 months | S09 (Bollinger, originator) |
| Bollinger Bands (20, 2σ) inside Keltner Channels (20, 1.5 ATR); "fire" when they exit; direction from a momentum histogram | S19 (Carter); **NEXA 8E E1 uses this** |

**Reading.** NEXA's "Squeeze UNPROVEN" result applies to the S19 definition **without** the momentum-histogram direction. The S09 definition and the S19 fire-plus-histogram variant are untested (backlog).

### A13. TD Sequential: canonical rules vs NEXA's implementation

S17 is the originator's specification. NEXA 8E's code differs in 6 ways:
1. flip inequality;
2. countdown start;
3. bar-13 qualifier;
4. cancellation (a);
5. recycle;
6. perfection.

**Reading.** NEXA's "TD veto CONTRADICTED" verdict concerns the simplified veto, not canonical TD as an entry (S17 note).

### A14. Momentum look-back

| Claim | Source |
|---|---|
| "A 10-day MOMP replicating Jegadeesh (1993)" | S20 |
| Jegadeesh–Titman momentum uses 3–12-month formation (12-1 with skip) | S22 §3.1; S02 (12-month benchmark) |

**Reading.** S20 is incorrect (✗).

### A15. "Cross-validation = out-of-sample testing"

| Claim | Source |
|---|---|
| Cross-validation equated with out-of-sample testing | S22 glossary p. 290 |
| Time-series OOS needs rolling/walk-forward train → deploy without leakage | S23, S26, S02, S13; S34 (split chronology UNKNOWN) |

**Reading.** For autocorrelated data, plain k-fold is not out-of-sample (STAT KB L4, L14).

### A16. Does HFT raise volatility?

| Side | Claim | Sources |
|---|---|---|
| Yes | Intraday volatility 2010–13 ≈ 40 % above 2004–06; front-runners profit from volatility; mini flash crashes; HFT encourages fragmentation | S30 Ch. 4 |
| Mechanism-neutral | Volatility = fundamental + transitory. Transitory volatility comes from uninformed liquidity demand and falls with resilient liquidity supply | S32 Ch. 20 |
| Measurement | Faster sampling *measures* more volatility under mean reversion (intervalling), but "faster trading raises buy-and-hold volatility" is an artefact | S38 |

**Reading.** S30's figure is a before/after correlation spanning the 2008 crisis aftermath, with no controls. S38's theory does not support the causal claim. **UNKNOWN** from the corpus.

### A17. Profitability of the "basic" warrant hedge vs edge decay

| Claim | Source |
|---|---|
| > 25 %/yr for 17 years (1946–66); author record 5 years, no losses | S21 |
| "When enough money is invested in the basic system it will be ruined"; capacity $4.6–15M | S21 itself |

**Reading.** Not a contradiction but a **self-limiting edge**. The return claim is in-sample and self-reported. The decay warning is the durable principle.

---

## B. Internal contradictions within single sources (preserved; detail in the source notes)

| # | Source | Contradiction | Status |
|---|---|---|---|
| B1 | S01 | Authors "make more bad trades than good" / "assume you lose 70 %" **vs** 14/17 showcased winners | Selection bias |
| B2 | S01 | "Good traders do not pyramid… suicide" **vs** scaling in (Ch. 11) and Shanghai BC pyramiding | Preserved; S21 avalanche maths explains both: compounding up, maximal size at reversal |
| B3 | S01 | Trader-profile R:R stated 1:3 vs implied 1:1.7–1:10; chart sets differ across chapters; trade #14 "50 pips" vs +59 | ✗ (inconsistency) |
| B4 | S01 | Thickness formula vs verbal definition | ✗ |
| B5 | S04 | SRFG lower calibration cost but **worse** re-simulation error than SLSQP | Explained by MC noise: the lesson H-NOISE-OBJ |
| B6 | S05 | Weighted sum of 1–5 scores with Σw = 1 cannot give tier averages 1.05 / 0.62 / 0.18 | ✗ |
| B7 | S12 | "Best Stock = perfect hindsight" vs equation (yesterday's best) | ✗ (mislabel) |
| B8 | S14 | Ch. 4 claims the Lévy area captures *nonlinear* lead-lag **vs** its own Thm 1 (≡ antisymmetrised lag-1 cross-covariance) | ✗ (claim not established) |
| B9 | S14 | Ch. 5 text "night premia smaller than when the market is open" **vs** Table 5.3 (+0.38 overnight vs −0.15 intraday) | ✗ |
| B10 | S14 | Footnote defines size and power backwards; p-value 0.2919 in table vs 0.284 in text | ✗ |
| B11 | S16 | Monte Carlo 20,000 vs 10,000 paths; sensitivity numbers in text ≠ tables; "confirming H1" while discussing H2 | ✗ |
| B12 | S29 | Text Δt = 10 s vs captions 30 s (Figs 8–9); gain "massively on the trader's side" vs caption "opposite-side imbalance" | ✗ |
| B13 | S33 | Abstract: multi-processor "outperformed all single runs" **vs** conclusion: "outperformed by using a single processor" | ✗ |
| B14 | S35 | Table 2 titled "QMC" with "Mean QMC / Mean LSMC" columns; text attributes Table 3's numbers to Table 2; Tables 4 and 8 swapped headers | ✗ |
| B15 | S36 | Kalman 19.3 %/yr, Sharpe 3.30 vs rolling OLS 2.5 %, same signal family | Explained by the P&L accounting error (FAILED_IDEAS) |
| B16 | S38 | Model is non-stationary as written (transient e^{−2θ(t+h)}) **vs** later stationarity assumption | ✗ |
| B17 | S39 | "Rule-based strategies outperform the minimum-rate strategy": the table shows they outperform the **no-minimum** strategy | ✗ (typo) |
| B18 | S39 | Notation Q(r_t \| X_{t−1}) vs regressors described as same-day aggregates | UNKNOWN which applies (look-ahead risk) |
| B19 | S22 | Glossary softmax (correct, with exponentials) vs eq. 535 "softmax" without exponentials | ✗ |
| B20 | S20 | Claimed 18–22 % cost reduction cites an Investopedia landing page; Chan–Jegadeesh–Lakonishok "2019" cites a 1996 DOI | ✗ (citation) |
| B21 | S24 | Unedited "INTERNAL NOTE" in App. B speculating fast MMs prefer to be slow | Draft artefact, not a result |
| B22 | S32 | The file title promises the book, but the file holds only chapter openings | File-content limitation (not an error by the author) |

---

## C. Contradictions between the corpus and NEXA's prior project facts

These are facts from NEXA memory/results, not from the corpus.

| # | Corpus | NEXA fact | Reading |
|---|---|---|---|
| C1 | S19 TTM squeeze presented as powerful ("one red dot as powerful as 20") | 8E E1 Squeeze **UNPROVEN** (51 % of bases better than random; −0.31R) | Consistent with "unverified claim"; the untested variants remain in the backlog |
| C2 | S17 TD exhaustion "4–5 tops/bottoms a year" | 8E TD veto **CONTRADICTED** (adds no information) | Different implementation and use (C-A13) |
| C3 | S02/S03 momentum edges | 8E momentum improves on base but **not net-positive**; Donchian negative on EUR/GBP | Consistent with cost fragility (S02) and FX trend failure (S03) |
| C4 | S07 EMA 5/13 entries | 8E MACD(5,13,4) not net-positive | Same family |
| C5 | S13/S26/S29/S34 imbalance/microprice | NEXA tick audit: Pepperstone has **no depth volumes**; OFI **NOT TESTABLE** | DATA-LIMITED |

**Count:** 17 cross-source contradictions or tensions (§A), 22 within-source contradictions (§B) and 5 corpus-vs-NEXA tensions (§C).
