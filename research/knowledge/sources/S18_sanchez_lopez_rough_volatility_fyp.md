# S18: Marc Sánchez López, "Rough Volatility Models" (BSc Economics final-year project, Univ. Pompeu Fabra?)
**File:** `TFG2024ECOSanchez_Rough.pdf`. 26 pp. Tutored by Prof. Elisa Alòs; Barcelona, June 2024. The faculty code EME08 suggests UPF; that inference is not stated in the file.

| Field | Value |
|---|---|
| **Source type** | Academic thesis (undergraduate) |
| **Evidence status** | Supported finding *only* for the textbook facts it restates (fat tails, the smile, rough volatility from Bayer-Friz-Gatheral). Its own simulations are illustrative, with no calibration to market data. **Contains formula errors** (verified visually). |
| **Processing** | All 26 pages read. Rendered: pp. 14 (eq. 3.6–3.7), 17 (eq. 4.6–4.7) and 21 (Fig. 10). Other figures (Q-Q plot, IV surface, fBm paths, ACFs) are described in the text. |

## 1. Content (SOURCE)
**Black–Scholes**
- dS = rS dt + σS dW (eq. 2.1).
- C = S₀N(d₁) − Ke^{−r(T−t)}N(d₂).
- Shortcomings: the EURO STOXX 50 Q-Q plot (2014–2024) shows **fat tails**; volatility is not constant.

**Implied volatility**
- BS(t, S_t, I_t) = V_t ("the wrong number in the wrong formula to get the right price", Rebonato).
- The IV surface has a **smile** and a **skew** (EURO STOXX 50, 17 Aug 2020).
- IV can be read as a weighted mean of future volatility (Alòs & García-Lorite).

**Fractional Brownian motion (Mandelbrot–Van Ness)**
- Covariance: E[B^H_t B^H_s] = ½ (t^{2H} + s^{2H} − |t−s|^{2H}) (eq. 3.2).
- H > ½: positively correlated increments (persistent, long memory).
- H < ½: negatively correlated increments (anti-persistent, **rough**).
- H = ½: standard Brownian motion.

**Riemann–Liouville fBm**
- B̂^H_t = (1/Γ(H + ½)) ∫₀ᵗ (t−s)^{H−½} dB_s (eq. 3.3).
- Its covariance involves the hypergeometric ₂F₁ (eq. 3.4).
- Its increments are **non-stationary**, unlike the fBm.

**rBergomi (Bayer, Friz & Gatheral 2016), as printed in eq. 3.6:** σ_t² = σ₀² (ν√(2H) Z_t − ½ν² t^{2H}), with Z_t = ∫₀ᵗ (t−s)^{H−½} dB_s.

**Simulation**
- Monte Carlo with a Cholesky factor of the fBm covariance: the price is the average payoff (eq. 4.2), with r = 0.
- **Conditional Monte Carlo** (Willard; Romano–Touzi): condition on the volatility path and use the BS formula.

**Results**
- **Figure 8 (call, S₀ = 100, K = 80, H = 0.15, ν = 0.4, ρ = 0):**
  - prices ≈ 20.1–20.5;
  - CMC is about 16 % faster with about 14 % lower standard deviation than MC.
- **Implied volatility by Brent's method** (bracketed root finding combining secant, bisection and inverse quadratic interpolation):
  - IV is higher for short maturity (T = 0.1) than long (T = 2);
  - the smile is steeper for H = 0.15;
  - there is no skew because ρ = 0.

## 2. Mathematical errors and caveats (verified)
1. **Eq. 3.6 omits the exponential.** The correct rBergomi variance is σ_t² = ξ₀(t) · exp( η√(2H) Z_t − ½ η² t^{2H} ), i.e. a lognormal-type forward variance. Without the exponential, the variance can go negative.
2. **Eq. 4.7, σ_T = √(1−ρ) σ₀, is wrong for the Romano–Touzi conditioning.**
   - The conditional BS volatility should be √( (1−ρ²) (1/T) ∫₀ᵀ σ_s² ds ).
   - The conditioned spot S′₀ = S₀ exp(−½ρ² ∫σ² ds + ρ ∫σ dW) is correct in eq. 4.6.
   - With ρ = 0, as in all of the author's runs, the error in the factor is masked. But the **integrated variance** should still replace σ₀.
3. **The interpretation that H < ½ means a "mean-reverting process" with an "exponentially decaying" ACF is imprecise.**
   - fBm increment autocorrelation decays as a **power law** (~ H(2H−1) k^{2H−2}), not exponentially.
   - H < ½ means anti-persistent increments (roughness at short scales). It is not the same as level mean reversion (an OU process).
4. **The "Brent's method minimises (BS − p̂)²" description is inaccurate.** `brentq` is a root-finder on BS(σ) − p̂, not a minimiser.
5. **No calibration to market data.** The author concedes this (p. 18).

## 3. Principles (SOURCE + INFERENCE)
**Established stylised facts** (consistent with S04 Rough, S14 Jin, S15 Boeker):
- fat-tailed returns;
- volatility clustering;
- a volatility smile and skew;
- rough log-volatility (H ≈ 0.1 in Gatheral-Jaisson-Rosenbaum; the value is cited, not measured here).

**NEXA trades spot CFDs, not options,** so option pricing has no direct use. The transferable part is the **volatility-process structure**:
- volatility is rough (anti-persistent at short lags) but persistent in level (long memory in log-volatility);
- implication: short-horizon volatility forecasts based on log-RV with power-law kernels (cf. HAR in S23) should beat naive ATR.

## 4. NEXA relevance
- **Hypothesis:** volatility forecasts for stop placement and regime (VEI-like) improve with rough / HAR-type log-RV models vs ATR14/ATR50. NEXA has M1 data for realised variance. A testable **volatility** (not direction) hypothesis.
- **Use S04 (Callum Rough, Imperial MSc) as the more rigorous rBergomi reference.**

**Cross-references:** S04 (rBergomi, Imperial thesis), S23 (ML volatility forecasting), S14 Jin, S15 Boeker (scaling, Hurst), S09 / S19 (volatility-compression heuristics).
