# NEXA — Integration Plan, Revision 2
**Supersedes `NEXA_INTEGRATION_PLAN.md` (retained, not overwritten).**
**Status: PLAN ONLY. No NEXA `.mq5`/`.mqh` modified, created, renamed or deleted.**

---

## 0. COMPILATION STATUS — CORRECTED, WITH ONE PRECISION THAT MATTERS

**Accepted:** NEXA has been compiled in MetaEditor with 0 errors and 0 warnings. MetaEditor cannot run in this environment, so compilation is **previously verified by the user, currently unreproducible here**. The "never compiled" statement in Revision 1 is withdrawn.

**The precision, because it changes what you must re-verify rather than because it is a quibble:** the last two passes rewrote code *after* any compile you performed. The 29-defect hardening pass rewrote all ten files wholesale; the D30–D44 adversarial pass then introduced constructs that did not exist in any earlier build:

| Construct | File | First appeared |
|---|---|---|
| `TRADE_TRANSACTION_REQUEST` branch, `request.*` field access | `NEXA_EA.mq5` | adversarial pass |
| `PositionFullyClosedByHistory()` (`HistorySelectByPosition`, `HistoryDealsTotal`) | `NEXA_EA.mq5` | adversarial pass |
| `NexaOrderPending()` (`OrderGetTicket`/`OrderGetString`/`OrderGetInteger`) | `NEXA_EA.mq5` | adversarial pass |
| `FileMove()` legacy-journal migration | `NEXA_EA.mq5` | adversarial pass |
| `MQLInfoInteger(MQL_TESTER)` | `NEXA_Intelligence.mqh` | adversarial pass |
| `Liquidity_ShouldProcessBar()` | `NEXA_Liquidity.mqh`, `NEXA_Features.mqh` | adversarial pass |
| `OnnxSetInputShape`/`OnnxSetOutputShape`, `NexaGMTNow()`, `CalcSetupStop()` | Intelligence / Common / EA | hardening pass |

So the correct status line is:

> **A NEXA build compiled cleanly in MetaEditor. The current bytes contain post-compile changes and are COMPILE-UNVERIFIED until re-run.**

That is not pedantry: `MqlTradeRequest` field access inside `OnTradeTransaction`, `HistorySelectByPosition`, and the ONNX shape calls are exactly the API surfaces most likely to differ by build. Re-compiling before the research tier is built costs one minute and protects everything downstream.

---

## 1. WHAT CHANGED FROM REVISION 1

Revision 1 concluded "no MQ5/MQH changes are required". **That conclusion is withdrawn.** It was correct that no repository code should be imported into the live tier, and then wrongly inferred that the live tier therefore needs nothing. Those are different claims.

The research tier cannot deliver value unless the live tier can *consume* what it produces. NEXA today can consume exactly one artifact — a raw ONNX model — and even that only as an uncalibrated probability. It cannot consume a calibration map, per-bucket expectancy, a discovered strategy definition, or a model-health verdict. **Those consumption seams are genuine, justified live-tier work**, and they are specified in §4.

Also revised per instruction: MiniBT reclassified to research reference; HMM and statistical arbitrage reclassified from rejected to **research candidates with explicit promotion criteria**.

---

## 2. REVISED SOURCE DISPOSITION

