# PRE-REGISTRATION H-GEX-VIX-RANGE: do SPX dealer gamma + VIX improve the range forecast for S&P-family futures on data NEXA has not looked at?

**Status: DRAFT, awaiting the user's approval. Nothing has been run.**
- Requested 2026-10-24 (chat): "Draft the ES + VIX gamma range model pre-registration for my approval. Don't run anything yet."
- Source: the secondary result of H-GEX-RANGE (`GEX_RANGE_REPORT.md`, prereg 8f7ccf39): ES, gamma added on top of VIX, +3.0 % error reduction, p 0.003, 7/11 years.
- **Written before any YM or RTY range has been compared with gamma or VIX**, and before any 2026 option chain has been loaded.

## 0. Read this first: what the lead really says (honest check of the H-GEX-RANGE numbers)
- **The ES + VIX "+3.0 %" compares two VIX models with each other** (M2 vs B2). It is not a comparison with the panel's baseline.
- **Adding VIX made the baseline worse**, on both instruments (out-of-sample loss, 2015–2025, from `qc_gex/gex_results.json`):

  | ES | Loss | vs B1 |
  |---|---|---|
  | B1 = 10-day mean, calibrated | 0.2093 | — |
  | B2 = B1 + VIX | 0.2145 | −2.5 % (worse) |
  | M1 = B1 + gamma | 0.2057 | +1.7 % |
  | M2 = B2 + gamma ("ES + VIX gamma") | 0.2081 | **+0.6 %** |

  (NQ: B1 0.1906, B2 0.1937, M2 0.1922: also worse than B1.) The B2/M2 rows exclude 11 days with no VIX, so the comparison with B1 is close but not exact.
- **So on the data already seen, the ES + VIX gamma model beats the plain 10-day baseline by only about 0.6 %.** The best ES model was gamma *without* VIX (+1.7 %, p 0.13, INCONCLUSIVE).
- **The 2015–2025 ES data cannot test this again.** Anything that "passes" there was selected after looking. A fair test needs instruments or dates that have not been examined.
- **Prior: low.** Even a pass is worth about 1–2 % better range estimates, for ES-family products only (NQ was rejected). Live use would also need a daily SPX gamma feed at $0, which NEXA does not have (no datafeed scraping, decision 8a71eb1).

## 1. Question
Does SPX naive net gamma (as a 252-day rank), added to the 10-day mean range and the prior VIX close, forecast the RTH range of S&P-family index futures better than the **plain calibrated 10-day mean the panel uses today**, on data NEXA has not compared with gamma before?

## 2. Data (QuantConnect free node, the user's website login; reads data only)
- **Fresh targets, never compared with gamma or VIX:**
  - **YM** (E-mini Dow) continuous: **binding**. YM prices were used before only for H-HOUGAARD (pre-open breakouts) and H-SWING (daily trend), never for ranges vs gamma.
  - **RTY** (E-mini Russell 2000) continuous, which starts on QC in 2017-07: **secondary**.
  - **ES 2026-01-02 → the end of QC data** (≈ 2026-07-21, ≈ 135 days): **holdout, descriptive only** (too few days for a verdict).
- **Futures:** minute bars, `BACKWARDS_PANAMA_CANAL`, open-interest roll, the same settings as `qc_gex/main.py`. RTH range = max high − min low of the bars ending 09:31 … 16:00 ET. Days with fewer than 300 RTH bars are excluded (counted).
- **Gamma:** the SPX net GEX already logged and hash-checked by H-GEX-RANGE (`qc_gex/runlogs/gex_2012…2025.txt`), joined by date. **No new 2012–2025 option reads.** For 2026, the frozen `qc_gex/main.py` runs once with `YEAR = 2026` (the only line that changes, as designed).
- **VIX:** prior-day VIX close. The new QC code requests history so that the first day of each chunk also has VIX (the H-GEX-RANGE gap).
- **Known overlap:** YM and RTY move with ES (daily ranges are highly correlated). This is a replication on related markets, not a fully independent test. That is why the bar stays strict (§5).

## 3. Features (identical to H-GEX-RANGE; reuse its code)
- **GEX_t:** Σ OI × Γ × 100 × S² × 0.01 × (+1 call, −1 put), SPX + SPXW chains as of the prior close.
- **GEXrank_t:** percentile of GEX_t within its trailing 252 trading days (prior data only).
- **Base_t:** mean RTH range of the previous 10 complete sessions of *that* instrument (the v6 panel rule).
- **lnVIX_t:** ln(VIX close of day t − 1).

