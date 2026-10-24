# PRE-REGISTRATION H-CE50: the "CE 50 % Model" (pre-open range midline + first 3-minute close, trailing 15-minute swing stop) on NQ (binding) and ES

**Status: BINDING.** User approval 2026-10-23 (chat): "approve H-CE50. Freeze it, build and test the code, then run it on QuantConnect (NQ, ES)."
- Requested 2026-10-22: "write the H-CE50 pre-registration (CE 50% Model on NQ binding + ES, free QC data) for my approval".
- Source: Instagram post by @cemarketsolutions, 2026-10-11 (`../instagram_2026-10-22/IG_SEARCH_DECODE.md`).
- **Written before any data was read for this hypothesis.**

## 0. Source rule (caption, paraphrased) and claim
- Mark the 08:30–09:30 ET high and low; split the range at 50 %.
- If the first 3-minute candle after the 09:30 open closes below the 50 % line, sell at the next open. The model "takes both sides", so the mirror is: closes above → buy.
- Stop beyond the range, trailed to every 15-minute swing (swing highs for a short, swing lows for a long). Out by 16:00 ET.
- "Most days it loses small; big days pay for them."
- **Claim:** 2016–2026 backtest, 2,625 trades, commissions included, ¼ Kelly sizing, 59.37 % a year compounded. Hypothetical; the full model is sent only by DM (not requested).
- **Not specified by the source** (fixed here, before data): the instrument (the example's "1,065 points" fits NQ), the exact swing definition, tick offsets, gap fills, the minimum risk, ties.

**Prior: low but not negligible.**
- Same opening-range family as H-ORB5 / H-ORB30L / H-HOUGAARD (all rejected).
- But here the stop is the far side of a 60-minute range and the exit trails, so trades are large in R, costs are a small share, and 1-minute bars can resolve the exits (unlike H-HOUGAARD's 3–11 point bracket).
- The claimed backtest window is 2016–2026, so 2010–2015 is **outside the creator's sample** and serves as the binding out-of-sample test.

## 1. Data and valid days
- QuantConnect free node, minute bars, continuous front contract by open interest, `BACKWARDS_RATIO`, **extended market hours on** (the range is pre-open).
- **NQ binding; ES secondary** (the files differ only in the `MODE` line).
- Period: 2010-01-04 → the last complete day at run time.
- Valid day: a weekday with every 1-minute bar from 08:30 to 15:59 ET (450 bars) and no roll that day.
- Sets:
  - **P (binding, outside the creator's sample)** = valid days 2010-01-04 → 2015-12-31;
  - **IN** = 2016-01-04 → end (the creator's window; must also be positive);
  - FULL = both (reported).

## 2. Rule as tested (fixed now)
- **Range:** H = max high and L = min low of the 60 one-minute bars starting 08:30 … 09:29. Midline M = (H + L) / 2.
- **Signal candle:** the 3-minute candle 09:30–09:32 (bars starting 09:30, 09:31, 09:32); its close = the close of the 09:32 bar.
  - Close < M → **short**; close > M → **long**; close = M → no trade (counted).
- **Entry:** the open of the 09:33 bar.
- **Initial stop:**
  - short: H + 1 tick;
  - long: L − 1 tick.
  - 1R = |entry − initial stop|. **No trade if 1R < 4 ticks** (counted); also no trade if the entry is already beyond the stop (counted).
- **15-minute bars** from 09:30 ET: 09:30–09:44, 09:45–09:59, … built from the 1-minute bars.
  - A **swing high** is a 15-minute bar whose high is strictly greater than the highs of the bars just before and just after it; a **swing low** is the mirror. A swing is confirmed at the close of the following 15-minute bar.
  - **Trailing:** at each confirmation, a short's stop moves to swing high + 1 tick (a long's to swing low − 1 tick) **only if this tightens the stop**. The new stop applies from the next 1-minute bar.
- **Exit (1-minute bars, from the entry bar on):**
  - stop touched (short: high ≥ stop; long: low ≤ stop), filled at the stop or at the bar open if the bar gaps through it;
  - otherwise at the close of the **15:59** bar (out by 16:00).
  - One trade per day.
- **Costs (round trip, points; NEXA standard):** NQ S0 1 / **S1 2** / S2 3; ES S0 0.30 / **S1 0.60** / S2 1.20. Net R = (direction × (exit − entry) − cost) / 1R.
- Sizing (¼ Kelly) is not modelled: the test is per-trade expectancy in R. The claim of 59 % a year is not re-derived.

## 3. Random-direction control
- 500 replicates (seed 20261022). On every P day with a real trade, the direction is drawn at random (±1, p = ½), with the same entry bar and price.
- The initial stop is on the far side of the range for that direction, and the same trailing and exit rules apply.
- Statistic = mean net R at S1 over P. Real percentile = share of replicates below the real mean.

## 4. Statistics and verdict (NQ binding; ES the same rule, reported)
- Primary statistic: mean net R per trade at S1 over **P**.
- Moving-block bootstrap over the chronological valid days as PREREG_SWEEP §7 (block 20, B = 2,000, seed 20261022; each replicate = Σ R ÷ trades on the resampled days), 95 % percentile CI, one-sided p; 4 equal consecutive blocks of P days.
- **REJECTED:** P mean ≤ 0.
- **VALIDATED:** all of
  - P mean ≥ **+0.025R** (H-PROP-EV threshold);
  - P CI lower > 0;
  - one-sided p ≤ **0.05 / 2** (two instruments);
  - ≥ 3/4 P blocks > 0;
  - **IN mean > 0**;
  - ≥ 300 P trades;
  - real mean > the 95th percentile of the control.
- **INCONCLUSIVE:** otherwise. **INSUFFICIENT-N:** < 300 P trades.
- **H-CE50 overall** = the NQ verdict.
- **Also reported:**
  - the same quantities on IN and FULL; per-year means; win rate (the source expects many small losses);
  - share of trades exiting by stop vs time; mean R won on winners vs lost on losers; largest win in R;
  - long vs short; S0/S2; trades per year; skipped counts (doji, R floor);
  - green-day share; max drawdown in R; longest losing streak;
  - the +0.025R comparison.

## 5. Use of the result
- REJECTED or INCONCLUSIVE: no strategy; no re-tuning (NEXA law L2); the opening-range family stays closed.
- VALIDATED: a separately pre-registered forward paper test (≥ 60 trading days) before any prop account. A trailing-stop day-hold executed by hand is feasible for the user (one decision at 09:33, then stop updates every 15 minutes).

## 6. Multiple testing
- 2 trials (NQ, ES). Ledger ≈ 183 → ≈ 185.

## 7. Code, freeze, use
- `qc_ce50/main.py` (MODE ∈ {NQ, ES}). Reads data only, no orders. Logs compact JSON (< 10 KB).
- `test_ce50.py` (synthetic data, `run_tests.py`):
  - range and midline;
  - the signal candle and the doji skip;
  - entry at the 09:33 open;
  - initial stop offsets and the 4-tick floor;
  - 15-minute bar building; swing detection and confirmation timing (no look-ahead);
  - trailing that only tightens;
  - gap-through-stop fills;
  - the 15:59 time exit;
  - P / IN split;
  - control stop side;
  - verdict logic and the log budget.
- Tests pass before the hash. The QC editor hash is checked before each run (website, the user's login). **One run per instrument.**
