# STATISTICAL KNOWLEDGE BASE: validation, inference and bias control

What the 39-file corpus (38 distinct works; S37 = S06) teaches about measuring, testing and *not fooling ourselves*. Every item cites its source(s). Batch-2 sources (S27–S39) are integrated into the tables below and summarised in §11.

| Tag | Meaning |
|---|---|
| SOURCE | Stated in the source |
| INFERENCE | Our reasoning |
| HYPOTHESIS | An untested proposal |

This file is the methodological companion to MATHEMATICAL_KNOWLEDGE_BASE.md. It is written to be applied to **any** future NEXA research.

---

## 1. Out-of-sample design: what the rigorous sources actually did

| Source | Design | Strength | Weakness |
|---|---|---|---|
| S23 (volatility ML) | Train on [start, t−251], validate on the last year, test the next year. Annual retraining; test period Jul-2015 → Jun-2021. Plus an **unseen-stock** test. | Gold standard in the corpus. Diebold–Mariano tests and an economic-utility metric **with costs**. | US equities only. |
| S26 (agent predictions) | Rolling 4-week train → 1-week deploy, ×12. Expanding window gives the same results. PCA fitted on weeks 1–4 only. | Explicitly causal preprocessing. Baseline-relative accuracy. **Information ablation.** | Latency not modelled. |
| S02 (DMN) | Expanding window, recalibrated every 5 years. Hyperparameter search re-run each block (50 random iterations). OOS 1995–2015. | Walk-forward. | No multiple-testing correction across 16 loss × architecture choices. Block dispersion ±2.08 Sharpe. Cost-free headline. |
| S03 (DRL) | 5-year retrain blocks; OOS 2011–2019. | Walk-forward. | One run per algorithm; no seeds or CIs. MDD figures unreliable. |
| S13 (sizing) | Train / validate / test months within 2018; test months 8–12. | — | One year; tuning months adjacent to the test; 5-month test. |
| S14 Ch. 5 | Tradable version predicts volume shock from information up to the open; OOS 2016/17–2022. | Separates "oracle" from tradable. | Cost-free; long-only beta not netted. |
| S14 Ch. 7 | Expanding regression using data up to t−12. | Causal. | Overlapping 12-month returns, no HAC: t = 2.05 overstated. |
| S25 | 24h estimation → 12h trading, rolling 357 times. | Rolling. | No significance test (our SE check: not significant vs Almgren–Chriss). |
| S04 | Single-date calibration. | — | No OOS; MC-noise-dominated objective. |
| S12 | Best-Sharpe grid selection; a walk-forward is "described". | — | UNKNOWN whether the reported tables are OOS. Frictionless. |
| S08 | "OOS" 2016–2018 for strategy 3 overlaps the development period (2008–2016). | — | Filters chosen after seeing results; no costs. |
| S16 | None (full-sample). | — | In-sample only; trade-resampling MC claimed as an overfitting test. |
| S21 | Rules derived from and tested on 1946–66. | Honest about rediscovery. | In-sample by modern standards. |

**SOURCE principle (S22 glossary, p. 314):**
- An **out-of-sample backtest** uses for time t only quantities computed from data *before* t.
- A **delay-d backtest** uses data at least d trading days before t (p. 291).

**INFERENCE:** most retail and practitioner material (S01, S07, S08, S09, S16, S17, S19, S20) has **no OOS design at all**. The academic material mostly does, but frequently with cost-free headline numbers.

## 2. Execution timing and look-ahead traps (catalogue)

