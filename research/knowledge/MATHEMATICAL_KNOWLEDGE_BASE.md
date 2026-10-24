# MATHEMATICAL KNOWLEDGE BASE: NEXA research corpus

Every important equation in the 39-file corpus (38 distinct works; S37 duplicates S06), organised by topic. Batch 2 (S27–S39, added 2026-10-02) is in **§M**, cross-linked from the earlier sections where relevant. Each entry gives:
- the **equation** (as in the source; notation normalised where extraction garbled it);
- **variables**, **intuition** and **assumptions**;
- **NEXA relevance** and **limitations / failure conditions**;
- the **reference** (source, page or section);
- the **verification** status.

| Verification tag | Meaning |
|---|---|
| ✓ | Re-derived or numerically checked by us |
| V | Verified against a rendered page image |
| S | Taken as stated in the source (standard result, not re-derived) |
| ✗ | Error found in the source; the correct form is given |

**Tag meanings (from the corpus deep-learning phase):**
- SOURCE = stated in the source.
- INFERENCE = our derivation or reasoning.
- HYPOTHESIS = untested proposal.

This is **not** a strategy document. "NEXA relevance" means *possible research use*, never a claim of edge.

---

## A. Returns, volatility and scaling

### A1. Annualisation and Sharpe (S22 glossary pp. 280–281; S14; S02)
- **Equations**
  - Annualised return = mean daily return × 252.
  - Annualised Sharpe = daily Sharpe × √252 (S).
  - S14 check: 8.82 bp/day mean, 0.59 %/day SD ⇒ (8.82/59)·√252 = 2.37 ✓.
- **Assumption:** i.i.d. daily returns.
- **Limitation:** autocorrelation biases the √252 scaling (Lo 2002, cited in S16 but not applied there).
- **NEXA:** use with HAC-aware or non-i.i.d. corrections; see STATISTICAL_KNOWLEDGE_BASE §3.

### A2. FX scaling law (S15 Ch. 4; Müller et al. 1990) ✓
- **Equation:** ⟨|Δx|⟩_{Δt} = c·Δt^E.
  - Δx = log-price change over horizon Δt; E = drift exponent; c = scale.
- **Findings (SOURCE):**
  - Thomson Reuters data, 1 min – 4 years: E median 0.567 (16 of 17 pairs > 0.5).
  - Commerzbank, 0.2 s – 7 days: median 0.574.
  - Random walk and OU simulations give E ≈ 0.49–0.51, so neither reproduces E > 0.5.
- **Intuition:** E = ½ is diffusion. E > ½ is mildly super-diffusive (persistence or multiscaling).
- **Generalised Hurst:** K_q(τ) ∝ τ^{qH(q)}. The process is multiscaling if H(q) is not constant.
- **DMA:** σ²(τ) = ⟨(X_i − SMA_τ,i)²⟩ ∝ τ^{2H}.
- **Directional change (Guillaume):** N(dr) = c′·r^{E′}, with E′ ≈ −1/E.
- **Assumptions:** stationary increments within the range fitted. Log-log fits on overlapping, dependent points give R near 0.999 trivially (INFERENCE: R² is not evidence of a law).
- **NEXA (HYPOTHESIS):** convert stop and volatility horizons with Δt^{0.56–0.58}, not √Δt. Estimate H per symbol and horizon (H-HURST-GATE).
- **Failure:** weekend-gap handling biases short-Δt points. Microstructure noise at sub-minute scales.

### A3. Fractional Brownian motion (S04 Ch. 4; S18 eq. 3.2) ✓ / V
- **Covariance:** Cov(B^H_t, B^H_s) = ½(|t|^{2H} + |s|^{2H} − |t−s|^{2H}).
- **Increments:** B_t − B_s ~ N(0, |t−s|^{2H}). Paths are α-Hölder for every α < H.
- **Fractional Gaussian noise ACF:** ρ_n = ½[(n+1)^{2H} − 2n^{2H} + (n−1)^{2H}] ~ **H(2H−1)·n^{2H−2}** as n → ∞.
  - H < ½: negative, summable (anti-persistent, "rough").
  - H > ½: long memory (Σ|ρ| = ∞).
  - Power law, **not exponential**. S18's "exponentially decaying ACF" is ✗ (CONTRADICTIONS C4).
- **p-variation:** V_p = ∞ if H < 1/p; = T·E|B₁|^{1/H} if H = 1/p; = 0 if H > 1/p. Not a semimartingale for H ≠ ½.
- **Riemann–Liouville fBm:** X_t = (1/Γ(H+½)) ∫₀ᵗ (t−s)^{H−½} dW_s. Non-stationary increments.
  - S04 Def 4.5.4 writes Γ(H−½), a typo.
- **NEXA:** the language for "persistence vs anti-persistence". A price Hurst near 0.5–0.58 (S15) must not be confused with a log-volatility Hurst near 0.1 (S04).

### A4. Roughness estimator (S04 Ch. 5; Gatheral–Jaisson–Rosenbaum) V
- **Equation:** m(q, Δ) = (1/N) Σ_k |log σ_{kΔ} − log σ_{(k−1)Δ}|^q ≈ K_q Δ^{ζ_q}. Regress log m on log Δ; then the slope of ζ_q vs q ≈ H.
- **Data:** daily realised variance, Oxford-Man library 2000–2018. H ∈ [0.066, 0.140] across 30 indices (SPX 0.105) (Table 5.1, p. 37, V).
- **Bias:** daily integrated variance smooths the path, so H is biased upward.
- **Rosenbaum smoothness index:** S^p_q = (1/p)(1 + log₂(V^p_{q+1}/V^p_q)).
- **NEXA (H-ROUGH-1):** compute daily log-RV from M1 bars for XAU and FX and estimate H. Closed bars only.

### A5. RFSV and rough Bergomi (S04 Ch. 6–9; S18 eq. 3.6 ✗) V
- **RFSV:** log σ_t = X_t, with dX = ν dB^H − κ(X − m)dt, H < ½, κ ≪ 1/T. As κ → 0, E|X_{t+Δ} − X_t|^q → ν^q K_q Δ^{qH}.
- **rBergomi (risk-neutral measure Q):**
  - S_t = S₀ ℰ(∫√v dZ);
  - v_u = ξ₀(u) **exp**(η B̃_u − ½η² u^{2H}), with B̃_u = √(2H) ∫₀ᵘ (u−s)^{H−½} dW_s and Z = ρW + √(1−ρ²)W′.
  - S18 omits the exponential (✗); without it the variance can go negative.
- **Effective spot–vol correlation:** Corr(B̃, Z) = ρ·D_H, with D_H = √(2H)/(H+½) (✓). The parameter ρ is **not** the empirical spot–vol correlation.
- **Short-maturity ATM skew** (S04 eq. 9.1.1, V, mislabelled "volatility"):
  - ψ(τ) = (ρη/2)·E_H·τ^{H−½} + ¼ρ²η²σ̄·τ^{2H}·[ (D_H²/(1+H))(1 + Γ(H+3/2)²/Γ(2H+3)) − (3/2)E_H² ], with E_H = D_H/(H+3/2).
  - The leading term τ^{H−½} gives the power-law skew explosion.
  - S04 finding: the approximate skew is non-monotone in H, peaking at H* ≈ 0.08–0.11 for τ = 5–20 days.
- **Calibrations:**
  - SLSQP: H = 0.0996, ρ = −0.848, η = 1.991.
  - SRFG: H = 0.0946, ρ = −0.896, η = 1.944. Lower in-sample MSE but **worse** re-simulation error, because MC noise dominates.
- **NEXA:** no option trading, so no direct use. The *volatility-process structure* motivates log-RV/HAR forecasting (A6).

### A6. Realised volatility, HAR and evaluation (S23) V
- **Definitions:**
  - Integrated variance IV(h) = ∫_{t−h}^{t} σ²_s ds.
  - Log realised volatility RV^{(h)}_t = log Σ_{s=t−h+1}^{t} r²_s, from 1-minute mid log returns.
