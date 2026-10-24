# NEXA × Pepperstone: Final Audit (2026-09-27)

All figures come from files in this repository. Pepperstone data is kept separate from the MetaQuotes/IC Markets data and is prefixed `PEPPERSTONE_`. Nothing was traded. `MTM_ENABLE_TRADING=false` and `MTM_ENABLE_EXEC=false` throughout.

## A. Pepperstone connection status
**CONNECTED, READ-ONLY.**
- Account `61603218`, Pepperstone-Demo (Pepperstone Group Limited). DEMO, hedging mode, USD, 1:200.
- Balance and equity $50,000.00. 0 positions, 0 orders.
- Bridge `bridge.env`: login 61603218, trading and exec flags false. The old account 5055943373 is no longer referenced.
- Every data script aborts unless the attached account is exactly this demo.
- **Environment issue:** the interactive terminal dies without a log line shortly after starting, intermittently and more often under memory pressure (8 GB Mac, ~60 MB free). Tester-mode starts mostly succeed: about 1 in 4 died early and were re-run until verified.

## B. Exact symbol mapping
All NEXA basket symbols exist under **exact names with no suffix**. NEXA's hard-coded basket `{EURUSD, GBPUSD, USDJPY, XAUUSD}` is directly compatible, and **no adapter is needed**. XAGUSD is exact too.

Non-spot look-alikes that must NOT be used as substitutes: `XAUUSD-F`/`XAGUSD-F` (futures CFD), `GOLD-PERP`, `XAUTUSD`/`PAXGUSD` (tokens), plus `XAUEUR` and the other XAU/XAG crosses.

FX universe: 92 pairs (majors, crosses, exotics). List and specs are in `data/pepperstone/contracts.json` and `export2_status.json`.

| Symbol | Digits | Point/tick | Tick value | Contract | Min / step / max lot | Stops level | Filling |
|---|---|---|---|---|---|---|---|
| EURUSD | 5 | 0.00001 | 1.00 | 100,000 | 0.01 / 0.01 / 100 | 0 | IOC (2) |
| GBPUSD | 5 | 0.00001 | 1.00 | 100,000 | 0.01 / 0.01 / 100 | 0 | IOC |
| USDJPY | 3 | 0.001 | 0.636 (varies) | 100,000 | 0.01 / 0.01 / 100 | 0 | IOC |
| XAUUSD | 2 | 0.01 | 1.00 | 100 oz | 0.01 / 0.01 / 50 | 0 | IOC |
| XAGUSD | 3 | 0.001 | 5.00 | 5,000 oz | 0.01 / 0.01 / 50 | 0 | IOC |

## C. Historical coverage by symbol (measured, not inferred from folders)

| Symbol | D1 (Python API) | M1 in the Strategy Tester | M1 via Python API | Real ticks |
|---|---|---|---|---|
| EURUSD | 7,544 bars, 2000-01-01 → 2026-09-25 | loaded from ≥ 2023 for 2024+ tests (tester log: history data begins 1993 for GBPUSD) | last 99,998 bars only (maxbars cap), 2026-06-22 → 09-25 | 2,457,556, 2026-08-28 → 09-25 |
| GBPUSD | 7,533, 2000-01-03 → | same | 99,998 | 5,412,393 |
| USDJPY | 7,512, 2000-01-01 → | same | 99,998 | 3,449,033 |
| XAUUSD | 6,970, 2000-01-03 → | same | 99,998 (from 2026-06-16) | 10,837,582 |
| XAGUSD | 5,140, 2007-01-01 → | not tested | 99,998 | 4,179,770 |
| 91 FX pairs | D1 from 2000 (majors/crosses) to 2025 (USDAED, CNH crosses) | – | – | – |
| GBPCAD | **no D1 returned** (call failed; not retried beyond 5 attempts) | – | – | – |

The factory H1 set (tester export): 57.5k–60.6k bars per symbol, 2016-12-30 → 2026-09-25.

## D. Tick-data availability
**Real ticks exist only from 2026-08-28 (≈16:00 server time) onward** for every core symbol. The tester log confirms it: "ticks data begins from 2026.08.28". Real-tick modelling covered **96.8%** of window B's minute bars; the only gaps were on the first day. All earlier windows used **generated ticks from M1 bars** (Model 0), labelled as such. No real-tick claim is made for 2024-01 → 2026-08.

