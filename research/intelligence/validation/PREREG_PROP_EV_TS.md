# PRE-REGISTRATION H-PROP-EV-TS: is a Topstep 50K Combine worth buying, and what edge does it need?

**Status: BINDING.**
- User decision 2026-10-18: Topstep, futures only, 1–2 trades a day; "Proceed with whatever is best".
- **Written before any simulation output exists.**
- **No market data.** Pure Monte Carlo of Topstep's published rules.
- **Rules source:** `TOPSTEP_COMBINE_RULES_2026-10-18.md` (hash recorded with this file).

**Why:**
- H-PROP-EV used Apex rules. The user's firm is Topstep. Its rules differ: no time limit, monthly fee, MLL that locks, XFA starting at $0, 90/10 split, capped payouts.
- The output sets the **minimum net edge per trade** the strategy search (step 2) must clear before a Combine is bought.

**Method:** identical to H-PROP-EV (`PREREG_PROP_EV.md` §1–2). The same functions `p_win`, `loss_peak`, `win_dip` are imported unchanged from `prop_ev.py` (ddd219c9).

## 1. Trader model (fixed)
- **Instrument:** MNQ / NQ, intraday, flat by the close.
- **Static bracket:**
  - stop **S = 25 NQ points**;
  - target **b·S**;
  - one position at a time.
- **Risk per trade r$** = 25 points × $2 × micros.
- **Grid of 36 configurations:**
  - b ∈ {1.0, 1.52, 2.0};
  - r$ ∈ {$250, $500, $750} (5 / 10 / 15 MNQ; all within the Combine limit and the XFA 2-lot minimum tier of 20 MNQ, so the scaling plan never binds);
  - **trades per day K ∈ {1, 2}** (the user's plan);
  - **XFA payout path ∈ {Standard, Consistency}**.
- **Costs:** S1 = 2 NQ points round trip ⇒ **c = 0.08R** (as H-PROP-EV).
- **μ grid (11):** −0.10, **−0.08 (zero market edge)**, **−0.045 (NEXA's measured T2a edge)**, −0.04, 0, +0.025, +0.05, +0.10, +0.15, +0.20, +0.30.
- **Path inside a trade:** driftless Brownian excursions as in H-PROP-EV. Liquidation happens if the path touches the MLL (balance set to the MLL, no extra slippage).

## 2. Combine (one "attempt" = one Combine life)
- Start $50,000.
- **MLL:** 48,000; after each day's close it becomes max(MLL, min(peak EOD close − 2,000, 50,000)), so it locks at $50,000.
- **Trading rule within a day:**
  - up to K trades;
  - the trader stops for the day once **profit ≥ $3,000 and today's P&L ≤ 55 % of total profit** (passing condition met);
  - **K = 2 does not add a stop after losses.**
- **Pass:** at a day's close, profit ≥ $3,000 and the largest single-day profit ≤ 55 % of profit (equivalent to Topstep's raised target = best day ÷ 0.55). The pass needs at least 2 trading days by construction (a single day can never satisfy both).
- **Fail:** the MLL is touched. The attempt ends; a new attempt = a Reset / new Combine at the same price.
- **Horizon cap:** 250 trading days (counted as fail; fees still charged).
- **Fee per attempt:**
  - **one monthly fee for every started 21-trading-day block** of the attempt;
  - plus the activation fee if passed (Standard path only).
  - Assumption A1: a Reset costs the same as a month and restarts the billing block.

## 3. Express Funded Account (after a pass)
- Balance $0.
- **MLL** −2,000 trailing on EOD, locking at $0 (= max(MLL, min(peak EOD − 2,000, 0))). **Set to $0 after the first payout.**
- **Standard path:** eligible at a day's close if:
  - ≥ 5 days with day P&L ≥ $150 since the last payout;
  - net since the last payout > 0 (first payout exempt);
  - amount = min(50 % × balance, $2,000) ≥ $125.
- **Consistency path:** eligible at a day's close if:
  - ≥ 3 trading days since the last payout;
  - net since the last payout > 0;
  - largest day ≤ 40 % of that net;
  - amount = min(50 % × balance, $3,000) ≥ $125.
- **The trader requests the maximum amount** on the first eligible day. Afterwards: balance − amount, counters reset, MLL = 0.
- **Cash received per payout** = 0.9 × amount − $30 (international wire).
- **XFA ends** when the MLL is touched or after 250 trading days.
  - The remaining balance is valued at **$0**.
  - The Live Funded call-up is ignored (discretionary; conservative).
  - Back2Funded is not purchased.

## 4. Outputs (396 cells × N = 10,000 attempts, seed 20261018)
- **Per cell:**
  - P(pass); mean months (fee blocks) per attempt;
  - P(≥ 1 payout | XFA); E[cash | XFA]; mean number of payouts;
  - E[cash per attempt]; P(≥ 1 payout per attempt).
- **Net EV per attempt** under:
  - **F-STD:** $49/month + $149 activation;
  - **F-NOACT:** $95/month, no activation.
- Cash-per-fee ratio.

## 5. Questions and decision rule (fixed now)
- **Q1 (μ = −0.08, zero market edge):** is the best of the 36 configurations' net EV per attempt > 0 under F-STD / F-NOACT?
- **Q2 (μ = −0.045, NEXA's measured edge):** same question.
- **Q3:** the smallest μ on the grid at which the best configuration's net EV is > 0, per fee path.
- **Q4 (descriptive):** P(≥ 1 payout per attempt) and P(no payout after 10 attempts) for the best configurations at μ = −0.08 and at the Q3 threshold.
- **Decision:**
  - **(a)** If Q1 and Q2 are negative under both fee paths: **no Combine purchase until a strategy shows ≥ the Q3 edge net, out of sample, and in forward paper trading.**
- **The Q3 value becomes the binding pass bar for the step-2 strategy search.**

## 6. Validation before running (G1, `test_prop_ev_ts.py`)
1. Combine MLL trails EOD and locks at 50,000 (worked example: +500 day → 48,500; −500 → stays 48,500; locks at 50,000).
2. XFA MLL locks at 0 (Topstep example: +500 → −1,500; +1,500 → locks at 0) and is 0 after the first payout.
3. Combine pass rule with consistency (Topstep example: best day $1,800 ⇒ needs $3,273; $1,600 best of $3,000 passes).
4. Standard payout: 5 days ≥ $150, cap $2,000, 50 % of balance, $125 minimum, positive net after the first payout.
5. Consistency payout: 3 days, 40 % rule (Topstep examples: $1,000 net / $400 best OK; $450 best not OK), cap $3,000.
6. Fee blocks: 1–21 days = 1 month, 22 days = 2.
7. A strong-edge sanity check produces payouts within caps.
8. The imported `p_win` / `loss_peak` / `win_dip` are the same objects as in `prop_ev.py`.

Code and tests are hashed before the run. The run is done **once**.

## 7. Limits (stated now)
- Topstep 50K only; rules as of 2026-10-18; no DLL (its limited-time doubled caps are not modelled).
- I.i.d. bracket trades; no streaks, regime changes or slippage beyond 0.08R.
- Remaining XFA balance and Live upside are valued at $0 (conservative). Human time, taxes and the TopstepX API fee ($14.50/month, only needed for automation) are not included.
