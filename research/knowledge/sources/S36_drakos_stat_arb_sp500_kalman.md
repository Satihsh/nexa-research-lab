# S36: Stefanos Drakos, "Statistical Arbitrage in S&P500" (Journal of Mathematical Finance 6, 2016, 166–177)

**File:** `jmf_2016022913315540.pdf`. 12 pp. International Centre for Computational Engineering, Rhodes. doi:10.4236/jmf.2016.61016.

| Field | Value |
|---|---|
| **Source type** | Other academic institution. Peer-reviewed, open-access journal (SCIRP; low tier). |
| **Evidence status** | **Research finding: weak, with probable methodological errors** (see §3). The headline Kalman results are **not credible as stated**. No transaction costs. |
| **Processing** | All 12 pages read. **Rendered and checked visually:** pp. 3, 5 and 6 (eqs. 4–6, 14–22, the profit equations and the trading rules). Tables 1–8 were parsed from the text. Figures 2–5 (equity curves) were interpreted from their captions. |

## 1. Method (SOURCE)
**Selection (Engle–Granger, step 2)**
- In-sample year: regress log S^SPY_t = γ_i log S^i_t + ε for each S&P 100 stock, then ADF-test the residuals.
- Candidates that pass are combined: log S^SPY = γ Σ_i log S^i + ε (eq. 5) = γ log ∏S^i (eq. 6). This is ADF-tested again.

**Hedge ratio, three variants**
1. Constant γ.
2. Rolling OLS. The regression frequency was "raised by an optimization procedure" (on which data is not stated).
3. **Multivariate Kalman filter** with state y_t = [γ¹…γⁿ, μ]ᵀ as a random walk (eqs. 8–10).
   - Prediction: P̂_{t|t−1} = P̂_{t−1|t−1} + V_w.
   - Measurement: ẑ_t = x_t·ŷ_{t|t−1}, residual ε_t = log S^SPY_t − ẑ_t.
   - S_t = x P xᵀ + V_e; gain K_t = P xᵀ/S_t.
   - Update: ŷ_{t|t} = ŷ_{t|t−1} + K_t ε_t, P_{t|t} = P_{t|t−1} − K S Kᵀ (eqs. 12–19, V).
   - V_w and V_e are "discussed in [11, 12]". The values used are not given.

**Trading rule (eq. 22, V)**
- z_t = (ε_t − E[ε])/σ(ε) over a look-back.
- Open long if z < z_low; short if z > z_high; exit on z crossing the exit levels.
- **The threshold values and the look-back length are not reported.**

**Profit (eqs. 20–21, V):** ε_{t+h} − ε_t = log(S^SPY_{t+h}/S^SPY_t) − log(∏(S^i_{t+h})^{γ_{t+h}} / ∏(S^i_t)^{γ_t}).

**Results (Tables 4–8):** five overlapping windows, each trained on one year and traded to 30/12/2015.

| Trading period | Kalman annual return | Kalman Sharpe | Kalman MDD | Rolling OLS | Constant γ | S&P 500 |
|---|---|---|---|---|---|---|
| 2007–15 | 19.3 % | 3.30 | 12.6 % | 2.5 %, Sharpe 0.89 | 1.3 %, 0.48 | 4.3 %, 0.30 |
| 2008–15 | 13.3 % | 1.14 | 28.6 % | — | — | — |
| 2009–15 | 21.0 % | 3.04 | — | — | — | — |
| 2010–15 | 13.3 % | 2.31 | — | — | — | — |
| 2011–15 | 12.7 % | 2.64 | — | — | — | — |

- Betas ≈ 0.
- The selected stock sets change every year: dim(S) = 4, 12, 5, 8, 4.

## 2. Mathematics (verified)
- Log returns are additive: Σ log(1 + r) = log(P_n/P_0) ✓ (eqs. 1–2).
- The Kalman recursions are standard ✓ (eqs. 12–19).
- **Notation error (p. 6, V):** the paper writes log ∏ γ√S^i (a γ-th *root*). The regression γ log S = log S^γ implies a **power**, not a root (✗).

## 3. Critical assessment (INFERENCE)
1. **P&L accounting with time-varying hedge ratios.**
   - Eq. 21 books ε_{t+h} − ε_t computed with γ_{t+h} at exit and γ_t at entry.
   - A position opened at t holds the γ_t amounts. Its P&L is log(S^SPY_{t+h}/S^SPY_t) − Σγ_t^i log(S^i_{t+h}/S^i_t). Re-estimation changes in γ are *not* trading profit.
   - Using filter-updated γ_{t+h} lets each day's re-fit reduce |ε| toward zero, so mean reversion is manufactured. This probably explains why the Kalman "spread" earns 5–8× the rolling-OLS version. **Not a tradable result.**
2. **Multiple testing in selection.**
   - About 100 ADF tests are run at a conventional level, so about 5 false "cointegrated" stocks are expected by chance. The selected set sizes (4–12) and their year-to-year turnover are consistent with selection that is largely noise.
   - The author reads the changing sets as "non constant cointegration".
3. **Position specification is in log-price units** ("sell γΣlog(S_t^i)"). A sum of log prices is not a portfolio value, so the tradable weights are undefined.
4. **No transaction costs and no shorting/borrow** in daily rebalancing of up to 12 legs plus the index. Thresholds, look-back and V_w/V_e are undisclosed, and the "optimization procedure" for the rolling-OLS frequency is unspecified. There is high researcher freedom.
5. **Overlapping evaluation windows** all ending in 2015, so they are not five independent tests.
6. **Survivorship:** S&P 100 constituents taken from Wikipedia, presumably as of writing.
7. **Typos:** Table 2 "20010–2015"; Table 6's header period does not match its in-sample/OOS lines; the ticker "CAN".

## 4. Principles worth keeping
- **SOURCE:** a Kalman-filter dynamic hedge ratio is a standard adaptive cointegration tool (Elliott–van der Hoek–Malcolm 2005, Vidyamurthy 2004).
- **INFERENCE: two rules for any adaptive-hedge spread backtest.**
  1. P&L must use the hedge ratio fixed at entry.
  2. The z-score must be computed from causal statistics. The Kalman *prediction* residual (innovation) is causal; a smoothed residual would not be.
- **INFERENCE:** cointegration selected from many candidates must be validated out of sample with a multiple-testing-aware threshold. S14 Ch. 6 showed 5-day correlation clusters ≈ industries; S25 showed cointegration across venues is mechanical.

## 5. NEXA relevance
- **H-XAUXAG-COINT (existing backlog idea, S22/S25):**
  - Any XAU–XAG (or EUR/GBP-vs-USD) spread study must use entry-fixed hedge ratios, causal Kalman innovations and costs on both legs.
  - Report the cost curve.
  - Data: available (XAU and XAG bars, if the XAG symbol is in the tester).
- **Teaching case for the NEXA causality certifier:** "adaptive parameter re-estimation inside the P&L" is a look-ahead / accounting class of bug to add to the checklist (STATISTICAL_KNOWLEDGE_BASE L-traps).

**Cross-references:**
- S25 (OU / VAR, Johansen);
- S14 Ch. 6 (clustering stat-arb, no costs);
- S22 §3.8 (pairs) and §10 (Kalman mentioned as a trend filter);
- S12 (cost-free stat-arb artefacts);
- S16 (in-sample backtests).