- **HAR (Corsi):** RV^d_{t+1} = α + β_d RV^d_t + β_w RV^w_t + β_m RV^m_t, with weekly = 5-day and monthly = 21-day averages. Long memory captured with 3 parameters.
- **HAR-D:** adds the diurnal term D_τ (the average over the last 21 days for the same intraday bucket) and lag-1 intraday RV. This is a log version of the Engle–Sokalska daily × diurnal × stochastic decomposition.
- **SHAR / HARQ:**
  - SHAR uses semivariances RV⁺ and RV⁻.
  - HARQ uses realised quarticity RQ = (M/3)Σ r⁴ to correct measurement error.
- **Commonality:** adjusted R² of RV_i on the market average RV_M = (1/N)ΣRV_j.
  - 10-min 0.56, 30-min 0.73, 65-min 0.74, 1-day 0.36.
- **QLIKE (on log RV):** mean[ exp(RV)/exp(R̂V) − (RV − R̂V) − 1 ]. Robust to noisy proxies (Patton).
- **Diebold–Mariano:** DM = d̄/σ̂_{d̄} → N(0, 1) on the loss differential.
- **Realised utility (Bollerslev et al. 2018):**
  - x* = (SR/γ)/√E_t[exp RV_{t+1}];
  - RU = (SR²/γ)·√(exp RV)/√(E exp RV) − (SR²/2γ)·exp RV/E exp RV;
  - the ideal is SR²/2γ = 4 % at SR = 0.4, γ = 2.
- **Findings (SOURCE):**
  - LSTM-augmented 10-min QLIKE 0.376 vs HAR-D 0.484.
  - At 1 day, linear ≈ NN.
  - Intraday RV (especially the last half hour) predicts next-day RV better than daily lags.
- **NEXA (H-VOL-1..4):** the most rigorous, directly portable method in the corpus. It is a *volatility* forecast, not a direction forecast.
- **Limits:** US equities. FX and XAU have a different diurnal shape (London/NY), and the 24h session needs handling of the rollover gap.

### A7. Simulation of rough processes (S04 Ch. 8; S18 Ch. 4) V
- **Cholesky:** exact; O(n³) time, O(n²) memory.
- **Hybrid scheme (Bennedsen–Lunde–Pakkanen):** power-law kernel near 0, step function elsewhere.
  - Optimal points b*_k = ((k^{H+½} − (k−1)^{H+½})/(H+½))^{1/(H−½)}.
  - O(n log n) via FFT.
- **Price step (S04 p. 56, V):** S_{i+1} = S_i + √v_i S_i ΔZ_i. This is Euler on S, not on log S, so positivity is not guaranteed.
- **Conditional Monte Carlo (S18):**
  - S′₀ = S₀ exp(−½ρ²∫σ² + ρ∫σ dW) ✓.
  - The conditional volatility must be √((1−ρ²)(1/T)∫σ²ds). S18's σ_T = √(1−ρ)σ₀ is ✗.
- **Monte Carlo noise lesson (S04 Tables 10.2–10.3):** the cost function's SD is 9.53 % of its mean at H = 0.1.
  - **INFERENCE:** when objective noise exceeds the parameter effect, the "optimum" is noise. This becomes H-NOISE-OBJ.

### A8. Practitioner volatility and trend measures (S01 Ch. 28; S21 Ch. 9) ✓ ✗
- **Directional movement:** DM_t = C_t − C_{t−N}.
- **Volatility (aggregate path):** V_t = Σ_{k=t−N+1}^{t} |C_k − C_{k−1}|.
- **INFERENCE:** the Kaufman efficiency ratio ER = |DM|/V ∈ [0, 1] measures trendiness.
- **S01 error:** the worked example (pp. 278–279, V) prints DM = 0.9 and V = 4.3; the correct values are 0.6 and 4.0 (✗).
- **S01 VB6 code bug (pp. 291–292):** it uses `Q(i).C` inside the j-loop, so it computes |C_i − SMA_N| instead of the path length (✗).
- **"Thickness":** the verbal definition is the overlap of consecutive bar ranges. The formula printed is (H₁−L₁)/(H₂−L₂), a ratio of ranges that does not measure overlap (✗ inconsistency).
  - **INFERENCE:** a proper overlap ratio is [min(H₁,H₂) − max(L₁,L₂)]⁺ / [max(H₁,H₂) − min(L₁,L₂)].
- **Thorp volatility proxy:** yearly range ÷ midpoint price. Dispersion ∝ √t ("square-root law").
- **NEXA (H-THICKNESS-ER):** ER and overlap as causal regime descriptors.

---

## B. Mean reversion and Ornstein–Uhlenbeck

### B1. OU process and estimation (S15 Ch. 2, 5) ✓
- **SDE:** dX = α(μ − X)dt + σ dW.
- **Exact discretisation:** X_{i+1} = X_i e^{−αΔ} + μ(1 − e^{−αΔ}) + σ√((1 − e^{−2αΔ})/(2α)) ε.
- **Stationary variance:** σ²/(2α). **Half-life:** ln 2/α.
- **Estimators:** regress X_i on X_{i−1} to get b̂ = e^{−α̂Δ}; then α̂ = −ln b̂/Δ and μ̂ = â/(1 − b̂).
- **Bias corrections:**
  - jackknife (Phillips–Yu): α̂_J = (n/(n−1))α̂ − Σα̂_part/(n² − n);
  - bootstrap (Tang–Chen): θ̂_B = 2θ̂ − mean(θ̂′).
- **Bias (SOURCE):** α̂ is upward-biased, O(1/T), worst near a unit root. The mean error is about +1,400 % when T = 1 yr and the reversion time is 5 yr (Table 5.2).
- **Gap biases (SOURCE):**
  - Linear weekend interpolation: σ̂ about −20 %.
  - "Business time" (dropping weekends): σ̂ about +25 %. Our check: √(168/108) = 1.247 ✓.
- **NEXA:** any half-life or "reversion speed" estimated on fewer than a few half-lives of data is unreliable. Document weekend handling (H-GAP-VOL).

### B2. OU mean absolute return (S15 eq. 4.3) ✓
- **Equation:** E|X_{t+Δ} − X_t| = σ√((2 − 2e^{−αΔ})/(πα)).
  - Small Δ: → σ√(2Δ/π). Large Δ: → σ√(2/(πα)).
- **Derivation:** the increment variance is (σ²/α)(1 − e^{−αΔ}), and E|N(0, v)| = √(2v/π).
- **Use:** OU gives a log-log mean-absolute-return curve that is linear and then flattens, which is distinguishable from the observed E ≈ 0.57 scaling.

### B3. Time-varying mean (S15; Sánchez–Gallego) ✓
- **Equation:** μ(t) = m(t) + ṁ(t)/α. Euler least squares: α̂ = Σ(Δx − ṁΔt)(m − x) / (Δt Σ(m − x)²).
- **Limitation:** both methods in S15 use a **symmetric (centred) moving average**, so they are **not causal** (look-ahead if used for trading).

### B4. MA-detrending artefact (S15 Ch. 6 + our inference) ✓
- **SOURCE:** calibrating OU to X − MA_τ gives α̂ ∝ τ^{Eα} with Eα ≈ −1, and long-run variance ∝ τ^{Evar} with Evar ≈ +1. Evar correlates 0.957 with 2H_DMA.
- **INFERENCE:** for a pure random walk, X − SMA_τ has variance ∝ τ and lag-1 autocorrelation 1 − O(1/τ). So α̂ ∝ 1/τ **automatically**: the "reversion speed" is set by the analyst's window, not the market.
- **NEXA (critical):** "price minus moving average" signals (bands, %b, distance-to-EMA) have built-in pseudo-mean-reversion for any random walk. Real reversion requires H < ½ at the trading horizon (H-HURST-GATE).

### B5. OU log-spot futures pricing (S22 eq. 462) ✓
- **Equation:** ln F(t, T) = e^{−κτ}X_t + a(1 − e^{−κτ}) + (σ²/(4κ))(1 − e^{−2κτ}), with τ = T − t.
- Commodity term structure under a mean-reverting log spot. Not NEXA-relevant (no futures curve). SOURCE: "fancy ≠ better OOS".

### B6. Multivariate OU / VAR(1) and cointegration (S25) V
- **SDE:** dR = β(μ − R)dt + σᵀdW.
  - β encodes cointegration *and* lead-lag.
  - Discretised as ΔR_t = a + ΠR_{t−1} + ε (VAR(1)/VECM).
