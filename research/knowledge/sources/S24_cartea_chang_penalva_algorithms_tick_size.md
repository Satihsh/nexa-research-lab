# S24: Cartea, Chang & Penalva, "Algorithms and Supracompetitive Prices in Electronic Markets: The Impact of Tick Size"
**File:** `ssrn-4105954.pdf`. 63 pp. SSRN 4105954; this version 20 Jan 2026 (first version May 2022). Oxford-Man Institute and Universidad Carlos III.

| Field | Value |
|---|---|
| **Source type** | Oxford / university research (working paper) |
| **Evidence status** | **Theoretical result (proofs) plus simulations.** No market data. |
| **Processing** | All 63 pages read: the main text, Appendix A (proofs), B (horizontal-competition micro-foundation), C (algorithm pseudocode), D (stochastic-approximation verification, conditions C1–C3), E (asymmetric algorithms), F (convergence times) and G (proofs of Props 3–4, Lemma 4). Figures are interpreted from their captions; the equations in the text extraction were legible. |
| **Source fact (drafting artefact)** | Appendix B (pp. 30–31) contains an unedited **"INTERNAL NOTE"** speculating that fast MMs may prefer to become slow under grid effects. It is a draft remark, not a result. |

## 1. Method: learning dynamics as ODEs (stochastic approximation, Benaïm 1999)
**Recursion:** x(n+1) − x(n) = γ_n f(x(n), π(n)), with Σγ_n = ∞ and Σγ_n^{1+q/2} < ∞.

**Decomposition**
- Rewrite the recursion as γ_n (F(x) + U(n)), with F = E[f] and U the martingale noise.
- The interpolated process is then an **asymptotic pseudotrajectory** of ẋ = F(x), given:
  - E|U|^q < ∞ (C1);
  - bounded x (C2);
  - vanishing approximation error (C3).

**Resulting dynamics**
- **Cross learning and EXP3 → replicator dynamics:** ẋ_k = x_k [(Πx)_k − xᵀΠx] (ODE 2).
- **Q-learning (single state):** Q̇_ik = x_ik [Π_ik + δ max Q_i − Q_ik] (ODE 1).
- **Frequency-adjusted and synchronous Q-learning → replicator–mutation dynamics:** ẋ = τ x[(Πx)_k − xᵀΠx] + x_k Σ x_ℓ ln(x_ℓ/x_k) (ODE 3).

**Results**
- **Proposition 1:** in partnership (potential) games, Cross learning and EXP3 converge almost surely to a **pure-strategy Nash equilibrium** of the stage game.
  - Proof: xᵀΠx is a strict Lyapunov function (Hofbauer); mixed equilibria are unstable (Duffy–Hopkins); Pemantle.
- **Proposition 6:** FAQ-learning and synchronous Q-learning do the same, given sufficient exploitation τ.
- **Proposition 2: standard Q-learning can get stuck in asymmetric, non-Nash outcomes.** With no exploration it cannot learn a best response to a fixed opponent.

## 2. Market-making stage game
**Set-up**
- I market-making algorithms post asks on the grid A = {ϑ, 2ϑ, …, 2}. ϑ is the tick size; 2 is the competitive fringe's price.
- **Fill probability:** P(a_i, a_{−i}) = e^{−µ a_i} / Σ_j e^{−µ a_j}, a smoothed price priority. µ is "price aggressiveness"; µ → ∞ gives Bertrand.
- **Payoff:** π = a_i P (eq. 5).

**Equilibria**
- **Proposition 3, continuous grid:** a unique Bertrand–Nash offer a_BN = I/(µ(I−1)) for µ > I/(2(I−1)); otherwise monopoly a_M = 2.
  - Pricing at zero (perfect competition) is strictly dominated for finite µ.
- **Proposition 4, discrete grid:** the symmetric pure Nash equilibria lie in [L*, U*], with
  - L* = ϑI/((I−1)(e^{µϑ} − 1));
  - U* = ϑI/((I−1)(1 − e^{−µϑ}));
  - the set is non-empty and contains a_BN, and both bounds → a_BN as ϑ → 0.
- **Proposition 5:** with I = 2 and ϑ = 1, there is a unique equilibrium (2, 2) if µ ≤ ln 3; otherwise two equilibria, (1, 1) and (2, 2).

**Spread decomposition** = Bertrand–Nash + **grid discreteness** (which can be negative) + **learning (equilibrium-selection) effect**.

## 3. Results (simulation; SOURCE)
**Basins of attraction**
- With µ = 2, the competitive equilibrium's basin covers 75.65 % of the policy square.
- With µ = ln 4 and ϑ = 1, 26.85 % of initial conditions converge to a_i = 1.

**Effect of tick size**
- **Smaller ticks give lower excess profits.** Normalised excess profits fall from 20–30 % to ≈ 0 for replicator-type algorithms, and from 30–40 % to 20–30 % for Q-learning.
- **Supracompetitive selection becomes *more frequent* among the multiple equilibria**, but the gap is bounded and smaller.
- **Smaller ticks give slower convergence** (Fig. F.11).

**Q-learning specifically**
- Rarely reaches a Nash equilibrium.
- Often asymmetric and supracompetitive (above the least-aggressive Nash equilibrium).
- Can be "fooled" into suboptimal play by adaptive opponents (App. E).

**Policy implication:** there is a tick-size trade-off. Targeting an "m-tick spread" policy is problematic because the spread is endogenous.

## 4. Principles and assessment
**SOURCE / established**
- Independent learning algorithms in repeated pricing games can sustain supracompetitive prices **without communication**.
- Equilibrium selection depends on initial conditions and on the algorithm class.

**INFERENCE**
- The spreads NEXA pays reflect the competitive structure of the price providers (Pepperstone's liquidity sources), not just volatility.
- Spreads can be "stuck" wider than fundamentals justify, especially at coarse effective ticks.

**Limits**
- Stylised: a single state, a fixed fringe, no inventory, no information asymmetry in the main model.

## 5. NEXA relevance
- **Low direct trading relevance.** It is market-design theory.
- **Indirect uses**
  1. Understanding why CFD spreads behave discretely: e.g. XAU's 12-point modal true spread, and the regime jumps to 17 at rollover in NEXA's tick audit.
  2. **The math toolkit for any NEXA adaptive allocator:** replicator dynamics, EXP3, Hedge.
     - **Caution:** naive Q-learning can lock into suboptimal actions.
     - Prefer algorithms with convergence guarantees (EXP3 / Hedge / FAQ).
     - This links to S12's online portfolio selection (Aggregating Algorithm / EG) and S03's DRL.
- **Hypothesis H-SPREAD-REGIME (descriptive):** model Pepperstone XAU spreads as a few discrete states, e.g. a hidden Markov chain over {9, 12, 13, 17} points. Use them as a regime / cost feature (data: 21 days of ticks; more needs recording).

**Cross-references:** S06 (collusion via signalling, same authors), S11 (spread formation), S12 (online learning algorithms), S03 (RL), S26 (algorithm behaviour from data).
