# 14: HYPOTHESIS REGISTRY (HYP-xxx)

**Binding rules (inherited from the original backlog):**
- These are hypotheses, not strategies.
- Every test needs a **separately approved, frozen protocol**: pre-registered definitions, parameters, metrics, holdout and candidate count (15).
- No change to production code, the S14 forward test, NEXA_Risk, schema v1, V2 or 8E.
- The original 40-item backlog (`research/knowledge/RESEARCH_HYPOTHESIS_BACKLOG.md`) **remains in force**. HYP-xxx entries cross-reference it ("Backlog link") instead of duplicating it.

**Status vocabulary:**
- **UNTESTED**
- **TESTING** (preliminary probe exists, no frozen verdict)
- **SUPPORTED**
- **REJECTED**
- **UNTESTED (BLOCKED: data)**: cannot be tested with current subscriptions.

**Priority:** P1 (method/data foundations), P2 (volatility/activity), P3 (structure/liquidity), P4 (flow proxies), P5 (options, blocked), P6 (cross-asset / T5).

**Data:** ✓ available · ◐ proxy/partial · ✗ unavailable (03).

## 0. Index

| ID | Name | Tier | Pri | Data | Status | Source | Backlog link |
|---|---|---|---|---|---|---|---|
| HYP-001 | Tick volume is an adequate activity proxy | T1 | P1 | ✓ | **TESTING** (1-month probe supportive) | MEASURED | — |
| HYP-001b | σ̂_YZ / HAR beats ATR as NEXA's volatility unit | T2 | P1 | ✓ | UNTESTED | S48, S23 | H-VOL-1 |
| HYP-034 | The causal futures–spot basis maps levels within ≤ 0.1 σ̂ | T1 | P1 | ✓ | UNTESTED | MEASURED, S44 | — |
| HYP-002 | Relative volume adds to HAR volatility forecasts | T1/2 | P2 | ✓ | UNTESTED | S40, S48 | H-VOL-1/3 |
| HYP-019 | Compression predicts expansion of volatility, not direction | T2 | P2 | ✓ | UNTESTED | S09, S19, S46 | H-SQUEEZE-VARIANTS |
| HYP-020 | Regimes persist; regime conditioning changes outcome laws | T2 | P2 | ✓ | UNTESTED | S42, S46, S47, S53 | H-HURST-GATE, H-THICKNESS-ER |
| HYP-004 | "Volume slows price" (LVN traversal speed) | T2 | P3 | ◐ | UNTESTED | S42, S46 | — |
| HYP-005 | Density-gradient drift ("magnet") | T2 | P3 | ◐ | UNTESTED | S43, S49 | — |
| HYP-006 | HVN reversion / LVN continuation | T2 | P3 | ◐ | UNTESTED | S42, S44, S49 | — |
| HYP-007 | Value-Area Rule | T2 | P3 | ◐ | UNTESTED | S42 | — |
| HYP-008 | 3-1 day continuation | T2 | P3 | ✓ | UNTESTED | S42 | — |
| HYP-009 | Neutral-extreme continuation | T2 | P3 | ✓ | UNTESTED | S42 | — |
| HYP-010 | Post-trend-day sideways or reversal | T2 | P3 | ✓ | UNTESTED | S46 | — |
| HYP-011 | IB width predicts range extension / day type | T2 | P3 | ✓ | UNTESTED | S46, S42 | H-SESSION-SPLIT |
| HYP-012 | Open-type extremes hold | T2 | P3 | ✓ | UNTESTED | S42, S49 | H-OPEN-CONT |
| HYP-013 | Trend-day base rate (descriptive) | T2 | P3 | ✓ | UNTESTED | S42 vs S46 (CN4) | — |
| HYP-014 | Profile concentration predicts next-session state | T2 | P3 | ◐ | UNTESTED | S49 | — |
| HYP-015 | Accumulation-zone retest (mechanical) | T2 | P3 | ◐ | UNTESTED | S49 | — |
| HYP-016 | True futures volume adds information beyond tick volume | T1 | P3 | ✓ (2 y) | UNTESTED | MEASURED | — |
| HYP-021 | Permutation entropy adds to ER/VR as a regime descriptor | T5 | P3 | ✓ | UNTESTED | EXTERNAL | H-VR-SCALE |
| HYP-023 | Stop-rule comparison H1–H5 | T2/3 | P3 | ◐ (H1 ✗) | UNTESTED | Directive §9 | H-HIT-PROB, H-VOL-2 |
| HYP-024 | Wider structural stops cut cost-in-R without cutting gross R | T1 | P2 | ✓ | UNTESTED | MEASURED (A4) | H-COST-SHRINK |
| HYP-003 | Effort–result / absorption predicts level reaction | T1 | P4 | ◐ | UNTESTED | S40, S44 | — |
| HYP-017 | Lagged proxy delta predicts the next return | T1 | P4 | ◐ | UNTESTED | S44, S51 | — |
| HYP-017b | The f30 quality gate adds value to the existing engine | T1 | P4 | ◐ (demo only) | UNTESTED | NEXA EA | H-ABLATE |
| HYP-018 | Proxy CVD divergence at levels predicts reaction | T1 | P4 | ◐ | UNTESTED | S44 | — |
| HYP-022 | WHERE (level) / WHEN (flow) decomposition | T1–3 | P4 | ◐ | UNTESTED | Directive §10, S44, S53 | H-ABLATE |
| HYP-025 | Dealer gamma regime → realised volatility | T3 | P5 | ✗ | UNTESTED (BLOCKED: data) | S50, S53 (Ni et al.) | — |
| HYP-026 | Conditional wall rejection | T3 | P5 | ✗ | UNTESTED (BLOCKED: data) | S53 | — |
| HYP-027 | Hedge-pressure-ratio dose–response | T3 | P5 | ✗ | UNTESTED (BLOCKED: data) | S48 + NEW | — |
| HYP-028 | GLD option-volume levels mark XAU reactions | T3 | P5 | ◐ | UNTESTED | S53 (volume toggle) | — |
| HYP-029 | Charm drift into monthly expiry | T3 | P5 | ✗/◐ | UNTESTED (BLOCKED: data) | S53 | — |
| HYP-030 | GLD IV − XAU RV spread predicts XAU RV | T3 | P5 | ◐ | UNTESTED | S48 | H-VOL-1 |
| HYP-031 | USD-basket / real-yield context conditions XAU | T4 | P6 | ✓ | UNTESTED | S39, S51 | H-LEADLAG-FX |
| HYP-032 | ES volatility spillover to XAU/FX | T4 | P6 | ✓ | UNTESTED | S14 | H-LEADLAG-FX |
| HYP-033 | Hawkes quote-burst endogeneity predicts spread and slippage | T5 | P6 | ◐ | UNTESTED | S34, S52 | H-SPREAD-REGIME |
| HYP-035 | Execution state predicts slippage (S14 demo) | T1 | P2 | ✓ (prospective) | UNTESTED | S10, S14 work | H-NEWS-SLIP, H-STOP-SLIP |
| HYP-036 | "Critical slowing down" precedes volatility-regime shifts | T5 | P6 | ✓ | UNTESTED | Physics analogy | — |

