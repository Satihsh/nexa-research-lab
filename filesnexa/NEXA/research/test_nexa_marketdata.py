"""
test_nexa_marketdata.py -- Stage 5 external data pipeline tests.

IMPORTANT DISTINCTION
---------------------
These tests build synthetic BYTES and synthetic CSV TEXT to exercise decoders,
converters and the quality gate. That is testing a parser against a known
format.

They do NOT create synthetic market data for research use. No frame produced
here ever reaches a model. The pipeline is being verified; the dataset it will
one day carry does not exist yet and is not invented.

No network access is required or attempted.
"""

from __future__ import annotations

import lzma
import os
import struct
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nexa_marketdata import (
    CANONICAL_BAR_COLUMNS,
    CANONICAL_TICK_COLUMNS,
    HISTDATA_FIXED_UTC_OFFSET_HOURS,
    PIPET_SCALE,
    MarketDataError,
    QualityStatus,
    assert_quality_or_halt,
    build_timeframe_set,
    cross_source_compare,
    decode_bi5,
    dukascopy_url,
    read_histdata_m1,
    resample_bars,
    ticks_to_bars,
    validate_bars,
    validate_ticks,
    write_dataset,
    write_manifest,
)

H0 = pd.Timestamp("2024-01-02 10:00:00", tz="UTC")


def _bi5(records, compress=True) -> bytes:
    """records: list of (ms_offset, raw_ask_int, raw_bid_int, ask_vol, bid_vol)."""
    payload = b"".join(struct.pack(">IIIff", *r) for r in records)
    return lzma.compress(payload, format=lzma.FORMAT_ALONE) if compress else payload


def _ticks(n=600, start=H0, symbol="EURUSD", bid0=1.1000, step=1e-5):
    ts = pd.date_range(start, periods=n, freq="1s", tz="UTC")
    bid = bid0 + np.sin(np.linspace(0, 8 * np.pi, n)) * 20 * step
    ask = bid + 2 * step
    return pd.DataFrame({
        "timestamp": ts, "symbol": symbol, "bid": bid, "ask": ask,
        "mid": (bid + ask) / 2, "spread": ask - bid,
        "bid_volume": 1.0, "ask_volume": 1.0,
        "source": "dukascopy", "source_file": "test", "timezone": "UTC",
    })[list(CANONICAL_TICK_COLUMNS)]


def _bars(n=500, tf="M1", symbol="EURUSD", start="2024-01-02 00:00:00",
          source="dukascopy", freq=None):
    freq = freq or "1min"
    t = pd.date_range(start, periods=n, freq=freq, tz="UTC")
    close = 1.1000 + np.sin(np.linspace(0, 10 * np.pi, n)) * 0.0020
    openp = np.concatenate([[close[0]], close[:-1]])
    return pd.DataFrame({
        "time": t, "symbol": symbol, "timeframe": tf,
        "open": openp, "high": np.maximum(openp, close) + 0.0001,
        "low": np.minimum(openp, close) - 0.0001, "close": close,
        "tick_volume": 10, "real_volume": np.nan,
        "source": source, "source_file": "test", "timezone": "UTC",
        "quality_status": "OK",
    })[list(CANONICAL_BAR_COLUMNS)]


def codes(res) -> set:
    return {f.code for f in res.findings}


# ---------------------------------------------------------------------------
# provider contract: Dukascopy
# ---------------------------------------------------------------------------

def test_dukascopy_months_are_zero_indexed():
    """January must be '00'. An off-by-one here fetches the wrong month."""
    url = dukascopy_url("EURUSD", pd.Timestamp("2024-01-02 10:00", tz="UTC"))
    assert "/2024/00/02/10h_ticks.bi5" in url


def test_dukascopy_december_is_eleven():
    url = dukascopy_url("XAUUSD", pd.Timestamp("2024-12-31 23:00", tz="UTC"))
    assert "/2024/11/31/23h_ticks.bi5" in url


