# PRE-REGISTRATION OF-20b: trend day → balance day, with a session-length-normalised day-type rule

**Inherits `PREREG_OF_COMMON.md`** except where stated here. Written 2026-10-11, before any OF-20b quantity is computed. The SHA-256 is in `PREREG_HASHES.txt`.

**Approval:** user, 2026-10-11, "Approved, pre-register OF-20b".

**New ID, new trial.** OF-20 stays INCONCLUSIVE under its own definitions (`OF_RESULTS_REPORT.md` §4). OF-20b does **not** re-run OF-20 with tweaked parameters. It is a separately registered codification and is counted in the day-type family's multiple-testing budget (RESEARCH_GATE rule).

## 0. Why OF-20b exists (GAP-K08)

- OF-20 used EQ-018 on 30-min periods with ROT ≤ 2. That rule was codified for pit sessions of about 13 thirty-minute periods (S46).
- On NEXA's anchored sessions (≈ 28 periods for FX, ≈ 17 for gold), the median ROT is 8 and P(TD) ≈ 0.04–1.5 %. CL-009 therefore could not be evaluated: n(TD) = 33 / 2 / 2 / 0.
- **OF-20b's design principle:** keep the source rule *unchanged* and normalise *time*.
  - Every session is cut into the same number of periods (13) that the rule was written for.
  - The initial balance becomes the same *fraction* of the session (2 of 13 periods) as the 60-min IB was of a 6.5-h pit session.
- No threshold is re-chosen from NEXA data. Every numeric threshold below is taken from EQ-016/017/018, or from OF-20's pre-registered BAL1, unchanged.

## 1. Disclosure: what has already been seen on this data (not blind)

The OF-20 full run (2026-10-11) computed the following on the same sessions, anchors and splits (2017/18 → 2026-09-25):
- the 30-min ROT distribution (EURUSD discovery: 5th / 50th / 95th percentiles 5 / 8 / 12);
- the shares of the close-location and REX ≥ 1 conditions (60-min IB);
- base rates of the OF-20 BAL1 outcome (0.45–0.49);
- P(BAL1 next | XD) and P(BAL1 next | not XD) for top-quintile range days;
- OF-20 TD / TD-lite conditionals (XAU n = 33);
- the 3×3 transition matrix under the OF-20 definitions.

**Not computed by anyone:** any quantity under the OF-20b definitions. This includes TDb frequency, BAL1b frequency, ROT13 and the joint distribution of TDb_d with BAL1b_{d+1}.

**Consequence:** the outcome-adjacent information already seen is correlated with OF-20b's outcomes. A historical OF-20b result is therefore labelled **RETROSPECTIVE (semi-blind)**. It can reach at most G3. **G4 requires the prospective confirmation in §6.**

## 2. Claims under test (unchanged from OF-20)

- **CL-009** (SRC-YT-013, 0:23–2:34): after a trend day, expect a balance day.
- **CL-031** (SRC-YT-002, 26:26–26:39) predicts the opposite. Its ≈ 10 % figure was already refuted for the XAU/FX analogue in OF-20 and is **not** re-tested here.
- **HYP-010** (≈ 0.9 sideways or reversal after a trend day) and **HYP-013** (trend-day base rate: S46 10–20 %, S42 20–30 %) are reported under the new codification.

## 3. Definitions

**Session S_d:** [a_d, E_d) with the symbol's primary anchor (COMMON §C3). The secondary anchor is a counted trial. T_d = E_d − a_d in minutes.

**Normalised periods**
- Period index j = floor( (t − a_d) · 13 / T_d ) ∈ {0, …, 12}, for each bar with open time t.
- A period is **usable** if it has bars on ≥ 50 % of its minutes (the period length is T_d / 13, which may be fractional).
- The session is **valid** if ≥ 11 of the 13 periods are usable. H_j and L_j are taken over each usable period. Unusable periods are skipped (no a_j).

