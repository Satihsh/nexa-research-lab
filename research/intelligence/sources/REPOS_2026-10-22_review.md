# User-supplied GitHub repos, batch 2026-10-22 (S66–S76): review

**Method.** GitHub public API (metadata, READMEs, file trees) and targeted reads of source files. **No code from these repos was installed or run.** One data file was downloaded into an isolated scratch folder and parsed with `python -I`: the s-k-28 published trade list. Repo text is treated as claims, not facts.

## Summary table
| # | Repo | What it is | Stars / age | Relevance to NEXA (NQ/ES futures, prop, ATAS, $0) | Verdict |
|---|---|---|---|---|---|
| S66 | HKUDS/Vibe-Trading | LLM "trading agent" over many markets (A-shares, US, crypto, brokers, chat channels) | 36k / since 2026-04 | Research assistant, not an edge. Its own changelog lists look-ahead and phantom-edge bugs fixed in Sept–Oct 2026 (a momentum factor read today's price; options backtests filled at the signal price). Warns about scam tokens using its name. | Not useful for NEXA; reading only |
| S67 | openbq-org/OpenBB (was OpenBB-finance/OpenBB) | Open data platform (Python, REST, MCP) | 74.5k / 2020 | Data plumbing; no free intraday futures history. **Ownership note below.** | Optional data tool; no action |
| S68 | microsoft/qlib | AI quant platform for daily cross-sectional stock factors | 49.6k / 2020 | Equity factor investing; needs capital, not prop. NEXA's intraday ML (H-ML1, H-FLOW-PRED) already covered the futures case. | Not relevant now |
| S69 | stefan-jansen/machine-learning-for-trading | Code for the ML4T book, 3rd ed. | 21.5k / 2018 | Good reference. NEXA already uses its core methods (purged walk-forward, triple-barrier labels, placebo). | Reference only |
| S70 | hummingbot/hummingbot | Crypto market-making / arbitrage bots | 20.6k / 2019 | Crypto exchanges, automation; outside futures-prop scope | Not relevant |
| S71 | StockSharp/StockSharp | C# trading platform with many broker connectors | 10.9k / 2014 | Alternative to ATAS for C#; user is committed to ATAS; custom licence | Not relevant now |
| S72 | LuxAlgo/prop-firm-sim | Monte Carlo of prop-firm challenges from exact rules, block bootstrap of real R-multiples, MIT | 94 / 2026-08 | **Useful cross-check** for NEXA's H-PROP-EV engine (same questions: pass odds, EV after fees, trailing-DD variants). Running it needs `npx` (an install, so user approval). | Worth a cross-check |
| S73 | s-k-28/nq-es-trader-5k-payout | 12-model MNQ intraday system for Topstep, Monte Carlo, live bots (TopstepX, IB) | 26 / 2026-05 | **Most relevant.** Strongest in-sample number NEXA has seen, but in-sample and cost-sensitive (below). | **Candidate for a true out-of-sample test** |
| S74 | Kza56/OFK_Atas_GEX | ATAS indicators + Python pipeline for options GEX/DEX levels on NQ/ES, AI briefing | 44 / 2026-05 | GEX levels and a context score with **hand-set weights, no backtest**. Scrapes CME with Playwright (conflicts with NEXA's no-scraping rule) and ships a **precompiled DLL** to load into ATAS. Non-commercial licence. | Do not install; idea only |
| S75 | Ax3lsk3r3/atas-mcp | MCP bridge: ATAS ↔ AI agents (quote, DOM, candles, positions, **orders**) | 7 / 2026-09-15 (single day) | Read-only DOM access is exactly what NEXA lacks. But the **order endpoints are unauthenticated** (below). NEXA rule: Claude never places orders; Apex bans automation. | **Do not install as is** |
| S76 | giovannibrusco/zarattini-2024-momentum-spy | Disciplined replication of Zarattini/Aziz/Barbon 2024 noise-area momentum (SPY + ES) | 4 / 2026-07 | Independent confirmation of NEXA's CFT result: the same trend layer has been flat since 2025. Pre-registered protocols, Deflated Sharpe, publishes failures. | Corroborates NEXA; keep |

## S73 s-k-28: the numbers checked
- **README claims (simulated, not live):** 2,716 trades from Dec 2022 to May 2026, +0.238R per trade, PF 1.66, 93.7 % evaluation pass rate.
- **Costs in the engine:**
  - only 0.25 tick of slippage on non-target exits (`backtest/engine_v2.py`);
  - **no commission and no entry slippage**.
- **"Walk-forward"** = prior years used "only as regime warmup". **No refit.**
  - The 12 models were built and tuned over 78 commits on the same 2022–25 data.
  - The repo even contains `trades_optimized.csv`.
  - Ambiguous bars (stop and target in one minute) go to whichever is nearer the bar's open, not stop-first. This was rare (3 of 2,280 trades), so it matters little.
- **Re-priced with NEXA's standard costs**, using their own published `data/trades_backtest_full.csv`: 2,280 trades, 2022-12-28 → 2025-12-11.

| Cost per round trip | Net R per trade | 95 % CI (iid bootstrap) |
|---|---|---|
| none (as published) | +0.420 | — |
| S0 = 1 NQ point | +0.280 | [+0.219, +0.347] |
| **S1 = 2 points (NEXA standard)** | **+0.141** | [+0.079, +0.209] |
| S2 = 3 points | +0.001 | [−0.061, +0.070] |

- **Why costs dominate:** the stops are tight (median 8.2 points, p10 4.3, p90 14.5), so 2 points of cost ≈ 0.24R per trade.
- **Per year at S1:** 2023 +0.079, 2024 +0.123, 2025 +0.250.
- **Per model at S1:** ou_rev +0.38 … pm_mom −0.14.
- **Reading:**
  - In-sample, built on these very years, with costs that decide the sign. This is not evidence of an edge, but it is the strongest in-sample candidate NEXA has seen. Every earlier NEXA rule that looked good in-sample failed out of sample.
  - **The honest test:** the author never saw NQ before Dec 2022. Running the frozen 12 models on QuantConnect NQ 1-minute data 2010-01 → 2022-11 (free) at S0/S1/S2 is a true out-of-sample test. It needs a pre-registration and the user's approval (a new hypothesis, ≈ 1–3 trials).
- **For the user's plan:** the system is an automated bot (TopstepX API / IB). Apex bans automation. Trailing stops and partials at this speed (4–8 pt stops on 1-minute bars) are hard to execute by hand.

## S75 atas-mcp: security finding
- `ATAS.McpBridge/McpBridgeStrategy.cs` runs an `HttpListener` on `localhost:8787` and `127.0.0.1:8787`.
- `POST /api/order`, `/api/order/cancel` and `/api/position/close` have **no token, no Origin check and no content-type check**; the body is read whatever its type.
- So any program on the PC can place, cancel or flatten orders. A malicious web page might also manage it: a browser "simple" POST to 127.0.0.1 reaches the listener unless Chrome's local-network protection blocks it.
- The README also suggests `netsh http add urlacl … user=Everyone`.
- **Safe use, if ever:** a read-only fork with the order routes deleted. Better still: add a DOM snapshot to NEXA's own read-only recorder. The ATAS licence §6 question still applies to exporting data.

## S67 OpenBB: ownership note
- `OpenBB-finance/OpenBB` now **redirects** (HTTP 301) to the same repository id 323048702 under **openbq-org**. That org was created 2026-09-11, is unverified, and has no name or website. The old OpenBB-finance org still exists.
- **Signs of a deliberate transfer:**
  - GitHub's own redirect, which only the repo's admins can create;
  - the long-time maintainer (deeleeramone) still commits, and commits are verified;
  - the new org holds `openbb-brightquery`, and some maintainers use `-bq` names (BrightQuery?).
- **No public announcement found.** Treat it as probably legitimate but unconfirmed. Install only the `openbb` package from PyPI, never lookalike names.

## Links to NEXA results
- S76 matches CFT stage A (Zarattini 2024 trend layer: ES −0.88 bp/day, NQ +0.13, 2024-05 → 2026-07). Two independent tests now agree that the edge compressed after 2024.
- S74's GEX idea remains untestable on history at $0 (no free futures-options history). Only a forward-collected dataset is possible: CBOE delayed SPX/NDX chains, not CME.

## Suggested next steps (need the user's decision)
1. **H-SK28-OOS:** pre-register a test of the frozen s-k-28 models on NQ 2010-01 → 2022-11 (QuantConnect, free, one run). Verdict bar: H-PROP-EV, at least +0.025R net at S1 with CI > 0.
2. **Cross-check H-PROP-EV** with LuxAlgo prop-firm-sim (needs `npx` install approval).
3. Nothing else from this batch should be installed.

## S77 nkaz001/hftbacktest (added 2026-10-22, user question "have we checked this?")
- **Status before today:** listed in S65's upstream link list only (`S65_awesome_systematic_trading/README_upstream.md` line 156), **never reviewed**.
- **What it is:**
  - an HFT / market-making backtester (Rust core, Python Numba API, MIT);
  - 4.9k stars, since 2022, last commit 2025-12-23, PyPI `hftbacktest` 2.4.4;
  - simulates feed and order latency and **queue position** for limit-order fills, rebuilding the book from **L2 (market-by-price) or L3 (market-by-order)** tick data;
  - live bots for Binance Futures and Bybit only.
- **Fit to NEXA:**
  - It is the right kind of tool for the DOM-level ideas: absorption, icebergs, book imbalance (it has an order-book-imbalance tutorial), and NEXA's untestable "family C full depth".
  - But it needs L2/L3 history, which NEXA does not have at $0 (QC = top of book; Databento MBO = paid; the NEXA recorder = trades plus delayed feed, a few sessions).
  - Market making / HFT itself is not reachable for a retail prop trader: latency, exchange fees, and prop rules on automation.
- **Safety:** an established project; safe to install if ever needed.
- **Verdict:** keep on file. Revisit only if NEXA obtains MBO/L2 history (e.g. a long recorder tape with DOM, or an approved paid sample). No install now.

## Batch 2 (2026-10-22, S78–S84)
| # | Repo | What it is | Stars / age | Verdict |
|---|---|---|---|---|
| S78 | aleks-drozy/fyp-trading-strategy (+ successor fyp-strategy-engine) | University final-year project: ICT IFVG + CISD on NQ 09:32–10:00, Pine Script | 2 / 2026 | **Honest negative, corroborates NEXA.** In-sample 2025–26: 72 trades, PF 1.70. Out of sample 2023–24: 95 trades, PF 0.90. The successor's pre-registered six-phase study on ≈ 10 years of ES, YM and NQ ends **DISPROVEN** (pooled PF 0.905, 90 % CI [0.810, 0.996]). |
| S79 | simoncampos1022/profitable-futures-trading-strategy-crypto-forex-stock ("Botara 3.0") | Crypto/forex bot advert | 23 / 2025-11 | **Marketing, not research.** No code in the repo (HTML, CSV, images only). All entry/exit levels hidden as "?". "2+ months of successful live trading" is unverified. 40 % of balance at 5× leverage per position. Avoid. |
| S80 | tschm/jsharpe | Probabilistic Sharpe ratio, minimum track record length, FDR/FWER corrections (López de Prado) | 25 / 2025-11, active | **Useful later**, as a cross-check of NEXA's multiple-testing statistics (ledger ≈ 177 trials) and for "how long must H-DISC1 run". MIT, pure Python. Not needed now; install only with approval. |
| S81 | MarcosACH/quant-strategies | WIP backtest framework, CVD + Bollinger on BTC perpetuals, QuestDB + Docker | 2 / 2025 | Unfinished, crypto, heavy setup. Not useful. |
| S82 | freqtrade/freqtrade | Crypto trading bot (spot and crypto perpetual "futures"), GPL-3.0 | 55.7k / 2017 | Mature and safe, but **crypto only**: no CME, no prop firms. Not relevant. |
| S83 | freqtrade/freqtrade-strategies | Community strategies for freqtrade | 5.6k / 2018 | Its own README calls them "a starting point… not ready to use" and warns that results depend on tuning. Crypto. Not relevant. |
| S84 | mementum/backtrader | Classic Python backtesting library, GPL-3.0 | 23.5k / 2015; last push 2024-08 | Works with futures bars (and Interactive Brokers), but **unmaintained**. NEXA already backtests on QuantConnect/LEAN and its own engines. No need. |

### S77 note: "free"
hftbacktest's "free" means the **software** is free (MIT). The CME order-book data it needs is not: it ships a Databento converter (`hftbacktest/data/utils/databento.py`) for paid MBO data. Its free sample data is crypto (Binance/Bybit).

### Data check prompted by S78 (relevant to S73 s-k-28)
- The FYP successor reports a **±60-minute DST bug, intra-day splices and fast-market infidelity** in a file called `Dataset_NQ_1min_2022_2025.csv`. s-k-28 trains on a file of the same name.
- **Check of s-k-28's copy** (72.5 MB, 766 days, timestamps "ET"): the RTH-VWAP reset is at 09:31 on every day.
  - The 09:31 volume jump is ≥ 3.9× in every month; 10:31 is never a spike.
  - Only 4 days lack a 09:31 spike, and all are 08:30 news days (2023-04-07 Good Friday jobs report, 2023-12-15, 2024-03-15, 2024-11-15).
  - ⇒ **no hour shift at the open in s-k-28's copy.** Splices and fast-market bars were not checked.
- **Methodological note:** both s-k-28 and the FYP project took their in-sample edges from the same 2022–25 data; the FYP one failed on independent data. This raises the prior that H-SK28-OOS would fail too.
