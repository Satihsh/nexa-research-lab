# S22: Zura Kakushadze & Juan Andrés Serur, *151 Trading Strategies* (2018; SSRN 3247865 free edition; originally Palgrave Macmillan 2018)

**File:** `ssrn-3247865.pdf`. 361 PDF pages; 16,015 extracted lines.

| Field | Value |
|---|---|
| **Source type** | Industry/practitioner–academic hybrid book. Kakushadze: Quantigic Solutions LLC, Free University of Tbilisi. A Springer/Palgrave monograph, **not** peer-reviewed as a whole; individual strategies are referenced to peer-reviewed literature. |
| **Evidence status** | **Mathematics:** established, consisting of standard payoff, pricing and portfolio algebra; we spot-verified many derivations (below). **Empirical claims:** unverified within the book. They are second-hand summaries of cited literature, and the book "intentionally do[es] not contain any numeric simulations, backtests, empirical studies" (Preface, p. 16 of PDF). Every "empirical studies suggest" statement is therefore a **pointer** to evidence, not evidence. |
| **Processing** | **Main text read in full (lines 1–6441):** front matter, preface, Ch. 1–20, Appendix A R code (fully traced), Appendix B disclaimers. **Glossary, acronyms and "Some Math Notations" read in full** (lines 12236–14377, PDF pp. 280–342). **Index (PDF pp. 343–361):** read in full in a compacted one-line-per-entry dump; it consists only of term → page locators. **Bibliography (PDF pp. 135–279, ~1,951 entries):** processed by an *automated full pass* (all entries parsed; decade and topic counts; keyword search for multiple-testing, FX, gold and TA references) plus targeted reading of entries relevant to NEXA. It was **not** read entry by entry by eye; this is disclosed here. **Rendered and visually verified:** PDF p. 104 (eq 496 and the 1+κ statement) and p. 120 (eq 535 "softmax"). Elsewhere the extracted math was checked algebraically. |

## 1. What the book is
- It is a catalogue of strategy *descriptions*: about 151 strategies and 550+ equations over options, stocks, ETFs, fixed income, indexes, volatility, FX, commodities, futures, structured assets, convertibles, tax arbitrage, miscellaneous assets, distressed assets, real estate, cash, crypto, global macro and infrastructure.
- The authors frame the field as follows (Ch. 1, SOURCE):
  - Strategies die. For example, the NYSE specialist → Hybrid Market transition in 2006–07 killed classic stat-arb profitability.
  - Modern alphas are "faint" and "ephemeral". They are tradable only when **combined** (alpha combos, §3.20), because transaction costs eat them individually.
- **Implication:** the book is a **taxonomy and maths reference**, not an evidence base. Its value for NEXA is (a) definitions and formulas, (b) the backtesting-hygiene vocabulary (delay-0/1, out-of-sample computation, survivorship, linear cost), and (c) pointers into the literature.

## 2. Mathematics (SOURCE, with our verification)

### 2.1 Options (Ch. 2, eqs 1–265)
- Payoffs for covered call/put, spreads, combos, straddles, strangles, guts, butterflies, condors, ladders, collars, seagulls, boxes and so on.
- Spot-checked eqs (1)–(8), (25)–(28), (95), (168)–(172), (241), (247), (253) and (265): **all algebraically correct.**
- NEXA relevance: none, since NEXA does not trade options.

### 2.2 Stocks (Ch. 3)
- **Price momentum (266)–(270):**
  - cumulative return over T = 12 months, skipping the most recent S = 1 month (because of 1-month reversal);
  - decile long/short; weights uniform, ∝1/σ or ∝1/σ².
- **Mean reversion:**
  - Pairs (283)–(291): demeaned returns, dollar-neutral.
  - Cluster mean reversion: D_i = −γR̃_i with γ = I/Σ|R̃_i|.
  - Multi-cluster mean reversion = regression on binary loadings; the residuals are cluster-demeaned returns (303)–(312).
  - Weighted regression with z_i = 1/σ_i² (313)–(318).
