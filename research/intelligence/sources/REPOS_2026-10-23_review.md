# Repo and site review, 2026-10-23 (S85–S97)

**Request (chat):** "Check all this … 13 links attached, should be useful for NEXA, Do deep research."

**Method:**
- GitHub public API (metadata, file trees), READMEs, and targeted reads of the source files that decide what each tool really measures.
- Web checks of prices, rules and the research literature.
- **No code was installed or run.**
- Repo text is treated as claims, not facts.

## Verdict table
| # | Link | What it is | Stars / last push | For NEXA |
|---|---|---|---|---|
| S85 | mahmoud20138/OrderFlow-Analysis-Pro | Python footprint/delta/profile dashboard; 5 pattern detectors (absorption, initiative, sweep, exhaustion, divergence); MT5 + Bybit feeds; Telegram alerts | 74 / 2026-04 | **Ideas only.** No backtest of any detector. On CFD MT5 feeds it guesses the aggressor side (see below). |
| S86 | Azhagesan-dev/order-flow-chart | Flask + Lightweight-Charts footprint for NIFTY futures (Angel One API) | 34 / 2026-03 | **No.** Indian broker; a chart, not a signal. |
| S87 | silenccy/orderflow-station | Footprint, heatmap, DOM and an iceberg-refill flag for Indonesian stocks | 6 / 2026-10 | **No (data source).** Built on a **reverse-engineered private websocket** (its own warning), which breaks NEXA's no-reverse-engineering rule. Two design ideas are worth copying (below). |
| S88 | marketcalls/openalgo | Self-hosted multi-broker trading platform: REST API, strategy host, no-code flows, AI agent, options tools | 2,903 / 2026-10-22 | **No.** 36 broker plugins, all Indian plus one crypto exchange. No CME, Rithmic, Tradovate or ProjectX. AGPL-3.0. |
| S89 | FutuCopy/futucopy-api-dotnet | .NET client for a paid cloud trade copier (Rithmic, Tradovate, NinjaTrader, ProjectX, dxFeed) | 2 / 2026-06 | **Not needed now.** Topstep has a **built-in TopstepX trade copier** (Topstep blog; copies your own trades across your own accounts). A third-party cloud copier would also hold broker credentials. Revisit only for multi-firm copying after an edge exists. |
| S90 | roq-trading/roq-api | C++ interfaces for Roq's HFT gateways | 517 / 2026-10 | **No.** The implementation is closed-source and licensed (SLA pricing); it is built for exchange-colocated HFT. |
| S91 | rundef/async_rithmic | Python async client for Rithmic's Protocol Buffer API: ticks, best bid/ask, full L2, orders | 123 / 2026-10 | **Not usable at $0.** Production access needs a **Rithmic conformance test** (contact Rithmic, run an app on their test plant) plus credentials and fees through an FCM/broker. It would give real-time CME data, but not through a prop login without conformance. Keep for later. |
| S92 | rainshen49/citadel-trading-comp | 2018 student competition bot (cross-exchange and ETF arbitrage, news reaction) on a simulated exchange | 4 / 2018 (archived) | **No.** A simulator game, not a real market. |
| S93 | fintools-ai/mcp-options-order-flow-server | MCP front-end for options "sweeps/blocks/institutional bias" | 11 / 2025-07 | **No.** It needs a separate Go "data broker" and an unnamed market-data provider. No data, no evidence. |
| S94 | twolven/mcp-optionsflow | MCP that prices covered-call / put-spread strategies from Yahoo Finance with Black-Scholes | 40 / 2026-08 | **No.** Despite the name it has no options *flow*: it is a strategy calculator on delayed Yahoo chains. |
| S95 | kkrib412/options-flow-tracker | Tradier-API scanner: volume/OI ratio, "sweeps", put/call sentiment | 1 / 2026-08 | **No.** `scanner.py` labels any contract with premium above a threshold a "sweep" (`is_sweep = premium >= SWEEP_PREMIUM`). A real sweep is one order filled across several exchanges, which needs trade-level OPRA data that Tradier chains do not give. No licence. |
| S96 | unusual-whales/unusual-whales-official-mcp | Official MCP for the Unusual Whales API (200+ endpoints: options flow, dark pool, greek exposure, congress trades; CME futures time-and-sales as a premium add-on) | 93 / 2026-08 | **Paid; not now.** API Basic is **$150/mo**, Advanced (WebSocket, futures add-on) **$375/mo**, historical option trades **+$250/mo**. The free retail tier has flow delayed 2 trading days and no API. It breaks the $0 rule. |
| S97 | dataroma.com | Free tracker of "superinvestor" 13F portfolios and insider buys | site | **No.** Quarterly US stock holdings filed up to 45 days late. Nothing intraday, nothing on futures. |

