"""Big-trade definition for NEXA order-flow research (E3, user decisions 2026-10-11). Research code only.

Definition (each element user-decided unless marked):
  unit       aggressor order = 6E trades aggregated by (instrument_id, ts_event, side)       [measured, CL-104]
  relative   threshold relative to recent activity, not a fixed lot size                    [user]
  percentile q = 99 (top 1 %)                                                                [user]
  lookback   L = 60 prior sessions (no look-ahead; the current session is never used)       [user]
  blocks     separate threshold per session block                                           [user]
             Asia   = CME open (18:00 NY) .. 08:00 London   boundaries reuse the frozen NEXA
             London = 08:00 London .. 08:30 NY              OF anchors A1/A2 (PREREG_OF_COMMON
             NY     = 08:30 NY .. 17:00 NY                  section C3), local clocks, DST-aware
  big        order size >= ceil(q-th percentile of that block's orders over the prior L sessions)
Sessions: CME trading day == server day (NY + 7 h). Thin (< 80 % median minutes) and Databento-degraded
sessions are excluded from both history and scoring.

Run directly to measure the definition on the data in ./data -> big_trades_definition.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

Q = 99.0
L = 60
BLOCKS = ("Asia", "London", "NY")


def session_block(ts_utc: pd.Series) -> np.ndarray:
    """Asia / London / NY per timestamp (A1 = 08:00 London, A2 = 08:30 NY); local clocks handle DST."""
    ny = ts_utc.dt.tz_convert("America/New_York")
    ldn = ts_utc.dt.tz_convert("Europe/London")
    ny_min = ny.dt.hour * 60 + ny.dt.minute
    ldn_min = ldn.dt.hour * 60 + ldn.dt.minute
    asia = (ny_min >= 17 * 60) | (ldn_min < 8 * 60)          # 17:00 NY server-day start (CME opens 18:00)
    london = ~asia & (ny_min < 8 * 60 + 30)
    return np.where(asia, "Asia", np.where(london, "London", "NY"))


def aggressor_orders(trades: pd.DataFrame) -> pd.DataFrame:
    """trades: Databento trades DataFrame (ts_event, instrument_id, side, size). Returns one row per order."""
    o = trades.groupby(["instrument_id", "ts_event", "side"], sort=False)["size"].sum().reset_index()
    srv = o["ts_event"].dt.tz_convert("America/New_York").dt.tz_localize(None) + pd.Timedelta(hours=7)
    o["sday"] = srv.dt.strftime("%Y-%m-%d")
    o["block"] = session_block(o["ts_event"])
    return o


def thresholds(sizes: dict, sessions: list) -> dict:
    """sizes[(sday, block)] -> order sizes. Returns {(sday, block): lots} for sessions with L prior sessions."""
    out = {}
    for j in range(L, len(sessions)):
        prior = sessions[j - L:j]
        for b in BLOCKS:
            hist = [sizes[(d, b)] for d in prior if (d, b) in sizes]
            if hist:
                out[(sessions[j], b)] = int(np.ceil(np.percentile(np.concatenate(hist), Q)))
    return out


if __name__ == "__main__":
    import databento as db
    HERE = Path(__file__).resolve().parent
    files = sorted((HERE / "data").glob("GLBX.MDP3_trades_6E.v.0_*.dbn.zst"))
    tr = pd.concat([db.DBNStore.from_file(f).to_df().reset_index()[["ts_event", "instrument_id", "side", "size"]]
                    for f in files], ignore_index=True)
    tr["ts_event"] = pd.to_datetime(tr["ts_event"], utc=True)
    o = aggressor_orders(tr)
    del tr
    degraded = {d for d, _ in json.loads((HERE / "dataset_condition_2025-09_2026-09.json").read_text())}
    touch = degraded | {(pd.Timestamp(d) + pd.Timedelta(days=1)).strftime("%Y-%m-%d") for d in degraded}
    nmin = o.assign(m=o["ts_event"].dt.floor("min")).groupby("sday")["m"].nunique()
    days = sorted(nmin.index)
    sessions = [d for d in days[1:] if nmin[d] >= 0.8 * nmin.median() and d not in touch]
    o = o[o["sday"].isin(sessions)]
    sizes = {k: g["size"].to_numpy() for k, g in o.groupby(["sday", "block"])}
    T = thresholds(sizes, sessions)

    def qs(x, ps=(0, 5, 50, 95, 100)):
        return {f"p{p}": round(float(np.percentile(x, p)), 3) for p in ps}

    res = {"definition": {"q": Q, "L": L, "blocks": "Asia 18:00NY-08:00LDN | London 08:00LDN-08:30NY | NY 08:30-17:00NY"},
           "sessions": len(sessions), "scored_sessions": len(sessions) - L, "blocks": {}}
    for b in BLOCKS:
        keys = [k for k in T if k[1] == b]
        thr = [T[k] for k in keys]
        fo = [100 * (sizes[k] >= T[k]).mean() for k in keys if k in sizes]
        fv = [100 * sizes[k][sizes[k] >= T[k]].sum() / sizes[k].sum() for k in keys if k in sizes]
        cnt = [int((sizes[k] >= T[k]).sum()) for k in keys if k in sizes]
        res["blocks"][b] = {"orders_share_of_all": round(float((o["block"] == b).mean()), 4),
                            "threshold_lots": qs(thr), "pct_orders_flagged": qs(fo, (5, 50, 95)),
                            "pct_volume_flagged": qs(fv, (5, 50, 95)), "big_orders_per_session": qs(cnt, (5, 50, 95))}
    (HERE / "big_trades_definition.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
