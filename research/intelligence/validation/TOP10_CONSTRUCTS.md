# TOP 10 MATHEMATICAL CONSTRUCTS NEXA SHOULD ACTUALLY TEST

**Selection basis:**
- EQUATION_PRIORITY_MATRIX × HYPOTHESIS_PRIORITY_MATRIX;
- evidence from T1/T2 (2026-10-04).

**Selection rule:** a construct must be computable with **data on hand** and must change P_U, the stop distance D or cost c (09 §2). Sophistication is not a criterion.

**Implementation cost:** S (≤ 1 day of research code), M (2–4 days), L (> 1 week). All research tier.

---

### 1. HAR volatility forecast (EQ-004), plus ATR(7) as the challenger to beat
- **Equation:** ln RV_{d+1} = β₀ + β_d ln RV_d + β_w ln RV^{(5)} + β_m ln RV^{(22)}, walk-forward.
- **Data:** required = M1 bars; available = 9 years, 4 symbols. **Proxy:** none.
- **Hypothesis:** HAR's σ̂ gives better-calibrated stop distances than ATR(14) / ATR(7).
- **Null:** equal QLIKE (Diebold–Mariano).
- **Status (T2):**
  - lowest QLIKE 4/4;
  - beats ATR14 significantly 1/4 → pre-registered "beats ATR" **FAILED**;
  - up/down hit rate 61–76 % vs ATR14 53–67 %.
- **Next falsification test:**
  - (a) the **intraday** horizon NEXA's stops use (1–4 hours, seasonal HAR);
  - (b) whether HAR-scaled D changes barrier outcomes (EQ-034) relative to ATR-scaled D on fixed entries.