| Source | Rev 1 | Rev 2 | Basis |
|---|---|---|---|
| handiko ML backtesting | RESEARCH | **RESEARCH — primary methodology source** | Purged+embargoed CV, walk-forward retrain, in-fold feature selection, confidence gating, bps costs |
| kairos-engine | RESEARCH | **RESEARCH — primary calibration source** | Isotonic calibration, Brier, ECE, 1.5× horizon outcome resolution, cost re-costing, HMM collapse detection |
| **MiniBT** | REJECT | **RESEARCH REFERENCE** | 272k LOC backtester. Value is as a *reference implementation* for event-driven fill semantics, commission/slippage models (`com_type`), and stop handling — to cross-check that the Python labeler and the MT5 Strategy Tester agree. Not imported; consulted. |
| HFT-trading-simulator | RESEARCH | RESEARCH REFERENCE | Realized-vol estimation, toxicity→refuse pattern, ML ensemble structure. Market making itself remains inapplicable (NEXA is a taker). |
| TradeHive | CONCEPT | CONCEPT | Competing-hypothesis structure; reflection→proposal loop shape for Bounded Evolution. No LLM in any decision path. |
| lite-qmt-executor | ADAPT | ADAPT | WAL intent-before-action + restart replay |
| qmt-gateway | ADAPT | ADAPT (read-only; **no licence**) | Snapshot-at-each-callback persistence |
| moss-trade-bot-skills | REJECT/concept | CONCEPT | Reflection loop only |
| quantdinger, adaq, Hyperliquid, polymarket-bot | REJECT | REJECT | Infrastructure scaffolding / UI / leaderboard scraping / **zero source files** |
| fin-cn-agent (Chanlun) | REJECT | **REJECT for live; RESEARCH-ABLATION candidate** | A competing structure taxonomy. May be tested *as an ablation* to see whether it adds OOS information over BOS/CHoCH/MSS. Must never be stacked as an independent confirmation. **No licence — ideas only.** |

---

## 3. RESEARCH TIER — FULL CAPABILITY SET

All 17 requested capabilities, mapped to files. Python, offline, outside MT5.

| Capability | Module | Method |
|---|---|---|
| Purged cross-validation | `nexa_validate.py` | TimeSeriesSplit + purge of train rows within embargo of the validation fold (handiko) |
| Embargo | `nexa_validate.py` | Embargo ≥ max label horizon (`InpMaxHoldBars`), in rows *and* wall-clock |
| Walk-forward training | `nexa_validate.py` | Expanding window, retrain every N periods |
| In-fold feature selection | `nexa_validate.py` | Top-K by importance computed **inside each training fold only** |
| Feature importance | `nexa_ablation.py` | Gain + permutation importance, per fold, with dispersion across folds |
| **Feature ablation** | `nexa_ablation.py` | Leave-one-feature-out and leave-one-*group*-out (structure / liquidity / MTF / microstructure / session); report ΔOOS expectancy, ΔBrier, ΔECE. A feature that does not survive ablation does not enter the schema. |
| Probability calibration | `nexa_calibrate.py` | Isotonic regression (kairos); Platt as comparator |
| Brier score | `nexa_calibrate.py` | On OOS folds and final holdout separately |
| ECE | `nexa_calibrate.py` | 10-bin expected calibration error + reliability curve |
| Cost-scenario analysis | `nexa_costs.py` | Re-cost the **same trade list** under measured / padded / stressed spread + commission + slippage (kairos) |
| Monte Carlo | `nexa_montecarlo.py` | Trade-order randomisation, bootstrap, spread/slippage perturbation; p5/p25/p50/p75/p95 equity and drawdown paths; risk of ruin |
| **Regime-specific expectancy** | `nexa_conditional.py` | Expectancy per regime bucket with confidence intervals |
| **Setup-specific probability** | `nexa_conditional.py` | Calibrated P(TP before SL) per setup family |
| **setup × regime × session × direction** | `nexa_conditional.py` | Full conditional cube; **minimum sample per cell enforced**; cells below threshold reported as UNKNOWN, never as zero |
| **Strategy discovery** | `nexa_discovery.py` | §5 |
| **Model drift detection** | `nexa_modelhealth.py` | PSI / KS on each feature: training distribution vs recent live distribution |
| **Model degradation detection** | `nexa_modelhealth.py` | Rolling Brier and OOS expectancy vs the model's own acceptance baseline |
| **Calibrated ONNX export** | `nexa_export_onnx.py` | Export model + calibration map together, shape-pinned `[1,48]→[1,1]`, with `model_id`, `schema_version`, training window, acceptance metrics |

---

## 4. LIVE TIER — JUSTIFIED CHANGES (this is what Revision 1 got wrong)

