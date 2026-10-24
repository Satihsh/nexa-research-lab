# NEXA_EXPORT_MANIFEST

**Export date:** 2026-09-25 09:09:13 UTC  
**Task:** DISCOVER → PRESERVE → VERSION → EXPORT. No file was modified, rewritten, regenerated or summarised.  
**Method:** two independent recursive scans; every exported file re-hashed from inside its archive and matched against the discovery hash.

## How content is delivered — read this first

File **content is carried byte-exact inside the two archives**, not pasted inline. Inlining would be the lossy option: the corpus includes binaries (`.tar.gz`, `.png`, `.pdf`), a 42 MB gzip and a 72 MB CSV, and pasting text through a chat reply risks silent whitespace, encoding and line-ending changes that no reader could detect. Instead every file below carries its SHA-256; unzip and verify with `sha256sum -c` against this table.

| Archive | Contents | Size |
|---|---|---|
| `NEXA_EXPORT_CORE.zip` | all source, docs, specs, plans, manifests, schema, tests, baseline, transcripts, evidence | 4,372,628 B |
| `NEXA_EXPORT_DATA.zip` | derived XAUUSD market data (M1–D1) | 56,740,959 B |

Both archives pass zip CRC checks. Internal root is `NEXA/`.

## Completeness verification

| Measure | Count |
|---|---|
| Files discovered (scan 1) | 91 |
| Files discovered (scan 2, independent) | 91 |
| In scan 2 but not scan 1 | 0 |
| In scan 1 but not scan 2 | 0 |
| Exported, byte-verified | 73 |
| Hash mismatches | 0 |
| Excluded (explicit, below) | 18 |

## Explicit exclusions

**EXCLUDED:** the 18 raw `uploads/XAUUSD*.zip` archives (131 MB).  
**REASON:** they are your own original uploads, already in your possession; bundling them doubles the export for zero information gain. Each is recorded below with its SHA-256 so your copies can be verified as the exact bytes this pipeline consumed. Say so and I will bundle them.

**EXCLUDED (scratch, not part of the workspace):** `/home/claude/` — `setA_m1.pkl` and `ladder.pkl` (caches, regenerable from the raw zips), `raw_xauusd/` (extracted copies of the raw zips), `repos/` and `datarepos/` (third-party git clones of the 13 + 3 evaluated repositories; re-clonable, and `qmt-gateway`, `polymarket-bot`, `fin-cn-agent`, `dukascopy-downloader` carry **no licence** so their code must not be redistributed), `.cache` `.npm` `.config` `.local` (tooling).

## Institutional-knowledge gap — the most important finding

**The narrative record ends at 2026-09-17.** The transcript (`transcripts/2026-09-17-07-03-31-nexa-mt5-ea-hardening.txt`) covers the conversation only up to that compaction, and `NEXA_RESEARCH_AUDIT_FULL.md` (Parts 1–40) is byte-identical to the baseline — it was last extended before Stage 0.

Everything after that — the 13-repository forensic analysis, integration plans V1/V2, implementation plan V3, the Stage 0 MetaEditor compile, Stages 1–5, the external-data pipeline, and the XAUUSD audit — **is not in any narrative document.** Verified: the audit contains 0 mentions of `nexa_ingest`, `nexa_parity`, `nexa_labels`, `nexa_validate`, `nexa_marketdata`, `schema v1.0` or `Axiory`; the transcript contains 0 mentions of `IMPLEMENTATION_PLAN_V3`, `Stage 5` or `Axiory`.