- **Validation:** walk-forward QLIKE plus a fixed-entry re-simulation (construct #3).
- **Cost:** S.
- **Feature:** σ̂_HAR as the volatility unit (NF-004).

### 2. Net expectancy with costs + two-barrier geometry (EQ-025, EQ-024, EQ-034)
- **Equation:** E[R_net] = P_U·U/D − (1 − P_U) − c/D. P_U from the drift/volatility two-barrier formula.
- **Data:** Trade DNA (tester 2024–26), M1, costs from spec and S14. **Proxy:** none.
- **Hypothesis (HYP-024):** scaling (U, D) by m ∈ {1, 1.5, 2, 3} lowers c/D by 1/m **without** lowering gross R.
- **Null:** the driftless barrier law, so gross E[R] = 0 for random entries. For NEXA entries, gross E[R](m) is constant in m.
- **Falsification:** the gross loss grows with m faster than the cost saving.
- **Validation:** fixed-entry exit re-simulation; block bootstrap; 4 m-values counted.
- **Cost:** M.
- **Feature:** none. It is a stop/target policy.

### 3. Stop-rule family H2 / H3 / H5 (EQ-030)
- **Equation:** D_H2 = k·σ̂; D_H3 = distance beyond the prior VA edge (or LVN) + ε·σ̂; D_H5 = max(D_H2, D_H3).
- **Data:** M1; profile from tick volume (proxy, see #5). **H1 (wall) is unavailable.**
- **Hypothesis (HYP-023):** structure-based stops beat volatility stops at equal mean D.
- **Null:** no difference after equalising mean D (expected under driftless motion).
- **Falsification:** H3 ≤ H2 in net R and in stop-out frequency at matched D.
- **Validation:** fixed entries (NEXA DNA plus random-entry null); per-symbol, per-regime.
- **Cost:** M.
- **Feature:** a stop-policy candidate.

### 4. Seasonal activity baseline + activity proxy confidence (EQ-005, TVPC_activity)
- **Equation:** RVOL = V / Ê[V | hour-of-week]; TVPC_activity per T1 §5.
- **Data:** tick volume (9 years); futures volume (2 years) for validation. **Proxy:** tick volume for spot (PROXY, measured).
- **Hypothesis:**
  - HYP-001 (proxy adequacy);
  - HYP-002 (RVOL adds to HAR).
- **Null:**
  - de-seasonalised r < 0.5;
  - no ΔQLIKE over HAR.
- **Status (T1):** the activity proxy PASSED for XAU, EUR and JPY (de-seasonalised r 0.55–0.60; 0.63–0.67 excluding roll windows) and FAILED for GBPUSD (0.45). Tick volume compresses surges (dispersion ratio ≈ 0.6). Hour-level proxy error is unpredictable (R² ≈ 0).
- **Validation:** next, the HYP-002 nested-HAR test (does RVOL add to HAR?), run on futures volume **and** tick volume (proxy swap).
- **Cost:** S.
- **Feature:** NF-010 / NF-011.

### 5. Value area from tick volume + profile proxy confidence (EQ-014, TVPC_profile)
- **Equation:** S42 greedy 70 % VA, POC; TVPC_profile (T1 §5).
- **Data:** M1 tick volume (proxy); futures volume (truth, 2 years).
- **Hypothesis:**
  - HYP-001 (profile proxy);
  - then HYP-007 (Value-Area Rule) using VA bounds only where TVPC is high.
- **Null:** for HYP-007, a matched placebo VA entry.
- **Status (T1):** the profile proxy PASSED for XAU, EUR and JPY (POC within 0.25σ on 67–75 % of days; VA Jaccard 0.76–0.82) and FAILED for GBPUSD. The dominant failure mode is bimodal days (POC failure 47–62 %). TVPC gating improves downstream agreement significantly. The pre-registered fitted TVPC failed its AUC bar; the exploratory TVPC_v1 reaches AUC 0.67.
- **Validation:** next, HYP-007 base rates with TVPC as a gate or covariate; XAU, EUR and JPY only.
- **Cost:** S (VA) + M (HYP-007).
- **Feature:** NF-024 / NF-035.

### 6. Causal futures→spot basis map (EQ-026)
- **Equation:** b̂_d = median over the previous day of (ln F − ln S').
- **Data:** Massive futures + MT5. **Proxy:** n/a.
- **Hypothesis (HYP-034):** mapping error ≤ 0.1 σ on ≥ 95 % of non-roll hours.
- **Status (T1):** PASSED for EUR, GBP and JPY (97–99.9 % of hours ≤ 0.1σ); **FAILED for gold** (88 %, p95 0.24σ).
- **Validation:** next, for gold, test an intraday basis update (e.g. hourly causal median). This needs a new ID.
- **Cost:** S.
- **Feature:** an enabler for NF-031 (futures-derived density at the spot price).

### 7. Regime transition matrix / HMM (EQ-023)
- **Equation:** P_ij on (σ̂ tercile × ER tercile), Dirichlet posterior; Gaussian HMM, filtered only.
- **Data:** M1, 9 years.
- **Hypothesis (HYP-020):**
  - regimes persist (P_ii > π_i);
  - the barrier outcome law differs by filtered regime beyond main effects.
- **Null:** i.i.d. regimes; no log-score gain.
- **Validation:** LR test, block bootstrap, walk-forward log score.
- **Cost:** M.
- **Feature:** NF-044.

### 8. Session / auction structure (EQ-016, 017, 018)
- **Equation:** IB, REX, CL, ROT with pre-registered UTC/DST anchors.
- **Data:** M1, 9 years. **Proxy:** none (time and price only).
- **Hypotheses:** HYP-008/009/010 (continuation vs post-trend reversal), HYP-011 (IB width), HYP-013 (base rate).
- **Null:** unconditional base rates (S42 provides none).
- **Validation:** Fisher exact tests with BH; per-symbol; discovery → validation → holdout.
- **Cost:** S–M.
- **Feature:** NF-040–043.

### 9. Revealed-liquidity field (EQ-012, 013)
- **Equation:** L(p,t) kernel density of traded (tick or futures) volume. g = ∂_p ln L; κ = h²∂²_p ln L.
- **Data:** M1 tick volume (proxy) or futures (2 years).
- **Hypotheses:** HYP-004 (traverse speed), HYP-005 (drift toward density), HYP-006 (HVN reversion / LVN continuation).
- **Null:** a placebo profile (different day); zero drift.
- **Validation:** survival model (HYP-004); hit-rate with block bootstrap (HYP-005); conditional autocorrelation (HYP-006).
- **Cost:** M.
- **Feature:** NF-030–033.

### 10. Effort–result residual / Amihud illiquidity (EQ-006, 007)
- **Equation:** EVR = ln|r| − fitted(ln V, season); ILLIQ = |r|/V.
- **Data:** M1 (proxy V); futures (true V, 2 years).
- **Hypotheses:**
  - HYP-003 (absorption at levels → reversal);
  - incremental volatility information (HYP-002 family).
- **Null:** off-level bars and placebo levels; zero coefficient.
- **Validation:** BH within the level family; proxy swap (futures V).
- **Cost:** S–M.
- **Feature:** NF-012 / NF-013.

---

**Deliberately excluded from the top 10:**
- **Every GEX equation** (EQ-027–029): data unavailable, sign unidentified.
- **True-flow equations** (EQ-011): no data.
- **Flow proxies** (EQ-008–010): proxy, circular, low prior.
- **Hawkes** (EQ-035): 28 days of ticks.
- **Entropy and physics analogies:** lower expected information gain.
