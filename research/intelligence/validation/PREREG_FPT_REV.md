# PRE-REGISTRATION H-FPT-REV: JJ Simon "fair-pricing" reversion to the 09:30 open (NQ primary, ES transfer; QuantConnect)

**Status: BINDING.**
- User approval 2026-10-18: "Pre-register JJ Simon's reversion".
- **Written before any data was read for this hypothesis.** No statistic of this rule has been computed on any data.

**Source:**
- JJ Simon, Chart Fanatics, "STEAL The 1-Minute Strategy That Made Him $1.8M+" (`KHEQ5g55dQ4`, 2026-10-04). SRC-YT-113; claims CL-155 (reversion) and CL-156 (opening continuation).
- Line references are to `../video_batch_2026-10-18b/KHEQ5g55dQ4.txt`.

**Prior:** low to moderate.
- Intraday reversion rules tested so far lost money:
  - T2a −0.045R;
  - OFC1 −0.21R.
- But the anchor (the 09:30 open) and the window (the first 90 minutes) are untested.

**Link to H-PROP-EV** (`PROP_EV_REPORT.md`): a strategy needs **≥ +0.025R net per trade** before an Apex 50K evaluation at list price is even break-even. That threshold is reported against, without changing the verdict rule.

**Not tuned.** Every number is from the source, from an earlier NEXA pre-registration, or fixed here with a stated reason.

## 1. Data, valid days
- **Instruments:**
  - QuantConnect AlgoSeek continuous futures;
  - front month by open interest (`DataMappingMode.OPEN_INTEREST`), `DataNormalizationMode.BACKWARDS_RATIO`;
  - minute trade bars; clock America/New_York; tick 0.25.
  - **NQ primary** (the source trades NQ only); **ES transfer**.
- **Extended hours are subscribed** only for the secondary V-OPEN inputs (§5). Everything else uses the 390 RTH bars 09:30–15:59.
- **Period:**
  - **2010-01-04 → the last complete trading day available at run time**;
  - warm-up from 2009-12-01;
  - one run per instrument; each run once.
- **A day d is valid if:**
  1. all 390 RTH minute bars exist;
  2. no contract-mapping change occurred between the previous valid day and d (roll days excluded and counted);
  3. at least 20 prior valid days exist (for RNG20, §2).