| # | Trap | Where seen | Correct practice |
|---|---|---|---|
| L1 | **Delay-0:** trading at the same price used to form the signal | S22 App. A: "borderline in-sample", real orders "could never be executed exactly at the open"; delay-1 "expected to backtest much worse" | Report delay-0 and delay-1 side by side; the gap measures the timing illusion (H-DELAY-PARITY). |
| L2 | **Same-close execution** (signal from close t−1, trade at close t−1) | S14 Ch. 4 lead-lag (MOC orders must be sent before the close is known); S14 Ch. 5 flags it for volume shocks | Execute at the next bar's open + spread (NEXA D-EXEC-ENTRYBAR lesson). |
| L3 | **Two-sided filters** (HP, centred MA, Kalman *smoother*, full-series wavelets) | S22 §8.1 (HP on FX), S15 (symmetric MA in OU calibration), S01 Ch. 28 ("semaphore" displaced back half the period), S20 (wavelet SVM) | Recursive or one-sided filters re-estimated each bar. |
| L4 | **Overlapping forward targets in k-NN / ML** | S22 §3.17 (neighbour targets with t′ < t + T) | Purge neighbours and targets whose horizon overlaps t (t′ ≥ t + T); embargo. |
| L5 | **Swing / zig-zag confirmation lag** | S01 GSCS (Return, intersections), S08 fractal | Mark swings only once confirmed by data available at that time. |
| L6 | **Normalisation using future statistics** | S02 winsorisation (causality UNKNOWN); S13 states backward-only | Expanding or rolling statistics only. |
| L7 | **Survivorship** | S22 App. A (not handled; "not detrimental" for intraday is an over-claim); S12 claims a survivor-free list | Point-in-time universes. Mostly N/A for NEXA (fixed symbols), but relevant to broker symbol history. |
| L8 | **Calendar and time-zone misalignment** | S01 App. D (fixed GMT offsets, no DST); NEXA memory: server = NY+7, MT5 calendar stamped with the export-time offset | Convert all timestamps to UTC with DST rules before event alignment. |
| L9 | **Index-level data treated as tradable** | S16 (NEPSE index); S14 Ch. 5 equal-weighted overnight (bid-ask bounce inflates it) | Tradable instrument, with costs and executable prices. |
| L10 | **"Oracle" vs tradable predictor** | S14 Ch. 5 (oracle Sharpe 1.11 vs predicted 1.00–1.08) | Always report the tradable version. |
| L11 | **Adaptive re-estimation booked as P&L** (hedge ratio updated after entry used to value the position) | S36 Kalman stat-arb: ε_{t+h} − ε_t with γ_{t+h} at exit | P&L must use parameters fixed at entry; z-scores from causal innovations only. |
| L12 | **Holdout inside the selection loop** | S33 GenFX: "IS & OOS → robustness testing → population"; S02 per-block random search (milder) | A frozen, never-consulted holdout (NEXA V2 prospective 2027); log every candidate evaluated. |
| L13 | **Same-day regressors in an "ex-ante" density/trigger** | S39 EGARCH-X: day's average spread, intraday range, ΔVIX, EUR/USD and oil returns (timing UNKNOWN) | Lag every regressor to information available before the decision. |
| L14 | **Train/test split not stated as chronological** | S34 (one-third/two-thirds of one month; UNKNOWN whether random) | Chronological splits with an embargo for autocorrelated data. |
| L15 | **Promised-but-absent proofs / unstated parameters** | S29 Prop 1 proof absent; S36 thresholds, look-back, V_w/V_e undisclosed; S33 fitness transform "special formula" | Treat as unverifiable; do not reuse numbers that depend on hidden choices. |

## 3. Inference: significance, dependence and multiple testing

- **Sharpe statistics (S16 cites Lo 2002 and Jobson–Korkie; S14):** the standard error of the Sharpe ratio depends on autocorrelation and non-normality. The √252 annualisation assumes i.i.d. returns.
  - INFERENCE: S16's z = 4.01 Sharpe test ignores serial correlation and the selection process.
- **Overlapping returns (S14 Ch. 7):** monthly sampling of 12-month returns induces MA(11) errors. Use Newey–West / HAC; otherwise t is overstated.
- **Cross-sectional dependence (S14 Ch. 7):** binomial "share of significant analysts" tests assume independence. Common shocks inflate significance.
- **Multiple testing / data snooping:**
  - S14 cites the Bailey–López de Prado deflated Sharpe ratio (DSR) but does not apply it to its own variant grid.
  - S22's 1,951-entry bibliography has only 3 data-snooping references (Sullivan–Timmermann–White 1999; Suhonen et al. 2017; Hsu et al. 2018) and no PBO/DSR/Harvey–Liu.
  - S01 App. B lists Aronson's *Evidence-Based Technical Analysis* but does not use it.
  - INFERENCE: across the corpus, **no source applies a multiple-testing correction to its own reported best result.**
  - **NEXA rule:** count variants and report a deflated or probability-of-backtest-overfitting (PBO)-style statistic.
