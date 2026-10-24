# PRE-REGISTRATION H-SK28-OOS: the frozen s-k-28 12-model NQ day-trading system on NQ 2010–2022 (outside its build data)

**Status: BINDING.** User approval 2026-10-23 (chat): "approve H-SK28-OOS. Freeze it, build and test the code, run the port gate, then the NQ 2010-2022 run on QuantConnect."
- Requested 2026-10-23 (chat): "write the H-SK28-OOS pre-registration (s-k-28 12-model NQ system, frozen, on QuantConnect NQ 2010-2022) for my approval."
- Source: github.com/s-k-28/nq-es-trader-5k-payout (MIT), reviewed as S73 in `../sources/REPOS_2026-10-22_review.md`.
- **Written before any of this system's trades on 2010–2022 data exist.** No s-k-28 code has been run yet.

## 0. The system and its claim
- 12 intraday models on 1-minute NQ bars, US Eastern time:
  - **mean reversion (8):** ou_rev, pd_rev, vwap_rev, or_rev, ou_lunch, vwap_scalp, ema_rev, sweep;
  - **momentum (4):** open_drive, trend, pm_mom, kalman_mom.
- A priority resolver picks one signal at a time:
  - no new signals from 15:30 ET;
  - within 3 bars, the lower priority number wins, ties go to the higher reward-to-risk;
  - an ou_rev signal also needs a quality score ≥ 3.
- **Engine** (`backtest/engine_v2.py`):
  - entry at the next bar's open;
  - stop 10–20 points (40–80 ticks), target ≥ 2R;
  - breakeven at 0.5–0.6R, partial exit and a trailing stop per model, a 20–45 minute time stop per model;
  - flat at 16:59 ET; one position at a time;
  - daily win cap +2R, a pause after 10 losses in a row;
  - 0.25 tick of slippage on non-target exits, nothing else.
- **Claim** (README, simulated): 2,716 trades from Dec 2022 to May 2026, +0.238R per trade, PF 1.66.
- **What NEXA found already (S73):**
  - The published trade list (`data/trades_backtest_full.csv`, 2,280 trades) re-priced at NEXA S1 (2 points per round trip) = **+0.141R**. At S2 (3 points) = +0.001R.
  - That list dates from 2026-05-21, **before** the 2026-05-24 commit "Eliminate look-ahead bias in backtest engine" (28e96d84). It also has a median stop of 8.2 points, below today's 10-point floor. So it does not describe the current code.
  - The models were built over 78 commits on the same 2022–25 file.

**Prior: low.**
- Every intraday ES/NQ rule NEXA has tested has failed.
- The FYP project tuned on a file of the same name and failed on independent data (S78).
- With 10–20 point stops, 2 points of cost is 0.10–0.20R per trade.
- **Scale warning, stated now:** the risk band is fixed in points (10–20). NQ traded near 2,000 in 2010 and near 12,000 in 2022. In the early years the same 10-point stop is a much wider stop relative to the day's range, so the frozen system may take few trades there, or behave differently. That is part of what "frozen" means and is not corrected. Trades per year are reported, and a late sub-window is reported (§4).

## 1. What is frozen
- Commit **0ee4392d4e11b1ab9a110cc05122f70c3b8af667** (2026-07-06, HEAD of `main` on 2026-10-23).
- The 25 run-path files listed in Appendix A, byte-identical (sha256).
- `Config()` defaults, unchanged:
  - no tier preset, no ES data (`df_es = None`);
  - the funded-account layer (dollar caps, daily profit target, Monte Carlo) is **not** part of the test. It changes sizing and stopping in dollars, not the per-trade R.
- The pipeline is exactly `run_multi.py`'s:
  1. `load_csv`
  2. `build_daily_bars`
  3. `MultiModelGenerator(cfg).generate(raw, daily, None)`
  4. `BacktestEngineV2(cfg).run(raw, signals)`
- **Allowed adapter changes (nothing else):**
  - **(a) Data in.** QC minute bars are written to an in-memory CSV with their column names (`timestamp ET, open, high, low, close, volume`) and read with **their own** `load_csv`.
  - **(b) Imports.** If QuantConnect cannot hold sub-folders, the files are flattened and only `import` lines are rewritten. The diff is saved and its hash recorded.
  - **(c) Year chunks** (§2).
  - Anything else is a logged deviation, decided before the binding run.

## 2. Data
- QuantConnect free node, NQ minute bars, continuous front contract by open interest.
- **`BACKWARDS_PANAMA_CANAL`** (additive), so point distances (stops, targets, the 10–20 point band) are true traded distances.
- Extended hours on (the source file is 23-hour: its first bar of a session is 18:01 ET); `fill_forward=False`.
- **Timestamps:** bar **end** time in ET, as in their file (the bar labelled 18:01 covers 18:00–18:01). This is checked in the gate (§3).
- **Year chunks:**
  - each calendar year Y is run on bars from (1 January Y − 120 days) to 31 December Y. This is their own regime warm-up (`run_multi.py --history` prepends 120 days);
  - only trades with an entry date in year Y are kept;
  - engine state (the 10-loss pause, daily caps) restarts each chunk, which can only touch the first days of a year;
  - chunks may be grouped several years per backtest. The grouping is fixed in the build note before the first run, from log size and QC time limits only.
