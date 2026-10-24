# 09: MATHEMATICAL FRAMEWORK

**Purpose:** state the probability model NEXA would reason with, and for every mathematical method answer the directive's four questions:
1. **WHY?** Which market phenomenon does it model?
2. **DATA:** what observable data does it need?
3. **DECISION:** what prediction or decision does it improve?
4. **FALSIFY:** how could it be shown wrong?

Methods are kept **only** if they pass all four *and* NEXA has the data (03). Equation IDs refer to the registry in 11_NEW_MATHEMATICAL_CONSTRUCTS.md.

---

## 1. The objects

**Time and information**
- **Instruments:** i ∈ {EURUSD, GBPUSD, USDJPY, XAUUSD}. Optional context instruments: XAGUSD, GC, 6E, 6B, 6J, ES, US Treasury yields.
- **Decision bar:** B_t = [t, t+Δ) with Δ = 1 min, the entry timeframe. 𝓕_t = σ-algebra of all data timestamped < t + Δ (03 §3).
- **Observation vector:** x_t ∈ ℝ^d, 𝓕_t-measurable.
  - Components are grouped into blocks: price/volatility, activity/volume, profile/liquidity field, structure, flow proxy, session/time, cross-asset, execution.
  - **Unavailable blocks are absent, not imputed** (§7).
- **Latent state:** z_t ∈ {1,…,K}, a market regime. It is not observed and is inferred from x_{≤t}.

**Trade hypothesis**
- **h = (direction d ∈ {±1}, entry e, stop distance D > 0, target distance U > 0, horizon H).**
- **Outcome:** R_net(h) = net R as defined in the cap-neutral protocol (fill to exit, plus commission and swap, divided by initial risk). It is labelled from `fill_ts` to barrier or horizon.

## 2. The decision rule (Bayesian decision theory)

NEXA acts on h at t only if all three conditions hold:

    (1) E[ R_net(h) | x_t ] > κ                      (expected value net of costs, in R)
    (2) P( R_net(h) > 0 | x_t ) is calibrated          (reliability diagram, Brier/log score)
    (3) the risk engine authorises                     (NEXA_Risk; unchanged)

The expected value of a barrier trade (EQ-025) is

    E[R_net | x] = P_U(x)·(U/D) − (1 − P_U(x) − P_H(x))·1 + P_H(x)·E[R_H | x] − c/D

where:
- P_U is the probability of reaching the target first;
- P_H is the probability of reaching the horizon first, with conditional R_H;
- **c/D is the round-trip cost in R**: spread at fill plus commission, divided by stop distance.

**Every intelligence component must enter through P_U, P_H, E[R_H] or c.** There is no other channel to value.

**Null and baseline (EQ-024, EQ-034).** Under arithmetic Brownian motion with drift μ and volatility σ:

    P_U = (1 − e^{2μD/σ²}) / (e^{−2μU/σ²} − e^{2μD/σ²}),     →  D/(U+D)   as μ → 0.

With μ = 0, E[R_gross] = 0 for **any** U and D (original MATH M1b). Two consequences:
- **Exit and stop geometry cannot create edge.** Edge must come from μ(x) ≠ 0 or from a non-Brownian conditional law near levels (reflection, absorption).
- **Volatility information still matters.** σ(x) sets the probability of reaching the horizon before either barrier, the cost-in-R (D must scale with σ), and the realised path. It does not create a gross edge.

## 3. Method-by-method audit

