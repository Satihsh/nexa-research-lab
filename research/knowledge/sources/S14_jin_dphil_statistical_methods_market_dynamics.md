# S14: Qi Jin, *Statistical methods in financial market dynamics and portfolio strategies* (DPhil thesis, University of Oxford, July 2025)
**File:** `Jin_2025_Statistical_methods_in.pdf`. 181 pp.
**Supervisors:** Á. Cartea and M. Cucuringu (OMI). Funded by OMI / Man Group. Collaborators include Mungo Wilson.

| Field | Value |
|---|---|
| **Source type** | Oxford / university DPhil thesis (examined; chapters are working papers, not stated as published). |
| **Evidence status** | **Ch. 4 lead-lag:** research finding; 60 years of CRSP, cost sensitivity shown, several methodological caveats (below). **Ch. 5 volume shock → overnight:** strongly supported *statistical* finding (huge t-stats), but the tradable version is modest (Sharpe ≈ 1.0–1.1 out of sample, cost-free). **Ch. 6 clustering stat-arb:** research finding; **no transaction costs**; clustering adds nothing over FF12 industries in Sharpe. **Ch. 7 analysts:** weak; alpha t = 2.05 on overlapping 12-month returns. |
| **Processing** | Full text read, pp. 1–181 (5,596 extracted lines), including App. A.1–A.10 (proof of Thm 1, ranking alternatives, summary tables A.2–A.6, alternative hyperparameters A.7, compositions A.8, feature list A.9, GBDT/LightGBM/TabNet). Low-text pages (1, 2, 4, 9, 11, 101, 163) are title/blank/short pages. **Rendered and verified visually:** p. 56 (Fig 4.6 cost sensitivity, eq 4.7) and p. 75 (eq 5.2 overnight return). Other figures (4.1–4.5, 5.1, 6.1–6.5, 7.1–7.2, A.1–A.2) were read from text, captions and the extracted axis labels only. |

## Ch. 4: Lead-lag detection with the Lévy area (US equities, 1963–2022)
### Mathematics
- **Model** (4.1): R_A,t = β_A f_t + ε, and R_B,t = β_B f_t + β̃_B f_{t−ℓ} + ε. The common factor f is i.i.d. and latent; the lagged exposure represents slow information diffusion.
- **Cross-correlation tests** (eqs 4.2–4.3):
  - C1 = argmax_ℓ Corr(R_A,t, R_B,t−ℓ). Low power when β_B > β̃_B.
  - C2 is a signed max-correlation difference. It cannot report "no lead-lag", so it produces false positives.
  - Footnote 5 defines **size/power backwards**. Size = P(Type I); power = 1 − P(Type II).
- **Signature / Lévy area** (eqs 4.4–4.5, App. A.2): A_{i,j} = ½(S^{i,j} − S^{j,i}).
- **Prop. 1 / Thm 1:** if ℓ = 1, E[A_{A,B}] = −E[A_{B,A}] = k_{g,f} β_A β̃_B. If ℓ ≠ 1, E[A] = 0. Nonlinear exposure g needs E[f g(f)] ≥ 0.
- **Our verification of the App. A.3 proof** (eq B.5): the "path" coordinates are the *(standardised) returns themselves*. The discrete Lévy area is then
  - ½ Σ_a (X^j_a X^i_{a−1} − X^i_a X^j_{a−1}),
  - i.e. **an antisymmetrised lag-1 cross-covariance**.
- **INFERENCE (important):**
  - Any g with E[f g(f)] > 0 also produces non-zero linear lag-1 correlation. The class of relationships the Lévy area detects at ℓ = 1 is therefore the same as lag-1 cross-covariance. The claimed "nonlinear" advantage is not established by Thm 1.
  - The empirical differences from C1/C2 come from antisymmetrisation and restriction to lag 1, not from capturing nonlinearity.
  - The proof also shows **any lag ℓ ≥ 2 gives zero**: the method is blind to multi-period lags at the sampling frequency.
- **Ranking:** column means of the skew-symmetric lead-lag matrix. Alternatives in App. A.4: SpringRank ≈ column-mean; SerialRank / SyncRank weaker, Sharpe 1.4–1.8.
- **Clustered variant:** spectral and Hermitian clustering on the lead-lag matrix.

### Portfolio (Algorithm 1)
- 60-day window; top-25 % market-cap universe (~550 stocks).
- Leaders = top 20 %, followers = bottom 20 %.
- Signal: if the mean leader return at t−1 ≥ 0, go long followers and short SPY; otherwise reverse.

### Results (SOURCE; Table 4.1, cost-free)
- **Global Lévy portfolio:** 24.87 %/yr, 8.82 bp/day, vol 0.59 %/day, **Sharpe 2.38**, MDD 24.7 %.
  - Checks: 8.82/59 × √252 = 2.37 ✓; (1.000882)^252 − 1 = 24.9 % ✓.
