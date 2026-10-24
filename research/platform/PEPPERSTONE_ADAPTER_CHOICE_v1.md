# Pepperstone adapter choice v1 (Phase 0, document only)

**Status:** RECOMMENDATION, 2026-10-12. Nothing is built, installed or connected.

**Inputs:**
- the user decision "Nautilus v2, Pepperstone + Dukascopy, free data";
- `RISK_ENGINE_SPEC_v1.md`;
- `NAUTILUS_ENV_PLAN_v1.md` (rc6 installed and accepted).

## 1. What the adapter is for (and what it is not)

| Need | Phase | Needs a Pepperstone adapter? |
|---|---|---|
| Backtests and research | 1–2 | **No.** Dukascopy free history is primary; the existing Pepperstone MT5 M1 exports (canonical pipeline) serve cost and parity checks. |
| Measuring real Pepperstone spreads / costs on new instruments (e.g. NAS100) | 2 | Read-only market data (an adapter, or the MT5 export path) |
| Paper trading via Nautilus | 3 | **Yes:** data + execution + reconciliation, on a **demo** account |
| Live trading | 5 | Yes, after every gate in the roadmap |

**Rule carried from the risk spec (§8):** a Nautilus node **never shares an account with S14** (MT5 demo <demo-account> on the GCP VM). The S14 forward check is untouched by everything here.

## 2. Verified facts (checked 2026-10-12)

**Nautilus v2 custom adapters:**
- `docs/developer_guide/python_adapters.md` (rc6): custom clients subclass `nautilus_trader.live.clients` and run on the node's asyncio loop.
- **Pure-Python adapters are officially supported in v2.**
- Limitation: Redis / PostgreSQL cache backing is unsupported with custom Python clients. That is fine for NEXA.

**`mt5-connector` (aulekator), the community listing:**
- MIT licence; v0.7.x; last push 2026-09-13; 23 stars; single maintainer; 2 open issues.
- **Requires `nautilus_trader>=1.190.0` and Python 3.10–3.12**, and uses v1 import paths (`nautilus_trader.model.data`, `.enums`, `.objects`). **Not compatible with the installed v2 rc6 (Python 3.13) without a port.**
- **Netting accounts only** ("Hedging accounts are not currently supported").
- Local mode needs Windows plus the `MetaTrader5` package (Windows-only).
- Linux mode = Docker + Wine + MT5 + a Flask API whose own README says it **"has no authentication"**.
- It polls ticks every 100 ms on Windows.

**cTrader Open API (Spotware), from help.ctrader.com:**
- Free and public; protobuf over SSL; works with any account linked to a cTrader ID.
- Pepperstone offers cTrader ("all your Pepperstone trading accounts linked to your cTrader ID will be available").
- **Rate limits:** 50 req/s per connection for non-historical requests; **5 req/s for historical** requests.
- **Ticks:** at most **one week per request** (`to − from ≤ 604,800,000 ms`), with paging via `hasMore`. The per-message tick cap depends on the backend.
- **Trend bars:** the range limit per request depends on the period (not listed on the page; must be probed).
- **Auth:** OAuth2 `authorization_code` + `refresh_token`.
  - The access token lasts **2,628,000 s (≈ 30 days)**.
  - The refresh token **does not expire**; using a new refresh token invalidates the old tokens.
  - Then `ApplicationAuth` → `GetAccountListByAccessToken` → `AccountAuth` per account.
- **The official Python SDK `spotware/OpenApiPy`** (MIT, Twisted-based) was **last pushed 2024-08-07**, with 14 open issues. It is stale, so NEXA would use only the official `.proto` message definitions with its own small asyncio client.

## 3. Options compared

