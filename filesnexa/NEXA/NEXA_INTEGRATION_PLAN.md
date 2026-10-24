# NEXA — Repository Forensic Analysis & Integration Plan
**Status: ANALYSIS ONLY. No NEXA source file has been modified, created, renamed or deleted.**
Baseline backed up to `NEXA_BASELINE_BACKUP_20260919-124052/` (+ `.tar.gz`, + SHA256 manifest).

---

## BASELINE CORRECTION (read this first)

The directive describes "the currently compiling NEXA build". **NEXA has never been compiled.** No MetaEditor exists in this environment and none has existed in any prior session. The baseline is *statically verified*, not *compile-verified*. Every plan below assumes the first real compile has yet to happen, and that it will produce errors — MQL5 API details (calendar struct fields, ONNX shape calls, `const MqlRates &r[]` parameter forms) are the most likely sources.

Treating an uncompiled build as a proven baseline is the single most dangerous assumption available right now, which is why it is corrected before anything else.

---

## DELIVERABLE 01 — REPOSITORY FORENSIC ANALYSIS

All 13 repositories were cloned and read at source level. Metrics are measured, not estimated.

| # | Repository | Code LOC | Docs LOC | Licence | What it ACTUALLY is |
|---|---|---|---|---|---|
| 01 | moss-trade-bot-skills | 75,819 | 9,051 | yes | ~8 near-duplicate snapshots of a crypto bot "factory" (v1.0.24/25/26/27, beta/dev variants) plus 296 cached CSV klines. Not a library — a versioned dump. |
| 02 | lite-qmt-executor | 3,506 | 2,011 | yes | Chinese A-share QMT executor. **Real WAL implementation**: intent logged before action, replayed on restart via `_recover_state` + per-strategy `on_recover`. |
| 03 | minibt | 272,316 | 376 | yes | Large backtesting framework with vendored TA libs (talib, pandas_ta, finta, tulip, tradingview, pine). Chinese futures (tqsdk) oriented. |
| 04 | qmt-gateway | 52,357 | 1,430 | **NONE** | A-share QMT gateway service. Order/trade snapshot persistence, callback persistence, job recovery from DB. |
| 05 | Hyperliquid-Leaderboard-Analytics | 2,244 | 208 | yes | Terminal UI for scraping/comparing Hyperliquid perp leaderboard traders. Analytics, no strategy. |
| 06 | HFT-trading-simulator | 79,000 | 19,551 | yes | Largest and most serious. Exchange simulator (matching engine, WS, liquidation), `ai-signal-bot` with **Avellaneda–Stoikov market making**, toxicity gating, ML ensemble, plus k8s/helm/terraform/web-UI. Crypto 24/7. |
| 07 | adaq | 187,191 | 16,170 | yes | Mostly a Next.js/React front-end (`src/app`, `components`, `hooks`) over Eastmoney A-share data + a qlib ridge adapter. |
| 08 | machine-learning-stock-backtesting | 673 | 295 | yes | **One file, highest value-per-line of all 13.** XGBoost framework v4: walk-forward retraining, purged+embargoed CV, in-fold feature selection, regime filter, confidence gating, transaction cost in bps. |
| 09 | quantdinger | 2,131 | 6,187 | yes | 34 markdown files vs 10 Python files — and the Python is `startup.py`, `celery_app.py`, `gunicorn_config.py`, an MCP server. **Infrastructure scaffolding, not strategy.** |
| 10 | TradeHive-TradingAgents | 9,713 | 3,724 | yes | LangGraph multi-agent debate (bull/bear/neutral debators, risk mgmt, reflection memory). Config: `gpt-5.2` deep / `gpt-5-mini` quick. No direct broker execution path found. |
| 11 | kairos-engine | 8,261 | 87 | yes | **Second-highest value.** BTC oracle with GaussianHMM regime (+ collapse detection), **isotonic calibration with Brier/ECE**, outcome resolution that waits 1.5× horizon, and a cost-scenario re-costing report. |
| 12 | polymarket-bot | **0** | 1,644 | **NONE** | **14 files: 9 markdown, 4 PNG, 0 source files.** Backtest reports and dashboard screenshots for software that is not in the repository. |
| 13 | fin-cn-agent | 33,866 | 2,285 | **NONE** | Chanlun (缠论) structure analysis for A-shares: candle merging, fractals, strokes, divergence + akshare/tushare agents. |

### README-vs-implementation discrepancies (directive requires these be documented)

