# Pepperstone cost and sizing audit: XAUUSD, NAS100 (EURUSD/GBPUSD controls). 2026-10-01

**How the data was obtained.** All values were measured read-only.
- `NEXA_SpecProbe.mq5` and `NEXA_TickProbe.mq5` ran in the Strategy Tester. Neither places orders.
- Inputs: the local M1 history (2017–2026) and the 21-day tick files.
- The FX and XAU evidence are kept separate, as required.

**Provenance.**
- `data/pepperstone/spec_probe/spec_probe_20261001.csv` (sha `daec08bd…`)
- `tick_probe_20261001.csv`
- `research/runs_8e/{capital_200_feasibility, tp10pip_feasibility, spread_truth_audit, xau_spread_profile, xau_spread_by_hour, cost_sensitivity_dev, m1_gap_audit}.txt`

## 1. Contract specification (PROVEN)
| Symbol | Contract | Tick size | $ per 1.0 price per lot | Min / step lot | $ per 1.0 price at min lot | Commission | Stops / freeze level | Margin at min lot (tester 1:100) |
|---|---|---|---|---|---|---|---|---|
| XAUUSD | 100 oz | 0.01 | 100 | 0.01 / 0.01 | $1.00 | $3.50/lot/side ($0.08 round trip at 0.01) | 0 / 0 | $42.91 |
| NAS100 | 1 | 0.1 | 1 | 0.1 / 0.1 | $0.10 | 0 (in the spread) | 0 / 0 | $15.27 |
| EURUSD | 100,000 | 0.00001 | 100,000 | 0.01 / 0.01 | $1,000 | $3.50/lot/side | 0 / 0 | $11.38 |
| GBPUSD | 100,000 | 0.00001 | 100,000 | 0.01 / 0.01 | $1,000 | $3.50/lot/side | 0 / 0 | $13.24 |

- US100 and USTEC are not offered. NAS100 swap mode is "interest".
- The live account leverage (1:200) differs from the tester's. Margin is never the binding constraint at $200; the minimum lot is.

## 2. $200 feasibility (items A–F)
**A. Valid instruments at $200, 1 % risk, min lot, all-in costs**

| Symbol | Maximum stop | Valid? |
|---|---|---|
| EURUSD | 19.1 pips | VALID |
| GBPUSD | 18.8 pips | VALID |
| XAUUSD | **$1.684** | Technically valid; broker stops level 0 |
| NAS100 | **18 pts** | Technically valid |

**B. Invalid at realistic stops.**
- **XAUUSD** (min-lot risk as a share of $200, and the equity that makes it 1 %):

| Stop basis | Stop | Min-lot risk | Equity needed for 1 % |
|---|---|---|---|
| M5 ATR median | $5.00 | 2.66 % | $532 |
| M15 ATR median | $9.10 | 4.71 % | $942 |
| H1 ATR median | $18.88 | 9.60 % | $1,920 |

- **NAS100** (assumed stops):

| Stop | Min-lot risk | Equity needed for 1 % |
|---|---|---|
| 20 pts | 1.10 % | $220 |
| 40 pts | 2.10 % | $420 |

**C. Minimum equity:** see the "Equity needed for 1 %" column in each table above. EUR $69 and GBP $92 at an M15-ATR-scale stop.

**D. Minimum stop.** The broker allows any stop (stops level 0, freeze level 0). The binding limit is the cost share:

| XAU stop | All-in cost per R |
|---|---|
| $1.68 | 18.8 % |
| M5 ATR | 6.3 % |
| M15 ATR | 3.5 % |

**E. Technical viability.** XAU and NAS100 at $200 are technically **valid only with micro-stops**. Only 0.3 % of XAU M5 ATR values are ≤ $1.75.

**F. Statistical viability (XAU, last 12 months of M1, 20,000 random entries, 8 h horizon)**

| Stop | Target | P(target first) | Driftless P | Expectancy after cost |
|---|---|---|---|---|
| $1.68 | 2R | 0.327 | 0.333 | **−0.207R** |
| $1.68 | 5R | 0.163 | 0.167 | −0.212R |
| $5.00 | 2R | 0.326 | 0.333 | −0.086R |
| $9.10 | 2R | 0.315 | 0.333 | −0.075R |

- **Micro-stops are statistically non-viable:** price is close to driftless at these scales, and cost takes 19 % of every R.
- **NAS100: DATA-LIMITED.** There is no M1 or tick history and no ATR distribution; the tester returned 1 tick.

## 3. XAUUSD cost validity (PROVEN for the 21-day tick sample; 2018–2026 for recorded M1)
**What the recorded spread is.** The recorded M1 spread equals the **minute-minimum** tick spread in 96.8 % of minutes, so it understates the typical spread. The true tick spread has median 12 pts, mean 11.8, p75 13, p90 14, p95 17, p99 18 (1 pt = $0.01).

