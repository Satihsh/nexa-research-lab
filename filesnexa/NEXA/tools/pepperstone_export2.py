"""Pepperstone export, pass 2. READ-ONLY (same account guard as pepperstone_export.py).

  * core symbols: most recent M1 bars (count = maxbars - 2, start_pos=1 -> closed bars only)
  * FX universe: D1 from 2000, two-phase (trigger every download first, wait, then collect)
    because a first copy_rates request only starts the server download.
  * contract specs for every symbol -> contracts.json

Usage: pepperstone_export2.py <out_dir_windows> --core=A,B --fx=C,D
"""
import json
import sys
import time
from datetime import datetime, timezone

import MetaTrader5 as mt5

EXPECT = (61603218, "Pepperstone-Demo")
SPEC = ("digits", "point", "trade_tick_size", "trade_tick_value", "trade_tick_value_loss",
        "trade_contract_size", "volume_min", "volume_step", "volume_max", "trade_stops_level",
        "trade_freeze_level", "trade_calc_mode", "trade_exemode", "filling_mode", "spread_float",
        "swap_long", "swap_short", "swap_rollover3days", "currency_base", "currency_profit",
        "currency_margin", "path", "description")


def ts(x):
    return datetime.fromtimestamp(int(x), timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def write_rates(path, r):
    with open(path, "w") as fh:
        fh.write("time,open,high,low,close,tick_volume,spread,real_volume\n")
        for row in r:
            fh.write(f"{ts(row['time'])},{row['open']:.6f},{row['high']:.6f},{row['low']:.6f},"
                     f"{row['close']:.6f},{int(row['tick_volume'])},{int(row['spread'])},{int(row['real_volume'])}\n")


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
        maxbars = mt5.terminal_info().maxbars
        status, contracts = {"maxbars": maxbars, "core_M1": {}, "fx_D1": {}}, {}
        now = datetime.now(timezone.utc)
        for s in core + fx:
            mt5.symbol_select(s, True)
            si = mt5.symbol_info(s)
            contracts[s] = {k: getattr(si, k) for k in SPEC} if si else None
        for s in core:
            m1 = None
            for _ in range(10):
                m1 = mt5.copy_rates_from_pos(s, mt5.TIMEFRAME_M1, 1, maxbars - 2)
                if m1 is not None and len(m1):
                    break
                time.sleep(2)
            if m1 is not None and len(m1):
                write_rates(f"{out}\\PEPPERSTONE_{s}_M1_recent.csv", m1)
                status["core_M1"][s] = {"bars": int(len(m1)), "first": ts(m1["time"][0]), "last": ts(m1["time"][-1])}
            else:
                status["core_M1"][s] = {"bars": 0, "last_error": str(mt5.last_error())}
            print("M1", s, status["core_M1"][s], flush=True)
        start = datetime(2000, 1, 1, tzinfo=timezone.utc)
        for s in fx:                                   # phase A: trigger downloads
            mt5.copy_rates_range(s, mt5.TIMEFRAME_D1, start, now)
        time.sleep(30)
        for s in fx:                                   # phase B: collect
            d1 = None
            for _ in range(5):
                d1 = mt5.copy_rates_range(s, mt5.TIMEFRAME_D1, start, now)
                if d1 is not None and len(d1):
                    break
                time.sleep(3)
            if d1 is not None and len(d1):
                write_rates(f"{out}\\PEPPERSTONE_{s}_D1.csv", d1)
                status["fx_D1"][s] = {"bars": int(len(d1)), "first": ts(d1["time"][0]), "last": ts(d1["time"][-1])}
            else:
                status["fx_D1"][s] = {"bars": 0, "last_error": str(mt5.last_error())}
            print("D1", s, status["fx_D1"][s], flush=True)
        with open(f"{out}\\export2_status.json", "w") as fh:
            json.dump(status, fh, indent=1)
        with open(f"{out}\\contracts.json", "w") as fh:
            json.dump(contracts, fh, indent=1, default=str)
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
