# 11: NEW MATHEMATICAL CONSTRUCTS + EQUATION REGISTRY

**Standard (directive §23):** a construct is kept only if it is:
- coherent;
- dimensionally sensible;
- interpretable;
- computable from NEXA data;
- causal;
- falsifiable;
- testable;
- robust;
- decision-useful.

**Existing mathematics is preferred whenever it already solves the problem.** In most cases below the "new" content is the *NEXA-specific definition, normalisation and test*, not a new formula. Truly new constructs are marked **NEW**; they are combinations defined here for NEXA and **have not been validated**.

**Provenance tags:**
- **SOURCE Sxx:** from a corpus file.
- **EXTERNAL:** standard literature outside the 56 files.
- **NEW:** defined here.

**Verification column:** ✓ = algebra or simulation checked in this session; — = definitional.

**Registry block format.** Each equation lists: formula, variables and units, assumptions, derivation, interpretation, data, bias, failure, validation, and NEXA applicability. Each line is abbreviated to its key point.

---

## A. Price and volatility

### EQ-001: log return and quadratic variation  ✓
- **r_i** = ln(m_i / m_{i−1}), with m the mid quote (or bid for bar data).
- **RV_t** = Σ_{i∈t} r_i².
- **Units:** dimensionless; RV is variance per window.
- **Assumptions:** zero-mean returns over the window (S48 App. A.2). Microstructure noise is negligible at 1 minute; at tick level it is **not**, so use ≥ 1-min returns.
- **Source:** EXTERNAL (Itô quadratic variation); S48.
- **Interpretation:** realised variance, the only principled "energy-like" additive quantity (10 §2).
- **Data:** MT5 M1 or ticks; Massive bars.
- **Bias:** weekend and rollover gaps inflate RV (H-GAP-VOL). Bid-only bars carry spread-change artefacts.
- **Fails when:** a session contains a gap; very low activity.
- **Validation:** variance-signature plot (RV vs sampling interval) to pick the interval.
- **NEXA:** core of the volatility layer.

### EQ-002: Yang–Zhang variance  ✓ (formula per EXTERNAL Yang & Zhang 2000; efficiency table SOURCE S48)
- **Formula:** σ²_YZ = σ²_O + k·σ²_C + (1−k)·σ²_RS, with k = 0.34 / (1.34 + (n+1)/(n−1)).
- **Components:**
  - σ²_O: variance of overnight (open-to-prior-close) log returns;
  - σ²_C: variance of open-to-close returns;
  - σ²_RS: Rogers–Satchell mean of ln(H/C)·ln(H/O) + ln(L/C)·ln(L/O).
- **Assumptions:** handles drift and opening jumps; minimum-variance among OHLC estimators (S48: up to 14× close-to-close efficiency).
- **Data:** M1 aggregated to the decision horizon.
- **Bias:** "open/close" must be defined for 24-hour markets: session anchors (06 §3).
- **Validation:** QLIKE vs ATR and close-to-close in predicting next-window RV (Diebold–Mariano).
- **NEXA:** replaces ATR as σ̂ wherever volatility units are needed (NF-004).

### EQ-003: Parkinson range variance  ✓
- **Formula:** σ²_P = (1/(4 ln 2)) · mean[(ln H/L)²].
- **Assumptions:** no drift, no gaps. Underestimates with gaps (S48).
- **NEXA:** a fallback and robustness check for EQ-002.

### EQ-004: HAR log-RV forecast (EXTERNAL Corsi 2009; already H-VOL-1)
- **Formula:** ln RV_{t+1} = β₀ + β_d ln RV_t + β_w ln RV_t^{(5)} + β_m ln RV_t^{(22)} + ε.
- **Assumptions:** linear in logs; stable coefficients over a rolling window.
- **Fails when:** structural breaks (news regimes). Refit rolling, **causally**.
- **Validation:** QLIKE / Diebold–Mariano vs ATR, GARCH(1,1) and EWMA.
- **NEXA:** σ̂_{t+1} feeds the stop distance D, P_H and cost-in-R.

## B. Activity and volume

