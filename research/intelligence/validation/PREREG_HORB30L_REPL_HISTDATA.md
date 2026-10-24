# PRE-REGISTRATION H-ORB30L-REPL Part A-H: out-of-sample replication on free HistData NSXUSD data

**Status: BINDING. Amends `PREREG_HORB30L_REPL_DUKA.md` (55fe9e68) §1 only: it replaces the data source.**
- Dukascopy history cannot be obtained within the user's constraints:
  - the user prefers not to install JForex;
  - the website export gives one day per file (tested 2026-10-16: one BID file = one UTC day), so about 4,000 downloads would be needed;
  - automating them would breach the Dukascopy Terms of Use.
- The user decided 2026-10-16: **"yes, go with HistData"**.
- Written **before** any HistData file has been downloaded. No statistic of the rule has ever been computed on any day before 2023-02-18. (The only Dukascopy file fetched is the 2026-10-16 test day, which is not used.)
- Everything else is **unchanged** from `PREREG_HORB30L_REPL_DUKA.md` and the parent `PREREG_HORB30L_REPL.md`: the frozen rule, calendar, stale filter, parity gate and thresholds, OOS statistics and seed, acceptance, verdict words, what follows.
- **This confirms ONE frozen rule. It is not a search.**

## 1. Data (replaces Part A-D §1)

**Source:** HistData.com free "Generic ASCII, M1 (1 Minute Bar)" data for **NSXUSD** (Nasdaq-100 CFD quotes). Each yearly zip contains `DAT_ASCII_NSXUSD_M1_<year>.csv`.

**Format:** per HistData's published specification:
- rows `YYYYMMDD HHMMSS;open;high;low;close;volume`;
- **BID quotes**;
- timestamps in **EST without daylight saving** (fixed UTC−5);
- the timestamp labels the bar's opening minute.

**Years downloaded:** 2010 → 2023, one yearly zip each (14 files), by Claude in the in-app browser with the user's approval. These are ordinary page downloads at human pace, not a scraper.
- **OOS period:** first available day → **2023-02-17** (NY date).
- **Parity period (in-sample):** 2023-02-21 → 2023-12-29.

**Storage:** `data/raw/histdata/NSXUSD/` (git-ignored, backed up to GCS). The zips are never edited.
- `MANIFEST.json` records each zip's sha256, the inner CSV's name and sha256, its row count, and its first and last timestamp.
- The manifest is written **before** the parity stage. Every later stage re-verifies the hashes.

**Price used by the rule:** the **bid** O/H/L/C. There is no ask, so:
- the executable variant is dropped;
- spreads cannot be reported;
- the S1 cost of 2.0 points per round trip stands for spread plus slippage, as in-sample.

**Clock:** the timestamp + 5 h = UTC → America/New_York (DST-aware), as in Part A-D.
- If HistData's clock or bar labelling were wrong (for example DST applied, or bars labelled at close), the entry minutes and statuses would disagree with NQ in summer months. **The parity gate (P1, P2a) is the pre-registered check of this. There is no other adjustment.**

## 2. Unchanged items, restated for clarity

- **Parity gate** (in-sample 2023-02-21 → 2023-12-29, frozen calendar, both sources covered):
  - P1 status agreement ≥ 0.80;
  - P2a entry-minute agreement ≥ 0.75;
  - P2b exit-kind agreement ≥ 0.75;
  - P3 net-R correlation ≥ 0.75.
  - Fail → **NOT EVALUABLE**, and no OOS day is read.
  - The parity stage discards every row before NY 2023-02-18 at load time.
- **OOS:** runs once.
  - S1 mean R; block bootstrap 20, B = 2,000, seed 20261015.
  - Acceptance:
    1. mean > 0 and CI lower bound > 0;
    2. primary − N2 > 0;
    3. ≥ 60 % of years positive and no year > 25 %;
    4. ≥ 300 trades.
  - Verdicts: REPLICATED / FAILED / INSUFFICIENT-N / NOT REPLICATED.
- **Reported, not decisive:** 2R, per-year, S0 / S2, the cost floor by year, the user-goal table, and the descriptive in-sample battery.
- **Calendar:** the frozen `IM1_US_CALENDAR.json` for dates ≥ 2017; the §2 rule calendar of Part A-D before that. **Stale filter:** ≥ 20 % of 09:30–15:29 minutes missing or flat.

## 3. Code and freeze

- **Script:** `horb30l_histdata_oos.py`. It imports the helpers of `horb30l_duka_oos.py` (95a89207: calendar, stale filter, day eligibility, bootstrap, acceptance) and the frozen engine `horb30l_nq.py` (7d4095bc). Only the loader and the bid-only reporting are new.
- **Stages:** `manifest` → `parity` → `oos`. Each refuses to overwrite its output. `oos` refuses unless parity passed and the hashes verify.
- **Tests:** `test_horb30l_histdata_oos.py`, synthetic data only.
- The script, tests and this file are hashed into `PREREG_HASHES.txt` **before** the first download.
