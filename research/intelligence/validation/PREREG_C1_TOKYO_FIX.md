# PRE-REGISTRATION C1: Tokyo-fix (gotobi) USDJPY flow strategy

**Status: BINDING.**
- Approved by the user 2026-10-11: "Approved, pre-register and run C1".
- Written before any C1 outcome is computed. Its SHA-256, the frozen holiday file and the code hashes go into `PREREG_HASHES.txt` before discovery is opened.
- It inherits `PREREG_OF_COMMON.md` for data rules, clocks, valid days, σ̂, costs (§C7), bootstrap and splits (§C8), **except where stated here**.

## 1. Hypothesis, source and disclosure

**Claim (source):**
- Ito & Yamada (2017, *J. Int. Econ.* 109:214–234; NBER w22820): around the Tokyo fix at **09:55 JST = 00:55 UTC** (no DST in Japan), USD/JPY tends to appreciate before the fix and fall back after it.
- A switch strategy (long 5 min before, short 5 min after) earned **+1.8 bp per day** on EBS deal prices over 1999–2013 (4,111 days), "slightly above" the interbank spread.
- It was **larger on the 5th/10th days and on month-end** (Fig. 6, bottom).
- Mechanism: predictable importer USD demand settled at the fix, plus bank pre-hedging and front-running.

**What is new here:**
- Post-publication data (2017-07 → 2026-09);
- the Pepperstone retail-CFD feed instead of EBS;
- retail costs.

This is a test of whether a published structural effect survives **net of retail costs** today.

**Disclosure (seen data):**
- No project analysis has computed USDJPY returns in the 00:45–01:30 UTC window by day of month.
- Related exposures:
  - T2 (daily RV) and T1 (hourly tick volume, incl. ASIA block 23–07 UTC) used this data;
  - V2 F5 (Asian mean reversion, frozen, unopened) covers the same clock window on USDJPY with a different signal.
- 8E (closed) traded USDJPY intraday, but not as a calendar/fix rule.

## 2. Data and calendars

- **Prices:** USDJPY Pepperstone M1 canonical (bid OHLC, `spread`), 2017-07-03 → 2026-09-25. UTC from the verified server→UTC conversion (COMMON §C3; 0 mismatches against `time_utc`).
- **Japanese business days:** weekdays that are not Japanese national holidays. The holiday list comes from the local MT5 calendar export `calendar/canonical_v2/PEPPERSTONE_MT5_CALENDAR_canonical_v2.csv.gz` (`country_code = JP`, `type = 2`, holidays, 2017+).
  - Year-end bank holidays (Dec 31 – Jan 3) are added explicitly, since banks do not fix on them.
  - The holiday list is frozen into a file and hashed before the run.
- **Day classes (fixed by the calendar; no fitting):**
  - **GOTOBI** = the Japanese business day whose calendar date ∈ {5, 10, 15, 20, 25, 30}, plus the **last Japanese business day of the month (ME)**. If a gotobi date is not a business day, the **previous business day** is used.
    - This roll rule is a NEXA assumption (Japanese settlement convention). Variant **G-noRoll** (dates exactly as listed; non-business dates dropped) is a counted secondary.
  - **OTHER** = all other Japanese business days.
  - Non-business days (no fix) are excluded.

## 3. Trading rules (exact)

Time t₀ = 00:55:00 UTC. All bars are M1 with open time in UTC.

| Claim | Role | Entry | Exit / switch | Days |
|---|---|---|---|---|
| **A** | **PRIMARY** | Buy at the open of the 00:50 bar | At the close of the 00:54 bar (≈ 00:55:00), sell 2 units (close long, open short); buy back at the close of the 00:59 bar (≈ 01:00:00) | GOTOBI |
| B | secondary | Buy at the open of the 00:50 bar | Sell at the close of the 00:54 bar (long leg only) | GOTOBI |
| C | secondary (replication) | As A | As A | ALL business days |
| D | secondary | As B but entry at the open of the 00:25 bar (30-min pre-hedge window, Ito & Yamada fn. 8) | Close of the 00:54 bar | GOTOBI |
| A-noRoll | secondary | As A | As A | GOTOBI under G-noRoll |

