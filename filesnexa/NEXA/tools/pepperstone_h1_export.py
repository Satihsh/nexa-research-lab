"""Pepperstone H1 export for the Strategy Factory. READ-ONLY (same account guard).

Most recent (maxbars - 2) CLOSED H1 bars (start_pos=1) per symbol - about 16 years on
this terminal. Written as PEPPERSTONE_<SYM>_H1_factory.csv in broker server time.
No order_* function is referenced in this file.

Usage: pepperstone_h1_export.py <out_dir_windows> SYM [SYM ...]
"""
import sys
import time
from datetime import datetime, timezone

import MetaTrader5 as mt5

EXPECT = (61603218, "Pepperstone-Demo")


def main():
    out, syms = sys.argv[1], sys.argv[2:]
    if not mt5.initialize():
        raise SystemExit(f"initialize failed: {mt5.last_error()}")
    try:
        a = mt5.account_info()
        if a is None or (a.login, a.server) != EXPECT or a.trade_mode != 0:
            raise SystemExit("ABORT: not the expected Pepperstone DEMO account")
        n = mt5.terminal_info().maxbars - 2
        for s in syms:
            mt5.symbol_select(s, True)
            r = None
            for _ in range(10):
                r = mt5.copy_rates_from_pos(s, mt5.TIMEFRAME_H1, 1, n)
                if r is not None and len(r):
                    break
                time.sleep(3)
            if r is None or not len(r):
                print(s, "NO DATA", mt5.last_error(), flush=True)
                continue
            with open(f"{out}\\PEPPERSTONE_{s}_H1_factory.csv", "w") as fh:
                fh.write("time,open,high,low,close,tick_volume,spread\n")
                for x in r:
                    t = datetime.fromtimestamp(int(x["time"]), timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    fh.write(f"{t},{x['open']},{x['high']},{x['low']},{x['close']},{int(x['tick_volume'])},{int(x['spread'])}\n")
            print(s, len(r), datetime.fromtimestamp(int(r["time"][0]), timezone.utc), flush=True)
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
