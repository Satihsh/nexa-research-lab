# D51 / S14: deviation policy, post-fill hard-ceiling guard. Engineering report (2026-10-04)

**Scope:** human-approved option C (with option A's documentation); option E (demo forward check) follows, subject to separate deployment decisions. Changed: `NEXA_EA.mq5` and the new `NEXA_FillGuard.mqh`. **Unchanged:** `NEXA_Risk.mqh`, sizing, limits, inputs, schema, V2 and 8E. **Not deployed:** `Experts\Advisors\NEXA_EA.ex5` is still `f0ae9618…`.

## Findings
- **The deviation setting does nothing at this broker.** `trade.SetDeviationInPoints(20)` was the only slippage control. Pepperstone runs EURUSD, GBPUSD, USDJPY and XAUUSD on **market execution** (`contracts.json` `trade_exemode = 2`, IOC fills), where MT5 ignores the deviation. Tester evidence: XAUUSD fills with up to 55 points of adverse slippage were accepted, far beyond the 20-point deviation.
- **The 1 % hard ceiling was only checked before the send.** Before each attempt, the EA re-reads the quote and refuses the order if the money at risk would rise. After the fill, nothing was checked, so an adverse fill could take the actual risk past `InpHardRiskCeiling`. Stops are tight (median 24 points on EURUSD, i.e. 2.4 pips), so 1 pip of slippage is about 0.4R.
- **Slippage direction was lost.** FILL rows recorded only absolute slippage.
- **Live fills:** none exist yet; that is what option E collects.

## Change (`NEXA_EA.mq5` `4ef7de88…` → `6932ad7d…`; pre-change copy at `build/s14_pre_source/`)
- **New `NEXA_FillGuard.mqh`** (`c656b712…`):
  - `NexaPositionRiskPct(ticket)`: the actual risk as % of equity, from the fill price to the stop via `OrderCalcProfit`. Negative means unknown (−1 position not found, −2 no stop, −3 calculation failed).
  - `NexaFillRiskExceeds(riskPct, ceiling)`: true if unknown or above the ceiling.
- **Entry-fill branch of `OnTradeTransaction`:** after the FILL row is written, the guard runs. If it trips, the EA journals `FILL_RISK_ABOVE_HARD_CEILING_x.xxPCT` and closes the position (`CloseNexaPositionIfAny`).
- **FILL reason:** `SLIPPAGE_PTS_<abs>_ADVERSE_<±x>` (+ = adverse). The absolute part is unchanged.
- **`SetDeviationInPoints(20)`:** the value is unchanged; a comment now says it has no effect under market execution.
- **Size of the change:** two lines replaced and the guard added; `ExecuteSignal`, `ManageOpenPosition` and `OnTick` are byte-identical (test-enforced). No input was added.
- **Build:** staged copies in `build/s14_src/` → `build/NEXA_EA_S14.ex5` (`ff30ac38…`) and `NEXA_FillGuardTest_S14.ex5`, **0 errors, 0 warnings**. Earlier binaries are untouched.

## Verification
| Check | Result |
|---|---|
| Harness (`NEXA_FillGuardTest.mq5`, `tester_runs/fillguard_s14_20261004/`) | **7/7.** Real tester positions at 0.501 % keep and at 1.607 % close; the compiled risk equals an independent price-distance calculation to 1e-6. A position without a stop, an unknown ticket and an unknown risk all close. The boundary holds: exactly 1.00 % keeps, 1.000001 % closes. |
| Regression (12 GBPUSD windows, production inputs, $200; vs S13; `engfix/s14/`) | 12/12 passed. **No row differs except the 561 FILL rows' reason text.** The absolute part is unchanged on 561/561, and the signed slippage matches the fill prices on 561/561 (30 adverse, 34 favourable, the rest zero). **Guard firings: 0.** |
| Static tests (`test_nexa_s14_fill_guard.py`) | Market execution confirmed from the broker specs. Guard logic and placement (entry-fill branch, after the FILL row). The change is confined to two replaced lines plus the guard. |
| Full suite | **634 passed**; ruff clean |

## Limits
- **Only the guard function is exercised in the tester.** The EA's close path itself cannot be triggered there, because tester slippage never breaches the ceiling. It is covered by the static placement tests plus the harness.
- **An immediate close realizes the slippage plus the spread.** That is the price of keeping the hard ceiling.
- **Thresholds tighter than the ceiling** (e.g. adverse slippage of more than X R) need live fill evidence. That is option E.
