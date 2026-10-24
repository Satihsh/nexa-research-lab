# NEXA Outcome Labeler (Stage 4)

`nexa_labels.py` determines what actually happened after an executed trade,
using the trade's **actual** fill, **actual** SL/TP, and subsequent closed M1
bars.

## What it may and may not see

**May see:** market bars strictly inside `[label_start_ts, label_end_ts]`.

**May not see:** model predictions, AI probabilities, composite or quality
scores, strategy decisions, any feature value, or any bar beyond
`label_end_ts`.

Labels are the one place in NEXA permitted to use information after
`decision_ts` — that is what a label *is*. The guard is that a label never flows
back into a feature, and this module never reads one.

## The contract this implements (not invented here)

Every exit parameter is sourced from `NEXA_TrainingExport.mq5`, which is
Stage-1 locked and compiled:

| Parameter | Value | Meaning |
|---|---|---|
| `InpMaxHoldBars` | **480** | absolute horizon, M1 bars |
| `InpBreakevenAtR` | **1.00** | at +1.0R the effective SL becomes entry |
| `InpTimeExitBars` | **48** | conditional time exit checkpoint |
| `InpTimeExitMinR` | **0.30** | below this progress at the checkpoint, EA closes |

These mirror the EA's own `InpBreakevenAtR`, `InpTimeExitBars` and its `r < 0.3`
condition. No horizon was invented. Changing one requires changing the EA, the
exporter and this module together — a label computed under different exit rules
than the EA actually uses describes a trade that never existed.

## Two documented conflicts between the MQL5 exporter and this directive

Both are exposed as explicit policies rather than silently resolved. Picking
either side without saying so would put an undisclosed assumption into every
label in the dataset.

### 1. Ambiguous bars

`NEXA_TrainingExport.mq5` documents: a bar spanning both barriers resolves to
LOSS (`AMBIGUOUS_BAR_RESOLVED_LOSS`), flagged.

The Stage 4 directive requires AMBIGUOUS, never collapsed to win/loss, *unless a
deterministic rule exists in the NEXA execution contract*.

**Reading taken:** the exporter's rule is a *labelling convention*, not an
*execution contract*. At runtime the broker decides which barrier filled and the
EA is never told; nothing in the EA defines an ordering. So no execution
contract rule exists, and ambiguity stays ambiguous.

**Default:** `AmbiguityPolicy.AMBIGUOUS`.
**Opt-in:** `PESSIMISTIC_LOSS` reproduces the exporter exactly, for
like-for-like comparison runs.

### 2. The fill bar

The exporter starts its walk **at** the bar containing the fill, reasoning that
the EA fires at a new bar's open so the whole bar is post-entry.

The directive requires the first closed bar **after** the fill.

**Reading taken:** with asynchronous execution a fill can land mid-bar, and that
bar's extremes may predate the fill. Crediting them to the trade is a real bias.

**Default:** `FillBarPolicy.EXCLUDE_FILL_BAR`.
**Opt-in:** `INCLUDE_FILL_BAR` reproduces the exporter.

Whichever policies are active are recorded in `exec_model` on **every row**, so
a downstream reader can never mistake one convention for the other:

```
M1_OHLC_BE1R_TIMEEXIT48@0.3R_HORIZON480_AMBIGUOUS_EXCLUDE_FILL_BAR
```

## Label vocabulary

| Label | Meaning |
|---|---|
| `TP_WIN` | take-profit touched first |
| `SL_LOSS` | stop-loss touched first (ratchet not yet armed) |
| `BREAKEVEN_STOP` | stop touched after the +1R ratchet moved it to entry |
| `TIME_EXIT` | EA's conditional close at bar 48 with progress < 0.30R |
| `TIMEOUT` | horizon expired, or market data exhausted, with no barrier touched |
| `AMBIGUOUS` | one bar spanned both barriers; order unknowable from OHLC |
| `UNLABELLED` | not an executed trade (REJECTED, OPEN without FILL, orphan row) |
| `INVALID` | data defect — see `label_reason` |

`RESOLVED_LABELS` = TP_WIN, SL_LOSS, BREAKEVEN_STOP, TIME_EXIT, TIMEOUT.
`training_view()` returns only those. AMBIGUOUS, UNLABELLED and INVALID are
excluded rather than coerced: a label that had to be guessed teaches the model
the guess, not the market.

## Resolution order within a bar

When several conditions could fire on one bar, the walk mirrors the EA's own
management sequence:

