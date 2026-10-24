# FAILED IDEAS, UNSUPPORTED CLAIMS AND ERRORS

Corpus: 39 files, 38 distinct works. Built 2026-10-02.

**What counts here:**
- A claim, method or result that **failed** on its own evidence or under our verification.
- A claim that is **contradicted** by stronger evidence.
- A claim presented **without supporting evidence**.
- A **mathematical/formula error**.

Each item gives its reference. Section A = failed/contradicted; B = unsupported; C = errors; D = recurring failure patterns; E = do-not-use list for NEXA; F = ideas that fail *for NEXA specifically* (data or cost).

---

## A. Failed or contradicted claims and results

| # | Claim / result | Source | Why it fails | Status |
|---|---|---|---|---|
| A1 | GenFX "robustness testing on out-of-sample data" | S33 §2.10, Fig 9 (rendered) | The OOS period is inside the GA selection loop over ≈ 480k backtests, so it is fitted. No costs, no P&L, no live test | **Failed** (invalid validation) |
| A2 | Predicting stock direction with GBM/VG + QMC/LSMC | S35 | Hit rates ≈ 46–56 % ("near random walk", authors). Under Q the drift is r by construction. Level MAPE 14–34 % is worse than the naive ≈ 2–4 % | **Failed** |
| A3 | Kalman-filter S&P 500 stat-arb: 19.3 %/yr, Sharpe 3.30 | S36 Tables 4–8 | P&L uses γ_{t+h} at exit, manufacturing reversion. ~100 ADF tests/yr; no costs/borrow; undisclosed thresholds; overlapping windows | **Failed** (accounting invalid) |
| A4 | "Monte Carlo of 20,000 paths rules out overfitting" | S16 | Resampling the strategy's own trades cannot detect selection or overfitting. The whole study is in-sample on an untradable index | **Failed** (method misused) |
| A5 | Online portfolio selection wealth (CWMR 1590×, PAMR 788×) | S12 | Frictionless; ≈ 100 %/day turnover erased by 10–20 bp (INFERENCE); parameters chosen by best Sharpe | **Failed as evidence of edge** (artefact) |
| A6 | "The Lévy area captures nonlinear lead-lag" | S14 Ch. 4 | Its own Thm 1 reduces to the antisymmetrised lag-1 cross-covariance; any lag ≥ 2 gives zero | **Contradicted** (by its own proof) |
| A7 | fBm with H < ½ is "mean-reverting with exponentially decaying ACF" | S18 §3 | Power-law ACF H(2H − 1)n^{2H−2} (S04); anti-persistent increments ≠ OU | **Contradicted** |
| A8 | "Shorter trading intervals raise buy-and-hold portfolio volatility" (Prop 1) | S38 | Bounded level variance divided by h diverges for any process; fixed-horizon P&L does not depend on reporting frequency | **Failed** (artefact) |
| A9 | Optimal AMM execution beats Almgren–Chriss | S25 Table 3 | $2.7k mean advantage vs SE ≈ $2.9k (n = 357); no significance test | **Not significant** |
| A10 | Uncertainty-based sizing as a standalone strategy | S13 | All Sharpe ratios < 0 at 0.06 bp, against a 0.5 bp spread (authors concede) | **Failed at real cost** |
| A11 | Transfer of Sharpe 2.8 deep momentum | S02 | Edge gone at 2–4 bps; LSTM Sharpe −5.3 at 10 bps; ±2.08 block dispersion | **Failed under costs** |
| A12 | Classical TSMOM in FX (2011–2019) | S03 Table 2 | Long −0.353, Sign(R) −0.306 | **Failed** (regime) |
| A13 | Opening-range breakout implementation; SVM-wavelet FX example | S20 p. 22, p. 57 (rendered) | 0 trades ("insufficient data"); flat/negative (PSR 0 %, −$553) | **Failed / no evidence** |
| A14 | GSCS "predictive" and its "15,000-example computer test" | S01 Ch. 27 | Test announced, no results; 3C carry-over rule makes the system unfalsifiable | **Unsupported / unfalsifiable** |
| A15 | Three "Beat the Markets" strategies | S08 | Cost-free, single vendor, post-hoc filters (skip Fridays, > 0.5 % move), overlapping "OOS" (2016). Strategy 1 is 87.5 % hit with win/loss 0.29 at 2.4 pips gross | **Failed as evidence** |
| A16 | SRFG calibration "better" (lower cost) | S04 Ch. 11 | Re-simulation error is worse than SLSQP; the cost difference is inside MC noise (SD 9.53 % of mean) | **Failed** (noise) |
| A17 | Iceberg vs limit order "up to 60 % improvement" | S29 Figs 8–9 | Model-implied under estimated parameters; V–A independence ignores adverse selection | **Unsupported as a realised result** |
| A18 | Imbalance–drift β = 116.6, t = 22.45 | S27 Table IV | Overlapping minute-sampled 60-minute windows, no HAC; precision grossly overstated (sign plausible) | **Precision failed** |
| A19 | MA-detrended OU calibration demonstrates FX mean reversion | S15 Ch. 6 | α̂ ∝ 1/window and variance ∝ window follow automatically for a random walk; the author concedes "inconclusive" | **Failed** (artefact) |
| A20 | Correlation-matrix clustering adds stat-arb value | S14 Ch. 6 | Sharpe ≈ FF12-industry benchmark (1.08); 5-day matrices on ~600 stocks have rank ≤ 4; no costs | **No added value shown** |
| A21 | "Fund-of-analysts" alpha (t = 2.05) | S14 Ch. 7 | Overlapping 12-month returns sampled monthly, no HAC; market β 1.58 | **Not significant once corrected** (INFERENCE) |
| A22 | PRISM-Bridge validation | S05 | Synthetic data; impossible tier scores; consistency check skipped | **No validation** |
| A23 | "$160M per day tax" on US equity investors | S30 Ch. 2 | Single 10M-share trade ($29k saved) extrapolated linearly to all volume | **Unsupported magnitude** |
| A24 | Lewis's "Scalpers Inc." volatility link (intraday volatility +40 % 2010–13 vs 2004–06) | S30 Ch. 4 | Before/after comparison across the crisis aftermath, no controls | **Unsupported causal claim** |
| A25 | "Volume shock → overnight" oracle Sharpe 4.76 as tradable | S14 Ch. 5 | Equal-weighted small caps embed bid/ask bounce and auction imbalance; the tradable VW version ≈ 1.0, cost-free, long-only | **Upper bound, not tradable** |
| A26 | Lévy lead-lag Sharpe 2.38 as tradable | S14 Ch. 4 | Same-close MOC execution assumption; ≈ 111 %/day turnover; Sharpe 0 at ≈ 7 bp | **Upper bound** |

