# HYPOTHESIS QUEUE (order-flow / profile family, OF-xx)

OF-01…OF-15 are defined in `../NEXA_ORDERFLOW_FRAMEWORK_REPORT.md` §5 and `../ADDENDUM_A_VISHAAL_FX_VIDEO.md` §A3. New items OF-16+ come from the video/channel study (2026-10-11). **Pre-registered (2026-10-11, hashes in `../../validation/PREREG_HASHES.txt`): OF-16, OF-19, OF-20 — see `../../validation/PREREG_OF_*.md`. Tested 2026-10-11 — see `../../validation/OF_RESULTS_REPORT.md`. Follow-up **OF-20b run 2026-10-11: INCONCLUSIVE (retrospective)** — `../../validation/OF20b_RESULTS_REPORT.md`; **trend→balance line CLOSED by user (no prospective confirmation).** OF-19x (EURUSD large-IB underperformance) is a candidate only; needs approval + new pre-registration.** Parameters shown are *candidates for a pre-registered grid*, taken from the sources where they exist — never tuned on outcomes.

**Common protocol:** see report §6 (pre-registration hash, discovery/holdout splits, geometry-matched nulls, driftless barrier law, net-of-cost R, day-block bootstrap, BH-FDR, DSR, proxy swap). FX/XAU session anchors must be pre-registered (GAP-K01).

## Priority list (feasibility × information value × testability)

| Rank | ID | Hypothesis | Source claims | Data | Notes |
|---|---|---|---|---|---|
| 1 | **OF-16** · TESTED: INCONCLUSIVE (70–80 % refuted) | Opening location vs prior-session value (above VAH / below VAL / inside) predicts the day's direction/rotation better than base rate — test the claimed 70–80 % | CL-005, CL-014 | CALC (M1 + profile; 9 y spot, 2 y futures) | Needs pre-registered "accuracy" definition (e.g. P(close beyond open in bias direction), P(reach opposite VA edge before X)); base rates per symbol; cheapest high-information test |
| 2 | **OF-19** · TESTED: REJECTED (P); INSUFFICIENT-N (T) | IB/OR width relative to the prior N sessions' widths predicts range extension & directional close after an accepted break (no return inside) | CL-003, CL-004 | CALC | Refines OF-07 into a trade rule; N, acceptance rule pre-registered |
| 3 | **OF-20 / OF-20b** · TESTED, **CLOSED** (both inconclusive; CL-031 10 % refuted) | After a trend day (pre-registered day-type rule), the next day is a balance day with probability > base rate — resolves the CL-009 vs CL-031 contradiction | CL-009, CL-031 | CALC | Pure base-rate study; extends HYP-010/013 |
| 4 | OF-01/02 | ORB and volume-confirmed ORB (unchanged) | CL-040/044 | CALC | Already rank 1–2 in report |
| 5 | **OF-17** | Session-open "overnight-high/low break" model transferred from SMB opening drive: gate (open beyond prior-day high/low and prior close), trigger = bar **close** beyond overnight/Asia range extreme with RVOL ≥ k SD (time-of-day norm), wick filter, stop under breakout bar | CL-040–042 | CALC (RVOL via tick vol / futures vol) | Transfer test from equities; k=3 per source as primary, grid counted |
| 6 | **OF-18** | Poor value area (pre-registered flatness metric: e.g. count of bins within x % of max volume / edge slope) ⇒ next-day re-entry from outside rotates through value; after 2 touches mean-reversion to VA mid | CL-011 | CALC | Requires new metric definition; T1 bimodality ratio z1 is related |
| 7 | OF-05 (+05c, 05f) | LVN: traverse (H-A) vs reaction (H-B); **05c** conditional on HTF trend (CL-016); **05f** LVN "cave" fill after trend days (CL-010) | CL-010, 015–017 | CALC | Resolves NOTE-001 N8 |
| 8 | **OF-21** | Break out of a multi-day balance ⇒ fast liquidation move, weaker next-day follow-through (P/b-profile signature) | CL-013 | CALC | Multi-day balance definition needed |
| 9 | OF-06/13 | Failed breakout / obvious-low break after long hold fades | CL-028 | CALC | — |
| 10 | **OF-22** | Break-and-reclaim of a high-volume price cluster ("behind the elephant" / "inversion" / NOTE-001 bubble) ⇒ move toward the opposite VA edge; **unsigned proxy version only** | CL-021, 023, 024 | PROXY (futures 1-min volume clusters; tick volume) | Label: does NOT test aggressor-signed absorption |
| 11 | **OF-23** | "Fashionably late" VWAP/9-EMA cross after a turn off the session extreme: hit-rate vs driftless null 25 % (1:⅓ geometry), net of costs | CL-043 | PROXY (VWAP from tick/futures volume) | Transfer from US stocks; low prior for FX |
| 12 | OF-09 | Unsigned absorption at VA edges | CL-020–024 | PROXY | — |
| 13 | OF-10 | HTF value relationship / trend filter | CL-008, 012 | CALC | Conditioning variable, not standalone |
| 14 | OF-11 | Delta divergence (proxy) | CL-026 | NO/PROXY | Low |
| 15 | OF-12 | GEX regime | CL-032–038 | NO | Blocked for XAU/FX |
| — | (abstain filter) | Abnormal gold–equity correlation ⇒ NO TRADE on gold | CL-046 | CALC | Candidate Stage-1 context filter; test as abstention value |

