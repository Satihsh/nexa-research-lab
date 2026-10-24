# NEXA RESEARCH GATE: THEORY → … → PRODUCTION CANDIDATE

**Every construct (equation, feature, hypothesis) carries exactly one stage label.** Advancing one stage requires the listed **evidence artefact**. Without it, the item stays where it is.

- **No item skips a stage.**
- **No item moves backwards silently.** A failure at any stage is recorded with the artefact and the item is marked **FAILED@stage**. Negative results are kept.

| Stage | Name | Entry evidence required (artefact) | Typical failure |
|---|---|---|---|
| G0 | **THEORY** | Registry entry (11/14): definition, mechanism, source tag (SOURCE/EXTERNAL/NEW), stated null | — |
| G1 | **COMPUTABLE** | Data-availability check (03) shows every input AVAILABLE or a *labelled* PROXY. A causal definition (information < decision-bar close). Reference implementation in `research/` with a unit test on a synthetic case | Input unavailable (GEX, true delta) → **BLOCKED@G1** |
| G2 | **TESTABLE** | **Pre-registration file hashed before results are seen:** metrics, null/placebo, splits, decision rule, candidate count | No valid null (e.g. curated examples only) |
| G3 | **IN-SAMPLE** | Discovery-split result with effect size, CI, the null comparison and BH within its family | Effect indistinguishable from null/placebo |
| G4 | **OOS** | The same frozen definition on the holdout, opened once. The effect keeps sign and passes the pre-registered rule | Sign flip or insignificance |
| G5 | **WALK-FORWARD** | Rolling/expanding re-estimation across ≥ 4 consecutive periods. Per-period effect reported; no single period > 50 % of the total effect | Instability; one-period dependence |
| G6 | **ROBUST** | 15 §5 battery: costs (+0.15R stress), slippage quantiles (S14 data), delay +1 bar, ±25 % parameter perturbation, per-symbol, per-regime, proxy swap (futures vs tick volume), calibration | Dies at cost, or only on one symbol or parameter |
| G7 | **PRODUCTION CANDIDATE** | Bar-reproducible definition plus an MQL5↔research parity test; ablation gain over the current model; written proposal | — (G7 is still **not production**) |

**Beyond G7 (outside this gate):** schema change, EA change and deployment each need **explicit human approval**. They are never automatic.

## Stage register (as of 2026-10-11: T1, T2; OF-16/19/20 tested)

