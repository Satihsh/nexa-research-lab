# EQUATION PRIORITY MATRIX (37 registered equations)

**Scoring (each axis 1–5).** "Higher is better" on every axis:
- **F:** complexity, 5 = simple.
- **G:** overfitting risk, 5 = low risk.

| Axis | 5 means | 1 means |
|---|---|---|
| A Data availability | TRUE data on hand, ≥ 2 years | data unavailable |
| B Mathematical soundness | standard, verified, assumptions explicit | ad hoc or unverifiable |
| C Economic interpretation | clear mechanism | label only |
| D Testability | a clean null and a frozen test are possible now | untestable |
| E Expected usefulness for NEXA | feeds P_U, D or cost directly, with prior evidence | marginal |
| F Complexity | few parameters, closed form | many parameters or heavy fitting |
| G Overfitting risk | no free thresholds, robust | many tunable choices |

**Composite score** = A × D × (B + C + E + F + G) / 5, maximum 125.
- Availability and testability are **multiplicative gates**: an unavailable or untestable equation cannot rank high, however elegant.
- The scores are judgements, recorded so they can be challenged. They are **not results**.
- **Updated by evidence:** the 2026-10-04 T2 run (below) is included where it changes a score.

| Rank | EQ | Name | A | B | C | D | E | F | G | Score | Evidence update |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | EQ-025 | Net expectancy in R with costs | 5 | 5 | 5 | 5 | 5 | 5 | 5 | **125** | Accounting identity; anchors every test (A4: cost 0.245R) |
| 2 | EQ-001 | RV / quadratic variation | 5 | 5 | 4 | 5 | 5 | 5 | 5 | **120** | Target and input of HAR (a measurement, not a forecast) |
| 3 | EQ-024 | Driftless two-barrier null | 5 | 5 | 5 | 5 | 4 | 5 | 5 | **120** | The null for all stop/target work |
| 4 | EQ-004 | HAR log-RV forecast | 5 | 5 | 4 | 5 | 5 | 4 | 4 | **110** | **T2:** lowest holdout QLIKE on 4/4 symbols; significant vs ATR14 only on XAU (q 0.068). Best up/down hit rate (61–76 %) |
| 5 | EQ-005 | Seasonal baseline / RVOL | 5 | 5 | 4 | 5 | 4 | 5 | 4 | **110** | The hour-of-day profile is shared across sources (r 0.93–0.98, probe); **T1:** tick-vol ↔ futures-vol de-seasonalised r 0.60 / 0.60 / 0.45 / 0.55 (XAU/EUR/GBP/JPY); intraday shape JS ≈ 0.03; GBP FAILED |
| 6 | EQ-034 | Two-barrier probability with drift | 5 | 5 | 5 | 5 | 4 | 4 | 4 | **110** | Verified by Monte Carlo; the state→expectancy bridge |
| 7 | EQ-021 | Variance ratio | 5 | 5 | 4 | 5 | 3 | 5 | 4 | **105** | Existing H-VR-SCALE |
| 8 | EQ-019 | Compression ratio | 5 | 4 | 4 | 5 | 3 | 5 | 4 | **100** | — |
| 9 | EQ-003 | Parkinson | 5 | 5 | 3 | 5 | 2 | 5 | 5 | **100** | **T2:** worse than ATR14 in the holdout on 3/4 (significant on EUR, GBP) |
| 10 | EQ-020 | Efficiency ratio | 5 | 4 | 3 | 5 | 3 | 5 | 4 | **95** | Existing family |
| 11 | EQ-017 | Close location | 5 | 5 | 3 | 5 | 2 | 5 | 4 | **95** | Label for day type |
| 12 | EQ-033 | Decision rule | 5 | 5 | 5 | 4 | 5 | 4 | 4 | **92** | Framework, not a feature |
| 13 | EQ-026 | Futures→spot basis map | 4 | 4 | 5 | 5 | 4 | 5 | 5 | **92** | Basis drift measured (−$0.6/day GC); **T1:** ≤ 0.1σ on 99.5 / 99.9 / 97.3 % of hours (EUR/GBP/JPY) PASS; **XAU 88 % FAILED** (p95 0.24σ) |
| 14 | EQ-016 | IB and range extension | 5 | 4 | 3 | 5 | 3 | 5 | 3 | **90** | Needs session anchors (pre-registered) |
| 15 | EQ-002 | Yang–Zhang | 5 | 5 | 3 | 5 | **1** | 5 | 4 | **90** | **T2:** YZ20 significantly **worse** than ATR14 on EUR, GBP, XAU (q < 0.04). YZ5/YZ10 ≈ ATR14. **Usefulness downgraded** |
| 16 | EQ-023 | Markov/HMM regime transition | 5 | 5 | 3 | 5 | 3 | 3 | 3 | **85** | — |
| 17 | EQ-007 | Amihud illiquidity | 4 | 4 | 4 | 5 | 3 | 5 | 4 | **80** | — |
| 18 | EQ-018 | Rotation count | 5 | 3 | 3 | 5 | 2 | 4 | 3 | **75** | Codification is NEXA's own |
| 19 | EQ-022 | Permutation entropy | 5 | 4 | 2 | 5 | 2 | 4 | 3 | **75** | — |
| 20 | EQ-006 | Effort–result residual | 4 | 4 | 4 | 5 | 3 | 4 | 3 | **72** | — |
| 21 | EQ-014 | Value area (algorithmic) | 4 | 4 | 3 | 5 | 3 | 5 | 3 | **72** | Proxy VA Jaccard 0.82 (1-month probe); **T1:** proxy POC within 0.25σ on 74 / 67 / 57 / 75 % of days; VA Jaccard 0.71–0.82; bimodal-day failure 47–62 %; GBP FAILED |
| 22 | EQ-039 | Absorption index | 4 | 3 | 4 | 5 | 3 | 5 | 3 | **72** | Same family as EQ-006 |
| 23 | EQ-012 | Revealed-liquidity field L(p,t) | 4 | 4 | 3 | 5 | 3 | 3 | 3 | **64** | Bandwidth, allocation and memory are free choices (overfitting risk) |
| 24 | EQ-015 | Profile concentration (entropy) | 4 | 4 | 3 | 5 | 2 | 4 | 3 | **64** | — |
| 25 | EQ-013 | Field gradient / curvature | 4 | 4 | 3 | 5 | 3 | 3 | 2 | **60** | — |
| 26 | EQ-030 | Stop-rule family (H1–H5) | 4 | 4 | 4 | 4 | 4 | 3 | 2 | **54.4** | H1 blocked |
| 27 | EQ-038 | Liquidity potential (analogy) | 4 | 3 | 2 | 5 | 1 | 4 | 3 | **52** | Identical to EQ-013; notation only |
| 28 | EQ-032 | WHERE/WHEN MI decomposition | 3 | 5 | 4 | 4 | 4 | 3 | 3 | **45.6** | Proxies only |
| 29 | EQ-010 | Normalised delta | 2 | 4 | 3 | 4 | 2 | 5 | 4 | **28.8** | Proxy input |
| 30 | EQ-009 | BVC delta | 2 | 3 | 3 | 3 | 2 | 5 | 3 | **19.2** | Same-bar circular; unvalidated |
| 31 | EQ-035 | Hawkes intensity | 2 | 5 | 3 | 3 | 2 | 2 | 3 | **18** | 28 days of ticks |
| 32 | EQ-008 | Tick-rule OBI (f30) | 2 | 3 | 2 | 2 | 2 | 5 | 3 | **12** | Non-reproducible offline |
| 33 | EQ-029 | Hedge-pressure ratio | 1 | 3 | 5 | 1 | 3 | 5 | 4 | **4** | Needs OI; the first quantity to measure if OI is acquired |
| 34 | EQ-031 | Delta-hedged P&L | 1 | 5 | 5 | 1 | 1 | 4 | 4 | **3.8** | Explanatory only |
| 35 | EQ-011 | Two-flow price impact | 1 | 4 | 5 | 1 | 2 | 4 | 3 | **3.6** | No flow data |
| 36 | EQ-027 | Per-strike GEX | 1 | 4 | 4 | 1 | 2 | 4 | 3 | **3.4** | No OI; sign unidentified |
| 37 | EQ-028 | Gamma flip | 1 | 4 | 4 | 1 | 2 | 3 | 3 | **3.2** | Needs EQ-027 |

## Reading the matrix

**Top tier (score ≥ 100):** the volatility/variance machinery and the outcome mathematics:
- EQ-001, 004, 005, 021, 024, 025, 034;
- EQ-003 and 019 as baselines.

**Middle tier (60–99):** auction/profile structure (EQ-012–018) and activity measures (EQ-006, 007).
- They are testable now.
- **Most carry free design choices**, so they score lower on overfitting risk G.

**Bottom tier:** every options/GEX equation and every true-flow equation. **The data gate (A = 1–2) dominates, not the mathematics.**

**Evidence changed one ranking materially.** Yang–Zhang was expected (S48: "most efficient estimator") to beat ATR. In NEXA's own data it does not, at the pre-registered n = 20.

**Plausible reason (INFERENCE, to be tested, not assumed):**
- FX and XAU trade about 24 hours, so the "overnight" component YZ is designed to handle is nearly empty.
- With n = 20 the estimator is slow relative to volatility clustering; short windows (YZ5/YZ10) recover to ≈ ATR.
- The efficiency claim concerns *estimating the current σ* from a fixed sample, not *forecasting next-day RV*.
