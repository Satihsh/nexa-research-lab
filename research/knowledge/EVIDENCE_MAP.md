# EVIDENCE MAP: what the corpus supports, how strongly, and from how many independent lines

Corpus: 39 files, 38 distinct works (S37 = S06). Built 2026-10-02.

**How to read this file:**
- **Evidence status** uses the required scale: Established evidence > Strongly supported > Supported finding > Research finding > Hypothesis > Unverified claim; plus Contradicted, Failed, Data-limited and Unknown.
- **Independent lines** counts *clusters*, not papers (SOURCE_MAP §5). The Cartea group (S06/S10/S11/S14/S24/S25/S26) is one cluster. The Zohren–Roberts group (S02/S03/S13) is one. S04 and S18 are one.
- **NEXA data** means whether NEXA currently has the data needed to test or use the item (✓ available, ◐ partial, ✗ not available).
- **Use** is the recommended stance: USE (as a research principle or method), TEST (hypothesis worth a protocol), CAUTION, or DO NOT USE.

Nothing here is a claim of profitability.

---

## 1. Principles ranked by evidence

### 1.1 Established or strongly supported (multiple independent lines)

| # | Principle | Supporting sources (clusters) | Status | Independent lines | NEXA data | Use |
|---|---|---|---|---|---|---|
| P1 | **Transaction costs are the dominant failure mode** of published edges; results must be shown as a cost curve | S02, S03, S13 (Z–R cluster); S14 (Cartea/Cucuringu); S12, S16, S08 (negative); S22 App. A; S32 Ch. 21–22; S31 (TCA); S10 | Strongly supported | ≥ 6 | ✓ (spread from bid/ask; slippage unlogged) | USE |
| P2 | **Volatility is clustered and highly forecastable**; HAR/GARCH-type log-variance models are hard baselines; direction is not | S23; S04/S18; S39 (β ≈ 0.99); S09/S19 (stylised); S15 (scaling); S02 (vol-scaling works) | Strongly supported | ≥ 5 | ✓ (M1 bars → RV) | USE / TEST (H-VOL-1..4) |
| P3 | **Resting/limit orders are adversely selected**: fills when price moves through you, misses when it runs away; a quote is a written option | S06; S10; S11; S29/S27; S32 (Ch. 1, 14, 18); S31 (practitioners); S30 (narrative) | Strongly supported | ≥ 5 | ◐ (needs live/demo fill logs) | USE (design principle) |
| P4 | **Volatility scaling of positions** (1/σ) is a robust risk normaliser; it reduces drawdown more than it adds return | S02, S03 (Z–R); S22 §6.5/§15.3.1 (literature pointers); S13 (μ/σ² generalisation) | Supported finding | 2–3 | ✓ | TEST within the fixed 1 % cap (H-VOLTARGET-CAP, H-VOL-2) |
| P5 | **Simple strong baselines usually match complex models** out of sample | S23 (HAR ≈ NN daily); S13 (Bayes OLS ≈ deep); S26 (RF +5 pts); S14 Ch. 6 (≈ FF12); S03 (long-only ≥ RL in equities); S39 (GARCH variants equivalent); S35 (naive beats Q-models) | Strongly supported | ≥ 5 | ✓ | USE |
| P6 | **Selection bias and multiple testing** inflate published results; a frozen holdout and a candidate count are required | S32 Ch. 22; S33 (fails); S36 (fails); S01/S08 (selected examples); S22 (no defence); S14 (cites DSR); S04 (noisy objective) | Strongly supported (as a methodological fact) | ≥ 5 | ✓ | USE (H-SEARCH-DEFLATE) |
| P7 | **Execution timing is part of the result**: delay-0 / same-bar execution is "borderline in-sample" | S22 App. A; S14 Ch. 4–5; NEXA D-EXEC-ENTRYBAR (prior fact) | Strongly supported | 2 + NEXA | ✓ | USE (H-DELAY-PARITY) |
| P8 | **Detrending and normalisation create artefacts** (MA-relative "mean reversion"; level-variance/h) | S15 (simulation + author concession); S38 (our analysis); S12, S14 Ch. 5 (bounce) | Strongly supported (maths) | 2–3 | ✓ | USE (null tests) |
| P9 | **FX returns scale super-diffusively**: ⟨\|Δx\|⟩ ∝ Δt^{0.56–0.58} from sub-second to years | S15 (two data sources) + Müller et al. (cited) | Established (replicated) | 1 (+ literature) | ✓ | TEST on XAU/FX (H-HURST-GATE) |
| P10 | **Spread ∝ volatility × toxic-flow share**; spreads widen in fast markets and around news; the slippage tail grows ×4–6 around news | S11 (theory); S10 (LMAX data); S01 (practice); S32 Ch. 14; S31 (March 2020) | Strongly supported | 4 | ◐ (spreads ✓; slippage logs ✗) | USE (H-NEWS-SLIP) |
| P11 | **Information lives in private/depth data**: public-only features predict order direction barely above chance; imbalance predictability needs depth | S26 (ablation); S34; S29; S13; S06 | Strongly supported | 3 | ✗ (no depth) | CAUTION (DATA-LIMITED) |
| P12 | **Edges decay** (crowding, rediscovery, regime change) | S21; S22 Ch. 1; S01; S14 Ch. 4 (decay over decades); S03 (FX trend failed 2011–19) | Strongly supported | ≥ 4 | ✓ | USE (prospective OOS) |
| P13 | **Win rate is not edge**; payoff asymmetry determines hit rate; driftless TP/SL geometry has zero expectancy | S08 (87.5 %/0.29); S02 (hit ≈ 50 %); S03 (P/L ratio); S01 G5; MATH M1b (derivation) | Established (maths) + supported | 3 | ✓ | USE (H-HIT-PROB null) |
| P14 | **Liquidity is conditional**: it withdraws in stress; fine-scale volatility rises disproportionately in stress | S30 (flash crash, quote withdrawal); S31 (March 2020 HSBC chart); S32 Ch. 28 (cascades); S10 (news flickers) | Supported finding | 3–4 | ◐ | USE (stress cost scenarios; H-STOP-SLIP) |
| P15 | **Estimator bias with short samples and gaps** (OU α̂, weekend handling ±20–25 % in σ) | S15 (simulations); S04 (daily-RV smoothing biases H) | Supported finding | 2 | ✓ | USE (H-GAP-VOL) |

