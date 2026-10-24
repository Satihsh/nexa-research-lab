# PRE-REGISTRATION T1: tick-volume ↔ real futures volume (HYP-001, HYP-034)

**Written before any T1 outcome is computed.** The SHA-256 is recorded in `PREREG_HASHES.txt`. Any deviation is reported as a deviation.

**Disclosure:** the 2026-10-04 one-month probe (Sep 2026, GC and 6E) already looked at part of the data descriptively.

## 1. Pairs and period

| Spot (Pepperstone M1, `tick_volume`) | Futures (Massive 1-min, `volume`, `transactions`) | Futures→spot price map |
|---|---|---|
| XAUUSD | GC (COMEX) | log basis b = ln F − ln S |
| EURUSD | 6E (CME) | log basis b = ln F − ln S |
| GBPUSD | 6B (CME) | log basis b = ln F − ln S |
| USDJPY | 6J (CME) | spot converted S' = 1/S; b = ln F − ln S' |

- **Period:** the overlap of Massive's entitlement and the MT5 canonical data, 2024-10-07 → 2026-09-25.
- **Split for fitted objects** (§5): **discovery** 2024-10-07 → 2025-09-30; **holdout** 2025-10-01 → 2026-09-25.

## 2. Futures front contract (causal)

For each server day d, the front contract is the candidate with the **highest volume in the previous completed session** (Massive `1session` bars). Ties go to the nearer expiry.

**Candidates:**
- **GC:** all listed months Z4 … Z6.
- **6E, 6B, 6J:** quarterly H/M/U/Z, Z4 … Z6.

## 3. Units and alignment

**Hourly**
- UTC clock hours.
- An hour counts only if spot has ≥ 30 M1 bars **and** futures volume is > 0. Hours failing this are excluded and their counts reported.

**Server day (A0)**
- Spot: `time_server` date (Pepperstone, NY+7).
- Futures: UTC + 3 h during US DST, + 2 h otherwise; date of the result.
- Weekends excluded. Days with fewer than 80 % of the median spot bar count are flagged **thin** and reported separately.

## 4. Metrics (all per pair)

### Hourly activity

| ID | Metric | Definition |
|---|---|---|
| M1 | Pearson | corr(ln V^T, ln V^F), pooled hours |
| M2 | Spearman | rank correlation |
| M3a | De-seasonalised (primary, causal) | Each log series minus its trailing 8-week median for the same hour-of-week (EQ-005); then Pearson |
| M3b | De-seasonalised (secondary) | Full-sample hour-of-week mean removed |
| M4 | Rolling | M3a within 20-trading-day windows stepping by 5 days. Report min, 5th percentile, median, max, and the share of windows < 0.30 |
| M5 | Regime-conditioned | M3a by **daily spot-volatility tercile** and by **daily efficiency-ratio tercile** (ER = \|close−open\| / Σ\|Δclose\| on M1). Tercile cut-points from discovery |
| M6 | Session-conditioned | M3a by UTC block: ASIA 23–07, LONDON 07–12, OVERLAP 12–16, NY 16–21, LATE 21–23 |
| M7 | Volatility-conditioned | M3a by **hourly** spot realised-volatility tercile (from M1 returns; cut-points from discovery) |
| M8a | Distributional (levels) | KS statistic and Wasserstein-1 distance between the distributions of seasonal ratios ln(V/Ê[V\|how]) for T and F |
| M8b | Distributional (intraday shape) | Per day, the 24-hour share vectors of T and F; Jensen–Shannon divergence (base 2). Report median and 90th percentile |

### Daily volume profile (server day, completed)

**Construction**
- **Bin width (futures price units):** GC 1.0; 6E 0.0001; 6B 0.0001; 6J 0.000001.
- **Volume assignment:** each 1-minute bar's volume is assigned to the bin of its typical price (h+l+c)/3.
- **Spot mapping:** spot bars are mapped into futures price space via F̂ = exp(ln S' + b̂_d), then binned identically.
- **Basis b̂_d, two variants:**
  - **(i) Alignment (primary for shape metrics):** median over the day's hours of (ln F_close − ln S'_close) at matching hh:59 bars.
  - **(ii) Causal:** the same median over the *previous* server day.
- **Profile objects:** POC = argmax bin; VA_0.70 by the S42 two-bin greedy rule (EQ-014; ties go to the upper side first, then lower).
- **Scale σ_day** = close price × sd of daily close-to-close log returns over the previous 20 server days (spot, causal).

