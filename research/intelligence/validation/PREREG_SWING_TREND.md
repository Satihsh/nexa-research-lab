# PRE-REGISTRATION H-SWING: daily trend-following on diversified CME futures (QuantConnect)

**Status: BINDING.**
- User approval 2026-10-18: "Start the daily swing trend test pre-registration".
- **Written before any data was read for this hypothesis.**

**Why this test:**
- Every intraday rule from the video sources has failed pre-registered testing: OFC1, OFC1R, H-ORB30L, T1, T2a, CFT, H-FPT-REV.
- The verified traders in batch 10 hold for days to months and follow trends:
  - Larry Williams: "the problem with intraday is purely mathematical";
  - Marci Silfrain: trend trades held up to ~3 months, ≤ 50 % WR;
  - Kevin McCormick: 3–5 day swings on daily bars;
  - Patrick Nill: 4 h–3 days.
- Longer holds cut the cost per unit of move.
- The best-documented long-horizon rule family is **time-series momentum / trend-following**:
  - Moskowitz, Ooi & Pedersen 2012, *JFE*;
  - Hurst, Ooi & Pedersen 2017, "A Century of Evidence on Trend-Following";
  - the Turtle rules (Covel; SRC already in the KB).

**Prior: low to moderate.**
- NEXA's C2 (FX + gold TSMOM on Pepperstone CFDs, 2000–2026) was REJECTED net.
- Trend-following is widely reported to have been weak in 2011–2018.
- **This test differs from C2:**
  - CME futures, not CFDs (no swap);
  - a 20-market, 6-sector universe instead of 8 FX/metal pairs;
  - the period 2010 → 2026.

**Practical constraint (stated now, not a verdict input):**
- Daily swing positions are held overnight. Apex prohibits "holding open trade positions through the market close" (`APEX_RULES_SNAPSHOT_2026-10-18.md`), so **this cannot run on that prop account**.
- It would need an own futures account with micro contracts.
- User rule (memory, 2026-10-14): never personal or borrowed capital until a strategy has passed tests **and** a forward demo. A VALIDATED result here leads at most to a forward paper/demo check, nothing else.

**Not tuned.** Every number is taken from the cited sources or fixed here before data.

## 1. Data, universe, clock
- QuantConnect AlgoSeek US futures, **daily** bars; continuous front contract by open interest (`DataMappingMode.OPEN_INTEREST`), `DataNormalizationMode.BACKWARDS_RATIO`; clock America/New_York.
- **Universe U20 (primary), 6 sectors:**

  | Sector | Markets |
  |---|---|
  | Equity indices | ES, NQ, YM, RTY |
  | Metals | GC, SI, HG |
  | Energy | CL, NG |
  | Currencies | 6E, 6J, 6B, 6A, 6C |
  | Rates | ZN, ZB, ZF |
  | Grains | ZC, ZS, ZW |

  - Each market enters when it has ≥ 252 + 60 valid daily bars. RTY data starts later than the rest; it simply joins when it qualifies.
- **Period:**
  - data from 2009-01-01;
  - **evaluation from 2011-01-03 → the last complete day at run time**;
  - one run, done once.
- **Daily return of market i:** r_{i,t} = C_t / C_{t−1} − 1 on the back-adjusted close. The roll gap is removed by the ratio adjustment; roll costs are charged separately (§4).

## 2. Primary rule P: time-series momentum (Moskowitz–Ooi–Pedersen)
- **Decision** at the close of the **last trading day of each month** (per market). The new weight earns returns from the **next** trading day's close-to-close return onward (one-day implementation lag; no same-day fill).
- **Signal:** s_i = sign(ln C_t − ln C_{t−252}). It is 0 if exactly 0 or if the history is too short.
- **Volatility:** EWMA of daily squared returns, centre of mass 60 days (δ = 60/61), data ≤ t, annualised ×252: σ_i.
- **Weight:** w_i = s_i · min(3, 0.40 / σ_i). This targets 40 % per market, as in MOP 2012, with a 3× cap.
- **Portfolio daily return:** R_t = (1 / N_t) · Σ_i w_i · r_{i,t}, where N_t is the number of markets with a valid weight that day. Equal risk across markets.