- **Forecast comparison (S23):**
  - Diebold–Mariano on loss differentials; Gu–Kelly–Xiu cross-sectional averaging.
  - QLIKE rather than MSE for volatility (robust to proxy noise).
- **Baseline-relative accuracy (S26):** report gain over the majority class (+18 pts direction), not raw accuracy.
- **Unseen-entity tests (S23):** train on other assets, test on a held-out asset. This shows mechanism universality.
- **Information ablation (S26):** blinded features cut direction accuracy from 70 % to 54 %. This quantifies *where the information lives*.
- **Monte Carlo misuse (S16):** resampling a strategy's own trades only reshuffles order. It cannot detect overfitting or selection.
  - Correct uses: random-entry nulls, block bootstrap of market returns, or synthetic nulls (random walk / OU with matched volatility, S15).
- **Noisy objective (S04):** the MC cost function has an SD of 9.53 % of its mean.
  - INFERENCE: if the objective's own noise exceeds the parameter effect, selection is noise. Measure objective noise by reruns or bootstrap **before** optimising (H-NOISE-OBJ).
- **Significance of mean P&L differences (S25, our check):** $2.7k difference vs SE ≈ $2.9k (n = 357), so not significant. Always compute SE = sd/√n.
- **Overlapping windows sampled finely (S27):** β = 116.6 with t = 22.45 from regressing 60-minute-ahead returns on 60-minute imbalance changes **sampled every minute**: ≈ 59/60 overlap ⇒ MA(59) errors; t is overstated by roughly √60 ≈ 7.7× if errors are near-perfectly overlapping (INFERENCE, order-of-magnitude). Use non-overlapping windows or HAC.
- **Tests on binned conditional means (S29):** correlations computed on per-bin MLE estimates (bins of imbalance) and significance at 0.001 overstate precision; two crisis months only.
- **Mass univariate screening (S36):** ≈ 100 ADF tests per year at a conventional level ⇒ ≈ 5 false "cointegrated" stocks expected by chance; year-to-year turnover of the selected set is consistent with noise.
- **Search size and the expected maximum (S33):** under no skill, the best of K Sharpe estimates is ≈ √(2 ln K) standard errors above zero; K ≈ 480k ⇒ ≈ 5.1 SE. A deflated Sharpe / PBO is mandatory for any sweep (H-SEARCH-DEFLATE).
- **AUC at low base rates (S34):** AUC ≈ 0.72 with jumps ≈ 10–15 % of events implies modest precision; report calibration (Brier, reliability) and precision–recall, not AUC alone.
- **Naive benchmarks (S35):** MAPE of 14–34 % for weekly price levels is *worse* than the random-walk no-change forecast (≈ 2–4 %). Report Theil's U or MAPE / MAPE_naive.
- **Thin VaR backtests (S39):** 15 exceedances at nominal 5 % over ≈ 200 days (expected ≈ 10) without Kupiec/Christoffersen coverage tests; PIT over 4 months only. Apply unconditional and conditional coverage tests.
- **Single-use randomness (S31 UBS; S32 Ch. 22):** "a single use of a strategy is highly random"; skill vs luck needs many observations; algo-wheel samples are small (S31 Afett).
- **TCA noise (S31 Sancetta; S32 Ch. 21):** execution-cost estimates are dominated by timing (market) risk; per-order comparisons are meaningless without large n.

## 4. Estimator bias and finite-sample effects

