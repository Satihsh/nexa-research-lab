# NEXA — Final Implementation Plan, Revision 3
**Supersedes V2 (retained). Status: PLAN ONLY — no NEXA `.mq5`/`.mqh` modified, created, renamed or deleted.**
**Baseline: 16/16 checksum-verified, untouched, not overwritten.**

---

## A. FINDING THAT CHANGES SEQUENCING (amendment 3)

Amendment 3 requires a canonical schema containing `decision timestamp`, `label start/end`, `timeframe`, `MFE`, `MAE`, `execution costs`, `model version`, `calibration version`. **Ten of those fields are absent from the current Trade DNA journal**, verified against `NEXA_EA.mq5`:

| Required field | Present today? | Where it must come from |
|---|---|---|
| `decision_ts` | **ABSENT** (only wall-clock write time) | Live — the closed bar's time driving the decision |
| `label_start_ts` / `label_end_ts` | **ABSENT** | Python labeler |
| `timeframe` | **ABSENT** | Live |
| `mfe_r` / `mae_r` | **ABSENT** | Python labeler (M1 reconstruction); live MFE/MAE optional later |
| `commission` / `swap` | **ABSENT** | Live, from deal history at close |
| `model_id` / `calibration_id` | **ABSENT** | Live (seam L6) |
| bid/ask separately | **ABSENT** (only `spread`) | Live |

**Consequence:** the schema cannot be written as documentation over the existing journal. Live seam **L6 (provenance + schema completion) becomes a Stage-0 prerequisite**, not a late-stage seam. Any data collected before L6 is structurally incapable of supporting calibration or drift detection, because it cannot say which model produced it or when the decision was taken.

This is the single most important consequence of amendment 3, and it moves work earlier rather than later.

---

## B. CANONICAL NEXA RESEARCH DATASET SCHEMA v1.0 (amendment 3)

One definition, emitted as `nexa_schema_v1.json`, consumed by both sides. MQL5 writes it; Python validates against it and **refuses to load a file whose `schema_version` differs**.

### B.1 Identity & timestamps (timestamp semantics are normative — amendment 4)

| Field | Type | Definition |
|---|---|---|
| `schema_version` | str | `"1.0"`. Mismatch = hard stop, both sides. |
| `row_id` | str | `symbol:decision_ts:seq` — unique, stable across re-export |
| `symbol` | str | Broker symbol string exactly as traded |
| `timeframe` | str | Entry timeframe of the deciding chart (e.g. `M1`) |
| `decision_ts` | datetime (broker server time, seconds) | **Open time of the CLOSED bar whose features drove the decision.** Not wall-clock, not the forming bar. This is the "standing here, now" instant for every causality claim. |
| `dispatch_ts` | datetime | When the order was sent |
| `fill_ts` | datetime | Deal execution time from history |
| `label_start_ts` | datetime | `= fill_ts`. Labelling starts at the fill, never at the decision. |
| `label_end_ts` | datetime | When a barrier was touched or the horizon expired |
| `bar_time_source` | str | `CLOSED_BAR` — asserted constant; any other value invalidates the row |

**Normative rule:** every feature in a row must be computable from data with timestamp **≤ `decision_ts` + one bar period** (i.e. from the closed bar at `decision_ts` and earlier). `label_*` fields are the only fields permitted to reference data after `decision_ts`, and they may never be used as model inputs.

### B.2 Market state at decision

`bid`, `ask`, `spread`, `spread_atr_ratio`, `atr`, `atr_m15`, `session_tag`, `regime_trend`, `regime_vol`, `regime_transitioning`.

### B.3 Features — the frozen 48

`f00..f47`, in the exact order emitted by `PackFeatures()` in `NEXA_Intelligence.mqh`, which is the **single authoritative source**:

```
00 structureBreakUp      12 sweepDown            24 trendM5              36 liqBarsBeyond
01 structureBreakDown    13 fvgBullActive        25 trendM15             37 liqBarsSinceReclaim
02 isBOS_up              14 fvgBearActive        26 trendH1              38 liqSweepDirection
03 isBOS_down            15 obBullActive         27 htfAlignment         39 liqResponseDirection
04 isCHoCH_up            16 obBearActive         28 spreadATRRatio       40 liqMssAfter
05 isCHoCH_down          17 inOTE_up             29 usdCompositeDirection41 liqDisplacementAfter
06 isMSS_up              18 inOTE_down           30 obiProxy             42 liqFvgAfter
07 isMSS_down            19 bprActive            31 cvdProxy             43 liqEventActive
08 displacementUp        20 trendState           32 liqState             44 liqLevel
09 displacementDown      21 volState             33 liqResolution        45 liqSetup
10 displacementATR       22 breakoutState        34 liqExcursionATR      46 liqOrigin
11 sweepUp               23 regimeTransitioning  35 liqWickBodyRatio     47 newsRiskActive
```

