"""Python oracle of the FAIL-CLOSED correlation cap in NEXA_Risk.mqh (human-approved safety fix,
2026-09-29). Mirrors NexaCorrelationFromBars() statement by statement, including summation order,
so its results can be compared with the compiled MQL5 core on identical fixtures.

This is NOT a V2 research module and is not part of the V2 pinned code. The MQL5 file remains the
live authority; this oracle only tests it.

States: OK (0) pass, BLOCK (1) |corr| >= threshold, INSUFFICIENT_DATA (2) -> the caller BLOCKS.
"""
from __future__ import annotations

import math

import numpy as np

OK, BLOCK, INSUFFICIENT_DATA = 0, 1, 2
STATE_NAME = {OK: "OK", BLOCK: "BLOCK", INSUFFICIENT_DATA: "INSUFFICIENT_DATA"}
MIN_ALIGNED_FRAC = 0.80
THRESHOLD = 0.75          # InpMaxCorrelation (unchanged)
BARS_BACK = 100           # InpCorrelationBars (unchanged)


def _finite(x: float) -> bool:
    return math.isfinite(x)


def _find(t: list[int], x: int) -> int:
    lo, hi = 0, len(t) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if t[mid] == x:
            return mid
        if t[mid] < x:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def _ascending(t: list[int]) -> bool:
    return all(t[i] > t[i - 1] for i in range(1, len(t)))


def correlation_from_bars(tA, cA, tB, cB, bars_back: int = BARS_BACK, threshold: float = THRESHOLD,
                          min_aligned_frac: float = MIN_ALIGNED_FRAC) -> tuple[int, float, int, str]:
    """Returns (state, corr, aligned, detail); mirrors NexaCorrelationFromBars."""
    tA, tB = [int(x) for x in tA], [int(x) for x in tB]
    cA, cB = [float(x) for x in cA], [float(x) for x in cB]
    nA, nB = len(tA), len(tB)
    if bars_back < 3 or not _finite(threshold) or threshold <= 0 or not _finite(min_aligned_frac) or min_aligned_frac <= 0:
        return INSUFFICIENT_DATA, 0.0, 0, "INVALID_CONFIG"
    if len(cA) != nA or len(cB) != nB:
        return INSUFFICIENT_DATA, 0.0, 0, "ARRAY_MISMATCH"
    if nA < bars_back + 1:
        return INSUFFICIENT_DATA, 0.0, 0, "HISTORY_SHORT_A"
    if nB < 2:
        return INSUFFICIENT_DATA, 0.0, 0, "HISTORY_SHORT_B"
    if not _ascending(tA) or not _ascending(tB):
        return INSUFFICIENT_DATA, 0.0, 0, "TIME_NOT_ASCENDING"
    ra, rb, aligned = [0.0] * bars_back, [0.0] * bars_back, 0
    for k in range(nA - bars_back, nA):
        j0, j1 = _find(tB, tA[k - 1]), _find(tB, tA[k])
        if j0 < 0 or j1 < 0:
            continue
        a0, a1, b0, b1 = cA[k - 1], cA[k], cB[j0], cB[j1]
        if not (_finite(a0) and _finite(a1) and _finite(b0) and _finite(b1)) or a0 <= 0 or a1 <= 0 or b0 <= 0 or b1 <= 0:
            continue
        with np.errstate(all="ignore"):
            ra[aligned] = float(np.float64(a1 - a0) / np.float64(a0))
            rb[aligned] = float(np.float64(b1 - b0) / np.float64(b0))
        aligned += 1
    need = math.ceil(min_aligned_frac * bars_back)
    if aligned < need:
        return INSUFFICIENT_DATA, 0.0, aligned, f"ALIGNED_{aligned}_OF_{bars_back}"
    with np.errstate(all="ignore"):
        mean_a = mean_b = np.float64(0.0)
        for i in range(aligned):
            mean_a += ra[i]
            mean_b += rb[i]
        mean_a /= aligned
        mean_b /= aligned
        cov = var_a = var_b = np.float64(0.0)
        for i in range(aligned):
            cov += (ra[i] - mean_a) * (rb[i] - mean_b)
            var_a += (ra[i] - mean_a) * (ra[i] - mean_a)
            var_b += (rb[i] - mean_b) * (rb[i] - mean_b)
        if not (_finite(float(var_a)) and _finite(float(var_b))) or var_a <= 0 or var_b <= 0:
            return INSUFFICIENT_DATA, 0.0, aligned, "ZERO_OR_INVALID_VARIANCE"
        r = float(cov / np.sqrt(var_a * var_b))
    if not _finite(r):
        return INSUFFICIENT_DATA, 0.0, aligned, "NON_FINITE"
    return (BLOCK if abs(r) >= threshold else OK), r, aligned, ""