| Item | Stage | Evidence |
|---|---|---|
| EQ-004 HAR | **G4 reached, rule FAILED** (HYP-001b) | T2 holdout: lowest QLIKE 4/4, but significant vs ATR14 only 1/4 (pre-registered rule needs 3/4) → **FAILED@G4 for "beats ATR"**. Retained at G4 as the *best-measured* forecaster |
| EQ-002 Yang–Zhang (n = 20) | **FAILED@G4** | Significantly worse than ATR14 on EUR, GBP and XAU in the holdout |
| ATR(7) (not in the registry; baseline) | G4 (descriptive) | Second-best holdout QLIKE on 3/4 symbols |
| HYP-001 activity proxy (tick vol ↔ futures vol, EQ-005 inputs) | **G4 PASSED (PROXY)** for XAU, EUR, JPY; **FAILED@G4 for GBPUSD** | T1: M3a 0.60 / 0.60 / 0.55 vs GBP 0.45; all pairs weaker in holdout than discovery |
| HYP-001 profile proxy (EQ-014 VA from tick volume) | **G4 PASSED (PROXY)** for XAU, EUR, JPY; **FAILED@G4 for GBPUSD** | T1: P1 ≤ 0.25σ on 74 / 67 / 75 % vs GBP 57 %; bimodal-day POC failure 47–62 % |
| EQ-026 basis map / HYP-034 | **G4 PASSED** for EUR, GBP, JPY; **FAILED@G4 for XAUUSD** | T1: ≤ 0.1σ on 99.5 / 99.9 / 97.3 % vs XAU 88.0 % (p95 0.24σ) |
| TVPC (pre-registered fitted form) | **FAILED@G4** (AUC 0.614 < 0.65) | Fit compromised: z5 undefined on 70 % of days (0-point FX spreads) |
| TVPC0 = 1 − z1 / TVPC as a downstream gate | **G4 PASSED** (downstream rule) | Top-vs-bottom tercile disagreement CI excludes 0 for F-a and F-b; F-a near-circular, F-b is the meaningful one |
| TVPC_v1 (E2: z1, z2, z3, z4, z6; EXPLORATORY) | **G1** (candidate; holdout already seen) | Exploratory AUC 0.667; needs a new ID, a pre-registration and a prospective holdout (2026-10 →) |
| TVPC_activity (hour level) | **FAILED@G4** | Holdout R² 0.003; hour-level proxy error is not predictable |
| EQ-012/013/015/016–018, 019–023 | G1 (computable; no pre-registration yet) | — |
| EQ-006/007/039 activity proxies | G1 | — |
| EQ-008/009/010 flow proxies | G1 (PROXY) | — |
| EQ-011, 027, 028, 029, 031 | **BLOCKED@G1** (data) | 03 |
| EQ-035 Hawkes | G1 (data short) | — |
| OF-16 open location vs prior VA (CL-005) | **INCONCLUSIVE@G3/G4**; EURUSD **FAILED@G4** | `OF_RESULTS_REPORT.md` §2: pooled θ16 XAU +0.004, EUR −0.018, JPY +0.021 (all CIs span 0); hit rate 0.48–0.53 refutes 70–80 % |
| OF-19 relative IB width (CL-003/004) | OF-19-P **FAILED@G4** (4/4 REJECTED); OF-19-T no verdict (INSUFFICIENT-N, net R < 0 every split) | `OF_RESULTS_REPORT.md` §3 |
| OF-20 trend → balance (CL-009 vs CL-031; HYP-010/013) | **INCONCLUSIVE@G3** (INSUFFICIENT-N 4/4: codification degenerate on 24 h sessions) | `OF_RESULTS_REPORT.md` §4; CL-031 ≈10 % refuted for analogue; HYP-013 base rate 0–1.5 % under EQ-016–018 |
| OF-20b trend → balance, session-length-normalised (13 equal periods; IB = 2/13 of session) | **INCONCLUSIVE@G3 (RETROSPECTIVE)**: GBPUSD REJECTED; XAU/EUR/JPY INSUFFICIENT-N (71/80/97 trend days) | `OF20b_RESULTS_REPORT.md`; P(TDb) 3.3–4.3 %; EURUSD +0.10 all splits (CI touches 0) is the only lead; **LINE CLOSED by user 2026-10-11; prospective §6 will not be started** |
| C1 Tokyo-fix / gotobi USDJPY (Ito & Yamada 2017) | **INCONCLUSIVE@G4 (not tradable)**: gross effect confirmed (+2.17 bp, beats 44/44 placebos every split; gotobi − other +1.12 bp CI > 0) but net S1 −0.58 bp | `C1_REPORT.md`; commission (1.4 bp per 2 round trips) consumes the edge; no follow-up under this ID |
| C2 FX/XAU time-series momentum (daily, vol-scaled; MOP 2012) | **FAILED@G4: REJECTED** (pooled net −0.19 %/mo, CI [−0.34, −0.02]; all 16 cells negative) | `C2_REPORT.md`; option-(a) points-swap snapshot dominates (XAU price-scaling artefact); even ex-swap only +0.12 %/mo, CI [−0.03, +0.31], n.s. |
| OFC1 core order-flow method (Setups A/B + mirrors; true CME aggressor data; 6E/6J/6B/GC) | **INSUFFICIENT-N@G4 (no edge)**: 130 trades (< 150); every split negative (disc −0.25, val −0.22, hold −0.09 R); pooled −0.21 R (S1 CI < 0); worse than the random-timing placebo (p 0.94); DSR 0.00 | `OFC1_REPORT.md`; order-flow confirmation +0.16 R vs none (n.s.) |
| OFC1R FINAL replication (frozen OFC1 rules; unseen 6E 2023-01→2025-08) | **FAILED@G4: REJECTED** (211 trades, −0.119 R, S1 CI < 0; 0/3 years positive; placebo p 0.61; DSR 0.0007). **OFC1 line CLOSED (user: final run)** | `OFC1R_REPORT.md` |
| IM1 market intraday momentum, last half-hour (Baltussen et al. 2021); EUR/GBP/JPY close 15:00 ET, XAU 13:30 ET | **FAILED@G4: REJECTED (net; not tradable)**: net S1 −1.08 bp/trade [−1.33, −0.83], every split and year negative; **gross confirmed** +0.35 bp [+0.10, +0.60], β CI > 0, EUR/GBP placebo p 0.029; XAU no effect | `IM1_REPORT.md`; cost ≈ 1 bp vs gross ≈ 0.5 bp FX (C1 pattern) |
| FX1 daily FX fix reversals (Krohn, Mueller & Whelan 2024 JF): W1 post-Tokyo, W2 pre-ECB, W3 post-London; EUR/GBP/JPY | **FAILED@G4: REJECTED (net; not tradable)** 2026-10-11. Gross +0.70 bp [+0.33, +1.12], 9/9 signs match the paper at ~¼ size; placebo p 0.024; net S1 −0.63 [−1.00, −0.22]; post-paper −0.60; S0 −0.13 | `PREREG_FX1_FIX_REVERSALS.md`, `FX1_REPORT.md` |
| FXC carry (G10 USD pairs, daily+) | **G1-BLOCKED (power / cost; not pre-registered)** 2026-10-11: MDE Sharpe 0.48 (26.7 y) / 0.96 (holdout-sized) vs post-2008 prior ≈ 0–0.3; Pepperstone swap markup 0.7–1.5 %/yr per side; rate history not on disk; price history seen in C2 | `FEASIBILITY_LONG_HORIZON_FX.md` |
| H-ORB-1 NAS100 5-min opening-range breakout (Zarattini & Aziz 2023; QQQ 2016–23, 675 %, ignores spread/slippage) | **INCONCLUSIVE@G4 (H only; 2026-10-13)**: CME NQ ohlcv-1m 2023-02-18→2026-10-10 (D-1/D-2), 881 S1 trades, mean +0.063 R [−0.059, +0.189], p 0.15; p_tod 0.19; DSR 0.009; 2025 = 65 % of R; N2 opposite −0.16 R (CI < 0). Not deployable; next = prospective pre-registration | `HORB1_REPORT.md`, `horb1_results_H.json` |
| H-IVB1-NQ Fabio Valentini IVB Model 1 (30-min NY range, fixed volume profile, retrace limit at VA edge, invalidation on 5-min close beyond the far VA edge, 2R; SRC-YT-031) on CME NQ | **INCONCLUSIVE@G4 (2026-10-14; no detectable edge)**: NQ ohlcv-1m+volume 2023-02→2026-10, 643 S1 trades, mean +0.010 R [−0.080, +0.117], p 0.36; p_tod 0.10; DSR 0.0003; 1/4 years positive (2025 = 186 % of R); short −0.077 R; N2 fade −0.03 R; all robustness variants ≈ 0. Not deployable; no ATAS alert | `HIVB1_REPORT.md`, `hivb1_results.json`, `DEVIATIONS_HIVB1_HIM.md` |
| H-IM-NQ market intraday momentum (Baltussen et al. 2021 ROD → last 30 min; Gao FH secondary) on CME NQ | **REJECTED (2026-10-14)**: 852 trades, S1 −3.08 bp [−4.58, −1.43]; gross −3.96 pts/trade (last 30 min *reverses* the day on NQ 2023–26); every year negative; Gao FH −1.50 bp; p_tod 1.00. A reverse (fade) rule may only be a NEW pre-registration on NEW data | `HIM_REPORT.md`, `him_results.json` |
| H-ORB30L-NQ 30-min ORB long-only, stop range low, 1R (2R secondary), exit 15:30, entry by 11:30 ET (Matteo Conti SRC-YT-081 / Gao 2018) | **REJECTED (OOS FAILED 2026-10-16)**; was INCONCLUSIVE@G4 (2026-10-15) — 6/7 checks pass, only DSR fails (0.07, 116 trials)**: 460 S1 trades, +0.058 R [+0.002, +0.123], p 0.020; p_tod 0.05 (0/19 placebos better); 4/4 years positive (max 37 %); beats N2 beta control (−0.058 R) by +0.116 R; median R 119 pts (≈$238 risk per MNQ); ≈+$100/month per MNQ, 64 % months positive. Next = NEW data only (older NQ OOS and/or prospective demo ≥100 trades). **2026-10-16 OOS REPLICATION FAILED → CLOSED**: QuantConnect NQ 2009-01-02→2023-02-17, 1,604 trades, S1 −0.071 R [−0.111, −0.035], 6/15 years positive, primary−N2 +0.016; ≈ −$48/month per MNQ (`HORB30L_REPL_REPORT.md`). HistData parity had failed earlier (NOT EVALUABLE). Forward log stopped | `HORB30L_REPORT.md`, `horb30l_results.json` |
| H-VAR-NQ Dalton Value-Area Rule (open outside d−1 VA, 2 consecutive 30-min periods inside → opposite VA edge; stop = session extreme; signal by 11:30 ET) | **INCONCLUSIVE (2026-10-15; no evidence)**: 192 trades, +0.053 R [−0.118, +0.199], p 0.40; stale-VA p 0.40; 1/4 years positive (2026 = 155 %); traverse rate 39.6 % (vs Dalton coin-flip, popular '80 %'); Dalton conditions n.s.; not deployable | `HVAR_REPORT.md`, `hvar_results.json` |

