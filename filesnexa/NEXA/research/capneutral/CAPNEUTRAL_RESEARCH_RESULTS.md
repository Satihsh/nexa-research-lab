# CAP-NEUTRAL RESEARCH — NOT PRODUCTION CONFIGURATION

## NEXA cap-neutral tester campaign: A4 results (2026-10-03)

**Scope:**
- The 48 verified tester runs of B-EXPOSURE-CAP option B: EURUSD, GBPUSD, USDJPY and XAUUSD, 2024-01-01 → 2026-09-26.
- The cap was made inert with `InpMaxSameCurrencyNet=10000`; every other frozen control was unchanged.
- **This is a measurement of the implemented EA, with the defect D-PARTIAL-AFTER-BE present (§3).** It is not the specified EA, not the production cap configuration, and not out-of-sample.

**Plan:**
- Plan: `CAPNEUTRAL_RESEARCH_PLAN.md`, sha256 `5692577d…` as recorded at 05:07:25 UTC, before any campaign result was opened.
- Amendment 1 covers the net-R definition and the disk/swap gates. Amendment 2 covers the defect, the ceiling and the $200 replay alignment.

**Code and outputs:**
- `capn_analysis.py` `b236f77e…` and its tests `test_capn_analysis.py` `2ae14d04…` (32 tests).
- Outputs in `results/`, chiefly `capn_results.json` `f38b33af…`.

**Evidence labels used throughout:**
- **OBSERVED:** read directly from the records.
- **FORMAL:** the pre-registered test, giving a verdict.
- **EXPLORATORY:** not justified by the frozen protocol; no verdict.
- **INFERENCE:** reasoning beyond the records.
- **ENGINEERING DEFECT:** an implementation fault.

---

## Summary

| Question | Answer | Basis |
|---|---|---|
| Does NEXA's rule set have an edge? | **No.** Net expectancy **−0.318R per trade**, 95 % CI [−0.384, −0.250], over 1,902 trades. Gate 8 verdict: **NEGATIVE_EXPECTANCY**. | FORMAL |
| Is the loss a cost problem only? | **No.** It is already −0.072R per trade *before* commission. Commission ($7.00 per lot round trip) adds −0.245R, because NEXA's stops are tiny (median EURUSD stop 2.4 pips). | OBSERVED |
| +24.5 %/day objective | **CONTRADICTED** for the tested configuration. It is arithmetically unreachable (ceiling +12.67 %/day) and observed on 0 of 3,125 symbol-days. The best day was +3.15 %. | OBSERVED + arithmetic |
| $200 feasibility | 0 of 140 twenty-day cycles reached the target path. FX is executable at $200; most gold trades are not (minimum lot exceeds the 1 % ceiling). | replay (not broker-executed) |
| EA engineering | One defect: no partial close or time exit after breakeven. Its estimated effect is about −0.008R per trade, immaterial to the verdict. Plus two observations: the survival pause, and the stop-rounding risk overshoot. | ENGINEERING DEFECT / OBSERVED |
| Change the production exposure cap? | **Not justified.** With no edge, lifting the cap would only let NEXA lose money faster. | INFERENCE |

---

## 1. Campaign integrity (all checks re-run inside `capn_analysis.py`)

