# PRE-REGISTRATION H-GEX-RANGE: does dealer net gamma improve the forecast of how far NQ / ES will move today?

**Status: BINDING.** User approval 2026-10-23 (chat): "approve H-GEX-RANGE. Freeze it, build and test the code, run the one-month probe, then the yearly QuantConnect runs."
- Requested 2026-10-23 (chat): "After H-SK28 finishes, write the H-GEX-RANGE pre-registration (does SPX/NDX net gamma improve the expected-range forecast) for my approval."
- Source of the idea: repo review S85–S97 (`../sources/REPOS_2026-10-23_review.md`). QuantConnect's US Index Options data (SPX, NDX; 2012+; open interest; free in cloud backtests) unblocks the order-flow KB claims CL-032 / CL-038 (gap GAP-D08).
- **Written before any options data has been loaded.**

## 0. Claim, why it matters, prior
- **Claim (literature):** when option market makers are net **long** gamma, their hedging dampens moves; when **short**, it amplifies them.
  - Dim, Eraker & Vilkov (SSRN 4692190): market-maker net gamma is negatively related to **future intraday volatility** of the S&P 500.
  - Ni, Pearson, Poteshman & White (2021, RFS): the same sign, for single stocks.
- **Why NEXA cares:**
  - The v6 Risk & Range panel shows an **expected range** = the mean RTH range of the previous 10 sessions. It drives the stop and size lines.
  - A better forecast means better-sized stops. This is a **volatility** claim, never a direction call, so it fits the panel's "predictable things only" rule.
- **Prior: moderate that gamma relates to range; low that it adds much beyond the 10-day mean and VIX.**
  - Open-interest gamma has to *assume* who holds which side (the dealer-sign problem).
  - Recent volatility already carries most of the information.

## 1. Data (QuantConnect free node, the user's login; reads data only)
- **Options:**
  - QC "US Index Option Universe" (daily: contract list, open interest, QC-computed implied volatility and Greeks) for **SPX (incl. SPXW)** and **NDX (incl. NDXP/NQX)**;
  - everything **as of the prior trading day's close**. The build verifies the timestamp, and a test checks that day *t* only sees data dated ≤ *t* − 1.
- **Futures:** NQ and ES continuous (open interest, `BACKWARDS_PANAMA_CANAL`), minute bars. RTH range on day *t* = max high − min low of bars ending 09:31 … 16:00 ET.
- **VIX:** prior-day close of the VIX index from QC (secondary model only; if QC has no VIX series on the free node, the secondary is dropped and the drop is logged).
- **Period:** 2012-01 → 2025-12.
  - The first 252 trading days are warm-up for the gamma rank.
  - Days with missing option data or fewer than 300 RTH minute bars are excluded (counted).

## 2. Features (fixed now)
- **Naive net GEX** (the standard practitioner convention: dealers long calls, short puts), in dollars per 1 % move:

  GEX_t = Σ_contracts OI × Γ × 100 × S² × 0.01 × (+1 call, −1 put)

  using every listed contract of the root on the prior close. S = the underlying index close.
- **GEXrank_t:** percentile of GEX_t within its own trailing 252 trading days (0–1, prior data only).
- **Base_t:** mean RTH range of the previous 10 complete sessions (exactly the v6 panel rule).
- **Primary gamma source:** **SPX** for both NQ and ES (the deepest options market, and the one the cited papers use).
- **Secondary sources (reported, no verdict effect):** NDX for NQ; absolute gamma (Σ OI × Γ without the call/put sign); the raw GEX sign (positive vs negative day).

## 3. Models and evaluation (walk-forward, no look-ahead)
- Target y_t = ln(RTH range_t).
- **Models:**

  | Model | Definition | Role |
  |---|---|---|
  | B0 | ln(Base_t) | The panel as it is today (no fitting) |
  | B1 | a + b · ln(Base_t) | Calibrated baseline |
  | **M1** | a + b · ln(Base_t) + c · GEXrank_t | **The test** |
  | B2 | B1 + d · ln(VIX_{t−1}) | Secondary |
  | M2 | B2 + c · GEXrank_t | Secondary |

- **Walk-forward:** ordinary least squares refitted once a year on all data before 1 January; forecast that year.
  - First fit 2013–2014; **out-of-sample years 2015–2025 (11 years)**.
- **Loss:** squared error of ln(range) per day.
- **Primary statistic:** % reduction in mean out-of-sample loss, M1 vs B1, pooled over all OOS days.
- **Significance:** Diebold–Mariano test on the daily loss difference, Newey–West (5 lags), one-sided.

## 4. Verdict (two primary trials: NQ (binding), ES; Bonferroni α = 0.025)
- **VALIDATED (per instrument):** all of
  - M1 reduces out-of-sample loss vs B1 by **≥ 2.0 %**;
  - Diebold–Mariano p ≤ 0.025;
  - the reduction is > 0 in **≥ 7 of 11** OOS years;
  - the pooled coefficient c is **negative** (higher gamma → smaller range, the mechanism's sign).
- **REJECTED:** reduction ≤ 0.
- **INCONCLUSIVE:** otherwise.
- **H-GEX-RANGE overall** = the NQ verdict (the panel trades MNQ).
- **Also reported (no verdict effect):**
  - B0 vs B1 (is the panel's raw 10-day mean already well calibrated?);
  - B2 / M2 (does gamma still add anything once VIX is known?);
  - the NDX, absolute-gamma and sign variants;
  - per-year reductions;
  - actual ÷ forecast range by GEXrank quintile, in plain points, so the size of the effect is visible.

## 5. Use of the result
- **VALIDATED:** gamma *may* enter the panel's expected-range line. But using it live needs a **daily SPX open-interest/Greeks feed at $0**, which NEXA does not have yet. That is a separate data decision; nothing is bought. Until then the result is knowledge, not a feature.
- **REJECTED / INCONCLUSIVE:** the panel keeps the 10-day mean. Gamma stays out, and CL-032/038 are recorded as "tested, no added value".
- **Either way:** this is not a trading edge and never a direction signal. H-GEX-IM (last-30-minute momentum on negative-gamma days) is a separate idea and would need its own pre-registration.

## 6. Multiple testing
- 2 primary trials (NQ, ES); the secondary variants are descriptive. Ledger ≈ 186 → ≈ 188.

## 7. Code, tests, freeze (after approval)
- **`qc_gex/main.py`:**
  - one backtest per calendar year (QC's 10 KB log limit);
  - each day it logs one compact record: date, NQ/ES RTH range, SPX and NDX net GEX, absolute gamma, index closes, VIX, and missing-data flags;
  - reads data only, no orders.
- **`gex_stats.py`:** local, from the saved logs: Base_t, GEXrank_t, the walk-forward fits, losses, Diebold–Mariano, verdict.
- **`test_gex.py`** (synthetic, `run_tests.py`):
  - GEX formula and signs;
  - trailing rank with no look-ahead;
  - the 10-day base identical to the panel's `RangeGuide`;
  - RTH range from minute bars;
  - walk-forward refit dates;
  - Diebold–Mariano with Newey–West;
  - verdict thresholds;
  - record encode/decode;
  - log budget;
  - a planted-effect test (synthetic data where gamma does shrink the range must read VALIDATED, and pure noise must not).
- **Gates before any real run:**
  - tests pass, then hashes are recorded;
  - a **one-month probe** on QC confirms the chain size, the timestamp lag and the runtime;
  - the probe's numbers are not looked at for the verdict;
  - the QC editor hash is checked before every run.
- **One run per year-chunk, no re-runs.**
