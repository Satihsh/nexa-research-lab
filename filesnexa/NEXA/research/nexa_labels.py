"""
nexa_labels.py -- Stage 4 of NEXA_IMPLEMENTATION_PLAN_V3.

Canonical outcome labeler. Determines what actually happened after an executed
trade, from the trade's ACTUAL fill, ACTUAL SL/TP, and subsequent closed M1 bars.

WHAT IT MAY AND MAY NOT SEE
---------------------------
May see: market bars strictly inside [label_start_ts, label_end_ts].
May NOT see: model predictions, AI probabilities, composite/quality scores,
strategy decisions, any feature value, or any bar beyond label_end_ts.

Labels are the one place in NEXA permitted to use information after
decision_ts -- that is what a label IS. The guard is that the label never flows
back into a feature, and this module never reads one.

THE CONTRACT THIS IMPLEMENTS (not invented here)
------------------------------------------------
Sourced from NEXA_TrainingExport.mq5, which is Stage-1 locked and compiled:

    InpBreakevenAtR  = 1.00   once +1.0R favourable is reached, effective SL
                              becomes entry (mirrors ManageOpenPosition)
    InpTimeExitBars  = 48     after 48 bars, if progress < InpTimeExitMinR the
                              EA closes at market
    InpTimeExitMinR  = 0.30
    InpMaxHoldBars   = 480    absolute horizon

These mirror the EA's own InpBreakevenAtR / InpTimeExitBars / 0.3R condition.
No horizon is invented here; changing one requires changing the EA, the
exporter, and this module together.

TWO DOCUMENTED CONFLICTS BETWEEN THE MQL5 EXPORTER AND THE STAGE 4 DIRECTIVE
----------------------------------------------------------------------------
Both are surfaced as explicit policies rather than silently resolved, because
picking either side without saying so would put an undisclosed assumption into
every label in the dataset.

1. AMBIGUOUS BARS.
   NEXA_TrainingExport.mq5 documents: a bar spanning both barriers resolves to
   LOSS ("AMBIGUOUS_BAR_RESOLVED_LOSS"), flagged.
   The Stage 4 directive requires: label AMBIGUOUS, never collapse to win/loss,
   unless a deterministic rule exists in the NEXA EXECUTION contract.
   Reading: the exporter's rule is a LABELLING convention, not an execution
   contract. At runtime the broker decides which barrier filled and the EA is
   never told; nothing in the EA defines an ordering. So no execution contract
   rule exists.
   DEFAULT: AmbiguityPolicy.AMBIGUOUS. PESSIMISTIC_LOSS reproduces the
   exporter exactly when a like-for-like comparison is wanted.

2. THE FILL BAR.
   The exporter starts its walk AT the bar containing the fill, on the reasoning
   that the EA fires at a new bar's open so the whole bar is post-entry.
   The Stage 4 directive requires the first closed bar AFTER the fill.
   Reading: with asynchronous execution a fill can land mid-bar, and that bar's
   extremes may predate the fill. Crediting them to the trade is a real bias.
   DEFAULT: FillBarPolicy.EXCLUDE_FILL_BAR (causally safe).
   INCLUDE_FILL_BAR reproduces the exporter.

Whichever policy is used is recorded in `exec_model` on every row, so a
downstream reader can never mistake one convention for the other.

NOT MODELLED, STATED PLAINLY
----------------------------
* partial close at InpPartialCloseAtR (the EA blends the position; this walk
  treats the episode as one unit)
* bid/ask on the exit side, slippage, commission, swap
* the intrabar path (M1 OHLC only)

`exec_model` carries this so no one mistakes an OHLC label for a fill simulation.

Self-contained: pandas + numpy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import pandas as pd

SUPPORTED_SCHEMA_VERSIONS = ("1.0",)

#: Fields this stage appends. Stage 2 columns are never overwritten.
STAGE4_COLUMNS = (
    "label_start_ts", "label_end_ts", "label", "label_reason",
    "ambiguous_bar", "bars_to_outcome", "mfe_r", "mae_r", "exec_model",
)


class Label(str, Enum):
    """Outcome vocabulary. Failure states are labels too -- never silent drops."""
    TP_WIN = "TP_WIN"
    SL_LOSS = "SL_LOSS"
    BREAKEVEN_STOP = "BREAKEVEN_STOP"   # SL hit after the ratchet moved it to entry
    TIME_EXIT = "TIME_EXIT"             # EA's conditional close at InpTimeExitBars
    TIMEOUT = "TIMEOUT"                 # horizon expired, no barrier touched
    AMBIGUOUS = "AMBIGUOUS"             # both barriers in one bar, order unknowable
    UNLABELLED = "UNLABELLED"           # not an executed trade (REJECTED/DECISION)
    INVALID = "INVALID"                 # data defect; see label_reason


#: Labels that represent a resolved market outcome usable for supervised training.
RESOLVED_LABELS = (Label.TP_WIN, Label.SL_LOSS, Label.BREAKEVEN_STOP,
                   Label.TIME_EXIT, Label.TIMEOUT)


class AmbiguityPolicy(str, Enum):
    AMBIGUOUS = "AMBIGUOUS"                  # directive default
    PESSIMISTIC_LOSS = "PESSIMISTIC_LOSS"    # reproduces NEXA_TrainingExport.mq5


class FillBarPolicy(str, Enum):
    EXCLUDE_FILL_BAR = "EXCLUDE_FILL_BAR"    # directive default: first bar AFTER fill
    INCLUDE_FILL_BAR = "INCLUDE_FILL_BAR"    # reproduces NEXA_TrainingExport.mq5


class Severity(str, Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"


@dataclass(frozen=True)
class Finding:
    severity: Severity
    code: str
    message: str
    count: int = 0
    episodes: tuple = field(default_factory=tuple)

    def __str__(self) -> str:
        loc = f" (e.g. episodes {list(self.episodes)})" if self.episodes else ""
        return f"[{self.severity.value}] {self.code}: {self.message} n={self.count}{loc}"


@dataclass
class LabelConfig:
    """
    Every value here is sourced from NEXA_TrainingExport.mq5, not chosen.

    `horizon_bars`, `breakeven_at_r`, `time_exit_bars` and `time_exit_min_r`
    must match the EA. They are exposed so a caller can prove a match, not so a
    researcher can tune them: a label computed under different exit rules than
    the EA actually uses describes a trade that never existed.
    """
    horizon_bars: int = 480             # InpMaxHoldBars
    breakeven_at_r: float = 1.00        # InpBreakevenAtR
    time_exit_bars: int = 48            # InpTimeExitBars
    time_exit_min_r: float = 0.30       # InpTimeExitMinR
    timeframe: str = "M1"               # contract centres on closed M1 bars
    ambiguity: AmbiguityPolicy = AmbiguityPolicy.AMBIGUOUS
    fill_bar: FillBarPolicy = FillBarPolicy.EXCLUDE_FILL_BAR

    def exec_model(self) -> str:
        """Machine-readable record of exactly which conventions produced a label."""
        return (f"{self.timeframe}_OHLC_BE{self.breakeven_at_r:g}R"
                f"_TIMEEXIT{self.time_exit_bars}@{self.time_exit_min_r:g}R"
                f"_HORIZON{self.horizon_bars}"
                f"_{self.ambiguity.value}_{self.fill_bar.value}")


@dataclass
class MarketBars:
    """Closed M1 bars per symbol: columns time, open, high, low, close, ascending."""
    frames: dict

    def m1(self, symbol: str):
        return self.frames.get(symbol)

    def after(self, symbol: str, start: pd.Timestamp, *, inclusive: bool):
        frame = self.frames.get(symbol)
        if frame is None or not len(frame):
            return None
        mask = (frame["time"] >= start) if inclusive else (frame["time"] > start)
        sub = frame[mask]
        return sub if len(sub) else None


@dataclass
class EpisodeOutcome:
    episode_id: int
    symbol: str
    label: Label
    label_reason: str
    label_start_ts: pd.Timestamp | None
    label_end_ts: pd.Timestamp | None
    ambiguous_bar: bool
    bars_to_outcome: int
    mfe_r: float
    mae_r: float
    exec_model: str
    entry_actual: float = float("nan")
    sl_price: float = float("nan")
    tp_price: float = float("nan")
    risk_dist: float = float("nan")
    direction: int = 0
    result_r_actual: float = float("nan")   # broker-realised, preserved verbatim


@dataclass
class LabelResult:
    frame: pd.DataFrame
    outcomes: list
    findings: list
    stats: dict

    @property
    def ok(self) -> bool:
        return not any(f.severity is Severity.ERROR for f in self.findings)

    def report(self) -> str:
        lines = [
            "NEXA outcome labelling report",
            "=" * 66,
            f"episodes seen      : {self.stats.get('episodes_seen')}",
            f"episodes labelled  : {self.stats.get('episodes_labelled')}",
            f"rows annotated     : {self.stats.get('rows_annotated')}",
            f"exec_model         : {self.stats.get('exec_model')}",
            (f"horizon            : {self.stats.get('horizon_bars')} "
             f"{self.stats.get('timeframe')} bars "
             "(source: NEXA_TrainingExport.mq5)"),
            f"ambiguity policy   : {self.stats.get('ambiguity')}",
            f"fill-bar policy    : {self.stats.get('fill_bar')}",
            f"label counts       : {self.stats.get('label_counts')}",
            f"ambiguous bars     : {self.stats.get('ambiguous_count')}",
            f"status             : {'OK' if self.ok else 'ERRORS PRESENT'}",
            "-" * 66,
        ]
        lines += [str(f) for f in self.findings] or ["(no findings)"]
        return "\n".join(lines)


class LabelContractError(ValueError):
    """Raised when the dataset or contract cannot support labelling at all."""


# ---------------------------------------------------------------------------
# geometry / validation
# ---------------------------------------------------------------------------

def validate_geometry(direction: int, entry: float, sl: float, tp: float):
    """
    Barrier geometry must match the stated direction.

    Returns (ok, reason). An invalid geometry is failed, never repaired: a row
    claiming LONG with the stop above entry is a data defect, and silently
    flipping it would manufacture a trade nobody took.
    """
    for name, val in (("entry_actual", entry), ("sl_price", sl), ("tp_price", tp)):
        if val is None or not np.isfinite(val) or val <= 0:
            return False, f"INVALID_{name.upper()}"
    if direction == 1:
        if not sl < entry:
            return False, "INVALID_GEOMETRY_LONG_SL_NOT_BELOW_ENTRY"
        if not tp > entry:
            return False, "INVALID_GEOMETRY_LONG_TP_NOT_ABOVE_ENTRY"
    elif direction == -1:
        if not sl > entry:
            return False, "INVALID_GEOMETRY_SHORT_SL_NOT_ABOVE_ENTRY"
        if not tp < entry:
            return False, "INVALID_GEOMETRY_SHORT_TP_NOT_BELOW_ENTRY"
    else:
        return False, "INVALID_DIRECTION"
    return True, ""


# ---------------------------------------------------------------------------
# the walk
# ---------------------------------------------------------------------------

def label_trade(symbol: str, direction: int, entry: float, sl: float, tp: float,
                fill_ts: pd.Timestamp, bars: MarketBars,
                cfg: LabelConfig | None = None) -> EpisodeOutcome:
    """
    Walk forward over closed M1 bars from the fill and resolve the outcome.

    Ordering within the walk mirrors the EA's own management sequence, which
    matters when several conditions could fire on one bar:

      1. both barriers inside the bar    -> policy (AMBIGUOUS by default)
      2. effective SL touched            -> SL_LOSS or BREAKEVEN_STOP
      3. TP touched                      -> TP_WIN
      4. breakeven ratchet arms          -> effective SL becomes entry
      5. conditional time exit           -> TIME_EXIT
      6. horizon expiry                  -> TIMEOUT

    Step 4 is evaluated AFTER the barrier tests on the same bar: the EA cannot
    move a stop it has not yet survived, and arming the ratchet first would let
    a bar that actually hit the original SL be recorded as a breakeven scratch.
    """
    cfg = cfg or LabelConfig()
    em = cfg.exec_model()

    def fail(reason: str) -> EpisodeOutcome:
        return EpisodeOutcome(-1, symbol, Label.INVALID, reason, None, None,
                              False, 0, float("nan"), float("nan"), em,
                              entry, sl, tp, float("nan"), direction)

    ok, reason = validate_geometry(direction, entry, sl, tp)
    if not ok:
        return fail(reason)

    risk = abs(entry - sl)
    if not np.isfinite(risk) or risk <= 0:
        return fail("INVALID_RISK_DISTANCE")

    if fill_ts is None or pd.isna(fill_ts):
        return fail("MISSING_FILL_TS")
    fill_ts = pd.Timestamp(fill_ts)
    if fill_ts.year < 1990:
        return fail("IMPOSSIBLE_FILL_TS")

    inclusive = cfg.fill_bar is FillBarPolicy.INCLUDE_FILL_BAR
    walk = bars.after(symbol, fill_ts, inclusive=inclusive)
    if walk is None:
        return EpisodeOutcome(-1, symbol, Label.INVALID, "NO_MARKET_DATA_AFTER_FILL",
                              fill_ts, None, False, 0, float("nan"), float("nan"), em,
                              entry, sl, tp, risk, direction)

    eff_sl = sl
    be_armed = False
    mfe = 0.0          # magnitudes in R, both non-negative
    mae = 0.0
    bars_seen = 0
    last_ts = fill_ts

    highs = walk["high"].to_numpy(dtype="float64")
    lows = walk["low"].to_numpy(dtype="float64")
    closes = walk["close"].to_numpy(dtype="float64")
    times = walk["time"].to_numpy()

    n = min(len(walk), cfg.horizon_bars)
    for i in range(n):
        hi, lo, cl, ts = highs[i], lows[i], closes[i], pd.Timestamp(times[i])
        bars_seen += 1
        last_ts = ts

        # excursions are measured on this bar BEFORE any exit resolves, so a bar
        # that both extends favourably and stops out still reports its MFE
        fav = (hi - entry) if direction == 1 else (entry - lo)
        adv = (entry - lo) if direction == 1 else (hi - entry)
        mfe = max(mfe, fav / risk)
        mae = max(mae, adv / risk)

        tp_hit = (hi >= tp) if direction == 1 else (lo <= tp)
        sl_hit = (lo <= eff_sl) if direction == 1 else (hi >= eff_sl)

        if tp_hit and sl_hit:
            if cfg.ambiguity is AmbiguityPolicy.PESSIMISTIC_LOSS:
                lab = Label.BREAKEVEN_STOP if be_armed else Label.SL_LOSS
                return EpisodeOutcome(-1, symbol, lab,
                                      "AMBIGUOUS_BAR_RESOLVED_LOSS", fill_ts, ts,
                                      True, bars_seen, mfe, mae, em,
                                      entry, sl, tp, risk, direction)
            return EpisodeOutcome(-1, symbol, Label.AMBIGUOUS,
                                  "BOTH_BARRIERS_IN_ONE_BAR_ORDER_UNKNOWABLE",
                                  fill_ts, ts, True, bars_seen, mfe, mae, em,
                                  entry, sl, tp, risk, direction)
        if sl_hit:
            lab = Label.BREAKEVEN_STOP if be_armed else Label.SL_LOSS
            return EpisodeOutcome(-1, symbol, lab,
                                  "BREAKEVEN_STOP" if be_armed else "SL_TOUCHED",
                                  fill_ts, ts, False, bars_seen, mfe, mae, em,
                                  entry, sl, tp, risk, direction)
        if tp_hit:
            return EpisodeOutcome(-1, symbol, Label.TP_WIN, "TP_TOUCHED",
                                  fill_ts, ts, False, bars_seen, mfe, mae, em,
                                  entry, sl, tp, risk, direction)

        if not be_armed and cfg.breakeven_at_r > 0 and (fav / risk) >= cfg.breakeven_at_r:
            eff_sl = entry
            be_armed = True

        if cfg.time_exit_bars > 0 and bars_seen >= cfg.time_exit_bars:
            prog = ((cl - entry) if direction == 1 else (entry - cl)) / risk
            if prog < cfg.time_exit_min_r:
                return EpisodeOutcome(-1, symbol, Label.TIME_EXIT,
                                      f"TIME_EXIT_PROGRESS_{prog:.3f}R",
                                      fill_ts, ts, False, bars_seen, mfe, mae, em,
                                      entry, sl, tp, risk, direction)

    if bars_seen == 0:
        return EpisodeOutcome(-1, symbol, Label.INVALID, "NO_BARS_IN_WALK",
                              fill_ts, None, False, 0, float("nan"), float("nan"), em,
                              entry, sl, tp, risk, direction)
    reason = ("HORIZON_EXPIRED" if bars_seen >= cfg.horizon_bars
              else "MARKET_DATA_EXHAUSTED_BEFORE_HORIZON")
    return EpisodeOutcome(-1, symbol, Label.TIMEOUT, reason, fill_ts, last_ts,
                          False, bars_seen, mfe, mae, em,
                          entry, sl, tp, risk, direction)


# ---------------------------------------------------------------------------
# episode assembly
# ---------------------------------------------------------------------------

def _episode_rows(frame: pd.DataFrame):
    """Yield (episode_id, rows) for every linked episode, in chronological order."""
    if "episode_id" not in frame.columns:
        return
    linked = frame[frame["episode_id"] >= 0]
    for eid, rows in linked.groupby("episode_id", sort=True):
        yield int(eid), rows.sort_values("source_row" if "source_row" in rows.columns
                                         else "decision_ts_effective", kind="mergesort")


def label_dataset(frame: pd.DataFrame, bars: MarketBars,
                  cfg: LabelConfig | None = None) -> LabelResult:
    """
    Label every executed episode in a Stage 2 canonical frame.

    An episode is OPEN -> FILL -> PARTIAL_CLOSE* -> CLOSE. It produces ONE
    label, attached to every row of that episode, because a partial close is a
    management action inside one trade, not a second trade. Counting each
    partial as an independent example would inflate the sample and correlate the
    duplicates, which is exactly the kind of quiet inflation that makes a model
    look better than it is.
    """
    cfg = cfg or LabelConfig()
    findings: list = []
    out = frame.copy()

    if "schema_version" in out.columns and len(out):
        versions = sorted(set(out["schema_version"].astype(str)))
        bad = [v for v in versions if v not in SUPPORTED_SCHEMA_VERSIONS]
        if bad:
            raise LabelContractError(
                f"unsupported schema_version {bad}; labeller supports "
                f"{list(SUPPORTED_SCHEMA_VERSIONS)}")

    for col in ("episode_id", "event"):
        if col not in out.columns:
            raise LabelContractError(
                f"dataset lacks '{col}'; Stage 2 ingestion must run first")

    # initialise Stage 4 columns without disturbing anything Stage 2 produced
    out["label"] = Label.UNLABELLED.value
    out["label_reason"] = ""
    out["label_start_ts"] = pd.NaT
    out["label_end_ts"] = pd.NaT
    out["ambiguous_bar"] = False
    out["bars_to_outcome"] = 0
    out["mfe_r"] = np.nan
    out["mae_r"] = np.nan
    out["exec_model"] = cfg.exec_model()

    outcomes: list = []
    episodes_seen = 0
    invalid_ids: list = []
    no_fill_ids: list = []

    for eid, rows in _episode_rows(out):
        episodes_seen += 1
        events = set(rows["event"])

        if "REJECTED" in events and "FILL" not in events:
            out.loc[rows.index, "label"] = Label.UNLABELLED.value
            out.loc[rows.index, "label_reason"] = "REJECTED_NOT_EXECUTED"
            continue

        fills = rows[rows["event"] == "FILL"]
        if not len(fills):
            out.loc[rows.index, "label"] = Label.UNLABELLED.value
            out.loc[rows.index, "label_reason"] = "NO_FILL_NOT_A_TRADE"
            no_fill_ids.append(eid)
            continue

        fill = fills.iloc[0]        # first fill anchors the episode
        symbol = str(fill.get("symbol", ""))
        direction = int(fill["direction"]) if pd.notna(fill.get("direction")) else 0
        entry = float(fill["entry_actual"]) if pd.notna(fill.get("entry_actual")) else float("nan")
        if not np.isfinite(entry) or entry <= 0:
            # never silently substitute entry_intended: the trade that existed is
            # the one that filled, and labelling the intended price describes a
            # trade nobody took
            out.loc[rows.index, "label"] = Label.INVALID.value
            out.loc[rows.index, "label_reason"] = "MISSING_ENTRY_ACTUAL"
            invalid_ids.append(eid)
            continue

        sl = float(fill["sl_price"]) if pd.notna(fill.get("sl_price")) else float("nan")
        tp = float(fill["tp_price"]) if pd.notna(fill.get("tp_price")) else float("nan")
        fill_ts = fill.get("fill_ts")

        oc = label_trade(symbol, direction, entry, sl, tp, fill_ts, bars, cfg)
        oc.episode_id = eid

        closes = rows[rows["event"] == "CLOSE"]
        if len(closes) and pd.notna(closes.iloc[-1].get("result_r")):
            # broker-realised R is authoritative and preserved verbatim; the
            # label never overwrites it and no synthetic result is manufactured
            oc.result_r_actual = float(closes.iloc[-1]["result_r"])

        outcomes.append(oc)
        if oc.label is Label.INVALID:
            invalid_ids.append(eid)

        out.loc[rows.index, "label"] = oc.label.value
        out.loc[rows.index, "label_reason"] = oc.label_reason
        out.loc[rows.index, "label_start_ts"] = oc.label_start_ts
        out.loc[rows.index, "label_end_ts"] = oc.label_end_ts
        out.loc[rows.index, "ambiguous_bar"] = bool(oc.ambiguous_bar)
        out.loc[rows.index, "bars_to_outcome"] = int(oc.bars_to_outcome)
        out.loc[rows.index, "mfe_r"] = oc.mfe_r
        out.loc[rows.index, "mae_r"] = oc.mae_r

    # orphan execution rows: Stage 2 already flags them; never invent an episode
    if "episode_id" in out.columns and "event" in out.columns:
        orphan = (out["episode_id"] < 0) & out["event"].isin(
            ("FILL", "PARTIAL_CLOSE", "CLOSE"))
        if orphan.any():
            out.loc[orphan, "label"] = Label.UNLABELLED.value
            out.loc[orphan, "label_reason"] = "ORPHAN_EXECUTION_ROW_NO_EPISODE"
            findings.append(Finding(
                Severity.WARN, "ORPHAN_EXECUTION_ROWS",
                "execution rows with no linked episode; not labelled, not trainable",
                count=int(orphan.sum())))

    if invalid_ids:
        findings.append(Finding(
            Severity.ERROR, "INVALID_EPISODES",
            "episodes whose execution data cannot support a label "
            "(geometry, risk distance, fill timestamp or market data)",
            count=len(invalid_ids), episodes=tuple(invalid_ids[:10])))
    if no_fill_ids:
        findings.append(Finding(
            Severity.WARN, "EPISODES_WITHOUT_FILL",
            "OPEN with no FILL; a decision, not a trade -- excluded from training",
            count=len(no_fill_ids), episodes=tuple(no_fill_ids[:10])))

    ambiguous = [o for o in outcomes if o.ambiguous_bar]
    if ambiguous:
        sev = (Severity.WARN if cfg.ambiguity is AmbiguityPolicy.AMBIGUOUS
               else Severity.INFO)
        findings.append(Finding(
            sev, "AMBIGUOUS_BARS",
            f"episodes where one bar spanned both barriers; policy="
            f"{cfg.ambiguity.value}", count=len(ambiguous),
            episodes=tuple(o.episode_id for o in ambiguous[:10])))

    label_counts = {}
    for o in outcomes:
        label_counts[o.label.value] = label_counts.get(o.label.value, 0) + 1

    stats = {
        "episodes_seen": episodes_seen,
        "episodes_labelled": len(outcomes),
        "rows_annotated": int((out["label"] != Label.UNLABELLED.value).sum()),
        "label_counts": label_counts,
        "ambiguous_count": len(ambiguous),
        "exec_model": cfg.exec_model(),
        "horizon_bars": cfg.horizon_bars,
        "timeframe": cfg.timeframe,
        "ambiguity": cfg.ambiguity.value,
        "fill_bar": cfg.fill_bar.value,
    }
    return LabelResult(out, outcomes, findings, stats)


def training_view(result: LabelResult) -> pd.DataFrame:
    """
    One row per episode with a RESOLVED outcome, for supervised training.

    AMBIGUOUS, UNLABELLED and INVALID are excluded rather than coerced: a label
    that had to be guessed teaches the model the guess, not the market.
    """
    keep = {lab.value for lab in RESOLVED_LABELS}
    frame = result.frame
    rows = frame[(frame["event"] == "OPEN") & frame["label"].isin(keep)]
    return rows.copy()


def load_m1(paths: dict) -> MarketBars:
    """Load closed M1 bars per symbol: {'EURUSD': 'eurusd_m1.csv'}."""
    frames = {}
    for symbol, path in paths.items():
        df = pd.read_csv(path)
        cols = {c.lower(): c for c in df.columns}
        df = df.rename(columns={cols.get("time", "time"): "time"})
        df["time"] = pd.to_datetime(df["time"])
        for c in ("open", "high", "low", "close"):
            if c in cols:
                df[c] = pd.to_numeric(df[cols[c]], errors="coerce")
        frames[symbol] = df[["time", "open", "high", "low", "close"]] \
            .sort_values("time").reset_index(drop=True)
    return MarketBars(frames=frames)


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(
        description="Label NEXA trade episodes with triple-barrier outcomes.")
    ap.add_argument("canonical", help="Stage 2 canonical dataset (.csv/.parquet)")
    ap.add_argument("--m1", action="append", required=True, metavar="SYMBOL=PATH",
                    help="closed M1 bars, repeatable (EURUSD=eurusd_m1.csv)")
    ap.add_argument("--ambiguity", choices=[p.value for p in AmbiguityPolicy],
                    default=AmbiguityPolicy.AMBIGUOUS.value)
    ap.add_argument("--fill-bar", choices=[p.value for p in FillBarPolicy],
                    default=FillBarPolicy.EXCLUDE_FILL_BAR.value)
    ap.add_argument("-o", "--out")
    ap.add_argument("--training-view", help="also write the one-row-per-episode view")
    args = ap.parse_args(argv)

    frame = (pd.read_parquet(args.canonical) if args.canonical.endswith(".parquet")
             else pd.read_csv(args.canonical))
    for c in ("decision_ts", "decision_ts_effective", "fill_ts", "dispatch_ts", "write_ts"):
        if c in frame.columns:
            frame[c] = pd.to_datetime(frame[c], errors="coerce")

    paths = {}
    for spec in args.m1:
        if "=" not in spec:
            raise SystemExit(f"--m1 expects SYMBOL=PATH, got {spec!r}")
        sym, path = spec.split("=", 1)
        paths[sym] = path
    bars = load_m1(paths)

    cfg = LabelConfig(ambiguity=AmbiguityPolicy(args.ambiguity),
                      fill_bar=FillBarPolicy(args.fill_bar))
    result = label_dataset(frame, bars, cfg)
    print(result.report())

    if args.out:
        out = result.frame.copy()
        for col in out.columns:
            if pd.api.types.is_datetime64_any_dtype(out[col]):
                out[col] = out[col].dt.strftime("%Y-%m-%dT%H:%M:%S").fillna("")
        out.to_csv(args.out, index=False, lineterminator="\n")
        print(f"\nwritten: {args.out}")
    if args.training_view:
        training_view(result).to_csv(args.training_view, index=False, lineterminator="\n")
        print(f"training view: {args.training_view}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
