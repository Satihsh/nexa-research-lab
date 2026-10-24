# H-VAR-NQ report: Dalton's Value-Area Rule on Nasdaq-100 futures

**Verdict: INCONCLUSIVE (§7). In practice there is no evidence of an edge.**
- The verdict is formally not "rejected" only because the S0 mean is positive.
- That positive mean comes entirely from 2026: 2023–2025 were all negative.
- The full period was opened once, on 2026-10-15.

| Item | Value |
|---|---|
| Pre-registration | `PREREG_HVAR_NQ.md` (687dbf38…) |
| Interpretations | `DEVIATIONS_HORB30L_HVAR.md` (I-1…I-5, I-13…I-21) |
| Code | `hvar_nq.py` b02512c9; tests 13/13 synthetic |
| Days | 896 eligible → **192 trades**; 299 opened inside value; 363 no acceptance by 11:30; 32 entry already past target; 7 below the cost floor; 3 missing |

## Primary result
| Level | Mean net R | 95 % CI | p | Win rate |
|---|---|---|---|---|
| S0 | +0.067 | [−0.104, +0.214] | 0.34 | 51.6 % |
| **S1** | **+0.053** | **[−0.118, +0.199]** | **0.40** | 51.6 % |
| S2 | +0.040 | [−0.132, +0.185] | 0.47 | 51.6 % |

Mean points per trade at S1: **−1.45**.

## Acceptance
Only the median-R check passes (96 points). Everything else fails:
- **CI:** spans zero.
- **Stale-value placebo p = 0.40:** yesterday's value area is no better than value areas 2–20 days old.
- **Years:** 1 of 4 positive (2023 −1.0 R, 2024 −2.0, 2025 −2.7, **2026 +16.0**).
- **Long/short:** longs −0.03.
- **DSR:** ≈ 0.

## Dalton's own claims, tested
| | Result |
|---|---|
| **Traverse rate** (trades that reached the opposite VA edge) | **39.6 %**: *below* Dalton's "flip of a coin" and far below the popular "80 % rule" |
| Dalton condition 1: open close to value | +0.075 R, not significant |
| Dalton condition 2: narrow value area | +0.021 R, not significant |
| Dalton condition 3: with the trend | +0.030 R, not significant |

## Robustness
| Variant | Mean R | 95 % CI |
|---|---|---|
| No deadline | +0.040 | [−0.091, +0.152] |
| One inside period | +0.055 | [−0.047, +0.160] |
| **Tighter stop** (¼ VA width) | **−0.181** | **[−0.335, −0.052]** |
| Target = previous POC | +0.006 | [−0.118, +0.150] |
| Excluding events | +0.058 | [−0.086, +0.142] |

**Money (descriptive):** ≈ −$4 per trade, −$15 per month per MNQ.

## Reading
- On NQ 2023–2026 the Value-Area Rule did **not** reliably carry price across yesterday's value. It got there 40 % of the time.
- None of Dalton's three conditions rescues it.
- The "80 % rule" claim fails clearly here.
- **Not deployable**, and there is no follow-up unless new evidence appears.
