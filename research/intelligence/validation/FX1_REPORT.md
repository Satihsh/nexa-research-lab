# FX1 results: daily FX fix reversals (Krohn, Mueller & Whelan 2024) on Pepperstone EUR, GBP, JPY (2026-10-11)

**Inputs, all frozen:**
- **Pre-registration:** `PREREG_FX1_FIX_REVERSALS.md` (sha 18207319…).
- **Code, tests 7/7, calendars and deviations D1–D16:** hashed before discovery (`PREREG_HASHES.txt`, 11:06 UTC). The shared modules `of_common.py` and `im1_intraday_momentum.py` matched their earlier hashes.

**Execution:**
- Splits were opened once each: discovery → validation → holdout.
- **Raw output:** `fx1_results_disc.json`, `fx1_results_val.json`, `fx1_results.json`.

**Rule:**
- Every eligible day, three windows anchored on the fixes: W1 Tokyo fix → 08:00 Frankfurt; W2 08:00 → ECB fix 14:15; W3 London 16:00 → 16:55 NY.
- Each trade takes the paper's direction for that window and currency.
- **Data:** EURUSD, GBPUSD, USDJPY, 2017-07 → 2026-09-25; 20,424 trades.

## Verdict: **REJECTED** (net). **The gross effect is confirmed: 9/9 signs match the paper, at about ¼ of its size.** Same pattern as C1 and IM1

| Pooled P (9 cells, equal weight per trade) | Discovery | Validation | Holdout | **Pooled** |
|---|---|---|---|---|
| Trades | 11,940 | 4,548 | 3,936 | 20,424 |
| **Gross** | +0.84 [+0.30, +1.39] | — | — | **+0.70 bp** [+0.33, +1.12] |
| Net S0 | −0.01 | −0.14 | −0.49 | **−0.13** [−0.50, +0.28] |
| **Net S1 (decides)** | −0.51 [−1.05, +0.04] | −0.64 | −0.99 | **−0.63** [−1.00, −0.22] |
| Net S2 | −1.01 | −1.14 | −1.49 | −1.13 |
| **Post-paper 2020-01 → 2026-09 (S1)** | | | | **−0.60** [−1.06, −0.15] |

**Acceptance:** 6 of 8 criteria failed; criteria 4 and 8 passed.

| # | Criterion | Result |
|---|---|---|
| 1 | Discovery | ✗ (p 0.96) |
| 2 | Validation / holdout | ✗ |
| 3 | Pooled CI | ✗ |
| 4 | **Placebo** (p_tod 0.024: the real windows beat all 41 shifted windows) | **✓** |
| 5 | Post-paper persistence | ✗ |
| 6 | Stability (2 of 10 years positive; pooled total negative) | ✗ |
| 7 | DSR ≈ 0 | ✗ |
| 8 | Stop / cost ≥ 5 (mechanical, D9) | ✓ |

**REJECTED** because the pooled S0 net is −0.13 ≤ 0.

## N2: gross replication against the paper's Table I

Unconditional window return, bp per day, + = foreign currency up vs USD. No stop, no costs. Bracketed values are the day-block 95 % CI.

| Window | EUR (paper → ours) | GBP | JPY |
|---|---|---|---|
| W1 post-Tokyo | +2.34 → **+0.48** [−0.07, +1.05] | +1.27 → **+0.42** [−0.15, +1.01] | +3.15 → **+0.72** [−0.17, +1.59] |
| W2 pre-ECB | −3.52 → **−1.28** [−2.24, −0.28] | −2.29 → **−0.82** [−1.93, +0.44] | −1.03 → **−0.73** [−1.66, +0.28] |
| W3 post-London | +2.73 → **+0.15** [−0.67, +0.93] | +2.65 → **+0.42** [−0.46, +1.32] | −1.16 → **−1.74** [−2.48, −0.97] |

