# H-ML1 results: machine-learning intraday direction model on NQ / ES (2026-10-18)

- **Pre-registration:** `PREREG_ML1.md` (before data).
- **Clarifications and pre-data placebo fix:** `DEVIATIONS_ML1.md` (C-1, C-2, D-1).
- **Code:** `qc_ml1/main.py` (00614c06), frozen after 10/10 synthetic G1 tests. The QC editor hash was verified before the run.
- **Run:** once; QC free node; project 38041026; backtest "Jumping Asparagus Caribou"; 326 s; 15.0 M data points.
- **Data:** 3,900 kept days, 2010-01-04 → 2026-07-20 (281 incomplete days and 90 roll days skipped); 81,480 decision rows per target.
- **Outputs:** raw log `qc_ml1/logs_jumping_asparagus_caribou.txt` (sha 1a38748e); parsed `qc_ml1/ml1_results.json`.

## Verdict: REJECTED on both instruments

| Target | Window | Trades | Trades/day | **Net R/trade (S1)** | 95 % CI | Gross R | Win rate | Green days | Placebo P-rank |
|---|---|---|---|---|---|---|---|---|---|
| **NQ (primary)** | V 2013–2022 | 1,015 | 0.43 | **−0.032** | [−0.092, +0.017] | +0.065 | 50.5 % | 47.7 % | — |
| **NQ (primary)** | **H 2023 → 2026-07** | 566 | 0.66 | **−0.007** | [−0.070, +0.045] | +0.025 | 53.0 % | 46.2 % | **0.25** (5 of 20 placebos as good) |
| ES (secondary) | V | 1,001 | 0.42 | −0.011 | [−0.058, +0.043] | +0.086 | 52.0 % | 47.4 % | — |
| ES (secondary) | H | 604 | 0.70 | −0.026 | [−0.085, +0.028] | +0.019 | 50.5 % | 44.6 % | 0.35 |

- **Binding rule:** the H mean ≤ 0 ⇒ **REJECTED**. Both instruments fail on every criterion:
  - the hold-out mean is negative;
  - neither CI excludes 0;
  - only 2 (NQ) or 1 (ES) of 4 hold-out blocks are positive;
  - 25–35 % of the placebos, trained on shifted labels, did as well.
- **The +0.10R Topstep target was never in reach.** The best single window (ES validation) earns +0.086R **before** costs and −0.011R after.
- **Costs are what remain:**
  - the model's small gross edge (+0.02 to +0.09R) is about the size of one round trip of costs in R;
  - at S0 (1 NQ point) NQ is +0.009 to +0.016R, at S2 negative;
  - this is the same pattern as C1, IM1 and FX1: something real-looking that is smaller than the cost of trading it.
- **The model mostly went long** (73–82 % of trades) yet did no better than going long at the same times (B1: NQ H −0.010R, V −0.133R). There is no meaningful direction skill.
- **Trade rate:** 0.4–0.7 trades a day, below the user's 1–2. The δ threshold, calibrated on the two preceding years, was rarely reached in later years.
- **Year by year (NQ H):** 2023 +0.041, 2024 +0.084, 2025 −0.033, 2026 (partial) −0.188. Positive stretches did not persist.
- **Green days** 45–48 %, **green months** 49–53 %. As always, not close to the user's 18/20 goal.

## What this closes
- Pre-registered §6: **the intraday ML search on ES/NQ with public price/volume features is closed at this feature set.** No feature or parameter re-tuning on this data (NEXA law L2).
- **The individual time-of-day cells** (e.g., NQ H 15:45 +0.34R on 11 trades) are noise across 21 × 4 cells and are **not** candidates.
- **NEXA intraday tally:** every pre-registered intraday test on index futures has now failed:
  - OFC1, OFC1R;
  - H-ORB30L (OOS);
  - H-IVB1, H-IM;
  - T1, T2a;
  - CFT;
  - H-FPT-REV;
  - **H-ML1**.
- **Multiple-testing ledger:** ≈ 163 trials.

## What it does *not* say
- It says nothing about data NEXA cannot see for free: full order book (MBO), options flow, news text, or co-located speed. Those are where professional intraday edges live, and they are costly or not available to a retail trader.
- It is one fixed model with fixed features. A different model could be tried, but each further attempt on the same data raises the chance of a false positive, and the prior from 10+ failures is low.
