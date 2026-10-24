# S15: Maria Elisabeth Boeker, *Scaling and mean reversion in foreign exchange time series* (PhD thesis, UCL Computer Science, Aug 2021)

**File:** `Maria Elisabeth Boeker PhD Thesis.pdf` (153 pp). Supervisors: G. Germano and J. James.

| Field | Value |
|---|---|
| Source type | University PhD thesis (UCL; not Oxford). Examined; not peer-reviewed as a whole. |
| Evidence status | **Scaling law** (Müller et al. 1990 mean-absolute-return law): *established stylised fact*, replicated here. **OU-estimator simulations:** *research finding* (Monte Carlo, well specified). **Part 3 (MA-detrended OU calibration ↔ Hurst):** *research finding*, but **it largely demonstrates an artefact**, as the author partially concedes. |
| Processing | Full text read, pp. 1–153 (5,265 extracted lines), including Appendix B tables and Appendix C figure captions. Appendix B tables B.3–B.7 extend the main tables 5.5–5.12 and were spot-read. 10 low-text pages are the Appendix A/C figure pages, read from captions. **Rendered and visually checked:** p. 77 (Figs 4.16–4.18, MARs before/after detrending) and p. 116 (Fig 6.5 DMA, Table 6.4). Other figures were taken from the text and captions. |

## 1. Data (SOURCE)
- **Thomson Reuters Eikon**
  - 17 pairs.
  - **Bid close** prices (not mid, despite the later "mid price" language) at 1d, 60m, 30m, 10m, 5m and 1m.
  - Daily history runs back about 40 years; minutely history about 40 days (downloaded Aug 2014).
  - Weekends were filled by **linear interpolation in physical time**.
- **Commerzbank**
  - Bank core quote streams (bid/ask) for 63 pairs, Jan 2015 – Dec 2016, London and NY sources. The median tick can be as small as 0.01 s.
  - After filtering (median tick < 1 s, ≥ 10k values, no recurring > 3-day gaps), 7 pairs remain: AUDJPY, AUDUSD, EURUSD, USDBRL, USDCAD, USDCHF, USDCNH.
  - The series were interpolated to a 0.2 s grid.
  - **XAUUSD and XAGUSD were present but excluded:** median tick about 2.1 s and 4.8 s, with only about 95 days of data.

## 2. Mathematics (verified)
### 2.1 Ornstein–Uhlenbeck (OU)
- **Process:** dX = α(µ − X)dt + σdW.
- **Exact discretisation:**
  - X_{i+1} = X_i e^{−αΔ} + µ(1 − e^{−αΔ}) + σ√((1 − e^{−2αΔ})/(2α)) ε;
  - stationary variance σ²/(2α).
- **Estimators:** least squares / maximum likelihood (eqs 2.25–2.32). b̂ = e^{−α̂Δ} from regressing X_i on X_{i−1}; α̂ = −ln b̂/Δ; µ̂ = â/(1 − b̂).
- **Bias corrections cited:**
  - jackknife (Phillips–Yu): α̂_J = (n/(n−1))α̂_whole − (Σα̂_part,i)/(n² − n);
  - bootstrap (Tang–Chen): θ̂_B = 2θ̂ − (1/n)Σθ̂′_i.
  - The bias of α̂ is O(1/T), positive, and largest near a unit root.
- **Mean absolute return of an OU** (eq 4.3; *verified*):
  - E|X_{t+Δ} − X_t| = σ√((2 − 2e^{−αΔ})/(πα)).
  - This follows from increment variance (σ²/α)(1 − e^{−αΔ}) and E|N(0,v)| = √(2v/π).
  - Limits: σ√(2Δ/π) as Δ→0, and σ√(2/(πα)) as Δ→∞. The log-log curve is linear and then flattens.
- **Trending OU** (Thierfelder): Var r_Δ → (σ²/α)(1 − e^{−αΔ}) ✓.
- **Time-dependent reversion level** (Sánchez–Gallego):
  - µ(t) = m(t) + ṁ(t)/α;
  - Euler least squares gives α̂ = Σ(Δx − ṁΔt)(m − x) / (Δt Σ(m − x)²) ✓.