def test_decode_bi5_scales_five_decimal_pair():
    raw = _bi5([(0, 110020, 110000, 1.5, 2.5)])
    out = decode_bi5(raw, "EURUSD", H0, "t.bi5")
    assert out["bid"].iloc[0] == pytest.approx(1.10000, abs=1e-9)
    assert out["ask"].iloc[0] == pytest.approx(1.10020, abs=1e-9)
    assert out["spread"].iloc[0] == pytest.approx(0.0002, abs=1e-9)


def test_decode_bi5_scales_three_decimal_metal():
    """XAUUSD uses 1e-3, not 1e-5. Wrong scale gives plausible false prices."""
    raw = _bi5([(0, 2050500, 2050300, 1.0, 1.0)])
    out = decode_bi5(raw, "XAUUSD", H0, "t.bi5")
    assert out["bid"].iloc[0] == pytest.approx(2050.300, abs=1e-6)
    assert out["ask"].iloc[0] == pytest.approx(2050.500, abs=1e-6)


def test_decode_bi5_applies_millisecond_offsets():
    raw = _bi5([(0, 110020, 110000, 1, 1), (1500, 110021, 110001, 1, 1)])
    out = decode_bi5(raw, "EURUSD", H0, "t.bi5")
    assert out["timestamp"].iloc[0] == H0
    assert out["timestamp"].iloc[1] == H0 + pd.Timedelta(milliseconds=1500)


def test_decode_bi5_empty_hour_is_not_an_error():
    """A market-closed hour genuinely has no ticks."""
    assert len(decode_bi5(b"", "EURUSD", H0)) == 0


def test_decode_bi5_truncated_file_raises():
    payload = struct.pack(">IIIff", 0, 110020, 110000, 1, 1)[:-3]
    raw = lzma.compress(payload, format=lzma.FORMAT_ALONE)
    with pytest.raises(MarketDataError, match="truncated or corrupt"):
        decode_bi5(raw, "EURUSD", H0, "bad.bi5")


def test_decode_bi5_rejects_non_lzma():
    with pytest.raises(MarketDataError, match="not valid LZMA"):
        decode_bi5(b"this is not lzma at all", "EURUSD", H0, "bad.bi5")


def test_unknown_symbol_refuses_to_guess_scale():
    raw = _bi5([(0, 110020, 110000, 1, 1)])
    with pytest.raises(MarketDataError, match="refusing to guess"):
        decode_bi5(raw, "ZZZZZZ", H0)


def test_pipet_registries_from_both_tools_agree():
    """
    TickVault stores multipliers, the downloader stores divisors. They must
    describe the same scaling; a divergence would silently misprice a symbol.
    """
    downloader_divisor = {"EURUSD": 100000, "GBPUSD": 100000,
                          "USDJPY": 1000, "XAUUSD": 1000}
    for sym, div in downloader_divisor.items():
        assert PIPET_SCALE[sym] == pytest.approx(1.0 / div, rel=1e-12), sym


# ---------------------------------------------------------------------------
# provider contract: HistData
# ---------------------------------------------------------------------------

def test_histdata_uses_fixed_offset_not_dst(tmp_path):
    """
    HistData is EST year-round. A July bar must shift by the same 5 hours as a
    January bar; localising to America/New_York would shift July by 4 and move
    every session boundary.
    """
    p = tmp_path / "DAT_ASCII_EURUSD_M1_2024.csv"
    p.write_text("20240102 100000;1.1000;1.1010;1.0990;1.1005;0\n"
                 "20240702 100000;1.0800;1.0810;1.0790;1.0805;0\n")
    out = read_histdata_m1(str(p), "EURUSD")
    assert out["time"].iloc[0] == pd.Timestamp("2024-01-02 15:00:00", tz="UTC")
    assert out["time"].iloc[1] == pd.Timestamp("2024-07-02 15:00:00", tz="UTC")
    assert HISTDATA_FIXED_UTC_OFFSET_HOURS == -5


