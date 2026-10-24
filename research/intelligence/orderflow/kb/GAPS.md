# GAPS, OPEN QUESTIONS AND STUDY QUEUE

## Knowledge gaps (K)
| ID | Gap | Why it matters | Next step |
|---|---|---|---|
| GAP-K01 | No agreed "cash session" for 24 h FX/XAU (sources use ES/NQ RTH 9:30–16:00 ET) | Every VA/IB/ORB rule depends on the session anchor | Anchors fixed per symbol in `validation/PREREG_OF_COMMON.md` §C3 (FX primary A1 London 08:00, XAU primary A2 08:20 ET; other = counted secondary) — partially closed for OF-16/19/20 |
| GAP-K02 | No source defines "stacked imbalance" for DeepCharts or gives a published threshold | Presenter (YT-001) uses it as a target | **Updated 2026-10-11:** NinjaTrader docs give imbalance defaults (1.5 ratio, min delta 10) but **no stacked definition** (CL-048/051). Defaults vary 150 %–300 % across vendors ⇒ not a standard object; UNTESTABLE as a claim; any NEXA use must pre-register its own |
| GAP-K03 | Absorption has ≥3 competing operational definitions (CL-020 vs CL-022 vs CL-024) | Determines what a proxy could even approximate | Choose one per hypothesis, pre-register, label the others |
| GAP-K04 (CLOSED — not pursued, user 2026-10-11) | Contradiction trend→balance (CL-009, Axia) vs ≈10 % rebalance (CL-031, DeepCharts) | Day-type sequence drives rotation vs breakout choice | OF-20 run 2026-10-11: UNRESOLVED — CL-009 untestable (trend-day rule degenerate on 24 h sessions); CL-031 10 % refuted for XAU/FX; see GAP-K08 |
| GAP-K05 | Cross-asset abstention rules (abnormal correlation ⇒ stand aside) never quantified | Possible cheap filter for gold | Define rolling-correlation regime; test abstention value |
| GAP-K06 | Practitioner statistics (70–80 %, 10 %, 13 %, 60 %) have no published data or method | They are the only quantitative claims in the corpus | 70–80 % (CL-005) and ≈10 % (CL-031) REFUTED for XAU/FX analogue 2026-10-11; OF-23 queued; CL-035 untestable |
| GAP-K08 | Market Profile day-type codification (EQ-016–018: ROT ≤ 2 on 30-min periods) is built for ~13-period pit sessions; on 14 h FX sessions median ROT = 8 and P(TD) ≈ 0.1 % | Every trend/balance-day hypothesis (OF-20, HYP-010/013, OF-05f, OF-21) depends on it | PARTLY CLOSED 2026-10-11: OF-20b normalisation fixes rotation (ROT13 median 3; ≤2 on 28–30 %) but full trend-day rule still fires on only 3–4 % ⇒ n too small for CL-009 on 9 y of data |
| GAP-K09 | MenthorQ methodology undisclosed: OI vs volume weighting, dealer-sign assumption, expiries, futures→spot mapping for FX/XAU; internal contradiction (native GC vs "monitor GLD", CL-064) | Determines whether vendor gold/FX levels mean anything | Read remaining Academy lessons (Q-10); ask vendor for a methodology note; never use vendor levels in NEXA without an independent computation |
| GAP-K10 | Bookmap iceberg and stop detection methods undisclosed ("100 %" native-iceberg claim on CME) | Any absorption/iceberg setup from Bookmap content | Find Bookmap KB add-on docs (the URL tried returned 404); otherwise mark vendor-only |
| GAP-K07 | What "P" means in YT-001 ("P and Delta") | Method decoding | Screenshots (see DEEPCHARTS study §7) |

## Data gaps (D) — identified, not collected
| ID | Missing data | Unblocks | Note |
|---|---|---|---|
| GAP-D01 | CME trades with aggressor side (GC, 6E, 6B, 6J) | Signed absorption, delta, footprint, big trades (K-04–K-07) | Massive trades NOT_ENTITLED |
| GAP-D02 | MBO / depth (price ladder) | Absorption as "reloading", icebergs (CL-020) | No historical backfill (DOC-001) |
| GAP-D03 | Gold/FX options OI + dealer positioning | GEX regime (K-08) | Only SPX/NDX in all sources |
| GAP-D04 | Futures history > 2 years | Longer OF tests on true volume | Massive rolling window |
| GAP-D05 | S14 live fills | Realistic cost/slippage in every OF test | Demo stopped since 2026-10-05 |
| GAP-D06 | Transcript/frames for SRC-YT-008 (3 h 42 m, no captions) | Study of that stream | User transcript or screenshots |
| GAP-D08 | Historical CME options-on-futures open interest by strike and expiry (GC/OG, 6E/EUU, 6B, 6J) plus settlement IVs | Independent GEX levels for XAU/FX (OF-24/25) | Paid (CME DataMine, **DataBento `GLBX.MDP3`** — trades with aggressor side + book confirmed; OI and GC/6E option coverage unverified, $125 free credits; or a vendor with history). **Not collected; any use of credits or purchase needs user approval** (CL-079) |
| GAP-D07 | Session-split futures volume share for GC/6E (analogue of CL-002). **6E CLOSED 2026-10-11 (CL-114); GC open** | Choosing profile sessions for FX/XAU | Computable from cached futures data (research only) |

