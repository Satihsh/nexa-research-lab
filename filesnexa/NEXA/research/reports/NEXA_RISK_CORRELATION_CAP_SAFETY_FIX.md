# NEXA_Risk.mqh: fail-closed correlation-cap safety fix (human-approved, 2026-09-29)

**Scope.** This change fixes live-trading safety behaviour only, and nothing outside it:
- no risk policy, threshold or trading behaviour changed;
- no strategy optimised;
- V2 not touched.

## Before and after
| Item | Value |
|---|---|
| `NEXA_Risk.mqh` before | `e706d453d346100f99d06ce3bf2b62697ce544d913bba6ba8053f506115ce5ed` (backup: `NEXA_PRE_CORRFIX_BACKUP_20260929T085610Z/`) |
| **`NEXA_Risk.mqh` after** | **`7fd5692a2bd3aec7443185f914be320158cfe55bcddcf370db059a6da0d908d1`** |
| Approved correlation block sha256 | `97f28759e6c4853ddb3b7cba9b2e47c29599d4efd08e9ac0dfc71844f319c62e` |
| Diff | confined to the block between `//=== PEARSON CORRELATION` (now `//=== CORRELATION CAP (fail-closed, time-aligned)`) and `//=== PORTFOLIO CURRENCY EXPOSURE`. The prefix and suffix are byte-identical to the baseline (enforced by `test_nexa_mql5_invariants.py`) |
| Immutable baseline `NEXA_BASELINE_BACKUP_20260919-124052/` | untouched; manifest OK |
| `NEXA_EA.mq5` | unchanged `97a3ff62…`. The call site `CorrelationCapOK(_Symbol, corrReason)` has an identical signature |

## What changed
- **Old behaviour.** `PearsonCorrelation` paired bars by shift and returned 0 (PASS) on unreadable history, fewer than 3 valid bars, zero variance or a non-finite result. An unreadable position symbol was skipped.
- **New behaviour.**

| Area | Change |
|---|---|
| Alignment | Returns are formed only over intervals of **consecutive closed bars of the new symbol whose two open times both exist in the other symbol**. Pairing is by bar open time. |
| State | `NexaCorrelationFromBars` (pure core) and `NexaCorrelationState` (terminal wrapper) return `OK / BLOCK / INSUFFICIENT_DATA`. |
| **INSUFFICIENT_DATA → BLOCK** | Any of these produces it: fewer than 80 % aligned pairs; unavailable symbol; unsynchronised series; short or failed `CopyRates`; non-ascending times; bad (≤ 0 or non-finite) prices, which are excluded and never zero-filled; zero or invalid variance; non-finite correlation; invalid configuration. |
| Unreadable position | `PositionGetSymbol` returning "" → block. Any state other than OK → block. |
| Unchanged | `InpMaxCorrelation = 0.75`, `InpCorrelationBars = 100`, `PERIOD_CURRENT`, closed bars only (start_pos = 1), the same simple-return definition, and the same 101-bar / 100-return window. |

**Behavioural consequence (fail-closed, by design).** When NEXA holds a position in one of its symbols and a new entry on another symbol cannot be checked on at least 80 % aligned bars, the entry is **blocked**. For example, XAUUSD against FX on M1 across gold's daily break. The fix never permits a trade that the old code blocked on valid data. It only adds blocks.

## Verification
| Check | Result |
|---|---|
| MetaEditor compile `NEXA_EA.mq5` (includes the fixed `NEXA_Risk.mqh`) | **0 errors, 0 warnings** (`build/NEXA_EA.compile.log`) |
| MetaEditor compile `NEXA_CorrCapTest.mq5` (test harness) | **0 errors, 0 warnings** |
| Harness executed in the Strategy Tester | run `corrcap_parity_20260929_t2` (EURUSD M1, 2024-01-08→12, no orders): 18 fixture cases + 3 wrapper/cap cases |
| **Compiled MQL5 core vs Python oracle** | identical state, aligned count and detail in all 18 cases; correlation equal to ≤ 1e-12 |
| Wrapper, nonexistent symbol | INSUFFICIENT_DATA (`SYMBOL_UNAVAILABLE`) → blocks |
| Deterministic unit tests (`test_nexa_corr_oracle.py`) | see the case table below |
| Regression documentation | the removed function returned \|corr\| < 0.75 (PASS) on the gap, empty-history and sparse cases, where the fix BLOCKs |
| Scoped invariant test | outside the block, the file is byte-identical to the baseline; the block equals the approved hash; all 10 hard-risk defaults unchanged |
| Full Python regression | **490 passed** (1 pre-existing warning); ruff clean |

