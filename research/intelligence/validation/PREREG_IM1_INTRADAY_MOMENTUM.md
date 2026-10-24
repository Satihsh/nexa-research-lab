# PRE-REGISTRATION IM1: market intraday momentum (last half-hour) on Pepperstone FX and gold

**Status: BINDING.**
- Approved by the user 2026-10-11: "Approved, pre-register intraday momentum".
- Written before any IM1 outcome is computed. Its SHA-256 goes into `PREREG_HASHES.txt` now.
- Code and the frozen holiday file are hashed **before discovery opens**. Implementation and the run need a separate user approval.
- It inherits `PREREG_OF_COMMON.md` (data rules, clock NY+7, valid days §C4, costs §C7, statistics §C8) and the cost and placebo design of `PREREG_C1_TOKYO_FIX.md`, **except where stated here**.

## 1. Hypothesis, source and honest prior

**Claim (sources):**
- **Baltussen, Da, Lammers & Martens (2021, JFE 142:377–403)**, "Hedging demand and market intraday momentum":
  - over 60+ futures (17 equity index, 16 bond, 21 commodity, 8 currency), 1974–2020;
  - the **last-30-minute return before the market close (r_LH)** is positively predicted by the **rest-of-day return r_ROD**, from the previous close to 30 minutes before today's close;
  - mechanism: gamma hedging (option market makers, leveraged ETFs) concentrated before the close.
- **Gao, Han, Li & Zhou (2018, JFE)** first showed it for SPY, using the first half-hour return as the predictor.

**Reported effect sizes for the instruments NEXA can trade** (Baltussen, App. A / Tables B3–B4; **gross; "we do not consider transaction costs"**):

| Market | Hours used | β_ROD | R² | R²_OOS | Timing strategy η(r_ROD) |
|---|---|---|---|---|---|
| **Currency futures** (EC, BP, JY, … US-listed) | Open / close per App. A 7:20–14:00 (labelled EST); body text: volume spikes at 8:21 and **15:00**, "the end of the daily settlement period" | 0.72 (t 4.57) pooled | 0.19 % | 0.26 % | **0.85 %/yr, SR 0.87** |
| **Gold** (COMEX GC) | **08:20–13:30 ET** | 1.09 (t 2.95) | 0.25 % | 0.08 % | Commodities: 4.34 %/yr, SR 1.42 |

**Honest prior (stated before data):**
- **FX:** 0.85 %/yr over about 250 trades ≈ **0.3 bp gross per trade**. NEXA's FX round trip is ≈ 0.7 bp commission + spread, ≈ 0.9 bp in total. **A net-negative FX result is the expected outcome.**
- **Gold:** about 1.7 bp gross per trade (commodity average) against ≈ 0.3 bp commission + spread; **marginal**.
- **Why test anyway:** this is the only peer-reviewed, cross-asset intraday effect in the NEXA programme, it was never tested on NEXA's feed, and it runs MT5-natively with one trade per day. A clean negative is also an answer.
- **Not covered:** US equity-index CFDs (the strongest asset class in the paper). They are not in the on-disk data; an extension would need an MT5 history export, a separate approval.

**Disclosure (seen data):**
- The Pepperstone M1 files were used in T1/T2, OF-16/19/20/20b, C1 and C2.
- **None computed the close-anchored r_ROD → r_LH relation** at 15:00 ET (FX) or 13:30 ET (XAU).
- OF tests computed NY-session outcomes that span these windows, but not this rule.

## 2. Data, clock and days

**Instruments:** EURUSD, GBPUSD, USDJPY, XAUUSD.
- Pepperstone M1 canonical (bid OHLC + `spread`), 2017-07-03 (XAU 2018-01-02) → 2026-09-25 (COMMON §C2).
- XAGUSD is excluded: not in the COMMON loader / cost constants, and not established for this test.

**Clock:** America/New_York local time via the verified server→UTC conversion (COMMON §C3).

**Close C** (from the source; no fitting):

| Instrument | C | Basis |
|---|---|---|
| EURUSD, GBPUSD, USDJPY | **15:00 ET** | Baltussen: currency-futures close = end of the daily settlement period. CME FX settles at 14:00 CT = 15:00 ET. The App. A "7:20–14:00 (EST)" label reads as Central time. **The 14:00 ET alternative is reported as robustness only** |
| XAUUSD | **13:30 ET** | Baltussen App. A (GC 08:20–13:30 ET; COMEX settlement) |

**Days:** NY business days that are valid COMMON §C4 server days. Excluded and counted:
- US exchange holidays;
- **CME early-close days** (day after Thanksgiving, Dec 24, Dec 31, and July 3 when a weekday), following Baltussen's removal of early-close days;
- a day without a valid previous close day;
- a day with any required M1 bar missing.

The holiday / early-close list is built from the MT5 calendar (US, type 2) plus these rules. It is **frozen into `IM1_US_CALENDAR.json` and hashed before discovery**.

## 3. Rule (exact; Baltussen's timing strategy η(r_ROD))

Let P(T) be the bid **close of the M1 bar whose open time is T − 1 min** (the price at T).

- **Predictor:** r_ROD,t = P(C − 30 min, day t) / P(C, previous valid day) − 1.
- **Position:**
  - **long if r_ROD > 0, short if r_ROD < 0, no trade if = 0**;
  - **entry** at the **open of the M1 bar starting at C − 30** (bid; longs pay the spread);
  - **exit** at the **close of the M1 bar starting at C − 1** (≈ C);
  - one trade per instrument per day.