## The two findings that matter

### 1. GEX data is not blocked any more, and it is free
- NEXA's dealer-gamma claims have been **BLOCKED-DATA** since the order-flow KB: CL-032 (positive gamma means chop, negative means expansion), CL-033 (zero-gamma line), CL-038 (dealer hedging drives SPX/NDX intraday), hypothesis OF-12, gap GAP-D08. The memory note says "GEX dashboard (Yahoo = no options data)".
- **QuantConnect's US Index Options dataset (AlgoSeek):**
  - covers **SPX, NDX (incl. NQX/NDXP weeklies) and VIX** options from **January 2012**;
  - minute trades and quotes plus daily **open interest**;
  - QC's page: "Free access … on the QuantConnect Cloud platform for research, backtest". The free node NEXA already uses can compute a daily net-gamma estimate from open interest.
- **What the research says** (checked 2026-10-23):
  - **Baltussen, Da, Lammers & Martens (2021, JFE), "Hedging demand and market intraday momentum":** short-gamma hedging trades with the move, which explains last-half-hour momentum.
  - **Dim, Eraker & Vilkov (SSRN 4692190, 0DTE study):** market makers' net gamma is on average **positive** and **predicts lower intraday volatility**. Positive gamma strengthens intraday **reversal**, negative gamma **momentum**. The evidence fits delta-hedging, not informed trading.
  - **Ni, Pearson, Poteshman & White (2021, RFS):** net gamma imbalance relates negatively to underlying volatility.
  - **Caution, "Does gamma survive the close?" (2026, Finance Research Letters):** daily-horizon gamma measured from trades is contaminated by vega. Open-interest gamma assumes who holds which side, which is a known weakness.
- **What it means for NEXA:**
  - NEXA's unconditional last-half-hour momentum test H-IM-NQ was **REJECTED** (−3.1 bp). The research says the effect lives on **negative-gamma days**. That conditional version was never tested: it was blocked by data, not rejected.
  - Separately, gamma may predict **how much** the day moves. That would be a better "expected range" for the v6 Risk & Range panel, and it is a volatility claim, not a direction call.
- **Candidates (not pre-registered; for the user's decision):**
  - **H-GEX-IM:** NQ/ES last-30-minute momentum only on days when the open-interest net gamma (from the previous close) is negative. QC 2012–2025, NEXA standard costs and pass bar.
  - **H-GEX-RANGE:** does previous-close net gamma improve the forecast of today's RTH range beyond the 10-day average already on the panel? Judged by out-of-sample error, no trading claim.
  - **Honest prior:** the last-half-hour family has already failed once, and open-interest gamma has a dealer-sign assumption built in. H-GEX-RANGE has the better chance, but it would only improve risk sizing, not create an edge.

### 2. Real-time CME data still has no $0 route
- Our recorder runs on dxFeed data delayed 15 minutes.
- The repos offer three real-time paths, none at $0:
  - **Rithmic:** conformance plus a broker.
  - **Unusual Whales futures:** $375/mo or more.
  - **Roq:** licensed.
- **Topstep's own TopstepX copier** removes the only practical reason for FutuCopy.

## Ideas worth copying (no code taken)
- **Capture-integrity panel** (orderflow-station):
  - logs every hole in the recorded tape (when, how long, why) and the share of the session captured;
  - breaks the CVD line where data is missing.
  - NEXA's recorder would benefit, because H-ICE-FEAS and the recorder decode depend on gap-free sessions.
- **Iceberg-style replenishment flag** (orderflow-station): marks levels that refill after being traded through, including a same-second refill that shows no net change on the ladder. This is the same idea as the sealed H-ICE-FEAS stat. Its definition can be compared with ours when H-ICE-FEAS is unsealed (≈ 2026-11-04). It must not be read before then.
- **Aggressor-side honesty** (OrderFlow-Analysis-Pro, `data/mt5_feed.py`):
  - it reads MT5 `TICK_FLAG_BUY/SELL`, and when they are missing it falls back to a price-vs-bid/ask guess;
  - CFD/forex feeds such as Pepperstone carry no exchange buy/sell flags (NEXA T1 validation, 2026-10-05), so on CFDs its "delta" is a guess;
  - its NAS100/SP500 "index futures" are CFD symbols, not CME contracts.

## Safety notes
- orderflow-station stores a live JWT in `subscribe_*.txt` and talks to a private API. Do not use it.
- Unusual Whales MCP setup sends a Bearer API key. Not set up; it would be paid anyway.
- No repo here was installed, and none needs to be.
