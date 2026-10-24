# PHASE3_SIX_FAMILIES_V2 — Out-of-sample determination

Date: 2026-09-28 (UTC). Status: **no historical period can be certified unseen → OOS is PROSPECTIVE.**

## Candidate historical periods and why each fails

| Period | Symbols | Exposure before V2 freeze | Verdict |
|---|---|---|---|
| 2017-06 → 2026-09 (Pepperstone M1) | EURUSD, GBPUSD, USDJPY, XAUUSD, XAGUSD | Factory runs (XAUUSD H1), the NEXA Strategy Tester campaign, the Phase-2 parity/cost/time audits, the V1 design (whose OOS 2025-01→2026-09 was fixed after the data had been inspected) | CONTAMINATED |
| 2026-08-28 → 2026-09-25 (ticks) | CORE4 + XAGUSD | All 21 days inspected in the tick audit | CONTAMINATED (F6 BLOCKED) |
| 2008 → 2016 (FX M1, local legacy files) | FX only | Not used by any strategy run, but D1 2000–2026 was inspected, and the designer (the model) has prior knowledge of that market history (crisis, SNB 2015, Brexit 2016…) | NOT CERTIFIABLE |
| XAUUSD before 2017-12 | XAUUSD | No M1 data (78 KB stubs) | UNAVAILABLE |

No period can be shown to be unseen by both the data pipeline and the designer. So the only clean OOS is one that has not happened yet.

## Decision

* **OOS = [2027-01-04T00:00:00Z, 2028-01-03T00:00:00Z)**, prospective, starting 98 days after the freeze.
* **EXCLUDED = [2025-01-01T00:00:00Z, 2027-01-04T00:00:00Z)**. This covers the prior V1 holdout plus the buffer up to the OOS start. It may be used for nothing: no selection, validation, promotion or reporting of any V2 claim.
* DEV = [2018-01-01Z, 2023-01-01Z); VAL = [2023-01-01Z, 2025-01-01Z); walk-forward years 2020–2024. These periods are known to be seen. They serve development and validation only, never as evidence of edge.
* Selection for OOS happens exactly once per (experiment, claim, symbol). It is sealed in the ledger (OOS_SELECTED) before the OOS start, and the OOS is scored once, after it ends. The registry enforces every step (`nexa_registry2.record` / `select_for_oos`).
* F1 OOS first prints must be logged live at release time. First-print status cannot be confirmed historically for the most recent release.
* The tick families (F4, F6) need tick data collected entirely after the freeze and remain BLOCKED.

## Consequence

No V2 claim can be promoted before 2028-01-03 plus the scoring time. This is deliberate: it is the price of a genuinely unseen OOS.
