# evidence/: measured data probes (2026-10-04)

**DATA-AVAILABILITY PROBES, NOT RESEARCH EVIDENCE OF EDGE.** No hypothesis outcome was computed.

| File | What |
|---|---|
| `gc_hourly.csv` | Massive GCZ6 1-min aggregates (2026-08-31 → 09-25) summed per UTC hour: volume, transactions, bar count. SQL run in the Massive workspace; result extracted verbatim |
| `e6_hourly.csv` | Massive 6EZ6 per-hour volume and transactions from 2026-09-15 (post-roll), joined with Massive C:EURUSD per-hour quote count (`n`) |
| `gc_daily_profile.csv` | GCZ6 daily (UTC date) volume profile on $1 bins of the typical price: POC, 70 % VA, total volume |
| `gc_hourly_close.csv` | GCZ6 close at hh:59 UTC, used for the futures–spot basis |
| `volume_proxy_check.py` → `volume_proxy_check_results.csv` | Hourly correlation of exchange volume vs Pepperstone M1 tick volume (log Pearson, Spearman, de-seasonalised, hour-of-day profile) |
| `profile_proxy_check.py` → `profile_proxy_check_results.csv` | Daily POC/VA agreement of the XAUUSD tick-volume profile (basis-shifted) vs the COMEX volume profile |

**Re-run:**
```
python volume_proxy_check.py .
python profile_proxy_check.py
```
Both need `filesnexa/NEXA/.venv-research` and the MT5 canonical M1 files.

**Caveat:** the basis in `profile_proxy_check.py` uses each day's median of hourly differences. That is acceptable for a descriptive probe and is **not causal** (03 §3).
