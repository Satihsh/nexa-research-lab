# 20: MASTER RESEARCH REPORT
## NEXA Knowledge + Intelligence Synthesis (research phase, 2026-10-04)

**Deliverable:** `research/intelligence/` (this package):
- documents 01–20;
- `sources/` (per-source notes for the 15 new PDFs);
- `evidence/` (two measured data probes, with code, inputs and outputs).

**Not touched:** the S14 forward test, the EA, NEXA_Risk, production inputs, schema v1, PackFeatures(), V2 and 8E.

---

## 1. What was done

1. **Inventory of the 56 files.**
   - **Original:** 39 PDFs (38 works).
   - **New:** 17 files, which are **15 PDFs and 2 `.bibtex` citation stubs**.
   - The two most GEX-specific "new" titles are **not in the corpus**.
   - Two new PDFs are **third-party summaries**, not the named books: S40 (Coulling cliff-notes) and S47 (a Bookey summary of Zuckerman).
2. **Read and classified all 15 new PDFs** (sources/), and merged them with the original knowledge base. The result is 01: tiers, duplicate families, 11 new contradictions and the agreements.
3. **Probed the connected Massive MCP** endpoint by endpoint and measured what the plan actually returns (03):
   - **aggregates only;**
   - **a rolling ≈ 2-year window;**
   - **no trades, quotes, OI, greeks, snapshots or indices.**
4. **Measured two proxy-validity questions** with real data (`evidence/`):
   - **CFD tick volume vs COMEX/CME volume** (hourly):
     - log r = 0.82 (GC) and 0.88 (6E);
     - **0.67 / 0.57 after removing intraday seasonality.**
   - **Tick-volume daily profile vs COMEX profile:**
     - VA Jaccard median **0.82**;
     - POC within $2 on 65 % of days, with **$12–68 misses on bimodal days**.
   - **Futures–spot gold basis:** +$49.7 → +$35.1 over September 2026.
5. **Built the framework:**
   - mathematics (09);
   - 37-entry equation registry (11; IDs EQ-001–035, 038, 039; 036–037 unassigned);
   - liquidity, order-flow, volume/delta, microstructure and options models (04–08);
   - physics audit (10);
   - 10 matrices (12);
   - feature catalog, RAW → PREDICTIVE (13);
   - 38 registered hypotheses (14);
   - validation protocol (15);
   - architecture (16);
   - ranked implementation candidates (17);
   - 22 rejected concepts (18);
   - data requirements (19);
   - 20 research gaps (02).

**No hypothesis was tested for outcomes.** All HYP statuses are UNTESTED, except HYP-001, which is TESTING (proxy validity).

## 2. Ten findings that matter most

1. **Data, not mathematics, is the binding constraint.**
   - True order flow, delta, footprint, book depth, option OI, greeks and dealer positioning are **unavailable** to NEXA.
   - Pepperstone ticks have no trade side (13.3M ticks checked). Massive's plan has no trades, quotes or OI.
2. **GEX is a measurement convention without predictive evidence in the corpus.**
   - The sign is an **inventory assumption** (put–call parity, S54).
   - **Two corpus sources use opposite signs** (S50 vs S53/S54).
   - **The only academically supported effect is on volatility, not direction** (Ni et al., via S50/S53).
3. **Pinning requires hedge flow that is large relative to underlying volume** (S48). Gold and major FX are deep markets. The proposed **hedge-pressure ratio** (EQ-029) is the first number to measure if OI is ever acquired.
4. **Order flow is strongly *contemporaneous* with returns** (S51: R² < 10 % → > 50 % with limit flow), and **heterogeneous** by participant type (S52). **No corpus evidence shows it predicts at NEXA's ≥ 1-minute decision clock** (contradiction CN8 / original A6).
5. **The new practitioner books give NEXA a precise, testable vocabulary**: IB, range extension, day types, open types, value-area rule, 3-1 days, profile shapes. **Their only statistics are Dalton's 1986–87 T-bond tallies, with no base rate**, so every claim is a hypothesis.
6. **Volume profiles are buildable now:** spot (9 years, proxy) and futures (2 years, true). **Value areas are a sound proxy; POC is not.**
7. **The directive's "Delta > 300 %"** is S44's footprint display default. It is unjustified, needs data NEXA lacks, and is replaced by percentile and seasonal-ratio normalisation.
8. **NEXA's own measured failure is a cost-geometry problem on top of a slightly negative gross edge.**
   - Gross −0.072R; commission alone 0.245R at 2.4-pip median stops.
   - Mathematically (EQ-024/025/034), **stops and exits cannot create edge without drift**, but **stop distance controls cost-in-R** (HYP-024).
