# Free-data plan v1: Dukascopy + Pepperstone history (Phase 0, document only)

**Status:** PLAN, 2026-10-12. Nothing has been downloaded.

**Inputs:** the user decision "free data only"; `NAUTILUS_ENV_PLAN_v1.md` (disk floor 8 GiB, catalog layout); `PREREG_HORB1_NAS100_ORB.md`.

## 1. Verified facts (checked 2026-10-12)

**Dukascopy website Terms of Use** (dukascopy.com/…/legal-pages/terms-of-use):
- Use is limited to "your own non-commercial use".
- The site and its information "may not be used to construct a database of any kind".
- "You shall not use or attempt to use any 'scraper,' 'robot,' 'bot,' 'spider,' 'data mining,' … to access, acquire, copy … any data … without the prior express written consent of DUKASCOPY."
- **Consequence:** the widely blogged method of *scripting bulk downloads* from the public datafeed URLs is **not** used by NEXA without written consent. (This replaces the stdlib `.bi5` downloader idea in `NAUTILUS_ENV_PLAN_v1.md` §4.4.)

**The official route for account holders** (the Dukascopy Historical Data Export page): "Log in to the demo or live version of JForex and select 'Historical Data Manager' from 'Tools'". It exports CSV "from tick-by-tick to monthly".
- The JForex API also has `IHistory` (`getBars` / `readBars` / ticks, by time range, BID / ASK) for the account holder's own strategies.

