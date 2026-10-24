# PRE-REGISTRATION OFC1: the user's core order-flow method on CME futures (Setups A, B and mirrors)

**Status: BINDING.**
- Approved by the user 2026-10-11: "Approved, buy 6J, 6B, GC and pre-register".
- Written before any OFC1 outcome is computed. Its SHA-256 goes into `PREREG_HASHES.txt` now.
- The code hashes are added **before discovery is opened**. Implementation and the run need separate user approval.
- Rules come from `orderflow/CORE_STRATEGY_SPEC.md`. **Every element was decided by the user** (E1–E12, E5b, window, venue, costs; 2026-10-11) or is from the user's notes / cited sources.
- §11 lists the implementation details fixed here, which the user has not individually reviewed. The user may change any of them **before the code is hashed**, as a numbered deviation; nothing after.
- Statistics, bootstrap conventions and verdict structure follow `PREREG_OF_COMMON.md` §C8 and `PREREG_C1_TOKYO_FIX.md` unless stated here.

## 1. Hypothesis, source and disclosure

**Claim:**
- The user's discretionary method (notes, NOTE-001; source video YT-001 Vishaal Fx; practitioner family B3 P1/P4/P5) earns a positive net expectancy on CME FX and gold futures.
- **The method:** at the prior NY session's value-area edges, a big aggressive order near the edge, confirmed by footprint order flow, gives a reversal back through value (Setup A and its mirror) or a continuation to the next low-volume node (Setup B and its mirror).

**Prior:**
- No peer-reviewed or audited test of any such rule exists (B1, CL-101).
- About 97 % of persistent discretionary day traders lose (B1 §7b).
- The method's own best evidence is practitioner contest placings (B3), not rules.

**Disclosure (seen data):** descriptive measurements only.
- **What was measured** (CL-103…115; `orderflow/databento/*.json`):
  - 6E trade-size distributions, basis, VA widths and profile agreement (13 months);
  - counts of big trades near VA edges and LVNs per profile (6E, all 13 months).
- **E2 (10 %) and E9 (depth ≤ 50 %)** were chosen by the user after seeing those 6E **counts**.
- **Never computed:** no price path after any event, no trade, no return.
- **6J / 6B / GC:** not yet seen.

## 2. Data

- **Source:** Databento `GLBX.MDP3` trades (aggressor side), continuous front month by volume `X.v.0` for 6E, 6J, 6B, GC, 2025-09-01 → 2026-10-01 (UTC).
  - 6E is on hand.
  - 6J/6B/GC need the approved purchase (USD 55.633).
  - **If any instrument cannot be obtained, OFC1 runs on the instruments available and states it.** Acceptance criterion §7.6 then applies to those available.
- **Session:** CME trading day = server day d (17:00 NY of d−1 → 17:00 NY of d; clock NY+7, as in COMMON §C3).
- **Session exclusions (counted, as in `year_6e_analysis.py`):**
  - the first session of the data;
  - thin sessions (< 80 % of the median count of minutes with trades);
  - sessions touching a Databento `degraded` UTC date (`dataset_condition_*.json`; a session spans UTC dates d−1 and d);
  - **roll sessions**, where the prior session's dominant instrument_id ≠ this session's.
- **Instrument constants** (CME specs; tick verified at implementation as the minimum positive price difference in the data, else a deviation is recorded):

| Instrument | Tick | USD per tick | Profile row W (from the frozen `of_common.BINW` spot row mapped to futures) |
|---|---|---|---|
| 6E | 0.00005 | 6.25 | 0.0001 (2 ticks) |
| 6B | 0.0001 | 6.25 | 0.0001 (1 tick) |
| 6J | 0.0000005 | 6.25 | 0.0000005 (1 tick ≈ 1 spot pip at USDJPY 150) |
| GC | 0.10 | 10.00 | 1.0 (10 ticks) |

## 3. Definitions (user decisions; §11 has implementation details)

