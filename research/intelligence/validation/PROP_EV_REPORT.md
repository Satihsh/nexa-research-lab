# H-PROP-EV results: Apex 50K evaluation + PA, Monte Carlo (2026-10-18)

- **Pre-registration:** `PREREG_PROP_EV.md` (29070c2b), rules snapshot `APEX_RULES_SNAPSHOT_2026-10-18.md` (cb2aec17).
- **Code:** `prop_ev.py` (ddd219c9); 8/8 G1 tests passed before the run.
- **Run:** once, 396 cells × 10,000 attempts, seed 20261018, 15.6 s.
- **Output:** `prop_ev_results.json`.
- **No market data.** The question was only: what do Apex's published rules pay out for a given per-trade edge?

## Verdict
| Question | F-LIST (eval $197 + $99 activation, EOD) | F-COUPON (eval at 90 % off + $99) | F-ZERO-ACT (coupon eval, $0 activation) |
|---|---|---|---|
| **Q1** zero market edge (μ = −0.08R after costs) | **negative**: best −$132 / attempt (EOD), −$85 (Intraday) | **positive**: best +$45 (EOD), +$33 (Intraday) | positive: +$64 / +$43 |
| **Q2** NEXA's measured edge (μ = −0.045R) | **negative**: −$98 / −$57 | positive: +$79 / +$61 | positive: +$100 / +$73 |
| **Q3** smallest edge with a positive best configuration | **+0.025R net** (both types) | ≤ −0.10R (the whole grid) | ≤ −0.10R |

**Pre-registered decision.**
- At list prices the evaluation is a losing purchase for anything short of a real edge of about **+0.025R per trade after costs**. That is rule (a).
- At the 90 %-off coupon price, even random entries have a small positive average. That is rule (b), **fee-structure convexity**. It is reported, not recommended. The reasons follow.

## What the positive coupon result really looks like
Best zero-edge configuration (EOD; 25-point stop, 1.52R target, $750 risk = 15 MNQ, 1 trade a day):

| Quantity | Value |
|---|---|
| P(pass the evaluation) | 18.7 % (≈ 5.6 trading days per attempt) |
| P(at least one payout \| funded) | 19.4 % |
| **P(at least one payout per evaluation bought)** | **3.6 %**, about **1 in 28** evaluations |
| E[payouts \| funded] | $445; PA lasts ≈ 9 days on average; P(all 6 payouts) 0.2 % |
| Cost per attempt (coupon) | $38 (eval $19.70 + 18.7 % × $99 activation) |
| **P(no payout at all after 10 evaluations, ≈ $380 spent)** | **69 %** |
| Average net per attempt | +$45, but almost all of it from rare payouts |

- This is a **lottery-shaped bet** funded by Apex's fee pricing.
  - The model's average is only positive because the downside of each attempt is capped at a small fee.
  - The best configuration risks 37.5 % of the drawdown on every trade: maximum variance, which is exactly what an option-like payoff rewards.
- **It matches the batch-10 testimony:**
  - JJ Simon: "≈ 9 % of evaluations ever pay; nine times out of ten you lose $100". Our zero-edge number is 3.6 %; with a modest real edge it rises.
  - Apex's founder: the fees help fund the payouts.
- **Why it is not a recommendation:**
  1. **Apex's prohibited activities** name "Stockpiling Evaluation Accounts … to intentionally blow up accounts in pursuit of windfall profits", plus "Unsustainable Strategies", and "Using the Trailing Threshold as a Stop Loss". Buying cheap evaluations to gamble on a random-entry strategy is what those clauses describe. Accounts and payouts can be forfeited.
  2. **The coupon is not a published rule.** It is a promotion that can disappear or change. At list price the same play loses $132 per attempt.
  3. **Human time:** ~6 sessions per evaluation × 28 evaluations per paying account ≈ 160 trading sessions per payout event. The model prices that time at $0.

## With a real edge, the prop route becomes clearly worthwhile
| Net edge per trade | Best EV per attempt at **list** price (EOD) | P(pass) | P(≥ 1 payout per attempt) | Best configuration |
|---|---|---|---|---|
| +0.025R | +$162 | 32 % | 9.9 % | 1R target, $500 risk, ≤ 3 trades a day |
| +0.05R | +$407 | 37 % | 13.5 % | same |
| **+0.10R** | **+$1,500** | 32 % | 20 % (P(6 payouts \| funded) 37 %) | 1R target, **$250 risk**, ≤ 3 trades a day |
| +0.20R | +$6,330 | 61 % | 54 % (P(6 payouts \| funded) 85 %) | same |

- **The best sizing flips** once there is an edge: from large risk (gambling on convexity) to **small risk with more trades** (letting the edge compound across the 6 capped payouts).
- **Q3 threshold:** a strategy NEXA tests needs **≥ +0.025R per trade net, out of sample**, before a list-price evaluation is even break-even, and roughly +0.10R before it pays well.
- For comparison, every intraday NQ/ES test so far:
  - T2a −0.045R;
  - H-ORB30L OOS −0.071R;
  - OFC1 −0.21R;
  - H-ORB-1 +0.063R in sample only, INCONCLUSIVE.

## Limits (as pre-registered)
- One firm, one size, rules as of 2026-10-18. Prices are from a secondary source (list) and the homepage coupon (25K product).
- I.i.d. bracket trades with Brownian paths inside each trade. No streaks, no regime changes, no gap/news slippage.
- Live-account upside and the residual balance after 6 payouts are both valued at $0 (conservative).
- Taxes, data and platform fees are not modelled.

## Bottom line for the user
- **No evaluation purchase is justified now.** At normal prices NEXA's measured edge loses about $100 per evaluation.
- At coupon prices the positive average is a lottery that breaches the spirit, and likely the letter, of Apex's rules.
- What the prop route actually needs is a strategy with **≥ +0.025R, ideally ~+0.10R, net per trade, out of sample**. Finding one is the job of the pre-registered tests, starting with H-FPT-REV.