- **Moving averages (319)–(324):**
  - EMA normalisation (1−λ)/(1−λ^T) ✓;
  - single/two/three-MA crossover rules;
  - stop-loss Δ = 2 % vs previous close (323).
- **Pivot point** C = (H+L+C_prev)/3, R = 2C − L, S = 2C − H (325)–(328) ✓ (standard floor pivots).
- **Donchian channel** (329)–(331): the source mentions both contrarian-at-band and breakout uses.
- **KNN single-stock (§3.17, eqs 332–341). INFERENCE, look-ahead risk:**
  - The neighbour set uses targets Y(t′) for t′ = t+1…t+T* (reverse-time indexing; t = 0 is "now").
  - Y(t′) is a T-period forward return, so for t′ < t+T it overlaps information after t, and at t = 0 the most recent T−1 targets are not yet realised.
  - A causal implementation needs t′ ≥ t+T. The source does not state this.
  - SOURCE adds: k ≈ floor(√T*), a 60/40 train/test split, and "fitted parameters often unstable out-of-sample".
- **Stat-arb mean–variance (§3.18):**
  - w ∝ C⁻¹E (350); dollar-neutrality via Lagrange multiplier (354)–(358).
  - Footnote: the sample covariance is singular if T ≤ N+1 and unstable unless T ≫ N, so use a factor-model covariance.
- **Alpha combos (§3.20):** an 11-step procedure (Kakushadze & Yu 2017b):
  - serially demean and normalise by σ;
  - cross-sectionally demean;
  - regress E/σ on the loadings Λ;
  - w = ηε/σ.
- **Single-stock TA verdict (§3.21, SOURCE):**
  - Single-stock technical analysis (MA, support/resistance, channels, KNN) is "deemed unscientific by many".
  - MA crossovers may be "momentum strategies in disguise".

### 2.3 ETFs (Ch. 4)
- Sector momentum rotation, with an MA filter (100–200 days) and a dual-momentum absolute filter.
- Alpha rotation; R²-selectivity.
- **IBS = (C − L)/(H − L)** mean reversion (370).
- Leveraged-ETF decay (short both legs).
- **Multi-asset trend (371)–(373):** w ∝ R, R/σ or R/σ². R/σ² is the max-Sharpe solution with a diagonal covariance ✓.

### 2.4 Fixed income (Ch. 5)
- Bond maths (374)–(389), standard.
- **Barbell vs bullet convexity:** C − C* = w1w2(T2 − T1)²/(w1 + w2)² > 0 (394) ✓. This is the variance of maturities, so a barbell always has more convexity at equal duration.
- Immunisation (396)–(403) ✓; butterflies (404)–(409); value spread regression (410)–(411).
- Carry = yield + roll-down (413)–(415).
- CDS basis, swap spread.

### 2.5 Indexes and volatility (Ch. 6–7)
- **Indexes:**
  - Cash-and-carry F* = (S − D)e^{r(T−t)} (421); basis (422).
  - Dispersion (423)–(424). Footnote: pairwise correlations are unstable out-of-sample.
  - Statistical risk model ψ = ξ²δ + ΣλVVᵀ, with K chosen by effective rank (425)–(427).
  - ETF intraday arbitrage with κ = 1.002 and FoK MLOs; "slippage will eat profits".
- **Volatility targeting:** w = σ*/σ with a rebalance threshold on |Δw|/w.
- **VIX futures basis:** D = (UX1 − VIX)/T, entry ±0.10 and exit ±0.05 (431).
- **VXX/VXZ:** roll loss; hedge h = ρσ_X/σ_Z; w = σ_X C⁻¹σρ (432).
- **Volatility risk premium:** sell straddles. Gamma hedging turns this into a theta play.
- Skew: risk reversal.
- **Variance swap:** v = (F/T)ΣR² (434)–(436), not demeaned.

### 2.6 FX (Ch. 8): the most NEXA-relevant chapter
- **§8.1 MA crossover on Hodrick–Prescott-filtered log FX rates (437)–(439), λ = 100n² (n = 12 for monthly data).**
  - **INFERENCE, look-ahead:** the HP filter is a **two-sided** smoother. Run on the full sample, the trend at time t uses data after t, with a well-known endpoint revision problem. For trading it must be computed recursively (one-sided, re-estimated each bar). The source does not warn about this.