def cap_ok(states: list[int]) -> bool:
    """CorrelationCapOK: passes only if EVERY other open position is OK."""
    return all(s == OK for s in states)


def legacy_pearson(closeA_by_shift, closeB_by_shift, bars_back: int = BARS_BACK) -> float:
    """The REMOVED shift-aligned PearsonCorrelation (for regression documentation only)."""
    retA, retB, valid = [0.0] * bars_back, [0.0] * bars_back, 0
    for i in range(bars_back):
        a0, a1 = closeA_by_shift[i + 1], closeA_by_shift[i + 2]
        b0, b1 = closeB_by_shift[i + 1], closeB_by_shift[i + 2]
        if a1 <= 0 or b1 <= 0 or a0 <= 0 or b0 <= 0:
            continue
        retA[i], retB[i] = (a0 - a1) / a1, (b0 - b1) / b1
        valid += 1
    if valid < 3:
        return 0.0
    ma, mb = sum(retA) / bars_back, sum(retB) / bars_back
    cov = sum((x - ma) * (y - mb) for x, y in zip(retA, retB, strict=True))
    va = sum((x - ma) ** 2 for x in retA)
    vb = sum((y - mb) ** 2 for y in retB)
    if va <= 0 or vb <= 0:
        return 0.0
    r = cov / math.sqrt(va * vb)
    return r if math.isfinite(r) else 0.0


# ---------------------------------------------------------------- deterministic fixtures

T0 = 1704704400          # 2024-01-08 09:00:00 UTC (arbitrary, fixed)
STEP = 60                # M1


def _pair(n=101, rho_noise=4e-5, seed=0):
    rng = np.random.default_rng(seed)
    common = rng.normal(0, 1e-4, n)
    ra = common + rng.normal(0, rho_noise, n)
    rb = common + rng.normal(0, rho_noise, n)
    ca = 1.10 * np.exp(np.cumsum(ra))
    cb = 1.27 * np.exp(np.cumsum(rb))
    t = [T0 + STEP * i for i in range(n)]
    return t, [round(float(x), 5) for x in ca], list(t), [round(float(x), 5) for x in cb]


def _case(*, tA, cA, tB, cB, expect) -> dict:
    return {"tA": tA, "cA": cA, "tB": tB, "cB": cB, "expect": expect}


