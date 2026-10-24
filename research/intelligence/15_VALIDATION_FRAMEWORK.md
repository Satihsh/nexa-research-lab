# 15: VALIDATION FRAMEWORK

**This builds on, and does not replace:**
- `research/knowledge/STATISTICAL_KNOWLEDGE_BASE.md` (look-ahead traps L1–L15, nulls, inference);
- NEXA's existing gates (Gate 8 net-expectancy block bootstrap; DSR/PBO; frozen holdouts; candidate counting).

## 1. Protocol skeleton (every HYP test)

**A. Before any data is touched**
1. **Pre-registration file**, hashed and committed before results are opened. It records:
   - definitions (from 11/13) and pre-registered parameters;
   - label definitions (13 §Y);
   - the metric;
   - the null and placebo design;
   - the sample split;
   - the candidate count;
   - the decision rule (what result counts as SUPPORTED or REJECTED).
2. **Data provenance:** source hashes, entitlement windows, roll calendar, session anchors, timezone conversion (D-TZ convention).

**B. Running the test**
3. **Causality audit:** an automated check that every feature at t uses data < t + Δ. This reuses the parity-oracle discipline; same-bar flow proxies are prohibited in predictive sets.
4. **In-sample estimation → frozen out-of-sample** (§3).

**C. Reporting**
5. **Report everything:**
   - effect size with CI;
   - p-value (HAC or block bootstrap);
   - BH-adjusted q within the family;
   - placebo result;
   - cost-adjusted value where relevant;
   - per-symbol and per-regime breakdown;
   - year-by-year stability.
6. **Status update** in 14:
   - SUPPORTED only if the OOS result passes the pre-registered rule **and** survives costs (if it is a trading claim);
   - otherwise REJECTED;
   - **failed results are never deleted.**

## 2. Nulls and placebos (mandatory by hypothesis type)

| Hypothesis type | Null / placebo |
|---|---|
| Level reaction (VA, HVN, walls, accumulation zones) | **Placebo levels:** random prices matched on distance from the current price (σ̂ units), time of day and prior volatility. **Placebo days:** the profile from a different session. The effect must exceed placebo, not just 50 % |
| Day-type / session conditional rates (3-1, neutral-extreme, post-trend) | **Unconditional base rate** of the same outcome on all sessions (S42 omits this; it is the critical number) |
| Stop/target rules | Driftless two-barrier (EQ-024), plus **random-entry with identical exits** |
| Predictive flow / activity coefficients | Zero coefficient; HAC errors; permutation of the feature within session blocks |
| Volatility forecasts | ATR(14), EWMA, GARCH(1,1), HAR (whichever is not the candidate); QLIKE + Diebold–Mariano |
| Regime models | i.i.d. regimes (P_ij = π_j); a K-regime HMM vs K−1 |
| Classifiers / probability models | Climatology (base rate) Brier/log score; logistic baseline; blinded-feature ablation (H-ABLATE) |
| Proxy validity (HYP-001, 034) | Pre-registered numeric acceptance thresholds (14) |

## 3. Sample design under NEXA's data constraints

| Data | Span | Split (pre-registered) |
|---|---|---|
| MT5 M1 (spot) | 2017-07 → 2026-09 | **Discovery:** 2017-07 → 2022-12. **Validation:** 2023-01 → 2024-12. **Holdout (frozen, opened once):** 2025-01 → 2026-09 |
| Massive futures / options (2 y) | 2024-10 → 2026-10 | **Discovery:** 2024-10 → 2025-09. **Holdout:** 2025-10 → 2026-09. No validation slice; use walk-forward inside discovery |
| Trade DNA (tester) | 2024-01 → 2026-09 (A-windows + B) | Existing campaign windows. Never 2027 (V2 OOS) |
| S14 demo fills | 2026-10-05 → | Prospective. Analyse only after the pre-registered n (≥ 100 fills) |
| 2027 | — | **Reserved for V2.** Not used by this programme |

