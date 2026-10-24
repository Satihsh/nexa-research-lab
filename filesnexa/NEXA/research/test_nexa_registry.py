"""Tests for nexa_registry: freezing, tamper evidence, trial accounting, state machine,
pre-declaration and one-shot OOS enforcement. Uses a temporary registry root."""
from __future__ import annotations

import json

import pytest

import nexa_registry as reg


def _rj(path):
    with open(path) as fh:
        return json.load(fh)


def _wj(obj, path):
    with open(path, "w") as fh:
        json.dump(obj, fh)


def _rt(path):
    with open(path) as fh:
        return fh.read()


def _wt(path, text):
    with open(path, "w") as fh:
        fh.write(text)


def proto(**over):
    p = {"experiment": "F3_FVG", "version": 1, "family": "fvg", "hypothesis": "h", "status": "ACTIVE",
         "symbols": ["EURUSD", "XAUUSD"], "grid": {"m": [0.1, 0.25], "k": [1, 2, 3]},
         "periods": {"DEV": ["2018-01-01", "2022-12-31"], "VAL": ["2023-01-01", "2024-12-31"],
                     "OOS": ["2025-01-01", "2026-08-27"]},
         "data": {"m1": "sha"}, "costs": {}, "execution": {}, "labels": {}, "metrics": [],
         "nulls": ["timing", "direction", "circular_shift"], "failure_criteria": [],
         "tests": {"alpha": 0.05, "fdr_q": 0.10, "dsr_min": 0.95, "pbo_max": 0.5,
                   "min_trades_report": 30, "min_trades_promote": 200}}
    p.update(over)
    return p


def test_hash_is_order_independent_and_content_sensitive():
    a = proto()
    b = json.loads(json.dumps(a, sort_keys=False))
    b = dict(reversed(list(b.items())))
    assert reg.protocol_hash(a) == reg.protocol_hash(b)
    assert reg.protocol_hash(a) != reg.protocol_hash(proto(hypothesis="h2"))


def test_freeze_is_immutable_and_versioned(tmp_path):
    r = reg.Registry(str(tmp_path))
    p1 = r.freeze_protocol(proto())
    assert r.freeze_protocol(proto())["sha256"] == p1["sha256"]          # idempotent
    with pytest.raises(reg.RegistryError):
        r.freeze_protocol(proto(hypothesis="changed"))                   # same version, new content
    p2 = r.freeze_protocol(proto(hypothesis="changed", version=2))
    assert p2["sha256"] != p1["sha256"]


def test_tampering_with_frozen_protocol_is_detected(tmp_path):
    r = reg.Registry(str(tmp_path))
    r.freeze_protocol(proto())
    path = r.protocol_path("F3_FVG", 1)
    d = _rj(path)
    d["grid"]["k"] = [1, 2, 3, 5]
    _wj(d, path)
    with pytest.raises(reg.RegistryError):
        r.load_protocol("F3_FVG", 1)


def test_ledger_hash_chain_detects_edits(tmp_path):
    r = reg.Registry(str(tmp_path))
    r.freeze_protocol(proto())
    r.freeze_protocol(proto(experiment="F5_ASIA"))
    assert r.verify_ledger()
    lines = _rt(r.ledger_path).splitlines()
    e = json.loads(lines[0])
    e["payload"]["declared_trials"] = 1
    lines[0] = json.dumps(e)
    _wt(r.ledger_path, "\n".join(lines) + "\n")
    assert not r.verify_ledger()


@pytest.mark.parametrize("bad", [
    {"periods": {"DEV": ["2018-01-01", "2023-06-30"], "VAL": ["2023-01-01", "2024-12-31"], "OOS": ["2025-01-01", "2026-08-27"]}},
    {"nulls": ["timing"]},
    {"status": "BLOCKED"},                     # blocked without a reason
    {"grid": {"m": []}},
    {"tests": {"alpha": 0.05}},
])
def test_invalid_protocols_rejected(tmp_path, bad):
    with pytest.raises(reg.RegistryError):
        reg.Registry(str(tmp_path)).freeze_protocol(proto(**bad))


def test_trial_accounting_includes_legacy_and_excludes_blocked(tmp_path):
    r = reg.Registry(str(tmp_path))
    r.freeze_protocol(proto())                                                       # 6 configs x 2 symbols
    r.freeze_protocol(proto(experiment="F4_LAT", status="BLOCKED", blocked_reason="no second feed"))
    c = r.create_campaign("C1", [("F3_FVG", 1), ("F4_LAT", 1)], legacy_trials=108, correction={"bh_q": 0.1})
    assert c["declared_trials_active"] == 12 and c["dsr_trial_count"] == 120 and c["primary_tests"] == 2