### EQ-005: seasonal activity baseline and relative volume (RVOL)  — (NEW for NEXA; standard idea)
- **Formula:** Ê[V | how(t)] = median of V over the same hour-of-week (or same 5-min-of-week) in the previous K closed weeks. **RVOL_t = V_t / Ê[V | how(t)].**
- **Units:** ratio.
- **Assumptions:** the weekly seasonal profile is stable over K weeks.
  - **MEASURED:** the hour-of-day profile correlation between tick volume and exchange volume is 0.93–0.98, so the *shape* is shared across sources.
- **Bias:** DST shifts the profile in server time. Compute in UTC with explicit session anchors.
- **Validation:** stability of Ê across years; RVOL's incremental value for next-hour RV over HAR (HYP-002).
- **NEXA:** NF-010, from both tick volume (spot) and futures volume.

### EQ-006: effort–result residual (EVR)  NEW (formalises Wyckoff "effort vs result", SOURCE S40)
- **Formula:** ln|r_t| = a + b·ln V_t + Σ_k c_k·1[how_k] + u_t, fitted on a rolling *past* window (t−W … t−1) and applied at t. **EVR_t = ln|r_t| − (â + b̂ ln V_t + ĉ_how).**
- **Interpretation:**
  - **EVR ≪ 0:** "effort without result" (absorption / high volume, small move).
  - **EVR ≫ 0:** "result without effort" (thin, gap-like move).
- **Assumptions:** a log-linear volume–volatility relation (EXTERNAL: the mixture-of-distributions literature).
- **Bias:** |r| = 0 bars. Use ln(|r| + ε) or range in place of |r|.
- **Fails when:** b̂ is unstable; the residual is pure noise.
- **Validation:** HYP-003. Does EVR predict the sign or size of the next-k-bar return beyond the null?
- **NEXA:** NF-012.

### EQ-007: Amihud-type illiquidity  (EXTERNAL Amihud 2002)
- **Formula:** ILLIQ_t = |r_t| / V_t, using **dollar volume** for futures (`dollar_volume` field) and tick volume for spot (proxy).
- **Interpretation:** price move per unit activity, a price-impact proxy.
- **NEXA:** NF-013. Closely related to EVR. Test them as one family.

## C. Flow proxies (PROXY: true signed flow is UNAVAILABLE)

### EQ-008: quote-direction imbalance (= NEXA f30 `obiProxy`)  SOURCE (NEXA_Microstructure.mqh)
- **Formula:** s_i = sign(bid_i − bid_{i−1}) per quote update (no BUY/SELL flags exist at Pepperstone: MEASURED). **OBI_t = Σ_{last W} s_i / Σ |s_i|**, with W = 50 updates.
- **Interpretation:** the direction of quote revisions, not trades.
- **Bias:**
  - non-reproducible offline (parity-exempt);
  - depends on the broker's quote-update policy;
  - W = 50 updates is a variable *time* window (seconds in a fast market, minutes in a slow one).
- **NEXA:** existing f30. Used in the quality gate (|OBI| > 0.15). **Its value has never been tested in isolation** (HYP-017b).

### EQ-009: bulk-volume classification on futures bars  (EXTERNAL Easley, López de Prado & O'Hara 2012)
- **Formula:** V^B_t = V_t·Φ(Δp_t / σ̂_Δp), V^S_t = V_t − V^B_t, **δ_t = V_t·(2Φ(Δp_t/σ̂_Δp) − 1)**.
- **Units:** contracts.
- **Assumptions:** the bar's price change is informative of the buy/sell split (a probit link). σ̂_Δp is estimated on past bars only.
- **Bias (critical):** δ_t is a monotone function of Δp_t, so **corr(δ_t, Δp_t) > 0 by construction.** Only δ_{t−1}, δ_{t−2}, … may be used to predict.
- **Validation:** none possible without true signed trades. **Unvalidated proxy.** An entitlement upgrade (futures trades with side, or quotes for Lee–Ready) would allow validation.
- **NEXA:** NF-020 (research only).

### EQ-010: normalised delta  NEW (NEXA convention, directive §13)
- **Formulas:**
  - δ̃_t = δ_t / V_t ∈ [−1, 1];
  - δ*_t = δ_t / Ê[|δ| | how(t)];
  - πδ_t = F̂_{same-how, past}(δ̃_t).