9. **Volatility remains the strongest-evidence layer** (original P2 plus S48's estimators). It is the unit for every other feature and the first thing to build (17 #2).
10. **Physics contributes notation, not laws.**
    - Density "potential/force" gives HYP-005.
    - Regimes give HYP-020.
    - Entropy gives HYP-021.
    - "Market energy", chaos, RMT, percolation and similar ideas are rejected.

## 3. The central question (directive §27)

> *Can NEXA build a mathematically rigorous, mechanical market-state model that combines option positioning + GEX + liquidity + volume profile + delta + order flow + market structure + volatility + regime + execution microstructure into a single probabilistic decision framework?*

### Answer: **PARTIALLY.**

**The mathematics is not the obstacle.**
- A single coherent framework exists (09):
  - a latent-regime state-space model over a block observation vector;
  - outcome laws mapped to P_U through the drift/volatility two-barrier formula (EQ-034);
  - net expectancy (EQ-025) with a cost model;
  - Bayesian decision rule plus deterministic risk engine.
- It is **mechanical, causal and testable**.
- **Absent data blocks are formally absent, not imputed.**

**What can be reliably combined *now*** (data available, definitions causal, tests specified):

| Component | Status |
|---|---|
| Price, volatility (YZ/HAR), compression, efficiency, variance ratio, entropy | **YES**: TRUE data, strongest prior |
| Regime (observed Markov / HMM, filtered) | **YES**: TRUE data |
| Market structure (existing f00–f46) + session/auction structure (IB, REX, day/open type) | **YES**: TRUE data; codification pre-registered |
| Volume profile / revealed liquidity (VA, HVN/LVN, gradient, curvature, concentration) | **YES, as PROXY** (spot tick volume; VA validated at 0.82 Jaccard on one month) and **TRUE** for futures over 2 years (basis-mapped) |
| Activity: seasonal RVOL, effort/result, Amihud, futures trade size | **YES**: futures TRUE, spot PROXY |
| Cross-asset context (USD basket, ES volatility, yields) | **YES**: TRUE, non-stationary |
| Execution microstructure (spread, quote intensity, own slippage) | **YES, prospectively** (S14 demo from 2026-10-05) |

**What cannot be combined, and exactly where it breaks:**

| Component | Breaks at | Specific failure |
|---|---|---|
| **Delta / order flow** | **Data** | No aggressor side anywhere in NEXA's sources. Only quote-direction or BVC proxies, which are same-bar circular, unvalidated and (for ticks) not reproducible offline. Proxy results cannot confirm or refute order-flow theory |
| **Delta profile** | **Data** | Proxy of a proxy |
| **Option positioning / GEX / walls / dealer hedging** | **Data and identification** | No OI or greeks; no COMEX gold options; FX options OTC. **Even with OI, the sign is unidentified** without signed flow (S54; S50 shows the opposite sign is economically valid in some markets) |
| **"Options for WHERE, flow for WHEN"** | **Evidence** | Neither half is tested in the corpus at NEXA's horizon. Only a **proxy** version (profile levels + lagged proxy flow) is testable (HYP-022, EQ-032) |
| **Any edge claim** | **Statistical evidence** | Every new-corpus trading claim is unverified. NEXA's own engines are negative after costs. **No component has passed a frozen out-of-sample test** |

**How the framework is built (the "show exactly how" part, for the reliable subset):**
1. **Observation vector:** blocks x^P, x^V, x^L, x^S, x^T, x^X, x^E (13). All normalised: σ̂ units, seasonal ratios, percentiles. All causal (< decision-bar close).
2. **State:**
   - filtered regime probabilities from M-06 (EQ-023);
   - the revealed-liquidity field M-02 (EQ-012–015) evaluated at the current price;
   - the volatility forecast σ̂_{t+1} (EQ-004).
3. **Forecast:**
   - μ(x) and σ(x) from regime-conditioned models (expected |μ| small; tested in HYP-020/005/006);
   - P_U from EQ-034;
   - P(level reaction) from level models (HYP-004–007, 015).
4. **Decision:**
   - E[R_net | x] = EQ-025 with c = E[c | x^E] (M-09);
   - act iff above κ, calibrated, validated (15 §7), and authorised by NEXA_Risk;
   - **otherwise abstain.**
5. **Learning:** the Trade DNA records forecasts (future schema v1.1). Outcomes update the registry (14). Failures are kept.

### What would turn PARTIALLY into YES

**Data:**
- **(a) Aggressor-signed futures trades or quotes** (19 D2): true delta, footprint, a real WHEN test.
- **(b) COMEX gold option OI + IV history, with signed volume** (D3, D4): GEX, HPR, sign identification, for **gold only**. **FX GEX remains impractical.**

**Evidence:**
- **(c) Frozen out-of-sample passes** for the volatility layer and at least one level-reaction family, robust to costs. **That is the statistical gate. Nothing here pre-judges its outcome.**

## 4. Recommended next steps (each needs approval; none touch production or the S14 test)

1. **17 #1, proxy-validation study, full 2 years:**
   - decides HYP-001 and HYP-034;
   - archives Massive data locally before the rolling window advances.
2. **17 #2, volatility layer:** HYP-001b, HYP-002, HYP-019.
3. **17 #3, fixed-entry stop/cost re-simulator:** HYP-024, HYP-023 (H2, H3, H5), aimed at the measured cost-in-R failure.
4. **17 #4 + #6, session anchors + placebo/base-rate engine:** then HYP-008–013 (the Market Profile claims) with base rates.
5. **Leave Tier 3 (GEX) blocked** until a data decision. If pursued, test the *volatility* channel (HYP-025) first, with both sign models.

## 5. Integrity statement

- **No data, equation, citation or result was fabricated:**
  - every corpus claim is tagged SOURCE with its file;
  - standard literature outside the corpus is tagged EXTERNAL and named;
  - every number from our own work is tagged MEASURED and backed by code in `evidence/`.
- **The two `.bibtex` files are not cited as content.** S40 and S47 are cited as summaries.
- **Previous NEXA failures (8E REJECTED; cap-neutral NO EDGE) are kept as constraints** and not reinterpreted.
- **The answer is PARTIALLY, not yes.** The breakdown is data first, then evidence.
