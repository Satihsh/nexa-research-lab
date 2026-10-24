"""Tests for nexa_factory: simulator arithmetic on hand-built bars, and
causality of every indicator/strategy (future bars must not change the past).
Bars here are constructed fixtures, not market data."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import nexa_factory as f

ZERO = f.CostModel("zero", 0.0, 0.0)


def bars(rows, start="2024-01-02 00:00", freq="1h"):
    t = pd.date_range(start, periods=len(rows), freq=freq)
    o, h, lo, c = zip(*rows, strict=True)
    return pd.DataFrame({"time": t, "open": o, "high": h, "low": lo, "close": c})


def random_walk(n=1500, seed=0):
    rng = np.random.default_rng(seed)
    c = 100 + np.cumsum(rng.normal(0, 0.3, n))
    o = np.concatenate(([100.0], c[:-1]))
    h = np.maximum(o, c) + rng.uniform(0, 0.3, n)
    lo = np.minimum(o, c) - rng.uniform(0, 0.3, n)
    return pd.DataFrame({"time": pd.date_range("2024-01-01", periods=n, freq="1h"),
                         "open": o, "high": h, "low": lo, "close": c})


# ------------------------------------------------------------- simulator

def test_long_tp_hit_enters_next_open():
    b = bars([(100, 100.5, 99.5, 100), (100, 100.5, 99.8, 100.2), (100.2, 102.5, 100.1, 102.4)])
    sig = np.array([1, 0, 0])
    tr = f.simulate(b, sig, np.full(3, 1.0), target_r=2.0, max_hold=10, cost=ZERO).frame
    assert len(tr) == 1
    row = tr.iloc[0]
    assert row.entry == 100 and row.exit_reason == "TP_WIN"
    assert row.r_net == pytest.approx(2.0)
    assert row.entry_ts == b.time[1]


def test_ambiguous_bar_takes_the_stop():
    b = bars([(100, 100, 100, 100), (100, 103, 98, 100)])
    tr = f.simulate(b, np.array([1, 0]), np.full(2, 1.0), 2.0, 10, ZERO).frame.iloc[0]
    assert tr.exit_reason == "SL_LOSS" and tr.ambiguous
    assert tr.r_net == pytest.approx(-1.0)


def test_gap_through_stop_fills_at_open_not_at_stop():
    b = bars([(100, 100, 100, 100), (100, 100.2, 99.9, 100), (97, 97.5, 96.5, 97)])
    tr = f.simulate(b, np.array([1, 0, 0]), np.full(3, 1.0), 2.0, 10, ZERO).frame.iloc[0]
    assert tr.exit_reason == "SL_LOSS" and tr.exit == 97
    assert tr.r_net == pytest.approx(-3.0)


def test_time_exit_at_close_of_last_bar():
    b = bars([(100, 100, 100, 100)] + [(100, 100.4, 99.6, 100.1)] * 3)
    tr = f.simulate(b, np.array([1, 0, 0, 0]), np.full(4, 1.0), 2.0, 2, ZERO).frame.iloc[0]
    assert tr.exit_reason == "TIME_EXIT" and tr.bars_held == 2
    assert tr.r_net == pytest.approx(0.1)


def test_costs_reduce_r_by_spread_plus_two_slippages():
    b = bars([(100, 100, 100, 100)] + [(100, 100.4, 99.6, 100.1)] * 3)
    cost = f.CostModel("c", spread=0.2, slippage=0.05)
    tr = f.simulate(b, np.array([1, 0, 0, 0]), np.full(4, 1.0), 5.0, 2, cost).frame.iloc[0]
    assert tr.r_gross - tr.r_net == pytest.approx(0.3)


def test_relative_costs_scale_with_price():
    b = bars([(1000, 1000, 1000, 1000)] + [(1000, 1004, 996, 1001)] * 3)
    cost = f.CostModel("bps", spread=2e-4, slippage=1e-4, relative=True)   # 0.2 + 2*0.1 price
    tr = f.simulate(b, np.array([1, 0, 0, 0]), np.full(4, 10.0), 5.0, 2, cost).frame.iloc[0]
    assert tr.r_gross - tr.r_net == pytest.approx(0.4 / 10.0)


def test_short_exits_trigger_on_ask():
    # bid high 100.9 + spread 0.2 = 101.1 ask >= stop 101.0 -> stopped although bid never reached it
    b = bars([(100, 100, 100, 100), (100, 100.9, 99.9, 100)])
    cost = f.CostModel("s", spread=0.2, slippage=0.0)
    tr = f.simulate(b, np.array([-1, 0]), np.full(2, 1.0), 2.0, 5, cost).frame.iloc[0]
    assert tr.exit_reason == "SL_LOSS"


def test_one_position_at_a_time():
    b = random_walk(300)
    sig = np.ones(300, dtype=int)
    tr = f.simulate(b, sig, np.full(300, 0.5), 2.0, 10, ZERO).frame
    assert (tr.entry_ts.values[1:] > tr.exit_ts.values[:-1]).all()


def test_nan_stop_means_no_trade():
    b = random_walk(50)
    assert f.simulate(b, np.ones(50, int), np.full(50, np.nan), 2.0, 5, ZERO).frame.empty


# ------------------------------------------------------------- causality

def _perturb_after(b, k, seed=99):
    b2 = b.copy()
    rng = np.random.default_rng(seed)
    n = len(b2) - k
    shift = rng.normal(0, 5, n)
    for col in ("open", "high", "low", "close"):
        b2.loc[k:, col] = b2.loc[k:, col].values + shift
    b2.loc[k:, "high"] = b2.loc[k:, ["open", "high", "low", "close"]].max(axis=1)
    b2.loc[k:, "low"] = b2.loc[k:, ["open", "high", "low", "close"]].min(axis=1)
    return b2


@pytest.mark.parametrize("fn", [
    lambda b: f.atr(b, 14),
    lambda b: f.adx(b, 14),
    lambda b: f.supertrend_dir(b, 3.0, 10).astype(float),
    lambda b: f.donchian_prior(b, 20)[0],
    lambda b: f.prev_day_hlc(b)[0],
    lambda b: f.htf_value_asof(b, f.resample_last_closed(b, "4h"),
                               f.resample_last_closed(b, "4h").close.values),
])
def test_indicator_is_causal(fn):
    b = random_walk(800)
    k = 500
    a, a2 = fn(b), fn(_perturb_after(b, k))
    np.testing.assert_array_equal(np.nan_to_num(a[:k], nan=-9e9), np.nan_to_num(a2[:k], nan=-9e9))


def test_htf_bar_not_visible_before_its_period_ends():
    b = random_walk(48)                     # 2 days of H1 from 00:00
    htf = f.resample_last_closed(b, "4h")
    v = f.htf_value_asof(b, htf, htf.close.values)
    assert np.isnan(v[:3]).all()            # 00:00-02:00: first H4 bar still forming
    assert v[3] == pytest.approx(b.close[3])  # 03:00 bar closes the 00-04 H4 bar


@pytest.mark.parametrize("strategy", f.registry(), ids=lambda s: s.name)
def test_every_registered_strategy_is_causal(strategy):
    b = random_walk(1200, seed=3)
    k = 900
    s1, d1 = strategy.build(b, **strategy.params)
    s2, d2 = strategy.build(_perturb_after(b, k), **strategy.params)
    np.testing.assert_array_equal(s1[:k], s2[:k])
    np.testing.assert_array_equal(np.nan_to_num(d1[:k]), np.nan_to_num(d2[:k]))


def test_registry_specs_are_complete_and_unique():
    reg = f.registry()
    assert len({s.name for s in reg}) == len(reg)
    for s in reg:
        for fld in ("hypothesis", "invalidation", "regime_assumption", "failure_conditions", "source"):
            assert getattr(s, fld)
    assert any(s.family == "null" for s in reg)


def test_load_bars_strips_mislabelled_utc_suffix(tmp_path):
    p = tmp_path / "x.csv"
    p.write_text("time,open,high,low,close\n2024-01-02T01:00:00+0000,1,2,0.5,1.5\n")
    b = f.load_bars(str(p))
    assert str(b.time[0]) == "2024-01-02 01:00:00"


def test_load_bars_rejects_bad_geometry(tmp_path):
    p = tmp_path / "x.csv"
    p.write_text("time,open,high,low,close\n2024-01-02 01:00,1,1.2,0.5,1.5\n")
    with pytest.raises(ValueError):
        f.load_bars(str(p))
