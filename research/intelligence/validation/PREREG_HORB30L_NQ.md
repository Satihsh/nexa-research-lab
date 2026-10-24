# PRE-REGISTRATION H-ORB30L-NQ: 30-minute opening-range breakout, long only, on Nasdaq-100 futures

**Status: BINDING.**
- Approved by the user 2026-10-14: "approved, pre-register H-ORB30L-NQ and H-VAR-NQ".
- Written **before** any statistic of this rule has been computed.
- The NQ data was used by H-ORB-1 (a *5-min* range, both directions, 10R / EoD), H-IVB1-NQ and H-IM-NQ. This rule (30-min range, long only, 1R / 2R, 15:30 exit) has never been computed. All earlier trials are counted in the DSR family (§6).
- **Implementation and the run each need a separate user approval.**
- Inherits the discipline of `PREREG_HIVB1_NQ.md` except where stated.

## 1. Hypothesis, source, honest prior

**Source:** Matteo Conti, SRC-YT-081 (`yW6c0K8uGvw`, 33:46–50:13), ex-bank trader. He derives the rule from Gao, Han, Li & Zhou (2018, JFE), "Market intraday momentum": overnight information plus the first 30 minutes reveal a buyer/seller imbalance that carries through the day. His stated rule:
- **Range:** high / low of 09:30–10:00.
- **Entry:** "open a long if the price closes above the high of the range".
- **Stop:** "at the low of the range".
- **Take profit:** "a classic reward to risk ratio either between one or two"; he works the 1:1 example.
- **Time exit:** close at 15:30 if neither stop nor target is hit.
- **Long only:** shorts "work worse".
- **Sizing:** one contract while developing, then volatility targeting (fixed $ risk).

**Honest prior:**
- The paper's own last-30-minutes rule was REJECTED on this NQ sample (H-IM-NQ, the close reverses the day).
- H-ORB-1 (5-min range) was INCONCLUSIVE (+0.063 R, p 0.15).
- Long-only on an index that rose over 2023–2026 risks measuring market beta, so N2 (§5) is mandatory.

## 2. Data, clock, days

- **Data:** CME NQ, Databento `NQ.v.0` ohlcv-1m with volume, 2023-02-18 → 2026-10-10, sha `35d1c3f5…` (frozen; `nq_volume_convert.py` from DBN `bf5b20b4…`).
- **Clock:** America/New_York, DST-aware (`horb1_orb.utc_of`).
- **Days:** `horb1_orb.eligible_days` with the frozen US calendar; holidays and early closes excluded; the latest NY date excluded.
- A day with any missing 1-min bar in 09:30–09:59, or a missing 15:29 bar, is `missing` (counted, no trade).

## 3. Rule (exact; design choices marked **DC**)

1. **Range:** A = max high, B = min low of the 1-min bars 09:30–09:59.
2. **Breakout:**
   - The first **5-min candle** on the grid from 10:00 (10:00–10:04, 10:05–10:09, …) whose close (= close of its last 1-min bar) is **> A**.
   - **DC-1:** 5-min candles, as H-ORB-1 / H-IVB1-NQ; the source does not name the timeframe. 1-min closes are robustness.
   - A candle whose last 1-min bar is missing is skipped.
   - Closes below B do nothing (long only).
3. **Executability deadline (user constraint, declared before data):**
   - The breakout candle must close **by 11:30 ET** (≈ 23:30 MYT in US summer / 00:30 in winter).
   - Reason: the user can act only in the first ~2 hours.
   - The source's no-deadline version is robustness §8.
4. **Entry:**
   - At the **open of the next 1-min bar** after the breakout candle closes (**DC-2**: a market order placed on the close; cannot fill at the close itself).
   - R = entry − B.
   - **Cost floor:** skip if R < 10 points (S1 cost > 20 % of R), counted.
5. **Stop:**
   - B, intrabar on 1-min bars.
   - A bar opening at or below B fills at its open (gap).
