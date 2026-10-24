# S27: Angelika Esser & Burkart Mönch, "The Navigation of an Iceberg: The Optimal Use of Hidden Orders" (working paper, 14 Jan 2005; later in *Strategic Trading in Illiquid Markets*, LNEMS 553, Springer 2005)

**File:** `175-moench_paper.pdf`. 33 pp. DekaBank and Goethe University Frankfurt. Data from the Deutsche Börse Trading Surveillance Office.

| Field | Value |
|---|---|
| **Source type** | Other academic institution, with a bank co-author. Academic working paper, later published as a book chapter (Springer lecture notes). |
| **Evidence status** | **Model:** established within assumptions. The first-passage mathematics is standard and was verified against rendered pages. **Empirical calibration:** research finding (one stock, MAN, Jan–Mar 2002). The **β imbalance → return regression** is likely overstated (overlapping windows). |
| **Processing** | All 33 pages read, including Appendix A (barrier-conditional density). **Rendered and verified visually:** pp. 14, 16, 17 and 22 (objective, hitting-time laws eqs. 2–6, drift model). Figs 1–3 (iceberg statistics) were read from the extracted bar labels. Figs 6–10 (optimal limit and peak curves) were interpreted from the text and axis values. |

## 1. Empirical facts (SOURCE: XETRA, MAN, 61 trading days, Jan 3 – Mar 28, 2002)
- **Order counts:** 786 iceberg sell orders, 140,948 pure limit sells, 4,130 market sells.
- **Iceberg size:** iceberg orders average **16,037 shares**, against 964 for limit orders and 1,069 for market orders. Hidden orders are 8.24 % of ask-side volume.
- **Peak sizing:** about **37 % of users set the peak = 1/10 of total size**. Limits are typically set 5–15 cents above the best bid (average spread 7 cents, mid about €26.91).
- **Execution (Table I):**
  - only **17.7 % completely executed** (139);
  - 29.4 % partially executed (231; average 32 % filled);
  - **52.9 % unexecuted** (416). The total 786 checks ✓.
  - Median time to completion or deletion is about 10 minutes, so traders monitor and cancel frequently.
