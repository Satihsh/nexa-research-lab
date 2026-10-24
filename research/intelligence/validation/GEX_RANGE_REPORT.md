# H-GEX-RANGE report: does SPX dealer net gamma improve the NQ / ES expected-range forecast?

**Verdict: REJECTED** (the binding instrument NQ: out-of-sample error reduction ≤ 0). ES: INCONCLUSIVE.
- Pre-registration `PREREG_GEX_RANGE.md` (8f7ccf39); probe and gate notes in `DEVIATIONS_GEX_RANGE.md`.
- Code frozen before any run: `qc_gex/main.py` 9c5be569, `gex_stats.py` a1db18f0, `test_gex.py` 43ade23e (10/10 tests incl. a planted effect).
- Date: 2026-10-24.

## What was tested
- **Feature:** naive dealer net GEX from the prior-close SPX + SPXW chains, as a percentile within its trailing 252 days (GEXrank). Chains come from QuantConnect's free index option universe, with open interest and QC gamma.
- **Target:** ln(RTH range) of NQ and ES.
- **Baseline:** the v6 panel's mean range of the previous 10 sessions.
- **Models:**

  | Model | Definition |
  |---|---|
  | B1 | a + b·ln(base) |
  | M1 | B1 + c·GEXrank |

- **Walk-forward:** refitted yearly; out-of-sample years **2015–2025** (2,740 days per instrument).
- **Timing verified:** the chain read at 09:25 ET carries the prior trading day's close (probe, 2015-01-05).

## Results
| | **NQ (binding)** | ES |
|---|---|---|
| OOS loss B1 → M1 | 0.1906 → 0.1907 | 0.2093 → 0.2057 |
| **Error reduction** | **−0.06 %** | +1.73 % |
| Diebold–Mariano p (one-sided) | 0.52 | 0.13 |
| Years better (of 11) | 6 | 7 |
| Pooled coefficient on GEXrank | −0.27 (right sign) | −0.40 (right sign) |
| Bar for VALIDATED | ≥ 2 %, p ≤ 0.025, ≥ 7/11, c < 0 | same |
| **Verdict** | **REJECTED** | **INCONCLUSIVE** |

- **NQ per year (reduction):**

  | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | +8.3 % | +3.0 % | −0.3 % | +0.4 % | −3.5 % | −10.8 % | −1.0 % | +0.7 % | −8.2 % | +4.1 % | +4.9 % |

  It helps in calm years and hurts in the 2020 and 2023 regime changes.
- **The panel's raw 10-day mean is already as good as the fitted baseline** (B1 vs raw B0: −0.4 % NQ, +0.4 % ES).
- **Descriptive (in-sample, no verdict effect) — actual range ÷ baseline forecast by gamma quintile:**

  | Gamma quintile | NQ | ES |
  |---|---|---|
  | Q1 (lowest / most negative) | 1.22 (217 pts mean range) | 1.31 |
  | Q2 | 1.14 | 1.17 |
  | Q3 | 1.09 | 1.10 |
  | Q4 | 1.11 | 1.07 |
  | Q5 (highest) | 0.98 (104 pts) | 0.96 |

  The relationship exists and has the theory's sign: high-gamma days move less than the 10-day average says, low-gamma days more. But most of it is already in recent ranges, and the extra part does not hold up out of sample for NQ.
- **Secondary variants (no verdict effect):**
  - NDX gamma for NQ −2.6 %;
  - absolute gamma −1.4 % (NQ) / −1.1 % (ES);
  - gamma-sign dummy −0.4 % / +1.1 %;
  - **with VIX in both models:** NQ +0.8 % (p 0.22); **ES +3.0 % (p 0.003, 7/11 years)**. This is the single strongest number in the run, but it is a pre-declared *secondary* on the non-binding instrument. Under the rules it is a lead for a new pre-registration at most, not a result.
- **Data notes:**
  - 2012–2014 and some 2018/2022 days have chains without an open-interest column (mostly SPXW weeklies early on). Those days use standard SPX contracts only, or are excluded when nothing is left.
  - The first trading day of each year has no VIX (secondary only).
  - 3,608 days were logged; 3,200 NQ and 3,239 ES rows usable.

## Use (pre-registered)
- **The v6 panel keeps the plain 10-day mean.** Gamma does not enter the expected-range line.
- **Claims CL-032 / CL-038** ("positive gamma = calmer, negative = bigger moves") are now **tested**: real as a pattern, but **no added forecasting value for NQ** beyond recent ranges.
- **Ledger:** 2 trials (NQ, ES) → ≈ 188.
- **H-GEX-IM** (last-30-minute momentum on negative-gamma days) remains a separate, untested idea; its prior is lower after this result.

## Files
- `qc_gex/runlogs/gex_2012.txt … gex_2025.txt`: 14 logs, each hash-checked against the page.
- `qc_gex/gex_results.json`: output of `gex_stats.py`.
- QuantConnect project 38340704: one backtest per year, plus probe 6dd7d567. The YEAR-line hash was checked in the editor before every run.
