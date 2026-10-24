# NEXA: platform-agnostic quant agent: architecture audit, options and phased roadmap

**Date:** 2026-10-12.

**Request:** the user's vision of a platform-agnostic quantitative trading agent. Research and planning only: no code, no changes to the running system.

**Constraints:**
- The frozen risk engine (NEXA_Risk `a43d8328`) stays unchanged.
- The S14 forward check (GCP VM, until ≤ 2026-12-07) stays untouched.
- V2 stays sealed (seq 11448).
- All research evidence is preserved.

## 1. Audit: what NEXA is today

| Layer | Today | Assessment |
|---|---|---|
| **Live strategy + risk + execution** | One MQL5 EA (`NEXA_EA.mq5` + 10 `.mqh`, ≈ 3,850 lines): features, liquidity engine, intelligence (ONNX veto seam), frozen `NEXA_Risk.mqh`, `NEXA_Safety`, `NEXA_FillGuard`, position management, FOMC gate | **Tightly coupled to MT5.** Strategy, risk and execution live in one binary. Well tested and safe, but every venue other than MT5 means a rewrite |
| **Research engine** | Python, 76 modules in `filesnexa/NEXA/research`: hash-chained pre-registration registries (`nexa_registry2`), execution simulator (`nexa_execution`), statistics (`nexa_stats`, `nexa_robust`: DSR / PBO / bootstrap), time / calendar, parity oracle (MQL5 ↔ Python, window-B PASS), V2 / 8E campaigns. Plus one bespoke script per hypothesis in `research/intelligence/validation` (`of_common` shared) | **Strong discipline, slow throughput.** Each hypothesis = new script + new data handling + new tests. That is the "wasting time" the user feels |
| **Market data** | Manual: MT5 terminal under Wine → `tools/pepperstone_*.py` exports → canonical M1 CSVs; Databento python client (metered; credit used); Massive / Alpha Vantage connectors (limited plans) | **The biggest bottleneck.** Exports need a GUI terminal and approvals, risk the 24 GB download trap, and cover 5 Pepperstone symbols only |
| **Strategy ↔ live parity** | The strategy exists twice (MQL5 + Python oracle), with a parity contract | Costly. Every change must be made twice and re-proven |
| **Ops** | GCP Windows VM (S14), heartbeat → Cloud Logging, 30-min alert, view-only Claude connector, off-machine registry artifact | Good foundation for an always-on node |
| **Source control / backup** | **The project is not a git repository.** Time Machine is failing | Critical gap (also the backup gap) |
| **Agents** | `agents/astra.py`, `opus.py` (legacy LLM debate) | Not part of the trading path |

**Core diagnosis:**
- NEXA's research quality is high, but the system is **single-venue (MT5 / Pepperstone CFD)** and **hand-cranked (data and tests are manual)**.
- The evidence shows the edges in the user's material live on **other venues / instruments** (index futures, US equities) with lower cost-to-range. NEXA cannot reach them.

## 2. The user's idea, evaluated

**Verdict: right direction, with three clarifications.**
1. **Platform-agnostic does not create edge.** It lets NEXA (a) test where edges are documented and costs are low, and (b) run one codebase for backtest and live.
2. **The biggest win is automating data + research**, not execution adapters. That is where weeks are lost; automation turns a 2–3 day hypothesis cycle into hours.
3. **"Complete this week" is not realistic for a multi-venue platform.** It is realistic for decisions, accounts, the repo / backup and the architecture contract (Phase 0).

## 3. Options for the core engine