## Unstudied-source queue (Q) — channels were sampled, not exhausted
| ID | Item | Why next |
|---|---|---|
| Q-01 | Axia: "How To Read The Price Ladder In Real Time" `SdJmiPUCsag` (20:18) | Absorption/reloading definition (GAP-K03) |
| Q-02 | Axia: "Execution Tactics In Real Time (Price Ladder Trading)" `_qA2W6ZAadQ` (23:42) | Execution / entry triggers |
| Q-03 | Axia: "How To Trade a Gap Failure (Live Order Flow)" `Ah3wSFG0eMQ` (9:52) | Gap/failed-auction rule → OF-06/16 |
| Q-04 | Axia: "3 Stages Every Market Goes Through" `pxsEv2VYSxU`; "Which Of These 2 Trends Will Reverse?" `UneUuyYFom4`; "3 Trades To Add To Your Playbook" `BSMtYfO7Qz0`; "How To Trade A Major Market Repricing" `CDO5r91QGLk` | Sequence/regime claims (K-09) |
| Q-05 | SMB: "I Built & Backtested Trading Strategies with Claude Code" `a6Cqx2t2Qyw` (48:16) | Their backtesting rigor — directly relevant to NEXA methods |
| Q-06 | SMB: "Our Prop Trading Formula (Secret to Grading Your Trades)" `hSunIc-qN3k`; "The True Formula for Profitable Trading" `YWQahVtmOnk`; "The 10 Rules That Catch Big Reversals" `P4Ijq-IJhE8`; "Revealing My Secret Relative Strength Breakout Strategy" `l7F9yIf8CeE` | Trade grading / reversal rules |
| Q-07 | DeepCharts GEX course Ep.1 and Ep.2 (referenced in SRC-YT-002) | Completes the GEX series |
| Q-08 | SRC-YT-008 (no transcript) | Needs user-provided material |

| Q-09 | **RESOLVED 2026-10-11 (Tavily extract; YT IP block bypassed without local network change).** ~~Transcripts blocked (YouTube HTTP 429 on 2026-10-11) for 9 batch-2 videos.** Retry in priority order: SRC-YT-017 `SLxM8wWVI8w` (4:30 hedging mechanism; 49:06 "how Doug calculates daily levels"; 57:18 pin), SRC-YT-022 `euw0k6noSH0` (GEX, 1 h), SRC-YT-019 `EgvZQ1kMntw` (AMT), SRC-YT-021 `u6EdCoyYqrA` (footprint), SRC-YT-020 `8Ry6ERddhoo` (DOM/heatmap), SRC-YT-015 `DK1lnqr_kKI`, SRC-YT-016 `BOKxcxyykAQ`, SRC-YT-018 `iED2nrVJPFo`, SRC-YT-023 `TizwRqyHizo` (setup; lowest) | Only metadata/chapters known; no speech-level claims extracted |
| Q-10 | MenthorQ Academy lessons. **Read 2026-10-11:** Put Support, 1D expected move, intraday vs EOD, gamma levels on futures options (none disclose a method). **Still unread:** 0DTE levels, GEX levels 1–10, "how options affect the futures market", "understanding gamma levels" (URLs in DOC-003 fetch, 2026-10-11) | Closes part of GAP-K09 |
| Q-11 | NinjaTrader help pages. **Read 2026-10-11:** Trade Detector, Volume Profile (VA 68 %). **Still unread:** Market Depth Map, VWAP bands, Delta Bars; Bookmap KB add-on pages (absorption, large lot tracker; one URL 404) | Completes the tool-default table |

| Q-12 | **RESOLVED 2026-10-11 (Tavily).** ~~Batch-3 transcripts (blocked, YouTube 429): priority SRC-YT-029 `d_UvMEVXtMQ` (GEX/DEX + DataBento), SRC-YT-026 `k0DqixCmPBk` (QC delta + entropy), SRC-CH-003 `Jmv0xvOg-RQ` (day-trading profitability paper), `a1813iCcsWQ` / `HXxHunu_Hkk` (ORB code), SRC-YT-028 `y_bsjZThP0o`, SRC-YT-025 `86AlV6174KI`, SRC-YT-024 `PMkBgsmXdTU`. Skip SRC-YT-027 (advertisement) | Speech-level claims |
| Q-13 | FlashAlpha articles not yet read: gamma-flip stability, call/put wall definitions, live vs settled GEX, COVID dealer-positioning replay, the "11 of 11 windows" walk-forward follow-up | Completes the GEX evidence picture (CL-075 is the strongest external evidence in the KB) |
| Q-14 | Scribd "Volume Profile Analysis in Trading" (SRC-DOC-008) is behind a login wall | Needs a user-provided copy |

## Method gaps (M)
| ID | Gap | Action |
|---|---|---|
| GAP-M04 | Futures→spot level transfer: using yesterday's basis gives a p95 error of 1.6 pips (> the practitioner stop buffer of 0.5–1 pip) | Tick-precise entries on Pepperstone from CME levels | Live futures price, or a pre-registered carry-drift correction tested on more months (CL-105) |
| GAP-K11 | Aggregating separate aggressor orders sent ms apart (algo slicing/icebergs) needs a time window; no KB source sets one | True Big Trades as platforms display them | Platform docs (DeepCharts/ATAS aggregation setting), or a user decision |
| GAP-M03 | `contracts.json` swaps are a 2026 snapshot in **price points**. Applied across decades they mis-scale with price (XAU ≈ 16× in 2001; C2) and ignore historical rate regimes | Any multi-year test: convert to % of price at the snapshot, or use rate-differential history (needs approval); report ex-swap beside it |
| GAP-M01 | Transcripts are auto-captions; the visual chart content (levels, numbers) is not captured | Use free storyboards to locate screen segments; request user screenshots for key frames |
| GAP-M02 | Channel-level coverage is a sample (2/30 SMB, 4/30 Axia videos by transcript) | Work through queue Q; record depth in SOURCES.md |
