"""6E 13-month extension (Databento trades 2025-09-01 -> 2026-10-01) of pilot_6e_analysis.py.

Same definitions as the pilot (see that docstring); descriptive only, no trading rules or returns.
Additions: all 6E files in data/, every quarterly roll, per-quarter breakdowns (stability check).
Sessions: CME trading day == Pepperstone server day; first session of the data, thin sessions
(< 80 % of median futures minutes), Pepperstone-invalid days and days after 2026-09-25 are excluded.
Output: year_6e_results.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "validation"))
import of_common as oc  # noqa: E402  (read-only use)
import databento as db  # noqa: E402

FILES = sorted((HERE / "data").glob("GLBX.MDP3_trades_6E.v.0_*.dbn.zst"))
PIP = 1e-4
W = oc.BINW["EURUSD"]
CONTRACT = {3624: "6EU5", 4274: "6EZ5", 57062: "6EH6", 20048: "6EM6", 10573: "6EU6", 5510: "6EZ6"}  # free symbology 2026-10-11
SIZE_T = (25, 50, 100)


def q(x, ps=(5, 25, 50, 75, 95)):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return ({f"p{p}": round(float(np.percentile(x, p)), 3) for p in ps} | {"n": int(len(x))}) if len(x) else {"n": 0}


def quarter(day: str) -> str:
    t = pd.Timestamp(day)
    return f"{t.year}Q{(t.month - 1) // 3 + 1}"


def size_profile(s: np.ndarray) -> dict:
    tot = s.sum()
    d = {"count": int(len(s)), "max": int(s.max()),
         "quantiles": {k: int(v) for k, v in zip(("p50", "p90", "p95", "p99", "p99.9"),
                                                 np.percentile(s, [50, 90, 95, 99, 99.9]))}}
    for t in SIZE_T:
        m = s >= t
        d[f">={t}"] = {"pct_events": round(100 * m.mean(), 3), "pct_volume": round(100 * s[m].sum() / tot, 2)}
    return d


# ------------------------------------------------------------------ load
parts = [db.DBNStore.from_file(f).to_df().reset_index() for f in FILES]
df = pd.concat(parts, ignore_index=True)
del parts
df["ts_event"] = pd.to_datetime(df["ts_event"], utc=True)
df = df.drop_duplicates(["ts_event", "sequence", "instrument_id", "price", "size", "side"])
df = df.sort_values(["ts_event", "sequence"], kind="stable").reset_index(drop=True)
srv = df["ts_event"].dt.tz_convert("America/New_York").dt.tz_localize(None) + pd.Timedelta(hours=7)
df["sday"] = srv.dt.strftime("%Y-%m-%d")
df["smin"] = ((srv - srv.dt.normalize()) // pd.Timedelta(minutes=1)).astype(np.int32)
del srv
out: dict = {"files": [f.name for f in FILES], "records": int(len(df)),
             "range_utc": [str(df["ts_event"].min()), str(df["ts_event"].max())],
             "side_N_pct": round(100 * float((df["side"] == "N").mean()), 3)}

# ------------------------------------------------------------------ Q1 aggressor orders (timestamp + side)
ga = df.groupby(["instrument_id", "ts_event", "side"], sort=False)["size"].sum()
out["Q1_single_prints"] = size_profile(df["size"].to_numpy())
out["Q1_aggressor_orders"] = size_profile(ga.to_numpy())
gq = ga.reset_index()
gq["qtr"] = gq["ts_event"].dt.tz_convert("America/New_York").dt.strftime("%Y-%m").map(lambda s: quarter(s + "-01"))
out["Q1_aggressor_orders_by_quarter"] = {k: size_profile(v["size"].to_numpy()) for k, v in gq.groupby("qtr")}
del ga, gq

# ------------------------------------------------------------------ per-minute futures, sessions
fm = df.groupby(["sday", "smin"], sort=True).agg(c=("price", "last"), h=("price", "max"), l=("price", "min"),
                                                v=("size", "sum")).reset_index()
nmin = fm.groupby("sday").size()
med_min = float(nmin.median())
dom = df.groupby("sday")["instrument_id"].agg(lambda s: s.value_counts().idxmax())
S = oc.load("EURUSD")
pday = {d: i for i, d in enumerate(S.days)}
first = nmin.index.min()
# Databento 'degraded' UTC dates (metadata.get_dataset_condition); server day d spans UTC dates d-1 and d
degraded = {d for d, _ in json.loads((HERE / "dataset_condition_2025-09_2026-09.json").read_text())}
touch = degraded | {(pd.Timestamp(d) + pd.Timedelta(days=1)).strftime("%Y-%m-%d") for d in degraded}
sessions = [d for d in nmin.index if d != first and d in pday and nmin[d] >= 0.8 * med_min and bool(S.valid[pday[d]])
            and d not in touch]
out["sessions_used"] = len(sessions)
out["sessions_excluded"] = {d: ("first (partial)" if d == first else "after Pepperstone end" if d not in pday else
                                "thin futures" if nmin[d] < 0.8 * med_min else
                                "Databento degraded" if d in touch else "Pepperstone invalid")
                            for d in sorted(set(nmin.index) - set(sessions))}
tr_idx = df.groupby("sday").indices
fm_idx = fm.groupby("sday").indices
price = df["price"].to_numpy()
size = df["size"].to_numpy(float)

rows, va_rows = [], []
for d in sessions:
    i = pday[d]
    sl = S.bars(i)
    sp = pd.DataFrame({"smin": S.smin[sl], "h": S.h[sl], "l": S.l[sl], "c": S.c[sl], "tv": S.tv[sl], "spr": S.spr[sl]})
    sp["mid"] = sp["c"] + sp["spr"] / 2
    f = fm.iloc[fm_idx[d]]
    m = f.merge(sp, on="smin", suffixes=("_f", "_s"))
    if len(m) < 0.5 * med_min:
        continue
    basis = (m["c_f"] - m["mid"]).to_numpy() / PIP
    med = float(np.median(basis))
    tail = (m["smin"] >= m["smin"].max() - 60).to_numpy()
    rows.append({"day": d, "q": quarter(d), "contract": CONTRACT.get(int(dom[d]), str(dom[d])), "common_min": int(len(m)),
                 "basis_med": med, "basis_close60": float(np.median(basis[tail])), "basis": basis,
                 "dev_abs": np.abs(basis - med)})
    ti = tr_idx[d]
    k = np.floor(price[ti] / W + 1e-9).astype(np.int64)
    k0 = int(k.min())
    poc, lo, hi = oc.va_greedy(np.bincount(k - k0, weights=size[ti]))
    P1 = ((k0 + lo) * W, (k0 + hi + 1) * W, (k0 + poc + 0.5) * W)
    P2 = oc.value_area(f["h"].to_numpy(), f["l"].to_numpy(), f["c"].to_numpy(), f["v"].to_numpy(float), W)
    P3 = oc.value_area(sp["h"].to_numpy(), sp["l"].to_numpy(), sp["c"].to_numpy(), sp["tv"].to_numpy(float), W)
    half = float(np.median(sp["spr"])) / 2
    P3f = tuple(x + half + med * PIP for x in P3)
    tp = (sp["h"] + sp["l"] + sp["c"]).to_numpy() / 3 + half + med * PIP
    ks = np.floor(tp / W + 1e-9).astype(np.int64)
    lo_k, hi_k = min(k0, int(ks.min())), max(int(k.max()), int(ks.max()))
    a = np.bincount(k - lo_k, weights=size[ti], minlength=hi_k - lo_k + 1)
    b = np.bincount(ks - lo_k, weights=sp["tv"].to_numpy(float), minlength=hi_k - lo_k + 1)
    rho = float(np.corrcoef(pd.Series(a).rank().to_numpy(), pd.Series(b).rank().to_numpy())[0, 1])
    va_rows.append({"day": d, "q": quarter(d), "va_width_P1": (P1[1] - P1[0]) / PIP,
                    **{f"{lab}_{nm}": (Px[j] - P1[j]) / PIP for lab, Px in (("P2", P2), ("P3", P3f))
                       for j, nm in enumerate(("VAL", "VAH", "POC"))},
                    "shape_spearman": rho})

# ------------------------------------------------------------------ summaries
out["Q3b_same_session_median_err"] = q(np.concatenate([r["dev_abs"] for r in rows]), (50, 90, 95, 99))
e2, e2q, jumps, dchg = [], {}, [], []
for prev, cur in zip(rows[:-1], rows[1:]):
    if prev["contract"] != cur["contract"]:
        jumps.append({"to": cur["day"], "roll": f"{prev['contract']}->{cur['contract']}",
                      "basis_jump": round(cur["basis_med"] - prev["basis_med"], 2)})
        continue
    err = np.abs(cur["basis"] - prev["basis_close60"])
    e2.append(err)
    e2q.setdefault(cur["q"], []).append(err)
    dchg.append(cur["basis_med"] - prev["basis_med"])
out["Q2_rolls"] = jumps
out["Q3b_prior_close_err"] = q(np.concatenate(e2), (50, 90, 95, 99))
out["Q3b_prior_close_err_by_quarter"] = {k: q(np.concatenate(v), (50, 95)) for k, v in sorted(e2q.items())}
out["Q3a_day_to_day_basis_change"] = q(dchg, (5, 25, 50, 75, 95))
out["Q3a_basis_level_by_contract"] = {c: q([r["basis_med"] for r in rows if r["contract"] == c], (5, 50, 95))
                                      for c in dict.fromkeys(r["contract"] for r in rows)}
V = pd.DataFrame(va_rows)
cols = [c for c in V.columns if c.startswith(("P2_", "P3_"))]
out["Q3c_abs_err"] = {c: q(V[c].abs(), (50, 75, 90)) for c in cols}
out["Q3c_signed"] = {c: q(V[c], (25, 50, 75)) for c in cols}
out["Q3c_va_width"] = q(V["va_width_P1"], (5, 50, 95))
out["Q3c_shape_spearman"] = q(V["shape_spearman"], (5, 25, 50, 75, 95))
out["Q3c_by_quarter"] = {k: {"n": int(len(g)), "va_width_p50": float(g["va_width_P1"].median()),
                             "spearman_p50": round(float(g["shape_spearman"].median()), 3),
                             **{f"|{c}|_p50": round(float(g[c].abs().median()), 2) for c in cols}}
                         for k, g in V.groupby("q")}
(HERE / "year_6e_results.json").write_text(json.dumps(out, indent=1, default=float))
print(json.dumps({k: v for k, v in out.items() if k not in ("sessions_excluded",)}, indent=1, default=float))
print("excluded:", out["sessions_excluded"])
