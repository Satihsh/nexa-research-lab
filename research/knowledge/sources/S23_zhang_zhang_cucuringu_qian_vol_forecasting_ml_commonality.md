# S23: Chao Zhang, Yihuang Zhang, Mihai Cucuringu & Zhongmin Qian, "Volatility forecasting with machine learning and intraday commonality"
**File:** `ssrn-4022147.pdf`. 44 pp. SSRN 4022147, Oct 2022. Oxford Statistics, Mathematical Institute, Alan Turing Institute and Oxford Suzhou Centre. Published later in J. Financial Econometrics, which is not stated in the file.

| Field | Value |
|---|---|
| **Source type** | Oxford / university research |
| **Evidence status** | **Supported finding.** Rigorous out-of-sample design: rolling annual retraining, Diebold–Mariano tests, an unseen-stock test, and a realised-utility economic metric with costs. |
| **Processing** | All 44 pages read, including Appendices A–D. Rendered: pp. 17 (QLIKE / DM) and 19 (utility equations). Figures 1–12 are described in the text. |

## 1. Data and definitions (SOURCE)
**Data**
- LOBSTER Nasdaq ITCH, mid-prices, 1-minute log returns.
- Top-100 S&P 500 names, 2011-07 → 2021-06; 93 stocks retained.
- Overnight excluded. Winsorised at 0.5 / 99.5 %.

**Integrated variance:** IV_{i,t}(h) = ∫_{t−h}^{t} σ²_{i,s} ds.

**Log realised volatility:** RV^{(h)}_{i,t} = log Σ_{s=t−h+1}^{t} r²_{i,s}, at horizons h = 10, 30 and 65 minutes and 1 day.

**Commonality.** The adjusted R² of RV_i on the equal-weighted market RV_M = (1/N) Σ RV_i (eqs. 5–6).

| Horizon | Mean R² | Std dev |
|---|---|---|
| 10-min | 0.56 | 0.068 |
| 30-min | 0.73 | 0.048 |
| 65-min | 0.74 | 0.041 |
| 1-day | 0.36 | 0.198 |

- Commonality is **stable intraday, turbulent daily**.
- Intraday commonality **rises toward the close**, opposite to the diurnal volatility pattern.
- Diurnal volatility has a reverse-J shape: high at the open, lower at midday, and higher again at the close.

**Sentiment link (App. A)**
- logit(R²) is regressed on VIX, the Michigan consumer sentiment index (CSI) and economic policy uncertainty (EPU).
- Adjusted R² 48–56 %. VIX and CSI are significant at all horizons.

## 2. Models
**Time-series and linear models**
- **SARIMA:** φ(L)(1−L)^d RV = θ(L)ε, with an intraday seasonal period. ARIMA(1,1,1) for daily.
- **HAR (Corsi):** RV^d_{t+1} = α + β_d RV^d_t + β_w RV^w_t + β_m RV^m_t, with weekly = 5-day and monthly = 21-day averages. This captures long memory parsimoniously.
- **HAR-D (eq. 10):** adds the diurnal average D_{τ}, computed over the last 21 days for the same time bucket, and the lag-1 intraday RV. This is the log version of the Engle–Sokalska multiplicative daily × diurnal × stochastic decomposition.
- OLS and LASSO on lags.

**Nonlinear models**
- XGBoost: tree boosting F(u) = Σ f_l(u).
- MLP: 3 layers, ReLU, batch normalisation, 10-network ensemble.
- LSTM: 2 layers, 10-network ensemble.

**Training schemes**
- **Single:** per stock.
- **Universal:** pooled across stocks.
- **Augmented:** pooled, plus the market RV lags.

**Evaluation**
- **MSE.**
- **QLIKE** (verified p. 17), on log RV: QLIKE = mean[ exp(RV)/exp(R̂V) − (RV − R̂V) − 1 ]. Robust to noisy volatility proxies (Patton).
- **Diebold–Mariano test:** DM = d̄/σ̂_d̄ → N(0, 1), using the cross-sectionally averaged loss difference (Gu-Kelly-Xiu variant).
- **Realised utility** (Bollerslev et al. 2018, verified p. 19):
  - mean-variance investor; position x* = (SR/γ)/√E_t[exp(RV_{t+1})];
  - RU_t = (SR²/γ)·√(exp RV_{t+1})/√(E^θ exp RV_{t+1}) − (SR²/2γ)·exp RV_{t+1}/E^θ exp RV_{t+1};
  - a perfect model gives RU = SR²/2γ, with SR = 0.4 and γ = 2, i.e. 4 %;
  - RU-TC subtracts costs at the full median bid-ask spread (90-day).