---

## 1. P1: foundations (they gate everything else)

### HYP-001: tick volume as an activity proxy
- **Hypothesis:** Pepperstone M1 tick volume tracks exchange volume closely enough to stand in for it in *activity-normalised* features.
- **Maths:** corr(ln V^T_h, ln V^F_h) after removing the hour-of-week mean (EQ-005); VA Jaccard; |ΔPOC|/σ̂.
- **Data:** MT5 M1; Massive GC, 6E, 6B, 6J 1-min (2 y).
- **Mechanism:** quote-update rates rise with exchange activity (common information arrival).
- **Prediction:**
  - de-seasonalised r ≥ 0.5;
  - VA Jaccard median ≥ 0.70;
  - |ΔPOC| ≤ 0.25 σ̂_day on ≥ 60 % of days.
- **Falsification:** any criterion fails on the full 2-year overlap (per symbol).
- **Validation:** full-span replication; stability by quarter; report per symbol.
- **Evidence so far:**
  - **One month (Sep 2026):** r = 0.67 (XAU), 0.57 (EUR); Jaccard 0.82.
  - **POC criterion:** 65 % of days within $2 (≈ 0.05 σ̂_day), so it passes on this sample.
- **Status:** **TESTING.**

### HYP-001b: volatility unit
- **Hypothesis:** σ̂ from Yang–Zhang or HAR forecasts next-session RV better than ATR(14), which NEXA uses throughout.
- **Maths:** EQ-002/004 vs ATR; QLIKE loss; Diebold–Mariano.
- **Data:** ✓.
- **Falsification:** the DM test does not reject equality (BH across 4 symbols).
- **Status:** UNTESTED.
- **Backlog link:** H-VOL-1.