- **§8.2 Carry:**
  - Uncovered interest parity (UIRP) (440) fails empirically: the forward-premium / **Fama puzzle**. High-rate currencies tend not to depreciate as UIRP implies.
  - Covered interest parity (CIRP): F = S(1 + r_d)/(1 + r_f) (441).
  - Risk: crash, i.e. sudden appreciation of the funding currency.
- **§8.2.1 High-minus-low (HML) carry** by forward discount D = s − f ≈ r_f − r_d (442)–(443). Quantiles are small because there are few currencies.
- **§8.3 Dollar carry:** sign of the average forward discount D (444).
- **§8.4 Momentum + carry minimum-variance combination (451)–(452):**
  - w1 = (σ2² − σ1σ2ρ)/(σ1² + σ2² − 2σ1σ2ρ) ✓.
- **§8.5 Triangular arbitrage:** trade when R = Bid·Bid/Ask > 1 (453). Ephemeral; an HFT domain.

### 2.7 Commodities and futures (Ch. 9–10)
- **Commodities (Ch. 9):**
  - roll yield φ = P1/P2 (454); COT hedging pressure;
  - value v = P_{5y}/P_0 (455);
  - **skewness premium:** buy low-skew, sell high-skew (456)–(458).
- **OU log-spot futures pricing (462) ✓ verified:** ln F = e^{−κτ}X + a(1 − e^{−κτ}) + σ²/(4κ)(1 − e^{−2κτ}).
  - SOURCE: "fancy" ≠ better. In-sample fit may have no out-of-sample power.
- **Hedging (§10.1):**
  - Cross-hedge payoff (463) = basis risk + underlying mismatch.
  - Interest-rate futures hedges (464)–(466); conversion-factor hedge h_C = C·M_B/M_F (467); duration hedge h_D = βD_B/D_F (468).
- **Calendar spreads (§10.2).**
- **§10.3 Futures contrarian:** w_i = −γ(R_i − R_m) with Σ|w_i| = 1 (469)–(471); weekly rebalance.
  - The volume/open-interest variant (472)–(473) uses v = ln(V/V′) and u = ln(U/U′): take the top half by volume change, then the bottom half by open-interest change.
- **§10.4 Time-series momentum (TSMOM) (474)–(480):** w_i = γ·sign(R_i)/σ_i.
  - This equals the mean–variance solution with diagonal C and E_i = η_iσ_i (verified: C⁻¹E = η/σ).
  - **Instability:** sign(R) flips for |R| ≪ σ. The fix is η = tanh(R/κ), with κ for example the cross-sectional SD of R.
  - Dollar-neutral variants: demeaning (477), or separate γ± (478)–(480). With skewed signs, demean returns against the market first.
  - Alternatives: EMA, HP or Kalman filters for the trend (fn. 172).

### 2.8 Structured assets, convertibles, tax arbitrage, miscellaneous (Ch. 11–14)
- **CDO tranches:**
  - expected loss L(t) = Σp_α max(min(ℓ_α, L_d) − L_a, 0) (481);
  - mark-to-market (MTM) = premium leg − contingent leg (482)–(484); risky duration (486);
  - delta hedges D/D_ix (487)–(489); curve-trade carry (490)–(491).
- **Mortgage-backed securities (MBS):** negative convexity; monotone-constrained regression for hedge ratios.
- **Convertible arbitrage:** h = Δ·C (492)–(493). Convertible option-adjusted spread (OAS) by bisection on a parallel curve shift (494).
- **Tax arbitrage:**
  - Muni tax arbitrage R = r_long − r_short(1 − τ) (495).
  - Dividend imputation (496) ✓, giving I = D(1 − τ_p)/(1 − τ_c).
  - **SOURCE ERROR (rendered p. 104):** the text states "1 + κ = 1/(1 + τ_c)". From (496), D + C = D/(1 − τ_c), so it must be **1/(1 − τ_c)**.
  - American put bound (497); deep-ITM put trick P&L = D(1 + κ) (499).