def test_histdata_volume_zero_does_not_become_real_volume(tmp_path):
    """HistData volume is a tick count and often 0. real_volume is unavailable."""
    p = tmp_path / "h.csv"
    p.write_text("20240102 100000;1.1000;1.1010;1.0990;1.1005;0\n")
    out = read_histdata_m1(str(p), "EURUSD")
    assert out["tick_volume"].iloc[0] == 0
    assert pd.isna(out["real_volume"].iloc[0])


def test_histdata_bad_timestamp_raises(tmp_path):
    p = tmp_path / "h.csv"
    p.write_text("not-a-date;1.1;1.1;1.1;1.1;0\n")
    with pytest.raises(MarketDataError, match="unparseable timestamps"):
        read_histdata_m1(str(p), "EURUSD")


def test_histdata_columns_are_canonical(tmp_path):
    p = tmp_path / "h.csv"
    p.write_text("20240102 100000;1.1000;1.1010;1.0990;1.1005;3\n")
    assert list(read_histdata_m1(str(p), "EURUSD").columns) == list(CANONICAL_BAR_COLUMNS)


# ---------------------------------------------------------------------------
# tick -> bar
# ---------------------------------------------------------------------------

def test_bars_are_left_labelled_like_mt5():
    """A bar stamped 10:00 covers [10:00, 10:01) -- MT5's iTime() convention."""
    bars = ticks_to_bars(_ticks(180), "M1")
    assert bars["time"].iloc[0] == H0
    assert bars["time"].iloc[1] == H0 + pd.Timedelta(minutes=1)


def test_bar_ohlc_matches_the_ticks_inside_it():
    ticks = _ticks(120)
    bars = ticks_to_bars(ticks, "M1")
    first = ticks[ticks["timestamp"] < H0 + pd.Timedelta(minutes=1)]
    assert bars["open"].iloc[0] == pytest.approx(first["bid"].iloc[0])
    assert bars["close"].iloc[0] == pytest.approx(first["bid"].iloc[-1])
    assert bars["high"].iloc[0] == pytest.approx(first["bid"].max())
    assert bars["low"].iloc[0] == pytest.approx(first["bid"].min())


def test_bars_built_from_bid_by_default():
    ticks = _ticks(120)
    bid_bars = ticks_to_bars(ticks, "M1", price="bid")
    ask_bars = ticks_to_bars(ticks, "M1", price="ask")
    assert (ask_bars["close"] > bid_bars["close"]).all()


def test_empty_interval_produces_no_bar():
    """A closed minute has no bar in MT5; inventing a flat one fabricates liquidity."""
    a = _ticks(30)
    b = _ticks(30, start=H0 + pd.Timedelta(minutes=5))
    bars = ticks_to_bars(pd.concat([a, b], ignore_index=True), "M1")
    times = list(bars["time"])
    assert H0 + pd.Timedelta(minutes=2) not in times
    assert len(bars) == 2


def test_tick_volume_counts_ticks():
    bars = ticks_to_bars(_ticks(120), "M1")
    assert int(bars["tick_volume"].iloc[0]) == 60


def test_ticks_to_bars_is_deterministic():
    ticks = _ticks(300)
    pd.testing.assert_frame_equal(ticks_to_bars(ticks, "M1"), ticks_to_bars(ticks, "M1"))


# ---------------------------------------------------------------------------
# resampling ladder
# ---------------------------------------------------------------------------

def test_m1_to_m5_aggregates_correctly():
    m1 = _bars(60)
    m5 = resample_bars(m1, "M5")
    assert len(m5) == 12
    assert m5["open"].iloc[0] == pytest.approx(m1["open"].iloc[0])
    assert m5["close"].iloc[0] == pytest.approx(m1["close"].iloc[4])
    assert m5["high"].iloc[0] == pytest.approx(m1["high"].iloc[:5].max())
    assert m5["low"].iloc[0] == pytest.approx(m1["low"].iloc[:5].min())


