# T1 REPORT: Pepperstone tick volume vs CME futures volume (2 years, 4 pairs)

**Pre-registration:** `PREREG_T1_TICKVOL_PROXY.md`, sha256 `1c33eb28…22c6`. Recorded 2026-10-04T13:46:35Z, before any T1 outcome; re-verified unchanged at run time.

**Code and outputs**
- `parse_exports.py`, then `t1_tickvol_proxy.py`, producing `t1_results.json`, `t1_daily.csv` and `t1_run.log`.
- **Exploratory, not pre-registered:** `t1_exploratory.py`, producing `t1_exploratory.json`.

**Data**
- **Spot:** Pepperstone M1 canonical.
- **Futures:** Massive 1-min aggregates, front contract per server day.

| Spot pair | Futures | Profile bin |
|---|---|---|
| XAUUSD | GC | 1.0 |
| EURUSD | 6E | 0.0001 |
| GBPUSD | 6B | 0.0001 |
| USDJPY | 6J (spot inverted to 1/S) | 0.000001 |

- **Period:** 2024-10-07 → 2026-09-25.
- **Discovery:** ≤ 2025-09-30. **Holdout:** after that date.
- **Size:** 11.3–11.7k hours per pair and 493–509 profile days per pair. No thin days.

**Deviations (all recorded in `t1_results.json`)**
- **D1.** 2026-03-30 is excluded for XAUUSD and EURUSD. Massive lacks the 2026-03-27 session bars for the main contracts, so the causal rule picked a thin back month.
- **D2.** The Massive workspace expired mid-export. Later pulls (GC from 2026-07, all of 6E/6B/6J) use the front schedule that the §2 rule had already produced on 2026-10-04, hard-coded rather than re-derived. The rule is the same and so is its output. Roll dates per contract are in the data files.
- **D3.** The downstream test was corrected **before any downstream output existed**:
  - F-a now uses per-edge |d_T − d_F| / σ_day at 08:00 only (the draft averaged signed distances, which cancel);
  - the bootstrap now resamples days, as the pre-registration specifies, not hour records.
- **D4.** Rows with a non-finite TVPC input are excluded from the fit. **This turned out to matter a lot** (§5.1).
- **Disclosed, not a deviation:**
  - Gold hourly closes were exported rounded to $1, adding about ±0.01 σ_day to the HYP-034 basis error (threshold 0.1 σ). FX closes were exported exactly.
  - A gold-only debug run was made before the FX data existed, to fix crashes (a pandas `.lt` name clash and a missing-pair loop). No definition was changed after seeing it.

---

## 1. Pre-registered verdicts (holdout rules, per pair)

| Hypothesis / rule | XAUUSD | EURUSD | GBPUSD | USDJPY |
|---|---|---|---|---|
| **HYP-001 activity:** M3a ≥ 0.50 | **PASS** 0.599 | **PASS** 0.600 | **FAIL** 0.447 | **PASS** 0.554 |
| **HYP-001 profile:** median P4 ≥ 0.70 | PASS 0.818 | PASS 0.759 | PASS 0.707 | PASS 0.818 |
| **HYP-001 profile:** P1 ≤ 0.25σ on ≥ 60 % of days | PASS 73.8 % | PASS 67.3 % | **FAIL** 57.4 % | PASS 74.7 % |
| **HYP-034 basis:** causal map ≤ 0.1σ on ≥ 95 % of non-roll hours | **FAIL** 88.0 % | PASS 99.5 % | PASS 99.9 % | PASS 97.3 % |
| **TVPC acceptance:** AUC ≥ 0.65 and Brier < climatology | **FAIL**, pooled AUC 0.614 (Brier 0.236 vs 0.240) | ← | ← | ← |
| **Downstream:** TVPC top vs bottom tercile, CI excludes 0 | **PASS** (both F-a and F-b; both TVPC and TVPC0) | ← | ← | ← |

**Overall**
- **HYP-001 (tick volume as an activity and profile proxy):**
  - **SUPPORTED** for XAUUSD, EURUSD and USDJPY;
  - **REJECTED for GBPUSD** on both the activity rule and the POC rule.
