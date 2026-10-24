"""
nexa_ingest.py -- Stage 2 of NEXA_IMPLEMENTATION_PLAN_V3.

Canonical ingestion of NEXA Trade DNA CSV exports into a research dataset.

SCOPE (deliberately narrow)
---------------------------
This module LOADS, VALIDATES and LINKS. It does not train, label, calibrate,
score, discover, ablate, export ONNX, or run a shadow. Those are later stages
and are absent here on purpose.

THE ONE RULE THAT MATTERS MOST
------------------------------
f00..f47 are consumed EXACTLY as MQL5 wrote them. Python never recomputes a
feature here. If Python recomputed even one of them slightly differently, a
model would be trained on values the live engine never actually sees -- a
failure that is silent, survives every unit test, and looks exactly like alpha
decay in production. Recomputation belongs solely to the parity oracle
(nexa_parity.py, a later stage) whose entire purpose is to compare the two.

TIMESTAMP SEMANTICS (preserved, never conflated)
------------------------------------------------
decision_ts     Open time of the CLOSED bar whose features produced the
                decision. The causality anchor: a feature is legitimate only
                if computable from data at or before this instant.
dispatch_ts     Order sent to the server. Empty on non-dispatch rows.
fill_ts         Broker deal execution time. FILL/PARTIAL_CLOSE/CLOSE only.
write_ts        Wall-clock line-write time. DIAGNOSTIC ONLY. This module will
                never substitute it for decision_ts, and downstream code must
                not either -- it is the one timestamp that carries no causal
                meaning.
label_start_ts  Reserved for the labeler (= fill_ts). Not produced here.
label_end_ts    Reserved for the labeler. Not produced here.

KNOWN UPSTREAM ARTIFACT (Stage 1, handled here, not silently patched)
---------------------------------------------------------------------
NEXA_EA.mq5 writes FILL / PARTIAL_CLOSE / CLOSE / REJECTED rows from a blank
NexaSignal, whose decisionBarTime is 0. MQL5 renders that as
"1970.01.01 00:00:00". Those rows therefore carry an epoch decision_ts that is
NOT a real decision time.

This module treats epoch decision_ts as MISSING (NaT), reports it as a finding,
and recovers the true value by linking the row to its originating OPEN row
(see "episode linking"). It does not rewrite MT5 source to fix it -- that would
be out of Stage 2 scope -- and it does not pretend the raw value is usable.

ai_raw_p
--------
RAW model output. NOT a calibrated probability. calibration_id is "NONE" until
seam L1 exists. This module preserves the distinction in both the column name
and the schema check; nothing here may treat 0.8 as "80% of the time".

Self-contained: pandas + numpy only.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import pandas as pd

SUPPORTED_SCHEMA_VERSIONS = ("1.0",)
FEATURE_COUNT = 48
FEATURE_COLUMNS = [f"f{i:02d}" for i in range(FEATURE_COUNT)]

VALID_EVENTS = ("DECISION", "OPEN", "FILL", "PARTIAL_CLOSE", "CLOSE", "REJECTED")

#: Rows written from a blank NexaSignal carry this rendered zero datetime.
EPOCH_SENTINELS = ("1970.01.01 00:00:00", "1970.01.01", "1970-01-01 00:00:00")

#: MQL5 TimeToString(TIME_DATE|TIME_SECONDS) format, and the date-only variant.
MT5_DATETIME_FORMATS = ("%Y.%m.%d %H:%M:%S", "%Y.%m.%d")

REQUIRED_COLUMNS = (
    "schema_version", "row_id", "write_ts", "decision_ts", "dispatch_ts", "fill_ts",
    "symbol", "timeframe", "event", "strategy_id", "direction", "decision_source",
    "bid", "ask", "spread", "spread_atr_ratio", "atr",
    "composite_score", "quality_score",
    "entry_intended", "entry_actual", "sl_price", "tp_price", "lots",
    "slippage_points", "commission", "swap", "result_r",
    "model_id", "model_schema_version", "calibration_id", "ai_raw_p",
    "reason",
) + tuple(FEATURE_COLUMNS)

TIMESTAMP_COLUMNS = ("write_ts", "decision_ts", "dispatch_ts", "fill_ts", "pd_src_bar")

NUMERIC_COLUMNS = (
    "direction", "bid", "ask", "spread", "spread_atr_ratio", "atr", "atr_m15",
    "regime_trend", "regime_vol", "regime_transitioning",
    "pdh", "pdl", "pdc", "liq_setup", "liq_origin", "liq_level", "liq_state",
    "composite_score", "quality_score",
    "entry_intended", "entry_actual", "sl_price", "tp_price", "target_r",
    "risk_dist", "lots", "slippage_points", "commission", "swap", "result_r",
    "ai_raw_p",
) + tuple(FEATURE_COLUMNS)


class Severity(str, Enum):
    ERROR = "ERROR"      # dataset is not trustworthy for research as-is
    WARN = "WARN"        # anomaly worth knowing; rows remain usable
    INFO = "INFO"


@dataclass(frozen=True)
class Finding:
    severity: Severity
    code: str
    message: str
    count: int = 0
    rows: tuple = field(default_factory=tuple)   # up to 10 example row indices

    def __str__(self) -> str:
        loc = f" (e.g. rows {list(self.rows)})" if self.rows else ""
        return f"[{self.severity.value}] {self.code}: {self.message} n={self.count}{loc}"


@dataclass
class IngestResult:
    frame: pd.DataFrame
    findings: list
    stats: dict

    @property
    def ok(self) -> bool:
        """True when nothing ERROR-level was found."""
        return not any(f.severity is Severity.ERROR for f in self.findings)

    def errors(self) -> list:
        return [f for f in self.findings if f.severity is Severity.ERROR]

    def report(self) -> str:
        lines = [
            "NEXA Trade DNA ingestion report",
            "=" * 60,
            f"source        : {self.stats.get('source')}",
            f"schema        : {self.stats.get('schema_version')}",
            f"rows in       : {self.stats.get('rows_in')}",
            f"rows out      : {self.stats.get('rows_out')}",
            f"symbols       : {self.stats.get('symbols')}",
            f"timeframes    : {self.stats.get('timeframes')}",
            f"events        : {self.stats.get('event_counts')}",
            f"episodes      : {self.stats.get('episodes')}",
            f"status        : {'OK' if self.ok else 'ERRORS PRESENT'}",
            "-" * 60,
        ]
        lines += [str(f) for f in self.findings] or ["(no findings)"]
        return "\n".join(lines)


class SchemaVersionError(ValueError):
    """Raised when a file's schema_version is absent or unsupported."""


