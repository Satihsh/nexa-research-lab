# NEXA Parity Oracle (Stage 3)

`nexa_parity.py` independently reconstructs the NEXA feature definitions in
Python and compares the result against the `f00..f47` values MQL5 actually
wrote.

## Why this exists

If Python and MQL5 compute a feature even slightly differently, a model gets
trained on values the live engine never sees. That failure is silent: it passes
every unit test, produces a plausible backtest, and shows up in production as
alpha decay that looks like the market changing.

This module is the only place in the research tier permitted to compute a
feature, and it computes them solely to be compared — never to be used.

## What it is not

* **Not a second feature engine.** Its output is never written to the canonical
  dataset, never fed to a model, never substituted for an MQL5 value.
* **Not a copy of the MQL5 code.** It reconstructs from the documented
  definitions. Copying the implementation would make the comparison vacuous —
  two copies of the same bug agree perfectly.

`PackFeatures()` in `NEXA_Intelligence.mqh` remains authoritative. When the two
disagree, that is a finding about the **research** side until investigation
proves otherwise. MQL5 is what trades.

## Honest limit of the test suite

The 45 tests verify the *comparison machinery*: tolerance behaviour, mismatch
detection, exemption handling, causality, fail-closed gating, determinism. Tests
that show a "PASS" feed the oracle a dataset whose features came from the
reconstruction itself, then perturb one value.

**They do not prove Python agrees with MQL5.** That is established only by
running this oracle against a real Strategy Tester export. Until that run
happens, parity is *untested against the live engine*, and nothing here claims
otherwise.

## Usage

```bash
python nexa_parity.py canonical.csv \
    --m1 EURUSD_M1.csv --m5 EURUSD_M5.csv --m15 EURUSD_M15.csv \
    --h1 EURUSD_H1.csv --d1 EURUSD_D1.csv \
    --point 0.00001 --gmt-offset 2 \
    --mql5-source ../NEXA_Intelligence.mqh \
    --out mismatches.csv
```

Exit code 0 only on `PASS`. In code:

```python
result = run_parity(frame, data, cfg, mql5_source="../NEXA_Intelligence.mqh")
assert_parity_or_halt(result)      # raises ParityGateError on anything but PASS
```

The D1 file must come from the **execution broker**: a different daily rollover
produces different PDH/PDL for the same calendar date, and the whole liquidity
engine is anchored to those levels.

## Coverage

**44 of 48 features reconstructed and compared** when the four basket symbols' entry-timeframe bars are supplied (`MarketData.basket`; `nexa_parity_full.py` loads them from the tester directory); 43 without them, in which case `usdCompositeDirection` is reported exempt for that run, never as passing. Since S13 (2026-10-03) the EA reads the basket by time, so f29 is reproducible.

| Group | Features |
|---|---|
| Structure | `structureBreakUp/Down`, `isBOS_up/down`, `isCHoCH_up/down`, `isMSS_up/down` |
| Displacement | `displacementUp/Down`, `displacementATR` |
| Sweep (bar-local) | `sweepUp`, `sweepDown` |
| SMC objects | `fvgBullActive/BearActive`, `obBullActive/BearActive`, `inOTE_up/down`, `bprActive` |
| Regime | `trendState`, `volState`, `breakoutState`, `regimeTransitioning` |
| MTF | `trendM5`, `trendM15`, `trendH1`, `htfAlignment` |
| Execution | `spreadATRRatio` |
| Liquidity machine | `liqState`, `liqResolution`, `liqExcursionATR`, `liqWickBodyRatio`, `liqBarsBeyond`, `liqBarsSinceReclaim`, `liqSweepDirection`, `liqResponseDirection`, `liqMssAfter`, `liqDisplacementAfter`, `liqFvgAfter`, `liqEventActive`, `liqLevel`, `liqSetup` |

ATR is reconstructed as **Wilder's**, with explicit warm-up: the first `period`
values are NaN and a simple mean of the first `period` true ranges seeds the
recursion, matching MT5 `iATR`. A reconstruction that smoothed from bar 0 would
drift for dozens of bars and produce mismatches resembling a formula error.

PDH/PDL/PDC come from the D1 bar **completed before** the decision bar's own
day, selected by date (the latest D1 bar of an earlier day), so a D1 export that
lacks the current forming day still yields yesterday's levels. Camarilla levels derive from the same previous-day bar; they are not packed
into `f00..f47` and so are not separately compared.

## Parity-exempt features

These are declared `PARITY_EXEMPT_DATA_DEPENDENT`, reported separately, and
**never counted as matching**:

| Feature | Why |
|---|---|
| `obiProxy` (f30) | Tick-flow proxy; the exact historical tick sequence is unavailable |
| `cvdProxy` (f31) | Same |
| `usdCompositeDirection` (f29) | **Only when the basket bars are not supplied.** Since S13 (2026-10-03) it is compared whenever the four basket symbols' bars are given (see Coverage) |
| `liqOrigin` (f46) | LIVE vs RECONSTRUCTED depends on EA process history, not market data |
| `newsRiskActive` (f47) | Calendar state at decision time is not reproducible offline |