- **HYP-034 (causal basis map):** **SUPPORTED** for the three FX pairs; **REJECTED for gold**.
- **TVPC:** "failure is **not detectable** with spot-only inputs" under the pre-registered form. Its fit is compromised; see §5.1. The exploratory fix (§6) clears the bar.

---

## 2. Hourly activity (tick volume V^T vs futures volume V^F)

| Metric | XAUUSD | EURUSD | GBPUSD | USDJPY |
|---|---|---|---|---|
| M1 Pearson, ln levels | 0.624 | 0.695 | 0.612 | 0.658 |
| M2 Spearman, levels | 0.621 | 0.700 | 0.628 | 0.670 |
| **M3a de-seasonalised (causal 8-week hour-of-week median)** | **0.599** | **0.600** | **0.447** | **0.554** |
| M3a discovery → holdout | 0.651 → 0.556 | 0.649 → 0.571 | 0.546 → **0.359** | 0.631 → 0.500 |
| M3b de-seasonalised (full-sample means) | 0.460 | 0.464 | 0.319 | 0.506 |
| M4 rolling 20-day: median / p05 / min | 0.69 / 0.41 / 0.33 | 0.69 / 0.43 / 0.37 | 0.57 / 0.23 / **0.01** | 0.65 / 0.28 / 0.08 |
| M4 share of windows < 0.30 | 0 % | 0 % | 13.6 % | 6.8 % |
| M8a sd(ln-ratio) T / F | 0.63 | 0.66 | 0.57 | 0.57 |
| M8a KS / W1 (log units) | 0.15 / 0.16 | 0.12 / 0.15 | 0.13 / 0.20 | 0.11 / 0.20 |
| M8b JS divergence of intraday shape: median / p90 | 0.025 / 0.049 | 0.038 / 0.058 | 0.048 / 0.083 | 0.026 / 0.061 |

**Reading**
- **Intraday shape is almost identical.** JS divergence is about 0.03, so tick volume reproduces *when* activity happens.
- **Day-to-day abnormal activity agrees only moderately** (de-seasonalised r 0.45–0.60). About 64–80 % of abnormal-activity variance is *not* shared.
- **Tick volume compresses swings.** Its de-seasonalised dispersion is only 57–66 % of futures'. Tick counts saturate when real volume surges, a known mechanism for count-based proxies.
- **Every pair is weaker in the holdout than in discovery** (a drop of 0.06–0.19). The relationship is not stationary.

### 2.1 Conditioned correlations (M3a residuals)

| Condition | XAUUSD | EURUSD | GBPUSD | USDJPY |
|---|---|---|---|---|
| Daily RV tercile: low / mid / high | 0.51 / 0.63 / 0.61 | 0.54 / 0.51 / 0.69 | 0.36 / 0.38 / 0.50 | 0.45 / 0.51 / 0.62 |
| Daily efficiency-ratio tercile: low / mid / high | 0.56 / 0.57 / 0.66 | 0.53 / 0.61 / 0.66 | 0.36 / 0.47 / 0.52 | 0.61 / 0.48 / 0.59 |
| Hourly RV tercile: low / mid / high | 0.50 / 0.60 / 0.60 | 0.47 / 0.51 / 0.65 | 0.31 / 0.37 / 0.52 | 0.43 / 0.42 / 0.55 |

**By session**

| Session | XAUUSD | EURUSD | GBPUSD | USDJPY |
|---|---|---|---|---|
| Asia | 0.64 | 0.56 | **0.38** | 0.55 |
| London | 0.56 | 0.56 | 0.45 | 0.51 |
| Overlap | 0.52 | 0.61 | 0.50 | 0.58 |
| NY | 0.61 | 0.66 | 0.52 | 0.57 |
| Late | 0.66 | 0.65 | 0.43 | 0.65 |

**When tick volume works best:** high-volatility, directional (high efficiency-ratio) days and NY hours.
**When it fails:** quiet, low-RV hours and days, GBPUSD outside NY, and the roll windows below.

---

## 3. Basis map (HYP-034)