### HYP-034: futures–spot basis mapping
- **Hypothesis:** the causal rolling-median basis (EQ-026, k = 6 closed hours) maps futures prices to spot with error ≤ 0.1 σ̂_day on ≥ 95 % of hours (excluding roll days).
- **Falsification:** error quantiles exceed that.
- **Why it matters:** gates every futures-derived spot feature (NF-031, HYP-016).
- **Status:** UNTESTED.

### HYP-024: cost-in-R vs stop width
- **Hypothesis:** for a fixed entry set, scaling (U, D) up by a factor m ∈ {1, 1.5, 2, 3} reduces c/D in proportion to 1/m. The question is whether gross R per trade is unchanged.
- **Maths:** EQ-025; gross E[R](m) vs net E[R](m); EQ-024 null.
- **Data:** ✓ (Trade DNA tester campaigns; re-simulate exits on M1 with fixed entries).
- **Mechanism:** the cost is fixed in price units, so the share of R it consumes falls with D.
- **Prediction:** net E[R] improves by ≈ 0.245·(1 − 1/m) R if gross is invariant.
- **Falsification:** gross E[R] falls by more than the cost saving (adverse conditional drift beyond small stops).
- **Validation:** fixed-entry re-simulation; block bootstrap; deflate for 4 m values.
- **Status:** UNTESTED.
- **Backlog link:** H-COST-SHRINK.
- **Note:** this alone cannot create edge if gross is ≤ 0 (A4: −0.072R gross).

### HYP-035: execution state → slippage
- **Hypothesis:** signed slippage (R) conditional on spread percentile, quote intensity, session and news differs from unconditional.
- **Data:** the S14 demo (prospective).
- **Falsification:** no out-of-sample pinball-loss gain.
- **Status:** UNTESTED (data accruing from 2026-10-05).

## 2. P2: volatility and activity

### HYP-002: relative volume → volatility
- **Hypothesis:** RVOL (NF-010/011) improves the next-hour and next-session RV forecast beyond HAR.
- **Maths:** ln RV_{t+1} = HAR + θ·ln RVOL_t + ε. Test θ ≠ 0 and ΔQLIKE.
- **Mechanism:** activity bursts cluster (mixture of distributions).
- **Falsification:** θ̂ CI includes 0 and ΔQLIKE ≈ 0 out of sample.
- **Status:** UNTESTED.

### HYP-019: compression → expansion
- **Hypothesis:** low CR percentile predicts higher next-session RV (volatility mean reversion).
- **Null:** the breakout *direction* is 50/50.
- **Falsification:**
  - no monotone relation of next RV with CR decile;
  - **or** direction predictable (which would be a surprise to be re-tested).
- **Status:** UNTESTED.

### HYP-020: regime persistence and conditioning
- **Hypothesis:**
  - (a) the transition matrix (M-06) differs from i.i.d.;
  - (b) the outcome law of Y-02 / Y-03 differs across filtered regimes, beyond x_t main effects.
- **Maths:** EQ-023; LR test; log-score gain of a regime-interacted model.
- **Falsification:** (a) LR not significant, or (b) no out-of-sample log-score gain.
- **Status:** UNTESTED.

## 3. P3: structure and liquidity (profile hypotheses use session anchors, 06 §3)

### HYP-004: "volume slows price"
- **Hypothesis:** time to traverse ±0.5 σ̂_day from p_t is shorter when NF-030 (density at price) is low.
- **Maths:** survival model of traverse time T_trav with covariate L(p_t); Cox HR < 1 for density.
- **Controls:** σ̂, RVOL, session.
- **Placebo:** the profile from a random other day.
- **Falsification:** HR ≈ 1, or equal to placebo.
- **Status:** UNTESTED.

### HYP-005: gradient drift
- **Hypothesis:** E[(p_{t+H} − p_t)/σ̂ · sgn g_t] > 0 for H ∈ {15, 60} minutes.
- **Null:** 0. Hit-rate binomial test with a block bootstrap.
- **Falsification:** the effect is ≤ the cost-equivalent (in σ̂) or insignificant after FDR.
- **Status:** UNTESTED.

### HYP-006: curvature
- **Hypothesis:** the conditional first-order autocorrelation of 5-min returns is negative in the HVN tercile (κ < 0) and positive in the LVN tercile (κ > 0).
- **Falsification:** no difference (permutation of κ labels within session).
- **Status:** UNTESTED.

### HYP-007: Value-Area Rule (S42)
- **Hypothesis:** given open outside the prior VA and acceptance (NF-035), P(touch the opposite VA edge before re-exiting the entry edge) exceeds the matched placebo (random VA entries at the same σ̂ distance and VA width).
- **Falsification:** the difference is ≤ 0, or not robust to the acceptance definition (1 vs 2 periods).
- **Status:** UNTESTED.

