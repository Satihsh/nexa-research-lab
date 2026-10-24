# S02: Lim, Zohren & Roberts, "Enhancing Time Series Momentum Strategies Using Deep Neural Networks"
**File:** `1904.04912v3.pdf`. arXiv:1904.04912v3 [stat.ML], 27 Sep 2020. 21 pp.
**Affiliation:** Dept. of Engineering Science and the Oxford-Man Institute, University of Oxford.

| Field | Value |
|---|---|
| **Source type** | Oxford / university research. arXiv preprint; a version later appeared in the J. Financial Data Science. The journal version is NOT in the file, so treat it as a preprint. |
| **Evidence status** | Research finding. Out-of-sample backtest on 88 futures, 1995–2015. No independent replication in the corpus. |
| **Processing** | Text pp. 1–21 read in full: body, references, Appendix A (dataset), B (hyperparameters), C (cross-validation tables, Exhibits 10–11).<br>Equation pages p. 4, 5, 12 inspected visually (the text extraction garbled the fractions).<br>Figure pages 11, 13 inspected. Pages 20–21 are per-asset box plots; captions read, no numbers extracted. |

## 1. Problem
Classical time-series momentum (TSMOM) needs two hand-specified parts:
1. a **trend estimator**;
2. a **position-sizing rule**.

DMNs learn both jointly with a neural network, trained directly on a **risk-adjusted objective** (the Sharpe ratio) rather than on prediction error.

## 2. Mathematics (as written; verified against the rendered pages)
**Eq. (1): TSMOM portfolio return (volatility scaling).**

r^TSMOM_{t,t+1} = (1/N_t) Σ_{i=1}^{N_t} X_t^(i) · (σ_tgt / σ_t^(i)) · r^(i)_{t,t+1}

| Symbol | Meaning |
|---|---|
| X_t^(i) ∈ [−1, 1] | Signal (position) |
| σ_tgt | 15 % annualised volatility target |
| σ_t^(i) | Ex-ante volatility: EWM standard deviation, 60-day span, on daily returns |
| N_t | Number of assets |

- **Intuition:** each asset contributes equal ex-ante risk. Volatility scaling is credited (via refs [7, 9]) as "critical" to TSMOM performance.
- **Assumption:** σ_t is a good forecast of next-day volatility (volatility clustering).
- **Failure modes:** sudden volatility jumps, where the ex-ante σ is too low and the position too large.

**Eqs. (2)–(3): Moskowitz–Ooi–Pedersen 2012 benchmark.**
- Y_t = r_{t−252, t} (the 12-month return).
- X_t = sgn(Y_t).

**Eqs. (4)–(8): Baz et al. 2015 volatility-normalised MACD.**
- q_t = MACD(i, t, S, L) / std(p_{t−63:t}) (price MACD divided by the 63-day price standard deviation).
- MACD = m(i, S) − m(i, L), where m is an EWMA with half-life HL = log 0.5 / log(1 − 1/S).
- Y_t = q_t / std(z_{t−252:t}). Rendered as "z", meaning the q series over the last year.
- Combined signal: Ỹ = Σ_{k=1}^{3} Y(S_k, L_k), with S ∈ {8, 16, 32} and L ∈ {24, 48, 96}.

**Eq. (7): non-monotone position response.**
- φ(y) = y·exp(−y²/4) / 0.89.
- The position grows until |y| = √2 ≈ 1.41, then decays to 0 for extreme moves (the "overbought/oversold" haircut).
- **Inference:** this embeds a mean-reversion-at-extremes prior into a trend signal.

**Eqs. (10)–(11): supervised losses.**
- MSE on volatility-normalised next returns, r/σ.
- Binary cross-entropy with label I(r/σ > 0).
- Positions: sgn(Y) (eq. 12) or sgn(Y − 0.5) (eq. 13).

**Eqs. (15)–(16): direct-output losses.**
- L_returns = −μ_R, where R(i, t) = X_t^(i) (σ_tgt/σ_t^(i)) r^(i)_{t,t+1}.
- L_sharpe = −μ_R·√252 / √( Σ_Ω R(i, t)²/M − μ_R² ).
  - This is the annualised Sharpe ratio computed over the whole minibatch Ω, pooled across assets and time.

**Architectures**
- Lasso (eqs. 17–18):
  - activation g = linear (regression), sigmoid (classification) or tanh (direct position);
  - L1 penalty α‖w‖₁;
  - τ = 5-day input window.
- MLP (19–20).
- WaveNet: dilated causal convolution with a gated activation ψ(u) = tanh(Wu) ⊙ σ(Vu) + Au + b (eq. 21). Weekly, monthly and quarterly stacks (eqs. 22–27).
- LSTM (28–33): standard gate equations.

**Eq. (34): turnover.** ζ_t = σ_tgt · | X_t/σ_t − X_{t−1}/σ_{t−1} |.

**Eq. (35): cost-adjusted training return (turnover regulariser).**
- r̃ = (σ_tgt/N) Σ ( X_t r/σ_t − c·| X_t/σ_t − X_{t−1}/σ_{t−1} | ).
- c = transaction cost.