- **Author's alternative:** subtract an MA, then apply known-mean OU maximum likelihood:
  - α̂ = −(1/Δ) ln(Σx_{i−1}x_i / Σx²_{i−1});
  - σ̂ from eq 5.9.

### 2.2 Scaling
- **Müller law:** ⟨|Δx|⟩_Δt = cΔt^E, i.e. the generalised Hurst H(q) at q = 1.
- **Generalised Hurst:** K_q(τ) ∝ τ^{qH(q)}. The process is multiscaling if H(q) is not constant.
- **Detrending moving-average analysis (DMA; Alessio et al.):** σ²(τ) = ⟨(X_i − SMA_τ,i)²⟩ ∝ τ^{2H}, giving H(2).
- **Guillaume:** directional-change count N(dr) = c′r^{E′}, with E′ ≈ −1/E.

## 3. Results (SOURCE)
### 3.1 Scaling law
- **Thomson Reuters, 1 min – 4 years:** median E = 0.567, mean 0.559, R ≥ 0.9948.
  - 16 of 17 pairs have E > 0.5; the exception is EURNOK at 0.476.
- **Commerzbank, 0.2 s – 7 days:** median E = 0.574, mean 0.585, R ≥ 0.9954.
  - USDCNH: E = 0.665.
- **Simulations:** both the random walk (Model 2) and an OU around a smoothed random walk (Model 1) give E ≈ 0.49–0.51.
  - **Neither reproduces E > 0.5.** The author suggests fractional noise would be needed.

### 3.2 Detrending (Figs 4.16–4.18, rendered)
- Subtracting an EMA from real FX **or from a pure random walk** produces an OU-like curve that flattens at a level set by the EMA window.
- **The author's conclusion:** "rendering our results inconclusive". A detrended random walk is indistinguishable from mean reversion. **There is no evidence of mean reversion to a constant level at observable scales.**

### 3.3 OU estimation under imperfect data (synthetic; Tables 5.1–5.13)
- **α̂ bias.** α̂ is positively biased, worst near the unit root and for short T. **The mean error is about +1,400 % when T = 1 year and the reversion time constant is 5 years** (Table 5.2).
- **Weekend gaps.**
  - Linear interpolation biases σ̂ by about **−20 %**.
  - "Business time" (closing the gap) biases σ̂ by about **+25 %**.
  - Neither bias depends on T.
  - *Our check:* in business time the 168-hour week is compressed to 108 steps, so σ̂² is inflated by 168/108 ≈ 1.556, i.e. σ̂ × 1.247 ✓.
  - Business time also inflates α̂ substantially. Interpolation is preferable for α̂.
- **Irregular sampling treated as regular** biases σ̂ and α̂, with a sign that depends on the parameter scale. Random-time sampling is worst.
- **Time-dependent mean (sine), comparing two methods.**
  - Both methods leave a large positive α̂ bias.
  - Sánchez is better for α; the author's method is better for σ.
  - Both use a symmetric (non-causal) MA, so neither is real-time.

### 3.4 Part 3: MA-detrended OU calibration on real FX (Tables 6.1–6.4)
- **Scaling of the estimates with MA window τ.**
  - α̂ ∝ τ^{Eα}, with **Eα ≈ −1**: TR −0.97 to −1.14; Commerzbank −0.87 to −1.09.
  - Long-term variance σ̂²/(2α̂) ∝ τ^{Evar}, with **Evar ≈ +1**.
  - σ̂ itself is about constant (CHF/JPY 0.0056/√day for every τ).
- **Link to H:** Evar correlates 0.957 with 2H_DMA. TR daily 2H ≈ 0.99–1.18, i.e. H ≈ 0.50–0.59.
- **Our analytic inference (INFERENCE):**
  - For a pure random walk, X − SMA_τ has variance ∝ τ and lag-1 autocorrelation 1 − O(1/τ). Hence α̂ ∝ 1/τ and variance ∝ τ¹ follow **automatically** for H = ½.
  - Therefore **the calibrated "reversion speed" is determined by the analyst's MA window, not by the market.** Deviations of Evar from 1 equal 2H − 1, i.e. mild persistence, H > ½.
  - Commerzbank intraday Evar values of 0.87–0.96 imply H ≈ 0.44–0.48 (anti-persistent at minute scale). This is consistent with quote-level microstructure mean reversion.
