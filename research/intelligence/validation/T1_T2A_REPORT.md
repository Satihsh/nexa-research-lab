# T1 (H-STATE) and T2a (H-VAR): results, 2026-10-18

**Pre-registrations:** PREREG_T1_STATE.md (3a162810), PREREG_T2A_VAR.md (b65cfc41), both commit c77177b.
**Code:** `qc_asm/main.py`, frozen at 686c288 with 10/10 synthetic tests; interpretations in DEVIATIONS_T1_T2A.md.

**Runs (QuantConnect project NEXA/ASM 37990423, free node; each run once; editor hash verified before each run):**

| Instrument | Backtest | Code hash | Log file |
|---|---|---|---|
| ES | "Crying Fluorescent Yellow Owlet" | 6eb5ff40 | `qc_asm/es_logs_crying_fluorescent_yellow_owlet.txt` |
| NQ | "Virtual Fluorescent Yellow Pony" | 197427f5 | `qc_asm/nq_logs_virtual_fluorescent_yellow_pony.txt` |

**Period:** 2010-01-04 → 2026-07-17. Valid days: 3,895 for ES, 3,823 for NQ.

## Verdicts

| Test | ES | NQ |
|---|---|---|
| **T1 · auction state predictable by 11:00 ET** | **NOT PREDICTABLE** | **NOT PREDICTABLE** |
| **T2a primary · VA re-entry, 15-min, 2R** | **REJECTED** | **REJECTED** |
| T2a V-5m | REJECTED | REJECTED |
| T2a V-VA (target = opposite VA edge) | REJECTED | REJECTED |
| T2a V-EVE (signals by 12:00 ET) | REJECTED | REJECTED |

## T1 detail (continuation score Y in bp of rest-of-day return; + = the morning move continues)

| | ES | NQ |
|---|---|---|
| Initiative days (outside prior VA at 11:00) | 2,748 | 2,707 |
| Responsive days (inside prior VA) | 1,147 | 1,116 |
| H1 mean Y, initiative (want > 0) | +0.23 [−2.42, +2.64], p 0.45 | +1.46 [−1.70, +4.33], p 0.20 |
| H2 mean Y, responsive (want < 0) | +0.14 [−3.11, +3.87], p 0.55 | **+3.45** [−1.19, +7.84] (wrong sign) |
| H3 Δ = H1 − H2 (want > 0) | +0.09 [−4.52, +3.98], p 0.51 | **−1.99** [−7.48, +3.35], p 0.80 |
| Blocks with Δ > 0 | 2 / 4 | 1 / 4 |
| Morning-direction baseline Y_B | +0.73 | +2.33 |
| Hit P(Y > 0): initiative / responsive | 0.52 / 0.50 | 0.53 / 0.50 |
| Mean \|rest-of-day return\| | 44 bp | 54 bp |

**Sub-labels (mean Y):**
- ES:
  - migration −0.16 (2,006 days);
  - breakout +1.30 (742);
  - **failed auction +1.92** (503);
  - responsive-inside −1.28 (627).
- NQ:
  - migration +0.57;
  - breakout +3.46;
  - **failed auction +4.54**;
  - responsive-inside +2.59.

**Reading:**
- Where price sits relative to yesterday's value at 11:00 tells nothing about whether the morning move continues or reverts.
- The classic "failed auction" day (opened outside value, back inside by 11:00), which the 80 % rule relies on, did **not** revert on either instrument. Its point estimates even lean toward continuation.
- All effects are a few bp against a typical 44–54 bp rest-of-day move, i.e. noise.

## T2a detail (net R per trade at S1 costs; bootstrap 95 % CI)

| Variant | ES trades | ES mean R [CI] | NQ trades | NQ mean R [CI] |
|---|---|---|---|---|
| **Primary (15m, 2R)** | 1,431 | **−0.046** [−0.100, +0.013] | 1,468 | **−0.045** [−0.096, +0.006] |
| V-5m | 2,088 | −0.110 [−0.160, −0.063] | 2,105 | −0.118 [−0.169, −0.069] |
| V-VA | 1,627 | −0.067 [−0.112, −0.015] | 1,643 | −0.071 [−0.121, −0.018] |
| V-EVE | 998 | −0.036 [−0.108, +0.038] | 1,038 | −0.060 [−0.128, +0.005] |

**Primary, ES:**
- Before costs: S0 −0.005R; S2 −0.126R.
- Exits: target hit 14.7 %, time exit 48.8 %.
- Payoff 1.25; green-day share 43 % (days with a trade).
- Max drawdown 93R; Sharpe of daily R −0.40.
- Positive in 1 of 4 blocks, and in 5 of 17 years.

**Primary, NQ:** S0 +0.007R; target 15.1 %; time exits 50 %; green-day share 42 %; Sharpe −0.40.

**Setup frequency:** the prior session closed inside its value area on about 61 % of days (ES 2,373 of 3,895).

**Descriptive DSR (primary, daily R moments):** ≈ 0.001 with 8 trials; ≈ 0.00001 with 150 trials (ES and NQ alike).

**Reading:**
- The re-entry close does not lead to a reliable rotation through value.
- Gross of costs the primary is essentially zero; with realistic costs it is negative.
- About half the trades are still open at the close: the wide stop at the excursion extreme makes 2R targets far away.
- The 5-minute version (more signals, nearer stops) is clearly worse.
- The evening-window version is no better.

## What this means for the 20-pillar plan (ASM)

1. **The "context first" foundation failed its first direct test.**
   - Pillars 2, 14, 16 (value-area location, failed auctions, initiative vs responsive), measured with the standard definitions on 16 years of ES and NQ, do not predict the rest of the day.
   - This matches OF-16 (FX/XAU, inconclusive) and the CFT ES result (no trend edge out of sample).
2. **The most mechanical, most widely repeated value-area setup (Dalton 80 % rule = Data Trader S2) is rejected on both instruments.**
3. **There is no basis for T3** (T2a conditioned on the T1 state): T1 found no state signal to condition on. T3 is dropped unless a new state definition is pre-registered.
4. **Still open and testable at $0:**
   - **T2b** stop-run reversal with approach speed / time-to-continuation (CL-145, CL-150);
   - **T2c** HVN first test (CL-142);
   - **T4** order-flow triggers (CL-143/144/151) at zones, using on-demand tick history.
   
   Prior expectation after T1/T2a, CFT, ORB and OF-16/19/20: low.
5. **DSR ledger:** T1 adds 6 trials, T2a adds 8.
