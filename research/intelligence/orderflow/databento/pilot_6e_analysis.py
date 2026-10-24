"""6E pilot (Databento trades, Sep 2026): descriptive measurements for NEXA order-flow research.

No trading rules, no returns, no thresholds chosen to look good. Three questions:
  Q1 Aggregation: how do single fills group into aggressor orders, and how does that change the
     'big trade' size distribution?
  Q2 Roll: where is the 6EU6 -> 6EZ6 switch and how large is the futures-spot gap jump?
  Q3 Level transfer to Pepperstone EURUSD (spot CFD):
     (a) futures-spot basis: level, intra-session stability, day-to-day drift;
     (b) error of converting futures levels to spot with (i) the same-session median basis (ideal)
         and (ii) the prior session's closing basis (what NEXA could do without a live futures feed);
     (c) value-area agreement: P1 futures trade prices x real volume (truth),
         P2 futures M1 typical price x real volume (M1 approximation),
         P3 Pepperstone M1 typical price x tick volume (NEXA proxy, OF-03P), aligned by basis.

Inputs : data/GLBX.MDP3_trades_6E.v.0_2026-09-01_2026-10-01.dbn.zst (Databento, purchased 2026-10-11)
         Pepperstone EURUSD M1 via validation/of_common.load (read-only; data ends 2026-09-25)
Output : pilot_6e_results.json (this folder)
Clock  : Pepperstone server time = New York local + 7 h; server day == CME Globex trading day (17:00 NY start).
Value area: of_common.va_greedy (70 %, two-bin greedy), 1-pip bins (0.0001), identical to OF tests.
Assumption: Pepperstone M1 OHLC are bid prices; spot mid = bid + spread/2.
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

FILE = HERE / "data" / "GLBX.MDP3_trades_6E.v.0_2026-09-01_2026-10-01.dbn.zst"
PIP = 1e-4
W = oc.BINW["EURUSD"]          # 1 pip bins
F_LAST = 0x80
CONTRACT = {10573: "6EU6", 5510: "6EZ6"}
SIZE_T = (25, 50, 100)


def q(x, ps=(5, 25, 50, 75, 95)):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return {f"p{p}": round(float(np.percentile(x, p)), 3) for p in ps} | {"n": int(len(x))} if len(x) else {"n": 0}


def to_server(ts_utc: pd.Series) -> pd.Series:
    return ts_utc.dt.tz_convert("America/New_York").dt.tz_localize(None) + pd.Timedelta(hours=7)


# ------------------------------------------------------------------ load futures
df = db.DBNStore.from_file(FILE).to_df().reset_index()
df["ts_event"] = pd.to_datetime(df["ts_event"], utc=True)
df = df.sort_values(["ts_event", "sequence"], kind="stable").reset_index(drop=True)
srv = to_server(df["ts_event"])
df["sday"] = srv.dt.strftime("%Y-%m-%d")
df["smin"] = ((srv - srv.dt.normalize()) // pd.Timedelta(minutes=1)).astype(int)
out: dict = {"file": FILE.name, "records": int(len(df))}

# ------------------------------------------------------------------ Q1 aggregation
size = df["size"].to_numpy()
# Method A: same instrument, same matching-engine timestamp, same aggressor side
ga = df.groupby(["instrument_id", "ts_event", "side"], sort=False).agg(
    size=("size", "sum"), n=("size", "size"), pmin=("price", "min"), pmax=("price", "max"))
# Method B: runs ending at a record carrying F_LAST
last = (df["flags"].to_numpy() & F_LAST) > 0
gid = np.r_[0, np.cumsum(last[:-1])]
gb = df.assign(g=gid).groupby("g", sort=False).agg(size=("size", "sum"), n=("size", "size"),
                                                   nside=("side", "nunique"), nts=("ts_event", "nunique"))


def size_profile(s: np.ndarray) -> dict:
    tot = s.sum()
    d = {"count": int(len(s)), "quantiles": {k: int(v) for k, v in
                                            zip(("p50", "p90", "p95", "p99", "p99.9"), np.percentile(s, [50, 90, 95, 99, 99.9]))},
         "max": int(s.max())}
    for t in SIZE_T:
        m = s >= t
        d[f">={t}"] = {"count": int(m.sum()), "pct_events": round(100 * m.mean(), 3),
                       "pct_volume": round(100 * s[m].sum() / tot, 2)}
    return d


out["Q1_aggregation"] = {
    "single_prints": size_profile(size),
    "A_ts_event_side": size_profile(ga["size"].to_numpy()) | {
        "multi_fill_orders_pct": round(100 * float((ga["n"] > 1).mean()), 2),
        "multi_level_orders_pct": round(100 * float((ga["pmax"] > ga["pmin"]).mean()), 3)},
    "B_flag_last_runs": size_profile(gb["size"].to_numpy()) | {
        "runs_with_mixed_side_pct": round(100 * float((gb["nside"] > 1).mean()), 3),
        "runs_with_mixed_ts_pct": round(100 * float((gb["nts"] > 1).mean()), 3)},
    "groups_A_vs_B": [int(len(ga)), int(len(gb))],
    "side_N_pct_records": round(100 * float((df["side"] == "N").mean()), 3),
}

# ------------------------------------------------------------------ futures per minute
fm = df.groupby(["sday", "smin"], sort=True).agg(
    instr=("instrument_id", "last"), c=("price", "last"), h=("price", "max"), l=("price", "min"),
    v=("size", "sum")).reset_index()
nmin = fm.groupby("sday").size()
med_min = float(nmin.median())
dom = df.groupby("sday")["instrument_id"].agg(lambda s: s.value_counts().idxmax())
out["Q2_roll"] = {"sessions": {d: {"contract": CONTRACT.get(int(dom[d]), str(dom[d])), "minutes": int(nmin[d])}
                               for d in nmin.index},
                  "median_minutes_per_session": med_min}

# ------------------------------------------------------------------ Pepperstone EURUSD
S = oc.load("EURUSD")
pday = {d: i for i, d in enumerate(S.days)}
sessions = [d for d in nmin.index
            if d in pday and d > "2026-09-01"          # Sep 1 session starts before the file (00:00 UTC)
            and nmin[d] >= 0.8 * med_min and bool(S.valid[pday[d]])]
excluded = sorted(set(nmin.index) - set(sessions))
out["sessions_used"] = sessions
out["sessions_excluded"] = {d: ("after Pepperstone data end" if d not in pday else
                                "partial (file starts 00:00 UTC)" if d <= "2026-09-01" else
                                "thin futures session" if nmin[d] < 0.8 * med_min else "Pepperstone invalid/thin")
                            for d in excluded}

rows, va_rows = [], []
for d in sessions:
    i = pday[d]
    sl = S.bars(i)
    sp = pd.DataFrame({"smin": S.smin[sl], "h": S.h[sl], "l": S.l[sl], "c": S.c[sl], "tv": S.tv[sl], "spr": S.spr[sl]})
    sp["mid"] = sp["c"] + sp["spr"] / 2
    f = fm[fm["sday"] == d]
    m = f.merge(sp, on="smin", suffixes=("_f", "_s"))
    basis = (m["c_f"] - m["mid"]).to_numpy() / PIP
    med = float(np.median(basis))
    tail = m["smin"] >= m["smin"].max() - 60
    rows.append({"day": d, "contract": CONTRACT.get(int(dom[d])), "common_min": int(len(m)),
                 "basis_med": med, "basis_close60": float(np.median(basis[tail.to_numpy()])),
                 "dev_abs": np.abs(basis - med), "basis": basis, "smin": m["smin"].to_numpy()})

    # ---- value areas
    tr = df[df["sday"] == d]
    k = np.floor(tr["price"].to_numpy() / W + 1e-9).astype(np.int64)
    k0 = int(k.min())
    v1 = np.bincount(k - k0, weights=tr["size"].to_numpy(float))
    poc, lo, hi = oc.va_greedy(v1)
    P1 = ((k0 + lo) * W, (k0 + hi + 1) * W, (k0 + poc + 0.5) * W)
    P2 = oc.value_area(f["h"].to_numpy(), f["l"].to_numpy(), f["c"].to_numpy(), f["v"].to_numpy(float), W)
    P3 = oc.value_area(sp["h"].to_numpy(), sp["l"].to_numpy(), sp["c"].to_numpy(), sp["tv"].to_numpy(float), W)
    # P3 is on bid prices; shift to mid with the session median spread, then to futures space with basis
    half = float(np.median(sp["spr"])) / 2
    P3f = tuple(x + half + med * PIP for x in P3)
    # profile-shape agreement: futures true profile vs spot tick-volume profile, basis-aligned, 1-pip bins
    tp = (sp["h"] + sp["l"] + sp["c"]) / 3 + half + med * PIP
    ks = np.floor(tp.to_numpy() / W + 1e-9).astype(np.int64)
    lo_k, hi_k = min(k0, ks.min()), max(k.max(), ks.max())
    a = np.bincount(k - lo_k, weights=tr["size"].to_numpy(float), minlength=hi_k - lo_k + 1)
    b = np.bincount(ks - lo_k, weights=sp["tv"].to_numpy(float), minlength=hi_k - lo_k + 1)
    rho = float(np.corrcoef(pd.Series(a).rank().to_numpy(), pd.Series(b).rank().to_numpy())[0, 1])  # Spearman = Pearson on ranks
    pear = float(np.corrcoef(a, b)[0, 1])
    va_rows.append({"day": d, "va_width_P1_pips": (P1[1] - P1[0]) / PIP,
                    **{f"{lab}_{nm}": (Px[j] - P1[j]) / PIP for lab, Px in (("P2", P2), ("P3", P3f))
                       for j, nm in enumerate(("VAL", "VAH", "POC"))},
                    "shape_spearman": rho, "shape_pearson": pear})

# ------------------------------------------------------------------ Q3 summaries
R = pd.DataFrame([{k: v for k, v in r.items() if k not in ("dev_abs", "basis", "smin")} for r in rows])
out["Q3a_basis_by_session"] = R.round(3).to_dict("records")
dev_all = np.concatenate([r["dev_abs"] for r in rows])
out["Q3b_error_same_session_median_pips"] = q(dev_all, (50, 75, 90, 95, 99))
# prior-session closing basis, same contract only (roll day not measurable with a v.0 file)
e2, e2_days, jumps = [], [], []
for prev, cur in zip(rows[:-1], rows[1:]):
    if prev["contract"] != cur["contract"]:
        jumps.append({"from": prev["day"], "to": cur["day"], "contracts": f"{prev['contract']}->{cur['contract']}",
                      "basis_med_change_pips": round(cur["basis_med"] - prev["basis_med"], 2)})
        continue
    err = np.abs(cur["basis"] - prev["basis_close60"])
    e2.append(err)
    e2_days.append({"day": cur["day"], "median_err": round(float(np.median(err)), 3),
                    "p95_err": round(float(np.percentile(err, 95)), 3),
                    "basis_med_change": round(cur["basis_med"] - prev["basis_med"], 3)})
out["Q3b_error_prior_close_basis_pips"] = q(np.concatenate(e2), (50, 75, 90, 95, 99)) | {"by_day": e2_days}
out["Q2_roll"]["basis_jump_at_roll"] = jumps
same = [x["basis_med_change"] for x in e2_days]
out["Q3a_day_to_day_basis_change_pips"] = q(same, (5, 25, 50, 75, 95))
V = pd.DataFrame(va_rows)
out["Q3c_value_area_vs_truth_pips"] = {c: q(V[c], (5, 25, 50, 75, 95)) for c in V.columns if c != "day"}
out["Q3c_abs_error_pips"] = {c: q(V[c].abs(), (50, 75, 90)) for c in V.columns
                             if c.startswith(("P2_", "P3_"))}
out["Q3c_by_session"] = V.round(2).to_dict("records")

(HERE / "pilot_6e_results.json").write_text(json.dumps(out, indent=1, default=float))
print(json.dumps({k: out[k] for k in ("Q1_aggregation",)}, indent=1))
print("sessions used:", len(sessions), "| excluded:", out["sessions_excluded"])
print("roll:", jumps)
print("basis by session (pips):", R[["day", "contract", "common_min", "basis_med", "basis_close60"]].round(2).to_string(index=False))
print("Q3b same-session median basis error:", out["Q3b_error_same_session_median_pips"])
print("Q3b prior-close basis error:", {k: v for k, v in out["Q3b_error_prior_close_basis_pips"].items() if k != "by_day"})
print("day-to-day basis change:", out["Q3a_day_to_day_basis_change_pips"])
print("VA vs truth (signed):"); [print("  ", c, out["Q3c_value_area_vs_truth_pips"][c]) for c in V.columns if c != "day"]
print("VA abs error:"); [print("  ", c, v) for c, v in out["Q3c_abs_error_pips"].items()]
