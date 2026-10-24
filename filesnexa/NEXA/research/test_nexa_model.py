"""Tests for nexa_model. Arrays are constructed fixtures used to check the
mechanics (veto policy, forward-only calibration, gates, registry). They are
not market data and say nothing about NEXA's performance."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

import nexa_model as nm
import nexa_validate as nv


def _splits(n, folds=5):
    bounds = np.array_split(np.arange(n), folds + 1)
    out = []
    for k in range(folds):
        te = bounds[k + 1]
        out.append(nv.Split(k, np.arange(0, te[0]), te, pd.Timestamp(0), pd.Timestamp(0), 0, 0))
    return out


def _data(n=6000, signal=1.5, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 48))
    logit = signal * X[:, 0] - 0.3
    y = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)
    return X, y


# ------------------------------------------------------------- policy

def test_meta_decision_thresholds_and_veto_only():
    cfg = nm.PolicyConfig(cost_r=0.0, ev_take=0.10)
    # target 2R: EV = 3p - 1  -> p=0.30 EV<0, p=0.35 EV=0.05, p=0.40 EV=0.20
    m = nm.meta_decision([0.30, 0.35, 0.40], 2.0, cfg)
    assert m.tolist() == [0.0, 0.5, 1.0]
    assert np.all(nm.meta_decision(np.linspace(0, 1, 101), 10.0) <= 1.0)


@pytest.mark.parametrize("p,t", [(np.nan, 2.0), (1.2, 2.0), (-0.1, 2.0), (0.9, 0.0), (0.9, np.nan)])
def test_invalid_contract_means_no_trade(p, t):
    assert nm.meta_decision([p], t)[0] == 0.0


# ------------------------------------------------------------- metrics

def test_brier_and_ece_known_values():
    assert nm.brier([1, 0], [1.0, 0.0]) == 0.0
    assert nm.brier([1, 0], [0.5, 0.5]) == pytest.approx(0.25)
    assert nm.ece([1, 0, 1, 0], [0.5, 0.5, 0.5, 0.5]) == pytest.approx(0.0)
    assert nm.ece([1, 1], [0.2, 0.2]) == pytest.approx(0.8)


# ------------------------------------------------------------- walk-forward + calibration

def test_fold0_uncalibrated_later_folds_calibrated():
    X, y = _data(1200)
    sp = _splits(len(y))
    res = nm.walk_forward_oos(X, y, sp)
    assert np.isnan(res.p_cal[sp[0].test_idx]).all()
    assert np.isfinite(res.p_cal[sp[1].test_idx]).all()
    assert np.isnan(res.p_raw[: sp[0].test_idx[0]]).all()     # first block is never scored


def test_calibration_for_fold_k_never_sees_fold_k_labels():
    X, y = _data(1800)
    sp = _splits(len(y))
    a = nm.walk_forward_oos(X, y, sp)
    y2 = y.copy()
    te = sp[2].test_idx
    y2[te] = 1 - y2[te]                                        # corrupt fold-2 outcomes
    b = nm.walk_forward_oos(X, y2, sp)
    np.testing.assert_array_equal(a.p_cal[te], b.p_cal[te])
    np.testing.assert_array_equal(a.p_raw[te], b.p_raw[te])


def test_gate_rejects_pure_noise():
    X, y = _data(3000, signal=0.0, seed=1)
    ok, fails = nm.model_gate(nm.walk_forward_oos(X, y, _splits(len(y))), y)
    assert not ok and any("AUC" in f or "Brier" in f for f in fails)


def test_gate_accepts_genuinely_informative_feature():
    X, y = _data(6000, signal=1.5, seed=2)
    ok, fails = nm.model_gate(nm.walk_forward_oos(X, y, _splits(len(y))), y)
    assert ok, fails


def test_single_class_training_fold_is_skipped_not_crashing():
    X, y = _data(600)
    y[:200] = 0
    res = nm.walk_forward_oos(X, y, _splits(600))
    assert any("skipped" in f for f in res.per_fold)


# ------------------------------------------------------------- integration + registry

def test_training_refuses_empty_dataset(tmp_path):
    with pytest.raises(nv.ValidationGateError):
        nm.train_meta_model(pd.DataFrame(), str(tmp_path / "reg.json"))
    assert not (tmp_path / "reg.json").exists()


def _load(p):
    with open(p) as fh:
        return json.load(fh)


def test_registry_is_append_only_and_refuses_live(tmp_path):
    p = str(tmp_path / "reg.json")
    e = {"model_id": "M1", "data_hash": "h", "status": "RESEARCH_ONLY"}
    nm.register(p, e)
    nm.register(p, e)
    reg = _load(p)
    assert len(reg) == 2 and reg[0]["model_id"] != reg[1]["model_id"]
    with pytest.raises(ValueError):
        nm.register(p, {**e, "status": "LIVE"})
    assert len(_load(p)) == 2


def test_feature_contract_is_frozen_48():
    assert nm.FEATURES == [f"f{i:02d}" for i in range(48)]
    assert nm.SCHEMA_VERSION == "1.0"
