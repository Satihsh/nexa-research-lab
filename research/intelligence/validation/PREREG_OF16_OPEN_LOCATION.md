# PRE-REGISTRATION OF-16: opening location vs prior-session value predicts the day

**Inherits `PREREG_OF_COMMON.md`.** Written before any OF-16 outcome is computed. The SHA-256 is in `PREREG_HASHES.txt`.

## 1. Claim under test

- **CL-005** (SRC-YT-005, 0:00–3:58 and 7:19–8:59; paraphrased): the opening location relative to the prior session's value area sets the daily bias.
  - Open above VAH ⇒ bullish.
  - Open below VAL ⇒ bearish.
  - Open inside ⇒ neutral; fade the edges.
  - Stated to be "≈ 70–80 % accurate". No data or method was given.
- **Not tested here:** CL-014 (news-conditioned acceptance outside value), because it needs a news calendar. Also not tested: HYP-007 (Value-Area Rule, re-entry then traverse), which is a separate registry item.
- **Evidence quality:** unverified practitioner statistic. Instrument transfer: ES RTH → spot FX/XAU, with tick-volume profiles.

## 2. Definitions

**Prior value**
- **Primary:** the VA of server day d−1 (A0 profile, full 24 h; COMMON §C6).
- **Secondary (counted):** the VA of the anchored session S_{d−1}.

**Open and close**
- **Open O_d:** the open of the anchor bar on day d (COMMON §C3), using the symbol's primary anchor. The secondary anchor is a counted trial.
- **Day close C_d:** the close of the last bar of server day d (at E = 17:00 NY).

**Location**

| Label | Condition | Bias b_d |
|---|---|---|
| ABOVE | O_d > VAH_{d−1} | +1 |
| BELOW | O_d < VAL_{d−1} | −1 |
| INSIDE | otherwise | 0 |

**Trial grid:** {primary, secondary anchor} × {A0, anchored profile} × 4 symbols = 16 cells.
- **Primary cell per symbol:** (primary anchor, A0 profile).
- **Primary family:** 3 symbols for the verdict (XAUUSD, EURUSD, USDJPY), plus GBPUSD reported (proxy rejected in T1).

## 3. Outcomes

**Y1 directional hit (primary):** on outside days (b_d ≠ 0), Y1_d = 1[ sign(C_d − O_d) = b_d ].
- Ties (C_d = O_d) count as 0.

**Drift-matched base rate:** π_s = the share of all valid days in split s (same symbol, same anchor) with C_d > O_d.
- For an outside day, the expected hit under "location has no information" is p0_d = π_s if b_d = +1, and 1 − π_s if b_d = −1.

**Primary effect:** θ16 = mean over outside days of (Y1_d − p0_d).

**Y2 barrier (secondary):** on outside days, P(price reaches O_d + b_d·0.5σ̂_d before O_d − b_d·0.5σ̂_d, within [anchor, E)).
- The null is the driftless symmetric barrier law, 0.5, drift-adjusted by the same π_s logic: report Y2 − 0.5 and Y2 − (π_s or 1 − π_s).
- If both barriers are touched in the same M1 bar, the day counts as 0 (against).
- If neither is touched by E, the day is "unresolved" and its share is reported. The primary Y2 rate counts unresolved days as 0; the rate among resolved days is reported.

**Y3 inside-open "neutral" claim (secondary):** on INSIDE days, P(C_d ∈ [VAL_{d−1}, VAH_{d−1}]), compared with the placebo N3 below.

**Magnitude (reported, not a verdict):** mean of b_d·(C_d − O_d)/σ̂_d on outside days, alongside the median round-trip cost (COMMON §C7) in σ̂ units.

## 4. Nulls

- **N1 drift-matched base rate:** p0_d above. This is the primary comparison and is built into θ16.
- **N2 volume-free pseudo-VA (nested; does volume add anything?):** replace [VAL, VAH]_{d−1} with [L + 0.15·R, H − 0.15·R] of the same profile session, where R = H − L. This is the central 70 % of the range.
  - Report θ16 under N2 and the difference θ16(VA) − θ16(N2), with a bootstrap CI.
- **N3 placebo value (geometry-preserving):** for each day d, draw a donor day j (same symbol and split; j ∉ {d−1, d}) and set:
  - VAL* = C_{d−1} + (VAL_j − C_j)·σ̂_d/σ̂_{j+1};
  - VAH* = C_{d−1} + (VAH_j − C_j)·σ̂_d/σ̂_{j+1}.
  - Recompute locations and Y1 for 200 placebo replicates (seed 20261011).
  - p_N3 = (1 + #{θ16* ≥ θ16}) / 201.

## 5. Decision rule

**Per symbol:** the COMMON §C8 rule on θ16, with additional requirement (4): pooled p_N3 < 0.10.

**OF-16 overall (predictive):**
- **SUPPORTED** if ≥ 2 of {XAUUSD, EURUSD, USDJPY} are SUPPORTED.
- **REJECTED** if ≥ 2 of the three are REJECTED.
- **INCONCLUSIVE** otherwise.
- GBPUSD is reported and labelled *proxy-invalid*.

**The "70–80 %" figure (CL-005), per symbol, primary cell, pooled H = mean Y1 on outside days:**

| Result | Condition |
|---|---|
| **REFUTED for the analogue** | 95 % CI upper bound < 0.70 |
| **CONSISTENT** | CI overlaps [0.70, 0.80] |
| **EXCEEDED** | CI lower bound > 0.80 |

The "70–80 %" figure is assessed separately from the edge verdict, because a hit rate can be < 70 % and still beat the base rate.

**Volume value (secondary):** reported as "volume adds information" only if θ16(VA) − θ16(N2) has a pooled 95 % CI lower bound > 0. This is required before any profile-specific claim is made.

## 6. Robustness (reported; does not change the verdict)

- Above and below reported separately.
- Friday→Monday excluded.
- σ-scaled bins.
- Per year.
- **Proxy swap, 2024-10-07 → 2026-09-25, EURUSD / GBPUSD / USDJPY only:**
  - futures VA from `*_fut_profile.csv`, mapped to spot with the causal basis (HYP-034 PASSED for these three);
  - the sign of θ16 must agree with the tick-volume version.
  - XAUUSD is excluded from the swap because the basis map FAILED in T1.
  - This is the only route by which GBPUSD can obtain a valid (futures-volume) OF-16 result, labelled 2-year-only.

## 7. Expected counts (for planning; not outcomes)

Weekday server days: ≈ 2,390 per FX symbol and ≈ 2,280 for XAUUSD over the full sample, before the thin-day and warm-up exclusions. The holdout has ≈ 450 per symbol. The outside-open share is unknown; it will be reported.
