# NEXA architecture gap audit (2026-09-29)

Scope: evidence from repository files. Commercial prior art is from `NEXA_COMMERCIAL_EA_PRIOR_ART_AUDIT_2026.md` and is unverified. Nothing speculative was implemented.

"Blocked" means work is blocked by data, by an open human decision, or by a missing validated component.

| Capability | Current NEXA state | Evidence | Commercial prior art | Gap | Risk | Future work | Blocked / unblocked |
|---|---|---|---|---|---|---|---|
| Research Engine | Offline Python tier with stats, robust, labels, parity, validate and factory modules; 446 tests | `research/` | — | no validated edge yet | overfitting (controlled by registry + DSR/PBO) | run V2 only after approval | unblocked (awaits opening) |
| Strategy Factory | Frozen-protocol factory; XAUUSD/Pepperstone H1 runs: 0 survivors | `nexa_factory*.py`, `FACTORY_XAUUSD_H1.md` | BM Trading-style single-strategy EAs | no multi-family portfolio | — | backlog B10–B12 | blocked (no validated family) |
| ML inference | ONNX seam: load, schema check, run; AI veto-only; fail-closed when required | `NEXA_Intelligence.mqh` | Mad Turtle, AI Forex Robot (claims) | no trained model | model overfit | backlog B1 | blocked (too few resolved trades; B-EXPOSURE-CAP) |
| ONNX | Runtime path present; `AI_ModelId` provenance | `NEXA_Intelligence.mqh` | Mad Turtle (claim) | no model artifact | — | B1/B2 | blocked |
| NEXA Judge | Composite gate: liquidity event required, hard vetoes, quality score ≥ 5 | `NEXA_EA.mq5` `ComputeCompositeScore` | multi-filter confirmation (Night Hunter etc.) | untested edge | — | — | unblocked (engineering) |
| Deterministic Risk | 1 % ceiling, 2 % daily, 10 % DD, 10/day, spread ≤ 15 % ATR, margin/correlation/exposure caps | `NEXA_Risk.mqh` (`e706d453d346100f`) | "Guardian"/drawdown modes (claims) | **M1: correlation cap fails open on missing history**; exposure cap blocks trading | HIGH (M1) | human decision (file frozen) | blocked (human) |
| Execution Engine | Async with in-flight guard; no retry of ambiguous retcodes; SL re-application; ratcheting stops | `NEXA_EA.mq5` | VPS/latency emphasis | no `OrderCheck` (M5), no freeze-level check (M6), fixed deviation (M9) | LOW | small engineering fixes | unblocked |
| Trade DNA | schema v1.0, 96 columns, causal `decision_ts`, provenance | `NEXA_EA.mq5`, `nexa_schema_v1.json` | AlgoBook `TradeReport` | no `OnTester` summary (M3) | LOW | OnTester R metrics | unblocked |
| Multi-symbol synchronisation | one instance per chart; cross-symbol reads by shift | `NEXA_Risk.mqh`, `NEXA_Intelligence.mqh` | AlgoBook `MultiSymbolMonitor` (same-time check) | no time alignment / sync check (M1, M4) | HIGH | time-aligned reads, fail closed | blocked (Risk file frozen) |
| Session engine | session tags; optional GMT session filter; weekend close (server Friday) | `NEXA_EA.mq5`, `NEXA_Common.mqh` | Asian/evening session EAs | D-TZ fixed offset (M2) | MEDIUM | DST-aware clock (research has `nexa_time`) | blocked (human D-TZ) |
| Event / calendar engine | Tier-3 news veto + FOMC hard gate (EA); research: MT5 calendar export, first-print provenance, prior-only baselines | `NEXA_FOMC.mqh`, `nexa_calendar.py` | news filters (most EAs) | no live first-print logger | — | calendar logger for F1 OOS | unblocked (engineering) |
| Regime detection | trend/vol regime + transition features (EA); D1 regime filter (V2 F5) | `NEXA_Features.mqh`, `nexa_v2_features.py` | AI Forex Robot regimes (claim) | no calibrated classifier | — | backlog B3 | unblocked (research) |
| Probability calibration | `AI_CalibrationId()="NONE"` (truthful) | `NEXA_Intelligence.mqh` | — | missing | — | backlog B2 | blocked (no model) |
| Model monitoring | expectancy buckets; shadow ledger (diagnostic only) | `NEXA_Intelligence.mqh`, `NEXA_EA.mq5` | — | no automated alerting | — | — | unblocked |
| Drift detection | research validate gate; parity oracle | `nexa_validate.py`, `nexa_parity_full.py` | — | liquidity state machine residual (0.2–0.85 %) | MEDIUM | debug one episode | unblocked |
| Tester reporting | Trade DNA + tester verify scripts | `nexa_tester_verify.py` | AlgoBook OnTester/frames | no `OnTester` | LOW | M3 | unblocked |
| Experiment registry | V2: external anchor, witness, R1 checkpoint (compare-and-swap), certified builders, closed universe, budgets | `nexa_registry2.py`; 70/70 attacks rejected | — | off-machine record is manual | R1 residual (human) | Git remote + signed tags | unblocked (human action) |
| Causal feature system | registry-run certification with sensitive cuts; event-table certification | `nexa_causality.py` | — | certification is empirical (perturbation), not proof | LOW | — | done |
| OOS governance | prospective OOS 2027; EXCLUDED 2025–2027-01-04; one OOS per group | `OOS_DETERMINATION_V2.md`, registry | — | OOS data still to be collected | — | collect 2027 data | time-blocked until 2028-01-03 |
| Execution simulation | trade-through limits, stop-first, gaps, latency, costs; intrabar-fill target fix | `nexa_execution.py` | — | bar spread may understate; swap snapshot | MEDIUM | real-tick validation (post-freeze ticks) | unblocked |
| Portfolio / risk orchestration | per-symbol instances + global caps via GlobalVariables | `NEXA_Risk.mqh` | cross-pair diversification EAs | no allocator; caps not testable in a single-symbol tester (M4) | MEDIUM | backlog B12 | blocked (no validated families) |