### HYP-008: 3-1 days (S42)
- **Hypothesis:** after a 3-1 day (initiative tail, TPO majority and range extension all in one direction; codified thresholds pre-registered), the next session trades beyond the prior VA in the 3-1 direction within the first 90 minutes more often than the unconditional base rate.
- **S42 figures:** 94 % vs ? (no base rate given). **The base rate is the critical comparison.**
- **Falsification:** the conditional rate ≤ base rate + margin (Fisher exact test, BH).
- **Status:** UNTESTED.

### HYP-009: neutral-extreme (S42)
- **Hypothesis:** a neutral day closing in the top or bottom 10 % (EQ-017) leads to next-session continuation beyond the VA more than the base rate.
- **S42 figures:** 64 % in the first 90 minutes.
- **Status:** UNTESTED.

### HYP-010: post-trend day (S46)
- **Hypothesis:** after a trend day (EQ-016–018), P(next session range-bound or reversing) ≈ 0.9 (S46).
- **Falsification:** the measured rate is ≤ the base rate after non-trend days. "Sideways or reverse" must be operationalised (e.g. next close within the prior VA, or opposite to the prior trend).
- **Note:** contradiction CN5 with HYP-008/009. Run them together.
- **Status:** UNTESTED.

### HYP-011: IB width
- **Hypothesis:** a smaller IBR (NF-040) predicts larger REX and a higher trend-day probability (S46).
- **Maths:** ordinal logistic of day type on IBR, controlling for σ̂.
- **Falsification:** no monotone relation.
- **Status:** UNTESTED.

### HYP-012: open types
- **Hypothesis:** extremes set in the first 30 minutes after an "open-drive" (NF-042) hold for the session more often than for other open types.
- **S42 claim:** "majority"; open-rejection-reverse extremes hold "less than half".
- **Falsification:** no difference across open types.
- **Status:** UNTESTED.
- **Backlog link:** H-OPEN-CONT.

### HYP-013: trend-day base rate
- **Hypothesis (descriptive):** the share of trend days per instrument under the EQ-016–018 codification. S46 says 10–20 %; S42 says 20–30 %.
- **Falsification:** n/a (a measurement), but it settles CN4 for NEXA's instruments.
- **Status:** UNTESTED.

### HYP-014: profile concentration
- **Hypothesis:** prior-session concentration C (NF-034) predicts the next session's REX or RV (low C → trend continuation; high C → balance).
- **Falsification:** no incremental value beyond σ̂ and the prior range.
- **Status:** UNTESTED.

### HYP-015: accumulation retest (S49)
- **Definition:**
  - a balance segment = ≥ 60 bars with ER_60 < 0.2;
  - a breakout = a close beyond the segment range ± 0.5 σ̂;
  - the zone = the segment's max-density price;
  - the event = the first return to the zone after the breakout.
- **Hypothesis:** P_U (in the breakout direction, U = D = 1 σ̂) exceeds the driftless 0.5 and a placebo (a random price within the segment).
- **Falsification:** no difference. **The definition is causal by construction** (zone fixed at breakout time).
- **Status:** UNTESTED.

### HYP-016: true volume vs tick volume
- **Hypothesis:** replacing or adding futures volume features (NF-011, NF-014, NF-031) to tick-volume features improves HYP-002/004/005 models.
- **Maths:** nested models; log score / QLIKE; within the 2-year overlap only.
- **Falsification:** no gain.
- **Status:** UNTESTED.

### HYP-021: permutation entropy
- **Hypothesis:** PE (NF-018) adds to ER and VR in predicting |next-session autocorrelation| or RV.
- **Falsification:** no gain.
- **Status:** UNTESTED.

### HYP-023: stop-rule comparison (directive §9)
- **Hypothesis family:** with *identical entries*, stop rules H2 (volatility), H3 (liquidity structure), H4 (flow invalidation, proxy) and H5 (hybrid) differ in E[R_net], P(stop), MAE/MFE (σ̂), slippage and regime dependence. **H1 (wall) is BLOCKED.**
- **Maths:** EQ-030; EQ-024/034 null.
- **Entry sets (each a separate stratum):**
  - (i) NEXA's existing signals (tester DNA);
  - (ii) a random-entry null with matched timing distribution.