### 1.2 Supported or research findings (single line or limited data)

| # | Finding | Source | Status | NEXA data | Use |
|---|---|---|---|---|---|
| R1 | Intraday RV commonality; last-half-hour RV predicts next-day volatility; pooled models generalise to unseen assets | S23 | Supported finding (US equities) | ✓ (to test on FX/XAU) | TEST (H-VOL-3, H-VOL-4) |
| R2 | Log-volatility is rough (H ≈ 0.07–0.14 in equity indices) | S04 (replication of GJR) | Research finding / established in literature | ✓ | TEST (H-ROUGH-1) |
| R3 | Short-horizon cross-asset lead-lag exists in equities and decays within months | S14 Ch. 4 | Research finding (cost-fragile; same-close execution) | ◐ (bars ✓; data-limited earlier) | TEST (H-LEADLAG-FX) |
| R4 | Signals can carry opposite premia overnight vs intraday | S14 Ch. 5 | Strongly supported statistically (equities) | ✓ | TEST (H-SESSION-SPLIT) |
| R5 | Optimal slippage tolerance δ* = cost of a miss; widen with volatility | S10 Ch. 3–4 | Established (model) + supported (LMAX) | ◐ | TEST when fill logs exist (H-DEVIATION-OPT) |
| R6 | μ/σ² sizing improves risk-adjusted P&L slightly (before costs) | S13 | Research finding (preliminary) | ◐ (needs calibrated μ) | CAUTION |
| R7 | Density forecasts (GARCH-t) beat unconditional/QR densities; quantile triggers fix trigger frequency | S39 | Research finding | ✓ | TEST (H-VAR-TRIGGER) |
| R8 | Imbalance predicts next trade sign (≈ 0.7–0.9) and jumps (AUC 0.72) | S34; S29 | Research finding | ✗ | DATA-LIMITED |
| R9 | MMs snipe retail spread-improving orders (62.58 % vs 0.08 %; 91 µs) | S06 (=S37) | Strongly supported (one market/month) | ✗ | Principle only (P3) |
| R10 | Variance ratio falls in stress (2 h vs 30 s vol) | S31 (HSBC Fig. 4, proprietary) + S38 (theory) | Research finding / practitioner | ✓ | TEST (H-VR-SCALE) |
| R11 | Algorithms can learn supracompetitive prices; tick size matters | S24 | Established (theory) + simulation | ✗ | Background (H-SPREAD-REGIME descriptive) |
| R12 | Cointegrated pool/oracle rates; optimal speed = AC term + signal term | S25 | Research finding (weak significance) | ✗ (no second feed) | Toolkit only |
| R13 | First-passage probabilities under GBM/ABM | S27 (verified) + MATH M1b | Established (maths) | ✓ | TEST as null (H-HIT-PROB) |
| R14 | Predictable flows (fix, month/quarter-end hedge rolls) are gameable | S31 (FX HedgePool), S01 (Tokyo fix/gotobi), S32 Ch. 11 (order anticipators) | Unverified claim / plausible mechanism | ✓ | TEST (H-FIX-FLOW, H-GOTOBI) |

