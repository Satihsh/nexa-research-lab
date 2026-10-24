# H-FLOW-PRED: the user's 20-component "Market Predicted" engine, spec draft (2026-10-21; APPROVED + pre-registered same day: validation/PREREG_FLOW_PRED.md)

## User request (2026-10-21, in short)
- Reverse engineer the 12 base + 8 expansion components (CFT, CFT-P, absorption, imbalance, stop runs, HVN, trapped traders, spoofing, icebergs, delta divergence, MOC, risk engine, tails, failed auctions, open drive, responsive/initiative, CVD sweeps, LVN, P/b shapes, anomalous nodes) plus ~23 ATAS indicators, in C#, in ATAS X, for an Apex account.
- Claude gives a **"Market Predicted"** signal ~10–15 min before a move; the user clicks buy/sell; the signal states entry, SL, TP and exit time.
- Goal stated: $400–500/day per account (stated as compulsory), 17/20 or 9/10 green days, later 5 accounts.
- The user's own scientific requirements (adopted as binding design rules):
  1. Define exactly what is predicted: at time T, P(price reaches +target before −invalidation within the next H minutes), **net of realistic costs**.
  2. Treat correlated indicators as one family (CVD, footprint delta, order-flow imbalance = aggressive flow); measure whether each family adds information, never count them as independent confirmations.
  3. Measure accuracy and profitability **per forecast horizon** (e.g. 30 s, 5, 10, 15 min); do not assume earlier is better.

## What NEXA already knows about the 20 components (status 2026-10-21)
| Component | Status |
|---|---|
| 1 CFT | NOT VALIDATED (ES −0.88 bp/day, NQ +0.13; order-flow gate hurt) |
| 2 CFT-P / value-area edges | T2a 80 % rule REJECTED (≈1,450 trades ES/NQ); OF-16, H-VAR inconclusive |
| 3 Absorption, 8 spoofing, 9 icebergs | need MBO; H-ICE-FEAS (free tape feasibility) pending ≈ 11-04 |
| 4 Imbalance / trend-riding | CFT gate (signed-flow persistence) added nothing |
| 5 Stop runs, 7 trapped traders | **H-SWEEP REJECTED 10-21** (NQ/ES, both directions) |
| 11 MOC / last 30 min | H-IM-NQ REJECTED (−3.1 bp) |
| 15 Open drive | ORB family: H-ORB5 REJECTED 10-21, H-ORB30L FAILED OOS |
| 16 Responsive vs initiative | T1 "auction state at 11:00" NOT PREDICTABLE |
| 18 LVN vacuum | H-LVN-SPEED: real but tiny (2–3.5 % faster) |
| 6 HVN pullback, 10 delta divergence, 13 tails, 14 failed auctions, 17 CVD sweep, 19 P/b shapes, 20 anomalous node | **Untested** |
| Options GEX / expected move / key levels | No free futures-options history (GEX dashboard: Yahoo has none) |

## Proposed design (for approval, then pre-registration)
- **Label (triple barrier):** at each decision minute T in RTH, long and short labels: +k·ATR target vs −k'·ATR stop within H ∈ {0.5, 5, 10, 15} min, outcome net of 2 NQ points (S1) and 1 point (S0). Exit = target, stop or time H.
- **Feature families** (each tested as a block, never as separate votes): A auction context (VA/POC, PDH/PDL, opening range, tails, failed auctions, profile shape, LVN/HVN distance); B aggressive flow (CVD, bar delta, imbalance stacks, big trades); C passive/DOM (walls, depth changes, absorption proxy: volume at a price with no progress); D time of day / volatility.
- **Tests:** walk-forward, purged by H; per family: drop-one-family ablation, calibration (Brier), out-of-sample R per signal at each H; placebo = shuffled-time features. Pass bar: net ≥ +0.025R per signal and CI > 0 out of sample (H-PROP-EV threshold), stable by block.
- **Data:** A + B + D from QuantConnect **tick** data for NQ/ES (trades + quotes, aggressor by quote rule), 2010–2026, free node; C (DOM) only from the NEXA recorder (since 2026-10-19, delayed feed) or paid MBO (Databento; $5 cap, needs a cost quote and user approval).
- **C# side (NEXA v6 "trade assistant"):** draws levels and walls, shows the model's probability, entry, SL, TP and exit time, and logs every forecast (taken or not) for forward scoring. Labelled **UNPROVEN** until its forward record passes the bar. Read-only; never places orders (Apex: "No Automation or Algorithm Usage").

## Honest constraints to keep in view
- No component above has passed a NEXA test; daily $ targets and 17/20 green days cannot be made compulsory by any code (see the ledger's green-day table: 17–18/20 needs ≈ 90 % daily win probability).
- H-ML1 (gradient boosting on 20 price features, 2013–2026) already failed net (−0.007R); this design differs by adding order-flow families and a short-horizon label, which is the untested part.
