"""V2 builders: declared configurations, causality certificates (incl. deliberately leaky variants
that MUST fail), timezone/closed-bar/rollover conventions and calendar handling.
Synthetic data only; no market data is read and no strategy is evaluated."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import nexa_calendar
import nexa_causality as nc
import nexa_v2_features as nf
import protocols_phase3_v2 as pv


@pytest.fixture(scope="module")
def bars():
    return nf.synthetic_bars()


def test_signal_columns_are_exactly_the_declared_configurations(bars):
    p = {x["experiment"]: {**x["grid"], **x["sensitivity"]} for x in pv.build()}
    f1 = {c for c in nf.f1_features(bars) if c.startswith("sig_")}
    assert f1 == {f"sig_f1_z{nf._fmt(z)}_d{d}" for z in p["F1_MACRO_EVENT"]["z_star"] for d in p["F1_MACRO_EVENT"]["delta_min"]}
    f2 = {c for c in nf.f2_features(bars) if c.startswith("sig_")}
    g2 = p["F2_XAU_SESSION_BREAKOUT"]
    assert f2 == {f"sig_f2_b{nf._fmt(b)}_ae{h}" for b in g2["buffer_b"] for h in g2["asian_end_utc_hour"]}
    f3 = {c for c in nf.f3_features(bars) if c.startswith("sig_")}
    g3 = p["F3_FVG_RETRACEMENT"]
    assert f3 == {f"sig_f3_{tf}_m{nf._fmt(m)}" for tf in g3["timeframe"] for m in g3["min_size_atr"]}
    f5 = {c for c in nf.f5_features(bars) if c.startswith("sig_")}
    g5 = p["F5_ASIAN_MEAN_REVERSION"]
    declared5 = {f"sig_f5_z{nf._fmt(z)}_a{a}_s{s}" for z in g5["z_star"] for a in g5["anchor"]
                 for s in g5["session_start_utc_hour"]}
    assert declared5 <= f5 and f5 - declared5 == {c for c in f5 if c.endswith("_sLDN")}      # only the null session
    with pytest.raises(ValueError, match="BLOCKED"):
        nf.declared("F6_TICK_QUOTE_IMBALANCE")
    with pytest.raises(ValueError, match="BLOCKED"):
        nf.declared("F4_CROSS_FEED_LATENCY")


@pytest.mark.parametrize("name", sorted(nf.BUILDERS))
def test_every_builder_certifies(bars, name):
    fn, cols = nf.BUILDERS[name]
    cert = nc.certify(fn, bars, extra_cols=cols)
    assert cert["passed"], cert["failures"]
    assert set(cols) <= set(cert["perturbed"])


# ---- deliberately leaky variants: each must FAIL certification (future information)

def leaky_f1_future_release(b):          # release value visible 3 bars before it happens
    return nf.f1_features(b.assign(f1_score=b["f1_score"].shift(-3)))


def leaky_f2_future_highs(b):            # Asian range built with highs from 30 bars ahead
    return nf.f2_features(b.assign(high=b["high"].shift(-30).fillna(b["high"])))


def leaky_f3_early_htf(b):               # FVG visible one M1 bar before the HTF bar closes
    return nf.f3_features(b).shift(-1).fillna(0.0)


def leaky_f5_centred(b):                 # z computed with 5 bars of future
    return nf.f5_features(b).shift(-5).fillna(0.0)


def leaky_f5_future_spread(b):           # spread filter reading the next bar's spread
    return nf.f5_features(b.assign(spread=b["spread"].shift(-1).fillna(0.0)))


@pytest.mark.parametrize("fn,cols", [(leaky_f1_future_release, ("f1_score",)), (leaky_f2_future_highs, ()),
                                     (leaky_f3_early_htf, ()), (leaky_f5_centred, ()),
                                     (leaky_f5_future_spread, ("spread",))])
def test_leaky_variants_fail_certification(bars, fn, cols):
    assert not nc.certify(fn, bars, extra_cols=cols)["passed"]


# ---- conventions

def test_f1_release_value_enters_on_the_release_bar_and_signal_after_delta(bars):
    t = pd.to_datetime(bars["time_utc"])
    ev = pd.DataFrame({"time_utc": [t.iat[5000], t.iat[9000] + pd.Timedelta(seconds=30)], "score": [2.0, -2.0]})
    b, info = nf.attach_f1(bars.drop(columns=["f1_score"]), ev)
    assert info == {"clusters": 2, "attached": 1, "no_exact_bar": 1}               # non-exact bar is dropped
    assert b["f1_score"].iat[5000] == 2.0 and b["f1_score"].notna().sum() == 1
    f = nf.f1_features(b)
    for d in (1, 2, 5):
        s = 5000 + d - 1                                                          # close of that row = release + d min
        col = f"sig_f1_z0.5_d{d}"
        if f[col].iat[s] != 0:
            assert f[col].iat[s] == 1 and f[f"f1_sl_d{d}"].iat[s] < bars["close"].iat[s]
            assert (f[col].iloc[:s] == 0).all()


def test_f1_event_table_sign_map_clusters_and_isolation():
    base = {"importance": 3, "timestamp_exact": True, "f1_eligible": True, "prior_surprise_sd": 1.0}
    cal = pd.DataFrame([
        {**base, "time_utc": "2024-03-08 13:30:00+00:00", "currency": "USD", "event_code": "nonfarm-payrolls",
         "actual": 3.0, "forecast": 1.0},
        {**base, "time_utc": "2024-03-08 13:30:00+00:00", "currency": "USD", "event_code": "unemployment-rate",
         "actual": 4.0, "forecast": 3.0},
        {**base, "time_utc": "2024-03-12 12:30:00+00:00", "currency": "USD", "event_code": "consumer-price-index-mm",
         "actual": 1.0, "forecast": 0.0},
        {**base, "time_utc": "2024-03-12 12:45:00+00:00", "currency": "USD", "event_code": "retail-sales-mm",
         "actual": 1.0, "forecast": 0.0},                                           # 15 min later: CPI not isolated
        {**base, "time_utc": "2024-03-20 14:30:00+00:00", "currency": "USD", "event_code": "eia-crude-oil-stocks-change",
         "actual": 9.0, "forecast": 0.0},                                           # no conventional sign -> excluded
        {**base, "time_utc": "2024-03-21 09:00:00+00:00", "currency": "EUR", "event_code": "gdp-qq",
         "actual": 1.0, "forecast": 0.0},
    ])
    eu = nf.f1_event_table(cal, "EURUSD")
    # NFP(+2, c=+1) and unemployment(+1, c=-1) cluster: g=-1 for USD in EURUSD -> mean(-2, +1) = -0.5
    nfp = eu[eu["time_utc"] == pd.Timestamp("2024-03-08 13:30", tz="UTC")]
    assert len(nfp) == 1 and nfp["score"].iat[0] == pytest.approx(-0.5) and nfp["n_events"].iat[0] == 2
    assert pd.Timestamp("2024-03-12 12:30", tz="UTC") not in set(eu["time_utc"])
    assert pd.Timestamp("2024-03-20 14:30", tz="UTC") not in set(eu["time_utc"])
    assert eu[eu["time_utc"] == pd.Timestamp("2024-03-21 09:00", tz="UTC")]["score"].iat[0] == pytest.approx(1.0)
    xau = nf.f1_event_table(cal, "XAUUSD")
    assert pd.Timestamp("2024-03-21 09:00", tz="UTC") not in set(xau["time_utc"])       # EUR is not an XAUUSD currency
    jp = nf.f1_event_table(cal, "USDJPY")
    assert jp[jp["time_utc"] == pd.Timestamp("2024-03-08 13:30", tz="UTC")]["score"].iat[0] == pytest.approx(0.5)


def test_windows_are_utc_across_us_dst_and_rollover_uses_server_clock():
    t = pd.date_range("2024-03-08 00:00", "2024-03-13 00:00", freq="1min", tz="UTC", inclusive="left")
    import nexa_time
    srv = nexa_time.utc_to_server(pd.Series(t))
    b = pd.DataFrame({"time_utc": t, "time_server": srv.to_numpy()})
    mod = nf.minute_of_day(b)
    assert (mod == t.hour * 60 + t.minute).all()                                   # UTC, not server hours
    off = (srv.to_numpy() - t.tz_localize(None).to_numpy()) / np.timedelta64(1, "h")
    assert set(np.round(off, 6)) == {2.0, 3.0}                                     # DST switch is inside the sample


def test_f5_no_signal_in_rollover_window_and_next_bar_in_session(bars):
    f = nf.f5_features(bars)
    ent = pd.to_datetime(bars["time_server"]) + nf.BAR
    ent_mod = ent.dt.hour * 60 + ent.dt.minute
    roll = (ent_mod >= 23 * 60 + 55) | (ent_mod <= 65)
    mod = nf.minute_of_day(bars)
    for c in [c for c in f if c.startswith("sig_f5_") and not c.endswith("_sLDN")]:
        s = f[c].to_numpy() != 0
        assert not (s & roll.to_numpy()).any()
        assert not (s & (mod == 6 * 60 - 1)).any()                                  # last session minute: no entry


def test_f3_fvg_visible_exactly_when_the_htf_bar_closes():
    t = pd.date_range("2024-01-02 00:00", periods=5 * 40, freq="1min", tz="UTC")
    n = len(t)
    c = np.full(n, 100.0)
    rng = np.random.default_rng(1)
    c = c + np.cumsum(rng.normal(0, 0.01, n))
    o, h, lo = c.copy(), c + 0.02, c - 0.02
    k0 = 30 * 5                                                                     # HTF bars 30, 31, 32
    h[k0:k0 + 5] = 100.0
    lo[k0:k0 + 5] = 99.95
    o[k0 + 5:k0 + 10], c[k0 + 5:k0 + 10] = 100.1, 101.5                            # displacement bar 31
    h[k0 + 5:k0 + 10], lo[k0 + 5:k0 + 10] = 101.6, 100.05
    o[k0 + 10:k0 + 15] = c[k0 + 10:k0 + 15] = 101.5
    h[k0 + 10:k0 + 15], lo[k0 + 10:k0 + 15] = 101.7, 101.2                          # low 101.2 > high(30) = 100
    b = pd.DataFrame({"time_utc": t, "time_server": t.tz_localize(None), "open": o, "high": h, "low": lo,
                      "close": c, "spread": 1.0})
    f = nf.f3_features(b)
    rows = np.flatnonzero(f["f3_dir_M5"].to_numpy() == 1)
    assert k0 + 14 in rows                                                          # the M1 bar closing HTF bar 32
    assert f["f3_top_M5"].iat[k0 + 14] == pytest.approx(101.2) and f["f3_bot_M5"].iat[k0 + 14] == pytest.approx(100.0)
    assert (f["f3_dir_M5"].iloc[k0:k0 + 14] == 0).all()


def test_calendar_prior_baselines_certify_and_full_sample_variant_fails():
    tab = nf.synthetic_calendar()
    ok = nc.certify_events(nf.calendar_prior_baselines, tab, "time_utc", nf.CAL_PERTURB_COLS, nf.CAL_CHECK_COLS)
    assert ok["passed"], ok["failures"]
    bad = nc.certify_events(full_sample_sd, tab, "time_utc", nf.CAL_PERTURB_COLS, nf.CAL_CHECK_COLS)
    assert not bad["passed"]


def full_sample_sd(tab):                 # the V1-style full-sample statistic: uses later releases
    x = nexa_calendar.prior_only_baselines(tab)[list(nf.CAL_CHECK_COLS)].copy()
    x["prior_surprise_sd"] = (tab["actual"] - tab["forecast"]).groupby(tab["event_id"]).transform("std")
    return x


def test_synthetic_data_is_deterministic():
    a, b = nf.synthetic_bars(days=10), nf.synthetic_bars(days=10)
    pd.testing.assert_frame_equal(a, b)
    pd.testing.assert_frame_equal(nf.synthetic_calendar(), nf.synthetic_calendar())