- **Inflation swaps:** zero-coupon (500)–(501) and year-on-year (502)–(503).
- **TIPS–Treasury arbitrage (504)–(508):** C(0) > 0 "even after transaction costs" (SOURCE citing Fleckenstein–Longstaff–Lustig).
- **Weather:** CDD/HDD indices (509)–(511); variance-minimising hedge ratios Cov/Var (512)–(515).
- **Spark spread:** S = P_E − H·P_F (516)–(517); hedge h = H·F_E/F_F with the contract-size integer approximation (518).

### 2.9 Distressed, real estate, cash, crypto, macro, infrastructure (Ch. 15–20)
- **Distressed debt (§15.1–15.3):**
  - distressed = spread over 1,000 bp;
  - "distress risk puzzle": healthy minus distressed (HMD), with bankruptcy probability from a logit.
- **§15.3.1 Volatility-managed HMD (519):** HMD* = (σ_target/σ)·HMD, with σ_target 10–15 % and σ the realised volatility over the prior year.
  - Purpose: HMD has a time-varying market beta that turns strongly negative after downturns, which produces crash risk on rebounds.
  - Same mechanism as the momentum-crash literature (Barroso & Santa-Clara 2014; Daniel & Moskowitz 2016).
  - Unlevered version: min(σ_target/σ, 1) (fn. 203).
- **Real estate:** return (520); diversification claims (low correlation, also in crises; SOURCE citing literature); MSA momentum.
- **Cash:**
  - **§17.2 money laundering is listed as a "strategy" (placement / layering / integration). It is descriptive only, excluded from the NEXA knowledge base as an action, and ethically and legally irrelevant.**
  - §17.6 loan sharking is likewise noted as illegal.
- **Crypto ANN (§18.2, eqs 521–537):**
  - inputs: normalised demeaned returns, EMA, EMSD and **RSI = ν+/(ν+ + ν−)**, a 0–1 scale with sums of positive and negative returns;
  - λ = (τ − 1)/(τ + 1); ReLU hidden layers; K-quantile classification with cross-entropy (536); trade the top or bottom predicted class (537);
  - fn. 225 excludes warm-up points from the quantiles (a correct causal detail).
  - **SOURCE ERROR (rendered p. 120):** eq (535), labelled "softmax", is printed as Y_i/ΣY_j **without exponentials**. That is not softmax, and it can give negative or undefined "probabilities". The glossary's own definition (exp(x_i)/Σexp(x_j), p. 325) is correct, so the book is internally inconsistent.
- **Naive Bayes Bernoulli (§18.3, eqs 538–546):**
  - assumes conditional independence across tweets *and* words given the class;
  - the "P(A), P(B) independently of each other" wording for marginals is loose.
- **Global macro (§19):**
  - fundamental macro momentum (4 state variables; 3–6 month holding);
  - inflation hedge CA = max(0, min((HI − CI)/HI, 1)) (547);
  - global fixed income ranking;
  - **§19.5 announcement-day effect:** equities earn higher returns on FOMC and other announcement days. This is SOURCE citing Savor & Wilson 2013 and Lucca & Moench 2012, for equities.
- **Infrastructure (§20):** descriptive only.

### 2.10 Appendix A: R backtest code `qrm.backtest()` (fully traced)
- **Design:**
  - intraday, dollar-neutral portfolio; top-2,000 ADDV universe recomputed every d.r = 21 days;
  - statistical risk model (PCA / effective rank) or heterotic model; bounded mean–variance optimiser;
  - linear cost.
- **Data layout:** dates descend (column 1 = most recent).
  - `close1`/`open1` shift by one column, so P&L at column i uses day i−1's close/open.
  - The signal `ret[,i]` is the overnight return close(day i) → open(day i−1).
  - So the mean-reversion example **trades at the same open it uses to compute the signal: delay-0.**