| | XAUUSD | EURUSD | GBPUSD | USDJPY |
|---|---|---|---|---|
| Share of hours ≤ 0.1 σ_day | **0.880** | 0.995 | 0.999 | 0.973 |
| Median / p95 error (σ_day units) | 0.020 / **0.243** | 0.015 / 0.056 | 0.008 / 0.028 | 0.021 / 0.083 |
| Basis, start → end (bp) | 72 → 82 | 29 → 33 | −1 → 5 | 90 → 63 |

**Gold fails** because of fat right tails in the map error (p95 = 0.24σ). The median error is small. The $1 close rounding explains at most about 0.01σ of this.

**Likely contributors (INFERENCE, untested):**
- the timing mismatch between the last spot M1 close and the last GC trade in fast hours;
- day-to-day carry drift in GC (≈ 2-month expiry, rate-sensitive).

**Consequence:** mapping futures-derived levels onto spot gold carries a tail error of about 0.25 σ_day on 5 % of hours. That is too large for stop-level precision without an intraday basis update.

---

## 4. Daily volume profiles (spot tick-volume profile vs futures profile, same bins)

**"align"** uses same-day basis alignment (a diagnostic). **"causal"** uses b̂_{d−1} (the deployable form).

| Metric (median; p90) | XAUUSD | EURUSD | GBPUSD | USDJPY |
|---|---|---|---|---|
| P1 POC error, σ_day (align) | 0.058; 0.70 | 0.079; 0.86 | 0.174; 0.94 | 0.051; 0.67 |
| P2 VAH error (align) | 0.055; 0.35 | 0.088; 0.45 | 0.108; 0.59 | 0.059; 0.39 |
| P3 VAL error (align) | 0.067; 0.39 | 0.089; 0.55 | 0.110; 0.64 | 0.048; 0.38 |
| P4 VA overlap, Jaccard (align) | 0.818 | 0.759 | 0.707 | 0.818 |
| P5 JS divergence (align) | 0.042 | 0.040 | 0.058 | 0.027 |
| P6 Wasserstein, σ_day (align) | 0.054 | 0.076 | 0.079 | 0.042 |
| P7 cosine similarity (align) | 0.935 | 0.924 | 0.886 | 0.949 |
| Share P1 ≤ 0.25σ, align / causal | 73.8 / 69.3 % | 67.3 / 64.1 % | 57.4 / 56.3 % | 74.7 / 73.8 % |
| **Reliable days** (P1 ≤ 0.25 and P4 ≥ 0.70), align / causal | 62.9 / 54.5 % | 51.0 / 46.9 % | 42.8 / 42.5 % | 61.9 / 58.5 % |

**Reading**
- **The typical day is good.** The POC lands within about 0.05–0.17 σ_day, the value areas overlap about 70–82 %, and cosine similarity is ≈ 0.9.
- **The failure distribution is heavy-tailed.** On the worst 10 % of days the proxy POC is 0.7–0.9 σ_day away: effectively a *different* POC.
- **Making the map causal costs about 5–8 points of reliability.**

### 4.1 Bimodal-profile failure (P8)

| | XAUUSD | EURUSD | GBPUSD | USDJPY |
|---|---|---|---|---|
| Futures profile bimodal (share of days) | 35.5 % | 28.7 % | 43.2 % | 22.8 % |
| POC failure rate (P1 > 0.25σ) on **bimodal** days | **46.9 %** | **52.7 %** | **62.3 %** | **56.0 %** |
| POC failure rate on unimodal days | 14.8 % | 24.6 % | 27.7 % | 16.3 % |
| Spot flags futures bimodality: precision / recall | 0.68 / 0.71 | 0.49 / 0.64 | 0.56 / 0.54 | 0.54 / 0.61 |

- **Bimodality is the dominant POC failure mechanism.** Failure is 2–3.5× more frequent on bimodal days. This is mechanical: when two peaks are near-equal, a small volume mis-weighting flips the argmax.
- **Spot data detects futures bimodality only moderately**, with precision ≈ 0.5–0.7. Most of the problem, then, is visible from spot alone, but not reliably.

---

