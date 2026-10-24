"""
test_nexa_labels.py -- Stage 4 tests.

Synthetic OHLC only. No MT5 terminal, no network, no recorded journal.

The tests construct price paths whose outcome is obvious by inspection, then
assert the labeler agrees. They deliberately do NOT mirror the implementation's
control flow: each fixture states what a human reading the bars would conclude,
which is the only way a test can catch the implementation being wrong rather
than merely being itself.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nexa_labels import (
    AmbiguityPolicy,
    FillBarPolicy,
    Label,
    LabelConfig,
    LabelContractError,
    MarketBars,
    label_dataset,
    label_trade,
    training_view,
    validate_geometry,
)

T0 = pd.Timestamp("2026-09-18 08:00:00")


def _bars_from(ohlc, start=T0, freq="1min", symbol="EURUSD") -> MarketBars:
    """ohlc: list of (open, high, low, close)."""
    t = pd.date_range(start, periods=len(ohlc), freq=freq)
    df = pd.DataFrame(ohlc, columns=["open", "high", "low", "close"])
    df.insert(0, "time", t)
    return MarketBars(frames={symbol: df})


def _flat(n, price=1.1000, wiggle=0.0001, start=T0):
    """Bars that move nowhere: never touch a barrier set outside +/- wiggle."""
    return [(price, price + wiggle, price - wiggle, price) for _ in range(n)]


def _walk(*bars, symbol="EURUSD"):
    """
    Build a series whose FIRST bar is the fill bar and whose remaining bars are
    the walk.

    The default FillBarPolicy excludes the fill bar (its range may predate the
    fill), so writing fixtures this way makes `bars_to_outcome` read as the
    position within the walk, which is what the assertions mean.
    """
    flat_fill = (1.1000, 1.1001, 1.0999, 1.1000)
    seq = [flat_fill]
    for b in bars:
        seq.extend(b if isinstance(b, list) else [b])
    return _bars_from(seq, symbol=symbol)


def _cfg(**over) -> LabelConfig:
    return LabelConfig(**over)


# ---------------------------------------------------------------------------
# 1-4: directional barrier resolution
# ---------------------------------------------------------------------------

def test_long_tp_first():
    bars = _walk(_flat(2), (1.1000, 1.1060, 1.0995, 1.1055))
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, T0, bars)
    assert oc.label is Label.TP_WIN
    assert oc.bars_to_outcome == 3
    assert oc.label_end_ts == T0 + pd.Timedelta(minutes=3)


def test_long_sl_first():
    bars = _walk(_flat(2), (1.1000, 1.1005, 1.0940, 1.0945))
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, T0, bars)
    assert oc.label is Label.SL_LOSS
    assert oc.bars_to_outcome == 3


def test_short_tp_first():
    bars = _walk(_flat(2), (1.1000, 1.1005, 1.0940, 1.0945))
    oc = label_trade("EURUSD", -1, 1.1000, 1.1050, 1.0950, T0, bars)
    assert oc.label is Label.TP_WIN


def test_short_sl_first():
    bars = _walk(_flat(2), (1.1000, 1.1060, 1.0995, 1.1055))
    oc = label_trade("EURUSD", -1, 1.1000, 1.1050, 1.0950, T0, bars)
    assert oc.label is Label.SL_LOSS


# ---------------------------------------------------------------------------
# 5: timeout  /  15: horizon boundary
# ---------------------------------------------------------------------------

def test_timeout_when_nothing_is_touched():
    cfg = _cfg(horizon_bars=20, time_exit_bars=0)
    bars = _bars_from(_flat(40))
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, T0, bars, cfg)
    assert oc.label is Label.TIMEOUT
    assert oc.bars_to_outcome == 20
    assert oc.label_reason == "HORIZON_EXPIRED"


def test_horizon_boundary_touch_on_last_allowed_bar_counts():
    cfg = _cfg(horizon_bars=5, time_exit_bars=0)
    bars = _walk(_flat(4), (1.1000, 1.1060, 1.0995, 1.1055), _flat(10))
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, T0, bars, cfg)
    assert oc.label is Label.TP_WIN and oc.bars_to_outcome == 5


def test_touch_one_bar_past_horizon_is_timeout():
    """A barrier reached after the horizon is not the trade's outcome."""
    cfg = _cfg(horizon_bars=5, time_exit_bars=0)
    bars = _walk(_flat(5), (1.1000, 1.1060, 1.0995, 1.1055), _flat(5))
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, T0, bars, cfg)
    assert oc.label is Label.TIMEOUT