| Option | What it is | Pros | Cons | Fit |
|---|---|---|---|---|
| **A. NautilusTrader** (open source; Rust core + Python) | Event-driven engine. **Same strategy code in backtest and live**; Parquet data catalog | Free. Official **Databento** (CME, US equities) and **Interactive Brokers** (equities, futures, FX, CFDs, options) adapters plus many crypto venues. Custom adapters are supported (Python), so a cTrader / Pepperstone adapter is buildable. Runs on Linux / macOS / Docker | No official MT5 or cTrader adapter (must be written). Learning curve | ⭐ **Recommended core** |
| **B. QuantConnect LEAN / cloud** | Hosted (or local LEAN) platform with an **official MCP server (60+ tools: write, backtest, optimise, deploy)** | Fastest automation out of the box; data included; many brokers (IBKR, OANDA, Alpaca, TradeStation, Tastytrade, Schwab, Binance, Bybit …) | **Paid node required for the MCP** (free A-MICRO can't). Cloud lock-in. **No Pepperstone / MT5.** Our registry and gate discipline would need re-implementing on top | Good **second opinion / rapid prototyping** tool, not the core |
| **C. Custom from scratch** | Write our own abstraction | Total control | Months of work re-inventing A | ✗ |
| **D. Stay MT5-only** | Current | Zero migration | Cannot reach the venues where edges are documented; manual data | ✗ for the vision (keep only for S14) |

## 4. Connectors needed (by layer)

### Market data (automated ingestion)

| Connector | Covers | Cost | Status |
|---|---|---|---|
| **Dukascopy public datafeed** (python `dukascopy-python`, or a `.bi5` downloader) | ≈ 20 y of FX, metals, energy and **index CFDs (USATECH / NAS100, USA500, USA30)**: tick → M1 with bid / ask spread | **Free**, no key | New (no account) |
| **cTrader Open API** (Spotware; Pepperstone offers cTrader) | **Pepperstone's own** prices: M1 trendbars, ticks (≤ 1 week per request), live spots, depth. Works on macOS / Linux (no Wine). Python SDKs exist | Free (needs a cTrader demo + an Open API app) | New. **Replaces manual MT5 exports** |
| **Databento** (python client; have) | CME futures (NQ / ES / 6E / GC), US equities, true order flow | Metered; credit nearly used. **Standard plan $199/mo** for live CME (raised 2026-06-22) | Have (budget-capped) |
| **Alpaca** (official MCP v2, hosted OAuth plugin for Claude Code) | US stocks / ETFs bars, quotes, trades, options, news | Free paper account; full real-time data needs Algo Trader Plus | New |
| Massive (Polygon) / Alpha Vantage | Equities / aggregates (plan-limited) | Have | Have (limited) |

### Execution (paper first)

| Connector | Venues | Notes |
|---|---|---|
| **cTrader Open API** | Pepperstone CFDs (FX, XAU, **indices**) | Custom Nautilus adapter. Platform-neutral successor to the MT5 bridge |
| **Interactive Brokers** (official Nautilus adapter, IB Gateway in Docker) | **NQ / ES futures**, US equities, FX, CFDs | Where Fabio-style and index edges live. Free paper account; CME data fees apply |
| **Alpaca** (MCP + API) | US equities / options paper and live | For an equities ORB ("stocks in play", Zarattini et al. 2024) |
| MT5 bridge (existing `meta-trader-mcp` / EA) | Pepperstone MT5 | **Keep only for S14** until it ends |

### Ops / agent

| Connector | Use |
|---|---|
| **GitHub** (connected) | **Private repo for NEXA code** (no data, no secrets) → backup, history, CI tests |
| **Google Cloud** (connected, view-only connector + owner gcloud) | Always-on Linux node for data jobs, Nautilus nodes, IB Gateway; Cloud Scheduler; logging and alerts |
| Claude scheduled tasks / routines | Orchestrate the research queue (approvals stay human) |
| QuantConnect MCP (optional, paid) | Independent cross-check of promising strategies |

## 5. Target architecture (layers and interfaces)

```
            ┌────────────── Research engine (hypothesis registry · pre-reg templates · stage runner · gate report) ──────────────┐
Data layer ─┤  Market-data adapters → unified Parquet catalog (instrument master, sessions, calendars, costs per venue)           ├─ Monitoring
(automated) └────────────── Strategy engine (signals as plug-ins; same code for backtest / paper / live) ─────────────────────────┘   (heartbeats,
                                         │                                                                                            alerts,
                              Portfolio / allocation  →  RISK ENGINE (frozen NEXA_Risk spec, venue-neutral)  →  Execution adapters   retirement)
                                                                                                    (cTrader · IBKR · Alpaca · MT5 bridge)
```

**Key contracts:**
1. **Instrument master + cost model per venue:** spread / commission / swap / tick / contract / session, from spec probes or APIs. Every backtest uses the venue's real cost.
2. **Risk engine as a venue-neutral specification:**
   - The **frozen MQL5 `NEXA_Risk` is the reference**.
   - A Python implementation must pass parity tests against it (the same pattern as the window-B feature parity).
   - No change to the frozen limits (1 % per trade, 2 % daily budget, 10 % DD, caps, fail-closed rules).
3. **Research gate unchanged:** pre-registration hash, stages opened once, DSR / PBO, costs S0 / S1 / S2, human approval before any deployment.
4. **Backtest / live parity:** one strategy code path; a reconciliation report compares paper fills with simulated fills.

## 6. Phased roadmap (realistic)

| Phase | Duration | Deliverables | Approval gates |
|---|---|---|---|
| **0: Decisions & foundations** | **This week** | (a) Choose the core (A recommended). (b) Private GitHub repo + backup (fixes the no-backup risk). (c) Open free accounts: cTrader demo + Open API app, IBKR paper, Alpaca paper. (d) Write the risk-engine spec from the frozen MQL5 (document only). (e) Instrument / cost master for Pepperstone (from spec probes) + IBKR / Alpaca fee schedules | Core choice; accounts (user creates them; keys never pasted in chat) |
| **1: Automated data layer** | 1–2 weeks | Ingest jobs (Dukascopy, cTrader Pepperstone, Databento metered, Alpaca) → Parquet catalog with QA (gaps, spreads, DST), scheduled on GCP Linux | Each new paid source |
| **2: Research engine v2 ("one command per hypothesis")** | 2–3 weeks | Generic pre-reg template → stage runner → gate report. **Validation: reproduce known NEXA results (IM1, FX1, C2) in the new engine** before trusting it. Then queue: H-ORB-1 (NAS100), index anomalies, equities ORB | Each pre-registration; each run |
| **3: Strategy + risk engine on the core** | 2–3 weeks | Signals as plug-ins; Python risk engine with **parity tests vs frozen NEXA_Risk**; paper adapters (cTrader demo, IBKR paper, Alpaca paper); fill-reconciliation reports | Parity sign-off |
| **4: Multi-venue paper forward tests** | ≥ 4–8 weeks per strategy | Only for strategies that passed the gate; the S14 lessons (real costs) feed the cost models | Per strategy |
| **5: Live (small)** | After evidence | Shadow → small live → scaling rules; monitoring and retirement rules (backlog B11) | Explicit human approval per venue / strategy |

**Unchanged throughout:**
- S14 runs on MT5 to its end date.
- V2 is scored after 2028-01-03.
- NEXA_Risk is frozen.
- No strategy is assumed profitable.

## 7. What the user should decide now

1. **Core engine:** NautilusTrader (recommended), or QuantConnect (faster but paid / cloud), or both (QC as a cross-check).
2. **First venues** (paper): cTrader / Pepperstone (indices + FX), IBKR paper (NQ / ES futures), Alpaca paper (US equities).
3. **Data budget:** start free (Dukascopy, cTrader, Alpaca paper, IBKR paper). Databento Standard ($199/mo) only if CME live / order-flow research is reopened (LC-1 is closed by the user).
4. **GitHub private repo** for code + backup: yes / no.

## Addendum 2026-10-12: NautilusTrader source cloned and inspected

- **Clone:** `vendor/nautilus_trader`, shallow clone of `develop` at `5edd36e1` (2026-10-12), 167 MB, LGPL-3.0. Not installed, not built.
- **Version state:**
  - `develop` is **v2**: Rust core plus a PyO3 Python package, version **2.0.0rc7 (release candidate)**, Python **3.13 / 3.14 only**.
  - Legacy v1 (Cython) is on `develop_v1` and gets critical security fixes only for ≈ 3 months after cutover.
  - **So NEXA would adopt v2 in a fresh Python 3.13+ environment, separate from the research venv (3.12).** Release-candidate maturity is a known risk.
- **Official adapters (Python + Rust):**
  - **Databento** and **Interactive Brokers**;
  - crypto venues: Binance, Bybit, OKX, Coinbase, Kraken, Deribit, dYdX, Hyperliquid, Lighter, Derive, Architect AX;
  - Betfair, Polymarket, Tardis, Blockchain;
  - `sandbox` (simulated execution).
- **Community adapters (unsupported; must be audited before any use):**
  - **mt5-connector** (MetaTrader 5 adapter) and tickerall (MT5 market data). These are a possible bridge to the existing Pepperstone MT5 path.
  - sinopac (Taiwan).
- **No adapter (custom work needed):** cTrader / Pepperstone, Dukascopy, Alpaca, OANDA. The documented custom-adapter path is a separate Python package.
- **Note:** the repo's `CLAUDE.md` / `AGENTS.md` are the project's own contributor guidance, not NEXA instructions.
