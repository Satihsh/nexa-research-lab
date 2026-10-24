"""Tests for nexa_causality: causal builders pass, leaky builders fail closed."""
from __future__ import annotations

import numpy as np
import pandas as pd

import nexa_causality as nc


def _bars(n=600, seed=0):
    rng = np.random.default_rng(seed)
    c = 100 + np.cumsum(rng.normal(0, 0.3, n))
    o = np.concatenate(([100.0], c[:-1]))
    return pd.DataFrame({"time": pd.date_range("2020-01-01", periods=n, freq="1min"), "open": o,
                         "high": np.maximum(o, c) + 0.1, "low": np.minimum(o, c) - 0.1, "close": c})


def causal_sma(b):
    return b["close"].rolling(20, min_periods=20).mean()


def leaky_centered(b):
    return b["close"].rolling(21, center=True, min_periods=21).mean()       # uses 10 future bars


def leaky_full_sample_z(b):
    return (b["close"] - b["close"].mean()) / b["close"].std()             # full-sample statistics


def leaky_shift_back(b):
    return b["close"].shift(-1)                                            # next bar's close


def test_causal_builder_certifies():
    cert = nc.certify(causal_sma, _bars())
    assert cert["passed"] and len(cert["source_sha256"]) == 64


def test_every_leaky_builder_fails_closed():
    for fn in (leaky_centered, leaky_full_sample_z, leaky_shift_back):
        cert = nc.certify(fn, _bars())
        assert not cert["passed"], fn.__name__
        assert cert["failures"][0]["rows_changed_before_cut"] > 0


def test_length_mismatch_is_rejected():
    def drops_rows(b):
        return b["close"].iloc[5:]
    try:
        nc.certify(drops_rows, _bars())
        raise AssertionError("expected failure")
    except ValueError:
        pass