**NEXA prior facts in the same category** (from project results, not the corpus):
- 8E Squeeze UNPROVEN;
- TD veto CONTRADICTED;
- momentum not net-positive;
- Donchian negative on EUR/GBP;
- OFI NOT TESTABLE.

See CONTRADICTIONS §C.

---

## B. Unsupported or unverified claims (no evidence presented in the source)

| Source | Claims (representative) |
|---|---|
| S01 | Post-news "price-trace-dispersement" reverses shocks; EUR/GBP and GBP/CHF lead EUR/USD "by a day or two"; Tokyo-open yen moves continue for days; "≥ 75 % of markets exhibit time rhythm" (in at least one of many time frames: chance-guaranteed); Jonathan's Wave "48 %/yr with zero expectation of a 50 % drawdown"; "> 95 % of traders fail"; "breaking even puts you ahead of 90 %"; Hartnagle "results seldom varied by > 5 %"; ME "high-DM/low-V evolves into low-DM/high-V at tops" |
| S07 | Market-maker 3-day cycle; "follow the money"; candlestick/TDI signals |
| S09 | Profitability of Methods I–IV; head-fake frequency; Babcock's preference for volatility breakouts |
| S17 | "Markets trend 25–30 % of the time"; completed 13s mark tops/bottoms "4–5 times a year"; endorsements by bank strategists (authority, not evidence) |
| S19 | "One red dot as powerful as 20"; "trailing stops get hit before the trend has run"; "futures have no gap risk" (also false) |
| S21 | Author cash record (5 years, no losses, ~25 %/yr), self-reported and unaudited |
| S22 | Every "empirical studies suggest…" statement (second-hand; the book has no backtests by design) |
| S28 | Icebergs "reduce slippage", "maintain liquidity" |
| S30 | HFT/dark-pool profit magnitudes ($1bn/yr dark-pool arbitrage from 15 days; Tabb $20bn/yr; Schwab "left ≥ $1bn"); "the market is rigged" as a general claim; SEC revolving-door count (RBC study, unreleased) |
| S31 | JPM algo share and volume growth (single firm); "all studies suggest Siren saves cost" (Raidne); "Pure Decay" metric (undefined); NCFX's claim that platform TCA mis-measures impact (plausible but marketing) |
| S35 | "Significant returns earned in the first 30 minutes of trading" (JSE), no statistics |
| S20 | "Reduce transaction costs by 18–22 %" (Investopedia footnote) |

