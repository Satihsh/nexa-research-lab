# PRE-REGISTRATION H-ML1: machine-learning intraday direction model on NQ (ES secondary), Topstep-compatible

**Status: BINDING.**
- User decisions 2026-10-18:
  - futures only, Topstep, 1–2 trades a day, ATAS/C# later;
  - "I approve installing scikit-learn and LightGBM";
  - "Proceed machine-learning search on ES/NQ".
- **Written before any data was read for this hypothesis.**
- **Pass bar** fixed by H-PROP-EV-TS (`PROP_EV_TS_REPORT.md`):
  - out-of-sample net edge with CI lower bound > 0;
  - target **≈ +0.10R net per trade**.

**Why this test is different from the 20+ rejected ones:**
- Earlier tests each took **one human rule** from a video or paper.
- Here a model learns from **many standard features at once**, with strict walk-forward training and a locked final hold-out.
- If intraday direction on NQ is predictable at all from public price and volume information, this is the honest way to find out.

**Prior: low.** Every simple intraday rule failed (T1, T2a, OFC1, CFT, H-ORB30L, H-IM, H-FPT-REV); the literature finds index-futures intraday returns close to unpredictable after costs. A REJECTED result is the most likely outcome and will be preserved.

**Nothing in this file is tuned on data.** Every number below is fixed now.

## 1. Data and sessions
- **Source:** QuantConnect AlgoSeek minute futures.
  - **NQ** (primary target) and **ES** (secondary target and cross-asset features);
  - continuous front contract by open interest, `BACKWARDS_RATIO`;
  - regular session only: 09:30–15:59 ET (390 one-minute bars).
- **Days kept:** weekdays with all 390 bars for both NQ and ES, and no roll that day for either (as all earlier NEXA QC tests). The previous kept day supplies "prior day" values.
- **Period:** data from 2010-01-04; the last day = the last complete day available at run time.

## 2. Decision points, trade and label
- **Decision times:** every 15 minutes from **10:00 to 15:00 ET** (21 per day). Decision at the **close of the minute bar ending at that time** (bar index k = minutes since 09:30 − 1).
- **Risk unit R (ex ante):**
  - σ60 = standard deviation of 60-minute log returns over the **previous 20 kept days**, sampled at the 21 decision times (420 values);
  - **stop = target = σ60 × entry price** (points); 1R = that distance.
  - A day needs 20 prior kept days; earlier days are skipped.
- **Trade:**
  - enter at the decision bar's close;
  - symmetric bracket ±1R; maximum hold **60 bars**; exit at the close of bar min(k+60, 389) if no barrier is hit;
  - if one bar touches both barriers, **the stop is assumed first** (conservative).
  - All exits are by 16:00 ET = 15:00 CT, before Topstep's 3:10 PM CT flat rule.
- **Costs (round trip, points; as all earlier NEXA tests):**
  - NQ S0 1 / **S1 2** / S2 3;
  - ES S0 0.30 / **S1 0.60** / S2 1.20.
  - In R: cost / stop points.
- **Label (training):** y = 1 if the **long** bracket's gross outcome > 0, y = 0 if < 0. Rows with exactly 0 are dropped.

## 3. Features (19, computed only from data at or before the decision bar)
Units: σ60 = the R unit above (in return terms); σd = standard deviation of daily close-to-close log returns over the previous 20 kept days.
1. `tod`: minutes since 09:30
2. `dow`: weekday 0–4
3. `r5`, `r15`, `r30`, `r60`: log return over the last 5/15/30/60 minutes ÷ σ60 (the 60-minute value at 10:00 uses the 09:30 open as start)
4. `r_open`: log return since the 09:30 open ÷ σ60
5. `gap`: log(09:30 open ÷ prior close) ÷ σd
6. `prev_ret`: prior day's log return (close to close) ÷ σd
7. `pos_prev`: (price − prior low) ÷ (prior high − prior low)
8. `pos_today`: (price − today's low so far) ÷ (today's range so far); 0.5 if the range is 0
9. `vwap_dist`: log(price ÷ session VWAP so far) ÷ σ60 (typical price × volume)
10. `or_hi`, `or_lo`: log(price ÷ opening-range high), log(price ÷ opening-range low) ÷ σ60 (opening range = 09:30–09:59)
11. `vol_ratio`: today's cumulative volume to the decision bar ÷ the mean cumulative volume to the same bar over the previous 20 kept days
12. `rv_ratio`: std of today's 1-minute log returns so far ÷ the mean daily std of 1-minute returns over the previous 20 days
13. `range_ratio`: today's range so far ÷ the mean daily range of the previous 20 days
14. `sd_regime`: σd ÷ the mean σd over the previous 250 kept days (computed with ≥ 60 days; NaN before that, which HGB handles)
15. `x_ropen`: the **other** instrument's r_open (in its own σ60)
16. `x_r30`: the other instrument's 30-minute return (in its own σ60)

