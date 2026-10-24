# NEXA PROGRESS

## LATEST: 2026-10-01 RESEARCH_8E_V1 integrity gate: STOPPED before VAL, selection and OOS

**Reports** (`research/reports/`):
- `NEXA_24_5_TRUTH_TABLE.md`
- `NEXA_8_ENGINE_RESULTS.md` (PRELIMINARY, DEV only)
- `NEXA_PEPPERSTONE_COST_AND_SIZING_AUDIT.md`
- Earlier: `NEXA_24_5_DAILY_FEASIBILITY_AUDIT.md`, `NEXA_8_ENGINE_SPECIFICATION.md`, `NEXA_CAPITAL_VELOCITY_DESIGN.md`, `NEXA_8_ENGINE_EXPERIMENT_MATRIX.md`, `NEXA_8_ENGINE_DEEP_RESEARCH_2026.md`

**Registries**
- **V2 integrity: PROVEN intact.** 42/42 files; verify passes at seq 6; FROZEN, not opened, 0 results.
- **8E:** `research/registry_8e`, anchor `6468fdea…`, OPENED for research at seq 3 `1e84a047…`; 0 results (no VAL/OOS rows).
- **Accidental duplicate freeze.** `freeze_8e.py --help` treated `--help` as the registry root and created anchor `c472d69f…` (seq 0, 0 results). It is now quarantined as `research/registry_8e_ACCIDENTAL_c472d69f` (+ `.ACCIDENTAL.txt`). Never open it. Its witness file is kept.

**+24.5 %/day math: PROVEN.**
- With ≤ 10 trades at 1 % risk, every trade needs ≥ 2.2156R.
- Zero-edge bound: P(target on a day) ≤ 10.84 %. This bounds a probability, not a return.
- **DEV evidence:** 0 target days in all 1,774 streams, at $200 and at $10k, under every stress scenario.

**$200**
- XAU needs stop ≤ $1.684, which is statistically non-viable: −0.21R at random entry after 18.8 % cost.
- NAS100 is DATA-LIMITED.
- EUR/GBP can be sized at $200, but their DEV edge is negative.

**Data limits**
- **OFI:** not measurable (quote-only feed). The 300 % hypothesis FAILED.
- **Big Trades:** not measurable. Renamed LARGE QUOTE/TICK EVENT ENGINE.

**Engines (DEV)**
- None is net-positive alone.
- MACD and VEI carry small information (ΔAUC +0.006 / +0.004).
- The TD veto adds none.
- The full 8-engine stack yields about 5 trades per 5 years, so it is NOT TESTABLE.

**New defect: D-EXEC-ENTRYBAR**
- **Location:** `nexa_execution.simulate_order`.
- **What happens:** a STOP fill followed by a same-bar SL is priced at `min(sl, bar open)`, an unreachable price. Pessimistic.
- **Size:** 24 % of 8E `stop_at_channel` baseline trades, with 0.60R excess loss.
- **Effect on conclusions:** none change.
- **V2 is not affected:** it uses MARKET and LIMIT only.
- **Not modified:** the file is pinned by V2 and 8E. Human decision needed.

**Other new defects**
- D-DAYLOSS-TRIGGER: 2 % is a halt trigger, not a cap; the realized day can reach about 2.97 %, in the EA as well.
- D-M1-GAPS: a few intraday M1 gaps in DEV.

**Run state**
- Tests: 546 passed; ruff clean.
- History bases: 25,177,852 KB, no download this gate.
- No trading, no deploy. NEXA_Risk unchanged.

**Next human decisions**
1. D-EXEC-ENTRYBAR fix route (8E harness only vs `nexa_execution` + re-freeze).
2. Authorize 8E VAL + pinned selection, or close 8E.
3. NAS100 history.
4. The 2 % cap semantics.
5. Still open: S11, D-TZ, B-EXPOSURE-CAP, the stale deployed build.

## LATEST: 2026-09-27 session 3, Pepperstone (supersedes the status tables below where they conflict)

Full report: `research/reports/pepperstone/PEPPERSTONE_FINAL_AUDIT.md` (sections A–T).
Promotion state: **RESEARCH_ONLY**. No model. No demonstrated edge.