| Effect | Magnitude (SOURCE) | Source | Implication |
|---|---|---|---|
| OU mean-reversion speed α̂ | Upward bias O(1/T); about +1,400 % at T = 1 yr, τ_rev = 5 yr | S15 Table 5.2 | Distrust half-lives estimated from short windows; jackknife/bootstrap corrections. |
| Weekend gap handling | Linear interpolation: σ̂ about −20 %. Business time: about +25 % (√(168/108) ✓) | S15 Ch. 5 | Document and test NEXA ATR/volatility conventions (H-GAP-VOL). |
| Irregular sampling treated as regular | Biased σ̂ and α̂; random-time sampling worst | S15 | Tick or bar irregularity matters (Sunday open, holidays). |
| Hurst from daily RV | Upward bias (daily integration smooths) | S04 | Use intraday RV and finer Δ. |
| Detrending | Creates spurious OU with α̂ ∝ 1/window | S15 + INFERENCE | Null-test every MA-relative signal on a simulated random walk. |
| Sample covariance | Singular if T ≤ N + 1; unstable unless T ≫ N | S22 fn. 62, S14 Ch. 6 | Factor or shrinkage covariance. 5-day correlation on 600 stocks has rank ≤ 4. |
| Log-log fit R² | R ≈ 0.999 trivially on overlapping points | S15 (INFERENCE) | R² is not evidence of a scaling law. |
| Win rate | Structurally inflated by exit asymmetry | S08 (87.5 % with win/loss 0.29), S02 (hit rate ≈ 50 % yet Sharpe varies) | Judge expectancy and skew, never hit rate alone. Compare with the driftless two-barrier null L/(U + L) (MATH M1b). |
| Measured volatility vs sampling interval | Per-unit variance (1 − e^{−θh})/(θh) under OU; VR < 1 with bounce, > 1 with trend | S38 (+ S15, S31 HSBC Fig. 4) | State bar size; test variance ratios before transferring ATR/vol across time frames (H-VR-SCALE). |
| "Level variance ÷ interval" normalisation | Diverges as h → 0 for any bounded process | S38 Prop 1 (artefact) | Use increment variances, not level variances. |
| Overlapping-window t-statistics | t inflated by ≈ √(overlap) | S27 β, S14 Ch. 7 | HAC / non-overlapping samples. |

## 5. Transaction costs: the dominant failure mode

