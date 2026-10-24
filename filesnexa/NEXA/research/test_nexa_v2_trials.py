"""V2 trial layer: order geometry, costs, swaps, nulls, bootstrap, selection and verdict logic.
Synthetic bars only; contracts.json is a specification file, not market data."""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest

import nexa_v2_features as nf
import nexa_v2_trials as tr

CONTRACTS = tr.load_contracts(os.path.join(os.path.dirname(__file__), "..", "data", "pepperstone", "contracts.json"))
F1 = {"z_star": 0.5, "delta_min": 2, "hold_min": 30, "target_r": 2}
F2 = {"buffer_b": 0.1, "target_r": 1.5, "stop": "range_mid", "asian_end_utc_hour": 6}
F3 = {"min_size_atr": 0.25, "validity_bars": 12, "target_r": 2, "entry": "edge", "timeframe": "M5", "fill_rule": "through_1pt"}
F5 = {"z_star": 1.5, "stop_k": 1.0, "hold_bars": 60, "anchor": "mean", "session_start_utc_hour": 23}


@pytest.fixture(scope="module")
def data():
    b = nf.synthetic_bars()
    return b, {k: fn(b) for k, (fn, _) in nf.BUILDERS.items()}


def _check_geometry(planned):
    assert planned
    for p in planned:
        o, d = p.order, p.order.direction
        ref = o.level if o.kind == "LIMIT" else p.ref
        assert d * (ref - o.sl) > 0                       # stop on the losing side
        assert o.tp is None or d * (o.tp - ref) > 0       # target on the winning side


def test_order_geometry_per_family(data):
    b, F = data
    for exp, claim, cfg in [("F1_MACRO_EVENT", "H1b_direction", F1), ("F2_XAU_SESSION_BREAKOUT", "continuation", F2),
                            ("F2_XAU_SESSION_BREAKOUT", "continuation", {**F2, "stop": "atr_x10"}),
                            ("F3_FVG_RETRACEMENT", "H3b_limit_expectancy", F3),
                            ("F3_FVG_RETRACEMENT", "H3b_limit_expectancy", {**F3, "entry": "mid"}),
                            ("F5_ASIAN_MEAN_REVERSION", "reversion", F5)]:
        _check_geometry(tr.plan_orders(exp, claim, cfg, b, F[exp]))


def test_time_rules(data):
    b, F = data
    for p in tr.plan_orders("F1_MACRO_EVENT", "H1b_direction", F1, b, F["F1_MACRO_EVENT"]):
        assert p.order.exit_time - p.order.signal_time == pd.Timedelta(minutes=30)
    for p in tr.plan_orders("F2_XAU_SESSION_BREAKOUT", "continuation", F2, b, F["F2_XAU_SESSION_BREAKOUT"]):
        assert p.order.exit_time == p.order.signal_time.normalize() + pd.Timedelta(hours=16)
        assert 6 * 60 <= p.order.signal_time.hour * 60 + p.order.signal_time.minute <= 10 * 60
    for p in tr.plan_orders("F5_ASIAN_MEAN_REVERSION", "reversion", F5, b, F["F5_ASIAN_MEAN_REVERSION"]):
        end = tr._session_end(p.order.signal_time, 6 * 60)
        assert p.order.exit_time <= end and p.order.exit_time <= p.order.signal_time + pd.Timedelta(minutes=60)
    for p in tr.plan_orders("F3_FVG_RETRACEMENT", "H3b_limit_expectancy", F3, b, F["F3_FVG_RETRACEMENT"]):
        o = p.order
        assert o.kind == "LIMIT" and o.max_hold == pd.Timedelta(minutes=48 * 5)
        assert o.expiry <= o.signal_time + pd.Timedelta(minutes=12 * 5)
        assert (o.cancel_level < o.level) if o.direction > 0 else (o.cancel_level > o.level)


def test_exec_config_costs_and_fill_rules():
    assert tr.exec_config("F1_MACRO_EVENT", F1).slip_spread_frac == pytest.approx(1.5)          # event x3
    assert tr.exec_config("F5_ASIAN_MEAN_REVERSION", F5).slip_spread_frac == pytest.approx(0.5)
    for rule, thr in [("touch", 0.0), ("through_1pt", 1.0), ("through_2pt", 2.0)]:
        assert tr.exec_config("F3_FVG_RETRACEMENT", {**F3, "fill_rule": rule}).through_points == thr
    c = tr.exec_config("F2_XAU_SESSION_BREAKOUT", F2)
    assert c.latency_ms == 250 and c.commission_per_lot_side == 3.5
    assert tr.instrument("USDJPY", CONTRACTS).account_is_base and tr.instrument("XAUUSD", CONTRACTS).contract_size == 100


def test_rollovers_wednesday_triple_and_server_midnight():
    # server = UTC+3 in summer: server midnight = 21:00 UTC
    assert tr.rollovers(pd.Timestamp("2024-07-02 20:30"), pd.Timestamp("2024-07-02 20:59")) == 0
    assert tr.rollovers(pd.Timestamp("2024-07-02 20:30"), pd.Timestamp("2024-07-02 21:30")) == 1     # Tue -> Wed
    assert tr.rollovers(pd.Timestamp("2024-07-03 20:30"), pd.Timestamp("2024-07-03 21:30")) == 3     # Wed -> Thu


