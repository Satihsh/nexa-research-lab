"""
nexa_validate.py -- Stage 5 of NEXA_IMPLEMENTATION_PLAN_V3.

DATASET VALIDATION GATE. The last checkpoint before any model may be fitted.

WHAT THIS GATE IS FOR
---------------------
Every defect it looks for produces a model that trains cleanly, scores well,
and is worthless: a label leaked into a feature, a test fold whose label window
overlaps a training row, duplicate episodes inflating the sample, a class
balance so skewed that predicting the majority beats the model. None of these
raise an exception anywhere else in the pipeline. They surface as unexplained
live underperformance months later.

So this module fails closed and refuses to be optimistic: zero rows is a FAIL,
not a clean bill of health; an unevaluated check is a FAIL, not a pass.

RELATIONSHIP TO THE OTHER GATES
-------------------------------
Stage 3 (parity)  asks: do Python and MQL5 compute the same features?
Stage 4 (labels)  asks: what actually happened after each trade?
Stage 5 (here)    asks: is the resulting dataset fit to train on at all?

All three must pass. They are independent questions and none subsumes another.

PURGING AND EMBARGO -- WHY BOTH
-------------------------------
A NEXA label can take up to `InpMaxHoldBars` (480 M1 bars) to resolve. So a
training row whose decision happened BEFORE a test row can still have a label
window that extends INTO the test period. Training on it leaks test-period
market outcomes into the fitted model.

  purge   removes training rows whose [label_start, label_end] window overlaps
          the test window at all
  embargo additionally drops training rows in a buffer AFTER the test window,
          because serial correlation means a row immediately adjacent still
          carries test-period information even without literal overlap

Embargo length must be at least the maximum label horizon; a shorter embargo
leaves exactly the overlap purging was meant to remove.

Self-contained: pandas + numpy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import pandas as pd

SUPPORTED_SCHEMA_VERSIONS = ("1.0",)
FEATURE_COUNT = 48
FEATURE_COLUMNS = [f"f{i:02d}" for i in range(FEATURE_COUNT)]

#: Columns that describe the OUTCOME. If any of these ever reaches the model's
#: input matrix the model is reading the answer. Checked explicitly.
LABEL_DERIVED_COLUMNS = (
    "label", "label_reason", "label_start_ts", "label_end_ts",
    "ambiguous_bar", "bars_to_outcome", "mfe_r", "mae_r",
    "result_r", "commission", "swap", "slippage_points",
    "entry_actual", "fill_ts", "exec_model",
)

#: Labels that represent a resolved outcome (mirrors nexa_labels.RESOLVED_LABELS).
RESOLVED_LABELS = ("TP_WIN", "SL_LOSS", "BREAKEVEN_STOP", "TIME_EXIT", "TIMEOUT")

#: Binary training target mapping. TIMEOUT is deliberately EXCLUDED rather than
#: called a loss: a trade that never resolved is not evidence either way, and
#: labelling it 0 teaches the model that indecision is failure.
BINARY_WIN = ("TP_WIN",)
BINARY_LOSS = ("SL_LOSS", "BREAKEVEN_STOP", "TIME_EXIT")


class Severity(str, Enum):
    ERROR = "ERROR"     # dataset must not be trained on
    WARN = "WARN"       # usable, but the reader must know
    INFO = "INFO"


class GateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class Finding:
    severity: Severity
    code: str
    message: str
    count: int = 0
    detail: tuple = field(default_factory=tuple)

    def __str__(self) -> str:
        d = f" (e.g. {list(self.detail)})" if self.detail else ""
        return f"[{self.severity.value}] {self.code}: {self.message} n={self.count}{d}"


@dataclass
class Split:
    """One walk-forward fold after purging and embargo."""
    fold: int
    train_idx: np.ndarray
    test_idx: np.ndarray
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    purged: int
    embargoed: int


@dataclass
class ValidationConfig:
    """
    Thresholds for the gate.

    `embargo_bars` defaults to the label horizon from NEXA_TrainingExport.mq5.
    Lowering it below the maximum observed label span re-opens the exact leak
    purging exists to close, so the gate checks that explicitly rather than
    trusting the setting.
    """
    min_resolved_episodes: int = 200        # below this, a fit memorises
    min_class_fraction: float = 0.05        # minority class floor
    max_ambiguous_fraction: float = 0.20
    min_symbols: int = 1
    min_regime_buckets: int = 2
    walk_forward_folds: int = 5
    embargo_bars: int = 480                 # InpMaxHoldBars
    bar_minutes: int = 1                    # M1 contract
    max_feature_nan_fraction: float = 0.0   # features must be complete
    min_feature_variance: float = 0.0       # a constant feature carries nothing


@dataclass
class ValidationResult:
    status: GateStatus
    findings: list
    splits: list
    stats: dict

    @property
    def passed(self) -> bool:
        return self.status is GateStatus.PASS

    def errors(self) -> list:
        return [f for f in self.findings if f.severity is Severity.ERROR]

    def report(self) -> str:
        lines = [
            "NEXA dataset validation gate",
            "=" * 70,
            f"rows                 : {self.stats.get('rows')}",
            f"episodes             : {self.stats.get('episodes')}",
            f"resolved episodes    : {self.stats.get('resolved_episodes')}",
            f"trainable episodes   : {self.stats.get('trainable_episodes')}",
            f"class balance        : {self.stats.get('class_balance')}",
            f"symbols              : {self.stats.get('symbols')}",
            f"timeframes           : {self.stats.get('timeframes')}",
            f"regime buckets       : {self.stats.get('regime_buckets')}",
            f"date range           : {self.stats.get('date_range')}",
            f"max label span (bars): {self.stats.get('max_label_span_bars')}",
            f"embargo (bars)       : {self.stats.get('embargo_bars')}",
            f"walk-forward folds   : {len(self.splits)}",
            f"STATUS               : {self.status.value}",
            "-" * 70,
        ]
        if self.splits:
            lines.append("folds (train / test / purged / embargoed):")
            for s in self.splits:
                lines.append(
                    f"  fold {s.fold}: train={len(s.train_idx):<6} test={len(s.test_idx):<6} "
                    f"purged={s.purged:<5} embargoed={s.embargoed:<5} "
                    f"[{s.test_start} .. {s.test_end}]")
            lines.append("-" * 70)
        lines += [str(f) for f in self.findings] or ["(no findings)"]
        return "\n".join(lines)


class ValidationGateError(RuntimeError):
    """Raised when the dataset must not be trained on."""


def assert_validation_or_halt(result: ValidationResult) -> None:
    """
    Fail-closed gate. Call before any model fitting.

    Raises rather than returning a flag: a caller that forgets to check a
    boolean trains on a bad dataset silently, which is the outcome this stage
    exists to prevent.
    """
    if result.status is not GateStatus.PASS:
        raise ValidationGateError(
            "DATASET VALIDATION FAILED -- model training is not valid.\n"
            + result.report())


def _ex(mask: pd.Series, limit: int = 8) -> tuple:
    return tuple(mask[mask].index.tolist()[:limit])


# ---------------------------------------------------------------------------
# episode view
# ---------------------------------------------------------------------------

def episode_view(frame: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse to one row per labelled episode -- the unit a model trains on.

    A trade is one observation regardless of how many journal rows describe it.
    Training on every row would repeat each trade several times with identical
    features, which inflates the sample and correlates the duplicates.
    """
    if "episode_id" not in frame.columns:
        return frame.iloc[0:0].copy()
    linked = frame[frame["episode_id"] >= 0]
    if "event" in linked.columns:
        opens = linked[linked["event"] == "OPEN"]
        if len(opens):
            return opens.drop_duplicates(subset=["episode_id"], keep="first").copy()
    return linked.drop_duplicates(subset=["episode_id"], keep="first").copy()


