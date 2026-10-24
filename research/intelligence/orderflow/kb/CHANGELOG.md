# KB CHANGELOG

## 2026-10-11 — Core strategy spec v3 (draft for confirmation)
- `../CORE_STRATEGY_SPEC.md`: GEX and option flow excluded; ORB → IVB made a separate strategy (user).
- Resolved from notes and sources: VA 70 %, context = price inside value, 1-min candle-close trigger, seller bubble, absorption = no close below the bubble (CL-024), entry at the trigger close (CL-042), stop below the bubble, TP VAH, Setup B trigger = close below bubble + VAL, target = nearest LVN below VAL, strict checklist.
- 12 essential decisions remain (E1–E12).

## 2026-10-11 — Original-method spec v2 (draft for approval)
- `../ORIGINAL_METHOD_SPEC.md` v2 adds 10 concept cards (Volume Profile, Delta Profile, VAH/VAL, LVN, Big Trades, Order Flow, Option Flow, GEX, ORB, IVB). Each card has a definition, role, setup, entry/exit, data, connections, NEXA status and evidence, labelled VERIFIED / PRESENTER / NEXA-RESULT / INTERP / UNRESOLVED.
- Adds a 7-stage process map (context → location → response → order flow → decision → risk → execution) and the presenter chains (Andrea Cimi is the only chain combining GEX + VA + LVN + order flow + IVB + walls).
- Adds the Big Trades original vs volume-only proxy separation (`OF-03-ORIG` vs `OF-03P`) and decisions D27–D32.

## 2026-10-11 — Original-method reconstruction (draft for approval)
- `../ORIGINAL_METHOD_SPEC.md`: the 5-stage process plus Setups A (bubble-reclaim long near VAL → VAH), B (bubble + VAL break short → LVN) and C (ORB → IVB), reconstructed from NOTE-001, the YT-001 whiteboard/audio, DOC-001 and related claims.
- Every element is source-labelled. 26 open decisions (D1–D26) are listed instead of invented rules.
- Reproducibility matrix: the core "big trade for sellers" condition is NOT reproducible without CME aggressor-side trades; proxy track possible on XAU/EUR/JPY.
- C3 and unrelated strategy research are paused (user).

## 2026-10-11 — C2 TSMOM tested
- REJECTED (pooled net −0.19 %/mo; all 16 cells negative). The points-swap snapshot dominates the result; ex-swap +0.12 %/mo is n.s. New GAP-M03 (swap scaling). See `validation/C2_REPORT.md`.

## 2026-10-11 — C1 Tokyo-fix tested
- SRC-LIT-002 and CL-086 added. Gross effect confirmed post-publication; not tradable at retail cost (net −0.58 bp at S1). Formal verdict INCONCLUSIVE. The exploratory post-fix short-leg observation needs a new ID plus prospective data.

## 2026-10-11 — Strategy-candidate ranking
- `validation/STRATEGY_CANDIDATE_RANKING.md` (9 candidates ranked; V2 duplicates, blocked and failed families preserved). Strongest testable: C1 Tokyo-fix/gotobi USDJPY (draft spec `validation/DRAFT_PREREG_C1_TOKYO_FIX.md`, not hashed, not run).

## 2026-10-11 — Transcript access rule (option A)
- YouTube 429 diagnosed (`../tools/YT_RATE_LIMIT_DIAGNOSIS.md`). Transcripts are fetched only via the guard (persistent cooldown, exponential backoff, budget); the MCP is used for metadata only. The guarded watcher is queued for 17 videos (Q-09 + Q-12); cooldown until 11:52.

## 2026-10-11 — Batch 3: GEX formula and evidence, GEX code, trading-bot videos, finance MCP servers
- **Registered:** SRC-CH-003, SRC-YT-024…029, SRC-DOC-006/007/008, SRC-CODE-001…006.
  - YouTube transcripts are still blocked (429). The videos are at META + chapters depth; queue Q-12.
  - Scribd is behind a login wall (Q-14).
- **Claims:** CL-072…CL-085 (section F), with a new evidence class `CODE-REVIEW`.
- **Most important finding:** FlashAlpha's disclosed 8-year SPY backtest (CL-075). GEX tracks next-day realised vol raw, but adds **nothing significant beyond VIX + ATM IV**. External evidence against an incremental GEX edge; the OF-24 prior is lowered and the design must control for IV and HAR.
- **Code reviews:**
  - GammaGEX has unit and sign errors and silent defaults (CL-077).
  - The Scorsone DataBento script is a 3-week, cost-free backtest, so not evidence (CL-078).
  - The MetaTrader MCP server is unsafe for NEXA: auto-execution, password in argv, unauthenticated 0.0.0.0, no SL (CL-080) ⇒ REJECT.
