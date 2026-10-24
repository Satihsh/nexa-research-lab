# D49 / C4: 2 % daily loss as a pre-trade budget. Engineering report (2026-10-03)

**Scope:** human-approved option B, a change to the frozen `NEXA_Risk.mqh` plus a 2-line call in `NEXA_EA.mq5`. Sizing (0.30 % target, 1.00 % hard ceiling), every limit, every input and default, the exits and the halt trigger are all unchanged. **Not deployed:** `Experts\Advisors\NEXA_EA.ex5` is still `f0ae9618…`.

## Defect
- **Old rule:** `DailyLossLimitBreached()` blocked new entries only once equity was **already** ≥ 2 % below the day's start equity, and it was checked once per new bar. Open positions were never closed by it.
- **Effect:** a trade opened just above the line, plus positions still open, could take the day past 2 %.
- **Evidence:** 12 of 732 traded days in the cap-neutral campaign ended beyond −2 %, the worst at −2.29 %. Theoretical worst case: about 2 % plus one trade at the 1 % ceiling plus gaps.

## Fix (`NEXA_Risk.mqh` `1f684cde…` → `a43d8328…`; `NEXA_EA.mq5` `3edcec11…` → `4ef7de88…`; pre-change copies in `build/c4_pre_source/`)
- **New section `DAILY LOSS BUDGET`, appended before `#endif`.** Every earlier block is byte-identical; the invariant test pins it as a third approved block.
- **`DailyLossBudgetOK(sym, dir, entry, stop, lots, reason)`** allows an entry only if
  `E_now − OpenRisk − NewRisk ≥ DailyStartEquity × (1 − InpMaxDailyLossPct/100)`.
  - **OpenRisk:** for every open position on the account (all symbols and strategies), the loss from its current price to its stop, via `OrderCalcProfit`.
  - **NewRisk:** the candidate trade's sized loss to its stop.
  - **Fail-closed:** each of these blocks the entry with its own reason: no start equity, invalid equity, a position without a stop, an unreadable position or calculation, and direction 0.
  - **Refusal reason:** `NO_TRADE_DAILY_LOSS_BUDGET_eq…_open…_new…_floor…`, which carries the numbers.
- **Unchanged from the old rule:** the start equity is the same as `DailyLossLimitBreached` uses (the first new bar of the server day, at 17:00 New York), and so are the equity basis and the daily reset. Open P&L counts through E_now; realized losses, commissions and swaps through equity; a partial close shrinks OpenRisk; a position at breakeven adds only its distance to the stop.
- **Placement:** `ExecuteSignal` calls it **inside the portfolio lock**, after the exposure and correlation caps and before the preflight check, slot reservation and order send, so entries from several charts cannot share the same budget.
- **Second line:** the halt trigger stays as it was.
- **Not covered:** stop slippage and gaps, and the new trade's own commission (about 0.01–0.04 % of equity at minimum size).
- **Build:** staged copies in `build/c4_src/` → `build/NEXA_EA_C4.ex5` (`149aa0b1…`), `NEXA_CorrCapTest_C4.ex5` and `NEXA_DailyBudgetTest_C4.ex5`, **0 errors, 0 warnings** each. The A3, D45, D46, S11 and D-TZ binaries are untouched.

## Verification
| Check | Result |
|---|---|
| Static tests (`test_nexa_risk_c4_budget.py`) | Formula and every fail-closed path present. Call inside the lock and before any order. The change is a pure append, with 2 lines added to the EA. The halt trigger, day roll and sizing are byte-identical. Inputs unchanged. |
| Compiled harness (`NEXA_DailyBudgetTest.mq5`, `tester_runs/dailybudget_c4_20261003/`) | **9/9** cases as expected. Floor $0.01 above → refused; $0.01 below → allowed, with and without an open position (whose $80 risk is counted). No start equity, direction 0 and a position without a stop are all refused. |
| Production-input regression (12 GBPUSD windows, $200; `c4/REG_C4_*`) | 12/12 runs passed. The account never neared −2 % (worst day −1.73 %), so there were **0 refusals** and every window is **byte-identical** to the D-TZ baseline. |
| Research configuration ($50k, cap off; 6 windows that had days beyond −2 %; D-TZ vs C4; `c4/capn_*`) | **34 refusals, 34 arithmetically justified**, 0 fail-closed rows. The first divergence is always a refusal. **Days beyond −2 %: 5 → 2. Worst day: −2.42 % → −2.01 %.** The two remaining days (−2.01 %) come from slippage on positions already open, the disclosed limit. |
| Correlation harness (it compiles the Risk file) | Re-run (`tester_runs/corrcap_parity_20261003_c4/`): 18/18 identical to 2026-09-29 |
| Full suite | **620 passed**; ruff clean |

## Test pins
- **Updated to the new approved file:** the invariant test (third approved block, `c6eabbb9…`; the S11 exposure text still hashes to `bb23581e…`), `test_nexa_mql5_safety.py`, `test_nexa_position_mgmt_fix.py` and `test_nexa_corr_oracle.py` (new evidence folder).
- **Evidence tests pinned to the sources their evidence ran with:**
  - D46 → `build/stale_src/` (`3edcec11…`), plus a check that `OnTick` is unchanged;
  - S11 → `build/s11_src/NEXA_Risk.mqh` (`1f684cde…`), plus a check that the exposure functions are unchanged;
  - D-TZ → `build/dtz_src/`.

  This is the same approach as D45.
- **Historical runner scripts:** still pinned to the hashes their evidence ran with, so they refuse by design. The current runners are `run_c4_regression.sh` and `run_c4_extra.sh`.

## Effect on NEXA
- **Per-trade risk:** unchanged.
- **On a losing day:** at 0.30 % risk, a 7th entry after six losses (−1.8 %) is refused. At the 1 % ceiling, a third entry after two losses is refused.
- **Winning days:** never limited.
- **+24.5 %/day objective:** unaffected; it remains ❌ REJECTED (Gate 8 negative expectancy; the sizing ceiling is about +12.7 %/day even if every trade hits 4R).
- **Deployment:** still needs separate approval.