- Features 1–14 are computed for the target instrument; 15–16 come from the other one.
- **For NQ** the "other" is ES. **For ES** it is NQ.

## 4. Model and walk-forward (fixed)
- **Model:** scikit-learn `HistGradientBoostingClassifier`, fixed:
  - `max_iter=200, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=200, l2_regularization=1.0, early_stopping=False, random_state=20261018`.
  - LightGBM is not available on QuantConnect; HGB is the same algorithm family. No hyperparameter search of any kind.
- **Walk-forward, expanding window, one model per test year:**
  - test years **Y = 2013 … 2022** (validation);
  - for each, **training = all kept days before 1 January Y**.
- **Final hold-out:**
  - **training = all days before 2023-01-01**;
  - **test = 2023-01-01 → last day**;
  - computed in the same single run and never refitted.
- **Trade threshold δ (per model, no peeking):**
  1. fit a calibration model on training years except the last 2;
  2. predict those last 2 years;
  3. δ = the 90th percentile of |p − 0.5| there (≈ 2 qualifying decisions per day);
  4. then refit on the full training window.
  - For Y = 2013 the calibration fit uses 2010 and calibrates on 2011–2012.
- **Trading rule in each test year:**
  - go through the day's decision times in order;
  - take a trade when |p − 0.5| ≥ δ, no trade is open (the previous trade's exit bar ≤ k), and fewer than **2 trades** have been taken that day;
  - **direction = sign(p − 0.5)**.

## 5. Statistics and verdict
- **Unit:** trade. Net R at S1. Moving-block bootstrap over trades in time order (block 20, B = 2,000, seed 20261018); 95 % percentile CI; one-sided p.
- **Primary target: NQ.**
  - **V (validation):** pooled test-year trades 2013–2022.
  - **H (hold-out):** 2023 → end; 4 equal consecutive blocks.
- **Placebo (hold-out only):**
  - 20 models trained on the same 2010–2022 data with labels **randomly permuted within each training day** (seeds 1–20), same δ procedure;
  - report the 20 hold-out mean net R values;
  - **P-rank** = share of placebos with mean ≥ the real model's.
- **Verdict (NQ, binding):**
  - **REJECTED:** H mean ≤ 0.
  - **VALIDATED (G4):** all of
    - H mean > 0 and H CI lower > 0;
    - V mean > 0 and V CI lower > 0;
    - ≥ 3 of 4 H blocks > 0;
    - P-rank ≤ 0.05 (at most 1 of 20 placebos as good).
  - **PROP-READY:** VALIDATED **and** H mean ≥ **+0.10R** (Topstep target).
  - **INCONCLUSIVE:** otherwise.
- **ES:** the same pipeline and verdict computed and **reported as secondary**, never substituted for NQ.
- **Also reported:**
  - trades per day; win rate; S0/S2 means; per-year means (V and H);
  - share of green days and green months;
  - longest losing streak;
  - **B1 = the same trade times but always long** (separates direction skill from drift);
  - mean R by time of day;
  - δ per fold.

## 6. Use of the result
- **REJECTED / INCONCLUSIVE:** no strategy. The intraday ML search on ES/NQ with public price/volume features is closed at this feature set. No feature or parameter re-tuning on this data (NEXA law L2).
- **VALIDATED but < +0.10R:** an edge exists but is below the Topstep target. Report to the user; forward paper test only.
- **PROP-READY:**
  1. pre-register a forward paper test on a Topstep Practice account (≥ 60 trading days);
  2. write the frozen model as a C# strategy (ATAS `ChartStrategy` or the TopstepX API, whichever connects);
  3. no Combine purchase until the forward test also passes.

## 7. Multiple testing
- H-ML1 counts as **2 trials** (NQ primary, ES secondary). Ledger ≈ 163.
- The model's internal fitting is not a trial count; it is fixed in advance, with no search.

## 8. Code, freeze, use
- `qc_ml1/main.py`: pure-numpy feature/label/trade engine + sklearn HGB; reads data only, no orders; logs `NEXA_ML1_PART i/n` chunks (QC truncates log lines at ~8,192 chars).
- `test_ml1.py` (synthetic data, local `.venv-ml`):
  1. label and bracket exit (stop-first, time exit, 15:59 cap);
  2. σ60 uses only prior days;
  3. no feature uses data after the decision bar (perturbation test);
  4. the 2-trades-a-day, no-overlap rule;
  5. δ calibration uses only training years;
  6. walk-forward folds never train on test-year days;
  7. placebo permutation stays within a day;
  8. bootstrap / verdict logic;
  9. log chunking is lossless.
- Tests must pass before the hash; the QC editor hash is verified before the run; **one run**.