- **Author's own interpretation:** mean reversion may be "inferred into the data by the calibration itself", and the term "mean-reversion strategy" applied to MAs "may be slightly misleading".

## 4. Principles
1. **SOURCE / established.** FX volatility scales as Δt^{≈0.56–0.58} (mean absolute return) from sub-second to multi-year horizons. Slightly super-diffusive, multiscaling. FX is neither a random walk nor an OU at a single scale.
2. **SOURCE + INFERENCE.** "Price minus moving average" signals have built-in pseudo-mean-reversion for *any* random walk. The apparent reversion speed ∝ 1/window. Profitable MA-reversion requires H(2) < ½ at the trading horizon; otherwise the signal is an artefact.
3. **SOURCE.** How weekend and overnight gaps are handled materially biases volatility and mean-reversion estimates (±20–25 % in σ). Estimator properties derived for regular data do not transfer to gapped or irregular data.
4. **SOURCE.** OU α̂ is badly upward-biased near a unit root on short samples. Any "half-life" estimate on less than a few half-lives of data is unreliable.

## 5. Critical assessment
- **Strengths:** careful simulations; candid about inconclusiveness; two independent data sources; spans a wide range of scales.
- **Weaknesses:**
  - Thomson Reuters prices are **bid**, not mid, and come pre-interpolated.
  - Linear interpolation over weekends in physical time biases small-Δt points (the author acknowledges this).
  - Correlation coefficients R near 0.999 on log-log fits of overlapping, dependent points are not evidence of a law.
  - Part 3 does not run the obvious control (the same calibration on a simulated random walk), although Part 1 does.
  - No trading tests and no costs.
  - No metals: XAU was excluded for low frequency.

## 6. NEXA relevance (high, conceptual)
- **NEXA's 8E engines use bands and MA-relative entries** (Bollinger/TTM squeeze S09/S19, TD exhaustion S17, mean-reversion families). Boeker shows MA-distance reversion is an artefact unless H < ½ at the horizon. This gives a **concrete pre-test**.
- **Hypothesis H-HURST-GATE** (data available: NEXA has XAU/FX M1–D1 bars):
  - Estimate H(2) via DMA, and H(1) via the mean-absolute-return scaling, per symbol and per horizon (M5 → D1), on rolling windows. Use **closed bars only** and **server-time (NY+7) session boundaries**.
  - **Prediction:** MA-reversion engines only have positive expectancy net of spread in horizon/regime cells where H < ½; trend engines need H > ½.
  - **Validation:** this is a descriptive conditioning variable. Test on in-sample (IS) data only, then prospectively. No retuning of frozen V2/8E.
  - **Risks:**
    - H estimates are noisy and biased (curvature).
    - Multiple horizons × symbols create a multiple-testing burden.
    - The Commerzbank minute-scale anti-persistence may be quote-microstructure and untradeable after spread.
  - Evidence level: hypothesis.
- **Volatility estimation hygiene (H-GAP-VOL):** NEXA's ATR/vol estimators straddle weekends and rollover. Quantify the bias from including or excluding weekend-gap bars (Boeker: about ±20–25 %), and document NEXA's convention. This links to the Pepperstone time-convention memory and the D-TZ open item.
- **Scaling law use:** convert volatility across horizons with Δt^{0.56–0.58} rather than √Δt when sizing multi-horizon stops. The difference is small at short horizons but grows with the ratio of horizons. Hypothesis only; verify on NEXA data.

**Cross-references:**
- S04 (rough volatility, H ≈ 0.1 for *volatility*; do not confuse with price H ≈ 0.5–0.58 here);
- S18 (Hurst/ACF confusion);
- S09/S19 (bands);
- S17 (TD);
- S25/S12 (OU stat-arb);
- S22 (mean-reversion strategies);
- S01 (Forex Essentials, practitioner MA usage).
