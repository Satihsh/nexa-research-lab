# CFT / CFT-P: results, 2026-10-18

**Pre-registration:** PREREG_CFT.md (d8ba8ce4, commit e8db910).
**Deviations:** DEVIATIONS_CFT.md (I-1…I-8, D-1, D-2).
**Code:** `qc_cft/main.py` (only the MODE line differs between runs). Editor hash verified before every run:

| MODE | Hash |
|---|---|
| F1 | f504897d |
| ACHK | 7604ebea |
| ES | f5ee7a3f |
| NQ | e11a7f20 |

**Where it ran:** QuantConnect project NEXA/CFT 37962171, free node. Each run once. The OOS window starts 2024-05-10 (the source paper's SSRN date) and ends 2026-07-17 (541 valid days).

## Verdicts

| Stage | Result | Verdict |
|---|---|---|
| **F1** classifier check (ES 2024-01-02…05) | Corrected after D-2: 1-s quote classifier corr 0.359 / sign 0.663; tick-rule fallback 0.683 / 0.751 | **FAIL → declared tick-rule fallback** |
| **A-chk** port check, ES 2009-05 → 2024-05-09 | Trend layer −0.14 bp/day [−1.31, +1.11]; S0 +1.08 | Not clearly negative → no porting investigation (§6) |
| **ES OOS (primary)** | A −0.75 [−3.25, +2.48]; **B −0.88 [−2.37, +0.54]**, 131 trades; B − A −0.14 | **INSUFFICIENT-N** (coded rule: < 150 B trades). The B mean is negative, so it is **REJECTED on the mean criterion** either way |
| B-EVE (ES) | −0.19 [−1.52, +1.35] | Fail |
| **NQ OOS (transfer)** | A **+2.72** [−1.35, +8.37], p 0.11, 3 / 4 blocks positive; **B +0.13** [−1.90, +2.54]; **B − A −2.59** [−7.90, +1.33] | **INCONCLUSIVE** |
| B-EVE (NQ) | +0.57 [−1.27, +2.42] | Fail (CI includes 0) |

All values are mean net daily bp at S1 costs; bootstrap 95 % CI in brackets.

**Primary verdict for CFT (core-flow gate on trend): NOT VALIDATED.**
- The gate did not improve the trend layer on either instrument (B − A < 0 on both).
- On ES, B lost money.
- On NQ, B is about zero.
- Descriptive DSR (NQ B, daily bp): 0.10 with 7 trials, 0.006 with 137 trials.

## CFT-P (prop overlay)
- PREREG §7: "CFT-P is used only if Stage B passes." **Stage B passed on neither instrument, so no overlay is recommended.**
- **ES:** every overlay × size cell had negative monthly $. Choice = none.
- **NQ:** the code's choice rule picked V3_k4 (+$259/month; P(pass 50K in 60 days) 19.5 %; **P(breach) 71.9 %**; P(≥ 20 green days of 21) = 0).
  - This is reported for completeness only. It rests on a B mean whose CI spans zero, and it fails the precondition.
- P(green day) was 6–12 % in every cell, because the gate trades rarely. The user's "20 green days a month" goal is at **0 %** in every cell on both instruments.

## Side observation (not a pre-registered claim; it must not be promoted without a new pre-registration)
- On NQ the **ungated trend layer (A)** averaged +2.7 bp/day (positive in 3 of 4 blocks, CI −1.3 to +8.4, p 0.11). Most of that came from shorts: 2,023 short points vs 831 long.
- On ES the same layer was −0.75 OOS and −0.14 over 2009–2024.
- One instrument, a CI including zero, and an in-sample loss on the primary instrument: this is not evidence of an edge. Under NEXA law L2 ("in-sample positives were regime luck"), the prior is low.

## Lessons recorded
1. **D-2:** a pre-OOS diagnostic (F1) had a silent data bug: one-sided quote ticks were dropped. It was caught only because the quote and tick-rule numbers came out identical. Diagnostics need a "can this be identical?" sanity check.
2. **A free signed-flow measure built from 1-second data is only moderately accurate** (corr ≈ 0.68 with tick-level aggressor flow). Any future order-flow gate on QuantConnect should use on-demand tick history at the decision points.
3. **The trend layer from Zarattini et al. (2024) did not replicate on ES futures after its publication date** at realistic costs.

## Files
| Item | File |
|---|---|
| ACHK log | `qc_cft/achk_logs_crying_blue_koala.txt` |
| ES OOS log | `qc_cft/es_oos_logs_upgraded_light_brown_chimpanzee.txt` → `cft_es_oos_results.json` |
| NQ OOS log | `qc_cft/nq_oos_logs_virtual_red_wolf.txt` → `cft_nq_oos_results.json` |
| F1 | `qc_cft/f1_results.json` |