---

## C. Mathematical / formula errors and documented inconsistencies

**At least 26 mathematical/formula errors in 10 sources** (verified by re-derivation or rendered pages; details in the source notes):

| # | Source | Error | Correct form |
|---|---|---|---|
| 1 | S01 | DM/V example prints DM = 0.9, V = 4.3 | DM = 0.6, V = 4.0 (prices also look like USD/JPY) |
| 2 | S01 | Five-currency equilibrium uses ÷ GBP/CHF | × GBP/CHF |
| 3 | S01 | "FOREX beta" = ratio of trend slopes, then ratio of price-level SDs | β = Cov/Var of returns; level SDs are scale/trend-dependent |
| 4 | S01 | VB6 volatility loop uses `Q(i)` for `Q(j)` | Computes \|C_i − SMA\|, not dispersion/path length |
| 5 | S01 | Thickness = (H1 − L1)/(H2 − L2) | Inconsistent with "overlap of consecutive ranges" |
| 6 | S04 | Def 4.5.4 Γ(H − ½) | Γ(H + ½) |
| 7 | S04 | Sign glitch in the Mandelbrot–Van Ness variance constant | Cosmetic |
| 8 | S04 | Eq. 9.1.1 labelled "ATM forward volatility" | It is the ATM **skew** |
| 9 | S05 | Tier averages 1.05/0.62/0.18 from a 1–5 weighted sum (Σw = 1) | Must lie in [1, 5] |
| 10 | S10 | "v̄_d = 1.2v̄" | 0.8v̄ (§3.5.3) |
| 11 | S10 | Heston SDE written with v instead of √v | √v diffusion (likely extraction/typo) |
| 12 | S14 | Size and power defined backwards (fn. 5) | Size = P(Type I); power = 1 − P(Type II) |
| 13 | S14 | Eq. 5.2 uses R^oc_{t+1} in the overnight return into day t | R^oc_t |
| 14 | S14 | C = (1/N)XᵀX | (1/T)XᵀX |
| 15 | S14 | VW Day Q3 Sharpe printed 0.98 | ≈ 0.10 (0.63 bp / 1.02 % × √252) |
| 16 | S18 | Eq. 3.6 rBergomi variance without exponential | σ² = ξ₀ exp(η√(2H)Z − ½η²t^{2H}) |
| 17 | S18 | Eq. 4.7 σ_T = √(1 − ρ)σ₀ | √((1 − ρ²)(1/T)∫σ²ds) |
| 18 | S18 | ACF "exponentially decaying" | Power law |
| 19 | S18 | brentq described as minimising (BS − p̂)² | Root-finding on BS(σ) − p̂ |
| 20 | S22 | "1 + κ = 1/(1 + τ_c)" (p. 104) | 1/(1 − τ_c) |
| 21 | S22 | Eq. 535 "softmax" Y_i/ΣY_j | exp(Y_i)/Σexp(Y_j) |
| 22 | S29 | I(Δ) printed with "I₀ − Δ_rN_r" | I₀ + Δ_rN_r (from its own numerator definition) |
| 23 | S36 | Spread P&L with γ_{t+h} at exit | P&L with γ fixed at entry |
| 24 | S36 | log ∏ γ√S^i (root) | log ∏ (S^i)^γ (power) |
| 25 | S38 | Prop 1 σ²_BH = σ_q²(h)/h as "unit-period variance" | Use increment variance per unit time σ²(1 − e^{−θh})/(θh) |
| 26 | S38 | Eq. 6 LMA/SMA = exp(w′Q) as an identity | Holds for geometric (log) means only; ignores µt |

**At least 15 further table/label/text inconsistencies:**
- **S01:** R:R vs stated 1:3; trade #14 "50 pips" vs +59.
- **S04:** Table 11.6 caption repeats the SLSQP parameters; ρ −0.848 vs −0.847; Table 10.1 "80 %" twice; unresolved citation "[?]".
- **S12:** "Best Stock" mislabelled as hindsight; EG = CRP to 4 decimals.
- **S14:**
  - Table 4.6 Panel B "50 %";
  - p-value 0.2919 vs 0.284;
  - night-premium text vs table;
  - Wynn/Disney market-cap claim (UNVERIFIED).
- **S16:** MC 20k vs 10k; sensitivity numbers text ≠ table; H1/H2 mix-up; ADF test mentioned but not reported.
- **S28:** duplicate "4th Block" label.
- **S29:** Δt 10 s vs 30 s; gain location text vs caption; Prop 1 proof promised but absent.
- **S33:** abstract vs conclusion; loose/incorrect Sharpe description.
- **S35:** Table 2/3 attribution; Tables 4 and 8 swapped headers.
- **S36:** "20010–2015"; Table 6 header mismatch; ticker "CAN".
- **S39:** "minimum-rate" should be "no-minimum-rate".

