# PRE-REGISTRATION T2a · H-VAR: value-area re-entry ("80 % rule" / Data Trader S2) on ES (NQ transfer; QuantConnect)

**Status: BINDING.**
- User approval 2026-10-18: "we can start T1 and T2a pre-registrations".
- **Written before any data was read for this hypothesis.**

**Sources:**
- **Data Trader** (SRC-YT-095, `Xa2fB097ajs` 14:29–17:19, CL-146 S2):
  - the prior session closed inside its value area;
  - price crosses outside the VAH / VAL;
  - a candle **closes** back inside;
  - trade toward value; stop at the swing extreme; target 2R;
  - repeatable within the session.
- **Dalton** value-area rule (S42): back inside value → "a good possibility" of auctioning to the other side. This defines the secondary target.
- **Valastro** (CL-147): failed auctions on mean-reversion days.

**Not tuned.** Every number is from a source or fixed here.

## 1. Data, valid days, value area
- Identical to `PREREG_T1_STATE.md` §1–§2:
  - ES primary, NQ transfer;
  - 2010-01-04 → the last complete day;
  - roll days excluded;
  - the prior-day 70 % value area by the Dalton two-tick rule over uniformly spread minute volume;
  - tick 0.25.
- **Same valid days and same value areas as T1** (computed in the same run).

## 2. Setup condition (per day)
- The prior session's close C(d−1) satisfies **VAL ≤ C(d−1) ≤ VAH** (closed inside its own value area). Otherwise there is no T2a trade on day d (count reported).

## 3. Signal (primary: 15-minute bars)
- **15-minute RTH bars** aligned to 09:30 (09:30–09:44, …, 15:45–15:59), built from the minute bars. Data Trader's own worked example uses 15-minute bars [8:55].
- **Excursion:**
  - a 15-minute bar **closes** below VAL (down excursion) or above VAH (up excursion);
  - the excursion's extreme is tracked from that bar's first minute onward.
- **Re-entry signal:** after an excursion, the first later 15-minute bar whose close satisfies **VAL < close < VAH**.
  - After a down excursion: **long**. After an up excursion: **short**.
- **Signal window:** the signal bar must end at or before **15:00 ET**. Later signals are ignored.
- **One position at a time.**
  - After a trade exits, a new trade needs a **new excursion that begins after the exit**, followed by a new re-entry close.
  - Excursions on either side count.
  - Signals that occur while a position is open are ignored.

## 4. Entry, stop, target, exit
- **Entry:** the open of the first minute bar after the signal bar (no same-bar fill).
- **Stop:**
  - for a long: the lowest low of all minute bars from the start of the excursion bar through the end of the signal bar, **minus 1 tick**;
  - for a short: the mirror (highest high + 1 tick).
- **R** = |entry − stop| in points. If R < 2 ticks, the trade is skipped (counted).
- **Target (primary):** entry ± **2R** (Data Trader).
- **Fills:**
  - from the entry minute onward, the stop and target are checked on each minute bar's high / low;
  - if both are touched in the same minute, **the stop is assumed first**;
  - fills happen at the stop / target price;
  - a position still open at 15:59 exits at the 15:59 bar close.
- **Costs (round trip, per contract, index points):**
  - ES: S0 = 0.30, **S1 = 0.60**, S2 = 1.20;
  - NQ: S0 = 1, **S1 = 2**, S2 = 3 (as PREREG_CFT §4).
- **Net R** = (direction × (exit − entry) − cost) / R.

## 5. Statistics and verdict (primary = ES, 15-minute, 2R target, S1)
- **Primary statistic:** mean net R per trade at S1.
- **Inference:**
  - moving-block bootstrap over the chronological sequence of valid days: block 20, B = 2,000, **seed 20261018**;
  - each replicate = Σ R over the resampled days ÷ the number of trades on them;
  - 95 % percentile CI; one-sided p.
- **Stability:** 4 equal consecutive blocks of valid days; the mean net R in each.
- **Verdicts:**
  - **VALIDATED (G4):** mean > 0, CI lower bound > 0, ≥ 3 of 4 blocks > 0, and ≥ 300 trades;
  - **REJECTED:** mean ≤ 0;
  - **INCONCLUSIVE:** otherwise;
  - **INSUFFICIENT-N:** fewer than 300 trades.
- **Driftless reference:** with a 2R target and a 1R stop, the hit rate under no edge is 1/3. The hit rate is reported against 1/3.
- **Also reported (no verdict effect):**
  - trades, trades per day, hit rate, payoff;
  - S0 / S2 means;
  - long vs short;
  - share of time exits;
  - mean R in points;
  - per-year means;
  - daily-P&L green-day share;
  - maximum drawdown in R;
  - the Sharpe of the daily R series.

## 6. Declared secondary variants (computed in the same run; reported, never substituted for the primary)
- **V-5m:** identical, but with 5-minute bars (Sowmya / Dale timeframe).
- **V-VA:** primary signal, but target = the opposite VA edge (Dalton). If that edge is not beyond the entry in the trade direction, the trade is skipped (counted).
- **V-EVE:** primary, but only signal bars ending by **12:00 ET** (the user's MYT evening window); time exit unchanged.
- **NQ:** the primary and all variants, as declared transfer tests with the same criteria.

## 7. Multiple testing
- T2a counts as **8 trials** in the DSR ledger: (primary, V-5m, V-VA, V-EVE) × (ES, NQ).
- Report the DSR of the primary using the cumulative NEXA trial count at run time.

## 8. Code, freeze, use of the result
- Same algorithm file as T1 (`qc_asm/main.py`, MODE ∈ {ES, NQ}), the same tests file, and the same freeze and hash procedure.
- **Output:** `NEXA_T2A_RESULT` JSON per run, plus a compact daily R series.
- **Not done here:** conditioning on the T1 state (that is T3, which needs its own pre-registration after T1's verdict), order-flow triggers (T4), and the prop overlay.
- **No live or paper trading follows from a single VALIDATED result.** The next step would be T3/T4 and a forward paper check.
