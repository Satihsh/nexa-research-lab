# H-IVB1-NQ report: Fabio Valentini's IVB Model 1 on Nasdaq-100 futures

**Verdict: INCONCLUSIVE** (§7). In practice there is **no detectable edge** after costs.
- The verdict is formally "inconclusive" rather than "rejected" only because the S0 mean is a hair above zero (+0.031 R).
- The full period was opened once, on 2026-10-14.
- No re-run with altered parameters is allowed under H-IVB1-NQ.

| Item | Value |
|---|---|
| Pre-registration | `PREREG_HIVB1_NQ.md` (sha `3ef68268…`, unchanged) |
| Interpretations / deviations | `DEVIATIONS_HIVB1_HIM.md` (I-1…I-14, I-21, I-22, D-1), all recorded before data |
| Code | `hivb1_nq.py` 10548c1a; tests `test_hivb1_him.py` 97909cd0 (16/16, synthetic only) |
| Data | Databento GLBX.MDP3 `NQ.v.0` ohlcv-1m with volume, 2023-02-18 → 2026-10-10 (sha `35d1c3f5…`, from the same frozen DBN as H-ORB-1) |
| Days | 896 eligible (2023-02-21 → 2026-10-08) → 643 trades, 234 no fill, 18 no breakout, 1 missing, 0 below the cost floor |
| Costs | S0 / S1 / S2 = 1 / 2 / 3 NQ points per round trip (S1 ≈ 3–4× a real round trip) |

## Primary result

| Level | Trades | Mean net R | 95 % CI | One-sided p | Win rate | Mean NQ points / trade |
|---|---|---|---|---|---|---|
| S0 | 643 | +0.031 | [−0.060, +0.138] | 0.23 | 43.7 % | +2.94 |
| **S1 (decides)** | **643** | **+0.010** | **[−0.080, +0.117]** | **0.36** | 43.5 % | +1.94 |
| S2 | 643 | −0.011 | [−0.102, +0.097] | 0.51 | 43.2 % | +0.94 |

**Exits at S1:** 193 invalidation (5-min close beyond the far VA edge), 174 target (2R), 168 time (15:59), 108 hard stop.

## Acceptance (§7)

| Check | Result |
|---|---|
| 1. Mean S1 R > 0 **and** CI low > 0 | ❌ +0.010, CI low −0.080 |
| 2. Timing placebo p_tod ≤ 0.05 | ❌ p_tod = 0.10 (1 of 19 anchors ≥ observed: 04:00 +0.089 R) |
| 3a. No year > 40 % of total R | ❌ total S1 R = +6.5 R; 2025 alone = +12.1 R (186 %) |
| 3b. ≥ 60 % of years positive | ❌ 1 of 4 (2023 −3.7 R, 2024 −1.0 R, 2025 +12.1 R, 2026 −0.9 R) |
| 3c. Long and short each ≥ 0 | ❌ long +0.086 (344), short −0.077 (299) |
| 4. DSR ≥ 0.95 (69 trials) | ❌ 0.0003 |
| 5. Median R ≥ 20 points | ✅ median R = 56.75 points |

**Secondaries** (BH q = 0.10): none significant. Long has p 0.079 (p_BH 0.27). 2025 has p 0.090 (p_BH 0.27).

## Nulls

- **N1 timing placebo:** 18 of 19 other anchors are negative, mostly −0.10 to −0.25 R. The 09:30 range is clearly the *least bad* time to run this model, but its own result is still ≈ 0.
- **N2 fade (opposite direction, same level and R):** −0.032 R, CI [−0.137, +0.063]. Fading is no better.
- **N3:** H-ORB-1 on the same days was +0.063 R (INCONCLUSIVE, `HORB1_REPORT.md`).

## Robustness (§8, reported only; never selected)

| Variant | Trades | Mean R | 95 % CI |
|---|---|---|---|
| 15-min range | 689 | +0.026 | [−0.061, +0.120] |
| Target 2.5R | 643 | +0.036 | [−0.069, +0.172] |
| Entry at the POC | 453 | +0.009 | [−0.081, +0.159] |
| Invalidation on a 1-min close | 643 | +0.002 | [−0.087, +0.109] |
| No hard stop | 643 | +0.032 | [−0.059, +0.141] |
| Re-entries up to 3 | 685 | +0.022 | [−0.070, +0.132] |
| Excluding FOMC / CPI / NFP days | 489 | +0.007 | [−0.092, +0.114] |

Every variant sits between 0 and +0.04 R with CIs spanning zero. **No variation rescues it**, and none may be selected after the fact.

## Sizing (report-only)

- Median R = 56.75 NQ points. One MNQ ($2 / point) risks about $114.
- 1 % risk per trade would need about **$11,350 per MNQ contract**.

## Reading

- The model was reproduced mechanically from the source (SRC-YT-031):
  - a 30-min NY-open range and a fixed volume profile with a 70 % value area;
  - the first 5-min close outside the range;
  - a retrace limit at the near VA edge;
  - invalidation on a 5-min close beyond the far edge;
  - a 2R target.
- On 3.6 years of CME NQ it **made essentially nothing after costs**: +1.9 points per trade at S1 (≈ $3.90 per MNQ trade).
- It was positive in only one of four years (2025), and shorts lost.
- The discretionary parts of his method could not be coded and were not tested:
  - reading order-flow aggression at the level;
  - TP1 at the previous balance;
  - "break and reload".
- **What this does show:** the mechanical skeleton that can be coded and alerted is **not an edge on its own**.
- **Not deployable.** It does not justify an ATAS alert.
