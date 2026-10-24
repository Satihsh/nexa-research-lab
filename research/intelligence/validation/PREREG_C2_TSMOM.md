# PRE-REGISTRATION C2: daily FX/gold time-series momentum (TSMOM)

**Status: BINDING.**
- Approved by the user 2026-10-11: "Approved, use option (a) and pre-register C2".
- Written before any C2 outcome is computed. The SHA-256 is recorded in `PREREG_HASHES.txt`.
- **Running C2 needs a separate go-ahead** (implementation, G1 unit tests, code hash, then discovery → validation → holdout, each once).

It inherits only the general rules of `PREREG_OF_COMMON.md`: no post-hoc changes, numbered deviations, bootstrap/BH/verdict conventions. **Data, clocks, splits and costs are defined here** (D1 data, not M1).

## 1. Hypothesis, sources, disclosure

**Claim.** The sign of an instrument's trailing 12-month return predicts its next-month return (time-series momentum). A volatility-scaled long/short portfolio earns a positive return net of costs, beyond what persistent drift or random switching would give.

**Sources:**
- Moskowitz, Ooi & Pedersen (2012, *JFE*, "Time series momentum"), whose evidence includes currency futures.
- Menkhoff, Sarno, Schmeling & Schrimpf (2012, *JFE*), on currency momentum (cross-sectional; supporting only).
- Internal: KB backlog H-TSMOM-TANH; `STRATEGY_CANDIDATE_RANKING.md` rank 2.