| Source | Cost result |
|---|---|
| S02 | Most ML edges vanish at **2–4 bps**. At 10 bps the LSTM's Sharpe is −5.3 (total loss); the turnover regulariser rescues it to 0.91. |
| S03 | DQN/A2C remain positive to 25 bp. **But the cost basis differs from S02's** (not comparable). |
| S13 | Every strategy's Sharpe is < 0 at **0.06 bp**, far below the actual 0.5 bp spread. |
| S14 Ch. 4 | Lévy lead-lag: Sharpe 2.38 → ≈ 1 at 4 bp → 0 at ≈ 7 bp. Turnover ≈ 111 %/day. |
| S12 | OPS mean reversion (CWMR 1590×) is a frictionless artefact. ~100 % daily turnover is erased by 10–20 bp (INFERENCE). |
| S08 | 2.4 pips gross per trade with zero cost assumed; a ~1-pip spread removes about 40 %. |
| S10 | Retail-relevant execution value is about $3.80/€M (≈ 0.4 bp), the size of fees. |
| S22 App. A | Linear cost τ = ζσ/ADDV, mean 10 bp; E_eff shrinkage. |
| NEXA (prior project facts) | XAU all-in cost ≈ 18.8 % of R at micro-stops (8E audit); ≈ 3.5 % of R at an M15 ATR stop (S02 note). |
| S36 | Kalman stat-arb with up to 12 legs + index rebalanced daily, **no costs, no borrow**. |
| S33 | Cost/spread settings of ≈ 480k MT5 backtests unspecified. |
| S31 | Aggressive TWAP ≈ ½ spread per child; slower execution beats risk-transfer price on average but adds variance; TCA dominated by time risk. |
| S30 | Latency-arbitrage "tax" ≈ 0.07 % of notional on one large order (author's extrapolation); stops/market orders fill through levels when liquidity withdraws. |
| S32 | Costs = explicit + implicit + **missed-trade opportunity cost**; most active traders lose because costs exceed their information advantage (Ch. 22 opener). |

**Principles:**
1. **SOURCE + INFERENCE:** report the **cost curve**, i.e. Sharpe vs per-trade cost (S14 Fig 4.6). Single-point cost-free numbers are upper bounds.
2. **Put costs inside the objective** (S02 eq. 35, S03 eq. 4). A turnover penalty in training changes *what is learned*.
3. **Cost is regime-dependent:**
   - news: slippage tail ×6 (S10); spreads balloon and gaps appear (S01);
   - Sunday open: illiquid (S01);
   - rollover: XAU spread jump (NEXA tick audit).
   - A single average cost understates tail cost.
4. **Fill selection:** last-look rejections (S11), sniping of slow limits (S06) and adverse selection of misses (S10) mean realised costs exceed quoted spreads in exactly the trades that would have won.

## 6. Overfitting and selection bias: corpus-wide patterns

- **Selected examples presented as evidence:**
  - S01: 15 trades, 14 of 17 winners vs the authors' own "lose 70 %";
  - S17: three hand-picked charts;
  - S19: hand-picked intraday charts;
  - S07: no data at all;
  - S08: "favourites of my students".
- **Post-hoc filters:** S08 (skip Fridays; skip if Close₃ > 0.5 % move); S01 ME-profile reviews every 10 trades.
- **Data mining without control:** S01 "bathtub analysis" ("what happens on the 5th hour after 2 up + 2 down hours?"); JOSTAN FX "100+ indicators, 5,000+ parameter sets".
- **Parameter insensitivity claim:** S01 Ch. 21 "results seldom varied by more than 5 %" across filters (unverifiable).
  - INFERENCE: robustness to parameters is desirable but must be shown with metrics, costs and OOS.
- **Grid selection by best Sharpe:** S12 (Anticor 8 configurations, etc.); S02 (50-iteration random search per block).
- **"Badge" heuristics are not validation:** S20 QuantConnect "Likely Not Overfit".
- **Strong baselines beat or tie complex models:**
  - S13: Bayesian OLS Sharpe 1.39 ≈ deep models; adding uncertainty sizing to OLS lowers it.
  - S23: at 1 day, HAR ≈ NN; OLS with good features captures most of the gain.
  - S26: the random forest adds only ≈ 5 points over logit, and **information** matters 10× more than nonlinearity.
  - S14 Ch. 6: random-ish clusters ≈ FF12 industries.
  - S03: long-only ≥ RL in equities.
  - **INFERENCE (cross-source agreement):** start with the simplest strong baseline; complexity must earn its keep out of sample.
- **Batch-2 overfitting patterns:**
  - S33: automated strategy generation with the holdout in the loop (≈ 480k candidates);
  - S36: undisclosed thresholds, re-fitted hedge ratios valued as P&L, five overlapping "OOS" windows ending on the same date;
  - S35: many uncorrected t-tests (19 stocks × 2 models × 2 methods × 3 periods × 2 metrics);
  - S29: "up to 60 %" improvement is a modelled number under estimated parameters, not a realised result;
  - S30/S31: magnitudes from interested parties, single trades extrapolated to market totals.
- **Strong-baseline lesson repeated:** S39 GARCH variants are statistically equivalent and beat quantile regression and unconditional KDE (Hansen–Lunde: hard to beat GARCH(1,1) for daily FX); S35 complex Q-models lose to the naive no-change forecast.

## 7. Regime dependence and out-of-sample (OOS) stability

| Evidence of non-stationarity | Source |
|---|---|
| FX trend-following negative 2011–2019 (Long and Sign(R) < 0) | S03 |
| Trend-following tested in the favourable 1995–2015 regime | S02 |
| Lead-lag pairs decay within about 6 months; sector leadership rotates; the daily advantage emerged over decades | S14 Ch. 4 |
| Cluster stability above random for ASML/ING, unstable for AHOLD/TOMTOM | S26 |
| Daily commonality turbulent (R² SD 0.198) vs stable intraday | S23 |
| Edge decay through rediscovery ("when enough money is invested… it will be ruined"); capacity $4.6–15M | S21 |
| "Strategies die" (NYSE Hybrid Market 2006 killed stat-arb); alphas are "faint, ephemeral" | S22 Ch. 1 |
| Fundamental drivers rotate (money-supply era; yield vs growth regimes) | S01 Ch. 4, 23 |
| Popular chart patterns abort as traders anticipate them | S01 Ch. 3, 18 |
| Regime-conditional evaluation recommended: split results by DM/V environment; prefer methods that "do not collapse in the weaker" regime | S01 Ch. 28 |
| FX "used to trend" (coordinated central banks), now behaves like other markets; "markets trend 25–30 % of the time" (unverified) | S17 |
| March 2020: fine-scale (30 s) volatility spiked more than 2-hour volatility; algo usage rose; spreads for large swaps several × normal | S31 (HSBC Fig. 4, BestX chart; proprietary) |
| Flash crash 2010, mini flash crashes, outage cluster 2012–13; liquidity providers withdraw in stress | S30 |
| Daily FX density widens and skews in COVID-19; VaR exceedances 7.5 % vs nominal 5 % | S39 |
| HFT algos' one-second predictions failed in Sep 2008 (Aleynikov quote) | S30 Ch. 5 |
| Cointegrated stock sets change every year (4, 12, 5, 8, 4 names) | S36 |
| Imbalance → price impact decays within tens of seconds; asymmetric (+3/−1 bp) | S29 |
| Market structure changes rules of the game (Reg NMS 2007, decimalisation, fragmentation) | S30, S32 |

**INFERENCE (methodology):**
1. Validate with **blocked / rolling OOS** and report **per-block dispersion** (S02's ±2.08 is the honest number).
2. Evaluate **per regime**: volatility tercile, ER/trendiness tercile, session, news window.
3. Treat any edge found in one regime as conditional until it is shown in others.

## 8. Metric selection

| Metric | When | Source |
|---|---|---|
| QLIKE (+ MSE) with DM test | Volatility forecasts | S23 |
| Realised utility (with costs) | Economic value of volatility forecasts | S23 |
| Sharpe, Sortino, MDD, cents-per-share, annualised return | Strategy P&L (state the cost basis) | S22 App. A, S12, S16 |
| Sharpe vs cost curve | Any turnover-heavy signal | S14 Fig 4.6, S02 Exhibits 6–8 |
| Baseline-relative accuracy | Classification | S26 |
| Permutation importance | Feature attribution | S26 |
| Expectancy in R units and skew; never hit rate alone | Discretionary/retail-style rules | S08, S01, S02 |
| Pips per hour of trading | Practitioner productivity (S01): not a statistical metric | S01 |
| Average R vs break-even p* = 1/(1+R) | Payoff design | S01 + INFERENCE |
| PIT histogram/ECDF with bands; log score; Diks test | Density / quantile forecasts | S39 |
| Kupiec / Christoffersen coverage | VaR / quantile triggers (missing in S39) | INFERENCE |
| AUC **plus** calibration and precision–recall | Rare-event classification | S34 + INFERENCE |
| MAPE / MAPE_naive, Theil's U | Level forecasts | S35 + INFERENCE |
| Benchmark-relative cost (arrival mid, independent reference), incl. opportunity cost of misses | Execution quality / slippage studies | S32 Ch. 21, S31 (BestX, NCFX, Sancetta) |
| Fill rate, round-trip time, post-trade mark-out (impact at 10/30/60 s) | Liquidity-source curation | S31 (HSBC, Commerzbank) |
| Number of candidates evaluated; deflated Sharpe / PBO | Any search or sweep | S33 + S14 citation |

## 9. Null models and controls (to make claims falsifiable)

- **Random-walk null** with matched volatility for any MA-relative or band signal (S15 artefact). Also a random-walk null for the S01 GSCS "Return ≈ 50 %" claim.
- **OU null** to check scaling-law curvature (S15 eq. 4.3).
- **Random-entry null** with identical exits, to separate entry skill from exit-induced payoff shape (S08 outside-bar).
- **Buy-and-hold / drift null** (S03 long-only; S16 B&H; NEXA XAU "gold trend = drift").
- **Majority-class null** for classifiers (S26).
- **Blinded-information null** (S26 ablation; H-ABLATE).
- **Industry/cluster null** for clustering (S14: FF12).
- **Cost-zero vs cost-real** pair for every result (S02, S14, S22).
- **Driftless two-barrier null** for TP/SL rules: P(target first) = L/(U + L) and zero expectancy before costs (MATH M1b; S27 maths).
- **Naive no-change forecast** for any level forecast (S35); unconditional density and GARCH(1,1) for any density forecast (S39).
- **Coverage tests** (Kupiec, Christoffersen) for any quantile/VaR trigger (S39 gap).
- **Re-estimation-free P&L** check for adaptive models (S36): recompute P&L with parameters frozen at entry.
- **Shuffled-holdout check** for automated search (S33): the holdout must never have been seen by the generator.

## 10. What the corpus does NOT provide (data and method gaps)

- No **FX or XAU intraday volatility-forecasting study.** S23 is equities; S15 is scaling, not forecasting. The transfer is HYPOTHESIS.
- No **retail CFD execution data** (S10 is LMAX exchange; S11 is theory). Pepperstone fill behaviour is UNKNOWN until logged.
- No **deflated Sharpe / PBO application** anywhere.
- No **test of practitioner pattern claims** (TD, Squeeze, GSCS, Dagger, BTMM, Nofri).
- No **session-level FX study** (S14's day/night is equities).
- No **XAU-specific statistical study.** Gold appears only inside futures panels (S02, S03), in practitioner slides (S19), in the Shanghai BC claim (S01), and as an executable precious metal in FX algo menus (S31 directory). Still true after batch 2.
- **Batch 2 adds one FX density-forecast study** (S39, MXN daily) and one FX volatility-structure chart (S31 HSBC, proprietary). Neither covers XAU or intraday NEXA horizons.
- No **study of retail CFD broker fills, requotes or stop slippage** (S30/S31 are institutional/equity; S10 is LMAX). H-STOP-SLIP and H-LASTLOOK-REJECT need NEXA's own logs.
- No **source supplies Pepperstone depth data**; all imbalance results (S13, S26, S27, S29, S34) remain DATA-LIMITED.

## 11. Batch-2 summary (S27–S39): what changed in the statistical picture

| Source | Statistical lesson | Strength |
|---|---|---|
| S27 | First-passage maths is sound; the empirical β is precision-inflated by overlap | Maths established; β weak |
| S28 | QA checklist for order logic; no inference | Descriptive |
| S29 | Model-implied gains are not realised gains; binned-mean significance overstated | Research finding |
| S30 | Mechanisms (stale-quote sniping, liquidity withdrawal) consistent with academic sources; magnitudes unverified | Anecdotal |
| S31 | Governance: calibration vs choice data, operational envelope, null/simple alternative, deviation kill switch | Practitioner consensus |
| S32 | Skill vs luck; selection bias "probably accounts for more trading losses than any other mistake"; cost = benchmark-relative | Established (textbook) |
| S33 | Holdout-in-loop invalidates OOS; search size must be reported | Failed |
| S34 | Imbalance predictability is real at the next-event horizon (AUC 0.72) but depth-data dependent | Research finding |
| S35 | Q-models cannot forecast direction; naive benchmark mandatory | Failed |
| S36 | Adaptive-parameter P&L accounting error; multiple ADF testing | Flawed |
| S37 | Duplicate of S06 | — |
| S38 | Sampling interval changes measured volatility; normalisation artefacts | Model-only |
| S39 | Density forecasts: PIT + log score + Diks; GARCH baseline; coverage tests missing | Research finding |
