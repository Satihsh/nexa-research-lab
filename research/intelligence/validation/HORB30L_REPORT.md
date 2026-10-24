# H-ORB30L-NQ report: 30-minute opening-range breakout, long only, on Nasdaq-100 futures

**Verdict: INCONCLUSIVE (§7).**
- **6 of 7 acceptance checks pass. Only DSR fails** (0.07 vs ≥ 0.95, with 116 trials counted on this NQ dataset).
- This is the **first rule in NEXA's research history to pass the mean, CI, timing-placebo, stability, cost and beta-control checks together.**
- It is **not** a research candidate under the pre-registered rules, and it is **not** deployable on money.
- The full period was opened once, on 2026-10-15. No re-run with altered parameters is allowed under H-ORB30L-NQ.

| Item | Value |
|---|---|
| Pre-registration | `PREREG_HORB30L_NQ.md` (75fd92dd…, unchanged) |
| Interpretations | `DEVIATIONS_HORB30L_HVAR.md` (I-1…I-12, D-1), before data |
| Code | `horb30l_nq.py` 7d4095bc; tests 13/13 synthetic. An independent re-computation of 60 random days matched (0 mismatches) |
| Data | Databento `NQ.v.0` ohlcv-1m + volume, 2023-02-18 → 2026-10-10 (sha 35d1c3f5…) |
| Days | 896 eligible → **460 trades**, 435 no breakout by 11:30, 1 missing |
| Rule | 09:30–09:59 range; first 5-min close above the high by 11:30; long at the next 1-min open; stop = range low; target 1R; exit at the 15:29 close |

## Primary result
| Level | Mean net R | 95 % CI | One-sided p | Win rate | Mean NQ points |
|---|---|---|---|---|---|
| S0 | +0.067 | [+0.012, +0.132] | 0.011 | 57.4 % | +5.95 |
| **S1 (decides)** | **+0.058** | **[+0.002, +0.123]** | **0.020** | 57.4 % | +4.95 |
| S2 | +0.049 | [−0.008, +0.113] | 0.042 | 56.7 % | +3.95 |

**Exits:** 196 time, 135 target, 129 stop. Median R = **118.75 points**.

## Acceptance (§7)
| Check | Result |
|---|---|
| 1. Mean > 0 and CI low > 0 | ✅ +0.058, CI low +0.002 (barely) |
| 2. Timing placebo p_tod ≤ 0.05 | ✅ 0.05: **none** of the 19 other anchors beat it. The best placebo is 04:00 at +0.056; most are negative |
| 3a. No year > 40 % | ✅ max 2023 = 37 % |
| 3b. ≥ 60 % of years positive | ✅ 4 of 4 (2023 +9.8 R, 2024 +4.8, 2025 +6.9, 2026 +5.1) |
| 4. DSR ≥ 0.95 (116 trials) | ❌ **0.07** |
| 5. Median R ≥ 20 points | ✅ 118.75 |
| 6. Beats the beta control | ✅ N2 (same bracket at the 10:00 open, no breakout) = **−0.058 R**; difference **+0.116 R** |

## Secondaries, nulls, robustness (reported only)
- **2R target:** +0.032 R, not significant. 1R was the pre-declared primary.
- **N3 buy-and-hold** 10:00 → 15:30: +2.4 points / day.
- **Robustness** (positive in 4 of 5 variants):

| Variant | Mean R | 95 % CI |
|---|---|---|
| No 11:30 deadline | +0.053 | [+0.003, +0.110] |
| Breakout on 1-min close | +0.064 | [+0.003, +0.133] |
| Excluding FOMC / CPI / NFP | +0.078 | [+0.022, +0.135] |
| Exit at 15:59 | +0.040 | [−0.020, +0.112] |
| Short mirror | +0.017 | [−0.049, +0.095] |

## What it means in money (descriptive; 1 MNQ, S1 costs)
- **Activity:** about 128 trades a year (≈ 10–11 a month). **57 % of trade days won.** **64 % of months positive** (29 of 45). The longest losing streak was 5 trades.
- **Average:** **≈ +$10 per trade ≈ +$100 per month per MNQ contract** (median month +$124). Best month +$1,596; worst month **−$2,444**.
- **Risk:** the median 30-min range is ~119 points, so **1 MNQ risks ≈ $238 per trade** (98 % of trades risk > $100). The minimum sensible account at ~1 % risk is ≈ $24,000.

## Reading
- A real-looking but **small** edge: +0.06 R per trade after conservative costs, positive every year, better than every other time of day, and better than simply buying at 10:00.
- **DSR fails** because many rules (116) have now been tried on these same 3.6 years. The chance that the best of them looks this good by luck alone is high.
- **The honest next step is new data the rule has never seen:**
  - (a) older NQ history (e.g. 2016–2022), one run with the frozen rule; and/or
  - (b) a prospective forward test on demo, ≥ 100 trades (≈ 9–10 months at this signal rate).
- Only a pass there would make it a candidate for an ATAS alert and a prop evaluation.
