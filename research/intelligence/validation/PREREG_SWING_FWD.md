# PRE-REGISTRATION H-SWING-FWD: forward paper test of H-SWING, with an ES + NQ drift control

**Status: BINDING.**
- User approval 2026-10-18: "Pre-register the forward paper test with ES+NQ control".
- **Written before any data was read for this hypothesis.** No NEXA analysis has used daily data after 2026-07-21 for a trend signal. The ES + NQ long-only and buy-and-hold controls (§3) have never been computed.

**Why this test:**
- H-SWING (`SWING_REPORT.md`) came out INCONCLUSIVE, the closest NEXA result so far:
  - primary P: +2.18 bp/day net, 95 % CI [−0.02, +4.65] bp, 4/4 blocks positive;
  - secondary V-IDX (P on ES + NQ only): positive, but with no ES + NQ drift control.
- This test answers two separate questions:
  - **Part A (historical, now):** did V-IDX add anything over simply holding ES + NQ, 2011-01-03 → 2026-07-21?
  - **Part B (forward):** does P (and V-IDX) hold up on data **after** the original run, 2026-07-22 → 2027-12-31?

**What "paper" means here:**
- No orders, no broker, no account, no money.
- The frozen rules are re-computed on QuantConnect's data as it becomes available.
- QC's free futures data currently lags real time by about 3 months (the H-SWING run on 2026-10-18 ended at 2026-07-21). Each checkpoint therefore sees data up to roughly 3 months before the run date.

**Practical constraint (not a verdict input):**
- **Neither Apex nor Topstep allows these positions.** Topstep requires every position to be flat by 3:10 PM CT and says "no swing trading" (`TOPSTEP_RULES_SNAPSHOT_2026-10-18.md`).
- A confirmed result could only ever be used in an own futures account, under the user's capital rule.
- **Capital at today's prices** (`SWING_REPORT.md`): P needs ≈ $1.7M; V-IDX needs ≈ $66k at its 40 %-vol sizing.

**Nothing is re-tuned.** The rules, costs, volatility target, lookback, universe and statistics are exactly those of `PREREG_SWING_TREND.md` + `DEVIATIONS_SWING.md`. The engine functions are copied byte-for-byte from `qc_swing/main.py` (e8cf492d).

## 1. Data and windows
- **Same data settings as H-SWING:**
  - QC AlgoSeek daily futures, the same 20 markets;
  - `OPEN_INTEREST` mapping, `BACKWARDS_RATIO` adjustment;
  - America/New_York clock; data from 2009-01-01.
- **Windows (fixed now):**

  | Window | From | To |
  |---|---|---|
  | HIST | 2011-01-03 | 2026-07-21 (the last day of the H-SWING run) |
  | FWD | 2026-07-22 | 2027-12-31 (or the last day of data, if earlier) |
  | POOLED | 2011-01-03 | 2027-12-31 (or the last day of data, if earlier) |

- **Each day's net return is computed once, on the full history, then assigned to a window by date.** Warm-up and signals use all data ≤ t, exactly as in H-SWING.

## 2. Rules tracked (no new trading rules)
| Name | Rule | Role |
|---|---|---|
| **P** | 12-month TSMOM, 20 markets, w = s · min(3, 0.40/σ), monthly, decision at close t → executed at close t+1 | **Primary** (as in H-SWING) |
| V-IDX | P on ES + NQ only | Secondary |
| LONG | +min(3, 0.40/σ) on all 20 markets | Control for P (as in H-SWING) |
| **LONG-IDX** | +min(3, 0.40/σ) on ES + NQ only (the same sizing as V-IDX, always long) | **New control for V-IDX** |
| **BH-IDX** | Constant +1× notional on ES + NQ (plain buy-and-hold), from the same first valid day | **New control for V-IDX** (descriptive) |

- **Costs as H-SWING:**
  - 1/2/4 ticks + $2.50 round-trip commission;
  - charged on weight changes and at rolls;
  - **S1 (2 ticks) is primary.**
- **BH-IDX** pays one entry cost and roll costs only.

## 3. Part A: historical ES + NQ control (one run, now)
- **A0, reproducibility gate:**
  - HIST P must reproduce the H-SWING S1 mean 0.00021849, and HIST V-IDX 0.00075084, to the logged 8 decimals.
  - If either differs, QC's data has been revised. The difference is reported, and every number in that run is labelled "revised data".
