# NEXA MASTER PROJECT STATUS

**Audit date:** 2026-10-02. **Type:** read-only audit of the actual files. **Updated:** 2026-10-02 after the human-approved 8E validation, selection and formal close; 2026-10-03 for the D45 position-management fix and the D46 stale-bar guard (engineering only, not deployed), for the B-EXPOSURE-CAP decision from the cap-neutral campaign, and for feature parity (B-PARITY-LIQ / EDGE / TOL).
- **The audit itself implemented, modified, deleted, froze, unfroze, deployed and traded nothing.** The only later change is the human-approved 8E run and close (section 1), recorded in `registry_8e` (plus its witness file in `~/.nexa_registry_witness/`), with outputs in `runs_8e/` (`selection.json`, analysis outputs, 12 stress tables in the cache).
- The only writes are this file, `NEXA_MASTER_ROADMAP.md` and `NEXA_MASTER_PROJECT_STATUS.json` in `research/`.

**Where things live:**
- **NEXA working copy:** `filesnexa/NEXA/` (MQL5 sources, Python research tier, registries, reports). Paths below are relative to it.
- **Agent-Lab:** paths marked `AL:` are relative to `NEXA-Agent-Lab/` (research corpus, knowledge base, agent orchestrator).

**Status legend:** 🟢 COMPLETE · 🔵 IN PROGRESS · 🟡 PENDING · 🔴 BLOCKED · ⚫ FROZEN · ❌ REJECTED/FAILED · ⚪ NOT FOUND (no evidence in the repository).

---

## 1. Executive status

