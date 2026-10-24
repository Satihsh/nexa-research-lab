# H-FPT-REV results: JJ Simon "fair-pricing" reversion (NQ primary, ES transfer), 2026-10-18

- **Pre-registration:** `PREREG_FPT_REV.md` (committed 20f9444, before any data).
- **Code:**
  - `qc_fpt/main.py` (22311f83), frozen after 9/9 G1 tests;
  - ES file `qc_fpt/main_es.py` (9512d6b5): only MODE and F_FROM_NQ = 0.100465 differ, taken from the NQ log as pre-registered.
  - The QC editor hash was verified before each run.
- **Runs (once each, QuantConnect free node):**
  - NQ "Crawling Fluorescent Pink Parrot" (project 38025743);
  - ES "Measured Light Brown Leopard" (project 38026425).
  - Data 2010-01-04 → 2026-07-20.
- **Outputs:** `qc_fpt/fpt_{nq,es}_results.json`, raw logs in `qc_fpt/`.
- **Source:** SRC-YT-113, claims CL-155 (reversion) and CL-156 (opening continuation).

## Verdict: REJECTED on every pre-registered stream, on both instruments

| Stream | Trades | Mean net R (S1) | 95 % CI | Approx. gross R | Hit rate (driftless 0.397) | Green days | Longest losing streak | Verdict |
|---|---|---|---|---|---|---|---|---|
| **NQ P (primary)** | 13,490 | **−0.456** | [−0.500, −0.409] | −0.16 | 0.374 | 30 % | 17 | **REJECTED** |
| NQ V-FIX (source's literal 25/38 pts, 2023→) | 2,489 | **−0.147** | [−0.206, −0.098] | −0.07 | 0.370 | 45 % | 18 | REJECTED |
| NQ V-NO80 | 17,382 | −0.424 | [−0.468, −0.377] | −0.13 | 0.386 | 25 % | 16 | REJECTED |
| NQ V-OPEN (opening continuation) | 1,115 | −0.219 | [−0.289, −0.150] | −0.07 | 0.390 | 39 % | 14 | REJECTED |
| ES P | 11,128 | −0.403 | [−0.441, −0.368] | −0.11 | 0.374 | 33 % | 18 | REJECTED |
| ES V-NO80 | 14,583 | −0.390 | [−0.428, −0.357] | −0.10 | 0.378 | 29 % | 21 | REJECTED |
| ES V-OPEN | 921 | −0.209 | [−0.289, −0.120] | −0.06 | 0.384 | 38 % | 11 | REJECTED |

- "Approx. gross" = the S0 mean plus the S0 cost in R. It is the edge **before** commission and slippage.
- **No stream has a positive year block.** All 4 time blocks are negative everywhere.
- In the primary streams, every single year 2010–2026 is negative on both instruments.
- **The trades lose before costs.** Every stream's target-hit rate is below what a random walk would give for this bracket (0.397).
  - Entering toward the 09:30 open after a 1-minute displacement or break of structure is, on average, entering *against* short-term continuation.
  - This is an observation only. The opposite direction is **not** a new candidate without a new pre-registration (NEXA law L2).
- **Losses shrink in recent years, but no year turns positive.** NQ P: 2010 −0.92 → 2022 −0.10, 2026 −0.14. Part of the early-year damage is the fixed point cost against small volatility-scaled stops (mean stop 10.4 NQ points over the whole sample).
  - **V-FIX removes that effect:** the literal 25-point stop in the source's own price regime, 2023 onward. It is still −0.147R net and −0.07R gross.
- **Prop threshold (H-PROP-EV):** none of the streams reaches +0.025R. The best, NQ V-FIX at −0.147R, would lose about $100+ per Apex 50K evaluation at list price, just like random entry.
- **DSR:** not meaningful. Every mean is negative with CIs entirely below 0 (≈ 0 at 7 and at ~157 trials).

## What this means
- The one fully mechanical strategy in batch 10, from the guest with the largest documented prop payouts, **has no edge on 16 years of CME data**, on either NQ or ES, or in its source's own period.
- This is consistent with H-PROP-EV and the source's own account (SRC-YT-113):
  - his income is explained by prop-firm convexity (fees, many accounts, capped downside, cross-account layering), not by the entry rule;
  - he reports ~$400k of fees and payouts that fall as firms tighten.
- **NEXA tally:** no intraday rule from the video sources has passed a pre-registered test. Rejected or not predictive so far:
  - OFC1, OFC1R;
  - H-ORB30L (OOS);
  - T1, T2a;
  - CFT;
  - H-FPT-REV.

## Files
| Item | File |
|---|---|
| NQ log / results | `qc_fpt/nq_logs_crawling_fluorescent_pink_parrot.txt`, `qc_fpt/fpt_nq_results.json` |
| ES log / results | `qc_fpt/es_logs_measured_light_brown_leopard.txt`, `qc_fpt/fpt_es_results.json` |
| Code / tests | `qc_fpt/main.py`, `qc_fpt/main_es.py`, `test_fpt.py` |