1. both barriers inside the bar → policy
2. effective SL touched → `SL_LOSS` / `BREAKEVEN_STOP`
3. TP touched → `TP_WIN`
4. breakeven ratchet arms
5. conditional time exit → `TIME_EXIT`
6. horizon expiry → `TIMEOUT`

**Step 4 comes after the barrier tests deliberately.** The EA cannot move a stop
it has not yet survived; arming the ratchet first would let a bar that actually
hit the original SL be recorded as a breakeven scratch, converting real losses
into scratches throughout the dataset.

## MFE / MAE

Both are magnitudes in R, non-negative, measured over
`[label_start_ts, label_end_ts]` using the trade's actual risk distance
`risk_dist = |entry_actual − sl_price|`.

| Direction | MFE | MAE |
|---|---|---|
| LONG | `(max high − entry) / risk` | `(entry − min low) / risk` |
| SHORT | `(entry − min low) / risk` | `(max high − entry) / risk` |

Excursions are measured on each bar **before** any exit resolves, so a bar that
extends favourably *and* stops out still reports its MFE. Nothing after
`label_end_ts` is counted — asserted by test with a deliberately enormous
subsequent bar.

`target_r` is never substituted for MFE. MFE reports what price did; `target_r`
reports what was aimed at.

## Episodes and partial closes

`OPEN → FILL → PARTIAL_CLOSE* → CLOSE` is **one episode producing one label**,
attached to every row of that episode. A partial close is management inside one
trade, not a second trade. Counting each partial as an independent example would
inflate the sample with correlated duplicates — the kind of quiet inflation that
makes a model look better than it is.

`training_view()` emits one row per episode (the OPEN row, which carries the
features), never one per partial.

The first FILL anchors the episode's entry, SL, TP and `label_start_ts`.

## result_r

Broker-realised `result_r` from the CLOSE row is **preserved verbatim** and never
overwritten by the label. The two are separate facts and may legitimately
disagree — a TP_WIN barrier label with a negative broker result is possible after
costs, and is recorded as such. No synthetic profit figure is manufactured.

Commission and swap remain execution fields, entirely separate from the barrier
label.

## Fail-closed

`LabelContractError` is raised for unsupported `schema_version` or a dataset
lacking `episode_id`/`event` (Stage 2 ingestion must run first).

Rows are labelled `INVALID` — never repaired — for: invalid barrier geometry
(LONG with SL above entry, SHORT with TP above entry), zero or negative risk
distance, invalid direction, missing `fill_ts`, epoch `fill_ts`
(`IMPOSSIBLE_FILL_TS`), missing `entry_actual`, or no market data after the fill.

`entry_intended` is **never** substituted for a missing `entry_actual`: the trade
that existed is the one that filled.

`label_dataset(...).ok` is `False` when any ERROR finding is present.

## Usage

```bash
python nexa_labels.py canonical.csv \
    --m1 EURUSD=eurusd_m1.csv --m1 GBPUSD=gbpusd_m1.csv \
    -o labelled.csv --training-view training.csv

# reproduce the MQL5 exporter's conventions exactly
python nexa_labels.py canonical.csv --m1 EURUSD=eurusd_m1.csv \
    --ambiguity PESSIMISTIC_LOSS --fill-bar INCLUDE_FILL_BAR
```

Exit code 0 only when no ERROR finding is present.

## Output

Stage 4 appends `label_start_ts`, `label_end_ts`, `label`, `label_reason`,
`ambiguous_bar`, `bars_to_outcome`, `mfe_r`, `mae_r`, `exec_model`.

All Stage 2 columns are preserved; no original MT5 field is overwritten.

## Unresolved contract ambiguity

Beyond the two policy conflicts above, one gap is inherited from the exporter and
carried forward unchanged:

**Partial close at `InpPartialCloseAtR = 1.5R` is not modelled.** The EA closes
half the position at +1.5R, after which the remaining position has a different
effective size. This walk treats the episode as one unit, so a labelled TP_WIN
on a partially-closed trade overstates the realised R relative to the blend the
EA actually held. `result_r` from the broker remains correct; the *label* is the
approximation. Resolving it needs either volume-weighted outcome tracking or an
EA change, and both are outside Stage 4.

Also not modelled: bid/ask on the exit side, slippage, commission, swap, and the
intrabar path (M1 OHLC only).

## Files

| File | Purpose |
|---|---|
| `nexa_labels.py` | Labeler, episode assembly, fail-closed contract |
| `test_nexa_labels.py` | 57 tests, synthetic OHLC, no MT5 required |