- **Interpretation:** replaces raw thresholds ("300 %").
- **NEXA:** NF-021.

### EQ-011: two-flow price-impact regression  SOURCE S51 (Kozhan–Moore–Payne)
- **Formula:** Δp_t = β₀ + λ_M·mo_t + λ_L·lo_t + ε_t, contemporaneous. Omitted-variable bias of λ̂_M when lo is dropped = λ_L·cov(mo,lo)/var(mo).
- **Assumptions:** linear impact; dealers both inform and absorb inventory.
- **Bias:** endogeneity of lo (IV results weak, S51).
- **NEXA:** **not estimable** (no mo, no lo). Only the **predictive** variant matters for trading: Δp_{t+1} = θ'(flows_{≤t}) + ε. It is testable with proxies only (HYP-017).

## D. Revealed-liquidity field (volume-at-price)

### EQ-012: liquidity field L(p,t)  NEW (formalises profile/HVN/LVN, SOURCE S42/S44/S49)
- **Formula:**

      L(p,t) = Σ_{bars s closed before t} w(t−s) · Σ_j v_{s,j} · K_h(p − p_{s,j})

  - **Bin assignment:** volume v_s is assigned to prices p_{s,j} inside bar s. Either at the typical price (h+l+c)/3, or uniformly over [l,h]. **The choice must be pre-registered.**
  - **Kernel:** K_h Gaussian with bandwidth h ∝ σ̂ (volatility-scaled; e.g. h = 0.1·σ̂_day).
  - **Memory:** w(τ) = e^{−τ/T}, or a session window.
- **Units:** volume per price unit.
- **Interpretation:** **revealed (traded) liquidity density.** It is **not** resting liquidity (no book data).
- **Assumptions:** traded volume at a price marks prices the market "accepted" (auction theory). Kernel smoothing removes bin artefacts.
- **Data:** futures true volume (2 y), or spot tick volume (9 y, proxy). **MEASURED:** VA overlap 0.82.
- **Bias:** intra-bar allocation error; tick-volume ≠ volume (moderate); the futures–spot basis (EQ-026).
- **Fails when:** a bimodal day makes argmax-based levels unstable (MEASURED: POC jumps of $12–68). **Use smooth functionals, not argmax.**
- **Validation:** HYP-004/005/006.
- **NEXA:** NF-030–NF-034.

### EQ-013: field gradient, curvature and log-force  NEW
- **Formulas:**
  - ∂_p L(p,t) = Σ w v K'_h(p − p_s);
  - ∂²_p L = Σ w v K''_h, with analytic Gaussian derivatives;
  - **g(p,t) = ∂_p ln L(p,t)** (the "log-force", scale-free);
  - **κ(p,t) = ∂²_p ln L(p,t)·h²** (dimensionless curvature).
- **Interpretation:**
  - g > 0 means density increases above price;
  - κ < 0 means near a local maximum (HVN);
  - κ > 0 means near a minimum (LVN, a "void").
- **Assumptions:** smooth density; h is chosen so that peaks represent multi-bar acceptance, not single prints.
- **Validation:**
  - HYP-005: sign(p_{t+H} − p_t) correlates with g(p_t)?
  - HYP-006: speed and continuation in LVN vs HVN.
- **NEXA:** NF-032, NF-033.

### EQ-014: value area (algorithmic)  SOURCE S42 App. 1; α = 0.70 (S42/S45) vs 0.68 (S46). **Pre-register α = 0.70.**
- **Algorithm:** POC = argmax_bin L.
  1. Start at the POC.
  2. Compare the sum of the next two bins above with the next two below; add the larger pair.
  3. Stop when cumulative mass ≥ α.
  - Output: VA = [VAL, VAH].
- **Bias:** the tie-break must be fixed; MT5 rounding bias is documented (S43 changelog v1.14).
- **NEXA:** NF-035/036 (distance to VAH/VAL in σ̂ units).

### EQ-015: profile concentration (normalised entropy)  NEW
- **Formula:** π_j = mass in bin j / total. H = −Σ π_j ln π_j / ln J. **C = 1 − H.**
  - Bins: J equal-width bins over the session range, or fixed σ̂-scaled bins.