**By UTC hour** (`xau_spread_by_hour.txt`; tick time = server − 3 h):
- 00–15 UTC: true median 12–13, p99 16–20.
- 16–19 UTC: 9, p99 14–16.
- 20 and 22 UTC: **17**, p99 20 (pre- and post-rollover).
- 21 UTC: no quotes (rollover break).
- Recorded minimum median: 8–9 in 13–15 UTC; 14–16 in 21–23 UTC.

**By session:**

| Session | True median / p99 | Recorded median / p99 |
|---|---|---|
| Asia | 12 / 17 | 11 / 42 |
| London | 12 / 18 | 9 / 29 |
| Overlap | 12 / 18 | 8 / 25 |
| NY late | 9 / 17 | 10 / 38 |
| Rollover 21–24 UTC | 14 / 20 | 14 / 94 |

**By day:** Sunday median 14 (p99 20); every other weekday 12 (p99 17–18).

**By volatility tercile** (recorded): low 11 / mid 10 / high 9 (median); p99 48 / 40 / 28. Spreads do **not** widen in high-ATR regimes here.

**By news regime** (recorded; within 30 min of a HIGH USD release vs otherwise): median 8 vs 10; p99 27 vs 42. Minute-minimum masks spikes; true tick news spreads are **not measured** (21-day sample).

**Spread as a share of the trade:**

| Stop basis | Spread / stop | Spread / TP 2R | Spread / TP 3R | Spread / TP 5R | All-in cost / stop |
|---|---|---|---|---|---|
| M15 ATR | 1.3 % | 0.6 % | 0.4 % | 0.3 % | 3.5 % |
| M5 ATR | 2.4 % | 1.2 % | 0.8 % | 0.5 % | 6.3 % |
| $1.75 | 6.7 % | 3.4 % | 2.2 % | 1.3 % | 18.1 % |

**Cost as a share of gross profit** (DEV baseline Donchian, 72 bases):
- Note that the harness's `r_gross` is already net of the bid/ask spread (fills at ask, exits at bid) and before commission and slippage.
- On that basis, gross R is ≤ 0 in **70/72** bases (−0.64 … +0.013).
- In the 2 bases with positive gross, the total mean cost (0.10–0.19R per trade) is **7.5× and 37×** the gross edge.

## 4. FX cost-sensitivity protocol (EUR/GBP; kept separate from XAU)
**Why a protocol is needed.** The recorded FX spread is the minute minimum.
- The median recorded spread is **0**.
- True tick medians: EUR 0, with 84 % of ticks at zero spread (mean 0.65 pts); GBP 1 (mean 2.08).
- Understatement vs the minute mean: EUR 0.28 pts, GBP 1.49 pts.

**DEV mean expectancy over 96 configs:**

| Scenario | EURUSD | GBPUSD |
|---|---|---|
| Recorded floor (minute minimum) | −0.359 | −0.296 |
| Minute mean | −0.365 | −0.318 |
| Conservative (p90) | −0.378 | −0.331 |
| Conservative ×2 | −0.397 | −0.369 |
| Conservative ×3 | −0.417 | −0.409 |

**Share of configs positive:**
- EUR: 2.1 % → 0 % at ×3.
- GBP: 7.3 % → 3.1 % at ×3.

FX conclusions are **cost-robust in sign** (negative everywhere). Any marginal FX positive must survive ×2 at minimum.

## 5. Cost minimisation for +24.5 %
- **Net profit per trade.** Cost per R falls as the stop widens. At $200, though, a wider stop forces a below-min-lot size on XAU and NAS100. **The $200 constraint and the cost constraint act in opposite directions** for XAU and NAS100. Only FX resolves both, and its edge is negative on DEV.
- **10-pip TP** (`tp10pip_feasibility.txt`):
  - **XAU ($1.00):** unreachable at any stop. With 10/10 winners the maximum is +21.86 %; costs are 30.6 % of the TP.
  - **EUR / GBP:** they need stops ≤ 2.96 / 2.51 pips. Driftless P(10/10) is 3.8·10⁻⁷ / 1.1·10⁻⁷.
- **Trades/day vs required average net R:**

| Trades/day | Required average net R |
|---|---|
| 1 | 24.5 |
| 2 | 11.58 |
| 3 | 7.58 |
| 4 | 5.63 |
| 5 | 4.48 |
| 6 | 3.72 |
| 7 | 3.18 |
| 8 | 2.78 |
| 9 | 2.47 |
| 10 | 2.216 |

  These figures use compounding and assume every trade wins. They are not reachable by any DEV stream; the empirical maximum single day was +20.2 % at $10k.

## 6. Classification
| Item | Status |
|---|---|
| Spec, commission, minimum lot, stops level | PROVEN |
| XAU true spread (21 days) | PROVEN |
| Recorded spread is the minute minimum | PROVEN |
| FX historical cost level | DATA-LIMITED (floor only) |
| XAU at $200 | technically valid only with micro-stops; statistically CONTRADICTED |
| NAS100 | DATA-LIMITED |
| News-time true spreads | DATA-LIMITED |
