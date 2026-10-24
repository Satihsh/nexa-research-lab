# NEXA +24.5 %/day feasibility audit (research only, 2026-10-01)

**The target is not lowered here.** This report computes exactly what +24.5 % net per trading day requires under NEXA's unchanged hard rules:
- **1 % risk per trade** on current equity;
- **halt at −2 %** from the day's starting equity;
- **at most 10 trades per day**;
- no martingale, grid, averaging, loss-chasing or risk increase after a miss.

The engine: `research/nexa_8e_feasibility.py`. It uses exact dynamic programming over every win/loss path, and its tests are in `research/test_nexa_capital_velocity.py`.

## Answers first

| Question | Answer (exact, derived below) |
|---|---|
| **R.** Reachable under 1 %/trade and the 2 % daily halt? | **Only with an extraordinary, unproven edge, and never reliably.** With ≤ 10 trades, every trade must deliver **≥ 2.216R if all 10 win**, or **24.5R from a single trade**. At ≤ 2R per winner the target is **mathematically unreachable** at any win rate (10/10 winners at 2R = +21.90 %). |
| **S.** Exact reason | ① The per-trade gain is capped at 1 % × R of equity. ② The 10-trade cap bounds the number of gains. ③ The 2 % halt ends the day after about 2–3 losses. ④ **Optional-stopping theorem:** any strategy without positive edge has **P(target) ≤ 10.84 %** per day, whatever its entries, exits or sequencing. |
| **M.** Minimum practical trade count | **1 trade** only if it pays **24.5R** net, which a driftless market does with P = 1/25.5 ≈ **3.9 %** before costs. Otherwise **3 trades at ≥ 7.58R each, 5 at ≥ 4.48R, or 10 at ≥ 2.22R**, all winners. |
| **N.** Required reward:risk | ≥ 2.22R as an absolute floor (10/10 winners). Practical regimes need **4–10R** with high hit rates (tables below). |
| **O.** Required win rate | Depends on R: e.g. 4R needs ~70 % wins for a 63 % daily hit rate; 5R needs ~60 % for 59 %. A driftless market gives 20 % and 16.7 % at those R. |
| **T.** P(+24.5 % before −2 %) | Tables below. At **zero edge**: **0.0000–0.022** per day (with 0.15R cost). |
| **U.** 20-day compounded outcome | At zero edge, P(20/20 targets) ≈ **1e-25 or smaller**, and expected equity decays with costs. Even at a hypothetical **70 % win rate with 5R winners (+3.05R expected per trade)**, P(20/20) is only **1.2 %**. |
| **Required edge** | Any strategy hitting the target on a fraction h of days must have **expected daily return ≥ h·24.5 % − (1−h)·2.98 %**: h = 50 % needs ≥ **+10.76 %/day expected**, and 20/20 days with 50 % probability (h = 96.6 %) needs ≥ **+23.57 %/day expected**. |

**"Strictly no loss" is not achievable and is not promised.** It is translated into the constraints listed in the Capital Velocity design: fixed ≤ 1 % loss per trade, the 2 % daily halt, and no stop widening, re-entry, doubling or target chasing.

## 1. Ideal compounding ($200, +24.5 %/day, 20 days)
| Day | Start equity | Profit objective | Target equity |
|---|---|---|---|
| 1 | $200.00 | $49.00 | $249.00 |
| 2 | $249.00 | $61.01 | $310.01 |
| 3 | $310.01 | $75.95 | $385.96 |
| 4 | $385.96 | $94.56 | $480.52 |
| 5 | $480.52 | $117.73 | $598.24 |
| 6 | $598.24 | $146.57 | $744.81 |
| 7 | $744.81 | $182.48 | $927.29 |
| 8 | $927.29 | $227.19 | $1,154.48 |
| 9 | $1,154.48 | $282.85 | $1,437.32 |
| 10 | $1,437.32 | $352.14 | $1,789.47 |
| 11 | $1,789.47 | $438.42 | $2,227.89 |
| 12 | $2,227.89 | $545.83 | $2,773.72 |
| 13 | $2,773.72 | $679.56 | $3,453.28 |
| 14 | $3,453.28 | $846.05 | $4,299.33 |
| 15 | $4,299.33 | $1,053.34 | $5,352.67 |
| 16 | $5,352.67 | $1,311.40 | $6,664.07 |
| 17 | $6,664.07 | $1,632.70 | $8,296.77 |
| 18 | $8,296.77 | $2,032.71 | $10,329.48 |
| 19 | $10,329.48 | $2,530.72 | $12,860.20 |
| 20 | $12,860.20 | $3,150.75 | $16,010.95 |