## 4. Models and evaluation (walk-forward, no look-ahead)
- Target y_t = ln(RTH range_t).

  | Model | Definition | Role |
  |---|---|---|
  | B1 | a + b · ln(Base_t) | **The baseline to beat** (the panel, calibrated) |
  | **M2** | a + b · ln(Base_t) + d · lnVIX_t + c · GEXrank_t | **The test** ("gamma + VIX model") |
  | B2 | a + b · ln(Base_t) + d · lnVIX_t | Secondary |
  | M1 | a + b · ln(Base_t) + c · GEXrank_t | Secondary |
  | B0 | ln(Base_t) | Secondary (the raw panel) |

- **Walk-forward:** ordinary least squares refitted once a year on all prior data of that instrument (from its first day with a full 252-day gamma rank).
  - YM: first fit 2013–2014, **out-of-sample 2015–2025 (11 years)**.
  - RTY: first fit 2018-07 → 2019, out-of-sample 2020–2025 (6 years).
  - ES 2026: fitted on ES 2013–2025, forecasts 2026.
- **Loss:** squared error of ln(range) per day. All models are scored on the same days (days missing VIX or gamma are dropped from every model).
- **Primary statistic:** % reduction in pooled out-of-sample loss, **M2 vs B1**.
- **Significance:** Diebold–Mariano test on the daily loss difference, Newey–West (5 lags), one-sided.

## 5. Verdict (one binding trial: YM)
- **VALIDATED:** all of
  - M2 reduces out-of-sample loss vs B1 by **≥ 2.0 %**;
  - Diebold–Mariano p **≤ 0.025** (kept strict because the idea was picked after seeing a secondary result);
  - the reduction is > 0 in **≥ 7 of 11** years;
  - the pooled gamma coefficient c is **negative**.
- **REJECTED:** reduction ≤ 0.
- **INCONCLUSIVE:** otherwise.
- **Reported, no verdict effect:** RTY with the same statistics; the ES 2026 holdout (reduction and sign only); M1 vs B1, B2 vs B1, M2 vs B2; per-year reductions; actual ÷ forecast range by GEXrank quintile, in points.

## 6. Use of the result
- **VALIDATED:** gamma + VIX *may* enter the expected-range line **for ES/MES/YM only** (NQ/MNQ stays on the 10-day mean). Live use still needs a daily SPX gamma feed at $0. That is a separate decision; nothing is bought.
- **REJECTED / INCONCLUSIVE:** the gamma line is closed for range forecasting. The panel keeps the 10-day mean.
- **Either way:** this is a volatility forecast, not a trading edge and never a direction signal.

## 7. Multiple testing
- 1 binding trial (YM); RTY and ES 2026 are descriptive. Ledger ≈ 188 → ≈ 189.

## 8. Code, tests, freeze (after approval)
- **`qc_gexvix/main.py`:** logs per day the YM and RTY RTH ranges and bar counts, plus the prior VIX close. No options, so it is fast. Year chunks are sized to stay under QC's 10 KB log limit (expected 3–5 backtests). Reads data only; no orders.
- **2026 gamma:** the frozen `qc_gex/main.py` with `YEAR = 2026` (editor hash checked; the YEAR line is the only change).
- **`gexvix_stats.py`:** imports the GEX, rank, base, walk-forward and Diebold–Mariano functions from `gex_stats.py` (no copies), adds the M2-vs-B1 comparison and the verdict.
- **`test_gexvix.py`:**
  - date join of the gamma logs with the new range logs;
  - VIX present on the first day of a chunk;
  - all models scored on the same days;
  - verdict thresholds;
  - a planted effect (synthetic gamma that shrinks the range must read VALIDATED; noise must not);
  - log budget.
- **Gates:** tests pass → hashes recorded → one-month probe (checks that YM/RTY bars exist, the VIX first-day fix works, the runtime, and the end date of QC data; the probe's ranges are not looked at) → QC editor hash checked before every run → one run per chunk, no re-runs.
- **Session budget:** logs ≤ 2 KB summaries where possible; logs saved to files, never pasted into the chat.
