# S03: Zhang, Zohren & Roberts, "Deep Reinforcement Learning for Trading"
**File:** `1911.10107v1.pdf`. arXiv:1911.10107v1 [q-fin.CP], 22 Nov 2019. 16 pp.
**Affiliation:** Oxford-Man Institute.

| Field | Value |
|---|---|
| **Source type** | Oxford / university research (arXiv preprint) |
| **Evidence status** | Research finding. One backtest; 2011–2019 out of sample; 50 futures. |
| **Processing** | Text pp. 1–16 read in full, including Appendices A–B.<br>Reward equation (p. 4) and Figure 2 (p. 9) inspected visually.<br>Note: the `file` utility reported "2 pages"; PDFKit found 16. |

## 1. Problem
Learn trade **positions** directly with RL, instead of forecasting and then hand-mapping forecasts to positions.

The link between portfolio theory and RL:
- **Eq. (1):** the agent maximises E[U(W_T)] = E[U(W_0 + Σ_t δW_t)].
- With **linear (risk-neutral) utility**, this equals maximising the expected cumulative reward.
- RL return: G_t = Σ_{k=t+1}^{T} γ^{k−t−1} R_k (eq. 2).

## 2. Mathematics
**MDP**
- State S_t: the last 60 observations of each feature.
- Action A_t:
  - discrete {−1, 0, 1} (DQN, PG);
  - continuous [−1, 1] (A2C).
- These are "target orders": the output is the position, not the trade.

**Features**
- Normalised close prices.
- Volatility-normalised returns over 1, 2 and 3 months and 1 year: r_{t−h,t} / (σ_t √h), with σ an EWM standard deviation of 60-day span.
- Baz MACD:
  - MACD_t = q_t / std(q_{t−252:t});
  - q_t = (m(S) − m(L)) / std(p_{t−63:t}).
- RSI(30), with the usual 20/80 thresholds.

**Reward, eq. (4)** (verified visually):

R_t = μ [ A_{t−1} (σ_tgt/σ_{t−1}) r_t − bp · p_{t−1} · | (σ_tgt/σ_{t−1}) A_{t−1} − (σ_tgt/σ_{t−2}) A_{t−2} | ]

| Symbol | Meaning |
|---|---|
| r_t = p_t − p_{t−1} | **Additive** P&L, for a fixed contract count |
| μ | 1 |
| bp | Cost rate (1 bp = 1e-4 of traded value) |
| Turnover term | The change in the volatility-scaled position |

- **Intuition:** volatility-scaled P&L minus proportional cost on the change in the scaled position.
- **Assumption:** risk-neutral (linear) utility.
- **Stated limitation:** multiplicative wealth needs a log reward, which "penalises large wealth growths". This is why additive P&L was chosen.

**Algorithms**
- **DQN loss:** L(θ) = E[(Q_θ(S, A) − Q′(S, A))²], with target r + γ max_{A′} Q(S′, A′).
  - Stabilised with fixed Q-targets, Double DQN and Dueling DQN.
- **Policy Gradient (REINFORCE):** ∇J = Σ_t ∇_θ log π_θ(A_t | S_t) G_t (eq. 6). Monte Carlo, updated at episode end.
- **A2C:** maximise E[log π(A|S, θ) · A^adv(S, A)].
  - A^adv = R_t + γV(S_{t+1}) − V(S_t) (eq. 8).
  - The critic minimises the squared TD error (eq. 9).

**Training setup**
- Networks: 2-layer LSTMs with 64 and 32 units, Leaky-ReLU, one model per asset class.
- **γ = 0.3** (short-horizon credit assignment).
- **bp = 0.0020 (20 bp) in training**, which acts as a turnover regulariser.
- Adam optimiser; replay memory 5000; target-network update every 1000 steps.

**Baselines**
- Long only.
- Sign(R) on 252-day returns.
- MACD via φ(MACD) = MACD·exp(−MACD²/4) / 0.89, summed over (S_k, L_k).

## 3. Data and results (SOURCE FACT)
**Data and protocol**
- 50 Pinnacle CLC ratio-adjusted futures: 25 commodity, 11 equity, 5 rates, 9 FX. Gold (ZG) is included.
- 2005–2019, retrained every 5 years. Out of sample 2011–2019.
- Equal-weight portfolio (eq. 13), with portfolio-level volatility scaling (Table 2).

**Table 2, all contracts (Sharpe)**

| Model | Long | Sign(R) | MACD | **DQN** | PG | A2C |
|---|---|---|---|---|---|---|
| Sharpe | 0.058 | 0.441 | 0.091 | **1.288** | 0.754 | 1.050 |

**Per asset class**
- FX:
  - Long −0.353, Sign(R) −0.306, MACD 0.007;
  - DQN 0.546, A2C 0.328.
- **Equity indices: Long-only (0.688) beats or ties the RL agents.**

**Cost tolerance**
- DQN and A2C remain positive at **25 bp**, about $3.5 per contract (Fig. 2).
- The classical benchmarks become negative at a few bp (Fig. 2, read visually).

**Hit rates** are about 50–54 % throughout. The edge comes from the profit/loss ratio (Ave P / Ave L ≈ 1.02–1.14).

**Anomaly (UNKNOWN cause):** the reported MDD values are implausibly small, e.g. 0.002 for DQN with an annualised standard deviation of 0.976. The units or definition probably differ (additive P&L). **Treat MDD figures as unreliable.**

## 4. Principles and critical assessment
- **SOURCE FACT: classical TSMOM loses in FX over 2011–2019** (both Long and Sign(R) are negative). This matches the regime-dependence of trend following.
- **INFERENCE: a single run per algorithm.**
  - There are no confidence intervals and no seeds reported.
  - With γ = 0.3 and 20 bp training cost, hyperparameters are fixed; their tuning process is not described (UNKNOWN).
  - Selection risk: DQN is "best" among 3 RL methods × 4 classes.
- **CONTRADICTION with S02** (same lab): S02's ML models lose their edge at 2–4 bps, while S03's DQN survives 25 bp. The cost bases differ:
  - S02 charges c on the change in volatility-scaled position;
  - S03 charges bp × price × change in scaled position, with additive P&L.
  - **The numbers are not comparable as "bp".**
- **Look-ahead:** walk-forward with 5-year blocks. Low risk as described.
- **Information used:** daily prices and technical indicators only.

## 5. NEXA relevance
- **The volatility-scaled reward with a turnover penalty (eq. 4)** is a template for any NEXA learning objective.
- **Long-only beats active models in a trending equity regime.** This is a benchmark lesson: always compare against the drift / buy-and-hold null. NEXA learned the same on XAU: gold trend = drift.
- **FX TSMOM was negative in 2011–2019 (SOURCE).** This supports the HYPOTHESIS that slow FX trend signals are weak in the post-2011 regime. It is consistent with NEXA's DEV finding that Donchian is negative on EUR/GBP.
- **NOT usable directly:**
  - daily futures with retail-level per-contract cost;
  - NEXA's intraday CFD cost structure differs;
  - the RL requires a simulator, and the authors acknowledge its difficulty (S02 p. 3).

**Cross-references:** S02 (same features, volatility scaling), S13, S22 (TSMOM), S14.