- Broker: Pepperstone-Demo 61603218, DEMO, $50k, 1:200, read-only. Symbols map exactly (no suffix): no adapter needed.
- Data: D1 2000→2026 for core + 91 FX pairs; M1 via the API is capped at the last 99,998 bars (maxbars); tester M1 goes deeper; **real ticks only from 2026-08-28**; commission $3.50/lot/side.
- Tester: 48/48 NEXA quarter-chunks + 49/49 bar exports verified (2024-01 → 2026-09, 4 symbols, 250 ms delay). **3,927,131 decisions, 1 trade.**
- **Top blocker B-EXPOSURE-CAP:** `InpMaxSameCurrencyNet=2` min-lots = 0.02 lots per currency blocks nearly every trade above ~$1.3k equity. Hard risk parameter, so it was NOT changed. Human decision needed.
- Parity: 3 oracle defects fixed (iATR=SMA, HTF look-ahead, volState window). Remaining: the liquidity state machine differs on 0.2–0.85% of 112,688 real-tick rows; the contract tolerance is below journal precision.
- EA journal fixes (tester-verified): FOMC veto rows anchored to the closed bar; `risk_dist` not journaled without a stop. NEXA_Risk / schema / f00–f47 unchanged.
- Factory (Pepperstone H1 ×5, frozen protocol): no candidate; 0/25 survive BH-FDR; gold trend = drift.
- Tests: 336 passed, ruff clean.

### 2026-09-27 (late): PHASE 2 infrastructure COMPLETE, stopped before Phase 3
- Report: `research/reports/INFRASTRUCTURE_READINESS_PHASE2.md`.
- New modules: `nexa_time` (Pepperstone clock = NY+7, US DST; IANA-verified), `nexa_execution` (deterministic fills), `nexa_calendar` (MT5 calendar; export-offset time basis), `nexa_m1_history` (canonical M1), `nexa_registry` + `protocols_phase2` (frozen protocols, hash-chained ledger).
- New MQL5: `NEXA_CalendarExport.mq5` (read-only; 0/0). `NEXA_BarExport` unchanged since the last session. No change to EA/risk/schema.
- Campaign `PHASE3_SIX_FAMILIES_V1` FROZEN (sha 9b5b78738950d3b8): 807 active trials + 108 legacy = 915 DSR trials; 18 primary tests; F4 BLOCKED. Evaluation refused until the human opens it.
- Tests: 382 passed, ruff clean. No broker download (history base 24,891,040 KB unchanged).

### 2026-09-27 (later): research design for six new factory families, PHASE 1 ONLY
- `research/reports/RESEARCH_DESIGN_SIX_FAMILIES.md`: design only, no strategy code, no results.
- Ranking (by testability/data/execution/identifiability/overfit resistance, NOT profitability): FVG retracement → Asian MR → XAU session breakout → tick microstructure → macro events → cross-feed latency (blocked: no second synchronous tick feed).
- Data facts measured: Pepperstone ticks are quote-only (volume=0, last=0, no aggressor flags), 21 days; DOM available=false (weekend, recheck); MT5 calendar not yet exported (the bridge calendar is Forex Factory, not MT5).
- Tests: 336 passed, ruff clean; NEXA_Risk == baseline.

### 2026-09-29: pre-live engineering safety audit (V2 untouched, not opened)
- Report: `research/reports/NEXA_PRELIVE_SAFETY_AUDIT_2026-09-29.md`.
- **Fixed (10):**
  - restart guard;
  - retry re-validation (risk never above sized);
  - cross-instance portfolio lock + atomic daily slot;
  - breached-stop recovery;
  - breakeven distance/freeze/throttle;
  - time-exit de-dup;
  - news fail-closed;
  - unique row_id;
  - close-by handling;
  - whole-position R.
- **Hashes:** EA `d65090cc…`, Intelligence `18e3b30c…`, new `NEXA_Safety.mqh` `843fc606…`; `NEXA_Risk` unchanged (`7fd5692a…`).
- **Verification:**
  - compile 0/0;
  - tester primitives 29/29;
  - pre/post DNA identical except the intended R fix;
  - 12/12 mutations detected;
  - 502 tests pass;
  - V2 attacks 70/70.
- **Needs human decision:**
  - S11 (`NEXA_Risk` exposure netting skips unreadable positions: fail-open);
  - D-TZ;
  - frozen USD-composite feature;
  - deviation;
  - deployment (the terminal still runs the 2026-09-27 build).

