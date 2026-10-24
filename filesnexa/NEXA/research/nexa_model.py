"""NEXA Gate 9 - meta-label model, forward-only calibration, veto policy, registry.

Primary strategies (the EA's rule engine) PROPOSE trades. This module learns,
from labelled Trade DNA, P(TP before SL | f00..f47) for those proposals, and
turns it into a VETO-ONLY policy:

    size multiplier in {0.0 (REJECT), 0.5 (REDUCE), 1.0 (TAKE)}   never > 1.0

It cannot originate a trade, widen a stop, or raise risk. NEXA_Risk.mqh still
authorises every order.

Hard rules enforced in code
  * No training unless nexa_validate's gate PASSES (fail-closed, raises).
  * Features are exactly f00..f47 as MQL5 emitted them (never recomputed here).
  * Predictions used for evaluation are out-of-fold from PURGED walk-forward
    splits; calibration for fold k is fitted only on OOS predictions of folds < k.
  * Every fitted model is registered with its data hash, feature list, schema
    version, splits and metrics. Status is RESEARCH_ONLY until shadow mode and
    the promotion gate say otherwise; this module can never set LIVE.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import nexa_validate as nv

FEATURES = [f"f{i:02d}" for i in range(48)]
SCHEMA_VERSION = "1.0"
STATUSES = ("RESEARCH_ONLY", "SHADOW", "REJECTED")   # LIVE is set by the promotion gate, not here


# ------------------------------------------------------------------ metrics

def brier(y, p) -> float:
    y, p = np.asarray(y, float), np.asarray(p, float)
    return float(np.mean((p - y) ** 2)) if y.size else float("nan")


def ece(y, p, bins: int = 10) -> float:
    """Expected calibration error with equal-width bins."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    if y.size == 0:
        return float("nan")
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    return float(sum(abs(p[idx == b].mean() - y[idx == b].mean()) * np.mean(idx == b)
                     for b in range(bins) if np.any(idx == b)))


def auc(y, p) -> float:
    y = np.asarray(y)
    return float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else float("nan")


# ------------------------------------------------------------------ policy

@dataclass(frozen=True)
class PolicyConfig:
    cost_r: float = 0.05        # per-trade cost in R charged to the EV estimate
    ev_take: float = 0.10       # EV (R) at or above which the trade keeps full size
    p_floor: float = 0.0        # optional absolute probability floor


def meta_decision(p, target_r, cfg: PolicyConfig | None = None) -> np.ndarray:
    """Size multiplier from calibrated p and the trade's own target R.

    EV = p * target_R - (1 - p) * 1 - cost_R.  EV <= 0 -> 0.0, 0 < EV < ev_take -> 0.5,
    EV >= ev_take -> 1.0. Invalid inputs (NaN p, p outside [0,1], target <= 0) -> 0.0,
    because an invalid decision contract means NO TRADE.
    """
    cfg = cfg or PolicyConfig()
    p = np.asarray(p, float)
    t = np.broadcast_to(np.asarray(target_r, float), p.shape)
    valid = np.isfinite(p) & (p >= 0) & (p <= 1) & np.isfinite(t) & (t > 0)
    ev = np.where(valid, p * t - (1 - p) - cfg.cost_r, -np.inf)
    mult = np.where(ev >= cfg.ev_take, 1.0, np.where(ev > 0, 0.5, 0.0))
    mult = np.where(valid & (p >= cfg.p_floor), mult, 0.0)
    assert np.all(mult <= 1.0)
    return mult


# ------------------------------------------------------------------ core fit on arrays

@dataclass
class OOSResult:
    p_raw: np.ndarray
    p_cal: np.ndarray
    fold: np.ndarray
    per_fold: list = field(default_factory=list)


def _new_model(seed: int):
    return make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=2000, random_state=seed))


def walk_forward_oos(X: np.ndarray, y: np.ndarray, splits: list, seed: int = 0) -> OOSResult:
    """Out-of-fold probabilities. Fold k is calibrated with an isotonic map fitted
    ONLY on the raw OOS predictions of folds < k (fold 0 stays uncalibrated: NaN)."""
    n = len(y)
    p_raw = np.full(n, np.nan)
    p_cal = np.full(n, np.nan)
    fold = np.full(n, -1)
    per = []
    seen_p, seen_y = [], []
    for s in splits:
        tr, te = np.asarray(s.train_idx), np.asarray(s.test_idx)
        if len(tr) == 0 or len(np.unique(y[tr])) < 2:
            per.append({"fold": s.fold, "skipped": "train fold empty or single-class"})
            continue
        m = _new_model(seed).fit(X[tr], y[tr])
        pr = m.predict_proba(X[te])[:, 1]
        p_raw[te], fold[te] = pr, s.fold
        if seen_p:
            iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
            iso.fit(np.concatenate(seen_p), np.concatenate(seen_y))
            p_cal[te] = iso.predict(pr)
        seen_p.append(pr)
        seen_y.append(y[te])
        base = float(np.mean(y[tr]))
        per.append({"fold": s.fold, "n_train": len(tr), "n_test": len(te),
                    "base_rate_train": base, "brier_raw": brier(y[te], pr),
                    "brier_base": brier(y[te], np.full(len(te), base)),
                    "brier_cal": brier(y[te], p_cal[te]) if seen_p[:-1] else None,
                    "ece_raw": ece(y[te], pr), "auc": auc(y[te], pr)})
    return OOSResult(p_raw, p_cal, fold, per)


