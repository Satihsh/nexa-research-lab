# D47 / S11: currency-exposure cap fails closed. Engineering report (2026-10-03)

**Scope:** human-approved change to the frozen `NEXA_Risk.mqh` (option A). No limit, size, input or default changed. **Not deployed:** `Experts\Advisors\NEXA_EA.ex5` is still `f0ae9618…`.

## Defect
- `NetCurrencyExposure` adds up net lots per currency across **all** open positions; `ExposureCapOK` uses that sum to cap the currency at `InpMaxSameCurrencyNet × min lot`.
- **Fail-open:** a position whose symbol read as `""` was skipped with `continue`. A volume of 0 or a currency spec that read empty also counted as nothing.
- **Effect:** an open position the EA could not read counted as zero exposure, so a new entry could pass a cap it should have failed.
- **Context:** the correlation cap next to it already failed closed (approved 2026-09-29); the exposure cap was outside that approval.

## Fix (`NEXA_Risk.mqh` `7fd5692a…` → `1f684cde…`; pre-change copy at `build/s11_pre_source/`)
- **`NetCurrencyExposure(string currency, bool &ok)`:** sets `ok = false` and returns when a position's symbol is unreadable, its volume is not a valid positive number, or its currency spec is empty. It never skips a position.
- **`ExposureCapOK`:**
  - blocks with `EXPOSURE_POSITION_UNREADABLE` when either sum is not `ok`;
  - adds an empty base or quote currency of the candidate symbol to the existing `EXPOSURE_CAP_INVALID_SPEC` check.
- **Unchanged:** the cap comparison and `PORTFOLIO_CURRENCY_EXPOSURE_CAP`.
- **Scope of the edit:** only these two functions changed. Everything before them is byte-identical, `GetSymbolCurrencies` is unchanged, and all inputs and defaults are unchanged (test-enforced).
- **Build:**
  - staged copies `build/s11_src/` → `build/NEXA_EA_S11.ex5` (`7d37dc7d…`) and `build/NEXA_CorrCapTest_S11.ex5`, **0 errors, 0 warnings** each;
  - the A3 (`91ee5e20…`), D45 (`28e8d925…`) and D46 (`fd2fe06e…`) binaries are untouched.

## Verification
| Check | Result |
|---|---|
| Static tests (`research/test_nexa_risk_s11_exposure.py`) | Every unreadable path reports `ok = false` and the cap blocks before comparing. The same rule flags the original `continue` in the pre-change source. The change is confined to the two functions. There is no other caller of the changed signature. |
| Invariant test (`test_nexa_mql5_invariants.py`) | Still byte-identical to the 2026-09-19 baseline outside two approved blocks: the correlation block (2026-09-29) and now the exposure block (S11, hash `bb23581e…`). All hard-risk defaults are unchanged. |
| Tester regression (`run_s11_regression.sh` + `s11_regression.py`; GBPUSD, 12 windows, production inputs, $200) vs the D46 runs | 12/12 runs passed. **995,400 rows, 0 differing.** 281 exposure-cap blocks are identical, and there are 0 new fail-closed rows. All positions are readable in the tester, so the unreadable path cannot fire there and is covered statically, as for the correlation fix. |
| Correlation-cap harness (compiles the Risk file) | Re-run in the tester (`tester_runs/corrcap_parity_20261003_s11/`). All 18 cases are identical to the 2026-09-29 run, which is kept. |
| Full suite | **606 passed**; ruff clean |

## Test and script pins
- **Updated** to the new approved hash: `test_nexa_mql5_safety.py`, `test_nexa_position_mgmt_fix.py`, `test_nexa_stale_bar_guard.py` (its D46 evidence stays pinned to `7fd5692a…`, the Risk file it ran with), and `test_nexa_corr_oracle.py` (new evidence folder).
- **Not edited, deliberately:** the historical runners `run_staleguard_regression.sh`, `run_engfix_regression.sh`, `run_capneutral_batch.sh` and `capn_analysis.py` stay pinned to `7fd5692a…`. They record what their evidence ran with, so they now refuse or flag a change. That is expected, as after D45.
- **Current regression runner:** `run_s11_regression.sh`.

## Deployment
Not deployed. The current verified build is `build/NEXA_EA_S11.ex5` (D45 + D46 + S11). Deployment still needs the D-TZ decision and separate approval.