**Differences from the source design (stated, not hidden):**
1. **Spot price returns, not futures excess returns.** Carry (the interest differential) is not in the signal or the return. Its cost side enters only through the swap convention in §4.
2. **8 instruments** (§2), not a 58-futures cross-section. Diversification is far lower, so the expected Sharpe is lower than the published portfolio's.
3. Retail CFD costs and an always-on catastrophe stop (NEXA's no-missing-stop invariant).

**Disclosure (seen data):**
- No project analysis has computed monthly or 12-month momentum returns on these D1 series.
- Related exposures:
  - the H1 strategy factory found trend families ≈ drift (TrendLock; Pepperstone H1, recent years);
  - 8E Donchian (intraday) was contradicted;
  - T2 used daily realised volatility 2017–2026 for 4 symbols.
- The author knows broad market history (e.g. the gold rise 2019–2026, the USD rallies of 2014–15 and 2022). The long-only and placebo benchmarks (§5) exist to control drift.
- A D1 data-quality check was done before writing (structure only): all 8 series cover 2000-01-03 → 2026-09-25 with full weekday coverage, a max gap of 4 days, and no invalid OHLC. Weekend stub rows (42–600 per symbol) are dropped.

## 2. Data, universe, clock

- **Data:** Pepperstone D1, `filesnexa/NEXA/data/pepperstone/PEPPERSTONE_<SYM>_D1.csv` (bid OHLC, server-day bars, NY+7). Weekend rows are dropped.
- **Universe U8 (primary):** EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD, USDCAD, USDCHF, XAUUSD.
  - **NEXA4 (secondary):** EURUSD, GBPUSD, USDJPY, XAUUSD.
- **Instrument direction** is as quoted: "long" = long the base currency or metal. TSMOM is direction-symmetric, so quote conventions do not bias the signal.

## 3. Strategy rules (exact)

**Decision and execution timing**
- **Decision time:** the close of the **last server trading day of each month** (primary; *monthly*).
- **Execution:** the **open of the next server trading day**. A decision never trades on the bar that produced it.

**Signal**
- s_i = sign(ln C_t − ln C_{t−L}), with **L = 252** trading days (primary; 12 months).
- s = 0 (flat) if the log return is exactly 0 or fewer than L + 60 prior bars exist.

**Volatility and weight**
- **Volatility:** EWMA of daily squared log returns (close to close), centre of mass 60 days (δ = 60/61), using data ≤ t. σ_i = √(261 · EWMA variance).
- **Weight (notional as a fraction of equity):** w_i = s_i · min(3, 0.10 / σ_i). This targets 10 % annualised volatility per instrument, with leverage capped at 3×.
- **Portfolio daily return:** R_t = (1/N_active) · Σ_i w_i · r_{i,t}.
  - r_{i,t} is the instrument's simple daily return.
  - On the execution day, r is measured from the open (C/O − 1). Otherwise it is close to close.
  - N_active is the number of instruments with a valid signal.

**Catastrophe stop (per instrument; always attached)**
- The stop distance is 3 · σ_i(daily) · √21 · P_entry (three monthly sigmas).
- **Long:** stopped if a daily low ≤ P_entry − distance.
- **Short:** stopped if a daily high + spread ≥ P_entry + distance.
- **Fill:** at the stop level, or at the open if the day gaps through it. The instrument is then flat until the next rebalance.

**Rebalance and cost**
- At each rebalance, only the change |Δw| is traded (turnover).

## 4. Costs and swaps (option (a), the NEXA V2/8E convention)

**Trading costs per unit of notional traded (one side):**
- **Commission:** half of USD 7 per lot round trip, converted to bp of notional:
  - USD-base pairs: 0.35 bp;
  - XXXUSD: 7/(2·1e5·P_USD)·1e4;
  - XAUUSD: 0.035/P·1e4 (USD 0.07/oz round trip).
- **Spread:** half of a **fixed assumed spread** (no historical spread exists for most symbols and years). These are about twice typical raw-account spreads (an assumption, U2):
  - EURUSD 0.4 pip; GBPUSD 0.8; USDJPY 0.5; AUDUSD 0.6; NZDUSD 0.9; USDCAD 0.9; USDCHF 0.9;
  - XAUUSD 0.30 USD.
- **Slippage stress per side:**
  - **S0** = 0 bp;
  - **S1** = 0.5 bp (decides);
  - **S2** = 1.0 bp (reported);
  - a **2× total-cost** stress is also reported.

**Swaps (option (a)), exactly as V2/8E:**
- `contracts.json` `swap_long` / `swap_short` in **points per lot per server rollover**.
- **Charges only, never credits**, because the 2026-09 snapshot is not the historical rate.
- Per held unit of notional per rollover: charge = max(0, −swap_pts) · point / price.
- **Rollover weights** per server trading day held overnight: Mon 1, Tue 1, **Wed 3**, Thu 1, Fri 1 (7 per week; `swap_rollover3days = 3`).
  - NOTE: the 8E helper `_rollovers` also counts Sat/Sun midnights. C2 does not, to match broker practice. This difference is disclosed.

**Reported alongside (never decides):**
- **ex-swap** results;
- **symmetric snapshot swaps** (charges and credits);
- swap × 2.

## 5. Benchmarks and nulls

- **N0 zero:** the net mean must be > 0.
- **N1 long-only vol-scaled:** the same sizing, stop and costs with s_i = +1 always. This measures how much a result could come from persistent drift (e.g. XAU).
- **N2 circular-shift placebo (primary null):**
  - for each replicate (1,000; seed 20261011), each instrument's monthly signal series is rotated by an independent random offset of 24 … (T − 24) months, with wrap-around;
  - sizing, stops and costs are recomputed;
  - this preserves each signal's persistence and turnover but breaks its timing;
  - p_N2 = (1 + #{placebo mean net ≥ observed}) / 1,001.
- **N3 matched-switching random signs (reported):** a two-state Markov sign process per instrument with the observed flip probability; 1,000 replicates.

## 6. Splits, sample requirements, statistics

**Splits:**
- **Evaluation starts** at the first month with valid signals (expected ≈ 2001-03 after the L + 60 warm-up).
- **Discovery:** start → 2012-12.
- **Validation:** 2013-01 → 2019-12.
- **Holdout:** 2020-01 → 2026-09-25 (opened once).
- **Prospective:** 2026-10 onward, accumulated, not evaluated without approval. No 2027 data.

**Unit:** monthly portfolio net return (decision month to decision month), built from daily returns.

**Minimum samples:**
- holdout ≥ 60 months (≈ 81 available);
- pooled ≥ 250 months (≈ 307 available);
- otherwise INSUFFICIENT-N.

**Uncertainty:** moving-block bootstrap over months (block 12, B = 2,000, seed 20261011). One-sided p as in COMMON §C8.

**Trial grid (counted):**
- L ∈ {21, 63, **252**, COMBO = sign of the mean of the three signs};
- rebalance ∈ {**monthly**, weekly (last server trading day of each week)};
- universe ∈ {**U8**, NEXA4};
- = **16 cells**. Primary = (252, monthly, U8).
- BH q = 0.10 over the 15 secondary cells (discovery p).

**DSR:** `nexa_robust.deflated_sharpe` (read-only import) on the primary monthly net (S1) returns, with n_trials = 16 and var_sr_trials = the variance of the 16 cells' monthly Sharpe ratios.

## 7. Acceptance criteria (all required ⇒ research candidate, RESEARCH_GATE G4)

1. **Discovery:** the primary net (S1) monthly mean > 0, one-sided p < 0.05.
2. **Validation and holdout:** net (S1) monthly means > 0.
3. **Pooled:** the 95 % CI lower bound of the net (S1) monthly mean > 0.
4. **Placebo:** p_N2 < 0.05 (pooled), **and** the pooled net Sharpe > the long-only N1 net Sharpe.
5. **Convention robustness:** the pooled **ex-swap** net mean > 0, and the pooled net mean stays > 0 under **swap × 2**.
6. **Breadth:** ≥ 5 of 8 instruments with a positive pooled net contribution. No single instrument contributes > 50 % of pooled net P&L.
7. **Stability:**
   - no calendar year > 50 % of pooled net P&L;
   - the holdout net (S1) mean remains > 0 under the **2× total-cost** stress.
8. **DSR ≥ 0.95** at N = 16.

**Verdicts:**
- **REJECTED** if the pooled net (S0) mean ≤ 0, or the discovery and holdout signs are opposite.
- **SUPPORTED** (research candidate) if all of §7 hold.
- **INCONCLUSIVE** otherwise.
- No re-run with altered parameters under this ID.

## 8. Reported (never decides)

- Annualised Sharpe, max drawdown, Calmar, turnover/yr, and stop frequency.
- Per-instrument and per-year contributions.
- Long-only and N3 results; ex-swap and symmetric-swap variants.
- Rolling 36-month Sharpe.
- **R translation for NEXA:** the monthly net return expressed per 1 % of equity at risk to the catastrophe stops.

## 9. Implementation plan (after approval to run)

- **New script** `c2_tsmom.py`. It reuses `of_common` (bootstrap, BH, verdict, year shares, `_f`) and `nexa_robust.deflated_sharpe`, both read-only.
- **New unit tests:**
  1. signal causality (no data after t);
  2. EWMA centre of mass;
  3. rollover weights (Wed ×3, no weekend nights);
  4. charges-only swap;
  5. turnover cost;
  6. catastrophe stop including a gap;
  7. circular-shift placebo preserves turnover.
- **Order:** code hashed before discovery; discovery → validation → holdout, once each.

## 10. Unresolved assumptions and missing data

| # | Item | Effect | Treatment |
|---|---|---|---|
| U1 | **No historical swaps** (option (a): a 2026 snapshot, charges only) | Overstates today's USD-carry charges for low-rate eras; omits credits. The direction of the bias is conservative for net P&L | Ex-swap / symmetric / ×2 variants reported; criterion 5 |
| U2 | **No historical spreads** for most symbols and years; fixed assumed spreads | Costs may be wrong in 2000–2010 (wider) or recently (narrower) | S1/S2 and 2× total-cost stress; turnover is low |
| U3 | **Spot vs futures excess return** (carry excluded) | Deviates from the literature's construction; carry and momentum interact | Disclosed. Cannot be fixed without rate data (option (b) declined) |
| U4 | Pre-2010 D1 history provenance (broker-supplied history) | Possible vendor stitching | Quality check passed (no gaps > 4 d, no invalid OHLC); per-split results reported |
| U5 | Commission USD 7/lot assumed for all symbols, incl. XAU at USD 0.07/oz | ±0.1 bp | Verify against real fills when available |
| U6 | **Production fit:** a monthly, multi-instrument, vol-scaled portfolio is outside the current EA design (4 symbols, intraday, 1 % fixed risk per trade, exposure caps) | Deployment would need a new design, approved separately, plus Risk Engine review (exposure cap, correlation cap) | Only after G4 plus approval |
