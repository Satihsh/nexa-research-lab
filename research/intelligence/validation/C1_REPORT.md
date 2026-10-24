# C1 Tokyo-fix (gotobi) USDJPY: results

**Run:** 2026-10-11 (user approval: "Approved, pre-register and run C1").

**Pre-registration:**
- `PREREG_C1_TOKYO_FIX.md` (sha `1a740098…`) and the frozen `C1_JP_HOLIDAYS.json` (`18ad62c2…`), both hashed 2026-10-11T00:30:25Z.
- Code `c1_tokyo_fix.py` (`0a1e447e…`), hashed after 11/11 unit tests and before discovery.

**Opening order:** discovery → validation → holdout, each once. **No deviations.** Nothing was changed after outcomes were seen.

**Outputs:** `c1_results{_disc,_val,}.json` and `c1_run*.log`, hashed in `RESULTS_MANIFEST.txt`.

## 1. Verdict

**INCONCLUSIVE by the pre-registered rule.**
- Not REJECTED: the pooled net at base cost is > 0 and the splits never flip sign.
- Not SUPPORTED: criteria 1, 2, 3, 6 and 7 fail.

**Practical reading:** the published structural effect **is still present gross**, but it is **not a tradable edge at Pepperstone retail costs**. **No deployment, no follow-up under this ID.**

| Acceptance criterion | Result |
|---|---|
| 1. Discovery net (S1) > 0, p < 0.05 | ✗ (−0.78 bp, p 0.99) |
| 2. Validation and holdout net (S1) > 0 | ✗ (−0.17, −0.45 bp) |
| 3. Pooled CI lower bound > 0 (S1) | ✗ (−0.58 bp [−1.06, 0.00]) |
| 4. Beats time-of-day placebos | ✓ p_tod = 0.022 (the minimum possible); 0 of 44 placebos ≥ observed **in every split** |
| 5. GOTOBI − OTHER (gross) CI > 0 | ✓ +1.12 bp [+0.50, +1.76] |
| 6. Stability (no year > 50 %, ≥ 6/10 years positive) | ✗ 2/10 years positive (S1) |
| 7. DSR ≥ 0.95 (N = 49) | ✗ ≈ 0 |
| 8. Stop ≥ 5× cost | ✓ median 24× |

Samples: holdout 130 and pooled 676 GOTOBI events, both above the pre-registered minimums (100 / 500). MDE (80 % power): 0.92 / 1.48 / 1.60 bp (discovery / validation / holdout).

## 2. Primary claim A (long 00:50–00:55 UTC, short 00:55–01:00, GOTOBI days)

| Split | n | Gross bp | Net S0 | Net S1 (decides) | Net S2 |
|---|---|---|---|---|---|
| Discovery 2017-07 → 2022 | 394 | **+2.00** | +0.22 | −0.78 [−1.55, −0.16] | −1.78 |
| Validation 2023–24 | 152 | **+2.57** | +0.83 | −0.17 [−1.32, +0.97] | −1.17 |
| Holdout 2025 → 2026-09 | 130 | **+2.22** | +0.55 | −0.45 [−1.11, +1.00] | −1.45 |
| Pooled | 676 | **+2.17** | +0.42 [−0.06, +1.00] | −0.58 [−1.06, 0.00] | −1.58 |

**Cost anatomy:**
- 2 round trips × 0.70 bp commission = 1.40 bp;
- plus ≈ 2 × 0.15–0.2 bp spread;
- ≈ 1.75 bp of base cost against a ≈ 2.2 bp gross move.

The effect is real but almost entirely consumed by retail commission.

## 3. Secondary claims (S1; BH within the secondary family, all not significant)

| Claim | Pooled n | Gross | Net S1 [95 % CI] |
|---|---|---|---|
| B long leg only (1 round trip) | 676 | +0.70 | −0.67 [−1.04, −0.28] |
| C all business days (paper replication) | 2,190 | +1.40 | −1.35 [−1.78, −0.94] |
| D 30-min pre-fix long (1 round trip) | 676 | +1.53 | +0.16 [−0.47, +0.98] (discovery +0.56 → validation −0.21 → holdout −0.62) |
| A without the gotobi roll | 504 | +2.26 | −0.49 [−1.13, +0.15] |

## 4. What the data says about the mechanism (descriptive)
- **The paper replicates out of sample, gross.** All business days: +1.40 bp (paper 1999–2013 EBS: +1.8 bp). Gotobi days: +2.17 bp. Gotobi minus other: +1.12 bp. This is **9–10 years after the paper's sample, on a retail CFD feed**.
- **Most of the move is after the fix:** the long leg alone is +0.70 bp gross, so the 00:55 → 01:00 decline carries ≈ +1.47 bp of the +2.17 bp. *Exploratory observation only.* A short-only post-fix rule was not pre-registered, its ~1-round-trip cost (~0.85 bp) would leave roughly +0.6 bp (S0) / +0.1 bp (S1), and any test of it now needs a **new ID plus prospective data** (2026-10 →), because these data have been seen.
- **Month-end-only** (+0.61 bp S1, n = 109) and **stop multiples** (3σ/6σ, unchanged) are robustness rows only; they cannot be selected after the fact.

## 5. Implications for NEXA
1. **The cost floor is binding.** With USD 7/lot commission, any intraday edge has to be ≥ ~2 bp per round trip. C1, the best-documented flow anomaly in the ranking, does not clear it.
2. **The value is in confirming a mechanism, not in trading.** Scheduled flows still move USDJPY in 2017–2026, and the measurement pipeline (pre-registration → frozen code → placebo → splits) works and detects a +1 bp structural effect cleanly.
3. **Next candidate per the ranking:** C2 (daily FX/XAU time-series momentum), where cost per trade is small relative to the move. It first needs the swap-history decision (U-C2-1).