**Correction of our own earlier statement:** the batch-1 MATHEMATICAL_KNOWLEDGE_BASE said "12 confirmed errors across S01, S04, S05, S14, S18 and S22". That undercounted even batch 1 (it omitted S10 and several S01/S14 items). The figures above supersede it.

**One correction to our own notes** (not a source error): in the S21 summary an earlier note said "Kelly ref [14]"; ref [14] is Markowitz (1959). Kelly is not cited in S21 (corrected in S21 §4).

---

## D. Recurring failure patterns (cross-source)

| Pattern | Instances | Countermeasure |
|---|---|---|
| **Cost-free results** | S08, S12, S14 Ch. 4–6, S16 (exit-only 0.25 %), S20, S29 (model), S33 (unknown), S36, S02/S03 headline numbers | Cost curve; costs inside the objective; E_eff gate (H-COST-SHRINK) |
| **Selected examples as evidence** | S01 (14/17 winners), S07, S09, S17, S19, S08 ("favourites") | Full denominators; random-entry nulls |
| **Holdout contamination / in-sample only** | S33 (OOS in GA loop), S16 (full-sample tuning), S08 (post-hoc filters), S21 (normal curves fitted on the evaluation period), S12 (best-Sharpe grids) | Frozen prospective holdout (NEXA V2 2027) |
| **Multiple testing without correction** | S33 (≈ 480k), S36 (~100 ADF/yr), S35 (many t-tests), S02 (random search), S14 (variant grid), S01 (bathtub, JOSTAN 5,000+ parameter sets) | Count variants; deflated Sharpe / PBO (H-SEARCH-DEFLATE) |
| **Look-ahead / timing** | S22 delay-0, HP filter, KNN; S14 same-close; S01 centred "shape"; S20 full-series wavelets; S36 re-fitted γ; S39 same-day regressors (UNKNOWN) | STAT KB §2 L1–L15 |
| **Wrong benchmark or none** | S35 (no naive), S16 (Sharpe vs B&H with 50 % exposure), S25 (no SE), S12 ("Best Stock") | Naive, drift, majority-class, and blinded nulls |
| **Artefacts mistaken for effects** | S15/S38 (detrending, normalisation), S12 (bounce), S14 Ch. 5 (bounce), S04 SRFG (MC noise) | Simulated random-walk / OU nulls; noise measurement |
| **Overlapping-sample significance** | S27 β, S14 Ch. 7 | HAC / non-overlapping |
| **Interested-party magnitudes** | S30, S31 | Treat as hypotheses; require independent data |
| **Model-implied ≠ realised** | S29 "60 %", S11 (no empirics), S24 (simulation), S38 (no data) | Empirical test before reliance |

---

## E. Do-not-use list for NEXA (explicit)

1. The S01 showcased trade results as evidence; Mundo/FOREX beta as defined; "shape" with centred MAs; GSCS 3C carry-over; Archer's ME VB code without fixing the bug.
2. Any S08 backtest number, S12 OPS wealth figures, S16 results, S20 Strategy-Explorer badges.
3. Two-sided filters (HP, centred MAs, Kalman *smoothers*, full-series wavelets) in any signal (S22 §8.1, S01, S20).
4. KNN/ML targets that overlap the forecast horizon (S22 §3.17).
5. Q-measure (risk-neutral) models as direction forecasters (S35); LSMC as a forecaster.
6. Kalman/adaptive hedge P&L computed with re-estimated parameters (S36).
7. GA/automated EA generation without a never-seen holdout and a candidate count (S33).
8. S38's conclusion that faster trading raises portfolio risk.
9. S07's market-maker narrative as a trading premise.
10. Any LOB-imbalance or microprice signal (S13, S26, S27, S29, S34): DATA-LIMITED at Pepperstone.
11. S30/S31 magnitudes as quantitative inputs (qualitative mechanisms only).
12. S02/S03/S14 headline Sharpe ratios as achievable targets.
13. Illegal or ethically excluded "strategies" in S22 (§17.2 money laundering, §17.6 loan sharking): descriptive only, never actions.
14. S32 statements beyond the chapter openings actually present in the file. The rest of Harris's book is **not in the corpus** and must not be cited as read.

---

## F. Ideas that fail for NEXA specifically (data or cost), not in general

