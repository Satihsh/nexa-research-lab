# PRE-REGISTRATION H-HOUGAARD: Tom Hougaard's pre-open range breakout, on NQ (binding), ES and YM

**Status: BINDING.** User approval 2026-10-22 (chat): "approve H-HOUGAARD. Freeze it, build and test the code, then run it on QuantConnect."
- Requested 2026-10-22: "write the H-HOUGAARD-ES pre-registration (Tom Hougaard pre-open range breakout on ES/NQ, free QC data) for my approval". Source: the user's saved reel IG-01 (`../instagram_2026-10-22/IG_SAVED_DECODE.md`).
- **Written before any data was read for this hypothesis.**

## 0. Source rule (Hougaard, "Breakout Strategy for the Dax and Dow Open", tradertom.com, written August 2021)
- Observation: the 59 minutes of trading before the cash open. Dow: 13:30–14:29 UK time = **08:30–09:29 New York**. DAX: 07:00–07:59 UK.
- In the minute before the open: a **buy stop at the high** and a **sell-short stop at the low** of that window.
- **Stop 9 points, target 6 points.** When one order fills, the other is cancelled.
- He trades CFDs (TD365) and discusses slippage on the open (e.g., 1.7 points on the Dow). He shows about 14–16 sessions (19 July – 9 August 2021), with wins and losses and no total.
- **Not specified by the source** (fixed here, before data): unfilled-order cancel time, maximum hold, range filter, what happens if both levels trade in one bar.
- He also mentions "always going for more" and testing 9, 10, 11 or 15-point targets. Only the published 6 and a 9-point (1:1) target are tested.

**Prior: low.**
- Same family as the opening-range breakouts NEXA already rejected: H-ORB5 NQ −0.20R; H-ORB30L out of sample −0.07R; H-ORB-1 inconclusive.
- It is a micro-scalp. With +6 / −9 points, break-even needs a win rate above 60 % **before costs**.
- With costs c in points, the break-even win rate is (stop + c) / (stop + target). On YM at S1 (c = 3) that is 80 %. On NQ with the scaled stop (≈ 4.4 points) and c = 2, about 87 %.
- So the costs likely decide the result; the test measures that honestly.

## 1. Data and valid days
- QuantConnect free node, minute bars, continuous front contract by open interest, `BACKWARDS_RATIO` (keeps percentage moves exact), **extended market hours on** (the window is before the 09:30 open).
- Instruments:
  - **NQ (binding)**;
  - ES (secondary);
  - **YM = Dow futures**: the source instrument, a literal check of the published rule (secondary).
  - One run per instrument; the files differ only in the `MODE` line.
- Period: 2010-01-04 → the last complete day at run time.
- Valid day: a weekday with all 59 window bars (08:30–09:28 ET start times) and all bars 09:29–11:29, and no roll that day.
- Windows:
  - **FULL** = all valid days (binding);
  - **POST** = 2021-08-10 → end, after publication (must also be positive);
  - **PRE** = 2010-01-04 → 2021-08-09 (reported).

## 2. Rule as tested (fixed now)
- Window high H and low L = max high / min low of the 59 bars starting 08:30 … 09:28 ET.
- Orders active from the bar starting **09:29** until the bar starting **10:29** (inclusive). If neither triggers, no trade (counted).
- **Trigger:**
  - long when a bar's high ≥ H (entry = max(H, bar open));
  - short when a bar's low ≤ L (entry = min(L, bar open)).
  - The first trigger cancels the other (OCO). One trade per day.
  - **If one bar triggers both levels before any fill**, the trade is counted as **−1R** (conservative; the order of the touches is unknown).
- **Stop and target distances (percentage scaling of the published points):**
  - Hougaard's 9 / 6 Dow points ≈ **0.0257 % / 0.0171 %** of the Dow at the time of writing (≈ 35,000 in August 2021).
  - Stop = 0.000257 × entry, rounded to the nearest tick, minimum 2 ticks.
  - Variant **A (published):** target = 0.000171 × entry, rounded to the nearest tick, minimum 1 tick.
  - Variant **B (1:1):** target = stop.
  - On YM this gives ≈ 9 / 6 points at a 35,000 Dow (literal check), and the same percentage on ES/NQ.
