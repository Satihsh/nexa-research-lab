# PRE-REGISTRATION H-ORB30L-REPL: out-of-sample replication + forward log of the frozen H-ORB30L-NQ rule

**Status: BINDING.**
- Approved by the user 2026-10-15: "approved, QuantConnect OOS + Dukascopy forward log". The user also decided **no spending** (the Databento option was declined).
- Written **before** any statistic of the rule has been computed on any data outside 2023-02-18 → 2026-10-10.
- In-sample result (`HORB30L_REPORT.md`, a4d12ad): INCONCLUSIVE 6/7. +0.058 R at S1, CI [+0.002, +0.123]; DSR failed (116 trials).
- **This is a confirmation of ONE frozen rule, not a search.** Nothing is tuned. No variant may replace the rule after results.

## 1. The rule (frozen; identical to `horb30l_nq.py` sha 7d4095bc, `PREREG_HORB30L_NQ.md` §3)

- **Range:** 09:30–09:59 ET.
- **Breakout:** the first 5-min candle (grid from 10:00) whose close > range high, closing by 11:30.
- **Entry:** long at the next 1-min open.
- **Stop:** the range low.
- **Target:** entry + 1R, filled only on a 1-tick trade-through.
- **Time exit:** the 15:29 bar close.
- **Same-bar and gap rules:** if stop and target are hit in the same bar → stop; a gap through the stop fills at the open; the entry bar checks the stop only.
- **Cost floor:** skip if R < 10 points.
- **Cost:** S0 / **S1** / S2 = 1 / **2** / 3 points per round trip.
- **N2 beta control:** the same bracket entered at the 10:00 open on every day.
- **Engine:** the shared engine semantics are `DEVIATIONS_HORB30L_HVAR.md` I-1…I-11.

## 2. Part A: QuantConnect out-of-sample (OOS) backtest

**Data:**
- QuantConnect cloud CME **E-mini Nasdaq-100 (NQ)** minute bars, front month by open interest, raw (unadjusted) prices.
- From the first day QuantConnect provides NQ minute data to **2023-02-17** (the day before the in-sample data began). Not one in-sample day is used.

**Clock and days:**
- America/New_York.
- A day is used only if all 30 range bars and the 15:29 bar exist (data-defined; this drops holidays and early closes).

**Implementation:**
- One private QuantConnect project.
- The algorithm only records each day's 1-min OHLC bars (09:30–15:59 ET) and applies a line-for-line port of the frozen engine. No QuantConnect order fills or slippage model is used.
- Per-day outcomes are written to the QuantConnect ObjectStore (no raw price data leaves QuantConnect), then read back through a research notebook.
- **Statistics:** computed locally with the same code as in-sample (`horb30l_nq.boot`, block 20, B = 2,000, seed 20261015).
- **Pre-flight:** one short smoke backtest of **at most 5 trading days in 2023-03** (in-sample days only) checks that the port reproduces the local engine's outcomes on those same days. Mismatch → fix the port and re-check (in-sample only). The OOS backtest itself runs **once**.

**Primary:** mean net R per trade at S1, OOS. Moving-block bootstrap over days, one-sided p.

**Acceptance (all required for "REPLICATED"):**
1. Mean S1 R > 0 **and** 95 % CI lower bound > 0.
2. Primary mean R − N2 mean R > 0.
3. ≥ 60 % of calendar years positive, and no single year > 25 % of total net R.
4. ≥ 300 trades (else INSUFFICIENT-N).

**Verdict:**
- **REPLICATED** if all pass.
- **FAILED** if the S1 mean ≤ 0.
- **OTHERWISE NOT REPLICATED.**
- Reported but not decisive: the 2R target, per-year table, S0 / S2, the cost-floor count by year, and the user-goal $ table at $2/point (MNQ).

**Note fixed in advance:** costs are in points (ticks), so in early years with lower NQ prices the 2-point cost is a larger share of each move. This makes the test conservative. It is not adjusted.

## 3. Part B: Dukascopy forward log (prospective)

**Data:**
- Dukascopy `USATECH.IDX/USD` (Nasdaq-100 CFD) M1 **bid and ask** via the read-only Dukascopy connector, at most 500 candles back.
- Read once per day, after the NY session: target window 05:00 MYT, i.e. 15:30–17:50 ET.
- Raw candles are saved to `research/intelligence/validation/forward_horb30l/raw/<date>.json` and hashed. Nothing is ever placed or traded through the connector.

**Rule:** §1, on **mid prices** (bid + ask) / 2, with S1 cost 2.0 points.
- Also reported: an executable version (entry at ask, exits at bid, no extra cost).

**Days:**
- Every NY trading day from **2026-10-15** (the first session after this freeze) onward.
- A day whose candles were not read in time is recorded as `not_observed`, never filled in later.
- A day with any missing range bar or 15:29 bar → `missing`.

**Evaluation:**
- Monthly descriptive updates.
- **One formal look at 100 forward trades:**
  - **BROKEN** if the forward mean R is significantly *below* the in-sample +0.058 R (one-sided bootstrap p < 0.05);
  - otherwise **CONSISTENT**. The forward mean and CI are reported either way.
- 100 trades cannot by themselves prove a +0.06 R edge (SE ≈ 0.085 R). Part A carries the statistical weight; Part B checks that live behaviour matches.

## 4. What follows

- **A = REPLICATED and B = CONSISTENT:** H-ORB30L becomes a research candidate for an ATAS alert + demo execution, then at most one prop evaluation (user rule: $0 until proven).
- **A fails:** the rule is closed. The forward log stops after notice to the user.
