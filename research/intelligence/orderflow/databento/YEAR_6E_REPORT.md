# 6E 13 months: true CME order flow vs the NEXA proxy (2026-10-11)

**Data**
- Databento `GLBX.MDP3` trades, `6E.v.0`, 2025-09-01 → 2026-10-01: 9,918,197 trades, 6 contracts (6EU5 → 6EZ6), 4 quarterly switches.
- Cost USD 11.6340 + the 0.7973 pilot, both from the free credit.

**Comparison data:** Pepperstone EURUSD M1 to 2026-09-25.

**Code:** `year_6e_analysis.py`. **Raw output:** `year_6e_results.json`. Definitions are identical to `PILOT_6E_REPORT.md`.

**Nature:** descriptive measurement only; no trading rules, thresholds or returns.

**Sessions:** 264 used. Excluded:
- 7 sessions touching Databento "degraded" dates (`dataset_condition_2025-09_2026-09.json`);
- 5 thin sessions (near contract expiry or holidays);
- the first, partial session;
- the days after the Pepperstone data ends.

## Q1. Aggressor orders (same timestamp + aggressor side)

**Over the whole period:**
- median 2 lots; p99 34; max 1,109.
- **≥ 25 lots = 1.75 % of orders / 19.4 % of volume.**
- ≥ 50 = 0.49 % / 9.7 %.
- ≥ 100 = 0.11 % / 4.0 %.
- No aggressor side: 1.6 % of records.

**Share of orders ≥ 25 lots by quarter:** 1.26 % (2025Q3) → 1.50 → 1.46 → 1.80 → **2.62 %** (2026Q3).
- p99 order size rose from 28 to 42 lots.
- **September 2026, the pilot month, was the most extreme month (3.4 %).**
- **A fixed lot threshold selects a drifting share of activity: about 2× within a year.**
  - A rule such as "≥ 25 lots" therefore means different things in different months.
  - A relative definition (e.g. a percentile of recent orders) would be stable. **That is a design decision for the user**; no source in the KB sets one.

## Q2. Contract switches

Basis jumps at each switch: +60.3 (Sep 2025), +51.6 (Dec), +48.5 (Mar), +41.8 (Jun), +40.8 (Sep 2026) pips. Each tracks the 3-month interest-rate differential, which narrowed over the year.

**One contract per session profile, always.**

## Q3. Transferring levels to Pepperstone EURUSD (pips)

**Basis error:**

| Measure | p50 | p90 | p95 | p99 |
|---|---|---|---|---|
| \|basis − same-session median\| | 0.2 | 0.5 | 0.6 | 0.8 |
| \|basis − prior session's last-hour basis\| (same contract) | 0.7 | 1.8 | 2.2 | 3.2 |

- **Prior-close basis error, p95 by quarter:** 4.3 / 2.4 / 2.05 / 2.05 / 1.55. The worst quarter covers a switch period.
- **The pilot understated this error** (p95 1.6 in the pilot vs 2.2 over the year).
- **The basis shrinks by a median of −0.6 pip per session** (p5–p95: −2.1 to −0.1).

**Value-area agreement** with the true futures profile (P1). Median true VA width: 27 pips (p5–p95: 13–63).

| Profile | \|VAL\| p50 / p75 / p90 | \|VAH\| p50 / p75 / p90 | \|POC\| p50 / p75 / p90 |
|---|---|---|---|
| P2 futures M1 bars, real volume | 1.0 / 2.0 / 4.0 | 1.0 / 2.0 / 5.0 | 1.0 / 6.0 / 16.7 |
| **P3 Pepperstone tick volume (OF-03P)** | **3.9 / 8.5 / 19.1** | **3.2 / 8.4 / 17.4** | **2.4 / 13.0 / 32.4** |

**Median \|P3 error\| by quarter (VAL / VAH / POC):**

| Quarter | VAL | VAH | POC |
|---|---|---|---|
| 2025Q3 | 7.1 | 6.4 | 6.9 |
| 2025Q4 | 3.7 | 2.7 | 2.2 |
| 2026Q1 | 3.2 | 3.6 | 2.5 |
| 2026Q2 | 4.4 | 4.6 | 2.2 |
| 2026Q3 | 4.1 | 2.5 | 1.8 |

**Profile-shape Spearman:** median 0.85 (p5 0.66). No systematic sign bias.

## Conclusions (evidence class: NEXA, descriptive, n = 264 sessions)

1. **The pilot's conclusion holds over 13 months and is sharper in the tails.**
   - The proxy profile matches the overall shape (ρ ≈ 0.85).
   - Its VA edges are typically 3–4 pips off.
   - **1 session in 10 is off by 17–19 pips**, about two-thirds of a typical value area.
   - The 1-minute-bar approximation alone stays at about 1 pip, so the gap is caused by **tick count ≠ traded volume**.
2. **True Big Trades require true CME data, and their definition must handle drift.** The share of orders ≥ 25 lots doubled within the year.
3. **Moving CME levels onto Pepperstone with yesterday's basis gives errors of about 0.7 pip typically and 2.2 pips at p95.**
   - That is acceptable for zones, but not for "1–2 tick" stops (GAP-M04).
   - The same-session basis would be precise (p95 0.6), but needs a live futures price.
4. **These are measurements of data fidelity, not of profitability.** No trading edge has been tested.
