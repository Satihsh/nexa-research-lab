# NEXA RESEARCH KNOWLEDGE BASE (master document)

**Phase:** complete research-corpus deep-learning phase. **Knowledge acquisition only.**
- No strategy is proposed, promoted or deployed.
- Nothing in this file claims profitability.

**Built:** 2026-10-01 (batch 1, 26 files) and 2026-10-02 (batch 2, 13 files).

**Binding constraints respected:**
- no change to NEXA production code, NEXA_Risk.mqh, V2, the frozen 8E campaign or any frozen protocol;
- no deployment, no trading, no live connection, no promotion.

---

## 0. How to navigate

| File | Purpose |
|---|---|
| `CORPUS_MANIFEST.json` | 39 files: sizes, SHA-256, pages, extraction stats, visual pages, classification, processing status |
| `_PROCESSING_LOG.md` | Per-file processing status (all 39 DONE; file 37 = duplicate of 06) |
| `sources/S01…S39_*.md` | Per-source study notes: equations, page references, critique, NEXA links |
| `SOURCE_MAP.md` | Classification by source type and evidence status; domains; author clusters; page index |
| `EVIDENCE_MAP.md` | Principles ranked by evidence and independent lines; agreement matrix; use/test/avoid |
| `MATHEMATICAL_KNOWLEDGE_BASE.md` | Every important equation with variables, intuition, assumptions, failure conditions, verification |
| `STATISTICAL_KNOWLEDGE_BASE.md` | Validation, look-ahead traps (L1–L15), inference, costs, overfitting, regimes, metrics, nulls |
| `CONTRADICTIONS.md` | 17 cross-source, 22 within-source and 5 corpus-vs-NEXA contradictions, both sides preserved |
| `FAILED_IDEAS.md` | 26 failed/contradicted results; unsupported claims; ≥ 26 formula errors; failure patterns; do-not-use list |
| `NEXA_KNOWLEDGE_GRAPH.json` | 157 nodes / 397 typed edges (sources, clusters, principles, methods, failures, hypotheses, NEXA components) |
| `RESEARCH_HYPOTHESIS_BACKLOG.md` | 40 hypotheses, each with the 13 required fields; prioritised |

**Tags used throughout:**
- **SOURCE** = stated in a source.
- **INFERENCE** = our reasoning or derivation.
- **HYPOTHESIS** = untested proposal.
- **UNKNOWN** = cannot be determined from the corpus.

---

## 1. Corpus overview

**Files and size**
- **39 PDF files, 92.37 MB** (decimal; 88.09 MiB). Batch 1: 26 files (~70.5 MB). Batch 2: 13 files (21.90 MB).
- **38 distinct works.** `ssrn-5080700.pdf` (S37) is the same paper as S06:
  - text identical;
  - all 48 pages pixel-identical at 400 px;
  - only the PDF wrapper/hash differs.
- `.DS_Store` ignored.

**Source types** (distinct works)

| Source type | Count |
|---|---|
| Oxford/university research | 12 (incl. the Oxford University Press textbook S32) |
| Academic theses, non-Oxford | 4 |
| Other academic institutions | 11 (7 peer-reviewed journal articles) |
| External research | 3 (S05 non-market, S39 IMF, S30 journalism) |
| Industry/practitioner | 8 |
| **User research** | **0** |
| Unknown provenance | 0 |

**Evidence status (primary, by source)**
- **Established / strongly supported content:** S04 (theory), S06, S10, S11 (theory), S15 (scaling), S21 (principle), S22 (maths), S23, S24 (theory), S26, S27 (maths), S32 (textbook principles).
- **Research findings:** S02, S03, S13, S14, S25, S29, S34, S38, S39.
- **Unverified claims:** S01, S05, S07, S08, S09, S16, S17, S19, S20, S28, S30, S31.
- **Failed / flawed:** S33, S35, S36 (and specific results elsewhere; FAILED_IDEAS §A).

**Processing completeness:** every file was opened and its full text read.
- Key equation, figure and low-text pages were rendered and inspected.
- Low-text pages were pixel-tested; blank pages were confirmed blank.
- Image-only appendices were read visually (S21 App. A–D).

**File-content caveat (not a processing gap): S32** (Harris, *Trading and Exchanges*, draft) holds only:
- Chapter 1 in full;
- the opening ≈ 2–4 pages of Chapters 2–29;
- a partial bibliography.