def test_downward_resampling_is_refused():
    """Deriving M1 from H1 would invent the intrabar structure features read."""
    h1 = _bars(50, tf="H1", freq="1h")
    with pytest.raises(MarketDataError, match="fabricate intrabar structure"):
        resample_bars(h1, "M1")


def test_full_timeframe_ladder_builds():
    ladder = build_timeframe_set(_bars(1440 * 3))
    for tf in ("M1", "M5", "M15", "H1", "H4", "D1"):
        assert tf in ladder and len(ladder[tf]) > 0
    assert len(ladder["M5"]) > len(ladder["H1"]) > len(ladder["D1"])


def test_resampled_volume_sums():
    m1 = _bars(10)
    m5 = resample_bars(m1, "M5")
    assert int(m5["tick_volume"].iloc[0]) == int(m1["tick_volume"].iloc[:5].sum())


# ---------------------------------------------------------------------------
# quality gate
# ---------------------------------------------------------------------------

def test_clean_ticks_pass():
    assert validate_ticks(_ticks(300)).status is QualityStatus.OK


def test_crossed_quote_is_rejected():
    t = _ticks(100)
    t.loc[5, "ask"] = t.loc[5, "bid"] - 0.0005
    res = validate_ticks(t)
    assert "CROSSED_QUOTE" in codes(res) and res.status is QualityStatus.REJECTED


def test_zero_price_is_rejected():
    t = _ticks(100)
    t.loc[3, "bid"] = 0.0
    assert "INVALID_PRICE" in codes(validate_ticks(t))


def test_out_of_order_ticks_rejected():
    t = _ticks(100)
    t = pd.concat([t.iloc[50:], t.iloc[:50]], ignore_index=True)
    assert "TICKS_OUT_OF_ORDER" in codes(validate_ticks(t))


def test_empty_ticks_rejected_not_passed():
    res = validate_ticks(pd.DataFrame(columns=list(CANONICAL_TICK_COLUMNS)))
    assert res.status is QualityStatus.REJECTED


def test_clean_bars_pass():
    assert validate_bars(_bars(500), expect_timeframe="M1").status is QualityStatus.OK


def test_impossible_ohlc_rejected():
    b = _bars(100)
    b.loc[7, "high"] = b.loc[7, "low"] - 0.001
    res = validate_bars(b)
    assert "IMPOSSIBLE_OHLC" in codes(res) and res.status is QualityStatus.REJECTED


def test_high_not_enclosing_close_rejected():
    b = _bars(100)
    b.loc[9, "close"] = b.loc[9, "high"] + 0.01
    assert "IMPOSSIBLE_OHLC" in codes(validate_bars(b))


def test_duplicate_bar_time_rejected():
    b = _bars(100)
    b = pd.concat([b, b.iloc[[10]]], ignore_index=True).sort_values("time")
    assert "DUPLICATE_BAR_TIME" in codes(validate_bars(b))


def test_mixed_symbols_rejected():
    b = pd.concat([_bars(50), _bars(50, symbol="GBPUSD")], ignore_index=True)
    assert "MIXED_SYMBOLS" in codes(validate_bars(b))


def test_weekend_gap_is_info_not_error():
    """A gate that errors on every Saturday teaches its operator to ignore it."""
    a = _bars(200)
    b = _bars(200, start="2024-01-08 00:00:00")
    res = validate_bars(pd.concat([a, b], ignore_index=True), expect_timeframe="M1")
    assert "SESSION_GAPS" in codes(res)
    assert res.status is not QualityStatus.REJECTED


def test_intraday_gap_is_warned():
    a = _bars(100)
    b = _bars(100, start="2024-01-02 05:00:00")
    res = validate_bars(pd.concat([a, b], ignore_index=True), expect_timeframe="M1")
    assert "INTRADAY_GAP" in codes(res)


def test_timeframe_mismatch_rejected():
    assert "TIMEFRAME_MISMATCH" in codes(validate_bars(_bars(50), expect_timeframe="H1"))


