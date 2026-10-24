# PRE-REGISTRATION T2: volatility forecasts (HYP-001b / H-VOL-1)

**Written before any T2 outcome is computed.** The SHA-256 is in `PREREG_HASHES.txt`.

## 1. Data
- **Pepperstone M1 canonical** (bid OHLC) for EURUSD, GBPUSD, USDJPY and XAUUSD.
- **Coverage:** 2017-07 (XAU 2018-01) → 2026-09-25.
- **Day = server day (A0).** Weekdays only.
- **Thin days** (< 80 % of the median bar count) are excluded **as targets** but kept as inputs.

## 2. Target
- **RV_{d}** = Σ (5-minute log-return)² within server day d.
- The first return of the day is the open versus the prior day's last close, so RV covers the full 24 hours.
- **Primary horizon:** h = 1 (forecast RV_{d+1} with information through day d).
- **Secondary horizon:** h = 5 (the mean of RV_{d+1..d+5}).

## 3. Forecasts (variance proxies), information through day d

| ID | Forecast |
|---|---|
| F1 | ATR(14), Wilder, daily bars: ATR² |
| F2 | ATR(7) |
| F3 | ATR(28) |
| F4 | Close-to-close variance, n = 20, zero mean |
| F5 | Parkinson, n = 20 |
| F6 | Garman–Klass, n = 20 |
| F7 | Rogers–Satchell, n = 20 |
| F8 | **Yang–Zhang**, n = 20 (sensitivity: n = 5, 10, 60) |
| F9 | Mean RV over the last 20 days |
| F10 | RV_d (random walk) |
| F11 | EWMA of RV, λ = 0.94 |
| F12 | **HAR-RV** (log): ln RV_{d+1} = β₀ + β_d ln RV_d + β_w ln RV^{(5)} + β_m ln RV^{(22)} |

**Calibration and refitting**
- **Mapping to the target scale:** every F1–F11 is mapped by a log-linear calibration ln RV_{d+h} ≈ a + b·ln F_d.
- **Fitting:** a, b (and the HAR β) are fit **walk-forward**: an expanding window starting with ≥ 250 days, refit at each month start, applied to the following month. This puts ATR (a range in price units) and every other forecast on equal footing.
- **Log-bias correction:** the forecast in variance units is exp(fitted + ½·s²), where s² is the in-sample residual variance.

## 4. Evaluation

**Loss functions**
- **Primary:** QLIKE, L = RV/F − ln(RV/F) − 1.
- **Secondary:** MSE of ln RV.

**Statistical comparison**
- **Diebold–Mariano test:** each forecast vs F1 (ATR(14)) and vs F12 (HAR), using Newey–West HAC with 5 lags.
- **Multiple testing:** Benjamini–Hochberg q = 0.10 across 4 symbols × comparisons.

**Directional usefulness**
- **(a)** Hit rate for "RV_{d+1} above vs below the trailing 60-day median of RV" from the forecast, vs 50 %. Binomial test with block bootstrap.
- **(b)** Spearman(forecast_d, next-day high−low range).

**Robustness and parameter sensitivity**
- **Regime stability:** QLIKE by calendar year and by RV tercile (cut-points from discovery).
- **Parameter sensitivity:** YZ n ∈ {5, 10, 20, 60}; ATR n ∈ {7, 14, 28}.

**Data splits (from 15 §3)**
- **Discovery:** 2017-07 → 2022-12.
- **Validation:** 2023-01 → 2024-12.
- **Holdout:** 2025-01 → 2026-09-25.
- All forecasts are walk-forward. Results are reported per split. **The verdict uses the holdout.**

## 5. Decision rule (holdout)

- **HYP-001b SUPPORTED** if F8 (YZ) **or** F12 (HAR) has lower QLIKE than F1 (ATR(14)) with BH-adjusted DM p < 0.10 for ≥ 3 of 4 symbols.
- **REJECTED** if ATR is not beaten on ≥ 3 symbols.
- **INCONCLUSIVE** otherwise.
- **Ranking:** the forecast with the lowest holdout QLIKE is reported per symbol, but **no single "best" model is declared** unless the DM test separates it from the runner-up.