The file was processed completely. **The rest of the book is not in the corpus** and must not be cited as read.

---

## 2. What the corpus establishes (core knowledge for NEXA)

Ranked by evidence; details and references in EVIDENCE_MAP §1.

1. **Costs decide outcomes** (P1, strongly supported).
   - Published edges are cost-fragile: ML momentum dies at 2–4 bps (S02); a microstructure forecaster dies at 0.06 bp vs a 0.5 bp spread (S13); lead-lag Sharpe 2.4 → 0 at ≈ 7 bp (S14).
   - Costs include **missed-trade opportunity cost** (S32 Ch. 21; S10).
   - *For NEXA:* any idea must survive a cost curve and an expected-move-vs-cost gate.
2. **Volatility is forecastable; direction mostly is not** (P2, P5, P11).
   - HAR/GARCH-type log-variance models are hard baselines (S23, S39).
   - Volatility is rough/persistent (S04, S18) and FX scales super-diffusively (S15).
   - Public-data direction prediction is near chance (S26 54 %; S35 ≈ 50 %; S02 hit ≈ 50 %).
3. **Slow resting orders are adversely selected; quotes are options** (P3).
   - S06: retail spread-improving orders sniped 62.58 % of the time within ≈ 91 µs.
   - S10: misses are adversely selected.
   - S11: spread is a strangle written to latency arbitrageurs.
   - S29/S27: exposure vs priority.
   - S32: free option; zero-sum.
   - S31/S30: practitioner corroboration.
4. **Execution degrades exactly when it matters** (P10, P14).
   - News: slippage probability ×4 and size ×6 (S10).
   - Liquidity withdraws in stress (S30 flash crash; S31 March 2020).
   - Stops fill through levels; no gap insurance (S01).
   - Stop and margin cascades (S32 Ch. 28).
5. **Validation failures are the norm in this corpus** (P6, P7, P8). Across 38 works:
   - **no source applies a multiple-testing correction to its own best result**;
   - holdouts are contaminated (S33);
   - adaptive parameters are booked as P&L (S36);
   - delay-0 is "borderline in-sample" (S22);
   - MA-detrending manufactures reversion (S15);
   - normalisation creates artefacts (S38).