`sole_basis_guard()` raises if a proposed feature set consists *only* of exempt
features: a model resting entirely on unverifiable inputs could never have those
inputs checked against the live engine, so it must not reach promotion however
good its backtest looks.

## Tolerance

Contract decided 2026-10-03 (B-PARITY-TOL, option A):

| Kind | Rule |
|---|---|
| Categorical (booleans, enums, bar counts) | exact equality, except rows in the reviewed tie register |
| Continuous | `abs_diff <= 1e-9` **OR** `rel_diff <= 1e-6` **OR** `abs_diff <= 0.5e-6 + abs(mql5) * 2**-23` |

Absolute tolerance carries values near zero, where a relative test is
meaningless — `1e-9` vs `2e-9` is a 100% relative difference and no error at
all. Non-finite values never count as a match, including `inf == inf`.

The third continuous term is the journal's own quantisation: the EA packs each
feature to float32 and writes it with 6 decimals (`DoubleToString(f, 6)`), so
a journalled value can differ from the engine's double by half a unit in the
6th decimal plus float32 rounding (bounded here at twice the float32 half-ulp).
`ParityConfig(journal_decimals=None)` restores the bare rule. Nothing is
rounded before comparison.

**Tie register** (`parity_accepted_ties.json`, `--accepted-ties`): human-accepted
exact floating-point ties at a decision threshold, and values that follow from
one, each with its root cause (`reports/pepperstone/B_PARITY_LIQ_ROOT_CAUSE.md`:
RC3 2.5-ATR acceptance tie, EDGE-2 1.20 displacement tie). An entry is accepted
only on the same symbol, decision bar and feature with the same MQL5 and Python
values; any other difference on that row still fails. Accepted ties are listed
in the report, never silently dropped. A new window's ties need review before
they are added.

## Causality

Reconstruction stands at `decision_ts`: the open time of the **closed** bar
whose features produced the decision. The bar at `decision_ts` is index 0 of the
series (MQL5 copies with `start_pos=1`, so its index 0 *is* that bar), and
nothing after it is reachable.

`test_reconstruction_never_sees_bars_after_decision_ts` truncates the entire
market history at `decision_ts` and asserts every feature is unchanged. If any
differed, future bars were being read.

The Asia session range is accumulated **incrementally**: a bar at 02:00 GMT sees
the range as of 02:00, never the completed 00:00–09:00 range known only at
09:00. As in MQL5 `UpdateSessionLevels`, the range restarts at the first GMT
hour-0 bar and is carried forward until the next one, so on Monday before GMT
00:00 the level is Friday's Asia range (see
`reports/pepperstone/B_PARITY_LIQ_ROOT_CAUSE.md`).

M5/M15/H1 windows contain only bars CLOSED at the decision clock, which is the
first tick of the next M1 bar (when MQL5 runs its new-bar logic and calls
`CopyRates(tf, 1, …)`). Normally that is `decision_ts + 1 min`; after a tick gap
(daily break, weekend, quiet minutes) it is the next M1 bar's open, so the
higher-timeframe bars that closed during the gap are visible (B-PARITY-EDGE-1).

Rows whose anchor is the Stage 2 epoch artifact (`1970`) are **skipped**, not
reconstructed against a fabricated timestamp.

## Fail-closed

Status is `FAIL` — and `assert_parity_or_halt()` raises — on any of:

* unsupported or mixed `schema_version`
* a missing `f00..f47` column
* feature order disagreeing with `PackFeatures()` (checked by reading the MQL5
  source for **order only**, never values)
* any categorical mismatch
* any continuous value outside tolerance
* zero rows causally reconstructable (an unestablished oracle is not a clean
  bill of health)
* a non-exempt feature that was never reconstructed — reported as
  `NOT_RECONSTRUCTED`, which is not a pass

## Two findings from building the fixtures

Both are properties of the feature definitions themselves, shared with the MQL5
implementation, and worth knowing before reading any parity report:

1. **A perfectly monotonic price path contains no swing points.** The strict
   definition requires a bar's neighbours to be lower on *both* sides, which a
   straight line never satisfies, so `trendState` reads `UNKNOWN`.

2. **Tied extremes defeat swing detection.** Because the test is `>=`, two
   consecutive bars sharing a high produce no swing there. Naively built
   synthetic bars tie at every turning point; real bars rarely do.

Neither is a defect. Both mean that flat or synthetic-looking data yields
`UNKNOWN` trend rather than a structure read.

## Files

| File | Purpose |
|---|---|
| `nexa_parity.py` | Oracle: reconstruction, comparison, fail-closed gate |
| `test_nexa_parity.py` | 45 tests, synthetic fixtures, no MT5 required |

No helper file was needed beyond these two.

## Next step (Stage 4, not started)

Export a Strategy Tester run to `NEXA_TradeDNA_*.csv`, ingest it with Stage 2,
export matching OHLC history per timeframe, and run this oracle. Its output is
the first real measurement of whether the two implementations agree.
