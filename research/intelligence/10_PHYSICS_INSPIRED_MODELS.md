# 10: PHYSICS-INSPIRED MODELS (Tier 5)

**Rule (directive §6):** separate
- **PHYSICAL LAW**, which markets do not obey;
- **MATHEMATICAL ANALOGY**, which borrows a formalism;
- **EMPIRICAL MARKET RELATIONSHIP**, which is measured.

A physics construct is retained only if it yields a measurable, testable advantage over the simpler statistic it reduces to.

| Physics idea | Category | Exact market translation | Reduces to | Test / verdict |
|---|---|---|---|---|
| **Diffusion** | ANALOGY → standard maths | Arithmetic or geometric Brownian motion as the *null* | EQ-024/034 (two-barrier probabilities) | **KEPT as null.** Already used. Empirical deviation: FX scaling exponent 0.56–0.58 (S15), rough volatility (S04) |
| **Energy** | ANALOGY (weak) | "Market energy" = price displacement × volume × volatility × flow? **No conserved quantity and no equation of motion exist** | The only principled additive "energy-like" quantity is **quadratic variation** RV = Σ r² (additive under zero drift, S48 App. A.2) | **Name REJECTED.** RV is kept (EQ-001). A composite "energy" index is rejected as an unfalsifiable mixture (18) |
| **Potential field / energy landscape** | ANALOGY | U(p) = −ln L(p) from the revealed-liquidity density | Density gradient g = ∂_p ln L (EQ-013/038) | **KEPT as notation only.** The one test is HYP-005 ("attraction" to density). No additional claim |
| **Force / pressure** | ANALOGY | "Order-flow pressure" = signed flow per unit liquidity: δ / L(p) | Kyle-λ-type impact: Δp ≈ λ·mo (S51). λ is inversely related to depth | **DATA-BLOCKED** (true δ and depth unavailable). The proxy version is HYP-003 (EVR/Amihud: move per unit volume) |
| **Particle interactions / statistical mechanics** | ANALOGY | Heterogeneous agents (S52 types) generating aggregate flow | Agent-based models | **REJECTED for estimation:** agent IDs are unavailable; calibration is impossible (S52 §1.1). Possible future simulator for *execution* stress tests only |
| **Phase transitions / criticality** | ANALOGY | Abrupt regime changes (calm → volatile; balance → trend) | Regime switching (EQ-023); vol-of-vol | **KEPT as HMM / Markov regimes** (HYP-020). "Critical slowing down" (rising autocorrelation and variance before a transition) is a testable early-warning claim: HYP-036, low priority |
| **Metastability / attractors** | ANALOGY | Balance areas (D-profiles) persisting, then breaking out | Regime persistence plus compression ratio (EQ-019) | Covered by HYP-019/020 |
| **Entropy** | MATHEMATICS (information theory) | Disorder of return patterns (permutation entropy); dispersion of the profile | EQ-015, EQ-022 | **KEPT for testing** (HYP-014, HYP-021). Must beat ER/VR |
| **Information propagation** | MATHEMATICS | Lead–lag across venues and assets | Cross-correlation, transfer entropy | Lead–lag decays within months and dies at about 7 bp of cost (original S14). **Low priority** (H-LEADLAG-FX) |
| **Conservation-like quantities** | — | Inventory conservation in dealer books (the sum of positions is zero) | Market clearing (S32 "zero-sum") | **A true accounting identity**, but it gives no forecast. Not a feature |
| **Field representations** | ANALOGY → statistics | L(p,t), DP(p,t) as fields over price × time | Kernel density estimation (EQ-012) | **KEPT** (06) |
| **Nonlinear dynamics / chaos** | Hypothetical LAW-like claim | Low-dimensional deterministic dynamics | Correlation dimension, Lyapunov exponents | **REJECTED:** noise-dominated, short, non-stationary series; no corpus evidence (18) |
| **Reaction–diffusion** | ANALOGY | Spread of a liquidity "front"? | — | **REJECTED:** no observable maps to the reactant field |
| **Percolation** | ANALOGY | Liquidity "connectivity" | — | **REJECTED:** no data on the book network |
| **Network dynamics** | ANALOGY | Asset networks | Correlation graphs | **REJECTED** at N ≤ 8 instruments |
| **Stochastic thermodynamics** | ANALOGY | Entropy production of price paths | Time-irreversibility statistics | **DEFER:** a time-reversal asymmetry test (skewness of returns at multiple scales) is a legitimate *statistic*. Keep only as an exploratory descriptor; no hypothesis registered |

## Summary

**Physics contributes notation and three tested ideas:**
1. density-gradient "attraction" (HYP-005);
2. regime/phase persistence (HYP-020);
3. entropy as a disorder measure (HYP-021).

**Everything else either reduces to an existing statistic or lacks data and is rejected.** No document in this package claims that markets obey a physical law.
