# PRE-REGISTRATION H-ORB5: the Zarattini & Aziz 5-minute opening range breakout on NQ (ES transfer), outside the paper's window, against random directions

**Status: BINDING.**
- User approval 2026-10-21: "all four, do it" (proposal P2 in `../INSTITUTIONAL_PATTERNS_REVIEW_2026-10-21.md`).
- **Written before any data was read for this hypothesis.** NEXA has not run this exact rule. Related NEXA tests: H-ORB-1 (NAS100, +0.063R, inconclusive), H-ORB30L-NQ (30-min, OOS −0.071R, failed).

**Source:** Zarattini & Aziz (2023), "Can Day Trading Really Be Profitable?", SSRN 4416622: QQQ 2016-01 → 2023-02-17, ~24 % winners, +0.13R/trade, commission only, no out-of-sample period.
- Independent replications already read (review §2): CFD 2015–2026 net ≈ 0; NQ futures 2020–2026 net +0.079R but random directions also profit; QQQ slippage ≈ 2 ¢ kills it.
- **Question here:** outside the paper's window, does the *direction of the first candle* add anything beyond what a random direction with the same bracket earns?

## 1. Data and valid days
- As PREREG_SWEEP §1 (QC continuous futures, OI mapping, backwards ratio, minute bars, RTH 390 bars, roll days excluded). Period 2010-01-04 → last complete day; ≥ 1 prior valid day not required (no lookback).
- **Primary set P** = valid days in **2010-01-04 → 2015-12-31** and **2023-03-01 → end** (both outside the paper's sample).
- **Reported set IN** = valid days 2016-01-04 → 2023-02-17 (the paper's window; no verdict effect).

## 2. Rule (the paper's base rule, unchanged)
- First 5-minute candle = bars 0 … 4 (09:30–09:34): O = o[0], C = c[4], H = max h[0..4], L = min l[0..4].
- Direction = +1 if C > O, −1 if C < O, no trade if C = O (counted).
- Entry at the open of bar 5 (09:35). Stop: L for a long, H for a short. R = |entry − stop|; **no trade if R ≤ 0 or R < 1.0 point** (counted; protects against a 1-tick risk dominated by cost).
- Target = entry + dir · 10R. Exit: first touch per minute from bar 5, stop first on ties; otherwise the 15:59 close. One trade per day.
- Costs and net R as PREREG_SWEEP §5 (NQ S1 = 2 points, ES S1 = 0.60), R_pts = R.

## 3. Random-direction placebo
- 500 replicates (seed 20261021). Each replicate gives every primary day an independent random direction (±1, p = ½), with the same candle, stop side for that direction (long → L, short → H), R floor, 10R target and exit.
- Statistic per replicate = mean net R per trade at S1 over set P. Real percentile = share of replicates below the real mean.

## 4. Statistics and verdict (NQ primary; ES transfer with the same rule)
- Primary statistic: mean net R per trade at S1 over set P.
- Bootstrap, blocks, CI and p as PREREG_SWEEP §7 (seed 20261021), over the chronological P days; 4 blocks over P days.
- **VALIDATED (G4):** mean > 0, CI lower > 0, ≥ 3/4 blocks > 0, ≥ 300 trades, and real mean > **95th percentile** of the placebo means.
- **REJECTED:** mean ≤ 0. **INCONCLUSIVE:** otherwise. **INSUFFICIENT-N:** < 300 trades.
- Reported: the same quantities on set IN and on 2010–2015 and 2023-03 → end separately; hit rate (paper ~24 %); share reaching 10R; time-exit share; long vs short; S0/S2; per-year means; green-day share; max drawdown in R; longest losing streak; the +0.025R comparison.

## 5. Multiple testing
- 2 trials (NQ, ES). Ledger before this batch ≈ 163 (+4 H-SWEEP).

## 6. Code, freeze, use
- `qc_orb5/main.py` (MODE ∈ {NQ, ES}). Unit tests `test_orb5.py`: candle and direction, doji skip, R floor, stop side, 10R target and tie rule, set P / IN split, placebo stop side, stats smoke. Hash before any run; QC editor hash checked before each run; output `NEXA_ORB5_RESULT`.
- No trading follows from one result.