def test_assert_quality_raises_on_rejection():
    b = _bars(50)
    b.loc[3, "high"] = b.loc[3, "low"] - 1
    with pytest.raises(MarketDataError, match="MARKET DATA REJECTED"):
        assert_quality_or_halt(validate_bars(b))


def test_assert_quality_silent_on_ok():
    assert_quality_or_halt(validate_bars(_bars(300), expect_timeframe="M1"))


def test_quality_gate_is_deterministic():
    b = _bars(300)
    assert validate_bars(b).report() == validate_bars(b).report()


# ---------------------------------------------------------------------------
# cross-source
# ---------------------------------------------------------------------------

def test_cross_source_agreement_passes():
    a = _bars(300, source="dukascopy")
    b = _bars(300, source="histdata")
    b["close"] = b["close"] + 0.00005      # sub-pip feed difference
    res = cross_source_compare(a, b)
    assert res.status is QualityStatus.OK


def test_cross_source_systematic_offset_is_rejected():
    """A large median offset means a timezone or scaling bug, not feed variation."""
    a = _bars(300, source="dukascopy")
    b = _bars(300, source="histdata")
    b["close"] = b["close"] + 0.0200       # 200 pips
    res = cross_source_compare(a, b)
    assert "CROSS_SOURCE_SYSTEMATIC_OFFSET" in codes(res)
    assert res.status is QualityStatus.REJECTED


def test_cross_source_no_overlap_is_rejected():
    a = _bars(100, start="2024-01-02 00:00:00")
    b = _bars(100, start="2024-06-02 00:00:00", source="histdata")
    res = cross_source_compare(a, b)
    assert "NO_OVERLAP" in codes(res)


def test_cross_source_never_merges_providers():
    a = _bars(200, source="dukascopy")
    b = _bars(200, source="histdata")
    res = cross_source_compare(a, b)
    assert res.stats["source_a"] == "dukascopy"
    assert res.stats["source_b"] == "histdata"
    # comparison only -- the inputs are untouched
    assert set(a["source"]) == {"dukascopy"} and set(b["source"]) == {"histdata"}


# ---------------------------------------------------------------------------
# manifest / provenance
# ---------------------------------------------------------------------------

def test_write_dataset_and_manifest(tmp_path):
    bars = _bars(300)
    entry = write_dataset(bars, str(tmp_path), symbol="EURUSD", timeframe="M1")
    assert entry["rows"] == 300 and len(entry["sha256"]) == 64
    path = write_manifest([entry], str(tmp_path))
    import json
    with open(path, encoding="utf-8") as fh:
        man = json.load(fh)
    assert man["timezone"] == "UTC"
    assert "NOT broker execution data" in man["provenance_note"]


def test_manifest_checksum_detects_tampering(tmp_path):
    bars = _bars(100)
    entry = write_dataset(bars, str(tmp_path), symbol="EURUSD", timeframe="M1")
    target = os.path.join(str(tmp_path), entry["file"])
    with open(target, "a", encoding="utf-8") as fh:
        fh.write("2024-01-09T00:00:00+0000,EURUSD,M1,1,1,1,1,1,,x,x,UTC,OK\n")
    from nexa_marketdata import sha256_file
    assert sha256_file(target) != entry["sha256"]


def test_source_identity_is_preserved_through_the_pipeline():
    bars = ticks_to_bars(_ticks(300), "M1")
    assert set(bars["source"]) == {"dukascopy"}
    assert set(resample_bars(bars, "M5")["source"]) == {"dukascopy"}


def test_no_network_access_is_attempted():
    """The pipeline decodes and validates; downloading is a separate concern."""
    import inspect

    import nexa_marketdata as m
    src = inspect.getsource(m)
    for token in ("requests.", "urlopen", "httpx.", "aiohttp", "socket."):
        assert token not in src, f"{token} must not appear in the pipeline"
