# Review of 12 GitHub repositories shared by the user (2026-10-20)

- **Method:** GitHub metadata (stars, licence, activity) plus each README, read via GitHub MCP / Firecrawl. For the options dashboard, also its stored output files.
- **Claim checked:** "all 100% can make profit". **None of the 12 is a proven profitable strategy.**
  - 9 are agent/coding tools;
  - 2 are trading engines NEXA already uses;
  - 1 is a reading list;
  - the two trading-specific apps carry no evidence (see below).

| # | Repo | What it is | Verdict for NEXA |
|---|---|---|---|
| 1 | Panniantong/Agent-Reach (MIT, ~100k★) | CLI giving agents access to X/Twitter, Reddit, Facebook, Instagram, LinkedIn, XiaoHongShu, YouTube… X, Reddit, XiaoHongShu and Xueqiu need **logged-in browser sessions / exported cookies** (Cookie-Editor) | ❌ Conflicts with the standing rule "do not export browser cookies"; platform ToS risk. Already covered legitimately: YouTube MCP, Exa, Tavily, Firecrawl, GitHub MCP |
| 2 | thedotmack/claude-mem (Apache-2.0, ~102k★) | Hooks record every session; AI-compressed memories in local SQLite + Chroma; optional cloud sync (cmem.ai); extra model calls (hosted observer trial, then your plan or your own key) | ⚠️ Duplicates NEXA's file memory + MEMORY.md and git ledger. Adds cost and a privacy surface (trading/account details could reach a cloud). Not recommended |
| 3 | anthropics/claude-plugins-official → claude-code-setup (official) | Read-only skill that scans a codebase and recommends 1–2 hooks / skills / MCP / subagents per category | ✅ Harmless, official, free. Worth one run to find automations for NEXA's repeated tasks |
| 4 | rebelytics/one-skill-to-rule-them-all (CC BY 4.0, 3.5k★) | Meta-skill that watches sessions and proposes skill updates for review (does not auto-modify) | 🟡 Useful idea. NEXA's repeated workflows (pre-registration, QC runs, cloud-ATAS health check) could become skills. Writing 2–3 targeted skills directly is simpler |
| 5 | morluto/rea (MIT) | Agent-driven reverse engineering of binaries/apps (Ghidra, IDA, decompilers) | ❌ The ATAS licence §6 forbids reverse engineering/decompiling. No legitimate NEXA use |
| 6 | ruvnet/ruflo (MIT, ~78k★) | Multi-agent "swarm" harness: 100+ agents, background workers, hooks, rewrites CLAUDE.md/settings, unsandboxed mods | ❌ Heavy token cost, autonomous background actions, changes the harness. Swarms do not create an edge; they multiply trials (bad for pre-registration discipline) |
| 7 | Hewkaw02/Futures-Options-SD-Dashboard (MIT, 20★) | Hourly GEX / gamma-flip / SD-band / IV dashboard for GC, ES, NQ (yfinance free; tastytrade/IB/Databento optional); claims a walk-forward signal evaluator | ⚠️ The idea matches NEXA's data-blocked GEX hypotheses, but its own report of 2026-10-19 15:59 flags **"Only 0.0% of options have liquid spreads", "Zero Bid at 50 strikes", QualityScore 0.0** for all three assets. Free-data GEX is unreliable, so it is not a sound basis for a test. Published snapshots only since 2026-09-03 (~33 sessions) |
| 8 | autopilotaitech/BookDepthIQ-Vest (MIT, 1★, created 2026-10-08) | Chrome extension for **Vest Markets** perps: one-click DOM orders using the session token of your logged-in Vest tab; journal; "SuperTrend scalp read" | ❌ Wrong venue (not CME/ATAS/Topstep); reads a login token; one-person project. Its evidence is "72 hours of data, 63% win", which is statistically meaningless. NEXA Monitor already journals the same fields for ATAS |
| 9 | nautechsystems/nautilus_trader (LGPL-3.0, 30k★) | Production-grade Rust/Python event-driven engine (backtest + live) | ✅ Already NEXA Phase 0 (rc6 env installed). Useful only once a strategy passes; no ProjectX/Topstep adapter |
| 10 | DietrichGebert/ponytail (MIT) | Plugin making the agent write minimal code (ladder: does it need to exist → stdlib → one line …) | 🟡 Benign but marginal; it mirrors how NEXA code is already written. Optional |
| 11 | QuantConnect/Lean (Apache-2.0, 22k★) | The engine behind QuantConnect | ✅ Already used for every ES/NQ test (QC free node). A local Lean install would avoid QC limits, but needs our own historical data (not free), so stay on QC cloud |
| 12 | paperswithbacktest/awesome-systematic-trading (14.9k★) | Curated list: libraries, data sources, ~100 paper strategies with Sharpe | 🟡 Good reading list / hypothesis source. Its futures strategies are long-horizon commodity momentum/reversal (Sharpe 0.36–0.65), i.e. the H-SWING family, which needs large capital and is incompatible with Topstep intraday rules. Published anomalies typically shrink after publication, so any idea must be pre-registered and tested on out-of-sample data |