### 2026-09-29: HUMAN-APPROVED correlation-cap safety fix in NEXA_Risk.mqh (V2 untouched)
- Report: `research/reports/NEXA_RISK_CORRELATION_CAP_SAFETY_FIX.md`.
- `NEXA_Risk.mqh`: `e706d453…` → **`7fd5692a2bd3aec7…`**. The diff is confined to the correlation block. The cap is now fail-closed and time-aligned, with states OK/BLOCK/INSUFFICIENT_DATA; INSUFFICIENT_DATA blocks; ≥ 80 % aligned pairs required; 0.75/100 unchanged.
- **Compile:** MetaEditor 0 errors / 0 warnings (`NEXA_EA`, `NEXA_CorrCapTest`).
- **Tests:** the compiled MQL5 core equals the Python oracle on 18 fixtures (Strategy Tester, no orders). 490 tests pass; ruff clean.
- **V2:** not pinned, so no re-freeze. Anchor `6090be68…` still FROZEN at seq 6 `bbd9a28e…`; 0 results.
- **Not done:** the new EA build is NOT deployed. The tester launches added about 1.7 MB of tester cache to the history base.

### 2026-09-29 (hold): read-only addendum on the two HIGH issues (V2 untouched, no new freeze)
- `research/reports/V2_FINAL_AUDIT_ADDENDUM_HIGH_ISSUES.md` (non-pinned).
- **Correlation cap (live-trading safety defect).** It fails open when history is absent, and when the shift-aligned windows are misaligned. XAU vs FX windows are misaligned in 11 % of M1 windows, 40 % of M5 and 100 % at M15 and above. The fix is a fail-closed, time-aligned tri-state check, awaiting human approval to edit `NEXA_Risk.mqh`.
- **F1 first print.** No look-ahead in feature values. Inclusion is conditioned on the next release, which is non-causal but price-independent: 6/3,562 DEV/VAL candidates excluded (shutdown ordering artifacts), and 1,487 revised releases still included.
- **State.** V2 is FROZEN (anchor `6090be68…`, head seq 6 `bbd9a28e…`); 0 results; trading and exec false. Human opening approval is NOT yet granted.

### 2026-09-29: FINAL PRE-OPENING AUDIT + FREEZE (V2 FROZEN / NOT OPENED / NOT EVALUATED)
- **Authoritative anchor `6090be68184af7643f82b680d144a1b9e1622b3bbceebfb872729b97b9d9324c`; published head seq 6 `bbd9a28ed6bc7e0b20f3fca9f9ba1fe437f4bd39dc9c1e99ed73fb7505be5b2b`.**
  - Superseded pre-opening freezes, never opened: `27b3463f`, `f2dc4ffb`, `faac4c86`, `88b7688b`.
  - Reports: `research/reports/V2_FINAL_PRE_OPENING_AUDIT.md`, `V2_OPENING_CHECKLIST.md`, `PHASE3_V2_MANIFEST.md`.
- **Added (all pinned):**
  - certified builders `nexa_v2_features` (F1, F2 + null, F3, F5, calendar baselines);
  - trial layer `nexa_v2_trials`;
  - evaluation driver `nexa_v2_runner`;
  - execution hardening;
  - sensitive-cut certification: the old fractional cuts had passed 3 leaky builders;
  - R1 control: compare-and-swap against the externally published ledger head.
- **Unchanged:** protocols, periods, universe (1,632 / DSR 1,740 / 17 primary), and F4/F6 BLOCKED.
- **Adversarial:** 70/70 rejected, 0 defects; real registry and witness byte-identical.
- **Tests:** 446 passed, ruff clean.
- **Invariants:** NEXA_Risk, schema, f00–f47 and the baseline unchanged; trading flags false; no MQL5 change; no broker download.
- **New finding M1 (HIGH):** the `NEXA_Risk.mqh` correlation cap fails open on unsynchronised or missing history (the file is frozen, so this is a human decision).
- **Prior art:** `NEXA_COMMERCIAL_EA_PRIOR_ART_AUDIT_2026.md` and `NEXA_FUTURE_RESEARCH_BACKLOG.md`. V2 is unchanged by them.
- **Non-pinned OOS date clarification:** `V2_OOS_DATE_CLARIFICATION_NOTE.md`.
- **Human actions:**
  1. publish the anchor and seq-6 head off-machine (no Git remote exists);
  2. an explicit OPEN V2 approval;
  3. decisions on B-EXPOSURE-CAP, D-TZ and M1.