| Check | Result |
|---|---|
| Runs verified (`VERIFIED_PASS`) | **48 / 48** |
| Per-run gate 1: "Test passed" inside the run's own time window | 48 / 48 |
| Per-run gate 2: Trade DNA covers the window (last decision ≥ window end − 4 days) | 48 / 48 |
| Per-run gate 3: all 64 logged inputs equal the source defaults, except `InpMaxSameCurrencyNet=10000` | 48 / 48 (no gate failures) |
| Per-run gate 4: zero `PORTFOLIO_CURRENCY_EXPOSURE_CAP` blocks | 48 / 48 |
| Smoke chunk reused | `CAPN_NEXA_USDJPY_A2026Q1` (started 2026-10-03 02:32:46, marker "smoke passed … closes=127"); the full batch skipped it as verified |
| Retries | 1: `FAILEDRUN_CAPN_NEXA_USDJPY_A2024Q4_try1` (no "Test passed", a random tester death); attempt 2 verified |
| Balance reconciliation (deals + CLOSE commission and swap = tester final balance) | **48 / 48**, max \|difference\| $0.012 (rounding) |
| Net-R P&L sum (Trade DNA) = tester final balance | 48 / 48, max \|difference\| $0.012 |
| Deal count = 2 × trades in every run | yes (3,804 deals, 1,902 trades) |
| Trade DNA SHA256 (`SHA256SUMS` `354b045f…`) | 48 / 48 files match |
| `NEXA_Risk.mqh` / `NEXA_EA.mq5` / `build/NEXA_EA.ex5` | `7fd5692a…` / `d65090cc…` / `91ee5e20…`: **unchanged** |
| Research EA `Experts\NEXA_Research\NEXA_EA_CAPN.ex5` | = `91ee5e20…` |
| Deployed `Experts\Advisors\NEXA_EA.ex5` | `f0ae9618…`: **unchanged** |
| V2 registry | 7 entries, head seq 6 = off-machine record `bbd9a28e…`: **untouched** |
| 8E registry | 2,171 entries, head seq 2170 = off-machine record `9f7249a2…` (REJECTED): **untouched** |

**OBSERVED, overlapping positions:** two runs each contain one new order dispatched before the previous position's CLOSE row; the positions closed and filled within the same minute. Trades are paired by exact volume and direction, and ambiguous cases raise an error. Both runs pair unambiguously.

---

## 2. Methodology (as pre-registered; deviations disclosed)

**Unit of analysis.** Each resolved trade is an OPEN → FILL → CLOSE sequence in the Trade DNA. There were no partial closes (§3).

**Net R** (plan §7A, amendment 1):
`net_R = realised_pnl_usd / initial_risk_usd`
- `realised_pnl_usd` = the sum over exit legs of `direction × (exit − actual fill) × lots × contract value`, plus the CLOSE row's commission and swap. USDJPY profit is converted at the exit rate.
- `initial_risk_usd` = OPEN lots × `risk_dist` (the placed stop distance) × contract value. USDJPY risk is converted at the intended entry.
- This reproduces every run's tester balance to the cent.
- The DNA's `result_r` (gross R from the *intended* entry, excluding entry slippage, commission and swap) is reported as "gross" only and never reaches Gate 8.

**Formal test.**
- `nexa_stats.evaluate` (Gate 8, unchanged code) with `StatsConfig(min_trades=200, block=10)`, pooled across symbols in entry-time order.
- Secondary views: iid bootstrap; per symbol, with Benjamini–Hochberg at q = 0.10.
- Also reported: an extra +0.15R stress test, and PSR (equal to DSR at the honest trial count of 1).

**Capital.**
- Daily return = realised balance change by server day ÷ the day's starting balance. Each run is its own $50,000 account, reset at every chunk; days without trades count as 0 %.
- The 20-trading-day cycles are non-overlapping and stay within a chunk.

**$200 replay.** Amendment 2 disclosed this before results were opened. It runs (a) NEXA's own sizing rule, (b) the same rule without the lot grid (theoretical), and (c) the pre-registered 8E simulator at 0.30 % risk. The broker volume grid comes from the spec probe, plus `contracts.json` for USDJPY.

**Not done:**
- No portfolio sum across the four runs (it would break the account-wide limits).
- No re-run of any campaign, no simulated alternative EA, and no new selection rule.

---

## 3. ENGINEERING DEFECT D-PARTIAL-AFTER-BE (disclosed before results; not repaired)

| | Behaviour |
|---|---|
| **Implemented (tested)** | At +1.0R the stop moves to exactly the entry price. `ManageOpenPosition` then computes `risk = |open − sl| = 0` and returns early. So the **1.5R partial close (50 %)** fires only if price jumps from below 1.0R to at least 1.5R within a single management pass, and the **48-bar time exit** is never checked for a trade at breakeven. Each trade exits in full at the stop, breakeven, take-profit (1.5R–4.0R), time exit (only if breakeven was never reached), the Friday close or the chunk end. |
| **Intended (specification)** | 50 % closed at +1.5R, the remainder managed to take-profit or breakeven, and the time exit active for the whole trade. |
| **Evidence** | 0 PARTIAL_CLOSE rows; deals = 2 × trades in all 48 runs (3,804 / 1,902). |

