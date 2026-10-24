# S11: Cartea, Jaimungal & Walton, "Foreign Exchange Markets with Last Look"
**File:** `Foreign-Exchange-Markets-with-Last-Look-Mathematics-and-Financial-Economics.pdf`. 40 pp. SSRN 2630662. Published in *Mathematics and Financial Economics*.
**Affiliations:** Oxford (Mathematics, OMI), Toronto (Statistics) and UCL.

| Field | Value |
|---|---|
| **Source type** | Oxford / university research. Peer-reviewed journal (M&FE); the file is the SSRN manuscript. |
| **Evidence status** | **Established theoretical result** (closed-form derivations with proofs). **No empirical test.** The model's predictions are theoretical. |
| **Processing** | All 40 pages read, including Appendix proofs A.1–A.9. Rendered: pp. 11, 12 and 14 (Props 1, 4, 5 and the balancing equation). Figures 2–7 are interpreted from the text. |

## 1. Setting (SOURCE)
- **OTC/ECN FX market.**
  - **Brokers:** risk-neutral, zero expected profit.
  - **Traders:** latency arbitrageurs (LAs, a fraction α) and slow traders (STs), who see the updated quote with probability β.
- **Mid-price:** P_{i+1} − P_i = σ Z_{i+1}, with (Z₁, Z₂) bivariate normal with correlation ρ.
  - ρ > 0 is momentum, e.g. from "spamming": hitting many venues at once.
  - ρ < 0 is mean reversion.
- **Stale quotes:** brokers allow trades on them, to attract flow.
- **Last Look:** the broker may reject a trade ex post at i = 2 if her loss is beyond a threshold ξ < 0.

## 2. Mathematics (verified)
**Without Last Look**
- **Profit from STs:** Ω_ST = β∆ + (1−β)E[P₁ − P₀ + ∆] = ∆.
- **Expected loss to LAs:** Ω_LA = E[(P₁ − P₀ − ∆)⁺ + (P₀ − P₁ − ∆)⁺] = 2E[(P₁ − (P₀ + ∆))⁺]. This is a **strangle / two calls** struck at ± the spread.
- **Proposition 1:** Ω_LA = 2σφ(∆/σ) − 2∆Φ(−∆/σ).
- **Balancing (Cor. 2):** α Ω_LA = (1−α) Ω_ST gives φ(x) − xΦ(−x) = ((1−α)/(2α)) x, with ∆* = σ x*.
  - The solution is unique iff α ∈ [0, 1) (Prop. 3). The proof uses the convexity of f(x) = φ(x) − xΦ(−x).
- **Proposition 4 (small α):** ∆*/σ = √(2/π) α + o(α).
  - This links to Glosten–Milgrom: spread ≈ α × (value range), using E|Z| = √(2/π).
- **Intuition:** the spread is the price of the free option the broker writes by quoting. It is proportional to volatility and to the share of fast, informed flow.

**With Last Look** (reject if P_e − P₂ ≤ ξ for a buy)
- **ST cost when updated:** ∆Φ(−ξ/σ) (eq. 7).
- **ST cost when stale:** σ√((1+ρ)/2) φ(ξ/(σ√(2(1+ρ)))) + ∆Φ(−ξ/(σ√(2(1+ρ)))) (eq. 8).
- **Proposition 5:** Ω_ST = σ(1−β)√((1+ρ)/2) φ(·) + ∆[βΦ(−ξ/σ) + (1−β)Φ(−ξ/(σ√(2(1+ρ))))].
- **Proposition 6, ST execution probability:** Ψ_ST = βΦ(−ξ/σ) + (1−β)Φ(−ξ/(σ√(2(1+ρ)))).
- **Proposition 7:** Ω_LA = 2(B(∆̃) − A(∆̃)∆̃)σ, with A and B given via the bivariate normal (eqs. 13–14).
- **Proposition 9:** P[LA | reject] = α(1 − Ψ_LA)/(1 − (αΨ_LA + (1−α)Ψ_ST)), by Bayes.

**Asymptotics (Props 10–12):** ∆*/σ = ∆̃₀ + ∆̃₁α + o(α), with ST costs and LA profits linear in α.

**Multi-venue equilibrium (Def. 13)**
- No-migration conditions with switching cost c.
- The equilibrium boundaries are **conic sections**: hyperbolae or parabolas through (0, 0) and (M, N).
- Migration ODEs (30); simulations in Table 1 and Figs 6–7.

## 3. Results (SOURCE, model-implied)
- **Last Look lowers the quoted spread for a given α.** A stricter threshold gives a tighter spread but more rejections.
- **Momentum (ρ > 0) makes Last Look more effective** at catching LAs, so spreads are tighter. Mean reversion (ρ < 0) works the other way.
- **Rejected trades are disproportionately the ones that moved in the trader's favour.** The trade-off for slow traders:
  - lower spread;
  - but lost profitable fills, immediacy cost and possible front-running.
  - The example optimum is ξ*/σ = −2.49, ∆*/σ = 0.065, against 0.12 without Last Look.
- **Two venues:** the outcome is coexistence or one survivor, depending on the starting LA proportions. Paradoxically, the Last Look venue can quote **wider** spreads in equilibrium.

## 4. Principles and assessment
- **SOURCE:** a quote is an option. Spread ∝ σ × (fraction of toxic flow). Latency arbitrage is a tax on slow traders.
- **INFERENCE: retail brokers (incl. CFD brokers like Pepperstone) can and do reject or requote on adverse moves** (MT5 "requote" / "off quotes" are last-look-like). The **fill probability is correlated with the subsequent price move.** This is a hidden cost that backtests ignore.
- **Assumption limits:** Gaussian increments, a single period, risk-neutral brokers, no inventory costs.

## 5. NEXA relevance
- **Execution realism (hypothesis H-EXEC-LL):** in live trading, rejected or requoted orders are more likely when the market has just moved in NEXA's favour. The live fill rate conditional on favourable micro-moves should be logged.
  - NEXA's Trade DNA journal can record requotes/rejections, *once live or demo forward-testing is approved*.
  - The backtest assumes 100 % fills at the stale-safe price, which is **optimistic** by this mechanism.
- **Spread–volatility proportionality** (∆* ∝ σ) supports NEXA's empirical finding that XAU spreads widen at rollover and news. The ATR-relative spread cap in the EA (≤ 15 % ATR) is consistent with this.
- **Momentum vs mean-reversion regimes change effective trading costs.** Interesting but not directly testable without broker-side data.

**Cross-references:** S06 (LOB signalling and latency, same group), S24 (market-maker algorithms), S10 / S26 (execution under uncertainty), S01 Forex Essentials (practitioner FX market structure).