### 2026-09-28: PHASE3_SIX_FAMILIES_V2 FROZEN (V1 permanently REJECTED), NOT opened
- Manifest: `research/reports/PHASE3_V2_MANIFEST.md`. **Anchor `f2dc4ffb4aafe02254547811f5430f2e3b202e2ede59589282dfbe7b142b105e`.** Ledger head seq0 `c0bf4935…d451`. Witness: `~/.nexa_registry_witness/`.
- OOS is PROSPECTIVE [2027-01-04Z, 2028-01-03Z). EXCLUDED [2025-01-01Z, 2027-01-04Z). See `OOS_DETERMINATION_V2.md`.
- 1,632 active + 108 legacy = 1,740 DSR trials; 17 primary tests; F4 and F6 BLOCKED.
- New: `nexa_registry2`, `nexa_causality`, `protocols_phase3_v2`, `build_calendar_v2`, `freeze_phase3_v2`, calendar `canonical_v2`.
- Adversarial: 50/51 fail closed. Residual R1: coordinated rewrite of ledger + witness. The first freeze `27b3463f` was superseded (never opened) after 3 defects were fixed.
- Tests: 399 passed, ruff clean. NEXA_Risk unchanged.

### Next actions
1. Human: decide B-EXPOSURE-CAP (re-denominate the cap, or authorise a design-scale-deposit tester campaign, labelled).
2. Debug the liquidity-machine parity residual on one mismatching episode, bar by bar.
3. Human: parity tolerance vs journal precision; D-TZ; schema v1.1; disk (6.7 GB free after the full-history download).

---

Last updated: 2026-09-27 06:15 (server-local GMT+8), Claude Code session 2.
Promotion state: **RESEARCH_ONLY**. No trained model. No demonstrated edge.

## Gate status

| Gate | Status | Evidence |
|---|---|---|
| 1 MQL5 build | **PASS** | Real MetaEditor compile (`tools/compile_mql5.sh`, logs in `build/`). NEXA_EA, TrainingExport, SpecSnapshot, TickLogger, DealAudit, BarExport: all 0 errors / 0 warnings |
| 2 Architecture / schema | PASS (audited) | Hashes match; `test_nexa_mql5_invariants.py`; decision-contract audit `research/reports/DECISION_CONTRACT_AUDIT.md`. Schema v1.1 **proposed, not implemented** (needs approval) |
| 3 Market data | PARTIAL | Tester bar tap `NEXA_BarExport` gave 30,224 real GBPUSD M1 bars with per-bar spread (`data/tester/`). Local broker history starts 2024-01-02 |
| 4 Parity | **NOT ESTABLISHED** | Oracle ran on real DNA and correctly failed closed: no reconstructable row (no history before the first decision) |
| 5 Labels | BLOCKED | No real trades yet |
| 6 External data | PARTIAL | Alpha Vantage GBPUSD daily saved (`data/external/`, sha `a4ac78fc`); matches tester D1 closes (median 0.6 pip). QuantConnect connector **invalidated** |
| 7 Trade DNA | **BLOCKED (human)** | 1 real DECISION row (`data/tester/NEXA_TradeDNA_GBPUSD_run8151dbc020fd_partial.csv`); run then blocked on history sync, because the demo login is invalid |
| 8 Quant validation | Code PASS / data BLOCKED | `nexa_stats.py` (14 tests) |
| 9 Meta-label / ML | Code PASS / data BLOCKED | `nexa_model.py` (15 tests): veto-only policy, forward-only calibration, gate, append-only registry |
| 10 Strategy Factory | PASS (ran) | XAUUSD H1: **no candidate** (`research/reports/FACTORY_XAUUSD_H1.md`) |
| 11 Portfolio / risk / exec | Not re-validated | Needs multi-symbol Trade DNA |
| 12 WF / OOS / robustness | Code PASS; applied in the factory | `nexa_robust.py` (11 tests); walk-forward, one-shot holdout, BH-FDR, DSR, PBO |
| 13 Final integration | Nothing to integrate | No component has passed validation |