def binary_target(labels: pd.Series) -> pd.Series:
    """1 for a win, 0 for a resolved loss, NaN for anything not trainable."""
    out = pd.Series(np.nan, index=labels.index, dtype="float64")
    out[labels.isin(BINARY_WIN)] = 1.0
    out[labels.isin(BINARY_LOSS)] = 0.0
    return out


# ---------------------------------------------------------------------------
# individual checks
# ---------------------------------------------------------------------------

def check_schema(frame: pd.DataFrame, findings: list) -> bool:
    if "schema_version" not in frame.columns:
        findings.append(Finding(Severity.ERROR, "NO_SCHEMA_VERSION",
                                "dataset has no schema_version column"))
        return False
    versions = sorted(set(frame["schema_version"].astype(str)))
    bad = [v for v in versions if v not in SUPPORTED_SCHEMA_VERSIONS]
    if len(versions) > 1:
        findings.append(Finding(Severity.ERROR, "MIXED_SCHEMA_VERSIONS",
                                f"dataset mixes schema versions {versions}",
                                count=len(versions)))
    if bad:
        findings.append(Finding(Severity.ERROR, "UNSUPPORTED_SCHEMA",
                                f"unsupported schema_version {bad}", count=len(bad)))
    missing = [c for c in FEATURE_COLUMNS if c not in frame.columns]
    if missing:
        findings.append(Finding(Severity.ERROR, "MISSING_FEATURES",
                                f"feature columns absent: {missing[:6]}",
                                count=len(missing)))
    for col in ("label", "label_start_ts", "label_end_ts", "episode_id", "event"):
        if col not in frame.columns:
            findings.append(Finding(Severity.ERROR, "MISSING_REQUIRED_COLUMN",
                                    f"'{col}' absent; Stage 4 labelling must run first"))
    return not any(f.severity is Severity.ERROR for f in findings)