1. **Value (E1):**
   - the prior session's **NY block** (08:30–17:00 NY) volume profile in rows of W;
   - POC / VAL / VAH by `of_common.va_greedy` (70 %);
   - VA width = VAH − VAL.
2. **LVN (E9):**
   - in that profile (no smoothing), row i is an LVN if v[i] < v[i−1], v[i] ≤ v[i+1], and v[i] ≤ 0.5 · min(max v[<i], max v[>i]);
   - LVN price = the row midpoint.
3. **Aggressor order and big trade (E3):**
   - trades of the session's instrument aggregated by (instrument_id, ts_event, side);
   - big = size ≥ ceil(q99) of the same block's orders over the prior 60 valid sessions (`orderflow/databento/big_trades.py`);
   - blocks: Asia 18:00 NY → 08:00 London; London → 08:30 NY; NY → 17:00 NY.
   - Sessions without 60 prior valid sessions are warm-up (not scored).
4. **Bubble near the edge (E2):**
   - seller bubble = a big order with side `A` (sell aggressor) whose lowest execution price pmin satisfies |pmin − VAL| ≤ 0.10 · VA width;
   - buyer bubble (mirror) = side `B` with |pmax − VAH| ≤ 0.10 · VA width;
   - bubble_low = pmin, bubble_high = pmax.
5. **1-min candles:**
   - from trades by ts_event minute (NY clock): open/high/low/close = first/max/min/last trade price, volume = Σ size;
   - delta = Σ size(side B) − Σ size(side A); side `N` counts in volume only.
6. **Footprint imbalance (E4):** on a candle, per tick price p:
   - **buy imbalance** at p if AskVol(p) ≥ 3 · BidVol(p − 1 tick), AskVol(p) ≥ 10, and BidVol(p − 1 tick) ≥ 1;
   - **sell imbalance** at p if BidVol(p) ≥ 3 · AskVol(p + 1 tick), BidVol(p) ≥ 10, and AskVol(p + 1 tick) ≥ 1;
   - AskVol = side B volume, BidVol = side A volume;
   - a **stack** = ≥ 3 consecutive tick prices with the same-side imbalance.
7. **Confirmation (E4/E5/E5b):**
   - **long confirmation** = ≥ 1 buy stack, delta > 0, and volume > baseline;
   - **short confirmation** = ≥ 1 sell stack, delta < 0, and volume > baseline;
   - **baseline** = the mean volume of the same NY clock minute over the prior 20 valid sessions (zero if no trades in that minute).

## 4. Trading rules (exact)

**Trading window:** 18:00 NY of d−1 → 17:00 NY of d. Flat at 17:00 NY (E11). **One open position per instrument; re-entry after exit.**

**Pending setups:**
- Each instrument holds at most one **low-side pending** (from the most recent seller bubble near VAL) and one **high-side pending** (from the most recent buyer bubble near VAH).
- A bubble creates or replaces its side's pending only if the **context** holds: the close of the last completed 1-min candle before the bubble's minute is inside [VAL, VAH].
- Pendings are cleared when a position opens, and at 17:00 NY.

**For each completed 1-min candle**, starting with the bubble's own minute, and only when flat:

| Pending | Candle close | Action |
|---|---|---|
| Low side | < min(bubble_low, VAL) | **Setup B (short)** if short confirmation holds, an LVN exists below VAL **and** below the entry price (target = the highest such LVN), and the cost floor passes. The low-side pending ends either way |
| Low side | < bubble_low but ≥ VAL | Setup A is **invalidated**. The pending stays for B only |
| Low side | > bubble_high and A still valid | **Setup A (long)** if long confirmation holds and VAH > entry; target = VAH. Otherwise the pending stays |
| High side (mirror) | > max(bubble_high, VAH) | **Setup B′ (long)**: long confirmation, target = the lowest LVN above VAH and above the entry price; none ⇒ no trade. The pending ends |
| High side | > bubble_high but ≤ VAH | A′ invalidated; the pending stays for B′ |
| High side | < bubble_low and A′ still valid | **Setup A′ (short)**: short confirmation; target = VAL |

