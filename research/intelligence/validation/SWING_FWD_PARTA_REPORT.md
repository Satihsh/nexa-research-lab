# H-SWING-FWD Part A: does 12-month trend timing on ES + NQ beat simply holding them? (2026-10-18)

- **Pre-registration:** `PREREG_SWING_FWD.md` (117a53b6), before any data. Deviation D-1 (log truncation) in `DEVIATIONS_SWING_FWD.md`.
- **Run (once, QC free node):**
  - project 38036244 "NEXA/SWING-FWD", backtest "Alert Green Caterpillar";
  - code be25c85c, editor hash verified before the run;
  - data to 2026-07-20.
- **Outputs:** raw log `qc_swing_fwd/logs_alert_green_caterpillar.txt` (sha ed3dd78d), parsed `qc_swing_fwd/parta_results.json` (complete part only, see D-1).
- **Window HIST:** 2011-01-03 → 2026-07-21, 4,005 days. Costs S1 (2 ticks + $2.50 round trip).

## Verdict A1: DRIFT ONLY
**V-IDX's positive H-SWING result came from being long two rising indices, not from trend timing.**

| ES + NQ rule | Ann. net return | Ann. vol | Sharpe | Mean daily net | 95 % CI | Max DD* | Green months |
|---|---|---|---|---|---|---|---|
| V-IDX (12-month trend, long or short) | +18.9 % | 40.6 % | 0.47 | +7.51 bp | [+0.32, +14.43] | 113 % | 59.9 % |
| **LONG-IDX (always long, same sizing)** | **+30.4 %** | 41.2 % | **0.74** | **+12.05 bp** | [+5.36, +19.02] | 80 % | 64.2 % |
| BH-IDX (plain buy-and-hold, 1× notional) | +14.8 % | 18.4 % | **0.80** | +5.86 bp | [+2.81, +8.98] | 35 % | 64.7 % |

*Summed-return drawdown at each rule's own sizing; above 100 % means the sizing would have wiped out the account.

- **A1 statistic:** mean daily V-IDX − LONG-IDX = **−4.54 bp/day** (≈ −11 %/yr at this leverage). This is ≤ 0, so **DRIFT ONLY** by the pre-registered rule. The bootstrap CI was lost to log truncation (D-1); the label does not depend on it.
- **A2 (descriptive):**
  - V-IDX − BH-IDX = +1.65 bp/day, only because V-IDX runs at ~2.2× BH-IDX's volatility.
  - **Risk-adjusted, timing is worse:** Sharpe 0.47 vs 0.74 (always long, same size) vs 0.80 (buy-and-hold).
- **Where the timing went wrong (yearly, V-IDX vs LONG-IDX):**
  - The two rules were identical in the 8 years the trend stayed long (2012–14, 2017, 2021, 2024–26).
  - Timing **helped in 1 year:** 2022, −18 % vs −49 %.
  - It **hurt in 6 years:** 2011 (−11 % vs +7 %), 2015, 2016, 2019 (−14 % vs +59 %), 2020, 2023 (+2 % vs +56 %). It went short or flat after declines and missed the rebounds.
- **A0, reproducibility:** HIST P (0.00021849) and V-IDX (0.00075084) match H-SWING exactly, so the data was not revised. The P − LONG re-check (A3) was in the truncated block and is deferred to the next checkpoint.

## What this means
1. **The ES + NQ variant is closed.** The only H-SWING variant that looked "validated" was equity drift plus leverage. The plain index did better per unit of risk.
2. **Part B (forward) continues for P,** the 20-market primary, as pre-registered. Its final, binding look is on or after 2028-01-03. Each checkpoint must use code v2 (chunked logging, D-1), which means creating a new QC project and verifying the editor hash before that run.
3. **This is not a recommendation to buy the index.** Buy-and-hold of ES/NQ is a market exposure, not an edge. It is also impossible at Topstep (no overnight positions) and lost 27 % in 2022 at 1× notional. NEXA gives no investment advice.
