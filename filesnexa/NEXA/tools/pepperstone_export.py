"""Pepperstone history export. READ-ONLY. Runs under the MT5 prefix Python (Wine).

Attaches to the running, logged-in terminal WITHOUT credentials and aborts unless
the account is Pepperstone-Demo 61603218 in DEMO mode. Calls only read functions.

Limits (recorded, not worked around):
  * The terminal's maxbars (100,000) caps what the Python API returns per timeframe:
    M1 is visible only for the most recent 100,000 bars. Deeper M1 must come from the
    Strategy Tester (NEXA_BarExport), which is not bound by maxbars.
  * copy_ticks_* returns only ticks the terminal already holds; it is not proof of
    deeper server-side tick history.

Outputs (per symbol, all tagged Pepperstone):
  PEPPERSTONE_<SYM>_D1.csv          full D1 from 2000-01-01 (server time)
  PEPPERSTONE_<SYM>_M1_recent.csv   most recent maxbars M1 bars (core symbols only)
  PEPPERSTONE_<SYM>_ticks_recent.csv.gz   ticks the terminal holds (core symbols only)
  export_manifest.json              counts, first/last, bid/ask/spread flags, gaps

Usage: pepperstone_export.py <out_dir_windows_path> --core S1,S2 --fx S3,S4,...
"""
import gzip
import json
import sys
from datetime import datetime, timezone

import MetaTrader5 as mt5
import numpy as np

EXPECT = (61603218, "Pepperstone-Demo")


def ts(x):
    return datetime.fromtimestamp(int(x), timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def write_rates(path, r):
    with open(path, "w") as fh:
        fh.write("time,open,high,low,close,tick_volume,spread,real_volume\n")
        for row in r:
            fh.write(f"{ts(row['time'])},{row['open']:.6f},{row['high']:.6f},{row['low']:.6f},"
                     f"{row['close']:.6f},{int(row['tick_volume'])},{int(row['spread'])},{int(row['real_volume'])}\n")


def rate_stats(r, step):
    t = r["time"].astype(np.int64)
    d = np.diff(t)
    geo = int(np.sum((r["high"] < np.maximum(r["open"], r["close"])) | (r["low"] > np.minimum(r["open"], r["close"]))))
    return {"bars": int(len(r)), "first": ts(t[0]), "last": ts(t[-1]),
            "duplicate_times": int(np.sum(d == 0)), "non_monotonic": int(np.sum(d < 0)),
            "gaps_over_step": int(np.sum(d > step)), "max_gap_hours": float(d.max() / 3600) if len(d) else 0.0,
            "ohlc_geometry_violations": geo, "spread_points_median": float(np.median(r["spread"])),
            "spread_points_p95": float(np.percentile(r["spread"], 95)),
            "spread_zero_frac": float(np.mean(r["spread"] == 0))}


def main():
    out = sys.argv[1]
    args = dict(a.split("=", 1) for a in sys.argv[2:])
    core = [s for s in args.get("--core", "").split(",") if s]
    fx = [s for s in args.get("--fx", "").split(",") if s]
    if not mt5.initialize():
        raise SystemExit(f"initialize failed: {mt5.last_error()}")
    try:
        a = mt5.account_info()
        if a is None or (a.login, a.server) != EXPECT or a.trade_mode != 0:
            raise SystemExit("ABORT: not the expected Pepperstone DEMO account")
        man = {"broker": "Pepperstone", "server": a.server, "login": a.login, "account": "DEMO",
               "terminal_build": mt5.terminal_info().build, "maxbars": mt5.terminal_info().maxbars,
               "exported_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "time_convention": "broker server time (MT5 epoch encoding), written unconverted",
               "symbols": {}}
        now = datetime.now(timezone.utc)
        for s in core + fx:
            e = {"role": "core" if s in core else "fx", "selected": bool(mt5.symbol_select(s, True))}
            si = mt5.symbol_info(s)
            if si is not None:
                e["contract"] = {k: getattr(si, k) for k in (
                    "digits", "point", "trade_tick_size", "trade_tick_value", "trade_tick_value_loss",
                    "trade_contract_size", "volume_min", "volume_step", "volume_max", "trade_stops_level",
                    "trade_freeze_level", "trade_calc_mode", "trade_exemode", "filling_mode", "spread_float",
                    "swap_long", "swap_short", "currency_base", "currency_profit", "path")}
            d1 = None
            for _ in range(3):                           # first request may only trigger the download
                d1 = mt5.copy_rates_range(s, mt5.TIMEFRAME_D1, datetime(2000, 1, 1, tzinfo=timezone.utc), now)
                if d1 is not None and len(d1):
                    break
            if d1 is not None and len(d1):
                write_rates(f"{out}\\PEPPERSTONE_{s}_D1.csv", d1)
                e["D1"] = rate_stats(d1, 3 * 86400)
            else:
                e["D1"] = {"bars": 0, "last_error": str(mt5.last_error())}
            if s in core:
                m1 = mt5.copy_rates_from_pos(s, mt5.TIMEFRAME_M1, 1, man["maxbars"])   # start_pos=1: closed bars only
                if m1 is not None and len(m1):
                    write_rates(f"{out}\\PEPPERSTONE_{s}_M1_recent.csv", m1)
                    e["M1_recent"] = rate_stats(m1, 60)
                else:
                    e["M1_recent"] = {"bars": 0, "last_error": str(mt5.last_error())}
                tk = mt5.copy_ticks_range(s, datetime(2026, 1, 1, tzinfo=timezone.utc), now, mt5.COPY_TICKS_ALL)
                if tk is not None and len(tk):
                    with gzip.open(f"{out}\\PEPPERSTONE_{s}_ticks_recent.csv.gz", "wt") as fh:
                        fh.write("time_msc,bid,ask,last,volume,flags\n")
                        for t in tk:
                            fh.write(f"{int(t['time_msc'])},{t['bid']:.6f},{t['ask']:.6f},{t['last']:.6f},"
                                     f"{int(t['volume'])},{int(t['flags'])}\n")
                    tm = tk["time_msc"].astype(np.int64)
                    sp = tk["ask"] - tk["bid"]
                    e["ticks_recent"] = {"ticks": int(len(tk)), "first": ts(tm[0] // 1000), "last": ts(tm[-1] // 1000),
                                         "bid_ask_both_present_frac": float(np.mean((tk["bid"] > 0) & (tk["ask"] > 0))),
                                         "negative_spread": int(np.sum(sp < 0)),
                                         "spread_price_median": float(np.median(sp)),
                                         "spread_price_p95": float(np.percentile(sp, 95)),
                                         "non_monotonic_time": int(np.sum(np.diff(tm) < 0))}
                else:
                    e["ticks_recent"] = {"ticks": 0, "last_error": str(mt5.last_error())}
            man["symbols"][s] = e
            print(s, e.get("D1", {}).get("bars"), e.get("M1_recent", {}).get("bars"),
                  e.get("ticks_recent", {}).get("ticks"), flush=True)
        with open(f"{out}\\export_manifest.json", "w") as fh:
            json.dump(man, fh, indent=1, default=str)
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
