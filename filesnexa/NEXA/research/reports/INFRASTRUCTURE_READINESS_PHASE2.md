# Phase 2 infrastructure readiness report (2026-09-27)

**Scope: infrastructure only.** None of the six strategy families was implemented, optimised or evaluated. The Phase-3 campaign is **FROZEN, not open**: the registry refuses any result until a human opens it with an approval note.

Invariants: `NEXA_Risk.mqh` byte-identical to the immutable baseline (`e706d453d346100f`); schema v1.0 (`c24198b09b0e7192`) and f00–f47 / `NEXA_Intelligence.mqh` (`efa6db4e4abae2a9`) unchanged; NEXA EA unchanged in this phase (`97a3ff62cb2c4d36`); `MTM_ENABLE_TRADING=false`, `MTM_ENABLE_EXEC=false`; no orders; no broad broker download (the local history base was **24,891,040 KB before and after** every export). Cross-feed latency (F4) remains BLOCKED.

## Readiness by prerequisite

| # | Prerequisite | Status | Evidence |
|---|---|---|---|
| 1 | DST-aware canonical time | **READY** | `nexa_time.py`; 9 tests, incl. an hour-by-hour match to IANA America/New_York 2000–2030 |
| 2 | Historical M1 from local Pepperstone data | **READY** (2 warm-up chunks skipped, documented) | 63/65 chunks PASSED, each verified from its own log; canonical files for 5 symbols; 0 overlap conflicts |
| 3 | Authoritative calendar with provenance | **READY** | MT5 calendar exported from the live terminal: 23 countries, 1,508 events, 139,409 values (2017-01 → 2026-09); provenance + SHA-256 |
| 4 | Deterministic execution/fill simulation | **READY** | `nexa_execution.py`; 9 tests, incl. exact agreement with the factory simulator where the rules coincide |
| 5 | Experiment/campaign/multiple-testing hierarchy + frozen protocols | **READY** | `nexa_registry.py` (14 tests); 6 protocols frozen; campaign `PHASE3_SIX_FAMILIES_V1` FROZEN, sha `9b5b78738950d3b8` |

Regression after every step: 345 → 354 → 367 → 375 → 379 → 380 → **382 passed**, ruff clean each time.

## Findings that change how research must be done

1. **Pepperstone's server clock is "New York + 7 h", not EU EET/EEST.** Across 144 weeks × 4 symbols the FX week opens Sunday 17:0x New York (Monday 00:01 server), and gold one hour later, in **every** week including the US/EU DST-gap weeks. Consequences:
   - NEXA's fixed `InpGMTOffset=2` is wrong from the 2nd Sunday of March to the 1st Sunday of November (D-TZ; EA untouched, human decision).
   - My Phase-1 design document stated EU DST. It is **corrected**.
   - Evidence: `reports/TIME_CONVENTION_EVIDENCE.json`.
2. **MT5 stamps ALL calendar history with the server offset at export time.** US Nonfarm Payrolls (08:30 New York all year) appeared at 15:30 in US-summer months and 16:30 in winter months of a summer export. Converting calendar text with the bar clock would have shifted every opposite-season event by 1 h.
   - `nexa_calendar` now converts with the provenance-recorded export offset (+3 h).
   - Result: NFP shows 08:30 New York in **115/116** releases; the remaining row (2025-11-20) is flagged, not repaired.
