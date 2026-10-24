# B5: Data sources for aggressor-side CME data (started 2026-10-11)

**Nothing purchased; no credits used.**

| Source | What it provides | Coverage / history | Price (as published) | Fit for NEXA | Status |
|---|---|---|---|---|---|
| **Databento `GLBX.MDP3`** | CME/CBOT/NYMEX/COMEX futures **and options on futures**. Schemas: trades (tick-by-tick, **aggressor side**), mbp-1/mbp-10, **mbo**, ohlcv, definition, **statistics** (daily volume, **open interest**, settlement; OI published the next UTC date) | Product coverage from **June 2010**; full MBO granularity from **May 2017** (MDP 3.0) | **Per-schema USD/GB, uncompressed size (verified via API `list_unit_prices` 2026-10-11):**<br>- trades / tbbo 28;<br>- mbo / mbp-1 1.8;<br>- mbp-10 0.5;<br>- ohlcv-1m 70;<br>- ohlcv-1d/1h 190;<br>- statistics 1.0;<br>- definition 1.7.<br>~~"from 0.50/GB"~~ applies to mbp-10 only. **USD 125 free credits** for new sign-ups; live data in paid plans | **Best fit:** true Big Trades, delta, footprint, imbalance, aggregation by aggressor; MBO absorption/icebergs from 2017; options OI if ever needed | Docs verified (pricing page, statistics example, GLBX.MDP3 knowledge base). **Size estimate unofficial:** ES trades ≈ 2 GB/month (NexusFi). 6E/6J/6B/GC are smaller; to be estimated with the official cost estimator (needs an account → approval) |
| Massive (connected MCP) | 1-min aggregates incl. **transactions** count; rolling 2 y. **Futures product GA May 2026**; CME **tick-level trades flat files** (nanosecond timestamps) in select plans (USD 29–999/month tiers) | 2 y on the current plan; history varies by plan | Current plan: trades NOT_ENTITLED | **Aggressor-side field undocumented** (verify on one day of flat file if a plan is ever upgraded) | Partly known |
| Rithmic / dxFeed (via DeepCharts, ATAS, Bookmap) | Live L1/L2 and MBO | Live; **no historical MBO backfill** (DeepCharts doc) | Platform/data subscriptions | Prospective only | To research (B5 next) |
| CME DataMine | Official historical Market Depth (5–10 deep futures; trades included), MBO FIX product, settlements, OI; 1- or 12-month subscriptions; futures and options sold separately; 2027 fees +3.5 % | Long history | **No public retail price found** (quote from CME) | Authoritative, costly, slow procurement | Partly known |
| Databento live CME | Live CME data, licence pass-through | Live | **from USD 32.65/month (non-professional)**; USD 740/month professional non-display | Needed only for live operation of a validated setup | Known (roadmap announcement) |
| Pepperstone (MT5) | Bid/ask quotes, tick-volume (quote count) | 2017–2026 M1; ticks 28 days + logger | — | **No aggressor side, no traded volume** (CL-050) | Known |

**SUPERSEDED (2026-10-11):** the earlier "≈ USD 65–225 for 2017–2026" estimate assumed USD 0.50/GB for trades. It is **wrong by about 50×**; trades cost USD 28/GB.

## Official `metadata.get_cost` quotes (free API calls, 2026-10-11)

**Request settings:** `GLBX.MDP3`, historical streaming; symbols are the continuous volume front month (`X.v.0`). **Nothing was purchased.**

| Schema | Symbol | 1 day (2026-10-08) | 1 week (10-05..10) | 1 month (Sep 2026) | 1 year (2025-10..2026-10) |
|---|---|---|---|---|---|
| trades | 6E | 0.051 | 0.255 | 0.797 | **11.47** (440 MB) |
| trades | 6J | 0.026 | 0.128 | 1.005 | **9.43** |
| trades | 6B | 0.018 | 0.085 | 0.341 | **5.13** |
| trades | GC | 0.118 | 0.537 | 2.930 | **36.54** (1.4 GB) |
| mbo | 6E | 0.214 (128 MB) | | | |
| mbp-10 | 6E | 0.321 (688 MB) | | | |
| tbbo | 6E | 0.086 | | | |
| ohlcv-1m | 6E | 0.005 | | | |

**Implications**
- 1 year of trades for all four products ≈ **USD 62.6**, so 9 years ≈ **USD 560** (if volumes were similar; earlier years are likely smaller).
- The USD 125 credit covers ≈ 2 years of 6E + 6J + 6B, or ≈ 10 years of 6E alone. GC is the expensive product.
- **User hard cap for now: USD 5.00** (enforced by `../../databento/db_guard.py`).
- **Trades `side` field = aggressor side** (A/B/N). This confirms the data can support true Big Trades (OF-03-ORIG).

**Account check:** the API key authenticates. 29 datasets are visible; `GLBX.MDP3` covers 2010-06-06 → 2026-10-10. Continuous symbols 6E/6J/6B/GC/ES/NQ `.v.0` all resolve.

## First purchase: 6E trades pilot (2026-10-11)

**Purchase:** USD 0.7973 from the new-user historical credit. Guard committed 0.80 of 5.00. File: `../../databento/data/GLBX.MDP3_trades_6E.v.0_2026-09-01_2026-10-01.dbn.zst` (12.8 MB).

**Integrity:**
- 636,982 records = the estimate exactly.
- 2026-09-01 00:00 → 09-30 23:59 UTC.
- Price 1.13485–1.16565.
- 2 instruments (ids 5510 and 10573): the `v.0` continuous symbol rolled by volume mid-month, so the series carries a contract-to-contract carry gap at the roll.

**Aggressor side:**
- A (sell aggressor) 313,018; B (buy aggressor) 311,170; N 12,794 (2.0 %; implied/unspecified, per the Databento docs).
- Volume: buy-aggressor 1.64 M vs sell-aggressor 1.65 M contracts, out of 3.42 M total.

**Single-print size distribution** (prints, not aggregated parent orders):
- median 2 lots; p90 12; p95 18; p99 48; p99.9 116; max 1,035.
- ≥ 25 lots (Trader Dale's 6E filter) = 3.24 % of prints and 27.9 % of volume.
- ≥ 50 lots = 0.94 % of prints and 13.4 % of volume.
- ≥ 100 lots = 0.17 % of prints and 4.2 % of volume.

**Open items** (no further spend needed):
- (1) Aggregate prints by timestamp/aggressor into parent orders; DeepCharts/ATAS "aggregated" trades differ from single prints.
- (2) Handle the roll gap.
- (3) Overlap with Pepperstone EURUSD M1 to 2026-09-25: test whether futures VA/POC/LVN levels transfer to the spot CFD (the basis question).