def test_market_data_exhausted_is_distinguished_from_horizon():
    cfg = _cfg(horizon_bars=500, time_exit_bars=0)
    bars = _bars_from(_flat(6))
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, T0, bars, cfg)
    assert oc.label is Label.TIMEOUT
    assert oc.label_reason == "MARKET_DATA_EXHAUSTED_BEFORE_HORIZON"


# ---------------------------------------------------------------------------
# 6 / 27: ambiguity
# ---------------------------------------------------------------------------

def test_ambiguous_bar_spans_both_barriers():
    bars = _bars_from(_flat(1) + [(1.1000, 1.1060, 1.0940, 1.1000)])
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, T0, bars)
    assert oc.label is Label.AMBIGUOUS
    assert oc.ambiguous_bar is True
    assert "UNKNOWABLE" in oc.label_reason


def test_ambiguous_never_becomes_win_or_loss_under_default_policy():
    bars = _bars_from(_flat(1) + [(1.1000, 1.1060, 1.0940, 1.1000)])
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, T0, bars)
    assert oc.label not in (Label.TP_WIN, Label.SL_LOSS, Label.BREAKEVEN_STOP)


def test_pessimistic_policy_reproduces_mql5_exporter():
    """Opt-in only: the MQL5 exporter's documented rule, for like-for-like runs."""
    bars = _bars_from(_flat(1) + [(1.1000, 1.1060, 1.0940, 1.1000)])
    cfg = _cfg(ambiguity=AmbiguityPolicy.PESSIMISTIC_LOSS)
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, T0, bars, cfg)
    assert oc.label is Label.SL_LOSS
    assert oc.ambiguous_bar is True
    assert oc.label_reason == "AMBIGUOUS_BAR_RESOLVED_LOSS"


def test_ambiguity_policy_recorded_in_exec_model():
    a = _cfg().exec_model()
    b = _cfg(ambiguity=AmbiguityPolicy.PESSIMISTIC_LOSS).exec_model()
    assert a != b and "AMBIGUOUS" in a and "PESSIMISTIC_LOSS" in b


# ---------------------------------------------------------------------------
# 7-9: MFE / MAE / R normalisation
# ---------------------------------------------------------------------------

def test_mfe_long_in_r():
    # risk = 50 pips; best favourable excursion 25 pips => 0.5R
    bars = _walk((1.1000, 1.1025, 1.0995, 1.1000), _flat(2),
                 (1.1000, 1.1005, 1.0940, 1.0945))
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, T0, bars)
    assert oc.label is Label.SL_LOSS
    assert oc.mfe_r == pytest.approx(0.5, abs=1e-6)


def test_mae_long_in_r():
    # worst adverse excursion 30 pips on a 50-pip risk => 0.6R
    bars = _walk((1.1000, 1.1005, 1.0970, 1.1000), _flat(1),
                 (1.1000, 1.1060, 1.0995, 1.1055))
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, T0, bars)
    assert oc.label is Label.TP_WIN
    assert oc.mae_r == pytest.approx(0.6, abs=1e-6)


def test_mfe_mae_for_short_are_mirrored():
    bars = _walk((1.1000, 1.1030, 1.0975, 1.1000),
                 (1.1000, 1.1005, 1.0940, 1.0945))
    oc = label_trade("EURUSD", -1, 1.1000, 1.1050, 1.0950, T0, bars)
    assert oc.label is Label.TP_WIN
    assert oc.mfe_r == pytest.approx(1.2, abs=1e-6)   # (1.1000-1.0940)/0.0050
    assert oc.mae_r == pytest.approx(0.6, abs=1e-6)   # (1.1030-1.1000)/0.0050


