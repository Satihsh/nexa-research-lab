# H-FLOW-PRED results: "Market Predicted" order-flow probability engine (NQ binding INCONCLUSIVE; ES REJECTED)

- **Pre-registration:** `PREREG_FLOW_PRED.md` (85ceb02d), before any data. Notes: `DEVIATIONS_FLOW_PRED.md` (C-1…C-6, D-1, R-1).
- **Code:** `qc_flow_pred/main.py`, frozen e507e5d0 after 14/14 synthetic tests; RUNG line set to 3 after the probe (5a23b034). The QC editor hash was verified before each run.
- **Probe:** 94 s per day on tick data ⇒ both tick windows over 8 h ⇒ **rung 3: 1-second bars, 2024 window** (D-1). Order flow is therefore signed by the tick rule (corr ≈ 0.68 with true aggressor flow in CFT) and the big-trade feature is off.
- **NQ run:** once; QC free node; project 38235648; backtest "FLOW_PRED NQ main 5a23b034" (352560e3); 2,567 s; 66.1 M data points.
- **Data:** 606 kept days after warm-up, 2024-01-31 → 2026-07-23 (25 incomplete and 9 roll days skipped); test quarters 2025Q1 … 2026Q2 (6).
- **Outputs:** raw log `qc_flow_pred/logs_nq_352560e3.txt` (sha 686ac50e, equal to the in-page hash of the QC log); parsed `qc_flow_pred/nq_results.json`.

## Verdict (NQ, binding): INCONCLUSIVE

| Horizon | OOS trades | Trades/day | **Net R/trade (S1)** | 95 % CI | One-sided p | Gross R | Win | Quarters > 0 | Brier skill | Placebo P-rank | B1 (always long, same times) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 30 s | 382 | 1.05 | **−0.203** | [−0.328, −0.117] | 1.00 | +0.053 | 47 % | 1/6 | −0.0002 | 0.10 | −0.279 | REJECTED |
| **5 min** | 172 | 0.47 | **+0.073** | [−0.037, +0.192] | 0.088 | +0.153 | 58 % | 5/6 | −0.0006 | 0.00 | **+0.067** | **INCONCLUSIVE** |
| 10 min | 127 | 0.35 | **−0.048** | [−0.158, +0.161] | 0.50 | +0.009 | 50 % | 2/6 | −0.0014 | 0.25 | −0.130 | REJECTED |
| 15 min | 112 | 0.31 | **−0.113** | [−0.249, +0.139] | 0.69 | −0.066 | 48 % | 2/6 | −0.0015 | 0.70 | −0.120 | REJECTED |

- **Binding rule:** 5 min misses VALIDATED on the CI (lower bound < 0) and p (0.088 > 0.0125). The other three are REJECTED. Overall = INCONCLUSIVE.
- **30 seconds:** the model has a small gross edge (+0.053R), but one round trip costs ≈ 0.27R at that horizon (2 points on a 7.3-point barrier). Short horizons are where costs dominate.

