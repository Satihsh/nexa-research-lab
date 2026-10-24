"""Tests for nexa_execution. Constructed quotes/bars only (not market data)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import nexa_execution as ex
import nexa_factory as fct

EURUSD = ex.Instrument("EURUSD", 1e-5, 100_000)
USDJPY = ex.Instrument("USDJPY", 1e-3, 100_000, account_is_quote=False, account_is_base=True)
ZERO = ex.ExecConfig(latency_ms=0, commission_per_lot_side=0.0, slip_points=0, slip_spread_frac=0, through_points=0)


def ticks(rows, start="2025-01-06 10:00:00", step_ms=100):
    t = pd.date_range(start, periods=len(rows), freq=f"{step_ms}ms")
    bid, ask = zip(*rows, strict=True)
    return ex.quotes_from_ticks(pd.DataFrame({"time": t, "bid": bid, "ask": ask}))


def bars(rows, spread_pts=0, start="2025-01-06 10:00"):
    t = pd.date_range(start, periods=len(rows), freq="1min")
    o, h, lo, c = zip(*rows, strict=True)
    return pd.DataFrame({"time": t, "open": o, "high": h, "low": lo, "close": c, "spread": spread_pts})


# ---------------------------------------------------------------- tick mode

def test_market_fills_at_first_quote_after_latency():
    q = ticks([(1.1000, 1.1001)] * 3 + [(1.1010, 1.1011)] * 10)
    cfg = ex.ExecConfig(latency_ms=250, commission_per_lot_side=0, slip_spread_frac=0, through_points=0)
    o = ex.Order(pd.Timestamp("2025-01-06 10:00:00"), 1, "MARKET", sl=1.0990, tp=1.1020)
    r = ex.simulate_order(q, o, EURUSD, cfg)
    assert r.entry == pytest.approx(1.1011)                 # quote at +300 ms, not the +0 ms quote
    assert pd.Timestamp(r.entry_time) == pd.Timestamp("2025-01-06 10:00:00.300")


def test_limit_touch_is_not_a_fill_but_trade_through_is():
    base = [(1.1005, 1.1006)] * 3
    touch = base + [(1.0999, 1.1000)] + [(1.1005, 1.1006)] * 3      # ask == limit: touch only
    cfg = ex.ExecConfig(latency_ms=0, commission_per_lot_side=0, through_points=1)
    o = ex.Order(pd.Timestamp("2025-01-06 10:00:00"), 1, "LIMIT", sl=1.0990, tp=1.1020, level=1.1000)
    assert ex.simulate_order(ticks(touch), o, EURUSD, cfg).status == "EXPIRED"
    through = base + [(1.09985, 1.09995)] + [(1.1005, 1.1006)] * 3
    r = ex.simulate_order(ticks(through), o, EURUSD, cfg)
    assert r.status in ("FILLED_CLOSED", "OPEN_AT_END") and r.entry == pytest.approx(1.09995)


def test_stop_loss_gap_fills_at_market_not_at_level():
    q = ticks([(1.1000, 1.1001)] * 2 + [(1.0980, 1.0981)])          # gaps through sl=1.0990
    r = ex.simulate_order(q, ex.Order(pd.Timestamp("2025-01-06 10:00:00"), 1, "MARKET", sl=1.0990), EURUSD, ZERO)
    assert r.exit_reason == "SL" and r.exit == pytest.approx(1.0980)
    assert r.r_net == pytest.approx((1.0980 - 1.1001) / (1.1001 - 1.0990))


def test_commission_in_r_usd_and_jpy_quoted():
    q = ticks([(1.1000, 1.1000)] * 2 + [(1.1020, 1.1020)])
    cfg = ex.ExecConfig(latency_ms=0, commission_per_lot_side=3.5, slip_spread_frac=0, through_points=0)
    r = ex.simulate_order(q, ex.Order(pd.Timestamp("2025-01-06 10:00:00"), 1, "MARKET", sl=1.0990, tp=1.1020), EURUSD, cfg)
    assert r.commission_price == pytest.approx(7.0 / 100_000)       # 0.7 pip
    assert r.r_net == pytest.approx((0.0020 - 0.00007) / 0.0010)
    assert USDJPY.commission_price(7.0, 150.0) == pytest.approx(7.0 * 150.0 / 100_000)


def test_invalid_stop_side_is_cancelled_not_traded():
    q = ticks([(1.1000, 1.1001)] * 3)
    r = ex.simulate_order(q, ex.Order(pd.Timestamp("2025-01-06 10:00:00"), 1, "MARKET", sl=1.1005), EURUSD, ZERO)
    assert r.status == "CANCELLED_INVALID"


# ---------------------------------------------------------------- bar mode

def test_bar_mode_ambiguous_bar_takes_stop_and_limit_fill_uses_ask():
    b = bars([(1.1005, 1.1006, 1.1004, 1.1005), (1.1003, 1.1030, 1.0985, 1.1000)], spread_pts=2)
    q = ex.quotes_from_bars(b, EURUSD.point)
    o = ex.Order(pd.Timestamp("2025-01-06 10:01"), 1, "MARKET", sl=1.0990, tp=1.1020)
    r = ex.simulate_order(q, o, EURUSD, ZERO)
    assert r.exit_reason == "SL" and r.ambiguous_bar
    assert r.entry == pytest.approx(1.1003 + 0.00002)


def test_bar_mode_latency_must_be_below_one_bar():
    q = ex.quotes_from_bars(bars([(1, 1, 1, 1)] * 3), 1e-5)
    with pytest.raises(ValueError):
        ex.simulate_order(q, ex.Order(pd.Timestamp("2025-01-06 10:01"), 1, "MARKET", sl=0.9),
                          EURUSD, ex.ExecConfig(latency_ms=60_000))


def test_matches_factory_simulator_where_rules_coincide():
    rng = np.random.default_rng(3)
    n = 600
    c = 1.10 + np.cumsum(rng.normal(0, 2e-4, n))
    o = np.concatenate(([1.10], c[:-1]))
    h = np.maximum(o, c) + rng.uniform(0, 2e-4, n)
    lo = np.minimum(o, c) - rng.uniform(0, 2e-4, n)
    b = pd.DataFrame({"time": pd.date_range("2025-01-06", periods=n, freq="1min"),
                      "open": o, "high": h, "low": lo, "close": c, "spread": 1})
    sig = np.zeros(n, int)
    sig[[20, 150, 300, 420]] = [1, -1, 1, -1]
    sd = np.full(n, 6e-4)
    fac = fct.simulate(b, sig, sd, target_r=2.0, max_hold=10_000,
                       cost=fct.CostModel("c", spread=1e-5, slippage=0.0)).frame
    q = ex.quotes_from_bars(b, 1e-5)
    got = []
    for _, row in fac.iterrows():
        d = int(row.direction)
        decision_close = pd.Timestamp(row.decision_ts) + pd.Timedelta(minutes=1)
        ent_bar = q.first_at_or_after(decision_close)
        entry = q.ao[ent_bar] if d > 0 else q.bo[ent_bar]
        order = ex.Order(decision_close, d, "MARKET", sl=entry - d * 6e-4, tp=entry + d * 12e-4)
        got.append(ex.simulate_order(q, order, EURUSD, ZERO).r_net)
    gaps_free = fac.exit_reason.isin(["SL_LOSS", "TP_WIN"])
    np.testing.assert_allclose(np.array(got)[gaps_free.values], fac.r_net[gaps_free].values, atol=1e-9)


def test_determinism_and_fill_summary_counts_unfilled_as_zero():
    b = bars([(1.1005, 1.1006, 1.1004, 1.1005)] * 5 + [(1.1005, 1.1050, 1.1004, 1.1045)] * 3, spread_pts=1)
    q = ex.quotes_from_bars(b, 1e-5)
    orders = [ex.Order(pd.Timestamp("2025-01-06 10:01"), 1, "LIMIT", sl=1.0980, tp=1.1040, level=1.0990,
                       expiry=pd.Timestamp("2025-01-06 10:08"), tag="never_fills"),
              ex.Order(pd.Timestamp("2025-01-06 10:05"), 1, "MARKET", sl=1.0990, tp=1.1040, tag="fills")]
    a = ex.run_one_at_a_time(q, orders, EURUSD, ZERO)
    b2 = ex.run_one_at_a_time(q, orders, EURUSD, ZERO)
    pd.testing.assert_frame_equal(a, b2)
    s = ex.fill_summary(a)
    assert s["placed"] == 2 and s["filled"] == 1 and s["fill_probability"] == 0.5
    assert s["expectancy_per_order_r"] == pytest.approx(s["expectancy_filled_r"] / 2)


# ---------------------------------------------------------------- V2 pre-opening hardening

def test_bar_mode_intrabar_limit_fill_cannot_take_target_on_fill_bar():
    # fill bar dips to 1.0990 (fills the buy limit) AND reaches 1.1040 (the target): order unknown
    b = bars([(1.1005, 1.1006, 1.1004, 1.1005), (1.1000, 1.1045, 1.0985, 1.1000),
              (1.1000, 1.1002, 1.0998, 1.1000), (1.1000, 1.1045, 1.0999, 1.1040)])
    q = ex.quotes_from_bars(b, EURUSD.point)
    o = ex.Order(pd.Timestamp("2025-01-06 10:01"), 1, "LIMIT", sl=1.0970, tp=1.1040, level=1.0990)
    r = ex.simulate_order(q, o, EURUSD, ZERO)
    assert pd.Timestamp(r.entry_time) == pd.Timestamp("2025-01-06 10:01")
    assert r.exit_reason == "TP" and pd.Timestamp(r.exit_time) == pd.Timestamp("2025-01-06 10:03")
    assert r.mfe_r < (1.1045 - 1.0990) / (1.0990 - 1.0970) + 1e-9


def test_bar_mode_intrabar_fill_still_checks_stop_on_fill_bar():
    b = bars([(1.1005, 1.1006, 1.1004, 1.1005), (1.1000, 1.1001, 1.0960, 1.0965), (1.0965, 1.0970, 1.0960, 1.0965)])
    q = ex.quotes_from_bars(b, EURUSD.point)
    o = ex.Order(pd.Timestamp("2025-01-06 10:01"), 1, "LIMIT", sl=1.0970, tp=1.1040, level=1.0990)
    r = ex.simulate_order(q, o, EURUSD, ZERO)
    assert r.exit_reason == "SL" and pd.Timestamp(r.exit_time) == pd.Timestamp("2025-01-06 10:01")


def test_max_hold_is_measured_from_the_fill():
    b = bars([(1.1005, 1.1006, 1.1004, 1.1005)] * 3 + [(1.1000, 1.1001, 1.0985, 1.1000)] + [(1.1000, 1.1002, 1.0998, 1.1000)] * 8)
    q = ex.quotes_from_bars(b, EURUSD.point)
    o = ex.Order(pd.Timestamp("2025-01-06 10:01"), 1, "LIMIT", sl=1.0950, tp=1.1100, level=1.0990,
                 max_hold=pd.Timedelta(minutes=5))
    r = ex.simulate_order(q, o, EURUSD, ZERO)
    assert pd.Timestamp(r.entry_time) == pd.Timestamp("2025-01-06 10:03")
    assert r.exit_reason == "TIME_EXIT" and pd.Timestamp(r.exit_time) == pd.Timestamp("2025-01-06 10:08")


def test_pending_order_cancelled_when_close_beyond_invalidation_level():
    b = bars([(1.1005, 1.1006, 1.1004, 1.1005), (1.1005, 1.1006, 1.0994, 1.0994),   # closes below 1.0995, no fill
              (1.0994, 1.0995, 1.0980, 1.0985)])                                        # would fill here
    q = ex.quotes_from_bars(b, EURUSD.point)
    o = ex.Order(pd.Timestamp("2025-01-06 10:01"), 1, "LIMIT", sl=1.0970, tp=1.1040, level=1.0990,
                 cancel_level=1.0995)
    assert ex.simulate_order(q, o, EURUSD, ZERO).status == "CANCELLED_INVALIDATED"