### Impact (D): counts from existing records

The excursion counts are approximate: they use the bid M1 bars exported from the same tester data, which the generated-tick model is built on.

| Measure | Trades |
|---|---|
| Reached ≥ +1.0R (breakeven territory) | **850** (44.7 %) |
| Reached ≥ +1.5R (partial-close territory) | **552** (29.0 %): exited at take-profit 317, breakeven 183, other 50, stop 2 |
| Exited at breakeven | 425 |
| Held more than 48 bars | 219 |
| Time exit blocked after breakeven (breakeven before bar 48, still open at bar 48, r < 0.3 at bar 48) | **8** |

**INFERENCE (magnitude bound, not campaign evidence):** if, for the 552 trades that reached +1.5R, half the position had been banked at +1.5R instead of its implemented exit:
- breakeven and other exits would have gained **+178.6R**;
- take-profit exits would have lost **−192.9R**;
- net **−14.3R**, i.e. **−0.008R per trade**.

This arithmetic ignores lot rounding, the time exit and any change to later decisions (for example the survival pause, §5.11). **The exact counterfactual cannot be established from the records**, and nothing was simulated or run to establish it. The bound is about 40 times smaller than the measured −0.318R expectancy, so the defect cannot plausibly change the edge verdict. The 8 blocked time exits are likewise too few to matter.

---

## 4. Daily-return ceiling (amendment 2, derived before results)

| Input | Value |
|---|---|
| Risk per trade (`InpRiskPercent`, rounded down) | r ≤ 0.30 % of current equity |
| Best implemented exit (`targetR = min(anchorR, InpMaxTP_R)`) | ≤ 4.0R (full take-profit; no partial) |
| Trades per day (`InpMaxTradesPerDay`, account-wide) | ≤ 10 |

- **Best possible trade:** a +4.0R win at 0.30 % risk multiplies equity by at most 1 + 0.003 × 4.0 = 1.012. Wins compound on current equity.
- **Implemented ceiling:** 1.012^10 − 1 = **+12.6692 %** per day, before costs.
  - The intended specification (2.75R best case) would give +8.5631 %. The earlier plan figure was based on that and was wrong for the implemented EA.
  - The formal 1 %-ceiling bound is +48.02 %, but only via the minimum-lot path, which is not a practical route at $50,000.
- **Trades needed for +24.5 %:** ln 1.245 / ln 1.012 = **18.37** consecutive maximum wins, against a cap of 10. **+24.5 % is unreachable on any day under the frozen controls, whatever the edge.**

---

## 5. Results

### 5.1 Edge / expectancy: FORMAL STATISTICAL RESULT

| Pooled, n = 1,902 | Value |
|---|---|
| **Gate 8 verdict (block 10)** | **NEGATIVE_EXPECTANCY**: the whole bootstrap CI of expectancy is below zero |
| Net expectancy | **−0.3180R**, 95 % CI [−0.3844, −0.2499] |
| iid bootstrap (secondary) | same verdict; CI [−0.3826, −0.2543] |
| With the +0.05R cost shock | CI [−0.4344, −0.2999] |
| With the +0.15R stress (reported) | CI [−0.5344, −0.3999] |
| Break-even extra cost | −0.318R: costs would have to be *negative* |
| Monte Carlo (5,000 resamples, 0.30 % per R, compounded) | the 10 % drawdown limit is hit in **100 %** of resamples; median max drawdown 611R |
| PSR (= DSR at the honest trial count of 1) | 4.1 × 10⁻¹⁷ |
| EXPLORATORY DSR at 25 / 1,000 / 4,008 trials (8E Sharpe variance) | ≈ 0 |

| Per symbol | n | Net expectancy | 95 % CI | Gate 8 | p (mean > 0) | BH q = 0.10 |
|---|---|---|---|---|---|---|
| GBPUSD | 460 | −0.319R | [−0.456, −0.177] | NEGATIVE_EXPECTANCY | 0.99999936 | not rejected |
| EURUSD | 522 | −0.436R | [−0.546, −0.315] | NEGATIVE_EXPECTANCY | ≈ 1 | not rejected |
| USDJPY | 457 | −0.404R | [−0.522, −0.262] | NEGATIVE_EXPECTANCY | ≈ 1 | not rejected |
| XAUUSD | 463 | −0.098R | [−0.219, +0.043] | EDGE_NOT_DEMONSTRATED | 0.934 | not rejected |