def check_feature_integrity(ep: pd.DataFrame, cfg: ValidationConfig, findings: list) -> None:
    present = [c for c in FEATURE_COLUMNS if c in ep.columns]
    if not present or not len(ep):
        return
    mat = ep[present]
    nan_frac = mat.isna().mean()
    bad = nan_frac[nan_frac > cfg.max_feature_nan_fraction]
    if len(bad):
        findings.append(Finding(
            Severity.ERROR, "FEATURE_NAN",
            f"features with missing values above {cfg.max_feature_nan_fraction:.0%}: "
            f"{list(bad.index[:6])}", count=len(bad)))

    arr = mat.to_numpy(dtype="float64", na_value=np.nan)
    nonfinite = ~np.isfinite(arr)
    if nonfinite.any():
        cols = [present[i] for i in np.unique(np.where(nonfinite)[1])][:6]
        findings.append(Finding(Severity.ERROR, "FEATURE_NONFINITE",
                                f"non-finite feature values in {cols}",
                                count=int(nonfinite.sum())))

    variances = mat.var(numeric_only=True)
    constant = variances[variances <= cfg.min_feature_variance]
    if len(constant):
        # not an ERROR: a constant feature is useless, not corrupting. It does
        # mean the dataset cannot support any claim about that feature.
        findings.append(Finding(
            Severity.WARN, "CONSTANT_FEATURES",
            f"zero-variance features carry no information here: "
            f"{list(constant.index[:8])}", count=len(constant)))


def check_labels(ep: pd.DataFrame, cfg: ValidationConfig, findings: list) -> dict:
    stats: dict = {}
    if "label" not in ep.columns or not len(ep):
        return stats
    counts = ep["label"].value_counts().to_dict()
    stats["label_counts"] = counts

    resolved = ep[ep["label"].isin(RESOLVED_LABELS)]
    stats["resolved_episodes"] = len(resolved)

    target = binary_target(ep["label"])
    trainable = target.notna()
    stats["trainable_episodes"] = int(trainable.sum())

    if trainable.sum() == 0:
        findings.append(Finding(Severity.ERROR, "NO_TRAINABLE_LABELS",
                                "no episode carries a win/loss outcome"))
        return stats

    wins = float((target == 1.0).sum())
    losses = float((target == 0.0).sum())
    total = wins + losses
    minority = min(wins, losses) / total if total else 0.0
    stats["class_balance"] = {"win": int(wins), "loss": int(losses),
                              "minority_fraction": round(minority, 4)}
    if minority < cfg.min_class_fraction:
        findings.append(Finding(
            Severity.ERROR, "CLASS_IMBALANCE",
            f"minority class is {minority:.1%} of trainable episodes, below "
            f"{cfg.min_class_fraction:.0%}; a model can beat this by always "
            f"predicting the majority", count=int(min(wins, losses))))

    if int(trainable.sum()) < cfg.min_resolved_episodes:
        findings.append(Finding(
            Severity.ERROR, "INSUFFICIENT_SAMPLE",
            f"{int(trainable.sum())} trainable episodes is below the minimum "
            f"{cfg.min_resolved_episodes}; a model fitted here memorises the sample",
            count=int(trainable.sum())))

    if "ambiguous_bar" in ep.columns and len(ep):
        amb = ep["ambiguous_bar"].astype(bool).mean()
        stats["ambiguous_fraction"] = round(float(amb), 4)
        if amb > cfg.max_ambiguous_fraction:
            findings.append(Finding(
                Severity.WARN, "HIGH_AMBIGUITY_RATE",
                f"{amb:.1%} of episodes hit both barriers in one bar; M1 OHLC "
                f"cannot resolve these and they are excluded from training",
                count=int(ep['ambiguous_bar'].astype(bool).sum())))

    invalid = ep["label"] == "INVALID"
    if invalid.any():
        findings.append(Finding(Severity.ERROR, "INVALID_LABELS",
                                "episodes Stage 4 could not label",
                                count=int(invalid.sum()), detail=_ex(invalid)))
    return stats