def test_swap_is_only_ever_a_charge(data):
    b, F = data
    p = tr.plan_orders("F5_ASIAN_MEAN_REVERSION", "reversion", F5, b, F["F5_ASIAN_MEAN_REVERSION"])
    t = tr.simulate(p, b, "USDJPY", CONTRACTS, tr.exec_config("F5_ASIAN_MEAN_REVERSION", F5))
    assert (t["swap_price"] >= 0).all()
    filled = t[t["status"].isin(["FILLED_CLOSED", "OPEN_AT_END"])]
    assert (filled["r_net_swap"] <= filled["r_net"] + 1e-12).all()


def test_nulls_preserve_structure(data):
    b, F = data
    p = tr.plan_orders("F1_MACRO_EVENT", "H1b_direction", F1, b, F["F1_MACRO_EVENT"])
    tm = tr.null_timing(p, 7)
    assert [x.order.signal_time for x in tm] == [x.order.signal_time for x in p]
    for a, z in zip(p, tm, strict=True):
        if a.order.direction != z.order.direction:
            assert z.order.sl == pytest.approx(2 * a.ref - a.order.sl)
    tt = pd.to_datetime(b["time_utc"], utc=True)
    how = (tt.dt.dayofweek * 24 + tt.dt.hour).to_numpy()
    dn = tr.null_direction(p, b, 7)
    assert [x.order.direction for x in dn] == [x.order.direction for x in p]
    assert all(how[a.row] == how[z.row] for a, z in zip(p, dn, strict=True))
    for a, z in zip(p, dn, strict=True):
        assert (z.order.sl - z.ref) == pytest.approx(a.order.sl - a.ref)
    cs = tr.null_circular(p, b, 7)
    assert len(cs) == len(p)                                          # synthetic sample is one year: nothing dropped
    for a, z in zip(p, cs, strict=True):
        assert abs(z.order.signal_time - a.order.signal_time) >= pd.Timedelta(days=7) - pd.Timedelta(minutes=1)
        assert z.order.signal_time.year == a.order.signal_time.year
    assert tr.null_timing(p, 7) == tm                                                     # deterministic


def test_matched_zones_same_size_side_and_distance(data):
    b, F = data
    f = F["F3_FVG_RETRACEMENT"]
    mz = tr.matched_zones(F3, b, f, 3)
    col = "sig_f3_M5_m0.25"
    real = f[f[col] != 0]
    null = mz[mz[col] != 0]
    assert len(null) > 0.8 * len(real)
    assert (null.index.isin(real.index)).mean() < 0.05                                   # different rows
    sizes_real = sorted(np.round((real["f3_top_M5"] - real["f3_bot_M5"]).to_numpy(), 9))
    sizes_null = np.round((null["f3_top_M5"] - null["f3_bot_M5"]).to_numpy(), 9)
    assert set(sizes_null) <= set(sizes_real)
    assert (f.loc[null.index, "f3_dir_M5"] == 0).all()                                    # no gap structure there


def test_f1_surprise_shuffle_permutes_within_event():
    cal = pd.DataFrame({"event_id": [1] * 5 + [2] * 5, "f1_eligible": True, "prior_surprise_sd": 2.0,
                        "forecast": 0.0, "actual": [1., 2., 3., 4., 5., 10., 20., 30., 40., 50.]})
    sh = tr.f1_shuffled_calendar(cal, 1)
    for ev in (1, 2):
        assert sorted(sh.loc[cal.event_id == ev, "actual"]) == sorted(cal.loc[cal.event_id == ev, "actual"])
    assert not sh["actual"].equals(cal["actual"])


def test_bootstrap_selection_and_verdicts():
    r = np.random.default_rng(0).normal(0.0, 1.0, 300)
    times = pd.date_range("2024-01-01", periods=300, freq="5h")
    a, b2 = tr.lower_bound(r, times), tr.lower_bound(r, times)
    assert a == b2 and a["lower"] < a["mean"]
    rows = [{"trial_id": "b", "n": 40, "lower": 0.1, "n_params": 4}, {"trial_id": "a", "n": 40, "lower": 0.1, "n_params": 4},
            {"trial_id": "c", "n": 10, "lower": 0.9, "n_params": 4}, {"trial_id": "d", "n": 50, "lower": 0.05, "n_params": 3}]
    assert tr.select(rows) == "a"                                                        # c: too few; tie -> id
    assert tr.select([{"trial_id": "x", "n": 5, "lower": 1.0, "n_params": 1}]) is None
    good = {"group": ("E", "C", "S"), "r": np.random.default_rng(1).normal(0.3, 1, 400), "n": 400, "p_boot": 0.001,
            "null_p": {"timing": 0.001, "direction": 0.001, "circular_shift": 0.001}, "pbo": 0.2}
    weak_null = {**good, "null_p": {**good["null_p"], "direction": 0.2}}
    v = tr.primary_verdicts([good, weak_null], dsr_trials=1740, var_sr_trials=0.0001)
    assert v[1]["verdict"] == "NOT_DEMONSTRATED" and not v[1]["checks"]["p_iut"]
    few = {**good, "n": 150}
    assert tr.primary_verdicts([few], 1740, 0.0001)[0]["verdict"] == "NOT_DEMONSTRATED"