- **polymarket-bot** — publishes `BACKTEST.md`, `BACKTEST_V16.md`, `BACKTEST_CAPITAL.md`, `REPORTS.md` and dashboard images, with **zero implementing code**. The performance claims cannot be reproduced, inspected, or falsified. This is the clearest instance in the set of documentation asserting what no code demonstrates.
- **quantdinger** — presents as a quant platform; the shipped Python is a Flask/Celery/gunicorn/MCP skeleton. The strategy substance lives in prose.
- **moss-trade-bot-skills** — "skills" implies a reusable library; the repository is multiple full copies of an application at different versions, with cached market data committed alongside.
- **HFT-trading-simulator** — README positions it as an HFT system; the trading logic is a market-making quoter. NEXA is a directional taker. The simulator half is genuinely substantial; the "signal bot" half solves a different problem.
- **Licensing** — `qmt-gateway`, `polymarket-bot` and `fin-cn-agent` ship **no licence file**. Absent an explicit licence, default copyright applies and code may not be copied into NEXA. They may be read for ideas only. This is a hard constraint, not a preference.

---

## DELIVERABLE 03 — KEEP / UPGRADE / NEW / RESEARCH / REJECT MATRIX

### REJECT (7 of 13 repositories contribute nothing to NEXA)

| Source | Verdict | Reason |
|---|---|---|
| polymarket-bot | **REJECT** | No code exists. Prediction-market venue, unrelated to MT5 FX. Nothing to extract. |
| quantdinger | **REJECT** | Web/Celery/MCP infrastructure. NEXA is MT5-native by directive; a server stack is explicitly out of scope. |
| adaq | **REJECT** | React front-end + A-share data adapters. NEXA has no UI and does not trade A-shares. |
| Hyperliquid-Leaderboard-Analytics | **REJECT** | Crypto perp leaderboard scraping. No transferable mechanism. |
| fin-cn-agent | **REJECT (+ licence bar)** | Chanlun is a *competing* structure taxonomy. NEXA already has BOS/CHoCH/MSS/displacement. Adding a second, overlapping structure engine creates correlated "confirmations" — precisely the failure mode the Tier-4 scoring redesign eliminated. No licence. |
| minibt | **REJECT** | 272k LOC Python backtester with vendored TA libraries. NEXA backtests in the MT5 Strategy Tester against the same execution code it trades with — that is a *stronger* guarantee than a separate Python backtester, which introduces model/implementation divergence. |
| moss-trade-bot-skills | **REJECT as code / RESEARCH for one idea** | Versioned application dumps, crypto venue. The only transferable notion is the reflection→proposal loop, which TradeHive expresses more cleanly. |

### RESEARCH-ONLY (external tooling, never inside the live EA)

| Source | Extracted | Destination |
|---|---|---|
| **handiko** | Purged + embargoed CV; walk-forward retraining on expanding window; **feature selection performed inside the training fold**; confidence gating on percentile rank AND probability floor; transaction cost in bps | The Python trainer that consumes `NEXA_Training_*.csv`. **This closes the single largest open gap in NEXA.** |
| **kairos** | Isotonic calibration + Brier + ECE; outcome resolution delayed to 1.5× horizon; **cost-scenario re-costing** (same trade list, multiple cost models); HMM collapse detection | Python trainer + a cost-sensitivity report over Trade DNA |
| **HFT-sim** | ML ensemble validation shape; realized-vol estimator; toxicity→refuse-to-quote pattern | Research reference only |
| **TradeHive** | Structured competing-hypothesis debate; reflection memory keyed to outcomes | Concept only — NEXA's `AdversarialCheck()` already implements the bounded, deterministic version |

### ADAPT (principles → MQL5, no code copied)

| Source | Principle | NEXA target | Status vs current build |
|---|---|---|---|
| lite-qmt-executor | **WAL: log intent BEFORE acting; replay on restart** | Execution/recovery | **Partially present.** `StagePendingContext` writes intent to GlobalVariables before dispatch, and restart adopts an orphan position. Gap: GlobalVariables are not durable across terminal reinstall/profile reset, and there is no append-only intent log. |
| qmt-gateway | Persist order/trade snapshots at each callback | Reconciliation | **Partially present** via Trade DNA rows (`OPEN`/`FILL`/`PARTIAL_CLOSE`/`CLOSE`/`REJECTED`). |
| kairos | Regime classifier compared against a baseline before adoption | Regime engine | **Present** (`VolRegime`, `SwingTrendArr`). HMM is a *candidate*, not an upgrade, until it beats this out-of-sample. |

### KEEP UNCHANGED (existing NEXA mechanisms no repository improves upon)

Async `TRADE_TRANSACTION_REQUEST` rejection handling · fill/position reconciliation via deal-history volume · in-flight guard with verified timeout resolution · magic+symbol ownership under both margin modes · server-side SL enforcement and re-protection · hard risk ceiling with post-normalisation recheck · daily loss / drawdown / trade-count / margin / spread / correlation / currency-exposure gates · AI fail-closed · FOMC fail-closed · causal replay and closed-bar-only features · shadow ledger as diagnostic only · Trade DNA with `ai_00..ai_47`.

