"""Unit tests for nexa_registry2 on a synthetic NEXA root (no market data)."""
from __future__ import annotations

import json
from datetime import UTC, datetime

import numpy as np
import pandas as pd
import pytest

import nexa_registry2 as r2

_rng = np.random.default_rng(3)
_c = 100 + np.cumsum(_rng.normal(0, .3, 800))
_o = np.r_[100, _c[:-1]]
BARS = pd.DataFrame({"open": _o, "high": np.maximum(_o, _c) + .1, "low": np.minimum(_o, _c) - .1, "close": _c})


def causal_b(b):
    return b["close"].rolling(20, min_periods=20).mean()


def leaky_b(b):
    return b["close"].shift(-3)


def uncertified_b(b):
    return b["close"].rolling(5, min_periods=5).max()


def proto(exp="E1", status="ACTIVE", **over):
    p = {"experiment": exp, "version": 2, "status": status, "family": "f", "hypothesis": "h", "symbols": ["EURUSD"],
         "grid": {"k": [1, 2]}, "sensitivity": {"s": ["a", "b"]},
         "claims": {"C": {"params": ["k", "s"], "primary": True}},
         "periods_utc": {"DEV": ["2018-01-01T00:00:00Z", "2023-01-01T00:00:00Z"],
                         "VAL": ["2023-01-01T00:00:00Z", "2025-01-01T00:00:00Z"], "WF_YEARS": [2020],
                         "OOS": ["2027-01-04T00:00:00Z", "2028-01-03T00:00:00Z"]},
         "purge_embargo": {"max_label_minutes": 60, "embargo_minutes": 1440}, "timezone": {"period_bounds": "UTC"},
         "leakage_rules": ["x"], "costs": {}, "execution": {}, "nulls": ["timing", "direction", "circular_shift"],
         "tests": {"alpha": .05, "fdr_q": .1, "dsr_min": .95, "pbo_max": .5, "min_trades_promote": 200,
                   "val_queries_per_trial": 1}}
    if status == "BLOCKED":
        p["blocked_reason"] = "no data"
    p.update(over)
    return p


@pytest.fixture
def env(tmp_path, monkeypatch):
    root = tmp_path / "nexa"
    (root / "research").mkdir(parents=True)
    (root / "NEXA_EA.mq5").write_text("marker")
    (root / "data.csv").write_text("1,2,3\n")
    (root / "code.py").write_text("x = 1\n")
    clock = {"now": datetime(2026, 9, 28, tzinfo=UTC)}
    monkeypatch.setattr(r2, "_utcnow", lambda: clock["now"])
    reg = r2.RegistryV2(str(root / "research" / "reg"), witness_dir=str(tmp_path / "witness"))
    import os
    os.makedirs(reg.root)
    pins = {"data": {"d": {"path": "data.csv", "sha256": r2.sha256_file(str(root / "data.csv"))}},
            "code": {"c": {"path": "code.py", "sha256": r2.sha256_file(str(root / "code.py"))}},
            "design_artifacts": {}}
    anchor = reg.create_and_freeze("T", [proto(), proto("E4", status="BLOCKED")], pins, 5, {"bh": 0.1}, {})
    return reg, anchor, clock, root


def cp(reg, anchor):
    """The head as the operator last published it off-machine (here: the honest current head)."""
    return reg.head_of(reg.verify(anchor)["ledger"])


def tid(k=1, s="a", exp="E1"):
    return r2.trial_id(exp, "C", "EURUSD", {"k": k, "s": s})


def good_record(reg, anchor, t, period="DEV", window=("2019-01-01T00:00:00Z", "2020-01-01T00:00:00Z"),
                first=None, label="2019-12-31T00:00:00Z", **kw):
    c = reg.verify(anchor)["campaign"]
    return reg.record(anchor, t, period, list(window), first or window[0], label, reg.digest(c["pins"]["data"]),
                      reg.digest(c["pins"]["code"]), kw.pop("builders", [causal_b]), {"m": 0}, **kw,
                      checkpoint=cp(reg, anchor))


def open_with_builder(reg, anchor):
    reg.register_builder(anchor, causal_b, BARS, checkpoint=cp(reg, anchor))
    reg.open_evaluation(anchor, "synthetic test approval note, not a real campaign", checkpoint=cp(reg, anchor))


