# S35: Masimba E. Sonono & Hopolang P. Mashele, "Prediction of Stock Price Movement Using Continuous Time Models" (Journal of Mathematical Finance 5, 2015, 178–191)

**File:** `jmf_2015052215132554.pdf`. 14 pp. North-West University and AIMS, South Africa. doi:10.4236/jmf.2015.52017.

| Field | Value |
|---|---|
| **Source type** | Other academic institution. Peer-reviewed, open-access journal (SCIRP). |
| **Evidence status** | **Failed / negative result** for direction (hit ratios ≈ 46–56 %; the authors say "near random walk"). The level-forecast claims are **unsupported** because there is no naive benchmark and the tables are mislabelled. |
| **Processing** | All 14 pages read. The equations were legible in the extraction: crude MC, QMC discrepancy, Halton, LSMC backward recursion, Laguerre basis, GBM and VG dynamics, and MLE via FFT. Tables 1–17 were parsed from the text. There are no figures. |

## 1. Methods (SOURCE; standard results ✓)
- **Crude Monte Carlo:** Î_N = (1/N)Σf(x_k) → I almost surely (SLLN), unbiased.
- **Quasi-Monte Carlo (QMC):** deterministic low-discrepancy points.
  - Star discrepancy D*_N = sup_A |#{x_k ∈ A}/N − vol(A)| over anchored boxes.
  - Halton sequences use van der Corput in prime bases.
- **Least-squares Monte Carlo (LSMC; Longstaff–Schwartz):**
  - optimal stopping V_n = max{Z_n, E[V_{n+1}|F_n]}, with V_T = Z_T;
  - the continuation value is regressed on weighted Laguerre polynomials Φ_j(x) = e^{−x/2}L_k(x).
- **GBM (risk-neutral):**
  - dS = rS dt + σS dW, so ln S_{i+1} = ln S_i + (r − σ²/2)Δt + σ√Δt Z ✓ (eqs. 19–23).
- **Variance Gamma (Madan–Seneta / Madan–Carr–Chang):**
  - X_VG(t; σ, ν, θ) = θγ_t + σW_{γ_t}, with a Gamma subordinator E[γ_t] = t and Var γ_t = νt;
  - S_t = S₀ exp{(r + ω)t + X_VG}, where ω makes the process a martingale (eqs. 24–27).
- **Estimation:** MLE with the density from FFT inversion of the characteristic function on 2¹⁴ points with binned data (Carr–Geman–Madan–Yor).
  - The authors note that **the likelihood has multiple local optima** and the results are sensitive to initial values.
- **Data and design:**
  - 19 JSE Top-40 stocks, 5-minute prices; weekly forecasts made at the start of the week;
  - a downtrend sample (May 2008 – Apr 2009) and an uptrend sample (Sep 2010 – Aug 2011);
  - about 2/3 in-sample and 1/3 one-step-ahead out of sample.
  - Metrics: hit ratio and MAPE = (100/N)Σ|y − ŷ|/y. Two-tailed t-tests at 5 %.

## 2. Results (SOURCE)
- **Hit ratios:**
  - downtrend: about 49–56 % in-sample and about 49–52 % out of sample;
  - uptrend: about 46–53 %.
  - Mostly no significant differences between models or methods.
  - The authors conclude the hit ratios are "near random walk behavior… even a random predictor can produce them".
- **MAPE (weekly price level):**
  - GBM-QMC about 14–16 %;
  - VG-LSMC about 3.3–8 %;
  - GBM-LSMC about 26–34 %;
  - VG-QMC about 21–23 %.
  - "GBM works well with QMC and VG with LSMC."
- **Descriptive:** "significant returns were on average earned during the first 30 minutes of trading" (JSE, 5-minute data). Asserted; no statistics shown.

## 3. Critical assessment (INFERENCE)
1. **Risk-neutral models cannot forecast direction.** Under Q the drift is r (plus a martingale compensator), so simulated paths carry no directional information beyond r. ≈ 50 % hit rates are guaranteed by construction. This is a **predictable negative result**, not evidence about markets.
2. **No naive benchmark.**
   - For weekly horizons, the random-walk "no-change" forecast has MAPE ≈ E|weekly return| ≈ 2–4 % for large caps. So MAPEs of 14–34 % are far *worse* than naive.
   - Only VG-LSMC (3–8 %) approaches the naive level. The level-forecast "findings" therefore do not show skill.
3. **LSMC is an optimal-stopping (American option) tool.** Using it to produce a price forecast is a category error. What it estimates here is undefined in the paper.
4. **Table labelling errors:**
   - Table 2 is titled "models using QMC" but its columns read "Mean QMC / Mean LSMC".
   - The text attributes Table 3's numbers (55.41 / 55.70) to Table 2.
   - Tables 4 and 8 carry swapped column headers.
   - The results cannot be reliably attributed.
5. **Multiple t-tests** (19 stocks × 2 models × 2 methods × 3 periods × 2 metrics) with no correction. The "significant" MAPE differences mostly reflect model misspecification, not forecasting skill.

## 4. Principles
- **SOURCE:** QMC (low discrepancy) improves integration accuracy over crude MC. LSMC estimates continuation values by regression.
- **INFERENCE (validation lesson):**
  - Every forecasting claim needs a **naive benchmark** (random walk, historical mean).
  - Pricing-measure (Q) models are not forecasting models under P.
  - Cf. S04's caution that a calibrated rBergomi is a Q model.
- **SOURCE + INFERENCE:** fat-tailed Lévy models (VG) better describe the return *distribution*. That matters for risk and tail sizing, not for direction.

## 5. NEXA relevance
- **Negative / cautionary.** It is consistent with NEXA's working assumption that direction is weakly predictable at best.
- **Potential use (low priority):** fit VG or another heavy-tailed distribution to XAU/FX M15–H1 returns for stop-out and tail-risk *simulation*: a Monte Carlo of loss streaks within the hard caps. Data available. Evidence: hypothesis (tool, not edge).
- **Methodological rule:** report naive-benchmark-relative errors (e.g. MAPE / MAPE_naive, or Theil's U).

**Cross-references:**
- S04/S18 (Q-measure models; Monte Carlo);
- S23 (QLIKE with Diebold–Mariano against strong baselines);
- S02 (hit rate is not P&L);
- S26 (baseline-relative accuracy);
- S38 (OU modelling claims without data).