| Method | WHY: phenomenon | DATA (NEXA) | DECISION it improves | FALSIFY | Verdict |
|---|---|---|---|---|---|
| **Conditional probability / Bayes rule** | Learning P(outcome \| state) | Trade DNA labels + x_t | Calibrated P_U, the go/no-go | Calibration fails out of sample (reliability slope ≠ 1, Brier no better than climatology) | **KEEP**: this is the backbone |
| **Bayesian decision theory** (expected utility in R) | Choosing actions under uncertainty with asymmetric costs | Same | Threshold κ, abstention | The decision rule loses to "never trade" net of costs in a frozen holdout | **KEEP** |
| **Stochastic processes: Brownian / diffusion** | Price as noisy diffusion | Bars | Nulls (EQ-024/034); volatility scaling | Variance ratio ≠ 1 with persistence (H-VR-SCALE); FX scaling exponent ≈ 0.56–0.58 (S15) | **KEEP as null**, not as truth |
| **Jump processes / bipower variation** (EXTERNAL Barndorff-Nielsen & Shephard 2004) | News gaps; stop fills through levels | M1, ticks | Separating jump from diffusive variance in σ̂; stop-slippage model | Jump share near 0 except on news; no improvement in RV forecast | **KEEP** (volatility layer) |
| **Stochastic / rough volatility** (S04, S18; HAR = EXTERNAL Corsi 2009) | Volatility clustering, long memory | M1 → RV | σ forecast → D sizing, P_H, cost-in-R | HAR does not beat ATR in QLIKE (Diebold–Mariano) on XAU/FX | **KEEP** (H-VOL-1, top priority) |
| **Markov chains / regime switching / HMM** (EXTERNAL Hamilton 1989; Baum–Welch; S47 mention) | Persistent latent market states (vol × trend) | Bars | Regime-conditioned μ(x), σ(x) | Transition matrix ≈ i.i.d. (diagonal ≈ row-marginal); regime labels do not separate outcome distributions out of sample | **KEEP** (HYP-020) |
| **State-space models / Kalman filter** (S36 errors noted) | Smoothly varying hidden quantity: futures–spot basis, fair value, local volatility level | Massive futures + MT5 | Causal basis b̂_t for mapping levels (EQ-026) | Innovations autocorrelated; a rolling median does as well | **KEEP narrowly** (basis, local level). Never a smoother: causal filter only |
| **Point processes / Poisson / Hawkes** (EXTERNAL Hawkes 1971; S34 and S52 in corpus) | Clustering of quote updates and activity bursts (endogeneity) | MT5 ticks (28 days plus forward logging) | Spread and slippage risk forecasting (execution), vol-burst onset | Branching ratio unstable or uninformative for next-minute spread or σ | **RESEARCH-LATER** (T5; data short) |
| **Signal processing / Fourier** | Periodicity (intraday seasonality) | Bars | De-seasonalised volume and volatility (EQ-005) | Hour-of-week profile unstable across years | **KEEP only as seasonal baselines** (simple averages; no spectral trading signals) |
| **Wavelets** | Multi-scale variance decomposition | Bars | Volatility by scale (like variance ratios) | Not better than VR / HAR multi-horizon | **DEFER**. Two-sided wavelet filters are on the do-not-use list as signals |
| **Shannon entropy / permutation entropy** (EXTERNAL Bandt & Pompe 2002) | Disorder or predictability of return patterns; profile dispersion | Bars | Regime descriptor | Entropy adds nothing beyond ER and VR in predicting \|autocorrelation\| or next-day range | **TEST** (HYP-021; EQ-015/022) |
| **Mutual information / information flow** | Non-linear dependence; WHERE vs WHEN decomposition | Features + labels | Feature ablation; layer value | Conditional MI ≈ 0 against the permutation null | **KEEP as a diagnostic** (EQ-032) |
| **Copulas** | Tail co-movement across symbols | Bars | Correlation cap and portfolio tail risk | Gaussian copula as good as t-copula for joint-loss frequency | **DEFER** (risk-engine research; not intelligence) |
| **Extreme value theory** (POT/GPD) | Tail losses, gap risk | Bars, DNA | Stress sizing, H-TAIL-SIM | Tail index unstable; no better than empirical quantiles | **KEEP** (risk research only) |
| **Random matrix theory** | Noise vs signal eigenvalues in large correlation matrices | Needs N ≫ 1 assets | — | — | **REJECT for NEXA**: N = 4–8 instruments; the Marchenko–Pastur bulk is meaningless at that N |
| **Graph theory** | Networks of assets or levels | — | — | — | **REJECT** (no decision it improves at N ≤ 8) |
| **Topology / TDA** | Shape of point clouds | — | — | — | **REJECT**: no market phenomenon identified that it models better than simpler statistics |
| **Convex optimisation** | Sizing under constraints; calibration | DNA | Risk allocation (risk engine) | — | **KEEP** (already in the risk/decision layer conceptually) |
| **Nonlinear dynamics / chaos** | Deterministic low-dimensional dynamics | — | — | Surrogate-data tests (EXTERNAL) routinely fail to reject noise in financial returns | **REJECT** (no evidence in corpus; 18) |
| **Control theory** | Feedback: position-dependent hedging | — | Possibly execution scheduling | — | **REJECT for intelligence**. Retail size has negligible impact (S25, S32) |
| **Game theory** | Strategic interaction: last look, sniping, dealers | Corpus theory (S06, S10, S11) | Interpretation of adverse selection; not a forecast | — | **KEEP as mechanism reasoning**, not as a model to estimate |
| **Statistical mechanics / agent-based models** | Heterogeneous agents (S52), emergent price | No agent data | — | Calibration impossible without IDs (S52 §1.1) | **REJECT for estimation**. Keep as a simulator idea only (10) |
| **Sequential probability / SPRT** | Monitoring live performance; early stop of a failing engine | DNA | Kill-switch timing (H-ENVELOPE) | False alarm rate ≠ nominal under autocorrelation | **KEEP** (governance) |
| **Survival / hazard models** | Time to target, stop or level break | DNA, bars | P_H, E[time-to-target]; level "break hazard" | Hazard indistinguishable from the driftless null | **KEEP** (HYP-007, 023) |
| **Causal inference** | Separating a level's effect from selection (where levels form) | Bars | Valid level effects | Matched non-level controls show the same reaction (placebo levels) | **KEEP**: placebo-level design is mandatory (15) |
| **Time-series econometrics** (HAC, unit roots, cointegration) | Inference with dependence | All | Correct standard errors | — | **KEEP** (existing STAT KB) |
| **Machine-learning probability models** (logistic, GBM, calibrated) | Non-linear P(outcome \| x) | DNA | P_U, E[R] | No ablation gain over a logistic baseline in a frozen holdout | **KEEP, last**: only after features pass their single-feature tests |

