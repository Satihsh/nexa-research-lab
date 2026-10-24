"""Nautilus v2 environment acceptance smoke test (NAUTILUS_ENV_PLAN_v1 section 7, checks 1-3).

Synthetic data only, no market data and no network. The expected result is fixed by hand BEFORE the run:
  - 6E-style future: multiplier 125,000, tick 0.00005, fee 2.50 USD per contract per fill.
  - Flat bars (O=H=L=C): bars 0-19 at 1.10000, bars 20-39 at 1.10500, so the fill price is unambiguous.
  - BUY 2 contracts on bar 5, SELL 2 on bar 30.
  - Gross = 2 x 125,000 x (1.10500 - 1.10000) = 1,250.00 USD; fees = 2.50 x 2 x 2 = 10.00 USD.
  - Final balance = 1,000,000 + 1,250 - 10 = 1,001,240.00 USD.
Run twice: both runs must match the expectation and each other exactly (determinism).
Usage: .venv-nautilus/bin/python -I nexa_platform/tests/env_smoke.py  (exit 0 = pass)
"""
from __future__ import annotations

import json
import sys
from datetime import UTC
from datetime import datetime
from decimal import Decimal

import nautilus_trader
from nautilus_trader.backtest import BacktestEngine
from nautilus_trader.common import LogLevel
from nautilus_trader.config import BacktestEngineConfig
from nautilus_trader.config import LoggerConfig
from nautilus_trader.config import StrategyConfig
from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.execution import PerContractFeeModel
from nautilus_trader.model import AccountType
from nautilus_trader.model import AssetClass
from nautilus_trader.model import Bar
from nautilus_trader.model import BarType
from nautilus_trader.model import Currency
from nautilus_trader.model import FuturesContract
from nautilus_trader.model import InstrumentId
from nautilus_trader.model import Money
from nautilus_trader.model import OmsType
from nautilus_trader.model import OrderSide
from nautilus_trader.model import Price
from nautilus_trader.model import Quantity
from nautilus_trader.model import Symbol
from nautilus_trader.model import TimeInForce
from nautilus_trader.model import TraderId
from nautilus_trader.model import Venue
from nautilus_trader.trading import Strategy

EXPECTED_VERSION = "2.0.0rc6"
EXPECTED_BALANCE = Decimal("1001240.00")
EXPECTED_FILLS = [("BUY", Decimal("2"), Decimal("1.10000")), ("SELL", Decimal("2"), Decimal("1.10500"))]
USD = Currency.from_str("USD")


def make_instrument(venue: Venue) -> FuturesContract:
    symbol = Symbol("SMOKE6E")
    return FuturesContract(
        instrument_id=InstrumentId(symbol, venue),
        raw_symbol=symbol,
        asset_class=AssetClass.FX,
        currency=USD,
        price_precision=5,
        price_increment=Price.from_str("0.00005"),
        multiplier=Quantity.from_int(125_000),
        lot_size=Quantity.from_int(1),
        underlying="EUR/USD",
        activation_ns=0,
        expiration_ns=dt_to_unix_nanos(datetime(2030, 12, 17, tzinfo=UTC)),
        ts_event=0,
        ts_init=0,
        margin_init=Decimal("0.05"),
        margin_maint=Decimal("0.04"),
        exchange="SIM",
    )


class OneTripConfig(StrategyConfig):
    def __init__(self, *, instrument_id: InstrumentId, bar_type: BarType, **_kwargs: object) -> None:
        super().__init__()
        self.instrument_id = instrument_id
        self.bar_type = bar_type


class OneTrip(Strategy):
    """Buys 2 on bar 5, sells 2 on bar 30. Nothing else."""

    def __init__(self, config: OneTripConfig) -> None:
        super().__init__(config)
        self._cfg = config
        self._n = -1

    def on_start(self) -> None:
        self.subscribe_bars(self._cfg.bar_type)

    def on_bar(self, bar: Bar) -> None:
        self._n += 1
        side = {5: OrderSide.BUY, 30: OrderSide.SELL}.get(self._n)
        if side is not None:
            self.submit_order(self.order_factory.market(
                instrument_id=self._cfg.instrument_id,
                order_side=side,
                quantity=Quantity.from_int(2),
                time_in_force=TimeInForce.GTC,
            ))


def run_once() -> dict:
    engine = BacktestEngine(config=BacktestEngineConfig(
        trader_id=TraderId.from_str("SMOKE-001"),
        logging=LoggerConfig(stdout_level=LogLevel.ERROR),
    ))
    venue = Venue("SIM")
    engine.add_venue(
        venue=venue,
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=USD,
        fee_model=PerContractFeeModel(Money.from_str("2.50 USD")),
        starting_balances=[Money.from_str("1000000 USD")],
    )
    inst = make_instrument(venue)
    engine.add_instrument(inst)
    bar_type = BarType.from_str(f"{inst.id}-1-MINUTE-LAST-EXTERNAL")
    t0 = dt_to_unix_nanos(datetime(2026, 1, 5, tzinfo=UTC))
    bars = []
    for i in range(40):
        px = inst.make_price(1.10000 if i < 20 else 1.10500)
        ts = t0 + i * 60_000_000_000
        bars.append(Bar(bar_type=bar_type, open=px, high=px, low=px, close=px,
                        volume=Quantity.from_int(1_000), ts_event=ts, ts_init=ts))
    engine.add_data(bars)
    engine.add_strategy(OneTrip(OneTripConfig(instrument_id=inst.id, bar_type=bar_type)))
    engine.run()

    orders = sorted(engine.cache.orders(), key=lambda o: o.ts_init)
    fills = [(o.side.name if hasattr(o.side, "name") else str(o.side).split(".")[-1],
              Decimal(str(o.filled_qty)), Decimal(str(o.avg_px))) for o in orders]
    balance = Decimal(str(engine.portfolio.account(venue).balance_total(USD).as_decimal()))
    result = {
        "fills": [[s, str(q), str(p)] for s, q, p in fills],
        "fills_ts": [int(o.ts_last) for o in orders],
        "final_balance_usd": str(balance),
    }
    engine.dispose()
    return result


def main() -> int:
    checks = {}
    checks["version"] = nautilus_trader.__version__ == EXPECTED_VERSION
    r1, r2 = run_once(), run_once()
    exp_fills = [[s, str(q), str(p)] for s, q, p in EXPECTED_FILLS]
    checks["fills_match_hand_calc"] = [[s, str(Decimal(q)), str(Decimal(p).quantize(Decimal("0.00001")))]
                                      for s, q, p in r1["fills"]] == [[s, q, str(Decimal(p).quantize(Decimal("0.00001")))]
                                                                      for s, q, p in exp_fills]
    checks["balance_match_hand_calc"] = Decimal(r1["final_balance_usd"]) == EXPECTED_BALANCE
    checks["deterministic_rerun"] = json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)
    out = {"nautilus_version": nautilus_trader.__version__, "python": sys.version.split()[0],
           "expected_balance_usd": str(EXPECTED_BALANCE), "run1": r1, "run2": r2, "checks": checks,
           "pass": all(checks.values())}
    print(json.dumps(out, indent=2))
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
