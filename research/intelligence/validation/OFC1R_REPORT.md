# OFC1R: final replication of OFC1 on unseen 6E data, 2023-01 → 2025-08 (2026-10-11)

- **Pre-registration:** `PREREG_OFC1R_REPLICATION.md` (sha 4c30f52f…), marked FINAL. It and the wrapper `ofc1r_run.py` (sha ee209a1f…) were hashed **before the data was downloaded**.
- **Engine:** `ofc1_core.py` unchanged (sha 4065c597…), with D1–D10 applied.
- **DSR:** computed with the research venv (D11).
- **Data:** Databento 6E trades, 2022-10-01 → 2025-09-01. 39,852,096 records, equal to the estimate. USD 49.88 from the free credit.
- **Sessions:** 671 scored; 10 roll sessions skipped; 7 excluded (thin or degraded). The run was executed once.
- **Raw output:** `ofc1r_results.json`, `ofc1r_dsr.json`.

## Verdict: **REJECTED.** The OFC1 line is closed.

| | Trades | Mean R (net) | 95 % CI | p (> 0) |
|---|---|---|---|---|
| **Pooled S0** | 211 | **−0.119** | [−0.262, 0.018] | 0.959 |
| Pooled S1 (+1 tick) | 211 | −0.180 | [−0.327, −0.040] | 0.994 |
| 2023 | 104 | −0.105 | [−0.307, 0.108] | 0.83 |
| 2024 | 66 | −0.202 | [−0.473, −0.035] | 0.99 |
| 2025 (Jan–Aug) | 41 | −0.020 | [−0.238, 0.365] | 0.36 |

**Acceptance:** 5 of 6 criteria failed; only criterion 4 passed.

| # | Criterion | Result |
|---|---|---|
| 1 | Mean > 0 with p < 0.05 | ✗ |
| 2 | S1 mean > 0 | ✗ |
| 3 | Timing placebo p ≤ 0.05 | ✗ (p = 0.61) |
| 4 | Δ vs no confirmation > 0 | ✓ (+0.09 R, CI [−0.34, 0.44], p 0.39) |
| 5 | ≥ 2 of 3 years positive | ✗ (0 of 3) |
| 6 | DSR ≥ 0.95 | ✗ (DSR = 0.0007) |

**By setup:**
- A −0.073 (101 trades);
- A′ −0.151 (106);
- B −0.215 (3);
- B′ −1.10 (1).

**By block:** Asia +0.016 (35), London −0.034 (74), NY −0.227 (102).

**Exits:** 91 at target, 95 stopped, 25 at the time limit.

**Benchmarks:**
- **Timing placebo:** random entries with the same geometry average −0.106 R. The method is **no better than random timing**.
- **No confirmation:** the same rules without confirmation give −0.209 R (81 trades).

**Robustness (report only):** every variant is negative, from −0.07 (stack ≥ 2; first bubble −0.09) to −0.30 (cost floor off).

**Combined with OFC1's 6E trades (descriptive, no verdict):** 258 trades, mean −0.160 R.

## Conclusion (evidence class: NEXA, pre-registered, out-of-sample)

1. **The user's core order-flow method, as fully specified in rules on true CME aggressor data, has no edge.** It loses about 0.1–0.2 R per trade after realistic costs:
   - in 10 months across four instruments (OFC1);
   - and in 32 unseen months of 6E (OFC1R).
2. **Its entries are not better timed than random entries** with the same stops and targets, in either test.
3. **The order-flow confirmation is the only component that helped,** reducing losses by about +0.1–0.16 R relative to the same levels without it. It is never significant and never enough to make the method profitable.
4. **This closes the OFC1 line**, as agreed with the user:
   - no further purchases, variants or re-runs;
   - any variant suggested by these results (e.g. "Asia only", "first bubble") would be data-mined and is **not** to be pursued under this evidence.
5. **What it does not test:** discretionary judgement, the DeepCharts visuals, or execution skill. It tests the rules the user approved (E1–E12).
