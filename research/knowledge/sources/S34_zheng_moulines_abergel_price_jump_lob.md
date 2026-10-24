# S34: Ban Zheng, Eric Moulines, Frédéric Abergel, "Price Jump Prediction in a Limit Order Book" (Journal of Mathematical Finance 3, 2013, 242–255)

**File:** `jmf_2013052414582995.pdf`. 14 pp.
**Affiliations:** Natixis (Equity Markets), Télécom ParisTech, and the École Centrale Paris BNP Paribas Chair of Quantitative Finance. doi:10.4236/jmf.2013.32024.

| Field | Value |
|---|---|
| **Source type** | Other academic institution, with an industry co-author (Natixis). Peer-reviewed, open-access journal (SCIRP). |
| **Evidence status** | **Research finding** for predictability: AUC ≈ 0.72 out of sample, consistent across all 40 CAC40 stocks. It rests on **one month** of data, and the train/test split is not described as chronological (UNKNOWN). **No trading or cost test.** |
| **Processing** | All 14 pages read. **Rendered:** p. 4 (Fig 2 LOB dynamics; W(i) definition) and p. 8 (Fig 5 conditional probabilities). Table 2 (event counts per stock) and Table 3 (AUC) were parsed from the text. Figs 6–8 (AUC by stock; LASSO selection frequencies) were interpreted from captions and text. |

## 1. Data and definitions (SOURCE)
- **Data:**
  - Euronext NSC; the 40 CAC40 stocks; 1–30 April 2011.
  - Natixis via Reuters Tick Capture, millisecond timestamps, L = 5 visible levels.
  - Window 09:05–17:25, split into morning (09:05–13:15) and afternoon (13:15–17:25) to handle intraday seasonality.
  - Iceberg and stop orders are ignored as rare.
- **Inter-trade price jump:** a market order executed at a price worse than the best bid (ask) prevailing just after the *previous* market order. This is post-trade impact.
  - It means a limit order placed at the best quote right after a market order is surely filled by the next one.
- **Trade-through:** a market order larger than the best-level quantity, which instantly moves the price.
- **Variables (all log):**
  - prices P^{b,i}, P^{a,i}; spread S; price gaps G^{b,i} = P^{b,i} − P^{b,i+1};
  - log volumes V^{b,i}, V^{a,i}; market-order size V^mo;
  - event dummies BLO, ALO, BMO, AMO, BTT, ATT.
- **Event counts (Table 2):** for example BNPP.PA had 432k/236k limit-order events (AM/PM), 3,164/3,160 market orders, and 377/368 bid jumps.
  - So jumps are about 10–15 % of market-order events.
  - Trade-throughs are more frequent in the morning; market orders and jumps more frequent in the afternoon.

## 2. Mathematics (SOURCE, V)
- **Depth-i bid–ask volume ratio (p. 4, V):**
  - W(i) = log Σ_{j≤i} exp(V^{b,j}) − log Σ_{j≤i} exp(V^{a,j}) = log(cumulative bid volume / cumulative ask volume to depth i).
  - At depth 1: W(1) = V^{b,1} − V^{a,1}.
- **Conditional trade sign:** P(I^ts = +1 | W(i) ≥ x) and P(I^ts = −1 | W(i) ≤ x).
- **Logistic model:** log[P(Y = 1|X)/(1 − P)] = βᵀX, with X stacking m = 5 lags of book-shape variables and n = 5 lags of event dummies (p = 76 features).
- **LASSO logit:** β̂ = argmin Σ[log(1 + e^{βᵀX_i}) − Y_iβᵀX_i] + λ‖β‖₁. λ is chosen by cross-validation (glmnet coordinate descent).
- **Metric:** AUC = P(score of a random positive > score of a random negative).

## 3. Results (SOURCE)
- **Liquidity imbalance predicts the next market order's sign (Fig 5, V):**
  - P(next = buy) rises from ≈ 0.5 at balance to ≈ 0.7–0.9 when best-level bid volume ≫ ask volume (W(1) ≈ +4).
  - Symmetric for sells. The text says the average reaches 0.80 when unbalanced.
  - Deeper levels (i > 1) are much noisier.
- **Out-of-sample AUC** (Table 3; one third used for estimation, two thirds for evaluation):

  | Window | BidJump AUC (SD) | AskJump AUC (SD) |
  |---|---|---|
  | Morning | 0.718 (0.058) | 0.717 (0.060) |
  | Afternoon | 0.722 (0.057) | 0.717 (0.056) |
  | All day | 0.722 (0.048) | 0.732 (0.050) |

  - The values are stable across windows and stocks.
- **Most selected features:**
  - best-level volume on the side to be hit (VB¹₀ / VA¹₀);
  - whether the last event was a market order on that side (BMO₀ / AMO₀);
  - last market-order size (VMO₀).
  - This is consistent with **long memory of order flow** (split metaorders; Bouchaud–Farmer–Lillo).
- **Trade-through is less informative than expected.**

## 4. Critical assessment (INFERENCE)
- The prediction target is **an execution/queue event, not a profitable price move**. There is no trading strategy, no cost and no latency model.
  - Knowing a jump is likely helps passive order placement and market making, not directional trading. Cf. S26: the information is in order flow and book state.
- **One month and one market.** Whether the one-third / two-thirds split is chronological is not stated. If random, the out-of-sample AUC can be inflated by within-month autocorrelation.
- An AUC of 0.72 at a ~10–15 % base rate translates into modest precision. No calibration or Brier score is reported.
- **Consistent with the corpus:**
  - S26: own and others' imbalance at levels 0–5 drive algorithm direction; large best-ask volume implies an expected down move;
  - S13: the microprice tilt toward the thinner side;
  - S06/S10: queue and fill dynamics.

## 5. NEXA relevance
- **NOT TESTABLE:** Pepperstone provides no depth volumes and no trade prints with sign (NEXA tick audit; OFI not testable). **DATA-LIMITED.**
- **Conceptual:**
  - the immediate next-event predictability lives in book imbalance and order-flow memory, which NEXA cannot see;
  - NEXA's bar-level signals should not expect to capture this horizon;
  - it supports S26's caution against public-quote LOB directional edges for NEXA.

**Cross-references:**
- S26 (agent order prediction, imbalance);
- S13 (microprice);
- S06 (sniping/queue);
- S10 (fills);
- S32 Harris (order types, market impact);
- S29 (iceberg detection uses the same dynamic-replenishment logic);
- S30 Flash Boys (order-flow information leakage).
