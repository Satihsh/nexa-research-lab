# PRE-REGISTRATION H-ORB30L-REPL Part A-D: out-of-sample replication on free Dukascopy data

**Status: BINDING. Amends `PREREG_HORB30L_REPL.md` (758f8a31) §2 only: it replaces the data source of Part A.**
- Part A (QuantConnect) could not run: its backtest is gated behind credit-card verification (`DEVIATIONS_HORB30L_REPL.md` D-10).
- The user decided 2026-10-15: **"use free Dukascopy data instead"**. No spending.
- Written **before** any Dukascopy history has been exported or read. No statistic of the rule has ever been computed on any day before 2023-02-18.
- §1 of the parent pre-registration (the frozen rule), its acceptance criteria and verdict words are unchanged. Part B (forward log) is unchanged.
- **This confirms ONE frozen rule. It is not a search.** Nothing is tuned, and no variant may replace the rule after the results are seen.

## 1. Data

**Instrument:** Dukascopy `USATECH.IDX/USD` (US Tech 100 index CFD), M1 candles, **both BID and ASK**, timestamps in **UTC/GMT**.

**Source:** the user exports it from their own Dukascopy account (JForex → Tools → Historical Data Manager, or Dukascopy's own historical-data export page). This is the sanctioned route (`research/platform/DUKASCOPY_DATA_PLAN_v1.md` §1). **No scripted download of the Dukascopy datafeed** (ToU).

**Range exported:** from the first day Dukascopy has to **2023-12-31**.
- **OOS period:** first available day → **2023-02-17** (NY date). Not one in-sample day is used.
- **Parity period (in-sample, §3):** 2023-02-21 → 2023-12-29.

**Storage:** `data/raw/dukascopy/USATECH.IDX-USD/` (git-ignored, backed up to GCS). Raw files are never edited.
- `MANIFEST.json` records each file's sha256, row count, first and last timestamp, and side.
- The manifest is written and committed **before** the parity or OOS stage runs. Every later stage re-verifies the hashes.

**Price used by the rule:** per-minute **mid** = (bid + ask) / 2 for O, H, L and C, on minutes present on both sides. This is identical to Part B.

## 2. Clock, days and data quality

**Clock:** UTC → America/New_York (DST-aware). Minutes are labelled by bar start, as in-sample.

**Calendar** (days excluded as holidays, early closes or in-sample calendar quirks):
- **Dates ≥ 2017-01-01:** the frozen in-sample calendar `IM1_US_CALENDAR.json`, unchanged, so the day selection matches in-sample.
- **Dates < 2017-01-01** (outside that file): a rule calendar with the same composition:
  - NYSE full holidays: New Year (observed; a Saturday New Year is not moved to the Friday), MLK Day, Presidents Day, Good Friday, Memorial Day, Independence Day (observed), Labor Day, Thanksgiving, Christmas (observed);
  - special closures 2012-10-29 and 2012-10-30;
  - early-close days: Jul 3 if a weekday, the Friday after Thanksgiving, Dec 24 if a weekday;
  - Dec 31 if a weekday;
  - Columbus Day (2nd Monday of October) and Veterans Day (Nov 11; Saturday → Friday, Sunday → Monday). These two are excluded because the in-sample calendar excludes them.
  - The rule calendar is printed in the results for audit.

**A day is used if:**
- it is a weekday not in the calendar;
- all 30 range minutes (09:30–09:59) and the 15:29 minute exist on mid;
- **and it is not stale.** A day is stale if ≥ 20 % of the 360 minutes 09:30–15:29 are missing **or** are flat repeats (O = H = L = C = previous close). Stale days are counted per year and reported, never used.

**Trading-day end:** the last complete NY day before the end of the export is the last usable day.

## 3. Pre-flight: parity gate (in-sample only, runs BEFORE any OOS day is read)

**Why:** a CFD on the cash index is not the NQ future. If the rule does not behave the same on both sources, an OOS result on Dukascopy would say nothing about the in-sample NQ result.

**Window:** 2023-02-21 → 2023-12-29 (all in-sample).
- **The parity stage discards every Dukascopy row before 2023-02-18 when loading, before any computation.**
- Day selection = the frozen calendar plus §2 coverage on both sources.

**Compared per day** (frozen engine, S1 cost; NQ = the in-sample Databento file `iv.DATA`):
1. Status (trade / no_breakout / cost_floor / …).
2. On days both trade: the entry minute and the exit kind.
3. On days both trade: the net R.

**Pass criteria (all required; fixed now):**

| # | Criterion | Threshold |
|---|---|---|
| P1 | Same status | ≥ 80 % of common days |
| P2a | Same entry minute (days both trade) | ≥ 75 % |
| P2b | Same exit kind (days both trade) | ≥ 75 % |
| P3 | Pearson correlation of net R (days both trade) | ≥ 0.75 |

Also reported, not decisive:
- mean S1 R on each source over the window;
- the median mid–NQ level offset;
- the median Dukascopy spread at 10:00 and at 15:29.

**If parity FAILS:** Part A-D is **NOT EVALUABLE**. The OOS stage refuses to run and no OOS day is ever read. Only Part B continues.
**If parity PASSES:** the OOS stage runs **once**.

## 4. OOS analysis (runs once; the results file is never overwritten)

- **Primary:** mean net R per trade at **S1 = 2.0 index points** on mid, OOS days only.
- **Bootstrap:** moving block over days, block 20, B = 2,000, **seed 20261015** (as Part A). One-sided p.
- **Acceptance:** the parent §2 rules unchanged:
  1. mean S1 R > 0 and 95 % CI lower bound > 0;
  2. primary − N2 > 0;
  3. ≥ 60 % of calendar years positive and no single year > 25 % of total net R;
  4. ≥ 300 trades.
- **Verdict:**
  - **REPLICATED** if all pass;
  - **FAILED** if the S1 mean ≤ 0;
  - **INSUFFICIENT-N** if there are fewer than 300 trades;
  - otherwise **NOT REPLICATED**.

**Reported, not decisive:**
- the 2R target; the per-year table; S0 and S2;
- the cost-floor count by year;
- the user-goal $ table at $2/point (MNQ);
- **the executable variant** (entry at the ask open, exits judged on the bid, no extra cost), as in Part B;
- the in-sample battery from `horb30l_nq.analyse` (time-of-day placebos, DSR with 116 trials, robustness), run as descriptive output only.

**Note fixed in advance:**
- Costs are in index points. Early years with lower prices make 2 points a larger share of each move, which makes the test conservative. It is not adjusted.
- The CFD's index level differs from NQ by the futures basis. R is measured in points within a day, so a constant offset does not change it.

## 5. Code and freeze

- **Script:** `horb30l_duka_oos.py`. It **imports** the frozen engine `horb30l_nq` (7d4095bc) and `forward_horb30l` helpers. No copy of the rule is made.
- **Stages:** `manifest` → `parity` → `oos`.
  - Each refuses to overwrite its output.
  - `oos` refuses unless the parity file exists and passed, and unless the manifest hashes verify.
- **Tests:** `test_horb30l_duka_oos.py`, synthetic data only.
- The script, tests and this file are hashed into `PREREG_HASHES.txt` **before** the user exports any data.

## 6. What follows

Same as the parent §4:
- **REPLICATED, and Part B CONSISTENT:** H-ORB30L becomes a research candidate for an ATAS alert plus demo execution, then at most one prop evaluation (user rule: $0 until proven).
- **FAILED or NOT REPLICATED:** the rule is closed. The forward log stops after notice to the user.
- **NOT EVALUABLE** (parity fails): it rests on Part B alone. The user decides whether to keep it.