def check_chronology(ep: pd.DataFrame, findings: list) -> None:
    """Timestamp ordering that must hold for every executed episode."""
    needed = {"decision_ts_effective", "label_start_ts", "label_end_ts"}
    if not needed <= set(ep.columns) or not len(ep):
        return
    d = pd.to_datetime(ep["decision_ts_effective"], errors="coerce")
    s = pd.to_datetime(ep["label_start_ts"], errors="coerce")
    e = pd.to_datetime(ep["label_end_ts"], errors="coerce")

    have = d.notna() & s.notna()
    bad = have & (s < d)
    if bad.any():
        findings.append(Finding(
            Severity.ERROR, "LABEL_BEFORE_DECISION",
            "label_start_ts precedes decision_ts: the outcome cannot start "
            "before the decision that caused it",
            count=int(bad.sum()), detail=_ex(bad)))

    have2 = s.notna() & e.notna()
    bad2 = have2 & (e < s)
    if bad2.any():
        findings.append(Finding(Severity.ERROR, "LABEL_END_BEFORE_START",
                                "label_end_ts precedes label_start_ts",
                                count=int(bad2.sum()), detail=_ex(bad2)))

    if "write_ts" in ep.columns:
        w = pd.to_datetime(ep["write_ts"], errors="coerce")
        if w.notna().any() and d.notna().any() and (w == d).all():
            findings.append(Finding(
                Severity.WARN, "WRITE_TS_EQUALS_DECISION_TS",
                "write_ts identical to decision_ts on every row; write_ts is "
                "diagnostic and must not be used as a causal anchor"))


def check_duplicates(frame: pd.DataFrame, ep: pd.DataFrame, findings: list) -> None:
    if "row_id" in frame.columns:
        dup = frame["row_id"].duplicated(keep=False) & (frame["row_id"].astype(str) != "")
        if dup.any():
            findings.append(Finding(Severity.ERROR, "DUPLICATE_ROW_ID",
                                    "duplicate row_id in the dataset",
                                    count=int(dup.sum()), detail=_ex(dup)))
    # Detect duplicate episodes on the RAW frame. episode_view() collapses to
    # one row per episode, so checking the collapsed view would silently hide
    # exactly the defect being looked for: the duplicate is already gone by then.
    if {"episode_id", "event"} <= set(frame.columns):
        opens = frame[(frame["event"] == "OPEN") & (frame["episode_id"] >= 0)]
        dup = opens["episode_id"].duplicated(keep=False)
        if dup.any():
            findings.append(Finding(
                Severity.ERROR, "DUPLICATE_EPISODE",
                "an episode_id carries more than one OPEN row; the same trade "
                "would be weighted multiply in training",
                count=int(dup.sum()), detail=_ex(dup)))
    present = [c for c in FEATURE_COLUMNS if c in ep.columns]
    if present and len(ep) > 1:
        dupf = ep.duplicated(subset=present, keep=False)
        if dupf.sum() > len(ep) * 0.5:
            findings.append(Finding(
                Severity.WARN, "REPEATED_FEATURE_VECTORS",
                f"{dupf.sum()} episodes share an identical 48-feature vector; "
                f"either the market repeated exactly or features are not varying",
                count=int(dupf.sum())))