- **Interpretation:** concentrated (D-shape, balance) vs dispersed (elongated, trend). A practitioner shape label becomes a number.
- **Bias:** H depends on J and on the range. Use σ̂-scaled fixed-width bins and report the relation with range.
- **Validation:** HYP-014.

## E. Session structure (auction / Market Profile, made mechanical)

### EQ-016: initial balance and range extension  SOURCE S42/S46 (codified)
- **Formulas:**
  - IB_s = max−min price over [a_s, a_s + 60 min), with a_s the session anchor (06 §3);
  - **REX_s = (H_s − L_s − IB_s) / IB_s**;
  - directional extension REX↑ = (H_s − IB_high)/IB, REX↓ = (IB_low − L_s)/IB;
  - **IBR_s = IB_s / σ̂_day** (IB width in volatility units).
- **Day type, Steidlmayer (S46), approximate:** nontrend REX ≈ 0; normal ≈ 0.5; normal variation ≈ 1; trend = small IBR plus the EQ-018 criterion.
- **NEXA:** NF-040/041. **Causal:** REX is known only at session end. Only *developing* REX is causal intraday.

### EQ-017: close location  SOURCE S46
- **Formula:** CL_s = (C_s − L_s)/(H_s − L_s) ∈ [0,1].
- **Trend day:** CL ≥ 0.9 (up) or ≤ 0.1 (down), plus non-rotation.

### EQ-018: rotation count  SOURCE S46 (codified)
- **Formula:**
  - For each 30-min period j ≥ 2, set a_j = +1 if H_j > H_{j−1} and L_j ≥ L_{j−1} (an up-auction).
  - Set a_j = −1 if L_j < L_{j−1} and H_j ≤ H_{j−1} (a down-auction).
  - Otherwise a_j = 0 (an inside or outside period).
  - **ROT_s = the number of sign changes in the sequence of non-zero a_j.**
- **Trend day:** at most 2 counter-rotations (S46: "may be broken once or at most twice").
- **Assumption:** the pre-registered rule above. Because S46's wording is informal, this codification is NEXA's own and must be labelled as such.

### EQ-019: compression ratio  NEW (standard idea; family "range/volatility state")
- **Formula:** CR_t = σ̂_YZ(short window) / σ̂_YZ(long window), e.g. 1 session / 20 sessions.
- **Interpretation:** compression → expansion.
- **Validation:** HYP-019. Volatility mean reversion is expected. **Breakout *direction* is expected to be unpredictable** (null).

### EQ-020: efficiency ratio (existing family; SOURCE original S01 DM/V, Kaufman)
- **Formula:** ER = |p_t − p_{t−n}| / Σ_{i=t−n+1}^{t} |Δp_i| ∈ [0,1].

### EQ-021: variance ratio (existing H-VR-SCALE)
- **Formula:** VR(q) = Var(r^{(q)}) / (q·Var(r)). VR > 1 means persistence; VR < 1 means reversion.

### EQ-022: permutation entropy  (EXTERNAL Bandt & Pompe 2002)
- **Formula:** for embedding order m (3–5), take the relative frequencies p_π of the m! ordinal patterns of consecutive returns. **PE = −Σ p_π ln p_π / ln m!**
- **Interpretation:** PE < 1 means ordinal structure (predictability).
- **Bias:** ties in discretised prices (round levels) create artificial patterns. Break ties randomly with a fixed seed, or drop them.
- **Validation:** HYP-021. Must add value beyond ER and VR.

## F. Regimes and transitions

### EQ-023: Markov / HMM regime transition matrix  (EXTERNAL Hamilton 1989; Baum–Welch)
- **Observed-regime version:**
  - z_t = (σ̂ tercile) × (ER tercile), so K = 9;
  - P̂_ij = n_ij / n_i·, with Dirichlet(α) posterior credible intervals.
- **HMM version:** emission on (r, ln RV, RVOL); Gaussian HMM, K = 2–4 chosen by out-of-sample log-likelihood.
- **Causal use:** the filtered (forward-algorithm) probability P(z_t | x_{≤t}) only. **Never the smoothed (backward) probability.**
- **Null:** P_ij = π_j (i.i.d. regimes). Test with a likelihood-ratio and a block bootstrap.
- **NEXA:** M-06 (12), HYP-020.

