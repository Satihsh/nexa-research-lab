# H-PROP-EV-TS results: Topstep 50K Combine + Express Funded Account, Monte Carlo (2026-10-18)

- **Pre-registration:** `PREREG_PROP_EV_TS.md`; rules `TOPSTEP_COMBINE_RULES_2026-10-18.md` (both hashed before code).
- **Code:** `prop_ev_ts.py`, with the engine imported unchanged from `prop_ev.py` (ddd219c9). 10/10 G1 tests passed, plus 8/8 for H-PROP-EV.
- **Run:** once; 396 cells × 10,000 attempts; seed 20261018; 19.6 s.
- **Output:** `prop_ev_ts_results.json`. No market data.

## Pre-registered answers
| Question | F-STD ($49/month + $149 activation) | F-NOACT ($95/month) |
|---|---|---|
| **Q1** zero market edge (μ = −0.08R net) | **positive**: best +$35 / attempt | **positive**: best +$20 |
| **Q2** NEXA's measured edge (μ = −0.045R) | **positive**: best +$75 | **positive**: best +$63 |
| **Q3** smallest μ with a positive best configuration | −0.10R (the whole grid) | −0.08R |

**By the pre-registered decision, this is rule (b): fee-structure convexity, not trading skill.**
- Topstep's low monthly fee, no time limit and a capped downside per attempt make the *average* of a lottery-sized bet slightly positive.
- **Q3 is therefore degenerate.** It is set by the lottery configurations, not by an edge, so it cannot serve as a pass bar.

## What the "positive" zero-edge result really is
Best zero-edge configuration: Consistency path, 2R target, **$750 risk per trade (15 MNQ = 37.5 % of the $2,000 MLL)**, 1 trade a day.

| Quantity | Value |
|---|---|
| P(pass the Combine) | 21.2 % |
| **P(at least one payout per Combine bought)** | **3.6 %**, about **1 in 28** |
| Cost per attempt (F-STD) | $81 |
| Average cash per attempt | $115 (almost all from rare long-lived XFAs) |
| **P(no payout at all after 10 Combines, ≈ $800 spent)** | **69 %** |

- **This configuration is what Topstep prohibits.** Its "Account Stacking" rule bans "repeatedly trading aggressively, hitting the MLL in one account, then switching to another… until a large win occurs" (`Prohibited Trading Strategies`, 2026-06-10). Payouts can be rejected.
- **With sensible sizing the zero-edge trader loses money.** At $250 risk and a 1R target:
  - 1 trade a day: net −$110 per attempt;
  - 2 trades a day: +$2 (break-even);
  - in both cases a payout comes from only 16–20 % of Combines, averaging $85–135 of cash per attempt.
- **NEXA's measured edge (−0.045R, T2a) has the same lottery shape:** the best configuration again uses $750 risk; P(payout per attempt) 4.5 %.

## What a real edge buys at Topstep
Sizing: $250 risk (5 MNQ), 1R target, 2 trades a day, Standard path, F-STD fees.

| Net edge per trade (out of sample) | P(pass) | P(≥ 1 payout per Combine) | Cash per Combine | Net per Combine |
|---|---|---|---|---|
| 0 (none) | 26 % | 16 % | $135 | **+$2** |
| +0.025R | 35 % | 23 % | $251 | +$101 |
| +0.05R | 45 % | 33 % | $408 | +$243 |
| **+0.10R** | **63 %** | **54 %** | **$1,128** | **+$935** |
| +0.15R | 79 % | 71 % | $2,790 | +$2,580 |

- Express Funded accounts end fast even with an edge (mean life 23–52 trading days). After each payout the MLL drops to $0, and withdrawing 50 % leaves a thin cushion. **Cash comes as a few capped payouts per funded account**, not as a steady income.

## Consequence for step 2 (strategy search)
- The pre-registered Q3 is degenerate (lottery). The pass bar for the strategy search is therefore set from the table above, **before** any step-2 data is touched:
  - **minimum:** a positive net edge whose out-of-sample 95 % CI lower bound is > 0 (μ > 0 proven, not assumed);
  - **target:** **≈ +0.10R net per trade** at 1–2 trades a day. This is where a Combine has a better-than-even chance of paying out (54 %) and a clearly positive value (+$935 per Combine).
- **No Combine purchase now.** NEXA has no strategy with a proven positive edge. Buying Combines to play the lottery configuration is both a likely rules breach and the risk profile the user's $0-until-proven rule exists to prevent.

## Limits (as pre-registered)
- Topstep 50K, rules as of 2026-10-18, no DLL (its limited-time doubled payout caps would raise the edge-case values).
- I.i.d. bracket trades; no streaks or regime changes.
- Remaining XFA balance and Live call-up are valued at $0 (conservative).
- Human time, taxes and the $14.50/month API fee (only for automation) are not included.