## 5. TICK_VOLUME_PROXY_CONFIDENCE (TVPC): definition and test

### 5.0 Definition (as pre-registered; spot-only, known at the end of day d)

**Inputs:**
- z1 = spot bimodality ratio s(p₂)/s(p₁) of the σ = 3-bin smoothed tick-volume profile (0 if there is a single peak);
- z2 = profile concentration 1 − H/ln J;
- z3 = ln(day tick volume / trailing 8-week same-weekday median);
- z4 = bar coverage;
- z5 = ln(median spread / trailing 20-day median);
- z6 = (H − L)/C / σ_day.

**Forms:**
- **TVPC0** = 1 − z1 (closed form).
- **TVPC** = logistic(β₀ + Σ βᵢ ẑᵢ + pair FE), where ẑ is standardised on discovery. It is fitted on discovery with target = reliable day.

**TVPC_activity(h):** a linear model of the hourly |e_h| on session, RV tercile, spread tercile, |r|/σ_h and ln V^T residual.

### 5.1 Pre-registered results

**Fitted TVPC: AUC 0.614.** Brier 0.2358 vs climatology 0.2397; calibration slope 0.48 (over-confident). **It FAILS the 0.65 bar.**

**Important defect discovered here.** z5 is **undefined on 1,416 of 2,019 days**.
- Pepperstone records a **0-point raw spread on most FX M1 bars**: 94 % of bars for EURUSD and about 64 % for GBPUSD and USDJPY.
- So the daily *median* spread is 0 on 72–100 % of FX days.
- The pre-registered fit therefore ran on a **biased 603-day subsample**: all of gold, a few JPY/EUR days and **no GBPUSD at all**.
- **This verdict is valid as a statement about the pre-registered construct.** As an estimate of how detectable proxy failure is, it is unreliable.

**TVPC0** (closed form, test AUC on the same subsample): **0.611**.

**TVPC_activity (hour level): not detectable.** Holdout R² = 0.003 and Spearman(predicted, realised |e|) = 0.07. *Which hours* tick volume misreads cannot be predicted from spot-side state.

### 5.2 Downstream reliability (holdout; F-a = VA-edge distance disagreement at 08:00; F-b = inside-prior-VA flag at 08:00/14:00)

| Score | Spearman(score, −F-a disagreement) | F-a: top − bottom tercile [95 % CI] | F-b agreement, top vs bottom tercile | F-b: top − bottom disagreement [95 % CI] |
|---|---|---|---|---|
| TVPC (pre-registered fit) | 0.35 | −0.171 [−0.265, −0.096] σ | 94.4 % vs 84.3 % | −0.101 [−0.167, −0.040] |
| TVPC0 = 1 − z1 | 0.27 | −0.128 [−0.165, −0.093] σ | 90.8 % vs 85.6 % | −0.052 [−0.092, −0.015] |

**PASS for both forms on both features.** Gating proxy-profile features by TVPC measurably improves their agreement with the true futures-derived features.

**Caveat (structural, stated before interpreting):**
- **F-a is close to circular.** The 08:00 price cancels out of d_T − d_F, so F-a is essentially the day's VAH/VAL error, which also enters the target.
- **F-b is the genuinely downstream measure.** It depends on where the next day's price actually sits. Its effect is modest: about +5 to +10 points of flag agreement.

---

## 6. EXPLORATORY follow-ups (not pre-registered; written after the results above)

| ID | What | Result |
|---|---|---|
| **E1** | z5 → ln(**mean** spread / trailing median); all 2,019 days | Holdout **AUC 0.667**, Brier 0.233 vs climatology 0.251, calibration slope 0.66. Per pair: XAU 0.64, EUR 0.62, **GBP 0.72**, JPY 0.64 |
| **E2** | z5 dropped | Identical to E1 (AUC 0.667). **Spread state carries no information** |
| **E0** | TVPC0 on all days | AUC 0.601 (EUR 0.565, the weakest) |
| E1 downstream | F-a Spearman 0.52; F-a top − bottom −0.26 σ [−0.31, −0.22]; F-b agreement **92.1 % vs 81.2 %** (−0.110 [−0.148, −0.073]) | Stronger than pre-registered |
| **E3** | Activity M3a excluding ±2 days around each futures roll | XAU 0.599 → **0.657**; EUR 0.600 → **0.666**; GBP 0.447 → **0.525**; JPY 0.554 → **0.631**. Inside roll windows: 0.37 / 0.30 / 0.16 / 0.23 |