### 1.3 Unverified, contradicted or failed (do not rely on)

See FAILED_IDEAS §A–B and CONTRADICTIONS.
- **Unverified:** S01 trade claims and pattern systems; S07; S08; S09 profitability; S17 predictive frequency; S19; S28 benefits; S30/S31 magnitudes; S22 second-hand empirics.
- **Failed or contradicted:** S33; S35; S36; S16; S12 (as edge); S14 nonlinear Lévy claim; S18 exponential ACF; S38 Prop 1.

---

## 2. Cross-source agreement matrix (independent clusters only)

| Topic | Practitioner (S01, S07–S09, S17, S19, S31) | Oxford/Cartea cluster | Oxford Z–R cluster | Other academic (S12, S15, S16, S21, S27–S29, S33–S36, S38) | Textbook / journalism (S32, S30) | External (S39, S05) | Net |
|---|---|---|---|---|---|---|---|
| Costs dominate | S01 (Guerrilla = pros only), S31 | S14, S10 | S02, S03, S13 | S12/S16 (negative), S21 | S32 Ch. 21–22 | — | **Agree** |
| Volatility forecastable | S09, S19 (squeeze) | S23 (Cucuringu) | S02 (vol-scaling) | S15, S04/S18 | S32 Ch. 20 | S39 | **Agree** |
| Adverse selection of resting orders | S31 (passive algo P&L), **S19 disagrees** | S06, S10, S11 | — | S27, S29, **S28 disagrees** | S32, S30 | — | **Agree** (practitioner dissent) |
| Direction weakly predictable at bar horizons | S01, S17, S09 claim otherwise (unverified) | S26 (public data ≈ chance) | S02 (hit ≈ 50 %) | S35 (≈ 50 %) | S32 Ch. 10 (random walk of values) | — | **Mostly agree** |
| Mean reversion around MAs | S09, S17, S01 claim | — | — | S15 (artefact), S16 (claim, failed), S12 (artefact), S38 | S32 (bounce) | — | **Contested** (CONTRADICTIONS A4) |
| Trend following | S01 (first-to-last close), S19 | S14 (lead-lag ≠ trend) | S02 (yes, 1995–2015), S03 (FX no, 2011–19) | S15 (E > 0.5), S21 (12-month term) | — | — | **Regime-dependent** |
| HFT = liquidity? | S31 (mirage) | S06 (snipe/collude), S24, S26 | — | — | S30 (tax), S32 (dealers supply immediacy) | — | **Contested** (CONTRADICTIONS A1) |
| Need frozen holdouts / multiple-testing control | S31 (calibration vs choice data) | S14 (cites DSR), S26 (walk-forward) | S02 (walk-forward) | S33, S36 (fail) | S32 Ch. 22 | — | **Agree** |
| Fat tails | S01 (gaps), S19 | — | — | S35 (VG), S27 (GBM assumption criticised) | S30 (flash crash) | S39 (ν ≈ 8.5) | **Agree** |

