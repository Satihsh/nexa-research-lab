"""E3 decision support: behaviour of RELATIVE big-trade thresholds on 13 months of 6E (descriptive only).

User decision 2026-10-11: big trades use a relative threshold. Its parameters are NOT chosen here;
this script only shows how candidate settings behave, for the user to pick.
  unit      : aggressor order = trades aggregated by (instrument, ts_event, side) [as measured, CL-104]
  threshold : T_d = ceil(q-th percentile of aggressor-order sizes over the prior L sessions) (no look-ahead)
  big       : order size >= T_d in session d
  grid      : q in {99, 99.5, 99.9}, L in {20, 60}; fixed 25 lots shown for comparison
  sessions  : CME day == server day (NY + 7 h); excludes first session, thin (< 80 % median minutes)
              and Databento-degraded sessions (same rules as year_6e_analysis.py)
Reports per setting: lot threshold over time, realized share of orders/volume flagged per session,
and where in the day flagged orders occur (NY-time blocks).
Output: relative_threshold_options.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import databento as db

HERE = Path(__file__).resolve().parent
FILES = sorted((HERE / "data").glob("GLBX.MDP3_trades_6E.v.0_*.dbn.zst"))
QS = (99.0, 99.5, 99.9)
LS = (20, 60)
FIXED = 25

df = pd.concat([db.DBNStore.from_file(f).to_df().reset_index()[["ts_event", "instrument_id", "side", "size"]]
                for f in FILES], ignore_index=True)
df["ts_event"] = pd.to_datetime(df["ts_event"], utc=True)
o = df.groupby(["instrument_id", "ts_event", "side"], sort=False)["size"].sum().reset_index()
del df
ny = o["ts_event"].dt.tz_convert("America/New_York").dt.tz_localize(None)
srv = ny + pd.Timedelta(hours=7)
o["sday"] = srv.dt.strftime("%Y-%m-%d")
h = ny.dt.hour
o["block"] = np.select([(h >= 18) | (h < 3), (h >= 3) & (h < 8), (h >= 8) & (h < 12)],
                       ["Asia 18-03 NY", "London 03-08 NY", "NY am 08-12"], "NY pm 12-17")
o["min"] = srv.dt.floor("min")

degraded = {d for d, _ in json.loads((HERE / "dataset_condition_2025-09_2026-09.json").read_text())}
touch = degraded | {(pd.Timestamp(d) + pd.Timedelta(days=1)).strftime("%Y-%m-%d") for d in degraded}
nmin = o.groupby("sday")["min"].nunique()
days = sorted(nmin.index)
keep = [d for d in days[1:] if nmin[d] >= 0.8 * nmin.median() and d not in touch]
o = o[o["sday"].isin(keep)]
sizes = {d: g["size"].to_numpy() for d, g in o.groupby("sday")}
blocks = {d: g["block"].to_numpy() for d, g in o.groupby("sday")}


def q(x, ps=(5, 50, 95)):
    x = np.asarray(x, float)
    return {f"p{p}": round(float(np.percentile(x, p)), 3) for p in ps}


out = {"sessions": len(keep), "orders": int(len(o)), "settings": {}}
block_names = ["Asia 18-03 NY", "London 03-08 NY", "NY am 08-12", "NY pm 12-17"]
base_mix = o["block"].value_counts(normalize=True).reindex(block_names).round(4).to_dict()
out["all_orders_by_block"] = base_mix
for L in LS:
    for qq in QS:
        thr, share_o, share_v, mix = [], [], [], {b: 0 for b in block_names}
        for j in range(L, len(keep)):
            hist = np.concatenate([sizes[keep[k]] for k in range(j - L, j)])
            T = int(np.ceil(np.percentile(hist, qq)))
            s = sizes[keep[j]]
            m = s >= T
            thr.append(T); share_o.append(100 * m.mean()); share_v.append(100 * s[m].sum() / s.sum())
            for b, n in zip(*np.unique(blocks[keep[j]][m], return_counts=True)):
                mix[b] += int(n)
        tot = sum(mix.values())
        out["settings"][f"q{qq}_L{L}"] = {
            "sessions_scored": len(thr), "threshold_lots": q(thr, (0, 5, 50, 95, 100)),
            "pct_orders_flagged_per_session": q(share_o), "pct_volume_flagged_per_session": q(share_v),
            "flagged_by_block": {b: round(mix[b] / tot, 4) for b in block_names}}
# fixed threshold over the same scored sessions (L=20 window) for comparison
fo = [100 * (sizes[d] >= FIXED).mean() for d in keep[20:]]
fv = [100 * sizes[d][sizes[d] >= FIXED].sum() / sizes[d].sum() for d in keep[20:]]
out["settings"][f"fixed_{FIXED}"] = {"sessions_scored": len(fo), "pct_orders_flagged_per_session": q(fo),
                                     "pct_volume_flagged_per_session": q(fv)}
(HERE / "relative_threshold_options.json").write_text(json.dumps(out, indent=1))
print("sessions", out["sessions"], "orders", f"{out['orders']:,}", "| all orders by block", base_mix)
for k, v in out["settings"].items():
    print(f"{k:12s} thr={v.get('threshold_lots', '-')}  orders%={v['pct_orders_flagged_per_session']}  "
          f"vol%={v['pct_volume_flagged_per_session']}  blocks={v.get('flagged_by_block', '-')}")