- **Sets:**
  - **P (binding, outside the build data):** entries 2010-01-04 → 2022-12-23. Their file starts 2022-12-26 18:01. If QC's NQ minute history does not reach back to 2009-09-06, P starts at the first day with 120 days of warm-up (logged).
  - **IN (their build window, on QC data):** 2023-01-03 → 2025-11-28 (run in the gate).
  - **P-late (reported, no verdict effect):** 2018-01-02 → 2022-12-23 (NQ ≥ 6,000; volatility in points closer to the build years).

## 3. Port-validation gate (before any P year is run)
The gate checks that the port reproduces their system. It does not judge profit.
- **G1 reference:**
  - run the frozen pipeline locally (`.venv-ml`, `python -I`, isolated folder, no network) on their own `data/Dataset_NQ_1min_2022_2025.csv` at the same commit;
  - output: the reference trade list REF (model, direction, entry time, gross R);
  - also reported: the current code's in-sample result at S0/S1/S2, replacing the stale published list.
- **G2 QC run on IN:**
  - the same frozen code on QC data for IN;
  - REF is uploaded as a data module (hash recorded) and the matching is done in QC.
  - A **match** = same model, same direction, entry time within ±2 minutes.
- **Gate PASS needs both:**
  - ≥ **50 %** of REF trades in IN matched;
  - QC trade count within **0.80–1.25 ×** REF's.
- **Also reported:** match rate per model; the median |gross R difference| on matched trades; and a check that the first ETH bar of each session is labelled 18:01 ET.
- **Gate FAIL:** stop. No P run. Report the cause (data source, timestamps, volume) to the user. Any fix is a deviation that needs the user's approval before P.

## 4. Measurement
- **Per-trade R:**
  - gross R = the engine's `total_r` (includes its partial exit and 0.25-tick slippage);
  - net R = gross R − cost ÷ 1R (points), where 1R = |fill − initial stop|;
  - cost per round trip (NEXA standard, NQ): S0 1 / **S1 2** / S2 3 points.
- **Random-direction control:**
  - for every real P trade, the mirror trade is simulated once with the frozen `_sim`: same signal bar, opposite direction, stop and target reflected around the signal's entry price, same risk profile;
  - 2,000 replicates (seed 20261023): each trade takes the real or the mirror outcome with p = ½;
  - mirrors the engine refuses (gap through the stop, risk band) are left out of that replicate and counted;
  - statistic = mean net R at S1. Real percentile = share of replicates below the real mean.
- **Bootstrap:**
  - moving-block bootstrap over chronological P trading days (block 20, B = 2,000, seed 20261023; each replicate = Σ R ÷ trades on the resampled days);
  - 95 % percentile CI and one-sided p;
  - 4 equal consecutive blocks of P days.
- **Logging (QC free-tier logs are about 10 KB):**
  - per-day aggregates (Σ gross R, Σ 1 ÷ 1R, trades), so any cost level can be rebuilt exactly;
  - per-model and per-year summaries;
  - per-replicate control sums.
  - Logs are saved locally and hashed.

## 5. Verdict (one binding trial: NQ, S1, set P)
- **REJECTED:** P mean net R ≤ 0.
- **VALIDATED:** all of
  - the gate passed;
  - P mean ≥ **+0.025R** (H-PROP-EV threshold);
  - P CI lower > 0; one-sided p ≤ 0.05;
  - ≥ 3/4 P blocks > 0;
  - IN mean > 0 (on QC data);
  - ≥ 300 P trades;
  - real mean > the 95th percentile of the control.
- **INCONCLUSIVE:** otherwise. **INSUFFICIENT-N:** < 300 P trades.
- **Also reported (no verdict effect):**
  - S0/S2; P-late; per year (trades and mean);
  - per model and long vs short; exit reasons (target, stop, breakeven, trail, time, session);
  - win rate; mean win vs mean loss; largest win; green-day share; max drawdown and longest losing streak in R;
  - a Topstep 50K path ($2,000 trailing end-of-day limit) trading 1 MNQ per trade at S1, illustrative only.

## 6. Use of the result
- **REJECTED / INCONCLUSIVE:**
  - S73 closes; no re-tuning (NEXA law L2);
  - models are not cherry-picked from the per-model table. Any single model would need its own pre-registration on data not yet seen, and none is left before 2010 on QC.
