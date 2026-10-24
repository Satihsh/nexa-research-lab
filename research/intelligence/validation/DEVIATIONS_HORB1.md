# H-ORB-1: interpretations and deviations

**Pre-registration:** `PREREG_HORB1_NAS100_ORB.md` (sha `af3b6169…`, read-only).

**Written 2026-10-13, before any NAS100 data exists on this machine.** No NAS100 outcome has been computed or seen.

The user approved the implementation and the test on 2026-10-13 ("yes start H-ORB-1 test now").

## Interpretations (I-n): where the pre-registration leaves a detail open; fixed now, before data

| # | Topic | Fixed choice |
|---|---|---|
| I-1 | "Missing a required M1 bar" (§2) | Required bars are the five first-candle bars (09:30–09:34), the 09:35 entry bar and the 15:59 exit bar. Gaps between entry and exit do not exclude a day; the stop/target path uses the bars that exist. |
| I-2 | Spread per bar (§3, §4 S0) | Each bar's recorded spread, floored at 1.0 index point. Entry uses the 09:35 bar; short stop/target triggers use each bar's own floored spread; the time exit uses the 15:59 bar. |
| I-3 | Stress "per side" (§4) | Applied to every fill: the entry, and the exit whether stop, target or time. The pre-registration names stop fills explicitly; target fills are treated the same (conservative). |
| I-4 | Definition of R | R = \|S0 entry (spread-inclusive, no stress) − stop\|. It is identical across S0/S1/S2. Outcome = net P&L ÷ R. |
| I-5 | DSR trial count (§6) | n_trials = 1 primary + 2 (long-only, short-only) + 20 placebo times = **23**. The trial-Sharpe variance is computed over these series. DSR is evaluated on **H at S1**. |
| I-6 | Target fill (§3.5) | Fills exactly at the target price, with no price improvement on gaps (conservative). |
| I-7 | Gap through the stop (§3.4) | Fills at the bar open, from the bar after entry. The entry bar opens at the entry price itself. In the §8 "entry at 09:35 close" variant, it applies from the first bar after entry. |
| I-8 | Stop already breached at entry | If the 09:35 entry price is at or beyond the first-candle stop, R ≤ 0: **no trade**, counted as `stop_breached_at_entry`. |
| I-9 | Calendar coverage (§2) | Uses the frozen `IM1_US_CALENDAR.json` (covers 2017–2026). Days outside it are excluded and counted. If the export starts before 2017, a deviation is recorded **before P is opened**. |
| I-10 | Where acceptance §7.4 / §7.6 are measured | On **H at S1** (the decisive holdout). P is reported for information and is only used for §7.1 and the sign check. |
| I-11 | Verdict order | INSUFFICIENT-N (H < 300 S1 trades) → REJECTED (H S0 mean ≤ 0, or P/H opposite signs) → RESEARCH_CANDIDATE if every check passes → otherwise INCONCLUSIVE. |
| I-12 | "Last complete day" | The latest New York date present in the export is excluded from H. |
| I-13 | §8 ATR variant | Stop = 5 % of the 14-day ATR, where ATR is the mean true range of the 14 previous eligible days' RTH bars (09:30–15:59). No target, EoD exit, S1. |
| I-14 | §8 event-day exclusion | US events in the MT5 calendar matching FOMC / Fed rate decision / CPI / NFP. Server date − 7 h gives the New York date. |
| I-15 | Sizing report (§7, not a criterion) | Also reports the account needed at 1 % risk for **one MNQ** ($2/pt). This is informational only; the verdict concerns Pepperstone NAS100. |

## Data source

**As pre-registered (§2), no deviation:** Pepperstone MT5 NAS100 M1 (bid OHLC + spread), exported with the canonical pipeline.
- The export runs on the **Mac MT5 terminal with EAs disabled**; it never touches the S14 GCP VM.
- Starting the Mac MT5 requires the user's explicit go-ahead (standing rule).
- The export is hashed and frozen before `--stage P`.

**Alternatives** (each would be a recorded deviation D-n before data is seen; not chosen):
- CME NQ 1-minute data from Databento: quoted 2026-10-13 at USD 13.76 for `ohlcv-1m` 2016-01-01→2026-10-10. The Databento cap is exhausted, so this needs new user approval.
- A Dukascopy USATECH JForex export.

## Deviations (D-n)

**Recorded 2026-10-13, after user approval "approve Databento $4.71 (option 1)", BEFORE the NQ data is downloaded.** No NQ or NAS100 outcome has been seen.

| # | Deviation from the pre-registration | Reason / effect |
|---|---|---|
| D-1 | **Data source:** CME **NQ futures**, continuous front month by volume (`NQ.v.0`, Databento `GLBX.MDP3`, `ohlcv-1m`, 2023-02-18 → 2026-10-10), replaces Pepperstone NAS100 M1 (§2). | Same Nasdaq-100 underlying, exchange trade prices. The user is moving to CME micro futures (MNQ); NQ has the identical price path. The Pepperstone export would have needed the Mac MT5 terminal. Quote USD 4.7078, within the user's remaining Databento credit. |
| D-2 | **Period:** **H only.** No data before 2023-02-18 is purchased, so **P is INSUFFICIENT by design**: §7.1 is not evaluated and the P-vs-H sign check is unavailable. | Budget (USD 7.06 credit; P+H minimum quoted USD 7.31). §6 already provides "only H is judged" when P is insufficient. H is the decisive, post-publication holdout. |
| D-3 | **Spread / cost:** trade OHLCV has no bid/ask, so every bar's spread = the S0 floor **1.0 index point**. Long entry = open + 1.0; short exit = close + 1.0; short stop/target triggers use high/low + 1.0. Stress S1/S2 unchanged. | Real NQ spread ≈ 0.25 point (1 tick), so this is conservative (≈ 4× the typical spread). §8 spread-floor variants (0.5 / 2.0) are still reported. |
| D-4 | **Code change:** `horb1_orb.py` gains `--data <path>` (default unchanged), and a converter `horb1_databento_convert.py` writes the canonical CSV layout (`time_server` = New York + 7 h, spread = 0 points so the floor applies, `time_status` = OK). | Rule logic unchanged. Tests re-run and code re-hashed before the download. |
| D-5 | **Roll handling:** `NQ.v.0` switches contract by Databento's daily volume mapping. Each trade lives inside one RTH session (09:35 → 15:59 ET), so no position spans a roll. | No adjustment needed. A roll day uses the contract mapped for that day. |
| D-6 | **Sizing report:** the §7 NAS100 sizing lines are kept for comparability. The MNQ line ($2 / point) is the relevant one for this data. | Report-only. |

**Scope note (not a deviation):** the user is moving toward CME micro futures (MNQ) via ATAS. The H-ORB-1 verdict concerns Pepperstone NAS100. Transferring it to MNQ would need its own cost check, and any further test would be pre-registered separately.
