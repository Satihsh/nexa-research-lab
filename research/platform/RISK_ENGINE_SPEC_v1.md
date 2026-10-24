# NEXA Risk Engine — venue-neutral specification v1 (Phase 0, document only)

**Status:** DRAFT for user review, written 2026-10-12. Phase 0 of `research/NEXA_PLATFORM_AGNOSTIC_ROADMAP.md`.

- **Purpose:** state *exactly* what the frozen MQL5 risk engine does, in broker-neutral terms, so a Python/Nautilus port can be proven **behaviour-identical** by parity tests before it ever touches an order.
- **This document changes nothing:**
  - S14, `NEXA_Risk.mqh`, the preset and schema v1 are untouched.
  - Every limit below is the frozen value.
  - Where the current behaviour has a quirk, it is **recorded, not fixed** (§7). Any change to policy needs a separate, explicit human approval, as with S11 and C4.

## 0. Source pins (the spec describes these bytes and nothing else)

All paths are under `filesnexa/NEXA/`.

| File | SHA-256 | Role |
|---|---|---|
| `NEXA_Risk.mqh` (= `build/s14_src/NEXA_Risk.mqh`) | `a43d8328178550657fe3af51717896d71accbd28fb43f5e0b0df825483e3a244` | Approved risk policy (baseline + correlation fix 2026-09-29 + S11 + C4) |
| `NEXA_Safety.mqh` (= `build/s14_src/`) | `843fc60674d4c3e761993af6dfe73b73480cadc274ccfad31ddb8680716d1456` | Broker-distance checks, atomic lock / slot primitives |
| `build/s14_src/NEXA_EA_S14.mq5` | `6932ad7dacda58cc09f5eef65e808a2c847b4081f12ddb450771c067a2ca501e` | Call order, input validation, send/retry revalidation, time gates |
| `build/s14_src/NEXA_Advanced_Ingest.mqh` | `f0a49c2fcdefdbd5c8a7d3f2a3bc8d893926a95ac1d82d1a78cd12046a8ad12a` | `PreflightExecutionCheck` |
| `build/s14_src/NEXA_Intelligence.mqh` | `81641c4e4a681f2d2859b99bfc4371b41cdea8092cea80452b0e35ab9f115765` | `AdversarialCheck`, `StrategySurvivalOK` (strategy guards, §5) |
| `research/forward_demo/gcp_g2/upload/NEXA_EA_S14_DEMO_PRODUCTION.set` | `1873bfe3f137af99e1b756eb6117543298d0bef0d0390cc6889d329c038ad4c9` | Parameter values running in the S14 forward check |

**Existing guards that keep these bytes frozen:** `research/test_nexa_mql5_invariants.py`, `test_nexa_risk_s11_exposure.py` and `test_nexa_risk_c4_budget.py`. If any pinned hash changes, this spec is void until it is re-derived.

## 1. Scope and layering

| Layer | Contents | Venue-neutral home |
|---|---|---|
| **A. Account risk policy** (NEXA_Risk) | Sizing, daily-loss halt and budget, drawdown halt and throttle, trade count, currency-exposure cap, correlation cap, margin cap | `nexa_risk` package: pure functions plus one state store |
| **B. Execution safety** (NEXA_Safety + EA) | Preflight, portfolio entry lock, trade-slot reservation, stop / freeze distance, send-retry revalidation, stale-bar guard, weekend close | Execution-adapter contract (each venue must satisfy it) |
| **C. Strategy guards** (Intelligence) | Spread / ATR tax, adversarial check, survival pause, news / FOMC windows, AI confirmation | Belong to the S14 *strategy* port, not the account engine; listed in §5 so nothing is lost |

**Invariant shared by all layers:** every check can only **block or reduce**; nothing in A or B can increase size or open a trade.

## 2. Frozen parameters (preset 1873bfe3, which equals the source defaults for every layer-A value)