def test_r_normalisation_uses_actual_risk_distance():
    """Halving the stop distance doubles every excursion expressed in R."""
    bars = _walk((1.1000, 1.1025, 1.0995, 1.1000), _flat(1),
                 (1.1000, 1.1005, 1.0940, 1.0945))
    wide = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, T0, bars)
    tight = label_trade("EURUSD", 1, 1.1000, 1.0975, 1.1050, T0, bars)
    assert tight.mfe_r == pytest.approx(wide.mfe_r * 2, abs=1e-9)


def test_target_r_is_not_used_as_mfe():
    """MFE must come from observed price, never from the intended target."""
    bars = _walk(_flat(2), (1.1000, 1.1005, 1.0940, 1.0945))
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, T0, bars)
    # the trade's intended target was 1.0R; the best price actually reached was
    # 5 pips on a 50-pip risk. MFE must report what happened, not what was aimed at.
    target_r = (1.1050 - 1.1000) / 0.0050
    assert oc.mfe_r == pytest.approx(0.1, abs=1e-6)
    assert oc.mfe_r < target_r / 2
    assert oc.label is Label.SL_LOSS


def test_mfe_mae_stop_at_barrier_touch():
    """Excursions after label_end_ts must not be counted."""
    bars = _walk(_flat(1),
                 (1.1000, 1.1060, 1.0995, 1.1055),      # TP here
                 (1.1055, 1.2000, 1.0000, 1.1500))      # huge, must be ignored
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, T0, bars)
    assert oc.label is Label.TP_WIN and oc.bars_to_outcome == 2
    assert oc.mfe_r == pytest.approx((1.1060 - 1.1000) / 0.0050, abs=1e-6)
    assert oc.mae_r < 1.0           # 1.0000 low of the later bar never seen


# ---------------------------------------------------------------------------
# 10: actual vs intended fill
# ---------------------------------------------------------------------------

def test_actual_fill_price_is_used_not_intended():
    """
    Entry slipped to 1.1010. TP 1.1050 is 40 pips away from the actual fill, not
    50. A bar peaking at 1.1052 hits TP either way, but the R scale differs, so
    MFE proves which entry was used.
    """
    bars = _walk((1.1010, 1.1052, 1.1005, 1.1050))
    oc = label_trade("EURUSD", 1, entry=1.1010, sl=1.0960, tp=1.1050,
                     fill_ts=T0, bars=bars)
    assert oc.label is Label.TP_WIN
    assert oc.mfe_r == pytest.approx((1.1052 - 1.1010) / 0.0050, abs=1e-6)


def test_dataset_refuses_when_entry_actual_missing():
    frame = _episode_frame(entry_actual=np.nan)
    res = label_dataset(frame, _bars_from(_flat(5)), _cfg())
    assert set(res.frame["label"]) == {Label.INVALID.value}
    assert any(f.code == "INVALID_EPISODES" for f in res.findings)
    assert not res.ok


# ---------------------------------------------------------------------------
# 11-12 / 23: geometry and risk validation
# ---------------------------------------------------------------------------

def test_invalid_long_geometry_sl_above_entry():
    ok, reason = validate_geometry(1, 1.1000, 1.1050, 1.1100)
    assert not ok and "LONG_SL_NOT_BELOW" in reason


def test_invalid_short_geometry_tp_above_entry():
    ok, reason = validate_geometry(-1, 1.1000, 1.1050, 1.1100)
    assert not ok and "SHORT_TP_NOT_BELOW" in reason


def test_invalid_geometry_is_failed_not_repaired():
    bars = _bars_from(_flat(5))
    oc = label_trade("EURUSD", 1, 1.1000, 1.1050, 1.1100, T0, bars)
    assert oc.label is Label.INVALID
    assert oc.label not in (Label.TP_WIN, Label.SL_LOSS)


def test_zero_risk_distance_is_invalid():
    bars = _bars_from(_flat(5))
    oc = label_trade("EURUSD", 1, 1.1000, 1.1000, 1.1050, T0, bars)
    assert oc.label is Label.INVALID


def test_invalid_direction_rejected():
    ok, reason = validate_geometry(0, 1.1000, 1.0950, 1.1050)
    assert not ok and reason == "INVALID_DIRECTION"


# ---------------------------------------------------------------------------
# 13-14: fill-bar boundary
# ---------------------------------------------------------------------------