- **The authors' own words:**
  - Delay-0 is "borderline in-sample"; real orders "could never be executed exactly at the open".
  - Delay-1 (yesterday's prices, trade today's open) is "basically 1 day out-of-sample (and, not surprisingly, is expected to backtest much worse)".
  - Using today's close to trade today's open is "grossly in-sample".
  - The momentum example (`-log(close/open)` of day i, traded on day i−1) is delay-1 ✓ by our trace.
- **Risk machinery:** universe, risk model and ADDV are 100 % out-of-sample. Our trace: `tr` and `addv` at column i use data up to day i's close, and trading is on day i−1 ✓.
- **Survivorship:** not handled. The authors claim it is "not detrimental" for intraday strategies (SOURCE, citing their own 2015b). INFERENCE: the universe is still survivor-selected (delisted names are absent), so the claim is weaker than stated.
- **Cost model:**
  - τ_i = ζσ_i/A_i (Almgren et al. 2005 form), normalised so that mean τ = 10 bp per dollar traded.
  - Expected-return shrinkage E_eff = sign(E)·max(|E| − τ, 0) (551), an approximation in place of full cost-aware optimisation.
- **Metrics:** total P&L; annualised return (×252); annualised Sharpe (×√252); cents-per-share.

### 2.11 Glossary, notations and index (read)
- **Backtest-hygiene definitions** (useful canonical vocabulary):
  - **delay-d backtest:** all quantities used at t computed from data ≥ d trading days before t (p. 291);
  - **out-of-sample backtest/computation:** quantities at t computed only from data before t (p. 314);
  - **over-fitting:** "fitting more free parameters than justified by the data … unpredictive out-of-sample" (p. 315);
  - **cross-validation** is equated with "out-of-sample testing" (p. 290). This is a loose equivalence; for time series, plain k-fold cross-validation is not out-of-sample.
- **Other definitions:**
  - Sharpe = (excess) return / volatility; annualised as daily × √252.
  - IBS defined as above; pivot = (H + L + C)/3.
  - RSI defined on a 0–1 scale.
  - Volatility risk premium: implied volatility > realised "most of the time".
  - Low-volatility anomaly; Kelly strategy = maximise expected log wealth.
- **Glossary typo:** "naked put: a stand-alone put call option".
- **Index:** survivorship bias appears only at p. 125 (App. A); Kelly appears only at p. 115 (fn. 213, cash vs Kelly; cites Kelly 1956, Thorp 2006, Thorp & Kassouf 1967 = S21); over-fitting at p. 118 (ANN only).
  - This confirms that multiple-testing and overfitting control is **not** a treated topic in the book.

## 3. Bibliography (automated full pass + targeted reading)
- **Entries:** 1,951. By decade: 1980s 138, 1990s 326, 2000s 628, 2010s 803.
- **Topic keyword counts:** FX ≈ 65–67; momentum 97; volatility 120; machine learning (ML) 44; technical analysis (TA) 35; Kelly 9.
- **Overfitting / data-snooping references: only 3** (Sullivan–Timmermann–White 1999; Suhonen et al. 2017; Hsu et al. 2018).
  - **No Bailey/López de Prado (PBO, deflated Sharpe), no Harvey–Liu–Zhu.**
  - This is notable for a 151-strategy catalogue: the book offers no defence against selecting among many strategies.
- **FX-relevant TA literature:** Osler 2000/2003 (support/resistance clustering at round numbers in FX); Taylor & Allen 1992 (chartist survey).
- **Gold literature:** Draper/Faff/Hillier 2006; Grudnitski & Osborn 1993; Poitras 1990.

## 4. Principles (tagged)
1. **SOURCE.** Backtest timing must be explicit: delay-0 is "borderline in-sample" and delay-1 "backtest[s] much worse". The gap between them measures how much of a signal is execution-timing illusion.
2. **SOURCE.** Faint alphas are not individually tradable after costs. Combination plus cost-aware shrinkage (E_eff) is the professional approach.
3. **SOURCE.** Single-instrument TA rules are viewed as unscientific by many. MA crossovers may be repackaged momentum.
4. **SOURCE + verified maths.** Vol-scaled TSMOM (sign/σ) equals mean–variance with a diagonal covariance. Sign instability near zero argues for a continuous (tanh) signal.
5. **SOURCE (citing literature).** Volatility targeting σ_target/σ mitigates factor/momentum crash risk after high-volatility downturns.
6. **INFERENCE.** Two-sided filters (HP, centred MAs, Kalman *smoothers*) and overlapping-horizon KNN targets are look-ahead traps that the book does not flag.
7. **INFERENCE.** The book's near-absence of multiple-testing literature means its catalogue should be treated as a *hypothesis space*, not as validated edges.