3. **Local-clock validation across all countries:** 14% of exact-time rows are off their event's modal local time. These are dominated by variable-time events (central-bank speeches, EIA stocks, a UK CPI schedule change). Only 4.4% of the high-importance off-mode rows are exactly ±60 min, and they do not cluster at DST transitions. There is no systematic time-basis error. F1 is therefore restricted to scheduled HIGH-importance **indicators**, excluding speeches, DATE/TENTATIVE rows and flagged rows (written into the frozen F1 protocol).
4. **MQL5 `FILE_ANSI` is cp1252**, not UTF-8 (0x80 = €). The calendar loader declares the encoding explicitly.
5. **Tester hang, XAUUSD/XAGUSD 2017-H2** (open-prices mode, 15+ min at 80% CPU, twice; every other chunk takes seconds). Those two warm-up chunks were skipped and recorded in `export_log.tsv`. DEV starts 2018-01-01, so no design period is affected.
6. **XAGUSD M1 ends 2023-12-29** (the 2024–26 tester campaign covered only NEXA's basket). XAGUSD is used only by F6 (ticks). Bar families use EURUSD/GBPUSD/USDJPY/XAUUSD.
7. **Rebuilt bars match the broker's bars:** M5/M15/H1 aggregated from canonical M1 match Pepperstone's own bars with mismatch ≤ 2.8e-5 of bars, which confirms the server-time bar alignment.
8. **The execution engine's differences from the factory simulator are intentional and documented:** TP is a resting limit (trade-through, no slippage, gap improvement), time exits happen at the next open, and limit fills need trade-through. It agrees exactly with the factory where the rules coincide (test-enforced).

## Data now available (Pepperstone-Demo, all hashed)

| Dataset | Coverage | Location |
|---|---|---|
| Canonical M1 (server + UTC + offset + status) | EURUSD/GBPUSD/USDJPY 2017-06 → 2026-09 (~3.43M bars each); XAUUSD 2017-12 → 2026-09 (3.09M); XAGUSD 2017-12 → 2023-12 (2.11M) | `data/pepperstone/m1_canonical/` + `manifest_<SYM>.json` |
| Raw M1/M5/M15/H1/D1 chunks | 2017-07 → 2023-12 | `data/pepperstone/m1_history/` (+ `export_log.tsv`, `SHA256SUMS`) |
| MT5 calendar, canonical | 2017-01 → 2026-09, UTC via export offset, local-clock flags | `data/pepperstone/calendar/canonical/` |
| MT5 calendar, raw export + provenance | as exported | `data/pepperstone/calendar/20260927T153535Z/` |
| Real ticks (quote-only) | 2026-08-28 → 09-25, 5 symbols | `data/pepperstone/*_ticks_recent.csv.gz` |

## Frozen Phase-3 campaign `PHASE3_SIX_FAMILIES_V1` (state: FROZEN)

| Experiment | Status | Declared trials | Protocol sha256 (16) |
|---|---|---|---|
| F1 Macro event | ACTIVE | 216 | c462db9027dcc9c3 |
| F2 XAU session breakout | ACTIVE | 24 | b49706d36550aa99 |
| F3 FVG retracement | ACTIVE | 288 | 1c1768690a4eab46 |
| F4 Cross-feed latency | **BLOCKED** (no second synchronous tick feed) | 32 (not counted) | b6d6c4c2fa0701e8 |
| F5 Asian mean reversion | ACTIVE | 144 | 2c5c50e480e77ae0 |
| F6 Tick quote imbalance | ACTIVE | 135 | c81063525fe810f2 |

- **Trial accounting:** 807 active + 108 legacy = **915** for the deflated Sharpe; **18** primary tests for campaign-level Benjamini–Hochberg (q = 0.10).
- **Hierarchy:** campaign (BH + DSR with 915 trials) → experiment (PBO/CSCV + parameter-surface stability) → configuration (intersection-union over every declared null).
- **Enforcement (tested):** results only for pre-declared configs and symbols; OOS evaluable once; BLOCKED experiments never; tampering with a protocol or the hash-chained ledger is detected.
- Every protocol pins the M1/calendar/tick/DNA hashes, the time-convention evidence and the execution-engine code hash.

## Not ready / open

- **F4:** blocked (needs a second broker login and parallel tick logging).
- **F6:** 21 days of quote-only ticks; true OOS needs ≥ 4 weeks of forward logging (`NEXA_TickLogger`) after the freeze.
- **DOM** availability unverified in open market.
- **B-EXPOSURE-CAP** (0.02 lots per currency) means even a validated family could not execute through NEXA at $50k. Human decision pending.
- D-TZ now spans roughly 8 months a year (US DST).
- Disk: 7.4 GB free.

## To start Phase 3
The human opens evaluation explicitly:
```
Registry("research/registry").open_evaluation("PHASE3_SIX_FAMILIES_V1", "<approval note>")
```
Any change to a protocol after that requires a new version and a new campaign; frozen protocols cannot be edited in place.
