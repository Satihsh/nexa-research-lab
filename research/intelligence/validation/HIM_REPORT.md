# H-IM-NQ report: market intraday momentum on Nasdaq-100 futures

**Verdict: REJECTED** (§7: the S0 mean ≤ 0; in fact even the gross mean is significantly negative).
- The full period was opened once, on 2026-10-14.
- No re-run with altered windows is allowed under H-IM-NQ.

| Item | Value |
|---|---|
| Pre-registration | `PREREG_HIM_NQ.md` (sha `1113e2ee…`, unchanged) |
| Interpretations / deviations | `DEVIATIONS_HIVB1_HIM.md` (I-15…I-22, D-1), recorded before data |
| Code | `him_nq.py` 2b2c43f4; tests `test_hivb1_him.py` 97909cd0 (16/16, synthetic only) |
| Data | Databento `NQ.v.0` ohlcv-1m 2023-02-18 → 2026-10-10 (canonical CSV, sha `18d54a1c…`) |
| Days | 854 day-pairs with an eligible previous weekday (2023-02-22 → 2026-10-08) → 852 trades, 2 missing |

## Primary result (Baltussen ROD signal → trade 15:30 open → 15:59 close)

| Level | Trades | Mean net bp | 95 % CI (bp) | One-sided p | Hit rate | Mean net points | Mean gross points |
|---|---|---|---|---|---|---|---|
| S0 | 852 | −2.57 | [−4.06, −0.92] | 1.00 | 46.1 % | −4.96 | **−3.96** |
| **S1 (decides)** | **852** | **−3.08** | **[−4.58, −1.43]** | **1.00** | 44.7 % | −5.96 | −3.96 |
| S2 | 852 | −3.58 | [−5.09, −1.92] | 1.00 | 43.2 % | −6.96 | −3.96 |

## Acceptance (§7)

All checks fail:
- mean −3.08 bp;
- p_tod 1.00;
- every year negative (2023 −604 bp, 2024 −786 bp, 2025 −1,043 bp, 2026 −188 bp);
- long −2.78 bp and short −3.43 bp;
- DSR ≈ 0;
- gross −3.96 points vs the required ≥ +4.0.

## Secondaries, nulls, robustness

- **Gao first-half-hour signal:** −1.50 bp, CI [−3.15, +0.33]. Not positive either.
- **N1 placebo:** 19 of the 20 other window ends are also negative. Only the 15:15 window is mildly positive (+0.55 bp).
- **N3 (unconditional long 15:30 → 15:59):** +0.19 points (about zero).
- **Robustness, all negative with CIs below zero:**
  - excluding FOMC / CPI / NFP days: −2.88 bp;
  - strong moves only (|r| > median): −3.85 bp;
  - entry at the 15:30 close: −2.32 bp.

## Reading

- On CME NQ in 2023–2026, the last half hour did **not** follow the day's direction.
- It **went against it**: about 4 points per trade, before costs.
- The effect is stronger on large-move days, the opposite of the hedging-demand story.
- The published momentum effect (Gao 2018 on 1993–2013 data; Baltussen 2021 on data to 2020) is not present in this post-publication sample.
- **REJECTED.**

**Note, not a strategy:**
- The negative gross mean means the *reverse* rule (fade the day into the close) was gross-positive in this sample.
- Choosing it now, after seeing the result, would be data-snooping.
- It may only be tested as a **new** pre-registration on **new data** (prospective, or a different period / market), with the user's approval.