| Name | Value | Meaning |
|---|---|---|
| `RiskPercent` | **0.30 %** | Target risk per trade, as a share of equity |
| `HardRiskCeiling` | **1.00 %** | Absolute per-trade ceiling after every rounding |
| `MaxDailyLossPct` | **2.00 %** | Daily halt trigger **and** pre-trade budget (C4) |
| `MaxDrawdownPct` | **10.00 %** | Peak-to-equity halt; the throttle starts at 5 % |
| `MaxTradesPerDay` | **10** | Account-wide, counted at dispatch |
| `MaxSpreadATRRatio` | **0.15** | Strategy guard (layer C) |
| `MaxMarginUsagePct` | **50 %** | Required margin ÷ free margin, applied in sizing |
| `PreflightMaxMarginPct` | **40 %** | The same ratio at preflight (the stricter one binds) |
| `MaxSameCurrencyNet` | **2** | Per-currency net cap, in *min-lot units of the candidate symbol* |
| `MaxCorrelation` | **0.75** | \|ρ\| at or above this blocks |
| `CorrelationBars` | **100** | Closed bars of the chart timeframe |
| `CORR_MIN_ALIGNED_FRAC` | **0.80** | Compile-time constant |
| `InFlightTimeoutSec` | 20 | The lock becomes reclaimable after 2× this (40 s) |
| `MaxRetries` | 3 | Send attempts; each one is re-validated |
| `WeekendCloseHour` | 21 (server time, Friday) | Flatten window |
| `STALE_BAR_MAX_SEC` | 6 h | Constant |

The EA's input validation (`ValidateInputs`, EA:158–200) refuses to start outside these ranges:
- `RiskPercent` must be in (0, 5] and ≤ `HardRiskCeiling`, which must itself be in (0, 5].
- `MaxDailyLossPct` must be in (0, 50].
- `MaxDrawdownPct` must be in (0, 90].
- `MaxSpreadATRRatio` must be in (0, 1].
- `MaxMarginUsagePct` must be in (0, 100].
- `CorrelationBars` must be ≥ 3.

**The port must reject the same ranges.**

## 3. Persistent state (account-scoped, shared by every NEXA instance)

The MQL5 engine keeps this state in terminal-global variables with the prefix `NEXA_`. The port must keep **one durable, atomic store per trading account**, not one per strategy.

| Key | Set / reset | Read by |
|---|---|---|
| `DayStamp` | At the roll, to the date of the **broker server clock** (`TimeCurrent`, yyyymmdd) | Roll detection |
| `DailyStartEquity` | At the roll, to the equity at that moment | Daily halt, C4 budget |
| `TradesToday` | 0 at the roll; atomic +1 at dispatch | Trade-count gate |
| `EmergencyStop` | 1 on a halt; **0 at every roll** | Entry gate |
| `EquityPeak` | Created once (if absent) at the first roll; raised whenever equity is above it | DD halt, throttle |
| `PortfolioEntryLock` | Compare-and-set: 0 means free, otherwise the time it was taken; reclaimable after 40 s | Serialises portfolio checks plus dispatch |

**Timing of the roll and halt checks:** the roll runs on the first tick of each new bar (EA:1197), before any halt check.

## 4. Layer A rules (exact semantics)

Notation:
- E = current account equity; FM = free margin.
- `lossToStop(side, sym, lots, from, stop)` = the broker's own P&L calculation (MT5 `OrderCalcProfit`) from `from` to `stop`, taken as a positive loss, in account currency.

### A1 Daily roll — `RollDailyStateIfNewDay`
If the server-clock date differs from `DayStamp`:
1. set `DayStamp`;
2. set `TradesToday` = 0;
3. set `DailyStartEquity` = E;
4. set `EmergencyStop` = 0;
5. if `EquityPeak` is absent, set it to E.

### A2 Halt gates (once per new bar, in this order, before any signal work)
1. **Emergency stop:** if `EmergencyStop` ≥ 1, no entries.
2. **Daily loss:**
   - Trigger: `(DailyStartEquity − E) / DailyStartEquity × 100 ≥ 2.00`.
   - Effect: set `EmergencyStop` and stop.
   - A missing `DailyStartEquity` → treated as E, i.e. 0 % loss (see §7 Q2).
   - `DailyStartEquity` ≤ 0 → halt.
3. **Drawdown:**
   - First update the peak: if E > peak, set peak = E.
   - Trigger: `(peak − E) / peak × 100 ≥ 10.00`.
   - Effect: set `EmergencyStop` and stop.
   - peak ≤ 0 → halt.
4. **Trade count:** if `TradesToday` ≥ 10, no entries.