def test_fill_bar_excluded_by_default():
    """
    The fill bar's own range may predate the fill, so it is not credited to the
    trade by default. Here the fill bar alone would hit TP.
    """
    bars = _bars_from([(1.1000, 1.1060, 1.0995, 1.1000)] + _flat(3))
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, T0, bars, _cfg(
        horizon_bars=10, time_exit_bars=0))
    assert oc.label is Label.TIMEOUT, "fill bar must not resolve the label by default"


def test_fill_bar_included_under_exporter_policy():
    bars = _bars_from([(1.1000, 1.1060, 1.0995, 1.1000)] + _flat(3))
    cfg = _cfg(fill_bar=FillBarPolicy.INCLUDE_FILL_BAR, horizon_bars=10, time_exit_bars=0)
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, T0, bars, cfg)
    assert oc.label is Label.TP_WIN


def test_fill_between_bars_starts_at_next_closed_bar():
    bars = _bars_from(_flat(4))
    mid = T0 + pd.Timedelta(seconds=90)      # inside the second bar
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, mid, bars,
                     _cfg(horizon_bars=10, time_exit_bars=0))
    assert oc.label_start_ts == mid
    assert oc.bars_to_outcome == 2           # bars at +2min and +3min only


# ---------------------------------------------------------------------------
# breakeven ratchet and time exit (the EA's documented exit semantics)
# ---------------------------------------------------------------------------

def test_breakeven_stop_after_ratchet_arms():
    """+1R reached, then price falls back through entry: a scratch, not a loss."""
    bars = _walk((1.1000, 1.1055, 1.0995, 1.1050),
                 (1.1050, 1.1052, 1.0999, 1.1000))
    cfg = _cfg(horizon_bars=10, time_exit_bars=0, breakeven_at_r=1.0)
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1200, T0, bars, cfg)
    assert oc.label is Label.BREAKEVEN_STOP
    assert oc.label_reason == "BREAKEVEN_STOP"


def test_ratchet_does_not_arm_before_barrier_test_on_same_bar():
    """
    A bar that reaches +1R and also hits the original SL is a LOSS, not a
    breakeven scratch: the EA cannot move a stop it has not yet survived.
    """
    bars = _walk((1.1000, 1.1055, 1.0940, 1.0945))
    cfg = _cfg(ambiguity=AmbiguityPolicy.PESSIMISTIC_LOSS, breakeven_at_r=1.0)
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1200, T0, bars, cfg)
    assert oc.label is Label.SL_LOSS


def test_time_exit_fires_when_progress_is_poor():
    cfg = _cfg(time_exit_bars=5, time_exit_min_r=0.30, horizon_bars=100)
    bars = _bars_from(_flat(20))
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, T0, bars, cfg)
    assert oc.label is Label.TIME_EXIT
    assert oc.bars_to_outcome == 5


def test_time_exit_does_not_fire_when_progress_is_good():
    cfg = _cfg(time_exit_bars=3, time_exit_min_r=0.30, horizon_bars=100,
               breakeven_at_r=99)     # keep the ratchet out of this test
    good = [(1.1000, 1.1030, 1.0999, 1.1030)] * 10
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1200, T0, _walk(good), cfg)
    assert oc.label is not Label.TIME_EXIT


# ---------------------------------------------------------------------------
# dataset-level: episodes, partials, rejects, orphans
# ---------------------------------------------------------------------------

