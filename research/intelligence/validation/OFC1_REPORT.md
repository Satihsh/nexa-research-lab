# OFC1 results: the user's core order-flow method on CME futures (2026-10-11)

- **Pre-registration:** `PREREG_OFC1_CORE_ORDERFLOW.md` (sha ede1bc8d…).
- **Code, tests and deviations D1–D10:** hashed before discovery opened (`PREREG_HASHES.txt`, 08:27 UTC); 14/14 unit tests passed.
- **Splits:** discovery → validation → holdout, each opened once.
- **Raw output:** `ofc1_results_disc.json`, `ofc1_results_val.json`, `ofc1_results.json` (all trades included), `ofc1_dsr_posthoc.json`.
- **Data:** Databento trades with aggressor side, 6E / 6J / 6B / GC, 2025-09 → 2026-09.
- **Evaluation:** on CME prices, net of USD 2.61/side (GC 2.66) and 1 tick of slippage on entries and stops.

## Verdict: **INSUFFICIENT-N** (per §6). Every point estimate is negative; there is **no evidence of an edge**.

- 130 trades in total, against a pre-registered minimum of 150; the holdout had 26, against a minimum of 30.
- **What the minimum-N rule means here:** the rule withholds a formal REJECTED. It does **not** make the result promising.
  - Discovery, validation and holdout are all negative.
  - The pooled S0 mean is −0.21 R; the S1 confidence interval lies entirely below zero.
- **Had the sample met the minimum, the pre-registered REJECTED rule (pooled mean ≤ 0) would apply.**

| Split | Trades | Mean R (S0) | 95 % CI | p (one-sided, > 0) |
|---|---|---|---|---|
| Discovery (Dec 2025 – Apr 2026) | 79 | **−0.246** | [−0.472, −0.004] | 0.976 |
| Validation (May – Jul 2026) | 25 | **−0.218** | [−0.669, −0.050] | 0.989 |
| Holdout (Aug – Sep 2026) | 26 | **−0.088** | [−0.522, 0.346] | 0.670 |
| **Pooled S0** | 130 | **−0.209** | [−0.393, 0.022] | 0.963 |
| Pooled S1 (+1 tick stress) | 130 | −0.257 | [−0.444, −0.024] | 0.985 |

**Acceptance criteria:** 6 of 7 failed. Only criterion 5 passed.

| # | Criterion | Result |
|---|---|---|
| 1 | Discovery p < 0.05 | ✗ |
| 2 | Validation and holdout > 0 | ✗ |
| 3 | Pooled CI lower bound > 0 | ✗ |
| 4 | Timing placebo p ≤ 0.05 | ✗ (p = 0.94) |
| 5 | Order-flow value Δ > 0 | **✓** (point estimate only, see below) |
| 6 | Stability | ✗ |
| 7 | DSR ≥ 0.95 | ✗ (DSR = 0.00) |

## Secondary results (pooled; BH within the family)

| Family | Trades | Mean R | Note |
|---|---|---|---|
| Setup A (long at VAL → VAH) | 55 | −0.275 | |
| Setup B (short below VAL → LVN) | 2 | −0.436 | Rare: needs a confirmed break **and** an LVN below |
| A′ (short at VAH → VAL) | 72 | −0.156 | |
| B′ (long above VAH → LVN) | 1 | +0.037 | n = 1, meaningless |
| 6E | 47 | −0.347 | CI [−0.60, −0.07] |
| 6J | 9 | +0.333 | **9 trades.** The block bootstrap is degenerate at this size; BH-adjusted 0.002 is **an artefact, not evidence** |
| 6B | 8 | −0.390 | |
| GC | 66 | −0.163 | |

**Nulls:**
- **N1 timing placebo:** random entry minutes with the same stops, targets and costs average −0.046 R. The method's −0.209 R is **worse than random timing** (p = 0.94).
- **N2 (the same rules without order-flow confirmation):** 1,143 trades at −0.372 R.
  - Confirmation improves the mean by Δ = +0.163 R (CI [−0.086, 0.428], p = 0.095).
  - So order-flow confirmation **cuts losses and filters about 90 % of triggers**, but leaves the result negative.

**By session block:** Asia −0.24 R (35 trades), London −0.03 (19), NY −0.24 (76).

**Exits:** 49 at target, 66 stopped, 15 at the time limit.

## Robustness (reported only; never changes the verdict)

All variants are negative: cost floor off −0.30 (211 trades); NinjaTrader imbalance form −0.21 (163); E2 5 % −0.32 (98); E2 20 % −0.23 (154); first bubble −0.04 (100); stack ≥ 2 −0.23 (357); exits on 1-min closes −0.31 (126).

## Post-run note (D11)

- **Missing DSR:** the run did not compute the DSR, because `nexa_robust` imports scipy, which the Databento venv lacks.
- **Computed afterwards** from the saved results with the NEXA research venv: the same formula and inputs, n_trials = 10, and var_sr over the 10 trial Sharpe ratios (`ofc1_dsr_posthoc.json`). **DSR = 0.00.**
- No other output was affected.

## Interpretation (evidence class: NEXA, pre-registered)

1. **As translated into rules and run on true CME aggressor data, the method lost money in every period tested:** about −0.2 R per trade after realistic costs.
2. **Its timing was worse than random entries with the same risk geometry.** That points away from costs alone as the cause.
3. **The order-flow confirmation is the only component with a hint of value (+0.16 R vs no confirmation).** It is not significant, and it is not enough.
4. **Limits:**
   - Ten scored months and one regime.
   - The trade count is below the pre-registered minimum.
   - A rule translation of a discretionary, visual method (U7).
   - CME prices, not Pepperstone (U1).
   - **This result does not test the user's discretion.** It tests these rules.
5. **No re-run with altered rules under OFC1.**
   - **Not allowed:** a variant (e.g. "London only", "first bubble") chosen from these results, unless it is pre-registered as new and tested on **unseen data**.
   - **Unseen data:** 2023–2025 history has not been bought or seen. A replication of the **frozen** OFC1 rules on it would be a clean out-of-sample test. It would cost about USD 62 per year for all four instruments, or about USD 26 per year for 6E/6J/6B.