## 4. The state-space formulation (what "market state" means mathematically)

    Observation:   x_t = h(z_t, ξ_t) + ε_t                    (blocks below)
    Latent state:  z_t ∈ {1..K},  P(z_{t+1}=j | z_t=i) = P_ij(x_t)   (EQ-023)
    Outcome law:   R_net(h) | z_t, x_t  ~  F( · ; θ_{z_t}, x_t )

**Block structure of x_t.** It mirrors the directive's ordering:
- **x^P, price and volatility:** returns, YZ and RV, compression ratio, ER, VR. EQ-001–004, 019–021.
- **x^V, activity:** RVOL (seasonally normalised), V/N trade size (futures), EVR (effort/result), Amihud. EQ-005–007.
- **x^L, revealed liquidity field:** L(p,t), ∂_p log L, ∂²_p L at the current price; VA/POC distances; concentration. EQ-012–015.
- **x^S, structure:** existing f00–f27 and f32–f46 (BOS, sweep, …) plus IB, REX and day type. EQ-016–018.
- **x^F, flow proxy:** f30/f31 (quote-direction) and lagged BVC δ̃ from futures. EQ-008–010. **Proxy.**
- **x^O, options:** **absent** (03). It would be GEX, flip distance, walls and HPR (EQ-027–029) **if data were acquired**.
- **x^T, time/session:** hour-of-week, session anchors, news proximity.
- **x^X, cross-asset:** USD basket (f29), ES volatility, real-yield change.
- **x^E, execution state:** spread/ATR (f28), quote intensity, own recent slippage (from S14 logging).

