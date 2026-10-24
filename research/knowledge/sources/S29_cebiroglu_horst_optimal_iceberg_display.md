# S29: Gökhan Cebiroğlu & Ulrich Horst, "Optimal Display of Iceberg Orders" (SFB 649 Discussion Paper 2011-057, Humboldt-Universität zu Berlin, Aug 2011)

**File:** `668476885.pdf`. 43 pp. EconStor cover (p. 1), SFB cover (p. 2) and the SFB paper list (pp. 40–43) are included. Data support from Deutsche Bank.

| Field | Value |
|---|---|
| **Source type** | Other academic institution (Humboldt Berlin), with an industry co-author (Deutsche Bank). Working paper, not peer-reviewed in this form. |
| **Evidence status** | **Model:** established within assumptions. Lemma 1 and Props 2–5 come with proofs; the Prop 1 proof is said to be "in the appendix" but is **not present** in this version. **Empirics:** research finding. INET message data, Jan–Feb 2009, 8 tech stocks. Imbalance → flow/price correlations are significant at 0.001. Headline "up to 60 %" execution improvement is **model-implied**, not realised. |
| **Processing** | All 43 pp. read. Pp. 34–37 (Figs 6–9, 3-D surfaces) are mostly axis labels in the text layer. **Rendered:** p. 21 (Figs 1–2 flow estimates) and p. 36 (Fig 8 performance surfaces). Tables 1–3 were parsed from the text. |

## 1. Model (SOURCE)
**Setup**
- A liquidity buyer of N shares over [0, T] posts an iceberg at the best bid B₀ and displays Δ ∈ [0, N].
- Anything unfilled at T is bought at the best ask A_T.
- **Relative cost:** P̄^Δ = (1 − V_T^Δ/N)·S_T^Δ, where S = (A_T − B₀)/B₀ is the opportunity cost of non-execution.
- **Key assumption:** V and A are conditionally independent given Δ. Then W(Δ) = (1 − E[V^Δ]/N)·μ(Δ), with μ = E[S_T]. The trader minimises W.

**Priority rules:** price, then display, then time.
- Volume ahead of the displayed part: Q_d = D(1 − C) + ŷ.
- Volume ahead of the hidden part: Q_h = Q_d + Δ + h + y.
- The execution volume V^Δ_T is piecewise in the market-order volume x (eq. 2.4).
- Aggregation gives a **lower bound** on execution (Remark 2).

**Flow distributions:** zero-inflated exponentials, f(s) = (1 − q)1{s = 0} + (q/β)e^{−s/β} (eqs. 2.6–2.9), for
- market orders x (p, α);
- limit orders at the price level y (q, β);
- limit orders ahead / price-improving ŷ (q̂, β̂);
- hidden liquidity h (r, γ).

**Prop 1 (closed form):**
- E[V^Δ] = αp·e^{−D(1−C)/α}(1 − β̂_r)[(1 − β_r)(1 − γ_r)(e^{−Δ/α} − e^{−N/α}) + 1 − e^{−Δ/α}].
- Ratios: β̂_r = q̂β̂/(α + β̂), β_r = qβ/(α + β), γ_r = rγ/(α + γ).
- Bound: 0 < E[V] ≤ pα·e^{−D/α}(1 − e^{−N/α}) < pα.
- *Our check:* the structure is consistent with sequential exponential queue depletion. The bracketed reconstruction is from garbled text; the proof is absent.

**Lemma 1:** ∂W/∂Δ < 0 (priority gain); ∂W/∂α < 0; ∂W/∂β̂_r > 0; ∂W/∂β_r > 0; ∂W/∂μ > 0.

**Exposure impact via imbalance**
- I₀ = (D_bid − D_ask)/(D_bid + D_ask).
- With display: I(Δ) = (I₀ + Δ_r N_r)/(1 + Δ_r N_r). The text prints "I₀ − Δ_r N_r" but defines the numerator as D_bid − D_ask + Δ, so the sign typo is inferred.
- All flow parameters and μ are functions of I.
- **Decomposition (eq. 2.16):** dW/dΔ = M_market − M_priority, i.e. exposure impact vs priority gain.

**Results**
- **Cor 1:** if larger imbalance raises liquidity demand, lowers competition and moves price toward the excess, then full display is optimal (Δ* = N).
- **Prop 2:** for large N, Δ* = 0 if ∂μ/∂I > 0 (price drifts away), and Δ* = N if ∂μ/∂I < 0.
- **Prop 3:**
  - for very large or very small D_ask, or extreme imbalances, Δ* = N;
  - for large D_bid, the sign of ∂μ/∂I decides.
  - Remark 4: this relies on exponential tails; fat tails may overturn it.