---

## 3. Strongest vs weakest content per source (one line each)

| Src | Strongest usable content | Weakest content |
|---|---|---|
| S01 | Execution hygiene around news, Sunday open, round-number stops; ER/overlap regime ideas | Showcased trades; GSCS; Mundo/beta; ME code |
| S02 | Vol-scaling; costs in objective; cost-curve honesty | Sharpe 2.8 transfer |
| S03 | FX TSMOM negative 2011–19; reward with cost | Cost tolerance numbers; MDD values |
| S04 | Rough-vol estimation; noisy-objective lesson | SRFG superiority |
| S05 | Governance vocabulary (measurement readiness) | Any validation |
| S06/S37 | Sniping and signalling facts | Collusion model (hypothesis) |
| S07 | Testable level/ADR/session components | MM manipulation cycle |
| S08 | Win-rate illusion example | All performance numbers |
| S09 | Canonical band definitions | Profitability |
| S10 | δ* = α; news flicker law; misses adversely selected | Transfer to OTC (hypothesis) |
| S11 | Spread as option; rejection asymmetry | No empirics |
| S12 | OPS maths toolkit | Wealth figures |
| S13 | μ/σ² derivation; strong OLS baseline | Standalone profitability |
| S14 | Cost-curve practice; lead-lag decay; session split | Nonlinear claim; tradability of Sharpes |
| S15 | Scaling law; MA artefact; gap biases | Part 3 as evidence of reversion |
| S16 | Negative checklist | Every result |
| S17 | Canonical TD rules | Predictive frequency claims |
| S18 | Textbook stylised facts | Formulas (errors) |
| S19 | TTM parameters (NEXA provenance) | Claims of power; "no gap risk" |
| S20 | Archetype catalogue | Results (none) |
| S21 | Hedge-vs-forecast; avalanche maths; decay/capacity | Self-reported returns |
| S22 | Delay-d vocabulary; TSMOM algebra; cost shrinkage | Second-hand empirics; HP/KNN traps |
| S23 | HAR/QLIKE/DM; commonality; intraday→daily | Equities-only transfer |
| S24 | Learning-dynamics maths; tick-size trade-off | Market data (none) |
| S25 | OU/VAR + Riccati toolkit | Liquidation superiority (n.s.) |
| S26 | Information ablation; walk-forward | Public-data LOB direction edges |
| S27 | First-passage maths | β precision |
| S28 | QA checklist | Benefits claims |
| S29 | Exposure vs priority decomposition | "Up to 60 %"; V–A independence |
| S30 | Mechanism catalogue (stale-quote sniping, last look, liquidity withdrawal) | Magnitudes; causal volatility claim |
| S31 | Governance (operational envelope, kill switch); TCA benchmark principles | Vendor statistics |
| S32 | Textbook principles (costs, adverse selection, skill vs luck) | Anything beyond the chapter openings present |
| S33 | Cautionary example | All results |
| S34 | Imbalance → trade sign evidence | Transfer to NEXA (no depth) |
| S35 | Naive-benchmark lesson; VG for tails | Direction/level forecasts |
| S36 | Causal-innovation and fixed-at-entry P&L rules (as lessons) | All results |
| S38 | Intervalling / variance-ratio kernel | Prop 1 conclusion |
| S39 | Density evaluation toolkit; quantile triggers | Regressor timing; thin backtest |

---

## 4. What NEXA should use, test, and avoid (summary)