- **Johansen trace test (S25):** rank 2 for (Z_ETH, Z_BTC, S_ETH, S_BTC). The cointegrating vectors are ≈ "pool ≈ oracle".
- **NEXA:** the toolkit for XAU–XAG or EUR/GBP spreads (HYPOTHESIS; stationarity of spreads over short windows is fragile).

### B7. Cross-sectional contrarian weights (S22 §3.9, §10.3) ✓
- **Cluster mean reversion:** D_i = −γR̃_i, with γ = I/Σ|R̃_i|; R̃ = demeaned return.
- **Futures contrarian:** w_i = −γ(R_i − R_m), Σ|w_i| = 1 (dollar-neutral automatically). Suppress by 1/σ_i or 1/σ_i².
- **Volume/open-interest filter:** v_i = ln(V_i/V′_i), u_i = ln(U_i/U′_i).
- **Multi-cluster** = regression on binary loadings; the residuals are cluster-demeaned returns.
- **NEXA:** needs a cross-section. NEXA trades a few instruments, so applicability is low.

### B8. Pairs / z-score (S22 §3.8; S20; S16)
- **Equation:** spread z = (s − SMA_n(s))/SD_n(s). Trade on |z| > k.
- **Same artefact as B4 if s is a random walk.** Requires cointegration evidence (Johansen/ADF) out of sample.

---

## C. Momentum and trend

### C1. Volatility-scaled TSMOM (S02 eq. 1–3) V
- **Portfolio return:** r_{t,t+1} = (1/N) Σ X_t^{(i)} (σ_tgt/σ_t^{(i)}) r^{(i)}_{t,t+1}.
  - σ_tgt = 15 % annualised.
  - σ = EWM SD with a 60-day span.
  - Moskowitz–Ooi–Pedersen signal: X = sgn(r_{t−252,t}).
- **Intuition:** equal ex-ante risk per asset. Vol-scaling is credited as "critical".
- **Failure:** volatility jumps (σ̂ too low makes the position too large).

### C2. Baz et al. volatility-normalised MACD and non-monotone response (S02 eqs. 4–8; S03) V ✓
- **Signal:**
  - q_t = (m(S) − m(L))/std(p_{t−63:t}), with m = EWMA, half-life HL = log 0.5/log(1 − 1/S);
  - Y = q/std(q_{t−252:t});
  - summed over (S, L) ∈ {(8,24), (16,48), (32,96)}.
- **Response:** φ(y) = y·exp(−y²/4)/0.89.
  - φ′(y) = 0 ⇒ 1 − y²/2 = 0 ⇒ y = √2 ✓. The position peaks at |y| = √2 and decays at extremes.
- **INFERENCE:** a mean-reversion-at-extremes prior inside a trend signal.
- **NEXA:** 8E momentum engines are binary. A capped or non-monotone response is a HYPOTHESIS.

### C3. TSMOM as diagonal mean–variance; tanh smoothing (S22 §10.4, eqs. 474–480) ✓
- **Weights:** w_i = γη_i/σ_i, with η_i = sign(R_i) and Σ|w_i| = 1.
- **Equivalence (verified):** w ∝ C⁻¹E with C = diag(σ²) and E_i = η_iσ_i, so w_i = η_i/σ_i.
- **Instability:** sign flips when |R| ≪ σ. Fix: η_i = tanh(R_i/κ), with κ for example the cross-sectional SD of R.
- **Dollar-neutral variants:**
  - demean: w_i = γ(η_i/σ_i − (1/N)Σ_j η_j/σ_j);
  - separate γ±;
  - or use market-demeaned returns R_i − R_m.
- **NEXA (H-TSMOM-TANH):** a continuous trend-strength descriptor.

### C4. Cross-sectional price momentum (S22 eqs. 266–270)
- **Equation:** R_cum over T = 12 months skipping S = 1 month (the skip avoids 1-month reversal). Decile long/short; weights uniform, 1/σ or 1/σ².
- **Residual momentum:** FF3 36-month regression, then 12-month residual risk-adjusted (eqs. 278–282).
- **NEXA:** needs a cross-section. Low applicability.

### C5. Multi-asset trend weights (S22 eqs. 371–373) ✓
- **Weights:** w ∝ R, R/σ, or **R/σ²**.
- R/σ² is the max-Sharpe solution with a diagonal covariance (w ∝ C⁻¹μ, μ ∝ R). It links to the μ/σ² sizing in G1.

### C6. Momentum + carry minimum-variance combination (S22 eqs. 451–452) ✓
- **Weight:** w₁ = (σ₂² − σ₁σ₂ρ)/(σ₁² + σ₂² − 2σ₁σ₂ρ), w₂ = 1 − w₁.
- Standard two-asset minimum-variance weights. Generic for combining any two NEXA signals' P&L streams.

### C7. Trend in practitioner and historical sources ✓
- **S01:** the "major trend" is the line from the first close to the last close of the chart, i.e. sign(C_T − C_0). Archer asks whether an MA adds information and answers "Not really".
  - **INFERENCE:** this is identical to the TSMOM sign (C1/C3).
- **S21 Kassouf term:** +1.015·ln(X/X̄), with X̄ = the 11-month average. Warrants on stocks above their 11-month average fit as relatively cheaper. A historical trend effect.
- **S22 MA rules:**
  - SMA; EMA with normalisation (1−λ)/(1−λ^T) ✓;
  - single, two and three-MA crossover rules (eqs. 319–324);
  - stop Δ = 2 % vs previous close.
  - SOURCE: these may be "momentum strategies in disguise".

---

## D. Indicator definitions (canonical forms)

| Indicator | Definition | Source | Notes |
|---|---|---|---|
| RSI (Wilder) | 100 − 100/(1 + RS), RS = average gain / average loss | S01 p. 71 (printed without parentheses), S22 glossary | S22 §18: RSI = ν⁺/(ν⁺ + ν⁻) = RS/(1 + RS) ∈ [0, 1], using sums of positive and negative returns ✓ equivalent (Wilder/100, except smoothing). |
| Bollinger Bands | SMA_n ± kσ_n (n = 20, k = 2; short n = 15, k = 1.5) | S09 | %b = (C − L)/(U − L). BandWidth = (U − L)/M. Squeeze = BandWidth at a 6-month low. |
| Method IV confirmed breakout | Day 1 inside band with BandWidth within 25 % of its 6-month low; Day 2 close outside; Day 3 close beyond Day 2 | S09 | — |
| Keltner / TTM Squeeze | ON when BB(20, 2σ) is inside KC(20, 1.5·ATR); "fire" when the BB exits the KC; direction from a momentum histogram | S19 pp. 30–32 V | NEXA 8E E1 uses this, but without the histogram direction. |
| Donchian channel | Max high / min low over n | S22 §3.15 | Contrarian at the band **or** breakout (both mentioned). |
| Floor pivots | C = (H + L + C)/3, R = 2C − L, S = 2C − H | S22 eqs. 325–328 ✓ | — |
| IBS | (C − L)/(H − L) | S22 §4.4 | Mean-reversion use. |
| MACD (Baz) | See C2 | S02/S03 | — |
| HP filter | min Σ(x − τ)² + λΣ(Δ²τ)², λ = 100n² (n = 12 monthly) | S22 §8.1 | **Two-sided:** look-ahead unless run recursively (INFERENCE). |
| TD Sequential | Price flip c[t−1] ≥ c[t−5]; Setup 9 closes < c[t−4]; perfection (bar 8/9 low < lows of 6 and 7); Countdown from Setup bar 9: close ≤ low[t−2], 13 counts with qualifier low₁₃ ≤ close₈; cancellation; recycle at an 18-bar setup | S17 | 6 discrepancies vs NEXA 8E code (S17 note). |
| Nofri congestion | Up, up, down, down with bar 4 inside the range of bars 1–2 ⇒ bar 5 continues the direction of bars 1–2 | S01 p. 46–47 V | No statistics. |
| Semaphore / "shape" | MAs of highs and lows, displaced back half the period | S01 Ch. 28 | **Centred:** look-ahead at the right edge. |
| EMSD | Exponential moving SD, λ = (τ−1)/(τ+1) | S22 §18 eqs. 526–527 | — |