## What would actually help NEXA now
1. **Run the official claude-code-setup recommender once** (read-only).
2. **Write 2–3 NEXA skills** (a lighter version of #4's idea):
   - "check cloud ATAS": update the firewall IP, read recording_ok / recorder_age_min, ATAS memory, recorder file freshness;
   - "pre-register + hash a hypothesis";
   - "run a QC backtest with editor-hash check".
3. Use #12 only as a source of hypotheses for the research ledger, each pre-registered.
4. Nothing here replaces the current bottleneck: **H-DISC1 real-time trades and the recorder running reliably.**

## Addendum 2026-10-21: Jakeschincariol/trader-skill (user-shared)
- **What it is:** 11 Claude skills (MIT, one commit 2026-10-14, ~135 stars) for US **stock investing**: copy a fund's 13F, Congress trade disclosures (House PTRs), news/8-K watch, budget sizing, risk check, tax lots, rebalancing, price alerts. Standard-library Python, public data (SEC EDGAR, House Clerk, RSS, unofficial Yahoo chart endpoint). No hooks in plugin.json.
- **Fit with NEXA: none.** NEXA is intraday futures (MNQ/ES, ATAS, Topstep); this is long-term stock portfolios. No futures, no intraday, no order flow.
- **Edge claim:** none made (README: "copying an investor does not copy their results"). 13F is up to 45 days after quarter end; PTRs up to 45 days after the trade. No backtest included.
- **Conflict:** `trader-broker` routes orders through the Alpaca MCP server: breaks the "no orders by Claude" rule. Never install that part.
- **Verdict:** do not install for NEXA. Read README, plugin.json and the broker config only; the Python code was not reviewed.

## Re-check 2026-10-21: #12 awesome-systematic-trading (user asked again)
- Parsed the README strategy tables (local clone ddfee8b, 2026-09-28): **61 strategies**, sections Bonds / Commodities / Crypto / Currencies / Derivatives / Equities / Multi-asset.
- **0 intraday strategies.** Futures-relevant = 3 commodity papers (momentum with intra-market correlation, Sharpe 0.65; long-run reversal 0.63; mean-reversion windows 0.36), all multi-week/month holding: banned under Topstep (no overnight). Verdict unchanged: reading list only, nothing to install.

## Addendum 2026-10-21b: three user links
- **nautechsystems/nautilus_trader:** already installed (`.venv-nautilus`, 2.0.0rc6, hash-locked, acceptance PASS b39e3f5). rc7 is now on PyPI; no upgrade (pin is deliberate; nothing in the current ATAS/Topstep plan uses Nautilus). It was chosen for the Pepperstone/MT5-era platform roadmap; role now = optional research backtester only.
- **Hewkaw02/Futures-Options-SD-Dashboard:** already installed (`vendor/`, own venv, yfinance). Upstream commits daily auto-updated reports (latest 2026-10-20 22:52 UTC). Verdict unchanged: Yahoo has no futures options, so no free GEX.
- **autopilotaitech/BookDepthIQ-Vest (new):** Chrome-extension DOM/scalping panel for **Vest Markets perps** (NQ perps, Vest prop accounts). TypeScript, MIT, created 2026-10-08, 1 star, Stripe tip jar. Places LIVE orders through the user's Vest web session (no official API: its own README warns this may breach Vest's prop terms). **Not usable for NEXA:** different venue (not CME/Topstep), sends orders (conflicts with no-orders-by-Claude), unofficial API. Its DOM/footprint/profile features already exist natively in ATAS.