## G. Trade outcome mathematics

### EQ-024: driftless two-barrier probability  ✓ (original MATH M1b)
- **Formula:** P(target U before stop D) = D/(U+D) under driftless continuous motion. Then **E[R_gross] = 0** for any U, D.
- **Role:** the null for every stop/target rule (H-HIT-PROB).

### EQ-025: net expectancy in R  ✓
- **Formula:** E[R_net] = p·W̄ − (1−p)·L̄ − c/D, where c = round-trip cost in price units (spread at fill + commission/lot ÷ value per price unit per lot).
- **MEASURED anchor:** c/D ≈ 0.245R at NEXA's median EURUSD stop of 2.4 pips (cap-neutral A4).
- **Implication:** halving cost-in-R requires doubling D (and U) *without* lowering gross R/trade. That is a testable trade-off (HYP-024).

### EQ-034: two-barrier probability with drift  ✓ (scale-function derivation; checked by Monte Carlo in this session)
- **Formula:** P_U = (1 − e^{2μD/σ²}) / (e^{−2μU/σ²} − e^{2μD/σ²}). It tends to D/(U+D) as μ → 0.
  - MC check with dt = 0.01: μ = 0.3 gave 0.598 vs 0.581 (discrete-monitoring bias); μ = −0.2 gave 0.288 vs 0.286.
- **Role:** translates any predicted drift μ(x) and σ(x) into P_U, then into E[R] via EQ-025. **The bridge from state to expectancy.**

## H. Basis and cross-venue mapping

### EQ-026: futures-to-spot level map  NEW (NEXA definition)
- **Formula:** b̂_t = median_{k most recent closed hours} (F_h − S_h), using contemporaneous hourly closes. **Spot level = futures level − b̂_t.**
  - For JPY futures (6J is quoted in USD per JPY, e.g. 0.0067): implied USDJPY = 1/F. Apply the basis in log space: ln S = −ln F − b̂^{log}_t.
  - The quote format must be checked against Massive's 6J price field before use; it was not probed in this session.
- **Assumptions:** the basis drifts slowly. **MEASURED:** about −$0.6/day for GCZ6 in September 2026, i.e. carry decay.
- **Bias:** roll dates create basis jumps. Restart the estimate at each roll.
- **Validation:** out-of-sample hourly |S − (F − b̂)|, the mapping error, in σ̂ units.
- **NEXA:** required by any futures-volume or profile-derived spot level (NF-031).

## I. Options / GEX (defined for completeness; data UNAVAILABLE, see 05)

### EQ-027: per-strike dealer gamma exposure  SOURCE S53/S54 (Model A sign)
- **Formula:** GEX_K = Γ_K·OI_K·M·S²·0.01·sgn(K), with sgn = +1 for calls, −1 for puts (an inventory *assumption*). Net = Σ_K. Normalised = Net / (S²·0.01·M).
- **Gamma:** Γ from Black-76 (futures options) or Black–Scholes–Merton, at per-strike IV.
- **Verified:** Γ_C = Γ_P (put–call parity, S54) ✓.
- **Fails when:** the sign assumption is wrong (S50: customer call *buying* → dealer short gamma).

### EQ-028: gamma flip (zero-gamma level)  SOURCE S53/S54
- **Repriced root:** solve N(S*) = Σ_K sgn_K·OI_K·Γ_K(S*; IV_K) = 0, choosing the sign-resolved nearest root (S53).
- **Local approximation:** S54 eq. 2, with the zero-straddle rule.

### EQ-029: hedge-pressure ratio (HPR)  NEW (formalises S48's pinning condition)
- **Formula:** HPR_t = |Net GEX_t| (dollars of hedge per 1 % move) / DV_t (average daily dollar volume of the hedging instrument: futures plus ETF plus spot, as available).
- **Interpretation:** the fraction of a normal day's volume dealers must trade per 1 % move. **Bennett's condition: pinning and walls are plausible only if HPR is non-negligible.**
- **Validation:** HYP-027. The wall/pin effect size should increase with HPR (dose–response). Absent a dose–response, wall claims fail.
- **NEXA:** not computable (needs OI).