**Daily metrics**

| ID | Metric |
|---|---|
| P1 | \|POC_T − POC_F\| / σ_day |
| P2 | \|VAH_T − VAH_F\| / σ_day |
| P3 | \|VAL_T − VAL_F\| / σ_day |
| P4 | VA Jaccard = \|overlap\| / \|union\| |
| P5 | Jensen–Shannon divergence between the binned profiles (common grid) |
| P6 | Wasserstein-1 between the profiles / σ_day |
| P7 | Cosine similarity |

**Bimodality**
- **Definition (on a Gaussian-smoothed profile,** kernel sd = 3 bins**):** BIMODAL if the second-highest local maximum is ≥ 0.6 × the highest, **and** the minimum between them is ≤ 0.8 × the second peak.
- **Computed on:**
  - the **futures** profile (truth) → used for the failure rates;
  - the **spot** profile → a detectable feature.
- **P8 bimodal failure rate:** P(P1 > 0.25 | futures profile bimodal) vs P(P1 > 0.25 | unimodal).
- **Reliable day (HYP-001 pre-registered):** P1 ≤ 0.25 **and** P4 ≥ 0.70.

## 5. TICK_VOLUME_PROXY_CONFIDENCE (TVPC)

### TVPC_profile(d): day level, from spot data only

**Inputs** (known at the end of day d, computed from Pepperstone data alone):

| Input | Definition |
|---|---|
| z1 | Spot bimodality ratio: second peak / first peak (0 if unimodal) |
| z2 | Spot profile concentration C = 1 − H/ln J (EQ-015) |
| z3 | ln(day tick volume / trailing 8-week median for the same weekday) |
| z4 | Bar coverage (bars / median bars) |
| z5 | ln(median spread / trailing 20-day median of daily median spread) |
| z6 | Day range / σ_day |

**Two forms**
- **TVPC0 (closed form, no fitting)** = 1 − z1. Rationale: bimodality is the measured POC failure mechanism.
- **TVPC (fitted)** = logistic(β'z), standardised inputs.
  - Fit on **discovery** (pooled over pairs, with pair fixed effects).
  - Target = reliable day.
  - Evaluated on **holdout**: AUC; Brier score vs climatology; calibration slope and intercept.

**Acceptance:** holdout AUC ≥ 0.65 **and** Brier better than climatology → "failure is detectable". Otherwise → "not detectable with spot-only inputs".

### TVPC_activity(h): hour level, from spot data only

- **Target:** |e_h| = |de-seasonalised ln V^T − de-seasonalised ln V^F| (M3a residuals).
- **Inputs:**
  - session block;
  - spot hourly-RV tercile;
  - |hourly return| / σ_hour;
  - spread-state tercile;
  - de-seasonalised ln V^T itself.
- **Model:** linear regression of |e_h| on these, fit on discovery; holdout R² and the Spearman of predicted vs realised |e_h|.
- **TVPC_activity** = 1 − F̂(predicted |e|), the percentile under the discovery distribution.

### Downstream reliability test (holdout only)

**Features compared** (computed twice: from the spot tick-volume profile and from the futures profile of the previous day):
- **F-a:** distance of the next day's 08:00 UTC spot price to the prior-day VAH and VAL, in σ_day units;
- **F-b:** inside-prior-VA flag at 08:00 and 14:00 UTC.

**Agreement measures**
- **F-a:** |distance_T − distance_F|.
- **F-b:** flag equality.

**Test**
- **Statistics:** Spearman(TVPC, −disagreement); difference in mean disagreement between the top and bottom TVPC terciles, with a 2,000-sample day-block bootstrap CI.
- **Pass:** the CI excludes 0 in the expected direction.
- **Run for both forms:** TVPC0 and the fitted TVPC.

## 6. Pre-registered conclusions

| Hypothesis | Pass condition |
|---|---|
| **HYP-001 activity** | M3a ≥ 0.50 for the pair over the full period |
| **HYP-001 profile** | Median P4 ≥ 0.70, and P1 ≤ 0.25 on ≥ 60 % of days |
| **HYP-034 basis** | The causal-basis map error \|ln F − (ln S' + b̂_{d−1})\| at hourly closes ≤ 0.1 × σ_day/price on ≥ 95 % of non-roll hours |

**Reporting rules:** results are reported per pair. **No metric, threshold or definition is changed after outcomes are seen.** Additional analyses are labelled **EXPLORATORY**.
