# NEXA Research Tier

Offline research tooling. **Nothing here executes trades or runs inside MT5.**
The live tier (MQL5) and this tier exchange exactly two artifacts:

```
MT5  --(Trade DNA CSV, schema v1.0)-->  research
MT5  <--(calibrated ONNX + calibration map)--  research     [seam L1, not yet built]
```

## Status

| Stage / Gate | Module | Status (2026-09-27) |
|---|---|---|
| 2 | `nexa_ingest.py` | built |
| 3 | `nexa_parity.py` | built; never run on real MQL5 output |
| 4 | `nexa_labels.py` | built; never run on real trades |
| 5 | `nexa_validate.py` | built; fails closed (`EMPTY_DATASET`) until Trade DNA exists |
| 5 (data) | `nexa_marketdata.py` | built; ran on Axiory XAUUSD |
| Gate 8 | `nexa_stats.py` | built: expectancy, PF, drawdown, bootstrap CI, Monte Carlo ruin, cost shocks, conservative verdict |
| Gates 10/12 | `nexa_robust.py` | built: BH-FDR, PSR/DSR, PBO (CSCV), walk-forward windows |
| Gate 10 | `nexa_factory.py`, `nexa_factory_run.py` | built; first run on XAUUSD H1 found **no candidate** (`reports/FACTORY_XAUUSD_H1.md`) |
| Gate 9 | `nexa_model.py` | built: meta-label (veto-only), forward-only isotonic calibration, model gate, append-only registry. **No model trained**: needs Trade DNA |
| — | `test_nexa_mql5_invariants.py` | static guards on NEXA_Risk.mqh, the FOMC table, and the PackFeatures width |
| 12 (export) | ONNX export | not built (`skl2onnx` not installed; blocked on a trained model anyway) |

## Stage 2 — `nexa_ingest.py`

Loads, validates and links NEXA Trade DNA exports into a canonical research
frame. It does not train, label, calibrate, score or export anything.

```bash
python nexa_ingest.py NEXA_TradeDNA_EURUSD.csv \
    --schema ../nexa_schema_v1.json -o canonical.parquet
python -m pytest test_nexa_ingest.py -v
```

Exit code is 0 only when no ERROR-level finding was raised.

### The rule this module exists to protect

`f00..f47` are consumed **exactly as MQL5 wrote them**. Python never recomputes
a feature here. Recomputing even one slightly differently would train a model on
values the live engine never sees — a failure that is silent, passes every unit
test, and presents in production as alpha decay. Feature recomputation belongs
solely to the parity oracle (Stage 3), whose whole purpose is to compare the two
implementations and halt training on a mismatch.

### Timestamp semantics

| Column | Meaning |
|---|---|
| `decision_ts` | Open time of the **closed bar** whose features produced the decision. The causality anchor. |
| `dispatch_ts` | Order sent to the server. Empty on non-dispatch rows. |
| `fill_ts` | Broker deal execution time. |
| `write_ts` | Wall-clock line write. **Diagnostic only** — carries no causal meaning and is never a sort key or a substitute anchor. |
| `label_start_ts` / `label_end_ts` | Reserved for Stage 4. Not produced here. |

### Known upstream artifact, handled explicitly

`NEXA_EA.mq5` writes FILL / PARTIAL_CLOSE / CLOSE / REJECTED rows from a blank
`NexaSignal`, whose `decisionBarTime` is 0 — rendered by MQL5 as
`1970.01.01 00:00:00`. Those rows carry an epoch `decision_ts` that is not a
real decision time.

The loader treats epoch as **missing** (`NaT`), raises `EPOCH_DECISION_TS`, and
recovers the true anchor by linking each execution row to its originating `OPEN`
row. Two columns make the recovery auditable:

- `decision_ts_effective` — own anchor if present, else the episode's `OPEN` anchor
- `decision_ts_inherited` — `True` when the value was inherited

The original `decision_ts` is never overwritten. No MT5 source was changed to
work around this; it is a Stage 1 property, recorded rather than hidden.

### `ai_raw_p` is raw

`calibration_id` is `"NONE"` until seam L1 exists. Until then `ai_raw_p` is raw
model output and must **not** be read as an empirical frequency. `-1.0` is the
documented "no model participated" sentinel, not an out-of-range probability, and
is validated as such.

### Validation findings

ERROR means the dataset is not trustworthy as-is; `write_canonical()` refuses to
write unless `allow_errors=True`. WARN means an anomaly worth knowing about with
rows still usable.

**ERROR** — `MIXED_SCHEMA_VERSIONS`, `UNSUPPORTED_SCHEMA`, `MISSING_COLUMNS`,
`MALFORMED_TIMESTAMP`, `MISSING_DECISION_TS`, `DUPLICATE_ROW_ID`,
`DUPLICATE_ROW_ID_ACROSS_FILES`, `EMPTY_ROW_ID`, `EMPTY_SYMBOL`,
`EMPTY_TIMEFRAME`, `INVALID_EVENT`, `INVALID_DIRECTION`, `NON_NUMERIC_FEATURE`,
`NONFINITE_FEATURES`, `INVERTED_QUOTE`, `NONPOSITIVE_LOTS`, `NEGATIVE_ATR`,
`NEGATIVE_SPREAD`, `AI_P_OUT_OF_RANGE`, `QUALITY_OUT_OF_RANGE`,
`BARRIERS_WRONG_SIDE_LONG`, `BARRIERS_WRONG_SIDE_SHORT`

**WARN** — `EPOCH_DECISION_TS`, `MISSING_FILL_TS`, `SPREAD_MISMATCH`,
`INCONSISTENT_SYMBOL`, `INCONSISTENT_TIMEFRAME`, `ORPHAN_EXECUTION_ROW`,
`UNDECLARED_COLUMNS`, `NON_NUMERIC_FIELD`

### Determinism

Output is sorted by `decision_ts_effective`, then original file order
(`source_row`), via a stable mergesort. `write_ts` is deliberately not a sort
key. Loading the same file twice yields an identical frame — asserted by test.

## Provenance of methods

No third-party repository code is copied into this tier. Methods adopted:

| Method | Source repository | Licence |
|---|---|---|
| Purged CV, embargo, in-fold feature selection, walk-forward retrain | `handiko/machine-learning-stock-backtesting` | present |
| Isotonic calibration, Brier/ECE, delayed outcome resolution, cost re-costing | `mohamadomar-ai/kairos-engine` | present |
| Event-driven fill semantics reference | `MiniBtMaster/minibt` | present |
| WAL intent-before-action (live tier, seam L7) | `lotey/lite-qmt-executor` | present |

`zillionare/qmt-gateway`, `naka2027/polymarket-bot` and `Harry0405LIU/fin-cn-agent`
carry **no licence file**; default copyright applies and no code from them may be
copied. They were read for ideas only.

## Dependencies

`pandas`, `numpy`. `pytest` for tests. `pyarrow` optional (parquet output; the
writer falls back to CSV automatically when absent).