| Idea | Why not for NEXA (now) | Source |
|---|---|---|
| Order-flow imbalance / microprice / queue position | No depth volumes or trade signs at Pepperstone | S13, S26, S29, S34, S27 |
| Cross-feed lead-lag (CFD vs COMEX/futures) | No second synchronous feed (V2 "cross-feed latency" BLOCKED) | S25, S30 (Chicago → NJ) |
| Carry / swap backtests | No historical swap series | S22 §8.2 |
| Speculative passive MLO execution gains | ≈ 0.4 bp, below spread granularity | S10 |
| Optimal liquidation (Almgren–Chriss) | Retail size: impact negligible | S25, S32 |
| Volume-shock overnight effects | CFD tick volume ≠ exchange volume; FX/metals trade ~24 h | S14 Ch. 5 |
| Iceberg / hidden-order strategies | No order book at the broker | S27–S29 |
| Latency arbitrage / speed | Retail latency; and the strategy class is predatory/HFT domain | S30, S10, S22 §8.5 |
| Analyst-target alpha | No data | S14 Ch. 7 |
| Option/warrant strategies | NEXA trades spot CFDs | S04, S18, S21, S22 Ch. 2 |

## G. NEXA-tested strategy candidates (2026-10-11)

| Idea | Result | Artefact |
|---|---|---|
| C1 Tokyo-fix / gotobi USDJPY | Gross effect real (+2.17 bp, beats 44/44 placebos); **not tradable**: net −0.58 bp at retail cost | `research/intelligence/validation/C1_REPORT.md` |
| C2 TSMOM, daily FX + XAU (8 instruments) | **REJECTED**: net −0.19 %/mo (snapshot swaps); ex-swap +0.12 %/mo n.s. | `research/intelligence/validation/C2_REPORT.md` |


### OFC1: user's core order-flow method (VAL/VAH big-trade bubble + footprint confirmation), 2026-10-11

**Verdict: INSUFFICIENT-N, with every estimate negative (no edge).** Pre-registered; true CME aggressor data (Databento) for 6E/6J/6B/GC, Dec 2025 → Sep 2026.
- **Results:** 130 trades; −0.21 R/trade net; disc / val / hold all negative.
- **Benchmarks:**
  - worse than random-timing entries with the same stops and targets (−0.05 R);
  - order-flow confirmation beat no confirmation (−0.37 R over 1,143 trades) by +0.16 R, not significant.
- **Do not:** re-tune on these data.
- **Open:** a frozen-rule replication on unseen 2023–25 history (needs purchase approval).
- **Report:** `research/intelligence/validation/OFC1_REPORT.md`.
- **OFC1R (final replication, 2026-10-11): REJECTED.**
  - **Results:** frozen OFC1 rules on unseen 6E 2023-01→2025-08: 211 trades, −0.12 R/trade net, every year negative; no better than random timing; DSR 0.0007.
  - **Status:** the OFC1 line is CLOSED by user decision. No further purchases or variants.
  - **Report:** `research/intelligence/validation/OFC1R_REPORT.md`.

### IM1: market intraday momentum (last half-hour), 2026-10-11

**Verdict: REJECTED net, gross CONFIRMED.**
- **Results:** 8,660 trades on EUR / GBP / JPY / XAU, 2017–2026. Gross +0.35 bp/trade (FX ≈ +0.5 bp, close-specific in EUR / GBP); net −1.08 bp (S1); every year negative. Gold shows no effect.
- **Lesson:** the C1 pattern again (real effect, cost ≈ 2× edge).
- **Possible levers** (execution cost, not signal), each needing a NEW pre-registration on unused data: passive or limit entries, a lower commission tier.
- **Report:** `research/intelligence/validation/IM1_REPORT.md`.

## FX1: daily FX fix reversals (Krohn, Mueller & Whelan 2024): REJECTED (net) 2026-10-11

- **Test:** pre-registered (`research/intelligence/validation/PREREG_FX1_FIX_REVERSALS.md`, report `FX1_REPORT.md`). Pepperstone EURUSD / GBPUSD / USDJPY, 2017-07 → 2026-09, 20,424 trades.
- **Gross confirmed:** +0.70 bp per trade, CI > 0; 9/9 signs match the paper at ~¼ size; timing beats 41 placebo shifts (p 0.024).
- **Net:** S1 −0.63 bp [−1.00, −0.22]; S0 −0.13; post-2020 −0.60; 2 of 10 years positive.
- **Lesson** (same as C1, IM1): intraday FX anomalies of 0.3–2 bp do not survive ≈ 1 bp market-order round trips.
- **Do not retry** with altered windows or cells. W3 USDJPY +0.53 is a post-hoc cell. Only new pre-registered cost-reduction or prospective tests.
