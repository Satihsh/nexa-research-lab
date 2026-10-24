# 16: NEXA INTELLIGENCE ARCHITECTURE

**Status: a research architecture.** It describes how validated components *would* connect. Today:
- **no component** beyond the existing EA is approved;
- **no layer** has passed 15;
- **the S14 forward test runs the unchanged production EA.**

## 1. Pipeline (directive §25), annotated with data reality

```
MARKET DATA ─────────────────────────────────────────────────────────────────────────
  MT5 quotes/M1 (TRUE price; tick volume = PROXY activity)     Massive futures 1-min (TRUE volume, 2 y)
  Massive FX/ETF/options aggs (unsigned)   Treasury yields   Trade DNA + tick logger (execution, prospective)
        │   [UNAVAILABLE: aggressor flow, depth, option OI/greeks, VIX]  → blocks ABSENT, never imputed
        ▼
OBSERVATION VECTOR x_t  (13: NF-xxx, all causal, normalised, PROXY-tagged)
        ▼
MARKET STATE        x^P volatility (YZ/HAR), compression, ER/VR/PE                 [AVAILABLE]
LIQUIDITY STATE     x^L revealed-liquidity field L(p,t): VA, HVN/LVN, g, κ, C      [PROXY spot / TRUE futures]
ORDER-FLOW STATE    x^F lagged proxy δ̃, absorption (EVR/ABS)                       [PROXY only]
OPTIONS/GEX STATE   x^O GEX, flip, walls, HPR                                       [ABSENT: data]
STRUCTURE/SESSION   x^S existing f00–f46 + IB/REX/open type/day type; x^T session    [AVAILABLE]
CROSS-ASSET         x^X USD basket, ES vol, ΔUS10Y                                   [AVAILABLE]
EXECUTION STATE     x^E spread, quote intensity, E[c|x^E] (M-09)                     [prospective]
        ▼
REGIME              filtered P(z_t | x_≤t) (HMM / observed Markov, M-06)
        ▼
PROBABILISTIC FORECAST   σ̂_{t+1}; μ(x) (drift, usually ≈ 0); P_U via EQ-034; P(level reaction)
        ▼
EXPECTED VALUE      E[R_net | x] = EQ-025 with c = E[c | x^E]
        ▼
TRADE HYPOTHESIS    h = (d, e, D, U, H): D from σ̂ / structure (HYP-023/024); U, H pre-registered
        ▼
NEXA JUDGE          act iff E[R_net|x] > κ  ∧ calibrated  ∧ candidate validated (15 §7)  ∧ not abstain
        ▼
DETERMINISTIC RISK ENGINE   NEXA_Risk (unchanged; fail-closed): ceiling, daily budget C4, exposure,
                            correlation cap, drawdown, survival pause, news gate
        ▼
EXECUTION           market/IOC (S14): post-fill hard-ceiling guard, signed slippage logging
        ▼
TRADE DNA           decision row: features + model version + forecast P_U, E[R] (needs schema v1.1)
        ▼
OUTCOME (labels from fill_ts)  →  VALIDATION / LEARNING (15)  →  registry status (14)
```

## 2. The separation the directive proposes: what the evidence supports

| Layer | Directive's content | What NEXA can actually populate | Evidence status |
|---|---|---|---|
| **LEVEL / SETUP ("WHERE")** | Option flow, GEX, walls, liquidity, volume profile | **Volume profile / revealed liquidity** (VA validated as a proxy) and **structure levels** (f32–f46). **GEX and walls: absent** | HYP-004–007, 015 UNTESTED. GEX BLOCKED |
| **CONTEXT** | Structure, delta profile, volatility, regime, session | Structure ✓, volatility ✓ (strongest prior), regime ✓, session ✓. Delta profile: proxy-of-proxy | Volatility layer: strongest. Others UNTESTED |
| **EXECUTION ("WHEN")** | Order flow, delta, aggression, absorption, consumption, microstructure | Lagged proxy δ̃ and **unsigned** absorption (EVR/ABS). Aggression and consumption: **absent** | HYP-003/017/018/022 UNTESTED; prior expectation weak |
| **RISK** | Deterministic engine | **Exists** (NEXA_Risk; S11, C4, D-TZ, S14 fixes) | Engineering-verified |
| **EXECUTION ENGINE** | — | **Exists** (S14 demo forward check now collecting fills) | Prospective |

**Is "options/GEX for WHERE, order flow for WHEN" quantitatively validatable?**
- **In principle, yes:** EQ-032, the WHERE/WHEN conditional-MI decomposition, with a placebo-level design.
- **For NEXA now:**
  - only a **proxy version** is testable: profile levels for WHERE, lagged proxy flow and absorption for WHEN (HYP-022);
  - the options half is **untestable** (data).
- The literature gives a mechanism for each half (dealer hedging; contemporaneous flow impact) but **no predictive test of either half at NEXA's horizon**.

## 3. Mapping onto NEXA's existing code (no change made or proposed here)

| Architecture box | Existing NEXA component | Gap (future, needs approval) |
|---|---|---|
| Observation / features | `PackFeatures()` f00–f47 (schema v1.0, frozen) | NF-xxx would require schema v1.1 (append-only, retrain) |
| Volatility state | ATR-based (`displacementATR`, `spreadATRRatio`, volState) | YZ/HAR σ̂ (HYP-001b) |
| Liquidity state | Liquidity-sweep event features (f32–f46, "liq*") | Revealed-liquidity field (06) |
| Order-flow state | f30 obiProxy, f31 cvdProxy (tick proxies; parity-exempt) | Lagged futures BVC (research only) |
| Regime | trendState, volState, breakoutState, regimeTransitioning (f20–f23) | Filtered HMM probability |
| Forecast / Judge | Composite score + quality points + optional ONNX meta-model (absent in the deployed setup: AI = NONE) | Calibrated P_U / E[R] model |
| Risk engine | NEXA_Risk (a43d8328…) | None proposed |
| Execution | NEXA_EA S14 (ff30ac38…), FillGuard | None proposed |
| DNA / learning | Trade DNA v1.0 + research tier (`nexa_parity`, `nexa_stats`, Gate 8) | Forecast columns (v1.1) |

## 4. Design principles (from the evidence)

1. **The only channels to value are P_U, P_H, E[R_H] and cost c** (09 §2). Every component must show its effect through one of them.
2. **Volatility first.** It is the strongest-evidence layer and it sets D, P_H and cost-in-R. It is also where NEXA's measured failure lives (commission at 0.245R from tiny stops).
3. **Abstention is a first-class output.** "No candidate" is the default (directive §14: "do not force trades").
4. **Absent data stays absent.** No GEX-like or order-flow-like feature is fabricated from price alone. Proxy features are labelled through to the Trade DNA.
5. **The deterministic risk engine stays the final authority.** Intelligence only *proposes*.
6. **Reproducibility:** bar-based definitions are preferred over tick-only ones (parity contract). Tick-only features can never be the sole basis.