6. **Exits cannot create edge without drift** (P13; MATH M1b, INFERENCE from S27's first-passage maths).
   - Under a driftless diffusion, P(target first) = L/(U + L), which equals the break-even win rate. Hit rate is a payoff-shape statistic, not skill (S08 87.5 % hit with 0.29 win/loss).
7. **Edges decay and depend on regime** (P12).
   - FX TSMOM negative 2011–19 (S03).
   - Lead-lag identities decay within months (S14).
   - Rediscovery ruins edges (S21).
   - "Strategies die" (S22).
   - Market-structure changes rewrite the game (S30, S32).
8. **Information lives in data NEXA does not have** (P11).
   - Depth volumes, trade signs, member/algo IDs, second synchronous feeds (S06, S13, S25, S26, S29, S34).
   - All imbalance/microprice results are **DATA-LIMITED** for NEXA.

---

## 3. Market-structure knowledge relevant to a retail CFD trader (NEXA at Pepperstone)

| Topic | Knowledge | Sources | Status |
|---|---|---|---|
| Who NEXA trades against | An OTC dealer/internaliser; NEXA is a small, slow, uninformed-by-default liquidity taker | S32 Ch. 13, 25; S30 (payment for order flow, internalisation); S11 | Established (structure) / INFERENCE (application) |
| Spread | Covers dealer costs + adverse selection; ∝ σ × toxic share; discrete states at coarse ticks | S11, S32 Ch. 14, S24, S10 | Established |
| Last look / requotes | Rejections cluster after favourable moves; can tighten average spreads but leak information | S11, S31, S30 | Theory + practitioner |
| News and opens | Slippage tails grow; spreads balloon; gaps; flat during news is a common professional rule | S10, S01, S31 | Strongly supported (CLOB) / practitioner |
| Fixes and scheduled flows | WMR 4 pm, LBMA gold, Tokyo fix, month/quarter-end hedge rolls are predictable flows | S31, S01, S32 Ch. 11 | Unverified / mechanism |
| Sessions and time | Diurnal volatility; session-dependent premia; time conventions must use UTC + DST | S23, S14, S01 App. D; NEXA time memory | Supported |
| Benchmarks for costs | Arrival mid from an independent reference; include misses | S32 Ch. 21, S31 (BestX, NCFX, Sancetta) | Established principle |
| Stress | Fine-scale volatility rises disproportionately; liquidity withdraws | S31 (HSBC), S30, S32 Ch. 28 | Supported |

---

## 4. Volatility knowledge

- **Stylised facts (established):** clustering (β ≈ 0.99, S39); fat tails (ν ≈ 8.5, S39; S18; S35); smile/skew in options (S04, S18); diurnal reverse-J (S23); commonality (S23).
- **Roughness:** log-volatility increments behave like fBm with H ≈ 0.07–0.14 in equity indices (S04). *Mechanism disputed* vs long memory (CONTRADICTIONS A7); forecasting implications agree.
- **Scaling:** FX mean absolute return ∝ Δt^{0.56–0.58} (S15). Use it, not √Δt, when transferring volatility across horizons (hypothesis to verify).
- **Sampling interval:** measured variance depends on bar size when returns are autocorrelated. VR < 1 with bounce (S38, S32), > 1 with trend. Stress lowers the long/short volatility ratio (S31).
- **Evaluation:** QLIKE + DM (S23); PIT + log score + Diks + coverage tests (S39 + INFERENCE).
- **Estimation hygiene:** weekend handling ±20–25 % in σ̂ (S15); OU α̂ badly biased on short samples (S15); daily RV biases H upward (S04).

---

## 5. Indicator redundancy (taxonomy)

Most named indicators in the corpus are transforms of five statistics (MATH §L1; EVIDENCE_MAP §6):

| Underlying statistic | Indicators |
|---|---|
| **Net change** | Trend sign, TSMOM, MOMP, momentum histogram, MACD-family |
| **Deviation from a moving average** | %b, bands, z-score, Keltner, LMA/SMA, OLMAR |
| **Range / volatility state** | ATR, BandWidth, squeeze, DM/V's V, RV |
| **Up/down ratio** | RSI, TDI |
| **Depth imbalance** | I₀, B, W(i), log-imbalance, microprice; all need depth data |

**INFERENCE:** testing many indicators from one family is one hypothesis tested many times. Count families, not names, in multiple-testing corrections.

**Path efficiency** (Kaufman ER = |DM|/V) and **bar overlap** are a distinct family: trend vs chop.

---

## 6. Direction prediction: what the corpus says

| Claim | Evidence |
|---|---|
| Daily/intraday price direction from public bar data | Weak to none: S26 (54 % for algo direction), S35 (≈ 50 %), S02/S03 (hit ≈ 50–54 %; edge from payoff ratio, not accuracy), S32 Ch. 10 (fundamental values follow a random walk) |
| Order-flow / depth direction at seconds or event horizon | Real but short-lived: S34 (AUC 0.72), S29 (3–30 s), S13 (< 10 events), S26 (with IDs) |
| Trend following at monthly-plus horizons | Regime-dependent: S02 positive 1995–2015; S03 FX negative 2011–19; S15 E > 0.5 but small |
| Practitioner patterns (TD, squeeze, GSCS, BTMM, outside bar, sessions) | Unverified; NEXA's own DEV results so far: UNPROVEN or CONTRADICTED (prior facts) |

---

## 7. Validation rules for any future NEXA research (condensed from STAT KB)

1. **Freeze the holdout** and never consult it during search (S33). NEXA V2's 2027 prospective OOS is the model.
2. **Count every candidate.** Report deflated Sharpe / PBO (H-SEARCH-DEFLATE).
3. **Execution realism:**
   - delay-1 next-bar-open plus spread (H-DELAY-PARITY);
   - stress slippage scenarios;
   - stops filled through levels.
4. **Cost curve** for every result; costs inside any learning objective.
5. **Nulls:**
   - random walk / OU for MA-relative signals;
   - random-entry with identical exits;
   - driftless two-barrier for TP/SL;
   - naive no-change for level forecasts;
   - GARCH(1,1) for densities;
   - majority class for classifiers;
   - blinded features (H-ABLATE).
6. **Causality:**
   - one-sided filters only;
   - causal Kalman innovations;
   - no overlapping targets;
   - lagged regressors;
   - UTC with DST.
7. **Inference:**
   - HAC for overlapping samples;
   - SE for mean differences;
   - coverage tests for quantile rules;
   - calibration with AUC.
8. **Per-regime and per-session reporting**, with block dispersion (S02's ±2.08 is the honest number).
9. **Simple baselines first.**
10. **Operational envelope** for any engine (S31): act only within tested states; kill switch on deviation.

---

## 8. Key mathematical discoveries and verifications (this phase)

**Verified correct**
- Last-look strangle and balancing equation (S11).
- Optimal discretion δ* = α (S10).
- Avalanche formula (S21).
- Hedge bound E(G) ≥ 0.2E (S21).
- Kassouf z = 2.441 (S21).
- OU mean absolute return; business-time σ inflation √(168/108) (S15).
- Barbell convexity; TSMOM = diagonal mean–variance (S22).
- GBM first-passage law (S27).
- Kalman recursions (S36).
- Latency arithmetic (13.3 ms Chicago–NJ fibre; 350 µs coil) (S30).
- Sharpe checks in S14.

**Our derivations (INFERENCE)**
- The Lévy area equals the antisymmetrised lag-1 cross-covariance and is blind to lags ≥ 2 (S14).
- MA-detrended OU: α̂ ∝ 1/window for any random walk (S15).
- Driftless two-barrier probability = break-even win rate (MATH M1b).
- The S38 Prop 1 artefact and the true intervalling kernel.
- The correct Kalman spread P&L with fixed-at-entry hedge ratios (S36).
- S33's expected best-of-K Sharpe ≈ 5.1 SE.

**Errors found:** ≥ 26 mathematical/formula errors in 10 sources, plus ≥ 15 table/label inconsistencies (FAILED_IDEAS §C).

---

## 9. Agreements, contradictions, failures (pointers)

**Strong cross-cluster agreements:** costs dominate; volatility forecastable; adverse selection of resting orders; simple baselines; selection bias; edge decay; fat tails (EVIDENCE_MAP §2).

**Main contradictions (preserved):**
- HFT liquidity vs tax;
- last look helps vs hurts;
- MA mean reversion real vs artefact;
- trend alive vs dead;
- public LOB predictability;
- roughness vs long memory;
- speed value.

See CONTRADICTIONS.md.

**Failed ideas:** GA "OOS" (S33); Q-model direction (S35); Kalman stat-arb (S36); MC-as-proof (S16); OPS wealth (S12); S38 Prop 1; nonlinear Lévy claim; rBergomi/ACF errors (S18); and others (FAILED_IDEAS §A).

---

## 10. Data gaps for NEXA

| Gap | Blocks |
|---|---|
| Depth volumes, trade signs, member/algo IDs | All imbalance/microprice/OFI work (S06, S13, S26, S29, S34) |
| Live/demo fill, requote, rejection and stop-slippage logs | H-NEWS-SLIP, H-STOP-SLIP, H-LASTLOOK-REJECT, H-DEVIATION-OPT |
| Long tick history (only ~21 days) | H-SPREAD-REGIME |
| Second synchronous price-forming feed (e.g. COMEX) | Cross-feed lead-lag (S25; V2 BLOCKED) |
| Historical swap/rate series | H-CARRY-SWAP |
| News consensus/surprise values with corrected timestamps | H-NEWS-PTD (partly) |
| An XAU-specific or FX intraday volatility study in the corpus | All volatility transfer is HYPOTHESIS until NEXA tests it |
| The full Harris textbook (only openings present) | Detailed spread models, liquidity measures, circuit-breaker analysis |

---

## 11. What NEXA should and should not use

**Use** (principles/methods; no edge implied):
- cost curves and the E_eff gate;
- delay-parity tests;
- candidate counting with DSR/PBO;
- noise bands;
- random-walk/OU, driftless-barrier and random-entry nulls;
- HAR/QLIKE/DM and PIT/coverage for any volatility or risk model;
- UTC/DST discipline;
- weekend-gap conventions documented;
- the operational-envelope governance;
- causal filters only;
- information ablation.

**Test** (hypotheses): see the RESEARCH_HYPOTHESIS_BACKLOG priority order.
- Method gates and the volatility/risk layer come first.
- Execution realism follows once logging is approved.
- Regime and session descriptors after that.
- Low-prior patterns last.

**Do not use:** FAILED_IDEAS §E (14 items) and §F (data/cost-limited for NEXA).

---

## 12. Future directions (research sequencing, not strategies)

1. Apply the **method gates** retrospectively to NEXA's existing research artefacts:
   - H-DELAY-PARITY;
   - H-COST-SHRINK;
   - H-SEARCH-DEFLATE;
   - H-NOISE-OBJ;
   - H-HIT-PROB;
   - H-ABLATE.
   Research copies only; frozen code untouched.
2. Build the **volatility/risk layer** evidence for XAU/FX:
   - H-VOL-1..4;
   - H-ROUGH-1;
   - H-VR-SCALE;
   - H-GAP-VOL;
   - H-VAR-TRIGGER;
   - H-TAIL-SIM.
   This layer has the strongest prior and needs only data NEXA holds.
3. When forward/demo testing is separately approved, **log execution** (requested vs filled prices, retcodes, timestamps) to enable H-NEWS-SLIP, H-STOP-SLIP, H-LASTLOOK-REJECT and H-DEVIATION-OPT.
4. Run **regime/session descriptors** (H-HURST-GATE, H-THICKNESS-ER, H-TSMOM-TANH, H-SESSION-SPLIT, H-FIX-FLOW) as conditioning studies on existing frozen engines' trades. Description first; prospective confirmation before any use.
5. Only then consider **low-prior pattern hypotheses** inside a deflated, frozen multi-test protocol.
6. Keep **DATA-LIMITED** items on file until data exist.

---

## 13. Completion audit (14 questions)

| # | Question | Answer |
|---|---|---|
| 1 | All files found? | **Yes.** 39 PDFs (26 batch 1 + 13 batch 2), 92.37 MB, matching the expected 26 + 13 and ≈ 70.5 + 21.9 MB. `.DS_Store` ignored. |
| 2 | Every file opened/read? | **Yes.** Full text read for all 39: 2,672 pages, ≈ 5.55 million extracted characters (per-file counts in the manifest). |
| 3 | Every file successfully processed? | **Yes.** All 39 rows DONE in `_PROCESSING_LOG.md`. File 37 is processed as a verified duplicate of file 06. |
| 4 | Any partially unreadable? | **No unreadable files.** Limitations recorded honestly:<br>• text extraction garbled display maths in several PDFs, so those pages were rendered and read visually (S02, S04, S21, S25, S27, S36, S38 and others);<br>• S21 App. A–D are image-only and were read visually;<br>• some figure-only pages were interpreted from captions;<br>• **S32's file contains only chapter openings** (a file-content limitation, not a read failure). |
| 5 | Math sections studied? | **Yes**, including appendices and proofs, e.g. S10 App. A–C, S11 App. A, S14 App. A.3, S24 App. A–G, S27 App. A, S29 Props/Lemma, S21 App. A–D, S38 App. A–B. |
| 6 | Equations and quantitative methods extracted? | **Yes.** MATHEMATICAL_KNOWLEDGE_BASE §A–M; per-source notes. |
| 7 | Tables/figures inspected where necessary? | **Yes.**<br>• Rendered pages are listed per source in the manifest (`visually_inspected_pages`).<br>• Contact sheets were used for low-text pages (S01, S31).<br>• Blank pages were pixel-tested (S32, S30, S37 vs S06). |
| 8 | All sources classified? | **Yes.** Source type and evidence status are separate axes, for all 39 files / 38 works (SOURCE_MAP, manifest). |
| 9 | Contradictions identified? | **Yes.** 17 cross-source, 22 within-source and 5 corpus-vs-NEXA (CONTRADICTIONS.md). |
| 10 | Failed/unsupported claims identified? | **Yes.** 26 failed/contradicted results, unsupported claims by source, ≥ 26 formula errors and ≥ 15 inconsistencies (FAILED_IDEAS.md). |
| 11 | Cross-source relationships identified? | **Yes.** Clusters, lineages, the duplicate, the agreement matrix and the knowledge graph (157 nodes, 397 edges). |
| 12 | NEXA knowledge base created? | **Yes.** This file plus the 10 required files. |
| 13 | Math and stat knowledge bases created? | **Yes.** Both updated for all 39 files; the earlier error-count statement was corrected. |
| 14 | Future hypotheses documented? | **Yes.** 40 hypotheses, each with the 13 required fields, prioritised (RESEARCH_HYPOTHESIS_BACKLOG.md). |

**Completion status:** all 39 files processed. Knowledge base complete for the current corpus.