**Reading:**
- **All 9 signs match the paper.** The W-shape around the fixes is present in 2017–2026 Pepperstone data.
- The size has shrunk to about 15–40 % of the 1999–2019 averages, except W3 USDJPY, which is larger than the paper.
- Only two cells are individually clear: W2 EUR and W3 JPY.
- This is consistent with decay after the 2015 WMR reform and the paper's publicity, but this test cannot separate those causes.

## Where the money goes (S1 net vs gross, bp per trade)

| Cell | Gross | Net S1 | | Cell | Gross | Net S1 | | Cell | Gross | Net S1 |
|---|---|---|---|---|---|---|---|---|---|---|
| W1 EUR | +0.40 | −0.90 | | W2 EUR | +1.17 | −0.13 | | W3 EUR | −0.00 | −1.30 |
| W1 GBP | +0.39 | −0.94 | | W2 GBP | +0.81 | −0.51 | | W3 GBP | +0.31 | −1.02 |
| W1 JPY | +0.62 | −0.76 | | W2 JPY | +0.69 | −0.68 | | **W3 JPY** | **+1.90** | **+0.53** [−0.19, +1.25] |

**Reading:**
- Gross is positive in 8 of 9 cells, averaging +0.70 bp. The S1 round trip is ≈ 1.3 bp (commission ≈ 0.7 + spread ≈ 0.2–0.4 + stress 0.5).
- **Only W3 USDJPY is net-positive.** It is one of 9 cells, the uncorrected p is 0.09, BH-adjusted secondaries are all 1.0, and its splits are mixed. It is **not** evidence of a tradable edge, and adopting it now would be post-hoc cell selection.
- By pair (net S1): EUR −0.78, GBP −0.82, JPY −0.29.
- By window (net S1): W1 −0.86, W2 −0.44, W3 −0.60.

**Placebo detail:**
- The real windows (−0.63) beat every shifted window. The best shifted window was δ = −150 min at −0.69.
- So the fix timing is genuinely special, but the timing advantage is smaller than the cost.

## Robustness (S1 net, reported only)

- **All variants are negative:**
  - paper's fixed-ET boundaries −0.85;
  - spread floor 0.1 / 0.3 pip −0.58 / −0.69;
  - stop 3σ / 6σ −0.64 / −0.62;
  - only W2 + W3 (no overnight W1) −0.52;
  - equal weight per day −0.61.
- **"W3 to 17:00 NY" is not computable.** The Pepperstone feed has no 16:59 NY bar (daily break) on 2,331 of 2,395 days. The variant ran with ~18 W3 trades and is uninformative (−0.64, driven by W1/W2).
- **Per year, S1 net:**
  - positive: 2017 (partial, from Oct) +0.90, 2020 +0.17;
  - negative: 2018 −1.00, 2019 −0.87, 2021 −1.06, 2022 −0.15, 2023 −0.64, 2024 −0.64, 2025 −0.68, 2026 −1.40.

## Conclusion (evidence class: NEXA, pre-registered)

1. **The fix-reversal W-shape survives in 2017–2026 FX** (9/9 signs; gross +0.70 bp per trade, CI > 0; timing beats the placebos). This is a **second successful gross replication** of a peer-reviewed intraday FX effect on NEXA's feed, after IM1.
2. **It has decayed to roughly a quarter of the paper's size and is not tradable at NEXA's cost.** It is net-negative at S1 in every split, in the post-paper period, and in 8 of 10 years. Even S0 (no stress) is −0.13 pooled.
3. **Four pre-registered tests now show the same pattern:** C1 Tokyo fix, IM1 intraday momentum, FX1 fix reversals and OFC1. Published intraday FX effects are real but sized at 0.3–2 bp. At commission + spread ≈ 1 bp per round trip with market orders, they do not clear costs.
   - **The binding constraint for NEXA in FX is execution cost, not signal discovery.**
4. **No re-run under FX1** with altered windows, signs or cells (including "W3 USDJPY only").
   - Any follow-up must be a **new pre-registered hypothesis tested on unseen data**, e.g. prospective 2026-10 onward, or a cost-reduction study (passive / limit entries at the window boundaries).