- Max-corr Sharpe 2.37; avg-corr Sharpe 2.21.
- Benchmarks: market-cap (Lo–MacKinlay) Sharpe 0.75; turnover (Chordia–Swaminathan) Sharpe 1.37.
- **Costs** (Fig 4.6, rendered):
  - turnover ≈ 111 %/day;
  - the Lévy portfolio's Sharpe falls to ≈ 1 at 4 bp per dollar traded and to 0 at ≈ 7–7.5 bp;
  - the benchmarks reach 0 at ≈ 4 bp.
  - The author claims close-auction execution means "no bid-offer spread".
- **Frequency decay** (Table 4.5): Sharpe falls from 2.37 daily to 1.23 every 2 days, 1.22 weekly and 0.86 monthly.
  - The advantage of daily over lower frequencies emerges sequentially from the 1970s to the 1990s (Table 4.6). This is the "slow information diffusion" interpretation.
  - Panel B of Table 4.6 is mislabelled "50 %" (it should be 100 %).
- **Factor regression** (Table 4.8): residual alpha ≈ 10–11 bp/day, R² 12.6 %. FF5 loadings are insignificant.
- **Lead-lag identity is unstable:** relationships rarely stay profitable beyond about 6 months, and sector leadership rotates (Fig 4.4).
- **Alternative universe** (Table 4.9): returns are higher but vol is about 4× higher; **Lévy MDD 91 %**, Market-cap MDD 99.6 %.

### Critical assessment
- **Execution-timing look-ahead risk (INFERENCE):**
  - The signal uses the leaders' close-to-close return ending at t−1, and the trade earns the return from close t−1 to close t.
  - Close-auction (MOC) orders must be submitted *before* the closing price is known. Using the close price to form the signal and to execute at that same price is a same-bar assumption, the same issue the author flags for Ch. 5's volume shocks.
  - The edge is concentrated at a 1-day horizon (Sharpe halves at 2 days), so this timing assumption is material.
- Turnover is above 100 %/day, so the result is cost-fragile.
- Sharpe and t-statistics are not deflated for the many variants tried (3 scores × ranking/cluster choices × windows × quantiles).

## Ch. 5: Volume shocks and overnight returns (CRSP 2000–2022)
- **Volume shock:** S_{i,t} = V_t / EMA_{t−1}(V) − 1, with EMA half-life 60 days.
- **Overnight return** (eq 5.2, rendered p. 75): R^on_{i,t} = (1 + R^cc_{i,t}) / (1 + R^oc_{i,t+1}) − 1.
  - **As printed, the index t+1 in the denominator is inconsistent.** The overnight return into day t requires R^oc_{i,t}. Probably a typo.
- **Result** (Table 5.1, "oracle" portfolios):
  - Top-quintile volume shock, **equal-weighted overnight: 71 %/yr, Sharpe 4.76, t = 22.8.** Value-weighted: 17 %/yr, Sharpe 1.20.
  - Next-day intraday: no monotonic effect.
- Factor regressions (Table 5.2): long–short overnight alpha 22.7 bp/day (EW, t = 62) and 3.7 bp/day (VW).
- **Fama–MacBeth premium** (Table 5.3): +0.38 overnight (t = 41), −0.15 intraday (t = −16), stable across 2000–09, 2010–19 and 2020–22.
  - The text says the night premia are "smaller … than when the market is open". This contradicts its own table.
- **Market regression** (Table 5.4): adding the VS portfolio raises overnight adjusted R² from 3.9 % to 17.5 %.
- **Tradable version** (Table 5.5): volume shock is predicted from information up to the open; OOS 2016/17–2022, value-weighted long-only top quintile.

  | Model | OOS R² | Sharpe |
  |---|---|---|
  | OLS | 0.178 | 1.00 |
  | TabNet | 0.333 | 1.08 |
  | Oracle | — | 1.11 |

  - The relationship between prediction R² and Sharpe is **concave**: doubling R² adds about 8 % Sharpe.
- **Table typo:** value-weighted Day Q3 Sharpe printed 0.98 should be ≈ 0.10 (0.63 bp / 1.02 % × √252).
- **Critical (INFERENCE):**
  - The EW overnight Sharpe of 4.76 includes small/illiquid stocks. Close-to-open returns embed bid-ask bounce and closing-auction imbalance (prints at bid/ask), so the EW "oracle" magnitude is likely inflated by microstructure.
  - The VW tradable Sharpe ≈ 1 is the realistic figure, still cost-free and long-only (its market beta is not netted).

## Ch. 6: Correlation-matrix clustering stat-arb (2000–2022, ~600 large caps)
- **Pipeline:**
  - market-residual returns (60-day β to SPY);
  - correlation matrix;
  - signed clustering: SPONGE, SPONGE_sym (generalised eigenproblem (L⁺ + τ⁻D⁻, L⁻ + τ⁺D⁺)), spectral on |C|, signed Laplacians L_rw and L_sym;
  - within each cluster, short previous winners and buy previous losers vs the cluster mean (w = 5 days);
  - rebalance every ℓ = 3 days; stop-win q = 5 %.