If both pendings trigger on the same candle, the low-side pending is evaluated first.

**Entry:** the trigger candle's close + 1 tick adverse slippage.

**Stop (E6/E7):**
- A / B′ long: bubble_low − 1 tick;
- B / A′ short: bubble_high + 1 tick.
- If the stop is on the wrong side of the entry, there is no trade.

**Exits:** processed trade by trade after the trigger minute.
- **Stop:** the first trade at or beyond the stop fills at that trade's price + 1 tick adverse.
- **Target:** the first trade strictly beyond the target fills at the target.
- **Time:** at 17:00 NY, exit at the last trade price before 17:00 + 1 tick adverse.
- The first event in trade sequence wins.

## 5. Costs

- **S0 (decides):**
  - fees USD 2.61 per side (6E/6J/6B: exchange 1.60 + NFA 0.01 + broker 1.00 assumed) or USD 2.66 (GC);
  - slippage of 1 tick on entry and on stop and time exits (§4); none on target fills.
- **S1 (reported):** S0 + 1 further tick on entry and on stop and time exits.
- **Cost floor (COMMON §C7, as in CORE_STRATEGY_SPEC D8):** skip a trade *ex ante* if (round-trip fees + 2 ticks) > 0.20 × the initial risk (|entry fill − stop| × USD per point). Skips are counted and reported.
- **R** = net USD P&L per contract / initial risk USD.

## 6. Benchmarks, nulls, splits, statistics