def _episode_frame(entry_actual=1.1000, direction=1, with_partial=False,
                   with_close=True, result_r=1.5, episode_id=0, symbol="EURUSD",
                   fill_ts=None, event_open=True, rejected=False):
    fill_ts = fill_ts if fill_ts is not None else T0
    rows = []
    src = 0
    if event_open:
        rows.append({"event": "OPEN", "episode_id": episode_id, "symbol": symbol,
                     "direction": direction, "entry_intended": 1.0999,
                     "entry_actual": np.nan, "sl_price": 1.0950, "tp_price": 1.1050,
                     "fill_ts": pd.NaT, "result_r": np.nan, "source_row": src})
        src += 1
    if rejected:
        rows.append({"event": "REJECTED", "episode_id": episode_id, "symbol": symbol,
                     "direction": direction, "entry_intended": 1.0999,
                     "entry_actual": np.nan, "sl_price": 1.0950, "tp_price": 1.1050,
                     "fill_ts": pd.NaT, "result_r": np.nan, "source_row": src})
        src += 1
    else:
        rows.append({"event": "FILL", "episode_id": episode_id, "symbol": symbol,
                     "direction": direction, "entry_intended": 1.0999,
                     "entry_actual": entry_actual, "sl_price": 1.0950,
                     "tp_price": 1.1050, "fill_ts": fill_ts,
                     "result_r": np.nan, "source_row": src})
        src += 1
        if with_partial:
            rows.append({"event": "PARTIAL_CLOSE", "episode_id": episode_id,
                         "symbol": symbol, "direction": direction,
                         "entry_intended": 1.0999, "entry_actual": entry_actual,
                         "sl_price": np.nan, "tp_price": np.nan,
                         "fill_ts": fill_ts + pd.Timedelta(minutes=2),
                         "result_r": 0.75, "source_row": src})
            src += 1
        if with_close:
            rows.append({"event": "CLOSE", "episode_id": episode_id, "symbol": symbol,
                         "direction": direction, "entry_intended": 1.0999,
                         "entry_actual": entry_actual, "sl_price": np.nan,
                         "tp_price": np.nan,
                         "fill_ts": fill_ts + pd.Timedelta(minutes=4),
                         "result_r": result_r, "source_row": src})
    frame = pd.DataFrame(rows)
    frame["schema_version"] = "1.0"
    return frame


def test_rejected_order_is_not_labelled():
    frame = _episode_frame(rejected=True)
    res = label_dataset(frame, _bars_from(_flat(10)), _cfg())
    assert set(res.frame["label"]) == {Label.UNLABELLED.value}
    assert "REJECTED_NOT_EXECUTED" in set(res.frame["label_reason"])


def test_rejected_order_never_enters_training_view():
    frame = _episode_frame(rejected=True)
    res = label_dataset(frame, _bars_from(_flat(10)), _cfg())
    assert len(training_view(res)) == 0


def test_open_without_fill_is_not_a_trade():
    frame = _episode_frame(event_open=True, rejected=False)
    frame = frame[frame["event"] == "OPEN"].copy()
    res = label_dataset(frame, _bars_from(_flat(10)), _cfg())
    assert "NO_FILL_NOT_A_TRADE" in set(res.frame["label_reason"])
    assert len(training_view(res)) == 0


def test_orphan_execution_row_is_not_given_an_episode():
    frame = _episode_frame()
    frame.loc[frame["event"] == "FILL", "episode_id"] = -1
    frame = frame[frame["event"] == "FILL"].copy()
    res = label_dataset(frame, _bars_from(_flat(10)), _cfg())
    assert "ORPHAN_EXECUTION_ROW_NO_EPISODE" in set(res.frame["label_reason"])
    assert any(f.code == "ORPHAN_EXECUTION_ROWS" for f in res.findings)


def test_partial_close_episode_yields_one_label():
    """A partial close is management inside one trade, not a second trade."""
    frame = _episode_frame(with_partial=True)
    bars = _bars_from(_flat(2) + [(1.1000, 1.1060, 1.0995, 1.1055)] + _flat(5))
    res = label_dataset(frame, bars, _cfg())
    assert res.stats["episodes_labelled"] == 1
    labels = set(res.frame["label"])
    assert labels == {Label.TP_WIN.value}
    assert len(training_view(res)) == 1      # one row per episode, not per partial


def test_multiple_independent_episodes():
    a = _episode_frame(episode_id=0)
    b = _episode_frame(episode_id=1, fill_ts=T0 + pd.Timedelta(minutes=30))
    frame = pd.concat([a, b], ignore_index=True)
    bars = _bars_from(_flat(2) + [(1.1000, 1.1060, 1.0995, 1.1055)] + _flat(60))
    res = label_dataset(frame, bars, _cfg(horizon_bars=20, time_exit_bars=0))
    assert res.stats["episodes_labelled"] == 2
    assert len(training_view(res)) == 2


