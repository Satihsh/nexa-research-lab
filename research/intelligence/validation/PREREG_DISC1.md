# PRE-REGISTRATION H-DISC1: does the user's own discretionary order-flow trading have an edge?

**Status: APPROVED by the user in chat on 2026-10-18 ("Yes approve H-DISC1"). Binding.**
- Hashed into PREREG_HASHES.txt on approval, **before any trade** (no warm-up or counted trade exists yet).
- Draft values approved unchanged. The user also said "taking risk I'm good because I'm going to use a prop firm account"; the $250 cap stays (H-PROP-EV-TS sizing), as approved.

**Why:**
- Every *mechanical* intraday rule on ES/NQ failed (ledger: about 163 trials, H-ML1 included).
- The one hypothesis no backtest can measure is the user's own discretionary read of order flow in ATAS.
- A pre-registered forward record is the only honest test.
- It costs $0 in trading capital, since it uses a simulated account.

## 1. Setup (fixed)
- **Platform:** ATAS X, demo account. **Real-time data is required.** Trades made on the free plan's 15-minute-delayed data never count.
- **Instrument:** MNQ (micro Nasdaq). One instrument for the whole test.
- **Hours:** 08:30–15:00 CT entries only (09:30–16:00 New York). Flat by 15:08 CT. Topstep-compatible.
- **Trades:** at most **2 per day**. Direction (long or short) is the trader's choice.
- **Stop required:** every trade has a **stop order placed at entry** (ATAS SL/TP template or a manual stop).
  - **1R** = |entry − initial stop| × contracts × $2.
  - The initial stop is read from `orders.csv` (NEXA Monitor journal).
- **Size:** risk per trade ≤ **$250** (Topstep 50K sizing used in H-PROP-EV-TS).
- **Journal:** NEXA Monitor v ≥ 1376de3 (later versions may only add journal fields, never change fills/round trips/orders logic) running on the chart for every counted trade (`fills.csv`, `roundtrips.csv`, `orders.csv` in ~/Documents/NEXA_ATAS).

## 2. Counting
- **Warm-up:** the first **20** real-time trades are practice and are **excluded** (learning the platform).
- **Evaluation sample:** the next **100** completed trades.
- **Every trade counts at its actual result:**
  - rule-breaking trades (no stop, a 3rd trade, after 15:08 CT) are **flagged but not removed**;
  - no trade may be deleted, redone or excluded after the fact.
- **Costs added in analysis** (the demo may not charge them): $1.22 commission per contract round trip (TopstepX MNQ) **plus 1 tick ($0.50) slippage per side per contract**.
- **A trade without a recorded stop** is valued with R = its loss if negative, otherwise excluded from the R mean but reported. If more than 10 % of trades lack a stop, the test is INVALID.

## 3. Verdict (computed once, after trade 100)
- **Statistic:** mean net R per trade. Moving-block bootstrap over trades (block 5, B = 2,000, seed 20261018), 95 % CI.
- **Verdicts:**
  - **NO EDGE:** mean ≤ 0.
  - **EDGE (not yet prop-ready):** CI lower bound > 0 and mean < +0.10R.
  - **COMBINE-READY:** CI lower bound > 0 **and** mean ≥ **+0.10R** (H-PROP-EV-TS target).
  - **INCONCLUSIVE:** mean > 0 but CI includes 0. One pre-declared extension to **200** trades, then the same rule. No further extensions.
- **Also reported:**
  - win rate; average win and loss in R;
  - longest losing streak;
  - green days and green months;
  - rule violations;
  - results by time of day and by long vs short;
  - a simulated Topstep 50K Combine path on the actual trade sequence (pass/fail, MLL);
  - **report only, never a verdict:** results by the user's setup tag and by journal context (trend/range, position vs VWAP and session levels, entry-bar delta, planned R:R, MAE/MFE). These breakdowns are exploratory: any pattern found becomes a *new* pre-registered hypothesis tested on later trades, not a filter applied to these 100.

## 4. Honest power statement (written now)
- Intraday R outcomes have a standard deviation of about 1R per trade. So 100 trades give a standard error of about **0.10R**.
- To show "CI lower bound > 0", the mean must be roughly **+0.20R or better**. Confirming exactly +0.10R would need about 400–500 trades.
- A truly profitable trader can therefore still come out INCONCLUSIVE at 100 trades. NO EDGE (mean ≤ 0) is decisive.

## 5. What follows
- **NO EDGE:** do not buy a Topstep Combine.
- **INCONCLUSIVE:** extend once, as in §3.
- **EDGE or COMBINE-READY:** a capital review with the user. Even then, no borrowed money; one Combine at a time.

## Approved values
| Item | Draft value |
|---|---|
| Instrument | MNQ |
| Max risk per trade | $250 |
| Warm-up trades | 20 |
| Evaluation trades | 100 (extension 200) |
| Entry window | 08:30–15:00 CT |

## Companion analysis (added 2026-10-23, before any trade)
- `PREREG_DISC1_RULES.md` (b2745942): red-day / green-day rule checks (daily stop −$250, two-loss pause, trailing winners, daily stop + trail) on the same counted trades, judged per session with Bonferroni. Computed with the H-DISC1 verdict; it never changes it. Code `disc1_rules.py`.
