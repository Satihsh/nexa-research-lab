"""E2 / E9 decision support on 6E: COUNTS ONLY (no prices after events, no outcomes, no returns).

Decided inputs (CORE_STRATEGY_SPEC, user 2026-10-11):
  value   = prior NY block (08:30-17:00 NY) volume profile, 1-pip rows, 70 % VA (of_common.va_greedy)   [E1]
  big     = big_trades.py (q99, 60 prior sessions, per block)                                          [E3]
  mirrors = included: seller big trade near VAL (Setup A/B) and buyer big trade near VAH (mirrors)      [E10]
E2 count : big orders with |order price - edge| <= f x VA width, f in {5,10,15,20,25 %}, per session and
           block of the next server day (the whole day after the profile completes; trading window not yet
           decided). Sessions whose prior profile is on a different contract (roll) are skipped.
E9 count : LVNs per prior-NY profile. Valley = local minimum of the k-row centred moving average
           (k in {1,3,5}); depth ratio = valley / min(highest smoothed row left, highest right);
           LVN if ratio <= d, d in {0.3, 0.5, 0.7}. Plus the TradeDevils double-distribution rule
           (trough <= 45 % of POC between peaks >= 65 % of POC, peaks >= 3 rows apart; k = 1).
           Reported: LVNs per profile, and share of sessions with >= 1 LVN below VAL / above VAH
           (Setup B and mirror targets need one).
Output: e2_e9_counts.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import databento as db

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "validation"))
import big_trades as bt  # noqa: E402
import of_common as oc   # noqa: E402

W = 1e-4
FRACS = (0.05, 0.10, 0.15, 0.20, 0.25)
KS = (1, 3, 5)
DS = (0.3, 0.5, 0.7)

files = sorted((HERE / "data").glob("GLBX.MDP3_trades_6E.v.0_*.dbn.zst"))
tr = pd.concat([db.DBNStore.from_file(f).to_df().reset_index()[["ts_event", "instrument_id", "side", "size", "price"]]
                for f in files], ignore_index=True)
tr["ts_event"] = pd.to_datetime(tr["ts_event"], utc=True)
tr["block"] = bt.session_block(tr["ts_event"])
srv = tr["ts_event"].dt.tz_convert("America/New_York").dt.tz_localize(None) + pd.Timedelta(hours=7)
tr["sday"] = srv.dt.strftime("%Y-%m-%d")
del srv

o = tr.groupby(["instrument_id", "ts_event", "side"], sort=False).agg(size=("size", "sum"), pmin=("price", "min"),
                                                                     pmax=("price", "max")).reset_index()
s2 = o["ts_event"].dt.tz_convert("America/New_York").dt.tz_localize(None) + pd.Timedelta(hours=7)
o["sday"] = s2.dt.strftime("%Y-%m-%d")
o["block"] = bt.session_block(o["ts_event"])
degraded = {d for d, _ in json.loads((HERE / "dataset_condition_2025-09_2026-09.json").read_text())}
touch = degraded | {(pd.Timestamp(d) + pd.Timedelta(days=1)).strftime("%Y-%m-%d") for d in degraded}
nmin = tr.assign(m=tr["ts_event"].dt.floor("min")).groupby("sday")["m"].nunique()
days = sorted(nmin.index)
sessions = [d for d in days[1:] if nmin[d] >= 0.8 * nmin.median() and d not in touch]
o = o[o["sday"].isin(sessions)]
sizes = {k: g["size"].to_numpy() for k, g in o.groupby(["sday", "block"])}
T = bt.thresholds(sizes, sessions)
dom = tr.groupby("sday")["instrument_id"].agg(lambda s: s.value_counts().idxmax())

# prior-NY profiles
ny = tr[tr["block"] == "NY"]
prof = {}
for d, g in ny.groupby("sday"):
    k = np.floor(g["price"].to_numpy() / W + 1e-9).astype(np.int64)
    k0 = int(k.min())
    v = np.bincount(k - k0, weights=g["size"].to_numpy(float))
    poc, lo, hi = oc.va_greedy(v)
    prof[d] = {"v": v, "k0": k0, "VAL": (k0 + lo) * W, "VAH": (k0 + hi + 1) * W, "lo": lo, "hi": hi, "poc": poc,
               "instr": int(g["instrument_id"].value_counts().idxmax())}


def lvns(v: np.ndarray, k: int, d: float) -> list:
    s = np.convolve(v, np.ones(k) / k, mode="same") if k > 1 else v.astype(float)
    out = []
    for i in range(1, len(s) - 1):
        if s[i] < s[i - 1] and s[i] <= s[i + 1]:
            lp, rp = s[:i].max(), s[i + 1:].max()
            if s[i] <= d * min(lp, rp):
                out.append(i)
    return out


def lvns_tradedevils(v: np.ndarray, poc: int) -> list:
    P = v[poc]
    peaks = np.where(v >= 0.65 * P)[0]
    out = []
    for i in range(1, len(v) - 1):
        if v[i] <= 0.45 * P and v[i] < v[i - 1] and v[i] <= v[i + 1]:
            L, R = peaks[peaks < i], peaks[peaks > i]
            if len(L) and len(R) and (R.min() - L.max()) >= 3:
                out.append(i)
    return out


scored = [d for d in sessions if (d, "NY") in T]
pairs = []
for d in scored:
    j = sessions.index(d)
    prev = sessions[j - 1] if j else None
    if prev is None or prev not in prof or prof[prev]["instr"] != int(dom[d]):
        continue
    pairs.append((prev, d))

# ---- E2 counts
e2 = {f: {"A_near_VAL": [], "M_near_VAH": [], "by_block": {b: 0 for b in bt.BLOCKS}} for f in FRACS}
og = {k: g for k, g in o.groupby("sday")}
for prev, d in pairs:
    P = prof[prev]
    wv = P["VAH"] - P["VAL"]
    g = og.get(d)
    if g is None:
        continue
    thr = g["block"].map(lambda b: T.get((d, b), np.inf)).to_numpy()
    big = g[g["size"].to_numpy() >= thr]
    sell, buy = big[big["side"] == "A"], big[big["side"] == "B"]
    for f in FRACS:
        a = sell[(sell["pmin"] - P["VAL"]).abs() <= f * wv]
        m = buy[(buy["pmax"] - P["VAH"]).abs() <= f * wv]
        e2[f]["A_near_VAL"].append(len(a)); e2[f]["M_near_VAH"].append(len(m))
        for b, n in pd.concat([a, m])["block"].value_counts().items():
            e2[f]["by_block"][b] += int(n)


def summ(x):
    x = np.asarray(x)
    return {"mean_per_session": round(float(x.mean()), 2), "median": float(np.median(x)),
            "sessions_with_>=1_pct": round(100 * float((x > 0).mean()), 1)}


out = {"sessions_scored": len(pairs), "va_width_pips_median": float(np.median([(prof[p]["VAH"] - prof[p]["VAL"]) / W for p, _ in pairs])),
       "E2": {f"{int(f*100)}%": {"seller_big_near_VAL": summ(v["A_near_VAL"]), "buyer_big_near_VAH": summ(v["M_near_VAH"]),
                                 "events_by_block": v["by_block"]} for f, v in e2.items()}}
# ---- E9 counts
e9 = {}
profiles = [prof[p] for p, _ in pairs]
for k in KS:
    for dd in DS:
        n, below, above = [], [], []
        for P in profiles:
            L = lvns(P["v"], k, dd)
            n.append(len(L)); below.append(any(i < P["lo"] for i in L)); above.append(any(i > P["hi"] for i in L))
        e9[f"k{k}_d{dd}"] = {"lvns_per_profile_median": float(np.median(n)), "lvns_per_profile_p90": float(np.percentile(n, 90)),
                             "pct_sessions_LVN_below_VAL": round(100 * np.mean(below), 1),
                             "pct_sessions_LVN_above_VAH": round(100 * np.mean(above), 1)}
n, below, above = [], [], []
for P in profiles:
    L = lvns_tradedevils(P["v"], P["poc"])
    n.append(len(L)); below.append(any(i < P["lo"] for i in L)); above.append(any(i > P["hi"] for i in L))
e9["tradedevils"] = {"lvns_per_profile_median": float(np.median(n)), "lvns_per_profile_p90": float(np.percentile(n, 90)),
                     "pct_sessions_LVN_below_VAL": round(100 * np.mean(below), 1),
                     "pct_sessions_LVN_above_VAH": round(100 * np.mean(above), 1)}
out["E9"] = e9
out["profile_rows_median"] = float(np.median([len(P["v"]) for P in profiles]))
(HERE / "e2_e9_counts.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
