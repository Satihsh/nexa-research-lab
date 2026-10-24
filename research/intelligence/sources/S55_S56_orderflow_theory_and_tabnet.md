# S55 & S56: order-flow theory (Hawkes / rough) and an order-flow neural-network paper

**Received 2026-10-16** (user upload). **Novelty check:**
- No earlier copy by sha256 in the repo or Downloads, and no citation in `research/knowledge/`, `research/intelligence/` or memory.
- Related items already held:
  - S34: *Zheng, Moulines & Abergel 2013*, a different Zheng, on LOB price jumps;
  - S14: Jin DPhil Ch. 5, which includes TabNet;
  - HYP-033: Hawkes quote bursts, UNTESTED.

**Files:**
- `research/corpus/2601.23172v2.pdf` (sha 95dbaa84…, 37 pp.);
- `research/corpus/Order_Flow_Technical_Analysis_And_Neural_Network_P.pdf` (sha 326addd0…, 13 pp.).

Both were read in full: text extracted with PDFKit, with the main text, theorems, figure captions and data appendix all read.

---

## S55: Muhle-Karbe, Ouazzani Chahdi, Rosenbaum & Szymanski (2026), "A unified theory of order flow, market impact, and volatility"

**Source:**
- arXiv 2601.23172v2 (2 Feb 2026), also SSRN 6155066.
- Imperial / Paris-Saclay / École Polytechnique / Luxembourg. Rosenbaum is a founder of the rough-volatility literature.
- **Preprint, not yet peer-reviewed.** OpenAlex: 1 citation.
- Status: **RESEARCH FINDING (theory + descriptive estimation)**.

**Model:**
- Order flow = **core flow** (slow, autonomous: metaorders, rebalancing, information) + **reaction flow** (market making, HFT, responses). Both are Hawkes processes.
- Requiring a non-degenerate large-time scaling limit pins almost everything to **one parameter H0**, the persistence of the core flow.

**Results:**

| Quantity | Scaling result | Value at H0 ≈ 0.75–0.80 |
|---|---|---|
| Signed order flow | → mixed fractional BM: fBM(H0) + martingale (reaction) | Hurst ≈ 0.5 at fine bins, rising to ≈ 0.65 hourly when fitted as pure fBM; **≈ 0.75–0.80 stable across bins when fitted as mixed fBM** (Fig. 4) |
| Unsigned volume | rough, Hurst H0 − ½ | ≈ 0.25; empirical 0.15–0.35 (Fig. 5) |
| Market impact of a metaorder | MI(t) ∼ t^(2−2H0) | **Square-root law** at H0 = ¾ |
| Volatility (extraday) | rough, Hurst 2H0 − 3/2 | ≈ 0–0.1, consistent with rough-vol estimates of 0.05–0.15 |

**Data:**
- BMLL trade-by-trade data with trade signs, 2021–2024.
- 40 large-cap stocks: 20 on Euronext Paris and 20 on NYSE (Appendix C).
- **No futures, no index products.**

**What it means for NEXA:**
1. **No directional signal, by construction.** Prices are kept martingales (no statistical arbitrage), and price = the market's expectation of future signed flow (eq. 2).
   - Persistent order flow is *already priced*. This is the Lillo–Farmer "efficiency paradox": order *signs* are predictable, price *changes* are not, because impact decays to cancel the predictability.
   - It is theoretical support for why our order-flow trade rules (OF-16/19/20, OFC1/OFC1R) found no edge.
2. **Execution:** square-root impact matters for large orders. At 1–5 MNQ contracts it is negligible next to the spread and commission, so there is nothing to change in NEXA's cost model (S0 / S1 / S2 = 1 / 2 / 3 points).
3. **Volatility:** rough (very anti-persistent) log-volatility supports log-HAR / rough-vol *forecasting* for risk sizing. NEXA's own T1/T2 test (2026-10-05) **rejected** "YZ/HAR beats ATR" on our instruments, so there is nothing new to adopt.
4. **Data feasibility:** estimating H0 needs aggressor-signed trades. NQ trade-level data with sides would be paid (Databento) or heavy QC tick data. A replication would be **descriptive only, with no trading value**.

**Verdict:** a high-quality theory source that **explains** the absence of order-flow edges. **No hypothesis registered.**

---

## S56: Zheng (2022), "Neural Network and Order Flow, Technical Analysis: Predicting Short-Term Direction of Futures Contract"

**Source:**
- arXiv 2203.12457v1, also TechRxiv 10.36227/techrxiv.19154276.
- Single author, Shanghai University (Dept. of Engineering).
- **Not peer-reviewed.** OpenAlex: 2 citations.
- Status: **WEAK EVIDENCE**.

