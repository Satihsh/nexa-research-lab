"""Causality certification for Phase-3 feature/signal builders.

A builder is any function f(bars: DataFrame) -> DataFrame | Series | ndarray aligned to bars,
whose row i may use ONLY bars 0..i. certify() tests that empirically: for several cut
points k it perturbs every bar at index >= k (OHLC shifted, geometry kept valid) and
requires the output rows < k to be bit-identical. It also requires the output length to
equal the input length (no silent re-alignment).

The certificate binds the result to the builder's SOURCE TEXT AND the full source of the module
that defines it (helpers included), so editing the builder or any helper in its module after
certification invalidates it. A registry records only results whose builders carry a passing
certificate with a matching source hash.

perturb_cols (default OHLC) lists every input column that is perturbed after the cut; columns
carrying time-stamped information (e.g. merged release values) must be listed so that a builder
reading a FUTURE row of them fails.

SENSITIVE CUTS. Fractional cuts alone almost never fall next to a sparse event, so a builder that
reads a release value a few bars early, or shifts a sparse signal by one bar, would pass. certify()
therefore also cuts at up to `sensitive_cuts` rows sampled deterministically from (a) rows where a
perturbed extra column carries a sparse value (an event) and (b) rows where a sparse output column
is non-zero (a signal), plus the row after each (b). A leak of any horizon then straddles a cut.

certify_events() is the event-table analogue: it perturbs value columns of every event at or after
a cut TIME and requires the declared causal output columns of all earlier events to be identical
(used for the calendar's prior-only baselines).
"""
from __future__ import annotations

import hashlib
import inspect

import numpy as np
import pandas as pd

OHLC = ("open", "high", "low", "close")


def source_sha256(fn) -> str:
    mod = inspect.getmodule(fn)
    try:
        mod_src = inspect.getsource(mod) if mod is not None else ""
    except (OSError, TypeError):
        mod_src = ""
    return hashlib.sha256((inspect.getsource(fn) + "\n#--module--\n" + mod_src).encode("utf-8")).hexdigest()


def _perturb_after(bars: pd.DataFrame, k: int, seed: int, extra_cols: tuple = ()) -> pd.DataFrame:
    b = bars.copy()
    rng = np.random.default_rng(seed)
    n = len(b) - k
    if n <= 0:
        return b
    scale = float(b["close"].std()) or 1.0
    shift = rng.normal(0.0, scale, n)
    for col in OHLC:
        b.loc[b.index[k:], col] = b[col].to_numpy()[k:] + shift
    ohlc = b[list(OHLC)].to_numpy()[k:]
    b.loc[b.index[k:], "high"] = ohlc.max(axis=1)
    b.loc[b.index[k:], "low"] = ohlc.min(axis=1)
    for col in extra_cols:
        v = b[col].to_numpy(float).copy()
        sc = float(np.nanstd(v)) or 1.0
        v[k:] = v[k:] + rng.normal(0.0, 3.0 * sc, n) + sc          # NaN stays NaN (absence of an event)
        b[col] = v
    return b


def _as_array(out, n: int) -> np.ndarray:
    a = out.to_numpy() if isinstance(out, (pd.Series, pd.DataFrame)) else np.asarray(out)
    if len(a) != n:
        raise ValueError(f"builder output length {len(a)} != input length {n}")
    return a.astype(float) if a.dtype != object else a


def _same(a: np.ndarray, b: np.ndarray) -> bool:
    if a.dtype == object or b.dtype == object:
        return bool(pd.DataFrame(a).equals(pd.DataFrame(b)))
    return np.array_equal(np.nan_to_num(a.astype(float), nan=-9.9e99), np.nan_to_num(b.astype(float), nan=-9.9e99))


def _spread_pick(rows: np.ndarray, k: int) -> list[int]:
    rows = np.unique(rows)
    if rows.size <= k:
        return rows.tolist()
    return rows[np.linspace(0, rows.size - 1, k).round().astype(int)].tolist()


