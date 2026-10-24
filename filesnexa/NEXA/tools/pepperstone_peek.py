"""READ-ONLY peek at what copy_rates_range returns for one window. No credentials, no orders."""
import sys
from datetime import datetime, timezone
import MetaTrader5 as mt5
assert mt5.initialize(), mt5.last_error()
try:
    a = mt5.account_info(); assert a.login == 61603218 and a.server == "Pepperstone-Demo" and a.trade_mode == 0
    for y in (2015, 2020, 2024):
        r = mt5.copy_rates_range("EURUSD", mt5.TIMEFRAME_M1, datetime(y, 1, 14, 10, tzinfo=timezone.utc), datetime(y, 1, 14, 11, tzinfo=timezone.utc))
        print(y, len(r) if r is not None else None, [datetime.fromtimestamp(int(t), timezone.utc).isoformat() for t in (r["time"][:2] if r is not None else [])], mt5.last_error())
    d1 = mt5.copy_rates_range("EURUSD", mt5.TIMEFRAME_D1, datetime(2000, 1, 1, tzinfo=timezone.utc), datetime(2026, 9, 27, tzinfo=timezone.utc))
    print("D1", None if d1 is None else (len(d1), datetime.fromtimestamp(int(d1['time'][0]), timezone.utc)), mt5.last_error())
finally:
    mt5.shutdown()