## 3. Declared secondary variants (same run; reported, never substituted)
- **V-DON (Turtle System 2, Covel / Faith):**
  - Daily decision at the close.
  - **Long entry** when the close > the highest high of the prior 55 days. **Long exit** when the close < the lowest low of the prior 20 days. Shorts mirror this.
  - While in a position the sign is kept; otherwise the market is flat. The signal flips only through an exit followed by a new entry.
  - Weight = s · min(3, 0.40/σ); position size recomputed monthly (at month-end), sign changes applied daily. One-day lag as in P.
- **V-MA:**
  - s = sign(SMA50 − SMA200) of the close, checked daily.
  - Weight as in P; size refreshed monthly, sign changes applied daily. One-day lag.
- **V-IDX:** P restricted to **ES and NQ only**, the markets the user knows (micros MES / MNQ exist).

## 4. Costs (charged in return units at each weight change and each roll)
- **Per market, round-trip cost in index points:**
  - c_i = k ticks × tick size + commission;
  - commission = $2.50 per contract round trip ÷ the contract multiplier (point value);
  - tick size and multiplier are read from QC SymbolProperties at run time.
  - **S0: k = 1, S1: k = 2 (primary), S2: k = 4.**
- **Trade cost in return units:**
  - at each rebalance: |Δw_i| · (c_i / 2) / C_t (half the round trip per side traded);
  - **at each roll** (mapped-contract change) while w_i ≠ 0: |w_i| · c_i / C_t (close the old contract and open the new one).
  - Costs are subtracted from that day's market return before averaging into R_t.

## 5. Statistics and verdict
- **Primary statistic:** the mean daily net portfolio return of rule P at S1, 2011-01-03 → end, also reported annualised, with the annualised Sharpe.
- **Inference:**
  - moving-block bootstrap of daily returns (block 20, B = 2,000, **seed 20261018**);
  - 95 % percentile CI for the mean; one-sided p.
- **Stability:** 4 equal consecutive time blocks.
- **Verdicts (same structure as earlier tests):**
  - **VALIDATED (G4):** mean > 0, CI lower bound > 0, ≥ 3 of 4 blocks > 0, and ≥ 36 months of evaluation;
  - **REJECTED:** mean ≤ 0;
  - **INCONCLUSIVE:** otherwise.
- **Drift control (reported; not a verdict input):**
  - **LONG-ONLY benchmark:** same markets, weight +min(3, 0.40/σ), same costs.
  - The difference P − LONG gets its own block-bootstrap CI.
  - A positive P driven only by equity drift would show up here.
- **Also reported:**
  - per-year and per-sector net contribution;
  - S0/S2 means;
  - turnover and roll share of costs;
  - max drawdown; skew;
  - **share of positive days and of positive months** (the user's "green days" goal; expected to be ~50 % for trend-following);
  - longest losing month streak;
  - the 2022 contribution alone (a known trend year);
  - P without 2022.
- **Feasibility table (descriptive):** for each market, the micro contract's notional and the smallest account at which a 1-micro position equals the rule's 40 %-vol weight / N. This shows the capital the rule would actually need with micros (MES, MNQ, MYM, M2K, MGC, SIL, MHG, MCL, M6E, M6A, M6B…).

## 6. Multiple testing
- H-SWING counts as **4 trials** (P, V-DON, V-MA, V-IDX).
- Cumulative ledger before this test ≈ 157 (after H-FPT-REV). Report the descriptive DSR of P at 4 and at ~161 trials.

## 7. Code, freeze, use
- Algorithm `qc_swing/main.py` (reads data only; no orders). Unit tests `test_swing.py` on synthetic series:
  1. sign / lookback;
  2. EWMA volatility and the weight cap;
  3. month-end decision and one-day lag;
  4. Donchian entry/exit state machine;
  5. MA cross;
  6. cost charging at rebalances and rolls;
  7. the portfolio average over active markets;
  8. bootstrap / verdict.
- Tests must pass before the code is hashed into PREREG_HASHES.txt. The QC editor hash is verified before the run. Output: `NEXA_SWING_RESULT` JSON in the log.
- **Use of the result:**
  - REJECTED or INCONCLUSIVE closes daily trend-following on this universe for now.
  - VALIDATED leads only to:
    - (a) a pre-registered forward paper check on new data (2026-07 → live);
    - (b) a capital-feasibility review with the user.
  - No live trading, no purchase, no personal capital follows from this test.
