# NEXA RESEARCH GATE: SUMMARY AFTER T1 + T2 (2026-10-05)

**Scope:** research only. Nothing in this folder touches S14, NEXA_Risk, schema v1, the EA, its inputs or the live demo. Nothing is deployed.

**Sources**
- T1_REPORT.md (tick volume ↔ futures volume);
- T2_REPORT.md (volatility forecasts);
- EQUATION_PRIORITY_MATRIX.md;
- HYPOTHESIS_PRIORITY_MATRIX.md;
- TOP10_CONSTRUCTS.md;
- RESEARCH_GATE.md.

**Hashes:** PREREG_HASHES.txt (pre-registrations) and RESULTS_MANIFEST.txt (outputs and data).

## What the two tests established

| Test | Pre-registered verdict | One-line meaning |
|---|---|---|
| **T1 HYP-001 activity** | PASS for XAU, EUR, JPY; **FAIL for GBP** | Tick volume tracks real activity moderately (r ≈ 0.6). It reproduces intraday shape almost perfectly and under-states surges. |
| **T1 HYP-001 profile** | PASS for XAU, EUR, JPY; **FAIL for GBP** | A tick-volume profile is usually right (POC within 0.25σ on about 70 % of days). It is badly wrong on two-peaked and wide-range days. |
| **T1 HYP-034 basis** | PASS for EUR, GBP, JPY; **FAIL for XAU** | Futures levels map onto FX spot causally. For gold, the error tails are too fat. |
| **T1 TVPC** (fitted) | **FAIL** (AUC 0.61) | Construct defect: the spread input is undefined for FX. The exploratory fix reaches AUC 0.67. |
| **T1 TVPC downstream** | **PASS** | Gating by TVPC significantly improves agreement with true-volume features. |
| **T2 HYP-001b** | **REJECTED** | Neither YZ nor HAR beats ATR(14) on ≥ 3/4 symbols. YZ(20) is *worse*. HAR is numerically best and not separable from ATR(7). |

---

## Top 10 equations
(EQUATION_PRIORITY_MATRIX, score = A × D × mean(B, C, E, F, G); evidence-updated)

| # | EQ | Why it ranks |
|---|---|---|
| 1 | EQ-025 Net expectancy in R with costs | The identity every result must pass through (cost 0.245R at 2.4-pip stops) |
| 2 | EQ-001 Realised variance | The target and input of all volatility work |
| 3 | EQ-024 Driftless two-barrier null | The null for every stop/target claim |
| 4 | EQ-004 HAR log-RV | Best measured forecaster (T2); "beats ATR" not established |
| 5 | EQ-005 Seasonal baseline / RVOL | Shape is valid on tick volume (T1). Abnormal-activity validity is moderate; not for GBP |
| 6 | EQ-034 Two-barrier probability with drift | The bridge from state to P_U |
| 7 | EQ-021 Variance ratio | Testable regime diagnostic |
| 8 | EQ-019 Compression ratio | Testable; low information gain |
| 9 | EQ-003 Parkinson | Baseline only (T2: worse than ATR14) |
| 10 | EQ-020 Efficiency ratio | Regime / day-type input; T1 shows proxy quality is best on high-ER days |

**Promoted by T1 evidence but outside the score top 10:**
- **EQ-014** value area: proxy validated for XAU, EUR, JPY.
- **EQ-026** basis map: validated for FX.
- Both are now usable as **gated PROXY** inputs.

## Top 10 hypotheses
(HYPOTHESIS_PRIORITY_MATRIX, IG × DF × TE × TR)

| # | HYP | Status |
|---|---|---|
| 1 | HYP-024 Wider stops cut cost-in-R without cutting gross R | Not tested. **Highest priority** |
| 2 | HYP-001 Tick volume as an activity / profile proxy | **Tested (T1):** supported for XAU, EUR, JPY; rejected for GBP |
| 3 | HYP-023 Stop-rule comparison (H2/H3/H5) | Not tested; now unblocked for H3 (TVPC-gated VA) |
| 4 | HYP-035 Execution state → slippage | Waiting for S14 demo fills |
| 5 | HYP-020 Regime persistence and conditioning | Not tested |
| 6 | HYP-034 Causal futures→spot basis map | **Tested (T1):** supported for FX; rejected for XAU |
| 7 | HYP-007 Value-Area Rule | Not tested; now admissible (TVPC-gated, XAU/EUR/JPY) |
| 8 | HYP-008 3-1 day continuation | Not tested |
| 9 | HYP-010 Post-trend-day reversal | Not tested |
| 10 | HYP-004 "Volume slows price" | Not tested; proxy volume admissible except GBP |

**Also tested:** HYP-001b (YZ/HAR beats ATR): **REJECTED (T2)**.

## Top 10 datasets

