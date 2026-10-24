# H-SK28-OOS deviations log (PREREG_SK28_OOS.md)

All entries are written before the result they could affect is known.

## D1 (2026-10-23, build, before any QuantConnect run): what the logs carry
- **Prereg §4** says the logs carry per-day aggregates, per-model/per-year summaries and per-replicate control sums.
- **Built:** each chunk logs **one 11-character record per trade** instead. A record holds:
  - entry day and minute, model, side, exit reason;
  - gross R in hundredths; 1R in ticks;
  - the mirror trade's gross R and 1R (or "refused").
- The chunk also logs a bitmap of its RTH days and the gate counts.
- **All statistics** (costs, bootstrap, blocks, the control replicates, the verdict) are computed locally by `sk28_stats.py` from these records.
- **Why:** the per-trade records hold strictly more information than the planned aggregates and fit the 10 KB log limit (about 9 KB at 800 trades a year). Computing the statistics locally lets them be unit-tested and re-checked.
- **Effects:**
  - R is rounded to 0.01 per trade. The rounding is unbiased.
  - |R| above 20.47 is clamped; the count of clamped trades is logged and should be 0.
  - The control uses 2,000 replicates (the prereg also says 2,000).
- Not result-driven.

## D2 (2026-10-23, build, before any QuantConnect run): half-year chunks
- **Prereg §2** says one calendar year per chunk.
- **Changed to half-year chunks:** January–June and July–December. Each chunk has the same 120-day warm-up before its first calendar day, and the same P/IN window clipping.
- **Why:** the local reference (G1, their own data, in-sample) produced up to **906 trades in a year** (2024). At 11 characters per trade that exceeds QuantConnect's free 10 KB log per backtest. Half years stay under ~5 KB.
- **Effect:** engine state (the 10-loss pause, daily caps) restarts twice a year instead of once.
- **Check (done 2026-10-23, before any QC run):** on their own file, the 2024 H1 chunk (warm-up from 2023-09-03, 291,204 bars) reproduced the full-history reference **exactly: 454 of 454 trades matched** in every one of the 12 models (gross +0.192R, S1 +0.027R for that half). So chunking adds no error; a gate mismatch on QC can only come from the data source.
- The decision uses only in-sample trade counts, never P data.

## D3 (2026-10-23, build, before any QuantConnect run): gate matching done locally
- **Prereg §3** says REF is uploaded as a data module and matched in QC.
- **Instead:** each chunk's per-trade records (D1) carry the entry day, minute, model and side. `sk28_stats.py` matches them locally against `qc_sk28/ref_trades.py`, using the same rule (`qm.match_ref`: same model and side, within ±2 minutes, one-to-one, nearest first).
- Gate thresholds are unchanged.
- **Why:** this avoids uploading a 42 KB reference file to QC, and the matching is unit-tested.

## D4 (2026-10-23, upload, before any QuantConnect run): 24 frozen files on QC, not 25
- QuantConnect free projects hold at most **25 files**. The project needs the 25 frozen files plus `main.py`.
- **Left out:** `backtest/__init__.py`, the **empty** file (sha256 e3b0c442…, 0 bytes). Python 3 imports `backtest.engine_v2` from a folder without `__init__.py` (namespace package), with identical code.
- If another package named `backtest` shadowed it, the import of `backtest.engine_v2` would fail loudly, not silently.
- The other 24 files were fetched from GitHub at 0ee4392d inside the page. Each was hash-checked against Appendix A before upload and again after reading it back from QC: **24/24 match**.
- `main.py` matches the frozen 7c8ce7d9 (page and QC read-back).
- `main.py`'s header comment still says "25 files"; it is left unchanged (the code hash is frozen).
