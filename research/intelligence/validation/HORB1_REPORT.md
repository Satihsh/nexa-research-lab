# H-ORB-1 report: 5-minute opening-range breakout on Nasdaq-100 futures

**Verdict: INCONCLUSIVE** (§7, interpretation I-11). The holdout was opened once on 2026-10-13. No re-run with altered times, stops or targets is allowed under H-ORB-1.

| Item | Value |
|---|---|
| Pre-registration | `PREREG_HORB1_NAS100_ORB.md` (sha `af3b6169…`, unchanged) |
| Interpretations / deviations | `DEVIATIONS_HORB1.md` (I-1…I-15, D-1…D-6), all recorded before data |
| Code | `horb1_orb.py` 400602bc, converter b6888518, tests 18/18 |
| Data | Databento GLBX.MDP3 `NQ.v.0` ohlcv-1m, 2023-02-18 → 2026-10-10 (1,289,540 bars, 16 contracts, sha `18d54a1c…`), USD 4.7078 |
| Period | **H only** (post-publication holdout). P is INSUFFICIENT by design (D-2) |
| Costs | Spread floor 1.0 index point on every bar (D-3, ≈ 4× the real NQ spread); S1 adds +0.5 point per side |

## Primary result (H, 896 eligible days)

| Level | Trades | Mean net R | 95 % CI | One-sided p | Win rate | Mean NQ points / trade |
|---|---|---|---|---|---|---|
| S0 | 890 | +0.078 | [−0.043, +0.203] | 0.104 | 24.8 % | +1.49 |
| **S1 (decides)** | **881** | **+0.063** | **[−0.059, +0.189]** | **0.150** | 25.1 % | +0.59 |
| S2 | 848 | +0.017 | [−0.094, +0.150] | 0.397 | 25.5 % | −0.72 |

**Exits at S1:** 655 stop, 208 time, 18 target.

## Acceptance (§7)

| Check | Result |
|---|---|
| 1. P mean > 0, p < 0.05 | n/a (P INSUFFICIENT, D-2) |
| 2. H mean > 0 **and** CI low > 0 | ❌ (CI low −0.059) |
| 3. Timing placebo p_tod ≤ 0.05 | ❌ p_tod = 0.190 (3 of 20 placebo times ≥ observed: 03:30, 04:00, 04:30) |
| 4a. No year > 40 % of total R | ❌ 2025 = 65 % |
| 4b. ≥ 60 % of years positive | ✅ 3 of 4 (2023 +24.0 R, 2024 +13.3 R, 2025 +35.6 R, 2026 −17.9 R) |
| 4c. Long and short means ≥ 0 | ✅ long +0.014, short +0.114 |
| 5. DSR ≥ 0.95 (23 trials) | ❌ 0.009 |
| 6. Cost check (median R ≥ 10 × costs) | ✅ median R = 43.5 points |

## Nulls

- **N2 (opposite direction):** −0.161 R, CI [−0.290, −0.017]. Fading the first candle loses significantly, so the first candle's direction carries some information. The effect is not large enough to pass the primary test.
- **N3 (buy-and-hold 09:35 → 15:59):** +2.05 points / day (+1.8 bp).

## Robustness (§8, reported only; never selected)

| Variant | Mean R | 95 % CI |
|---|---|---|
| ATR stop, no target | +0.033 | [−0.167, +0.275] |
| Target 5R | +0.073 | [−0.052, +0.196] |
| No target (EoD exit) | +0.133 | [−0.005, +0.298] |
| Entry at 09:35 bar close | +0.058 | [−0.070, +0.195] |
| Spread floor 0.5 | +0.071 | [−0.051, +0.193] |
| Spread floor 2.0 | +0.012 | [−0.096, +0.132] |
| Excluding FOMC / CPI / NFP days | +0.047 | [−0.110, +0.217] |

The "no target" variant is the closest to significance. Picking it **after** seeing these numbers would be data-snooping, so it may only enter a **new** pre-registration tested on **new** (prospective) data.

## Sizing (report-only)

- Median stop distance: 43.5 NQ points.
- One MNQ ($2 / point) risks about $87, so 1 % risk per trade needs about **$8,700 per MNQ contract**.
- 9.5 % of trades have R ≤ 20 points.

## Reading

- The opening-range breakout on Nasdaq futures was **slightly positive after conservative costs** in the 3.6 years after publication: +0.06 R per trade at S1.
- But the result is **not statistically distinguishable from zero**:
  - p = 0.15;
  - the CI includes negative values;
  - it fails the timing placebo and DSR;
  - most of the gain came from 2025, and 2026 to date is negative.
- **It is not a demonstrated edge, and it is not deployable on real money.**
- It is also **not rejected**: the sign is positive at S0/S1, and fading the first candle is significantly negative.

**The honest next step** is prospective evidence:
- a fresh pre-registration, frozen before new data;
- forward-logged daily, on demo only;
- the rule fixed in advance (either the H-ORB-1 rule as is, or the no-target variant declared as the single primary);
- at least about 300 new trades (≈ 1.2 years) before any decision.