def test_mixed_long_and_short_dataset():
    a = _episode_frame(episode_id=0, direction=1)
    b = _episode_frame(episode_id=1, direction=-1,
                       fill_ts=T0 + pd.Timedelta(minutes=30))
    b.loc[b["event"] == "FILL", ["sl_price", "tp_price"]] = [1.1050, 1.0950]
    frame = pd.concat([a, b], ignore_index=True)
    bars = _bars_from(_flat(2) + [(1.1000, 1.1060, 1.0995, 1.1055)] + _flat(60))
    res = label_dataset(frame, bars, _cfg(horizon_bars=20, time_exit_bars=0))
    labels = [o.label for o in res.outcomes]
    assert Label.TP_WIN in labels          # the long hit TP
    assert len(res.outcomes) == 2


def test_actual_result_r_is_preserved_not_manufactured():
    frame = _episode_frame(result_r=1.5)
    bars = _bars_from(_flat(2) + [(1.1000, 1.1060, 1.0995, 1.1055)] + _flat(5))
    res = label_dataset(frame, bars, _cfg())
    assert res.outcomes[0].result_r_actual == pytest.approx(1.5)
    # broker result and barrier label are separate facts
    assert res.outcomes[0].label is Label.TP_WIN


def test_result_r_untouched_when_label_disagrees():
    """A losing broker result is never rewritten to match a winning barrier label."""
    frame = _episode_frame(result_r=-1.0)
    bars = _bars_from(_flat(2) + [(1.1000, 1.1060, 1.0995, 1.1055)] + _flat(5))
    res = label_dataset(frame, bars, _cfg())
    assert res.outcomes[0].result_r_actual == pytest.approx(-1.0)


def test_stage2_columns_are_preserved():
    frame = _episode_frame()
    frame["f00"] = 1.0
    frame["decision_ts_effective"] = T0
    res = label_dataset(frame, _bars_from(_flat(10)), _cfg())
    for col in ("f00", "decision_ts_effective", "entry_intended", "event", "episode_id"):
        assert col in res.frame.columns
    assert res.frame["entry_intended"].iloc[0] == pytest.approx(1.0999)


def test_stage4_columns_are_appended():
    frame = _episode_frame()
    res = label_dataset(frame, _bars_from(_flat(10)), _cfg())
    for col in ("label_start_ts", "label_end_ts", "label", "label_reason",
                "ambiguous_bar", "bars_to_outcome", "mfe_r", "mae_r", "exec_model"):
        assert col in res.frame.columns


# ---------------------------------------------------------------------------
# fail-closed contract
# ---------------------------------------------------------------------------

def test_unsupported_schema_version_raises():
    frame = _episode_frame()
    frame["schema_version"] = "2.0"
    with pytest.raises(LabelContractError, match="unsupported schema_version"):
        label_dataset(frame, _bars_from(_flat(5)), _cfg())


def test_missing_episode_id_raises():
    frame = _episode_frame().drop(columns=["episode_id"])
    with pytest.raises(LabelContractError, match="episode_id"):
        label_dataset(frame, _bars_from(_flat(5)), _cfg())


def test_missing_fill_ts_is_invalid():
    bars = _bars_from(_flat(5))
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, None, bars)
    assert oc.label is Label.INVALID and oc.label_reason == "MISSING_FILL_TS"


def test_epoch_fill_ts_is_impossible_chronology():
    bars = _bars_from(_flat(5))
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050,
                     pd.Timestamp("1970-01-01"), bars)
    assert oc.label is Label.INVALID and oc.label_reason == "IMPOSSIBLE_FILL_TS"


def test_missing_market_data_for_symbol_is_invalid():
    bars = MarketBars(frames={})
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, T0, bars)
    assert oc.label is Label.INVALID
    assert oc.label_reason == "NO_MARKET_DATA_AFTER_FILL"


def test_fill_after_all_available_bars_is_invalid():
    bars = _bars_from(_flat(5))
    late = T0 + pd.Timedelta(days=5)
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, late, bars)
    assert oc.label is Label.INVALID