**The Dukascopy MCP connector** (official, linked to the user's demo):
- `get_candles` returns at most **500 candles going back from now** (M1 / H1 / D1, bid / ask / both).
- That covers live spot checks only (500 M1 ≈ 8 h); **not** a history source.

**Instrument names** (Dukascopy MCP `search_instruments`):

| Name | Instrument | Pip | Min contract |
|---|---|---|---|
| `USATECH.IDX/USD` | US 100 Tech | 0.01 | 1 |
| `USA500.IDX/USD` | — | 0.01 | 1 |
| `USA30.IDX/USD` | — | 0.01 | 0.1 |
| `DEU.IDX/EUR`, `GBR.IDX/GBP`, … | other indices | — | — |

Metals use `XAU/USD`, FX uses `EUR/USD`, etc.

**Pepperstone history already on disk** (own account, canonical MT5 export pipeline):
- `filesnexa/NEXA/data/pepperstone/PEPPERSTONE_{EURUSD,GBPUSD,USDJPY,XAUUSD,XAGUSD}_M1_recent.csv` (≈ 6–7 MB each);
- quarterly tester exports under `data/pepperstone/tester/`.
- **No NAS100 history exists** (H-ORB-1 §1).

## 2. Source options

| Source | Legal / ToS status | Automation | Coverage | Use in NEXA |
|---|---|---|---|---|
| **A. JForex Historical Data Manager** (the user's Dukascopy demo) | **Sanctioned** (the documented route) | Manual GUI export, a few clicks per instrument and range | Tick → monthly, BID and ASK, long history | **Primary bulk history** (indices, metals, FX) |
| **B. JForex SDK `IHistory`** (Java, the user's demo credentials) | Sanctioned API for account holders | Fully scriptable | Same as A | **Later**, if A becomes a bottleneck (needs a Java JDK + Dukascopy SDK install, approval) |
| C. Scripted bulk download of the public datafeed | **ToS conflict without written consent** | Scriptable | Same | **Not used.** Only if the user obtains Dukascopy's written consent (an optional email to their support) |
| D. Dukascopy MCP `get_candles` | Official | Yes | Last 500 bars only | Live sanity checks (spread, clock) |
| **E. Pepperstone MT5 export** (canonical pipeline) | Own account | Scripted (existing tooling) | As deep as the server provides | **The execution venue's own prices:** costs, parity, H-ORB-1 as pre-registered |
| F. Paid (Databento etc.) | — | — | — | Excluded by the user's "free data" decision |

## 3. Recommendation

**Use A + E now; keep B as the upgrade path; C only with written consent.**

1. **Dukascopy (A)** gives long, free, bid/ask history for backtests and research on Nautilus.
2. **Pepperstone (E)** gives the prices NEXA would actually trade at.
3. **Every strategy verdict is computed with Pepperstone costs**, regardless of whose prices drive the signal. Dukascopy spreads are never assumed to be Pepperstone spreads.

## 4. Instruments and priority

| Priority | Dukascopy | Pepperstone | Why | Gate |
|---|---|---|---|---|
| P1 | `USATECH.IDX/USD` | NAS100 | H-ORB-1 (pre-registered, approval ON HOLD) | **User approval of data acquisition.** A Dukascopy source is a **deviation** from the pre-registration §2 (which names Pepperstone M1) and is recorded before export. Files are hashed and frozen **before any statistic** is computed. |
| P2 | `XAU/USD`, `EUR/USD` | XAUUSD, EURUSD | Parity calibration: these overlap the existing Pepperstone exports | Approval of the export |
| P3 | `USA500.IDX/USD`, `GBP/USD`, `USD/JPY` | US500, GBPUSD, USDJPY | Platform breadth | Later |

**Not planned:** bulk ticks. Ticks are used only for short validation windows (disk: §7).

## 5. Export specification (for A; so every export is reproducible)

- **Timeframe:** M1, **both sides** (BID file + ASK file), plus tick exports only for named validation weeks.
- **Time zone in the export: GMT/UTC**, recorded in the manifest. Pepperstone stays in its server time (NY + 7 h) at export and is converted to UTC in the decode step. Each day's offset is DST-aware, as in the canonical pipeline.
- **Range:**
  - For P1: from the first available day to the last complete day. H-ORB-1's replication period P ends 2023-02-17 and its holdout H runs from 2023-02-18, both from the pre-registration.
  - For P2: the windows that overlap the Pepperstone exports.
- **File naming:** `data/raw/dukascopy/<INSTR>/<SIDE>_M1_<from>_<to>_UTC.csv`. Raw files are **never edited**. A `MANIFEST.json` records the sha256, row count, first and last timestamp, and the export settings.

## 6. Pipeline (Phase 1 code, after approval)

```
raw CSV (immutable, hashed)
  -> decode: parse, UTC ns timestamps, price scale per instrument master
  -> validate (report, never "fix" silently):
       duplicate / out-of-order timestamps; OHLC sanity (L <= O,C <= H);
       ask >= bid per minute (bid/ask pairing); gaps vs the exchange calendar
       (weekends, holidays, daily breaks); flat-bar runs; DST weeks
  -> Nautilus ParquetDataCatalog: Bar types
       <INSTR>.DUKASCOPY-1-MINUTE-BID-EXTERNAL / -ASK-EXTERNAL
       (Pepperstone: <SYM>.PEPPERSTONE-...), instruments from the instrument master
  -> catalog MANIFEST (hashes of the inputs + code version)
  -> GCS backup (ops/backup, once enabled)
```

## 7. Cross-source validation (pre-registered tolerances, written before any comparison)

Validation runs on overlap windows (P2 first), comparing Dukascopy and Pepperstone after UTC alignment. Reported per instrument:

| Metric | Tolerance |
|---|---|
| Missing-minute rate (each source vs the calendar) | Reported, not a tolerance |
| Median \|close difference\| | ≤ 1 × the Pepperstone median spread |
| 1-minute return correlation | ≥ 0.95 |
| Daily (17:00 NY) OHLC agreement | High / low within 2 spreads on ≥ 95 % of days |
| Spread distributions | Both reported. **Pepperstone spread is the cost basis.** |

**Index CFDs:** the reference underlying (cash index vs futures-based pricing) and the session hours may differ between the brokers. Any systematic offset is reported, never subtracted silently.

**If a tolerance fails:** the instrument's Dukascopy history may still be used for **signal research** only with a recorded deviation; costs always come from Pepperstone.

## 8. Disk budget (free ≈ 16 GiB, floor 8 GiB)

| Item | Estimate |
|---|---|
| Raw M1 CSV, bid + ask, per instrument per ~10 years | ≈ 0.5–1 GB (text) |
| Parquet catalog, per instrument | ≈ 0.1–0.3 GB |

- P1 + P2 (3 instruments) fit comfortably.
- Raw CSVs are gzip-compressed after hashing (the hash is of the original export).
- **Bulk ticks:** not kept locally.
- Every ingest step checks free space first and stops below 8 GiB.

## 9. What the user does vs what NEXA does

**User (one-time, private):**
1. Install JForex desktop.
2. Log in with the Dukascopy demo. **Change the demo passwords first**; they appeared in screenshots on 2026-10-12.
3. Check whether the demo is time-limited (some Dukascopy demos expire); if so, note the expiry date.
4. Export per §5 into `data/raw/dukascopy/`.

**NEXA (after each approval):**
- the manifest and hashes;
- decode / validate / catalog;
- the validation report;
- the Pepperstone exports via the canonical pipeline. The pipeline runs on the **Mac MT5 terminal with EAs disabled** (`common.ini Enabled=0`), read-only, which never touches the S14 VM. Starting the Mac MT5 requires the user's go-ahead each time (standing rule).

## 10. Approvals needed (in order)

1. **H-ORB-1 data acquisition** (lifts the ON HOLD), including the deviation note naming Dukascopy and/or Pepperstone as sources.
2. P2 parity exports (Dukascopy XAU/USD, EUR/USD; Pepperstone overlap windows).
3. Phase 1 code: decode / validate / catalog + parity report.
4. (Optional) B, the JForex SDK (Java install), or C, an email to Dukascopy for written consent to scripted access.
