# D46 stale-bar guard (D-STALE-BAR-EVAL): engineering report (2026-10-03)

**Scope:** engineering correction only, human-approved option C. No input, strategy parameter, entry rule, risk limit or V2/8E artefact changed. **Not deployed:** `Experts\Advisors\NEXA_EA.ex5` is still `f0ae9618…`.

## Defect
- **When the EA evaluates a bar:** at the first tick of the next bar (`OnTick` tier 2).
- **What the weekend guard checks:** `IsWeekendCloseWindow()` uses the **current** server time (Friday ≥ `InpWeekendCloseHour`).
- **The gap:** at Monday's first tick the guard sees Monday, so Friday's last bar (≈23:54, inside the no-entry window) was evaluated and could have been traded at Monday's price on Friday's setup. Public-holiday closures behave the same way.
- **Journals (96 tester runs):**
  - 588–589 evaluations happened more than 1 day after their bar.
  - **0 trades** resulted, but only because 535–536 were spread-vetoed (median spread/ATR 5.61 against 0.15) and 53 had no qualified event.
- **Not a money-risk hole:** `ExecuteSignal` re-checks the stop side against the live quote and sizes the position from the actual distance.

## Fix (`NEXA_EA.mq5` `3edcec11…`, previously `10b62623…`)
- **Constant:** `const int NEXA_STALE_BAR_MAX_SEC = 6 * 3600;`. This is a constant, not an input, so there are still 64 inputs. It sits well above every regular daily break; the longest non-weekend lag seen was 1.92 h.
- **Rule:** `NexaClosedBarStale(closedBarOpen, periodSec, now, maxSec)` is true when (now − bar close) > maxSec.
- **Where it runs in `OnTick`:** **after** `BuildFeatures` and the proxies, before the spread veto, scoring and `ExecuteSignal`. A stale bar is journalled as `NO_TRADE_STALE_BAR` and returns.
- **Effect on features:** they are built exactly as before, so the liquidity state and all f00–f47 values are unchanged and parity is unaffected.
- **Size of the change:** 17 added lines, 0 removed (test-enforced against the D45 source). `NEXA_Risk.mqh` is unchanged (`7fd5692a…`).
- **Build:** staged copy `build/stale_src/NEXA_EA_STALE.mq5` → `build/NEXA_EA_STALE.ex5` (`fd2fe06e…`), **MetaEditor 0 errors, 0 warnings**. The A3 binary `build/NEXA_EA.ex5` (`91ee5e20…`) and the D45 build (`28e8d925…`) are untouched.

## Regression (ENGINEERING REGRESSION, not research evidence)
- **Setup:** `run_staleguard_regression.sh` uses the same setup as the D45 regression (GBPUSD, 12 windows, production inputs pinned, $200). `staleguard_regression.py` compares each journal row by row with the D45 baseline. Evidence: `staleguard/regression_evidence.json`.

| Check | Result |
|---|---|
| Runs with Test passed | 12 / 12 (one early tester death retried automatically) |
| Rows per window, stale build vs baseline | identical counts (29,312–92,568) |
| Rows flagged `NO_TRADE_STALE_BAR` = rows evaluated more than 6 h after their bar closed | **147 / 147** in every window (weekends lag 48.1 h, holidays ≥ 26.1 h) |
| Rows differing outside those 147 | **0**: every OPEN, FILL, PARTIAL_CLOSE and CLOSE row is byte-identical |
| Columns differing on the 147 rows | `reason` only (all were `NO_TRADE_SPREAD_TAX` before) |
| Longest lag among unflagged decisions | 1.92 h |

## Tests
- **New `research/test_nexa_stale_bar_guard.py` (4 tests):**
  - the rule and the 6 h limit;
  - the guard sits after `BuildFeatures` and before every trade path;
  - the change only adds lines, and the D45-era functions are byte-identical;
  - the tester evidence is pinned to the current source and binary hashes.
- **`test_nexa_position_mgmt_fix.py`:** the D45 evidence is now pinned to the D45 source snapshot `build/pmfix_src/NEXA_EA_PMFIX.mq5` (`10b62623…`), plus a new check that `ManageOpenPosition` in the current source is byte-identical to it.
- **Full suite:** **600 passed**; ruff clean.

## Consequences and limits
- `run_engfix_regression.sh` (D45) now refuses to run, because its staged copy no longer equals the current source. That is expected, as for the cap-neutral runner after D45.
- The regression did not exercise the "no qualified event" variant: in GBPUSD under production config every stale row was spread-vetoed. The guard's position before scoring is test-enforced.
- Deployment still needs the open decisions (S11, D-TZ, stale build) and separate approval.
