# TOOLING EVALUATIONS (MCP servers, bots, data vendors)

**Purpose:** record what each external tool or integration does, its safety surface, and whether NEXA should use it. **Nothing here is installed, configured or run.** Any adoption needs the user's explicit approval. NEXA's standing rules apply:
- no trading or execution enablement;
- no secrets in arguments or config pasted to chat;
- the Risk Engine is final;
- no new data acquisition without approval.

## Verdict table (2026-10-11)

| Tool | What it is | Safety / quality findings | Verdict for NEXA |
|---|---|---|---|
| `ariadng/metatrader-mcp-server` (SRC-CODE-005) | MCP/HTTP/SSE bridge letting an LLM trade MT5 | Skill says execute "immediately — no additional confirmation". Password as a CLI argument. SSE binds 0.0.0.0 with no auth. Market orders without SL/TP (CL-080) | **REJECT.** Keep the existing `meta-trader-mcp` (trading/exec disabled; risk interceptor) |
| `fintools-ai/mcp-options-order-flow-server` (SRC-CODE-004) | MCP front-end to an external Go options-flow broker | Unnamed data provider; unverifiable "institutional-grade" claims; US equity options only (CL-081) | **Not relevant** (no XAU/FX); do not install |
| `twolven/mcp-optionsflow` (SRC-CODE-003) | Yahoo-based option-strategy analyser | Well engineered (locked deps, Host/Origin validation, localhost binding), but Yahoo data is unofficial (CL-082) | **Not relevant** (not order flow; no XAU/FX options) |
| `modelcontextprotocol/servers` (SRC-CODE-006) | Official reference servers | "Not production-ready" by design (CL-083) | Reference only. NEXA's file-based KB already serves the "memory" role |
| `aakash-code/GammaGEX` (SRC-CODE-001) | GEX/greeks momentum toolkit (Indian options via OpenAlgo) | Unit and sign errors, silent defaults, no licence, no tests (CL-077) | **Do not reuse.** If NEXA ever computes GEX, implement CL-072 from scratch with unit tests |
| `Scorsone GEX-DEX script` (SRC-CODE-002) | DataBento CME options flow-GEX backtest | Black–Scholes on futures options, 3-week sample, no costs, no OOS (CL-078) | Data-access template only |
| DataBento `GLBX.MDP3` (CL-079) | CME tick data vendor (trades with aggressor side, book, definitions) | Coverage of OI and GC/6E options unverified; usage-priced; $125 free credits | **Candidate data source** for GAP-D01/D02/D08. Needs verification plus user approval; no credits used |
| Mnemox finance-MCP list (SRC-DOC-007) | Discovery list (11 servers; 4 trade) | Vendor self-promotion; no security guidance (CL-084) | Discovery only |
| Bot-building videos (YT-024/025/028) | Lumibot/Alpaca, Claude Code + TradingView, HMM bot | Profit claims unsupported; heavy optimisation (CL-085) | No adoption. NEXA's validation stack is stricter |

## Checklist for any future MCP / bot integration
1. **Execution surface:** can it place, modify or close orders? If yes, it must be disabled by default, and every action must require explicit user confirmation plus the Risk Engine.
2. **Secrets:** credentials come only from env or a keychain, never CLI args. Nothing is printed or logged.
3. **Network:** stdio or loopback only. Any HTTP needs auth plus Host/Origin validation (DNS-rebinding defence).
4. **Data provenance:** a named upstream with a licence, history depth and an entitlement check.
5. **Code quality:** a licence, tests, maintained (recent push), units/signs checked against a reference.
6. **Fit:** does it cover XAUUSD / EURUSD / GBPUSD / USDJPY or their CME futures? If not, it is irrelevant to NEXA.