@dataclass(frozen=True)
class ModelGate:
    min_folds_scored: int = 3
    require_brier_skill_every_fold: bool = True
    max_ece: float = 0.05
    min_auc: float = 0.55


def model_gate(res: OOSResult, y: np.ndarray, gate: ModelGate | None = None) -> tuple[bool, list]:
    gate = gate or ModelGate()
    fails = []
    scored = [f for f in res.per_fold if "brier_raw" in f]
    if len(scored) < gate.min_folds_scored:
        fails.append(f"only {len(scored)} scored folds < {gate.min_folds_scored}")
    if gate.require_brier_skill_every_fold and any(f["brier_raw"] >= f["brier_base"] for f in scored):
        fails.append("no Brier skill over the base rate in at least one fold")
    cal = np.isfinite(res.p_cal)
    if cal.sum() == 0:
        fails.append("no calibrated OOS predictions")
    else:
        e = ece(y[cal], res.p_cal[cal])
        if e > gate.max_ece:
            fails.append(f"calibrated ECE {e:.3f} > {gate.max_ece}")
    ok = np.isfinite(res.p_raw)
    a = auc(y[ok], res.p_raw[ok]) if ok.any() else float("nan")
    if not (np.isfinite(a) and a >= gate.min_auc):
        fails.append(f"OOS AUC {a:.3f} < {gate.min_auc}")
    return (not fails), fails


# ------------------------------------------------------------------ dataset integration

def trainable_in_split_order(frame: pd.DataFrame) -> pd.DataFrame:
    """Rows in EXACTLY the order nexa_validate.make_purged_walk_forward indexes:
    trainable episodes with valid label windows, stable-sorted by label_start_ts."""
    ep = nv.episode_view(frame)
    tr = ep[nv.binary_target(ep["label"]).notna()]
    s = pd.to_datetime(tr["label_start_ts"], errors="coerce")
    e = pd.to_datetime(tr["label_end_ts"], errors="coerce")
    return tr[s.notna() & e.notna()].assign(_s=s).sort_values("_s", kind="mergesort").drop(columns="_s")


def data_hash(df: pd.DataFrame) -> str:
    cols = [c for c in FEATURES + ["label", "label_start_ts", "symbol"] if c in df.columns]
    return hashlib.sha256(pd.util.hash_pandas_object(df[cols], index=False).values.tobytes()).hexdigest()[:16]


def train_meta_model(frame: pd.DataFrame, registry_path: str, seed: int = 0,
                     vcfg: nv.ValidationConfig | None = None) -> dict:
    """Fail-closed end-to-end: validate -> purged walk-forward OOS -> gate -> register."""
    result = nv.validate_dataset(frame, vcfg)
    nv.assert_validation_or_halt(result)                     # raises on FAIL
    work = trainable_in_split_order(frame)
    n_split = sum(len(s.test_idx) for s in result.splits)
    if max(int(np.max(s.test_idx)) for s in result.splits) >= len(work):
        raise RuntimeError("split indices do not align with the trainable ordering")
    X = work[FEATURES].astype(float).values
    y = nv.binary_target(work["label"]).astype(int).values
    res = walk_forward_oos(X, y, result.splits, seed)
    ok, fails = model_gate(res, y)
    entry = {
        "model_id": f"NEXA-META-{data_hash(work)}-s{seed}",
        "created_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "schema_version": SCHEMA_VERSION, "features": FEATURES,
        "algorithm": "StandardScaler+LogisticRegression(C=0.5)", "calibration": "isotonic, forward-only",
        "data_hash": data_hash(work), "n_trainable": len(work), "n_oos": int(n_split),
        "folds": res.per_fold, "gate_passed": ok, "gate_failures": fails,
        "status": "RESEARCH_ONLY" if ok else "REJECTED",
        "note": "veto-only meta-label; cannot authorise or enlarge risk",
    }
    register(registry_path, entry)
    return entry


def register(path: str, entry: dict) -> None:
    """Append-only registry. Existing entries are never rewritten."""
    if entry.get("status") not in STATUSES:
        raise ValueError(f"status {entry.get('status')!r} not allowed from the research tier")
    reg = []
    if os.path.exists(path):
        with open(path) as fh:
            reg = json.load(fh)
    if any(r["model_id"] == entry["model_id"] and r["data_hash"] == entry["data_hash"] for r in reg):
        entry = {**entry, "model_id": entry["model_id"] + f"-r{len(reg)}"}
    reg.append(entry)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as fh:
        json.dump(reg, fh, indent=1, default=_jd)


def _jd(o):
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if hasattr(o, "__dataclass_fields__"):
        return asdict(o)
    return str(o)
