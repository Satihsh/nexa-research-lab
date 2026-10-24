# PRE-REGISTRATION OFC1R: final out-of-sample replication of the frozen OFC1 rules on 6E, 2023–2025

**Status: BINDING. FINAL.**
- **User approvals (2026-10-11):**
  - "Approved, buy 2023–2025 6E/6J/6B and replicate OFC1, make sure this is final run, I dont want to spend more here";
  - then the choice "6E only, 2023–2025" (USD 49.88, from the free credit; the full 6E/6J/6B request at USD 110.80 exceeded the remaining credit).
- **Timing:** written and hashed **before the data is downloaded or seen**.
- **Finality:**
  - After this run, the OFC1 line is **closed whatever the result**.
  - No further data purchases, no variants and no re-runs on this question.

## 1. Purpose and rules

- **Purpose:** a confirmatory test of the **unchanged** OFC1 rules on data no one has seen.
- **Rules:** `ofc1_core.py` (sha 4065c597…, read-only), with deviations D1–D10 (`DEVIATIONS_OFC1.md`, sha 18376024…).
- **DSR:** computed with the NEXA research venv (D11).
- **Not re-chosen:** no parameter, threshold, cost or setup.

## 2. Data

- **Source:** Databento `GLBX.MDP3` trades, `6E.v.0`, 2022-10-01 → 2025-09-01. Only this file is loaded; the 2025-09 → 2026-10 OFC1 files are **not** part of this run.
- **Degraded dates:** `orderflow/databento/dataset_condition_2022-10_2025-08.json`, fetched before download; 1 date, 2024-09-18.
- **Exclusions:** sessions touching a degraded date are excluded, as in OFC1.
- **Warm-up:** from 2022-10 until 60 prior Q-valid sessions exist.
- **Scored sample:** server days **2023-01-01 → 2025-08-31**, one sample (`replication`), opened once.

## 3. Statistics and criteria

**Statistics:**
- **Primary:** pooled net (S0) mean R per trade.
- **Uncertainty:** session-date moving-block bootstrap (block 5, B 2,000, seed 20261011); one-sided p for mean > 0.
- **Reported:** S1, nulls N1 (timing placebo, 200 draws per trade) and N2 (no confirmation, Δ), per setup, per calendar year (2023, 2024, 2025 partial), per block, and the robustness variants of OFC1 §8.

**Minimum sample:** ≥ 150 trades; otherwise **INSUFFICIENT-N**.

**Acceptance** ("replicated", research candidate under RESEARCH_GATE G4); all are required:
1. Pooled S0 mean R > 0 with one-sided p < 0.05.
2. Pooled S1 mean R > 0.
3. N1 timing placebo p ≤ 0.05.
4. N2: Δ > 0 (point estimate).
5. ≥ 2 of the 3 calendar years with a positive mean, and no year > 50 % of pooled net R.
6. DSR ≥ 0.95 at n_trials = 10 (the OFC1 trial count; the configuration is unchanged).

**Verdicts:**
- **REJECTED** if pooled S0 mean ≤ 0 (evaluated before the N check, so a negative result is never masked as INSUFFICIENT-N).
- **INSUFFICIENT-N** if n < 150 and the mean > 0.
- **REPLICATED** if all criteria pass.
- **INCONCLUSIVE** otherwise.

**Descriptive only:** the combined OFC1 + OFC1R 6E sample is reported alongside, with no verdict from it.

## 4. Code

- **Wrapper:** `ofc1r_run.py`, thin. It imports `ofc1_core` unchanged and overrides only the split table, the loaded file, the degraded-date file and the instrument list (6E).
- **Hashing:** hashed with this file before the download.