- **Prop 4:** with strong limit-order competition or weak demand, the sign of ∂μ/∂I decides.
- **Prop 5:** a volume-maximising trader displays more than a cost-minimising trader when ∂μ/∂I > 0, because volume traders underweight opportunity cost. This is consistent with Bessembinder–Panayides–Venkataraman (2009).

## 2. Empirics (SOURCE)
- **Data:**
  - INET (NASDAQ ECN) message data, Jan–Feb 2009, 9:30–15:30;
  - NASDAQ ModelView minute snapshots used as a proxy for hidden depth;
  - stocks CSCO, DELL, EBAY, HPQ, MSFT, ORCL, plus AAPL and AMZN (wider spreads);
  - non-overlapping windows Δt ∈ {3, 10, 30} s;
  - imbalance bins of 0.15 from −0.7 to 0.7; MLE per bin, then cubic weighted OLS smoothing.
- **Findings:**
  - **"Front-running" (price-improving) limit flow ŷ reacts most strongly to imbalance.** For ORCL (CSCO), E[ŷ] rises from < 4,000 (5,000) to > 15,000 (25,000) shares as I goes from strongly negative to strongly positive. This is driven by arrival probability q̂ (< 15–20 % → > 50–65 %).
  - The market-order flow response is weak.
  - **Price moves in the direction of excess imbalance.** E[A_T | I] at 30 s is ≈ +4 bp (CSCO) and +2 bp (ORCL) for I > 0.5. That is comparable to the 5–6 bp spreads.
  - The effect is asymmetric: about +3 / −1 bp at I = ±0.5.
  - **Table 2 correlations** of I with the price increment: CSCO 0.23 (3 s) → 0.12 (30 s); HPQ 0.19 → 0.06. Impact decays with horizon, more slowly for less active stocks (DELL, EBAY peak at 10 s).
  - **Interpretation (SOURCE):** this supports Harris's (1996) parasitic / quote-matching traders who undercut visible orders. There is only weak support for Moinas's "impatient traders retreat".
- **Calibrated optimal display (Figs 6–7):**
  - small orders: full display;
  - intermediate orders: partial display, more when imbalance is on the opposite side;
  - large orders: hide.
- **Iceberg vs limit order (Figs 8–9):** relative improvement σ = (W_ice − W_lim)/W_lim reaches up to **−60 %** for large orders. The paper is internally inconsistent about *where* the gain arises (§3 below).

## 3. Critical assessment (INFERENCE)
1. **The V–A independence assumption omits adverse selection.**
   - A bid fills when sell market orders arrive, and those coincide with downward price pressure. Fills are therefore correlated with A_T, which W ignores.
   - S06, S10 and S11 show fill-conditional drift is first-order for passive orders.
   - The filled part is also costed at zero relative to B₀.
2. **Internal inconsistencies:**
   - The text says Figs 8–9 use Δt = 10 s; the captions say 30 s.
   - The text says the gain is largest when "imbalance-excess is massively on the trader's side". The Fig 8 caption says the gain is "reached for opposite-side imbalance-excess".
   - The proof of Prop 1 is promised but absent.
   - The I(Δ) sign typo noted above.
3. **Hidden-depth proxy:** NASDAQ ModelView is used for INET hidden depth (acknowledged). Market fragmentation means only INET flow is seen.
4. **"Up to 60 %" is a modelled cost reduction under estimated parameters,** not a realised execution study.
5. **Correlations are on binned conditional means.** The significance tests may overstate precision. Two months of a single crisis period (early 2009).

## 4. Principles
- **SOURCE + S27/S34/S26:**
  - displayed liquidity is information; exposure triggers competing (front-running) limit orders and adverse price drift;
  - hiding costs queue priority;
  - the optimal display trades **exposure impact** against **priority gain**.
- **SOURCE:** the order-book imbalance near the touch predicts very short-horizon (seconds) price changes of the order of the spread. The effect decays within tens of seconds.
- **INFERENCE:** the choice of objective changes optimal behaviour (Prop 5). An execution metric that ignores opportunity cost (fill rate) induces over-exposure. This parallels NEXA's need to judge fills by *cost incl. misses* (S10's δ* = α logic).

## 5. NEXA relevance
- **No direct use:** retail CFD, no order book, no icebergs. DATA-LIMITED for all imbalance effects.
- **Transferable:**
  1. If NEXA ever uses resting LIMIT entries, evaluate them on *total cost including the opportunity cost of misses*, not fill rate (cf. H-DEVIATION-OPT in S10).
  2. Seconds-scale imbalance effects (≈ spread size) are irrelevant to M15+ engines, beyond implying that fills cluster at adverse micro-moments.

**Cross-references:**
- S27 (Esser–Mönch, the predecessor model);
- S28 (iceberg QA);
- S34 (imbalance → trade sign);
- S26 (agents use imbalance);
- S06 (displayed size as a signal; sniping);
- S32 Harris (parasitic traders, order exposure);
- S10 (fill/miss trade-off).