No symbol shows a positive edge. Gold is the least negative, but its interval still includes zero and its point estimate is negative.

### 5.2 Trade frequency: OBSERVED

- **Trades:** 1,902: EURUSD 522, XAUUSD 463, GBPUSD 460, USDJPY 457.
- **By year:** 2024: 584, 2025: 649, 2026 (to 26 Sep): 669.
- **Days:** 3,125 symbol trading days; entries on 732 (23.4 %); at most 10 entries in one day (the cap).
- **Lots:** median 3.21, range 0.04–18.95. Every trade was far above the production 0.02-lot cap, so this is a pure cap-neutral sample.

### 5.3 Win/loss distribution: OBSERVED

- **Rates and sizes:** win rate **19.6 %**; average win +2.147R; average loss −0.917R; payoff ratio 2.34; profit factor **0.569**.
- **Middle and tails:**
  - median −1.013R; worst trade −2.22R;
  - the worst 5 % of trades average −1.76R (5 % CVaR);
  - skew +1.58, excess kurtosis 1.72.
- **Exits:**

| Exit (classified by price) | Trades | Mean net R |
|---|---|---|
| Stop-loss | 964 | −1.275R |
| Breakeven | 425 | −0.231R |
| Take-profit | 317 | +2.472R |
| Other (time exit, Friday close, chunk end) | 196 | −0.313R |

Breakeven exits are still negative (−0.23R) because commission is charged on every trade.

### 5.4 Gross R: OBSERVED

The mean of `result_r` (price only, from the intended entry) is **−0.0724R**. Gross is negative for every symbol: EURUSD −0.090, USDJPY −0.074, GBPUSD −0.063, XAUUSD −0.060. **NEXA has no edge even before commission.**

### 5.5 Net R (corrected definition): OBSERVED / FORMAL

The mean is **−0.3180R** (§5.1). In dollars, summed over 48 independent $50,000 chunk accounts:
- price P&L **−$19,265.57**;
- commission **−$60,060.28**;
- swap **−$20.76**;
- realised total **−$79,346.61**.

### 5.6 Costs and their contribution: OBSERVED

| Component (mean per trade) | R |
|---|---|
| Gross (price, from intended entry) | −0.0724 |
| Entry slippage (fill vs intended) | +0.0001 |
| Commission ($7.00 per lot round trip, measured) | **−0.2453** |
| Swap | −0.0001 |
| **Net** | **−0.3180** |
| (Spread at decision, already inside gross; estimate) | 0.045 |

| Per symbol | Gross | Commission | Net |
|---|---|---|---|
| EURUSD | −0.090 | −0.347 | −0.436 |
| USDJPY | −0.074 | −0.330 | −0.404 |
| GBPUSD | −0.063 | −0.255 | −0.319 |
| XAUUSD | −0.060 | −0.038 | −0.098 |

**Why commission is so large:** NEXA's stops are very tight.
- **Placed stop distance, median:** EURUSD 2.4 pips (minimum 0.8), GBPUSD 3.2, USDJPY 3.9 pips, XAUUSD $2.22.
- **On FX:** a $7.00-per-lot round trip is 0.7 pips, about a quarter to a third of a typical stop.
- **On gold:** commission is small relative to the stop (median $2.22, minimum $0.38).

### 5.7 Slippage and fill differences: OBSERVED

- **Entry fills:** 422 of 1,902 (22.2 %) filled at a price different from the intended entry.
- **Size:** mean +0.0001R; 1st–99th percentile −0.048R to +0.050R; extremes ±0.32R.
- **Verdict:** entry slippage is negligible on average (250 ms execution delay, generated ticks in window A).