## What the 5-minute result really is
The binding verdict stands as INCONCLUSIVE. These diagnostics, all pre-registered outputs, say how to read it:
1. **It is mostly drift, not prediction.** The model went long on 74 % of its trades. Going long at the same times without the model earns **+0.067R**, almost all of the model's +0.073R. NQ rose through most of 2025–26.
2. **The probabilities are not better than a coin.** The Brier skill score is slightly *negative* at every horizon: the model's probabilities are a little worse than always saying the base rate (≈ 50.6 %).
3. **No family adds information** (the user's rule 2). At every horizon, dropping any family (auction context A, aggressive flow B, top of book C, time/volatility D) leaves the Brier score the same or *better*. Not one ΔBrier CI is above 0.
4. **The model leans on the clock.** The largest fitted weights are time of day (`tod` +0.16, `tod²` −0.15). The flow and book weights are about 0.01–0.03 on standardised features.
5. **Why the placebo P-rank is 0.00:** placebo models still pay costs on near-random directions (mean −0.12R), while the real model mostly went long into a rising market. A low P-rank here shows a long bias, not order-flow skill.

## Rule 3: does an earlier horizon help?
No. Accuracy does not improve at shorter horizons (Brier skill ≈ 0 everywhere). Profitability gets *worse* as the horizon shortens, because the cost per trade in R grows as the barrier shrinks (2 points = 0.27R at 30 s, 0.09R at 5 min, 0.05R at 15 min).

## What this means for the 20 components
- With free data (1-second flow, top of book, auction profile), **none of the four families carries usable information** about the next 30 s to 15 min on NQ, out of sample in 2025–26.
- This adds to the earlier single-rule failures (CFT, T2a, H-SWEEP, H-ORB5, H-ML1) and covers several components that had been untested: HVN/LVN distance, P/b profile shape, CVD, delta divergence, top-of-book imbalance and the absorption proxy.
- **Limits:**
  - flow was signed by the tick rule on 1-s bars, not true aggressor flow;
  - big trades were not measured;
  - full depth, MBO, icebergs and spoofing were not testable;
  - the test window is 2.5 years.
  - A null on true tick or MBO flow is *not* shown here.

## Use of the result (PREREG §6, binding)
- INCONCLUSIVE allows the NEXA v6 "Market Predicted" panel with the frozen 5-minute coefficients (logged in the raw file), labelled **UNPROVEN**, logging every forecast for a separately pre-registered forward test.
- **Honest note for that decision:** on this evidence the panel would mostly show a time-of-day long bias with probabilities no better than 50/50. It would not show an order-flow prediction. Building it is allowed, not recommended. It is the user's decision.
- No re-tuning on this data (NEXA law L2).

## ES (secondary): REJECTED at every horizon
- **Run:** once; backtest "FLOW_PRED ES main 440e7e2e" (7cdfbbde); editor hash 440e7e2e verified; 2,250 s; 64.4 M data points; same 606 days and test quarters as NQ.
- **Outputs:** raw log `qc_flow_pred/logs_es_7cdfbbde.txt` (sha 77ed54ff, equal to the in-page hash); parsed `qc_flow_pred/es_results.json`.

| Horizon | OOS trades | Trades/day | **Net R/trade (S1)** | 95 % CI | Gross R | Win | Quarters > 0 | Brier skill | Placebo P-rank | B1 | Long share | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 30 s | 435 | 1.20 | **−0.321** | [−0.407, −0.207] | +0.071 | 47 % | 0/6 | +0.0007 | 0.00 | −0.337 | 63 % | REJECTED |
| 5 min | 198 | 0.54 | **−0.108** | [−0.225, −0.009] | +0.007 | 47 % | 2/6 | −0.0006 | 0.35 | −0.123 | 92 % | REJECTED |
| 10 min | 201 | 0.55 | **−0.099** | [−0.207, +0.053] | −0.012 | 50 % | 2/6 | −0.0011 | 0.55 | −0.139 | 88 % | REJECTED |
| 15 min | 212 | 0.58 | **−0.094** | [−0.205, +0.050] | −0.022 | 48 % | 2/6 | −0.0012 | 0.50 | −0.122 | 89 % | REJECTED |

- **The NQ 5-minute result does not transfer:** on ES the same horizon loses −0.108R, with its whole CI below 0.
- Again, no family adds information at any horizon. The only positive Brier skill (+0.0007 at 30 s) is tiny, and costs (≈ 0.40R per trade at 30 s on ES) swamp it.
- The ES model went long 88–92 % of the time at 5–15 min, the same long tilt as NQ. On ES it did not pay.

## Overall conclusion
- **Binding: H-FLOW-PRED = INCONCLUSIVE (NQ).** ES, the secondary, is REJECTED on all four horizons.
- Read together, the evidence says free order-flow, top-of-book and auction-profile features **do not predict** NQ/ES moves 30 s – 15 min ahead, out of sample in 2025–26:
  - the one positive cell (NQ 5 min) matches the always-long drift;
  - it fails on ES;
  - no family carries information in either market.
- Under §6 the NQ verdict still permits an UNPROVEN v6 panel. Given ES, it is **not recommended**.

## Multiple testing
8 trials (4 horizons × NQ, ES). Ledger ≈ 177.