- **A1 (decision statistic):** daily V-IDX − LONG-IDX over HIST. Moving-block bootstrap (block 20, B = 2,000, seed 20261018), 95 % CI, one-sided p. Verdict:
  - **TIMING VALUE:** mean > 0 and CI lower bound > 0. Following the 12-month trend on ES + NQ beat holding them long at the same size.
  - **DRIFT ONLY:** mean ≤ 0. V-IDX's H-SWING gain is explained by being long rising indices.
  - **UNRESOLVED:** otherwise.
- **A2 (descriptive):**
  - V-IDX − BH-IDX, and the Sharpe ratios of V-IDX, LONG-IDX and BH-IDX.
  - The raw difference mixes leverage, so only the Sharpe comparison is interpreted.
- **A3 (descriptive):** P − LONG over HIST, which must reproduce H-SWING's P_minus_LONG (8.589e-05).

## 4. Part B: forward checkpoints
- **Interim checkpoints:**
  - **descriptive only**; at most one per calendar quarter;
  - each re-runs the same frozen QC project;
  - no rule, parameter or window may change after any interim look.
- **Final checkpoint:**
  - the first run **on or after 2028-01-03** whose QC data reaches 2027-12-31;
  - if QC data has not reached 2027-12-31 by **2028-06-30**, the final run is made then on whatever data exists;
  - **FWD must have ≥ 250 trading days, otherwise INSUFFICIENT-N.**
- **Forward verdict (P primary; V-IDX reported the same way as secondary).** Let μ_H be this run's HIST S1 mean.
  - **FAILED:**
    - the POOLED mean ≤ 0, **or**
    - the FWD 95 % CI upper bound < μ_H, i.e. the forward period came in significantly below the backtest.
  - **CONFIRMED:**
    - the FWD mean > 0, **and**
    - the POOLED series meets the H-SWING G4 rule (CI lower bound > 0, ≥ 3 of 4 equal blocks > 0, ≥ 36 months).
  - **INCONCLUSIVE:** otherwise.
  - The code computes this label at every checkpoint. It is **binding only at the final checkpoint**.
- **Reported each checkpoint:**
  - FWD and POOLED statistics for all 5 rules;
  - V-IDX − LONG-IDX and P − LONG on FWD and POOLED;
  - share of green days and green months;
  - max drawdown;
  - descriptive DSR at the then-current trial count;
  - V-IDX figures rescaled to 10 % annual vol by one fixed factor (0.10 / HIST ann. vol of V-IDX). This is descriptive only, not a new rule.

## 5. Honest power statement (written before data)
- With ~360 forward days, the forward window alone **cannot** show that a Sharpe-0.4 rule works. Its standard error is ≈ 4 bp/day against a backtest mean of 2.2 bp/day.
- **If the true edge equals the backtest mean,** the chance that the POOLED series reaches G4 is roughly **a coin flip**.
- **If the true edge is zero,** CONFIRMED is unlikely but possible.
- FAILED catches only large shortfalls, e.g. a forward mean far below the backtest, or a collapse that turns the pooled mean negative.
- The test can confirm, kill, or leave the question open, and "open" is a likely outcome.

## 6. Multiple testing
- **No new trading rules.** P and V-IDX were already counted among H-SWING's 4 trials.
- **Ledger:** ≈ 161 trials, unchanged.
- **The forward look is one pre-declared final test.** Interim looks have no decision power.

## 7. Code, freeze, use
- **Algorithm `qc_swing_fwd/main.py`:**
  - H-SWING engine functions copied unchanged (the test checks that the source text matches);
  - adds `decisions_fwd` (LONG-IDX, BH-IDX), windowing, difference statistics and the verdict functions in §3–4;
  - logs `NEXA_SWING_FWD` JSON; places no orders.
- **Unit tests `test_swing_fwd.py`** on synthetic data:
  1. shared engine identical to H-SWING;
  2. LONG-IDX / BH-IDX weights;
  3. window boundaries;
  4. HIST statistics equal H-SWING `run_all` on data that ends before HIST_END;
  5. difference statistics on common dates;
  6. A1 control verdict;
  7. forward verdict incl. INSUFFICIENT-N;
  8. end-to-end smoke run across the HIST/FWD boundary.
- Tests must pass before hashing into PREREG_HASHES.txt. The QC editor hash is verified before every run.
- **Use of the result:**
  - Part A only labels V-IDX. It does not reopen daily trend-following.
  - **FAILED or INCONCLUSIVE at the final checkpoint:** daily trend-following stays closed.
  - **CONFIRMED:** leads only to a capital-feasibility review with the user (own account; not possible at Topstep or Apex).
  - No live trading, no purchase, no personal or borrowed capital follows from this test.