def check_coverage(ep: pd.DataFrame, cfg: ValidationConfig, findings: list) -> dict:
    stats: dict = {}
    if not len(ep):
        return stats
    if "symbol" in ep.columns:
        syms = sorted(set(ep["symbol"].astype(str)) - {""})
        stats["symbols"] = syms
        if len(syms) < cfg.min_symbols:
            findings.append(Finding(Severity.ERROR, "INSUFFICIENT_SYMBOL_COVERAGE",
                                    f"{len(syms)} symbol(s), need {cfg.min_symbols}"))
    if "timeframe" in ep.columns:
        tfs = sorted(set(ep["timeframe"].astype(str)) - {""})
        stats["timeframes"] = tfs
        if len(tfs) > 1:
            findings.append(Finding(
                Severity.ERROR, "MIXED_TIMEFRAMES",
                f"episodes span multiple timeframes {tfs}; feature semantics and "
                f"the label horizon are timeframe-specific and cannot be pooled",
                count=len(tfs)))
    # f20 trendState / f21 volState encode the regime the decision was taken in
    buckets = set()
    if "f20" in ep.columns and "f21" in ep.columns:
        pairs = ep[["f20", "f21"]].dropna().round().astype(int)
        buckets = {tuple(r) for r in pairs.to_numpy()}
    stats["regime_buckets"] = len(buckets)
    if buckets and len(buckets) < cfg.min_regime_buckets:
        findings.append(Finding(
            Severity.WARN, "NARROW_REGIME_COVERAGE",
            f"episodes span only {len(buckets)} (trend,volatility) bucket(s); "
            f"nothing can be claimed about regimes absent from the sample",
            count=len(buckets)))
    return stats


def check_feature_label_leakage(ep: pd.DataFrame, findings: list) -> None:
    """
    Detect outcome information sitting inside the feature block.

    Two ways this happens in practice: an outcome column accidentally included
    in the model's input list, or a feature that is a perfect function of the
    label because it was computed after the fact. Both produce spectacular
    backtests and no live edge.
    """
    present = [c for c in FEATURE_COLUMNS if c in ep.columns]
    if not present or "label" not in ep.columns or len(ep) < 10:
        return

    overlap = [c for c in LABEL_DERIVED_COLUMNS if c in present]
    if overlap:
        findings.append(Finding(
            Severity.ERROR, "OUTCOME_COLUMN_IN_FEATURE_BLOCK",
            f"outcome-derived columns inside f00..f47: {overlap}", count=len(overlap)))

    target = binary_target(ep["label"])
    mask = target.notna()
    if mask.sum() < 10:
        return
    y = target[mask].to_numpy(dtype="float64")
    if len(np.unique(y)) < 2:
        return
    suspicious = []
    for col in present:
        x = ep.loc[mask, col].to_numpy(dtype="float64")
        if not np.isfinite(x).all() or np.std(x) == 0:
            continue
        r = abs(float(np.corrcoef(x, y)[0, 1]))
        if np.isfinite(r) and r > 0.95:
            suspicious.append((col, round(r, 4)))
    if suspicious:
        findings.append(Finding(
            Severity.ERROR, "FEATURE_ALMOST_PERFECTLY_PREDICTS_LABEL",
            "feature(s) correlate with the outcome at |r|>0.95, which market "
            "features do not legitimately do -- investigate before training",
            count=len(suspicious), detail=tuple(suspicious[:5])))


def check_overlapping_label_horizons(ep: pd.DataFrame, findings: list) -> dict:
    """
    Quantify how much episodes' label windows overlap each other.

    Overlap is not itself a defect -- concurrent trades are normal -- but it is
    the reason purging is mandatory, and a dataset that is almost entirely
    overlapping supports far fewer independent observations than its row count
    suggests. That gap is where false confidence comes from.
    """
    stats: dict = {}
    if not {"label_start_ts", "label_end_ts"} <= set(ep.columns) or len(ep) < 2:
        return stats
    s = pd.to_datetime(ep["label_start_ts"], errors="coerce")
    e = pd.to_datetime(ep["label_end_ts"], errors="coerce")
    ok = s.notna() & e.notna()
    if ok.sum() < 2:
        return stats
    intervals = sorted(zip(s[ok], e[ok]))
    overlaps = 0
    for i in range(1, len(intervals)):
        if intervals[i][0] < intervals[i - 1][1]:
            overlaps += 1
    frac = overlaps / (len(intervals) - 1)
    stats["overlapping_label_fraction"] = round(float(frac), 4)
    if frac > 0.5:
        findings.append(Finding(
            Severity.WARN, "HIGH_LABEL_OVERLAP",
            f"{frac:.0%} of consecutive episodes have overlapping label windows; "
            f"effective independent sample is well below the episode count",
            count=overlaps))
    return stats