- **Exit:**
  - first touch per minute from the entry bar on;
  - if a bar touches both stop and target, **stop first** (also within the entry bar);
  - otherwise at the close of the bar starting **11:29 ET** (time exit).
- 1R = the stop distance in points. Gross R = +target/stop, −1, or (exit − entry)/stop for a time exit.
- **Costs (round trip, points; NEXA standard):**
  - NQ S0 1 / **S1 2** / S2 3;
  - ES S0 0.30 / **S1 0.60** / S2 1.20;
  - **YM** S0 2 / **S1 3** / S2 5 (1-point tick; commission ≈ 1 point, plus slippage on stop entries at the open, which Hougaard himself reports).
  - Net R = gross R − cost / stop.

## 3. Random-direction control
- 500 replicates (seed 20261022). On each FULL day with a trade, the direction is drawn at random (±1, p = ½).
- The entry is at the real trigger bar and price for that direction's side; if that side never triggered, the replicate uses the real trigger bar's open. Same stop, target, exit and costs.
- Statistic = mean net R at S1. Real percentile = share of replicates below the real mean.

## 4. Statistics and verdict (per instrument and variant; NQ variant A is binding)
- Primary statistic: mean net R per trade at S1. Moving-block bootstrap over the chronological valid days as PREREG_SWEEP §7 (block 20, B = 2,000, seed 20261022; each replicate = Σ R ÷ trades on the resampled days), 95 % percentile CI, one-sided p; 4 equal consecutive blocks of valid days over FULL.
- **REJECTED:** FULL mean ≤ 0.
- **VALIDATED:** all of
  - FULL mean ≥ **+0.025R** (H-PROP-EV threshold);
  - FULL CI lower > 0;
  - one-sided p ≤ **0.05 / 6** (Bonferroni over 3 instruments × 2 variants);
  - ≥ 3/4 blocks > 0;
  - POST mean > 0;
  - ≥ 300 trades;
  - real mean > the 95th percentile of the random-direction control.
- **INCONCLUSIVE:** otherwise. **INSUFFICIENT-N:** < 300 trades.
- **H-HOUGAARD overall** = the NQ variant A verdict. ES, YM and variant B are reported, never substituted.
- **Also reported:**
  - fill rate; win rate vs the break-even win rate; S0/S2 means; gross R;
  - long vs short; time-exit share; "both levels in one bar" count;
  - per-year means; green-day share; max drawdown in R; longest losing streak;
  - a YM fixed-points cut (literal 9 / 6 Dow points instead of the percentage), descriptive only.

## 5. Use of the result
- REJECTED or INCONCLUSIVE: no strategy; the opening-range family stays closed. No re-tuning on this data (NEXA law L2).
- VALIDATED: a separately pre-registered forward paper test (≥ 60 trading days) before any prop account. Manual execution of a 4–9 point bracket at the open is itself a risk to state at that point.

## 6. Multiple testing
- 6 trials (3 instruments × 2 variants). Ledger ≈ 177 → ≈ 183.

## 7. Code, freeze, use
- `qc_hougaard/main.py` (MODE ∈ {NQ, ES, YM}; both variants and the control in one run). Reads data only, no orders. Logs a compact JSON (< 10 KB, free-tier limit).
- `test_hougaard.py` (synthetic data, `run_tests.py`):
  - window high/low;
  - order activation and cancel time;
  - OCO and the both-levels-in-one-bar rule;
  - gap fills at the bar open;
  - stop-first ties, including in the entry bar;
  - percentage stop/target and tick rounding;
  - time exit;
  - FULL/POST/PRE split;
  - control side handling;
  - verdict logic and the log budget.
- Tests pass before the hash. The QC editor hash is checked before each run, through the website with the user's login (the QC API is paid). **One run per instrument.**