def test_ambiguous_excluded_from_training_view():
    frame = _episode_frame()
    bars = _bars_from(_flat(1) + [(1.1000, 1.1060, 1.0940, 1.1000)] + _flat(5))
    res = label_dataset(frame, bars, _cfg())
    assert res.outcomes[0].label is Label.AMBIGUOUS
    assert len(training_view(res)) == 0


# ---------------------------------------------------------------------------
# causality, determinism, timestamps
# ---------------------------------------------------------------------------

def test_no_lookahead_bars_before_fill_are_never_read():
    """
    Bars before the fill contain a barrier touch. Deleting them must not change
    the label; if it did, pre-fill data was being used to resolve the trade.
    """
    pre = [(1.1000, 1.1400, 1.0500, 1.1000)] * 3     # would hit both barriers
    post = _flat(2) + [(1.1000, 1.1060, 1.0995, 1.1055)]
    full = _bars_from(pre + post)
    fill = T0 + pd.Timedelta(minutes=3)
    with_pre = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, fill, full)
    trimmed = _bars_from(post, start=fill + pd.Timedelta(minutes=1))
    without = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, fill, trimmed)
    assert with_pre.label is without.label is Label.TP_WIN
    assert with_pre.mfe_r == pytest.approx(without.mfe_r, abs=1e-12)
    assert with_pre.mae_r == pytest.approx(without.mae_r, abs=1e-12)


def test_no_lookahead_bars_after_label_end_are_never_read():
    base = _flat(1) + [(1.1000, 1.1060, 1.0995, 1.1055)]
    short = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, T0, _bars_from(base))
    long_tail = _bars_from(base + [(1.1055, 1.5000, 0.9000, 1.2000)] * 5)
    extended = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, T0, long_tail)
    assert short.label is extended.label
    assert short.mfe_r == pytest.approx(extended.mfe_r, abs=1e-12)
    assert short.mae_r == pytest.approx(extended.mae_r, abs=1e-12)
    assert short.bars_to_outcome == extended.bars_to_outcome


def test_labeling_is_deterministic():
    frame = _episode_frame()
    bars = _bars_from(_flat(2) + [(1.1000, 1.1060, 1.0995, 1.1055)] + _flat(5))
    a = label_dataset(frame, bars, _cfg())
    b = label_dataset(frame, bars, _cfg())
    assert a.stats == b.stats
    assert [o.label for o in a.outcomes] == [o.label for o in b.outcomes]
    pd.testing.assert_frame_equal(a.frame, b.frame)


def test_timestamps_are_preserved_and_distinct():
    frame = _episode_frame()
    frame["decision_ts"] = T0 - pd.Timedelta(minutes=5)
    frame["decision_ts_effective"] = T0 - pd.Timedelta(minutes=5)
    frame["write_ts"] = T0 + pd.Timedelta(hours=3)
    bars = _bars_from(_flat(2) + [(1.1000, 1.1060, 1.0995, 1.1055)] + _flat(5))
    res = label_dataset(frame, bars, _cfg())
    row = res.frame[res.frame["event"] == "FILL"].iloc[0]
    assert row["label_start_ts"] == T0
    assert row["label_start_ts"] != row["decision_ts"]
    assert row["label_end_ts"] > row["label_start_ts"]
    assert row["write_ts"] != row["label_end_ts"]


def test_label_start_equals_fill_ts_exactly():
    bars = _bars_from(_flat(4))
    fill = T0 + pd.Timedelta(seconds=37)
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, fill, bars,
                     _cfg(horizon_bars=10, time_exit_bars=0))
    assert oc.label_start_ts == fill


def test_timezone_aware_timestamps_round_trip():
    t = pd.Timestamp("2026-09-18 08:00:00", tz="UTC")
    bars = _bars_from(_flat(1) + [(1.1000, 1.1060, 1.0995, 1.1055)], start=t)
    oc = label_trade("EURUSD", 1, 1.1000, 1.0950, 1.1050, t, bars)
    assert oc.label is Label.TP_WIN
    assert oc.label_end_ts.tzinfo is not None


def test_exec_model_records_the_full_convention():
    em = _cfg().exec_model()
    for token in ("M1_OHLC", "BE1R", "TIMEEXIT48", "HORIZON480",
                  "AMBIGUOUS", "EXCLUDE_FILL_BAR"):
        assert token in em