- **VALIDATED:**
  - a separately pre-registered forward paper test (≥ 60 trading days) before any prop account;
  - execution is minute-level (12 models, breakeven/trail/time stops). By hand this is hard, so it would run as NEXA panel alerts with the user clicking (no automated orders: Topstep/Apex rules, NEXA rule).

## 7. Multiple testing
- 1 binding trial (the per-model, P-late and cost tables are descriptive). Ledger ≈ 185 → ≈ 186.

## 8. Code, tests, freeze (after approval)
- **`qc_sk28/main.py`:** QC adapter (data → `load_csv`, chunks, costs, control, gate matching, compact logs). Reads data only, no orders. The 25 frozen files are uploaded unchanged, transported base64 and checked by sha256 in the page.
- **`sk28_ref.py`:** the local G1 runner. It produces REF and the module uploaded to QC.
- **`test_sk28.py`** (synthetic, `run_tests.py`):
  - frozen-file hashes vs Appendix A;
  - the QC-bars → CSV → `load_csv` adapter (end-labelled ET times, volume 0 → 1);
  - chunk year filtering;
  - net R at S0/S1/S2 and the rebuild from per-day aggregates;
  - mirror-signal construction (reflection, refusals);
  - gate matching (±2 minutes, model + direction) and thresholds;
  - bootstrap, blocks and verdict logic;
  - log budget;
  - an end-to-end smoke run of the frozen pipeline on their own `generate_synthetic_data`.
- Tests pass before the hash. Then the gate runs. P runs only after a gate PASS.
- The QC editor hash is checked before each run (website, the user's login). **One run per chunk, no re-runs.**

## Appendix A: frozen run-path files at 0ee4392d (sha256)
```
0ff4ea1af933776596ab791f10a3ddf1d0044a70dd9ee37e500b778da9c80d0c  config.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  data/__init__.py
23da25c0648f8c7e82f28ffc41844d85863a5da164acf20c3e46bbfe187fc1d9  data/loader.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  strategy/__init__.py
ae5e5afd9237ccade9a5f1aa45462e2c0a009476f0a170292e7e762999f3f51a  strategy/vwap.py
8fa5d94a5087fd6cf8ac21c2ecbd1acffeff8b9d93134b35d6177717b46d63ab  strategy/quality.py
071a5f1701bff3dbb18e89b5605d5340182031f6ea5a4f403012267ebfe38e4b  strategy/multi.py
22621353f3472d2a1ce3f3347c9a90a4c548da5889eb78dad68be1eab3e56ba3  strategy/quant/__init__.py
452caa4b4d0c82268ffec6c3150aad1e29aa058805cc727eb75f4b2d9cc3b714  strategy/quant/features.py
d838816acfc9bf809a29d9f12d38079460fb01bada323b462a51b6dc0253201e  strategy/models/__init__.py
bee42271a64f619116e352f32af1121b0642117ae4d43db107c3ed64650b3a71  strategy/models/base.py
a2fdf51c70d4a06d493a98fa7c793879a0983b975f9411423ed99772d248dd9f  strategy/models/ou_reversion.py
dfd10b6222900eaccc22514645ace06fda5ae45f69d1a4f95161d487ba9218c6  strategy/models/pd_level_reversion.py
d073030d4f35a15f0523e10f1a30d4510926826cde4845a89b87e5bb3154c2cf  strategy/models/vwap_reversion.py
4daa828ab884af74215829ca779d83ef22027047a067210f5ed606329e999ebe  strategy/models/or_reversion.py
868e846abf402a6fecaa5211d61c485f71ffa4a7b56f073cf3b959610a1d3a6e  strategy/models/ou_lunch.py
9d212e0bcf84b47689d806dce348476e3a7180afc3351f982864109e45ea546e  strategy/models/vwap_scalper.py
c9078e7140c5113cc1edbf375c5367ae0c8eca18ac65c6f1acd3a6b047dd9adc  strategy/models/opening_drive.py
6263f4555ede55ec2a3c8247bba37c811014bcb5ebb8d2f52cd990b31507bc80  strategy/models/trend_cont.py
f53b6a7aebcebb6b4966d184c91a1c71bc45d7e44a291ff306eabcb113ee5713  strategy/models/afternoon_momentum.py
f44ec4d9e94c9b8aea6b03ce4367c27d0817a5021d65f2992445b1701ea55689  strategy/models/ema_reversion.py
b5170a019cf04a193edac115c2b8d6d08377f5e0979aa2f8c890eb4e4ed2c983  strategy/models/kalman_momentum.py
9f4dc60d104d44bd63e09b114830df6695a8e950c79be8247be93ddc4d63c386  strategy/models/sweep_reversal.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  backtest/__init__.py
347a9b41aab1a2fa1f93383434209243c76791cde3451c5aadd2aa4da1ed30b5  backtest/engine_v2.py
```
