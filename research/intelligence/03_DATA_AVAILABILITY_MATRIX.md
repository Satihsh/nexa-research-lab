# 03: DATA AVAILABILITY MATRIX

All entitlement facts below are **MEASURED**: live calls made on 2026-10-04 with the connected Massive MCP and the local MT5/Pepperstone archive. Nothing here is inferred from documentation alone.

**Status codes:**
- **AVAILABLE:** observed directly at the needed resolution.
- **DERIVABLE:** computable exactly from available data.
- **APPROXIMABLE:** only a proxy is computable; the proxy's error is unknown or partly measured.
- **UNAVAILABLE:** not obtainable with the current subscriptions.

## 1. Sources actually held or reachable

| Source | What exists (measured) | History | Resolution | Timestamps | Notes |
|---|---|---|---|---|---|
| **MT5 Pepperstone M1 bars** (`data/pepperstone/m1_canonical/`) | OHLC, `tick_volume`, `spread` (points) for EURUSD, GBPUSD, USDJPY, XAUUSD, XAGUSD | 2017-06-30 → 2026-09-25 (EURUSD: 3.43M rows) | 1 minute | Server time (NY+7, US DST) plus derived `time_utc` and `utc_offset_h` | Spread is the bar-close spread. Tick volume counts quote updates |
| **MT5 Pepperstone ticks** (`*_ticks_recent.csv.gz`) | `time_msc`, bid, ask. **`volume` = 0 and `last` = 0 on every tick** (EURUSD 2.46M, XAUUSD 10.84M). Flags: 2/4/128/1024 only. **No `TICK_FLAG_BUY` (32) or `SELL` (64) ever** | About 28 days (2026-08-28 → 09-26) | Quote update | ms | **Quotes only: no trades, no aggressor side, no size** |
| **MT5 live terminal** | Symbol specs; XAUUSD reports `ticks_bookdepth = 10` (a broker book of depth 10 may be offered live) | Live only; no history | Event | ms | Broker DOM = the broker's aggregated LP quotes, **not** an exchange book. It would have to be logged forward to be usable |
| **Trade DNA** (EA journal) | Decisions, f00–f47, fills, slippage (signed since S14), commission, swap | Tester 2024–2026; **live demo from 2026-10-05** (S14 forward check) | Per decision bar / event | decision, dispatch, fill, label ts | **Own execution microstructure is AVAILABLE prospectively** |
| **Massive FX aggregates** `C:EURUSD…` | OHLC, `v`, `vw`, `n`. **`v == n` (quote-update count), not traded volume** | **2024-10-04 → present** (2024-09-30 NOT_ENTITLED, 2024-10-07 OK) | 1 minute | UTC ms, bar start | A second (aggregated) quote source. **Not a trade source** |
| **Massive FX quotes / ticks** `/v3/quotes`, `/v1/historic/forex` | **NOT_ENTITLED** | — | — | — | — |
| **Massive futures aggregates** `/futures/v1/aggs` (GC, 6E, 6B, 6J, ES, …) | OHLC, **`volume` (contracts, exchange-reported)**, `transactions`, `dollar_volume`, settlement | **≈ 2 years** (GCZ4 on 2024-10-07 OK) | **1 minute finest**; `1sec` is NOT_ENTITLED | `window_start` ns UTC; `session_end_date` | **Real centralised volume.** Contract-specific: needs a roll calendar |
| **Massive futures trades / quotes / snapshot** | **NOT_ENTITLED** | — | — | — | **No aggressor side, no BBO** |
| **Massive stocks/ETF aggregates** (SPY, GLD, FXE, …) | OHLC, `v` (shares), `vw`, `n` | About 2 years | 1 minute | UTC ms | Equity trades and quotes NOT_ENTITLED |
| **Massive options reference** `/v3/reference/options/contracts` | Contract list incl. **expired** (GLD 2025-03-21 chain enumerable) | About 2 years plus listings | — | — | American style for GLD |
| **Massive options aggregates** (per contract) | OHLC, `v` (contracts), `n`, daily open/close | About 2 years (GLD Nov-2024 chain OK) | 1 minute and daily | ET-based bars | **Unsigned volume. No OI** |
| **Massive options snapshot / quotes / trades / greeks / IV / OI** | **NOT_ENTITLED** (GLD chain snapshot, contract trades) | — | — | — | **No open interest at any horizon** |
| **Massive indices** (`I:VIX`) | **NOT_ENTITLED** | — | — | — | — |
| **Massive economy** `/fed/v1/treasury-yields` (+ inflation, funding) | Daily US Treasury curve 1M–30Y | Back to 1962 (per docs; 2026-10-01 row observed) | Daily | Date | Usable for rate/carry context |
| **Massive Black–Scholes functions** | `bs_price`, `bs_delta`, `bs_gamma`, `bs_vega`, `bs_vanna`, `bs_volga`, … | — | — | — | **No IV solver.** IV must be inverted locally |
| **MT5 economic calendar** (`data/pepperstone/calendar`) | Event times (export-offset caveat in memory) | NEXA archive | Event | Export-time offset issue | Parity-exempt (f47) |