# ---------------------------------------------------------------------------
# purged walk-forward splits
# ---------------------------------------------------------------------------

def make_purged_walk_forward(ep: pd.DataFrame, cfg: ValidationConfig,
                             findings: list) -> list:
    """
    Chronological folds with purging and embargo applied.

    A training row is dropped when either:
      * its [label_start, label_end] window overlaps the test window (purge), or
      * its label window starts inside the embargo buffer after the test window
    """
    splits: list = []
    need = {"label_start_ts", "label_end_ts"}
    if not need <= set(ep.columns) or len(ep) < cfg.walk_forward_folds * 2:
        findings.append(Finding(
            Severity.ERROR, "CANNOT_SPLIT",
            f"cannot build {cfg.walk_forward_folds} walk-forward folds from "
            f"{len(ep)} episodes"))
        return splits

    work = ep.copy()
    work["_s"] = pd.to_datetime(work["label_start_ts"], errors="coerce")
    work["_e"] = pd.to_datetime(work["label_end_ts"], errors="coerce")
    work = work[work["_s"].notna() & work["_e"].notna()].sort_values("_s", kind="mergesort")
    if len(work) < cfg.walk_forward_folds * 2:
        findings.append(Finding(Severity.ERROR, "CANNOT_SPLIT",
                                "too few episodes with usable label windows"))
        return splits

    embargo = pd.Timedelta(minutes=cfg.embargo_bars * cfg.bar_minutes)
    max_span = (work["_e"] - work["_s"]).max()
    if embargo < max_span:
        findings.append(Finding(
            Severity.ERROR, "EMBARGO_TOO_SHORT",
            f"embargo {embargo} is shorter than the longest label span {max_span}; "
            f"a shorter embargo leaves exactly the overlap purging removes"))

    idx = np.arange(len(work))
    bounds = np.array_split(idx, cfg.walk_forward_folds + 1)
    positional = {pos: i for i, pos in enumerate(work.index)}

    for fold in range(cfg.walk_forward_folds):
        test_pos = bounds[fold + 1]
        if not len(test_pos):
            continue
        test_rows = work.iloc[test_pos]
        t_start, t_end = test_rows["_s"].min(), test_rows["_e"].max()

        candidate = work.iloc[: test_pos[0]]
        overlap = (candidate["_e"] >= t_start) & (candidate["_s"] <= t_end)
        in_embargo = (candidate["_s"] > t_end) & (candidate["_s"] <= t_end + embargo)
        keep = ~(overlap | in_embargo)

        splits.append(Split(
            fold=fold,
            train_idx=np.array([positional[i] for i in candidate[keep].index], dtype="int64"),
            test_idx=np.array([positional[i] for i in test_rows.index], dtype="int64"),
            test_start=t_start, test_end=t_end,
            purged=int(overlap.sum()), embargoed=int(in_embargo.sum())))

    empty = [s.fold for s in splits if len(s.train_idx) == 0]
    if empty:
        findings.append(Finding(
            Severity.ERROR, "EMPTY_TRAIN_FOLD",
            f"folds {empty} have no training rows after purging; the dataset "
            f"does not span enough independent time to validate on",
            count=len(empty)))
    return splits