def test_counts_and_state(env):
    reg, anchor, _, _ = env
    v = reg.verify(anchor)
    tc = v["campaign"]["trial_counts"]
    assert tc["active_trials"] == 4 and tc["dsr_trial_count"] == 9 and tc["primary_tests"] == 1
    assert reg.state(v["ledger"]) == "FROZEN"
    with pytest.raises(r2.RegistryError):
        good_record(reg, anchor, tid())


def test_wrong_anchor_fails(env):
    reg, _, _, _ = env
    with pytest.raises(r2.RegistryError):
        reg.verify("0" * 64)


def test_failed_certificate_and_uncertified_builder(env):
    reg, anchor, _, _ = env
    with pytest.raises(r2.RegistryError):
        reg.register_builder(anchor, leaky_b, BARS, checkpoint=cp(reg, anchor))                                     # certify fails
    with pytest.raises(r2.RegistryError):                                               # forged certificate dict
        reg.register_builder(anchor, {"builder": "leaky", "source_sha256": "X", "passed": True}, BARS,
                             checkpoint=cp(reg, anchor))
    with pytest.raises(r2.RegistryError):
        reg.register_builder(anchor, causal_b, BARS.iloc[:100], checkpoint=cp(reg, anchor))                         # too few bars
    open_with_builder(reg, anchor)
    for bad in ([uncertified_b], [causal_b, leaky_b], ["sha-string"]):
        with pytest.raises(r2.RegistryError):
            good_record(reg, anchor, tid(), builders=bad)
    with pytest.raises(r2.RegistryError):
        reg.register_builder(anchor, uncertified_b, BARS, checkpoint=cp(reg, anchor))                               # after opening


def test_period_embargo_purge_rules(env):
    reg, anchor, _, _ = env
    open_with_builder(reg, anchor)
    good_record(reg, anchor, tid())
    with pytest.raises(r2.RegistryError):     # VAL first entry inside the embargo
        good_record(reg, anchor, tid(), "VAL", ("2023-01-01T00:00:00Z", "2024-01-01T00:00:00Z"),
                    first="2023-01-01T06:00:00Z", label="2023-06-01T00:00:00Z")
    with pytest.raises(r2.RegistryError):     # label crosses the DEV end (purge)
        good_record(reg, anchor, tid(), "DEV", ("2022-01-01T00:00:00Z", "2023-01-01T00:00:00Z"),
                    label="2023-01-01T00:30:00Z")
    with pytest.raises(r2.RegistryError):     # non-UTC timestamp
        good_record(reg, anchor, tid(), "DEV", ("2019-01-01T00:00:00", "2020-01-01T00:00:00Z"))


def test_val_budget_selection_and_oos_lifecycle(env):
    reg, anchor, clock, _ = env
    open_with_builder(reg, anchor)
    val = ("2023-01-02T00:00:00Z", "2024-12-01T00:00:00Z")
    good_record(reg, anchor, tid(1, "a"), "VAL", val, label="2024-11-30T00:00:00Z")
    with pytest.raises(r2.RegistryError):
        good_record(reg, anchor, tid(1, "a"), "VAL", val, label="2024-11-30T00:00:00Z")      # budget = 1
    with pytest.raises(r2.RegistryError):
        reg.select_for_oos(anchor, tid(2, "a"), "no VAL yet", checkpoint=cp(reg, anchor))
    reg.select_for_oos(anchor, tid(1, "a"), "best lower bound", checkpoint=cp(reg, anchor))
    with pytest.raises(r2.RegistryError):
        good_record(reg, anchor, tid(2, "b"), "DEV")                                          # group sealed
    oos = ["2027-01-04T00:00:00Z", "2028-01-03T00:00:00Z"]
    with pytest.raises(r2.RegistryError):
        good_record(reg, anchor, tid(1, "a"), "OOS", oos, first="2027-01-06T00:00:00Z", label="2028-01-01T00:00:00Z")  # not ended
    clock["now"] = datetime(2028, 1, 10, tzinfo=UTC)
    with pytest.raises(r2.RegistryError):
        good_record(reg, anchor, tid(2, "a"), "OOS", oos, first="2027-01-06T00:00:00Z", label="2028-01-01T00:00:00Z")  # not sealed
    good_record(reg, anchor, tid(1, "a"), "OOS", oos, first="2027-01-06T00:00:00Z", label="2028-01-01T00:00:00Z")
    with pytest.raises(r2.RegistryError):
        good_record(reg, anchor, tid(1, "a"), "OOS", oos, first="2027-01-06T00:00:00Z", label="2028-01-01T00:00:00Z")  # repeat
    with pytest.raises(r2.RegistryError):
        good_record(reg, anchor, tid(2, "b"), "VAL", val, label="2024-11-30T00:00:00Z")      # IS closed after OOS start
    assert reg.verify(anchor)