**Measured proxy-validity probes (2026-10-04)** (`evidence/volume_proxy_check*`, `evidence/profile_proxy_check*`)

| Probe | n | Result |
|---|---|---|
| COMEX GCZ6 hourly volume vs Pepperstone XAUUSD hourly tick volume | 456 h | log r = **0.822**, Spearman 0.812; **with hour-of-week mean removed r = 0.668**; hour-of-day profile r = 0.929 |
| COMEX GCZ6 transactions vs XAUUSD tick volume | 456 h | log r = 0.842; de-seasonalised **0.695** |
| CME 6EZ6 volume vs EURUSD tick volume (2026-09-15 → 09-25, post-roll) | 136 h | log r = **0.881**; de-seasonalised **0.567** |
| Massive C:EURUSD quote count vs Pepperstone EURUSD tick volume | 136 h | log r = 0.911; de-seasonalised 0.521 |
| Daily volume profile, POC and 70 % VA (COMEX volume vs XAU tick volume, basis-shifted) | 20 days | **POC within $2 on 65 % of days; misses of $12–68 on 4 bimodal days**; VA Jaccard median **0.82** (range 0.53–1.00) |
| GCZ6 − XAUUSD basis (median of hourly differences) | 20 days | **+49.7 → +35.1 USD** across 2026-08-31 → 09-25 |

## 2. Concept-by-concept matrix (directive §3, eleven questions)

**Column key**
- **Q1–Q4:** Massive direct (Q1), Massive derivable (Q2), MT5 derivable (Q3), both (Q4). Given as one status code.
- **Freq:** best sampling frequency.
- **Depth:** history.
- **TS/TZ:** timestamp and timezone.
- **Pre-dec?:** observable before decision_ts (Q9).
- **Bias:** survivorship or look-ahead risk (Q10).
- **Reliab.:** reliable enough for backtesting? (Q11).
- **T/P:** TRUE data or PROXY.