| Item | Value |
|---|---|
| **Promotion state** | **RESEARCH_ONLY.** No trained model. No demonstrated edge (`NEXA_BUILD_MANIFEST.json`, `PROGRESS.md`). |
| **Engineering** | Two-tier system built and tested. **628 tests pass, ruff clean (2026-10-04).** EA compiles 0/0. Pre-live safety fixes S1–S10 done. **D45 fixed in source 2026-10-03:** the 1.5R partial close and 48-bar time exit now work after breakeven (verified; not deployed). **D46 fixed in source 2026-10-03:** a bar evaluated more than 6 h after it closed (Friday's last bar at Monday open) can no longer open a trade (verified; not deployed). **D-TZ fixed in source 2026-10-03:** the EA clock now follows US DST, so sessions, the Asia range and the LATE veto run on real GMT (verified; not deployed). **C4 fixed in source 2026-10-03:** the 2 % daily loss is a pre-trade budget, not only a halt trigger (verified; not deployed). **S13 fixed in source 2026-10-04:** the USD composite (f29) reads the basket by time and is now parity-compared (44 features); trading unchanged (verified; not deployed). |
| **Risk Engine** | `NEXA_Risk.mqh` FROZEN at the approved hash `a43d8328…` (2026-10-03). Correlation cap (2026-09-29) and currency-exposure cap (**S11**) fail closed; the 2 % daily loss is now a **pre-trade budget** (**C4**, 2026-10-03), with the halt trigger kept; hard limits unchanged. The exposure cap (B-EXPOSURE-CAP) was decided 2026-10-03: unchanged. |
| **Main finding** | **NEXA's rule set has no edge.** The cap-neutral tester campaign (2026-10-03, 1,902 trades) returned Gate 8 **NEGATIVE_EXPECTANCY**: −0.318R per trade, 95 % CI [−0.384, −0.250]; negative even before commission. **B-EXPOSURE-CAP decided:** the production cap stays unchanged (the 0.02-lot cap had allowed 1 trade in 3,927,131 decisions; lifting it would only let a losing rule set trade larger). |
| **V2 research** | FROZEN, not opened, 0 results. Anchor `6090be68…`, head seq 6 `bbd9a28e…` (verified today). Opening needs explicit human "OPEN V2". Selection deadline 2027-01-04; OOS scored once after 2028-01-03. |
| **8E research** | **CLOSED: REJECTED (terminal) at seq 2170 `9f7249a2…`, 2026-10-02.** Human-approved Route A: 2,160 single-query VAL results, 6 pinned selections sealed, analysis run, then formal close. **PRELIMINARY VALIDATION / SEEN DATA:** 0/11 DEV-positive trials replicated; no pick passes DSR (max 0.076 vs 0.95); both XAU picks untradeable at $200; +24.5 %/day target-hit rate 0. **No edge found.** D-EXEC-ENTRYBAR disclosed, not corrected; no pick uses `stop_at_channel`. |
| **Knowledge** | Corpus (39 files / 38 works), knowledge base, math KB, stat KB and 40 hypotheses: COMPLETE. **The "205-indicator research library" was NOT FOUND** anywhere in the repository or the usual user folders. |
| **Deployment** | The terminal runs a **stale 2026-09-27 build**, which predates the correlation fix and safety audit. Not deployed by design. |

**Item counts (53 tracked items):**
- 🟢 COMPLETE: 26
- 🔵 IN PROGRESS: 0
- 🟡 PENDING: 9
- 🔴 BLOCKED: 6
- ⚫ FROZEN: 4
- ❌ REJECTED: 7
- ⚪ NOT FOUND: 1

### Verification performed during this audit (read-only)

| Check | Result |
|---|---|
| `pytest -q` in `research/` (no cache writes) | **546 passed**, 1 warning, 59 s (audit); **587 passed** after the D45 fix; **590 passed** after the B-PARITY-LIQ oracle fix; **591 passed** after the B-PARITY-EDGE oracle fix; **596 passed** after the B-PARITY-TOL contract; **600 passed** after the D46 stale-bar guard; **606 passed** after the S11 fix; **614 passed** after the D-TZ fix; **620 passed** after the C4 change; **628 passed** after the S13 change (2026-10-04) |
| `ruff check .` | All checks passed |
| sha256 `NEXA_Risk.mqh` | `7fd5692a…` = approved at the audit; `1f684cde…` after the human-approved S11 fix; now `a43d8328…` after the human-approved C4 change (2026-10-03) |
| sha256 `NEXA_EA.mq5` | `d65090cc…` = post-audit; `10b62623…` after the D45 fix; `3edcec11…` after the D46 stale-bar guard; now `4ef7de88…` after the C4 call (2026-10-03) |
| sha256 `NEXA_Intelligence.mqh` | `18e3b30c…` = post-audit; now `81641c4e…` after the human-approved S13 change (2026-10-04) |
| sha256 `NEXA_Safety.mqh` | `843fc606…` = post-audit |
| sha256 schema | `c24198b0…` = v1.0 |
| `registry_v2/ledger.jsonl` | 7 events, last = BUILDER_CERTIFIED seq 6 `bbd9a28e…`; no EVALUATION_OPENED |
| `registry_8e/ledger.jsonl` | At audit time: 4 events, last = EVALUATION_OPENED seq 3 `1e84a047…`, no results. **Now (re-verified 2026-10-02):** 2,171 events; 2,160 VAL results (seq 4–2163), 6 OOS_SELECTED (seq 2164–2169), CAMPAIGN_REJECTED seq 2170 `9f7249a2…` (terminal) |
| `registry/ledger.jsonl` (V1) | seq 8 CAMPAIGN_REJECTED |
| Witness files `~/.nexa_registry_witness/` | 7 present (V2, 8E, superseded, accidental) |
| Deployed terminal EA | `NEXA_EA.ex5` 2026-09-27 19:38; deployed `NEXA_Risk.mqh` 11,846 B vs repository 17,273 B ⇒ **stale** |
| MT5 terminal | not running |
| Disk free | 7.2 GiB (97 % used) |

---

## 2. Completed work

| ID | Area | Component | Status | Evidence | Next action | Dependency |
|---|---|---|---|---|---|---|
| A1 | Architecture | Core two-tier architecture (MQL5 live tier ⇄ Python research tier; Trade DNA schema v1.0 contract) | 🟢 COMPLETE | research/README.md (tier contract); research/reports/DECISION_CONTRACT_AUDIT.md; nexa_schema_v1.json sha c24198b0…; NEXA_BUILD_MANIFEST.json | Decide schema v1.1 (decision-contract fields) — PROPOSED, not implemented | Human approval (DECISION_CONTRACT_AUDIT.md §3) |
| B1 | MQL5 EA | NEXA_EA.mq5 source (incl. pre-live safety fixes S1–S10, NEXA_Safety.mqh, D45 position-management fix, D46 stale-bar guard, C4 daily-loss budget call) | 🟢 COMPLETE | NEXA_EA.mq5 sha 4ef7de88… after the C4 daily-loss budget call in ExecuteSignal (2026-10-03, 2 lines; D49). Before: 3edcec11… after the D46 stale-bar guard (2026-10-03: a closed bar evaluated > 6 h after it closed never opens a trade; filesnexa/NEXA/research/engfix/STALEGUARD_REPORT.md: compile 0/0, 12/12 regression runs, 147/147 stale rows flagged, 0 other rows changed; NEXA_DEFECT_MATRIX.md D46). Before: 10b62623… after D45 (preserved at build/pmfix_src/), d65090cc… post-safety-audit (preserved at build/pmfix_pre_source/); NEXA_PositionMgmt.mqh b98a49b5…; NEXA_Safety.mqh 843fc606…; research/reports/NEXA_PRELIVE_SAFETY_AUDIT_2026-09-29.md (compile 0/0, 29/29 primitives, 12/12 mutations); build/NEXA_EA.sha256 | Resolve open items S14–S15 (S11 fixed 2026-10-03 as D47, S12/D-TZ as D48, S13 as D50; see E-section) | Human decisions |
| C2 | Risk Engine | S11 NetCurrencyExposure skips unreadable positions (fail-open) | 🟢 COMPLETE | FIXED 2026-10-03 (human-approved option A, frozen file): an unreadable position or currency spec now blocks with EXPOSURE_POSITION_UNREADABLE / EXPOSURE_CAP_INVALID_SPEC; NEXA_Risk.mqh 1f684cde…; build/NEXA_EA_S11.ex5 7d37dc7d… (compile 0/0, NOT deployed); regression 12/12 runs, 995,400 rows identical, 281 cap blocks identical; correlation harness re-run identical (18/18); filesnexa/NEXA/research/engfix/S11_REPORT.md; NEXA_DEFECT_MATRIX.md D47 (was NEXA_PRELIVE_SAFETY_AUDIT_2026-09-29.md S11) | Ships with the next approved deployment (B2); no separate action | Deployment decision (B2) |
| C3 | Risk Engine | B-EXPOSURE-CAP: InpMaxSameCurrencyNet=2 min-lots (0.02 lots) blocks trading above ~$1.3k | 🟢 COMPLETE | DECIDED. Cause: pepperstone/PEPPERSTONE_FINAL_AUDIT.md §S1/§T (3,927,131 decisions → 1 trade). Human chose option B (2026-10-02): tester-only cap-neutral campaign, cap inert, every other control frozen; 48/48 runs verified (2026-10-03). Result (filesnexa/NEXA/research/capneutral/CAPNEUTRAL_RESEARCH_RESULTS.md): Gate 8 NEGATIVE_EXPECTANCY: net −0.318R/trade, 95 % CI [−0.384, −0.250], n = 1,902; gross −0.072R before commission; every symbol negative (XAUUSD inconclusive). Decision: production cap UNCHANGED — a change is not justified without an edge | Keep the production cap at 2; revisit only if a future, properly validated edge appears (then option C: risk-counted cap, separately approved) | — |
| C4 | Risk Engine | D-DAYLOSS-TRIGGER: 2% is a halt trigger, realised day loss can reach ≈2.97% | 🟢 COMPLETE | FIXED 2026-10-03 (human-approved option B, frozen file): pre-trade budget E_now − OpenRisk(all open positions to their stops) − NewRisk ≥ 0.98 × DailyStartEquity, checked inside the portfolio lock; halt trigger kept; fail-closed on unreadable state; NEXA_Risk.mqh a43d8328…, NEXA_EA.mq5 4ef7de88…, build/NEXA_EA_C4.ex5 149aa0b1… (compile 0/0, NOT deployed); harness 9/9; production-input regression 12/12 byte-identical (gate never bound at $200); research-config pairs 34/34 refusals justified, days beyond −2 % 5 → 2, worst day −2.42 % → −2.01 % (residual = stop slippage); filesnexa/NEXA/research/engfix/C4_REPORT.md; NEXA_DEFECT_MATRIX.md D49 (was research/reports/NEXA_24_5_TRUTH_TABLE.md 2% row) | Ships with the next approved deployment (B2); no separate action | Deployment decision (B2) |
| D1 | Intelligence Engine | NEXA_Intelligence.mqh: ONNX seam, AI veto-only, fail-closed, news fail-closed (S7) | 🟢 COMPLETE | NEXA_Intelligence.mqh sha 81641c4e… after S13 (2026-10-04: UsdCompositeDirection reads the basket by time; D50; was 18e3b30c… post-audit, copy build/s13_pre_source/); NEXA_ARCHITECTURE_GAP_AUDIT_2026.md (ML inference / ONNX rows) | — | — |
| E1 | Research Engine | Python research tier (ingest, parity, labels, validate, stats, robust, factory, model, time, calendar, execution, registry, causality) | 🟢 COMPLETE | research/*.py; 628 tests passed + ruff clean (2026-10-04, after the S13 change; 620 after C4; 614 after D-TZ; 606 after S11; 600 after D46; 596 after B-PARITY-TOL; 591 after B-PARITY-EDGE; 590 after B-PARITY-LIQ; 587 after D45; 546 at the 2026-10-02 audit) | — | — |
| E2 | Execution Engine | Live execution in EA (async, in-flight guard, retry re-validation, breached-stop recovery) | 🟢 COMPLETE | NEXA_PRELIVE_SAFETY_AUDIT_2026-09-29.md S1–S10 | Optional: OrderCheck (M5), OnTester summary (M3) | Engineering (unblocked) |
| E5 | Execution Engine | Position management D45 (D-PARTIAL-AFTER-BE): 1.5R partial close and 48-bar time exit were unreachable after breakeven | 🟢 COMPLETE | Fixed in source 2026-10-03: R vs the original initial risk RiskDist_<posId>; partial exactly once (deal history + pending close order + in-flight window); NEXA_PositionMgmt.mqh. Compile 0/0; harness 47/47; mutants 6/6 killed; pre/post regression 24 tester runs at production inputs (partials 0 → 52, sends = executions, 24/24 reconcile); filesnexa/NEXA/research/engfix/ENGINEERING_REPORT_D45.md; NEXA_DEFECT_MATRIX.md D45 | Ships with the next approved deployment (B2); no separate action | Deployment decision (B2) |
| F1 | Trade DNA | Schema v1.0 journaling + ingest; real Pepperstone DNA (48 files, 3,927,134 rows, 0 ingest errors) | 🟢 COMPLETE | PEPPERSTONE_FINAL_AUDIT.md §L; nexa_ingest.py; PEPPERSTONE_DNA_AUDIT.json | — | — |
| F3 | Trade DNA / Parity | Feature parity MQL5 ⇄ Python oracle | 🟢 COMPLETE | PEPPERSTONE_FINAL_AUDIT.md §M (3 oracle defects fixed). B-PARITY-LIQ RESOLVED 2026-10-03 (research/reports/pepperstone/B_PARITY_LIQ_ROOT_CAUSE.md): 2 more oracle defects fixed (RC1 weekend Asia carry-over, RC2 last-day PDH/PDL; nexa_parity.py 6c58f6aa…), RC3 accepted as a floating-point tie; window B liqState mismatches 0.51–0.84 % → 0 on all 4 symbols. B-PARITY-EDGE RESOLVED 2026-10-03 (same report): EDGE-1 oracle decision clock after tick gaps fixed (nexa_parity.py 590c977e…; trend/htfAlignment → 0 on all 4 symbols), EDGE-2 accepted as a floating-point tie (1.20 displacement threshold). Window-B categorical mismatches are now accepted ties only. CONTRACT PASS 2026-10-03 under B-PARITY-TOL option A (F4): all 4 symbols, 112,688 rows, 0 mismatches, 47 accepted ties (research/reports/pepperstone/B_PARITY_TOL_VERIFY_WINDOW_B.json f02aa017…; nexa_parity.py a4bf9f93…). Scope: window B only (the only real-tick full-parity window). Re-run 2026-10-03 after D-TZ (DST-aware EA clock + oracle mirror nexa_parity.py 728c4631…): PASS on all 4 symbols, 0 mismatches, 47/47 ties matched (research/reports/pepperstone/B_PARITY_DTZ_VERIFY_WINDOW_B.json 58952feb…); the stored report still shows the pre-D-TZ PASS. Re-run 2026-10-04 after S13 (f29 time-aligned and now COMPARED, nexa_parity.py d938a078…): PASS on all 4 symbols with 44 features compared (was 43), f29 0 mismatches, 47/47 ties (research/reports/pepperstone/B_PARITY_S13_VERIFY_WINDOW_B.json 39cbd88e…); exempt now only obiProxy, cvdProxy, liqOrigin, newsRiskActive | Stored window-B reports replaced 2026-10-03 (human-approved): research/reports/pepperstone/PEPPERSTONE_PARITY_FULL_B.json = the PASS result (f02aa017…, provenance file alongside); pre-fix FAIL reports kept as SUPERSEDED_*_pre_parity_fixes_2026-10-03.*. Next: review new ties before any new window is added to the register | — |
| F4 | Trade DNA / Parity | B-PARITY-TOL: contract tolerance (1e-9) tighter than journal precision | 🟢 COMPLETE | PEPPERSTONE_FINAL_AUDIT.md §S3; also holds the accepted window-B floating-point ties (2026-10-03, research/reports/pepperstone/B_PARITY_LIQ_ROOT_CAUSE.md): RC3 18 GBPUSD rows (exact 2.5-ATR tie) and EDGE-2 8 rows + 3 dependent MSS rows (exact 1.20 displacement tie). DECIDED 2026-10-03 (human, option A): continuous abs ≤ 0.5e-6 + |mql5|·2⁻²³ (journal 6-decimal + float32 quantisation) added to the 1e-9 / 1e-6 rule; categorical exact except the reviewed register research/parity_accepted_ties.json (47 entries, e92a8866…; exact symbol/bar/feature/values match only). README_PARITY.md §Tolerance updated | — | — |
| G1 | Strategy Factory | Frozen-protocol factory (Axiory XAUUSD H1; Pepperstone H1 ×5) | 🟢 COMPLETE | nexa_factory*.py; reports/FACTORY_XAUUSD_H1.md; pepperstone/FACTORY_PEPPERSTONE_H1.md | — | — |
| H1 | Learning / validation | Gate 8 stats, Gate 12 robust (BH-FDR, PSR/DSR, PBO, WF), Gate 9 meta-label code | 🟢 COMPLETE | nexa_stats.py, nexa_robust.py, nexa_model.py + tests (in the 546) | — | — |
| I1 | Data infrastructure | Pepperstone M1 2017-06→2026-09 (5 symbols), D1 2000→2026 (core + 91 FX), MT5 calendar export, nexa_time (NY+7, US DST), canonical M1 | 🟢 COMPLETE | data/pepperstone (4.4 GB); INFRASTRUCTURE_READINESS_PHASE2.md; TIME_CONVENTION_EVIDENCE.json; NEXA_8_ENGINE_SPECIFICATION.md §0 | — | — |
| J1 | MT5 / Pepperstone | Pepperstone-Demo 61603218 read-only integration; compile via tools/compile_mql5.sh; tester batch + verify | 🟢 COMPLETE | PEPPERSTONE_FINAL_AUDIT.md §A–§G; tools/*.sh; research/nexa_tester_verify.py; 48/48 chunks verified | Known: ~25% random tester deaths (B-TERMINAL), 8 GB RAM, 7.2 GiB disk free | — |
| J2 | MCP | meta-trader-mcp (read-only data/market access) | 🟢 COMPLETE | Used read-only throughout; PROGRESS.md D-BRIDGE-COMPILE: MCP compile_ea cannot compile multi-file EAs (use tools/compile_mql5.sh); no MCP code in repo | Keep read-only; never enable trading tools | — |
| M2 | Capital Velocity | Capital-velocity simulator + exact feasibility math (research only) | 🟢 COMPLETE | NEXA_CAPITAL_VELOCITY_DESIGN.md; nexa_8e_capital.py, nexa_8e_feasibility.py; test_nexa_capital_velocity.py | — | — |
| N1 | Research corpus | 39 PDFs (38 distinct works) fully studied | 🟢 COMPLETE | AL:research/knowledge/_PROCESSING_LOG.md (39 DONE); AL:research/knowledge/CORPUS_MANIFEST.json | — | — |
| N2 | Knowledge base | Master KB, source map, evidence map, contradictions, failed ideas, knowledge graph | 🟢 COMPLETE | AL:research/knowledge/NEXA_RESEARCH_KNOWLEDGE_BASE.md (+ 10 files, 39 source notes) | — | — |
| N4 | Knowledge base | Mathematical knowledge base | 🟢 COMPLETE | AL:research/knowledge/MATHEMATICAL_KNOWLEDGE_BASE.md (§A–§M) | — | — |
| N5 | Knowledge base | Statistical knowledge base | 🟢 COMPLETE | AL:research/knowledge/STATISTICAL_KNOWLEDGE_BASE.md (L1–L15) | — | — |
| O1 | Testing infrastructure | pytest suite + ruff + MQL5 invariants/safety tests + V2 adversarial suite (70/70) + tester verify | 🟢 COMPLETE | 628 passed, ruff clean (2026-10-04, incl. 9 D45 tests, 9 parity-oracle tests from B-PARITY-LIQ/EDGE/TOL, 4 D46 tests, 6 S11 tests, 8 D-TZ tests, 6 C4 tests and 8 S13 tests; 587 after D45; 546 at the 2026-10-02 audit); test_nexa_mql5_invariants.py; test_nexa_position_mgmt_fix.py; test_nexa_stale_bar_guard.py; test_nexa_risk_s11_exposure.py; test_nexa_dtz_clock.py; test_nexa_risk_c4_budget.py; test_nexa_s13_usd_composite.py; test_nexa_mql5_safety.py; reports/adversarial_v2_final | Note: safety/parity tests pin tester evidence that goes stale if MQL5 sources change | — |
| Q1 | Engineering safety | D-TZ fixed InpGMTOffset=2 (wrong during US DST) | 🟢 COMPLETE | FIXED 2026-10-03 (human-approved option A): NEXA_Common.mqh bbf22ee9… adds +1 h inside US DST (same explicit rule as nexa_time.py; InpGMTOffset = standard-time offset; no input added); oracle mirror nexa_parity.py 728c4631…; build/NEXA_EA_DTZ.ex5 53439394… (compile 0/0, NOT deployed); compiled clock = nexa_time on 271,690/271,690 hours 2000–2030; 980,197 journalled session tags = true clock (0 mismatches); window-B parity PASS on all 4 symbols; filesnexa/NEXA/research/engfix/DTZ_REPORT.md; NEXA_DEFECT_MATRIX.md D48 (was NEXA_PRELIVE_SAFETY_AUDIT S12). Changes frozen feature VALUES in US-DST months: earlier NEXA evidence (Gate 8, D45/D46/S11 regressions, stored parity report) used the old fixed clock | Ships with the next approved deployment (B2); no separate action | Deployment decision (B2) |
| Q2 | Engineering safety | S13 UsdComposite reads other symbols by shift (no time alignment) | 🟢 COMPLETE | FIXED 2026-10-04 (human-approved option B): UsdCompositeDirection reads each basket symbol by TIME (CopyRates; last bar at or before the decision bar and 10 bars earlier; stale / degenerate symbols skipped); vote rule unchanged; NEXA_Intelligence.mqh 81641c4e…; build/NEXA_EA_S13.ex5 dec57013… (compile 0/0, NOT deployed); regression 12/12 windows: 995,081 rows, 0 differ outside f29 (trading identical), f29 changed on 15.05 % of decisions; f29 now parity-COMPARED: window B PASS, 44 features; filesnexa/NEXA/research/engfix/S13_REPORT.md; NEXA_DEFECT_MATRIX.md D50 (was NEXA_PRELIVE_SAFETY_AUDIT S13) | Ships with the next approved deployment (B2); existing journals keep the old positional f29 | Deployment decision (B2) |
| Q4 | Engineering safety | Off-machine publication of V2/8E anchors and heads (R1 residual) | 🟢 COMPLETE | Published 2026-10-02 as the private claude.ai record NEXA Registry Checkpoints (https://claude.ai/artifact/6o1hnw9docUUW48gZ5Wf59, version 1, server-side version history): V2 anchor 6090be68… + full ledger, head seq 6 bbd9a28e…; 8E anchor 6468fdea…, heads seq 3, 2163, 2169, 2170 9f7249a2…; all 19 hashes verified against the ledgers and witness files before publishing. Earlier copy: the 2026-10-02 conversation transcript. Limit: no independent copy of the 8E seq-3 head exists from before 2026-10-01 | Republish the record (same URL) after every new V2 event, and take every future checkpoint from it, never from the local ledger. Optional second independent copy: email to self or signed Git tag | — |

---

## 3. In-progress work

_None at present._

---

## 4. Pending work

| ID | Area | Component | Status | Evidence | Next action | Dependency |
|---|---|---|---|---|---|---|
| A2 | Architecture | Agent-Lab dual-agent orchestrator (Astra/Opus debates: main.py, agents/, prompts/) | 🟡 PENDING | AL:main.py; AL:workspace/nexa/debates (9 runs); AL:workspace/nexa/evidence and patches EMPTY; PROGRESS.md 2026-09-27 'debates hold no usable content' | None required; development-governance tooling only, not an EA component | Human decision whether to keep using it |
| E3 | Execution Engine | S14 fixed deviation 20 points for every symbol | 🟡 PENDING | NEXA_PRELIVE_SAFETY_AUDIT S14 | Decide deviation policy (knowledge base H-DEVIATION-OPT needs fill logs) | Human decision; fill logs |
| E4 | Execution Engine | Execution simulator nexa_execution.py — defect D-EXEC-ENTRYBAR (pessimistic STOP same-bar exit) | 🟡 PENDING | NEXA_8_ENGINE_RESULTS.md §1.1; runs_8e/gate_dev/entry_bar_exit_defect.txt; still pinned by V2. 8E closed 2026-10-02 with the defect disclosed and uncorrected (no 8E re-freeze needed any more) | Fix before any FUTURE campaign that uses STOP entries is frozen (new code path or new pinned module); not time-critical | Human approval; editing nexa_execution.py itself breaks the V2 code pins (V2 behaviour unaffected: MARKET/LIMIT only) |
| F2 | Trade DNA | Labels / resolved episodes at scale (Gate 5/7) | 🟡 PENDING | Production config: 1 trade (PEPPERSTONE_FINAL_AUDIT.md §N–§R). Cap-neutral campaign 2026-10-03: 1,902 resolved trades (research config, implemented EA; data/pepperstone/tester_capneutral/); nexa_labels not run on them | Label them only if a later research phase needs it | Research-phase approval |
| I2 | Data infrastructure | Real tick history | 🟡 PENDING | Only 2026-08-28 → 2026-09-25 (21 days) quote-only ticks (8E spec §0); NEXA_TickLogger.mq5 exists, not running (MT5 not running) | Start post-freeze tick logging (needs terminal running, read-only) | Human approval to run terminal logger; disk space (7.2 GiB free) |
| N3 | Knowledge base | 205-indicator research library | ⚪ NOT FOUND | No file in AL: or filesnexa/NEXA, nor in ~/Documents, ~/Desktop, ~/Downloads, references a 205-indicator library (searched 2026-10-02) | User to supply location; until then it cannot be counted | User input |
| N6 | Research hypotheses | 40 hypotheses (13 fields each) — documented, none tested | 🟡 PENDING | AL:research/knowledge/RESEARCH_HYPOTHESIS_BACKLOG.md; filesnexa/NEXA/research/reports/NEXA_FUTURE_RESEARCH_BACKLOG.md (B1–B12) | Approve a research phase; start with method gates + volatility layer | Human approval; new frozen protocols |
| Q3 | Engineering safety | Multi-instance lock contention & requote/freeze-level paths untested in tester | 🟡 PENDING | NEXA_PRELIVE_SAFETY_AUDIT ('Not verifiable in the tester') | Multi-chart demo forward check | Human approval; B2 deployment |
| Q5 | Engineering safety | Documentation drift | 🟡 PENDING | V2_OPENING_CHECKLIST.md §B still expects NEXA_Risk = e706d453 (now a43d8328, approved: correlation fix 2026-09-29 + S11 + C4 2026-10-03); NEXA_BUILD_MANIFEST.json top-level fields dated 2026-09-20 ('No dataset exists') | Update the two NON-pinned docs (checklist is not in the V2 pin set — verified) | Human approval to edit docs |
| Q6 | Engineering safety | D-M1-GAPS (intraday M1 gaps in DEV) | 🟡 PENDING | PROGRESS.md 2026-10-01; runs_8e/m1_gap_audit.txt | Document handling; sensitivity shows no sign change | — |

---

## 5. Blocked work

| ID | Area | Component | Status | Evidence | Next action | Dependency |
|---|---|---|---|---|---|---|
| B2 | MQL5 EA | Deployment of current EA build to MT5 terminal | 🔴 BLOCKED | Terminal MQL5/Experts/Advisors/NEXA_EA.ex5 dated 2026-09-27 19:38 (f0ae9618…) and deployed NEXA_Risk.mqh 11,846 B (pre-fix; repo 17,273 B) — STALE build; S15 in safety audit. The verified current build build/NEXA_EA_S13.ex5 (dec57013…, D45 + D46 + S11 + D-TZ + C4 + S13, compile 0/0) exists and is NOT deployed (earlier builds NEXA_EA_C4.ex5 149aa0b1…, NEXA_EA_DTZ.ex5 53439394…, NEXA_EA_S11.ex5 7d37dc7d…, NEXA_EA_STALE.ex5 fd2fe06e… and NEXA_EA_PMFIX.ex5 28e8d925… are superseded) | Do not deploy until risk/safety decisions are made; then redeploy + multi-chart demo forward check | Human deployment approval (S11 and D-TZ fixed 2026-10-03; B-EXPOSURE-CAP decided 2026-10-03: no change; C4 and S13 fixed 2026-10-03/04; remaining policy item E3 (S14 deviation) is an open decision) |
| D2 | Intelligence Engine | Trained model / ONNX artifact / calibration (seam L1) | 🔴 BLOCKED | research/README.md ('No model trained'); AI_CalibrationId()='NONE'; PEPPERSTONE_FINAL_AUDIT.md §R; cap-neutral campaign 2026-10-03: Gate 8 NEGATIVE_EXPECTANCY: net −0.318R/trade, 95 % CI [−0.384, −0.250], n = 1,902 — a veto-only meta-model has no edge to protect | Not warranted for the current rule set | A rule set with a demonstrated edge (none) |
| I3 | Data infrastructure | NAS100 history | 🔴 BLOCKED | NEXA_24_5_TRUTH_TABLE.md (DATA-LIMITED); registry_8e E8_NAS100 BLOCKED | Decide whether to download NAS100 history | Human data decision (no broad downloads rule) |
| I4 | Data infrastructure | Depth/volume/aggressor data, historical swaps, second synchronous feed | 🔴 BLOCKED | 8E spec §0 (no DOM, no volume, no aggressor); NEXA_FUTURE_RESEARCH_BACKLOG.md B9 (no historical swaps); V2 F4/F6 BLOCKED | None possible at this broker; F4 needs a second broker login | External data / second broker (human) |
| K2 | V2 research | V2 families F4 cross-feed latency, F6 tick quote imbalance | 🔴 BLOCKED | registry_v2/campaign.json (status BLOCKED) | — | Second synchronous feed (F4); measurable order flow (F6) |
| P1 | Production readiness | Promotion state | 🔴 BLOCKED | NEXA_BUILD_MANIFEST.json promotion_state RESEARCH_ONLY; PROGRESS.md 'No model. No demonstrated edge.' | Nothing to promote; requires a validated edge + model + shadow mode + promotion gate | Demonstrated edge (none; cap-neutral Gate 8 NEGATIVE_EXPECTANCY 2026-10-03), D2, safety decisions |

---

## 6. Rejected / failed work

| ID | Area | Component | Status | Evidence | Next action | Dependency |
|---|---|---|---|---|---|---|
| G2 | Strategy Factory | Factory results: 0/25 families pass; TrendLock synthesis = drift; MR & Camarilla negative | ❌ REJECTED | pepperstone/PEPPERSTONE_FINAL_AUDIT.md §O/§Q; PROGRESS.md finding 3 | No re-tuning; new families only via new frozen campaigns | — |
| H2 | Learning / validation | Gate 8/9/11/12 applied to NEXA itself | ❌ REJECTED | Gate 8 run 2026-10-03 on the cap-neutral campaign (filesnexa/NEXA/research/capneutral/CAPNEUTRAL_RESEARCH_RESULTS.md): Gate 8 NEGATIVE_EXPECTANCY: net −0.318R/trade, 95 % CI [−0.384, −0.250], n = 1,902 (PRELIMINARY: not out-of-sample). Gates 9/11/12 not run: there is no edge to filter or validate | No Gate 9/12 work on the current rule set; any new rule set needs its own frozen campaign | — |
| K3 | V2 research | PHASE3_SIX_FAMILIES_V1 | ❌ REJECTED | research/registry/ledger.jsonl seq 8 CAMPAIGN_REJECTED | Never open | — |
| L1 | 8-engine research | RESEARCH_8E_V1 (E8_STACK, E8_THRESH; 2,160 trials): DEV → VAL → pinned selection → formally CLOSED (no edge) | ❌ REJECTED | research/registry_8e ledger (human-approved Route A, 2026-10-02): 2,160 single-query VAL results (seq 4–2163, head d838e2d6…); 6 OOS_SELECTED (seq 2164–2169, head 80eacbd8…); CAMPAIGN_REJECTED seq 2170 9f7249a2… (terminal, re-verified). PRELIMINARY VALIDATION / SEEN DATA: 0/11 DEV-positive trials replicated; 15/1,787 eligible trials with VAL lower bound > 0 (all XAUUSD close_next_open, mostly nested qb_0.995); no pick passes DSR (max 0.076 vs 0.95); both XAU picks untradeable at $200 (below min lot); +24.5 %/day target-hit rate 0. runs_8e/selection.json, selected_analysis.json, stack.csv, info_summary.csv | None: terminal, never reopen. Any follow-up idea (e.g. XAU quote-burst) only as a hypothesis for a NEW, properly frozen campaign | — |
| L2 | 8-engine research | 8E DEV verdicts: Donchian CONTRADICTED; TD veto CONTRADICTED; OFI proxy FAILED; Squeeze/EMA200 UNPROVEN; MACD/VEI PROMISING (information only) | ❌ REJECTED | NEXA_24_5_TRUTH_TABLE.md; NEXA_8_ENGINE_RESULTS.md §2–§3; VAL 2026-10-02: 0/11 DEV-positive trials replicated, every stacked layer net-negative on VAL (runs_8e/stack.csv) | No engine is net-positive alone; full stack ≈5 trades/5 yrs (NOT TESTABLE). Final with the 8E close | — |
| L3 | 8-engine research | E8_NAS100 | ❌ REJECTED | registry_8e campaign.json (BLOCKED, never evaluated); closed with the campaign at seq 2170 | None: any NAS100 test needs a new frozen campaign | NAS100 data (I3) for any future campaign |
| M1 | Capital Velocity | +24.5%/day objective | ❌ REJECTED | NEXA_24_5_TRUTH_TABLE.md: CONTRADICTED on DEV (0 target days in 1,774 streams); $200 XAU/NAS100 infeasible; 10-pip TP XAU unreachable. Cap-neutral campaign 2026-10-03: CONTRADICTED again for the tested configuration (0 of 3,125 symbol-days; best day +3.15 %; implemented ceiling +12.67 %/day under the frozen controls) | Do not pursue as an objective; keep math as a constraint | — |

**Also rejected or failed** (recorded in earlier reports):
- the 300 % OFI hypothesis (FAILED; true OFI NOT TESTABLE);
- "Big Trades" (NOT TESTABLE; renamed quote-event engine);
- the TD 8/9/13 veto (CONTRADICTED);
- Donchian standalone (CONTRADICTED);
- QuantConnect connector (invalidated);
- MetaQuotes demo account 5055943373 (invalid; replaced by Pepperstone).

---

## 7. Frozen components

| ID | Area | Component | Status | Evidence | Next action | Dependency |
|---|---|---|---|---|---|---|
| C1 | Risk Engine | NEXA_Risk.mqh (1% / 2% daily / 10% DD / 10 trades / spread ≤15% ATR / caps) | ⚫ FROZEN | sha a43d8328… = approved hash since 2026-10-03 (C4 pre-trade daily-loss budget appended, human-authorised; before: 1f684cde… after S11, 7fd5692a… after the 2026-09-29 correlation fix; pre-change copies build/c4_pre_source/, build/s11_pre_source/); hard-risk limits and defaults unchanged; test_nexa_mql5_invariants.py pins all three approved blocks; NEXA_RISK_CORRELATION_CAP_SAFETY_FIX.md (M1 fixed, fail-closed) | Any change only with explicit human authorisation | Human |
| K1 | V2 research | PHASE3_SIX_FAMILIES_V2 (F1, F2, F3, F5 ACTIVE; 1,632 trials; DSR 1,740; 17 primary tests) | ⚫ FROZEN | research/registry_v2: ANCHOR 6090be68…; ledger 7 events, head seq 6 bbd9a28e… (verified today), no EVALUATION_OPENED; witness file present; V2_OPENING_CHECKLIST.md | Human: explicit 'OPEN V2' (checkpoint taken from the off-machine record, Q4); then DEV/VAL; seal selection before 2027-01-04; score OOS once after 2028-01-03 | Human approval; republish the off-machine record after every V2 event |
| K4 | V2 research | Superseded V2 freezes 27b3463f, f2dc4ffb, faac4c86, 88b7688b | ⚫ FROZEN | registry_v2_superseded_* (+ .SUPERSEDED.txt) | Never open | — |
| L4 | 8-engine research | Accidental freeze c472d69f; superseded 834473f0 | ⚫ FROZEN | registry_8e_ACCIDENTAL_c472d69f(.ACCIDENTAL.txt); registry_8e_superseded_834473f0 | Never open | — |

**Other frozen / pinned artefacts that must not be edited:**
- Trade DNA schema v1.0 and f00–f47 / `PackFeatures`;
- `NEXA_BASELINE_BACKUP_20260919-124052`;
- every file in the V2 pin set (42 files: code 23, data 14, design 5, including `nexa_execution.py` and `OOS_DETERMINATION_V2.md`);
- the 8E pin set (including `nexa_execution.py`, `run_8e.py`, `NEXA_8_ENGINE_SPECIFICATION.md`, `NEXA_24_5_DAILY_FEASIBILITY_AUDIT.md`);
- witness files in `~/.nexa_registry_witness/`.

---

## 8. Critical dependencies

```
B-EXPOSURE-CAP ──► cap-neutral tester campaign (done 2026-10-03) ──► 1,902 resolved trades ──► Gate 8 NEGATIVE_EXPECTANCY ──► cap unchanged; Gate 9 / ONNX / calibration not warranted for this rule set
Off-machine anchor record ──► any registry mutation (OPEN V2)
8E ──► CLOSED (REJECTED seq 2170); no remaining dependencies
D-EXEC-ENTRYBAR fix ──► any FUTURE STOP-entry campaign (V2 unaffected; editing nexa_execution.py breaks V2 pins)
"OPEN V2" ──► DEV/VAL ──► selection sealed < 2027-01-04 ──► 2027 OOS data ──► single OOS score > 2028-01-03
deviation (S11, D-TZ, C4 and S13 fixed) ──► deployment ──► multi-chart demo forward check ──► execution logs
Parity (window-B contract PASS 2026-10-03) ──► tester replica of any candidate (none yet)
Validated edge (none yet) ──► shadow mode ──► promotion gate ──► production
```

---

## 9. Remaining engineering work

| Item | Blocked by |
|---|---|
| ✅ B-PARITY-LIQ: RESOLVED 2026-10-03 (oracle RC1 + RC2 fixed; RC3 tie accepted) | — |
| ✅ B-PARITY-EDGE: RESOLVED 2026-10-03 (oracle EDGE-1 decision clock fixed; EDGE-2 tie accepted) | — |
| ✅ EA evaluating Friday's last bar at Monday's first tick (found by EDGE-1): fixed in source 2026-10-03 as D46 (stale-bar guard) | — |
| ✅ B-PARITY-TOL: DECIDED 2026-10-03 (option A: journal-quantisation tolerance + reviewed tie register) → window-B contract PASS | — |
| ✅ Stored window-B parity reports replaced with the PASS result (2026-10-03; pre-fix reports archived as SUPERSEDED_*) | — |
| ✅ S11 exposure fail-open fix: done in source 2026-10-03 (human-approved; D47); deploys with the build below | — |
| ✅ D-TZ DST-aware clock: done in source 2026-10-03 (human-approved; D48); deploys with the build below | — |
| ✅ S13 UsdComposite alignment: done in source 2026-10-04 (human-approved; D50); f29 now parity-compared; deploys with the build below | — |
| S14 deviation policy | Human |
| ✅ D-DAYLOSS-TRIGGER pre-trade budget (C4): done in source 2026-10-03 (human-approved; D49); deploys with the build below | — |
| D-EXEC-ENTRYBAR fix (before any future STOP-entry campaign; 8E closed) | Human; pinned by V2 |
| Optional: `OrderCheck` (M5), `OnTester` R summary (M3) | Unblocked; low risk |
| Schema v1.1 (decision-contract fields) | Human approval |
| D45 position-management fix (partial close / time exit after breakeven) | **Done in source 2026-10-03**; verified; deploys with the build below |
| D46 stale-bar guard (no trade on a bar evaluated > 6 h after it closed) | **Done in source 2026-10-03**; verified (12/12 regression runs); deploys with the build below |
| Redeploy the current verified build, then a multi-chart demo forward check | Human, after the decisions above |
| Documentation drift: `V2_OPENING_CHECKLIST.md` §B still expects `NEXA_Risk` = `e706d453`; the `NEXA_BUILD_MANIFEST.json` header still reads 2026-09-20 "No dataset exists". Neither is in the V2 pin set (verified). | Approval to edit |
| Off-machine record: republish after every new V2 event (published 2026-10-02, Q4) | Human approval of each V2 event |
| Disk headroom (7.2 GiB free) and the 8 GB-RAM tester instability (B-TERMINAL) | Human/infrastructure |

---

## 10. Remaining research work

1. **8E:** DONE. VAL, pinned selection and analysis run, then CLOSED as REJECTED (no edge). Any follow-up only as a new frozen campaign.
2. **V2:** open, then DEV/VAL, then sealed selection before 2027-01-04, then prospective OOS.
3. **Knowledge-base hypotheses** (40, none tested), in the priority order of `AL:research/knowledge/RESEARCH_HYPOTHESIS_BACKLOG.md`:
   - method gates;
   - volatility/risk layer;
   - execution realism (needs logs);
   - regime/session descriptors;
   - patterns.
4. **NEXA future backlog B1–B12** (`research/reports/NEXA_FUTURE_RESEARCH_BACKLOG.md`): mostly blocked by the absence of a validated edge (cap-neutral Gate 8: NEGATIVE_EXPECTANCY).
5. **205-indicator library:** location unknown. It cannot be included until it is supplied.

---

## 11. Remaining validation work

| Item | Current state |
|---|---|
| NEXA Gate 5/7 labels at scale | 1,902 resolved cap-neutral trades exist (research config); not labelled |
| Gate 8 statistics on NEXA | **Done 2026-10-03 (cap-neutral): NEGATIVE_EXPECTANCY**, −0.318R/trade |
| Gate 9 model / calibration | Not warranted: no edge to filter |
| Gate 11 portfolio/risk/exec re-validation | Needs multi-symbol Trade DNA |
| Gate 12 WF/OOS on NEXA | Not warranted for this rule set (Gate 8 negative) |
| Gate 13 integration | Nothing to integrate |
| Feature parity | **PASS (window B, 2026-10-03):** all 4 symbols, 112,688 rows, 0 mismatches, 47 reviewed ties accepted |
| Multi-instance contention, requotes, freeze-level paths | Untested in the tester; needs a demo forward check |
| 8E statistical validation | DONE 2026-10-02: VAL + DSR/PBO + stress; no pick passes DSR; campaign REJECTED |
| V2 statistical validation | Not started (0 results) |

---

## 12. Remaining data work

| Data item | State |
|---|---|
| Real ticks | Only 21 days (2026-08-28 → 2026-09-25). Tick logger exists but is not running. |
| NAS100 history | None (BLOCKED decision) |
| Depth / volume / aggressor / trade size | Not provided by Pepperstone (NOT TESTABLE) |
| Historical swap rates | None (only a 2026-09 snapshot) |
| Second synchronous feed | None (V2 F4 BLOCKED) |
| FX historical spread | The recorded M1 spread is the minute minimum, so it understates cost (DATA-LIMITED) |
| Execution logs (fills, requotes, slippage) | None until demo forward testing is approved |
| Intraday M1 gaps in DEV | D-M1-GAPS documented |
| Disk | 7.2 GiB free; avoid broad downloads (the 24 GB D1 trap) |

---

## 13. Recommended execution order

| Step | Title | Action | Items | Dependency |
|---|---|---|---|---|
| 0 | ✅ DONE 2026-10-02 (8E) | RESEARCH_8E_V1: Route A approved and run (VAL 2,160 + pinned selection of 6 groups + analysis), then formally CLOSED as REJECTED at seq 2170 9f7249a2…. No edge found. | L1, L2, L3 | — |
| 1 | ✅ DONE 2026-10-02 (registry integrity) | V2 anchor 6090be68… / head seq 6 bbd9a28e… and 8E anchor 6468fdea… / heads through seq 2170 9f7249a2… published off-machine as the private claude.ai record NEXA Registry Checkpoints (https://claude.ai/artifact/6o1hnw9docUUW48gZ5Wf59). Ongoing: republish after every new V2 event; optional email or signed Git tag copy. | Q4 | — |
| 2 | ✅ DONE 2026-10-03 (B-EXPOSURE-CAP) | Option B run: tester-only cap-neutral campaign (48/48 runs verified). Gate 8 NEGATIVE_EXPECTANCY: net −0.318R/trade, 95 % CI [−0.384, −0.250], n = 1,902. Production cap UNCHANGED; a change is not justified. | C3 | — |
| 3 | Other frozen-file / policy decisions | S14 deviation; schema v1.1. (B-PARITY-TOL decided 2026-10-03: option A; S11 and D-TZ fixed 2026-10-03: option A; C4 fixed 2026-10-03: option B; S13 fixed 2026-10-04: option B.) | E3, A1 | Human |
| 4 | Unblocked engineering | Feature parity DONE 2026-10-03: B-PARITY-LIQ and B-PARITY-EDGE resolved (oracle RC1, RC2, EDGE-1 fixed; RC3 and EDGE-2 accepted ties) and B-PARITY-TOL decided (option A) → window-B contract PASS on all 4 symbols. Stored window-B parity reports replaced with the PASS result. The Friday-to-Monday evaluation found by EDGE-1 is fixed in source (D46 stale-bar guard). With approval, fix documentation drift (V2 checklist hash, build-manifest header). | F3, Q5 | None (docs need approval) |
| 5 | Research method gates (research copies only) | Apply KB hypotheses H-DELAY-PARITY, H-COST-SHRINK, H-SEARCH-DEFLATE, H-NOISE-OBJ, H-HIT-PROB to existing NEXA artefacts. No frozen file touched. | N6 | Human approval of a research phase |
| 6 | V2 opening | If approved: 'OPEN V2' → DEV/VAL per checklist → seal selection before 2027-01-04 → collect 2027 OOS → score once after 2028-01-03. | K1 | Steps 1 + explicit human OPEN V2 |
| 7 | ✅ NEXA's own validation chain: Gate 8 DONE 2026-10-03 | The cap-neutral campaign produced 1,902 resolved trades; Gate 8 = NEGATIVE_EXPECTANCY. Gate 9 meta-label and calibration are not warranted for this rule set. | F2, H2, D2 | — |
| 8 | Data | Approve post-freeze tick logging (NEXA_TickLogger); decide NAS100 history; record execution logs once demo forward testing is approved. | I2, I3 | Human approval; disk (7.2 GiB free) |
| 9 | Volatility / risk-layer research | H-VOL-1..4, H-ROUGH-1, H-VR-SCALE, H-GAP-VOL, H-VAR-TRIGGER, H-TAIL-SIM on existing bars (strongest evidence prior). | N6 | Step 5 gates |
| 10 | Deployment and forward check | Redeploy current verified build (now incl. the D45 position-management fix, the D46 stale-bar guard, the S11 exposure fail-closed fix, the D-TZ DST-aware clock, the C4 daily-loss budget and the S13 time-aligned USD composite; build/NEXA_EA_S13.ex5 dec57013…); multi-chart demo forward check (lock contention, requotes, freeze levels). | B2, Q3 | Step 3 decided; human deployment approval |
| 11 | Production | Only after a PASS_CANDIDATE (V2 OOS 2028) or other validated edge: tester replica → shadow mode → promotion gate, NEXA_Risk unchanged. | P1 | All of the above |

---

## 14. Definition of DONE for the entire NEXA project

**NEXA is DONE only when every criterion below holds with repository evidence.**

| # | Criterion | Current state |
|---|---|---|
| 1 | A frozen campaign yields a PASS_CANDIDATE on its prospective OOS (no re-tuning) | Not yet — V2 OOS cannot be scored before 2028-01-03; 8E REJECTED 2026-10-02 (no pick passes DSR on VAL); factory 0 survivors |
| 2 | The candidate is replicated in the MT5 Strategy Tester with the live EA (parity within an approved tolerance) | Not yet — no candidate exists. The parity half is met: window-B contract PASS on all 4 symbols under the approved tolerance (2026-10-03) |
| 3 | NEXA itself produces ≥200 resolved trades → labels → Gate 8 stats pass (expectancy CI > 0 after stress costs, DSR/PBO) | No — the cap-neutral campaign produced 1,902 resolved trades (2026-10-03) and Gate 8 returned NEGATIVE_EXPECTANCY (−0.318R/trade) |
| 4 | Optional ML: a veto-only meta-label beats a random-veto null OOS; calibrated (Brier skill > 0) | Not yet — no model |
| 5 | All engineering safety items resolved or explicitly accepted (S11, D-TZ, S13, S14, D-DAYLOSS-TRIGGER, D-EXEC-ENTRYBAR) | Not yet — S11, D-TZ, D-DAYLOSS-TRIGGER (C4) and S13 fixed in source 2026-10-03/04 (human-approved, D47–D50); S14 still open, human decision (D-EXEC-ENTRYBAR no longer blocks 8E, which is closed; still open for future STOP-entry campaigns). D45 position-management defect and D46 stale-bar evaluation fixed in source 2026-10-03 (not deployed) |
| 6 | NEXA_Risk.mqh limits unchanged except by explicit human authorisation; invariant tests green | Yes, currently: limits and defaults unchanged; NEXA_Risk.mqh changed only by human-authorised fixes (now a43d8328 after S11 and C4, 2026-10-03); 628 tests pass |
| 7 | Current verified build deployed; multi-chart demo forward check passed; execution logs recorded | Not yet — terminal runs the stale 2026-09-27 build |
| 8 | Shadow mode + promotion gate passed; promotion state moves from RESEARCH_ONLY | Not yet — RESEARCH_ONLY |
| 9 | Monitoring / strategy-retirement rule pre-declared (backlog B11) | Not yet |
| 10 | Registry anchors and heads published off-machine; evidence reproducible | Yes, as of 2026-10-02 (claude.ai record https://claude.ai/artifact/6o1hnw9docUUW48gZ5Wf59); must be republished after every new V2 event |

**Explicitly NOT part of DONE** (contradicted or prohibited):
- +24.5 %/day;
- guaranteed "no loss";
- martingale, grid or averaging down;
- any bypass of `NEXA_Risk.mqh`.

---

# WHAT WE SHOULD START NOW

**Do not start these until you approve them.** They are listed in dependency order.

1. **✅ 8E: DONE (2026-10-02).** VAL and pinned selection ran under human-approved Route A, then the campaign was formally CLOSED as REJECTED at seq 2170 `9f7249a2…`. No edge found. The 2026-10-12 deadline no longer applies.
2. **✅ Off-machine record: DONE (2026-10-02).** The V2 anchor/head and the 8E heads are published in the private claude.ai record [NEXA Registry Checkpoints](https://claude.ai/artifact/6o1hnw9docUUW48gZ5Wf59). Republish it after every new V2 event, and take every future checkpoint from it. An email or signed Git tag copy is optional.
3. **✅ B-EXPOSURE-CAP: DECIDED (2026-10-03).** The tester-only cap-neutral campaign showed no edge (Gate 8 NEGATIVE_EXPECTANCY, −0.318R per trade), so the production cap stays unchanged. Revisit only if a future, properly validated edge appears.
4. **Decide the remaining frozen-file and policy items:**
   - deviation;
   - schema v1.1.

   (Parity tolerance decided 2026-10-03: option A. S11 exposure fail-open fixed 2026-10-03: option A, D47. D-TZ DST-aware clock fixed 2026-10-03: option A, D48. 2 % daily-loss budget (C4) fixed 2026-10-03: option B, D49. S13 USD composite fixed 2026-10-04: option B, D50.)
5. **✅ B-PARITY-LIQ: RESOLVED (2026-10-03).** Two oracle defects fixed (RC1 weekend Asia carry-over, RC2 last-day PDH/PDL); RC3 accepted as a floating-point tie. Liquidity state parity is exact on all four window-B symbols. **✅ B-PARITY-EDGE: RESOLVED (2026-10-03).** The oracle now reads M5/M15/H1 at the EA's real decision time after tick gaps (EDGE-1); exact 1.20 displacement ties accepted (EDGE-2). Window-B parity is exact apart from accepted ties and journal rounding; **✅ B-PARITY-TOL: DECIDED (2026-10-03), option A** → the window-B parity contract **PASSES** on all four symbols (0 mismatches, 47 reviewed ties). The stored window-B parity reports now hold the PASS result. The Friday-to-Monday evaluation found by EDGE-1 is fixed in source (D46). **With approval:** correct the two drifted non-pinned docs.
6. **Approve a research phase that runs the knowledge-base method gates** on research copies:
   - H-DELAY-PARITY;
   - H-COST-SHRINK;
   - H-SEARCH-DEFLATE;
   - H-NOISE-OBJ;
   - H-HIT-PROB.
   No frozen file is touched.
7. **Decide whether to OPEN V2.** It needs step 2; selection must be sealed before 2027-01-04.
8. **✅ NEXA tester campaign and Gate 8: DONE (2026-10-03)** via the cap-neutral campaign (1,902 trades, NEGATIVE_EXPECTANCY). Gate 9 and calibration are not warranted for this rule set.
9. **Data approvals:** tick logging, NAS100, and execution logging for a later demo forward check.
10. **Only after all of the above:** redeploy the verified build and run a multi-chart demo forward check. Production stays RESEARCH_ONLY until a validated edge exists.

**STOP.** Items 1 (8E), 2 (off-machine record), 3 (B-EXPOSURE-CAP), 5 (parity: B-PARITY-LIQ, B-PARITY-EDGE, B-PARITY-TOL) and 8 (tester campaign + Gate 8) are done. No other action above has been started.