## Batch-2 additions (2026-10-11): candidates only, all data-blocked

| ID | Hypothesis | Source claims | Data | Notes |
|---|---|---|---|---|
| **OF-24** | Gold GEX regime: with XAUUSD (mapped from GC) above the HVL / positive net gamma computed from CME GC options OI, the next session's realised range (σ̂ units) is smaller and intraday mean reversion higher than below it | CL-032, CL-057, CL-060 | **BLOCKED** (GAP-D08: no historical GC options OI by strike; vendor levels have no history) | Low prior: CME gold options gamma is a small share of gold flow. The XAU basis map failed in T1, so mapping would need the futures price directly. **Batch 3:** FlashAlpha's 8-y SPY test (CL-075) finds no GEX value beyond VIX + ATM IV, so any pre-registration must control for implied vol (GVZ/CVOL if available) **and** HAR/lagged RV (T2). Prior lowered further |
| **OF-25** | Currency-futures gamma levels (6E/6B/6J, max-gamma strikes) act as reaction or pin levels for spot EUR/GBP/JPY beyond distance-matched placebo levels | CL-057, CL-059, CL-061, CL-062 | **BLOCKED** (GAP-D08) | The futures→spot basis map PASSED in T1 for EUR/GBP/JPY, so mapping is feasible if OI history existed. Low prior (OTC FX options dominate) |
| **OF-26** | (Method, not a market hypothesis) "Delta" from spot-FX quote ticks is not aggressor flow (CL-050). OF-11 / HYP-017 proxy-delta tests are downgraded to "quote-pressure" labels | CL-049, CL-050 | — | Classification change only; no test |

## Evidence-quality flags to carry into every pre-registration
- **Selection on outcome:** CL-041 (30 *best* drives); example-only claims (YT-004, YT-005, YT-007, YT-002 live narration).
- **Unverified statistics:** CL-005 (70–80 %), CL-031 (10 %), CL-035 (13 %), CL-043 (60 %). Treat as *priors to falsify*, not facts.
- **Instrument transfer:** most sources trade ES/NQ/stocks with a real cash open and exchange volume; NEXA trades spot FX/XAU with tick-volume proxies (T1: GBP proxy rejected; gold basis map failed).
- **Costs:** NEXA measured −0.245R commission at 2.4-pip stops; every hypothesis is judged net of costs in R.