**Normalised initial balance IB_b:** periods 0 and 1 (the first 2/13 of the session).
- Valid if bars exist on ≥ 90 % of its minutes (mirrors 54/60).
- IBH_b and IBL_b are its high and low.

**Session statistics**
- O = open of the first bar in S_d. C = close of the last bar. H, L, R = H − L.
- **CL** = (C − L)/R (EQ-017).
- **REX_b** = (R − IB_b)/IB_b (EQ-016).
- **ROT13:** the EQ-018 rotation count over usable periods j = 1…12. For j ≥ 1:
  - a_j = +1 if H_j > H_{j−1} and L_j ≥ L_{j−1};
  - a_j = −1 if L_j < L_{j−1} and H_j ≤ H_{j−1};
  - else 0.
  - "Previous" means the previous usable period. ROT13 = the number of sign changes among the non-zero a_j.

**Day types**

| Label | Rule | Threshold origin |
|---|---|---|
| **TDb↑ (primary event)** | CL ≥ 0.90 **and** H > IBH_b **and** L = IBL_b **and** REX_b ≥ 1.0 **and** ROT13 ≤ 2 | EQ-017; EQ-016 one-sided extension, REX ≥ 1; EQ-018 "at most twice" |
| **TDb↓** | Mirror: CL ≤ 0.10, L < IBL_b, H = IBH_b, REX_b ≥ 1.0, ROT13 ≤ 2 | same |
| **BAL1b (primary outcome)** | ROT13 ≥ 3 **and** 0.25 ≤ CL ≤ 0.75 | OF-20 BAL1, unchanged except for the period grid |
| **BAL2b (secondary outcome)** | C_{d+1} inside the VA of S_d (COMMON §C6), **or** sign(C_{d+1} − O_{d+1}) = −dir_d. dir_d = the TDb direction on trend days, sign(C_d − O_d) otherwise (OF-20 implementation note (c), now pre-registered). GBPUSD is excluded from BAL2b counts (profile proxy rejected) | HYP-010 operationalisation |

**Variant A (counted secondary codification):** the same as above, except rotation is measured on 30-min periods (as in OF-20) with a threshold scaled to the number of possible sign changes.
- Let P30 be the number of usable 30-min periods. The OF-20 rule applies: the last partial period is kept if it has ≥ 15 bars.
- θ_A = floor( 2 · (P30 − 2) / 11 ).
  - In S46, a 13-period session has 11 possible sign changes and allows 2. The ratio 2/11 is carried over.
- **TDa** uses ROT30 ≤ θ_A in place of ROT13 ≤ 2. **BAL1a** uses ROT30 ≥ θ_A + 1.
- The IB is IB_b, as in the primary.

**Trial grid:** {primary codification (13 periods), variant A} × {primary, secondary anchor} × {BAL1b/BAL1a, BAL2b} × 4 symbols = 32 cells.
- **Primary cell:** (13-period, primary anchor, BAL1b).
- **Primary family:** 4 symbols.

## 4. Statistics

**Pairs:** (d, d+1) as in OF-20 (COMMON §C4). Both sessions must be valid under the codification being evaluated.

**Primary effect:** θ20b = P(BAL1b_{d+1} | TDb_d) − P(BAL1b_{d+1} | not TDb_d).
- 2,000-resample day-block bootstrap (COMMON §C8).
- Pair-order permutation within split and symbol (1,000 reps) → p_perm.
- Fisher's exact p reported.

**Reported for every cell**
- n(TDb); P(TDb) per split and pooled, against HYP-013 (10–20 % / 20–30 %).
- P(BAL | TDb), P(BAL | not TDb), P(BAL).
- Persistence: P(TDb_{d+1} | TDb_d) vs P(TDb).
- The 3×3 transition matrix {TREND, BALANCE, OTHER}.
- Up vs down trend days.
- Fri→Mon excluded.
- Per year with year shares.
- The prior σ̂ tercile (discovery cut-points).