Append-only. Reorder or delete = new `schema_version` + mandatory retrain.

### B.4 Setup, decision, execution

`strategy_id`, `liq_setup`, `liq_origin`, `liq_level`, `direction`, `composite_score`, `quality_score`, `entry_intended`, `entry_actual`, `sl_price`, `tp_price`, `target_r`, `risk_dist`, `lots`, `slippage_points`, `commission`, `swap`, `spread_cost_r`.

### B.5 Model provenance (seam L6)

`model_id`, `model_schema_version`, `calibration_id`, `ai_raw_p`, `ai_calibrated_p`, `conditional_expectancy_r`, `conditional_sample_n`, `decision_source` ∈ {`RULE_ONLY`, `RULE_PLUS_AI`, `SHADOW`}.

### B.6 Outcome (Python-populated; never a model input)

`label` ∈ {1 TP-first, 0 SL-first, −1 horizon}, `label_reason`, `ambiguous_bar`, `bars_to_outcome`, `mfe_r`, `mae_r`, `result_r`, `exec_model`.

---

## C. FEATURE PARITY CONTRACT (amendments 4 & 5)

**The problem being prevented:** MQL5 and Python each computing "ATR" or "displacement" slightly differently produces a model trained on features the live engine never actually sees. It fails silently and looks like alpha decay.

**Rule: Python does not reimplement features.** For training, Python consumes `f00..f47` exactly as MQL5 emitted them. The Python feature engine exists **only** as a parity oracle and for research-only candidate features never yet in the live path.

**Parity test (`nexa_parity.py`), mandatory gate:**
1. MQL5 exports features for N historical `decision_ts` values (Strategy Tester run over a fixed window).
2. Python recomputes the same 48 from the same OHLC/tick history.
3. Compare per feature: booleans/enums must match **exactly**; continuous features within `1e-6` relative tolerance.
4. Report per-feature mismatch rate and worst-case delta.
5. **Any material mismatch halts training.** Not a warning — an exit code. The parity report is an artifact attached to every trained model.

