# S26: Cartea, Cohen, Graumans, Labyad, Sánchez-Betancourt & van Veldhuijzen, "Statistical Predictions of Trading Strategies in Electronic Markets"
**File:** `ssrn-4442770.pdf`. 60 pp. Forthcoming in the *Journal of Financial Econometrics* (version 20 Sep 2024).
**Affiliations:** Alan Turing Institute, AFM (the Dutch regulator), OMI and the Mathematical Institute Oxford.

| Field | Value |
|---|---|
| **Source type** | Oxford / university research. Peer-reviewed (forthcoming JFEC). Regulator co-authors. |
| **Evidence status** | **Strongly supported finding.** Unique data with member and algorithm IDs; walk-forward out-of-sample over 12 weeks; four shares; robustness checks. |
| **Processing** | All 60 pages read. Main text pp. 1–37 read in full. Appendix pp. 42–60 read: feature formulae (B), per-share accuracy tables (C.1), feature-importance robustness (C.2) and clustering for the other shares (C.3). Figures are interpreted via captions; the cluster Sankey plots and stability lines are described in the text. |

## 1. Data (SOURCE)
**Coverage**
- Euronext Amsterdam, 11 Oct 2021 – 30 Jan 2022 (80 days, 16 weeks).
- Shares: ASML, ING, AHOLD, TOMTOM.
- Every message with nanosecond timestamps, plus member and algorithm IDs.
- ASML: 96 algorithms active in every week.

**Order and fill structure**
- **97 % of trades match two limit orders.** Liquidity is mostly taken with *limit* orders, 2/3 of them IoC.

## 2. Method
**Target per limit order:** (D_t, P_t, V_t).
- **Direction** D_t ∈ {−1, 1}.
- **Price bucket** relative to the best quote: 1 = "eager" (inside or through the spread); 2 = at the touch; 3 = deeper.
  - The distance used is P_t − S^b_t for buys and S^a_t − P_t for sells.
- **Volume decile bucket** of log(1 + V).

**53 features** (App. B formulas, at t−)
- LOB volumes at levels 0–5, 6–10 and 11–20: the algorithm's own versus others'.
- Imbalance I(V_b, V_a) = log(1 + V_b) − log(1 + V_a) (eq. 11), own and others', and its change.
- Best-quote log volumes; spread in bp.
- Returns R^δ_t = log(S̃_{t−}/S̃_{t−δ}) over 1, 5, 60 and 300 s.
- Realised volatility V^δ_t = √(Σ|Δ log S̃|²) over 1, 5, 15 and 60 min.
- Message counts over the last 1 s, 100 ms, 1 ms and 100 µs.
- Aggressive buy, sell and net counts over the last 1, 5, 60 and 360 s.
- Size of the last trade.
- Inventory and cash of the algorithm and of the member, transformed as sign(x)·log(1 + |x|).

**Dimension reduction:** PCA from 53 to 30 features (> 90 % of variance), fitted on weeks 1–4 only and then applied forward (no look-ahead).

**Models**
- Logistic regression: P(D = 1) = 1/(1 + exp(β₀ + β·x)).
- Multinomial logit for P and V (eqs. 5–7).
- Random-forest benchmark: 50 trees, depth 5.

**Validation:** rolling train on 4 weeks, deploy on the next week, 12 times. An expanding window gives the same results.

**Interpretation tools**
- Permutation feature importance (Breiman).
- Hierarchical agglomerative clustering of the direction coefficients: cosine affinity, complete linkage, k = 3.

## 3. Results (SOURCE)
**ASML out-of-sample accuracy (order-weighted)**

| Target | Accuracy |
|---|---|
| Direction | **70 %** |
| Price bucket | 85 % (88 % conditional on direction) |
| Volume | 62 % |

- Gain over the "most frequent bucket" baseline: +18 pts (direction), +4 (price), +3 (volume).
- **Random forest** adds only about +5 pts on direction. Logit is preferred for interpretability and privacy.

**Other shares:** direction 67–69 %, gain 15–18 pts. TOMTOM (illiquid) is weakest on volume (52 %).

**Blind to member and algorithm ID:** direction accuracy falls to **54 %** (only 4 pts above a coin flip), price to 53 % and volume to 24 %.
- **"The added value of agent-labelled data… one order of magnitude higher" than going nonlinear.**

**Important features**
- **Direction:** the algorithm's own imbalance at levels 0–5, then own and member inventory, then best volumes.
- **Price:** spread, then inventory/cash, then message counts in the last 100 µs.
- **Volume:** inventory and cash.
- **Recent activity (µs–ms) matters more than older activity**, consistent with the AFM (2023) survey.

**Three behavioural clusters (ASML)**

| Cluster | Count | Liquidity-taking share of trades | Order/trade ratio | Median resting time | Behaviour |
|---|---|---|---|---|---|
| 1, directional | 54 algos | 51 % | 2.86 | 2.9 s | Trades with own inventory: position building |
| 2, opportunistic | 25 | **73 %** | — | — | Follows LOB imbalance, posts deep, no inventory reversion |
| 3, market makers | 17 | 26 % | 8.04 | **0.69 s** | Reverts inventory to zero; 81 % of eager orders improve the spread |

- **Only about 1/3 of registered Liquidity Providers behave as market makers.**
- **Stylised facts confirmed:**
  - wider spread ⇒ more liquidity provision inside the spread and less crossing;
  - higher recent quadratic variation ⇒ less aggressive (except the 60-minute horizon);
  - **large volume at the best ask ⇒ algorithms expect a down move.** They place buys deeper and are less aggressive on buys (P-x, LT-iv).
- **Cluster stability** is above random for ASML/ING but unstable for AHOLD/TOMTOM.

## 4. Principles and assessment
- **SOURCE:** order-book imbalance and own inventory drive algorithmic decisions; this is market microstructure. The prediction targets are *agent actions*, not prices.
- **INFERENCE: public-only features predict order direction barely above chance (54 %).** The predictability resides in *private* (identity / inventory) information.
  - For an outside trader with only public quotes, like NEXA, this is a strong caution against expecting LOB-derived *directional* edges.
- **Look-ahead:** the PCA was fitted on the first 4 weeks only; the walk-forward is explicit. Latency was not modelled (acknowledged).

## 5. NEXA relevance
- **Methodological template:** rolling train/deploy, permutation importance, baseline-relative accuracy, and a "blinded vs full information" ablation to quantify where the information lives.
  - **Hypothesis H-ABLATE:** for any NEXA engine, run the information ablation: does the edge survive using only features NEXA truly has (bid/ask quotes plus counts)?
- **"Large resting best-ask volume ⇒ expected down move"** is a LOB imbalance effect. **NOT TESTABLE** at Pepperstone: no depth volumes, BOOKDEPTH unverified.
- **Agent-based simulation** (the stated future use) is a possible route for realistic execution modelling. Out of scope for NEXA (no LOB data).

**Cross-references:** S06 (same AFM data, MM signalling), S10 (Sánchez-Betancourt DPhil: latency and execution), S24 (algorithmic market makers), S13 (microprice / imbalance), S23 (ML vs linear, walk-forward).