### A3 Sizing — `CalcLotSizeHardened(dir, entry, stop)` → lots or a reason code
1. Reject if the direction is 0, a price is non-finite or ≤ 0, E ≤ 0, the broker volume spec is invalid (step / min / max ≤ 0 or max < min), or the risk config is ≤ 0.
2. `riskPerLot = |lossToStop(dir, sym, volStep, entry, stop)| / volStep`. Reject if this is ≤ 0 or non-finite.
   - Here *entry* is the ask for a long and the bid for a short, so the **entry spread is included**.
3. `raw = E × 0.30 % / riskPerLot`, then `lots = floor(raw / step) × step`.
4. **Below the minimum lot:**
   - If lots < volMin, the minimum lot is allowed **only if** `riskPerLot × volMin / E ≤ 1.00 %`.
   - Otherwise return `MIN_LOT_EXCEEDS_HARD_RISK_CEILING` (no trade).
   - If not below the minimum, lots = min(lots, volMax).
5. **Margin:**
   - `marginReq = broker margin(dir, sym, lots, entry)`.
   - Reject if FM ≤ 0 or `marginReq / FM > 50 %`.
6. **Drawdown throttle:**
   - The multiplier `m` is 1.0 when DD < 5 %, 0.50 when DD ≥ 5 %, 0.25 when DD ≥ 7.5 %, and 0 when DD ≥ 10 %.
   - Then `lots = floor(lots × m / step) × step`.
   - Reject if the result is below the minimum lot.
7. **Final re-check:** `riskPerLot × lots / E ≤ 1.00 %`, else reject. This is the last word.
8. The reason string records the size mode, the throttle and the actual risk %. It is journalled.

### A4 Currency-exposure cap — `ExposureCapOK(sym, dir, lots)` (S11 fail-closed)
1. `cap = 2 × volMin(sym)`, in lots.
2. For both the base and the profit currency of `sym`, compute the net exposure across **all open positions on the account** (all symbols, all strategies): +volume when the currency is that position's base and it is long; −volume when it is the quote; signs reversed for shorts.
3. Add the candidate trade: base `+dir × lots`, quote `−dir × lots`.
4. Block if either |after| > cap.
5. **Fail-closed:** an unreadable position, a volume ≤ 0, or empty currencies block the trade.

### A5 Correlation cap — `CorrelationCapOK(sym)` (fail-closed, time-aligned, 2026-09-29)
For every *other* symbol with an open position:
1. Take the last 101 **closed** bars of `sym` on the chart timeframe, and that symbol's bars over the same time window.
2. Simple close-to-close returns are paired **only where both bar open times exist in both series**.
3. At least ⌈0.80 × 100⌉ = 80 aligned pairs are required.
4. Pearson ρ; |ρ| ≥ 0.75 → block.
5. Every data problem → `INSUFFICIENT_DATA` → **block**: not synchronised, short history, non-ascending times, a bad price, zero variance, non-finite ρ, or an unreadable position.

`NexaCorrelationFromBars` is already a **pure function**; it is the reference for parity.

### A6 Daily-loss budget — `DailyLossBudgetOK` (C4, pre-trade)
Allow the entry only if:

`E − Σ_open lossToStop(pos, from = current price, to = pos.SL) − lossToStop(new, entry, stop) ≥ DailyStartEquity × (1 − 2.00 %)`

**Fail-closed** on any of:
- a missing or invalid start equity;
- **any open position without a stop**;
- an unreadable position;
- a failed broker calculation.

**Not covered (documented in the source):** gap or slippage beyond the stop, and the new trade's commission.

### A7 Evaluation order inside an entry (EA `ExecuteSignal`, lines 503–600)
Layer-C guards (adversarial, survival, AI, TP room) run first, then:
1. `A3` sizing;
2. **acquire the portfolio lock** (if busy, skip);
3. `A4` exposure;
4. `A5` correlation;
5. `A6` budget;
6. `B1` preflight;
7. `B2` reserve a trade slot;
8. dispatch.

Any failure after the lock releases the lock. A dispatched order keeps the lock until the order resolves.

## 5. Layer B and C rules the port must carry (summary; exact text in the pinned files)