- **Literature cited (SOURCE):**
  - hidden volume is 26 % of trades in Spain (Pardo–Pascual) and about 30 % of depth for CAC40 (D'Hondt et al.);
  - iceberg orders are cancelled more often and less often fully filled;
  - a limit order is a free option (Copeland–Galai);
  - Lo–MacKinlay–Zhang (2002): first-passage fill models predict poorly.

## 2. Model (SOURCE; verified)
- **Price model:** the best bid follows GBM, dS = µS dt + σS dW, below the limit S̄. On a hit it jumps down to (1 − ε)S̄. Each hit trades φ_s shares. Other sell orders φ_a with time priority sit ahead of each new peak φ_p.
- **Hits needed for a complete fill:** n* = ⌈φ₀(1 + φ_a/φ_p)/φ_s⌉ ✓. A smaller peak means more hits, which is the cost of losing priority.
- **Executed after n hits:** h(n) = min{max(φ_p⌊nφ_s/(φ_a + φ_p)⌋, nφ_s − φ_a(1 + ⌊nφ_s/(φ_a + φ_p)⌋)), φ₀}.
- **Hitting time to the limit (p. 17, V ✓):** let a = ln(S̄/S₀) and ν = µ − σ²/2.
  - **P(τ₁ < ∞) = 1 if ν ≥ 0; exp(−2a|ν|/σ²) if ν < 0.**
  - Defective density f₀,₁(t) = (a/(σ√(2πt³)))·exp(−(a − νt)²/(2σ²t)), the inverse Gaussian.
  - ✓ Identity check: the conditional density with drift |ν| times P(τ < ∞) equals the defective density with drift ν.
  - After each hit the process restarts at ln S̄ + ln(1 − ε). Subsequent intervals use a = −ln(1 − ε) (eq. 5).
  - t_n is the n-fold convolution (eq. 6), computed via cubic-spline convolution or Laplace-transform inversion: E e^{−λτ} = exp(−(a/σ²)(√(ν² + 2σ²λ) − ν)).
- **Probabilities:** P(M = n) = ∫₀ᵀ f₀,n − ∫₀ᵀ f₀,n+1. P(M ≥ n*) = ∫₀ᵀ f₀,n*.
  - E(S_T | M = n) uses a barrier ("knock-out") conditional density (App. A, Harrison 1990).
- **Two formulations:**
  - **Open approach (Prop 1):** max φ₀S̄ subject to P(M ≥ n*) ≥ P*, S₀ < S̄ and φ_p ≤ φ₀.
  - **Self-contained approach (Prop 2):** max E[G], where unfilled shares are dumped at T at (1 − Ψ(·))S_T.
- **Drift and imbalance (§5):**
  - imbalance B = bid volume / (bid + ask volume) = c/(d + φ_dp);
  - µ_{n+1} = µ_n + β(B_{t_{n+1}} − B_{t_n}).
  - So showing a larger peak lowers B and the drift, which lowers fill probability: the information-leakage cost.
- **Calibration (Tables III–IV, MAN):**
  - φ_s = 868, φ_a = 1,554, ε = 0.00091, c = 166k, d = 292k, σ = 0.7.
  - **β = 116.6 (t = 22.45)** from regressing 60-minute-ahead returns on the past-60-minute imbalance change, sampled **minute by minute**.

## 3. Results (SOURCE)
- **Example (φ₀ = 10,000 shares, about 1–2 % of daily turnover; T = 10 h):** the optimal limit falls as the target P* rises. For P* ≤ 59 %, the **optimal peak is 8,000 shares**, insensitive to P*. Even at the smallest limit (€28.56), P(full fill) < 60 %.
- **Longer horizons** allow higher limits and smaller peaks. The peak falls to 4,000 shares when T > 46 h (a step function).
- **Larger positions** need lower limits. The optimal peak is non-monotone in φ₀ because the fill grid is discrete.
- **The model's optimal peaks are far above observed practice** (the 1/10 rule). The authors say either the model underestimates display impact or traders overestimate it.

## 4. Critical assessment (INFERENCE)
- **β's t = 22.45 is overstated.** Minute-sampled, overlapping 60-minute returns and imbalance changes give highly autocorrelated errors and no HAC correction (same issue as S14 Ch. 7). The sign is plausible (consistent with S34 and S26); the precision is not.
- **The structure is stylised:**
  - GBM for the best bid;
  - constant trade size φ_s, constant queue φ_a and constant jump ε (Table III SDs exceed the means for φ_s and φ_a);
  - a static strategy, whereas Table I shows traders act dynamically;
  - one stock and one quarter.
- The **open approach maximises revenue conditional on a full fill.** Revenue from partial fills is ignored.
- **Value:** a clean decomposition of the iceberg trade-off: priority loss vs information leakage vs non-execution risk. The first-passage machinery is a reusable tool.

## 5. Principles
- **SOURCE:** passive (limit/iceberg) execution trades price improvement against **execution risk**. Fill probability depends on the limit distance, the horizon, queue position and the information the order reveals.
- **SOURCE + S34/S26/S06:** displayed volume and order-book imbalance carry short-horizon directional information. Large visible orders move others' behaviour.
- **INFERENCE:** a limit order is an option written to the market (Copeland–Galai). Hidden orders reduce the option's informational cost but worsen priority.

## 6. NEXA relevance
- **Not directly applicable.** NEXA trades small retail CFD size, with no LOB queue and no icebergs at Pepperstone.
- **Reusable maths:**
  - **first-passage probability of GBM/ABM to a level, P(hit before T)**, for any NEXA analysis of **stop or target hit probabilities** under drift and volatility (H-HIT-PROB);
  - a reflection-principle barrier density for expected price conditional on no hit (TP/SL probability modelling);
  - **caution:** real XAU/FX paths are not GBM (S15 scaling; S04 roughness; fat tails S35/S18).
- **If NEXA ever uses LIMIT entries** (V2 FVG retracement), model the fill probability vs limit distance and the adverse selection of fills (S06/S10/S11). This paper gives the structural template.

**Cross-references:**
- S29 Cebiroğlu–Horst (optimal iceberg display, the follow-up literature);
- S28 Sahni (iceberg QA, descriptive);
- S32 Harris (hidden orders, order exposure);
- S10 (discretion/fill trade-off);
- S25 (Almgren–Chriss);
- S34 (imbalance → trade sign);
- S21 (barrier / avalanche maths).