**ENGINEERING OBSERVATION:**
- The EA sizes lots on its internal stop distance, then rounds the stop price to the broker tick. For sub-pip stops this changes the real risk by a few percent.
- Measured at the placed stop, risk reached at most **0.333 %** of the realised balance, against the 0.30 % target. It never came close to the 1 % hard ceiling.
- The same rounding is why `result_r` (internal distance) and the DNA price R (placed stop) differ by up to 0.22R on individual trades.

### 5.8 Symbol by symbol: OBSERVED (formal per-symbol verdicts in §5.1)

| | Win rate | Avg win | Avg loss | PF | Max consecutive losses | Max drawdown (R) | Net USD |
|---|---|---|---|---|---|---|---|
| GBPUSD | 19.8 % | +2.12R | −0.92R | 0.57 | 14 | 151.6 | −$20,246 |
| EURUSD | 19.0 % | +2.11R | −1.03R | 0.48 | 20 | 229.2 | −$28,776 |
| USDJPY | 19.3 % | +2.00R | −0.98R | 0.49 | 17 | 184.6 | −$23,774 |
| XAUUSD | 20.3 % | +2.35R | −0.72R | 0.83 | 23 | 61.9 | −$6,550 |

### 5.9 Quarter by quarter: EXPLORATORY (no verdict per quarter)

Net expectancy in R, with trade counts in brackets:

| Window | GBPUSD | EURUSD | USDJPY | XAUUSD |
|---|---|---|---|---|
| 2024 Q1 | −0.41 (22) | −0.46 (103) | −0.47 (21) | −0.35 (20) |
| 2024 Q2 | −0.85 (20) | −0.17 (131) | −0.55 (20) | −0.15 (39) |
| 2024 Q3 | −0.82 (20) | −0.71 (20) | −0.73 (20) | −0.26 (20) |
| 2024 Q4 | −0.33 (23) | −0.75 (20) | −0.39 (65) | −0.18 (20) |
| 2025 Q1 | −0.56 (20) | −1.19 (20) | −0.51 (20) | −0.26 (20) |
| 2025 Q2 | −0.11 (126) | −0.28 (49) | −0.28 (26) | **+0.12** (107) |
| 2025 Q3 | −0.39 (21) | −0.49 (20) | −0.59 (20) | **+0.01** (109) |
| 2025 Q4 | −0.58 (20) | −0.46 (23) | −0.45 (28) | −0.28 (20) |
| 2026 Q1 | −0.44 (32) | −0.63 (20) | −0.23 (127) | −0.41 (20) |
| 2026 Q2 | −0.18 (115) | −0.45 (70) | −0.49 (20) | −0.52 (20) |
| 2026 Q3 (to 28 Aug) | −0.47 (21) | −0.59 (24) | −0.43 (70) | −0.49 (20) |
| B (28 Aug–26 Sep) | −0.38 (20) | −0.56 (22) | −0.67 (20) | **+0.03** (48) |

### 5.10 Stability across time: EXPLORATORY

- **Quarters:** 3 of 48 symbol-quarters are net-positive, all gold: 2025 Q2 +0.12R, 2025 Q3 +0.01R, B +0.03R. 8 of 48 are gross-positive.
- **By year:** −0.396R (2024), −0.217R (2025), −0.347R (2026). The losses are persistent, not one bad period.
- **Account outcomes:** chunk accounts finished between −8.3 % and +3.6 %, median −3.2 %. Only 3 of 48 were positive.

### 5.11 Survival pause: OBSERVED (shapes the whole sample)

The EA's own circuit breaker (`NEXA_Intelligence.mqh`, `SURVIVAL_PAUSED_EXPECTANCY_…`) stops new entries once NEXA's running expectancy is below −0.1R (`InpExpectancyPauseR`) over at least 20 trades (`InpMinSampleForSurvival`).
- **40 of 48 runs** paused themselves, almost always after 20 to 23 trades. **No run opened a single trade after its pause.**
- **8 runs never paused:** EURUSD 2024 Q2, GBPUSD 2025 Q2 and 2026 Q2, USDJPY 2026 Q1 and 2026 Q3, and XAUUSD 2025 Q2, 2025 Q3 and B.
- The tester re-initialises the EA at every quarterly chunk, so the pause was reset 48 times. **The sample is therefore mostly "the first ~20 trades after each restart" (1,069 trades from paused runs), plus 833 trades from the 8 runs that never paused.**