**Why a latent state at all (INFERENCE).** Every practitioner framework in the new corpus (day types, gamma regimes, "balance vs imbalance") is a discrete regime claim. A regime model makes those claims **testable as one family**: does conditioning on z_t change the outcome law beyond x_t itself? The test is a likelihood-ratio or log-score gain out of sample.

## 5. Normalisation as mathematics (directive §13)

Every raw quantity q_t is replaced by a **causal, scale-free** version. The choice depends on the economic question:

| Question | Transform | Formula |
|---|---|---|
| "Is this unusual *for this time of week*?" | Seasonal ratio | q_t / Ê[q \| how(t)] (rolling K-week median, closed weeks only) (EQ-005) |
| "Is this unusual *relative to recent history*?" | Rolling percentile / empirical CDF | F̂_{t−W..t−1}(q_t) ∈ [0,1] |
| "How large relative to volatility?" | Volatility units | q_t / σ̂_t (YZ or HAR forecast, *lagged*) |
| "What share of activity?" | Within-bar share | δ_t / V_t ∈ [−1, 1] |
| "Comparable across instruments?" | Cross-sectional rank | rank_i(q_{i,t}) / N (only for N ≥ 4; weak at N = 4) |

**Raw thresholds are rejected unless economically justified.** The directive's example "Delta > 300 %" originates in S44's footprint display default: the diagonal ask/bid ratio ≥ 3. It is not justified there and cannot be computed by NEXA.

**Replacements, if a delta proxy is used:**
- δ̃ = δ/V, the share of volume;
- the percentile of δ̃ within the same hour-of-week;
- δ / Ê[|δ| | how], magnitude relative to normal.

**Preference order:**
1. **Percentile or seasonal ratio**: robust to the broker feed's level shifts, which 2017–2026 tick volume shows.
2. **Volatility units**: for price distances.
3. **z-scores**: only where approximate normality is checked.

## 6. Physics-inspired constructs: what survives (detail in 10)

Only constructs with an explicit definition, data and a falsification test survive:
- **The "potential" U(p) = −log L(p)** of the revealed-liquidity field (EQ-038). It is a re-expression of the density; it is not energy. The "force" F = ∂_p log L(p) gives the same test as HYP-005.
- **Quadratic variation (realised variance)** as the only principled "energy-like" quantity. It is additive across time under zero drift (S48 App. A.2). **No conservation law exists, so "market energy" as a name is rejected.**
- **Phase transitions / criticality** become regime switching (§4). The empirical claim reduces to HMM transition behaviour and vol-of-vol.

## 7. Missing data is structural, not random

Blocks x^O (options/GEX), true x^F (aggressor flow) and depth are **unavailable** (03).

**Rules:**
- They are **not imputed**: no zero-fill, no carry-forward, no model-based fill.
- The model is defined on the available blocks only. If a block is later acquired, it enters through **nested model comparison** (log-score gain, frozen holdout), never by assumption.
- Every proxy (f30, f31, BVC, tick-volume profile, GLD-derived IV) carries a **PROXY** tag through the feature catalog (13) and into the Trade DNA documentation.

## 8. How the framework answers the WHERE/WHEN question (directive §10)

Let Lv_t be the level/setup features and F_t the flow features. By the chain rule of mutual information (EQ-032):

    I(Y; Lv, F) = I(Y; Lv) + I(Y; F | Lv)

- **"Options/GEX/profile is better for WHERE"** means: I(Y_reach; Lv) > I(Y_reach; F), where Y_reach is whether price reaches or reacts at a level.
- **"Order flow is better for WHEN"** means: I(Y_timing; F | Lv) > 0 and > I(Y_timing; Lv | F), where Y_timing is the reaction within the next k bars given price is at the level.

**Estimation:**
- nested probabilistic classifiers;
- log-score differences on a frozen holdout;
- a permutation null (shuffle F within level episodes).

**With NEXA's data both sides are proxies** (profile from tick volume or futures volume; flow from quote-direction or BVC). A positive result supports the *architecture*, not the true-data version. A negative result with proxies does **not** refute the true-data version. Both conclusions are recorded as such (HYP-022).
