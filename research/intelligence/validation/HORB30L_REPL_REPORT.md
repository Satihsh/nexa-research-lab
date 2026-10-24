# H-ORB30L-REPL Part A report: out-of-sample replication on QuantConnect NQ, 2009–2023. **FAILED.**

**Date:** 2026-10-16.
- **Pre-registration:** `PREREG_HORB30L_REPL.md` (758f8a31); deviations D-1…D-12 in `DEVIATIONS_HORB30L_REPL.md`.
- **Code:** QuantConnect project 37866267.
  - The editor contents were hash-verified as `main_oos_variant.py` (c9682d25), byte-identical to the frozen in-sample engine port (0 / 896 mismatches locally, D-3) except for the MODE line.
- **Pre-flight:** the smoke check on 2023-03-01…07 matched the local engine exactly, 5 / 5 (D-12).
- **Run:** backtest "Focused Yellow Green Bee", algorithm c4a3b304…, free Community node, LEAN 2.5.0.0.18184, 19,112,101 data points. **Run once.** No orders placed.
- **Raw output:**
  - `qc_horb30l_oos/oos_logs_focused_yellow_green_bee.txt` (sha a2922b1e…);
  - `horb30l_qc_oos_results.json`;
  - trades hash ef132768….

## Verdict: **FAILED**, so H-ORB30L-NQ is CLOSED

The out-of-sample mean net R is **negative**, and its whole 95 % interval is below zero.

| | Out-of-sample 2009-01-02 → 2023-02-17 (NQ) | In-sample 2023-02-18 → 2026-10-10 |
|---|---|---|
| Trades | **1,604** | 460 |
| Mean R, S1 (2 pts) | **−0.071** [−0.111, −0.035] | +0.058 [+0.002, +0.123] |
| Mean R, S0 / S2 | −0.029 / −0.113 | — |
| Mean points per trade, S1 | −1.02 | — |
| Win rate | 50.0 % | — |
| Exits (stop / target / time) | 471 / 405 / 728 | — |
| 2R target (secondary) | −0.049 [−0.090, −0.010] | — |
| N2 beta control (10:00 entry) | −0.087 (1,838 days) | −0.058 |
| Primary − N2 | +0.016 | +0.116 |
| Years positive | 6 / 15 (40 %) | 4 / 4 |
| MNQ at $100 risk per trade | **−$48 per month mean** (median −$34); 44 % of months positive; worst month −$1,207 | ≈ +$100 per month |

**Pre-registered checks:**

| Check | Result |
|---|---|
| 1. Mean > 0 and CI lower bound > 0 | ✗ |
| 2. Primary − N2 > 0 | ✓ (+0.016) |
| 3. ≥ 60 % of years positive and no year > 25 % | ✗ (40 %) |
| 4. ≥ 300 trades | ✓ |

The S1 mean ≤ 0, so the verdict is **FAILED**.

**Per year (sum of R, S1):**

| Year | Sum of R |
|---|---|
| 2009 | −14.9 |
| 2010 | +2.9 |
| 2011 | −24.6 |
| 2012 | −13.7 |
| 2013 | −19.3 |
| 2014 | −6.7 |
| 2015 | −17.2 |
| 2016 | −21.1 |
| 2017 | −9.1 |
| 2018 | −8.6 |
| 2019 | +3.9 |
| 2020 | +0.2 |
| 2021 | +9.3 |
| 2022 | +3.0 |
| 2023 (to 17 Feb) | +2.0 |

The cost floor (R < 10 pts) skipped 133 days, mostly 2009–2013.

## What this means (no spin)

- The in-sample edge (+0.058 R, 2023–26) was **specific to that period**. Over 14 earlier years the same frozen rule lost about 0.07 R per trade after a 2-point cost.
- It also lost before costs: −0.03 R even at a 1-point cost.
- The rule's small advantage over simply buying at 10:00 (+0.016 R) does not cover costs.
- The years after 2019 are mildly positive and 2009–2018 clearly negative. That is a description, **not a new hypothesis**. Choosing "recent years only" after seeing this would be curve-fitting.

**Consequences (`PREREG_HORB30L_REPL.md` §4):**
- The rule is **closed**. No ATAS alert, no demo, no prop evaluation.
- The Part B forward log stops after notice to the user (2026-10-16).
- Parts A-D (Dukascopy, never run) and A-H (HistData, NOT EVALUABLE) are superseded by this result.