Unit-test cases covered in `test_nexa_corr_oracle.py`:

| Case | Expected state |
|---|---|
| valid aligned, high correlation | BLOCK |
| low correlation | OK |
| negative high correlation | BLOCK |
| missing history (empty / one bar / short A) | INSUFFICIENT_DATA |
| shifted timestamps | INSUFFICIENT_DATA |
| 15-bar gap, time-aligned | BLOCK |
| 60-bar gap | INSUFFICIENT_DATA |
| 8 sparse missing bars | BLOCK |
| 20 sparse missing bars | INSUFFICIENT_DATA |
| exactly 80 aligned | computed |
| 79 aligned | INSUFFICIENT_DATA |
| zero variance | INSUFFICIENT_DATA |
| zero prices | INSUFFICIENT_DATA |
| one NaN price | excluded, correlation still computed |
| non-finite returns | INSUFFICIENT_DATA |
| non-ascending times | INSUFFICIENT_DATA |
| invalid configuration | INSUFFICIENT_DATA |
| threshold boundary (≥ blocks) | BLOCK |
| any non-OK state | cap blocks |
| MQL5 parity for all 18 fixtures | equal to the oracle |

**Coverage limits (not a defect).**
- The final `NON_FINITE` branch on the correlation value is defensive. With finite positive prices it cannot be reached, because non-finite inputs are stopped earlier by the price and variance guards. Every one of those paths blocks.
- The `SERIES_SYNCHRONIZED` / `CopyRates` failure branches were exercised only through the nonexistent-symbol and empty-symbol cases. A real unsynchronised-history state cannot be forced deterministically in the tester.
- The live multi-position path, `CorrelationCapOK` with real open positions, is not exercisable in a single-symbol tester run. It is covered by the pure-core parity tests and static source checks.

**Tester side-effects (disclosed).**
- Each tester launch authorised the terminal on the demo account (0 positions, 0 orders before and after; the harness has no order code).
- The first attempt (H1, 1-day range) never started a pass and was superseded by the M1 one-week run.
- The MT5 history base grew from 25,113,084 KB to 25,114,812 KB (+1.7 MB) across the two tester launches: tester cache and sync for one EURUSD week. This was not a broad download.
- The bridge `MTM_ENABLE_TRADING` and `MTM_ENABLE_EXEC` stayed false throughout.

## V2 impact: none
- `NEXA_Risk.mqh` (and every `.mq5` / `.mqh`) is **not** in the V2 pinned universe (14 data, 23 code and 5 design pins).
- No pinned file was modified. `test_nexa_mql5_invariants.py`, `nexa_corr_oracle.py` and `test_nexa_corr_oracle.py` are not pinned. **No re-freeze was required and none was created.**
- V2 still verifies:
  - anchor `6090be68184af7643f82b680d144a1b9e1622b3bbceebfb872729b97b9d9324c`;
  - `verify(anchor, checkpoint seq 6 bbd9a28e…5b2b)` PASS;
  - registry tree `de0c101accf58655…` and witness `05d4544b4c86340d…` unchanged;
  - FROZEN; 0 results; 0 OOS rows.
- The research experiment is scientifically identical.

## Deployment status
- The new EA build (`build/NEXA_EA.ex5`) was compiled but **not deployed** to the terminal's Experts folder.
- Live or demo deployment requires a separate human decision.
- The other live-trading blockers remain open: B-EXPOSURE-CAP and D-TZ.