| # | Dataset | State | Note |
|---|---|---|---|
| 1 | Pepperstone M1 canonical (4 symbols, 2017/18 →) | On hand | OHLC + tick volume reliable. **The spread field is 0 points on 64–94 % of FX bars**, so it is unusable as a state variable |
| 2 | NEXA Trade DNA (tester, 2024–26) | On hand | Fixed entries for exit/stop re-simulation (HYP-024/023) |
| 3 | CME futures 1-min, front-month: GC, 6E, 6B, 6J (Massive) | **Cached locally, 2024-10 → 2026-10** (`data/*_fut_hourly.csv`, `*_fut_profile.csv`) | Massive keeps only a rolling 2 years. **The local cache is now the only copy of the oldest months** |
| 4 | Massive `1session` futures bars | Re-pullable | Front-contract rule |
| 5 | S14 demo forward (account <demo-account>) | Accruing since 2026-10-04 | The only real-execution source (HYP-035) |
| 6 | NEXA TickLogger ticks | ≈ 28 days | Too short for Hawkes / microstructure |
| 7 | MT5 economic calendar | On hand | Stamped with the export-time offset (known trap) |
| 8 | Massive ES/NQ and other futures aggregates | Available | Cross-asset spillover (HYP-032) |
| 9 | Massive treasury yields / FX aggregates | Available | Cross-asset XAU drivers (HYP-031) |
| 10 | Options aggregates (ETF volume only) | Partial | **No OI or greeks:** the GEX family stays blocked |

## Top 10 missing-data problems

1. **No signed trade flow** (Massive trades/quotes NOT_ENTITLED). Blocks true delta, EQ-011 and the flow hypotheses; only circular proxies remain.
2. **No open interest or greeks.** Blocks every GEX / gamma / charm hypothesis (HYP-025–029).
3. **The futures history is a rolling 2-year window.** Old months disappear daily. Mitigated for T1 by the local cache; any new futures study must cache on pull.
4. **FX spread is recorded as 0 raw points on most bars.** Spread-state features are undefined (this broke the pre-registered TVPC). Costs must come from commission plus measured fills, not the M1 spread.
5. **Roll contamination of front-month volume.** About 0.06–0.08 of correlation is lost around rolls. The fix is *total* volume across listed months (more pulls).
6. **Gold intraday basis tail** (p95 0.24σ). Futures-derived gold levels need an intraday basis update before use at stop precision.
7. **Short tick history** (28 days). It cannot support event-intensity or queue models.
8. **Tiny live-execution sample.** Slippage and latency models (HYP-035) must wait for S14 fills.
9. **Massive session gaps** (2026-03-27). Every futures pipeline needs an automatic missing-session check.
10. **The 2027 data is reserved as V2 OOS.** It needs explicit approval, so prospective validation of anything new (e.g. TVPC_v1) is limited to 2026-10 → 2026-12 unless approved.

## Top 10 experiments to run next

| # | Experiment | ID / pre-registration needed | Data | Cost |
|---|---|---|---|---|
| 1 | **Cost geometry:** fixed NEXA entries, exit re-simulation with (U, D) scaled by m ∈ {1, 1.5, 2, 3}; gross vs net R; block bootstrap | HYP-024 (new prereg) | DNA + M1 | M |
| 2 | **Intraday HAR vs ATR(7)/ATR(14)** at the 1–4-hour horizons NEXA's stops use | HYP-001c (new prereg) | M1 | S |
| 3 | **Stop-rule comparison** H2 (σ-stop) vs H3 (beyond prior VA edge, TVPC-gated) vs H5 at matched mean D; XAU/EUR/JPY | HYP-023 | DNA + M1 + TVPC | M |
| 4 | **RVOL adds to HAR?** Nested HAR with ln RVOL; proxy swap (futures vs tick volume) | HYP-002 | M1 + cached futures | S |
| 5 | **Regime persistence** and barrier outcome by filtered regime | HYP-020 | M1 | M |
| 6 | **Value-Area Rule base rates** vs a placebo VA, with TVPC as a gate | HYP-007 | M1 (+ futures check) | M |
| 7 | **Day-type continuation** (3-1, post-trend, neutral-extreme): base rates, Fisher + BH | HYP-008/009/010 | M1 | S |
| 8 | **Roll-robust truth:** T1 activity metrics with all-month total futures volume (robustness only; verdicts unchanged) | T1-R (exploratory) | Massive re-pull | S |
| 9 | **Gold intraday basis map** (hourly causal update) vs the daily map | HYP-034b | Cached GC + M1 | S |
| 10 | **TVPC_v1 prospective check:** freeze the formula now; evaluate 2026-10 → 2026-12 | TVPC-v1 (prereg now) | Massive (cache monthly) | S |

## Recommended research sequence

**Stage A, now (data on hand; highest information gain per day):**
1. **HYP-024 cost geometry** (#1). It speaks directly to NEXA's measured failure mode (cost 0.245R). If gross R collapses as m grows, the stop/target design question is answered negatively, cheaply.
2. **HYP-001c intraday HAR** (#2). It decides which σ̂ the stop experiments use.
3. **Freeze and pre-register TVPC_v1** (#10). Start caching Massive data monthly so the prospective window accumulates.

**Stage B, after A (needs A's σ̂ and cost geometry):**
4. **HYP-023 stop rules** (#3), using A's σ̂ and TVPC-gated VA edges.
5. **HYP-020 regimes** (#5) and **HYP-002 RVOL** (#4), both as covariates for the stop/outcome law.

**Stage C, structure (only if A/B show any conditional outcome dependence worth explaining):**
6. HYP-007 VA rule (#6) and the day-type family (#7).
7. The liquidity field (HYP-004/005/006).

**Stage D, data-gated:**
8. **HYP-035 slippage** once the S14 demo has a meaningful fill count.
9. **HYP-034b gold basis** (#9) before any futures-derived gold level is used.
10. **T1-R roll-robust re-check** (#8) whenever futures pulls are next made.

**Blocked:** GEX family, true flow, Hawkes. They stay blocked until OI, trades or long tick history are acquired. **No experiment in this list can change production** without a written G7 proposal and explicit human approval.