def test_results_file_tamper_detected(env):
    reg, anchor, _, _ = env
    open_with_builder(reg, anchor)
    good_record(reg, anchor, tid())
    with open(reg.results_path) as fh:
        rows = fh.read().replace('"m":0', '"m":9')
    with open(reg.results_path, "w") as fh:
        fh.write(rows)
    with pytest.raises(r2.RegistryError):
        reg.verify(anchor)


def test_invalid_protocols_rejected():
    for bad in ({"sensitivity": {"k": [1]}},                                        # axis both grid and sensitivity
                {"grid": {"k": [1, 1.0]}},                                           # duplicate values after normalisation
                {"purge_embargo": {"max_label_minutes": 60, "embargo_minutes": 30}},
                {"timezone": {"period_bounds": "server"}},
                {"claims": {"C": {"params": ["zz"], "primary": True}}}):
        with pytest.raises(r2.RegistryError):
            r2.validate_protocol(proto(**bad))


def test_blocked_experiment_not_in_universe():
    u = r2.derive_universe([proto(), proto("E4", status="BLOCKED")])
    assert {t["experiment"] for t in u} == {"E1"}
    json.dumps(u)


def test_ledger_truncation_detected_by_witness(env):
    reg, anchor, _, _ = env
    open_with_builder(reg, anchor)
    val = ("2023-01-02T00:00:00Z", "2024-12-01T00:00:00Z")
    good_record(reg, anchor, tid(), "VAL", val, label="2024-11-30T00:00:00Z")
    with open(reg.ledger_path) as fh:
        rows = fh.read().splitlines()[:-1]
    with open(reg.ledger_path, "w") as fh:
        fh.write("\n".join(rows) + "\n")
    with open(reg.results_path, "w") as fh:
        fh.write("")
    with pytest.raises(r2.RegistryError, match="witness"):
        good_record(reg, anchor, tid(), "VAL", val, label="2024-11-30T00:00:00Z")


def test_missing_witness_and_malformed_ledger(env, tmp_path):
    reg, anchor, _, _ = env
    other = r2.RegistryV2(reg.root, nexa_root=reg.nexa_root, witness_dir=str(tmp_path / "empty"))
    with pytest.raises(r2.RegistryError, match="witness missing"):
        other.verify(anchor)
    with open(reg.ledger_path, "a") as fh:
        fh.write('{"seq": 1, "event": "EVALUATION_OPENED"}\n')
    with pytest.raises(r2.RegistryError):
        reg.verify(anchor)
    with open(reg.ledger_path, "a") as fh:
        fh.write("not json\n")
    with pytest.raises(r2.RegistryError):
        reg.verify(anchor)


def _rewrite_both(reg, anchor, keep):
    """R1 actor: truncates ledger AND witness consistently (local write access to both)."""
    for pth in (reg.ledger_path, reg.witness_path(anchor)):
        with open(pth) as fh:
            rows = fh.read().splitlines()[:keep]
        with open(pth, "w") as fh:
            fh.write("\n".join(rows) + "\n")


def test_r1_consistent_rollback_is_caught_by_external_checkpoint(env):
    reg, anchor, _, _ = env
    open_with_builder(reg, anchor)
    val = ("2023-01-02T00:00:00Z", "2024-12-01T00:00:00Z")
    good_record(reg, anchor, tid(), "VAL", val, label="2024-11-30T00:00:00Z")
    published = cp(reg, anchor)                                   # operator publishes this off-machine
    _rewrite_both(reg, anchor, keep=published["seq"])            # roll back the VAL query locally
    with open(reg.results_path, "w") as fh:
        fh.write("")
    reg.verify(anchor)                                            # local-only verification cannot see R1 ...
    with pytest.raises(r2.RegistryError, match="checkpoint not found"):
        reg.verify(anchor, checkpoint=published)                  # ... the external checkpoint can
    c = reg.verify(anchor)["campaign"]
    with pytest.raises(r2.RegistryError, match="checkpoint not found"):
        reg.record(anchor, tid(), "VAL", list(val), val[0], "2024-11-30T00:00:00Z", reg.digest(c["pins"]["data"]),
                   reg.digest(c["pins"]["code"]), [causal_b], {"m": 0}, checkpoint=published)