## E. Bid/ask/spread availability
- **Ticks:** bid and ask present on 100% of ticks, 0 crossed quotes. Pepperstone quotes raw spreads: zero spread on 84% (EURUSD), 21% (GBPUSD) and 9% (USDJPY) of ticks. Median and p95 spread: EURUSD 0 / 0.2 pip, GBPUSD 0.1 / 0.3 pip, USDJPY 0.3 / 0.5 pip, XAUUSD $0.12 / $0.17, XAGUSD $0.033 / $0.042.
- **Commission:** the tester charged **$3.50 per lot per side** (observed on NEXA's XAUUSD trade), so costs are spread plus commission.
- **M1 bars:** carry a spread field. Median in points is 0 for the FX majors, 10 for XAUUSD and 29 for XAGUSD.

## F. Data-quality findings (no data was altered)
- Across 96 D1 files and 5 recent-M1 files: **0 duplicate timestamps, 0 OHLC geometry violations, 0 non-positive prices, 0 non-monotonic times.**
- Intra-week gaps are the daily rollover (minutes), plus one metals gap of 3.5 h (2026-09-07 21:30 → 09-08 01:01).
- **Server time is EET/EEST.** The FX week opens Monday 00:01 server time, which is GMT+3 in summer. NEXA's fixed `InpGMTOffset=2` is therefore 1 h off during DST on Pepperstone too (**D-TZ, human decision pending**).
- The 3-year H1 chunks overlap by 20 bars, with 0 conflicting overlaps.
- **Self-inflicted:** requesting D1 for 92 FX pairs made MT5 download full M1 history. The Pepperstone base grew to ~24 GB and free disk fell to 6.7 GB. Nothing was deleted.

## G. MT5 tester configuration
- Terminal/MetaTester build 6230, Wine 11.1 on macOS.
- Expert `Advisors\NEXA_EA` (source sha `9d1e6aaf…`, the unmodified Stage 1 source, for the main batch). Chart M1. Deposit $50,000 USD, leverage 1:200.
- **Execution delay 250 ms** (the measured ping to Pepperstone LD1 was 251 ms; not ideal execution).
- **All NEXA inputs at defaults** (risk 0.30%, ceiling 1%, etc.).
- Window A: Model 0 (generated ticks), 11 calendar-quarter chunks. Window B: Model 4 (real ticks).
- A single 2.7-year run kills the terminal during data preparation, hence the chunking. Each chunk re-initialises the EA; any open position would be closed at chunk end (none were open at any chunk end).
- **Verification:** every chunk was accepted only on its own "Test passed" line and DNA reaching the window end (`reports/pepperstone/tester_verify.json`). **48/48 NEXA runs and 49/49 bar exports passed**, after up to 3 re-runs.

## H. NEXA test period
2024-01-01 → 2026-09-25 (2.7 years) for EURUSD, GBPUSD, USDJPY and XAUUSD. It starts in 2024 because NEXA's FOMC table begins there.

## I. Decisions
**3,927,131 DECISION rows** (EURUSD 994,279 · GBPUSD 993,855 · USDJPY 993,334 · XAUUSD 945,663).

## J. Trades
**1**: XAUUSD long, decision bar 2026-02-02 15:53. Details:
- 0.02 lots, 0.21% risk. Fill 4719.12 against 4719.38 intended.
- Commission $0.14 round trip.
- Broker result **−0.005R**. Label TIME_EXIT; MFE +1.46R, MAE −0.76R.

## K. NO_TRADE decisions
**3,927,130.** By reason family:

| Reason | Count |
|---|---|
| no qualified liquidity event | 2,820,364 |
| spread tax | 980,915 |
| FOMC window | 51,997 |
| insufficient target room | 33,748 |
| **portfolio currency exposure cap** | 21,081 |
| stop on wrong side | 13,735 |
| adversarial fail | 5,232 |
| margin usage | 49 |

**Root cause of near-zero trading (FACT from `NEXA_Risk.mqh`):** `capLots = InpMaxSameCurrencyNet × SYMBOL_VOLUME_MIN = 2 × 0.01 = 0.02 lots` per currency. At $50k equity a 0.30% risk trade is 0.1–0.5 lots, so every signal that reached sizing was blocked, except the XAUUSD trade whose wide stop sized it to exactly 0.02. Combined with the minimum-lot-versus-1%-ceiling rule, NEXA as configured can only trade within roughly **$100–$1,300 of equity** (it depends on stop width). This is a hard risk limit, so it was **not changed**, and the tester was **not** re-run at a smaller deposit to manufacture trades.

## L. Trade DNA status
- **Real Trade DNA exists**: 48 files, 3,927,134 rows, schema 1.0, ingests with 0 errors.
- All f00–f47 are finite. f19 `bprActive`, f46 `liqOrigin` and f47 `newsRiskActive` are constant in every file; f47 is expected, because the calendar is unavailable in the tester.
- Causality: 98.2% of DECISION rows have exactly a one-bar `decision_ts`→`write_ts` lag, and 0.5% have longer lags at session gaps.
- **Defect found and fixed:** 51,791 FOMC-veto rows carried the forming bar's timestamp. The EA now anchors them to the closed bar, and this was verified in the tester (0 violations). The batch DNA predates the fix; those rows are identifiable by reason `NO_TRADE_FOMC_*`.
- **Second defect fixed:** CLOSE rows journaled the entry price as `risk_dist`.
- Known D-EPOCH: FILL/CLOSE `decision_ts` = 1970, recovered by ingest.

## M. Feature parity status: **FAIL, narrowed to one subsystem**
**Three oracle defects were found on real data and fixed, with tests:**
1. ATR was Wilder, but MT5 `iATR` is a simple mean of true range (proven on 400/400 rows).
2. Higher-timeframe windows admitted the forming M5/M15/H1 bar, a look-ahead in the oracle.
3. The volState averaging window was wrong: it excluded the current ATR and took the oldest values.

**Full chronological parity on all four real-tick windows (112,688 rows):** every categorical feature matches except the **liquidity state machine (0.2–0.85% of rows)**. Trend and displacement edge cases occur in ≤ 6 rows per window. All continuous `displacementATR`/`spreadATRRatio` differences are within the Trade DNA's own precision (6 decimals plus float32). But the contract tolerance (abs 1e-9) is tighter than that precision, so the contract as written cannot pass on real data (**a contract defect, reported, not loosened**).

Correction on record: an earlier sampled-parity result was invalid for stateful features, because sampling breaks the state chain. It is kept as `PEPPERSTONE_PARITY_SAMPLED.json`, valid for stateless features only.

## N. OOS results
- **NEXA:** no OOS evaluation is possible with n=1 trade.
- **Strategy Factory:** one-shot holdout 2025-01 → 2026-09 for every family and symbol (table in `FACTORY_PEPPERSTONE_H1.md`). No family is promoted; holdouts are noisy and are never used for selection.

## O. Walk-forward results
Factory walk-forward 2020–24 (config re-chosen yearly on prior years): **0 of 25 families pass**. Best: XAUUSD trend_breakout +0.097R, CI [−0.028, +0.227], p=0.07, DSR 0.31. NEXA's own walk-forward is not possible (1 trade; validation gate FAIL: 1 < 200 episodes).

## P. Monte Carlo / robustness
- NEXA: **INSUFFICIENT_SAMPLE** (n=1). No Monte Carlo, bootstrap or cost-shock result is claimed.
- Factory: bootstrap CIs, STRESS/SEVERE cost reruns, PBO, DSR and cross-symbol BH-FDR are all in the factory JSONs. Nothing survives them.

## Q. Strategy Factory results
**No candidate, on Axiory XAUUSD (earlier) or Pepperstone ×5 (now).** Mean reversion and Camarilla fading are reliably negative. Trend rules on metals do not beat random entries.

## R. Model status
**No model trained.** Gate 9 code exists (veto-only meta-label, forward-only calibration, append-only registry), but validation FAILS (1 episode < 200). Calibration and drift: not applicable. Promotion state: **RESEARCH_ONLY**.

## S. Remaining blockers
1. **B-EXPOSURE-CAP (human decision, hard risk parameter):** at any realistic account size NEXA cannot produce enough trades to validate. Options:
   - (a) authorise re-denominating `InpMaxSameCurrencyNet` (e.g. as % of equity or lots); or
   - (b) authorise a tester campaign at a design-scale deposit (~$500–$1,000), labelled as such.
2. **B-PARITY-LIQ:** the liquidity state machine diverges on 0.2–0.85% of rows. Next step: diff one mismatching episode bar by bar.
3. **B-PARITY-TOL:** the parity contract tolerance is below journal precision. Human decision: set continuous tolerance to the journal's quantisation, or journal more decimals (an EA change, same schema).
4. **B-TZ:** fixed GMT+2 against an EET/EEST broker.
5. **B-TERMINAL:** the interactive MT5 terminal dies intermittently on this 8 GB Mac. Disk has 6.7 GB free after the full-history download.
6. **B-SCHEMA-1.1:** decision-contract fields (adversarial_result, risk %, portfolio exposure, expected_R, reason list) need approval.

## T. Exact next action required
**Decide B-EXPOSURE-CAP.** Everything downstream (labels at scale, Gate 8 statistics, Gate 9 training, walk-forward/OOS on NEXA itself) is blocked on NEXA producing ≥ 200 resolved trades, and under the current cap it produces ~1 per 4 million decisions at $50k.