---

## E. Dependence, lead-lag and cross-sections

### E1. Lévy area (signature) lead-lag (S14 Ch. 4, App. A.3) ✓ (our derivation)
- **Equation:** A_{i,j} = ½(S^{i,j} − S^{j,i}).
- **Theorem 1:** if R_A = β_A f + ε and R_B = β_B f + β̃_B f_{t−ℓ} + ε, with f i.i.d., then ℓ = 1 gives E[A_{A,B}] = k·β_A·β̃_B; ℓ ≠ 1 gives E = 0.
- **Our identity:** on discrete standardised returns, A = ½Σ_a(X^j_a X^i_{a−1} − X^i_a X^j_{a−1}). This is **an antisymmetrised lag-1 cross-covariance.**
  - The "nonlinear" advantage is not established, since E[f g(f)] > 0 implies a linear lag-1 correlation.
  - The estimator is blind to lags ≥ 2.
- **Ranking:** column means of the skew-symmetric matrix (≈ SpringRank).
- **Portfolio:** leaders = top 20 %, followers = bottom 20 %; the sign of the leaders' t−1 return sets the follower trade.
- **NEXA (H-LEADLAG-FX):** use the simple antisymmetric lag-1 cross-covariance on closed bars, and trade at the next bar's open.

### E2. Cross-correlation lead-lag tests (S14 eqs. 4.2–4.3)
- **C1:** argmax_ℓ Corr(R_A,t, R_B,t−ℓ). Low power when β_B > β̃_B.
- **C2:** a signed max-correlation difference. It cannot report "none", so it has false positives.
- Source defect: "size" and "power" are swapped in a footnote.

### E3. Correlation matrices, random-matrix noise and clustering (S14 Ch. 6; S22 §6.3.1) ✓
- **Correlation matrix:** C = (1/T)XᵀX. S14 prints 1/N (✗).
- **Marchenko–Pastur edge:** λ₊ = (1 + √ρ)², with ρ = N/T. Eigenvalues above it are "signal".
- **Rank:** a T-day correlation matrix has rank ≤ T − 1. S14 Ch. 6 uses a 5-day window, so rank ≤ 4 and 10–30 clusters are largely noise (INFERENCE).
- **Signed clustering:** SPONGE solves the generalised eigenproblem (L⁺ + τ⁻D⁻, L⁻ + τ⁺D⁺).
- **Statistical risk model (S22):** Γ = ξ²δ + Σ_{A≤K} λ_A V_A V_Aᵀ, with K chosen by eRank (effective rank).
- **Sample covariance (S22 fn. 62):** singular if T ≤ N + 1 and unstable unless T ≫ N.

### E4. Commonality (S23)
- See A6. The R² of single-asset RV on market RV.
- **NEXA (H-VOL-4):** a cross-symbol RV factor.

### E5. FX parity and arbitrage identities (S22 §8; S01 Ch. 24/26) ✓ ✗
- **UIRP:** E[s_{t+1} − s_t] = r_d − r_f. It fails empirically (Fama puzzle).
- **CIRP:** F = S(1 + r_d)/(1 + r_f).
- **Forward points:**
  - S01 uses the linear approximation S·Δr (105 × −0.0575 = −6.04).
  - Exact CIRP gives 105 × 1.005/1.0625 − 105 = −5.68 (INFERENCE: about 6 % overstatement).
- **Forward discount:** D = s − f ≈ r_f − r_d (HML carry quantiles).
- **Triangular arbitrage:** EUR/USD = EUR/GBP × GBP/USD ✓. Arbitrage exists when Bid·Bid/Ask > 1.
- **S01 five-currency identity** (p. 245, V): printed with "÷ GBP/CHF" (✗). Correct form: (EUR/GBP **×** GBP/CHF) × (CHF/JPY ÷ USD/JPY).
- **Rollover / carry:** daily swap ≈ short-rate differential (S01 Ch. 4).

### E6. Synthetic indices and "beta" (S01 Ch. 26) ✗
- **Mundo:** the arithmetic mean of X/USD prices in pips (JPY scaled ×1e6). Weights ∝ price level, and it is effectively an inverse-USD basket.
- **"FOREX beta" v1** = slope(OLS of price on time) / slope(market). Not beta.
- **"FOREX beta" v2** = SD(price level)/SD(Mundo). Scale- and trend-dependent.
- **Correct beta:** β = Cov(r_i, r_m)/Var(r_m) (S22 glossary: "market beta").

---

## F. Execution, microstructure and costs

### F1. Last look: the spread as an option (S11 Props 1–12) V
- **Without last look:**
  - Ω_ST = Δ (slow traders pay the half-spread).
  - Ω_LA = 2E[(P₁ − P₀ − Δ)⁺] = 2σφ(Δ/σ) − 2ΔΦ(−Δ/σ) (Prop 1). A strangle struck at ±Δ.
- **Balancing:** αΩ_LA = (1−α)Ω_ST ⇒ φ(x) − xΦ(−x) = ((1−α)/(2α))x, with Δ* = σx*. Unique for α ∈ [0, 1).
- **Small α (Prop 4):** Δ*/σ = √(2/π)·α + o(α). Spread ∝ volatility × the toxic share (Glosten–Milgrom).
- **With last look** (reject if P_e − P₂ ≤ ξ):
  - fill probability Ψ_ST = βΦ(−ξ/σ) + (1−β)Φ(−ξ/(σ√(2(1+ρ)))) (Prop 6);
  - P[LA | reject] by Bayes (Prop 9);
  - the example optimum is ξ*/σ = −2.49 and Δ*/σ = 0.065, against 0.12 without last look.
- **INFERENCE:** fills are negatively selected (rejections cluster when the trader would have profited).
- **NEXA:** backtests at 100 % fills are optimistic (H-EXEC-LL). The spread-cap ∝ ATR logic is consistent.

### F2. Optimal discretion (S10 Ch. 3–4) ✓ / S
- **Ch. 3 (LQ with ambiguity aversion):**
  - micro-price volatility dv = κ(v̄ − v)dt + σ_v v dW;
  - fill ratio dF = [λ(F̄ − F) + aδ − b(v − v̄)]dt + σ_F dW^F.
  - The value-function ansatz is quadratic. The control is δ*_t = δ̂ + (a/2φ_δ)[g₁ + g₂(F̂ − F_t) + g₃(v_t − v̄)], with g₂, g₃ > 0.
  - Discretion widens when the fill ratio is below target or volatility is above its mean.
  - Our check: σ_v enters only h₄, so it is absent from δ*.
- **Ch. 4 (FBSDE):** the fill rule is δ ≥ Z (shock).
  - Cost C = ∫∫ z·1{δ ≥ z} p(dz, dt); miss cost αD + γD².
  - Thm 2: **δ*_t = 2γE_{t−}[D_T] + γ + α**.
  - With a linear miss cost (γ = 0): **δ* = α**. Optimal slippage tolerance = cost of a miss.
  - Simulation: Z ~ N(0.1, 1), zero discretion misses about 54 % (= P(Z > 0)).
- **NEXA (H-DEVIATION-OPT):** the MT5 `deviation` parameter = discretion. Calibrate it to the expected edge forgone by a miss, never beyond the stop/ATR economics.

### F3. Flicker / slippage distribution (S10 Ch. 5, Table 5.11) S
- **Law:** ν = p₀δ₀ + p₊η₊e^{−η₊z} (improvement) + p₋η₋e^{η₋z} (slippage). Three parts: a point mass plus two exponentials.
- **Normal window:** p₋ 0.057, p₀ 0.901, p₊ 0.042.
- **±1 min around news:** p₋ 0.229, and the slippage size is about **6×** larger.
- **NEXA (H-NEWS-SLIP):** a time-varying, asymmetric slippage model in backtests.

### F4. Microprice (S13; Gatheral–Oomen) S
- **Equation:** P = (V_a·P_b + P_a·V_b)/(V_a + V_b), tilted toward the side with less queue.
- **NEXA:** **not computable** (no sizes at Pepperstone). DATA-LIMITED.

