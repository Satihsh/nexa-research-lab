# PRE-REGISTRATION H-FLOW-PRED: "Market Predicted" order-flow probability engine on NQ (ES secondary)

**Status: BINDING.**
- User decision 2026-10-21 (chat): "continue NEXA and approve H-FLOW-PRED, build it and push to github".
- Design source: `../FLOW_PRED_SPEC_2026-10-21.md` (the user's 20-component request and their three scientific rules).
- **Written before any data was read for this hypothesis.** Nothing below is tuned on data.

**What is tested (the user's rule 1).** At a decision time T: P(price reaches +target before −stop within the next H), and whether trading on that probability earns money **net of costs**, separately for each H (rule 3). Correlated indicators are grouped into 4 families and each family is tested as one block (rule 2).

**Prior: low.** Every pre-registered intraday ES/NQ test has failed (ledger ≈ 169 trials; H-ML1 with 20 price/volume features: −0.007R net). What is new here: tick-level aggressor flow, top-of-book quotes and auction-profile features, and short horizons. A REJECTED result is the most likely outcome and will be kept.

## 1. Data
- **Source:** QuantConnect AlgoSeek **tick** data (trade and quote ticks), free node, the user's own login (QC MCP and API are paid; runs go through the website as in DEVIATIONS_SWEEP_ORB5_LVN D-3).
- **Instruments:** **NQ primary** (binding). ES secondary (reported, never substituted). Continuous front contract by open interest, `BACKWARDS_RATIO`. One run per instrument; the ES file differs from the NQ file only in the `MODE` line.
- **Session:** regular hours 09:30:00–15:59:59 ET (algorithm time zone New York; tick times taken from the algorithm clock).
- **Window:** 2024-01-02 → the last day available at run time (subject to §1a).
- **Days kept:** weekdays with at least one trade in every one of the 390 minutes, and no contract roll that day. The first 20 kept days are warm-up only (they supply history, no rows).
- **Per-second store (per day):** trade high, low, last price, volume; buy and sell volume; big-trade buy and sell volume; trade-tick count; quote-update count; last bid size and ask size. Minute bars are built from it.
- **Aggressor side (quote rule):** a trade at or above the last ask is a buy, at or below the last bid a sell; otherwise compare with the mid; at the mid, the tick rule (sign of the last differing trade price); 0 if none. Bid and ask are updated **separately** when each side's price is > 0 (CFT D-2 lesson).
- **Big trade:** one trade tick with size ≥ **10 contracts (NQ)** or **≥ 50 (ES)**.

### 1a. Runtime probe and fallback ladder (decided now, on runtime only)
- QC's free tier gives 10 KB of logs per backtest, so all modelling runs inside QC and only a compact summary is logged.
- Tick runtime on the free node is unknown. First run: `MODE = 'PROBE'`, 2024-01-02 → 2024-01-08, NQ. It logs only tick counts and wall-clock seconds. No features, labels or outcomes are computed.
- Projected time = probe seconds per day × trading days in the window.
  1. If ≤ 8 h: the primary window above.
  2. Else, if the 2025-01-02 → end window projects to ≤ 8 h: that window.
  3. Else: **second-resolution fallback** on the primary window. Each 1-s trade bar counts as one trade, signed by the **tick rule** (CFT D-1 fallback); the 1-s quote bar gives bid/ask size. The big-trade feature (b5) is set to 0. Declared caveat: 1-s tick-rule flow agrees with true aggressor flow only moderately (CFT: corr 0.68).
- The rung used is logged in DEVIATIONS_FLOW_PRED.md before the main run.

## 2. Decision times, horizons, barriers, labels
- **Decision times:** the close of every minute bar from 10:00 to 15:30 ET (bar index k = 29 … 359; 331 per day). Entry price = the last trade price at or before T.
- **Horizons:** **H ∈ {30 s, 5 min, 10 min, 15 min}**. All exits are by 15:45 ET, before Apex's 4:59 PM ET and Topstep's 3:10 PM CT cut-offs.
- **Risk unit:** σ1 = mean, over the previous 20 kept days, of the daily standard deviation of 1-minute close-to-close changes (points, RTH).
  - Barrier u_H = max(σ1 · √(H / 60 s), 4 ticks), tick = 0.25 for both.
  - Target = stop = u_H (symmetric, k = k′ = 1); 1R = u_H.
- **Path:** per-second trade high/low over seconds (T, T + H]. If one second touches both barriers, **the stop is assumed first**. Otherwise time exit at the last trade price at or before T + H. Gross R = +1, −1 or (exit − entry)/u_H, for long and for short.
- **Costs (round trip, points, as all NEXA tests):** NQ S0 1 / **S1 2** / S2 3; ES S0 0.30 / **S1 0.60** / S2 1.20. Net R = gross − cost/u_H.
- **Label:** y_H = 1 if the long gross R > 0, 0 if < 0; rows with exactly 0 are dropped for training.

## 3. Features (29, only data at or before T; four families)
Notation: c_k = minute close, σ1 as above, V̄ = mean per-minute volume over the previous 20 kept days, R̄ = mean daily RTH range over the previous 20 kept days. Each feature is clipped to [−20, 20] before scaling.

**D: time, volatility, price (8)**
1. `tod` = k / 389; 2. `tod2` = tod²
3. `r1` = (c_k − c_{k−1}) / σ1; 4. `r5` = (c_k − c_{k−5}) / (σ1√5); 5. `r15` (√15); 6. `r30` (√30)
7. `rv` = std of today's 1-min changes up to k ÷ σ1; 8. `rng` = today's range so far ÷ R̄

**A: auction context (10)** (profiles: each second's volume at its last trade price, tick precision; value area = 70 % grown from the POC, the larger neighbouring price added first)
9. `poc_p` = (p − prior day POC)/σ1; 10. `vah_p` (prior VAH); 11. `val_p` (prior VAL)
12. `pdh` = (p − prior day high)/σ1; 13. `pdl` (prior low)
14. `orh` = (p − opening-range high)/σ1; 15. `orl` (opening range = 09:30–09:59)
16. `dpoc` = (p − today's developing POC)/σ1
17. `shape` = (developing POC − today's low)/(today's range) (P-shape high, b-shape low; 0.5 if range 0)
18. `node` = log((today's volume within ±2 ticks of p + 1) / (5 × mean volume per traded price today + 1)) (HVN > 0, LVN < 0)

**B: aggressive flow (7)** (imbalance = (buy − sell)/(buy + sell), 0 if no volume)
19. `imb1`, 20. `imb5`, 21. `imb15`: over the last 1/5/15 minutes
22. `cvd` = cumulative (buy − sell) since 09:30 ÷ cumulative volume
23. `big15` = (big buy − big sell volume, last 15 min) ÷ total volume last 15 min
24. `div15` = r15 × imb15 (price vs delta divergence)
25. `part5` = log((volume last 5 min + 1) / (5V̄ + 1))

**C: passive / top of book (4)**
26. `book` = (bid size − ask size)/(bid size + ask size) at T (0 if both 0)
27. `book5` = mean of the minute-close `book` over the last 5 minutes
28. `absorb5` = log(1 + vol5/V̄) − log(1 + |c_k − c_{k−5}|/σ1) (much volume, little progress)
29. `qrate5` = log(1 + quote updates last 5 min) − log(1 + trade ticks last 5 min)

Full depth (walls, DOM changes, true absorption, icebergs, spoofing) is **not testable here**: QC has top of book only, the NEXA recorder has 2 days of delayed data, and paid MBO is outside the $0 rule. Tails, failed auctions, MOC and options/GEX are not in this test.

## 4. Model and walk-forward (fixed, no search)
- **Model:** per H, scikit-learn `StandardScaler` + `LogisticRegression(C=1.0, penalty='l2', solver='lbfgs', max_iter=1000)`. Missing values become 0 after scaling (the training mean). Chosen because a linear model can be copied exactly into C# for the ATAS panel.
- **Walk-forward:** rows grouped by calendar quarter. Every quarter with at least 4 earlier quarters of rows is a test quarter (a final partial quarter counts if it has ≥ 20 kept days). Training = all rows before the test quarter's first day (expanding). Exits never cross days, so splitting by day is the purge.
- **Threshold δ (per fold, no peeking):** fit on training minus its last 2 quarters, predict those 2 quarters, δ = the **98th percentile** of |p − 0.5|; then refit on the full training set.
- **Trading rule (per H, per test day):** in time order, take a signal when |p − 0.5| ≥ δ, no trade of that H is open (the previous exit time ≤ T), and fewer than **3 trades** that day. Direction = sign(p − 0.5).

## 5. Statistics and verdict
- **Per H (pooled OOS trades, time order):** mean net R at S1; moving-block bootstrap (block 20, B = 2,000, seed 20261021), 95 % CI, one-sided p; mean per test quarter; S0/S2 means; gross; win rate; trades per day; green-day share; **B1** = always long at the same times.
- **Calibration (all OOS decision rows):** Brier score and Brier skill score against the training base rate.
- **Family ablation (rule 2):** in every fold refit without family F (A, B, C, D in turn). ΔBrier_F = Brier(without F) − Brier(full), per OOS day; moving-block bootstrap over days (block 5). Family F **adds information at H** only if the ΔBrier CI lower bound > 0. The net R of the without-F model is also reported.
- **Placebo:** 20 seeds; in every fold the training labels are taken from another day (circular day shift by m, m drawn from the seed, as H-ML1 D-1); same δ and trading; **P-rank** = share of placebo OOS means ≥ the real mean.
- **Verdict per H (NQ binding):**
  - INSUFFICIENT-N: fewer than 100 OOS trades.
  - **REJECTED:** mean S1 ≤ 0.
  - **VALIDATED:** mean ≥ **+0.025R** (H-PROP-EV threshold) **and** CI lower > 0 **and** one-sided p ≤ **0.0125** (Bonferroni over 4 horizons) **and** ≥ ⅔ of test quarters positive **and** P-rank ≤ 0.05.
  - INCONCLUSIVE: otherwise.
- **H-FLOW-PRED overall (NQ):** VALIDATED if any H is VALIDATED; REJECTED if every H is REJECTED or INSUFFICIENT-N; otherwise INCONCLUSIVE.
- **ES:** same pipeline, reported as secondary only.

## 6. Use of the result
- **REJECTED:** no prediction model is shown to the user. No re-tuning on this data (NEXA law L2). The family ablation is still reported (which families carry information at all).
- **INCONCLUSIVE or VALIDATED (any H):** NEXA v6 "Market Predicted" panel (ATAS, C#, read-only, never places orders):
  - uses the frozen coefficients logged by this run for the best non-rejected H;
  - shows probability, entry, SL, TP and exit time;
  - logs every forecast, taken or not;
  - labelled **UNPROVEN** until a separately pre-registered forward record passes the same bar.
  - The ATAS features must reproduce §3 exactly; any difference goes in a deviation note before forward scoring.
- No daily $ target or green-day count can be made compulsory by any code; the report states the green-day share as measured.

## 7. Multiple testing
- 8 trials (4 horizons × 2 instruments). Ledger ≈ 177.

## 8. Code, tests, freeze
- `qc_flow_pred/main.py`: per-second store, quote-rule classifier, features, barrier labels, walk-forward logistic model, ablation, placebo, statistics. Reads data only, no orders. Logs `NEXA_FP_PART i/n` chunks; the coefficient block only for horizons that are not REJECTED.
- `test_flow_pred.py` (synthetic data, `.venv-ml`, `run_tests.py`):
  1. quote-rule and tick-rule classification, one-sided quote updates;
  2. barrier labels: stop-first, time exit, 30-s horizon, 4-tick floor;
  3. no feature uses data after T (perturbation test);
  4. value area and POC on a known profile;
  5. walk-forward folds never train on test-quarter days; δ uses only training;
  6. trading rule: 3 a day, no overlap;
  7. placebo day shift keeps the minute and moves the day;
  8. a planted flow signal is found and a pure-noise market is not (end-to-end);
  9. verdict logic and the 10 KB log budget.
- Tests pass before the hash; the QC editor hash is checked before each run; **one main run per instrument** (the probe does not count).
