# 12: NEW MATRIX MODELS

**Each matrix lists:**
- dimensions;
- variables;
- units;
- meaning;
- update frequency;
- source;
- normalisation;
- missing-data handling;
- causal timestamp;
- interpretation;
- statistical test;
- feasibility.

"Feasibility" uses the 03 status codes.

**Global rules:**
- **Causal timestamp:** every entry at time t uses bars closed before t (03 §3).
- **Missing data:** a matrix is *not computed* if any required input block is unavailable. No imputation.

---

## M-01: Market State Matrix  𝐗 ∈ ℝ^{N_inst × d}

| Field | Specification |
|---|---|
| Dimensions | Rows: instruments (EURUSD, GBPUSD, USDJPY, XAUUSD; optional XAGUSD). Columns: the d state variables of 09 §4 (blocks x^P, x^V, x^L, x^S, x^F, x^T, x^X, x^E) |
| Variables / units | All normalised (σ̂ units, seasonal ratios, percentiles); see 13 for each column |
| Meaning | Snapshot of every instrument's observable state at decision time |
| Update | Every decision bar (1 min); slow columns (HAR σ̂, profile) once per bar but from closed data |
| Source | MT5 M1 / ticks; Massive futures (context columns) |
| Normalisation | Per column, as in the feature catalog |
| Missing data | Proxy columns flagged; unavailable blocks (x^O) absent |
| Interpretation | The input to P(outcome \| x) |
| Statistical test | Column-wise stationarity (rolling mean/var by year); cross-column collinearity (VIF > 10 → drop or orthogonalise) |
| Feasibility | **AVAILABLE** (minus the options block) |

## M-02: Liquidity Matrix  𝐋 ∈ ℝ^{N_price × N_time} (per instrument)

| Field | Specification |
|---|---|
| Dimensions | Price grid (σ̂-scaled bins around the current price, e.g. ±4 σ̂_day, 81 bins) × time (bars) |
| Variables / units | L(p,t), volume per price unit, normalised to a density (∫L dp = 1) |
| Meaning | The revealed-liquidity field (06) |
| Update | Each bar (developing session) and each session end (completed profile) |
| Source | Spot tick volume (proxy) or futures volume via the basis (true) |
| Normalisation | Unit mass; bandwidth ∝ σ̂ |
| Missing data | Bars with zero activity contribute nothing; sessions with < 50 % bar coverage are flagged |
| Interpretation | HVN = ridges, LVN = valleys; g, κ derived along price |
| Statistical test | Proxy agreement (VA Jaccard, \|ΔPOC\|/σ̂) between sources (06 §2); HYP-004–007 |
| Feasibility | **AVAILABLE** (proxy); TRUE for futures (2 y) |

## M-03: Order Flow Matrix  𝐅 ∈ ℝ^{N_inst × N_lag}

| Field | Specification |
|---|---|
| Dimensions | Instruments × lags ℓ = 1…L (1-min bars) |
| Variables | δ̃_{t−ℓ} (BVC on futures; tick-rule on spot), seasonal percentile πδ, RVOL, ABS |
| Units | δ̃ ∈ [−1,1]; percentiles ∈ [0,1] |
| Meaning | Recent signed-activity history (proxy) |
| Update | Each bar |
| Source | Massive futures (BVC); MT5 ticks (f30/f31) |
| Normalisation | Shares and percentiles (EQ-010) |
| Missing data | Futures closed or illiquid (roll week, holidays): column absent, not zero |
| Interpretation | **PROXY.** Lag 0 forbidden in predictive use |
| Statistical test | HYP-017 (lagged predictive β); HYP-022 (conditional MI at levels) |
| Feasibility | **APPROXIMABLE only** |

## M-04: Option Positioning Matrix  𝐎 ∈ ℝ^{N_strike × N_expiry}

| Field | Specification |
|---|---|
| Dimensions | Strikes × expiries (front monthly, weekly) |
| Variables | OI, IV, Γ, vanna, charm per series; the sign model |
| Meaning | Dealer positioning (if the sign is right) |
| Update | Daily (OI is prior-session) |
| Source | **None available.** It would need COMEX OG OI plus quotes (19) |
| Missing data | Matrix not computed |
| Interpretation | Inputs to GEX (M-05) |
| Statistical test | Sign sensitivity (Model A vs C, S54 isolation experiment); OI stability |
| Feasibility | **UNAVAILABLE.** A GLD *volume* (not OI) version is APPROXIMABLE (HYP-028) |

## M-05: Gamma Exposure Matrix  𝐆 ∈ ℝ^{N_strike × N_spot-grid}

| Field | Specification |
|---|---|
| Dimensions | Strikes × hypothetical spot levels (for the repriced flip) |
| Variables | GEX_K(S) = sgn·OI_K·Γ_K(S)·M·S²·0.01 (EQ-027) |
| Meaning | Dealer hedge flow per 1 % move as a function of spot. Row sums give N(S); the root gives the flip |
| Update | Daily, plus intraday repricing with spot |
| Source | Needs M-04 |
| Normalisation | N(S)/(S²·0.01·M); HPR = \|N\|/DV (EQ-029) |
| Interpretation | Regime (sign of N at spot), flip, walls, HPR |
| Statistical test | HYP-025/026/027 |
| Feasibility | **UNAVAILABLE** |