**USE now (methods/principles, no data gaps):**
- P1 cost curves and E_eff gate;
- P5 strong baselines first;
- P6 candidate counting with DSR/PBO;
- P7 delay-0 vs delay-1;
- P8 random-walk/OU nulls;
- P13 driftless TP/SL null;
- P15 gap/weekend conventions;
- S31 operational envelope + deviation kill switch (governance);
- S39 PIT/log-score and coverage tests for any volatility or quantile model.

**TEST (hypotheses; see RESEARCH_HYPOTHESIS_BACKLOG):**
- volatility layer: H-VOL-1..4, H-ROUGH-1, H-VR-SCALE, H-VAR-TRIGGER;
- regime descriptors: H-HURST-GATE, H-THICKNESS-ER, H-TSMOM-TANH;
- session/time effects: H-SESSION-SPLIT, H-FIX-FLOW, H-GOTOBI/H-OPEN-CONT, H-NEWS-PTD;
- execution realism: H-NEWS-SLIP, H-STOP-SLIP, H-LASTLOOK-REJECT, H-DEVIATION-OPT (when logs exist);
- payoff null: H-HIT-PROB;
- method hygiene: H-DELAY-PARITY, H-COST-SHRINK, H-SEARCH-DEFLATE, H-NOISE-OBJ, H-ABLATE.

**AVOID:** FAILED_IDEAS §E (the do-not-use list) and §F (data/cost-limited for NEXA).

---

## 5. Novel concepts (relative to standard retail/quant practice) worth keeping

| Concept | Source | Why novel/useful |
|---|---|---|
| Information ablation (blinded vs full features) | S26 | Quantifies *where* information lives before modelling |
| Optimal discretion δ* = cost of a miss | S10 | Turns MT5 `deviation` into an economic parameter |
| Spread as a strangle written to latency arbitrageurs | S11 | Explains spread ∝ σ × toxic share |
| Lévy-area ≡ antisymmetrised lag-1 cross-covariance (our derivation) | S14 + INFERENCE | A cheap, causal lead-lag statistic |
| Noisy-objective test before optimising | S04 | Prevents selecting noise |
| MA-detrending artefact (α̂ ∝ 1/window) | S15 | A pre-test for every band/MA reversion idea |
| Driftless two-barrier null P = L/(U + L) | S27 maths + INFERENCE | A null for every TP/SL rule |
| Quantile-of-density triggers with fixed frequency | S39 | Regime-adaptive gates without frequency drift |
| Operational envelope + no live parameter changes + deviation kill switch | S31 | Matches NEXA's frozen-protocol governance |
| Exposure impact vs priority gain decomposition | S29 | Framework for any passive-order decision |
| Speed bump / arrive-simultaneously routing | S30 | The remedy for stale-quote risk is not speed |
| Variance-ratio by sampling interval | S38 + S31 | Prevents cross-time-frame mis-sizing |

---

## 6. Redundant ideas (same statistic under different names)

| Underlying quantity | Names in the corpus |
|---|---|
| Net change / sign of N-bar return | "Major trend" (S01), TSMOM sign (S02, S22), MOMP (S20), momentum histogram (S19), Kassouf ln(X/X̄) (S21) |
| Deviation from a moving average | %b and bands (S09), z-score (S16, S36), MA distance (S01 VB bug), OLMAR (S12), squeeze/KC (S19), LMA/SMA (S38) |
| Range or volatility state | ATR, BandWidth, squeeze (S09, S19), DM/V V (S01), RV (S23), ATR-relative spread caps |
| Up vs down move ratio | RSI (S01, S22, S16), TDI (S07) |
| Depth imbalance | I₀, B, W(i), log-imbalance, microprice (S29, S27, S34, S26, S13) |
| Path efficiency | Kaufman ER = \|DM\|/V (S01), thickness/overlap (S01) |
| Equal-risk sizing | 1/σ (S02, S03, S22 TSMOM), vol targeting (S22 §15.3.1) |
| Kelly-like sizing | μ/σ² (S13), max-Sharpe diagonal (S22 eq. 373), log-optimal (S12, S21) |

**INFERENCE:** testing several "different" indicators from the same row multiplies tests without adding independent information. Count them as one family in any multiple-testing correction.
