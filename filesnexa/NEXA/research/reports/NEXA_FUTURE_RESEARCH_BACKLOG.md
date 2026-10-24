# NEXA future research backlog (NOT part of PHASE3_SIX_FAMILIES_V2)

These are hypotheses only. None is added to V2, changes V2 protocols or universe, or has been evaluated.

Each item needs:
1. its own frozen campaign;
2. a declared trial count, added to the global multiple-testing ledger (V2 already consumes 1,740 DSR trials);
3. causality-certified builders;
4. a genuinely unseen, prospective OOS.

Sources are listed in `NEXA_COMMERCIAL_EA_PRIOR_ART_AUDIT_2026.md`.

| ID | Falsifiable research question | Motivating prior art | Data needed | Primary test / null | Invariant constraints | Status |
|---|---|---|---|---|---|---|
| B1 | Does a veto-only meta-label model (P(trade R>0 \| features at decision_ts)) reduce NEXA's per-trade loss rate **without** reducing E[R] per opportunity, out of sample, versus the unfiltered rule? | Mad Turtle (meta-model), Perceptrader (AI gate) | NEXA Trade DNA with resolved labels (≥ 200 resolved), purged | E[R] per decision filtered vs unfiltered; random-veto null at the same veto rate; DSR | AI may only veto (inv. 16); `InpRequireAIConfirmation` fail-closed (inv. 17) | blocked: too few resolved NEXA trades (B-EXPOSURE-CAP) |
| B2 | Are ONNX model probabilities **calibrated**: does the Brier score and reliability curve beat a base-rate predictor OOS? | Mad Turtle, AI Forex Robot | same as B1 | Brier skill > 0 with bootstrap CI; isotonic vs Platt pre-declared | schema v1.0 unchanged; calibration is seam L1 | blocked (no model) |
| B3 | Does a pre-declared regime classifier (trend/range/high-vol/event) separate NEXA's conditional expectancy, i.e. differ across regimes beyond a shuffled-label null? | AI Forex Robot (regime detection) | D1/H1 bars; Trade DNA | between-regime E[R] difference; permutation null; FDR over regimes | may only reduce or veto risk | open |
| B4 | Does a US-evening (19:00–23:00 broker) M5 mean-reversion rule on crosses beat timing/direction/circular nulls after costs? | Evening Scalper Pro | M1 crosses with spread (outside NEXA's 4 symbols, so a data decision is needed) | as V2 §1.3 + a same-rule-other-session null | new symbols need human approval | open (data) |
| B5 | Does an "ATR candle breakout" (bar range > k·ATR) continue beyond matched random bars after costs on H1 XAUUSD/FX? | BM Trading | existing H1 | continuation vs matched-bar null | none | open; note the prior factory breakout ≈ random on gold |
| B6 | Is there a day-of-week effect (e.g. Monday-to-Tuesday reversal on index CFDs) that survives costs and a day-shuffle null? | BM Trading "Turnaround Tuesday" | index CFD D1 (not in NEXA) | day-shuffled null | new symbols need human approval | open (data) |
| B7 | Does a hard one-trade-per-day cap change risk-adjusted outcome versus NEXA's current 10/day cap (drawdown and E[R] per day)? | Apex Drawdown Zero (SC) | NEXA tester runs | paired comparison on identical signals | may only tighten risk (inv. 16); 10/day stays the ceiling | blocked (B-EXPOSURE-CAP) |
| B8 | Does conditioning on execution quality (spread percentile at the decision bar, rollover proximity) change realised slippage and E[R]? | Night Hunter / Evening Scalper (latency, spread sensitivity) | real ticks logged after the freeze (`NEXA_TickLogger`) | realised vs modelled cost; regression with HAC SE | spread ≤ 15 % ATR stays a hard veto | blocked until enough post-freeze ticks |
| B9 | Does a swap-aware filter (skip entries whose expected hold crosses rollover on the negative-swap side) improve net E[R]? | Night Hunter, Evening Scalper | historical swap rates (**not available**; only a 2026-09 snapshot) | net E[R] with vs without | none | blocked: no historical swap data |
| B10 | Does a strategy-disagreement / abstention rule (trade only when independent families agree) improve E[R] per opportunity beyond a random-abstention null? | AlgoBook strategy pool, Perceptrader | ≥ 2 independently validated families (none yet) | agreement vs random abstention | none | blocked (no validated family) |
| B11 | Does a pre-declared strategy-retirement rule (retire a strategy when a rolling OOS E[R] CI falls below 0) reduce drawdown versus no retirement, in walk-forward? | Night Hunter (post-2023 decay), Waka Waka (2024 losses) | ≥ 1 validated live strategy | walk-forward drawdown and E[R] | may only reduce risk | blocked |
| B12 | Does cross-pair allocation (inverse-vol or equal-risk across families) reduce portfolio drawdown versus single-family trading, with correlation estimated causally? | Night Hunter / Evening Scalper multi-pair | ≥ 2 validated families | portfolio DD and E[R] | correlation / exposure caps unchanged (inv. 7) | blocked |

**Explicitly excluded from the backlog as incompatible:** grid, martingale or lot scaling after losses, averaging down, recovery modes, disabled stop-losses, forced trade frequency, and any mechanism that bypasses `NEXA_Risk.mqh`.