### EQ-031: delta-hedged option P&L  ✓ SOURCE S48
- **Formula:** ΔΠ ≈ ½·Γ·S²·(r² − σ_impl²·dt). Carry ∝ (σ_realized − σ_impl).
- **Role:** explains *why* long-gamma hedgers dampen moves (they rebalance against price) and short-gamma hedgers amplify them.

### EQ-030: stop-rule family  NEW (formalises directive §9; tested in HYP-023)
For a long entry at e, with D the stop distance:

| Rule | Definition | Data |
|---|---|---|
| **H1 wall** | D = (e − (W_put − ε·σ̂)) | Put wall W_put. **UNAVAILABLE** |
| **H2 volatility** | D = k·σ̂_YZ | Available |
| **H3 liquidity structure** | D = (e − (VAL − ε·σ̂)), or beyond the nearest LVN below the entry HVN | Available (proxy profile) |
| **H4 flow invalidation** | Exit when lagged δ̃ (or f30) crosses −θ for m consecutive bars, with a catastrophic hard stop | Proxy only |
| **H5 hybrid** | D = max(k·σ̂, distance to structure) with a flow exit | Partial |

- **The directive's literal phrasing** (put-wall setup, stop "above" the wall) applies to a *short* rejected at a wall from below, mirrored.
- **Comparison metric:** E[R_net], P(stop), MAE/MFE in σ̂, slippage. **Entries identical across rules.**

## J. Information decomposition

### EQ-032: WHERE/WHEN mutual-information decomposition  ✓ (chain rule)
- **Formula:** I(Y; Lv, F) = I(Y; Lv) + I(Y; F | Lv).
- **Estimation:** log-score differences of nested calibrated classifiers on a frozen holdout. Permutation null.
- **NEXA:** HYP-022.

### EQ-033: decision rule  (09 §2)
- **Act iff:** E[R_net | x] > κ ∧ calibration passes ∧ the risk engine authorises.

## K. Point-process and microstructure (research-later)

### EQ-035: Hawkes intensity  (EXTERNAL Hawkes 1971)
- **Formula:** λ(t) = μ + Σ_{t_i<t} α·e^{−β(t−t_i)}. Branching ratio n = α/β < 1. n → 1 means endogenous bursts.
- **Data:** tick quote updates. Only 28 days of history, plus forward logging (S14 tick logger).
- **Validation:** HYP-033 (quote-burst → spread widening / slippage).

## L. Physics-analogy constructs (labelled ANALOGY; see 10)

### EQ-038: liquidity potential  NEW (ANALOGY)
- **Formula:** U(p,t) = −ln L(p,t); "force" F = −∂_p U = g(p,t) (EQ-013).
- **Mathematically identical to EQ-013.** It adds no new test, only an interpretation (an attractor at HVN). **Kept only as notation.**

### EQ-039: absorption index  NEW (variant of EVR)
- **Formula:** ABS_t = πV_t − πR_t, where πV is the seasonal percentile of volume and πR the percentile of the range (in σ̂ units).
- **Interpretation:** high volume, small range. Absorption at a level is a practitioner claim (S44 "absorption confirmation").
- **Validation:** merged with HYP-003 (one family).

---

## Summary table

| Group | IDs | Status |
|---|---|---|
| Volatility (strong prior, data available) | EQ-001–004, 019–021 | **Ready to test** |
| Activity / volume (data available; proxy for spot) | EQ-005–007, 039 | Ready to test |
| Flow proxies | EQ-008–010 | **PROXY**; same-bar circularity; lagged use only |
| Flow (true) | EQ-011 | Not estimable |
| Liquidity field | EQ-012–015, 038 | Ready to test (proxy for spot; true for futures) |
| Session structure | EQ-016–018 | Ready to test (session anchors required) |
| Regime | EQ-022, 023 | Ready to test |
| Outcome maths | EQ-024, 025, 034 | Verified; used as nulls and bridges |
| Basis | EQ-026 | Needed for any futures-derived level |
| Options / GEX | EQ-027–029, 031 | Defined; **data unavailable** |
| Stop rules | EQ-030 | H2, H3 testable; H1 blocked; H4, H5 proxy |
| Information | EQ-032, 033 | Diagnostic and decision |
| Point processes | EQ-035 | Research-later (data short) |