**What survives, in structured form:** `NEXA_IMPLEMENTATION_PLAN_V3.md` (the plan and every amendment), `NEXA_BUILD_MANIFEST.json` (stage status, tests, blockers, conflicts C1–C3), the four `research/README*.md` (each stage's contract and design decisions), `data/NEXA_DATASET_MANIFEST.json` (XAUUSD findings), `NEXA_DEFECT_MATRIX.md` (D01–D44). The *decisions* are largely preserved; the *reasoning trail between them* is not.

Per your instruction I have **not** reconstructed that history from memory. If you want it captured, it would have to be written as a new, clearly-labelled document — not presented as a recovered original.

## Authoritative files

| Role | File |
|---|---|
| **Authoritative EA** | `NEXA_EA.mq5` (Stage 1, sha `9d1e6aaf8150fae7`) |
| **Authoritative master spec** | `uploads/NEXA_COMPLETE_RESEARCH_MASTER.md` (original, user-supplied) |
| Accumulated research audit | `NEXA_RESEARCH_AUDIT_FULL.md` (Parts 1–40; predates Stages 1–5) |
| Current implementation plan | `NEXA_IMPLEMENTATION_PLAN_V3.md` |
| **Latest build manifest** | `NEXA_BUILD_MANIFEST.json` |
| **Latest defect/audit document** | `NEXA_DEFECT_MATRIX.md` (D01–D44) |
| Trade DNA schema | `nexa_schema_v1.json` (v1.0, 96 MT5 columns, f00–f47) |
| Risk engine | `NEXA_Risk.mqh` — **byte-identical to baseline through every stage** |

**`NEXA_COMPLETE_RESEARCH_MASTER_UPDATED.md` does not exist** in any location. Only the original `NEXA_COMPLETE_RESEARCH_MASTER.md` was found.

## MQL5 dependency graph (verified from `#include` lines)

```
NEXA_EA.mq5
├── <Trade\Trade.mqh>                  (MetaQuotes standard library)
├── NEXA_Common.mqh
├── NEXA_Features.mqh ── NEXA_Common.mqh, NEXA_Liquidity.mqh
├── NEXA_Risk.mqh ── NEXA_Common.mqh
├── NEXA_Intelligence.mqh ── NEXA_Common.mqh
├── NEXA_Microstructure.mqh ── NEXA_Common.mqh
├── NEXA_Advanced_Ingest.mqh ── NEXA_Common.mqh
├── NEXA_FOMC.mqh ── NEXA_Common.mqh
├── NEXA_Liquidity.mqh ── NEXA_Common.mqh
Standalone scripts (no NEXA includes): NEXA_TrainingExport.mq5, NEXA_SpecSnapshot.mq5,
  NEXA_TickLogger.mq5, NEXA_DealAudit.mq5
Not in build: NEXA_MALE5_Bridge.mqh (optional; requires external MALE5 library)
```

Includes are **quoted**, so they resolve from the including file's directory first. Place `NEXA_EA.mq5` and all eight `.mqh` together in `MQL5\Experts\`.

## Version relationships

**MQL5, baseline → current.** Modified in Stage 1: `NEXA_EA.mq5`, `NEXA_Common.mqh`, `NEXA_Features.mqh`, `NEXA_Intelligence.mqh`, `NEXA_TrainingExport.mq5`. Byte-identical to baseline: `NEXA_Liquidity.mqh`, `NEXA_Risk.mqh`, `NEXA_Microstructure.mqh`, `NEXA_Advanced_Ingest.mqh`, `NEXA_FOMC.mqh`, `NEXA_SpecSnapshot.mq5`, `NEXA_TickLogger.mq5`, `NEXA_DealAudit.mq5`, `NEXA_MALE5_Bridge.mqh`. The baseline directory is the **pre-Stage-1** snapshot and is not authoritative.

**Research audit family.** `NEXA_RESEARCH_AUDIT.md` (Parts 1–8) and `NEXA_RESEARCH_AUDIT_PART2.md` (Parts 9–26) are the early split versions. `NEXA_RESEARCH_AUDIT_FULL.md` contains 27/27 and 84/85 of their substantive paragraphs verbatim — the single miss is `PART2.md`'s own title line. All three preserved.

**PART 25 was never written.** It is absent from `FULL.md`, absent from `PART2.md` (which jumps 24 → 26), and never mentioned in the transcript. A numbering skip at authoring — not lost content.

**Duplicates.** `NEXA_INTEGRATION_PLAN.md` and `_V2.md` exist in both `outputs/` and `uploads/`, byte-identical. Both preserved.

## Stage mapping

| Stage | Files | Status | Tests | Executed or static |
|---|---|---|---|---|
| 0 | 10 MQL5 files | PASS | MetaEditor compile | **executed** — MetaEditor 5.00 build 6204, 18 Sep 2026, Wine/macOS; both units 0 errors / 0 warnings |
| 1 | EA, Common, Features, Intelligence, TrainingExport, `nexa_schema_v1.json` | PASS | 9 static invariant checks | **executed** compile (user-reported 0/0) |
| 2 | `research/nexa_ingest.py` | PASS | 37 | executed (synthetic fixtures) |
| 3 | `research/nexa_parity.py` | PASS (machinery) | 45 | executed on synthetic data — **never run against real MQL5 output** |
| 4 | `research/nexa_labels.py` | PASS | 57 | executed (synthetic OHLC) — **never run on real trades** |
| 5 gate | `research/nexa_validate.py` | PASS (machinery) | 39 | executed; **gate returns FAIL on real input: no Trade DNA exists** |
| 5 data | `research/nexa_marketdata.py` | PASS | 48 | executed on **real** XAUUSD data |
| 6–12, L1, L2, L4, L5, L7, Shadow | — | **BLOCKED / NOT STARTED** | — | — |

**Combined research suite: 226 passed**, three identical deterministic repeats, ruff clean. All figures are from `NEXA_BUILD_MANIFEST.json` and executed runs in this environment.

## Blockers

1. **No Trade DNA exists.** Stage 5's contract consumes labelled Trade DNA, which requires NEXA *decisions* — i.e. an MT5 Strategy Tester run of `NEXA_EA`. MetaQuotes-Demo lacked EURUSD/XAUUSD history and the GBPUSD tester run restarted MT5 under Wine.
2. **No bid/ask or tick data.** The Axiory export is OHLC + tick count. NEXA's hard spread veto (`spreadATRRatio > 0.15`) cannot be evaluated, so a simulation would take trades live NEXA refuses. f28 uncomputable; f29–f31, f46, f47 exempt or unavailable → 42/48 features computable.
3. **Parity never measured.** Stage 3 has no real MQL5 output to compare against.
4. **External data hosts unreachable from this environment** (`datafeed.dukascopy.com`, `histdata.com`, `drive.google.com` → 403 `host_not_allowed`).
5. **L7 WAL** requires an MT5 source change and therefore MetaEditor.

## Unresolved conflicts and known defects

| ID | Topic | Source A | Source B | Current policy |
|---|---|---|---|---|
| C1 | Ambiguous same-bar TP+SL | `NEXA_TrainingExport.mq5`: resolve to LOSS | Stage 4 directive: AMBIGUOUS | AMBIGUOUS default; `PESSIMISTIC_LOSS` flag; stamped in `exec_model` |
| C2 | Fill-bar inclusion | exporter: include fill bar | Stage 4 directive: first bar after fill | EXCLUDE default; `INCLUDE_FILL_BAR` flag; stamped in `exec_model` |
| C3 | Partial close at 1.5R | EA closes half at +1.5R | labeler treats episode as one unit | documented, unresolved |
| D-TZ | **Fixed `InpGMTOffset` vs DST broker** | NEXA uses fixed offset 2 | Axiory server is EET/EEST (GMT+2 winter, +3 summer) | **Found in XAUUSD audit. Session tags off by 1h late-Mar→late-Oct. Not fixed; MT5 untouched** |
| D-EPOCH | Execution rows carry `1970.01.01` `decision_ts` | `ResetSignal(blank)` sets 0 | — | handled downstream via `decision_ts_effective`; MT5 not changed |
| D-FOMC | FOMC table ends 2026-12-09 | — | — | gate fails closed from 2027 until 2027 dates added |
| D-XAU | Two XAUUSD "versions" | Set A | Set B = Set A **+0.10 constant** | not independent sources; use one |

**Promotion state: `RESEARCH_ONLY`.** No model trained, calibrated, shadowed or promoted. Engineering validity is not trading validity.

## Per-file records

Every discovered file. `BUNDLE` = which archive holds its exact bytes.

### `NEXA_Advanced_Ingest.mqh`
- **PATH:** `NEXA_Advanced_Ingest.mqh`
- **SIZE:** 5,481 bytes
- **SHA256:** `f0a49c2fcdefdbd5c8a7d3f2a3bc8d893926a95ac1d82d1a78cd12046a8ad12a`
- **STATUS:** CURRENT
- **PURPOSE:** Pre-flight checks (live broker state), diagnostic-only shadow ledger
- **DEPENDENCIES:** NEXA_Common.mqh
- **AUTHORITATIVE:** YES
- **STAGE:** pre-S0 (unchanged)
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_BUILD_MANIFEST.json`
- **PATH:** `NEXA_BUILD_MANIFEST.json`
- **SIZE:** 10,797 bytes
- **SHA256:** `33d31fc05bf18374ebc245bd9656562c5b33c55d4677de3a5a025d392805ba6a`
- **STATUS:** CURRENT
- **PURPOSE:** Build/stage status, hashes, tests, blockers, conflicts C1-C3, promotion state
- **DEPENDENCIES:** all
- **AUTHORITATIVE:** YES (latest build manifest)
- **STAGE:** S0-S5
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_Common.mqh`
- **PATH:** `NEXA_Common.mqh`
- **SIZE:** 10,220 bytes
- **SHA256:** `f4d0a7de036adf46ce9348b62ef967188c1fe52ed0c793f1c8cdcc6139c069e1`
- **STATUS:** CURRENT
- **PURPOSE:** Shared enums, NexaSignal struct, ResetSignal, GMT clock helper, DNA schema version
- **DEPENDENCIES:** none
- **AUTHORITATIVE:** YES
- **STAGE:** S1
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_DEFECT_MATRIX.md`
- **PATH:** `NEXA_DEFECT_MATRIX.md`
- **SIZE:** 9,789 bytes
- **SHA256:** `9fca6ce8061bf3c7f23c35df24f37ff504ae9e24aead693ba774dc78c8817c16`
- **STATUS:** CURRENT
- **PURPOSE:** 29-defect hardening matrix (D01-D29) + adversarial pass (D30-D44)
- **DEPENDENCIES:** MQL5 sources
- **AUTHORITATIVE:** YES (latest defect doc)
- **STAGE:** pre-S0 hardening
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_DealAudit.mq5`
- **PATH:** `NEXA_DealAudit.mq5`
- **SIZE:** 2,847 bytes
- **SHA256:** `a38a9c068b360d073be5858a0f6b001198ee3764af98e20a3fea6605f084ed89`
- **STATUS:** CURRENT
- **PURPOSE:** Standalone script: commission/swap from deal history
- **DEPENDENCIES:** none
- **AUTHORITATIVE:** YES
- **STAGE:** data tool
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_EA.mq5`
- **PATH:** `NEXA_EA.mq5`
- **SIZE:** 49,501 bytes
- **SHA256:** `9d1e6aaf8150fae782fb7058fbbe819f87d1e33423c319f9deab28ff34c29da2`
- **STATUS:** CURRENT
- **PURPOSE:** Main Expert Advisor: orchestrator, decision gate, execution, Trade DNA writer (schema v1.0)
- **DEPENDENCIES:** NEXA_Common.mqh, NEXA_Features.mqh, NEXA_Liquidity.mqh, NEXA_Risk.mqh, NEXA_Intelligence.mqh, NEXA_Microstructure.mqh, NEXA_Advanced_Ingest.mqh, NEXA_FOMC.mqh, <Trade\Trade.mqh>
- **AUTHORITATIVE:** YES
- **STAGE:** S0-S1
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_FOMC.mqh`
- **PATH:** `NEXA_FOMC.mqh`
- **SIZE:** 5,513 bytes
- **SHA256:** `7d47467e5d9796004cf5a56d1b26a8fe8c7385c34c489946929f74441a30694c`
- **STATUS:** CURRENT
- **PURPOSE:** FOMC hard time gate, fail-closed on stale schedule (2026 dates only)
- **DEPENDENCIES:** NEXA_Common.mqh
- **AUTHORITATIVE:** YES
- **STAGE:** pre-S0 (unchanged)
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_Features.mqh`
- **PATH:** `NEXA_Features.mqh`
- **SIZE:** 25,324 bytes
- **SHA256:** `fee0d7a53a55da26763862a6a7db26bfbaf6ef19633c2a10b70e45e9f93a5718`
- **STATUS:** CURRENT
- **PURPOSE:** MTF features, structure/SMC primitives, session levels, causal replay wiring
- **DEPENDENCIES:** NEXA_Common.mqh, NEXA_Liquidity.mqh
- **AUTHORITATIVE:** YES
- **STAGE:** S1
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_IMPLEMENTATION_PLAN_V3.md`
- **PATH:** `NEXA_IMPLEMENTATION_PLAN_V3.md`
- **SIZE:** 17,748 bytes
- **SHA256:** `d0559c45e9392215a4e2021c7f9b633b385f3023b2feadebb92fe47c53f99613`
- **STATUS:** CURRENT
- **PURPOSE:** Final implementation plan: schema, parity, shadow, promotion gate, seams L1-L7, stage order
- **DEPENDENCIES:** all
- **AUTHORITATIVE:** YES (current plan)
- **STAGE:** plan
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_Intelligence.mqh`
- **PATH:** `NEXA_Intelligence.mqh`
- **SIZE:** 14,870 bytes
- **SHA256:** `efa6db4e4abae2a9468906238a4c1fb2dccd9fdbc336208c564200a3ed679885`
- **STATUS:** CURRENT
- **PURPOSE:** AI/ONNX hook, frozen 48-feature PackFeatures, adversarial, expectancy, news, provenance ids
- **DEPENDENCIES:** NEXA_Common.mqh
- **AUTHORITATIVE:** YES
- **STAGE:** S1
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_Liquidity.mqh`
- **PATH:** `NEXA_Liquidity.mqh`
- **SIZE:** 19,446 bytes
- **SHA256:** `99b961a636296798e48e7a26d197cd493c3e55f3aa38d89d5cc9a40fb1575472`
- **STATUS:** CURRENT
- **PURPOSE:** PDH/PDL/Asia liquidity state machine, causal reconstruction
- **DEPENDENCIES:** NEXA_Common.mqh
- **AUTHORITATIVE:** YES
- **STAGE:** pre-S0 (unchanged)
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_Microstructure.mqh`
- **PATH:** `NEXA_Microstructure.mqh`
- **SIZE:** 3,979 bytes
- **SHA256:** `3c549add661ab388ef3e80227dc551d771ffbc3ee65264a2f875d15ea3618663`
- **STATUS:** CURRENT
- **PURPOSE:** OBI/CVD tick-flow PROXIES (inferred, not real LOB)
- **DEPENDENCIES:** NEXA_Common.mqh
- **AUTHORITATIVE:** YES
- **STAGE:** pre-S0 (unchanged)
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_RESEARCH_AUDIT_FULL.md`
- **PATH:** `NEXA_RESEARCH_AUDIT_FULL.md`
- **SIZE:** 137,597 bytes
- **SHA256:** `c0bbd5619b836d3c978c872bb1547f308c2f35804af6c4015e7ec341079e29dc`
- **STATUS:** CURRENT
- **PURPOSE:** Accumulated research audit Parts 1-40 (PART 25 never written). Predates Stages 1-5
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** YES (latest audit)
- **STAGE:** research
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_Risk.mqh`
- **PATH:** `NEXA_Risk.mqh`
- **SIZE:** 11,846 bytes
- **SHA256:** `e706d453d346100f99d06ce3bf2b62697ce544d913bba6ba8053f506115ce5ed`
- **STATUS:** CURRENT
- **PURPOSE:** HARD RISK ENGINE: sizing, ceilings, daily loss, drawdown, correlation, exposure
- **DEPENDENCIES:** NEXA_Common.mqh
- **AUTHORITATIVE:** YES
- **STAGE:** pre-S0 (UNCHANGED through S0-S5)
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_SpecSnapshot.mq5`
- **PATH:** `NEXA_SpecSnapshot.mq5`
- **SIZE:** 5,571 bytes
- **SHA256:** `e04ba6984c53cef1ec238af672346b93cb45ae7f75becbbfa2e88008908ee7eb`
- **STATUS:** CURRENT
- **PURPOSE:** Standalone script: broker symbol spec snapshot
- **DEPENDENCIES:** none
- **AUTHORITATIVE:** YES
- **STAGE:** data tool
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_TickLogger.mq5`
- **PATH:** `NEXA_TickLogger.mq5`
- **SIZE:** 2,800 bytes
- **SHA256:** `f1bd3a20d4085229a84c976fef24303714470983b42d58ec58c2f6a79862de0e`
- **STATUS:** CURRENT
- **PURPOSE:** Standalone script: per-tick spread logger
- **DEPENDENCIES:** none
- **AUTHORITATIVE:** YES
- **STAGE:** data tool
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_TrainingExport.mq5`
- **PATH:** `NEXA_TrainingExport.mq5`
- **SIZE:** 13,722 bytes
- **SHA256:** `e618697172fcebf9c4b4bd5672cfff19ec703c920d971dc5f51528063b17ad0b`
- **STATUS:** CURRENT
- **PURPOSE:** Standalone script: Trade DNA -> labelled training CSV (schema v1.0 names)
- **DEPENDENCIES:** none
- **AUTHORITATIVE:** YES
- **STAGE:** S1
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `data/NEXA_DATASET_MANIFEST.json`
- **PATH:** `data/NEXA_DATASET_MANIFEST.json`
- **SIZE:** 3,790 bytes
- **SHA256:** `cf693389470bfb0186fc4fa71209b6d1c80c14c17b3ed97cc13895e71f738161`
- **STATUS:** CURRENT
- **PURPOSE:** Derived XAUUSD market data (Axiory M1 2018-2026) / dataset manifest
- **DEPENDENCIES:** nexa_marketdata.py
- **AUTHORITATIVE:** YES (research data)
- **STAGE:** S5 data
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `data/XAUUSD_D1.csv`
- **PATH:** `data/XAUUSD_D1.csv`
- **SIZE:** 267,200 bytes
- **SHA256:** `1f3ce9d8ebba396d96981fe8da1f0e6925f115e0dddc6fdc70502954c4ecef55`
- **STATUS:** CURRENT
- **PURPOSE:** Derived XAUUSD market data (Axiory M1 2018-2026) / dataset manifest
- **DEPENDENCIES:** nexa_marketdata.py
- **AUTHORITATIVE:** YES (research data)
- **STAGE:** S5 data
- **CONTENT:** byte-exact in `NEXA_EXPORT_DATA.zip`

### `data/XAUUSD_H1.csv`
- **PATH:** `data/XAUUSD_H1.csv`
- **SIZE:** 6,045,233 bytes
- **SHA256:** `427a359c9c8750ede97eb0c08502454b7060368639611ff9eb4ef349da68149f`
- **STATUS:** CURRENT
- **PURPOSE:** Derived XAUUSD market data (Axiory M1 2018-2026) / dataset manifest
- **DEPENDENCIES:** nexa_marketdata.py
- **AUTHORITATIVE:** YES (research data)
- **STAGE:** S5 data
- **CONTENT:** byte-exact in `NEXA_EXPORT_DATA.zip`

### `data/XAUUSD_H4.csv`
- **PATH:** `data/XAUUSD_H4.csv`
- **SIZE:** 1,587,514 bytes
- **SHA256:** `ab3e404842b226c258ad10604f83a45cd33612274f806e8f855bdfc3e620d131`
- **STATUS:** CURRENT
- **PURPOSE:** Derived XAUUSD market data (Axiory M1 2018-2026) / dataset manifest
- **DEPENDENCIES:** nexa_marketdata.py
- **AUTHORITATIVE:** YES (research data)
- **STAGE:** S5 data
- **CONTENT:** byte-exact in `NEXA_EXPORT_DATA.zip`

### `data/XAUUSD_M1.csv.gz`
- **PATH:** `data/XAUUSD_M1.csv.gz`
- **SIZE:** 42,328,499 bytes
- **SHA256:** `f0c95a7a289058561c5db3ed485de32f32530b6bbd83ae1f0e48aae7571c8d9d`
- **STATUS:** CURRENT
- **PURPOSE:** Derived XAUUSD market data (Axiory M1 2018-2026) / dataset manifest
- **DEPENDENCIES:** nexa_marketdata.py
- **AUTHORITATIVE:** YES (research data)
- **STAGE:** S5 data
- **CONTENT:** byte-exact in `NEXA_EXPORT_DATA.zip`

### `data/XAUUSD_M15.csv`
- **PATH:** `data/XAUUSD_M15.csv`
- **SIZE:** 24,450,138 bytes
- **SHA256:** `df2392d153df21fa1e8f7f6b54e3abae5e6d3c62e156b64ef35e21960d4f6292`
- **STATUS:** CURRENT
- **PURPOSE:** Derived XAUUSD market data (Axiory M1 2018-2026) / dataset manifest
- **DEPENDENCIES:** nexa_marketdata.py
- **AUTHORITATIVE:** YES (research data)
- **STAGE:** S5 data
- **CONTENT:** byte-exact in `NEXA_EXPORT_DATA.zip`

### `data/XAUUSD_M5.csv`
- **PATH:** `data/XAUUSD_M5.csv`
- **SIZE:** 71,768,989 bytes
- **SHA256:** `d518bb359425fa55f114856178a780902e70296bc838d0c4aa6688b959a44dd2`
- **STATUS:** CURRENT
- **PURPOSE:** Derived XAUUSD market data (Axiory M1 2018-2026) / dataset manifest
- **DEPENDENCIES:** nexa_marketdata.py
- **AUTHORITATIVE:** YES (research data)
- **STAGE:** S5 data
- **CONTENT:** byte-exact in `NEXA_EXPORT_DATA.zip`

### `nexa_schema_v1.json`
- **PATH:** `nexa_schema_v1.json`
- **SIZE:** 5,785 bytes
- **SHA256:** `c24198b09b0e7192b4c7946c8377add0b2516474da9b5d105d54bab8e0eff273`
- **STATUS:** CURRENT
- **PURPOSE:** Canonical Trade DNA schema v1.0 contract (96 MT5 cols), generated from SchemaHeader()
- **DEPENDENCIES:** NEXA_EA.mq5
- **AUTHORITATIVE:** YES
- **STAGE:** S1
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `research/README.md`
- **PATH:** `research/README.md`
- **SIZE:** 5,178 bytes
- **SHA256:** `04dad299f888bbdf01d12b71d3ab204615bd5962eecdda4776b77b324d923f4a`
- **STATUS:** CURRENT
- **PURPOSE:** Research-tier documentation
- **DEPENDENCIES:** pandas, numpy
- **AUTHORITATIVE:** YES
- **STAGE:** research docs
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `research/README_LABELS.md`
- **PATH:** `research/README_LABELS.md`
- **SIZE:** 8,611 bytes
- **SHA256:** `d3cc3c697811032dde8e56c3532114bbc9fbed06a5cc9095f3879158c3cb1c6f`
- **STATUS:** CURRENT
- **PURPOSE:** Research-tier documentation
- **DEPENDENCIES:** pandas, numpy
- **AUTHORITATIVE:** YES
- **STAGE:** research docs
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `research/README_MARKETDATA.md`
- **PATH:** `research/README_MARKETDATA.md`
- **SIZE:** 4,466 bytes
- **SHA256:** `7d02890849784f673ed31bbeb7fa3473531fcc94aadfcd516f3d20d839f22402`
- **STATUS:** CURRENT
- **PURPOSE:** Research-tier documentation
- **DEPENDENCIES:** pandas, numpy
- **AUTHORITATIVE:** YES
- **STAGE:** research docs
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `research/README_PARITY.md`
- **PATH:** `research/README_PARITY.md`
- **SIZE:** 7,636 bytes
- **SHA256:** `b06313d8be592923b365fdedb16f254ccefa63eb98de6a64f1a0898137b8ef85`
- **STATUS:** CURRENT
- **PURPOSE:** Research-tier documentation
- **DEPENDENCIES:** pandas, numpy
- **AUTHORITATIVE:** YES
- **STAGE:** research docs
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `research/nexa_ingest.py`
- **PATH:** `research/nexa_ingest.py`
- **SIZE:** 28,906 bytes
- **SHA256:** `7311ce95da3225464aed496ba95be56dc93eca25adaa3fb1b2dd3ff8cca44829`
- **STATUS:** CURRENT
- **PURPOSE:** Trade DNA ingestion + validation + episode linking
- **DEPENDENCIES:** pandas, numpy
- **AUTHORITATIVE:** YES
- **STAGE:** S2
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `research/nexa_labels.py`
- **PATH:** `research/nexa_labels.py`
- **SIZE:** 27,002 bytes
- **SHA256:** `e4217ed54fbaf19fb3617503eb095d90936f1741ee36e7cbee4d0128639754a3`
- **STATUS:** CURRENT
- **PURPOSE:** Triple-barrier labeler (480 M1 horizon, BE 1R, time exit 48/0.3R)
- **DEPENDENCIES:** pandas, numpy
- **AUTHORITATIVE:** YES
- **STAGE:** S4
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `research/nexa_marketdata.py`
- **PATH:** `research/nexa_marketdata.py`
- **SIZE:** 25,922 bytes
- **SHA256:** `0a849dc9a8ba4fc085719d2956b12dbc8ea928af9a0145bdfe0616de0a72a82a`
- **STATUS:** CURRENT
- **PURPOSE:** External market-data adapters + quality gate + TF ladder
- **DEPENDENCIES:** pandas, numpy
- **AUTHORITATIVE:** YES
- **STAGE:** S5 (data)
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `research/nexa_parity.py`
- **PATH:** `research/nexa_parity.py`
- **SIZE:** 48,101 bytes
- **SHA256:** `f43b6aaffa5dcd87bd32afd22bf89e17c02eb80cfd9fa0418bdc8dfb295d432d`
- **STATUS:** CURRENT
- **PURPOSE:** Independent parity oracle (43/48 reconstructable, 5 exempt)
- **DEPENDENCIES:** pandas, numpy
- **AUTHORITATIVE:** YES
- **STAGE:** S3
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `research/nexa_validate.py`
- **PATH:** `research/nexa_validate.py`
- **SIZE:** 30,326 bytes
- **SHA256:** `18448790c1cc84e433a3c9b9e4275c4f639b4f48e414eb544560b20aab6faf71`
- **STATUS:** CURRENT
- **PURPOSE:** Dataset validation gate (purge, embargo, leakage)
- **DEPENDENCIES:** pandas, numpy
- **AUTHORITATIVE:** YES
- **STAGE:** S5
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `research/test_nexa_ingest.py`
- **PATH:** `research/test_nexa_ingest.py`
- **SIZE:** 16,319 bytes
- **SHA256:** `bb2c46c44649047346b7079b6a173fc7dc1f5c48d4534cb14013078b81c66d84`
- **STATUS:** CURRENT
- **PURPOSE:** Unit tests for nexa_ingest.py
- **DEPENDENCIES:** nexa_ingest.py
- **AUTHORITATIVE:** YES
- **STAGE:** research
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `research/test_nexa_labels.py`
- **PATH:** `research/test_nexa_labels.py`
- **SIZE:** 26,817 bytes
- **SHA256:** `200f06db32ed1719f56f4ae296dfcfc269ce719af85b59da2198e33d65639168`
- **STATUS:** CURRENT
- **PURPOSE:** Unit tests for nexa_labels.py
- **DEPENDENCIES:** nexa_labels.py
- **AUTHORITATIVE:** YES
- **STAGE:** research
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `research/test_nexa_marketdata.py`
- **PATH:** `research/test_nexa_marketdata.py`
- **SIZE:** 16,805 bytes
- **SHA256:** `86c2c66c3792116a574dd9ed89b8e798179b837d2409cd72fd792c1306f2ab49`
- **STATUS:** CURRENT
- **PURPOSE:** Unit tests for nexa_marketdata.py
- **DEPENDENCIES:** nexa_marketdata.py
- **AUTHORITATIVE:** YES
- **STAGE:** research
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `research/test_nexa_parity.py`
- **PATH:** `research/test_nexa_parity.py`
- **SIZE:** 22,916 bytes
- **SHA256:** `021a8a54b5a2edbb38b1e75519e23ee9a8585d0668d07de8dc29a2f9c1d56513`
- **STATUS:** CURRENT
- **PURPOSE:** Unit tests for nexa_parity.py
- **DEPENDENCIES:** nexa_parity.py
- **AUTHORITATIVE:** YES
- **STAGE:** research
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `research/test_nexa_validate.py`
- **PATH:** `research/test_nexa_validate.py`
- **SIZE:** 14,903 bytes
- **SHA256:** `7de49ae282529f0952c7b4c6196ee198bbb6066aab80f71a58a1aa52925d57cd`
- **STATUS:** CURRENT
- **PURPOSE:** Unit tests for nexa_validate.py
- **DEPENDENCIES:** nexa_validate.py
- **AUTHORITATIVE:** YES
- **STAGE:** research
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `transcripts/2026-09-17-07-03-31-nexa-mt5-ea-hardening.txt`
- **PATH:** `transcripts/2026-09-17-07-03-31-nexa-mt5-ea-hardening.txt`
- **SIZE:** 2,066,353 bytes
- **SHA256:** `19c9fdb9268c29b2db58068635147f2bfe614af1138724787b24e276022c7b40`
- **STATUS:** CURRENT
- **PURPOSE:** FULL TRANSCRIPT of the NEXA conversation up to the 2026-09-17 compaction (institutional history)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** YES (history)
- **STAGE:** history
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `transcripts/journal.txt`
- **PATH:** `transcripts/journal.txt`
- **SIZE:** 614 bytes
- **SHA256:** `8dc30251cb0590376a6910bf608b732e35bd9a32ab6fc69a030a2f28bb862b24`
- **STATUS:** CURRENT
- **PURPOSE:** Transcript journal index
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** YES (history)
- **STAGE:** history
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `uploads/NEXA_COMPLETE_RESEARCH_MASTER.md`
- **PATH:** `uploads/NEXA_COMPLETE_RESEARCH_MASTER.md`
- **SIZE:** 64,397 bytes
- **SHA256:** `dfb0438527a8fd7e944e7bb524e710d6a5e6b27431fe9c530d88f33dd7b28ded`
- **STATUS:** CURRENT
- **PURPOSE:** ORIGINAL MASTER RESEARCH SPEC supplied by the user (institutional knowledge base)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** YES (authoritative master spec)
- **STAGE:** origin
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_MALE5_Bridge.mqh`
- **PATH:** `NEXA_MALE5_Bridge.mqh`
- **SIZE:** 3,947 bytes
- **SHA256:** `40f53537f27b4aa7aa1269ed7c3c36e373a68ca6844146470de07cb0e7101ffc`
- **STATUS:** OPTIONAL
- **PURPOSE:** Opt-in MQL5-native ML bridge (MALE5). NOT included by the EA
- **DEPENDENCIES:** external MALE5 library
- **AUTHORITATIVE:** NO (not in build)
- **STAGE:** optional
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_RESEARCH_AUDIT_FULL.html`
- **PATH:** `NEXA_RESEARCH_AUDIT_FULL.html`
- **SIZE:** 153,404 bytes
- **SHA256:** `176c85a5c199fa8b2911ef40b2d1da91c530bacb3ec9cc570c75366f98340d81`
- **STATUS:** DERIVED
- **PURPOSE:** HTML render of AUDIT_FULL.md for artifact publishing
- **DEPENDENCIES:** NEXA_RESEARCH_AUDIT_FULL.md
- **AUTHORITATIVE:** NO (derived)
- **STAGE:** research
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `artifacts/63e1a823-8b69-49cb-b122-ad2d47267287/index.html`
- **PATH:** `artifacts/63e1a823-8b69-49cb-b122-ad2d47267287/index.html`
- **SIZE:** 99,521 bytes
- **SHA256:** `31f7242a49fefec6d5a00debb9ba14d7e2ff711d9012263cfe62d8578be37b46`
- **STATUS:** DERIVED
- **PURPOSE:** Published artifact render of the research audit
- **DEPENDENCIES:** NEXA_RESEARCH_AUDIT_FULL
- **AUTHORITATIVE:** NO (derived)
- **STAGE:** research
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_INTEGRATION_PLAN.md`
- **PATH:** `NEXA_INTEGRATION_PLAN.md`
- **SIZE:** 14,386 bytes
- **SHA256:** `1ffa82af59da2210d57960fbcb3eec268b2c9d573aeb58795364e175333954cd`
- **STATUS:** SUPERSEDED
- **PURPOSE:** Integration plan rev 1: 13-repo forensic analysis (superseded; retained)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO
- **STAGE:** plan history
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_INTEGRATION_PLAN_V2.md`
- **PATH:** `NEXA_INTEGRATION_PLAN_V2.md`
- **SIZE:** 15,353 bytes
- **SHA256:** `6835dad7ac17ee01319f4306ca97a55f7cd3d0d209f42fb508456496bb41ca45`
- **STATUS:** SUPERSEDED
- **PURPOSE:** Integration plan rev 2 (superseded by V3; retained)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO
- **STAGE:** plan history
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_RESEARCH_AUDIT.md`
- **PATH:** `NEXA_RESEARCH_AUDIT.md`
- **SIZE:** 28,308 bytes
- **SHA256:** `7acb9c9de32853a9aa6ea028a553549f333151b0a08f7396150bda4a3c379374`
- **STATUS:** SUPERSEDED
- **PURPOSE:** Audit Parts 1-8 (early split; 100% contained in FULL; retained)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO
- **STAGE:** research history
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_RESEARCH_AUDIT_PART2.md`
- **PATH:** `NEXA_RESEARCH_AUDIT_PART2.md`
- **SIZE:** 57,098 bytes
- **SHA256:** `60b74017257ea37b6b301c8aa365d6bf6c4b6b1478a7338579eee0401461f88a`
- **STATUS:** SUPERSEDED
- **PURPOSE:** Audit Parts 9-26 (early split; contained in FULL except its title line; retained)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO
- **STAGE:** research history
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `uploads/NEXA_INTEGRATION_PLAN.md`
- **PATH:** `uploads/NEXA_INTEGRATION_PLAN.md`
- **SIZE:** 14,386 bytes
- **SHA256:** `1ffa82af59da2210d57960fbcb3eec268b2c9d573aeb58795364e175333954cd`
- **STATUS:** DUPLICATE
- **PURPOSE:** User copy of plan rev 1 (byte-identical to outputs copy)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO (duplicate)
- **STAGE:** plan history
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `uploads/NEXA_INTEGRATION_PLAN_V2.md`
- **PATH:** `uploads/NEXA_INTEGRATION_PLAN_V2.md`
- **SIZE:** 15,353 bytes
- **SHA256:** `6835dad7ac17ee01319f4306ca97a55f7cd3d0d209f42fb508456496bb41ca45`
- **STATUS:** DUPLICATE
- **PURPOSE:** User copy of plan rev 2 (byte-identical to outputs copy)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO (duplicate)
- **STAGE:** plan history
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `uploads/Sentiment-Pips-FOMC-Complete-Visual-Guide-1.pdf`
- **PATH:** `uploads/Sentiment-Pips-FOMC-Complete-Visual-Guide-1.pdf`
- **SIZE:** 1,816,533 bytes
- **SHA256:** `d5022cb97d0ed66b4a79e2846c5e949fc0a46917d9f86d1fdd8cfa6307ddd210`
- **STATUS:** REFERENCE
- **PURPOSE:** FOMC reference guide (source for NEXA_FOMC time structure)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** reference
- **STAGE:** research input
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `uploads/1789889307902_image.png`
- **PATH:** `uploads/1789889307902_image.png`
- **SIZE:** 913,093 bytes
- **SHA256:** `ad6b418656e5991c6813088dc04e7894c1ce5d6dc01280c9066d44e97cbbb2bc`
- **STATUS:** EVIDENCE
- **PURPOSE:** Screenshot: NEXA_EA.mq5 compile 0 errors/0 warnings, MetaEditor, Wine/macOS
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** EVIDENCE (Stage 0)
- **STAGE:** S0
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `uploads/1789889624776_image.png`
- **PATH:** `uploads/1789889624776_image.png`
- **SIZE:** 929,088 bytes
- **SHA256:** `718324c7cc332fc5aa04c2137e4466d47737a8677018b539d6d4bf4b99cbac89`
- **STATUS:** EVIDENCE
- **PURPOSE:** Screenshot: NEXA_TrainingExport.mq5 compile 0 errors/0 warnings
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** EVIDENCE (Stage 0)
- **STAGE:** S0
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_BASELINE_BACKUP_20260919-124052.tar.gz`
- **PATH:** `NEXA_BASELINE_BACKUP_20260919-124052.tar.gz`
- **SIZE:** 104,385 bytes
- **SHA256:** `88376caaeecd66ad16dafa8361d9f6da5e20345dd47e3e7bee67b8b5e7ab4743`
- **STATUS:** BACKUP
- **PURPOSE:** Immutable pre-Stage-1 baseline archive
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO (baseline)
- **STAGE:** baseline
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_Advanced_Ingest.mqh`
- **PATH:** `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_Advanced_Ingest.mqh`
- **SIZE:** 5,481 bytes
- **SHA256:** `f0a49c2fcdefdbd5c8a7d3f2a3bc8d893926a95ac1d82d1a78cd12046a8ad12a`
- **STATUS:** BACKUP
- **PURPOSE:** Pre-Stage-1 baseline copy of NEXA_Advanced_Ingest.mqh
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO (baseline snapshot)
- **STAGE:** baseline
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_Common.mqh`
- **PATH:** `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_Common.mqh`
- **SIZE:** 9,370 bytes
- **SHA256:** `247112376eb16368481dc38b809ea1e13744bf276d613699b88f8787a6ccd600`
- **STATUS:** BACKUP
- **PURPOSE:** Pre-Stage-1 baseline copy of NEXA_Common.mqh
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO (baseline snapshot)
- **STAGE:** baseline
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_DEFECT_MATRIX.md`
- **PATH:** `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_DEFECT_MATRIX.md`
- **SIZE:** 9,789 bytes
- **SHA256:** `9fca6ce8061bf3c7f23c35df24f37ff504ae9e24aead693ba774dc78c8817c16`
- **STATUS:** BACKUP
- **PURPOSE:** Pre-Stage-1 baseline copy of NEXA_DEFECT_MATRIX.md
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO (baseline snapshot)
- **STAGE:** baseline
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_DealAudit.mq5`
- **PATH:** `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_DealAudit.mq5`
- **SIZE:** 2,847 bytes
- **SHA256:** `a38a9c068b360d073be5858a0f6b001198ee3764af98e20a3fea6605f084ed89`
- **STATUS:** BACKUP
- **PURPOSE:** Pre-Stage-1 baseline copy of NEXA_DealAudit.mq5
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO (baseline snapshot)
- **STAGE:** baseline
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_EA.mq5`
- **PATH:** `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_EA.mq5`
- **SIZE:** 42,291 bytes
- **SHA256:** `71885384eb8e50efba1850e235cca650b242bcaa47222fb5b43eefc75738a5eb`
- **STATUS:** BACKUP
- **PURPOSE:** Pre-Stage-1 baseline copy of NEXA_EA.mq5
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO (baseline snapshot)
- **STAGE:** baseline
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_FOMC.mqh`
- **PATH:** `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_FOMC.mqh`
- **SIZE:** 5,513 bytes
- **SHA256:** `7d47467e5d9796004cf5a56d1b26a8fe8c7385c34c489946929f74441a30694c`
- **STATUS:** BACKUP
- **PURPOSE:** Pre-Stage-1 baseline copy of NEXA_FOMC.mqh
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO (baseline snapshot)
- **STAGE:** baseline
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_Features.mqh`
- **PATH:** `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_Features.mqh`
- **SIZE:** 25,027 bytes
- **SHA256:** `6c000d332b429b5bf3a27c9684c9b30e9d4b6a08f912babbd1263ab601fe6073`
- **STATUS:** BACKUP
- **PURPOSE:** Pre-Stage-1 baseline copy of NEXA_Features.mqh
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO (baseline snapshot)
- **STAGE:** baseline
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_Intelligence.mqh`
- **PATH:** `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_Intelligence.mqh`
- **SIZE:** 14,209 bytes
- **SHA256:** `b5954689adcc0f08f9d0ddd3dff3767ea587d645a9852413385724904d216689`
- **STATUS:** BACKUP
- **PURPOSE:** Pre-Stage-1 baseline copy of NEXA_Intelligence.mqh
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO (baseline snapshot)
- **STAGE:** baseline
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_Liquidity.mqh`
- **PATH:** `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_Liquidity.mqh`
- **SIZE:** 19,446 bytes
- **SHA256:** `99b961a636296798e48e7a26d197cd493c3e55f3aa38d89d5cc9a40fb1575472`
- **STATUS:** BACKUP
- **PURPOSE:** Pre-Stage-1 baseline copy of NEXA_Liquidity.mqh
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO (baseline snapshot)
- **STAGE:** baseline
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_MALE5_Bridge.mqh`
- **PATH:** `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_MALE5_Bridge.mqh`
- **SIZE:** 3,947 bytes
- **SHA256:** `40f53537f27b4aa7aa1269ed7c3c36e373a68ca6844146470de07cb0e7101ffc`
- **STATUS:** BACKUP
- **PURPOSE:** Pre-Stage-1 baseline copy of NEXA_MALE5_Bridge.mqh
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO (baseline snapshot)
- **STAGE:** baseline
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_Microstructure.mqh`
- **PATH:** `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_Microstructure.mqh`
- **SIZE:** 3,979 bytes
- **SHA256:** `3c549add661ab388ef3e80227dc551d771ffbc3ee65264a2f875d15ea3618663`
- **STATUS:** BACKUP
- **PURPOSE:** Pre-Stage-1 baseline copy of NEXA_Microstructure.mqh
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO (baseline snapshot)
- **STAGE:** baseline
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_RESEARCH_AUDIT_FULL.md`
- **PATH:** `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_RESEARCH_AUDIT_FULL.md`
- **SIZE:** 137,597 bytes
- **SHA256:** `c0bbd5619b836d3c978c872bb1547f308c2f35804af6c4015e7ec341079e29dc`
- **STATUS:** BACKUP
- **PURPOSE:** Pre-Stage-1 baseline copy of NEXA_RESEARCH_AUDIT_FULL.md
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO (baseline snapshot)
- **STAGE:** baseline
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_Risk.mqh`
- **PATH:** `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_Risk.mqh`
- **SIZE:** 11,846 bytes
- **SHA256:** `e706d453d346100f99d06ce3bf2b62697ce544d913bba6ba8053f506115ce5ed`
- **STATUS:** BACKUP
- **PURPOSE:** Pre-Stage-1 baseline copy of NEXA_Risk.mqh
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO (baseline snapshot)
- **STAGE:** baseline
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_SpecSnapshot.mq5`
- **PATH:** `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_SpecSnapshot.mq5`
- **SIZE:** 5,571 bytes
- **SHA256:** `e04ba6984c53cef1ec238af672346b93cb45ae7f75becbbfa2e88008908ee7eb`
- **STATUS:** BACKUP
- **PURPOSE:** Pre-Stage-1 baseline copy of NEXA_SpecSnapshot.mq5
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO (baseline snapshot)
- **STAGE:** baseline
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_TickLogger.mq5`
- **PATH:** `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_TickLogger.mq5`
- **SIZE:** 2,800 bytes
- **SHA256:** `f1bd3a20d4085229a84c976fef24303714470983b42d58ec58c2f6a79862de0e`
- **STATUS:** BACKUP
- **PURPOSE:** Pre-Stage-1 baseline copy of NEXA_TickLogger.mq5
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO (baseline snapshot)
- **STAGE:** baseline
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_TrainingExport.mq5`
- **PATH:** `NEXA_BASELINE_BACKUP_20260919-124052/NEXA_TrainingExport.mq5`
- **SIZE:** 12,892 bytes
- **SHA256:** `0b812f2b538148a76c8de0b29c2571504c32a8622f5db2b3405b72e5c9fd8cc7`
- **STATUS:** BACKUP
- **PURPOSE:** Pre-Stage-1 baseline copy of NEXA_TrainingExport.mq5
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO (baseline snapshot)
- **STAGE:** baseline
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_BASELINE_BACKUP_20260919-124052_MANIFEST.sha256`
- **PATH:** `NEXA_BASELINE_BACKUP_20260919-124052_MANIFEST.sha256`
- **SIZE:** 1,377 bytes
- **SHA256:** `893b1e1d3583ecbc3d96935cf142fdf2339f183d7d63242dcd3d0d3745e5c7f1`
- **STATUS:** BACKUP
- **PURPOSE:** SHA256 manifest of the 16 baseline files
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO (baseline)
- **STAGE:** baseline
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `NEXA_BASELINE_BACKUP_20260919-124052_MANIFEST.txt`
- **PATH:** `NEXA_BASELINE_BACKUP_20260919-124052_MANIFEST.txt`
- **SIZE:** 1,377 bytes
- **SHA256:** `893b1e1d3583ecbc3d96935cf142fdf2339f183d7d63242dcd3d0d3745e5c7f1`
- **STATUS:** BACKUP
- **PURPOSE:** Same manifest, .txt for viewing (byte-identical content)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** NO (baseline)
- **STAGE:** baseline
- **CONTENT:** byte-exact in `NEXA_EXPORT_CORE.zip`

### `uploads/XAUUSD.zip`
- **PATH:** `uploads/XAUUSD.zip`
- **SIZE:** 8,082,950 bytes
- **SHA256:** `9bd01aa87ef0a5dd540c6034118e656d50c95644dda3e0e1592a884103d1ed07`
- **STATUS:** RAW_INPUT
- **PURPOSE:** Raw Axiory XAUUSD M1 archive (user upload; immutable input)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** raw input
- **STAGE:** S5 data
- **CONTENT:** **EXCLUDED** — your original upload; verify your copy against the SHA-256 above

### `uploads/XAUUSD__10_.zip`
- **PATH:** `uploads/XAUUSD__10_.zip`
- **SIZE:** 8,100,513 bytes
- **SHA256:** `967b3e5da06f1298271cbd64d79476b4d3af86c500ef2b119168522f7c672b85`
- **STATUS:** RAW_INPUT
- **PURPOSE:** Raw Axiory XAUUSD M1 archive (user upload; immutable input)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** raw input
- **STAGE:** S5 data
- **CONTENT:** **EXCLUDED** — your original upload; verify your copy against the SHA-256 above

### `uploads/XAUUSD__11_.zip`
- **PATH:** `uploads/XAUUSD__11_.zip`
- **SIZE:** 8,921,268 bytes
- **SHA256:** `1fd408d58e840e250704ed8c83534e527aa8f5ce3503bf187347b35319c92ba7`
- **STATUS:** RAW_INPUT
- **PURPOSE:** Raw Axiory XAUUSD M1 archive (user upload; immutable input)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** raw input
- **STAGE:** S5 data
- **CONTENT:** **EXCLUDED** — your original upload; verify your copy against the SHA-256 above

### `uploads/XAUUSD__12_.zip`
- **PATH:** `uploads/XAUUSD__12_.zip`
- **SIZE:** 7,061,716 bytes
- **SHA256:** `4fe00775d7657449470c5e78c5cff0bedf56682318f35af62432879097d5c200`
- **STATUS:** RAW_INPUT
- **PURPOSE:** Raw Axiory XAUUSD M1 archive (user upload; immutable input)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** raw input
- **STAGE:** S5 data
- **CONTENT:** **EXCLUDED** — your original upload; verify your copy against the SHA-256 above

### `uploads/XAUUSD__13_.zip`
- **PATH:** `uploads/XAUUSD__13_.zip`
- **SIZE:** 7,103,847 bytes
- **SHA256:** `c3e0be8476dfb9204c84795f3d6b023490f1ca58e3be1c9e8339db0d77e49e8f`
- **STATUS:** RAW_INPUT
- **PURPOSE:** Raw Axiory XAUUSD M1 archive (user upload; immutable input)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** raw input
- **STAGE:** S5 data
- **CONTENT:** **EXCLUDED** — your original upload; verify your copy against the SHA-256 above

### `uploads/XAUUSD__14_.zip`
- **PATH:** `uploads/XAUUSD__14_.zip`
- **SIZE:** 8,613,189 bytes
- **SHA256:** `e907ddfcd9e25103bc033bed9e639c8733b1cff4c6ebff2e0900f5b3dd104014`
- **STATUS:** RAW_INPUT
- **PURPOSE:** Raw Axiory XAUUSD M1 archive (user upload; immutable input)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** raw input
- **STAGE:** S5 data
- **CONTENT:** **EXCLUDED** — your original upload; verify your copy against the SHA-256 above

### `uploads/XAUUSD__15_.zip`
- **PATH:** `uploads/XAUUSD__15_.zip`
- **SIZE:** 7,422,570 bytes
- **SHA256:** `1fc01f7d4d5d7ab9576338b0f52cc2ff6f4ebcf451009bb0686258c802b90fd7`
- **STATUS:** RAW_INPUT
- **PURPOSE:** Raw Axiory XAUUSD M1 archive (user upload; immutable input)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** raw input
- **STAGE:** S5 data
- **CONTENT:** **EXCLUDED** — your original upload; verify your copy against the SHA-256 above

### `uploads/XAUUSD__16_.zip`
- **PATH:** `uploads/XAUUSD__16_.zip`
- **SIZE:** 8,087,516 bytes
- **SHA256:** `e3ec99c527f956fc8ba2e6c4daa957e0d267b9f651cae8d0351ed5d2a269a35c`
- **STATUS:** RAW_INPUT
- **PURPOSE:** Raw Axiory XAUUSD M1 archive (user upload; immutable input)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** raw input
- **STAGE:** S5 data
- **CONTENT:** **EXCLUDED** — your original upload; verify your copy against the SHA-256 above

### `uploads/XAUUSD__17_.zip`
- **PATH:** `uploads/XAUUSD__17_.zip`
- **SIZE:** 3,026,029 bytes
- **SHA256:** `21b9549720ab5ca81f9562cc3eda5b3a18bc7a76400ff1390f8f32dae69b3083`
- **STATUS:** RAW_INPUT
- **PURPOSE:** Raw Axiory XAUUSD M1 archive (user upload; immutable input)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** raw input
- **STAGE:** S5 data
- **CONTENT:** **EXCLUDED** — your original upload; verify your copy against the SHA-256 above

### `uploads/XAUUSD__1_.zip`
- **PATH:** `uploads/XAUUSD__1_.zip`
- **SIZE:** 8,101,504 bytes
- **SHA256:** `47dc49a17985a10710642df488a58b94ea8e5712793e6520345da17d66fef83a`
- **STATUS:** RAW_INPUT
- **PURPOSE:** Raw Axiory XAUUSD M1 archive (user upload; immutable input)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** raw input
- **STAGE:** S5 data
- **CONTENT:** **EXCLUDED** — your original upload; verify your copy against the SHA-256 above

### `uploads/XAUUSD__2_.zip`
- **PATH:** `uploads/XAUUSD__2_.zip`
- **SIZE:** 8,920,942 bytes
- **SHA256:** `d6dc99206d824c968d5daef804ea2e31111ec925aa1c0c92fe367aa3fd2502c4`
- **STATUS:** RAW_INPUT
- **PURPOSE:** Raw Axiory XAUUSD M1 archive (user upload; immutable input)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** raw input
- **STAGE:** S5 data
- **CONTENT:** **EXCLUDED** — your original upload; verify your copy against the SHA-256 above

### `uploads/XAUUSD__3_.zip`
- **PATH:** `uploads/XAUUSD__3_.zip`
- **SIZE:** 7,061,067 bytes
- **SHA256:** `9291c94a87ea3b679564506f6f9e6841929f3b256ec32ae2b0df21ee219bc7e6`
- **STATUS:** RAW_INPUT
- **PURPOSE:** Raw Axiory XAUUSD M1 archive (user upload; immutable input)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** raw input
- **STAGE:** S5 data
- **CONTENT:** **EXCLUDED** — your original upload; verify your copy against the SHA-256 above

### `uploads/XAUUSD__4_.zip`
- **PATH:** `uploads/XAUUSD__4_.zip`
- **SIZE:** 7,105,243 bytes
- **SHA256:** `39da2ebc941471859346777bf9f55d5c59960099e6e10c08a51b25e5c1d2732c`
- **STATUS:** RAW_INPUT
- **PURPOSE:** Raw Axiory XAUUSD M1 archive (user upload; immutable input)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** raw input
- **STAGE:** S5 data
- **CONTENT:** **EXCLUDED** — your original upload; verify your copy against the SHA-256 above

### `uploads/XAUUSD__5_.zip`
- **PATH:** `uploads/XAUUSD__5_.zip`
- **SIZE:** 8,614,114 bytes
- **SHA256:** `8cb440c27dfd642004e3e6531476f257328687f2bd262fbff17196ebc447dfe9`
- **STATUS:** RAW_INPUT
- **PURPOSE:** Raw Axiory XAUUSD M1 archive (user upload; immutable input)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** raw input
- **STAGE:** S5 data
- **CONTENT:** **EXCLUDED** — your original upload; verify your copy against the SHA-256 above

### `uploads/XAUUSD__6_.zip`
- **PATH:** `uploads/XAUUSD__6_.zip`
- **SIZE:** 7,422,110 bytes
- **SHA256:** `0c7771bee3e36ae79ee95472ef21eea1a722adcb14f4b0f62555f862544e8b60`
- **STATUS:** RAW_INPUT
- **PURPOSE:** Raw Axiory XAUUSD M1 archive (user upload; immutable input)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** raw input
- **STAGE:** S5 data
- **CONTENT:** **EXCLUDED** — your original upload; verify your copy against the SHA-256 above

### `uploads/XAUUSD__7_.zip`
- **PATH:** `uploads/XAUUSD__7_.zip`
- **SIZE:** 8,080,030 bytes
- **SHA256:** `cab4d5c020d4b7e9c85b0e16581b22e499b8039f41af2b822fbf85bfd858c725`
- **STATUS:** RAW_INPUT
- **PURPOSE:** Raw Axiory XAUUSD M1 archive (user upload; immutable input)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** raw input
- **STAGE:** S5 data
- **CONTENT:** **EXCLUDED** — your original upload; verify your copy against the SHA-256 above

### `uploads/XAUUSD__8_.zip`
- **PATH:** `uploads/XAUUSD__8_.zip`
- **SIZE:** 3,025,403 bytes
- **SHA256:** `a23daad54a6605b60e991182eaf2d23750334102f467a2319229b28b61d16832`
- **STATUS:** RAW_INPUT
- **PURPOSE:** Raw Axiory XAUUSD M1 archive (user upload; immutable input)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** raw input
- **STAGE:** S5 data
- **CONTENT:** **EXCLUDED** — your original upload; verify your copy against the SHA-256 above

### `uploads/XAUUSD__9_.zip`
- **PATH:** `uploads/XAUUSD__9_.zip`
- **SIZE:** 8,082,173 bytes
- **SHA256:** `9f2afab649a6d8e82566ca4a72dcfa9b354861bb43205acf821d2d90b5949c66`
- **STATUS:** RAW_INPUT
- **PURPOSE:** Raw Axiory XAUUSD M1 archive (user upload; immutable input)
- **DEPENDENCIES:** -
- **AUTHORITATIVE:** raw input
- **STAGE:** S5 data
- **CONTENT:** **EXCLUDED** — your original upload; verify your copy against the SHA-256 above
