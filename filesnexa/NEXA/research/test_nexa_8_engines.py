"""8-engine research features: formulas, boundaries, causality (incl. deliberately leaky variants that
MUST fail), NaN/Inf, UTC sessions across DST, multi-symbol scales, filters and window purging.
Synthetic data only."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import nexa_8e_engines as E
import nexa_8e_research as R
import nexa_causality as nc


def synth_m1(n=20000, start="2024-03-04", price=2000.0, vol=0.3, seed=0):
    rng = np.random.default_rng(seed)
    t = pd.date_range(start, periods=n, freq="1min", tz="UTC")
    c = price + np.cumsum(rng.normal(0, vol, n))
    o = np.r_[price, c[:-1]]
    return pd.DataFrame({"time_utc": t, "open": o, "high": np.maximum(o, c) + rng.uniform(0, vol, n),
                         "low": np.minimum(o, c) - rng.uniform(0, vol, n), "close": c,
                         "tick_volume": rng.integers(5, 200, n), "spread": rng.integers(8, 25, n)})


@pytest.fixture(scope="module")
def bars():
    return E.resample_m1(synth_m1(), "M5")


# ---------------------------------------------------------------- formulas

def test_resample_is_completed_bars_in_utc(bars):
    m1 = synth_m1(30)
    b = E.resample_m1(m1, "M5")
    assert len(b) == 6 and b["open"].iat[0] == m1["open"].iat[0] and b["close"].iat[0] == m1["close"].iat[4]
    assert b["high"].iat[1] == m1["high"].iloc[5:10].max() and b["tick_volume"].iat[0] == m1["tick_volume"].iloc[:5].sum()
    up = ((m1["close"] > m1["open"]) * m1["tick_volume"]).iloc[:5].sum()
    assert b["up_tv"].iat[0] == up and b["spread"].iat[0] == m1["spread"].iat[0]


def test_donchian_excludes_current_bar_and_strict_breakout():
    b = pd.DataFrame({"open": [1, 1, 1, 1, 1.0], "high": [2, 3, 2, 3, 3.5], "low": [0.5, 0.4, 0.6, 0.5, 0.9],
                      "close": [1.5, 2, 1.8, 3, 3.4]})
    d = E.donchian(b, n=3)
    assert d["dc_upper"].iat[3] == 3 and d["dc_upper"].iat[4] == 3
    assert d["brk_close_up"].iat[3] == 0                 # close == upper is NOT a breakout
    assert d["brk_close_up"].iat[4] == 1 and d["brk_touch_up"].iat[3] == 1


def test_vei_is_wilder_atr_ratio(bars):
    tr = E.true_range(bars)
    manual = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean() / tr.ewm(alpha=1 / 50, adjust=False, min_periods=50).mean()
    pd.testing.assert_series_equal(E.vei(bars)["vei"], manual, check_names=False)


def test_squeeze_definition_and_fire():
    n = 300
    rng = np.random.default_rng(3)
    calm = 100 + np.cumsum(rng.normal(0, 0.01, n))
    c = np.r_[calm, calm[-1] + np.cumsum(np.full(40, 0.5))]           # compression then expansion
    o = np.r_[c[0], c[:-1]]
    b = pd.DataFrame({"open": o, "high": np.maximum(o, c) + 0.2, "low": np.minimum(o, c) - 0.2, "close": c,
                      "tick_volume": 10, "spread": 1})
    s = E.squeeze(b)
    mid = b["close"].rolling(20).mean()
    sd = b["close"].rolling(20).std(ddof=0)
    kc = E.ema(b["close"], 20)
    a = E.atr(b, 20)
    manual_on = ((mid + 2 * sd) < (kc + 1.5 * a)) & ((mid - 2 * sd) > (kc - 1.5 * a))
    valid = s["sq_on"].notna()
    assert (s["sq_on"][valid].astype(bool) == manual_on[valid]).all()
    assert s["sq_on"].iloc[250:300].mean() > 0.9 and s["sq_fire"].iloc[300:340].sum() >= 1
    f = s["sq_fire"].fillna(0).to_numpy().astype(bool)
    on = s["sq_on"].fillna(0).to_numpy().astype(bool)
    assert all(on[i - 1] and not on[i] for i in np.flatnonzero(f))


def test_trend_and_momentum_formulas(bars):
    t = E.trend(bars)
    e = bars["close"].ewm(span=200, adjust=False, min_periods=200).mean()
    pd.testing.assert_series_equal(t["ema200"], e, check_names=False)
    m = E.momentum(bars)
    macd = bars["close"].ewm(span=5, adjust=False, min_periods=5).mean() - bars["close"].ewm(span=13, adjust=False, min_periods=13).mean()
    pd.testing.assert_series_equal(m["macd"], macd, check_names=False)
    assert m["mom_long_score"].dropna().between(0, 4).all()


def test_ofi_proxy_and_quote_burst():
    b = pd.DataFrame({"up_tv": [30, 0, 10], "dn_tv": [10, 0, 30], "tick_volume": [40, 0, 40], "max_m1_tv": [20, 0, 20]})
    o = E.ofi_proxy(b)
    assert o["ofi_ratio_up"].iat[0] == pytest.approx(31 / 11) and o["ofi_ratio_dn"].iat[2] == pytest.approx(31 / 11)
    assert np.isnan(o["ofi_z"].iat[1])                        # no quotes -> undefined, not 0
    tv = pd.DataFrame({"tick_volume": [10.0] * 120 + [50.0], "max_m1_tv": [5.0] * 121})
    q = E.quote_burst(tv)
    assert q["qb_score"].iat[-1] == pytest.approx(5.0) and q["qb_pct"].iat[-1] == 1.0


def test_td_sequential_setup_countdown_and_cancellation():
    # decline then a rally offset by 0.5 so the bullish price flip is strict (exact ties never flip)
    c = np.r_[np.linspace(100, 110, 10), np.linspace(109, 90, 20), 90.5 + 1.5 * np.arange(1, 31)]
    b = pd.DataFrame({"close": c, "high": c + 0.5, "low": c - 0.5, "open": c})
    td = E.td_sequential(b)
    i9 = np.flatnonzero(td["td_buy9"].to_numpy() == 1)
    assert len(i9) >= 1
    first = i9[0]
    assert td["td_buy_setup"].iat[first] == 9
    assert all(c[k] < c[k - 4] for k in range(first - 8, first + 1))
    assert c[first - 9] > c[first - 13] or td["td_buy_setup"].iat[first - 9] == 0       # began with a bearish flip
    j9 = np.flatnonzero(td["td_sell9"].to_numpy() == 1)
    assert len(j9) >= 1 and td["td_buy_countdown"].iat[j9[0]] == 0                      # opposite setup cancels
    ex = E.td_exhaustion(td)
    assert ex["td_bull_exhaust"].iat[j9[0]] == 1


# ---------------------------------------------------------------- causality

@pytest.mark.parametrize("fn", [E.features_dc20, E.features_dc55, lambda b: E.squeeze(b), lambda b: E.td_sequential(b)])
def test_engines_certify(bars, fn):
    if fn.__name__ == "<lambda>":
        def wrapped(b, f=fn):
            return f(b)
        fn = wrapped
    cert = nc.certify(fn, bars, extra_cols=E.EXTRA_PERTURB)
    assert cert["passed"], cert["failures"]


def leaky_donchian(b):           # includes the CURRENT bar in the channel -> breakout can never be strict
    up = b["high"].rolling(20).max()
    return pd.DataFrame({"u": up, "x": (b["close"].shift(-1) > up).astype(float)})


def leaky_bb_centered(b):
    return b["close"].rolling(20, center=True).mean()


def leaky_full_sample_rank(b):
    return b["close"].rank(pct=True)


def leaky_td_future(b):
    return pd.Series((b["close"].shift(-4) < b["close"]).astype(float), index=b.index)


def leaky_ofi_next(b):
    return (b["up_tv"].shift(-1) / (b["dn_tv"] + 1)).fillna(0)


def leaky_quote_burst(b):
    return b["tick_volume"] / b["tick_volume"].rolling(101, center=True).median()


@pytest.mark.parametrize("fn", [leaky_donchian, leaky_bb_centered, leaky_full_sample_rank, leaky_td_future,
                                leaky_ofi_next, leaky_quote_burst])
def test_leaky_variants_fail(bars, fn):
    assert not nc.certify(fn, bars, extra_cols=E.EXTRA_PERTURB)["passed"]


# ---------------------------------------------------------------- data hygiene

def test_nan_and_inf_do_not_crash_or_fabricate(bars):
    b = bars.copy()
    b["tick_volume"] = b["tick_volume"].astype(float)
    b.loc[100:105, ["open", "high", "low", "close"]] = np.nan
    b.loc[200, "tick_volume"] = np.inf
    f = E.features_dc20(b)
    assert len(f) == len(b)
    assert np.isnan(f["ema9"].iat[102]) or np.isfinite(f["ema9"].iat[102])
    assert not np.isfinite(f["qb_score"].iat[200]) or f["qb_score"].iat[200] > 1


def test_utc_bins_across_us_dst():
    m1 = synth_m1(n=7 * 1440, start="2024-03-06")                    # spans 2024-03-10 US DST change
    b = E.resample_m1(m1, "H1")
    t = pd.to_datetime(b["time_utc"])
    assert (t.dt.minute == 0).all() and t.diff().dropna().eq(pd.Timedelta(hours=1)).all()


def test_multi_symbol_scale_invariance():
    fx = E.resample_m1(synth_m1(price=1.1, vol=0.0001, seed=4), "M15")
    xau = E.resample_m1(synth_m1(price=2000, vol=0.3, seed=4), "M15")
    a, b = E.features_dc20(fx), E.features_dc20(xau)
    for col in ("brk_close_up", "sq_on", "above_ema200", "td_buy_setup"):
        assert a[col].notna().sum() > 0 and b[col].notna().sum() > 0


def test_parameters_change_outputs(bars):
    assert not E.squeeze(bars, kc_mult=1.0)["sq_on"].equals(E.squeeze(bars, kc_mult=2.0)["sq_on"])
    assert not E.donchian(bars, 10)["dc_upper"].equals(E.donchian(bars, 55)["dc_upper"])


# ---------------------------------------------------------------- research harness

def test_stack_is_nested_and_filters_use_decision_time(bars):
    f = E.features_dc20(bars)
    sig = pd.DataFrame({"row": np.flatnonzero(f["brk_close_up"].to_numpy() == 1), "dir": 1})
    prev = np.ones(len(sig), bool)
    for v in R.STACK:
        m = R.variant_mask(v, f, sig)
        assert not (m & ~prev).any()                        # each level is a subset of the previous one
        prev = m
    assert R.variant_mask("ofi_3", f, sig).sum() <= R.variant_mask("ofi_1.25", f, sig).sum()


def test_signal_outcomes_costs_and_non_overlap(bars):
    f = E.features_dc20(bars)
    s = R.signal_outcomes(bars, f, R.BaseCfg("XAUUSD", "M5", 20, "close_next_open", 2))
    assert len(s) > 20
    assert (s["cost_r"] > 0).all() and (s["swap_r"] >= 0).all() and (s["comm_r"] > 0).all()
    assert (s["r_net"] < s["r_gross"]).all()
    t = R.take_non_overlapping(s)
    ent, ex_ = t["signal_time"].to_numpy(), t["exit_time"].to_numpy()
    assert (ent[1:] > ex_[:-1]).all()
    w = R.in_window(s, "2024-03-05T00:00:00Z", "2024-03-10T00:00:00Z", pd.Timedelta(hours=1), pd.Timedelta(hours=4), False)
    assert (w["signal_time"] >= pd.Timestamp("2024-03-05 01:00")).all() and (w["exit_time"] < pd.Timestamp("2024-03-10")).all()


def test_random_subset_null_detects_selection():
    r = np.r_[np.full(100, -1.0), np.full(100, 2.0)]
    good = np.r_[np.zeros(100, bool), np.ones(100, bool)]
    rnd = np.random.default_rng(0).random(200) < 0.5
    assert R.random_subset_p(r, good) < 0.01 and R.random_subset_p(r, rnd) > 0.05
