# NEXA: commercial EA and MQL5 prior-art audit (2026-09-29)

**Scope and status.** This is technical prior art only. Nothing here changes PHASE3_SIX_FAMILIES_V2: its protocols, universe and dates are frozen under anchor `6090be68…9324c`.
- No EA is ranked, scored or recommended for purchase.
- No proprietary logic was copied.
- No strategy was run.

**Evidence types used below**
- **SC** (source claim): a statement by a vendor or reviewer.
- **VF** (verified fact): checked by me against a primary artifact.
- **TO** (technical observation): what the source *describes* as the mechanism.
- **INF** (inference): my reasoning.
- **UMC** (unverified marketing claim): performance numbers, ratings, "Myfxbook-verified" labels.

**No performance number in this report has been independently verified.** A reviewer writing "Myfxbook verified" does not verify the account's risk, history or survivorship. I did not inspect any Myfxbook account.

## 1. Sources and access
| # | Source | Access | Type |
|---|---|---|---|
| 1 | [MQL5 AlgoBook: Big EA example](https://www.mql5.com/en/book/automation/tester/tester_example_ea) | read | primary technical documentation |
| 2 | [NYC Servers: Quantum Queen](https://newyorkcityservers.com/blog/quantum-queen-ea-review) | read | secondary review (VPS vendor) |
| 3 | [NYC Servers: Mad Turtle](https://newyorkcityservers.com/blog/mad-turtle-ea-review) | read | secondary review |
| 4 | [NYC Servers: Night Hunter Pro](https://newyorkcityservers.com/blog/night-hunter-pro-review) | read | secondary review |
| 5 | [NYC Servers: Waka Waka](https://newyorkcityservers.com/blog/waka-waka-ea-review) | read | secondary review |
| 6 | [NYC Servers: Perceptrader AI](https://newyorkcityservers.com/blog/perceptrader-ai-ea-review) | read | secondary review |
| 7 | [NYC Servers: AI Forex Robot](https://newyorkcityservers.com/blog/ai-forex-robot-mql5-ea-review-2026) | read | secondary review |
| 8 | [NYC Servers: EA Gold Stuff](https://newyorkcityservers.com/blog/ea-gold-stuff-review) | read | secondary review |
| 9 | [NYC Servers: Evening Scalper Pro](https://newyorkcityservers.com/blog/evening-scalper-pro-review) | read | secondary review |
| 10 | [RoboForex: first MQL5 EA](https://roboforex.com/blog/education/first-mql5-expert-advisor/) | read | educational |
| 11 | [BM Trading EAs](https://bmtrading.de/en/expert-advisors/) | read | vendor catalogue |
| 12 | [Scribd "Manual"](https://www.scribd.com/document/849557005/Manual) | **preview only; body behind login** | a "London Session" range-breakout EA manual (title/summary only) |
| 13 | Apex Drawdown Zero: [MQL5 listing](https://www.mql5.com/en/market/product/163054) (primary); [vendor site](https://apexdrawdownzero.com/), [review](https://theforexgeek.com/apex-drawdown-zero-ea-mt5-review/), [NYC list](https://newyorkcityservers.com/blog/best-mt5-expert-advisors) (secondary) | read the primary listing; secondary sources via search snippets | **primary and secondary sources CONFLICT** (see below) |
| 14 | XenClarity: [MQL5 listing](https://www.mql5.com/en/market/product/162516) (did **not** render the product); [NYC list](https://newyorkcityservers.com/blog/best-mt5-expert-advisors) | secondary only | **not independently verified** |

**Source-quality notes**
- **Commercial interest.** Sources 2–9 come from a VPS vendor. Several of its reviews stress sub-10 ms VPS latency, which is that vendor's product.
- **Apex Drawdown Zero.** The primary MQL5 listing describes:
  - instruments XAUUSD, EURUSD and EURJPY on H1;
  - at most one qualified trade per day;
  - no grid or martingale;
  - volatility-aware stops.

  Secondary sources describe something different:
  - an M15 gold Asian-session (02:00–06:00 server) range breakout;
  - a "0.39 % max drawdown" figure.

  The conflict is unresolved. The specification is **not independently verified**.
- **XenClarity.** The only details come from one secondary list: "XAUUSD H1 level trading with dynamic buffers", with a defined SL/TP. **Not independently verified**; no primary source was accessible.

## 2. Prior-art matrix

Column key:
- **Impl?** = already implemented in NEXA: A (yes), B (partially), C (missing but relevant).
- **Compat?** = compatible with NEXA hard invariants. **D** marks an incompatible mechanism.
- **Future hyp.?** = whether it becomes a hypothesis in the future research backlog (**F**).

| Source | EA/System | Claimed mechanism (SC) | Observed/documented mechanism (TO) | Evidence type | Potential NEXA relevance | Impl? | Missing? | Compat? | Future hyp.? | Data required | Validation required | Risk conflict | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | AlgoBook Big EA | multi-symbol strategy pool | `MultiSymbolMonitor`/`UnityController`: process only when the last bars of **all** symbols share the same time; bar- or tick-mode | TO (primary doc) | multi-symbol bar synchronisation for NEXA's cross-symbol reads (USD composite, correlation cap) | B | time-aligned cross-symbol reads | yes | no (engineering) | none | tester replay across 4 symbols | none; `NEXA_Risk.mqh` is frozen, so any fix there needs a human decision | NEXA reads other symbols by **shift**, not time (see V2_FINAL_PRE_OPENING_AUDIT.md §12, M1) |
| 1 | AlgoBook Big EA | custom tester metric | `OnTester` returns a volume-normalised R²; `TradeReport` computes DD/Sharpe/PF/recovery from deals | TO | machine-readable tester result for NEXA (R-based expectancy, trade count) | B | `OnTester()` absent; Trade DNA exists | yes | no | none | tester run | none | Trade DNA already gives per-trade R |
| 1 | AlgoBook Big EA | optimisation frames | `FrameAdd`/`FrameNext` collect per-pass reports | TO | only if NEXA ever optimises in the tester (the research tier optimises offline) | C | — | yes | no | — | — | risk of in-tester overfitting | low priority |
| 1 | AlgoBook Big EA | position scaling | lot **increases after losses** (factor, capped by `lotsLimit`) | TO | **none** | — | — | **D** | no | — | — | martingale-type scaling; violates "no martingale / loss chasing" | take the architecture only |
| 2 | Quantum Queen | "trend-following grid", 6 strategies; martingale removed in v2 (SC) | adds positions as price moves; hedging account required | SC/TO | none for entries; illustrates grid dependence on 24/7 VPS | — | — | **D** (grid/averaging) | no | — | — | grid, averaging | +214 %, 87.85 % backtest win rate, 4.98★ = UMC |
| 3 | Mad Turtle | ONNX neural net + cascade meta-model filter, single position, no grid (SC) | ML direction model; meta-filter; 30–50 % held-out validation (SC) | SC | ONNX inference and meta-labelling filter | B (ONNX seam in `NEXA_Intelligence.mqh`, no model) | trained, calibrated model | yes, if AI only vetoes | F (meta-label veto) | NEXA Trade DNA + labels | purged CV, calibration, DSR, OOS | none if veto-only | 68 %, 46 % over 7 weeks, "~1,200 pips/trade" = UMC; 7 weeks is not evidence |
| 4 | Night Hunter Pro | Asian-session M5 mean-reversion scalping, SL on every trade, news/swap filters (SC) | session-conditioned MR with multi-filter confirmation | SC/TO | overlaps V2 F5 (Asian MR) | B (V2 F5 frozen) | — | yes | covered by V2 F5 (no change) | M1 + spread | as V2 | none | the review notes performance flattening after 2023 (SC); illustrates regime decay |
| 5 | Waka Waka | RSI/BB mean reversion with ATR-spaced grid (SC) | adds positions in drawdown | SC/TO | none | — | — | **D** | no | — | — | grid/averaging; 40–50 % DD (SC) | "70+ profitable months" = UMC |
| 6 | Perceptrader AI | perceptron filter gating a grid; optional LLM queries (SC) | AI filter decides grid activation | SC/TO | the *filter* idea only | B | — | grid **D**; filter pattern OK | F (regime/abstain filter) | — | — | grid | LLM trading value "unproven" per the review itself |
| 7 | AI Forex Robot | LSTM-Transformer, regime detection, "Guardian" exposure reduction in losing streaks (SC) | undisclosed logic; one position | SC | regime classifier; drawdown-conditioned de-risking | B (NEXA regime states; `StrategySurvivalOK`) | calibrated regime model | yes, only if it reduces risk | F | Trade DNA, D1/H1 | OOS + calibration | must only reduce risk | "no independent verification" per the review |
| 8 | EA Gold Stuff | trend signal + grid + 1.5× martingale + hedging, SL off by default (SC) | martingale grid | SC/TO | none | — | — | **D** | no | — | — | martingale, grid, no SL | the review itself warns of blow-up risk |
| 9 | Evening Scalper Pro | US-evening M5 MR on crosses, SL every trade, swap/news filters (SC) | session MR | SC/TO | an evening-session MR analogue of F5 | C | an evening session is not in V2 | yes | F (future campaign only) | M1 crosses + spread | full new frozen campaign | none | PF ≈ 1.0, 41 % DD (SC): no edge even by its own numbers |
| 10 | RoboForex guide | EA structure, new-bar detection, CTrade, normalisation | standard patterns | TO | baseline engineering hygiene | A | — | yes | no | — | — | — | NEXA already exceeds this |
| 11 | BM Trading | range breakout, index long-only, Turnaround Tuesday, Donchian, pullback, ATR candle breakout (SC) | independent single-strategy EAs; no portfolio framework | SC/TO | range breakout overlaps F2 | B (F2 frozen) | index CFDs are outside NEXA symbols | yes | F (ATR candle breakout; index day-of-week), future only | index CFD history | new campaign | none | no verification links |
| 12 | Scribd manual | London-session range breakout, 1:2 R:R (SC; preview only) | not accessible | SC | London-range breakout analogue of F2 | C | — | yes | F | M1 + spread | new campaign | none | manual body inaccessible; nothing filled from memory |
| 13 | Apex Drawdown Zero | one trade/day, volatility-aware SL, spread/margin checks, BE + trailing, no grid (SC primary) | conflicting descriptions (H1 multi-symbol vs M15 gold Asian breakout) | SC (primary) + UMC (secondary) | one-trade-per-day cap; pre-trade margin/spread validation | A/B (NEXA 10 trades/day cap, spread gate; no `OrderCheck`) | explicit pre-send `OrderCheck` | yes | no | — | — | none | "0.39 % max DD over 18 months" = UMC and implausible for a leveraged gold strategy (INF) |
| 14 | XenClarity | XAU H1 level trading, dynamic buffers, defined SL/TP (secondary) | not accessible | SC (secondary) | none specific | — | — | unknown | no | — | — | unknown | **not independently verified** |

## 3. Concepts classified
| Concept | Class | Where in NEXA / notes |
|---|---|---|
| Multi-strategy orchestration | C / F | NEXA is one strategy; V2 families are research only |
| Regime detection | B | trend/vol regime, `regimeTransitioning` (features); no calibrated classifier |
| Probability outputs / calibration | B | ONNX probability seam; `AI_CalibrationId()="NONE"`; no calibrated model |
| ML/ONNX inference | B | `OnnxCreate` / `OnnxRun` with schema check; no trained model; fails closed when required |
| Neural networks | E / F | vendor claims unverified; only as a future veto-only model |
| AI filtering / meta-labelling | B / F | AI can only veto (invariant 16); a meta-label veto is a future hypothesis |
| Session filters | B | `InSessionWindow` (off by default), session tags; V2 F2/F5 session families |
| Asian-session behaviour | B | V2 F5 (frozen) |
| American-evening behaviour | C / F | not in V2 |
| Range breakout | B | V2 F2 (frozen) |
| Mean reversion | B | V2 F5; the factory z-MR was negative (prior evidence) |
| Trend following | B | factory TrendLock tested: drift, not skill |
| Gold-specific systems | B | V2 F2 is XAU-only |
| Cross-pair diversification | C / F | correlation cap exists; no portfolio allocator |
| Execution / broker sensitivity | A | `nexa_execution` (trade-through fills, latency, stop-first), cost shocks in the protocol |
| Spread filter | A | spread ≤ 15 % ATR (invariant) |
| News filter | A | Tier-3 news veto + FOMC hard gate |
| Volatility filter | A | volState; displacement thresholds |
| Swap filter | C | EA has none; V2 research charges swaps (never credits) |
| VPS / latency | B | 250 ms latency modelled; no live latency monitor |
| Multi-symbol architecture | B | one EA instance per chart with shared GVs; cross-symbol reads not time-synchronised |
| Tester reporting / custom metrics | B | Trade DNA CSV (schema v1.0); no `OnTester()` |
| Adaptive logic | E | "adapts in real time" claims are untestable as stated |
| Model monitoring / drift | B | expectancy stats, shadow ledger (diagnostic), research validate gate |
| Drawdown controls | A | daily 2 %, max DD 10 %, emergency stop, survival gate |
| Recovery mechanisms (lot-up) | **D** | rejected: martingale / loss chasing |
| Signal confirmation | A | composite + quality score, HTF alignment |
| Trade selection / "unique trades" | C / F | untested diversification idea |
| Position management | A | BE at 1R, partial at 1.5R, time exit, weekend close |
| Grid / averaging down | **D** | rejected (invariants 8–10) |
| Forced trading | **D** | rejected; NO_TRADE is valid |
| Mechanisms bypassing `NEXA_Risk` | **D** | rejected |
| Performance / rating claims | **E** | all unverified marketing claims |

## 4. What NOT to take from this prior art
- **Rejected as incompatible:** grid, martingale (including capped "factor" scaling as in the AlgoBook example), averaging down, recovery lot-ups, hedged grids, disabled stop-losses, and "trade every night" frequency targets.
- **Win rate is never a selection criterion.** Many of these EAs report high win rates alongside large drawdowns or PF ≈ 1.
- **V2 is unchanged by this report.** Any idea from it must enter a **new** frozen campaign with its own trial count added to the multiple-testing ledger. See `NEXA_FUTURE_RESEARCH_BACKLOG.md`.