## 2. Scale: the source's fixed points, carried across 16 years
- The source's numbers (stop 25, target 38, NQ points) are calibrated to NQ ≈ 18,000–25,000 (his trading period, ~2025-04 → 2026-10).
- NQ was ≈ 1,800 in 2010. A fixed 25-point stop then was a different trade. So the primary scales the bracket by **volatility**:
  - **RNG(d)** = high − low of the minute bars 09:30–10:59 on day d (the source's 90-minute window);
  - **RNG20(d)** = mean RNG over the 20 prior valid days (not including d);
  - **REF** = mean RNG over all NQ valid days from **2025-04-01** to the end of the sample (the source's own period). This is a scale constant only. It uses ranges, never trade outcomes.
  - **F = 25 / REF.**
  - **Stop distance s(d) = max(F · RNG20(d), 1.0 point)**; **target distance t(d) = 1.52 · s(d)** (= 38/25).
  - On average this gives ≈ 25 / 38 NQ points in the source's period.
- **ES run:** uses the same F, taken from the NQ run's logged value (`NEXA_FPT_F`) and written into the ES file before the ES run. This is the only other line that differs, besides MODE. The stop is then the same fraction of ES's own opening-range scale.

## 3. Primary rule P (reversion toward the 09:30 open)
- **Fair price** FP = the open of the 09:30 bar.
  - *Not used:* the source's news-day override (the pre-08:30 price on CPI/PPI days) and the "new consolidation after unexpected news". The second is not mechanisable; the first is a separate hypothesis (H-NEWS-REV).
- **Bars** are 1-minute RTH bars indexed k = 0 (09:30) … 389 (15:59).
- **Direction at a signal bar i:** dir = −1 (short) if close c[i] > FP; +1 (long) if c[i] < FP; none if equal.
- **Entry triggers** (bar close confirmed; source [018–034, 063, 192–252]). A signal exists at bar i if either holds in the trade direction:
  - **Displacement:** bar i−1 has the opposite colour to the trade; bar i has the trade's colour (short: c < o; long: c > o); |c[i] − o[i]| > |c[i−1] − o[i−1]|; and c[i] closes beyond bar i−1's wick (short: c[i] < low[i−1]; long: c[i] > high[i−1]).
  - **Break of structure (BOS):** a *fractal low* is bar j with low[j] < low[j−1] and low[j] < low[j+1]; it is confirmed at bar j+1's close. The *active* fractal low is the most recent confirmed one that no close has gone below. A short BOS signal is c[i] < active fractal low, which then becomes consumed (no active low until a new one confirms). Fractal highs and long signals mirror this. Fractals form from k ≥ 1 (bar 0 may be a neighbour), and the state is tracked through the whole window, including while a position is open.
- **Distance filter (source's 80 % rule [281–288]):** |c[i] − FP| ≥ 0.8 · t(d).
- **Window:** signal bars i = 1 … 88 (09:31 … 10:58). Entry is at the **open of bar i+1** (no same-bar fill), so the latest entry is 10:59.
- **Bracket** (static, source's evaluation rule [028–040]):
  - stop = entry − dir·s(d);
  - target = entry + dir·t(d);
  - checked on each minute's high/low from the entry bar; **if both are touched in one minute, the stop counts first**;
  - otherwise exit at the 15:59 close (prop rule: flat by the close).
- **One position at a time.** After an exit at bar x, signals are taken only from bars i > x.
- **Session stop:** after **3 consecutive losing trades** in the day (net R < 0), no more entries [118–119, 139–141].
- **Costs (round trip, points; as PREREG_CFT §4):**
  - NQ: S0 = 1, **S1 = 2**, S2 = 3;
  - ES: S0 = 0.30, **S1 = 0.60**, S2 = 1.20.
- **Net R = (dir·(exit − entry) − cost) / s(d).**

## 4. Statistics and verdict (as PREREG_T2A §5)
- **Primary statistic:** mean net R per trade at S1, NQ, rule P.
- **Inference:**
  - moving-block bootstrap over the chronological sequence of valid days (block 20, B = 2,000, **seed 20261018**);
  - each replicate = Σ R ÷ the number of trades on the resampled days;
  - 95 % percentile CI; one-sided p.
- **Stability:** 4 equal consecutive blocks of valid days.
- **Verdicts:**
  - **VALIDATED (G4):** mean > 0, CI lower bound > 0, ≥ 3/4 blocks > 0, ≥ 300 trades;
  - **REJECTED:** mean ≤ 0;
  - **INCONCLUSIVE:** otherwise;
  - **INSUFFICIENT-N:** < 300 trades.
- **Driftless reference hit rate:** 1/2.52 = 0.397.
- **Reported (no verdict effect):**
  - trades, trades per day; hit rate vs 0.397; payoff;
  - S0 / S2 means; long vs short; displacement- vs BOS-triggered means; time-exit share;
  - mean s(d) in points; per-year means;
  - green-day share of trading days; maximum drawdown in R; daily Sharpe;
  - the longest losing streak;
  - **the mean vs the +0.025R prop threshold.**

## 5. Declared secondary variants (same run; reported, never substituted)
- **V-FIX:** rule P with the source's literal fixed **25 / 38 points** (NQ only), restricted to **2023-01-03 → end** (NQ ≈ 11,000–25,000).
- **V-NO80:** rule P without the distance filter.
- **V-OPEN (CL-156, opening continuation)**, its own trade stream, independent of P:
  - **Direction** = the colour of the 09:30 bar (doji → no trade).
  - It must "break structure of the previous candles" [015–016]: long if c[0] > max(high of the 09:25–09:29 bars), short if c[0] < min(low of the 09:25–09:29 bars). Missing pre-market bars → no trade.
  - **Higher-timeframe filter** [014, 021] ("inverting whatever happened for the previous 6–12 hours"): the trade direction must be **opposite** the sign of (09:30 open − the last close in 21:00–21:29 ET of the previous calendar day). Missing or zero → no trade.
  - **Entry** at bar 1's open. Bracket s(d) / t(d). If the 09:30 bar's range > s(d), the source halves size and doubles distances [016]: in R terms, 2·s and 2·t. Exit as in P. One trade per day.
- **ES:** P, V-NO80 and V-OPEN as transfer tests, with the same criteria.

## 6. Multiple testing
- H-FPT-REV counts as **7 trials:** NQ {P, V-FIX, V-NO80, V-OPEN} + ES {P, V-NO80, V-OPEN}.
- Cumulative NEXA ledger before this test: ~150 (T1_T2A_REPORT). Report the descriptive DSR of the NQ primary at 7 and at ~157 trials.

## 7. Code, freeze, use
- Algorithm: `qc_fpt/main.py` (MODE ∈ {NQ, ES}; the ES file additionally carries F from the NQ log).
- Unit tests `test_fpt.py` run on synthetic days:
  1. displacement definition;
  2. fractal confirmation / break / consumption;
  3. direction toward the fair price and the 80 % filter;
  4. next-bar entry and stop-first tie;
  5. the 3-consecutive-loss session stop;
  6. the one-position rule;
  7. V-OPEN structure / HTF filter / doubled distances;
  8. scale F and the RNG20 warm-up.
- They must pass before the code is hashed into PREREG_HASHES.txt.
- The QC editor hash is verified before each run (as T1/T2a). Output: `NEXA_FPT_RESULT` JSON in the log.
- **No live or paper trading follows from a single result.**
  - A VALIDATED NQ primary would next need a forward paper check (and a pre-registered news-day variant).
  - Only after that a re-run of H-PROP-EV with the measured R distribution.
  - No evaluation purchase follows from this test (user rule: $0 until an edge is proven).