**Risk rule (all claims):**
- A **catastrophe stop** is always attached (NEXA's no-missing-stop invariant):
  - long stop = entry − 4·σ̂₁₀;
  - short stop = switch price + 4·σ̂₁₀.
- **σ̂₁₀** = the sample sd of the [00:50, 01:00) log return over the **previous 60 business days** (causal, all days).
- Stops are checked on M1 bid high/low (long: low ≤ stop; short: high + spread ≥ stop). A gap through the stop fills at the bar open.
- **Sizing:** 1 % account risk to the stop. Results are reported in bp of notional **and** in R (= net P&L / stop distance).
- **No overnight holding:** there is no swap, and server rollover (17:00 NY) is not crossed.

## 4. Costs (COMMON §C7, instrument-specific)

| Item | Value | Note |
|---|---|---|
| Commission | USD 7.00 per lot round trip = **0.70 bp per round trip** | Claims A and C = 2 round trips; B and D = 1. Re-verify against the first real S14 CLOSE row |
| Spread | s = max(**0.2 pip**, trailing-20-day median of the daily p90 M1 `spread`) | The `spread` field is the bar minimum (0 points on most FX bars, T1), so a 0.2-pip floor (≈ 0.13 bp at 150) is a NEXA assumption. Buys pay bid + s |
| Slippage stress | **S0** = commission + spread; **S1** = S0 + 0.25 bp per side; **S2** = S0 + 0.50 bp per side | **S1 decides.** S2 is reported. No real fills exist yet (S14 forward test down) |
| Swap | 0 | Intraday only |

## 5. Benchmarks and nulls

- **N0 (zero):** no trade. Net mean > 0 is the minimum.
- **N1 (time-of-day placebo; the paper's Fig. 6 design):** run the identical rule with the switch time moved to every 5-min boundary from 23:00 to 03:00 UTC, excluding 00:45–01:05 (44 placebo times), on the same days.
  - p_tod = (1 + #{placebo mean ≥ observed}) / 45.
- **N2 (day-class contrast):** the same rule at 00:55 on OTHER days. Contrast Δ = mean(GOTOBI) − mean(OTHER), gross and net.
- **N3 (drift):** the day-level USDJPY drift scaled to 10 min, reported (expected ≈ 0).

## 6. Splits, sample requirements, statistics

**Splits (COMMON §C8):**
- discovery 2017-07 → 2022-12;
- validation 2023 → 2024;
- holdout 2025-01 → 2026-09-25 (opened once);
- prospective from 2026-10 (accumulated, not evaluated without approval).
- No 2027 data.

**Expected GOTOBI events (calendar arithmetic, before data):** ≈ 6.5 per month, × ~0.95 business-day rate ⇒ ≈ 70/yr.
- discovery ≈ 380, validation ≈ 140, holdout ≈ 125, pooled ≈ 645.

**Minimum samples:**
- holdout ≥ 100 GOTOBI events;
- pooled ≥ 500.
- If not met, the result is **INSUFFICIENT-N** (no verdict).

**Power** is reported, not assumed: σ of the per-event return is estimated on **discovery only**, and the minimum detectable effect at 80 % power for each split is reported alongside the result.

**Uncertainty:**
- moving-block bootstrap over events (block = 20 events, B = 2,000, seed 20261011);
- one-sided p as in COMMON §C8.

**Multiplicity:**
- primary family = {A};
- secondaries {B, C, D, A-noRoll} under BH q = 0.10 within the secondary family;
- the **DSR** counts all 5 claims plus the 44 placebo times as trials (N = 49).

## 7. Acceptance criteria (all required for "research candidate", RESEARCH_GATE G4)

1. **Discovery:** A net (S1) mean > 0 with one-sided p < 0.05.
2. **Validation and holdout:** A net (S1) point estimates > 0.
3. **Pooled:** the 95 % CI lower bound of the A net (S1) mean > 0. The S2 result is reported.
4. **Placebo:** p_tod ≤ 0.05 pooled, and the 00:55 switch ranks in the top 20 % of placebo times **in the holdout**.
5. **Mechanism:** the pooled 95 % CI of Δ (GOTOBI − OTHER, gross) has lower bound > 0.
6. **Stability:**
   - no calendar year > 50 % of pooled net P&L;
   - ≥ 6 of the 10 calendar years (2017 partial … 2026 partial) with a positive net mean.
7. **DSR** ≥ 0.95 at N = 49 trials.
8. **R-feasibility:** the median catastrophe-stop distance is ≥ 5 × the round-trip cost (so cost ≤ 0.2R; COMMON §C7 cost floor). Events failing this floor *ex ante* are skipped and counted.

**Verdicts:**
- **REJECTED** if the pooled A net (S0) mean ≤ 0, or the discovery and holdout signs are opposite.
- **INCONCLUSIVE** otherwise.
- If REJECTED or INCONCLUSIVE, the KB records the result and the next candidate (C2) is proposed. **No re-run with altered windows under this ID.**

## 8. Robustness (reported only; never changes the verdict)

- Sub-periods by year.
- 5th/10th days vs month-end separately.
- Fridays.
- Weeks with a US holiday.
- Spread-floor 0.1 / 0.3 pip.
- Stop multiple 3σ / 6σ.
- Exit at the close of the 00:55 bar (≈ 00:56) instead of the 00:54 bar.

## 9. Reuse (no new code paths beyond a thin script)

- `of_common.py`: load, server→UTC clock, valid days, splits, commission, bootstrap, BH, verdict, year shares (unchanged).
- A new `c1_tokyo_fix.py`: day classification, event extraction, costs, placebo loop.
- New unit tests in `test_of_common.py`:
  - gotobi roll rule on known dates;
  - 00:55 UTC bar mapping in US DST and winter;
  - cost arithmetic for 1 and 2 round trips;
  - stop handling.
- Expected runtime: a few minutes (one symbol, ~2,300 days × 45 switch times).

## 10. Unresolved assumptions and missing data

| # | Item | Effect | Resolution path |
|---|---|---|---|
| U1 | **Pepperstone CFD quotes ≠ EBS deal prices**; the bid-only M1 feed | The effect may be smaller or partly absorbed by LP pricing | The test itself measures it |
| U2 | **Real fill quality at 00:50 / 00:55 UTC** (last look, slippage at the fix minute) | Could erase a ~1 bp edge | S1/S2 stress now; prospective spread/fill evidence only via the S14 TickLogger or demo (needs approval) |
| U3 | **Spread floor** of 0.2 pip (the `spread` field is the bar minimum) | The cost estimate could be optimistic | Sensitivity 0.1–0.3 pip; TickLogger quotes later |
| U4 | Gotobi roll convention for weekend/holiday dates | Misclassifies a few days per year | Primary roll-back plus a counted no-roll variant |
| U5 | MT5 calendar holidays are a snapshot at export time (2017+ only) | A missing holiday mislabels a day | Spot-check 3 known holidays per year in the frozen holiday file |
| U6 | Post-2014 regulation (fixing reforms, Japanese banks' practices) | Decay since the paper's sample | That is what the out-of-sample test answers |
| U7 | Commission USD 7/lot round trip | ±0.1 bp | Verify from the first real CLOSE row |
| U8 | **Production fit:** a calendar-timed 10-minute trade is not in the current EA logic | Deployment would need a new, separately approved EA module plus Risk Engine review | Only after G4 plus approval |

## 11. Implementation clarifications (fixed before any outcome)

1. **Holiday file `C1_JP_HOLIDAYS.json`** (frozen, hashed):
   - MT5 calendar JP `type = 2` dates (161), plus Dec 31 – Jan 3 every year.
   - Plus 5 one-off public holidays absent from the MT5 export, found by the U5 spot-check: 2019-04-30, 2019-05-01, 2019-05-02, 2019-10-22, 2026-09-22.
   - The spot-check also confirmed: 2018-12-24, 2020-02-24, the 2020/2021 Olympic moves, 2021-08-09, 2024-08-12, 2025-05-06, 2026-09-21.
2. **Event date:** the JST date D of the fix equals the UTC date of 00:55 UTC. Placebo switch times before 00:00 UTC belong to the previous UTC date but the same JST fix day D.
3. **Required bars:**
   - an event is valid only if M1 bars exist at exactly the entry-bar, switch-bar and exit-bar minutes;
   - for D, the entry bar is 00:25;
   - missing bars ⇒ the event is skipped and counted.
4. **σ̂ for each window:** σ̂₁₀ is computed per switch time (primary and each placebo) from that window's own 10-min log return (open of the T−5 bar → close of the T+4 bar) over the previous 60 valid business days (causal). Claim D uses σ̂₁₀ at 00:55, as specified.
5. **Leg accounting:**
   - A leg's net P&L = price P&L − spread (buy side) − commission (0.70 bp of notional) − stress per side.
   - If the long leg is stopped, the short leg still opens at the switch (legs are independent).
   - R = leg net / leg stop distance; the claim R = sum of its legs' R.
6. **Cost-floor skip (§7.8):** a leg is skipped if (commission + s) > 0.20 × its stop distance (4·σ̂₁₀·price). Skipped legs count as zero trades and are reported.
7. **Δ (GOTOBI − OTHER):** one series of all valid business days in date order, each carrying its class. A block bootstrap over days (block 20) computes the difference of class means.
8. **DSR:** `nexa_robust.deflated_sharpe` (imported read-only):
   - r = the claim's per-event net (S1) returns;
   - n_trials = 49;
   - var_sr_trials = the variance of the per-event Sharpe ratios of the 5 claims plus the 44 placebo switch times (A rule, GOTOBI days, S1), computed on the same opened data.
9. **Calendar years for §7.6:** 2017 (partial) through 2026 (partial) = 10 years. "Positive" means the year's net (S1) mean > 0.

