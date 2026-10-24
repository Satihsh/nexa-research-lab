# S13: Spears, Zohren & Roberts, "Investment sizing with deep learning prediction uncertainties for high-frequency Eurodollar futures trading"
**File:** `Investment-sizing-with-deep-learning-prediction-uncertainties-for.pdf`. 15 pp. arXiv:2007.15982v1 [q-fin.ST], 31 Jul 2020. Oxford-Man Institute.

| Field | Value |
|---|---|
| **Source type** | Oxford / university research (arXiv preprint) |
| **Evidence status** | Research finding, **preliminary**. The authors themselves call it "a preliminary demonstration". One year of data (2018); out-of-sample test months 8–12 only. **Not profitable at the actual bid-ask spread** (the authors acknowledge this). |
| **Processing** | All 15 pages read. Appendix derivation (p. 13) and Figure 4 (p. 8) inspected visually. Fig. 2 (architecture), Fig. 3 (α-surface) and Figs 5–6 are described in the text and captions. |

## 1. Data (SOURCE)
- Thomson Reuters Level-1 LOB (best bid/ask and sizes, plus trades) for Eurodollar futures EDc1–EDc15, every US trading day of 2018.
- Analysis on EDc7–EDc15, the most active contracts: median 157k–318k quotes and ~2k trades per day (Table 1).
- Median daily bid-ask spread **0.5 bp**. Daily microprice high-low median 3–5.3 bp (Table 2).

**Microprice** (Gatheral & Oomen):

P_t = (askVol·bidPx + askPx·bidVol) / (askVol + bidVol)

The midprice tilted toward the side with less queue. It captures order-book **volume imbalance**.

**Event-time down-sampling:** record a new curve observation only when any contract's microprice moves ≥ M = 0.1 bp. This filters noise.

**Inputs and normalisation**
- Inputs: a window of 100 curve observations; the target is the next-event curve.
- Window normalisation uses only backward statistics. The authors state that no step introduces look-ahead bias.

## 2. Mathematics
**Model:** Y_t ~ MVN(μ(D_t), Σ(D_t)), with heteroskedastic, input-dependent mean and covariance ("aleatoric" uncertainty).

**Eq. (1), Gaussian negative log-likelihood with a Cholesky-parametrised precision**
- (Σ^A_t)^{−1} = L_t L_tᵀ.
- L = −2 Σ_i log l_t^{ii} + (Y_t − μ_t)ᵀ L_t L_tᵀ (Y_t − μ_t).
- The diagonal entries of L are exponentiated to guarantee positive definiteness.
- **Intuition:** the network learns both the forecast and its own confidence, without covariance labels.

**Epistemic uncertainty via MC dropout** (Gal & Ghahramani). With N = 30 stochastic forward passes:
- μ̂ = (1/N) Σ μ̂_n;
- Σ̂^A = (1/N) Σ Σ̂^A_n;
- Σ̂^E = N/(N−1) · [ (1/N) Σ μ̂_n μ̂_nᵀ − μ̂ μ̂ᵀ ];
- total Σ̂ = Σ̂^A + Σ̂^E.

**Sizing rule (Appendix A.1, verified visually):**
- Maximise S = Σ α_j μ_j / √(Σ α_j² σ_j²) over N independent normal opportunities, each traded equally often.
- Setting dS/dα_i = 0 gives α_i* = μ_i / σ_i², up to a common positive scale, since S is scale-invariant.
- The second derivative < 0, so this is a maximum.
- **INFERENCE:** this is the mean-variance / Kelly-like rule. Size ∝ expected return ÷ variance, *not* ÷ standard deviation.
- Contrast with S02 / S03 volatility scaling (size ∝ 1/σ with sign-only signals). μ/σ² additionally scales by conviction μ and penalises variance quadratically.
- **Assumptions:**
  - uncorrelated, normal opportunities;
  - additive returns;
  - μ, σ taken as *true* parameters (plug-in).
- **Failure modes (SOURCE):** epistemic-only σ → 0 produced "unreasonably large α". The authors did not report that variant.

**Baseline:** Bayesian multivariate OLS with an inverse-Wishart prior on Σ and a matrix-normal prior on β. The posterior predictive is a multivariate Student-t (App. A.3).

## 3. Results (SOURCE)
**Model fit.** CNN-LSTM-Inception has about half the validation NLL of the MLP. Its MSE is better in 3 of 5 months (p ≤ 1e-4); on average MSE is only **2.5 % lower**.

**Cumulative 5-month out-of-sample Sharpe, before costs** (Table 3)

| Model | Base | Al+Ep | Gain |
|---|---|---|---|
| Diagonal MLP | 1.40 | 1.44 | — |
| CNN-LSTM, full Σ | 1.26 | 1.41 | — |
| Range over models | — | — | **+2.9 % to +12.7 %** vs Base; ≥ +11.3 % vs realised-volatility sizing |

**The Bayesian-OLS Base achieves 1.39**, comparable to the deep models. Adding uncertainty sizing to OLS *lowers* it to 1.10 (Fig. 6).

**Costs (Fig. 4, visual)**
- The cost unit is 0.005 bp per unit volume.
- All strategies' Sharpe falls below zero by **12 units = 0.06 bp**, far below the 0.5 bp spread.
- The authors: "may not necessarily be traded outright as a stand alone strategy". Its utility may come inside market-making or execution.

**Horizon decay (App. A.3):** prediction skill falls with horizon. By t+100 events, all models are equally poor; the inflection is around t+10.

**Dropout robustness:** uncertainty-sized strategies vary < 1.8 % across dropout rates; Base is sensitive.

## 4. Principles and critical assessment
- **SOURCE + INFERENCE:** sizing by μ/σ² is principled. The *relative* improvement is robust in sign but small, and it holds before costs.
- **The deep-model forecasting gain is marginal** (2.5 % MSE). The simple Bayesian OLS is a strong baseline. This is a recurring corpus theme; see S23 (NN vs HAR) and S12.
- **Horizon:** microstructure predictability decays within roughly 10 events. **Not transferable** to NEXA's M15/H1 bars.
- **Data NEXA lacks:** L1 sizes (bid/ask volume) for the microprice. Pepperstone gives prices only, with no sizes (NEXA tick audit).
- **Selection:** a single year; hyperparameters were tuned on validation months adjacent to the tests. Small test sample (5 months).

## 5. NEXA relevance
- **α ∝ μ/σ²** is a sizing *hypothesis* for NEXA *within* the hard cap of ≤ 1 % risk. It can only scale *down* from 1 %, never up.
  - It requires a calibrated μ (expected R) and σ per signal; NEXA does not currently have such estimates.
  - Plug-in error amplifies μ/σ² sizing (INFERENCE). The fractional-Kelly caution is from S21 Thorp.
- **The microprice needs queue sizes.** **NOT computable** from Pepperstone quote-only data. **DATA-LIMITED.**
- **Evidence that tiny cost multiples kill high-frequency edges.** This reinforces the NEXA cost findings: in the 8E audit, XAU all-in cost was 18.8 % of R at micro-stops.

**Cross-references:** S02 / S03 (volatility scaling, Sharpe objective); S21 Thorp (Kelly); S10 / S26 Sánchez-Betancourt (LOB execution); S23 (ML vs simple models); S14 Jin.