| R per winner | Winners needed (no cost) | Winners needed (0.15R cost/trade) | Reachable within 10 trades? |
|---|---|---|---|
| 1 | 23 | 26 | **NO** |
| 1.5 | 15 | 17 | **NO** |
| 2 | 12 | 12 | **NO** |
| 2.5 | 9 | 10 | yes |
| 3 | 8 | 8 | yes |
| 4 | 6 | 6 | yes |
| 5 | 5 | 5 | yes |
| 10 | 3 | 3 | yes |
| 24.5 | 1 | 2 | yes |

| W wins / L losses | R=2 | R=2.5 | R=3 | R=4 | R=5 |
|---|---|---|---|---|---|
| 10/0 | +21.90% | +28.01% | +34.39% | +48.02% | +62.89% |
| 9/1 | +18.31% | +23.64% | +29.17% | +40.91% | +53.58% |
| 8/1 | +15.99% | +20.62% | +25.41% | +35.49% | +46.27% |
| 7/1 | +13.72% | +17.68% | +21.76% | +30.28% | +39.30% |
| 6/1 | +11.49% | +14.81% | +18.21% | +25.27% | +32.67% |
| 5/1 | +9.30% | +12.01% | +14.77% | +20.45% | +26.35% |
| 8/2 | +14.83% | +19.42% | +24.16% | +34.13% | +44.81% |
| 7/3 | +11.46% | +15.34% | +19.33% | +27.68% | +36.53% |
| 5/2 | +8.21% | +10.89% | +13.62% | +19.24% | +25.09% |
| 3/1 | +5.06% | +6.61% | +8.18% | +11.36% | +14.60% |
| 2/0 | +4.04% | +5.06% | +6.09% | +8.16% | +10.25% |
| 1/0 | +2.00% | +2.50% | +3.00% | +4.00% | +5.00% |

**P(reach +24.5 % before -2 % halt, <= 10 trades), cost 0.0 R/trade**

| R \ win rate | 0.30 | 0.40 | 0.50 | 0.60 | 0.70 | 0.80 | 0.90 |
|---|---|---|---|---|---|---|---|
| 2 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 2.5 | 0.000 | 0.000 | 0.002 | 0.010 | 0.040 | 0.134 | 0.387 |
| 3 | 0.000 | 0.004 | 0.020 | 0.071 | 0.196 | 0.436 | 0.775 |
| 4 | 0.012 | 0.058 | 0.178 | 0.389 | 0.654 | 0.880 | 0.987 |
| 5 | 0.055 | 0.179 | 0.390 | 0.640 | 0.849 | 0.965 | 0.998 |
| 10 | 0.449 | 0.670 | 0.828 | 0.922 | 0.971 | 0.992 | 0.999 |

**P(reach +24.5 % before -2 % halt, <= 10 trades), cost 0.15 R/trade**

| R \ win rate | 0.30 | 0.40 | 0.50 | 0.60 | 0.70 | 0.80 | 0.90 |
|---|---|---|---|---|---|---|---|
| 2 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 2.5 | 0.000 | 0.000 | 0.001 | 0.006 | 0.028 | 0.107 | 0.349 |
| 3 | 0.000 | 0.002 | 0.012 | 0.049 | 0.154 | 0.383 | 0.740 |
| 4 | 0.010 | 0.052 | 0.164 | 0.366 | 0.628 | 0.859 | 0.979 |
| 5 | 0.044 | 0.153 | 0.347 | 0.587 | 0.803 | 0.936 | 0.989 |
| 10 | 0.335 | 0.536 | 0.704 | 0.826 | 0.907 | 0.960 | 0.990 |

**P(reach +24.5 % before -2 % halt, <= 10 trades), cost 0.3 R/trade**

| R \ win rate | 0.30 | 0.40 | 0.50 | 0.60 | 0.70 | 0.80 | 0.90 |
|---|---|---|---|---|---|---|---|
| 2 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 2.5 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 3 | 0.000 | 0.002 | 0.011 | 0.046 | 0.149 | 0.376 | 0.736 |
| 4 | 0.004 | 0.024 | 0.088 | 0.227 | 0.455 | 0.730 | 0.942 |
| 5 | 0.042 | 0.149 | 0.342 | 0.583 | 0.800 | 0.935 | 0.989 |
| 10 | 0.311 | 0.516 | 0.693 | 0.822 | 0.907 | 0.960 | 0.990 |

