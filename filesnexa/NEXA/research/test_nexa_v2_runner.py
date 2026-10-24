"""V2 evaluation driver on SYNTHETIC bars only: every declared trial maps onto certified builder output,
records satisfy purge/embargo/window rules, and a temporary registry accepts them. No market data."""
from __future__ import annotations

import copy
import os
from datetime import UTC, datetime

import pandas as pd
import pytest

import nexa_registry2 as r2
import nexa_v2_features as nf
import nexa_v2_runner as rn
import nexa_v2_trials as tr
import protocols_phase3_v2 as pv

CONTRACTS = tr.load_contracts(os.path.join(os.path.dirname(__file__), "..", "data", "pepperstone", "contracts.json"))
PROTOS = {p["experiment"]: p for p in pv.build()}
UNIVERSE = r2.derive_universe(pv.build())


@pytest.fixture(scope="module")
def bars():
    return nf.synthetic_bars()


@pytest.fixture(scope="module")
def feats(bars):
    return {k: fn(bars) for k, (fn, _) in nf.BUILDERS.items()}


def test_every_declared_trial_maps_onto_builder_output(bars, feats):
    n = 0
    for t in UNIVERSE:
        exp, claim, cfg = t["experiment"], t["claim"], t["config"]
        if claim == "H3a_revisit":
            tr.h3a_events(cfg, bars, feats[exp])
        else:
            tr.plan_orders(exp, claim, cfg, bars, feats[exp])
            tr.exec_config(exp, cfg)
        n += 1
    assert n == 1632


def _group(exp, claim, sym):
    return [t for t in UNIVERSE if (t["experiment"], t["claim"], t["symbol"]) == (exp, claim, sym)]


def test_records_respect_window_embargo_and_purge(bars):
    p = copy.deepcopy(PROTOS["F2_XAU_SESSION_BREAKOUT"])
    p["periods_utc"]["VAL"] = ["2023-01-01T00:00:00Z", "2024-02-15T00:00:00Z"]       # end inside the synthetic data
    trials = _group("F2_XAU_SESSION_BREAKOUT", "continuation", "XAUUSD")[:6]
    recs = rn.run_group(p, "continuation", "XAUUSD", "VAL", bars, CONTRACTS, trials)
    assert [r["trial_id"] for r in recs] == sorted(t["trial_id"] for t in trials)
    emb = pd.Timedelta(minutes=p["purge_embargo"]["embargo_minutes"])
    for r in recs:
        assert r["window_utc"] == p["periods_utc"]["VAL"]
        fe, le = (pd.Timestamp(r2.parse_utc(x)) for x in (r["first_entry_utc"], r["max_label_end_utc"]))
        assert fe >= pd.Timestamp("2023-01-01", tz="UTC") + emb
        assert le <= pd.Timestamp("2024-02-15", tz="UTC")
        assert r["metrics"]["open_at_end"] == 0 if r["metrics"]["n"] else True
    assert rn.run_group(p, "continuation", "XAUUSD", "VAL", bars, CONTRACTS, trials) == recs         # deterministic


def test_bars_after_window_are_never_passed(bars):
    ws, we = pd.Timestamp("2024-01-10"), pd.Timestamp("2024-02-01")
    s = rn.slice_bars(bars, ws, we)
    t = pd.to_datetime(s["time_utc"]).dt.tz_localize(None)
    assert t.max() < we and t.min() >= ws - pd.Timedelta(days=rn.WARMUP_DAYS)


def test_blocked_family_and_foreign_trial_rejected(bars):
    with pytest.raises(ValueError, match="BLOCKED"):
        rn.run_group(PROTOS["F6_TICK_QUOTE_IMBALANCE"], "executable_edge", "EURUSD", "DEV", bars, CONTRACTS, [])
    wrong = _group("F5_ASIAN_MEAN_REVERSION", "reversion", "EURUSD")[:1]
    with pytest.raises(ValueError, match="does not belong"):
        rn.run_group(PROTOS["F2_XAU_SESSION_BREAKOUT"], "continuation", "XAUUSD", "VAL", bars, CONTRACTS, wrong)


def test_h3a_records(bars):
    trials = _group("F3_FVG_RETRACEMENT", "H3a_revisit", "EURUSD")[:2]
    recs = rn.run_group(PROTOS["F3_FVG_RETRACEMENT"], "H3a_revisit", "EURUSD", "VAL", bars, CONTRACTS, trials)
    for r in recs:
        m = r["metrics"]
        assert m["n"] > 0 and m["n_matched"] > 0 and m["lower"] <= m["diff"]


def test_driver_output_is_accepted_by_a_registry(tmp_path, monkeypatch, bars):
    root = tmp_path / "nexa"
    (root / "research").mkdir(parents=True)
    (root / "NEXA_EA.mq5").write_text("marker")
    (root / "d.txt").write_text("d")
    monkeypatch.setattr(r2, "_utcnow", lambda: datetime(2026, 9, 29, tzinfo=UTC))
    reg = r2.RegistryV2(str(root / "research" / "reg"), witness_dir=str(tmp_path / "w"))
    os.makedirs(reg.root)
    pins = {"data": {"d": {"path": "d.txt", "sha256": r2.sha256_file(str(root / "d.txt"))}},
            "code": {"c": {"path": "d.txt", "sha256": r2.sha256_file(str(root / "d.txt"))}}, "design_artifacts": {}}
    a = reg.create_and_freeze("T", pv.build(), pins, 108, {}, {})
    cp = reg.head_of(reg.verify(a)["ledger"])
    e = reg.register_builder(a, nf.f2_features, bars, checkpoint=cp, extra_cols=("spread",))
    e = reg.open_evaluation(a, "synthetic test approval note for the driver test", checkpoint={"seq": e["seq"], "entry_sha256": e["entry_sha256"]})
    cp = {"seq": e["seq"], "entry_sha256": e["entry_sha256"]}
    trials = _group("F2_XAU_SESSION_BREAKOUT", "continuation", "XAUUSD")[:3]
    recs = rn.run_group(PROTOS["F2_XAU_SESSION_BREAKOUT"], "continuation", "XAUUSD", "VAL", bars, CONTRACTS, trials)
    cp = rn.record_all(reg, a, cp, recs)
    assert cp["seq"] == e["seq"] + 3 and len(reg._results()) == 3
    with pytest.raises(r2.RegistryError, match="budget"):
        rn.record_all(reg, a, cp, recs[:1])                                                # VAL budget = 1