### F5. LOB adverse selection and collusion (S06) V
- **Payoff functions:** L(x) = P(J > x)·E[J − x | J > x] (latency-arbitrage payoff).
- **Half-spreads:**
  - ½p_LO p_LT s_a/2 = ½p_LO p_pub L(s_a/2) + ((N−1)/N)p_priv L(s_a/2);
  - s_a ≥ s_na, with equality iff p_priv = 0.
- **Snipe if:** p_LO δ/N > p_priv L(δ)/N.
- **Green–Porter incentive-compatibility constraint (ICC):** ρ[c(q_C − q_D)(1 − ρ^T) + g q_C + ρ^T(1 − q_C)g] ≥ g.
  - Collusion is harder with larger N and with less private information.

### F6. Algorithmic pricing (S24) S
- **Fill probability:** P(a_i) = e^{−μa_i}/Σ_j e^{−μa_j}. Payoff π = a·P.
- **Bertrand–Nash:** a_BN = I/(μ(I − 1)).
- **Discrete grid:** L* = ϑI/((I−1)(e^{μϑ} − 1)), U* = ϑI/((I−1)(1 − e^{−μϑ})). Both → a_BN as ϑ → 0.
- **Learning dynamics:**
  - replicator ẋ_k = x_k[(Πx)_k − xᵀΠx];
  - Q-learning Q̇ = x(Π + δ max Q − Q);
  - FAQ ⇒ replicator–mutation.
  - Q-learning can stick at non-Nash outcomes.
- **NEXA:** spreads can be "stuck" wider (H-SPREAD-REGIME). Allocator algorithms with convergence guarantees are preferable.

### F7. CFMM impact and optimal execution with signals (S25) V
- **Impact:** |Z − Z̃(Δy)| ≈ ½φ″(y)|Δy| = (1/κ)Z^{3/2}|Δy|.
- **HJB → Riccati.** Optimal speed ν* = (1/2η)D(ζ)⁻¹(B_ζᵀ(μ − R) − 2A_ζỹ) = signal term + Almgren–Chriss inventory term. With β = 0 it reduces to AC.
- **Empirics (our SE check):** optimal vs AC differ by ≈ $2.7k, against SE ≈ $2.9k, so they are not distinguishable.
- **NEXA:** impact scheduling is irrelevant at retail size. The signal term needs evidence.

### F8. Linear cost model and expected-return shrinkage (S22 App. A) ✓
- **Cost:** τ_i = ζσ_i/A_i (Almgren et al. 2005 form), with A = average daily dollar volume (ADDV). Normalised so that mean τ = 10 bp.
- **Shrinkage:** E_eff = sign(E)·max(|E| − τ, 0). Zero the signal when expected return < cost.
- **NEXA (H-COST-SHRINK):** a gate requiring expected move > all-in cost (spread + commission + slippage).

### F9. Turnover-penalised objectives (S02 eqs. 34–35; S03 eq. 4) V
- **S02:**
  - turnover ζ_t = σ_tgt|X_t/σ_t − X_{t−1}/σ_{t−1}|;
  - net return r̃ = (σ_tgt/N)Σ(X r/σ − c·|ΔX/σ|).
- **S03:** R_t = μ[A_{t−1}(σ_tgt/σ_{t−1})r_t − bp·p_{t−1}·|(σ_tgt/σ_{t−1})A_{t−1} − (σ_tgt/σ_{t−2})A_{t−2}|].
- **Caution:** S02 "bps" and S03 "bp" use different bases, so they are **not comparable** (CONTRADICTIONS C2).

### F10. Order-book imbalance and agent features (S26 App. B) S
- **Imbalance:** I(V_b, V_a) = log(1 + V_b) − log(1 + V_a).
- **Other features:** inventory transform sign(x)log(1 + |x|); realised volatility √(Σ|Δlog S|²); returns over 1/5/60/300 s; message counts down to 100 µs.
- **NEXA:** no depth or IDs, so NOT TESTABLE.

### F11. Fill economics in practitioner sources (S01; S08) ✓
- **Pip arithmetic:** 1 % of EUR/USD at 1.48 = 148 pips = $1,480 per 100k.
- **Position size:** units = $risk / stop distance. $500/0.0148 = 33,783 units.
- **News fill (S01):** placed at 1.4910, filled at 1.4955 (45 pips) during NFP.

---

## G. Position sizing, growth, risk and payoff mathematics

### G1. Mean-variance / Kelly sizing (S13 App. A.1; S22 §3.18; S12) V ✓
- **Derivation:** max S = Σα_jμ_j/√(Σα_j²σ_j²) ⇒ **α_i* ∝ μ_i/σ_i²**. S is scale-invariant; the second derivative is < 0.
- **Assumptions:** independent, normal opportunities with plug-in true parameters.
- **Failure (SOURCE):** epistemic σ → 0 makes α explode. Plug-in error amplifies.
- **Mean–variance portfolio:** w ∝ C⁻¹E. Dollar-neutral via a Lagrange multiplier (S22 eqs. 350–358).
- **Kelly / log-optimal (S12):**
  - growth W_n = (1/n)log(S_n/S_0);
  - BCRP b* = argmax Σlog(b·x_t);
  - semi-log approximation f(z) = z − ½(z − 1)².
- **NEXA:** can only scale *down* within the 1 %-risk hard cap (NEXA_Risk unchanged).

### G2. Volatility targeting (S22 §6.5, §15.3.1; S02) ✓
- **Weight:** w = σ*/σ̂. For HMD (healthy minus distressed): HMD* = (σ_target/σ̂)·HMD, with σ_target 10–15 % and σ̂ the prior-year realised volatility. The unlevered form is min(σ*/σ̂, 1).
- **Rebalance** when |Δw|/w > κ.
- **Mechanism (SOURCE citing the literature):** factor/momentum crash risk after high-volatility downturns.
- **NEXA (H-VOLTARGET-CAP):** apply σ*/σ̂ capped at 1, inside the hard caps.

### G3. Avalanche / pyramiding (S21 App. A, image pp. 206–207, V) ✓
- **Proportional margin m:** **P = V₀[(W₀/W_f)^{1/m} − 1]** (short in a falling price).
  - Long analogue: V₀[(W_f/W₀)^{1/m} − 1].
  - Book check: W₀ = 13 → 10, m = ½, V₀ = $6,500 ⇒ $4,485 ✓.
- **Constant per-share margin k:** **P = V₀(e^{(W₀−W_f)/k} − 1)**. Check: $10,340·(e − 1) = $17,767 ✓.
- **Derivation:** dV = −(V/(mW))dW ⇒ ln V ∝ −(1/m)ln W.
- **Risk:** the pyramided position is largest exactly at reversal. Gaps break continuous reinvestment.
- **NEXA:** caution only. NEXA's caps forbid pyramiding (contradiction across S01/S21; CONTRADICTIONS C9).

### G4. Hedge expectation bound (S21 App. C, V) ✓
- **Setup:** buy common at 0.5E and short warrants at 0.2E; then G = min(X, E) − 0.3E.
- **Weak symmetry** P(X ≥ x₀ + t) ≥ P(X ≤ x₀ − t) ⇒ **E(G) ≥ 0.2E** ✓.
- **Pacific Petroleums:** E(G) ≥ 0.16E ✓ (truncation loss ≤ 0.06E·½).
- **Principle:** harvest a priced premium while hedging direction. It needs only weak symmetry, not a forecast.

### G5. Expectancy, break-even win rate and payoff asymmetry (S01 Ch. 9; S08; S02) ✓
- **Expectancy:** E = p·R − (1 − p)·1 (in risk units). Break-even **p* = 1/(1 + R)**: 25 % for R = 3.
- **S01 campaign:** 3 × $300 − 7 × $100 = +$200 ✓.
- **S08 outside-bar:** p = 0.875, average win/loss = 0.29.
  - E per trade = 0.875·0.29 − 0.125 ≈ +0.129 (in average-loss units).
  - Only 2.4 pips gross, so a ~1-pip cost removes about 40 %.
  - **A high win rate is structural, from exit asymmetry, and negatively skewed** (INFERENCE).
- **S02:** classifiers reach about 50 % accuracy with Sharpe 0–0.3. Hit rate is a poor proxy for P&L.