def verify_no_leakage(ep: pd.DataFrame, splits: list, findings: list) -> None:
    """
    Independently re-check every produced split for overlap.

    The split builder and this verifier are separate on purpose: a bug in the
    builder that silently kept an overlapping row would otherwise be invisible,
    and leakage is the one defect that makes every downstream number wrong.
    """
    if not splits or not {"label_start_ts", "label_end_ts"} <= set(ep.columns):
        return
    s_all = pd.to_datetime(ep["label_start_ts"], errors="coerce").to_numpy()
    e_all = pd.to_datetime(ep["label_end_ts"], errors="coerce").to_numpy()
    bad_folds = []
    for sp in splits:
        if not len(sp.train_idx):
            continue
        ts = np.datetime64(sp.test_start)
        te = np.datetime64(sp.test_end)
        tr_s, tr_e = s_all[sp.train_idx], e_all[sp.train_idx]
        overlap = (tr_e >= ts) & (tr_s <= te)
        if overlap.any():
            bad_folds.append((sp.fold, int(overlap.sum())))
    if bad_folds:
        findings.append(Finding(
            Severity.ERROR, "LEAKAGE_TRAIN_TEST_OVERLAP",
            "training rows whose label window overlaps the test window survived "
            "purging -- HARD FAILURE", count=len(bad_folds), detail=tuple(bad_folds)))


# ---------------------------------------------------------------------------
# the gate
# ---------------------------------------------------------------------------

def validate_dataset(frame: pd.DataFrame,
                     cfg: ValidationConfig | None = None) -> ValidationResult:
    """Run every check. Deterministic: same input yields an identical report."""
    cfg = cfg or ValidationConfig()
    findings: list = []
    stats: dict = {"rows": len(frame), "embargo_bars": cfg.embargo_bars}

    if not len(frame):
        findings.append(Finding(
            Severity.ERROR, "EMPTY_DATASET",
            "no rows. An empty dataset is a FAIL, not a clean result: nothing "
            "was checked, so nothing can be asserted"))
        return ValidationResult(GateStatus.FAIL, findings, [], stats)

    schema_ok = check_schema(frame, findings)
    if not schema_ok:
        return ValidationResult(GateStatus.FAIL, findings, [], stats)

    ep = episode_view(frame)
    stats["episodes"] = len(ep)
    if not len(ep):
        findings.append(Finding(Severity.ERROR, "NO_EPISODES",
                                "no linked episodes; Stage 2 ingestion must run first"))
        return ValidationResult(GateStatus.FAIL, findings, [], stats)

    check_feature_integrity(ep, cfg, findings)
    stats.update(check_labels(ep, cfg, findings))
    check_chronology(ep, findings)
    check_duplicates(frame, ep, findings)
    stats.update(check_coverage(ep, cfg, findings))
    check_feature_label_leakage(ep, findings)
    stats.update(check_overlapping_label_horizons(ep, findings))

    if {"label_start_ts", "label_end_ts"} <= set(ep.columns) and len(ep):
        s = pd.to_datetime(ep["label_start_ts"], errors="coerce")
        e = pd.to_datetime(ep["label_end_ts"], errors="coerce")
        if s.notna().any():
            stats["date_range"] = f"{s.min()} .. {e.max()}"
            span = (e - s).max()
            if pd.notna(span):
                stats["max_label_span_bars"] = int(
                    span / pd.Timedelta(minutes=cfg.bar_minutes))

    trainable = ep[binary_target(ep["label"]).notna()] if "label" in ep.columns else ep.iloc[0:0]
    splits = make_purged_walk_forward(trainable, cfg, findings) if len(trainable) else []
    if splits:
        verify_no_leakage(trainable, splits, findings)

    status = (GateStatus.FAIL if any(f.severity is Severity.ERROR for f in findings)
              else GateStatus.PASS)
    return ValidationResult(status, findings, splits, stats)


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(
        description="NEXA dataset validation gate (Stage 5).")
    ap.add_argument("labelled", help="Stage 4 labelled dataset (.csv/.parquet)")
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--embargo-bars", type=int, default=480)
    ap.add_argument("--min-episodes", type=int, default=200)
    ap.add_argument("--out", help="write the report here")
    args = ap.parse_args(argv)

    frame = (pd.read_parquet(args.labelled) if args.labelled.endswith(".parquet")
             else pd.read_csv(args.labelled))
    for c in ("decision_ts", "decision_ts_effective", "fill_ts",
              "label_start_ts", "label_end_ts", "write_ts", "dispatch_ts"):
        if c in frame.columns:
            frame[c] = pd.to_datetime(frame[c], errors="coerce")

    cfg = ValidationConfig(walk_forward_folds=args.folds,
                           embargo_bars=args.embargo_bars,
                           min_resolved_episodes=args.min_episodes)
    result = validate_dataset(frame, cfg)
    print(result.report())
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(result.report() + "\n")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