Each is a **consumption seam**: it exists so a validated research artifact can be used. None imports repository code. None weakens an existing control. All are additive and default to OFF.

| # | Change | File | Why it cannot live in research |
|---|---|---|---|
| L1 | **Calibration map consumer.** Load isotonic breakpoints from `NEXA_Calibration.json`; apply to raw ONNX output before any threshold test. Fail closed if the map's `schema_version`/`model_id` does not match the loaded model. | `NEXA_Intelligence.mqh` | The live EA is what thresholds the probability. An uncalibrated 0.55 is not 55%. |
| L2 | **Conditional expectancy table consumer.** Read a research-produced `setup × regime × session × direction` table; expose expected R and sample size to the decision gate. Cells below minimum sample return UNKNOWN → no contribution. | new `NEXA_Expectancy.mqh` (extracted from `NEXA_Intelligence.mqh`) | Live sizing and the EV floor need the bucket value at decision time. |
| L3 | **Bucket key widened.** `UpdateExpectancyStats()` currently keys on (trend, vol). Extend to (setup, regime, session, direction) to match L2 and the research cube. | `NEXA_Intelligence.mqh` | Live stats must be comparable to research stats or drift detection is meaningless. |
| L4 | **Strategy registry.** A table of strategy families (id, eligibility predicate, survival state ACTIVE/WATCH/DEGRADED/SUSPENDED/RETIRED, its own stats). Liquidity-event becomes family #1; discovered families are added as data, not as new code paths. | new `NEXA_Strategy.mqh` | Promotion of a discovered strategy must not require an EA rewrite each time. |
| L5 | **Model health telemetry.** Rolling live Brier and realised-vs-predicted gap; auto-demote the model to advisory (or fail closed if `InpRequireAIConfirmation`) when degradation crosses a threshold. | new `NEXA_ModelHealth.mqh` | Degradation happens live; research sees it only after the fact. |
| L6 | **Model provenance in Trade DNA.** Log `model_id`, `calibration_id`, `strategy_id` per row. | `NEXA_EA.mq5` (`LogRow`) | Without it, forensic reconstruction cannot attribute a trade to a model version. |
| L7 | **Durable intent log (WAL).** Append-only `NEXA_WAL_<symbol>.log`: INTENT → DISPATCH → CONFIRM/REJECT, replayed at init. | `NEXA_EA.mq5` | GlobalVariables do not survive profile reset/reinstall. This is the lite-qmt-executor principle, adapted. |

**Invariant preserved across all seven:** none of L1–L7 may raise risk, widen a limit, or authorise a trade. L1/L2/L5 can only *veto or shrink*. That is the same rule the AI layer already obeys.

**Sequencing:** L1, L3, L6 are prerequisites for the research tier to be useful at all. L2, L4, L5, L7 follow once the first calibrated model exists. Nothing is built until a compile of the current bytes is confirmed.

---

## 5. STRATEGY DISCOVERY ENGINE (research tier)

**Purpose.** Search combinations such as `LiquiditySweep + MSS + FVG + Session + Regime + Spread + Microstructure + Volatility` and find which produce positive OOS expectancy after realistic costs.

**The central danger, stated up front.** A combinatorial search over ~8 predicate groups with several levels each yields thousands of candidate buckets. Testing thousands of hypotheses against one dataset *guarantees* apparently excellent in-sample cells that are pure noise. A discovery engine without multiple-testing control is a machine for manufacturing false edges — it will reliably produce the 80–90% win-rate cell you were told not to chase, and it will not survive contact with the market.

Therefore the engine is specified as a **falsification pipeline**, not a search:

```
enumerate candidate predicate combinations
  → enforce MINIMUM SAMPLE per cell (else UNKNOWN, discarded)
  → evaluate ONLY on training folds
  → apply MULTIPLE-TESTING CORRECTION (Benjamini-Hochberg FDR across
    all cells tested; record the exact number tested)
  → survivors go to walk-forward OOS
  → survivors re-costed under stressed spread (kairos)
  → Deflated Sharpe Ratio / PBO to quantify selection bias
  → Monte Carlo stability
  → ACCEPTANCE GATE
  → strategy registry entry (live-eligible, family added as DATA)
```