- **Catastrophe stop** (NEXA no-missing-stop invariant, as C1):
  - ± 4·σ̂₃₀ from the entry, where σ̂₃₀ = the sample sd of the [C − 30, C) log return over the **previous 60 valid days** (causal).
  - Checked on M1 bid high/low (shorts: high + spread). A gap through the stop fills at the bar open.
- **Results:** reported in **bp of notional** and in **R** (= net P&L / stop distance).
- **No overnight holding:** all exits are before the 17:00 NY rollover, so there is no swap.

## 4. Costs (COMMON §C7, as C1)

| Item | Value |
|---|---|
| Commission | USD 7.00 per lot round trip: EUR/GBP 0.00007; JPY 0.00007 × P; XAU 0.07 per oz |
| Spread | s = trailing-20-valid-day median of the daily p90 M1 `spread` × point. **FX floor 0.2 pip** (as C1: the `spread` field is the bar minimum, 0 on most FX bars). XAU without a floor (its field is non-zero), covered by the stress levels |
| Stress | **S0** = commission + spread; **S1** = S0 + 0.25 bp per side; **S2** = S0 + 0.50 bp per side. **S1 decides**; S2 is reported |
| Cost floor | Skip if (commission + s) > 0.20 × the stop distance (counted) |

## 5. Benchmarks and nulls

- **N0:** zero.
- **N1 (time-of-day placebo):** the identical rule with C replaced by **placebo closes C′ every 15 minutes from 06:00 to 16:45 ET**, excluding C ± 75 min. That gives 37 placebo times per instrument (FX excludes 13:45–16:15; XAU excludes 12:15–14:45), with r_ROD′ anchored at the previous day's C′.
  - p_tod = (1 + #{placebo mean ≥ observed}) / 38, per instrument and pooled (pooled placebo mean = average across instruments at the same C′ offset rank).
- **N2 (gross replication, mechanism):** the predictive regression r_LH = α + β·r_ROD, pooled and per instrument (r in bp, gross), with a day-block bootstrap CI for β.
  - It is reported against Baltussen's β (FX 0.72, gold 1.09).

## 6. Splits, samples, statistics

**Splits (COMMON §C8):**
- discovery 2017-07 → 2022-12;
- validation 2023 → 2024;
- holdout 2025-01 → 2026-09-25 (opened once);
- no 2027 data.

**Expected events:** ≈ 245 trading days/yr × 4 instruments ⇒ discovery ≈ 5,200, validation ≈ 1,900, holdout ≈ 1,700.
- **Minimum:** holdout ≥ 800 trades pooled, else INSUFFICIENT-N.

**Power** (reported, not assumed): σ of the per-trade net return is estimated on discovery only; the MDE at 80 % power per split is reported.

**Uncertainty:** moving-block bootstrap over days (block 20, B = 2,000, seed 20261011); one-sided p as COMMON §C8.

**Multiplicity:**
- primary **P** = all four instruments pooled (equal weight per trade), S1 net mean in bp;
- secondaries = the four instruments (BH q = 0.10);
- **DSR** (`nexa_robust.deflated_sharpe`, research venv) with n_trials = 1 + 4 + 37 = **42**, var_sr over those trials.

## 7. Acceptance criteria (all required for "research candidate", RESEARCH_GATE G4)

1. **Discovery:** P net (S1) mean > 0 with one-sided p < 0.05.
2. **Validation and holdout:** P net (S1) point estimates > 0.
3. **Pooled:** the 95 % CI lower bound of the P net (S1) mean > 0. S2 is reported.
4. **Placebo:** pooled p_tod ≤ 0.05.
5. **Mechanism:** the pooled gross β (N2) has a 95 % CI lower bound > 0.
6. **Stability:** no calendar year > 50 % of pooled net P&L; ≥ 6 of 10 years (2017 partial … 2026 partial) with a positive net mean; ≥ 3 of 4 instruments positive.
7. **DSR** ≥ 0.95 at n_trials = 42.
8. **Cost feasibility:** the median stop distance ≥ 5 × the round-trip cost (cost floor §4).

**Verdicts:**
- **REJECTED** if the pooled P net (S0) mean ≤ 0, or the discovery and holdout signs are opposite.
- **INSUFFICIENT-N** per §6.
- **INCONCLUSIVE** otherwise.
- The **gross** replication result (criterion 5) is reported separately, as C1 did ("gross confirmed, not tradable" is a possible reading).
- **No re-run with altered windows under this ID.**

## 8. Robustness (reported only; never changes the verdict)

- FX close at 14:00 ET.
- Gao-style predictor r_ONFH (previous close → 30 min after the market open: 08:20+30 ET for FX, 08:20+30 ET for XAU).
- Entry at the close of the C − 31 bar.
- FX spread floor 0.1 / 0.3 pip.
- Stop multiple 3σ / 6σ.
- Days with |r_ROD| above the 80th percentile (the paper's "large move" days).
- Per year.

## 9. Code (thin; reused)

- `of_common.py`: load, clock, valid days, splits, commission, bootstrap, BH, verdict.
- New `im1_intraday_momentum.py`: calendar, events, costs, stop, placebos, the regression.
- New unit tests: the C mapping in EST and EDT, the r_ROD anchoring across weekends, the sign rule, cost arithmetic, stop fills, placebo exclusion windows.
- Code, tests and `IM1_US_CALENDAR.json` are hashed before discovery opens.
