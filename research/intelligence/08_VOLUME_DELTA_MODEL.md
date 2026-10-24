# 08: VOLUME & DELTA MODEL (Tiers 1–2)

## 1. Volume: three different things that must never be mixed

| Measure | Meaning | Source | Status |
|---|---|---|---|
| **Exchange volume** V^F | Contracts traded on CME/COMEX | Massive futures 1 min (2 y) | TRUE |
| **Exchange transactions** N^F and **average trade size** V^F/N^F | Trade count; size per trade (a "participant size" proxy) | Massive futures | TRUE |
| **Tick volume** V^T | Count of the broker's quote updates per bar | MT5 M1 (9 y) | PROXY for activity (hourly r 0.82–0.88; de-seasonalised 0.57–0.70) |
| **Massive FX `v`** | Count of Massive's FX quote updates (v == n) | Massive FX 1 min (2 y) | PROXY (r 0.91 with Pepperstone tick volume) |
| **Option volume** | Contracts per option series (GLD) | Massive options | TRUE for GLD options. Unsigned. Not positioning |

**Rule:** every volume feature carries its source tag (F/T/MFX/OPT). Comparisons across sources use **seasonal ratios or percentiles only**, never raw levels.

## 2. Volume models

**V-1: seasonal activity (EQ-005).** RVOL_t = V_t / Ê[V | how(t)].
- **Foundation for everything else**, because the raw level is dominated by the intraday cycle. MEASURED: the hour-of-day profile is shared across sources at r = 0.93–0.98.

**V-2: volume–volatility relation** (mixture-of-distributions, EXTERNAL Clark 1973; S48 variance focus).
- E[ln RV_{t+1} | HAR terms, ln RVOL_t] (HYP-002). Question: does activity add to volatility forecasts beyond past volatility?

**V-3: effort vs result (EQ-006, S40).**
- EVR_t is the residual of ln|r| on ln V (rolling, lagged coefficients).
- **Interpretation:** absorption (EVR ≪ 0) vs a thin move (EVR ≫ 0).
- **Test (HYP-003):** sign and magnitude of the next-k-bar return conditional on EVR, at levels vs off levels.

**V-4: participant-size proxy (futures).** Abnormal V/N (large average trade size) relative to seasonal median.
- **Mechanism (S52):** institutional "signal" agents trade large clips. **The data cannot identify agents.**
- HYP-016 includes it as an ablation candidate.

**V-5: volume profile = revealed liquidity** (06): a separate model.

## 3. Delta (signed volume): proxy only

**True delta δ = V^{buy-initiated} − V^{sell-initiated} is UNAVAILABLE.** Two proxies exist:

| Proxy | Formula | Pros | Cons |
|---|---|---|---|
| **Tick-rule on spot quotes** (f30/f31) | EQ-008 | Live, per quote | Quote revision ≠ trade; non-reproducible (parity-exempt); 28 days history |
| **BVC on futures 1-min bars** | EQ-009: δ = V(2Φ(Δp/σ̂) − 1) | 2 years; reproducible; uses true volume | Monotone in the same-bar return (circular); unvalidated at 1-min granularity; loses intra-bar sequencing |

**Normalisation (EQ-010):** δ̃ = δ/V; δ* = δ/Ê[|δ| | how]; seasonal percentile πδ. **Never raw thresholds.**

**Delta profile (signed volume at price):**
- **Definition:** DP(p,t) = Σ_{s<t} w(t−s)·δ_s·K_h(p − p̄_s), with the bar's delta assigned at its typical price.
- **Status:** PROXY of a PROXY (BVC sign × bar allocation).
- **Not prioritised.**

## 4. Delta hypotheses (14)

| ID | Statement | Expected (prior) |
|---|---|---|
| HYP-017 | Lagged proxy δ̃ predicts next-H return (σ̂ units) | **Null expected** (corpus A6; S51 contemporaneous only) |
| HYP-018 | Proxy cumulative-δ divergence on the approach to a level predicts reaction (S44) | Low prior; test as part of the level family |
| HYP-017b | f30 quality gate (\|OBI\| > 0.15) adds value to the existing engine | Unknown. **The existing EA uses it untested.** Ablation on the S14 demo plus tick-logger data only (non-reproducible offline) |

## 5. What would make delta real

**Futures trades with aggressor side** (vendor or entitlement upgrade) would allow:
1. validation of BVC at 1 minute;
2. true δ, footprint and imbalance features;
3. re-running HYP-017/018 on true data.

**Until then, every "delta" result is a statement about a proxy, and its negative results do not refute order-flow theory** (09 §8).