**Benchmarks and nulls:**
- **N0:** zero.
- **N1 (timing placebo):** for every executed trade, 200 draws with the same instrument, session, direction and stop/target distances in ticks, and the same cost model. The entry minute is drawn uniformly from the session's trading-window minutes that leave at least 1 minute before 17:00 NY.
  - p_N1 = (1 + #{draw means ≥ observed mean}) / 201.
  - Seed 20261011.
- **N2 (does order flow add value?):** the identical state machine **without** the confirmation checks (§3.7).
  - Δ = mean R(OFC1) − mean R(N2), using a paired session-block bootstrap.

**Splits (calendar, all instruments):**
- discovery 2025-12-01 → 2026-04-30;
- validation 2026-05-01 → 2026-07-31;
- holdout 2026-08-01 → 2026-09-30;
- each opened once, in order.
- Earlier sessions are warm-up only. No data after 2026-10-01; no 2027 data.

**Minimum samples:**
- pooled P1 ≥ 150 trades and holdout ≥ 30;
- otherwise **INSUFFICIENT-N** (no verdict).

**Power (reported, not assumed):**
- σ_R is estimated on discovery only.
- For each split, the minimum detectable mean R at 80 % power is reported (≈ 2.5 σ_R / √N).
- **Before data:** with σ_R ≈ 1.0–1.5 and N = 150 the MDE is ≈ 0.20–0.31 R per trade, so **only a large edge is detectable** in 10 scored months.
- The cost of more history is in B5; extending the window needs a **deviation before discovery opens**, plus purchase approval.

**Uncertainty:** moving-block bootstrap over sessions (block = 5 sessions; B = 2,000; seed 20261011). One-sided p as in COMMON §C8.

**Multiplicity:**
- primary **P1** = all four setups, all instruments, pooled;
- secondaries (BH q = 0.10 within the family): setups A, B, A′, B′ (instruments pooled); instruments 6E, 6J, 6B, GC (setups pooled); the N2 contrast Δ;
- **DSR** via `nexa_robust.deflated_sharpe`, n_trials = 10.

## 7. Acceptance criteria (all required for "research candidate", RESEARCH_GATE G4)

1. **Discovery:** P1 net (S0) mean R > 0 with one-sided p < 0.05.
2. **Validation and holdout:** P1 net (S0) point estimates > 0.
3. **Pooled:** the 95 % CI lower bound of the P1 net (S0) mean R > 0. S1 is reported.
4. **Timing placebo:** p_N1 ≤ 0.05 (pooled).
5. **Order-flow value:** the pooled point estimate of Δ (OFC1 − N2) > 0. Its CI is reported.
6. **Stability:**
   - ≥ 3 of 4 instruments (or all but one of those available) have a positive net mean R;
   - no instrument > 60 % of pooled net R;
   - no calendar month > 35 % of pooled net R.
7. **DSR** ≥ 0.95 at n_trials = 10.

**Verdicts:**
- **REJECTED** if the pooled P1 net (S0) mean ≤ 0, or the discovery and holdout signs are opposite.
- **INSUFFICIENT-N** per §6.
- **INCONCLUSIVE** otherwise.
- **No re-run with altered rules under this ID.** A negative result is preserved in the KB and FAILED_IDEAS.

## 8. Robustness (reported only; never changes the verdict)

- Cost floor off.
- Imbalance as NinjaTrader's min-delta form (AskVol(p) − BidVol(p−1) ≥ 10).
- E2 at 5 % / 20 %.
- First bubble instead of most recent.
- Stack ≥ 2.
- Per block (Asia / London / NY) and per setup × instrument.
- Exits evaluated on 1-min closes instead of trade by trade.

## 9. Code (thin; reused where possible)

- **Reused:** `orderflow/databento/big_trades.py` (session blocks, thresholds); `of_common.py` (`va_greedy`, `bh`, bootstrap conventions); `nexa_robust.deflated_sharpe` (read-only).
- **New:** `validation/ofc1_core.py` (profiles, LVNs, candles, footprint, state machine, exits, costs, nulls).
- **Unit tests** (`validation/test_ofc1.py`): synthetic sessions for each setup path (trigger, invalidation, B with and without LVN, mirrors), the imbalance and stack rules, stop/target/time exits in trade order, cost arithmetic and the cost floor, and the warm-up and roll skips.
- Code and test hashes are recorded **before discovery opens**.

## 10. Unresolved assumptions

| # | Item | Effect |
|---|---|---|
| U1 | **CME evaluation ≠ Pepperstone execution** (user's venue choice) | A positive result is not yet tradable at Pepperstone. Mapping error p95 2.2 pips (CL-108); the proxy cannot substitute (CL-109) |
| U2 | Broker commission USD 1.00/side is an assumption | ±0.16 tick per side on 6E |
| U3 | Continuous `v.0` (volume roll); roll sessions skipped | Fewer sessions near expiries |
| U4 | Bubble = one aggressor order (timestamp + side), not a millisecond-window aggregation (GAP-K11) | Platform bubbles may be larger and rarer |
| U5 | Candles and footprints from trades only (no quotes); the close is the last trade | Standard for footprints; entry fills are modelled with slippage |
| U6 | Only 10 scored months; a single regime | Low power (§6). A rejection or inconclusive result says little about longer periods |
| U7 | The user's original method uses DeepCharts visuals (bubble scaling, Valleys sensitivity) that are undocumented | The rules are the user-approved translation, not an exact replica |

## 11. Implementation clarifications (fixed before any outcome; changeable by the user only before the code hash)

1. **Trigger timing:** the bubble's own 1-min candle may be the trigger candle.
2. **Context** is checked once, at the bubble, against the last completed candle before the bubble's minute. If there is no earlier candle in the session, there is no pending.
3. **A non-confirmed Setup A trigger** keeps the pending (a later candle may confirm). A non-confirmed Setup B break ends it.
4. **The B (B′) target** is the nearest LVN beyond the edge that is also beyond the entry fill. If none, no trade, and the pending ends.
5. **Setup A also needs VAH > entry fill** (A′: VAL < entry fill). Otherwise no trade, and the pending stays.
6. **While a position is open,** no pendings are tracked. After an exit, new bubbles are needed.
7. **The volume baseline** uses the NY clock minute. The prior 20 valid sessions include warm-up sessions but not excluded ones.
8. **Big-trade history** uses valid sessions only (excluded sessions count neither as history nor as scored).
9. **Calendar month** for §7.6 = the NY date of the entry.