- **Data lead:** DataBento `GLBX.MDP3` confirmed for CME trades with aggressor side and book (CL-079). It is a candidate for GAP-D01/D02/D08; OI coverage is unverified; **no credits used; approval needed**.
- **New files:** `TOOLING_EVALUATIONS.md` (verdict table plus an integration safety checklist); CONCEPTS K-13.
- No installs, no executions, no data collected, no production change.

## 2026-10-11 — Batch 2: Bookmap, MenthorQ, NinjaTrader, Doug Pless streams, Real Deal Futures playlist
- **Registered:**
  - SRC-DOC-002 (Bookmap), SRC-DOC-003/004 (MenthorQ site, models, Academy; self-ranking GEX guide), SRC-DOC-005 (NinjaTrader Order Flow+ docs);
  - SRC-YT-015/016/017 (Doug Pless × Bookmap streams; same series as YT-003);
  - SRC-PL-001 plus SRC-YT-018–023 (Real Deal Futures "Order Flow Series", 6 videos).
- **Duplicate skipped:** `7WVX5Y5Mfjk` = SRC-YT-007.
- **Transcripts unavailable:** YouTube returned HTTP 429 (IP rate limit) via the MCP and the browser. All 9 videos are at META + chapters depth; queued as Q-09 with a priority order. No claims were taken from video speech.
- **Claims:** CL-048…CL-066 (new section E), tagged with the new evidence classes (README).
- **Key verified facts:**
  - NinjaTrader imbalance default 1.5 / min delta 10, with no stacked-imbalance definition;
  - **bid/ask delta unsupported on spot FX** ⇒ Pepperstone-quote "delta" is not order flow.
- **Key vendor claims:**
  - MenthorQ native gamma levels for **GC and 6E/6B/6J** and FX key levels incl. XAU (methodology undisclosed; EOD only; contradicts its own GLD advice);
  - Bookmap "100 %" native-iceberg detection.
- **Concepts:** K-04/05/06/07/08 appended; new K-12 (order book / heatmap / MBO-MBP), NEXA = NO.
- **Hypotheses:** OF-24 (gold GEX regime), OF-25 (currency-futures gamma levels), both BLOCKED by data (GAP-D08). OF-26 reclassifies proxy delta.
- **Gaps:** GAP-K02 updated (no standard ⇒ untestable as a claim); new GAP-K09, GAP-K10, GAP-D08, Q-09, Q-10, Q-11.
- **Follow-up reads (same day):** MenthorQ Put Support, 1D expected move, intraday vs EOD and futures-options lessons; NinjaTrader Trade Detector and Volume Profile.
  - Claims CL-067…CL-071 added.
  - **Notable:** MenthorQ's 85–87 % expected-move containment = calibration, not edge (NEXA analysis).
  - NinjaTrader VA default 68 % documents the α disagreement.
  - Futures/FX gamma levels are EOD-only.
- Narrative summary: `../BATCH2_SOURCE_STUDY.md`. Housekeeping: IDs **CL-019 and CL-039 were never assigned** (earlier session); the register holds 69 claims (CL-001…CL-071 minus those two).
- No data collected, no tests run, no production change.

## 2026-10-11 — Trend→balance line CLOSED (user)
- OF-20/OF-20b closed; prospective confirmation not started. CL-009 stays INCONCLUSIVE; GAP-K04 closed as not pursued.

## 2026-10-11 — OF-20b implemented and run (user-approved; RETROSPECTIVE, semi-blind)
- `validation/OF20b_RESULTS_REPORT.md`; G1 tests 10/10; code hashed before discovery; no deviations.
- CL-009 retro INCONCLUSIVE: GBPUSD REJECTED; XAU/EUR/JPY INSUFFICIENT-N (71/80/97 trend days). EURUSD +0.10 in all splits (p_perm 0.036, CI touches 0) is the only lead.
- HYP-013 measured: P(trend day) 3.3–4.3 % under the normalised codification (vs 10–30 % claimed for ES-type RTH). No trend persistence. HYP-010 undetermined / ≈ base rate.
- GAP-K08 partly closed; GAP-K04 open. Prospective confirmation needs ~3 y of data (approval required).

## 2026-10-11 — OF-20b pre-registered (user-approved)
- `validation/PREREG_OF20b_TREND_BALANCE_NORMALISED.md`, hashed, read-only. Keeps EQ-016/017/018 thresholds unchanged and normalises time: every session cut into 13 equal periods (the S46 pit-session count), IB = first 2/13. Variant A (30-min periods, threshold scaled 2/11 of possible sign changes) counted.
- Disclosed as semi-blind (OF-20 outcome-adjacent rates already seen on the same data) ⇒ historical verdict capped at RETROSPECTIVE/G3; G4 needs prospective confirmation (≥100 pooled trend-day pairs from 2026-10-12; data acquisition and 2027 data need approval).
- Not implemented or run.