- **Number of clusters:** Marchenko–Pastur upper edge λ₊ = (1 + √ρ)², or 90 % variance explained, on a 20-day window; or fixed K = 30.
  - Eq. text writes C = (1/N) XᵀX; normalisation should be 1/T (as written it is wrong).
- **Results** (Table 6.1, **cost-free**): annual return 10–12 %, Sharpe 0.85–1.11, Sortino 1.5–2.0.
  - **The FF12-industry benchmark has Sharpe 1.08**, the same as the clusters. SPY: Sharpe 0.32.
  - ARI vs FF12 is about 13–15 %.
- **Critical (INFERENCE):**
  - A 5-day correlation matrix on about 600 stocks has rank ≤ 4, so 10–30 clusters from it are largely noise.
  - Equal Sharpe for random-ish clusters and industries suggests the P&L is generic **short-term (5-day) reversal**, not cluster structure.
  - No costs at roughly 3-day turnover, so the economic significance is UNKNOWN.

## Ch. 7: Alpha in analysts (IBES price targets, 1999–2024)
- Per-analyst long–short portfolio weighted by target-implied 12-month returns; alpha vs an EW long-only portfolio of the stocks covered.
- **Average analyst alpha ≈ 0.**
- Share of analysts significant at 5 %: 8.8 % overall, 12.5 % among those with more than 5 years' experience. Binomial tests reject chance.
  - The binomial test assumes independent analysts, but cross-sectional correlation (shared stocks and market) inflates significance (INFERENCE).
- **"Fund-of-analysts"** (expanding regression on 6 predictors, using data only up to t−12):
  - Sharpe 0.41 vs baseline 0.39; alpha 2.36 %/month, **t = 2.05**.
  - The observations are **overlapping 12-month returns sampled monthly**, and no HAC correction is reported, so t is overstated (INFERENCE).
  - FF3 loadings: market β 1.58, SMB 1.14. Not neutral.
- **Source errors:**
  - p-value 0.2919 in the table vs 0.284 in the text;
  - "baseline outperforms by ~2 % per month" is inconsistent with the 12-month figures;
  - the App. A.1 claim that "Wynn Resorts has larger market cap than Disney" is very likely factually wrong (UNVERIFIED).

## Principles extracted
1. **SOURCE:** cross-asset lead-lag at short horizons exists in large-cap equities. It is **non-stationary**: pairs decay within months and sector roles rotate. It is strongest at the shortest horizon and was arbitraged toward faster horizons over the decades.
2. **SOURCE:** day/night decomposition matters. The same signal can have opposite-sign premia overnight and intraday (also Hendershott et al. 2020).
3. **SOURCE:** prediction quality and portfolio value are concavely related. Modest predictability captures most of the value.
4. **INFERENCE:** many "data-driven" edges in this thesis are cost-free and/or rely on same-close execution. Treat them as upper bounds.

## NEXA relevance
- **Lead-lag across NEXA instruments (H-LEADLAG-FX):**
  - Apply the antisymmetric lag-1 cross-covariance (≡ discrete Lévy area) to NEXA's symbols (XAU, XAG, EURUSD, GBPUSD, USDJPY, indices) at M5/M15/H1 bars, with rolling windows.
  - **Data:** NEXA has bars. **Look-ahead risk:** use only fully closed bars and execute at the next bar's open + spread, not the signal bar's close (cf. D-EXEC-ENTRYBAR lesson).
  - **Expected:** any edge decays fast (1-period horizon) and may be below Pepperstone spreads. Cf. S02/S03 cost sensitivity.
  - **Earlier finding:** the lead-lag study was DATA-LIMITED. Re-check with this method before any claim. Evidence level: hypothesis.
- **Session decomposition (H-SESSION-SPLIT):**
  - Decompose any NEXA signal's P&L into Asia / London / NY / rollover segments. Signals can carry opposite-sign premia by session.
  - Data available (server time = NY+7; use the established time conventions).
- **Methodological:**
  - (a) Always report the cost curve (Sharpe vs per-trade cost) as in Fig 4.6.
  - (b) Deflate Sharpe for variant count (Bailey–López de Prado DSR, cited in Ch. 6).
  - (c) Correct overlapping-return t-stats (HAC).
  - (d) Check rank and noise of any correlation matrix before clustering (window ≫ N).
- **Not usable:** volume-shock overnight (CFD tick volume is not exchange volume, and FX/metals trade nearly 24h). Analyst targets (no data).

**Cross-references:**
- S25 (Cartea: stat-arb / OU / cointegration);
- S12 (online portfolio, mean reversion);
- S22 (151 Strategies: pairs, cross-sectional reversal);
- S23 (Zhang/Cucuringu: commonality, ML vs linear, intraday → daily);
- S26 (Cartea group: walk-forward logit; information ablation);
- S02 (cost fragility of high-turnover signals).