| # | Concept | Status | Source | Freq | Depth | TS/TZ | Pre-dec? | Bias risk | Reliab. | T/P |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Spot price (bid/ask) for NEXA's instruments | AVAILABLE | MT5 ticks/M1 | tick / 1 min | ticks 28 d; M1 9 y | server→UTC (D-TZ fixed) | yes | none | high | TRUE (the broker's own quote) |
| 2 | Spread | AVAILABLE | MT5 | tick / bar close | as above | as above | yes | bar spread = close snapshot only | medium | TRUE |
| 3 | Traded volume, spot FX/XAU | **UNAVAILABLE** | — | — | — | — | — | — | — | — |
| 4 | Activity proxy (tick volume) | AVAILABLE | MT5 M1 | 1 min | 9 y | as 1 | yes | broker feed changes over years (non-stationary) | medium | **PROXY**: measured hourly r ≈ 0.82–0.88 vs exchange volume; ≈ 0.57–0.70 after de-seasonalising |
| 5 | Exchange volume (gold, FX futures) | AVAILABLE | Massive futures aggs | 1 min | ≈ 2 y | ns UTC | yes, if bar closed ≤ decision time | **roll** (contract choice); futures-spot basis | high | TRUE for futures; **PROXY for spot** via basis |
| 6 | Transactions count (futures) | AVAILABLE | Massive | 1 min | ≈ 2 y | ns UTC | yes | as 5 | high | TRUE |
| 7 | Average trade size V/N (futures) | DERIVABLE | Massive | 1 min | ≈ 2 y | — | yes | as 5 | high | TRUE (aggregate) |
| 8 | Bid/ask (BBO) quotes, futures | **UNAVAILABLE** | NOT_ENTITLED | — | — | — | — | — | — | — |
| 9 | Aggressor-signed volume ("delta"), true | **UNAVAILABLE** | needs trades with side or quote matching | — | — | — | — | — | — | — |
| 10 | Delta proxy: tick rule on spot quotes (NEXA f30/f31) | APPROXIMABLE | MT5 ticks | tick | 28 d history (live only beyond) | ms | yes | **non-reproducible offline** (parity-exempt) | low | PROXY (quote direction ≠ trade direction) |
| 11 | Delta proxy: bulk-volume classification (BVC) on futures 1-min bars | APPROXIMABLE | Massive futures | 1 min | ≈ 2 y | ns UTC | yes | **same-bar circularity**: proxy sign derives from the same bar's return | unvalidated | PROXY (EXTERNAL method: Easley, López de Prado & O'Hara 2012) |
| 12 | Cumulative delta | APPROXIMABLE | from 10 or 11 | as source | as source | — | yes | inherits | low | PROXY |
| 13 | Footprint (bid×ask per price), imbalances, stacked imbalances, "unfinished business" | **UNAVAILABLE** | needs per-trade price and side | — | — | — | — | — | — | — |
| 14 | Limit-order flow / cancellations (S51) | **UNAVAILABLE** | needs an order book | — | — | — | — | — | — | — |
| 15 | Order-book depth / imbalance / microprice | **UNAVAILABLE** historically. APPROXIMABLE *prospectively* for XAU only, if the broker DOM (depth 10) is logged forward | MT5 live | event | none | ms | yes (if logged) | broker-specific, not an exchange | unknown | PROXY (broker book) |
| 16 | Volume profile (volume at price) | DERIVABLE (futures, true volume) / APPROXIMABLE (spot, tick volume) | Massive futures; MT5 M1 | 1-min bins (intra-bar distribution unknown; typical-price or uniform-over-range assignment) | 2 y / 9 y | — | yes, if built only from closed bars | bin assignment within a bar is an approximation | VA: good (Jaccard 0.82); **POC: fragile** | futures TRUE; spot PROXY |
| 17 | TPO (time) profile | DERIVABLE | MT5 M1 or Massive | 1 min | 9 y | — | yes | none | high | TRUE (time-at-price is exact from bars at bar resolution) |
| 18 | Delta profile (signed volume at price) | APPROXIMABLE only (from 11) | Massive | 1 min | 2 y | — | yes | inherits 11 | unvalidated | PROXY |
| 19 | Market structure (swings, BOS, sweeps, FVG) | DERIVABLE | MT5 M1 (existing f00–f19, f32–f46) | bar | 9 y | — | yes (parity-verified) | swing confirmation lag must be respected | high | TRUE (as defined) |
| 20 | Realised volatility (YZ, Parkinson, RV) | DERIVABLE | MT5 M1; Massive | 1 min → any | 9 y | — | yes | weekend/rollover gaps (H-GAP-VOL) | high | TRUE |
| 21 | Implied volatility, gold | APPROXIMABLE: GLD option bar closes → BS inversion (American; stale last-trade prices; no quotes) | Massive options aggs + GLD aggs | 1 min / daily | 2 y | ET bars | yes | **stale-print bias**; early-exercise model error | low–medium | PROXY (ETF, not COMEX OG) |
| 22 | Implied volatility, FX | APPROXIMABLE only via FXE/FXB/FXY ETF options (thin) | Massive | daily | 2 y | — | yes | illiquidity | low | PROXY |
| 23 | IV skew / term structure | APPROXIMABLE (from 21) | Massive | daily | 2 y | — | yes | as 21, amplified at the wings | low | PROXY |
| 24 | Option volume by strike/expiry | AVAILABLE (unsigned) | Massive options aggs | 1 min / daily | 2 y | ET | yes | listing/expiry survivorship: enumerate via reference with `expired=true` | medium | TRUE for GLD/ETF options; PROXY for gold/FX |
| 25 | **Open interest** | **UNAVAILABLE** | snapshot NOT_ENTITLED; no historical OI endpoint entitled | — | — | — | — | — | — | — |
| 26 | Greeks (delta, gamma, vanna, charm) | DERIVABLE from 21 plus contract terms (Massive `bs_*` functions or local) | Massive | — | 2 y | — | yes | inherits 21 | low | PROXY |
| 27 | **Dealer positioning / GEX / gamma flip** | **UNAVAILABLE**: needs OI (25), and the sign needs signed flow (S50/S54) | — | — | — | — | — | — | — | — |
| 28 | "Volume-GEX" (S53 volume toggle): Σ Γ·volume (unsigned) | APPROXIMABLE (GLD only) | Massive | daily / intraday | 2 y | — | yes, prior-day or intraday-to-date only | not positioning; sign undefined | very low | PROXY of a proxy |
| 29 | Call/put walls, pins, max pain | **UNAVAILABLE** (need OI). A volume-based analogue is only APPROXIMABLE (28) | — | — | — | — | — | — | — | — |
| 30 | Native COMEX gold options (OG) | **UNAVAILABLE** (Massive futures API has no futures-options endpoint; S53 uses the Sierra/Denali feed) | — | — | — | — | — | — | — | — |
| 31 | Cross-asset: USD basket (NEXA f29), rates, gold–FX | DERIVABLE | MT5 (basket), Massive treasury yields | 1 min / daily | 9 y / decades | — | yes (time-aligned since S13) | — | high | TRUE |
| 32 | Equity-index context (ES futures volume and price) | AVAILABLE | Massive futures | 1 min | 2 y | ns UTC | yes | roll | high | TRUE |
| 33 | VIX / index levels | **UNAVAILABLE** (`I:` NOT_ENTITLED). VX futures not probed | — | — | — | — | — | — | — | — |
| 34 | News / macro calendar | AVAILABLE with an offset caveat | MT5 calendar | event | archive | export-time offset | yes, if the corrected offset is used | timestamp offset (memory) | medium | TRUE (with fix) |
| 35 | Own execution: slippage, latency, requotes, fills | AVAILABLE **prospectively** (S14 demo, from 2026-10-05) | Trade DNA + tick logger | event | from now | ms | — (labels) | demo ≠ live | medium | TRUE (demo venue) |

