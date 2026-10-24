# H-SWING-FWD deviations

## D-1: QC log truncation (recorded 2026-10-18, after the Part A run, before any forward data exists)
- **What happened:**
  - Part A ran once ("Alert Green Caterpillar", project 38036244, code be25c85c).
  - QuantConnect cut the `NEXA_SWING_FWD` log line at 8,193 characters, mid-way into `controls`.
  - All five rules' HIST / FWD / POOLED statistics arrived complete. Lost were:
    - the `controls` block (bootstrap CIs of V-IDX − LONG-IDX, V-IDX − BH-IDX, P − LONG);
    - `A1_verdict`, `A0` and `fwd_verdict`.
  - The H-SWING log (7.9 k chars) had been just under the limit.
- **Part A verdict without the lost block.** §3 A1 says DRIFT ONLY if the mean of V-IDX − LONG-IDX is ≤ 0. That mean is recoverable exactly from the logged means:
  - V-IDX and LONG-IDX use the same two markets, the same warm-up mask (both from `decisions(..., 'LONG' | 'P')` with identical NaN positions) and the same `portfolio()` averaging;
  - both report n_days = 4,005, so their day sets are identical;
  - the mean of the daily difference is therefore the difference of the means: 0.00075084 − 0.0012045 = **−0.00045366** (±1e-8 from the logged rounding);
  - this is ≤ 0, so the pre-registered rule gives **A1 = DRIFT ONLY**. The CI is not needed for this label.
  - The CI is reported as "not available in the Part A run". The next checkpoint recomputes the identical HIST statistic deterministically (same data unless QC revises it; A0 flags that) and will log it.
- **A0 (reproducibility) from the complete part:** HIST P S1 mean 0.00021849 and HIST V-IDX 0.00075084 match H-SWING exactly. **Data not revised.** The P − LONG check (A3) was in the lost block; it is deferred to the next checkpoint.
- **Fix for all later checkpoints (code v2):**
  - The JSON output is logged in numbered chunks of ≤ 7,000 characters: `NEXA_SWING_FWD_PART i/n …`.
  - `fwd_post.py` reassembles the chunks.
  - Nothing else changes. Test 9 checks that every function and constant of v1 (`qc_swing_fwd/main_v1_be25c85c.py`) is source-identical in v2. Test 10 checks that chunking is lossless and that every line fits.
  - G1 tests 10/10 (+ H-SWING 9/9) pass. The v2 hash is recorded in PREREG_HASHES.txt.
- **No statistic, window, rule, threshold or verdict changes.** No forward data existed when this was written (QC data ends 2026-07-20).