| Criterion | **A. cTrader Open API, custom NEXA adapter** | B. `mt5-connector` (ported to v2) | C. Own MT5 bridge (EA + socket) |
|---|---|---|---|
| Runs natively on Mac / Linux | **Yes** (TCP + SSL) | No (Windows, or Wine-in-Docker) | No (MT5 needs Windows / Wine) |
| Works with Nautilus v2 now | Needs to be written | **Needs a port** (v1 → v2, Python 3.13) | Needs to be written |
| Official, documented protocol | **Yes** (Spotware) | Unofficial wrapper of the MT5 Python API | MQL5 sockets (official, low-level) |
| Hedging accounts | Yes (account type chosen at opening) | **No** | Yes |
| Security posture | OAuth tokens; no open ports | Unauthenticated Flask in remote mode | Own socket: must be built secure |
| Push vs poll | **Push** (spot / execution events) | Poll (100 ms / 250 ms) | Push |
| Historical data | Bars + ticks (≤ 1 week per request, 5 req/s) | MT5 history via the terminal | MT5 history via the terminal |
| Same price feed as NEXA's research data (Pepperstone MT5) | **No:** cTrader feed, to be measured | Yes | Yes |
| Interference risk with S14 | **None** (different platform and account) | Needs a 2nd MT5 terminal, never on the S14 VM | Same as B |
| Maintenance owner | NEXA (protocol is stable and versioned) | One external maintainer | NEXA |
| Build effort (estimate) | Medium: protobuf client, instrument provider, data client, exec client, reconciliation | Medium: port + audit + Wine ops | High: EA + bridge + adapter |

## 4. Recommendation

**Choose A: a custom cTrader Open API adapter for Pepperstone, built in-house on the official protobuf definitions, with an asyncio client.**

**Why:**
1. It is the only option that runs natively where Nautilus runs (Mac now, a Linux VM later) with **no Windows or Wine layer**. NEXA's worst operational failures came from exactly that layer (the MT5/Wine traps in the tooling memo, and S14's stop on 10-04 and 10-05).
2. It is an official, versioned protocol with push events, non-expiring refresh tokens and published rate limits.
3. It gives complete separation from S14 by construction.
4. B is v1-only and netting-only, and its Linux mode is unauthenticated. Porting and hardening it costs about as much as A and still leaves Wine in the loop.

**B is not used**, but its MIT-licensed `parsing.py` and `execution.py` may be read as a reference for MT5-specific edge cases. Nothing is installed.

**Main risk of A, and how it is handled:** the cTrader price feed and costs are **not** the MT5 feed that NEXA's history came from. Before any strategy result is trusted on cTrader, a **feed-parity study** runs on the same instruments and windows. It compares cTrader demo spot and bars with Pepperstone MT5 M1 exports and Dukascopy, covering spread distribution, bar OHLC differences, commission per lot, and swap. Divergence beyond tolerance means costs are re-estimated, never assumed.

## 5. Build plan (each step needs its own approval; demo only)

| Step | Content | Gate |
|---|---|---|
| P-1 | The user opens a **Pepperstone cTrader demo** account (same cTID) and registers an Open API application at openapi.ctrader.com. **Credentials stay with the user**, stored in a gitignored `.env`, never in chat. | The user does this |
| P-2 | Protocol client: asyncio + SSL + protobuf framing, heartbeat, auth, refresh-token rotation, rate limiter (≤ 45 / 4 req/s), reconnect. Unit tests against recorded message fixtures. | Tests pass offline |
| P-3 | **Read-only** instrument provider + market-data client (spots, trend bars, ticks with `hasMore` paging), writing to the Parquet catalog. | Symbol specs match the cTrader UI; no trading permission used |
| P-4 | Feed-parity study vs MT5 exports and Dukascopy (pre-registered tolerances) | Report reviewed |
| P-5 | Execution client on **demo**: market / limit / stop orders with SL/TP, amend, cancel, execution events, **startup and continuous reconciliation**. Every order passes `nexa_risk` (risk spec) first; Nautilus `RiskEngine` stays enabled. | Spec / exec conformance tests (`docs/developer_guide/spec_exec_testing.md`), kill-switch test |
| P-6 | Paper run on demo, a minimum of 4 weeks, with a journal in the schema-v1-compatible format | Roadmap Phase 3 gate |

**Dependencies to add when P-2 is approved** (hash-locked into `requirements-nautilus.txt`):
- `protobuf`;
- the official Spotware `.proto` files, vendored at a pinned commit.

Nothing else; no Twisted.

## 6. Open items for the user (not needed until P-1)

- **Account type for the cTrader demo:** hedging (matches how NEXA thinks about positions per strategy) or netting (matches Nautilus `OmsType.NETTING` defaults). **Recommended: hedging**, with Nautilus `OmsType.HEDGING`.
- **Base currency USD** (matches S14's preset assumptions).
- **Confirm Pepperstone offers the instruments you want on cTrader** (NAS100 / US Tech 100 naming differs by platform). P-3 records the exact cTrader symbol names and specs.