### G6. Hedge ratios and minimum-variance hedging (S22 Ch. 10, 14) ✓
- **Optimal hedge ratio:** h = Cov(q, I)/Var(I) (eqs. 512–515, weather; general).
- **Conversion-factor hedge:** h_C = C·M_B/M_F. **Duration hedge:** h_D = βD_B/D_F.
- **Spark-spread hedge:** h = H·F_E/F_F, as an integer ratio approximation.
- **NEXA:** cross-hedge maths for any future XAU–XAG relative-value research.

### G7. Bond convexity facts (S22 §5.3) ✓
- **Barbell minus bullet convexity:** C − C* = w₁w₂(T₂ − T₁)²/(w₁ + w₂)² > 0 (the variance of maturities). Not NEXA-relevant.

### G8. Leverage and margin (S01 Ch. 1–2) ✓
- **Equations:** Leverage = 100/Margin %; Leverage = Position / Required Margin (USD 148k/500 = 296:1).
- **Risk-of-ruin intuition:** S19 (doubling up "only has to not work once"); S01 ("nine of ten times the bounce saves you"). This is negative skew of averaging down (INFERENCE).

### G9. Drawdown measures (S22 glossary; S16; S02/S03) S
- **MDD** = peak-to-trough decline.
- S16 cites the Magdon-Ismail Brownian MDD expectation but does not apply it.
- S03 MDD values are implausible (units), so treat them as unreliable.

---

## H. Machine learning and objective functions

### H1. Sharpe loss (S02 eq. 16) V
- **Equation:** L = −μ_R√252/√(Σ_Ω R²/M − μ_R²), pooled over the minibatch of assets × time.
- **INFERENCE:** this learns de-risking. The LSTM's E[R] ≈ benchmark at 3× lower volatility.

### H2. Heteroskedastic Gaussian NLL and MC dropout (S13 eq. 1) V
- **NLL:** L = −2Σ_i log l^{ii} + (Y − μ)ᵀLLᵀ(Y − μ), with the precision Σ⁻¹ = LLᵀ (Cholesky; the diagonal is exponentiated).
- **Epistemic covariance:** Σ̂^E = (N/(N−1))[(1/N)Σμ̂_nμ̂_nᵀ − μ̂μ̂ᵀ] over N = 30 dropout passes. Total Σ̂ = Σ̂^A + Σ̂^E.

### H3. Reinforcement learning (S03) S
- **DQN:** L = E[(Q_θ(S, A) − (r + γ max Q′))²], plus Double/Dueling variants.
- **REINFORCE:** ∇J = Σ∇log π(A|S)G_t.
- **A2C:** advantage = R + γV(S′) − V(S).
- **Setting:** γ = 0.3; training cost 20 bp acts as a regulariser.

### H4. Neural network for BTC (S22 §18.2) V ✗
- **Inputs:** normalised demeaned returns, EMA, EMSD, RSI. Hidden layers use ReLU.
- **Output:** softmax. **S22 prints Y_i/ΣY_j without exp** (✗, p. 120 rendered). The correct form is exp(Y_i)/Σexp(Y_j).
- **Loss:** cross-entropy E = −ΣΣS_α ln p_α.
- **Target:** quantile classes from the training set. Footnote 225 drops warm-up points (causal ✓).

### H5. Naive Bayes Bernoulli (S22 §18.3) S
- **Classifier:** C_pred = argmax P(C_α) Π_i Π_a P(w_a|C_α)^{X_ia}(1 − P(w_a|C_α))^{1−X_ia}. Assumes conditional independence across words and tweets.

### H6. Logit, multinomial logit, PCA and permutation importance (S26) S
- **Logit:** P(D = 1) = 1/(1 + exp(β₀ + β·x)).
- **PCA** from 53 to 30 features, fitted on weeks 1–4 only (causal).
- **Permutation importance; HAC clustering** of coefficients (cosine, complete linkage).

### H7. k-nearest neighbours single-stock (S22 §3.17) ✗ (look-ahead)
- **Rule:** k ≈ floor(√T*); 60/40 split.
- **Neighbour targets Y(t′)** for t′ = t+1…t+T* overlap the forecast horizon. A causal version needs **t′ ≥ t + T** (INFERENCE).

### H8. Stochastic approximation ODE method (S24 §1) S
- **Recursion:** x(n+1) − x(n) = γ_n f(x(n), π(n)), with Σγ = ∞ and Σγ^{1+q/2} < ∞.
- The interpolated process is an asymptotic pseudotrajectory of ẋ = F(x), under conditions C1–C3.

### H9. Kassouf warrant model (S21 App. D) ✓
- **Model:** y = (x^z + 1)^{1/z} − 1, with z = 1.307 + 5.355/T + 14.257R + 0.298D + 1.015 ln(X/X̄) + 0.405x.
- **Check (Sperry Rand):** z = 2.441 ✓ and y = 0.355 ✓.
- **Limits:** z → ∞ gives the minimum-value line; z → 1 gives the maximum-value line. An in-sample econometric fit that predates BSM.

### H10. Online learning updates (S12) S
- **Exponentiated gradient:** b_{t+1,i} ∝ b_{t,i}exp(η(x_{t,i}/(b_t·x_t) − 1)).
- **FTRL** adds −(β/2)‖b‖².
- **Aggregating Algorithm:** w ∝ w·exp(−ηℓ).
- **ONS:** b_t = b_{t−1} − ηA⁻¹∇ℓ.
- **PAMR:** ε-insensitive loss max{0, b·x − ε}.
- **CWMR:** b ~ N(μ, Σ), updated by a minimum-KL step with a confidence constraint.
- **OLMAR:** x̂ = (1/w)Σx_{t−i}.

---

## I. Derivatives (low NEXA relevance; kept for completeness)

### I1. Black–Scholes and implied volatility (S18; S22) S
- **Model:** dS = rSdt + σSdW; C = S₀N(d₁) − Ke^{−rT}N(d₂).
- **Implied volatility:** the root of BS(σ) − p̂. S18 says "minimises", which is inaccurate: Brent's method is root-finding.
- **Put-call parity:** C − P = forward payoff.
- American put bound: V_put ≤ V_call − S₀ + K + D (S22 eq. 497).

### I2. Option payoff strategies (S22 Ch. 2, eqs. 1–265) ✓ (spot-checked)
- Covered call/put, spreads, butterflies, condors, guts, collars, seagulls, ladders: all correct algebra. NEXA has no options.

### I3. Warrant bounds (S21 Ch. 2) S
- **Bounds:** max(S − E, 0) ≤ W ≤ S.
- **Normal price curves** (W/E vs S/E by months to expiry; ≈ 0.43 at S/E = 1, 24 months). Time decay is shown by the curves collapsing to the minimum-value line.

### I4. Variance swap, VIX basis, CDO (S22 Ch. 7, 11) S
- **Variance swap:** v = (F/T)ΣR² (not demeaned). **VIX basis:** D = (UX1 − VIX)/T.
- **CDO expected loss:** L = Σp_α max(min(ℓ_α, L_d) − L_a, 0).
- **CDO mark-to-market** = premium leg − contingent leg. Risky duration D = ∂M/∂S.

### I5. Tax arbitrage (S22 Ch. 13) ✓ ✗
- **Dividend imputation:** I = D(1 − τ_p)/(1 − τ_c) ✓.
- **Source error:** the text says 1 + κ = 1/(1 + τ_c); the correct value is **1/(1 − τ_c)** (✗, p. 104 rendered).

---

## J. Game theory and market design (summary)

| Topic | Key result | Source |
|---|---|---|
| Latency-arbitrage indifference | Budish logic: MM spread s.t. MM ≈ sniper | S06, S11 |
| Collusion | Green–Porter trigger, signalling via order size; harder with N↑ or less private information; batch auctions reduce it | S06 |
| Tick size | Smaller tick ⇒ lower excess profit but more frequent supracompetitive selection and slower convergence | S24 |
| Venue competition | Last-look venue may quote *wider* in equilibrium; migration boundaries are conic sections | S11 |

---

## K. Decision analysis (non-market)

