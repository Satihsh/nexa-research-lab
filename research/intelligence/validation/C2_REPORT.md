# C2 daily FX/XAU time-series momentum: results

**Run:** 2026-10-11 (user approval: "Approved, implement and run C2").

**Pre-registration:** `PREREG_C2_TSMOM.md` (sha `acfcfe13…`, hashed 2026-10-11T00:45:27Z). Swaps use option (a).

**Code:** `c2_tsmom.py` (`aad16587…`), hashed with `contracts.json` after 12/12 unit tests, before discovery.

**Opening order:** discovery → validation → holdout, each once. **No deviations.**

**Outputs:** `c2_results{_disc,_val,}.json` and `c2_run*.log` (hashed in `RESULTS_MANIFEST.txt`).

## 1. Verdict

**REJECTED by the pre-registered rule:** the pooled net (S0) monthly mean is ≤ 0.

| Acceptance criterion | Result |
|---|---|
| 1. Discovery net (S1) > 0, p < 0.05 | ✗ −0.26 %/mo |
| 2. Validation and holdout > 0 | ✗ −0.16 %, −0.09 %/mo |
| 3. Pooled CI lower bound > 0 | ✗ −0.19 %/mo [−0.34, −0.02] |
| 4. p_N2 < 0.05 and beats long-only | ✓ (p_N2 = 0.047; the long-only benchmark is worse, −0.23 %/mo). Both carry the same swap drag |
| 5. Ex-swap > 0 **and** swap ×2 > 0 | ✗ (ex-swap +0.12 % ✓; swap ×2 −0.50 % ✗) |
| 6. Breadth (≥ 5/8 instruments positive, none > 50 %) | ✗ (3/8 positive; XAU dominates) |
| 7. Stability (no year > 50 %; holdout > 0 at 2× cost) | ✗ |
| 8. DSR ≥ 0.95 (N = 16) | ✗ ≈ 0.001 |

**All 16 grid cells are negative pooled.** Lookbacks 21/63/252/COMBO × monthly/weekly × U8/NEXA4 range from −0.19 % to −0.46 %/mo; BH = 1.0 for every secondary cell.

## 2. Primary (12-month, monthly, U8, vol-scaled 10 %/instrument, S1)

| Split | Months | Net (option-a swaps) | Sharpe | **Ex-swap** | Ex-swap Sharpe |
|---|---|---|---|---|---|
| Discovery 2001-05 → 2012 | 140 | −0.26 %/mo | −0.52 | **+0.20 %** | +0.39 |
| Validation 2013–19 | 84 | −0.16 % | −0.36 | **+0.02 %** | +0.04 |
| Holdout 2020 → 2026-09 | 81 | −0.09 % | −0.18 | **+0.10 %** | +0.20 |
| Pooled | 305 | −0.19 % [−0.34, −0.02] | −0.39 | **+0.12 % [−0.03, +0.31]** | +0.25 |

Other descriptors: annualised −2.2 %; max drawdown −48 %; turnover 4.3×/yr per instrument; 20 catastrophe stops in 25 years.

## 3. The swap convention dominates the formal result (a methodological finding)

**Mechanism.** Option (a) applies the 2026-09 `contracts.json` swaps (**fixed price points per lot per night**, charges only) to every year.
- For XAUUSD the long charge of 86.55 points is ≈ 0.02 %/night at today's ≈ $4,300 but **≈ 0.32 %/night at 2001's ≈ $270**, about 16× larger in relative terms.
- FX pairs carry today's rate differentials into the 2009–2021 near-zero-rate era.

**Size of the effect.**
- Swaps cost the primary ≈ 0.31 %/mo pooled (net −0.19 % vs ex-swap +0.12 %).
- XAU is 71 % of the (negative) pooled P&L.
- The long-only benchmark is negative for the same reason.

**What this does and does not change:**
- The verdict stands as registered.
- The convention was pre-registered and disclosed as conservative (U1). Its magnitude on 25-year history was underestimated at design time.
- **Lesson:** a points-denominated swap snapshot must never be applied across decades of changing price levels.
  - Any future multi-year test must convert swaps to a % of price at the snapshot date, or use historical rate differentials (option (b)).
  - Recorded in the KB as a method gap.

## 4. Does the strategy work even without swap costs? No reliable evidence

Ex-swap ignores real financing charges, so it is optimistic:
- **Pooled:** +0.12 %/mo, Sharpe 0.25, CI [−0.03, +0.31] %/mo. **Not significant.**
- **Splits:** discovery +0.20 → validation +0.02 → holdout +0.10.
- **Symmetric snapshot swaps** (credits allowed): −0.14 %/mo pooled.

This is consistent with weak post-2000 currency trend-following on a small universe. The literature's stronger results rely on broad multi-asset cross-sections and futures excess returns (carry included), which are not available here.

## 5. Implications for NEXA

1. **C2 is closed under this ID.** Re-testing a %-swap or ex-swap variant on the same data would be a new ID, and these data have now been seen. A valid follow-up needs either:
   - rate-differential history (option (b), new data, approval), or
   - prospective data (2026-10 →) at monthly frequency, which takes years.
2. **The cost lesson from C1 generalises to financing.** For any holding period over a day, the swap/carry layer is first-order; it is not a detail.
3. **Ranking update:** C1 and C2 are both tested without a tradable edge. The remaining ranked candidates have lower evidence scores:
   - C3, London fix reversal: hurt by its 2015 window reform; needs equity data for the month-end signal;
   - C4, LBMA gold auction: literature unverified.