**Walk-forward** inside discovery (expanding or rolling, step = 1 quarter) for every parameterised model. **Coefficients are refit only on the past.**

**Contamination disclosure:**
- The 2026-10-04 data probes (`evidence/`) looked *descriptively* at 2026-08-31 → 09-25. They examined:
  - volume and profile agreement;
  - the basis.
- **No hypothesis outcome was computed.**
- 2024–2026 was also used by NEXA's earlier engine campaigns (cap-neutral A4, 8E). Those tested a *different* rule set.
- A holdout inside 2025-01 → 2026-09 is therefore **unused for HYP-xxx outcomes but not pristine data**.
- If stricter independence is required, the only clean option is **prospective collection** (from 2026-10 onward).
  - Example: HYP-001/016 re-run on data collected from 2026-10 onward.
  - **Any use of 2027 data requires explicit approval**, because 2027 is V2's reserved prospective OOS period.

## 4. Multiple testing and search accounting

- **Families** as listed at the end of 14.
- **Within a family:** Benjamini–Hochberg, q = 0.10.
- **Any parameter sweep** (bandwidth h, α of the VA, thresholds, lags) **counts every variant**.
- **Strategy-like searches** (choosing entry/exit combinations) report:
  - the **Deflated Sharpe Ratio** (DSR) with the honest trial count;
  - the **Probability of Backtest Overfitting** (PBO, combinatorially symmetric cross-validation);
  - the **parameter sensitivity surface** (the result must not sit on an isolated peak).
- **Count families, not names** (01 §4): ten level definitions are one hypothesis tested ten times.

## 5. Robustness battery (applied to anything that passes OOS)

| Test | Pass criterion |
|---|---|
| Transaction costs | Positive at measured spread + $7/lot commission + slippage quantiles from M-09. Stress: +0.15R per trade (A4 convention) |
| Slippage | Robust to the 90th-percentile adverse slippage (S14 demo data when available) |
| Latency sensitivity | Robust to entry at bar + 1 minute (delay parity, H-DELAY-PARITY) |
| Regime | The sign holds in ≥ 2 of 3 volatility terciles; no single year carries > 50 % of the effect |
| Symbol | Reported per symbol; pooled only if heterogeneity is insignificant |
| Parameter perturbation | ±25 % on each parameter keeps the effect sign and ≥ 50 % of its size |
| Proxy swap | For profile features: the result reproduces with futures volume in place of tick volume (2-year overlap) |
| Calibration | Reliability-diagram slope within [0.8, 1.2]; Brier better than climatology |
| Monte Carlo | Block bootstrap of trade sequences for drawdown distribution (H-TAIL-SIM) |

## 6. Causality and look-ahead checklist (new items N1–N8, added to L1–L15)

| # | Trap | Rule |
|---|---|---|
| N1 | Same-bar flow proxies (BVC, tick rule) | Lag ≥ 1 for prediction |
| N2 | Completed-session profile used intraday | Developing profile only intraday. Completed after the session close |
| N3 | Final REX, CL, day type used as features | They are **labels** (Y-05) until the session ends |
| N4 | Futures roll chosen by future volume | Pre-declared calendar roll |
| N5 | Full-day basis | Causal rolling basis (EQ-026) |
| N6 | Option daily bars / OI used before publication | Daily bar after 16:15 ET; OI next session |
| N7 | "Accumulation zone" defined by the later breakout direction | Zone fixed at breakout time; event = later retest |
| N8 | Curated example levels (S44/S49 charts) | All level touches enter the sample |

## 7. Decision rules for promotion (research → candidate; never directly to production)

1. **SUPPORTED** in 14 with a frozen OOS pass plus the robustness battery.
2. **Ablation shows incremental value** on top of the current best model (log score or net R).
3. **Parity:** a bar-reproducible definition exists, and the MQL5 vs research oracle matches (NEXA parity contract). Tick-only features remain exempt and **cannot be the sole basis** (`sole_basis_guard`).
4. **Separate human approval** for any schema v1.1 change, EA change or deployment. **This package authorises none.**