## This session's changes

- **MQL5** (backup `NEXA_PRE_GATES_BACKUP_20260927-001905/`):
  - `NEXA_FOMC.mqh`: official 2024/2025 schedules plus 2027 (tentative); ends 2027-12-08.
  - `NEXA_SpecSnapshot.mq5`: checked return values.
  - `NEXA_BarExport.mq5`: new, tester-only, no orders.
  - All were deployed to the terminal's `Experts/Advisors`.
- **Research:** `nexa_stats.py`, `nexa_robust.py`, `nexa_factory.py`, `nexa_factory_run.py`, `nexa_model.py`, plus tests. `README.md` status table corrected.
- **Tools:** `tools/compile_mql5.sh` (real headless MetaEditor), `tools/run_dna_pipeline.sh` (Stage 2 → Gate 8).
- **Manifest:** `NEXA_BUILD_MANIFEST.json` gains a `sessions[]` record (existing content untouched).
- **Risk:** `NEXA_Risk.mqh` is **unchanged** (`e706d453d346100f`). Tests: **321 passed**, ruff clean.

## Key findings

1. **Tester root cause:** `'5055943373': authorization on MetaQuotes-Demo failed (Invalid account)`. Every history sync then waits about 8.5 minutes. A GBPUSD-only EA finishes the month in 0.35 s after one sync. NEXA reads EURUSD, USDJPY and XAUUSD too (USD composite, correlation cap), produced 1 row after about 25 minutes, then stalled for 12+ minutes on the next bar.
2. **Spread veto on real broker bars** (GBPUSD Jan 2024, M1, iATR(14) definition):
   - Server 09–18: passes 99.9% of bars.
   - Server 00–08: blocks 96.9%.
   - Server 19–23: blocks 72.8%.
   - Rollover median spread is 46 points against 1 point in session.
3. **Factory (XAUUSD H1, 18 configs, protocol `b1d8203b159fa2ef` frozen before running):** no family passes.
   - TrendLock synthesis: +0.086R walk-forward OOS, CI includes 0, DSR 0.29.
   - Its holdout +0.160R is indistinguishable from coin-flip entries (+0.151R), so it is drift, not skill.
   - Mean reversion and Camarilla fading are reliably negative.
4. **Agent-Lab review:**
   - `prompts/nexa_master_spec.md` is a governance spec. Its risk values match NEXA_Risk; Astra/Opus are *development* agents, not EA components.
   - `astra_gap_audit.md` is a prompt only.
   - The debates hold no usable content: one truncated Astra output proposes L6, which is already built. `evidence/` and `patches/` are empty.
   - `TrendLock_Quantum_Synthesis.mq5` is the only strategy artifact. It now compiles 0/0 and was tested as a hypothesis (finding 3).
   - Strategy families from the research master (§11 Camarilla, §12 quant, §20 factory) were converted into factory specs.

## New defects

- D-DEMO-EXPIRED: MT5 demo login invalid. **Blocks Gate 7.**
- D-HISTORY-START: local broker history starts 2024-01-02, so features and parity have no warm-up. Resolves with a valid login.
- D-XAU-TZLABEL: the Axiory ladder files label server-time values as `+0000 UTC`. `nexa_factory.load_bars` strips the label.
- D-QC-CONNECTOR: QuantConnect connector invalidated.
- D-BRIDGE-COMPILE: `compile_ea` from meta-trader-mcp can't compile multi-file EAs. Use `tools/compile_mql5.sh`.

## Next actions, in order

1. **Human:** log MT5 into a valid demo account (MetaQuotes-Demo or another broker), let history sync for EURUSD/GBPUSD/USDJPY/XAUUSD, then close MT5.
2. Rerun GBPUSD M1 Jan 2024 via `trigger_backtest` (NEXA_EA and NEXA_BarExport, same settings). Expect DNA in Common\Files.
3. `tools/run_dna_pipeline.sh <dna> GBPUSD <M1> <D1> research/runs/<id>`, then read STATUS, parity and validate.
4. Widen to multi-month and multi-symbol runs for enough episodes (validate needs ≥200 resolved), then Gate 8 stats and Gate 9 training.
5. Human decisions still open: D-TZ, C1/C2/C3 label policies, schema v1.1 approval, the 2027 FOMC dates once final.