**EXPLORATORY:** net expectancy is −0.472R in the paused runs and −0.121R in the never-paused runs. Both are negative.

**INFERENCE:**
- This stopping rule ends runs after bad starts and lets better ones continue, so it likely makes the pooled figure look *better* than an always-on version of the rules would. It does not create the negative result.
- In continuous live operation, NEXA would very probably have disabled itself within its first few weeks.

### 5.12 Drawdown and losing sequences: OBSERVED

- **Drawdown:** the largest within-chunk drawdown of the $50,000 accounts was **8.67 %**.
- **Throttle:** 359 trades were sized below 0.25 % of balance. 334 of them were entered while the chunk account was at least 5 % below its peak, the drawdown-throttle zone (×0.5 risk, ×0.25 from 7.5 %), before the 10 % stop.
- **Losing streaks:** longest per symbol 14 to 23 losses; 29 for the pooled time-ordered sequence.
- **Daily losses:** 12 symbol-days lost ≥ 2 %; the worst day was −2.29 % (the daily-loss halt allows a final trade to overshoot slightly).

### 5.13 Distribution and fat tails: OBSERVED

- **Per trade (net R):** right-skewed (+1.58): many −1R losses and a few +2R to +4R take-profits; excess kurtosis 1.72.
- **Per day:**
  - 2,392 of 3,125 symbol-days were flat (no trade or no close);
  - left-skewed (−1.19), heavy-tailed (excess kurtosis 14.8);
  - 1 %/99 % quantiles −1.54 % and +1.05 %.
- **Note:** there is no single extreme event; the losses are broad-based.

---

## 6. Capital analysis (separate from the edge verdict)

### 6.1 Capital velocity: OBSERVED (each run is its own $50,000 account)

| Measure | Value |
|---|---|
| Symbol-days | 3,125: 220 up, 513 down, 2,392 flat |
| Mean daily return | **−0.051 %** (sd 0.355 %) |
| Median daily return | 0.000 % |
| Maximum daily return | **+3.15 %** (GBPUSD 2025-04-14) |
| Worst daily return | −2.29 % |
| Days at or above +24.5 % | **0** (one-sided 95 % upper bound: 0.096 % of days) |
| 20-day cycles (within chunks) | 132: mean −1.15 %, best +3.78 %, worst −6.02 %, 61 ended below their start, **0 reached ×80.05** |

### 6.2 $200 feasibility: replays of the tested trades, NOT broker-executed

Each symbol was replayed separately in 35 cycles of 20 weekdays, each starting at $200 with profit extracted (or the loss realised) at cycle end.

| Symbol | Replay | Trades executed | Cycles profitable | Mean cycle end | Cycles reaching ×80.05 |
|---|---|---|---|---|---|
| GBPUSD | NEXA rule (executable lots) | 438 | 2 / 35 | $197.73 | 0 |
| EURUSD | NEXA rule | 510 | 3 / 35 | $196.86 | 0 |
| USDJPY | NEXA rule | 430 | 2 / 35 | $197.69 | 0 |
| XAUUSD | NEXA rule | **188 of 428** | 6 / 35 | $199.15 | 0 |
| all | theoretical (no lot grid) | 1,843 | 13 / 140 | $196.4–$199.2 | 0 |
| all | pre-registered 8E simulator | 1,123 | 9 / 140 | $198.0–$200.0 | 0 |

**Theoretical versus executable:**
- **FX:** tight stops make FX trades executable at $200 on the broker's 0.01-lot grid, so the theoretical and executable replays almost coincide.
- **Gold:** **224 of 428 trades are not executable at $200.** A 0.01-lot gold position risks more than 1 % of $200 at NEXA's stops, which NEXA's own rule forbids. The pre-registered 8E simulator, which also counts costs in its sizing, executes only 2 of 428.
- **Cycle results:** many cycles end at exactly $200 because no trades fell in them (survival pause, §5.11). The best cycle in any replay ended at **$220.37 (+10.2 %)**; the target path requires $16,010.95 (×80.05) after 20 days.

### 6.3 +24.5 % daily objective (the user's objective, preserved verbatim)