def _examples(mask: pd.Series, limit: int = 10) -> tuple:
    idx = mask[mask].index.tolist()[:limit]
    return tuple(int(i) for i in idx)


def _parse_mt5_datetime(series: pd.Series) -> pd.Series:
    """
    Parse MQL5 TimeToString output without inventing values.

    Empty strings become NaT -- an absent dispatch_ts means the row was not a
    dispatch, which is information, not a defect. Epoch sentinels also become
    NaT: a blank-signal row's rendered zero is not a real timestamp, and
    silently keeping 1970 would put a decade-wrong anchor into the dataset.
    """
    s = series.fillna("").astype(str).str.strip()
    s = s.mask(s.isin(EPOCH_SENTINELS), "")
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    remaining = s != ""
    for fmt in MT5_DATETIME_FORMATS:
        if not remaining.any():
            break
        parsed = pd.to_datetime(s.where(remaining), format=fmt, errors="coerce")
        out = out.fillna(parsed)
        remaining = remaining & out.isna()
    return out


def _to_numeric_strict(series: pd.Series) -> tuple:
    """
    Convert to float64, reporting which entries were non-numeric and non-empty.

    Empty is legitimate (a field not applicable to this event type) and yields
    NaN without a complaint. A non-empty unparseable value is a real defect and
    is reported, because it means the writer emitted something unexpected.
    """
    raw = series.fillna("").astype(str).str.strip()
    converted = pd.to_numeric(raw.replace("", np.nan), errors="coerce")
    bad = (raw != "") & converted.isna()
    return converted.astype("float64"), bad


