# PRE-REGISTRATION H-SWEEP: prior-day high/low stop runs, continuation vs reclaim reversal (NQ primary, ES transfer; QuantConnect)

**Status: BINDING.**
- User approval 2026-10-21: "all four, do it" (proposal P1 in `../INSTITUTIONAL_PATTERNS_REVIEW_2026-10-21.md`).
- **Written before any data was read for this hypothesis.** No statistic of these rules has been computed on any data.

**Sources and prior:**
- Osler (2005), JIMF 24(2) / NY Fed SR150: stop-loss orders cluster just beyond obvious levels; when they trigger, prices move **faster in the same direction**, for hours (FX). → **Arm A (continuation).**
- Video claim (user's list, idea 5; SRC-YT batches; NEXA T2 / T2b): a sweep beyond a level that **closes back inside** is a manipulative stop run → fade it. → **Arm B (reclaim reversal).**
- Prior: low. Related NEXA tests lost (T2a −0.045R, FPT-REV −0.456R, OFC1 −0.21R); the prior-day high/low trigger itself is untested.
- Prop link: **≥ +0.025R net per trade** is needed before any evaluation is break-even (H-PROP-EV); reported, no verdict effect.

## 1. Data and valid days (as PREREG_FPT_REV §1)
- QuantConnect AlgoSeek continuous futures, front month by open interest, `BACKWARDS_RATIO`, minute trade bars, America/New_York, tick 0.25. **NQ primary, ES transfer.** RTH bars only (390 bars 09:30–15:59).
- Period **2010-01-04 → the last complete trading day available at run time**; warm-up from 2009-12-01; one run per instrument, each once.
- Day d is valid if: all 390 RTH bars exist; no contract-mapping change since the previous valid day (roll days excluded and counted); ≥ 20 prior valid days exist; the previous valid day is ≤ 4 calendar days before d.

## 2. Levels and scale
- **PDH / PDL** = highest high / lowest low of the previous valid day's 390 RTH bars.
- **RNG20(d)** = mean of (RTH high − RTH low) over the 20 prior valid days (not d).
- **s(d) = max(0.10 · RNG20(d), 1.0 point).** Fixed here: one tenth of a typical day's range is a short-term bracket comparable to the FPT test (no tuning; no outcome has been seen).
- **Sweep** of PDH at bar k: h[k] ≥ PDH + 2 ticks (0.5 pt). Of PDL: l[k] ≤ PDL − 2 ticks.
- **Gap rule:** if the 09:30 bar's open is already beyond the level (o[0] ≥ PDH for the high side, o[0] ≤ PDL for the low side), that side has no trade that day.
- The first sweep of each side in bars k = 1 … 329 (09:31 … 14:59) is the only event for that side.

## 3. Arm A: continuation (Osler)
- On the first PDH sweep at bar k: **long** at the open of bar k+1; stop = entry − s(d); target = entry + 2·s(d).
- PDL mirror: **short**, stop = entry + s(d), target = entry − 2·s(d).
- Exit: first touch on each minute's high/low from the entry bar, **stop first if both touch in one minute**; otherwise the 15:59 close.
- **One position at a time.** If the other side's event comes while a position is open, it is skipped (counted).

## 4. Arm B: reclaim reversal (the video claim)
- After the first PDH sweep at bar k: the first bar j in k … k+15 whose **close is back below PDH** (c[j] < PDH) gives the signal, provided j ≤ 329.
- **Short** at the open of bar j+1. Stop = (highest high of bars k … j) + 1 tick. R = stop − entry; **no trade if R ≤ 0 or R < 1.0 point** (counted). Target = entry − 2R.
- PDL mirror: close back above PDL → long; stop = lowest low of k … j − 1 tick; target = entry + 2R.
- Exit and one-position rule as Arm A. Arm A and Arm B are separate trade streams (they are never combined).

## 5. Costs and R
- Round trip, points (as PREREG_FPT_REV): NQ S0 = 1, **S1 = 2**, S2 = 3; ES S0 = 0.30, **S1 = 0.60**, S2 = 1.20.
- Net R = (dir · (exit − entry) − cost) / R_pts, with R_pts = s(d) for Arm A and R for Arm B.
- Driftless reference hit rate for a 2R target: 1/3.

## 6. Placebo (distance-matched levels)
- 20 replicates (seed 20261021). In each replicate and day, each side's level is replaced by
  - high side: L' = o[0] + m · (PDH − o[0]); low side: L' = o[0] − m · (o[0] − PDL);
  - m ~ Uniform(0.7, 1.3), redrawn if 0.95 ≤ m ≤ 1.05, independently per side and day.
- Everything else (sweep, gap rule, window, both arms, costs) is identical. If o[0] is already beyond the real level, that side is skipped in the placebo too.
- Placebo statistic = mean net R per trade at S1, per replicate. Real percentile = share of replicates with a mean below the real mean.

## 7. Statistics and verdict (per arm and instrument)
- **Primary statistic:** mean net R per trade at S1.
- Moving-block bootstrap over the chronological valid days (block 20, B = 2,000, **seed 20261021**); each replicate = Σ R ÷ trades on the resampled days; 95 % percentile CI; one-sided p.
- 4 equal consecutive blocks of valid days. **Hold-out** = valid days from 2023-01-03 to the end.
- **VALIDATED (G4):** mean > 0, CI lower > 0, ≥ 3/4 blocks > 0, ≥ 300 trades, hold-out mean > 0, and the real mean above the **95th percentile** of the placebo means (≥ 19 of 20).
- **REJECTED:** mean ≤ 0. **INCONCLUSIVE:** otherwise. **INSUFFICIENT-N:** < 300 trades.
- Reported (no verdict effect): trades, trades/day, hit rate vs 1/3, payoff, S0/S2 means, long vs short, high-side vs low-side, time-exit share, mean R in points, per-year means, green-day share, max drawdown in R, longest losing streak, daily Sharpe, skipped counts, the +0.025R comparison.

## 8. Multiple testing
- 4 trials: {Arm A, Arm B} × {NQ, ES}. Ledger before this batch ≈ 163. DSR of the NQ primaries reported at 4 and at the cumulative count.

## 9. Code, freeze, use
- `qc_sweep/main.py` (MODE ∈ {NQ, ES}; only MODE differs between runs). Unit tests `test_sweep.py` on synthetic days: levels and gap rule; first-sweep detection and window; Arm A bracket and stop-first tie; Arm B reclaim window, stop, R floor; one-position rule; placebo level construction; RNG20 warm-up; stats/verdict smoke.
- Tests must pass before the code is hashed into PREREG_HASHES.txt. The QC editor hash is checked before each run. Output: `NEXA_SWEEP_RESULT` JSON in the log (chunked if > 7,000 characters).
- No live or paper trading follows from one result. A VALIDATED arm would next need a forward paper check and a re-run of H-PROP-EV-TS with its R distribution.
