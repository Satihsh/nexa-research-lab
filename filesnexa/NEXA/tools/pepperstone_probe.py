"""Pepperstone history coverage probe. READ-ONLY.

Runs under the MT5 prefix Python (Wine). Attaches to the ALREADY RUNNING, already
logged-in terminal with mt5.initialize() and NO credentials, then aborts unless the
account is the expected Pepperstone DEMO. Only read functions are called:
account_info, terminal_info, symbol_info, symbol_select (Market Watch visibility),
copy_rates_*, copy_ticks_*. No order_* function is referenced anywhere in this file.

Usage (wine python): pepperstone_probe.py <out_json> SYMBOL [SYMBOL ...]
"""
import json
import sys
from datetime import datetime, timezone

import MetaTrader5 as mt5

EXPECT_LOGIN = 61603218
EXPECT_SERVER = "Pepperstone-Demo"


def ts(x):
    return datetime.fromtimestamp(int(x), timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def main():
    out, syms = sys.argv[1], sys.argv[2:]
    if not mt5.initialize():
        raise SystemExit(f"initialize failed: {mt5.last_error()}")
    try:
        acc = mt5.account_info()
        if acc is None or acc.login != EXPECT_LOGIN or acc.server != EXPECT_SERVER or acc.trade_mode != 0:
            raise SystemExit(f"ABORT: unexpected account {getattr(acc, 'login', None)} "
                             f"{getattr(acc, 'server', None)} mode {getattr(acc, 'trade_mode', None)}")
        ti = mt5.terminal_info()
        rep = {"broker": "Pepperstone", "server": acc.server, "login": acc.login,
               "account_trade_mode": "DEMO", "terminal_build": ti.build,
               "maxbars": ti.maxbars, "probed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "note": "MT5 python returns times as broker SERVER time encoded as epoch seconds",
               "symbols": {}}
        now = datetime.now(timezone.utc)
        for s in syms:
            r = {"selected": bool(mt5.symbol_select(s, True))}
            info = mt5.symbol_info(s)
            if info is None:
                r["error"] = "symbol_info None"
                rep["symbols"][s] = r
                continue
            d1 = mt5.copy_rates_range(s, mt5.TIMEFRAME_D1, datetime(2000, 1, 1, tzinfo=timezone.utc), now)
            r["D1"] = ({"bars": int(len(d1)), "first": ts(d1["time"][0]), "last": ts(d1["time"][-1])}
                       if d1 is not None and len(d1) else {"bars": 0, "last_error": str(mt5.last_error())})
            # M1 and ticks: one bounded sample window per year (a Wednesday in mid-January,
            # 10:00-11:00 UTC-epoch server time). copy_*_range never returns data outside the
            # window, so an empty result means "not available", never "jumped forward".
            m1_years, tick_years = {}, {}
            for y in range(2005, now.year + 1):
                d = datetime(y, 1, 15, tzinfo=timezone.utc)
                while d.weekday() != 2:
                    d = d.replace(day=d.day + 1)
                a, b = d.replace(hour=10), d.replace(hour=11)
                m1 = mt5.copy_rates_range(s, mt5.TIMEFRAME_M1, a, b)
                if m1 is not None and len(m1):
                    m1_years[str(y)] = int(len(m1))
                tk = mt5.copy_ticks_range(s, a, b, mt5.COPY_TICKS_ALL)
                if tk is not None and len(tk):
                    tick_years[str(y)] = {"ticks_in_hour": int(len(tk)),
                                          "bid_ask_present": bool((tk["bid"] > 0).all() and (tk["ask"] > 0).all())}
            r["m1_sample_bars_per_hour_by_year"] = m1_years
            r["ticks_sample_by_year"] = tick_years
            rep["symbols"][s] = r
            print(s, json.dumps({k: v for k, v in r.items() }), flush=True)
        with open(out, "w") as fh:
            json.dump(rep, fh, indent=1)
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