## 5. Critical assessment
- **Strengths:**
  - breadth and clean notation; equations largely correct;
  - candid statements on delay-0 and fading alphas;
  - working out-of-sample backtest scaffolding with a realistic cost heuristic;
  - an enormous bibliography.
- **Weaknesses:**
  - no empirical verification by design;
  - "empirical studies suggest" claims cannot be checked inside the book;
  - two confirmed formula errors (1 + κ; non-exponential "softmax");
  - look-ahead traps left unflagged (HP filter, KNN target overlap);
  - survivorship hand-waved;
  - almost no multiple-testing content;
  - includes illegal activities as "strategies" (descriptive).

## 6. NEXA relevance
- **H-DELAY-PARITY** (execution timing; links D-EXEC-ENTRYBAR and S14 same-close execution):
  - Every NEXA engine should be re-run with a delay-0 vs delay-1 (next-bar-open) execution switch. The edge that survives delay-1 is the honest one; the delay-0 minus delay-1 gap estimates the timing illusion.
  - Data: available (NEXA M1–D1 bars, closed-bar evaluation).
  - Validation: in-sample only, no retuning of the frozen V2/8E campaign.
  - Evidence: research principle (SOURCE) / hypothesis for NEXA.
- **H-TSMOM-TANH:**
  - A vol-scaled time-series momentum descriptor η = tanh(R_T/κ)/σ per symbol, as a *conditioning/regime variable* rather than an engine.
  - Test whether the 8E trend engines' trade outcomes covary with it, and whether it is just "momentum in disguise" (the S22 §3.21 critique).
  - Risks: horizon multiplicity; overlap with H-HURST-GATE (S15).
  - Evidence: hypothesis.
- **H-VOLTARGET-CAP:**
  - σ_target/σ exposure scaling, capped at 1 (no leverage), **inside** NEXA_Risk's fixed caps (not modifying them). Compare drawdown clustering in research only.
  - Source mechanism is equities/factors (SOURCE citing literature); transfer to spot FX/XAU is a hypothesis.
- **H-COST-SHRINK:**
  - Apply E_eff = sign(E)·max(|E| − spread − commission − slippage, 0) as a research **gate**: any NEXA signal whose expected move per trade does not exceed the round-trip cost should be zeroed.
  - Links S10 (asymmetric news slippage) and S02/S03 cost tolerance.
- **H-CARRY-SWAP** (DATA-PARTIAL):
  - FX carry and the Fama puzzle are relevant to multi-day holds, and swap/rollover cost is a real P&L term for NEXA.
  - MT5 exposes current swap_long/swap_short per symbol, but **no historical swap series** is in NEXA data. A carry signal cannot be backtested honestly; only the current-cost impact can be estimated.
  - Evidence: established phenomenon in literature (SOURCE); data-limited for NEXA.
- **Do not use:**
  - two-sided HP-filtered signals;
  - KNN/ML targets that overlap the horizon;
  - the triangular-arbitrage / HFT family (latency domain);
  - options, credit, real estate, tax, infrastructure and illegal "strategies";
  - BTC ANN/naive-Bayes recipes, which are overfit-prone and not NEXA instruments.

**Cross-references:**
- S21 (Thorp, cited for Kelly in fn. 213);
- S14 (delay/same-close look-ahead);
- S15 (MA-reversion artefact; HP/MA filters);
- S10 (costs/slippage);
- S04 (noisy objective);
- S17 (TD), S09/S19 (bands);
- S23/S25 (volatility/execution);
- S01 (practitioner FX).