| R | zero-edge win rate 1/(1+R) | P(target) | P(-2 % halt) | E[day return] | P(all 20 days) |
|---|---|---|---|---|---|
| 3 | 0.250 | 0.0000 | 0.756 | -0.0075 | 4.3e-89 |
| 4 | 0.200 | 0.0008 | 0.745 | -0.0070 | 2.8e-62 |
| 5 | 0.167 | 0.0024 | 0.806 | -0.0063 | 5.7e-53 |
| 10 | 0.091 | 0.0201 | 0.826 | -0.0051 | 1.2e-34 |
| 24.5 | 0.039 | 0.0222 | 0.923 | -0.0039 | 8.3e-34 |

| Required daily target hit rate h | Minimum expected daily return (any strategy) | Implied P(all 20 days) |
|---|---|---|
| 0.1 | -0.23% | 1e-20 |
| 0.25 | +3.89% | 9.09e-13 |
| 0.5 | +10.76% | 9.54e-07 |
| 0.75 | +17.63% | 0.00317 |
| 0.9 | +21.75% | 0.122 |
| 0.966 | +23.57% | 0.501 |
| 0.99 | +24.23% | 0.818 |

Day 20 ends at **$16,010.95**: 80.05 × the starting balance. Extracted profit if reset to $200 is $15,810.95. These are mathematical targets, not forecasts.

## 2. Winners required (fixed 1 % risk, in-day compounding)
The R table above lists, for each R, the minimum number of consecutive full winners, (1 + 0.01·(R − c))ⁿ ≥ 1.245. Any row needing **more than 10 winners cannot meet the target under the 10-trade cap**, so the 1R, 1.5R and 2R rows are infeasible. The win/loss table shows the net day return for mixed outcomes. A single loss costs about 1 %, so mixed days need even larger R.

## 3. Probability of reaching +24.5 % before the −2 % halt
The exact DP tables above assume i.i.d. trades with win rate p and payoff R. Costs are charged in R units: 0.15R is typical for XAUUSD at minimum lot with a 1×ATR(M5) stop (see the cost audit). Trades are capped at 10 per day.

## 4. The zero-edge baseline and the general bound
For a driftless price the probability of hitting +kR before −1R is 1/(1+k). With those win rates the target is essentially never reached (table above).

**The bound holds for every strategy.** If no trade has positive expected value, equity is a supermartingale. The lowest equity at which a day can end is W_min = 0.98 × 0.99 = 0.9702: one more full loss just above the halt line. By optional stopping:

  P(target) ≤ (1 − W_min)/(1.245 − W_min) = **10.84 %**.

The bound rises slightly to 11.3 % when W_min is computed with costs. It is loose: real zero-edge strategies achieve 0–6 %. The required-edge table inverts it: the minimum expected daily return any strategy needs for a daily hit rate h.

## 5. Dependence between trades
The DP assumes independent trades. Positively correlated trades in one session, such as several breakout entries on the same move, raise the variance of the day's result, not its mean. The supermartingale bound in §4 and the required-edge inequality need **no** independence assumption, so the conclusion stands.

## 6. Instrument feasibility at $200 (real Pepperstone specs; see the cost and sizing audit)
- **XAUUSD.** Minimum lot 0.01 = $1 per $1 move. 1 % of $200 = $2.00, minus about $0.20 spread and commission, leaves a stop of **≤ $1.80**. The last 12 months of XAUUSD ATR(14) were: **M5 median $5.00 (only 0.3 % of bars ≤ $1.75), M15 $8.96, H1 $18.88**. **At $200 a 1×ATR(M5) stop on XAUUSD violates the 1 % rule on 99.7 % of bars, so NO compliant XAUUSD trade exists for most of the day.** A median 1×ATR stop needs equity of roughly $525 (M5), $925 (M15) or $1,910 (H1).
- **NAS100.** Minimum lot 0.1 = $0.10 per index point, no commission, 1-point sampled spread. 1 % of $200 allows a stop of about **19 index points**. The ATR distribution cannot be measured: **no NAS100 history is held locally**.
- **Live EA constraint.** The live EA's `InpMaxSameCurrencyNet = 2` × minimum lot (B-EXPOSURE-CAP) limits each currency to 0.02 lots. It is unchanged here and would block the compounding path once the 1 % size exceeds that cap.

## 7. Conclusion
Under the unchanged hard rules, **+24.5 %/day is not reachable reliably by any strategy**. It can be reached occasionally only with a large, demonstrated per-trade edge. NEXA has no such evidence for any engine (see `NEXA_8_ENGINE_RESULTS.md`).

Raising the hit rate would require changing what the rules forbid: risk per trade, the daily loss halt or the trade cap. **That is not done here.** For reference: a single trade reaching +24.5 % at 3R needs **8.2 % risk per trade**; at 5R, 4.9 %. Either would breach the 1 % ceiling and could exhaust the 2 % daily halt in one trade.
