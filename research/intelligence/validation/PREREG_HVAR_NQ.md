# PRE-REGISTRATION H-VAR-NQ: Dalton's Value-Area Rule on Nasdaq-100 futures

**Status: BINDING.**
- Approved by the user 2026-10-14: "approved, pre-register H-ORB30L-NQ and H-VAR-NQ".
- Written **before** any value-area-rule statistic has been computed on NQ.
- **Implementation and the run each need a separate user approval.**
- Inherits the discipline of `PREREG_HIVB1_NQ.md` except where stated.

## 1. Hypothesis, source, honest prior

**Source:** James Dalton, *Mind over Markets* (corpus PDF, pp. 278–280, "Special Situations: The Value-Area Rule"). Paraphrase:
- If the market opens outside the previous day's value area, and price is then **accepted (double TPO prints) within that value area**, "there is a good possibility that the market will auction completely through that value area".
- Dalton's three conditions for higher reliability:
  1. **distance**: an open closer to value;
  2. a **narrow value area**;
  3. **market direction**: the entry agrees with the longer-term auction.
- Dalton's own warning (p. 280): taken *without* those conditions, the probability of trading all the way through is "little better than a flip of a coin".
- The popular "80 % rule" figure is **not** in Dalton's text.

**This test answers two questions:**
- (a) Is the unconditional rule profitable after costs?
- (b) Do Dalton's three conditions, defined mechanically before data, change it?

**Honest prior:** coin-flip-like unconditionally (by the source's own words). The conditions are untested here.

## 2. Data, clock, days

- **Data:** CME NQ ohlcv-1m with volume, sha `35d1c3f5…` (as H-IVB1-NQ).
- **Clock and calendar:** as H-IVB1-NQ.
- **Day d needs:**
  - the previous **eligible** RTH session d−1 complete (09:30–15:59; any missing bar → no setup);
  - d's 09:30 bar;
  - d's 15:59 bar.

## 3. Rule (exact; **DC** = design choice where the source is silent)

1. **Previous-day value area:**
   - Volume profile of d−1, 09:30–15:59, in 0.25-point bins.
   - Each 1-min bar's volume is spread uniformly over its range (**DC-1**, as H-IVB1-NQ).
   - POC and **70 % VA** via `of_common.va_greedy`.
   - VAL / VAH = lower / upper edge of the VA bins.
   - Dalton defines value by volume ("the range where the greatest volume of trade took place").
2. **Setup:** d's **09:30 open** is **< VAL** (long setup, target VAH) or **> VAH** (short setup, target VAL). An open inside the VA → no setup.
3. **Acceptance ("double TPO prints"):**
   - TPO periods are the 30-min brackets 09:30–09:59, 10:00–10:29, ….
   - A period is "inside" if its high ≥ VAL + 0.25 and its low ≤ VAH − 0.25 (it traded at least one tick inside value).
   - **Acceptance = two consecutive inside periods (DC-2).**
   - The signal is at the end of the second period.
4. **Executability deadline (user constraint, declared before data):**
   - The signal period must end **by 11:30 ET**, i.e. signals at 10:30, 11:00 or 11:30.
   - The source's no-deadline version is robustness §8.
5. **Entry:**
   - Open of the next 1-min bar after the signal.
   - Long if the open was below value, short if above.
   - If that bar opens already at or beyond the target → no trade (counted).
6. **Stop (DC-3, the source gives none):**
   - The session extreme made outside value: the day's low so far (long) or high so far (short), at the signal time.
   - Logic: a return beyond where the rejected auction came from invalidates the acceptance.
   - Intrabar; a gap fills at the bar open.
   - R = |entry − stop|.
   - **Cost floor:** skip if R < 10 points, counted.
7. **Target:** the opposite VA edge (VAH for longs, VAL for shorts). It fills only on a ≥ 1-tick trade-through.
8. **Same bar:** if stop and target are touched together → stop. On the entry bar, only the stop is checked.
9. **Time exit:** close of the 15:59 bar.
10. **One trade per day.**
11. **Outcome** = (exit − entry − cost) × direction ÷ R.

## 4. Costs

S0 / **S1** / S2 = 1 / **2** / 3 NQ points per round trip (as H-IVB1-NQ).

## 5. Nulls

- **N1 stale-value placebo:**
  - The identical rule using the value area of session **d−k** for k = 2 … 20 instead of d−1 (**19 placebos**).
  - If yesterday's value matters, it must beat stale value.
  - p_stale = (1 + #{placebo mean R ≥ observed}) / (1 + 19).
- **N2 (reported):** the **traverse rate**, i.e. the share of trades that reach the target. Compared with Dalton's "flip of a coin" (≈ 50 %) and the popular "80 %".

## 6. Statistics

- **One stage:** the full period, **opened once**.
- **Primary:** mean net R per trade at S1 (unconditional rule, 11:30 deadline). Moving-block bootstrap (block 20, B = 2,000, seed 20261014), one-sided p.
- **Secondaries (BH q = 0.10):**
  - long only; short only;
  - **Dalton condition 1 (distance):** |open − nearest VA edge| ÷ VA width ≤ its median, using the trailing median of the previous 60 eligible days' setup values (no lookahead);
  - **Dalton condition 2 (narrow value):** d−1 VA width < the median VA width of the previous 20 eligible sessions;
  - **Dalton condition 3 (direction):** trade direction agrees with the sign of (d−1 RTH close − the RTH close 20 eligible sessions earlier);
  - per calendar year.
- **DSR family:** shared NQ family of **116 trials** (69 earlier + H-ORB30L-NQ 22 + H-VAR-NQ 25 = primary + long + short + 3 Dalton conditions + 19 placebos). The trial-Sharpe variance is computed over this hypothesis's own series.
- **Minimum sample:** ≥ 150 trades at S1, else INSUFFICIENT-N. Fewer days qualify (open outside value and accepted); the threshold is set before data.

## 7. Acceptance (all required for "research candidate")

1. Mean net S1 R > 0 **and** CI lower bound > 0.
2. p_stale ≤ 0.05.
3. **Stability:**
   - no year > 40 % of total net R;
   - ≥ 60 % of years positive;
   - long and short each ≥ 0.
4. DSR ≥ 0.95 (116 trials).
5. Median R ≥ 20 points.

**Verdict order:** INSUFFICIENT-N → REJECTED (S0 mean ≤ 0) → RESEARCH CANDIDATE → otherwise INCONCLUSIVE.
- **A Dalton-condition subgroup that is positive does NOT make the hypothesis pass.** It may only become a new pre-registration tested on new data.

## 8. Robustness (reported only)

- No deadline (signals all day).
- Acceptance = one inside period.
- Stop one quarter of the VA width beyond the re-entered VA edge (long: VAL − 0.25 × (VAH − VAL)).
- Target = d−1 POC.
- Excluding FOMC / CPI / NFP days.
- S0 / S2 costs.

**User-goal report:**
- winning days and months;
- the longest losing streak;
- $ per MNQ at a fixed $100 risk.

## 9. Code (after approval)

- `hvar_nq.py` + synthetic tests covering:
  - the d−1 VA;
  - the open-outside setup;
  - the two-inside-periods acceptance with the deadline;
  - the extreme stop;
  - the opposite-edge target;
  - the gap stop;
  - same-bar → stop;
  - the stale-VA placebo (19);
  - the Dalton subgroups without lookahead.
- Reuses `hivb1_nq.profile` / loaders read-only.
- Hashed before the run.