def test_state_machine_blocks_evaluation_until_opened(tmp_path):
    r = reg.Registry(str(tmp_path))
    r.freeze_protocol(proto())
    r.create_campaign("C1", [("F3_FVG", 1)], legacy_trials=0, correction={})
    cfg = {"k": 1, "m": 0.1}
    with pytest.raises(reg.RegistryError):
        r.record_result("C1", "F3_FVG", cfg, "EURUSD", "DEV", {})                    # DRAFT
    r.freeze_campaign("C1")
    with pytest.raises(reg.RegistryError):
        r.record_result("C1", "F3_FVG", cfg, "EURUSD", "DEV", {})                    # FROZEN, not open
    with pytest.raises(reg.RegistryError):
        r.open_evaluation("C1", "ok")                                                # note too short
    r.open_evaluation("C1", "Phase 3 approved by user on 2026-10-01")
    r.record_result("C1", "F3_FVG", cfg, "EURUSD", "DEV", {"e": 0.0})


def test_undeclared_config_symbol_and_repeat_oos_rejected(tmp_path):
    r = reg.Registry(str(tmp_path))
    r.freeze_protocol(proto())
    r.freeze_protocol(proto(experiment="F4_LAT", status="BLOCKED", blocked_reason="no second feed"))
    r.create_campaign("C1", [("F3_FVG", 1), ("F4_LAT", 1)], legacy_trials=0, correction={})
    r.freeze_campaign("C1")
    r.open_evaluation("C1", "Phase 3 approved by user on 2026-10-01")
    with pytest.raises(reg.RegistryError):
        r.record_result("C1", "F3_FVG", {"k": 4, "m": 0.1}, "EURUSD", "DEV", {})     # not in grid
    with pytest.raises(reg.RegistryError):
        r.record_result("C1", "F3_FVG", {"k": 1, "m": 0.1}, "GBPUSD", "DEV", {})     # not declared
    with pytest.raises(reg.RegistryError):
        r.record_result("C1", "F4_LAT", {"k": 1, "m": 0.1}, "EURUSD", "DEV", {})     # blocked
    r.record_result("C1", "F3_FVG", {"k": 1, "m": 0.1}, "EURUSD", "OOS", {"e": 0.1})
    with pytest.raises(reg.RegistryError):
        r.record_result("C1", "F3_FVG", {"k": 1, "m": 0.1}, "EURUSD", "OOS", {"e": 0.2})
    assert r.verify_ledger()


def test_campaign_freeze_detects_protocol_swap(tmp_path):
    r = reg.Registry(str(tmp_path))
    r.freeze_protocol(proto())
    r.create_campaign("C1", [("F3_FVG", 1)], legacy_trials=0, correction={})
    path = r.protocol_path("F3_FVG", 1)
    d = _rj(path)
    d["hypothesis"] = "swapped"
    d["sha256"] = reg.protocol_hash(d)                     # even a re-hashed swap must be caught
    _wj(d, path)
    with pytest.raises(reg.RegistryError):
        r.freeze_campaign("C1")


def test_phase2_protocols_are_valid_and_freeze_without_evaluating(tmp_path):
    import protocols_phase2 as pp
    refs = {"m1_canonical": {"sha": "x"}, "calendar": {"sha": "y"}, "ticks": {"sha": "z"}, "dna_audit": {"sha": "w"}}
    out = pp.freeze_all(str(tmp_path), refs, campaign="T")
    assert out["campaign"]["state"] == "FROZEN" and out["ledger_valid"]
    assert out["protocols"]["F4_CROSS_FEED_LATENCY"]["status"] == "BLOCKED"
    assert out["campaign"]["dsr_trial_count"] == out["campaign"]["declared_trials_active"] + 108
    r = reg.Registry(str(tmp_path))
    with pytest.raises(reg.RegistryError):
        r.record_result("T", "F3_FVG_RETRACEMENT", {}, "EURUSD", "DEV", {})       # not open for evaluation


def test_rejected_campaign_can_never_be_opened(tmp_path):
    r = reg.Registry(str(tmp_path))
    r.freeze_protocol(proto())
    r.create_campaign("C1", [("F3_FVG", 1)], legacy_trials=0, correction={})
    r.freeze_campaign("C1")
    r.reject_campaign("C1", "OOS contaminated; enforcement insufficient")
    with pytest.raises(reg.RegistryError):
        r.open_evaluation("C1", "Phase 3 approved by user on 2026-10-01")
    assert r.verify_ledger()
