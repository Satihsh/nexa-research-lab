# PRE-REGISTRATION T1 · H-STATE: is the auction state predictable by 11:00 ET? (ES primary, NQ transfer; QuantConnect)

**Status: BINDING.**
- User approval 2026-10-18: "we can start T1 and T2a pre-registrations".
- Design sources:
  - `../NEXA_UNIFIED_AUCTION_STATE_2026-10-17.md` §3, §6;
  - `../video_batch_2026-10-18/VIDEO_BATCH_DECODE_2026-10-18.md` (CL-142…154);
  - Dalton S42 (value area, initial balance);
  - CL-005, CL-147, CL-149.
- **Written before any data was read for this hypothesis.** No T1 statistic has been computed on any data.
- Earlier NEXA tests on related questions used other instruments or other rules:
  - OF-16 (open location vs prior VA) on FX/XAU proxies;
  - the CFT noise-band trend on ES.
- **Not tuned.** There are no fitted parameters. Every threshold is either taken from a source or fixed here.
- **This is a prediction test, not a trading test.** No orders, no costs in the primary statistic.

## 0. Question

Every source in batches 1–9 starts with "what kind of day is it". T1 asks whether a fixed, source-based rule at 11:00 ET separates:
- **initiative days**, where the morning's move away from value continues, from
- **responsive days**, where the morning move reverts,

better than the unconditional behaviour of the morning move. If it does not, the "context first" pillars (2, 13, 15, 16, 19) have no measurable foundation.

## 1. Data, sessions, valid days
- **Instruments:**
  - **ES primary**, **NQ transfer**;
  - QuantConnect AlgoSeek continuous futures;
  - front month by open interest (`DataMappingMode.OPEN_INTEREST`), `DataNormalizationMode.BACKWARDS_RATIO`;
  - minute **trade** bars, regular hours only; clock America/New_York;
  - tick size 0.25 index points for both.
- **Period:**
  - **2010-01-04 → the last complete trading day available at run time**;
  - one run per instrument; each run once;
  - warm-up from 2009-12-01 (prior-day profile and 20-day IB history).
- **A day d is valid if:**
  1. all 390 RTH minute bars 09:30–15:59 exist for d and for the prior valid day d−1;
  2. no contract-mapping change occurred between d−1 and d (roll days are excluded and counted);
  3. at least 20 prior valid days exist for the IB percentile.
- **Bar convention:**
  - P(hh:mm) = close of the 1-minute bar *starting* at hh:mm−1, i.e. the last price at hh:mm;
  - O = open of the 09:30 bar;
  - C = close of the 15:59 bar.

## 2. Prior-day value area (fixed algorithm)
- **Volume at price:** for each of d−1's 390 bars, the bar volume is spread **uniformly** over every tick from its low to its high inclusive.
- **POC** = the tick with the most volume. Ties go to the tick closest to the midpoint of d−1's range, then to the lower one.
- **Value area** (Dalton, *Mind over Markets*, App. 1):
  - start at the POC;
  - compare the summed volume of the next two ticks above with the next two below;
  - add the larger pair (above wins ties);
  - repeat until the included volume is ≥ 70 % of the total.
  - **VAH / VAL** = the highest / lowest included tick.

## 3. Features at 11:00 ET (nothing after 11:00 is used)
- **P11** = P(11:00).
- **Loc11** ∈ {above, inside, below}: P11 > VAH / VAL ≤ P11 ≤ VAH / P11 < VAL.
- **LocO**: the same classification for O.
- **Morning direction:** Dm = sign(P11 − O). Days with Dm = 0 are excluded only from statistics that use Dm.
- **IB** = high / low of the 09:30–10:29 bars:
  - IBW = (IB high − IB low) / O;
  - IBpct = rank percentile of IBW among the previous 20 valid days (secondary only).

## 4. State rule (fixed; sources: Rogers CL-149, Valastro CL-147, Dalton value-area rule)
- **I⁺** if Loc11 = above (D = +1); **I⁻** if Loc11 = below (D = −1).
  - *Initiative:* by 11:00 the market is accepted outside yesterday's value.
- **R** if Loc11 = inside.
  - *Responsive:* the market is still inside, or back inside, yesterday's value.
- **Sub-labels (secondary only):**
  - I-migration = LocO on the same side as Loc11;
  - I-breakout = otherwise;
  - R-failed = LocO outside and Loc11 inside (the failed auction / 80 % rule case);
  - R-inside = LocO inside.

## 5. Outcome
- **Rest-of-day return:** Rr = ln(C / P11), in basis points.
- **Continuation scores:**
  - initiative days: **Y_I = D · Rr** (positive = continues away from value);
  - responsive days: **Y_R = Dm · Rr** (negative = the morning move reverts);
  - baseline, all valid days with Dm ≠ 0: **Y_B = Dm · Rr**.

## 6. Hypotheses, tests, verdict (ES primary; NQ identical, declared transfer)

| ID | Hypothesis | Statistic |
|---|---|---|
| **H1** | Initiative days continue | mean Y_I > 0 |
| **H2** | Responsive days revert | mean Y_R < 0 |
| **H3 (primary)** | The state separates continuation from reversion | Δ = mean Y_I − mean Y_R > 0 |

- **Inference:**
  - moving-block bootstrap over the **full chronological sequence of valid days**: block 20, B = 2,000, **seed 20261018**;
  - each replicate recomputes the group means on the resampled days;
  - 95 % percentile CI; one-sided p = share of replicates on the wrong side of 0.
- **Stability:** split the valid days into 4 equal consecutive blocks and report the sign of H1, H2 and Δ in each.
- **Verdicts:**
  - **STATE PREDICTABLE:**
    - H3 p ≤ 0.05;
    - H1 CI lower bound > 0;
    - H2 CI upper bound < 0;
    - Δ > 0 in ≥ 3 of 4 blocks.
  - **PARTIAL:** H3 p ≤ 0.05, but only one of H1 / H2 has a CI that excludes 0.
  - **NOT PREDICTABLE:** otherwise.
  - **INSUFFICIENT-N:** fewer than 300 valid days in either I (I⁺ ∪ I⁻) or R.
- **Also reported (no verdict effect):**
  - day counts by state and sub-label;
  - mean Y_B (the plain morning-direction effect);
  - hit rates P(Y > 0);
  - mean |Rr|;
  - sub-label means;
  - H1 / H2 by IBpct tercile;
  - the gross size of mean Y_I and mean |Y_R| relative to one ES S1 round-trip cost (0.60 points expressed in bp of O). This judges economic relevance, not the verdict.

## 7. Multiple testing
- T1 counts as **6 trials** (3 hypotheses × 2 instruments) in the NEXA DSR ledger. DSR is descriptive here, because T1 is not a trading rule.

## 8. Code and freeze
- QuantConnect algorithm: `qc_asm/main.py` (shared with T2a).
  - MODE ∈ {ES, NQ}. Each run computes T1 and T2a on the same valid days.
  - **Only the MODE line differs between runs.**
- Local synthetic tests: `test_asm.py`. They cover:
  - the value-area algorithm on hand-built profiles;
  - the uniform spread;
  - state labels;
  - outcome signs;
  - the bootstrap.
- Before any run:
  - this file, `PREREG_T2A_VAR.md`, the code and the tests are hashed into `PREREG_HASHES.txt`;
  - the code is hash-verified in the QuantConnect editor before every run (as in CFT).
- **Output:** one `NEXA_T1_RESULT` JSON log line per run. A daily series of (state, Y) in integer bp may be logged for local replication.
- **Results are never overwritten. A negative result is preserved.**
