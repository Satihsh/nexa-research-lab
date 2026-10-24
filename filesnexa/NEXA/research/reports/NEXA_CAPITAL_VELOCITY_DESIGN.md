# NEXA Capital Velocity Engine: design (research only; subordinate to the deterministic Risk Engine)

**Code:** `research/nexa_8e_capital.py` (simulator) and `research/nexa_8e_feasibility.py` (exact mathematics).
**Tests:** `research/test_nexa_capital_velocity.py`.
**Not** in the live EA and **not** deployed.

## 1. Daily objective (exact, no internal rounding)
For each Pepperstone **server** trading day (New York close, `nexa_time`):

```
start_equity        = ending equity of the previous day
daily_profit_target = start_equity × 0.245
daily_target_equity = start_equity × 1.245
```

From $200: day 1 target $249.00, day 2 $310.005, … day 20 **$16,010.95**. The full table is in `NEXA_24_5_DAILY_FEASIBILITY_AUDIT.md` §1.

## 2. Session lock and stop rules (all enforced in the simulator; risk rules unchanged)
| Rule | Effect |
|---|---|
| Equity ≥ daily_target_equity | **LOCK**: no new entries for the rest of the session; the Trade DNA row is closed and ending equity carried over. A new signal never re-opens the session. |
| Equity ≤ 0.98 × start_equity | **DAILY LOSS HALT** (NEXA hard rule, unchanged at 2 %) |
| 10 trades taken | **TRADE CAP** (NEXA hard rule) |
| Size below the broker minimum lot at ≤ 1 % risk | **SKIP** the trade. It is never rounded up. |
| After a loss | nothing changes: no doubling, martingale, grid, averaging down, re-entry, revenge trade or target chasing. The next trade is sized at ≤ 1 % of the **current** (lower) equity. |
| Stops | never widened, never moved farther away. Ratcheting only, as in the live EA. |

## 3. "Strictly no loss": engineering translation
Zero losing trades cannot be promised by any system and **is not promised**. The enforceable equivalents are:
- maximum loss per trade ≤ 1 % of equity, including costs;
- maximum daily loss of 2 %;
- the prohibitions in §2.

The simulator reports, per day and in aggregate:
- probability of loss, expected win and loss, expected value;
- MAE and MFE;
- probability of reaching the target, probability of hitting the daily halt;
- drawdown.

## 4. Position sizing (`nexa_8e_costs.size_trade`)
```
risk_cash   = equity × 1 %
loss/lot    = (stop_distance + spread + 2 × slippage) × value_per_price_per_lot + commission_round_trip/lot
raw_lots    = risk_cash / loss_per_lot
lots        = floor(raw_lots / volume_step) × volume_step   (≤ volume_max; < volume_min ⇒ NOT TRADABLE)
```
`value_per_price_per_lot = tick_value / tick_size` comes from the broker's spec, measured by `NEXA_SpecProbe.mq5`: XAUUSD 100, NAS100 1.0, EURUSD and GBPUSD 100,000 (USD account).

Margin, stops and freeze levels, spread, exposure, correlation and commission are validated by the live Risk Engine at execution time. They are outside this simulator's authority.

## 5. Flow (research architecture)
```
REGIME (EMA200, VEI, squeeze state) ──► STRUCTURAL TRIGGER (Donchian) ──► MOMENTUM (EMA9 + MACD 5/13/4)
     ──► MICROSTRUCTURE PROXIES (quote-activity OFI proxy, quote burst; NOT order flow / trade size)
     ──► EXHAUSTION VETO (TD Sequential) ──► COST CHECK (net-of-cost R ≥ 0 at the target)
     ──► CAPITAL VELOCITY (session open? target hit? halt? cap?) ──► DETERMINISTIC RISK ENGINE (final authority)
     ──► BROKER-VALID SIZE (round down; skip below min lot) ──► EXECUTION ──► TRADE DNA
```
The Capital Velocity layer can only **stop** or **skip** trading. It never raises size, risk or frequency.

## 6. When NEXA stops initiating new trades for the day (answer X)
1. The daily target is reached (lock).
2. The −2 % daily halt is reached.
3. Ten trades have been taken.
4. The 1 % size is below the broker minimum lot, or the stop violates the stops or freeze level.
5. The expected **net** R at the target is ≤ 0 after spread, commission, slippage and swap.
6. The spread exceeds the live cap (≤ 15 % ATR) or a news, FOMC or rollover window is active (the existing live gates).
7. Any fail-closed condition in the live EA: missing history, correlation data insufficient, an order in flight, or the portfolio lock busy.
