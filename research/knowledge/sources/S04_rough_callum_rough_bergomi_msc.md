# S04 — Callum Rough, *The Rough Bergomi Model: From Motivation to Implementation* (MSc Mathematics & Finance thesis, Imperial College London, 2022–23)
File: `212261203---Callum-Rough---ROUGH_CALLUM_01333836.pdf` · 94 pp · supervisor Dr I. Gasteratos; acknowledges JP Morgan exotics desk staff

| Field | Value |
|---|---|
| Source type | University thesis (MSc, Imperial College; **not** Oxford). Not peer-reviewed. |
| Evidence status | Theory chapters = **established** (textbook results on fBm; Gatheral–Jaisson–Rosenbaum 2018, Bayer–Friz–Gatheral 2016, Bennedsen–Lunde–Pakkanen 2017, all cited, mostly *without proof*). Own empirics = **research finding (replication)**: Hurst estimates on 30 indices (Oxford-Man RV library 2000–2018) and a single-date SPX calibration (30 May 2022). Novel "SRFG" calibration = **hypothesis-level method** (one date, one surface, no out-of-sample test). |
| Processing | Full text pp. 1–94 read (5,020 extracted lines; 1 low-text page). Text extraction garbles display math; **rendered and verified visually**: p. 37 (Fig 5.3 ζ_q vs q, Table 5.1 Hurst estimates), p. 56 (Algorithm 8.3.1 incl. Euler step), p. 64 (eq 9.1.1 ATM skew approximation + Fig 9.3). Other figures (smiles, skews, cost surfaces, heat maps, App. A.1–A.3) interpreted from captions/text only. |

## 1. Mathematics (SOURCE, with our verification notes)
### 1.1 fBm (Ch. 4)
- Cov(B^H_t, B^H_s) = ½(|t|^{2H} + |s|^{2H} − |t−s|^{2H}); H-self-similar; stationary increments B_t − B_s ~ N(0, |t−s|^{2H}).
- Fractional Gaussian noise autocovariance: ρ_n = ½[(n+1)^{2H} − 2n^{2H} + (n−1)^{2H}] ~ **H(2H−1) n^{2H−2}** (n→∞). H<½ ⇒ negative autocorrelation (anti-persistence), summable; H>½ ⇒ long memory (Σ|ρ_n| = ∞). *Verified* (standard). **Power-law, not exponential**, so it contradicts the ACF claim in S18 §ACF (recorded in CONTRADICTIONS).
- Not a semimartingale for H≠½ (p-variation argument, eq 4.1.2: V_p = ∞ if H<1/p, = T·E|B₁|^{1/H} if H=1/p, = 0 if H>1/p).
- Hölder regularity: paths are α-Hölder for every α<H (Kolmogorov–Chentsov).
- Representations: Mandelbrot–Van Ness (non-canonical), the canonical R⁺ representation (Picard), Molchan–Golosov. **Riemann–Liouville ("type 2") fBm**: X_t = ∫₀ᵗ (t−s)^{H−½} dW_s / Γ(H+½); this has non-stationary increments, but increments approach type-1 fBm for large S (Picard Thm 5.1).
- Typos found: Def 4.5.4 writes Γ(H−1/2) where (4.5.1) normally uses Γ(H+1/2); there is a sign glitch in the stated MVN variance constant. Both are cosmetic.

### 1.2 Roughness estimation (Ch. 5; Gatheral–Jaisson–Rosenbaum method)
- m(q,Δ) = (1/N) Σ_k |log σ_{kΔ} − log σ_{(k−1)Δ}|^q ≈ K_q Δ^{ζ_q}. Regress log m on log Δ for each q, then regress ζ_q on q. **Slope = smoothness s ≈ H** (monofractal if ζ_q = qH).
- Proxy: daily realised variance (Oxford-Man Realized Library, 3 Jan 2000 – 27 Jun 2018, 4,714 days).
- **Result (Table 5.1, rendered):** H ∈ [0.066 (MXX), 0.140 (SSMI)] across 30 indices. SPX = 0.105; FTSE 0.094; DJI 0.100. The estimates are slightly below GJR's (data to 2014).
  - Fig 5.3 check: ζ_q at q≈1.5 ≈ 0.158, so slope ≈ 0.105 ✓.
