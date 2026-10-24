# S51 & S52: order-flow papers (new corpus)

## S51: Kozhan, Moore & Payne (2018), "Market order flows, limit order flows and returns: theory and evidence"
**File:** `ssrn-2403000.pdf`, 51 pp. Main text, tables and figure captions read.
**Status:** academic working paper (SSRN), established authors in FX microstructure. **RESEARCH FINDING**.

**Model (SOURCE, §2):**
- **Setup:** an extension of Naik–Neuberger–Viswanathan (1999). The informed dealer MM0 sees a customer order y = x + u, with signal x = w + v, and E[w|x] = φx where φ = σ_w²/(σ_w²+σ_v²).
- **Choice:** MM0 picks a market-order quantity D_M and a limit-order quantity D_L. The limit order executes with probability q.
- **Price schedule:** p₂ = α + βD_M + δD_L. In equilibrium α = 0 and β = θ(σ_U²/K + 2ησ_I²)/(2(1−2η)).
  - δ = qη(β+θσ_I²)/(1−η) = qβ − qθσ_U²/K/(2(1−η)), as printed, eq. 12.
- **Proposition 1:**
  - β, δ > 0;
  - β > δ;
  - δ/β ≤ q, tending to q as K → ∞;
  - δ/β falls as risk aversion rises.
- **Omitting limit flow biases β** by δ·cov(D_M, D_L)/var(D_M). Because the correlation is negative empirically, the bias is downward.

**Evidence (SOURCE, §3–4):**
- **FX sample:** Reuters D3000 inter-dealer data, GBP/USD and GBP/EUR 2003–04, with full order-book reconstruction.
  - A 14-pair proxy sample for 2003–14 uses trade *counts* and quote-change counts in place of sizes.
- **Equity sample:** FTSE-100, Q1 2015, 30-minute bars.
- **Contemporaneous regression:** Δp_t = β₀ + β_ir·Δir_t + β_mo·mo_t + β_lo·lo_t.
  - **Daily:** β_mo = 281 bp per $1bn, β_lo = 108 bp, so δ/β ≈ 0.38.
  - **Hourly:** δ/β ≈ 0.50.
- **corr(Δp, mo):** 0.25–0.56. corr(mo, lo) is negative in 13 of 14 pairs.
- **Equities:** adding limit flow raises R² from under 10 % to over 50 %. The market-flow coefficient is biased about −25 % without limit flow.
- **IV robustness:** instruments are weak for most pairs. The authors favour OLS because Durbin–Wu–Hausman mostly does not reject exogeneity.
- **Average limit-order execution probability:** 0.36 for GBP/USD and 0.27 for GBP/EUR.

**Critical reading (INFERENCE)**

1. **Contemporaneous, not predictive.** Every regression explains Δp_t with flows measured over the *same* interval. Nothing here shows that order flow at t predicts returns at t+1.
   - For a trading system the relevant object is E[Δp_{t+1} | flows ≤ t], which this paper does not test.
   - The finding supports order flow as a *state/explanatory* variable (price formation), not as a forecast.
2. **The data are inter-dealer, with IDs and sizes.** NEXA has none of this:
   - no trade signs;
   - no limit-order arrivals or cancellations;
   - no depth.
3. **The 14-pair proxy (trade counts, quote-change counts) is the closest analogue** to anything derivable from public bars.
   - "Number of best-price increases not due to a transaction minus decreases" is a quote-event count. NEXA's tick data (bid/ask, about 28 days) could approximate it, but the transaction flag is unknown at a CFD broker.
4. **Robust lesson for NEXA:** signed flow and price change are jointly determined. Any "delta" proxy built from price movement, such as the tick rule or bulk-volume classification, is *mechanically* correlated with the same-bar return.
   - That correlation is an identity, not evidence of information. **It is a look-ahead trap whenever same-bar proxy delta is used to "explain" the same bar.**

## S52: Cont, Cucuringu, Glukhov & Prenzel (2021), "Analysis and modeling of client order flow in limit order markets"
**File:** `ssrn-3997109.pdf`, 32 pp. Main sections read.
**Status:** Oxford / JP Morgan, proprietary broker data. **RESEARCH FINDING** (descriptive).

**Content (SOURCE)**
- **Signed-measure representation of the order book:** μ on ℝ₊ × δℕ × A (time, price, agent). Three views:
  - **public:** queue sizes Q_p = Σ_α μ;
  - **broker:** its own clients plus an aggregate "Δ";
  - **omniscient.**
- **Clustering method:** spectral clustering (RBF kernel, Laplacian eigenmaps, then K-means) of STOXX-600 parent-order features per ticker-month. K = 4 is chosen by ARI agreement with K-means (0.80) and a variance elbow.
- **The four agent types:**
  - **C-Quant:** many small orders throughout the day; highest cancellation rate; closest to best price; positive trade-to-close P&L.
  - **C-Day-VWAP:** pre-open orders, passive VWAP, few cancellations.
  - **C-Signal:** afternoon around the US open; large orders; dark venues; best 20-day P&L.
  - **C-Res:** the mixed residual cluster.
- **Stability:**
  - agents land in the same cluster about 80 % of the time (entropy ≈ 0.4 vs a maximum of 1.39);
  - meta-clusters are nearly perfectly separated across tickers and months.
- **Cross-component net-inventory and OFI correlations are about 0, insignificant, average p ≈ 0.25.** The flow types are close to independent.
- **OFI normalisations:** OFI = Σ q_exec / Σ |q_exec|, and OFI_ADV = Σ q_exec / ADV₂₀.

**Critical reading (INFERENCE)**
1. **Heterogeneity is real**, but it can only be seen with agent IDs. **NEXA cannot observe agent types.**
2. **The method is transferable:** "normalise flow by own gross flow" vs "by ADV" are two different questions. The second is the economically meaningful one, impact relative to normal activity. This informs 13_NORMALIZATION and the Delta / expected-Delta construction.
3. **Diurnal agent timing** (VWAP at the open, "signal" flow at the US open) gives a microstructural *reason* why session/time-of-day conditioning may carry information. This supports H-SESSION-SPLIT as a mechanism, not as an edge.
4. **The hypothetical P&L is gross, has no costs, and is computed from execution price to close.** It is not evidence of a tradable edge.