def test_r1_consistent_forged_append_is_caught_and_mutations_need_checkpoint(env):
    reg, anchor, _, _ = env
    published = cp(reg, anchor)
    led = reg.verify(anchor)["ledger"]
    body = {"seq": 1, "utc": "2026-09-28T00:00:00+00:00", "event": "EVALUATION_OPENED",
            "payload": {"approval_note": "forged by a local actor with write access", "sealed_ledger_head": "x"},
            "prev_sha256": led[-1]["entry_sha256"]}
    body["entry_sha256"] = r2.sha256_text(r2.canonical_json(body))
    with open(reg.ledger_path, "a") as fh:
        fh.write(r2.canonical_json(body) + "\n")
    with open(reg.witness_path(anchor), "a") as fh:
        fh.write(r2.canonical_json({"seq": 1, "entry_sha256": body["entry_sha256"]}) + "\n")
    assert reg.state(reg.verify(anchor)["ledger"]) == "OPEN"      # locally consistent forgery ...
    with pytest.raises(r2.RegistryError, match="beyond the external checkpoint"):
        reg.verify(anchor, checkpoint=published)                  # ... rejected against the published head
    with pytest.raises(r2.RegistryError, match="checkpoint"):
        reg.reject(anchor, "no checkpoint supplied", checkpoint=None)
    with pytest.raises(r2.RegistryError, match="checkpoint"):
        reg.reject(anchor, "malformed checkpoint", checkpoint={"seq": True, "entry_sha256": "x"})


def calendar_like(n=260, seed=0):
    rng = np.random.default_rng(seed)
    t = pd.date_range("2020-01-03 13:30", periods=n, freq="7D", tz="UTC")
    return pd.DataFrame({"time_utc": t, "v": rng.normal(0, 1, n)})


def prior_mean(tab):
    return pd.DataFrame({"m": tab["v"].shift(1).expanding().mean()}, index=tab.index)


def full_mean(tab):
    return pd.DataFrame({"m": np.full(len(tab), tab["v"].mean())}, index=tab.index)


def test_event_builder_certified_by_registry_and_leaky_rejected(env):
    reg, anchor, _, _ = env
    tab = calendar_like()
    with pytest.raises(r2.RegistryError, match="FAILED"):
        reg.register_event_builder(anchor, full_mean, tab, "time_utc", ("v",), ("m",), checkpoint=cp(reg, anchor))
    e = reg.register_event_builder(anchor, prior_mean, tab, "time_utc", ("v",), ("m",), checkpoint=cp(reg, anchor))
    assert e["payload"]["kind"] == "events" and e["payload"]["perturbed"] == ["v"]
    with pytest.raises(r2.RegistryError, match=">= 200"):
        reg.register_event_builder(anchor, prior_mean, tab.iloc[:50], "time_utc", ("v",), ("m",),
                                   checkpoint=cp(reg, anchor))


def test_missing_protocol_file_fails_as_registry_error(env):
    import os
    reg, anchor, _, _ = env
    os.remove(reg.protocol_path("E4", 2))
    with pytest.raises(r2.RegistryError, match="unreadable or incomplete"):
        reg.verify(anchor)


def test_corrupt_or_missing_universe_fails_as_registry_error(env):
    import os
    reg, anchor, _, _ = env
    os.remove(reg.universe_path)
    with pytest.raises(r2.RegistryError, match="unreadable or incomplete"):
        reg.verify(anchor)


def test_malformed_record_arguments_and_pinned_path_as_directory(env):
    import os
    reg, anchor, _, root = env
    open_with_builder(reg, anchor)
    c = reg.verify(anchor)["campaign"]
    for bad in (["2019-01-01T00:00:00Z"], "2019-01-01T00:00:00Z", [1, 2]):
        with pytest.raises(r2.RegistryError, match="window_utc"):
            reg.record(anchor, tid(), "DEV", bad, "2019-01-01T00:00:00Z", "2019-12-31T00:00:00Z",
                       reg.digest(c["pins"]["data"]), reg.digest(c["pins"]["code"]), [causal_b], {"m": 0},
                       checkpoint=cp(reg, anchor))
    os.remove(root / "data.csv")
    os.makedirs(root / "data.csv")
    with pytest.raises(r2.RegistryError, match="changed or missing"):
        reg.verify(anchor)


@pytest.mark.parametrize("bad", ["garbageZ", "2023-01-01T00:00:00+07:00Z", "2023-13-01T00:00:00Z", 20230101])
def test_parse_utc_rejects_malformed_and_offset_timestamps(bad):
    with pytest.raises(r2.RegistryError):
        r2.parse_utc(bad)