## 2026-10-11 — OF-16 / OF-19 / OF-20 implemented and run (user-approved)
- Results: `validation/OF_RESULTS_REPORT.md`; JSON/logs hashed in `validation/RESULTS_MANIFEST.txt`; code hashed before discovery in `PREREG_HASHES.txt`; G1 tests 9/9 PASS.
- OF-16 INCONCLUSIVE (EUR REJECTED; XAU, JPY CIs span 0; volume adds nothing over a range-based pseudo-VA). CL-005's 70–80 % REFUTED (H 0.48–0.53, 4/4).
- OF-19-P REJECTED 4/4 (accepted small-IB breaks ≈ driftless law; small IB travels *less* on XAU/JPY). OF-19-T INSUFFICIENT-N, net R negative every split, = random-entry null.
- OF-20: trend-day codification ~never fires on FX/XAU sessions (n_TD 33/2/2/0) ⇒ CL-009 INSUFFICIENT-N; new GAP-K08. CL-031's ≈10 % REFUTED (0.45–0.52, 4/4). Contradiction unresolved.
- Statuses updated: CL-003 CONTRADICTED, CL-004 INCONCLUSIVE, CL-005 CONTRADICTED (figure), CL-009 INCONCLUSIVE, CL-031 CONTRADICTED.
- Deviation OF-D1 (robustness-only crash fix) and reporting correction RC-1 disclosed. No production change; no data collected.

## 2026-10-11 — OF-16 / OF-19 / OF-20 pre-registered (user-approved)
- Files: `validation/PREREG_OF_COMMON.md`, `PREREG_OF16_OPEN_LOCATION.md`, `PREREG_OF19_RELATIVE_IB.md`, `PREREG_OF20_TREND_BALANCE.md`; SHA-256 in `validation/PREREG_HASHES.txt` (recorded 2026-10-10T19:54:33Z); files set read-only.
- Claims CL-003/004/005/009/031 linked to their pre-registration (status unchanged — TESTABLE until a result exists).
- Key design choices declared as NEXA's (sources give none): IB lookback N=20, acceptance m=30 min, balance-day rule (ROT≥3, CL 0.25–0.75), expansion day = top-quintile R/σ̂; each with counted sensitivity cells.
- Drift-matched base rates and geometry/placebo nulls are primary comparisons; raw 50 % never decides.
- GBPUSD excluded from profile-based verdicts (T1 proxy rejected); counts in price-only OF-19/OF-20.
- **No outcome computed; no code written yet (G1 implementation + synthetic unit test pending); no data collected.**