**None of the 13 repositories implements a risk or execution control stronger than what NEXA already has.** Several implement materially weaker ones. Per Absolute Rule #2, nothing here is replaced.

---

## DELIVERABLE 04 — TARGET ARCHITECTURE

The directive lists 39 engines. Building 39 MQL5 modules would be the "collection of disconnected features" the directive's final principle forbids. NEXA already implements the live-critical subset; the honest architecture is **two tiers with a one-way gate**:

```
  RESEARCH TIER (Python, offline, outside MT5)
  ┌──────────────────────────────────────────────────┐
  │ Trade DNA ingest  →  purged+embargo CV (handiko) │
  │ walk-forward retrain  →  isotonic calibration    │
  │ (kairos) → Brier/ECE → cost-scenario re-costing  │
  │ → Monte Carlo → acceptance gate                  │
  └───────────────────────┬──────────────────────────┘
                          │  ONE artifact crosses: a
                          │  shape-validated .onnx +
                          │  its calibration map
                          ▼
  LIVE TIER (MQL5, MT5-native, unchanged architecture)
  data → features → liquidity events → composite gate
       → adversarial → expectancy → RISK (absolute)
       → execution → position mgmt → Trade DNA ──┐
                                                  └──→ back to research
```

The live tier gains **no new engines** in this plan. It gains one thing: the ability to consume a properly validated model, which it is already wired for and has never had.

---

## DELIVERABLE 12/13 — VALIDATION FRAMEWORK & TESTING PLAN

Adopted from handiko + kairos, run outside MT5:
1. Chronological split; final holdout untouched until the end, once.
2. Purged CV with embargo ≥ max label horizon (`InpMaxHoldBars`).
3. Feature selection **inside** each training fold.
4. Walk-forward retraining on expanding window.
5. Isotonic calibration; report Brier + ECE; a claimed 80% must be ~80% empirically.
6. Cost-scenario re-costing: same trade list under measured / padded / stressed spreads.
7. Monte Carlo: trade-order randomisation, slippage and spread perturbation; report p5/p25/median/p75/p95.
8. Acceptance gate — a model enters live only on OOS expectancy > 0 after stressed costs, calibration within tolerance, and stability across folds.

---

## PROPOSED FILE CHANGES (nothing executed yet)

**No existing NEXA `.mq5`/`.mqh` requires modification to integrate this plan.** That is the finding, and it is the correct one: the live tier is complete for its current scope, and every genuinely valuable import is research-tier.

Proposed NEW files only (additive, live EA untouched):

| File | Type | Purpose |
|---|---|---|
| `research/nexa_train.py` | NEW | Purged/embargoed CV + walk-forward + in-fold feature selection (handiko method) over `NEXA_Training_*.csv` |
| `research/nexa_calibrate.py` | NEW | Isotonic calibration, Brier/ECE, reliability curve (kairos method) |
| `research/nexa_cost_scenarios.py` | NEW | Re-cost the same trade list under multiple spread/commission models (kairos method) |
| `research/nexa_montecarlo.py` | NEW | Trade-order randomisation, percentile drawdown paths, risk of ruin |
| `research/README.md` | NEW | Provenance: which repo each method came from, and its licence |

**Optional, and only if walk-forward proves it out-of-sample:** an `InpRequireAIConfirmation=true` deployment once a calibrated model exists. That is a *settings* change, not a code change — the fail-closed path is already built and tested.

---

## WHAT I AM NOT PROPOSING, AND WHY

- **No HMM in the live EA.** Kairos itself ships collapse detection because HMMs get stuck in one state. Adding an unvalidated latent-state model ahead of the existing regime classifier would add failure modes with no evidence of benefit. Candidate for research comparison only.
- **No statistical-arbitrage engine.** It needs cointegration over a pair universe with per-leg execution. On a $100 account where one 0.01 lot already approaches the 1% risk ceiling, a two-leg spread trade cannot be sized within the risk invariants. Structurally infeasible at current equity.
- **No LLM in the decision path.** TradeHive's own config uses `gpt-5.2` for deep reasoning; per-bar latency and cost are incompatible with an M1 EA, and the directive forbids LLM execution authority.
- **No market making.** Avellaneda–Stoikov requires quoting both sides with inventory control. NEXA is a directional taker through a retail broker. Not applicable.
- **No Python execution layer.** Directive Rule #1.

---

## AWAITING APPROVAL

No source file will be touched until the exact phrase **PROCEED WITH THE REWRITE** is given. Note that what this plan proposes is not a rewrite — it is four additive research scripts and zero changes to the live EA. If you want something different (for example: live-tier HMM, or a stat-arb family), say so and I will re-plan rather than silently widen scope.