- Caveat (SOURCE): daily integrated variance smooths the path, so H is **biased upward**; true log-vol may be rougher still. Only q ≤ 1.5 was used (smaller than GJR's range).
- Rosenbaum smoothness index S^p_q = (1/p)(1 + log₂(V^p_{q+1}/V^p_q)) → s (Besov B^s_{p,∞}); = ½ for continuous semimartingales.

### 1.3 RFSV and rBergomi (Ch. 6–7)
- **RFSV:** log σ_t = X_t, with dX_t = ν dB^H_t − κ(X_t − m)dt, H<½, κ ≪ 1/T. Then E|X_{t+Δ} − X_t|^q → ν^q K_q Δ^{qH} as κ→0 (GJR Cor 3.1).
  - An RFSV process *appears* long-memory under classical tests while having none by construction (GJR §4). The "long memory of volatility" stylised fact is therefore questioned.
- **rBergomi (Bayer–Friz–Gatheral), under Q:**
  - S_t = S₀ ℰ(∫√v dZ);
  - v_u = ξ₀(u) ℰ(η B̃_u), with B̃_u = √(2H) ∫₀ᵘ (u−s)^{H−½} dW_s and Z = ρW + √(1−ρ²)W′.
  - ξ₀(u) = forward variance curve (from var-swap strikes: ξ_T(t) = ∂_T V^T_t).
  - Three parameters (H, η, ρ). Non-Markovian in v_t; Markovian in the infinite-dimensional state ξ_t(·).
- Classical Bergomi N-factor model (exponential kernels, OU factors) = Markovian approximation of the power-law kernel.
- **Effective spot–vol correlation** (§9.1.2, verified): Corr(B̃_t, Z_t) = ρ·D_H, with D_H = √(2H)/(H+½). D_H = 1 at H=½ and falls fast for H<0.1. So **ρ is not the spot–vol correlation** in rBergomi.
- **ATM skew, short-maturity approximation** (eq 9.1.1, rendered p. 64; Bayer et al. eq 7.6, flat ξ = σ̄²):
  ψ(τ) = (ρη/2) E_H τ^{H−½} + ¼ρ²η²σ̄ τ^{2H} [ (D_H²/(1+H))(1 + Γ(H+3/2)²/Γ(2H+3)) − (3/2)E_H² ], with E_H = D_H/(H+3/2).
  - Leading term ∝ τ^{H−½}: the **power-law skew explosion** (Fukasawa ψ ~ τ^{H−½}). Empirical SPX fit ψ ≈ Aτ^{−0.4} (GJR Fig 1.2), i.e. H ≈ 0.1.
  - Thesis text calls (9.1.1) "ATM forward volatility"; **it is the skew** (mislabel).
- **Own finding (Fig 9.3–9.4):** with ρ=−0.9, η=1.9, ξ=0.04, the approximate short-τ skew is **non-monotone in H** and peaks at H*(τ) ≈ 0.08–0.11 for τ = 5–20 business days. H*(τ) increases with τ. Implication: pushing H → 0 does not maximise short-term skew. (Model-approximation result; second order in η.)

### 1.4 Simulation (Ch. 8)
- **Cholesky:** exact, O(n³) time and O(n²) memory, but vectorises over paths, so fastest for m ≳ 10⁴ (Matas & Pospíšil).
- **Hybrid scheme** (Bennedsen–Lunde–Pakkanen):
  - power-law kernel near 0 + step function elsewhere;
  - optimal b*_k = ((k^{H+½} − (k−1)^{H+½})/(H+½))^{1/(H−½)};
  - κ=1 version (eq 8.2.7) uses bivariate normal increments; O(n log n) via FFT convolution.
- **rDonsker scheme** (Horvath–Jacquier–Muguruza): O(n log n).
- Price step (verified p. 56): S_{i+1} = S_i + √v_i S_i ΔZ_i, a forward **Euler on S, not on log S**. Positivity is not guaranteed (INFERENCE; minor, given small h).
- **"Turbocharging"** (McCrickerd–Pakkanen) was rejected after Matas–Pospíšil reported negative prices and bias for deep OTM.

### 1.5 Calibration (Ch. 10–11)
- **Cost:** c(H,ρ,η) = Σ_{30 options} (σ_mkt − σ_rB)², on grid G1. Only OTM options are used; implied volatilities are inverted from MC prices. Domain: H∈[0.01,0.49], ρ∈[−0.99,−0.01], η∈[0.5,5.5].
- **MC noise** (Tables 10.2–10.3):
  - 5y ATM price SD across 20 reruns of 200k paths = 0.34 % (H=0.1);
  - **cost-function SD = 9.53 % of its mean at H=0.1**, against 0.54 % at H=0.3.
- **SLSQP result:** H=0.0996, ρ=−0.848, η=1.991, MSE 3.73e−5; re-sim mean abs IV error 0.0063.
- **SRFG** (novel brute-force nested grids, 4 grids × 11² points): H=0.0946, ρ=−0.896, η=1.944, MSE 3.45e−5.
  - Re-sim mean abs error 0.00655, **worse** than SLSQP despite a lower calibration cost.
  - The author attributes this to MC noise: the calibration cost cannot distinguish nearby parameter sets.
- Largest errors are at 1-month maturity (1.1–1.25 vol pts), i.e. the short end the model is supposed to fit.
- **Inconsistencies found:**
  1. Table 11.6 caption repeats the SLSQP parameters (0.0996/−0.848/1.991) instead of the SRFG ones;
  2. Table 11.1 has ρ −0.848 but the caption of Table 11.2 says −0.847;
  3. the Table 10.1 header lists "80 %" twice (the second should be 90 %);
  4. there is an unresolved citation "[?]" (§8.3.3).

## 2. Principles
- **SOURCE/established:** log-volatility of equity indices behaves locally like fBm with **H ≈ 0.1** (rough, anti-persistent increments). Volatility is mean-reverting at short scales without a separate mean-reversion term. Apparent long memory can be an estimation artefact.
- **SOURCE:** a power-law kernel generates the τ^{H−½} short-maturity skew that Brownian SV models (Heston) cannot.
- **INFERENCE:** under a noisy objective, *a lower in-sample objective ≠ a better model*. A precise analogue of backtest-optimisation noise: when objective SD (≈ 9.5 %) exceeds the parameter-induced differences, the "optimum" is noise. This directly transfers to NEXA parameter selection (cf. PBO/DSR in S22/S23-type literature).
- **Limits:** equity indices only (no FX/metals). One calibration date. No out-of-sample dynamics test. Pricing-measure focus (Q). No forecasting results.

## 3. NEXA relevance
- No direct trading content (option pricing under Q; NEXA trades spot CFDs).
- **Hypothesis H-ROUGH-1 (DATA: available, from NEXA's own M1/M5 bars):**
  - Estimate H for XAUUSD / EURUSD etc. via the m(q,Δ) scaling of daily log-RV built from intraday bars, as in Ch. 5. Is FX/metal log-vol also rough (H ≈ 0.1)?
  - If yes, power-law-kernel vol forecasts (or HAR as an approximation) are theoretically justified for NEXA's volatility-regime and position-sizing inputs.
  - **Validation:** compare QLIKE out-of-sample vs HAR / EWMA (S23 method).
  - **Look-ahead risk:** RV must be computed only from bars closed before the decision time.
  - **Overfitting risk:** low (one parameter H).
  - Evidence level: hypothesis.
- **Methodological lesson (H-NOISE-OBJ):** when choosing parameters by backtest metric, measure the metric's resampling noise (bootstrap or reruns). If noise ≥ the parameter effect, do not select. This is consistent with NEXA's frozen-protocol philosophy.
- **Effective-correlation lesson:** model parameters named "correlation" may not equal empirical correlation (ρ vs ρD_H). Always verify the semantics of a parameter before mapping it onto data.

Cross-refs: S18 (Sánchez rough-vol FYP: same models; S04 corrects S18's ACF claim), S23 (HAR/QLIKE vol forecasting; RV features), S15 (Boeker: scaling laws in FX), S14 (Jin DPhil: vol/statistics), S22 (volatility strategies).
