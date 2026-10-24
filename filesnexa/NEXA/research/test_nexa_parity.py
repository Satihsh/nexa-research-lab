"""
test_nexa_parity.py -- Stage 3 tests.

All fixtures are synthetic. No MT5 terminal, no network, no recorded journal.

Two kinds of test appear here and the distinction matters:

  * ORACLE-BEHAVIOUR tests feed the oracle a dataset whose f00..f47 were
    produced BY the reconstruction itself, then perturb one value. These verify
    that the comparison machinery detects what it should. They do not and cannot
    verify that the reconstruction agrees with MQL5.

  * CONTRACT tests verify ordering, exemption, fail-closed behaviour and
    causality independently of any market data.

Real agreement between Python and MQL5 is only established by running this
oracle against a genuine Strategy Tester export. That is stated plainly in
README_PARITY.md rather than implied by a green test suite.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nexa_parity import (
    EXEMPT_INDICES,
    FEATURE_COLUMNS,
    FEATURE_COUNT,
    FEATURE_SPECS,
    BreakoutMemory,
    FeatureKind,
    LiquidityMachine,
    MarketData,
    ParityConfig,
    ParityGateError,
    ParityStatus,
    assert_parity_or_halt,
    detect_fvg,
    reconstruct_features,
    run_parity,
    sole_basis_guard,
    swing_trend,
    verify_feature_order,
    wilder_atr,
    within_tolerance,
)

MQL5_SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "NEXA_Intelligence.mqh")


# ---------------------------------------------------------------------------
# synthetic market builders
# ---------------------------------------------------------------------------

def _bars(prices, start="2026-09-14 00:00:00", freq="1min", spread=0.0002, subs=8):
    """
    Build an OHLC frame by SUB-SAMPLING the price path within each bar.

    Naive construction (high = max(open, close) + constant) produces TIED highs
    on consecutive bars at every turning point, and the strict swing definition
    rejects ties -- `highs[idx +/- i] >= h` fails -- so such a series contains no
    swing points at all and every trend reads UNKNOWN. That is correct behaviour
    of the definition (and of the MQL5 implementation, which uses the same >=),
    but it makes for a fixture that tests nothing.

    Sampling each bar from its own sub-path is how real bars form and gives
    each extreme a distinct value.
    """
    prices = np.asarray(prices, dtype="float64")
    n = len(prices)
    t = pd.date_range(start, periods=n, freq=freq)
    padded = np.concatenate([[prices[0]], prices])
    o = np.empty(n); h = np.empty(n); low_a = np.empty(n); c = np.empty(n)
    for i in range(n):
        sub = np.linspace(padded[i], padded[i + 1], subs)
        # symmetric intrabar excursion: up in the first half, down in the second,
        # so BOTH the high and the low come from an interior sub-sample. A
        # one-sided wobble leaves every low tied to a bar endpoint and produces
        # swing highs with no swing lows at all.
        wob = spread * np.sin(np.linspace(0, 2 * np.pi, subs)) * (1.0 + 0.1 * ((i % 5) - 2))
        path = sub + wob
        o[i] = path[0]; c[i] = path[-1]
        h[i] = path.max() + spread * 0.25
        low_a[i] = path.min() - spread * 0.25
    return pd.DataFrame({"time": t, "open": o, "high": h, "low": low_a, "close": c})


def _trend_path(n=400, start=1.10, step=0.00010):
    """
    Uptrend WITH PULLBACKS.

    A perfectly monotonic ramp contains no swing points at all: the strict
    definition requires a bar's neighbours to be lower on BOTH sides, which a
    straight line never satisfies. Such a path yields trendState=UNKNOWN, which
    is correct behaviour and a useless fixture. Real trends retrace, so the
    fixture retraces.
    """
    base = start + np.arange(n) * step
    pullback = 20.0 * step * np.sin(np.linspace(0, 14 * np.pi, n))
    return base + pullback


def _range_path(n=400, start=1.10, amp=0.0008):
    return start + amp * np.sin(np.linspace(0, 12 * np.pi, n))


def _vol_transition_path(n=400, start=1.10):
    quiet = start + 0.00002 * np.sin(np.linspace(0, 20 * np.pi, n // 2))
    loud = quiet[-1] + 0.0004 * np.sin(np.linspace(0, 8 * np.pi, n - n // 2))
    return np.concatenate([quiet, loud])


def _sweep_path(n=300, start=1.10, level=1.1050):
    """Rise to just above `level`, reject, then fall away: a liquidity grab."""
    up = np.linspace(start, level + 0.0004, n // 2)
    down = np.linspace(level + 0.0004, level - 0.0020, n - n // 2)
    return np.concatenate([up, down])


def _market(path_fn=_trend_path, n=400, point=1e-5) -> MarketData:
    m1 = _bars(path_fn(n))
    m5 = _bars(path_fn(max(n // 5, 60)), freq="5min")
    m15 = _bars(path_fn(max(n // 15, 60)), freq="15min")
    h1 = _bars(path_fn(max(n // 60, 60)), freq="1h")
    d1 = _bars(path_fn(30), freq="1D", spread=0.0030)
    return MarketData(bars={"M1": m1, "M5": m5, "M15": m15, "H1": h1, "D1": d1},
                      point=point)


def _canonical_from_reconstruction(data: MarketData, decision_times, cfg=None,
                                   symbol="EURUSD", tf="M1"):
    """
    Build a Stage-2-shaped frame whose features ARE the reconstruction.

    This exists only to exercise the comparison machinery. It deliberately does
    NOT prove Python matches MQL5 -- see the module docstring.
    """
    cfg = cfg or ParityConfig()
    machine = LiquidityMachine(cfg)
    breakout = BreakoutMemory(cfg.breakout_fail_window)
    prev_trend = None
    rows = []
    for i, ts in enumerate(decision_times):
        rec = reconstruct_features(pd.Timestamp(ts), data, cfg,
                                   quote=(1.10000, 1.10012), machine=machine,
                                   breakout=breakout, prev_trend_state=prev_trend)
        if not rec.causal_ok:
            continue
        if 20 in rec.values:
            prev_trend = int(rec.values[20])
        row = {
            "schema_version": "1.0", "row_id": f"{symbol}:{ts}:{i}",
            "symbol": symbol, "timeframe": tf, "event": "OPEN",
            "decision_ts": pd.Timestamp(ts), "decision_ts_effective": pd.Timestamp(ts),
            "bid": 1.10000, "ask": 1.10012,
        }
        for spec in FEATURE_SPECS:
            col = f"f{spec.index:02d}"
            row[col] = rec.values.get(spec.index, 0.0)
        rows.append(row)
    return pd.DataFrame(rows)


def _times(data: MarketData, count=12, tail_offset=30):
    m1 = data.bars["M1"]
    return list(m1["time"].iloc[-(count + tail_offset):-tail_offset])


# ---------------------------------------------------------------------------
# indicator reconstruction
# ---------------------------------------------------------------------------

def test_wilder_atr_warmup_is_nan_then_seeded():
    n = 60
    h = np.linspace(1.10, 1.11, n) + 0.0002
    low = np.linspace(1.10, 1.11, n) - 0.0002
    c = np.linspace(1.10, 1.11, n)
    atr = wilder_atr(h, low, c, 14)
    assert np.all(np.isnan(atr[:14])), "no ATR value may exist before warm-up completes"
    assert np.isfinite(atr[14]) and atr[14] > 0
    assert np.all(np.isfinite(atr[14:]))


def test_wilder_atr_insufficient_history_is_all_nan():
    atr = wilder_atr(np.ones(5), np.ones(5), np.ones(5), 14)
    assert np.all(np.isnan(atr))


def test_swing_trend_detects_uptrend():
    data = _market(_trend_path)
    w = data.window("M1", data.bars["M1"]["time"].iloc[-1], 200)
    assert swing_trend(w["high"], w["low"], 2) == 0        # UP


def test_detect_fvg_finds_a_real_gap():
    highs = np.array([1.1050, 1.1030, 1.1000])   # series order: 0 newest
    lows = np.array([1.1040, 1.1020, 1.0990])
    bull, bear = detect_fvg(highs, lows)
    assert bull is True and bear is False        # bar2.high < bar0.low


def test_detect_fvg_no_gap():
    highs = np.array([1.1010, 1.1015, 1.1020])
    lows = np.array([1.1000, 1.1005, 1.1010])
    bull, bear = detect_fvg(highs, lows)
    assert not bull and not bear


# ---------------------------------------------------------------------------
# causality
# ---------------------------------------------------------------------------

def test_reconstruction_never_sees_bars_after_decision_ts():
    """
    Causal leakage detection: truncating the series AT decision_ts must not
    change the reconstruction. If it did, future bars were being read.
    """
    data = _market(_trend_path, n=400)
    ts = data.bars["M1"]["time"].iloc[-50]
    full = reconstruct_features(ts, data, ParityConfig())

    truncated = MarketData(
        bars={tf: df[df["time"] <= ts].reset_index(drop=True)
              for tf, df in data.bars.items()},
        point=data.point)
    cut = reconstruct_features(ts, truncated, ParityConfig())

    assert full.causal_ok and cut.causal_ok
    for idx in sorted(set(full.values) & set(cut.values)):
        assert full.values[idx] == pytest.approx(cut.values[idx], rel=1e-12, abs=1e-15), \
            f"feature {idx} changed when future bars were removed -> leakage"


def test_asia_range_is_incremental_not_final():
    """The completed session range must not leak backwards onto an earlier bar."""
    from nexa_parity import _asia_range_as_of
    data = _market(_range_path, n=600)
    m1 = data.bars["M1"]
    early = m1["time"].iloc[100]
    late = m1["time"].iloc[500]
    h_early, l_early = _asia_range_as_of(data, early, 2)
    h_late, l_late = _asia_range_as_of(data, late, 2)
    if h_early > 0 and h_late > 0:
        assert h_early <= h_late + 1e-12
        assert l_early >= l_late - 1e-12


def test_insufficient_warmup_reports_not_causal():
    short = _bars(_trend_path(20))
    data = MarketData(bars={"M1": short, "D1": _bars(_trend_path(5), freq="1D")})
    rec = reconstruct_features(short["time"].iloc[-1], data, ParityConfig())
    assert rec.causal_ok is False
    assert "warm-up" in rec.reason or "history" in rec.reason


def test_epoch_decision_ts_is_skipped_not_reconstructed():
    data = _market(_trend_path)
    frame = _canonical_from_reconstruction(data, _times(data, 4))
    frame.loc[0, "decision_ts_effective"] = pd.Timestamp("1970-01-01")
    res = run_parity(frame, data, ParityConfig())
    assert res.stats["rows_skipped"] >= 1


# ---------------------------------------------------------------------------
# feature order / schema contract
# ---------------------------------------------------------------------------

def test_feature_specs_are_complete_and_ordered():
    assert len(FEATURE_SPECS) == FEATURE_COUNT
    assert [s.index for s in FEATURE_SPECS] == list(range(FEATURE_COUNT))


def test_feature_order_matches_mql5_packfeatures():
    """The schema here must mirror PackFeatures() exactly."""
    if not os.path.exists(MQL5_SOURCE):
        pytest.skip("MQL5 source not present next to the research tier")
    ok, problems = verify_feature_order(MQL5_SOURCE)
    assert ok, f"feature order drift: {problems}"


def test_wrong_feature_order_is_detected(tmp_path):
    fake = tmp_path / "fake.mqh"
    body = "\n".join(f"   out[k++] = (float)sig.{s.name};" for s in FEATURE_SPECS[:-1])
    body = body.replace("sig.structureBreakUp", "sig.somethingElse", 1)
    fake.write_text(body)
    ok, problems = verify_feature_order(str(fake))
    assert not ok and problems


def test_missing_mql5_source_is_not_silently_ok(tmp_path):
    ok, problems = verify_feature_order(str(tmp_path / "nope.mqh"))
    assert not ok and problems


def test_unsupported_schema_version_fails_closed():
    data = _market(_trend_path)
    frame = _canonical_from_reconstruction(data, _times(data, 3))
    frame["schema_version"] = "2.0"
    res = run_parity(frame, data, ParityConfig())
    assert res.status is ParityStatus.FAIL
    assert not res.passed


def test_missing_feature_column_fails_closed():
    data = _market(_trend_path)
    frame = _canonical_from_reconstruction(data, _times(data, 3)).drop(columns=["f21"])
    res = run_parity(frame, data, ParityConfig())
    assert res.status is ParityStatus.FAIL
    assert any("absent" in n for n in res.notes)


# ---------------------------------------------------------------------------
# tolerance
# ---------------------------------------------------------------------------

def test_tolerance_relative():
    ok, _abs_d, rel_d = within_tolerance(1.0, 1.0 + 5e-7, 1e-6, 1e-9)
    assert ok and rel_d < 1e-6


def test_tolerance_relative_breach():
    ok, _abs_d, rel_d = within_tolerance(1.0, 1.0 + 5e-5, 1e-6, 1e-9)
    assert not ok and rel_d > 1e-6


def test_tolerance_absolute_carries_near_zero():
    """Near zero the relative test is meaningless; absolute must carry it."""
    ok, _abs_d, _rel_d = within_tolerance(0.0, 5e-10, 1e-6, 1e-9)
    assert ok, "values a fraction of a pip apart near zero must not be a mismatch"


def test_tolerance_near_zero_breach_still_caught():
    ok, _, _ = within_tolerance(0.0, 1e-6, 1e-6, 1e-9)
    assert not ok


def test_nonfinite_never_counts_as_a_match():
    ok, _, _ = within_tolerance(float("nan"), 1.0, 1e-6, 1e-9)
    assert not ok
    ok2, _, _ = within_tolerance(float("inf"), float("inf"), 1e-6, 1e-9)
    assert not ok2


# ---------------------------------------------------------------------------
# mismatch detection (oracle behaviour)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path_fn,label", [
    (_trend_path, "trend"),
    (_range_path, "range"),
    (_vol_transition_path, "volatility transition"),
    (_sweep_path, "liquidity sweep/reclaim"),
])
def test_self_consistent_dataset_passes(path_fn, label):
    data = _market(path_fn, n=400)
    frame = _canonical_from_reconstruction(data, _times(data, 10))
    if not len(frame):
        pytest.skip(f"no causally reconstructable row for {label}")
    res = run_parity(frame, data, ParityConfig())
    assert not res.mismatches, f"{label}: {res.report()}"


def test_perturbed_continuous_feature_is_caught():
    data = _market(_trend_path)
    frame = _canonical_from_reconstruction(data, _times(data, 6))
    frame.loc[frame.index[0], "f10"] = float(frame.loc[frame.index[0], "f10"]) + 0.01
    res = run_parity(frame, data, ParityConfig())
    assert res.status is ParityStatus.FAIL
    assert any(m.feature_name == "displacementATR" for m in res.mismatches)


def test_perturbed_categorical_feature_is_caught():
    data = _market(_trend_path)
    frame = _canonical_from_reconstruction(data, _times(data, 6))
    frame.loc[frame.index[0], "f21"] = 0.0 if frame.loc[frame.index[0], "f21"] != 0 else 2.0
    res = run_parity(frame, data, ParityConfig())
    assert res.status is ParityStatus.FAIL
    assert any(m.feature_name == "volState" for m in res.mismatches)


def test_categorical_requires_exact_equality():
    """A sub-tolerance drift is fine for a float, never for an enum."""
    data = _market(_trend_path)
    frame = _canonical_from_reconstruction(data, _times(data, 5))
    idx = frame.index[0]
    frame.loc[idx, "f20"] = float(frame.loc[idx, "f20"]) + 1.0
    res = run_parity(frame, data, ParityConfig())
    assert any(m.feature_name == "trendState" and m.tolerance == "exact"
               for m in res.mismatches)


def test_mismatch_record_carries_full_audit_fields():
    data = _market(_trend_path)
    frame = _canonical_from_reconstruction(data, _times(data, 5))
    frame.loc[frame.index[0], "f10"] = 99.0
    res = run_parity(frame, data, ParityConfig())
    m = res.mismatches[0]
    for attr in ("row_id", "symbol", "timeframe", "decision_ts", "feature_index",
                 "feature_name", "mql5_value", "python_value", "abs_diff",
                 "rel_diff", "tolerance", "status"):
        assert hasattr(m, attr)
    assert m.symbol == "EURUSD" and m.timeframe == "M1"
    df = res.mismatch_frame()
    assert len(df) == len(res.mismatches)


# ---------------------------------------------------------------------------
# parity-exempt handling
# ---------------------------------------------------------------------------

def test_exempt_features_are_declared():
    names = {s.name for s in FEATURE_SPECS if s.kind is FeatureKind.EXEMPT}
    assert {"obiProxy", "cvdProxy", "liqOrigin", "newsRiskActive"} <= names
    # S13 (2026-10-03): f29 is compared when the basket bars are supplied, exempt only without them
    from nexa_parity import BASKET_INDICES
    assert "usdCompositeDirection" not in names and BASKET_INDICES == (29,)


def test_exempt_features_are_never_reported_as_passing():
    data = _market(_trend_path)
    frame = _canonical_from_reconstruction(data, _times(data, 6))
    frame["f30"] = 123.456        # nonsense OBI: must not be compared
    frame["f31"] = -987.0
    res = run_parity(frame, data, ParityConfig())
    assert res.per_feature["obiProxy"]["status"] == ParityStatus.EXEMPT.value
    assert res.per_feature["cvdProxy"]["status"] == ParityStatus.EXEMPT.value
    assert not any(m.feature_index in EXEMPT_INDICES for m in res.mismatches)


def test_exempt_features_are_not_silently_counted_as_compared():
    data = _market(_trend_path)
    frame = _canonical_from_reconstruction(data, _times(data, 6))
    res = run_parity(frame, data, ParityConfig())
    from nexa_parity import BASKET_INDICES
    assert res.stats["features_exempt"] == len(EXEMPT_INDICES) + len(BASKET_INDICES)     # no basket bars here
    assert res.stats["features_compared"] <= FEATURE_COUNT - len(EXEMPT_INDICES) - len(BASKET_INDICES)
    assert "usdCompositeDirection" in res.stats["exempt_names"]


def test_sole_basis_guard_rejects_exempt_only_feature_set():
    with pytest.raises(ParityGateError, match="sole basis"):
        sole_basis_guard(EXEMPT_INDICES)


def test_sole_basis_guard_allows_mixed_feature_set():
    sole_basis_guard(list(EXEMPT_INDICES) + [10, 20])     # must not raise


# ---------------------------------------------------------------------------
# fail-closed gate
# ---------------------------------------------------------------------------

def test_assert_parity_raises_on_fail():
    data = _market(_trend_path)
    frame = _canonical_from_reconstruction(data, _times(data, 5))
    frame.loc[frame.index[0], "f10"] = 42.0
    res = run_parity(frame, data, ParityConfig())
    with pytest.raises(ParityGateError, match="PARITY FAILED"):
        assert_parity_or_halt(res)


def test_assert_parity_silent_on_pass():
    data = _market(_trend_path)
    frame = _canonical_from_reconstruction(data, _times(data, 8))
    res = run_parity(frame, data, ParityConfig())
    if res.status is ParityStatus.PASS:
        assert_parity_or_halt(res)     # must not raise


def test_empty_dataset_is_fail_not_pass():
    """Zero comparisons is an unestablished oracle, never a clean bill."""
    data = _market(_trend_path)
    empty = pd.DataFrame(columns=["schema_version", "row_id", "symbol", "timeframe",
                                  "event", "decision_ts", "decision_ts_effective",
                                  "bid", "ask"] + FEATURE_COLUMNS)
    res = run_parity(empty, data, ParityConfig())
    assert res.status is ParityStatus.FAIL
    with pytest.raises(ParityGateError):
        assert_parity_or_halt(res)


def test_unreconstructable_feature_is_not_a_pass():
    data = _market(_trend_path)
    frame = _canonical_from_reconstruction(data, _times(data, 5))
    res = run_parity(frame, data, ParityConfig())
    for name, stat in res.per_feature.items():
        if name in res.stats["exempt_names"]:
            assert stat["status"] == ParityStatus.EXEMPT.value and stat["compared"] == 0
        elif stat["kind"] != FeatureKind.EXEMPT.value and stat["compared"] == 0:
            assert stat["status"] == ParityStatus.NOT_RECONSTRUCTED.value


# ---------------------------------------------------------------------------
# determinism
# ---------------------------------------------------------------------------

def test_parity_run_is_deterministic():
    data = _market(_trend_path)
    frame = _canonical_from_reconstruction(data, _times(data, 8))
    a = run_parity(frame, data, ParityConfig())
    b = run_parity(frame, data, ParityConfig())
    assert a.status == b.status
    assert len(a.mismatches) == len(b.mismatches)
    assert a.stats["rows_compared"] == b.stats["rows_compared"]
    assert a.per_feature == b.per_feature


def test_reconstruction_repeats_identically():
    data = _market(_range_path)
    ts = data.bars["M1"]["time"].iloc[-40]
    r1 = reconstruct_features(ts, data, ParityConfig())
    r2 = reconstruct_features(ts, data, ParityConfig())
    assert r1.values == r2.values


# ---------------------------------------------------------------------------
# boundary conditions
# ---------------------------------------------------------------------------

def test_missing_d1_history_skips_liquidity_without_crashing():
    m1 = _bars(_trend_path(400))
    data = MarketData(bars={"M1": m1}, point=1e-5)
    rec = reconstruct_features(m1["time"].iloc[-1], data, ParityConfig())
    assert rec.causal_ok
    assert rec.values[32] == 0.0        # IDLE, not an invented event


def test_zero_atr_path_is_handled():
    flat = np.full(200, 1.10)
    m1 = _bars(flat, spread=0.0)
    data = MarketData(bars={"M1": m1, "D1": _bars(flat[:20], freq="1D", spread=0.0)})
    rec = reconstruct_features(m1["time"].iloc[-1], data, ParityConfig())
    assert rec.causal_ok is False       # zero ATR cannot normalise anything


def test_near_zero_continuous_value_does_not_false_positive():
    data = _market(_range_path)
    frame = _canonical_from_reconstruction(data, _times(data, 5))
    idx = frame.index[0]
    frame.loc[idx, "f34"] = 0.0
    frame.loc[idx, "f35"] = 1e-12       # far below abs_tol from 0
    res = run_parity(frame, data, ParityConfig())
    near_zero = [m for m in res.mismatches
                 if m.feature_name == "liqWickBodyRatio" and m.abs_diff < 1e-9]
    assert not near_zero


def test_liquidity_machine_reaches_confirmed_on_sweep_and_response():
    """State machine contract: grab then structural response -> CONFIRMED."""
    cfg = ParityConfig()
    mach = LiquidityMachine(cfg)
    level, atr = 1.1050, 0.0010
    # probe above the level and close back inside -> RECLAIMED
    mach.advance(0, level, atr, 1.1054, 1.1040, 1.1045, 1.1046,
                 False, False, False, False, False, False, 1e-5)
    assert mach.events[0].state in (1, 2)
    mach.advance(0, level, atr, 1.1048, 1.1035, 1.1046, 1.1036,
                 False, False, False, False, False, False, 1e-5)
    # bearish MSS after the reclaim -> CONFIRMED reversal, direction from response
    mach.advance(0, level, atr, 1.1040, 1.1020, 1.1038, 1.1022,
                 False, True, False, True, False, True, 1e-5)
    ev = mach.events[0]
    assert ev.state == 3 and ev.resolution == 1 and ev.response_direction == -1
    assert ev.setup == 1                      # PDH_REVERSAL


def test_breakout_memory_detects_two_stage_failure():
    """A false breakout is break-THEN-rejection; one bar cannot express it."""
    bm = BreakoutMemory(5)
    assert bm.classify(True, False, 1.1050, 1.1000, 1.1055) == 1    # TRUE
    assert bm.classify(False, False, 1.1050, 1.1000, 1.1045) == 2   # FALSE


def test_breakout_memory_expires_after_window():
    bm = BreakoutMemory(2)
    bm.classify(True, False, 1.1050, 1.1000, 1.1055)
    for _ in range(3):
        bm.classify(False, False, 1.1050, 1.1000, 1.1060)
    assert bm.direction == 0


# --- MT5 iATR is a SIMPLE average of true range (found on real Pepperstone DNA) ---

def test_mt5_iatr_is_simple_mean_of_true_range():
    from nexa_parity import mt5_iatr
    h = np.array([10.0, 12.0, 11.0, 13.0, 12.5])
    low = np.array([9.0, 10.0, 10.0, 11.0, 11.5])
    c = np.array([9.5, 11.0, 10.5, 12.0, 12.0])
    # TR: bar0 = h-l = 1; bar1 = max(2, |12-9.5|, |10-9.5|) = 2.5; bar2 = max(1, 0, 1) = 1;
    #     bar3 = max(2, 2.5, 0.5) = 2.5; bar4 = max(1, 0.5, 0.5) = 1
    atr = mt5_iatr(h, low, c, 3)
    assert np.isnan(atr[:2]).all()
    np.testing.assert_allclose(atr[2:], [(1 + 2.5 + 1) / 3, (2.5 + 1 + 2.5) / 3, (1 + 2.5 + 1) / 3])


def test_mt5_iatr_differs_from_wilder_and_reconstruction_uses_it():
    import inspect

    import nexa_parity
    from nexa_parity import mt5_iatr
    rng = np.random.default_rng(0)
    c = 1 + np.cumsum(rng.normal(0, 1e-4, 300))
    h, low = c + 2e-4, c - 2e-4
    assert not np.allclose(mt5_iatr(h, low, c, 14)[30:], wilder_atr(h, low, c, 14)[30:])
    src = inspect.getsource(nexa_parity)
    assert "atr_chron = mt5_iatr(" in src and "atr_chron = wilder_atr(" not in src


# --- HTF causality: a higher-timeframe bar is visible only once it has CLOSED ---

def _htf_bars(freq, start, n):
    t = pd.date_range(start, periods=n, freq=freq)
    v = np.arange(n, dtype=float) + 1
    return pd.DataFrame({"time": t, "open": v, "high": v + 0.5, "low": v - 0.5, "close": v})


def test_forming_m5_bar_is_not_visible_at_m1_decision():
    from nexa_parity import MarketData
    md = MarketData({"M1": _htf_bars("1min", "2025-06-02 09:00", 180), "M5": _htf_bars("5min", "2025-06-02 09:00", 36)})
    # decision on the 10:02 M1 bar (closed at 10:03): the 10:00 M5 bar closes at 10:05 -> NOT visible
    w = md.window("M5", pd.Timestamp("2025-06-02 10:02"), 3)
    assert pd.Timestamp(w["time"][0]) == pd.Timestamp("2025-06-02 09:55")
    # decision on the 10:04 M1 bar (closed at 10:05): the 10:00 M5 bar has just closed -> visible
    w = md.window("M5", pd.Timestamp("2025-06-02 10:04"), 3)
    assert pd.Timestamp(w["time"][0]) == pd.Timestamp("2025-06-02 10:00")


def test_m1_window_still_ends_at_the_decision_bar():
    from nexa_parity import MarketData
    md = MarketData({"M1": _htf_bars("1min", "2025-06-02 09:00", 180)})
    w = md.window("M1", pd.Timestamp("2025-06-02 10:02"), 2)
    assert pd.Timestamp(w["time"][0]) == pd.Timestamp("2025-06-02 10:02")


def test_forming_h1_bar_is_not_visible():
    from nexa_parity import MarketData
    md = MarketData({"H1": _htf_bars("1h", "2025-06-02 00:00", 24)})
    w = md.window("H1", pd.Timestamp("2025-06-02 10:30"), 2)
    assert pd.Timestamp(w["time"][0]) == pd.Timestamp("2025-06-02 09:00")


# --- volState mirrors MQL5 VolRegime(): newest `history` ATRs INCLUDING the current one ---

def test_vol_regime_uses_newest_values_including_current():
    from nexa_parity import VOL_HIGH, VOL_NORMAL, vol_regime
    # series order: [atr_now, older...]. Newest 3 = [2.0, 1.0, 1.0] -> avg 1.333, ratio 1.5 -> HIGH.
    series = np.array([2.0, 1.0, 1.0, 5.0, 5.0, 5.0])
    assert vol_regime(series, 2.0, 3) == VOL_HIGH
    # had it used the OLDEST values (5.0s) the ratio would be 0.4 -> LOW; had it excluded
    # the current ATR the newest 3 would be [1, 1, 5] -> ratio 0.857 -> NORMAL
    assert vol_regime(np.array([1.0, 1.0, 1.0]), 1.0, 3) == VOL_NORMAL


def test_vol_regime_skips_invalid_values_inside_span():
    from nexa_parity import VOL_NORMAL, vol_regime
    assert vol_regime(np.array([1.0, np.nan, 0.0, 1.0]), 1.0, 4) == VOL_NORMAL


# --- PDH/PDL: the D1 bar of the previous day, selected by date (B-PARITY-LIQ RC2) ---

def _d1(days):
    t = pd.to_datetime(days)
    return pd.DataFrame({"time": t, "open": 1.0, "high": [1.10 + 0.01 * i for i in range(len(t))],
                         "low": [1.00 - 0.01 * i for i in range(len(t))], "close": 1.05})


def test_prev_day_levels_when_d1_lacks_the_forming_day():
    from nexa_parity import MarketData
    # tester D1 exports end at the day BEFORE the window's last M1 day
    md = MarketData({"D1": _d1(["2026-09-22", "2026-09-23", "2026-09-24"])})
    h, lo, _, src = md.prev_day_levels(pd.Timestamp("2026-09-25 10:00"))
    assert src == pd.Timestamp("2026-09-24") and (h, lo) == (1.12, 0.98)


def test_prev_day_levels_unchanged_when_d1_has_the_forming_day():
    from nexa_parity import MarketData
    md = MarketData({"D1": _d1(["2026-09-23", "2026-09-24", "2026-09-25"])})
    assert md.prev_day_levels(pd.Timestamp("2026-09-25 10:00"))[3] == pd.Timestamp("2026-09-24")
    assert md.prev_day_levels(pd.Timestamp("2026-09-25 00:00"))[3] == pd.Timestamp("2026-09-24")
    # Monday: previous day is Friday (no weekend D1 bars)
    md = MarketData({"D1": _d1(["2026-09-17", "2026-09-18", "2026-09-21"])})
    assert md.prev_day_levels(pd.Timestamp("2026-09-21 03:00"))[3] == pd.Timestamp("2026-09-18")
    assert md.prev_day_levels(pd.Timestamp("2026-09-17 03:00")) is None


# --- Asia range: carried forward to the next GMT hour-0 bar, as MQL5 UpdateSessionLevels (RC1) ---

def _m1_hours(spec):
    """spec: [(server_time_start, n_bars, high, low)] -> contiguous M1 frames concatenated."""
    parts = []
    for start, n, h, lo in spec:
        t = pd.date_range(start, periods=n, freq="1min")
        parts.append(pd.DataFrame({"time": t, "open": lo, "high": h, "low": lo, "close": lo}))
    return pd.concat(parts, ignore_index=True)


def test_asia_range_carried_over_weekend_until_next_gmt_hour0():
    from nexa_parity import MarketData, _asia_range_as_of
    # Carry-over logic under a FIXED clock (us_dst=False): gmt_offset 2, GMT hour 0 = server 02:00. Friday Asia 1.30/1.20; London later 1.40/1.10;
    # Monday server 00:00-01:59 is GMT hour 22-23 of Sunday; Monday Asia starts 02:00 server.
    m1 = _m1_hours([("2026-09-11 02:00", 60, 1.30, 1.20), ("2026-09-11 03:00", 360, 1.25, 1.22),
                    ("2026-09-11 11:00", 60, 1.40, 1.10),
                    ("2026-09-14 00:00", 120, 1.50, 1.00), ("2026-09-14 02:00", 30, 1.27, 1.26)])
    md = MarketData({"M1": m1})
    assert _asia_range_as_of(md, pd.Timestamp("2026-09-11 12:00"), 2, False) == (1.30, 1.20)   # same day, after Asia
    assert _asia_range_as_of(md, pd.Timestamp("2026-09-14 01:30"), 2, False) == (1.30, 1.20)   # Monday, carried
    assert _asia_range_as_of(md, pd.Timestamp("2026-09-14 02:00"), 2, False) == (1.27, 1.26)   # restarts at GMT 0
    assert _asia_range_as_of(md, pd.Timestamp("2026-09-11 01:59"), 2, False) == (0.0, 0.0)     # no session seen yet


# --- decision clock = first tick of the next entry bar (B-PARITY-EDGE-1) ---

def test_htf_window_advances_across_a_tick_gap():
    from nexa_parity import MarketData
    m1 = pd.concat([_htf_bars("1min", "2026-08-31 23:00", 59),      # 23:00 .. 23:58, then the daily break
                    _htf_bars("1min", "2026-09-01 00:01", 30)], ignore_index=True)
    m5 = pd.concat([_htf_bars("5min", "2026-08-31 23:00", 12), _htf_bars("5min", "2026-09-01 00:00", 6)],
                   ignore_index=True)
    h1 = pd.concat([_htf_bars("1h", "2026-08-31 20:00", 4), _htf_bars("1h", "2026-09-01 00:00", 1)],
                   ignore_index=True)
    md = MarketData({"M1": m1, "M5": m5, "H1": h1})
    # the 23:58 bar is evaluated at the 00:01 tick: the 23:55 M5 and 23:00 H1 bars have closed
    assert pd.Timestamp(md.window("M5", pd.Timestamp("2026-08-31 23:58"), 2)["time"][0]) == pd.Timestamp("2026-08-31 23:55")
    assert pd.Timestamp(md.window("H1", pd.Timestamp("2026-08-31 23:58"), 2)["time"][0]) == pd.Timestamp("2026-08-31 23:00")
    # no gap: the 23:57 bar is evaluated at 23:58 -> 23:50 M5, 22:00 H1 (unchanged behaviour)
    assert pd.Timestamp(md.window("M5", pd.Timestamp("2026-08-31 23:57"), 2)["time"][0]) == pd.Timestamp("2026-08-31 23:50")
    assert pd.Timestamp(md.window("H1", pd.Timestamp("2026-08-31 23:57"), 2)["time"][0]) == pd.Timestamp("2026-08-31 22:00")
    # the entry-timeframe window still ends at the decision bar itself
    assert pd.Timestamp(md.window("M1", pd.Timestamp("2026-08-31 23:58"), 2)["time"][0]) == pd.Timestamp("2026-08-31 23:58")


# --- B-PARITY-TOL option A (2026-10-03): journal-quantisation tolerance + reviewed tie register ---

def test_continuous_contract_accepts_journal_quantisation_only():
    from nexa_parity import DEFAULT_JOURNAL_DECIMALS, journal_quantum
    assert ParityConfig().journal_decimals == DEFAULT_JOURNAL_DECIMALS == 6
    q = journal_quantum(1.2, 6)                                          # 5e-7 + 1.2 * 2**-23
    assert within_tolerance(1.2, 1.2 + 0.99 * q, 0.0, 0.0, 6)[0]
    assert not within_tolerance(1.2, 1.2 + 1.01 * q, 0.0, 0.0, 6)[0]
    assert not within_tolerance(1.2, 1.2 + 4e-7, 0.0, 1e-9, None)[0]    # None = bare rule, unchanged
    assert not within_tolerance(0.0, 1e-6, 1e-6, 1e-9, 6)[0]            # a full 6th-decimal step still fails


def test_sub_quantum_drift_passes_but_real_drift_fails():
    data = _market(_trend_path)
    frame = _canonical_from_reconstruction(data, _times(data, 6))
    idx = frame.index[0]
    frame.loc[idx, "f10"] = float(frame.loc[idx, "f10"]) + 4e-7        # 6-decimal journal rounding
    assert not [m for m in run_parity(frame, data, ParityConfig()).mismatches if m.feature_name == "displacementATR"]
    frame.loc[idx, "f10"] = float(frame.loc[idx, "f10"]) + 1e-5
    assert any(m.feature_name == "displacementATR" for m in run_parity(frame, data, ParityConfig()).mismatches)


def _one_categorical_flip():
    data = _market(_trend_path)
    frame = _canonical_from_reconstruction(data, _times(data, 6))
    idx = frame.index[0]
    py_v = float(frame.loc[idx, "f21"])
    frame.loc[idx, "f21"] = 0.0 if py_v != 0 else 2.0
    return data, frame, idx, py_v


def test_listed_tie_is_accepted_and_reported_not_hidden():
    from nexa_parity import AcceptedTie
    data, frame, idx, py_v = _one_categorical_flip()
    tie = AcceptedTie("EURUSD", str(frame.loc[idx, "decision_ts"]), "volState",
                      float(frame.loc[idx, "f21"]), py_v, "test tie")
    res = run_parity(frame, data, ParityConfig(accepted_ties=(tie,)))
    assert res.status is ParityStatus.PASS and not res.mismatches
    assert len(res.accepted) == 1 and res.accepted[0].status.startswith("ACCEPTED_TIE")
    assert res.stats["ties_accepted"] == 1 and "accepted ties      : 1" in res.report()


def test_tie_with_different_values_or_feature_still_fails():
    from nexa_parity import AcceptedTie
    data, frame, idx, py_v = _one_categorical_flip()
    ts = str(frame.loc[idx, "decision_ts"])
    wrong_value = AcceptedTie("EURUSD", ts, "volState", float(frame.loc[idx, "f21"]) + 1.0, py_v, "t")
    res = run_parity(frame, data, ParityConfig(accepted_ties=(wrong_value,)))
    assert res.status is ParityStatus.FAIL and any("does not match" in n for n in res.notes)
    other_feature = AcceptedTie("EURUSD", ts, "trendState", 0.0, 0.0, "t")
    res = run_parity(frame, data, ParityConfig(accepted_ties=(other_feature,)))
    assert res.status is ParityStatus.FAIL and any(m.feature_name == "volState" for m in res.mismatches)
    other_symbol = AcceptedTie("GBPUSD", ts, "volState", float(frame.loc[idx, "f21"]), py_v, "t")
    assert run_parity(frame, data, ParityConfig(accepted_ties=(other_symbol,))).status is ParityStatus.FAIL


def test_repository_tie_register_is_the_reviewed_window_b_set():
    from nexa_parity import load_accepted_ties
    ties = load_accepted_ties(os.path.join(os.path.dirname(os.path.abspath(__file__)), "parity_accepted_ties.json"))
    assert len(ties) == 47
    assert all(t.cause.startswith(("RC3:", "EDGE-2:")) for t in ties)
    assert {t.symbol for t in ties} == {"GBPUSD", "EURUSD"}
    assert sum(t.cause.startswith("RC3:") for t in ties) == 36
    assert {t.feature_name for t in ties if t.cause.startswith("EDGE-2:")} <= {
        "displacementUp", "displacementDown", "isMSS_up", "isMSS_down"}


# --- D-TZ (2026-10-03): DST-aware server clock, mirror of MQL5 NexaServerGMTOffsetHours ---

def test_server_offset_mirror_equals_nexa_time_every_hour():
    import nexa_time
    from nexa_parity import server_gmt_offset_hours
    t = pd.Series(pd.date_range("2005-01-01", "2031-01-01", freq="1h", inclusive="left"))
    off = server_gmt_offset_hours(t, 2, True)
    ok = nexa_time.classify_server_times(t).eq("OK").to_numpy()
    assert (off[ok] == nexa_time.utc_offset_hours(t[ok]).to_numpy()).all()
    assert set(off[~ok]) == {3} and (~ok).sum() == 2 * 26          # switch hours: [start, end) -> DST
    assert set(server_gmt_offset_hours(t, 2, False)) == {2}


def test_dst_boundaries_2026():
    from nexa_parity import server_gmt_offset_hours
    # US DST 2026: 2026-03-08 02:00 NY (server 09:00) -> 2026-11-01 02:00 NY (server 09:00)
    ts = ["2026-03-08 08:59", "2026-03-08 09:00", "2026-11-01 08:59", "2026-11-01 09:00", "2026-07-01 12:00",
          "2026-01-15 12:00"]
    assert list(server_gmt_offset_hours(ts, 2, True)) == [2, 3, 3, 2, 3, 2]


def test_asia_window_follows_the_dst_clock():
    from nexa_parity import MarketData, _asia_range_as_of
    # 2026-07-01 (US DST): GMT 00:00 = server 03:00, so the Asia range restarts at 03:00, not 02:00
    m1 = _m1_hours([("2026-06-30 03:00", 60, 1.30, 1.20), ("2026-07-01 02:00", 60, 1.50, 1.00),
                    ("2026-07-01 03:00", 30, 1.27, 1.26)])
    md = MarketData({"M1": m1})
    assert _asia_range_as_of(md, pd.Timestamp("2026-07-01 02:59"), 2, True) == (1.30, 1.20)   # carried
    assert _asia_range_as_of(md, pd.Timestamp("2026-07-01 03:10"), 2, True) == (1.27, 1.26)   # restart
    assert _asia_range_as_of(md, pd.Timestamp("2026-07-01 02:30"), 2, False) == (1.50, 1.00)  # old fixed clock


def test_compiled_mql5_clock_equals_python_mirror_every_hour_2000_2030():
    import hashlib

    from nexa_parity import server_gmt_offset_hours
    run = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tester_runs", "clock_dtz_20261003")
    if not os.path.exists(os.path.join(run, "mql5_results.csv.gz")):
        pytest.skip("MQL5 clock evidence not present")
    with open(os.path.join(run, "PROVENANCE.txt")) as fh:
        prov = dict(line.strip().split("=", 1) for line in fh if "=" in line)
    common = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "NEXA_Common.mqh")
    with open(common, "rb") as fh:
        assert prov["common_sha256"] == hashlib.sha256(fh.read()).hexdigest(), "stale evidence: rerun NEXA_ClockTest"
    m = pd.read_csv(os.path.join(run, "mql5_results.csv.gz"))
    t = pd.to_datetime(m["server_time"], format="%Y.%m.%d %H:%M:%S")
    assert len(m) == 271752
    assert (server_gmt_offset_hours(t, 2, True) == m["offset_hours"].to_numpy()).all()
    assert ((t - pd.to_timedelta(m["offset_hours"], unit="h")).dt.hour.to_numpy() == m["gmt_hour"].to_numpy()).all()


# --- S13 (2026-10-03): usdCompositeDirection read by TIME, mirror of MQL5 UsdCompositeDirection ---

def _basket(series):
    """series: {sym: [(minute_offset, close), ...]} from 2026-09-14 10:00."""
    t0 = pd.Timestamp("2026-09-14 10:00")
    return {s: pd.DataFrame({"time": [t0 + pd.Timedelta(minutes=m) for m, _ in v], "close": [c for _, c in v]})
            for s, v in series.items()}


def test_usd_composite_votes_and_jpy_inversion():
    from nexa_parity import usd_composite_direction
    t = pd.Timestamp("2026-09-14 10:20")
    usd_up = {"EURUSD": [(10, 1.10), (20, 1.09)], "GBPUSD": [(10, 1.30), (20, 1.29)],
              "USDJPY": [(10, 150.0), (20, 151.0)], "XAUUSD": [(10, 2000.0), (20, 1990.0)]}
    assert usd_composite_direction(_basket(usd_up), t) == 1
    usd_dn = {"EURUSD": [(10, 1.10), (20, 1.11)], "GBPUSD": [(10, 1.30), (20, 1.31)],
              "USDJPY": [(10, 150.0), (20, 149.0)], "XAUUSD": [(10, 2000.0), (20, 2010.0)]}
    assert usd_composite_direction(_basket(usd_dn), t) == -1
    mixed = dict(usd_up, EURUSD=[(10, 1.10), (20, 1.11)], GBPUSD=[(10, 1.30), (20, 1.31)])
    assert usd_composite_direction(_basket(mixed), t) == 0


def test_usd_composite_is_time_aligned_not_positional():
    from nexa_parity import usd_composite_direction
    t = pd.Timestamp("2026-09-14 10:20")
    # XAUUSD has a gap: positionally its "11 bars ago" would reach far back; by time it reads 10:10 / 10:20
    b = {"EURUSD": [(10, 1.10), (20, 1.09)], "GBPUSD": [(10, 1.30), (20, 1.29)],
         "USDJPY": [(10, 150.0), (20, 151.0)], "XAUUSD": [(-60, 1900.0), (10, 2000.0), (20, 1990.0)]}
    assert usd_composite_direction(_basket(b), t) == 1
    # a symbol whose latest bar is > 5 bars stale is not counted (3 left, all agree -> still +1)
    stale = dict(b, XAUUSD=[(0, 2000.0), (12, 2100.0)])
    assert usd_composite_direction(_basket(stale), t) == 1
    # fewer than two countable symbols -> 0
    only_one = {"EURUSD": [(10, 1.10), (20, 1.09)]}
    assert usd_composite_direction(_basket(only_one), t) == 0
    # a bar AFTER the decision bar is never read (causality)
    future = dict(b, EURUSD=[(10, 1.10), (20, 1.09), (21, 2.00)])
    assert usd_composite_direction(_basket(future), t) == 1


def test_f29_is_compared_when_basket_bars_are_supplied():
    data = _market(_trend_path)
    times = _times(data, 6)
    m1 = data.bars["M1"]
    data.basket = {s: m1[["time", "close"]].assign(close=m1["close"] * k) for s, k in
                   (("EURUSD", 1.0), ("GBPUSD", 1.2), ("USDJPY", 140.0), ("XAUUSD", 2000.0))}
    frame = _canonical_from_reconstruction(data, times)
    res = run_parity(frame, data, ParityConfig())
    assert "usdCompositeDirection" not in res.stats["exempt_names"]
    assert res.per_feature["usdCompositeDirection"]["compared"] == len(frame)
    frame.loc[frame.index[0], "f29"] = 9.0
    assert any(m.feature_name == "usdCompositeDirection" for m in run_parity(frame, data, ParityConfig()).mismatches)