**E3 changes the interpretation of "when tick volume fails".** A large part of the measured activity failure, and **every worst rolling window**, sits on futures roll dates. On those dates the causal front rule tracks a contract whose volume is migrating away. That is **truth-side contamination, not a tick-volume defect**.

GBPUSD remains the weakest pair even ex-roll: holdout ex-roll 0.44, below the 0.50 bar.

### 6.1 Candidate TVPC_v1 (EXPLORATORY; E2 form, standardised on discovery)

```
TVPC_v1(d) = logistic( 0.149
              − 0.277·(z1 − 0.5666)/0.3196        # bimodality ratio
              + 0.163·(z2 − 0.0713)/0.0249        # concentration
              + 0.068·(z3 − 0.0843)/0.2978        # abnormal tick volume
              + 0.049·(z4 − 0.9984)/0.0092        # bar coverage
              − 0.533·(z6 − 1.5850)/0.7885        # range / sigma_day  (strongest)
              + pair FE {EUR 0, GBP −0.286, JPY +0.484, XAU +0.373} )
```

**Interpretation:** the proxy profile is least trustworthy on **wide-range (trend/expansion) days** and **two-peaked days**. It is most trustworthy on concentrated, single-peaked, normal-range days.

**Status:** this is a *candidate*. To advance it needs:
- a new ID;
- its own pre-registration;
- a fresh holdout (2026-10 onward, prospective).

The 2025-10 → 2026-09 holdout has now been seen and cannot validate it.

---

## 7. Answers to the four questions

1. **When is tick volume reliable?**
   - As an **intraday-shape / seasonal activity proxy: always** (JS ≈ 0.03).
   - As an **abnormal-activity proxy:** moderately (r ≈ 0.6 ex-roll; XAU, EUR, JPY). It is best on high-RV, directional days and in NY hours.
   - As a **daily profile proxy:** on single-peaked, normal-range days (72–85 % POC hit rate on unimodal days).
2. **When does it fail?**
   - On **bimodal days** (POC failure 47–62 %).
   - On **wide-range days**.
   - In **quiet / low-RV hours**.
   - On **GBPUSD** generally (it fails both HYP-001 rules).
   - In the **holdout year** (correlations decayed on all pairs).
   - Apparent failures in **roll windows** are mostly a measurement artefact.
   - Tick volume systematically **under-states activity surges** (dispersion ratio ≈ 0.6).
3. **Is failure detectable?**
   - **At the day level, partly.** Pre-registered: no (AUC 0.61, compromised fit). Exploratory full sample: AUC 0.67. That is useful for gating, not for per-day certainty.
   - **At the hour level, no** (R² ≈ 0).
4. **Can a confidence score be assigned?**
   - **Yes, as a coarse gate.** TVPC terciles separate downstream agreement significantly (F-b 92 % vs 81 % in E1).
   - It is not precise enough to treat any single day's proxy POC as reliable.

## 8. Implications for NEXA (research-tier only; nothing deployed)

- **Volume-profile features built from Pepperstone tick volume** (NF-024/035, EQ-014) are **admissible as PROXY features for XAU, EUR and JPY, gated by TVPC**, and **not for GBPUSD**.
- **Every downstream test must carry TVPC as a covariate or a gate.**
- **Hour-level abnormal-volume features** (RVOL, EQ-005) share at most about 36 % of their variance with true volume (r ≤ 0.6). Treat them as a noisy proxy whose errors cannot be predicted.
- **Futures-derived levels mapped onto spot** (EQ-026) are acceptable for FX but **not yet for gold**: the tail error needs an intraday basis update, to be tested separately.
- **Constraint compliance:** no S14 / NEXA_Risk / schema / EA / production change; nothing deployed.