- **Prediction:** a stop rule can only reshape the payoff unless the conditional law near structure differs from driftless (H-HIT-PROB). The expected finding under the null is that H3 ≈ H2 after scaling D to equal σ̂ multiples.
- **Falsification:** structure-based stops show no gain over volatility stops at equal average D.
- **Status:** UNTESTED.

## 4. P4: flow proxies (results describe proxies only; 09 §8)

### HYP-003: effort–result / absorption
- **Hypothesis:** at defined levels (VA edge, HVN), high-volume small-range bars (EVR ≪ 0 or ABS high) are followed by reversal more often than (a) the same bars off-level and (b) placebo levels.
- **Falsification:** no difference (BH within the level family).
- **Status:** UNTESTED.

### HYP-017: lagged proxy delta
- **Hypothesis:** β_ℓ ≠ 0 in r_{t+1:t+H}/σ̂ on δ̃_{t−ℓ+1}, ℓ = 1…5.
- **Prior expectation:** null (A6, S51).
- **Falsification:** HAC t-stats insignificant after FDR, or the effect is below cost.
- **Status:** UNTESTED.

### HYP-017b: f30 gate ablation
- **Hypothesis:** demo trades passing the |OBI| > 0.15 quality point have higher net R than otherwise similar trades.
- **Data:** S14 demo plus tick logger only (f30 is not reproducible offline).
- **Falsification:** no difference over ≥ 100 trades.
- **Status:** UNTESTED.
- **Note:** this is a test of an *existing production rule*. A positive or negative result would only inform a future, separately approved change.

### HYP-018: CVD divergence at levels
- **Hypothesis:** on the approach to a level (last 15 bars), price making a new extreme while proxy cumulative δ moves the opposite way predicts reaction (Y-04) more than non-divergent approaches.
- **Status:** UNTESTED.

### HYP-022: WHERE / WHEN
- **Hypothesis:**
  - (a) I(Y_reach; Lv) > I(Y_reach; F);
  - (b) I(Y_react; F | Lv) > 0 (EQ-032).
- **Lv:** profile and structure levels. **F:** lagged proxy flow and absorption.
- **Falsification:** (b) not above the permutation null.
- **Interpretation rule:** proxy results support or fail to support the *architecture*. They do not test true-data theory.
- **Status:** UNTESTED.

## 5. P5: options / GEX (05)

| ID | Hypothesis | Falsification | Data |
|---|---|---|---|
| HYP-025 | Positive dealer net gamma (sign model stated) → lower next-day XAU RV, beyond HAR | Coefficient ≈ 0 or wrong sign; results flip under the alternative sign model (S54 isolation) | ✗ (OI) |
| HYP-026 | P(reject at wall) > matched placebo **only** if regime > 0 and HPR > median | No difference, or no regime/HPR dependence | ✗ |
| HYP-027 | The wall/pin effect is monotone increasing in HPR | Flat (isotonic test) | ✗ |
| HYP-028 | GLD option-volume gamma concentration (unsigned) marks XAU levels with abnormal reaction | ≤ placebo | ◐ |
| HYP-029 | Drift toward heavy strikes in the last 5 sessions before monthly expiry | No drift difference | ✗ / ◐ |
| HYP-030 | GLD-derived IV minus XAU RV predicts XAU RV (VRP mean reversion) | No gain over HAR | ◐ |

## 6. P6: cross-asset and T5

| ID | Hypothesis | Falsification |
|---|---|---|
| HYP-031 | XAU next-session RV and direction are conditioned by the prior-day USD-basket move and ΔUS10Y; coefficients are unstable but significant within rolling windows | No out-of-sample gain; sign instability across years (expected) |
| HYP-032 | ES 1-min RV bursts lead XAU/FX RV by ≤ 5 minutes | No lead beyond the contemporaneous; disappears at cost |
| HYP-033 | The Hawkes branching ratio of quote updates (tick logger) predicts spread widening and slippage in the next minute | No out-of-sample gain |
| HYP-036 | Rising lag-1 autocorrelation and variance of RV ("critical slowing down") precede high-volatility regime entry | No lead relation beyond HAR |

---

**Multiple-testing accounting** (15 §4): families are:
- volatility (HYP-001b, 002, 019, 021, 030);
- level-reaction (HYP-003, 004–007, 015, 018, 026, 028);
- session/day-type (HYP-008–014);
- flow (HYP-017, 017b, 018, 022);
- stops/cost (HYP-023, 024);
- regime (HYP-020, 036);
- cross-asset (HYP-031, 032);
- execution (HYP-033, 035).

BH at q = 0.10 within families; DSR/PBO for any strategy-like search.
