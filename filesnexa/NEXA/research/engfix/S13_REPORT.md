# D50 / S13: time-aligned USD composite (f29). Engineering report (2026-10-04)

**Scope:** human-approved option B. `NEXA_Intelligence.mqh` changed; the parity oracle (`nexa_parity.py`, `nexa_parity_full.py`) mirrors it. **`NEXA_EA.mq5`, `NEXA_Risk.mqh` and `NEXA_Common.mqh` are unchanged.** `PackFeatures` and the schema are unchanged. **Not deployed:** `Experts\Advisors\NEXA_EA.ex5` is still `f0ae9618…`.

## Defect
- **What f29 is:** `UsdCompositeDirection()` votes the four basket symbols' 10-bar direction into USD strong, weak or mixed (+1 / −1 / 0). It is journalled as f29 and is part of the model input vector.
- **The defect:** it read each symbol by **bar position**, `iClose(sym, tf, 1)` against `iClose(sym, tf, 11)`. When a symbol had a tick gap or a different trading break, "1 bar ago" and "11 bars ago" were different moments from the traded chart's.
- **Measured before the fix:** a time-aligned read disagreed with the EA's f29 on 14.9 % (GBPUSD) and 16.5 % (XAUUSD) of window-B decisions. Even my offline replica of the positional read matched only 84–86 %, so f29 was not reproducible and stayed parity-exempt.
- **Impact:** none on trading. f29 is never scored (`ComputeCompositeScore`), no model exists, and no research code uses it.

## Fix (`NEXA_Intelligence.mqh` `18e3b30c…` → `81641c4e…`; pre-change copy at `build/s13_pre_source/`)
- **Decision time:** `t` = `iTime(_Symbol, PERIOD_CURRENT, 1)`, the closed decision bar that `BuildFeatures` used, so the EA's call site needed no change.
- **Bars read per basket symbol:** via `CopyRates(sym, tf, t10 − stale, t)` (bars at or before `t` only, so it is causal), take
  - its last bar at or before `t`;
  - its last bar at or before `t10 = t − 10 bars`.
- **Symbols skipped:** if either bar is more than 5 bars stale, or both are the same bar.
- **Unchanged:** the vote rule, the USDJPY inversion and the "≥ counted − 1 agree" threshold.
- **New constants:** `NEXA_USDCOMP_LOOKBACK_BARS = 10` and `NEXA_USDCOMP_STALE_BARS = 5`. No input was added.
- **Oracle mirror:** `nexa_parity.usd_composite_direction`, plus `MarketData.basket` and `load_market_data(basket_paths=)`. f29 is now a categorical feature, **compared whenever the four basket symbols' bars are supplied** (`nexa_parity_full.py` loads them) and reported exempt for a run without them, never counted as a pass.
- **Build:** staged copy `build/s13_src/` → `build/NEXA_EA_S13.ex5` (`dec57013…`), **0 errors, 0 warnings**. Earlier binaries are untouched.

## Verification
| Check | Result |
|---|---|
| Static tests (`test_nexa_s13_usd_composite.py`) | No positional `iClose` left; reads are by time and causal (bars at or before `t` only); the skip rules are present. The vote rule, everything before the composite, and `PackFeatures` are byte-identical to the pre-change source. The EA still does not score f29. |
| Oracle unit tests (`test_nexa_parity.py`) | Votes and the JPY inversion; a positional gap doesn't matter; stale symbols are skipped; fewer than 2 symbols counted gives 0; a future bar is never read; f29 is compared and a perturbation is caught when the basket is supplied. The 3 new tests fail on the pre-S13 oracle. |
| Tester regression (12 GBPUSD windows, production inputs, $200, against C4; `engfix/s13/`) | 12/12 runs passed. **995,081 rows: 0 differ in any column except f29**, so trading is identical (561 trades). f29 changed on **149,519 of 993,333 decisions (15.05 %)**, matching the estimate before the fix. |
| Window-B parity, S13 journals, all 4 symbols (`reports/pepperstone/B_PARITY_S13_VERIFY_WINDOW_B.json`) | **PASS on all 4.** **44 features compared** (was 43); f29 has **0 mismatches** across 112,688 rows. Exempt: only obiProxy, cvdProxy, liqOrigin and newsRiskActive. All 47 reviewed ties matched, none unused. |
| Full suite | **628 passed**; ruff clean |

## Consequences
- **Journals:** existing journals carry the old positional f29. New journals carry the time-aligned value.
- **Stored report:** `PEPPERSTONE_PARITY_FULL_B.json` still holds the pre-D-TZ PASS with 43 features. Replacing it with the current result needs approval.
- **Deployment:** still needs separate approval.
