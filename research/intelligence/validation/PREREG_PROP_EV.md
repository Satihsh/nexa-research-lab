# PRE-REGISTRATION H-PROP-EV: is an Apex 50K evaluation positive expected value for the edge NEXA actually has?

**Status: BINDING.**
- User approval 2026-10-18: "Start with the prop-firm maths check".
- **Written before any simulation output exists.**
- **No market data.** Pure Monte Carlo of the firm's published rules.

**Rules source:** `APEX_RULES_SNAPSHOT_2026-10-18.md` (Apex help centre, read 2026-10-18; hash recorded with this file).

**Why:**
- Batch-10 sources say the "$1M payout" results come from prop-firm convexity:
  - JJ Simon (SRC-YT-113): "random entry = break-even", ≈ 9 % of evaluations pay;
  - Brun (SRC-YT-105): Drawdown Shield;
  - Apex founder (SRC-YT-123): "fees help pay it out", ~2 % go live.
- The question is whether the prop route can work **without** a market edge. If it cannot, it must wait for a validated edge, as the user rule already says.

## 1. Trader model (fixed)
- **Instrument:** MNQ / NQ futures, intraday only, flat by the close.
- **Each trade is a static bracket:**
  - stop **S = 25 NQ points** (JJ Simon's evaluation stop; CL-155);
  - target **b·S**;
  - one position at a time.
- **Risk per trade r$** = 25 points × $2 × number of micros (5 micros = $250).
- **Grid of trader configurations (36):**
  - b ∈ {1.0, **1.52** (JJ 25/38), 2.0};
  - r$ ∈ {$250, $500, $750} (5 / 10 / 15 micros, all within every contract limit);
  - trades per day K ∈ {1, 3};
  - drawdown type ∈ {EOD, Intraday}.
  - With K = 3 the trader stops after 3 consecutive losses (JJ's session stop), which equals at most 3 trades.
- **Day stop:** after K trades, or when the DLL is hit.
- **The evaluation ends** when the target is reached (pass; trading stops), the threshold is touched (fail), or 21 trading days pass (≈ 30 calendar days, fail).
- **The PA is traded every session** until:
  - the threshold is touched (closed);
  - the 6th payout is made (cycle complete; any remaining balance is valued at **$0**, because live transfer is invite-only, ~2 %); or
  - 250 trading days pass (the remaining balance is valued at $0).
- **Payouts are requested** at the end of the first day on which all conditions in §3 hold. Amount = min(cap#k, balance − $52,100), and only if ≥ $500.

## 2. Edge model
- **Per-trade net expectancy μ in R** (after costs). Win probability **p = (μ + 1 + c) / (b + 1)**.
- **Outcomes:** win = +b − c R, loss = −1 − c R.
- **Costs c in R** = round-trip cost / (S points). NQ **S1 = 2 points ⇒ c = 0.08R**; S0 = 1 point ⇒ 0.04R (as PREREG_CFT §4).
- **μ grid (11 values):**
  - −0.10;
  - **−0.08 (zero market edge at S1 costs = "random entry")**;
  - **−0.045 (NEXA's measured T2a net edge, ES −0.046 / NQ −0.045)**;
  - −0.04 (zero edge at S0 costs);
  - 0.00, +0.025, +0.05, +0.10, +0.15, +0.20, +0.30.
- **Path inside a trade** (needed because thresholds are enforced in real time on unrealised P&L): driftless Brownian motion between barriers −1 and +b, conditioned on the outcome. Drawn by inverse CDF:
  - **losers:** the peak excursion before the stop, P(max ≥ m | loss) = (b − m) / (b(1 + m)), so m = b(1 − u) / (1 + u·b);
  - **winners:** the deepest excursion before the target, P(min ≤ −k | win) = b(1 − k) / (b + k), so k = b(1 − u) / (u + b);
  - u ~ U(0,1).
  - The approximation (driftless shape even when μ ≠ 0) is accepted; μ is small relative to the barrier.
- **Liquidation:** if the path touches the threshold, the account is closed with balance = threshold (no extra slippage). If the path touches the day's DLL level, the position is closed at that level and the day ends.
- Costs are charged at the exit.

## 3. Rules simulated (from the snapshot)
- **Evaluation:**
  - start $50,000, target $53,000, drawdown $2,000;
  - EOD: threshold = max EOD close − 2,000, capped at $53,000, updated at the day's close; DLL $1,000;
  - Intraday: threshold = peak (including unrealised) − 2,000, updated in real time, capped at $53,000; no DLL.
- **PA:**
  - start $50,000; same drawdown types; **the threshold locks at $50,100**;
  - DLL by tier from the previous close (L1/L2 $1,000, L3 $2,000, L4 $3,000);
  - payout conditions (all must hold):
    - ≥ 5 qualifying days since the last payout (day P&L ≥ $250 EOD / $200 Intraday);
    - net profit since the last payout > 0;
    - the largest profitable day since the last payout ≤ 50 % of that net (Apex's own worked example counts exactly 50 % as met: $1,000 / $2,000 → "✓ Consistency Met"; its calculator says net ≥ highest day / 0.5);
    - balance ≥ $52,600;
    - fewer than 6 payouts so far.
  - Caps: EOD 1,500 / 1,500 / 2,000 / 2,500 / 2,500 / 3,000; Intraday 1,500 / 2,000 / 2,500 / 2,500 / 3,000 / 3,000.
  - After a payout the balance falls by the amount and the counters reset.
- **Assumption A1:** "5 trading days between rewards" means 5 *new* qualifying days per payout.

## 4. Outputs per cell (36 configs × 11 μ = 396 cells; N = 10,000 attempts per cell; seed 20261018)
- **P(pass)**, mean trading days per attempt.
- For PAs: **P(≥ 1 payout)**, **E[total payouts]**, mean number of payouts, P(6 payouts).
- **E[payout per attempt]** = P(pass) × E[payouts | PA].
- **Break-even fee per attempt F\*:** the eval fee E and activation A satisfy E + P(pass)·A = E[payout per attempt].
- **Net EV per attempt** under fee scenarios:
  - **F-LIST:** EOD $197 + $99, Intraday $131 + $79 (secondary source);
  - **F-COUPON:** 90 % off the eval (official homepage shows "$167 → $16.70") + full activation (EOD $19.70 + $99, Intraday $13.10 + $79);
  - **F-ZERO-ACT:** coupon eval + $0 activation (lower bound of cost).
- **Payout per $ of fees.**

## 5. Primary questions and decision rule (fixed now)
- **Q1 (zero market edge, μ = −0.08):** under each fee scenario, is the **best** of the 36 configurations' net EV per attempt > 0?
- **Q2 (NEXA's measured edge, μ = −0.045):** same question.
- **Q3:** the smallest μ on the grid at which the best configuration's net EV > 0, per fee scenario and drawdown type.
- **Decision:**
  - **(a)** If Q1 and Q2 are negative under F-LIST and F-COUPON: **"the prop route needs a validated market edge first"**. This confirms the current rule; no evaluation purchase.
  - **(b)** If Q1 or Q2 is positive under any scenario:
    - report it as **fee-structure convexity, not trading skill**;
    - list the Apex clauses it may breach ("Stockpiling Evaluation Accounts", "Unsustainable Strategies", "High-Risk Strategies");
  - **Q3** sets the minimum edge NEXA's strategy research must demonstrate (net, out of sample) before a prop evaluation is reconsidered.
- **Choosing the best of 36 configurations** is an optimisation over a known model, not data mining (there is no data). The full grid is reported.

## 6. Validation before running (G1)
Unit tests in `test_prop_ev.py` must pass before the full run:
1. p formula reproduces μ.
2. Excursion samplers match a discrete random-walk check within tolerance.
3. EOD threshold example from Apex's page: 50,800 → 48,800; 51,600 → 49,600; 50,900 → unchanged; 52,000 → 50,000.
4. PA threshold locks at 50,100.
5. Apex consistency example table: eligible only on day 9.
6. Payout cap sequence and the $500 minimum.

The code and tests are hashed into PREREG_HASHES.txt before the run. The run is done **once**.

## 7. Limits (stated now)
- One firm (Apex), one size (50K), rules as of 2026-10-18. Firms change rules and prices often.
- The static-bracket i.i.d. trade model has no streaks, regime changes or fat-tail days. Real autocorrelation would widen the outcome spread.
- Live-account upside is ignored (invite-only, ~2 %), and so is the residual sim balance after cycle end. Both are conservative toward *lower* EV.
- Human time cost is not priced. Taxes, data fees and platform fees are not included.
