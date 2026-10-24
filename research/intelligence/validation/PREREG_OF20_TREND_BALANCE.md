# PRE-REGISTRATION OF-20: is a trend day followed by a balance day more often than base rate?

**Inherits `PREREG_OF_COMMON.md`.** Written before any OF-20 outcome is computed. The SHA-256 is in `PREREG_HASHES.txt`.

## 1. Claims under test (a source contradiction, GAP-K04)

**The contradiction**
- **CL-009** (SRC-YT-013, 0:23–2:34; paraphrased): after a trend day, expect a balance day (the sequence trend → balance → trend). The source calls this a tendency, not an absolute.
- **CL-031** (SRC-YT-002, 26:26–26:39): an expansion followed by a rebalance day happens only ≈ 10 % of the time. Stated for SPX in a GEX context, with no data shown.

**Related registry items**
- **HYP-010** (S46): after a trend day, P(next session range-bound or reversing) ≈ 0.9.
- **HYP-013:** the trend-day base rate (S46 says 10–20 %, S42 says 20–30 %; CN4).

**Evidence quality**
- Both statistics are unverified.
- "Trend", "expansion", "balance" and "rebalance" are not operationally defined by either source. Any definition is NEXA's, so the result constrains *these definitions* on *these instruments*.
- The definitions are price-only. GBPUSD counts in the verdicts, except for BAL2, which uses a profile.

## 2. Session statistics (anchored session S_d, primary anchor; COMMON §C3)

- O, H, L, C of S_d. Range R = H − L. IB as in COMMON §C3, with IBH/IBL.
- **REX** = (R − IB)/IB (EQ-016).
  - Upward extension: H > IBH.
  - Downward extension: L < IBL.
- **CL** = (C − L)/R (EQ-017). Sessions with R = 0 are invalid.
- **ROT** (EQ-018):
  - 30-min periods j = 1… from the anchor. The last, partial period is kept if it has ≥ 15 bars.
  - For j ≥ 2: a_j = +1 if H_j > H_{j−1} and L_j ≥ L_{j−1}; a_j = −1 if L_j < L_{j−1} and H_j ≤ H_{j−1}; else a_j = 0.
  - ROT = the number of sign changes in the sequence of non-zero a_j.

## 3. Day types

**TD, trend day (primary conditioning event; EQ-016/017/018 codification)**
- **TD↑:** CL ≥ 0.90 **and** H > IBH **and** L = IBL (extension on the up side only) **and** REX ≥ 1.0 **and** ROT ≤ 2.
- **TD↓:** the mirror (CL ≤ 0.10, L < IBL, H = IBH, REX ≥ 1.0, ROT ≤ 2).
- **Origin of the thresholds:**
  - CL 0.9/0.1 from EQ-017;
  - ROT ≤ 2 from EQ-018 ("broken once or at most twice");
  - one-sided extension and REX ≥ 1.0 from the EQ-016 Steidlmayer typology (trend beyond "normal variation" ≈ 1).
- **TD-lite (counted sensitivity):** the CL and ROT conditions only.

**XD, expansion day (CL-031 analogue, secondary conditioning event)**
- R/σ̂_d ≥ the discovery 80th percentile of R/σ̂ for that symbol and anchor (frozen).
- NEXA's definition; the source gives none.

**BAL1, balance day (primary outcome)**
- ROT ≥ 3 **and** 0.25 ≤ CL ≤ 0.75: two-sided rotation, and a close in the middle half of the range.
- NEXA's definition. Thirds (1/3 ≤ CL ≤ 2/3) are a counted sensitivity.

**BAL2, "sideways or reversal" (secondary outcome; the registry's HYP-010 operationalisation)**
- C_{d+1} inside the VA of S_d (anchored-session tick-volume profile; COMMON §C6), **or** sign(C_{d+1} − O_{d+1}) = −(trend direction of d).
- Profile-based, so GBPUSD BAL2 is reported but excluded from counts.

**Trial grid:** {TD, TD-lite, XD} × {BAL1, BAL1-thirds, BAL2} × {primary, secondary anchor} × 4 symbols = 72 cells.
- **Primary cell:** (TD, BAL1, primary anchor).
- **Primary family:** 4 symbols.

## 4. Statistics

**Primary effect:** θ20 = P(BAL1_{d+1} | TD_d) − P(BAL1_{d+1} | not TD_d), over valid consecutive pairs (COMMON §C4). A risk difference. Fisher's exact p is reported beside the bootstrap.

**Reported for every cell**
- n(TD), and P(TD) = the HYP-013 base rate, compared with 10–20 % (S46) and 20–30 % (S42).
- P(BAL | TD), P(BAL | not TD), P(BAL).
- P(TD_{d+1} | TD_d) vs P(TD): persistence. This is the direct counterpart of CL-031's implied continuation.
- The full 3×3 transition matrix over {TREND (TD), BALANCE (BAL1), OTHER}.

**Null:** the unconditional base rate P(BAL1 | not TD) is built into θ20. A pair-order permutation (shuffling d+1 outcomes across days within split and symbol, 1,000 times) gives p_perm.

## 5. Decision rules

**CL-009 (trend → balance above base rate), per symbol:** the COMMON §C8 rule on θ20, with additional requirements (4):
- pooled p_perm < 0.10;
- pooled n(TD) ≥ 100.
- If n(TD) < 100, the symbol is **INSUFFICIENT-N**, not REJECTED.

**CL-009 overall:**
- **SUPPORTED** if ≥ 3 of 4 symbols are SUPPORTED.
- **REJECTED** if ≥ 3 of 4 are REJECTED.
- **INCONCLUSIVE** otherwise. INSUFFICIENT-N symbols count as neither.

**CL-031 (the ≈ 10 % figure; XAU/FX analogue), per symbol, pooled q = P(BAL1_{d+1} | XD_d), reported again with BAL2:**

| Result | Condition |
|---|---|
| **CONSISTENT** | The 95 % CI overlaps [0.05, 0.15] |
| **REFUTED for the analogue** | The CI lies wholly outside [0.05, 0.15] |

**HYP-010 (≈ 0.9 figure):** pooled P(BAL2_{d+1} | TD_d).
- **CONSISTENT** if the CI overlaps [0.85, 0.95].
- **REFUTED for the analogue** if the CI upper bound < 0.85.
- Also reported against P(BAL2 | not TD). A high rate that equals the base rate is not evidence for the claim.

**Resolution of the contradiction (stated in advance):**

| CL-009 verdict | CL-031 analogue | Reading |
|---|---|---|
| SUPPORTED | REFUTED (q above 0.15) | Axia's sequence holds for XAU/FX under these definitions; DeepCharts' 10 % does not transfer |
| REJECTED, with persistence P(TD\|TD) > P(TD) | CONSISTENT | DeepCharts' continuation reading holds; Axia's does not transfer |
| REJECTED, no persistence | Any | Neither: day types are roughly independent; neither claim adds information |
| INCONCLUSIVE / INSUFFICIENT-N | Any | Unresolved; stays as CONTRADICTED-BY-SOURCE in the KB |

## 6. Robustness (reported)

- Friday→Monday excluded.
- The A0 full-day session in place of the anchored session (IB = the first 60 min after 17:00 NY; reported only, with the caveat that it is illiquid).
- Per year.
- Up vs down trend days.
- Conditioning on the prior σ̂ tercile (discovery cut-points).