def read_schema(path: str) -> dict:
    """Load nexa_schema_v1.json. Optional: the loader works without it."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_trade_dna(
    path: str,
    *,
    schema_path: str | None = None,
    strict_schema: bool = True,
) -> IngestResult:
    """
    Load one Trade DNA CSV into a canonical research frame.

    Parameters
    ----------
    path : CSV produced by NEXA_EA.mq5 (schema v1.0).
    schema_path : optional nexa_schema_v1.json for column-set cross-checking.
    strict_schema : raise SchemaVersionError on an unsupported schema_version.
                    Set False only to inspect a rejected file.

    Raises
    ------
    SchemaVersionError : unsupported/missing schema_version (when strict).
    FileNotFoundError  : no such file.
    """
    findings: list = []
    stats: dict = {"source": os.path.basename(path)}

    # Read every column as text. Letting pandas infer dtypes would coerce empty
    # timestamp fields to NaN-of-float and silently re-type mixed columns before
    # validation has had a chance to look at them.
    frame = pd.read_csv(path, dtype=str, keep_default_na=False, na_filter=False)
    stats["rows_in"] = len(frame)
    frame.columns = [c.strip() for c in frame.columns]

    # ---- schema version -------------------------------------------------
    if "schema_version" not in frame.columns:
        raise SchemaVersionError(
            f"{path}: no schema_version column. This is not a NEXA schema v1.0 "
            f"Trade DNA export (pre-v1.0 journals used a different header)."
        )
    versions = sorted(set(frame["schema_version"].str.strip())) if len(frame) else []
    stats["schema_version"] = versions[0] if len(versions) == 1 else versions
    if len(versions) > 1:
        findings.append(Finding(
            Severity.ERROR, "MIXED_SCHEMA_VERSIONS",
            f"file mixes schema versions {versions}; a single file must be one schema",
            count=len(versions)))
    unsupported = [v for v in versions if v not in SUPPORTED_SCHEMA_VERSIONS]
    if unsupported:
        msg = (f"{path}: unsupported schema_version {unsupported}; "
               f"this loader supports {list(SUPPORTED_SCHEMA_VERSIONS)}")
        if strict_schema:
            raise SchemaVersionError(msg)
        findings.append(Finding(Severity.ERROR, "UNSUPPORTED_SCHEMA", msg,
                                count=len(unsupported)))

    # ---- required columns ------------------------------------------------
    missing = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
    if missing:
        findings.append(Finding(
            Severity.ERROR, "MISSING_COLUMNS",
            f"required columns absent: {missing[:12]}"
            + (f" (+{len(missing) - 12} more)" if len(missing) > 12 else ""),
            count=len(missing)))
        # Without the feature block or the key identity columns nothing
        # downstream is meaningful, so stop rather than emit a broken frame.
        if any(c in missing for c in ("row_id", "event", "decision_ts")) or \
           any(c in missing for c in FEATURE_COLUMNS):
            stats["rows_out"] = 0
            return IngestResult(frame.iloc[0:0].copy(), findings, stats)

    if schema_path and os.path.exists(schema_path):
        declared = set(read_schema(schema_path).get("mt5_columns", []))
        extra = [c for c in frame.columns if c not in declared]
        if extra:
            findings.append(Finding(
                Severity.WARN, "UNDECLARED_COLUMNS",
                f"columns not in the schema contract: {extra[:8]}", count=len(extra)))

    out = pd.DataFrame(index=frame.index)

    # ---- identity / provenance (kept verbatim) ---------------------------
    passthrough = [
        "schema_version", "row_id", "symbol", "timeframe", "event",
        "decision_source", "session_tag", "pd_src_bar", "strategy_id",
        "model_id", "model_schema_version", "calibration_id", "reason",
    ]
    for col in passthrough:
        if col in frame.columns:
            out[col] = frame[col].astype(str).str.strip()

    # ---- timestamps ------------------------------------------------------
    for col in TIMESTAMP_COLUMNS:
        if col not in frame.columns:
            continue
        raw = frame[col].astype(str).str.strip()
        parsed = _parse_mt5_datetime(raw)
        malformed = (raw != "") & (~raw.isin(EPOCH_SENTINELS)) & parsed.isna()
        if malformed.any():
            findings.append(Finding(
                Severity.ERROR, "MALFORMED_TIMESTAMP",
                f"{col} unparseable as MQL5 datetime", count=int(malformed.sum()),
                rows=_examples(malformed)))
        if col == "decision_ts":
            epoch = raw.isin(EPOCH_SENTINELS)
            if epoch.any():
                findings.append(Finding(
                    Severity.WARN, "EPOCH_DECISION_TS",
                    "decision_ts rendered as 1970 (row written from a blank signal); "
                    "treated as missing and recovered via episode linking where possible",
                    count=int(epoch.sum()), rows=_examples(epoch)))
        out[col] = parsed

    # ---- numerics --------------------------------------------------------
    for col in NUMERIC_COLUMNS:
        if col not in frame.columns:
            continue
        converted, bad = _to_numeric_strict(frame[col])
        if bad.any():
            sev = Severity.ERROR if col in FEATURE_COLUMNS else Severity.WARN
            code = "NON_NUMERIC_FEATURE" if col in FEATURE_COLUMNS else "NON_NUMERIC_FIELD"
            findings.append(Finding(
                sev, code, f"{col} contains non-numeric values",
                count=int(bad.sum()), rows=_examples(bad)))
        out[col] = converted

    # non-finite feature values would poison any model silently
    present_features = [c for c in FEATURE_COLUMNS if c in out.columns]
    if present_features:
        feat = out[present_features]
        nonfinite = ~np.isfinite(feat.to_numpy(dtype="float64", na_value=np.nan))
        rowmask = pd.Series(nonfinite.any(axis=1), index=out.index)
        # A DECISION row may legitimately hold an unpacked (empty) feature block.
        if "event" in out.columns:
            rowmask = rowmask & out["event"].isin(("OPEN", "FILL"))
        if rowmask.any():
            findings.append(Finding(
                Severity.ERROR, "NONFINITE_FEATURES",
                "OPEN/FILL rows carry NaN or infinite feature values",
                count=int(rowmask.sum()), rows=_examples(rowmask)))
        out["features_complete"] = ~pd.Series(
            nonfinite.any(axis=1), index=out.index)

    # ---- structural validation ------------------------------------------
    _validate_events(out, findings)
    _validate_identity(out, findings)
    _validate_numeric_sanity(out, findings)

    # ---- episode linking -------------------------------------------------
    out = _link_episodes(out, findings)

    # ---- deterministic ordering -----------------------------------------
    # Sort by the causal anchor, then by file order. write_ts is deliberately
    # NOT a sort key: it carries no causal meaning.
    out["source_row"] = np.arange(len(out), dtype="int64")
    sort_anchor = out["decision_ts_effective"] if "decision_ts_effective" in out.columns \
        else out.get("decision_ts")
    if sort_anchor is not None:
        out = out.assign(_anchor=sort_anchor).sort_values(
            ["_anchor", "source_row"], kind="mergesort", na_position="last"
        ).drop(columns=["_anchor"]).reset_index(drop=True)

    stats["rows_out"] = len(out)
    stats["symbols"] = sorted(set(out["symbol"])) if "symbol" in out.columns else []
    stats["timeframes"] = sorted(set(out["timeframe"])) if "timeframe" in out.columns else []
    stats["event_counts"] = (out["event"].value_counts().to_dict()
                             if "event" in out.columns else {})
    stats["episodes"] = int(out["episode_id"].nunique()) if "episode_id" in out.columns else 0
    return IngestResult(out, findings, stats)


def _validate_events(out: pd.DataFrame, findings: list) -> None:
    if "event" not in out.columns:
        return
    bad = ~out["event"].isin(VALID_EVENTS)
    if bad.any():
        findings.append(Finding(
            Severity.ERROR, "INVALID_EVENT",
            f"event outside {list(VALID_EVENTS)}",
            count=int(bad.sum()), rows=_examples(bad)))

    # decision_ts is required on rows that represent a decision the engine took
    if "decision_ts" in out.columns:
        needs = out["event"].isin(("DECISION", "OPEN"))
        missing = needs & out["decision_ts"].isna()
        if missing.any():
            findings.append(Finding(
                Severity.ERROR, "MISSING_DECISION_TS",
                "DECISION/OPEN row without a usable decision_ts",
                count=int(missing.sum()), rows=_examples(missing)))

    # fill_ts should exist wherever a deal occurred
    if "fill_ts" in out.columns:
        needs = out["event"].isin(("FILL", "PARTIAL_CLOSE", "CLOSE"))
        missing = needs & out["fill_ts"].isna()
        if missing.any():
            findings.append(Finding(
                Severity.WARN, "MISSING_FILL_TS",
                "deal row without fill_ts", count=int(missing.sum()),
                rows=_examples(missing)))


def _validate_identity(out: pd.DataFrame, findings: list) -> None:
    if "row_id" in out.columns:
        dup = out["row_id"].duplicated(keep=False) & (out["row_id"] != "")
        if dup.any():
            findings.append(Finding(
                Severity.ERROR, "DUPLICATE_ROW_ID",
                "row_id must be unique; duplicates usually mean two journal files "
                "were concatenated or a run was restarted into the same file",
                count=int(dup.sum()), rows=_examples(dup)))
        empty = out["row_id"] == ""
        if empty.any():
            findings.append(Finding(
                Severity.ERROR, "EMPTY_ROW_ID", "row_id is blank",
                count=int(empty.sum()), rows=_examples(empty)))

    for col, code in (("symbol", "INCONSISTENT_SYMBOL"),
                      ("timeframe", "INCONSISTENT_TIMEFRAME")):
        if col in out.columns:
            vals = sorted(set(out[col]) - {""})
            if len(vals) > 1:
                findings.append(Finding(
                    Severity.WARN, code,
                    f"file mixes {col} values {vals}; one journal file is expected to "
                    f"cover a single {col}", count=len(vals)))
            if (out[col] == "").any():
                findings.append(Finding(
                    Severity.ERROR, f"EMPTY_{col.upper()}",
                    f"{col} is blank", count=int((out[col] == "").sum()),
                    rows=_examples(out[col] == "")))

    if "direction" in out.columns and "event" in out.columns:
        trading = out["event"].isin(("OPEN", "FILL", "PARTIAL_CLOSE", "CLOSE"))
        bad = trading & ~out["direction"].isin((1.0, -1.0))
        if bad.any():
            findings.append(Finding(
                Severity.ERROR, "INVALID_DIRECTION",
                "trade row with direction not in {+1,-1}",
                count=int(bad.sum()), rows=_examples(bad)))


def _validate_numeric_sanity(out: pd.DataFrame, findings: list) -> None:
    """Impossible values. Each check states why the value cannot occur."""
    def flag(mask: pd.Series, code: str, msg: str, sev=Severity.ERROR) -> None:
        if mask.any():
            findings.append(Finding(sev, code, msg, count=int(mask.sum()),
                                    rows=_examples(mask)))

    ev = out["event"] if "event" in out.columns else pd.Series("", index=out.index)

    if {"bid", "ask"} <= set(out.columns):
        quoted = out["bid"].notna() & out["ask"].notna() & (out["bid"] > 0)
        flag(quoted & (out["ask"] < out["bid"]), "INVERTED_QUOTE",
             "ask below bid: a crossed quote cannot be a decision input")
        if "spread" in out.columns:
            recomputed = out["ask"] - out["bid"]
            drift = quoted & out["spread"].notna() & (
                (out["spread"] - recomputed).abs() > 1e-6)
            flag(drift, "SPREAD_MISMATCH",
                 "spread does not equal ask-bid", sev=Severity.WARN)

    if "lots" in out.columns:
        flag(ev.isin(("OPEN", "FILL")) & (out["lots"] <= 0), "NONPOSITIVE_LOTS",
             "an executed row with zero or negative volume")

    for col in ("atr", "spread"):
        if col in out.columns:
            flag(out[col].notna() & (out[col] < 0), f"NEGATIVE_{col.upper()}",
                 f"{col} cannot be negative")

    if "ai_raw_p" in out.columns:
        # -1 is the documented "model unavailable" sentinel, not a probability.
        bad = out["ai_raw_p"].notna() & (out["ai_raw_p"] != -1.0) & (
            (out["ai_raw_p"] < 0.0) | (out["ai_raw_p"] > 1.0))
        flag(bad, "AI_P_OUT_OF_RANGE",
             "ai_raw_p outside [0,1] and not the -1 unavailable sentinel")

    if "quality_score" in out.columns:
        bad = out["quality_score"].notna() & (
            (out["quality_score"] < 0) | (out["quality_score"] > 10))
        flag(bad, "QUALITY_OUT_OF_RANGE", "quality_score outside 0..10")

    # SL/TP must straddle entry correctly for the stated direction
    if {"entry_intended", "sl_price", "tp_price", "direction"} <= set(out.columns):
        live = ev.isin(("OPEN", "FILL")) & (out["sl_price"] > 0) & (out["tp_price"] > 0) \
            & (out["entry_intended"] > 0)
        longs = live & (out["direction"] == 1.0)
        shorts = live & (out["direction"] == -1.0)
        flag(longs & ~((out["sl_price"] < out["entry_intended"]) &
                       (out["tp_price"] > out["entry_intended"])),
             "BARRIERS_WRONG_SIDE_LONG",
             "long row where SL is not below and TP not above entry")
        flag(shorts & ~((out["sl_price"] > out["entry_intended"]) &
                        (out["tp_price"] < out["entry_intended"])),
             "BARRIERS_WRONG_SIDE_SHORT",
             "short row where SL is not above and TP not below entry")


def _link_episodes(out: pd.DataFrame, findings: list) -> pd.DataFrame:
    """
    Group rows into trade episodes: OPEN -> FILL -> PARTIAL_CLOSE* -> CLOSE.

    Why this exists: FILL/CLOSE rows are written from a blank signal, so they
    carry neither the feature block nor a real decision_ts. The decision that
    produced them lives on the preceding OPEN row. Linking recovers that
    association explicitly rather than leaving later stages to guess by
    proximity.

    `decision_ts_effective` is the row's own decision_ts when it has one, else
    the episode's OPEN decision_ts. The original column is never overwritten --
    a consumer that needs to know a value was inherited can compare the two.
    """
    if "event" not in out.columns:
        return out

    episode_id = np.full(len(out), -1, dtype="int64")
    open_decision = pd.Series(pd.NaT, index=out.index, dtype="datetime64[ns]")
    current = -1
    seen_open = False
    orphan_rows = []

    events = out["event"].tolist()
    decisions = out["decision_ts"].tolist() if "decision_ts" in out.columns else [pd.NaT] * len(out)

    for i, ev in enumerate(events):
        if ev == "OPEN":
            current += 1
            seen_open = True
            episode_id[i] = current
            open_decision.iloc[i] = decisions[i]
        elif ev in ("FILL", "PARTIAL_CLOSE", "CLOSE", "REJECTED"):
            if not seen_open:
                orphan_rows.append(i)
                continue
            episode_id[i] = current
            open_decision.iloc[i] = open_decision.iloc[
                int(np.flatnonzero(episode_id == current)[0])]
            if ev in ("CLOSE", "REJECTED"):
                seen_open = False      # episode is finished
        # DECISION rows are standalone observations; they belong to no episode.

    if orphan_rows:
        findings.append(Finding(
            Severity.WARN, "ORPHAN_EXECUTION_ROW",
            "FILL/CLOSE/REJECTED row with no preceding OPEN in this file "
            "(usually a journal that begins mid-trade)",
            count=len(orphan_rows), rows=tuple(orphan_rows[:10])))

    out = out.copy()
    out["episode_id"] = episode_id
    if "decision_ts" in out.columns:
        out["decision_ts_effective"] = out["decision_ts"].fillna(open_decision)
        out["decision_ts_inherited"] = out["decision_ts"].isna() & \
            out["decision_ts_effective"].notna()
    return out


def write_canonical(result: IngestResult, path: str, *, allow_errors: bool = False) -> str:
    """
    Write the canonical dataset deterministically.

    Refuses by default when ERROR-level findings exist: an unusable dataset that
    looks usable is worse than no dataset, because every downstream stage would
    inherit the defect silently.

    Parquet when pyarrow is available (preserves dtypes exactly), else CSV with
    ISO-8601 timestamps.
    """
    if not result.ok and not allow_errors:
        raise ValueError(
            "refusing to write a canonical dataset with ERROR findings:\n  "
            + "\n  ".join(str(f) for f in result.errors())
            + "\nPass allow_errors=True only to inspect the damage."
        )
    frame = result.frame.copy()
    if path.endswith(".parquet"):
        try:
            frame.to_parquet(path, index=False)
            return path
        except Exception:  # noqa: BLE001 - any pyarrow/fastparquet failure is a
            # non-fatal capability gap, not a data problem: fall back to CSV so
            # ingestion still produces a usable artifact on a minimal install.
            path = path[: -len(".parquet")] + ".csv"
    for col in frame.columns:
        if pd.api.types.is_datetime64_any_dtype(frame[col]):
            frame[col] = frame[col].dt.strftime("%Y-%m-%dT%H:%M:%S").fillna("")
    frame.to_csv(path, index=False, lineterminator="\n")
    return path


def load_many(paths, **kwargs) -> IngestResult:
    """
    Load several journals (one per symbol) into one frame.

    Each file is validated independently first, so a defect in one symbol is
    attributed to that file rather than surfacing as a confusing cross-symbol
    anomaly after concatenation.
    """
    frames, findings, per_file = [], [], {}
    for p in paths:
        res = load_trade_dna(p, **kwargs)
        tagged = [Finding(f.severity, f.code, f"{os.path.basename(p)}: {f.message}",
                          f.count, f.rows) for f in res.findings]
        findings.extend(tagged)
        per_file[os.path.basename(p)] = res.stats
        if len(res.frame):
            fr = res.frame.copy()
            fr["source_file"] = os.path.basename(p)
            frames.append(fr)

    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if len(combined) and "row_id" in combined.columns:
        dup = combined["row_id"].duplicated(keep=False) & (combined["row_id"] != "")
        if dup.any():
            findings.append(Finding(
                Severity.ERROR, "DUPLICATE_ROW_ID_ACROSS_FILES",
                "the same row_id appears in more than one file",
                count=int(dup.sum()), rows=_examples(dup)))
    stats = {
        "source": f"{len(paths)} file(s)",
        "rows_in": sum(s.get("rows_in", 0) for s in per_file.values()),
        "rows_out": len(combined),
        "symbols": sorted(set(combined["symbol"])) if len(combined) and "symbol" in combined else [],
        "timeframes": sorted(set(combined["timeframe"])) if len(combined) and "timeframe" in combined else [],
        "event_counts": combined["event"].value_counts().to_dict() if len(combined) and "event" in combined else {},
        "episodes": int(combined["episode_id"].nunique()) if len(combined) and "episode_id" in combined else 0,
        "per_file": per_file,
    }
    return IngestResult(combined, findings, stats)


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(
        description="Ingest NEXA Trade DNA CSV exports into a canonical research dataset.")
    ap.add_argument("inputs", nargs="+", help="NEXA_TradeDNA_*.csv")
    ap.add_argument("-o", "--out", help="output .parquet or .csv")
    ap.add_argument("--schema", help="nexa_schema_v1.json for column cross-check")
    ap.add_argument("--allow-errors", action="store_true",
                    help="write output even when ERROR findings exist")
    args = ap.parse_args(argv)

    result = load_many(args.inputs, schema_path=args.schema) if len(args.inputs) > 1 \
        else load_trade_dna(args.inputs[0], schema_path=args.schema)
    print(result.report())
    if args.out:
        written = write_canonical(result, args.out, allow_errors=args.allow_errors)
        print(f"\nwritten: {written}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