## M-06: Regime Transition Matrix  𝐏 ∈ [0,1]^{K × K}

| Field | Specification |
|---|---|
| Dimensions | K regimes. Observed version: σ̂ tercile × ER tercile (K = 9). HMM version: K = 2–4 |
| Variables | P_ij = P(z_{t+1} = j \| z_t = i), per instrument and per session block |
| Meaning | Persistence and switching of market states |
| Update | Estimated on a rolling past window (e.g. 250 sessions); applied causally (filtered probabilities) |
| Source | MT5 bars |
| Normalisation | Row-stochastic; Dirichlet(1) prior; report posterior intervals |
| Missing data | Weekends and holidays excluded from transitions (no transition across a gap) |
| Interpretation | Diagonal ≫ off-diagonal means persistent regimes; a regime-conditioned outcome law is possible |
| Statistical test | LR vs the i.i.d. null (P_ij = π_j); stability across years (χ² homogeneity); out-of-sample log score of next-regime prediction |
| Feasibility | **AVAILABLE** |

## M-07: Signal Interaction Matrix  𝐒 ∈ ℝ^{d × d}

| Field | Specification |
|---|---|
| Dimensions | Feature × feature |
| Variables | Off-diagonal: interaction gain ΔLogScore(f_i × f_j) beyond main effects, or the conditional MI I(Y; f_j \| f_i). Diagonal: single-feature gain |
| Meaning | Which components *combine* (e.g. level × flow: WHERE × WHEN) |
| Update | Per research run (not live) |
| Source | Trade DNA labels + features |
| Normalisation | Bits or nats of log-score gain per 1,000 decisions |
| Missing data | Pairs involving unavailable features omitted |
| Interpretation | Supports the architecture's layering when the level→flow interaction is positive |
| Statistical test | Permutation null per cell; **FDR (Benjamini–Hochberg) across all d(d−1)/2 cells** |
| Feasibility | **AVAILABLE** (research) |

## M-08: Cross-Asset Matrix  𝐂(t) ∈ [−1,1]^{N × N} (+ lead–lag tensor)

| Field | Specification |
|---|---|
| Dimensions | Assets: EURUSD, GBPUSD, USDJPY, XAUUSD, XAGUSD, GC, 6E, ES, US10Y Δ (daily) |
| Variables | Rolling time-aligned correlations of 1-min / 1-h returns; lead–lag cross-correlations at lags ±1…±5 bars |
| Meaning | Co-movement; risk-on/off context; USD factor (f29 basket) |
| Update | Hourly (rolling window W) |
| Source | MT5 + Massive |
| Normalisation | Correlations; Fisher-z for comparisons |
| Missing data | Asynchronous trading hours: pairwise-complete, time-aligned by closed bar (S13 lesson) |
| Interpretation | **Non-stationary by assumption.** Used as context and for the correlation cap (risk), not as signal |
| Statistical test | Stability: correlation-of-correlations across windows; lead–lag significance with HAC; cost-adjusted value (expected to vanish) |
| Feasibility | **AVAILABLE** (indices like VIX unavailable) |

## M-09: Execution Quality Matrix  𝐄 ∈ ℝ^{N_inst × N_state × k}

| Field | Specification |
|---|---|
| Dimensions | Instrument × execution state (spread tercile × quote-intensity tercile × session × news flag) × k metrics |
| Variables | Mean and quantiles of signed slippage (points and R), fill latency, requote/reject rate, realised spread |
| Meaning | Expected cost c(x^E) for EQ-025 |
| Update | Each fill (S14 demo); summarised weekly |
| Source | Trade DNA (signed slippage since S14), NEXA_TickLogger |
| Normalisation | Points → σ̂ units and R |
| Missing data | Cells with < 20 fills are pooled up the hierarchy (instrument → all) |
| Interpretation | Feeds abstention and stop-distance choice |
| Statistical test | Quantile regression of slippage on state; out-of-sample pinball loss vs unconditional |
| Feasibility | **AVAILABLE prospectively** (demo from 2026-10-05) |

## M-10: Risk-State Matrix  𝐑 ∈ ℝ^{N_inst × m}

| Field | Specification |
|---|---|
| Dimensions | Instrument × m risk variables |
| Variables | σ̂ forecast (HAR), tail quantile (EVT/empirical), current open risk, correlation-cap state, daily budget used (C4), drawdown state, news proximity, gap risk (weekend) |
| Meaning | The state the deterministic risk engine reads |
| Update | Each bar |
| Source | MT5 + NEXA_Risk state |
| Normalisation | % equity and R |
| Missing data | **Fail-closed** (NEXA_Risk convention: unknown → refuse) |
| Interpretation | The risk engine stays deterministic. This matrix only *informs* research on sizing (H-VOL-2, H-VOLTARGET-CAP) |
| Statistical test | Calibration of VaR-type quantiles (Kupiec / Christoffersen coverage); H-VAR-TRIGGER |
| Feasibility | **AVAILABLE**. Changing NEXA_Risk is out of scope |