## 3. Data and protocol (SOURCE FACT)
**Data**
- 88 ratio-adjusted continuous futures (Pinnacle CLC). Only contracts with <10 % missing data were kept, out of 98.
- 1990–2015, covering commodities, equities, fixed income and FX. **Gold (GC, ZG) is included** (App. A).
- Winsorised at 5 EWM standard deviations around the EWM mean, using a 252-day half-life.

**Features**
- Normalised returns over 1 day, 1 month, 3 months, 6 months and 1 year, each divided by σ·√horizon.
- The 3 MACD Y signals.

**Training**
- Expanding-window recalibration every 5 years, with the full hyperparameter search re-run each time.
- Out-of-sample period 1995–2015.
- Adam optimiser; 90/10 time split for validation; early stopping after 25 epochs without improvement; 50-iteration random search.
- Dropout is "key"; the LSTM is trained on 63-step trajectories.

## 4. Results (SOURCE FACT; no transaction costs unless stated)
**Raw signal (Exhibit 2)**

| Model | Sharpe | MDD |
|---|---|---|
| Sharpe-optimised LSTM | **2.804** | 0.021 |
| Long Only | 0.738 | — |
| Sgn(Returns) | 1.192 | — |
| MACD | 0.976 | — |
| Sharpe-optimised MLP | 1.383 | — |

The LSTM's volatility is only 0.016. Its Sharpe gain is mostly lower volatility, not higher return: E[R] is 0.045 vs 0.054 for Sgn (Exhibit 5c, p. 10).

**Rescaled to 15 % volatility (Exhibit 3):** LSTM Sharpe 2.907 and MDD 0.209, vs Sgn(Returns) 1.392.

**Binary classifiers:** accuracy ≈ 50 %, Sharpe ≈ 0.0–0.3. Accuracy is a poor proxy for P&L; a high hit rate does not imply profit (p. 2, p. 10).

**Cross-validation by 5-year block (Exhibit 10)**
- LSTM Sharpe 2.781 ± 2.081 (± 2 standard deviations) and MLP Sharpe 1.669 ± 2.332.
- **The block-to-block dispersion is very large.**

**Turnover and costs (Exhibits 6–8)**
- ML models trade about 10× more than Long Only.
- Profitability persists only up to about 4 bps for most ML models; the LSTM beats the benchmarks only up to 2–3 bps.
- At c = 10 bps:
  - LSTM Sharpe −5.313, MDD 1.000 (total loss).
  - With the turnover regulariser, the LSTM's Sharpe is 0.912 vs Sgn 0.861.

## 5. Principles and critical assessment
- **SOURCE FACT: volatility scaling + direct outputs + Sharpe loss** are the three ingredients the authors credit (p. 10).
- **INFERENCE: the Sharpe loss mostly learns de-risking.**
  - The LSTM's E[R] is similar to the benchmarks while its volatility is 3× lower.
  - It is effectively a dynamic volatility and exposure filter.
  - That is useful, but it is not a large "alpha" gain in return terms.
- **INFERENCE: cost fragility is severe.** Edge disappears at 2–4 bps per unit of turnover.
  - NEXA's XAUUSD all-in cost is about 3.5 % of R at an M15 ATR stop, far above a few bps of notional.
  - For intraday CFD trading the published edge is unlikely to transfer without turnover control.
- **Overfitting risks (INFERENCE):**
  - 50-iteration random search per 5-year block;
  - large ± ranges;
  - a single dataset (Pinnacle CLC) with no replication;
  - the selection of the best loss and architecture is post hoc across 16 combinations.
  - There is no deflated Sharpe or multiple-testing correction (UNKNOWN whether one was done; none is reported).
- **Look-ahead:** the vol-scaling uses ex-ante EWM σ and the walk-forward is explicit. Low risk as described. Winsorisation uses EWM statistics; the paper does not state explicitly whether these are causal (UNKNOWN).
- **Regime:** the test spans 1995–2015, a strong period for trend following. The authors flag non-stationarity as future work.
- **Information used:** daily OHLC-derived returns only. No volume, no order book.

## 6. NEXA relevance
- **Volatility-targeted sizing (eq. 1)** is a well-documented risk normaliser. It is consistent with NEXA's 1 %-risk / ATR-stop philosophy. It is relevant to any NEXA engine (HYPOTHESIS: it lowers drawdown more than it raises return).
- **The non-monotone φ(y) response** suggests trend strength should be capped or reversed at extremes. It is relevant to the 8E EMA/MACD "momentum" engine, which is binary in NEXA.
- **A turnover-cost regulariser** is applicable to any learned NEXA signal; costs must be inside the training objective.
- **Do NOT import the claimed Sharpe 2.8.** It is cost-free, on daily futures, and in a favourable trend regime.

**Cross-references:**
- S03 Zhang–Zohren–Roberts DRL: the same group, the same volatility scaling and the same futures universe.
- S13 Spears et al.: uncertainty-based sizing.
- S22 151 Trading Strategies: TSMOM definitions.
- S14 Jin: momentum and portfolio.