**Layer B (execution safety):**
- **B1 Preflight:**
  - The terminal and account must be connected and allow trading (the EA's own algo-trading permission included).
  - The symbol trade mode must allow the side (CLOSEONLY blocks).
  - Margin ≤ 40 % of free margin.
- **B2 Trade slot:** atomic compare-and-set increment of `TradesToday`, up to 10. A send that never reaches the server gives the slot back; a rejected dispatch keeps it (conservative).
- **B3 Send revalidation:** before every retry, re-quote and abort if:
  - the stop is now on the wrong side, or inside the stops level; or
  - target room < `MinTP_R` (1.5 R); or
  - **risk distance > the sized distance** (never resend at a worse price).

  Timeout or connection results are *ambiguous*: never resend, and keep the lock and slot until they resolve.
- **B4 Stop / freeze distance:** a stop modification must sit outside max(stops level, freeze level), and no modification is made while the current SL/TP is inside the freeze level.
- **B5 Stale bar:** a closed bar that ended more than 6 h ago can be journalled but never opens a trade.
- **B6 Weekend:** flatten from Friday 21:00 server time.

**Layer C (strategy guards, belong to the S14 strategy):**
- Spread / ATR ≤ 0.15.
- Adversarial check:
  - stressed spread (3× spread) ÷ stop ≤ 0.40;
  - no contradictory structure;
  - the bucket win rate must be ≥ 25 % once n ≥ 20;
  - stop ≥ 0.5 ATR.
- Survival pause when the rolling expectancy is < −0.10 R after ≥ 20 trades.
- The news window fails closed (calendar errors count as risk).
- FOMC table.
- AI confirmation is fail-closed when required (it is *off* in the preset).

## 6. Venue abstraction (what every adapter must supply)

The port is pure functions over these inputs. The venue's only job is to provide them **truthfully** or report that it cannot.

| Interface | Fields / methods | MT5 source today | Notes for other venues |
|---|---|---|---|
| `AccountState` | equity, free margin, account currency, trade-allowed flags | `AccountInfo*` | Nautilus: `Portfolio` / `Account`. Equity must include unrealised P&L. |
| `InstrumentSpec` | vol min / step / max, base currency, profit currency, point, stops level, freeze level, trade mode | `SymbolInfo*` | cTrader / Dukascopy publish these differently; currencies for index CFDs (NAS100: profit = USD, base = n/a) need an explicit rule. **This is an open design point; see §7 Q4.** |
| `lossToStop(side, lots, from, to)` | Loss in account currency | `OrderCalcProfit` | Must reproduce the broker's own figure, including the quote→account FX conversion and contract size. **Highest parity risk.** |
| `marginFor(side, lots, price)` | Required margin | `OrderCalcMargin` | Leverage tiers differ by venue and instrument. |
| `Positions` | symbol, side, volume, SL, current price | `PositionGet*` | Must include **all** positions on the account, not only NEXA's. |
| `Bars(sym, tf, closed only)` | open time, close | `CopyRates` | Venue time base must match; Pepperstone server = NY + 7 h. |
| `ServerClock` | The date used for the roll | `TimeCurrent` | See §7 Q1. |
| `StateStore` | Atomic get / set / compare-and-set, durable across restarts | Terminal global variables | One store per account. |

## 7. Behaviours preserved as-is (quirks to keep for parity; any change needs approval)

| # | Current behaviour | Why it matters off-MT5 |
|---|---|---|
| **Q1** | The trading day = the **broker server date**. Pepperstone server = NY + 7 h, so the day rolls at **17:00 New York**. | Other venues use UTC or other servers. The port must use an explicit `day_roll = 17:00 America/New_York` to stay identical to S14 on Pepperstone; a different roll is a policy change. |
| **Q2** | The daily halt with no stored start equity falls back to current equity (0 % loss, no halt). The C4 budget, by contrast, **blocks** without a start equity. | The net effect is still fail-closed for entries, because C4 runs on every entry. Keep both. |
| **Q3** | `EmergencyStop` is cleared at each daily roll. A DD halt re-fires on the next bar if DD is still ≥ 10 %. | A recovery above the 10 % line (e.g. open trades recovering) re-enables trading. This is not a permanent kill switch. |
| **Q4** | The exposure cap compares **raw lots across different symbols** (1 lot EURUSD = 1 lot XAUUSD = 1 lot NAS100). The cap unit is the min lot of the *candidate* symbol. | This is already documented as a blocker in the exposure-cap memo (cap-neutral campaign 2026-10-03, no edge; no change justified). For index CFDs the outcome depends on a broker field **not yet recorded** (NAS100's `SYMBOL_CURRENCY_BASE`):<br>• if empty → **fail closed** (`EXPOSURE_CAP_INVALID_SPEC`);<br>• if = USD (= profit currency) → the USD leg is counted twice with opposite signs, so any candidate above 2 × 0.1 = 0.2 lot is blocked.<br>**Either way, H-ORB-1 on NAS100 may not trade through this engine unchanged.** Confirm with a read-only symbol-spec probe. This is a design decision for later, not now. |
| **Q5** | Risk = entry→stop at the broker calculation, **excluding commission and slippage** (consistent with DNA `result_r`). | Commission venues (FX ECN) carry more true risk than 0.30 %. Report it; don't change it. |
| **Q6** | Correlation is on the **chart timeframe** of the instance making the decision. | Must be passed in explicitly. |
| **Q7** | `EquityPeak` is lifetime (never reset at the roll). | Must persist across restarts and migrations; copy it at cut-over. |
| **Q8** | Trades are counted at **dispatch**, not at fill. | Keep. |
| **Q9** | Two margin caps: 50 % in sizing and 40 % in preflight. | The effective cap is 40 %. Keep both for parity of reason codes. |

## 8. Mapping onto NautilusTrader v2 (verified against the source in `vendor/nautilus_trader`, develop 5edd36e1)

- **The built-in `RiskEngine` covers only generic order hygiene.** `crates/risk/src/engine/config.rs` exposes:
  - `bypass`;
  - `max_order_submit` / `max_order_modify` rate limits;
  - `max_notional_per_order` per instrument;
  - `full_position_exit_venues`;
  - `debug`.
- `TradingState` = Active / Reducing / Halted (`crates/model/src/enums.rs`).
- **None of NEXA's policy (A1–A6) exists in Nautilus.** It is implemented as a NEXA pre-trade gate called by the strategy before `submit_order`, with the A2 halts mapped to `TradingState.HALTED`. Nautilus's own engine stays **enabled** (never `bypass`) as a second line.
- **The pure core** (`nexa_risk/`) has no Nautilus import, so the same code is used by research back-tests, Nautilus back-tests and live trading.
- **Account-level scope** (Q4, A4, A6 need *all* positions) must come from the venue account, not from Nautilus's per-strategy cache alone. Otherwise positions opened by MT5 / S14 on the same account are invisible. **Rule:** a Nautilus NEXA node never shares a trading account with S14.

## 9. Parity plan (Phase 1; nothing below runs without approval)

1. **Golden vectors from MQL5 pure functions.** `NexaCorrelationFromBars`, `NexaStopDistanceOK`, `NexaFreezeAllows`, `NexaClosedBarStale` and the C4 harness already compile as testable code. A test script, run in the **Strategy Tester only** (never on the S14 terminal), writes inputs and outputs to JSON. The Python port must match:
   - decisions and reason codes **exactly**;
   - numbers to 1e-9 relative.
2. **Sizing and budget vectors:** sweep (equity, stop distance, vol spec, DD level, open-position sets). Include every reject path in §4. Target ≥ 2,000 vectors, with every reason code hit at least once.
3. **Broker-calculation conformance:**
   - For each Pepperstone symbol in use, compare `lossToStop` / `marginFor` from the Python `InstrumentSpec` with MT5 `OrderCalcProfit` / `OrderCalcMargin` on recorded snapshots.
   - Tolerance: ≤ 0.5 % or 0.01 account currency.
   - For Dukascopy / cTrader, compare against that venue's own reported P&L on demo fills.
4. **Replay parity:** replay a recorded S14 decision journal (schema v1) through the port. Every `NO_TRADE_*` / `DISPATCHED_*` risk decision must reproduce. Any mismatch blocks Phase 2.
5. **Invariant tests in Python** (mirrors of the MQL5 invariants):
   - ceiling after rounding;
   - the throttle only reduces;
   - fail-closed on every unreadable input;
   - the lock is never released by a non-holder.

## 10. Open decisions (for the user, later; not needed to finish Phase 0)

- **D-R1:** the index-CFD currency rule for A4 (Q4). Needed before any NAS100 strategy can pass the engine. Options: (a) treat the profit currency as the only exposure leg; (b) a separate per-asset-class cap. Either is a **policy change** that needs approval and its own regression evidence.
- **D-R2:** keep the day roll at 17:00 New York for all venues (recommended, identical to S14) or adopt UTC (policy change).
- **D-R3:** whether the Python engine also owns layer B for MT5 (via the mt5 adapter) or MT5 keeps its own EA guards. Recommended: S14 stays as is until its forward check ends; Nautilus venues use the port.