def fixtures() -> dict[str, dict]:
    """Named cases: inputs + the fail-closed expectation (state only; corr checked separately)."""
    f: dict[str, dict] = {}
    t, a, tb, b = _pair(seed=1)
    f["valid_aligned_high_corr"] = _case(tA=t, cA=a, tB=tb, cB=b, expect=BLOCK)
    rng = np.random.default_rng(2)
    b_ind = [round(float(x), 5) for x in 1.27 * np.exp(np.cumsum(rng.normal(0, 1e-4, 101)))]
    f["low_corr_pass"] = _case(tA=t, cA=a, tB=tb, cB=b_ind, expect=OK)
    f["negative_high_corr_block"] = _case(tA=t, cA=a, tB=tb, cB=[round(1.27 * 1.10 / x * 1.10, 5) for x in a], expect=BLOCK)
    f["missing_history_empty_B"] = _case(tA=t, cA=a, tB=[], cB=[], expect=INSUFFICIENT_DATA)
    f["missing_history_one_bar_B"] = _case(tA=t, cA=a, tB=tb[:1], cB=b[:1], expect=INSUFFICIENT_DATA)
    f["short_history_A"] = _case(tA=t[:60], cA=a[:60], tB=tb, cB=b, expect=INSUFFICIENT_DATA)
    f["shifted_timestamps_B_30s"] = _case(tA=t, cA=a, tB=[x + 30 for x in tb], cB=b, expect=INSUFFICIENT_DATA)
    # a 15-bar gap in B (e.g. a trading break): old shift code misaligns; new code aligns the rest -> BLOCK
    gap = set(range(40, 55))
    f["gap_15_bars_B_time_aligned"] = _case(tA=t, cA=a, tB=[x for i, x in enumerate(tb) if i not in gap],
                                           cB=[x for i, x in enumerate(b) if i not in gap], expect=BLOCK)
    gap60 = set(range(20, 80))
    f["gap_60_bars_B_insufficient"] = _case(tA=t, cA=a, tB=[x for i, x in enumerate(tb) if i not in gap60],
                                           cB=[x for i, x in enumerate(b) if i not in gap60], expect=INSUFFICIENT_DATA)
    sparse = set(np.random.default_rng(3).choice(np.arange(1, 100), 8, replace=False).tolist())
    f["sparse_missing_8_bars_B"] = _case(tA=t, cA=a, tB=[x for i, x in enumerate(tb) if i not in sparse],
                                        cB=[x for i, x in enumerate(b) if i not in sparse], expect=BLOCK)
    many = set(np.random.default_rng(4).choice(np.arange(1, 100), 20, replace=False).tolist())
    f["sparse_missing_20_bars_B_insufficient"] = _case(tA=t, cA=a, tB=[x for i, x in enumerate(tb) if i not in many],
                                                      cB=[x for i, x in enumerate(b) if i not in many], expect=INSUFFICIENT_DATA)
    # boundary: exactly 80 aligned (pass the sufficiency rule) vs 79 aligned (insufficient)
    t80, t79 = [x for i, x in enumerate(tb) if i < 81], [x for i, x in enumerate(tb) if i < 80]
    f["aligned_exactly_80"] = _case(tA=t, cA=a, tB=t80, cB=b[:81], expect=BLOCK)
    f["aligned_79_insufficient"] = _case(tA=t, cA=a, tB=t79, cB=b[:80], expect=INSUFFICIENT_DATA)
    f["zero_variance_B"] = _case(tA=t, cA=a, tB=tb, cB=[1.27] * 101, expect=INSUFFICIENT_DATA)
    bad = list(b)
    for i in range(0, 101, 4):
        bad[i] = 0.0                                   # unreadable prices (iClose-style 0)
    f["zero_prices_B_insufficient"] = _case(tA=t, cA=a, tB=tb, cB=bad, expect=INSUFFICIENT_DATA)
    nanb = list(b)
    nanb[50] = float("nan")
    f["one_nan_price_B_excluded"] = _case(tA=t, cA=a, tB=tb, cB=nanb, expect=BLOCK)
    infb = list(b)
    infb[10] = 1e308
    infb[11] = 1e-300
    f["non_finite_returns_B"] = _case(tA=t, cA=a, tB=tb, cB=infb, expect=INSUFFICIENT_DATA)
    f["time_not_ascending_B"] = _case(tA=t, cA=a, tB=list(reversed(tb)), cB=list(reversed(b)), expect=INSUFFICIENT_DATA)
    return f


def write_fixtures(path: str) -> None:
    """CSV consumed by the MQL5 harness: case,series,time,close (one row per bar; empty series allowed)."""
    rows = ["case,series,time,close"]
    for name, c in fixtures().items():
        rows.append(f"{name},META,{len(c['tA'])},{len(c['tB'])}")
        rows += [f"{name},A,{t},{x!r}" for t, x in zip(c["tA"], c["cA"], strict=True)]
        rows += [f"{name},B,{t},{x!r}" for t, x in zip(c["tB"], c["cB"], strict=True)]
    with open(path, "w", newline="\n") as fh:
        fh.write("\n".join(rows) + "\n")