**What it does (SOURCE):**
- **Data:** SHFE near-month **silver** futures, Jan 2018 – Dec 2021. CTP **500 ms snapshots**: last price, cumulative volume, open interest, 5 book levels.
- **Target:** the sign of R = log(Pα(t+15) / Pα(t)), where Pα is a **2-minute rolling VWAP** (120 snapshots). The text says "15 minutes"; the notation is ambiguous.
  - Samples with |R| < 0.001 are removed: 38.3 M → 24.3 M.
- **Features (about 100):**
  - TA on 1-min bars: A/D, OBV, CMF, Force, EOM, VPT, Bollinger, Keltner, Donchian, MACD, SMA 16/32, StochRSI;
  - accumulated spread and volume imbalance over book levels 1–5 × 4 windows (5–30 min);
  - "snapshot types" from price × open-interest change (long/short opening and closing), with a ≥ 10-lot "institutional" filter;
  - open/close-contract ratio and OI change.
  - Feature–target Pearson correlations: max 0.20, mean 0.017.
- **Model:** TabNet (n_d = n_a = 32, 5 steps), semi-supervised pre-training, Purged Group Time-Series Split with 5 folds, ensemble of the 5 fold models.
  - Train Jan 2018 – Aug 2021 (21.6 M samples).
  - **Test Sep 1 – Dec 1, 2021 (3 months, 1.41 M samples).**
- **Result:** accuracy **0.601**, recall 0.590, prediction–target correlation 0.207.
- **Backtest:**
  - Rules: long if p ≥ 0.75, short if p ≤ 0.25, exit when p crosses 0.5.
  - **Zero fees, fills at the last price, 10 % margin (≈ 10× leverage).**
  - Results: total return 20.48 %, Sharpe 1.21, **max drawdown 24.1 %**.

**Problems (NEXA review):**
1. **Look-ahead in sample selection.** The |R| < 0.1 % filter is applied to the **test set too** (Table 9 counts only the filtered rows).
   - A live trader cannot know in advance which 15-minute windows will be flat. Removing them inflates accuracy, and flat windows are exactly where the spread is lost.
2. **Mechanical predictability from the smoothed label.** Pα(t) is a *backward* 2-minute VWAP, so the label partly encodes the price path already observed between t − 2 min and t (VWAP lag). Recent-momentum features then "predict" part of the label without any forecast of the future.
   - A max feature correlation of 0.20 at a 15-minute horizon is a warning sign. No baseline tests this (for example the sign of the last 2-minute return, or logistic regression on 3 features).
3. **Overlap inflates the sample size.** A new sample every 0.5 s with a 15-minute horizon gives about 1,800 overlapping labels per independent outcome. The 1.41 M test rows correspond to only a few thousand independent 15-minute windows. **No confidence interval or significance test is reported.**
4. **The backtest cannot be used:**
   - 3 months only;
   - no costs;
   - last-price fills (no bid-ask);
   - 10× leverage (≈ +2 % unlevered gross over 3 months);
   - the number of trades is not reported, so costs cannot be estimated;
   - −24 % drawdown in a quarter.
5. **Cannot be transferred to NEXA's markets.** Tick-level open-interest changes exist in China's CTP feed but **not** in CME data, where OI is published daily. So the key "snapshot type" and open/close features cannot be built for NQ, ES or GC.
6. **Literature context:**
   - Kolm, Turiel & Westray (2023, *Math. Finance*, 115 Nasdaq stocks): order-flow-imbalance forecasts work, but the effective horizon is about **two average price changes** (seconds), not 15 minutes.
   - Nagy et al. (2023) and others: high-frequency predictability "does not directly translate into trading profits" after spread and costs.
   - This matches NEXA's own gate (LC-1: intraday edges smaller than the round-trip cost).

**Verdict:** **WEAK EVIDENCE.**
- The headline 60 % accuracy and 20 % return are not credible as a tradable edge: look-ahead sample filtering, label smoothing, overlap, a 3-month zero-cost leveraged backtest, and no baselines.
- **No hypothesis registered.**
- The user closed the order-flow line on 2026-10-11 (E1–E12; OFC1 and OFC1R REJECTED). Nothing here meets the bar to reopen it.

---

## What would change the verdicts

- **S56:** an independent replication on CME data with:
  - live-knowable samples (no outcome filtering);
  - an unsmoothed mid-price label;
  - a ≥ 2-year walk-forward test;
  - costs ≥ 1 tick per side;
  - simple baselines.
- **S55:** nothing tradable is claimed. It stays as theoretical background for the cost and volatility models.