### K1. AHP / weighted scoring (S05) S ✗
- **Score:** Σw_k s_k with Σw = 1, so the score lies in [1, 5] for 1–5 scores.
- **Reported tier averages** of 1.05, 0.62 and 0.18 are impossible under the stated scheme (✗).
- **AHP consistency:** CI = (λ_max − n)/(n − 1), CR = CI/RI < 0.10. The paper skips this.
- **NEXA:** caution for any hand-weighted "confluence score".

---

## M. Batch-2 mathematics (S27–S39)

### M1. GBM first-passage time to a level (S27 p. 17, V) ✓
- **Equations.** Let a = ln(S̄/S₀) > 0 and ν = µ − σ²/2 (log-drift).
  - **P(τ < ∞) = 1 if ν ≥ 0; = exp(−2a|ν|/σ²) if ν < 0.**
  - Defective density: f(t) = a/(σ√(2πt³)) · exp(−(a − νt)²/(2σ²t)) (inverse Gaussian).
  - Laplace transform: E[e^{−λτ}] = exp(−(a/σ²)(√(ν² + 2σ²λ) − ν)).
  - P(hit before T) = ∫₀ᵀ f(t)dt; the n-th hit time is an n-fold convolution (eq. 6).
- **Verification.** The conditional density with drift |ν| multiplied by P(τ < ∞) equals the defective density with drift ν ✓.
- **Intuition.** With adverse drift, a level may never be reached; with zero or favourable drift it is reached a.s., but the time can be very long (heavy t^{−3/2} tail).
- **Assumptions.** Continuous GBM; constant µ, σ; no jumps; continuous monitoring.
- **Failure conditions.** Fat tails/jumps (S35, S39 ν ≈ 8.5), volatility clustering (S23, S04), discrete bar monitoring (a bar's high/low can jump a level), spread (bid vs ask triggers).
- **NEXA relevance.** The building block for **H-HIT-PROB** (stop/target hit probabilities).

### M1b. Two-barrier exit probability for arithmetic Brownian motion (INFERENCE, standard result; links S27, S01 G5)
- **Setting.** X_t = µt + σW_t, X₀ = 0, stop at −L, target at +U. Let θ = 2µ/σ².
- **P(target first) = (1 − e^{θL}) / (e^{−θU} − e^{θL}).** (Scale-function argument with s(x) = e^{−θx}.)
  - **Driftless limit (µ → 0): P(target first) = L/(U + L).**
- **Consequence ✓.** With zero drift, a reward:risk of R = U/L gives win probability 1/(1 + R), which is **exactly the break-even win rate** p* = 1/(1 + R) of G5. **Without drift (edge), any TP/SL geometry has zero expectancy before costs; spread and slippage make it negative.** Exit geometry changes the *shape* of the payoff (hit rate vs payoff ratio), not its mean.
- **Limits.** Continuous paths; constant σ; real prices have bounce (S32, S38), gaps (S15, S01) and fat tails, which shift realised hit rates (a negative-expectancy bias for stops filled through the level, S30, S10).
- **NEXA relevance.** A null model for any TP/SL rule: a backtest's hit rate should be compared with L/(U + L) (adjusted for drift and costs) before attributing skill. Evidence level: established mathematics; its use as a NEXA null is a hypothesis (H-HIT-PROB).

### M2. Iceberg execution counts (S27) ✓
- Hits needed for a complete fill: **n\* = ⌈φ₀(1 + φ_a/φ_p)/φ_s⌉** (smaller peak φ_p ⇒ more hits ⇒ priority loss).
- Executed after n hits: h(n) = min{max(φ_p⌊nφ_s/(φ_a + φ_p)⌋, nφ_s − φ_a(1 + ⌊nφ_s/(φ_a + φ_p)⌋)), φ₀}.
- Drift–imbalance link: µ_{n+1} = µ_n + β(B_{t_{n+1}} − B_{t_n}), B = bid/(bid + ask volume). The β estimate (t = 22.45) comes from **overlapping minute-sampled 60-minute windows with no HAC correction**, so its precision is overstated (STAT KB §2).

### M3. Optimal iceberg display (S29) ✓ / S
- **Flow model.** Zero-inflated exponential f(s) = (1 − q)1{s = 0} + (q/β)e^{−s/β} for market orders, same-level limit orders, price-improving ("front-running") orders and hidden liquidity.
- **Prop 1 (closed form; proof absent in the file).** E[V^Δ] = αp·e^{−D(1−C)/α}(1 − β̂_r)[(1 − β_r)(1 − γ_r)(e^{−Δ/α} − e^{−N/α}) + 1 − e^{−Δ/α}], with ratios β̂_r = q̂β̂/(α + β̂), β_r = qβ/(α + β), γ_r = rγ/(α + γ); bound 0 < E[V] < pα.
- **Objective.** W(Δ) = (1 − E[V^Δ]/N)·µ(Δ) under the assumption that fills V and terminal price A are **independent given Δ** (omits adverse selection ✗ by our assessment).
- **Exposure decomposition.** dW/dΔ = M_market − M_priority (exposure impact vs priority gain). Imbalance with display: I(Δ) = (I₀ + Δ_rN_r)/(1 + Δ_rN_r) (sign typo in the source corrected ✗).
- **Lesson.** The choice of objective changes optimal behaviour (Prop 5): a fill-rate objective ignores the opportunity cost of misses (cf. S10 δ* = α).

### M4. Imbalance definitions across the corpus (S26, S27, S29, S34) S ✓
| Source | Definition | Notes |
|---|---|---|
| S29 | I₀ = (D_bid − D_ask)/(D_bid + D_ask) ∈ [−1, 1] | best-level depth |
| S27 | B = bid volume / (bid + ask volume) ∈ [0, 1] | B = (I₀ + 1)/2 |
| S34 | W(i) = log Σ_{j≤i} e^{V^{b,j}} − log Σ_{j≤i} e^{V^{a,j}} (V = log volume) | = log(cum. bid / cum. ask); W(1) = V^{b,1} − V^{a,1} |
| S26 | I = log(1 + V_b) − log(1 + V_a) | own and others' volumes |
| S13 | Microprice = (V_a·P_b + V_b·P_a)/(V_a + V_b) | mid tilted toward the thinner side |
- **INFERENCE ✓.** All are monotone transforms of the bid/ask depth ratio; they carry the same information at one level. **All require depth volumes, which Pepperstone does not provide (DATA-LIMITED).**
- **S34 LASSO logit:** β̂ = argmin Σ[log(1 + e^{βᵀx}) − yβᵀx] + λ‖β‖₁; AUC = P(score⁺ > score⁻).

### M5. Risk-neutral (Q) price models used for forecasting (S35) S ✗(use)
- GBM under Q: ln S_{t+Δ} = ln S_t + (r − σ²/2)Δ + σ√Δ Z.
- Variance Gamma: X = θγ_t + σW_{γ_t}, Gamma subordinator with E γ_t = t, Var γ_t = νt; S_t = S₀ exp{(r + ω)t + X_t} with ω = (1/ν)ln(1 − θν − σ²ν/2) (standard martingale correction).
- QMC star discrepancy D*_N = sup_A |#{x_k ∈ A}/N − vol(A)|; LSMC: V_n = max{Z_n, E[V_{n+1}|F_n]}.
- **✗ (as a forecasting method, INFERENCE):** under Q the drift is fixed at r, so simulated paths carry no directional information; ≈ 50 % hit rates are guaranteed by construction. LSMC is an optimal-stopping tool, not a forecaster.
- **Valid use for NEXA:** heavy-tailed (VG/Student-t) return distributions for **tail and loss-streak simulation**, not for direction.

### M6. Kalman-filter dynamic hedge ratio (S36, V) S ✗(P&L)
- State γ_t (random walk, covariance V_w); observation log S^Y_t = x_tγ_t + ε_t (variance V_e).
- Predict: P_{t|t−1} = P_{t−1|t−1} + V_w. Innovation e_t = y_t − x_tγ̂_{t|t−1}; S_t = x_tP_{t|t−1}x_tᵀ + V_e; gain K_t = P_{t|t−1}x_tᵀ/S_t; update γ̂_{t|t} = γ̂_{t|t−1} + K_te_t, P_{t|t} = P_{t|t−1} − K_tS_tK_tᵀ ✓.
- **✗ P&L error.** The paper books ε_{t+h} − ε_t with γ_{t+h} at exit. **Correct P&L for a position opened at t:** log(S^Y_{t+h}/S^Y_t) − Σ_iγ_t^i log(S^i_{t+h}/S^i_t). Re-estimation changes in γ are not trading profit; using γ_{t+h} manufactures mean reversion.
- **✗ Notation.** "log ∏ γ√S^i" (root) should be a power, log ∏ (S^i)^{γ}.
- **Causality rule.** Use the **innovation** e_t (prediction residual) for the z-score; a smoothed residual is look-ahead.

### M7. OU sampling interval and variance ratio (S38, V) ✓ / ✗
- **Model.** dq = −θq dt + σdW.
- **True intervalling effect ✓.** Increment variance over interval h: Var(q_{t+h} − q_t) = (σ²/θ)(1 − e^{−θh}) (stationary). **Per unit time: σ²(1 − e^{−θh})/(θh)**, → σ² as h → 0, decreasing in h.
  - **Variance ratio** VR(h) = (1 − e^{−θh})/(θh) < 1 under mean reversion; > 1 under positive autocorrelation (trend).
  - Equivalent to S15 B2 (mean absolute return of OU) and the S15 scaling exponent.
- **✗ Prop 1 artefact.** σ²_BH(h) = σ_q²(h)/h divides a bounded *level* variance by h, so it diverges as h → 0 regardless of the market. A buy-and-hold P&L over a fixed horizon does not depend on reporting frequency.
- **✗ Eq. 6.** LMA/SMA = exp(w′Q) holds for geometric means (means of log p), not arithmetic means of p.
- **NEXA (H-VR-SCALE).** VR(k) = Var(r_k)/(k Var(r_1)) on closed bars from M1 to H4.

### M8. EGARCH-X with skewed-t innovations and density evaluation (S39) S
- Mean: r_t = c + ρr_{t−1} + βX_t + ε_t; ε_t = σ_tε̃_t, ε̃ ~ Hansen skew-t(ν, λ).
- Volatility: log σ²_t = ω + β log σ²_{t−1} + αz_{t−1} + γ(|z_{t−1}| − E|z|).
- Estimates (MXN daily): β ≈ 0.99 (persistence), ν ≈ 8.5 (fat tails), λ ≈ 0.08 (skew); R² 0.058 → 0.276 with regressors **that may be same-day (look-ahead risk; UNKNOWN timing)**.
- **Quantile trigger.** Region R_t = {r < Q(θ | X_{t−1})} ∪ {r > Q(1 − θ | X_{t−1})}: trigger *frequency* fixed at 2θ by construction, threshold adapts to volatility.
- **Density evaluation.**
  - PIT u_t = F̂_t(r_t) ~ U(0, 1) i.i.d. under a correct model (Diebold–Gunther–Tay; Rossi–Sekhposyan bands).
  - Log score LS = Σ log f̂_t(r_t); Diks et al. (2011) test of mean log-score differences.
  - Coverage tests (Kupiec / Christoffersen) are *not* run in the source (STAT KB).

### M9. Market-microstructure accounting (S32) S ✓
- **Transaction-cost benchmark (Ch. 21, p. 84):** Estimated Cost = TradeSize × TradeSign × (TradePrice − BenchmarkPrice); sums to zero across counterparties.
- **Cost components:** explicit + implicit (spread and impact) + **missed-trade opportunity cost**.
- **Spread decomposition (Ch. 14):** total = transitory (transaction-cost; reverses; bid/ask bounce) + adverse-selection (permanent).
- **Realised spread < quoted spread** after informed flow (Ch. 13 example: quoted 0.3, realised −0.1).
- **Information aggregation (Ch. 10 box; derivation truncated in the file):** f_i = V + e_i, D_i = a(f_i − P), ΣD_i = 0 ⇒ P = mean(f_i), error (1/N)Σe_i (INFERENCE completes the derivation).
- **Unilateral search stopping rule (Ch. 19):** continue while P(better)·(expected improvement) > search cost.

### M10. Latency arithmetic (S30) ✓
- Light in fibre ≈ ⅔ c ≈ 124 miles/ms. Spread Networks 827 miles ⇒ 6.7 ms one way ⇒ **13.3 ms round trip ✓** (reported 13 ms). Microwave (≈ c, straighter) ≈ 8 ms round trip (reported).
- IEX speed bump: 38 miles of coiled fibre ⇒ 38/124 ≈ 0.31 ms ≈ **350 µs ✓** (rounded up from the 320 µs worst-case inter-exchange hop).
- "Tax" extrapolation: $29k on 10M Citigroup shares at ≈ $4 ⇒ ≈ 0.07 % of notional; applied to $225bn/day ⇒ ≈ $160M/day (author's extrapolation, not a measurement).

### M11. Execution-practice rules of thumb (S31) S
- Aggressive TWAP pays ≈ ½ spread per child versus the arrival mid; participation caps 15–20 % of volume; VWAP requires a forecast intraday volume curve (fix, day of week, month end).
- **Variance-ratio view of March 2020 (HSBC Fig. 4, V):** the ratio of 2-hour to 30-second volatility *fell* (≈ 1.35 → ≈ 1.15) as short-horizon volatility spiked: VR-type evidence that stress raises fine-scale volatility disproportionately (links M7).

### M12. Genetic-algorithm search (S33) S ✗(validation)
- Steady-state GA on EA syntax trees; fitness = equal-weighted 0–100 transforms of Net Profit, PF, MaxDD %, Stability, Sharpe (transform not given).
- **Search size ≈ 200 generations × 200 children × 12 processes ≈ 480k backtests**, with the "OOS" period inside the selection loop. Under the null of no skill, the maximum of K independent Sharpe estimates grows like σ_SR·√(2 ln K) (STAT KB §3): for K = 480k, √(2 ln K) ≈ 5.1 standard errors. **Any reported "best" is expected to look excellent by chance.**

---

## L. Cross-cutting mathematical lessons (INFERENCE unless stated)

1. **Many named indicators are transforms of the same few statistics:**
   - net change (momentum sign, "major trend", TSMOM);
   - deviation from an MA (bands, %b, z-score, MA-distance);
   - range or volatility (ATR, BandWidth, squeeze, DM/V);
   - ratios of up and down moves (RSI).
   - Redundancy is high. See NEXA_RESEARCH_KNOWLEDGE_BASE §5.
2. **Normalising by volatility appears everywhere** (S02, S03, S13, S22, S23). The choice between 1/σ (equal risk) and μ/σ² (Kelly-like) is a real modelling decision.
3. **Detrending creates mean reversion** (B4). Two-sided filters create look-ahead (D: HP, semaphore; B3: centred MA). Swing and zig-zag definitions have confirmation lag.
4. **Formula errors are common even in published or examined work.** **At least 26 confirmed mathematical/formula errors in 10 sources** (S01 ×5, S04 ×3, S05 ×1, S10 ×2, S14 ×4, S18 ×4, S22 ×2, S29 ×1, S36 ×2, S38 ×2), **plus ≥ 15 table/label/text inconsistencies** in further sources (S04, S12, S14, S16, S29, S33, S35, S39). Full list: FAILED_IDEAS §C. Re-derive before use. (This corrects the earlier batch-1 statement of "12 errors in 6 sources", which undercounted even batch 1.)
5. **Option-theoretic thinking:**
   - a quote is a written option (S11);
   - a hedged premium is harvestable (S21);
   - no-stop averaging down is a short option (S01, S19).
   - This is the unifying lens for payoff skew.
6. **Without drift there is no exit geometry that creates edge** (M1b): under a driftless diffusion, P(target first) = L/(U + L) equals the break-even win rate, so stops and targets only reshape the payoff. Edge must come from drift (prediction) or from cost/structure; exits can only lose it more slowly or quickly (costs, fills through stops).
7. **Sampling frequency is part of the measurement** (M7, S15, S23, S31): volatility, beta and "mean reversion" estimates change with bar size whenever returns are autocorrelated (bounce, trend). Always state the bar size and test the variance ratio.
8. **Imbalance-based predictability needs depth data** (M4, S26, S29, S34): every definition in the corpus is a transform of displayed bid/ask volume.
