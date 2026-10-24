# H-SK28-OOS report: the frozen s-k-28 12-model NQ system on 2010–2022

**Verdict: REJECTED** (pre-registered rule: P mean net R ≤ 0). Pre-registration `PREREG_SK28_OOS.md` (5c8569bf); deviations D1–D4 in `DEVIATIONS_SK28_OOS.md`, all logged before any QuantConnect run. Date 2026-10-23.

## What was tested
- Their code at commit 0ee4392d, 25 files byte-identical (24 uploaded to QC; the empty `backtest/__init__.py` left out, D4).
- Pipeline exactly as their `run_multi.py`.
- NQ continuous, Panama-adjusted, 23-hour minute bars on QuantConnect's free node.
- Half-year chunks with a 120-day warm-up (D2).
- Costs: NEXA standard, 2 NQ points per round trip (S1).

## The port check passed (the copy is faithful)
| Check | Result | Bar |
|---|---|---|
| Their own file, chunked vs full run (offline) | **454 / 454** trades identical | — |
| QC data 2023–2025 vs their file: reference trades matched | **2,297 / 2,435 = 94.3 %** (every model 90–98 %) | ≥ 50 % |
| QC trade count vs reference | 2,418 vs 2,435 = **0.99** | 0.80–1.25 |
| End-labelled bars (first ETH bar 18:01) | 1,256 / 1,258 sessions | — |

## Results (net R per trade at S1 unless stated)
| Set | Trades | Gross | S0 | **S1** | S2 | 95 % CI (S1) | Blocks > 0 |
|---|---|---|---|---|---|---|---|
| **P 2010–2022 (binding)** | 3,708 | +0.144 | +0.061 | **−0.021** | −0.104 | [−0.057, +0.013] | **0 / 4** |
| P-late 2018–2022 | 3,240 | +0.152 | +0.070 | −0.012 | −0.094 | [−0.045, +0.027] | 1 / 4 |
| IN 2023–2025 (their build window, QC data) | 2,418 | +0.215 | +0.135 | +0.054 | −0.026 | [+0.019, +0.096] | 4 / 4 |
| Their file, HEAD code (local reference) | 2,435 | +0.225 | +0.145 | +0.064 | −0.017 | — | — |

- **Random-direction control (2,000 replicates):** control mean −0.014, 95th percentile +0.011. The real −0.021 sits at the **33rd percentile**: no better than flipping the direction at random.
- **Per year (trades, S1):**

  | Year | Trades | S1 |
  |---|---|---|
  | 2010 | 25 | −0.06 |
  | 2011 | 41 | −0.01 |
  | 2012 | 21 | +0.06 |
  | 2013 | 30 | +0.18 |
  | 2014 | 55 | −0.18 |
  | 2015 | 108 | −0.11 |
  | 2016 | 97 | −0.07 |
  | 2017 | 91 | −0.20 |
  | 2018 | 503 | −0.03 |
  | 2019 | 348 | −0.04 |
  | 2020 | 732 | −0.02 |
  | 2021 | 774 | −0.01 |
  | 2022 | 883 | +0.02 |

  Only 2012, 2013 and 2022 are positive; in the build years 2023/24/25 S1 is +0.01/+0.03/+0.13.
- **Per model (S1), none passes alone, and this is descriptive only:** pd_rev +0.10 (176), kalman_mom +0.07 (335), sweep +0.03, vwap_rev +0.02, pm_mom 0.00, ou_rev −0.01 (615), ou_lunch −0.04, ema_rev −0.04, trend −0.04, vwap_scalp −0.05, open_drive −0.09 (490), or_rev −0.11 (411).
- Long −0.026 (2,039), short −0.016 (1,669).
- Win rate 45.7 %; average win +0.96R vs average loss −0.85R.
- Exits: trail 2,381, stop 1,232, time stop 80, target 15.
- Max drawdown 129R; longest losing streak 14.
- **Topstep 50K, 1 MNQ per trade:** the trailing limit is first breached on **2020-02-11**.
- **Scale effect (pre-declared):** 2010–2017 has only 21–108 trades a year, because NQ's moves rarely fit the fixed 10–20-point stop band. That part of P is thin. But P-late (2018–2022, ≈ 650 trades a year, comparable to the build years) is also negative (−0.012R).

## Reading
- The system has a **small gross edge (+0.14R)** that a realistic 2-point cost wipes out. Before costs it is real; after costs it is not.
- Its out-of-sample S1 is below zero and no better than random direction. The +0.054R on QC data 2023–2025 lives in the window the 12 models were built on, mostly 2025 (+0.13R).
- This matches the prior: tuned on 3 years, tight stops, and the same 2022–25 file that the failed FYP project used.

## Use (pre-registered)
- S73 closes; no re-tuning (NEXA law L2).
- No cherry-picking of pd_rev / kalman_mom: any single model would need its own pre-registration on data not yet seen, and QC has no NQ history before 2009.

## Files
- **Logs:** `qc_sk28/runlogs/sk28_<year>-<half>.txt`, 32 files, each hash-checked against the page.
- **Results:**
  - `qc_sk28/sk28_results.json` (from `sk28_stats.py`);
  - `qc_sk28/gate_result.json`;
  - `qc_sk28/ref_out/` (local reference, chunk check).
- **QuantConnect:** project 38332500; one backtest per chunk. Each backtest's name ends in the first 8 characters of its frozen `main.py` hash, and that hash was checked in the QC editor before every run.
