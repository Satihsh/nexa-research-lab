# S39: Romain Lafarguette & Romain Veyrune, "Foreign Exchange Intervention Rule for Central Banks: A Risk-Based Framework" (IMF Working Paper WP/21/32, Feb 2021)

**File:** `wpiea2021032-print-pdf.pdf`. 33 pp. IMF Monetary and Capital Markets Department. Replication code is on the authors' site (Python, using K. Sheppard's `arch` package).

| Field | Value |
|---|---|
| **Source type** | External research. IMF working paper: an international institution, not peer-reviewed. |
| **Evidence status** | **Research finding (proof of concept).** Daily MXN/USD data since 2001; out-of-sample density checks over a short window (4–10 months of 2020); counterfactual back-test. **Not a trading result.** |
| **Processing** | All 33 pp. read, including Appendix I (financial comparison) and Appendix II (out-of-sample benchmarking). Table 1 (EGARCH-X estimates) was parsed from a garbled extraction; the column assignment was reconstructed from the column headers. Figures 1–13 (density, fan chart, PIT, CDF triggers, Mexico interventions) were interpreted from captions and text. p. 33 holds figure-only tail pages. |

## 1. Framework (SOURCE)
**Exchange-rate-at-risk (ERaR):** the θ-quantile of the conditional density f(r_{t+1} | X_t) of daily log returns r_t = log(e_t/e_{t−1}).

**Intervention region:** R_t = {r < Q(r_t | X_{t−1}, θ)} ∪ {r > Q(r_t | X_{t−1}, 1 − θ)}. Symmetric, e.g. 2.5 % each side.
- The central bank (CB) buys or sells FX when the cumulative intraday move enters the region (at most once a day).
- **Fixed intervention frequency** = θ on average, which bounds the intervention budget.
- **Claimed advantages:**
  - triggers adapt to volatility regimes and trends, unlike fixed-volatility triggers (e.g. a 2 % daily move);
  - harder to front-run or speculate against;
  - "budget neutral" over the medium term;
  - the CB buys cheap and sells dear.

**Model: EGARCH(1,1)-X with skewed-t (Hansen) innovations, estimated by MLE**
- Mean: AR-X, r_t = c + ρ r_{t−1} + βX_t + ε_t.
- Volatility: log σ²_t = ω + β log σ²_{t−1} + α z_{t−1} + γ(|z_{t−1}| − E|z|), an asymmetric response.
- Innovations: ε = σ ε̃, ε̃ ~ skew-t(ν, λ).
- **Regressors:**
  - average daily bid–ask spread;
  - intraday range (max − min);
  - interbank rate − LIBOR;
  - Δ one-month forward points;
  - ΔVIX;
  - EUR/USD log return;
  - oil log return;
  - lagged intervention dummy.
- **Estimates (Table 1, baseline):**
  - ρ ≈ −0.08***; forward points +19***; rate differential +34*** (as printed; sign conventions per the authors);
  - EUR/USD −0.16***; VIX +15***; oil −0.02***;
  - GARCH: ω 0.12, α 0.15, γ 0.05, **β 0.99** (high persistence), **ν ≈ 8.5** (fat tails), λ ≈ 0.08 (right skew = depreciation);
  - **R² 0.058 (micro) → 0.276 (baseline).**
- **Model selection** by AIC/BIC lags. Year dummies were insignificant.

## 2. Validation (SOURCE)
- **Out-of-sample density** with an expanding window, Jan–Oct 2020. The COVID-19 period shows wider and more skewed densities.
- **PIT test** (Diebold–Gunther–Tay; Rossi–Sekhposyan bands) over 4 months: the empirical CDF of PITs stays within the bands.
- **Appendix II, against the baseline** (uncensored log score, Diks et al. 2011):

  | Model | PIT | Log-score difference vs baseline |
  |---|---|---|
  | Unconditional KDE | Fail | −6.36 (p ≈ 0) |
  | Quantile regression | Pass | −2.09 (p = 0.02) |
  | Gaussian EGARCH | Fail ("by a few percentiles") | +1.2 to +1.9 (p 0.89–0.97) |
  | Skew-t GARCH | Fail | (within the range above) |
  | Gaussian GARCH | Fail | (within the range above) |

  - The GARCH variants are statistically equivalent; GARCH beats unconditional and quantile-regression densities.
  - Cites Hansen–Lunde (2005): nothing beats GARCH(1,1) for daily FX.