**Protocol:** train on [2011-07, t−251], validate on the last year, test the next year, retrained annually. The test period is Jul-2015 → Jun-2021 (6 years).

## 3. Results (SOURCE)
**QLIKE, 10-min horizon (Table 3)**

| Model | QLIKE |
|---|---|
| SARIMA | 0.617 |
| HAR-D, Single | 0.484 |
| HAR-D, Augmented | 0.453 |
| OLS, Augmented | 0.430 |
| XGBoost, Universal | 0.417 |
| MLP, Augmented | 0.386 |
| **LSTM, Augmented** | **0.376** |

- **At 1-day, linear models ≈ NNs:** HAR-D Augmented 0.180 vs MLP 0.180. NNs lack data at the daily horizon.
- **Augmented (market RV) helps most models.** Universal pooling alone does not help linear models.
- **Unseen stocks (Table 4):** models trained on other stocks beat per-stock OLS, e.g. MLP 10-min QLIKE 0.328 vs 0.372. Evidence for a **universal volatility mechanism**.
- **Intraday2Daily (§7):** forecasting the daily RV from lagged *intraday* RVs beats lagged daily RVs.
  - OLS QLIKE 0.192 → 0.186 (Single); MLP 0.171.
  - **The last half-hour (15:30–16:00) RV has the largest coefficient** for the next day's volatility (Fig. 12).
- **SHAR (semivariances RV⁺/RV⁻) and HARQ** (realised quarticity RQ = (M/3)Σ r⁴ correcting measurement error) are also improved by intraday inputs.
- **Update frequency** (weekly / monthly / yearly) barely matters (App. D).
- **The economic gains are small but positive.** For example, RU at 1-day ranges 3.55–3.59 % against an ideal of 4 %.

## 4. Principles and assessment
**SOURCE / established:**
- volatility is **highly forecastable** (unlike returns);
- log RV with HAR-type long-memory structure is a strong baseline;
- QLIKE plus DM tests is the correct evaluation toolkit;
- the diurnal seasonality must be modelled.

**INFERENCE**
- The NN advantage is real but incremental, about 0.01–0.04 QLIKE intraday. **OLS with good features captures most of it.**
- **Universality across assets** supports pooling data across NEXA symbols for *volatility* models.
- **Limits:** US large-cap equities only; mid-prices from LOBSTER. FX/XAU are not tested here; their diurnal shape differs (London/NY sessions).

## 5. NEXA relevance (high)
- **Hypotheses (backlog)**
  - **H-VOL-1.** HAR-D / log-RV forecasts from M1 data predict next-hour / next-session XAU and FX realised volatility better than ATR14. Use QLIKE + DM, out of sample.
    - **Data:** NEXA has M1 OHLC, so RV from 1-minute close-to-close returns is computable. Pepperstone quotes only, but mid ≈ bid + spread/2 is fine.
  - **H-VOL-2.** Volatility-forecast-based stop and size scaling (cf. S02's 1/σ, S13's μ/σ²) reduces drawdown at the same return. Test within the 1 % cap.
  - **H-VOL-3.** The last-hour-of-session RV (e.g. NY 20:00–21:00 UTC for FX/XAU) carries extra information about the next day's volatility.
  - **H-VOL-4.** A cross-symbol (XAU / EUR / GBP / USDJPY) "market RV" factor improves single-symbol forecasts (commonality).
- **This is the corpus's most direct, rigorously validated, NEXA-applicable method** for the volatility (not direction) layer: VEI, squeeze and stop sizing.

**Cross-references:** S04 / S18 (rough volatility, long memory), S14 Jin (statistics in markets), S02 (volatility scaling), S09 / S19 (squeeze = volatility-state heuristic), S15 Boeker (FX scaling).