> PRIMARY CAPITAL OBJECTIVE: +24.5% net equity growth per trading day, compounded over the trading period, with the intended 20-day cycle and monthly profit extraction/reset described in the NEXA System Blueprint.

The objective is not lowered here. It was not used to select, reject or tune anything, and the experiment was not shaped toward it.

- **Arithmetic:** unreachable under the frozen controls (§4). The implemented ceiling is +12.67 %/day, and the target needs 18.4 maximum wins against a cap of 10.
- **Observed:** 0 days at target in 3,125. The best day, +3.15 %, is about 13 % of the daily target; 20-day cycles reached at most ×1.038 against the required ×80.05.
- **Verdict for the tested configuration: CONTRADICTED.**
- **What reaching it would require:** changing the hard controls (risk per trade, trade cap, daily halt) **and** a large demonstrated edge. Neither exists, and the first is outside this campaign by design.
- **Source note:** the "NEXA System Blueprint" document is not in the repository. The cycle parameters come from `NEXA_24_5_DAILY_FEASIBILITY_AUDIT.md` §1.

---

## 7. Limitations

- **Not out-of-sample:** the EA was developed and hardened during this period. Even a positive result would have been PRELIMINARY.
- **Implemented EA only:**
  - D-PARTIAL-AFTER-BE is present (§3);
  - the specified exit logic was not tested;
  - the survival pause shapes the sample (§5.11).
- **Tester model:** generated ticks from M1 in window A, real ticks only in window B; 250 ms execution delay.
- **Account structure:**
  - single-symbol accounts reset to $50,000 each quarter, so compounding never spans chunks;
  - cross-pair exposure is not exercised.
- **Approximations:** excursion counts (§3) use bid M1 bars and are approximate; exit types are classified by price within 0.05R.
- **Inherited clock issue:** D-TZ (a fixed GMT+2 offset) shifts session tags and FOMC windows by an hour during US daylight time. Not corrected.
- **$200 figures:** these are replays of tested trades at a different size, not broker-executed results. At $200 the EA's own filters and survival pause could produce a different trade sequence.

---

## 8. Final conclusions

1. **Cap-neutral research edge: NONE.**
   - **FORMAL:** Gate 8 returns NEGATIVE_EXPECTANCY. Net −0.318R per trade, 95 % CI [−0.384, −0.250], n = 1,902.
   - **By symbol:** negative for every symbol, statistically so for EURUSD, GBPUSD and USDJPY; gold is inconclusive at −0.098R.
   - **Before costs:** negative too (−0.072R gross).
   - The defect bound (≈ −0.008R per trade) cannot change this.
   - **No profitability claim is supported.**
2. **Capital velocity and the +24.5 % objective: CONTRADICTED for the tested configuration.**
   - Unreachable by arithmetic (ceiling +12.67 %/day) and absent in the data (0 of 3,125 days; best +3.15 %).
   - $200 cycles: 0 of 140 on the target path. At $200, most gold trades are not executable within NEXA's 1 % hard ceiling.
   - The objective itself is preserved unchanged.
3. **EA engineering status: functional but not production-ready.**
   - **ENGINEERING DEFECT D-PARTIAL-AFTER-BE:** the partial close and the time exit are unreachable after breakeven. It is unrepaired and needs a separately approved fix and test.
   - **OBSERVED:**
     - the survival pause self-disables NEXA after about 20 losing-expectancy trades;
     - stop-tick rounding lets risk reach 0.333 % against the 0.30 % target (still within the 1 % ceiling);
     - two brief position overlaps occurred.
   - **Not production-ready:** there is no validated edge, and the earlier open items (S11, D-TZ, the stale deployed build) remain.
4. **Production risk-cap change: NOT JUSTIFIED.**
   - The cap-neutral campaign was the cheapest way to learn whether NEXA's signals are worth more trading capacity, and they are not.
   - **INFERENCE:** re-denominating the production cap (option C) would only let a negative-expectancy rule set trade larger.
   - The B-EXPOSURE-CAP decision can rest: keep the production cap unchanged unless a future, properly validated edge appears.

**STOP.** No defect fix, no new campaign, and no production change has been started.