- **Counterfactual:** the VaR rule would have intervened on about 15 days over Jan–Oct 2020, i.e. 7.5 % of days at a nominal 5 % region (the crisis period).
- **Banco de México history:**
  - 62 minimum-rate auctions (2008–2016, triggered at the previous close × 1.02 / 1.015 / 1.01) occurred mostly above the 95th conditional percentile;
  - 322 auctions without a minimum rate were spread across the whole conditional distribution, implying other motives (e.g. reserve management).
- **Appendix I (Oct 2015 – Oct 2016, 18 interventions each):**
  - average day move at intervention: −6.1 bp (no-min), 108.8 bp (min-rate), 164.8 bp (VaR);
  - "FX performance" vs no-min: +6.9 % and +8.3 %.
  - The authors caveat selection effects.

## 3. Critical assessment (INFERENCE)
1. **Timing of the regressors.**
   - Several X variables are same-day aggregates: the day's average spread, the day's high−low range, ΔVIX, the EUR/USD return, the oil return.
   - If they enter contemporaneously, R² ≈ 0.28 is an *explanatory* fit. An ex-ante trigger Q(r_t | X_{t−1}) could not use them.
   - The paper's notation says X_{t−1}, but the variable descriptions are "over the day". **UNKNOWN which applies.** A potential look-ahead in any trading use.
2. **VaR backtest is thin.** 15 exceedance days at a nominal 5 % (expected about 10). No Kupiec / Christoffersen coverage tests, and only a 4-month PIT window.
3. **"Budget neutral"** follows from equal *frequency* on both sides, not equal value or P&L. In a trending currency (MXN roughly 10 → 20 per USD over the sample) the two sides are not symmetric in value.
4. **Appendix I is a small-sample (n = 18), in-sample comparison.** The text says rule-based strategies "outperform the minimum rate strategy"; it means the no-minimum-rate strategy (a typo).
5. **Strengths:**
   - proper density-forecast evaluation (PIT and log scores);
   - a sensible preference for conditional, regime-adaptive thresholds over fixed ones;
   - candid about scope.

## 4. Principles
- **SOURCE / established:** daily FX returns have strong volatility clustering (β ≈ 0.99), fat tails (ν ≈ 8–9) and skew. A GARCH(1,1) family model is a hard-to-beat daily density baseline (Hansen–Lunde).
- **SOURCE:** fixed-size triggers (e.g. "a 2 % move") imply a regime-dependent frequency and risk transfer. Quantile-of-conditional-density triggers keep the frequency fixed and adapt to volatility.
- **SOURCE:** density forecasts should be judged by calibration (PIT) and sharpness / log score, not by point accuracy.
- **INFERENCE: CB intervention is a real FX market mechanism.** Interventions cluster at conditional tails, which may create mean reversion after extreme moves in intervened currencies. Not tested here; relevant only to EM pairs.

## 5. NEXA relevance
- **H-VAR-TRIGGER** (risk layer, not entry):
  - Replace fixed thresholds in NEXA risk gates (e.g. "skip if the bar range > k × ATR" or news/volatility filters) with conditional-quantile thresholds from an EGARCH/GARCH-t on closed bars, so that gate *frequency* is stable across regimes.
  - Evaluate with PIT and coverage tests (Kupiec / Christoffersen).
  - Data: available (XAU/FX D1–H1).
  - **Look-ahead risk:** use only lagged regressors.
  - Evidence: hypothesis.
- **Volatility-forecast evaluation toolkit:** PIT, log score and the Diks et al. test complement S23's QLIKE / Diebold–Mariano for H-VOL-1..4.
- **XAU note:** gold is not a CB-intervened price, but USD-leg interventions (JPY, CHF historically) can create gaps and violent intraday moves. NEXA's FX symbols inherit this event risk. Treat it as a regime / news-filter consideration (S10, S01).

**Cross-references:**
- S23 (volatility forecasting evaluation);
- S04 / S18 (volatility persistence);
- S15 (FX scaling, fat tails);
- S35 (VG heavy tails);
- S22 §8 (carry, UIRP / CIRP; the IMF IPF uses UIP deviations);
- S01 Ch. 4 (central-bank management of the JPY; pegs);
- S31 FX algo handbook (FX market structure).