**Diagnostics (reported before any outcome is tabulated, in the run log)**
- The ROT13 distribution.
- The share of each TDb component condition.
- Session validity counts.
- These are definitional checks. If they reveal a coding error, the fix is a disclosed deviation; thresholds are never changed.

## 5. Decision rules (historical data; RETROSPECTIVE label)

**Per symbol:** the COMMON §C8 rule on θ20b, with additional requirements (4):
- pooled p_perm < 0.10;
- pooled n(TDb) ≥ 100. Otherwise the symbol is **INSUFFICIENT-N**.

**CL-009 (retrospective, OF-20b):**
- **SUPPORTED-RETRO** if ≥ 3 of 4 symbols are SUPPORTED.
- **REJECTED** if ≥ 3 of 4 are REJECTED.
- **INCONCLUSIVE** otherwise. INSUFFICIENT-N counts as neither.

**HYP-013:** pooled P(TDb) with a 95 % CI, per symbol.
- **CONSISTENT with S46** if the CI overlaps [0.10, 0.20].
- **CONSISTENT with S42** if it overlaps [0.20, 0.30].
- Otherwise outside both.

**HYP-010:** pooled P(BAL2b | TDb) against [0.85, 0.95].
- **UNDETERMINED** if n(TDb) < 100.
- Always reported beside P(BAL2b | not TDb).

**Resolution of CL-009 vs CL-031:**

| CL-009 (OF-20b) | Persistence P(TDb\|TDb) > P(TDb) (pooled CI > 0 on ≥ 3 symbols) | Reading |
|---|---|---|
| SUPPORTED-RETRO | No | Axia's sequence holds retrospectively for XAU/FX (DeepCharts' ≈ 10 % already refuted in OF-20) — **pending §6** |
| REJECTED | Yes | Continuation (DeepCharts-style) reading holds; Axia's does not transfer |
| REJECTED | No | Day types ≈ independent; neither claim adds information |
| INCONCLUSIVE / INSUFFICIENT-N, or SUPPORTED-RETRO with persistence | — | Unresolved; GAP-K04 stays open |

## 6. Prospective confirmation (required for G4)

**Data:** sessions from 2026-10-12 onward, under exactly these definitions and this code. **Nothing is collected now** (the standing "stop collecting data" instruction applies).
- Evaluation happens only when you approve acquiring the new M1 data.
- Any data dated 2027 additionally needs your explicit approval (it is reserved as V2 OOS).

**Trigger:** first evaluation once ≥ 100 pooled TDb pairs (4 symbols) have accrued, or at a date you set, whichever comes first.

**Rule:** pooled θ20b > 0 with one-sided day-block bootstrap p < 0.10 **and** ≥ 3 of 4 symbols with a positive point estimate ⇒ **CONFIRMED (G4)**.
- **NOT CONFIRMED** if the pooled point estimate ≤ 0.
- **INCONCLUSIVE** otherwise.
- Opened once. If inconclusive, the next look requires a new trigger set in advance (n ≥ 200), and the number of looks is disclosed.

## 7. Implementation (before any run)

- A new script, `of20b.py`, reuses `of_common.py` and the OF-20 pair, bootstrap and permutation machinery unchanged.
- **New synthetic unit tests**, added to `test_of_common.py`:
  1. the 13-period partition of an 8 h 40 m and a 14 h session;
  2. the usable-period and valid-session rules;
  3. IB_b bounds;
  4. ROT13 on a constructed path;
  5. θ_A for P30 = 13 (→ 2), 17 (→ 2), 28 (→ 4).
- The code is hashed into `PREREG_HASHES.txt` before discovery is opened. Discovery → validation → holdout are each opened once (`--stage disc|val|full`), as for OF-16/19/20.
- **Running OF-20b requires a separate go-ahead.** This document only pre-registers it.
