# S16: Poudel & Paudel (2025), "Quantitative Trading Strategy, Backtesting, and Performance Analysis Using Python: A Data-Driven Analysis"
**File:** `Quantitative_Trading_Strategy_Backtesting_and_Perf.pdf`. 20 pp.
**Publication:** Quest Journal of Management and Social Sciences 7(2):219–238, doi:10.3126/qjmss.v7i2.87782. Authors at Lumbini Banijya Campus, Nepal.

| Field | Value |
|---|---|
| **Source type** | Other academic institution. A peer-reviewed journal, low-tier and regional. |
| **Evidence status** | **Unverified claim / weak evidence.** In-sample backtest on an index; incomplete rules; internal inconsistencies (see below). |
| **Processing** | All 20 pages read. Figures 2–14 are charts; their stated statistics are in the text and tables, which were read. |

## Content (SOURCE)
**Data and rules**
- NEPSE index, daily, Jul-1997 → Mar-2025: 6,298 observations.
- Long-only. Signals combine:
  - a z-score (window 15) for extremes;
  - RSI thresholds (35 / 60 in the base case);
  - an MA240 trend filter;
  - an MA70 "stop" for mean reversion.
- Constraints:
  - at most 4 open trades;
  - cooldowns (momentum 4, mean reversion 3);
  - risk-based sizing;
  - a 4 % stop for momentum;
  - a stated reward:risk of 1:4.5.
- Costs: a fixed 0.25 % "execution adjustment" on exits only.

**Results**

| Metric | Quant | Buy & Hold |
|---|---|---|
| Total return | 2,877 % | 1,454 % |
| CAGR | 14.38 % | 11.47 % |
| Max drawdown | −28.11 % | −75.16 % |
| Sharpe | 1.39 | 0.64 |
| Sortino | 1.35 | 0.89 |

- Win rate 53.64 %, profit factor 3.38; in the market 49.5 % of days.
- **On active days only, B&H had the *higher* mean log return** (0.0014 vs 0.0011) (Table 2).
- **Monte Carlo:** 20,000 resampled paths; all profitable; average max drawdown −10.2 %.
- **Statistical tests:**
  - KS test: return distributions differ (p ≈ 0).
  - Z-test on Sharpe ratios (daily 0.0843 vs 0.0339): z = 4.01, p = 0.0001.

## Methodological problems (INFERENCE, grounded in the text)
1. **The index is not tradable.** There are no tradable-instrument costs, liquidity or slippage. The 0.25 % exit-only adjustment is not a cost model.
2. **No train / test split.** The parameters were chosen and evaluated on the full 1997–2025 sample, and the "sensitivity analysis" re-uses the same data. This is **in-sample only**.
3. **The rules are not fully specified.** The exact entry conditions combining z, RSI and MA are not given, so the strategy is not reproducible.
4. **The Monte Carlo resamples the strategy's own trades.** It cannot "rule out overfitting or randomness" as claimed; it only reshuffles the order of trades that were already selected.
5. **Internal inconsistencies**
   - The Monte Carlo is described as 20,000 paths (Table 6) and as 10,000 (Discussion).
   - The sensitivity text quotes Sharpe 1.34 / Sortino 1.22 / PF 3.34 → 3.05 / RF 99.23 → 84.13, while the tables show 1.32 / 1.24 / 3.12 / 92.55.
   - The Discussion says "confirming H1" while describing risk-adjusted returns (H2).
   - It mentions an ADF test that is not reported in the Results.
6. **Comparing a ~50 %-invested strategy's Sharpe with B&H's** is largely an exposure/drawdown effect (cash in bear markets). The MA240 filter mechanically avoids drawdowns.
7. **"Unit-root pretesting is methodologically unnecessary"** is asserted, citing a thesis. This is debatable.

## Principles worth keeping
- **Trend-filtered mean reversion** (buy oversold only when above the long MA) is a common construction. It is also the structure of Connors-type rules (S22 lists RSI/MA strategies).
- **"Better Sharpe than B&H" often comes from being out of the market in downtrends.** This is a regime-filter effect, not timing skill. It parallels NEPSE / Buy & Hold here and S03's long-only-beats-RL in equities.
- **Lo (2002) Sharpe statistics, the Jobson–Korkie test, and the Magdon-Ismail Brownian maximum-drawdown result** are cited. They are valuable methods, but they are **not applied** correctly here (e.g. no serial-correlation adjustment).

## NEXA relevance
- **A negative example for validation design.** Use it as a checklist of what NEXA's protocol already prevents:
  - in-sample-only evaluation;
  - a trade-resampling Monte Carlo presented as proof;
  - an undefined cost model;
  - an untradable index.
- **Hypothesis seed (low prior):** a z-score + RSI mean-reversion entry gated by a long-MA regime on XAU / FX H1–D1, tested out of sample with real costs.

**Cross-references:** S12 / S20 (other student-level backtests), S08 (practitioner backtests), S22 (RSI / MA strategies), S14 Jin (proper statistical methods).