## 3. Causality rules per source (Q9)

**Decision clock (NEXA convention):**
- The decision row is labelled by `decision_ts`, the open time of the *closed* decision bar B = [t, t+Δ).
- Features may use information timestamped **< t + Δ**. The order is sent **no earlier than the first tick ≥ t + Δ** (EDGE-1 oracle, 2026-10-03).
- *Documentation note:* the schema's sentence "computable from data at or before [decision_ts]" should be read as "at or before the decision bar's close". The bar's own close is used by every bar-based feature.

**Rules by source**
- **Massive futures 1-min bar:** usable for decision time T only if `window_start + 60 s ≤ T`. `session_end_date` must never be used intraday; it is the *settlement* date.
- **Massive FX and options aggregates:** `t` is the bar *start* (ms). The same + 60 s rule applies. **Daily option bars are ET-session bars:** a daily bar for date d is usable only after 16:15 ET on d (options close).
- **Settlement prices and daily OI** (if ever acquired) are published **after** the session. Use for the *next* session only.
- **Volume profile at time T:** built only from bars closed before T. A "developing" profile is allowed; the completed-session profile is used only after the session ends.
- **Basis for mapping futures levels to spot:** estimate from contemporaneous closed bars only (rolling median of F − S over the last k hours). Never use the day's full median (our probe used the full-day median for *measurement*, which is acceptable only for a descriptive probe).

## 4. Survivorship and look-ahead traps specific to these data

1. **Futures roll:** a "continuous" series built with knowledge of future volume (the roll on the day volume crosses over) is look-ahead. **Roll on a pre-declared calendar rule** (e.g. N business days before last trade, or the prior session's OI/volume crossover).
2. **Option chain enumeration:** use `/v3/reference/options/contracts?expired=true`. Listing a chain "as of" a past date must not include strikes listed later.
3. **Same-bar flow proxies** (BVC, tick rule): the proxy is a function of the bar's own return, so its correlation with that return is mechanical. **Only lagged proxies may enter predictive features.**
4. **Profile POC instability:** POC is an argmax and can jump between modes. Prefer VA bounds, density functionals or smoothed modes (06).
5. **Broker feed regime changes:** tick volume and spread series across 2017–2026 may change with LP or feed configuration. Normalise by rolling or hour-of-week baselines, and test stability by year.
6. **Two-year Massive window:** every futures- or options-derived feature has **at most about 2 years** (2024-10 → 2026-10).
   - That overlaps NEXA's windows A2024Q4 (partial) through B.
   - **A frozen holdout must be carved from inside this span, or collected prospectively.** V2's 2027 OOS is not available to this programme.

## 5. Bottom line by directive component

| Component | NEXA can measure it | How |
|---|---|---|
| A Price | **YES** | MT5 (true) |
| B Volume | **PARTIAL** | Spot: tick-volume proxy (validated, moderate). Futures: true volume (2 y) |
| C Order flow / D Delta | **NO** (true) / PROXY only | Quote-direction (f30/f31) or futures BVC (unvalidated) |
| E Volume profile | **YES** (futures, true; spot, proxy with VA ≈ COMEX) | Bars |
| F Delta profile | **PROXY only** | From BVC |
| G Liquidity (resting) | **NO** | No book. Only *revealed* liquidity (traded volume at price) |
| H Market structure | **YES** | Existing f00–f46 |
| I Options flow / J Options structure | **WEAK PROXY** (GLD unsigned volume, derived IV) | Massive options aggs |
| K GEX / L–M Walls / N Dealer hedging | **NO** | Need OI plus the sign |
| O Volatility, P Momentum, Q Mean reversion, R Regimes, S Session | **YES** | Bars |
| T Intermarket | **YES** (FX basket, gold, ES, Treasuries) | MT5 + Massive |
| U Statistical relationships | **YES** | — |
| V Execution microstructure | **YES, prospectively** | S14 demo plus tick logger |
| W Historical analogues | **YES** (bars) | — |
| X Behavioural patterns | **Only as defined statistics** | — |
