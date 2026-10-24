# S12: Lahanis, Liu & Zhou (NYU Stern, Glucksman Fellowship), "Online Quantitative Trading Strategies: An Empirical Performance Overview Through Backtesting"
**File:** `Glucksman_Lahanis.pdf`. 20 pp. Student research fellowship report (≈2025) with a faculty mentor. Code is on GitHub (nglahani).

| Field | Value |
|---|---|
| **Source type** | Other academic institution: a student research report (NYU Stern), not peer-reviewed. |
| **Evidence status** | Research finding, **weak**. The authors state frictionless backtests (no costs); the universe is NASDAQ-100, 1998–2010; hyperparameters are chosen by the best Sharpe. |
| **Processing** | All 20 pages read. Tables 2–6 and Appendix Exhibit A were parsed from the text. Figures 1–9 (wealth curves, architecture) are described in the text. |

## 1. Framework (SOURCE): Online Portfolio Selection (OPS), after the Li & Hoi (2013) survey
**Setup**
- Price relatives x_{t,i} = p_{t,i}/p_{t−1,i}.
- Portfolio b_t lies in the simplex Δ_N.
- Wealth S_n = Π_t (b_t · x_t).
- Exponential growth rate W_n = (1/n) log(S_n/S_0) (Kelly).
- Sharpe uses rf = 5 %.

**Benchmarks**
- **BAH:** b_t ∝ b_{t−1} ⊙ x_{t−1}.
- **Best Stock:** eq. 2, b_t = e_{argmax x_{t−1}}. **This is "yesterday's best", not hindsight**, which contradicts the text's "perfect hindsight" description. It explains Best Stock's −99.95 % drawdown.
- **CRP:** b_t = b. **BCRP:** b* = argmax_b Σ_t log(b · x_t) (eq. 4). Constant rebalancing gives "volatility pumping".

**Follow-the-Winner**
- Universal Portfolio (Cover): a wealth-weighted average of CRPs, Monte Carlo approximation (eq. 5).
- **Exponential Gradient:** b_{t+1,i} = b_{t,i} exp(η (x_{t,i}/(b_t·x_t) − 1)), normalised (eq. 6).
- FTL: b_t = argmax Σ_{τ<t} log(b · x_τ).
- **FTRL:** adds −(β/2)‖b‖² (eq. 8).
- Aggregation: exponential weights on base portfolios (eqs. 9–10).

**Follow-the-Loser (mean reversion)**
- **Anticor** (Borodin et al.): cross-correlation of log relatives over a window w; moves wealth from recent winners to losers.
- **PAMR:** ε-insensitive loss ℓ_ε(b; x) = max{0, b·x − ε}; minimal-change update (passive-aggressive).
- **CWMR:** b ~ N(μ, Σ), updated by minimising D_KL(N(μ, Σ) ‖ N(μ_t, Σ_t)) subject to a confidence constraint.
- **OLMAR:** forecast x̂_{t+1} = (1/w) Σ_{i=1}^{w} x_{t−i} (moving-average reversion).
- **RMR:** an L1-median (robust) forecast.

**Pattern matching (nonparametric, Györfi et al.)**
- Choose similar past windows by histogram, kernel, k-NN or correlation.
- Then optimise log-optimal, **semi-log-optimal** (f(z) = z − 0.5(z−1)², a quadratic approximation of log) or Markowitz b·μ − λ bᵀΣb.

**Meta-learning**
- **Aggregating Algorithm (Vovk):** w^(i)_t ∝ w^(i)_{t−1} exp(−η ℓ^(i)_t).
- Fast Universalization.
- Online Gradient / Newton updates (ONS: b_t = b_{t−1} − η A^{−1} ∇ℓ).
- FTLH (Hazan & Seshadhri).

## 2. Data, protocol and results (SOURCE)
**Data:** QuantQuote minute data, survivorship-bias-free. The experiments use the NASDAQ-100 from 1998–2010, and the results are on **daily** price relatives.

**Protocol**
- Grid search with selection by the best Sharpe (Table 2, Anticor: 8 configurations).
- Rolling walk-forward validation is described: up to 5 windows, the final 20 % of each window held out.

**Results (final wealth, Sharpe, MDD)**

| Strategy | Final wealth | Sharpe | MDD |
|---|---|---|---|
| **CWMR** | **1590×** | **1.75** | −51 % |
| PAMR | 788× | 1.63 | — |
| Anticor | 36.9× | 1.02 | — |
| Histogram pattern matching | ~600× | ~1.15 | ~−76 % |
| OGU / Fast-Universalization meta (CWMR + FTRL + PAMR) | 66–68× | ~1.26 | — |
| FTRL | 15.2× | 1.04 | — |
| CRP | 12.16× | 0.755 | — |
| BAH | 9.17× | 0.58 | −68 % |
| FTL | 8.4× | 0.53 | — |

**Self-declared limitations:** frictionless (no transaction costs or slippage); a limited market and period.

## 3. Critical assessment
**INFERENCE: the extreme mean-reversion wealth (CWMR 1590×) is a known OPS artefact.**
- Daily rebalancing exploits **negative first-order autocorrelation** in individual stock returns (bid-ask bounce, short-term reversal).
- With turnover near 100 % per day, even 10–20 bp costs erase it.
- The Li & Hoi survey itself cautions about transaction costs (that knowledge is external to this file; it is flagged here as inference).
- **The cost-free result is not evidence of a tradable edge.**

**Selection bias**
- Hyperparameters were chosen by the best Sharpe across grids.
- How the walk-forward feeds into the reported full-period tables is unclear. UNKNOWN whether the tables are out of sample.

**Survivorship:** the NASDAQ-100 constituents were "survivorship bias-free lists" (claimed). The 1998–2010 window includes the dot-com crash.

**Implementation anomalies**
- The "Best Stock" mislabel described above.
- EG and CRP have identical results (12.1584) to 4 decimals. This is suspicious: with η = 0.05 EG barely moves from uniform.

## 4. NEXA relevance
- **Mathematical toolkit:** log-optimal growth, CRP volatility pumping, exponential weighting of experts (Hedge / Aggregating Algorithm), and regret-minimisation ensembles.
  - **Hypothesis:** a regret-bounded ensemble across NEXA engines (if any engine ever shows edge) as a *meta-allocator*. It is low priority while no engine is positive.
- **Short-term reversal at the daily stock level** does not transfer to NEXA's single-instrument CFD trading (FX / XAU). OPS needs a cross-section.
- **A cost-free OPS result is a cautionary example**, parallel to S08 and S16.

**Cross-references:** S21 Thorp (Kelly / log-optimal), S14 Jin (portfolio statistics), S22 (151 Strategies: mean reversion and momentum in a cross-section), S20 (QuantConnect thesis), S02 (Sharpe as objective).