6. **Target (primary): entry + 1R.**
   - Fills only when a 1-min bar trades ≥ 1 tick through (high ≥ target + 0.25), at the target price.
   - **Secondary:** entry + 2R (pre-declared; the source's other end).
7. **Same bar:** if one bar touches stop and target, assume **stop**. On the entry bar itself, only the stop is checked.
8. **Time exit:** close of the 15:29 bar (= 15:30), if neither stop nor target is hit.
9. **One trade per day.** No re-entry.
10. **Outcome** = (exit − entry − cost) ÷ R.

## 4. Costs (per round trip, NQ points)

| Level | Cost |
|---|---|
| S0 | 1.0 |
| **S1 (decides)** | 2.0 |
| S2 | 3.0 |

These are the same conservative levels as H-IVB1-NQ.

## 5. Nulls

- **N1 timing placebo:**
  - The identical rule (30-min range, 5-min breakout candles, entry next bar, 1R, exit 15:30) with the range anchored at **19 other times**:
    - every 30 min 02:30–08:00 ET (12);
    - 11:00–14:00 ET (7).
  - Breakout deadline = min(anchor + 2 h, 15:00).
  - p_tod = (1 + #{placebo mean R ≥ observed}) / (1 + 19).
- **N2 beta control (mandatory, long-only rule):**
  - On every eligible day, enter long at the **10:00 bar open** with the same stop (B), the same 1R target and the same 15:30 exit, without the breakout condition.
  - **The breakout condition must add value: primary mean R − N2 mean R > 0** (acceptance item 6).
- **N3:** buy-and-hold 10:00 open → 15:30 in points (reported).

## 6. Period and statistics

- **One stage:** the full period, **opened once**.
- **Primary statistic:** mean net R per trade at S1, 1R target, 11:30 deadline. Moving-block bootstrap over days (block 20, B = 2,000, seed 20261014), one-sided p.
- **Secondaries (BH q = 0.10):** the 2R target; per calendar year.
- **DSR family:** every series computed on this NQ dataset:
  - H-ORB-1 23 + H-IVB1-NQ 22 + H-IM-NQ 24 = 69;
  - H-ORB30L-NQ 22 (primary + 2R + 19 placebos + N2);
  - H-VAR-NQ 25 (see its pre-registration);
  - **= 116 trials.**
  - The trial-Sharpe variance is computed over this hypothesis's own series.
- **Minimum sample:** ≥ 200 trades at S1, else INSUFFICIENT-N.

## 7. Acceptance (all required for "research candidate", RESEARCH_GATE G4)

1. Mean net S1 R > 0 **and** 95 % CI lower bound > 0.
2. p_tod ≤ 0.05.
3. **Stability:**
   - no calendar year > 40 % of total net R;
   - ≥ 60 % of years positive.
4. DSR ≥ 0.95 (116 trials).
5. Median R ≥ 20 points (10 × S1 cost).
6. Primary mean R − N2 mean R > 0.

**Verdict order:** INSUFFICIENT-N → REJECTED (S0 mean ≤ 0) → RESEARCH CANDIDATE (all pass) → otherwise INCONCLUSIVE. No re-run with altered parameters under H-ORB30L-NQ.

## 8. Robustness (reported only; never selected)

- No deadline (the source's full-day rule).
- Breakout on 1-min closes.
- Time exit 15:59.
- Short-side mirror (the source says it is worse).
- Excluding FOMC / CPI / NFP days.
- S0 / S2 costs.

**User-goal report (descriptive, no acceptance role):**
- the share of winning trading days and of winning months;
- the longest losing streak;
- **$ per MNQ** at a fixed $100 risk per trade (volatility-targeted contract count, rounded down, min 1).

## 9. Code (after approval)

- `horb30l_nq.py` + tests (synthetic bars) covering:
  - the range;
  - the 5-min breakout with the deadline;
  - next-bar entry;
  - the gap stop;
  - the 1-tick target fill;
  - same-bar → stop;
  - the 15:29 exit;
  - the cost floor;
  - N2;
  - the placebo count (19).
- Reuses `horb1_orb` / `hivb1_nq` loaders and calendar and `of_common` statistics, read-only.
- Hashed before the run.

**If it passes:**
- An ATAS alert with a bracket order: buy stop / market at the 5-min close, stop at B, target 1R.
- Then a parity test → forward demo → at most one prop evaluation (user constraint: $0 until proven).