**Reported per candidate:** trade count, calibrated win probability, expectancy in R, profit factor, max DD, tail loss, cost sensitivity, fold dispersion, number of hypotheses tested alongside it, FDR-adjusted significance, DSR/PBO.

**Explicitly not an optimiser toward a win-rate target.** The engine answers "does any setup/regime bucket sustain a high *calibrated* probability while keeping positive expectancy after realistic costs?" — and it is permitted to answer **no**. That answer is a valid and useful result, and will be reported as such rather than tuned away.

---

## 6. RESEARCH CANDIDATES WITH PROMOTION CRITERIA

Neither is live by default. Neither is rejected.

**HMM regime model.** Compared head-to-head against the existing `VolRegime`/`SwingTrendArr` classifier and against a no-regime baseline. Kairos ships collapse detection because HMMs get stuck in a single state — that guard is mandatory in any NEXA evaluation. *Promotion criteria:* beats baseline on OOS expectancy across ≥3 walk-forward folds, does not collapse, improves ECE, and adds no live dependency beyond a state label.

**Statistical arbitrage.** Reclassified from rejected to **future strategy family, capital-gated**. The obstacle is arithmetic, not conceptual: a two-leg spread at 0.01 lots per leg on a $100 account exceeds the 1% risk ceiling before the thesis is even tested. *Eligibility:* equity sufficient for both legs inside the hard ceiling (roughly $600+ on majors by the Part 27 analysis, higher with XAUUSD), plus cointegration stability, half-life within holding horizon, and OOS expectancy after both legs' costs. Research may proceed at any time; live eligibility waits on capital.

---

## 7. PROPOSED FILE TREE

```
MQL5/Experts/          NEXA_EA.mq5                [L6, L7]
MQL5/Include/          NEXA_Common.mqh
                       NEXA_Features.mqh
                       NEXA_Liquidity.mqh
                       NEXA_Risk.mqh              [unchanged]
                       NEXA_Intelligence.mqh      [L1, L3]
                       NEXA_Expectancy.mqh        NEW [L2]
                       NEXA_Strategy.mqh          NEW [L4]
                       NEXA_ModelHealth.mqh       NEW [L5]
                       NEXA_Microstructure.mqh    [unchanged]
                       NEXA_Advanced_Ingest.mqh   [unchanged]
                       NEXA_FOMC.mqh              [unchanged]
MQL5/Scripts/          NEXA_TrainingExport.mq5
                       NEXA_SpecSnapshot.mq5  NEXA_TickLogger.mq5  NEXA_DealAudit.mq5
research/              nexa_ingest.py       nexa_validate.py    nexa_calibrate.py
                       nexa_conditional.py  nexa_ablation.py    nexa_discovery.py
                       nexa_costs.py        nexa_montecarlo.py  nexa_modelhealth.py
                       nexa_export_onnx.py  PROVENANCE.md
```

`NEXA_Risk.mqh` is deliberately untouched. Every risk invariant currently in the build stays exactly as it is.

---

## 8. EXECUTION ORDER

1. **Re-compile the current bytes in MetaEditor** and report errors/warnings. Everything downstream assumes this passes.
2. Live seams L1, L3, L6 (calibration consumer, widened bucket key, model provenance).
3. Research tier: ingest → validate → calibrate → conditional → ablation.
4. Strategy Discovery with FDR + DSR/PBO.
5. Cost scenarios + Monte Carlo.
6. Acceptance gate → first calibrated ONNX export.
7. Live seams L2, L4, L5, L7.
8. HMM and stat-arb evaluated as candidates against baseline.

---

## AWAITING APPROVAL

No source file will be modified until you give the explicit instruction. Baseline remains backed up and checksum-verified (16/16 OK).
