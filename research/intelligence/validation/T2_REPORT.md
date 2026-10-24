# T2 REPORT: Yang–Zhang and HAR vs ATR / RV / range volatility forecasts

**Pre-registration:** `PREREG_T2_VOLATILITY.md`. The hash was recorded in `PREREG_HASHES.txt` before the run.
**Code:** `t2_volatility.py`. **Raw output:** `t2_results.json`, `t2_run.log`. Run on 2026-10-04.
**Data:** Pepperstone M1 canonical (bid) for 4 symbols, 2017-07 (XAU 2018-01) → 2026-09-25, server days.
**Holdout:** 2025-01 → 2026-09-25 (≈ 449 days per symbol).
**Deviations:** none.

## 1. Pre-registered verdict

**HYP-001b ("YZ or HAR beats ATR(14)"): REJECTED.**

The rule required a significant win (BH q < 0.10) on at least 3 of 4 symbols. HAR's lower holdout QLIKE than ATR(14) is significant only on XAUUSD. YZ(20) never beats ATR(14). It is significantly *worse* on three symbols.

| Holdout, h = 1 | HAR vs ATR14: DM t | q (BH) | YZ20 vs ATR14: DM t | q (BH) |
|---|---|---|---|---|
| EURUSD | −1.57 | 0.191 | **+2.54** (YZ worse) | 0.038 |
| GBPUSD | −1.54 | 0.196 | **+3.68** (YZ worse) | 0.003 |
| USDJPY | −1.48 | 0.215 | −0.19 | 0.939 |
| XAUUSD | **−2.20** | **0.068** | **+2.64** (YZ worse) | 0.031 |

A negative t means a lower loss than ATR(14).

## 2. Forecast error (holdout QLIKE, h = 1; lower is better)

| Model | EURUSD | GBPUSD | USDJPY | XAUUSD |
|---|---|---|---|---|
| **HAR** | **0.162** | **0.124** | **0.298** | **0.160** |
| ATR7 | 0.166 | 0.125 | 0.346 | 0.189 |
| ATR14 (baseline) | 0.180 | 0.136 | 0.368 | 0.245 |
| ATR28 | 0.205 | 0.151 | 0.381 | 0.313 |
| RV1 (random walk) | 0.184 | 0.138 | 0.307 | 0.197 |
| EWMA 0.94 | 0.190 | 0.146 | 0.354 | 0.263 |
| YZ5 | 0.179 | 0.129 | 0.338 | 0.217 |
| YZ10 | 0.177 | 0.135 | 0.355 | 0.244 |
| **YZ20** | 0.194 | 0.150 | 0.359 | 0.303 |
| YZ60 | 0.226 | 0.172 | 0.408 | 0.419 |
| Parkinson20 | 0.194 | 0.151 | 0.360 | 0.281 |
| Garman–Klass20 | 0.188 | 0.147 | 0.360 | 0.292 |
| Rogers–Satchell20 | 0.191 | 0.147 | 0.361 | 0.303 |
| Close-to-close20 | 0.225 | 0.168 | 0.376 | 0.306 |
| Mean RV 20d | 0.201 | 0.154 | 0.364 | 0.288 |

**Observations:**
- **HAR has the lowest point estimate on all 4 symbols.** Under the pre-registered ranking rule, though, it is **not declared "best"** because the DM test does not separate it from the runner-up. Its margin over ATR(7) is not significant: HAR vs ATR7 q = 0.62 (EUR), 0.93 (GBP), 0.28 (JPY) and 0.09 (XAU).
- **ATR(7) beats ATR(14)** with q ≈ 0.05 on GBPUSD and XAUUSD (EUR 0.12, JPY 0.13). **Shorter memory is the main thing that helps.** The same pattern shows across the YZ windows (5 < 10 < 20 < 60 in loss).
- **h = 5:** HAR is lowest on EUR (0.102) and XAU (0.202); ATR7 on GBP (0.075 vs HAR 0.077); RVM20 on JPY (0.261). No HAR h = 5 DM test against ATR14 was pre-registered as decisive. Descriptive only.

## 3. Directional usefulness (holdout)

**(a) Hit rate for "next-day RV above the trailing 60-day median"**, with a 95 % block-bootstrap CI:

| | EURUSD | GBPUSD | USDJPY | XAUUSD |
|---|---|---|---|---|
| HAR | **0.61** [0.55, 0.67] | **0.64** [0.57, 0.70] | **0.61** [0.55, 0.66] | **0.76** [0.72, 0.83] |
| ATR14 | 0.57 [0.48, 0.65] | 0.53 [0.43, 0.62] | 0.56 [0.48, 0.62] | 0.67 [0.60, 0.77] |
| YZ20 | 0.55 [0.46, 0.63] | 0.49 [0.38, 0.58] | 0.57 [0.49, 0.63] | 0.69 [0.63, 0.77] |
| EWMA | 0.48 | 0.51 | 0.51 | 0.63 |

- **HAR is the only forecaster whose CI excludes 50 % on all four symbols.** ATR(14)'s CI excludes 50 % only on XAU.
- This is a pre-registered secondary metric. It is **not** part of the decision rule.

**(b) Spearman(forecast, next-day high−low range):**

| | EURUSD | GBPUSD | USDJPY | XAUUSD |
|---|---|---|---|---|
| HAR | 0.56 | 0.37 | 0.53 | 0.63 |
| ATR14 | 0.55 | 0.35 | 0.52 | 0.56 |
| YZ20 | 0.53 | 0.33 | 0.37 | 0.55 |

## 4. Regime stability

**QLIKE by calendar year (holdout):**

| | 2025: HAR | 2025: ATR14 | 2026: HAR | 2026: ATR14 |
|---|---|---|---|---|
| EURUSD | 0.171 | 0.185 | 0.150 | 0.173 |
| GBPUSD | 0.124 | 0.135 | 0.125 | 0.139 |
| USDJPY | 0.167 | 0.178 | **0.476** | **0.626** |
| XAUUSD | 0.119 | 0.184 | 0.215 | 0.329 |

- **HAR ≤ ATR14 in every symbol-year.**
- **USDJPY 2026 is a loss regime for every model** (QLIKE roughly 3× its 2025 level). This is a structural break, not a model difference.

**QLIKE by RV tercile** (discovery cut-points):
- **All models lose most in the top tercile.** HAR's top-tercile loss is lower than ATR14's on all four symbols (EUR 0.30 vs 0.34; GBP 0.42 vs 0.50; JPY 0.38 vs 0.48; XAU 0.18 vs 0.28).
- **In the bottom tercile the ordering is mixed.** For USDJPY, YZ20 is worst at 0.55.

**Splits (h = 1 QLIKE, HAR vs ATR14):**

| Split | EURUSD | GBPUSD | USDJPY | XAUUSD |
|---|---|---|---|---|
| Discovery | 0.112 vs 0.137 | 0.123 vs 0.181 | 0.239 vs 0.287 | 0.164 vs 0.220 |
| Validation | **0.140 vs 0.140** | **0.119 vs 0.116** | 0.284 vs 0.353 | 0.126 vs 0.146 |
| Holdout | 0.162 vs 0.180 | 0.124 vs 0.136 | 0.298 vs 0.368 | 0.160 vs 0.245 |

**HAR's advantage is not uniform over time.** In 2023–24 it disappears entirely on EURUSD and GBPUSD.

## 5. Parameter sensitivity

- **ATR:** n = 7 < 14 < 28 in loss on every symbol at h = 1. The default ATR(14) is not the best ATR.
- **YZ:** n = 5 is best and n = 60 worst on every symbol. YZ(5) is roughly level with ATR(14) (better on 3 of 4, none significant). YZ's 20-day default is the problem: **range-based estimators with long windows react too slowly.**

## 6. Conclusions (and what they do not say)

1. **The pre-registered claim "YZ/HAR beats ATR" is REJECTED.** EQ-002 (YZ, n = 20) is **FAILED@G4**: it is significantly worse than ATR14 on 3 of 4 symbols. EQ-004 (HAR) **FAILED@G4 for the "beats ATR14" rule.**
2. **HAR is the best-measured forecaster** (lowest point QLIKE 4/4, best directional hit rate 4/4). It is not statistically separated from ATR(7). **ATR(7) is a cheap, nearly equivalent alternative.**
3. **Everything here is daily-horizon RV.** NEXA's stops live at intraday horizons, which this test did not measure. Before any stop-sizing claim, the follow-up is an intraday (hourly) HAR vs ATR test on fixed entries (`TOP10_CONSTRUCTS.md` #1). That follow-up needs a new ID (HYP-001c) and its own pre-registration.
4. **Not tested:** whether a better σ̂ changes trade outcomes. Lower QLIKE is a statement about forecast error, not about P_U, D or net R.
