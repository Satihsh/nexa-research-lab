# 06: LIQUIDITY MODEL (Tiers 1–2): the revealed-liquidity field

**Key distinction (directive §17):**
- **Resting liquidity** (the limit order book: depth at each price) is **UNAVAILABLE** to NEXA.
- What NEXA can measure is **revealed liquidity**: where volume (true for futures, tick-count proxy for spot) actually traded, and how fast price moved through each price region.
- **Every quantity here is a function of executed or quoted activity, not of the book.**
- The practitioner terms in the new corpus (value area, POC, HVN/LVN, volume clusters, "accumulation zones") all describe this same revealed density (01 §4).

## 1. The field

**L(p,t)** (EQ-012) is a kernel-smoothed, time-weighted volume-at-price density built **only from bars closed before t**:

    L(p,t) = Σ_{s < t} w(t−s) Σ_j v_{s,j} K_h(p − p_{s,j})

**Pre-registered design choices** (they must be fixed *before* testing; alternatives are separate candidates counted in the multiple-testing budget):

| Choice | Default | Alternatives (counted) |
|---|---|---|
| Volume source | Spot tick volume (9 y) | Futures true volume via the basis (2 y); time-at-price (TPO) |
| Intra-bar allocation | Uniform over [low, high] | Typical price (h+l+c)/3 |
| Kernel bandwidth h | 0.10 × σ̂_day (YZ, lagged) | 0.05, 0.20 × σ̂_day |
| Memory | Prior completed session plus the developing session | Exponential, T = 1, 3, 5 sessions |
| Session anchor | §3 below | — |

**Derived quantities:**
- g = ∂_p ln L (gradient, "log-force");
- κ = h²·∂²_p ln L (curvature);
- VA_0.70 and POC (EQ-014);
- concentration C (EQ-015);
- **distance to the nearest HVN/LVN in σ̂ units.**

**HVN/LVN definitions (NEW, mechanical):**
- **HVN:** a local maximum of L with prominence ≥ q·max L, q = 0.2 pre-registered.
- **LVN:** a local minimum between two HVNs whose depth is ≤ 0.5 × the lower adjacent HVN.

## 2. Measured proxy quality (2026-10-04, `evidence/`)

| Quantity | Tick-volume (spot) vs COMEX (true) agreement | Implication |
|---|---|---|
| 70 % value area | Jaccard median **0.82** (range 0.53–1.00), 20 days | **VA-based features are acceptable proxies** |
| POC | Within $2 on 65 % of days; **$12–68 misses on bimodal days** | **POC is fragile.** Prefer smooth density functionals (g, κ, HVN set) or VA bounds |
| Hourly activity level | log r = 0.82–0.88 (0.57–0.70 de-seasonalised) | Activity normalisation must be seasonal (EQ-005) |

**Next validation step (no trading implication):**
- **What:** extend the probe to the full 2-year overlap (2024-10 → 2026-09) and to EURUSD vs 6E.
- **Measure:** distributions of VA Jaccard, |ΔPOC|/σ̂ and HVN-set overlap.
- **Acceptance rule (pre-registered here):** median VA Jaccard ≥ 0.70 and |ΔPOC| ≤ 0.25 σ̂_day on ≥ 60 % of days. If either fails, spot-profile features are demoted to "futures-only".

## 3. Session anchors for 24-hour markets (required by every auction concept)

Market Profile was built on pit sessions (S42, S46). NEXA's instruments trade about 24 hours, so "the open", "IB" and "the day" must be **defined**. The anchors below are pre-registered as UTC with DST-aware rules (D-TZ fixed 2026-10-03).

| Anchor | Definition | Rationale |
|---|---|---|
| **A0 Trading day** | 17:00 New York (= server midnight, NY+7) to 17:00 NY | Pepperstone server day; the FX market convention |
| **A1 London open** | 08:00 London local | Highest-volume FX session start |
| **A2 New York open** | 08:20 ET for gold (COMEX metals open outcry legacy); 08:30 ET (US data) for FX | COMEX gold "day session" convention; US data releases |
| **IB** | First 60 minutes after the chosen anchor | S42/S46 |
| **Session for profiles** | A0 day (primary); A1–17:00 NY (secondary) | Two candidates count as two tests |

**MEASURED support:** the hour-of-day activity profile is shared across sources (r = 0.93–0.98), so anchors defined on one source transfer.

## 4. Liquidity hypotheses (all testable now; registered in 14)

| ID | Statement (mechanism) | Prediction | Falsification / null |
|---|---|---|---|
| **HYP-004 "volume slows price"** (S42, S46: practitioner consensus) | In low-density regions (LVN, κ > 0) price travels faster | Time to traverse a fixed σ̂-distance is shorter, and \|r_{t+1}\|/σ̂ larger, when L(p_t) is low (density percentile) | Rank correlation ≈ 0 after controlling for σ̂ and RVOL. Placebo: shuffle the profile day |
| **HYP-005 "magnet" (gradient)** (S49 POC target; S43 "traders tend to return") | Price drifts toward nearby density mass | sign(p_{t+H} − p_t) agrees with sign g(p_t) more than 50 % of the time; E[(p_{t+H} − p_t)·sgn g] > 0 in σ̂ units | Hit rate = 50 % (binomial, block bootstrap); the effect disappears net of costs at any tradable H |
| **HYP-006 "transition zones" (curvature)** | At HVN (κ < 0), moves revert; at LVN (κ > 0), moves continue | Next-k-bar return autocorrelation is conditionally negative at HVN and positive at LVN | No difference in conditional VR or autocorrelation between κ terciles |
| **HYP-007 Value-Area Rule** (S42) | Opening outside yesterday's VA, then *acceptance* inside (2 consecutive 30-min closes inside) → price traverses to the opposite VA edge | P(touch opposite VA edge before re-exiting the entry edge) > base rate for random entries into VA at matched distance and σ̂ | Probability ≤ placebo; or the effect depends on the acceptance definition (fragility) |
| **HYP-015 "accumulation retest"** (S49 Setup #1, mechanical) | After a balance range (≥ N bars with ER < e) followed by a breakout (close beyond range ± kσ̂), the first return to the range's max-density price produces a reaction in the breakout direction | MFE/MAE in σ̂ units and P_U (EQ-034) above the driftless null and a placebo level (random in-range price) | No difference vs placebo; or only "works" with the zone defined after the fact (look-ahead) |

## 5. Physics vocabulary, demoted to notation (10)

- **U(p) = −ln L(p)** ("potential") and **F = ∂_p ln L** ("force"): HYP-005 is the only test of this "attractor" picture.
- **"Liquidity voids" = LVN (κ > 0):** HYP-004/006.
- **No conservation law, no equation of motion.** These are empirical regularity claims only.

## 6. What would upgrade this model

| Upgrade | Effect |
|---|---|
| Futures true volume (already available, 2 y) | A true-volume field for gold/FX; proxy validation; HYP-016 (incremental value of true volume over tick volume) |
| XAU broker DOM logging (depth 10), prospective | First *resting* liquidity measure, but the broker's book, not the exchange's. A separate approval is needed because it changes the tick logger |
| Futures trades/quotes entitlement | Signed volume at price (delta profile) and footprint; validation of BVC |