def _sensitive_rows(bars: pd.DataFrame, base: np.ndarray, extra_cols: tuple, k: int) -> list[int]:
    n = len(bars)
    ev = []
    for col in extra_cols:
        v = bars[col].to_numpy(float)
        fin = np.isfinite(v)
        if 0 < fin.mean() < 0.05:                                   # sparse, event-like input
            ev.append(np.flatnonzero(fin))
    b2 = base.reshape(n, -1).astype(float) if base.dtype != object else np.zeros((n, 1))
    active = np.isfinite(b2) & (b2 != 0)
    sparse = active.mean(axis=0) < 0.05
    sig_rows = np.flatnonzero(active[:, sparse].any(axis=1)) if sparse.any() else np.array([], int)
    ev_rows = np.concatenate(ev) if ev else np.array([], int)
    picks = _spread_pick(ev_rows, k // 2) + _spread_pick(sig_rows, k // 2)
    picks += [r + 1 for r in _spread_pick(sig_rows, k // 2)]
    return sorted({r for r in picks if 1 <= r < n})


def certify(fn, bars: pd.DataFrame, cuts: tuple[float, ...] = (0.3, 0.5, 0.7, 0.9), seeds: int = 3,
            extra_cols: tuple = (), sensitive_cuts: int = 16) -> dict:
    n = len(bars)
    missing = [c for c in extra_cols if c not in bars.columns]
    if missing:
        raise ValueError(f"perturbation columns missing from bars: {missing}")
    base = _as_array(fn(bars), n)
    failures = []
    plan = [(max(1, int(n * frac)), s) for frac in cuts for s in range(seeds)]
    plan += [(k, 0) for k in _sensitive_rows(bars, base, tuple(extra_cols), sensitive_cuts)]
    for k, s in plan:
        try:
            pert = _as_array(fn(_perturb_after(bars, k, 1000 + s + k, tuple(extra_cols))), n)
        except Exception as exc:  # noqa: BLE001 - any failure under perturbation = NOT certified (fail closed)
            failures.append({"cut": k, "seed": s, "error": repr(exc)})
            continue
        a, b = base[:k], pert[:k]
        same = np.array_equal(np.nan_to_num(a.astype(float), nan=-9.9e99), np.nan_to_num(b.astype(float), nan=-9.9e99)) \
            if a.dtype != object else bool((a == b).all())
        if not same:
            diff_rows = int((np.nan_to_num(a.astype(float), nan=-9.9e99) != np.nan_to_num(b.astype(float), nan=-9.9e99)).reshape(len(a), -1).any(axis=1).sum()) \
                if a.dtype != object else -1
            failures.append({"cut": k, "seed": s, "rows_changed_before_cut": diff_rows})
    return {"kind": "bars", "builder": f"{fn.__module__}.{fn.__qualname__}", "source_sha256": source_sha256(fn),
            "rows": n, "cuts": list(cuts), "seeds": seeds, "sensitive_cuts": len(plan) - len(cuts) * seeds,
            "perturbed": list(OHLC) + list(extra_cols),
            "passed": not failures, "failures": failures[:10]}


def certify_events(fn, table: pd.DataFrame, time_col: str, perturb_cols: tuple, check_cols: tuple,
                   cuts: tuple[float, ...] = (0.3, 0.5, 0.7, 0.9), seeds: int = 3) -> dict:
    """fn(table) -> DataFrame aligned to table (same index). For each cut TIME, perturb perturb_cols of
    every row with time >= cut; check_cols of every row with time < cut must be unchanged."""
    t = pd.to_datetime(table[time_col])
    base = fn(table)
    if len(base) != len(table) or not base.index.equals(table.index):
        raise ValueError("event builder must return a frame aligned to the input table")
    failures = []
    for frac in cuts:
        cut = t.quantile(frac)
        after = (t >= cut).to_numpy()
        before = ~after
        for s in range(seeds):
            rng = np.random.default_rng(2000 + s)
            x = table.copy()
            for col in perturb_cols:
                v = x[col].to_numpy(float).copy()
                sc = float(np.nanstd(v)) or 1.0
                v[after] = v[after] + rng.normal(0.0, 3.0 * sc, int(after.sum())) + sc
                x[col] = v
            try:
                out = fn(x)
            except Exception as exc:  # noqa: BLE001 - any failure under perturbation = NOT certified (fail closed)
                failures.append({"cut": str(cut), "seed": s, "error": repr(exc)})
                continue
            for col in check_cols:
                if not _same(base.loc[before, col].to_numpy(), out.loc[before, col].to_numpy()):
                    failures.append({"cut": str(cut), "seed": s, "column": col})
    return {"kind": "events", "builder": f"{fn.__module__}.{fn.__qualname__}", "source_sha256": source_sha256(fn),
            "rows": len(table), "cuts": list(cuts), "seeds": seeds, "perturbed": list(perturb_cols),
            "checked": list(check_cols), "passed": not failures, "failures": failures[:10]}