Known parity hazards to be resolved explicitly, not papered over: broker-specific D1 boundary for PDH/PDL; `InpGMTOffset` session attribution; ATR seeding (Wilder's smoothing warm-up); the `liqOrigin` LIVE-vs-RECONSTRUCTED distinction; and tick-derived `obiProxy`/`cvdProxy`, which **cannot** be reproduced from bar data and are therefore parity-**exempt but flagged** — with an explicit test that they are never the sole basis of a promotion decision.

---

## D. LIVE SEAM CONTRACTS (amendment 8)

Every seam specifies input, output, failure, default, version compatibility, tests, rollback. Universal invariant: **a seam may veto or shrink; it may never authorise, widen a limit, or raise risk.**

### L6 — Provenance & schema completion  *(Stage 0 prerequisite)*
- **In:** live signal, model/calibration ids, deal history at close.
- **Out:** Trade DNA rows conforming to schema v1.0.
- **Failure:** file unavailable → journal disabled, **trading continues** (journalling is not a risk control); schema mismatch on existing file → move aside (existing `FileMove` behaviour).
- **Default:** always on.
- **Version:** writes `schema_version`; Python refuses on mismatch.
- **Tests:** header matches `nexa_schema_v1.json`; `decision_ts` == closed-bar time (never wall-clock); commission/swap reconcile against `NEXA_DealAudit` output.
- **Rollback:** revert file; journal reverts to prior format; no trading behaviour touched.

### L1 — Calibration map consumer
- **In:** `NEXA_Calibration.json` (isotonic breakpoints, `model_id`, `calibration_id`, `schema_version`).
- **Out:** `ai_calibrated_p` ∈ [0,1].
- **Failure:** file missing/malformed/`model_id` mismatch/non-monotone map → **calibrated p unavailable (−1)**. With `InpRequireAIConfirmation=true` → NO TRADE (existing fail-closed). With false → rule engine decides, exactly as today.
- **Default:** OFF (`InpUseCalibration=false`) → behaviour byte-identical to current build.
- **Version:** map `schema_version` must equal model's must equal `NEXA_AI_SCHEMA_VERSION`.
- **Tests:** monotonicity; endpoints in [0,1]; mismatched id rejected; absent file leaves behaviour unchanged.
- **Rollback:** set input false.

### L3 — Widened expectancy bucket key
- **In:** `(strategy_id, liq_setup, regime_trend, regime_vol, session, direction)`.
- **Out:** rolling expectancy + sample count per cell.
- **Failure:** cell below `InpMinBucketSample` → **UNKNOWN**, contributes nothing (never treated as zero or as a pass).
- **Default:** new keys written alongside legacy keys for one release; no gate consumes them until L2.
- **Tests:** UNKNOWN never unlocks a trade; legacy stats preserved.
- **Rollback:** ignore new keys.

### L2 — Conditional expectancy consumer
- **In:** research-produced table, same cube as L3.
- **Out:** expected R + n for the current cell.
- **Failure/UNKNOWN:** no contribution. May only **veto** (EV floor) — never size up.
- **Default:** OFF.
- **Tests:** negative-EV cell vetoes; UNKNOWN is neutral; table cannot increase lots.
- **Rollback:** input false.

### L4 — Strategy registry
- **In:** registry table (id, eligibility predicate, survival state).
- **Out:** eligible strategy for the bar.
- **Failure:** unparseable → only built-in family #1 (liquidity event) active.
- **Default:** family #1 only — identical to today.
- **Tests:** SUSPENDED/RETIRED never trades; unknown id ignored.
- **Rollback:** input false.

### L5 — Model health
- **In:** rolling live outcomes vs predicted p.
- **Out:** rolling Brier, PSI, verdict ∈ {HEALTHY, WATCH, DEGRADED}.
- **Failure:** insufficient sample → HEALTHY-but-unproven; **no authority either way**.
- **Action on DEGRADED:** demote model to advisory; if `InpRequireAIConfirmation=true`, fail closed. **Never** relaxes a gate.
- **Tests:** degradation demotes and never promotes.
- **Rollback:** input false.

### L7 — Durable intent log (WAL) — amendment 2
- **In:** INTENT / DISPATCH / CONFIRM / REJECT records.
- **Out:** replayed intent at init.
- **AUTHORITY — explicit:** **WAL is never authoritative.** It records intent and aids reconciliation. On any disagreement, **broker state wins**: if WAL says a position exists and the broker shows none → WAL entry closed as UNRESOLVED, no position assumed, no trade opened to "restore" it. If the broker shows a position the WAL lacks → the broker's position is adopted and managed. WAL may never cause an order to be sent, never re-creates a position, never authorises size.
- **Failure:** unwritable → log the failure, **continue trading** (existing GlobalVariable staging remains; WAL is additive durability).
- **Default:** OFF.
- **Tests:** WAL-says-open/broker-says-flat → no order sent; broker-says-open/WAL-silent → adopted; corrupted tail → truncate and continue.
- **Rollback:** input false; file ignored.

---

## E. STAT-ARB CAPITAL ELIGIBILITY — DYNAMIC (amendment 1)

The "$600" figure is withdrawn. Eligibility is computed from live broker state at evaluation time:

```
for each leg L in {A, B}:
    riskPerStep_L = |OrderCalcProfit(type_L, sym_L, volStep_L, entry_L, stop_L)|
    riskPerLot_L  = riskPerStep_L / volStep_L
    minLotRisk_L  = riskPerLot_L * volMin_L          // unavoidable risk at broker minimum
    margin_L      = OrderCalcMargin(type_L, sym_L, volMin_L, entry_L)

pairMinRisk    = minLotRisk_A + minLotRisk_B          // correlation-adjusted where hedge ratio < 1
pairMinMargin  = margin_A + margin_B

ELIGIBLE  iff  (pairMinRisk / AccountEquity * 100) <= InpHardRiskCeiling
          AND  pairMinMargin <= AccountMarginFree * (InpMaxMarginUsagePct / 100)
          AND  hedge ratio achievable within volume steps of both legs
```

No constant appears anywhere. The same broker-native calls the risk engine already uses (`OrderCalcProfit`, `OrderCalcMargin`, `SYMBOL_VOLUME_*`) decide eligibility, so it adapts automatically to symbol, broker, leverage and equity. Where the hedge ratio cannot be expressed in whole volume steps on both legs, the pair is **INELIGIBLE** — residual unhedged exposure is not silently accepted.

---

## F. SHADOW MODE (amendment 6)

Mandatory stage between research acceptance and live authority. The candidate runs on live/demo data with **zero execution authority**.

Per bar, one `SHADOW` row: `decision_ts`, incumbent decision + reason, candidate decision + reason, `ai_raw_p`, `ai_calibrated_p`, `conditional_expectancy_r`, `conditional_sample_n`, and — once resolvable — the actual outcome of the *incumbent's* trade, plus the counterfactual outcome of the candidate's proposal under the same triple-barrier labeler.

**Implementation constraint that keeps this honest:** the shadow path calls the same `ComputeCompositeScore`/`CalcSetupStop`/labeler as live. A shadow evaluated by different code proves nothing about the live system.

**Exit criteria:** ≥ `InpShadowMinDecisions` overlapping decisions; candidate's calibrated probabilities pass Brier/ECE on shadow data; candidate expectancy after **measured** costs exceeds incumbent's on the same period; no increase in tail loss. Shadow disagreement alone is not failure — only worse calibrated, cost-adjusted expectancy is.

---

## G. PROMOTION GATE (amendment 14)

```
RESEARCH → VALIDATION (purged CV + embargo, in-fold selection)
         → OOS (walk-forward, untouched holdout once)
         → COST STRESS (measured / padded / stressed re-costing)
         → MONTE CARLO (order randomisation, p5..p95, risk of ruin)
         → CALIBRATION (isotonic; Brier + ECE within tolerance)
         → SHADOW (live/demo, no authority, exit criteria §F)
         → PROMOTION (signed record: model_id, calibration_id, training window,
                       parity report, all gate metrics, approver)
         → LIVE (seam default flipped on; rollback = flip off)
```

Any gate may return **REJECT**, including "no bucket qualifies" (amendment 13). That outcome is reported as a result, not iterated away. **No stage may be skipped, and no model reaches LIVE without a passing parity report.**

---

## H. BUILD ORDER WITH INTEGRATION TESTS (amendments 7, 11, 12)

**Stage 0 — baseline compile (blocking).** Re-compile current bytes in MetaEditor; report exact errors/warnings. **If the baseline does not compile, nothing proceeds.** Post-compile constructs to watch: `request.*` in `OnTradeTransaction`, `HistorySelectByPosition`/`HistoryDealsTotal`, `OrderGetTicket`, `FileMove`, `MQLInfoInteger(MQL_TESTER)`, `OnnxSetInputShape`/`OnnxSetOutputShape`.

| Stage | Deliverable | Integration test before proceeding |
|---|---|---|
| 1 | Schema v1.0 + **L6** | Tester run emits rows validating against `nexa_schema_v1.json`; `decision_ts` == closed-bar time |
| 2 | `nexa_ingest.py` | Round-trip: every exported row parses, no silent drops, counts reconcile |
| 3 | `nexa_parity.py` | 48/48 features within tolerance; exempt tick features flagged |
| 4 | `nexa_labels.py` | Labels reproduce EA exit logic on known trades; ambiguity rate reported |
| 5 | `nexa_validate.py` | Purge/embargo verified: no train row within embargo of any val row |
| 6 | `nexa_model.py` | Trains; in-fold selection provably inside folds |
| 7 | `nexa_calibrate.py` | Brier/ECE improve vs uncalibrated; map monotone |
| 8 | `nexa_conditional.py` | Cube cells respect minimum sample; UNKNOWN propagates |
| 9 | `nexa_ablation.py` | Leave-one-out and leave-one-group-out ΔOOS reported |
| 10 | `nexa_discovery.py` | FDR correction applied; hypothesis count recorded; DSR/PBO computed |
| 11 | `nexa_costs.py` + `nexa_montecarlo.py` | Same trade list re-costed; percentile paths produced |
| 12 | `nexa_export_onnx.py` | Shape `[1,48]→[1,1]`; model+calibration exported together |
| 13 | **L1, L3** | Absent/invalid map → unchanged behaviour; UNKNOWN never unlocks |
| 14 | Shadow (§F) | Shadow rows logged; zero execution authority demonstrated |
| 15 | **L2, L4, L5, L7** | Each seam's test set in §D |

After **every** stage: compile → run tests → inspect logs → verify invariants → only then proceed.

---

## I. PRESERVED WITHOUT CHANGE (amendments 9, 10, 15)

`NEXA_Risk.mqh` unchanged unless a concrete defect is demonstrated with a reproducing case. All existing execution/recovery invariants retained: broker-authoritative state, async `TRADE_TRANSACTION_REQUEST` handling, deal-history full-close detection, verified in-flight timeout resolution, magic+symbol ownership, server-side SL enforcement and re-protection, hard ceiling with post-normalisation recheck, daily loss / drawdown / trade-count / margin / spread / correlation / exposure gates, AI fail-closed, FOMC fail-closed, causal closed-bar features, shadow ledger diagnostic-only.

Baseline backup `NEXA_BASELINE_BACKUP_20260919-124052/` is **immutable**: never overwritten, never deleted. Any future backup takes a new timestamp.

---

## STOPPING HERE

No source modified. Next action is yours: **Stage 0 — compile the current bytes and paste the exact MetaEditor output.** If it is clean, say so and I will build Stage 1 (schema + L6). If it errors, paste verbatim and I will fix before anything else is built.