## 2026-10-11 — KB created
- **Sources registered:** NOTE-001, YT-001, DOC-001 (from earlier same-day studies); YT-002…YT-007 (full transcripts), YT-008 (metadata only — no captions), SMB Capital and Axia Futures channels (30-video lists each), YT-009/010 (SMB, full), YT-011…014 (Axia, full). Duplicate `evBNCCVPDxI` registered once.
- **Claims:** CL-001…CL-047 (paraphrased, timestamped).
- **Concepts:** K-01…K-11.
- **New hypotheses queued:** OF-16 (open location vs value), OF-17 (overnight-high break, SMB transfer), OF-18 (poor value area), OF-19 (relative IB width), OF-20 (trend→balance; resolves CL-009 vs CL-031), OF-21 (liquidation break), OF-22 (break-and-reclaim of volume cluster, unsigned), OF-23 (VWAP/EMA "fashionably late" transfer); OF-05 sub-variants 05c/05f.
- **Key findings:** (1) every source puts context/profile first and order flow last (timing only); (2) the only quantitative claims are unverified practitioner statistics; (3) a direct contradiction exists on post-trend-day behaviour (Axia vs DeepCharts); (4) the user's "bubble + reclaim" note matches Axia's "behind the elephant" and Faiz's "inversion" patterns; (5) all GEX content is SPX/NDX-specific and blocked for XAU/FX.
- **Nothing tested; no data collected; no production change.**
- 2026-10-11: B5 Databento pricing CORRECTED (trades USD 28/GB, not 0.50); official get_cost quote table added; databento/ access + USD 5 guard set up.
- 2026-10-11: first Databento purchase (6E trades Sep-2026, USD 0.80 from free credit); integrity + size/side stats in B5.
- 2026-10-11: 6E pilot analysis — CL-103…106 (NEXA-MEASURED), GAP-M04, GAP-K11; report databento/PILOT_6E_REPORT.md.
- 2026-10-11: 13-month 6E (USD 11.63 free credit) — CL-107…109; YEAR_6E_REPORT.md. Big-trade share drifts 2×/yr; proxy VA edge err p50 ≈ 3–4, p90 ≈ 17–19 pips.
- 2026-10-11: USER DECISION E3: big trades use a RELATIVE threshold (not a fixed lot size). Candidate behaviour measured (relative_threshold_options.py/.json); percentile / lookback / session-block choice still open.
- 2026-10-11: E3 RESOLVED by user: big = top 1 % (q99) of aggressor orders per session block (Asia/London/NY via A1/A2 anchors), 60 prior sessions; code databento/big_trades.py; CL-111.
- 2026-10-11: batch 5 platform docs (DOC-010…016, CODE-008…010, WEB-004): CL-112 imbalance consensus = diagonal; CL-113 LVN detection has no standard; CL-114 6E volume split (closes GAP-D07 for 6E). Decision brief for open E-items written.
- 2026-10-11: USER DECISIONS E1 = prior NY block; E4 = diagonal 300 % (stack/min-vol/role open); E9 = smoothed + min depth (params open); E10 = include mirrors.
- 2026-10-11: USER DECISIONS E2 = fraction of VA width; E5 = delta + above-avg volume; E6 = buffer ≥ transfer error (~2 pips); E7 = bubble high.
- 2026-10-11: USER DECISIONS E8 = exit only; E11 = flat at 17:00 NY; E12 = 6E+6J+6B+GC; venue = evaluate on CME prices (E6 re-opened; CME cost model needed).
- 2026-10-11: USER DECISIONS E6 = 1 tick (CME prices); E4 = diagonal 300 %, ≥3 stacked, confirmation only. E2/E9: measure counts first.
- 2026-10-11: E2/E9 count measurement (CL-115).
- 2026-10-11: USER DECISIONS E2 = 10 % of VA width; E9 = no smoothing, depth ≤ 50 %, no-LVN → no trade; E5 = same minute, prior 20 sessions.
- 2026-10-11: USER DECISIONS window = whole next day (18:00→17:00 NY); E4 min vol 10; costs USD 1.61 exch+NFA (GC 1.66) + 1.00 broker per side; slippage 1 tick entries+stops. ALL E-ITEMS RESOLVED.
- 2026-10-11: USER DECISIONS E5b = mirrored confirmation on break candles; most recent bubble; one position at a time, re-entry ok. 6J/6B/GC purchase attempts 402 (Databento monthly limit), unbilled pending user check.
- 2026-10-11: OFC1 PRE-REGISTERED (PREREG_OFC1_CORE_ORDERFLOW.md, sha256 ede1bc8d…); read-only; RESEARCH_GATE row added. Implementation/run needs separate approval.
- 2026-10-11: 6J/6B/GC 13 months bought (USD 55.63 free credit, after the user raised the Databento monthly limit); integrity OK, ticks match the OFC1 prereg. Total Databento spend USD 68.06; credit left ≈ 56.94.
- 2026-10-11: OFC1 RUN (disc→val→full once each): INSUFFICIENT-N, all splits negative, pooled −0.21 R; CL-116; RESEARCH_GATE + FAILED_IDEAS updated.
- 2026-10-11: OFC1R FINAL replication REJECTED (CL-117). OFC1 line CLOSED by user (no further spending). Total Databento spend USD 117.95 (all free credit; ≈ 7.06 left).
- 2026-10-11: FINAL master document v1 written (NEXA_ORDERFLOW_METHODOLOGY_MASTER.md); v0 archived in archive/.
- 2026-10-11: transcripts unblocked via Tavily extract (29 + 1 fetched); batch 6 Fabio primary sources YT-031…037; claims CL-118…126 (IVB Models 1/2 now PRIMARY; contest selection effect confirmed).
- 2026-10-11: batch 6 continued, YT-038…042 + CL-127…131 (Fabio uses reading (b); NY cash-session profile; LVN as rebalance pivot; order-book patterns; live sessions).
- 2026-10-11: all 30 queued transcripts fetched via Tavily (~6 credits) and processed; CL-132…134; Q-09/Q-12 resolved; B7 DONE. Guard watcher retired.
- 2026-10-11: batch 7 (15 user-supplied videos via Tavily) → YT-043…057, CL-135…141; strategy decode report written.
- 2026-10-11: B1 §9 FX fix literature (Krohn-Mueller-Whelan 2024; Melvin-Prins 2015; Evans 2018) + Pepperstone cost tiers; S14 forward check found with 0 fills (stopped since 2026-10-05 06:59).
- 2026-10-12: Batch 7 (23 user videos) decoded; 6 duplicate IDs, 7 duplicate substance; candidates H-ORB-1 (NAS100 ORB, best), H-ICT-1, H-VB-1, H-PSC-1 — none pre-registered. See video_batch_2026-10-12/.