## Closed research lines (no new pre-registrations without explicit user approval)

| ID | Line | Closed | Evidence | What may reopen it |
|---|---|---|---|---|
| **LC-1** | Order-flow / volume-profile rule strategies (OF-16/19/20/20b, OFC1, OFC1R) | 2026-10-11 by the user ("final run") | `OFC1R_REPORT.md`; KB `orderflow/` | Nothing planned. The user decided no further spending |
| **LC-2** | **Intraday FX timing anomalies with gross edge < ≈ 2.6 bp per trade** (2× the S1 round trip) | 2026-10-11 by the user ("Approved 1") | C1 (gross +2.17 → net −0.58), IM1 (+0.35 → −1.08), FX1 (+0.70 → −0.63). Commission alone (USD 7/lot ≈ 0.65 bp) ≥ the IM1 / FX1 gross edge, so **no execution improvement can make them tradable** at this broker | (a) an expected gross edge ≥ 2.6 bp per trade from a published source **before** testing, or (b) a verified cost structure < 0.3 bp per round trip with real fills |
| **LC-3** | Long-horizon FX on the Pepperstone G10 universe: trend (C2 REJECTED) and carry (FXC G1-BLOCKED) | 2026-10-11 | `C2_REPORT.md`, `FEASIBILITY_LONG_HORIZON_FX.md` | A materially larger cross-section or institutional financing |

**Rules of use**
- **One artefact per transition, stored under `research/intelligence/validation/`, hashed in `PREREG_HASHES.txt` or a results manifest.**
- **A failed rule cannot be re-run with tweaked parameters under the same ID.** A variant gets a new ID, a new pre-registration and is counted in the family's multiple-testing budget.
- **Proxies advance only as proxies.** A G6 result on tick volume is not a G6 result on true volume.
