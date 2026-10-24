# PRE-REGISTRATION OF-19: relative initial-balance width predicts the outcome of an accepted break

**Inherits `PREREG_OF_COMMON.md`.** Written before any OF-19 outcome is computed. The SHA-256 is in `PREREG_HASHES.txt`.

## 1. Claims under test

- **CL-003** (SRC-YT-006, 10:50–12:32; paraphrased): when the initial balance is small relative to recent days, a break that does not return inside should produce a large directional move. Large-IB days tend to stay inside the IB. The source states this as a default rule; no statistics are given.
- **CL-004** (SRC-YT-006, 12:47–13:04): a break that immediately returns inside the IB should be exited quickly. This is used **only** as the exit rule of the trade translation (§6).
- **Registry links:** HYP-011, and OF-07 (IB width as context).
- **Evidence quality:** practitioner rule, ES futures RTH. Instrument transfer to the spot FX/XAU anchored sessions.
- **No volume is used,** so the T1 proxy status is irrelevant. GBPUSD **counts** in the verdicts.

## 2. Definitions

**Session, IB and relative width**
- **Session and IB:** COMMON §C3, with the symbol's primary anchor. The secondary anchor is a counted trial.
  - IB_d = max(high) − min(low) over the IB window.
  - IBH, IBL = the IB high and low.
- **Relative width:** RIB_d = IB_d / median(IB_k over the N most recent valid sessions k < d).
  - **N = 20 is primary.** The source says only "recent days", so N is a NEXA choice, matched to the σ̂ window.
  - N ∈ {10, 60} are counted sensitivity trials.
- **Width classes:** SMALL / MID / LARGE = the RIB terciles, with cut-points from discovery per symbol and anchor, frozen.

**Break, acceptance and failure**
- **Break:** the first bar t with a + 60 min ≤ t and t + m ≤ E whose **close** is > IBH (up, β = +1) or < IBL (down, β = −1). Only the first break per session is used.
- **Acceptance** (the source's "does not return inside"): no bar in (t, t + m] trades back inside the IB.
  - Up: every low ≥ IBH.
  - Down: every high ≤ IBL.
  - **m = 30 min is primary** (one 30-min TPO period). The source gives no duration, so this is a NEXA choice; m ∈ {15, 60} are counted sensitivity trials.
  - T_a = t + m, and P_a = the close of the bar at T_a.
- **Failed break:** a break that is not accepted. Counted and reported (CL-004 context).

**Session close:** C_E = the close of the last bar before E.

**Trial grid:** {primary, secondary anchor} × N ∈ {10, 20, 60} × m ∈ {15, 30, 60} × 4 symbols = 72 cells.
- **Primary cell:** (primary anchor, N = 20, m = 30).
- **Primary family:** 4 symbols.

## 3. Outcomes (accepted breaks only, measured after T_a)

**Y1 directional close (primary):** Y1 = 1[ β·(C_E − level) > 0 ], where level = IBH for up and IBL for down.

**Driftless null p0 (per event):** p0 = Φ( β·(P_a − level) / σ_rem ).
- σ_rem = σ̂_d · √share(T_a, E).
- share(T_a, E) = Σ over New-York-local minutes in (T_a, E] of the discovery mean of r²_min / Σ_day r², using M1 close-to-close log returns. This is per symbol: the intraday variance-share curve, frozen from discovery.

**Excess:** e = Y1 − p0, with mean E1_c within width class c.

**Primary effects (both required):**
- θ19a = E1_SMALL − E1_LARGE (the relative-width effect claimed by CL-003);
- θ19b = E1_SMALL (an accepted small-IB break beats the driftless benchmark).

**Y2 extension (secondary):** MFE_σ = β·(extreme in (T_a, E] − P_a) / σ_rem.
- The driftless benchmark is √(2/π) ≈ 0.798.
- Report the SMALL − LARGE difference and SMALL − 0.798.

**Y3 stays inside (secondary, descriptive):** P(no accepted break | width class).
- Partly mechanical (wider ranges are harder to exceed), so it is reported beside the same split by IBR = IB/σ̂_d terciles, to separate *relative-to-recent* from *absolute-in-σ* width.

## 4. Nulls

- **N1 driftless law** (built into p0 and the 0.798 benchmark).
- **N2 width-label permutation:** within each split and symbol, permute the SMALL / MID / LARGE labels across sessions that had an accepted break, 1,000 times. p_N2 for θ19a.

## 5. Decision rule (predictive form, OF-19-P)

**Per symbol:** the COMMON §C8 rule applied to θ19a **and** θ19b, each with its own BH family (4 symbols). A symbol is SUPPORTED only if both are SUPPORTED **and** the pooled p_N2 < 0.10.

**OF-19-P overall:**
- **SUPPORTED** if ≥ 3 of 4 symbols are SUPPORTED.
- **REJECTED** if ≥ 3 of 4 are REJECTED (either effect).
- **INCONCLUSIVE** otherwise.

## 6. Trade translation (OF-19-T; source-derived, secondary family of 1 pooled test)

| Element | Rule | Origin |
|---|---|---|
| Setup | SMALL class, accepted break (primary cell) | CL-003 |
| Entry | Open of the first bar after T_a, direction β | Source: take the accepted break |
| Initial risk D | β·(entry − level), with the level = IBH / IBL | — |
| Stop | First bar trading back inside the IB (up: low < IBH; down: high > IBL). Exit at the level, or at that bar's open if it gaps through | CL-004: "back inside ⇒ exit" |
| Exit | Otherwise the close of the last bar before E (17:00 NY) | **NEXA choice:** the source gives no target |
| Costs | COMMON §C7, including the cost floor (cost > 0.20·D ⇒ no trade) | — |

- **R** = net P&L / D.
- **Comparison set:** the same rules on the LARGE class (reported).
- **Null (geometry-matched random entries, framework §6 (ii)):** for each trade, 50 sessions from the same symbol and split with the same New-York-local entry minute, a random direction, the same D in σ̂ units, and the same stop/exit rules. p_null = the share of null means ≥ the observed mean, over 1,000 replicate means.

**Decision (holdout, pooled over the 4 symbols):**

| Verdict | Condition |
|---|---|
| **SUPPORTED-T** | ≥ 200 trades; 95 % CI lower bound of net E[R] > 0 after the +0.05R stress; ≥ 3 of 4 symbols with a positive point estimate; discovery pooled estimate > 0; p_null < 0.10 |
| **INSUFFICIENT-N** | < 200 holdout trades. No verdict; the result is reported descriptively |
| **REJECTED-T** | Pooled holdout net E[R] after stress ≤ 0 |
| **INCONCLUSIVE-T** | Otherwise |

A SUPPORTED-T result is a research candidate only: G4 at most; G5+ need walk-forward, the robustness battery and S14 fill evidence.

## 7. Robustness (reported)

- Up and down reported separately.
- Per year.
- Friday sessions vs others.
- The secondary anchor.
- +0.10R stress.
- The D distribution in pips and in σ̂.
