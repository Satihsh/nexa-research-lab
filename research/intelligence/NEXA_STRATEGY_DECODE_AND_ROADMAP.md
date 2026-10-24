# NEXA strategy decode and roadmap (2026-10-11)

**Scope (user request, 2026-10-11):**
1. Fabio Valentini's IVB rules in detail.
2. Decode 15 user-supplied videos and find the real strategy in each.
3. Which can run in MT5, and what to do where MT5 cannot.
4. Cross-check against everything NEXA has researched and tested.
5. Advanced mathematics and quantum physics: what is useful.
6. The best next steps for NEXA.

**Status:** research only.
- No production code, MT5, NEXA_Risk or EA change.
- No data purchased; no test run.
- Every test proposed below needs the user's approval and a pre-registration.

**Evidence references:**
- `orderflow/kb/CLAIMS.md` CL-118…141, `SOURCES.md` YT-031…057;
- prior tests in `validation/RESEARCH_GATE.md`;
- the corpus backlog in `../knowledge/RESEARCH_HYPOTHESIS_BACKLOG.md`.

---

## 1. Fabio Valentini's IVB model, in detail

**Sources:**
- primary: `cUTsoU-15Tc` (YT-031), "5 Edges" `StaphlRH8NQ` (YT-036), live sessions YT-040…042 / YT-056;
- third-party test: YT-030.

**What is stated:** the rules below. **What is missing:** marked **GAP**.

| Step | Rule as stated | GAP / note |
|---|---|---|
| Market and session | NASDAQ futures (NQ), New York cash session (opens 09:30 ET). He has "only tested NASDAQ" and warns that correlated markets (ES) can behave differently | Not FX or gold |
| 0. Daily bias (optional, his routine) | **Profile framing:** prior cash-session profile shape (P-shape / acceptance → bias). Options and gamma pressure as context | How the bias overrides IVB is not specified |
| 1. Opening range | Point A = high and point B = low of the **first 15 or 30 minutes** of the cash session. DeepCharts' IVB waits for the **first 30 minutes** to complete; the range expands until then | His 30-min version is the documented one |
| 2. Range profile | A **fixed volume profile** over the opening range → the range's **POC, VAH, VAL** | VA % not stated (DeepCharts default) |
| 3. Direction | The **first side to break** the range tells "who won the battle of the most important time of the day". Trade only in the breakout direction once price **accepts** outside the range | **GAP:** the breakout confirmation (candle close? which timeframe?) |
| 4a. Model 1: location | After the breakout, wait for a **retrace into the zone between the range's value-area edge and its POC** ("the real block of orders, where buyers reload"). Use alerts or limits there | **GAP:** which half (VAH–POC vs POC–VAL) is ambiguous in the transcript |
| 4b. Model 1: invalidation / stop | A **candle close back through the range's VA low** (long case) invalidates the setup. Stop there; no need to wait for the opposite extreme | The mirror applies for shorts |
| 4c. Model 2: confirmation | In the same zone, wait for an **order-flow trigger:** (a) **absorption** (aggressive sellers with zero result at the POC/VA) → long; or (b) **exhaustion** of sellers plus buyer aggression with momentum → tight-stop momentum entry. Sequence: **direction 1, location 2, order-flow confirmation 3** | **GAP:** no thresholds. Live practice: big-trade bubbles ≥ 30 NQ contracts (NY) |
| 5. Targets | **TP1 = "protection level"**, a DeepCharts algorithm (claimed NN/ML on years of data, reached with "65–70 %" probability). **TP2 = "maximum extreme average"**, lower probability. Typical R:R 1:2–1:2.5 (Model 1), up to 1:3–1:5 with order flow | **GAP:** the protection-level algorithm is proprietary and not reproducible |
| 6. Before a breakout | Inside the range: mean-revert at the range top/bottom on absorption or exhaustion until a side breaks | — |
| 7. Management (live) | Scale in small; go **risk-free fast**; trail below the last aggression / effort box; **no partial profits on NQ** (they "always hurt") | Discretionary |
| 8. Risk (live) | Daily max loss ≈ USD 10k; stop after ≈ USD 20k; ≈ USD 2k risk per trade on ≈ USD 1M+ accounts (≈ 0.2 %). Personal guidance 0.5–1.25 % per trade | — |

**Claims and evidence:**
- **"13.5 % skew over a coin flip"** for the plain 30-min IB breakout on NQ at 1:1: presenter claim, no sample shown.
- **"Audit by an ex-market maker":** unverified.
- **Independent coding of the reel** (YT-030): the volume confirmation **hurt**; profitable settings came only after about 9,900 optimisation runs, with no out-of-sample test.
- **ORB literature (B1):** gross-positive on US equities; **net ≈ 0** on five index CFDs (independent replication); the Zarattini paper assumes no slippage (CL-132).
- **Verdict: unverified.** It is the best-documented public part of Fabio's method, but its key target (the protection level) is a black box.

**MT5 feasibility:**
- **Model 1** (range + range profile + retrace zone + VAL invalidation) can be approximated on **Pepperstone NAS100** with a tick-volume profile (shape proxy OK, edges ±several points; CL-109).
- **Model 2** needs true order flow (not on MT5 / Pepperstone).
- **The protection level** cannot be reproduced.

---

## 2. The 15 videos decoded

| # | Video | Real strategy (one line) | Needs | MT5 / Pepperstone? |
|---|---|---|---|---|
| 1 | **HUYBdYnXUNc** (IQCapital), Fabio's "entire new strategy" | **Value-migration scalp:** each candle's VA/POC migrating with the candle colour and delta → repeated 1:1 entries in the migration direction, stop beyond the candle VA; proprietary "effort" boxes as a filter and trailing. Trend-only; ≈ break-even in chop; he would **not** automate it (CL-135) | Per-candle volume at price (true volume) | **Partly:** a per-candle VA from tick volume is a proxy. The effort boxes are proprietary |
| 2 | **DyS79Eb92Ug** (Chart Fanatics), Fabio live 2 h 21 m | AAA setup: VA low on a momentum day, absorption → VA high; VAH break-and-test; momentum squeeze. Bubbles ≥ 30 (NY) / 20 (London). Strict daily loss / profit stops (CL-136) | Aggressor data | **No** (the trigger) |
| 3 | **xUyqIjCfZzg**, Fabio + Carmine Rosato live 3 h 49 m | Discretionary: Carmine = mean reversion at horizontal areas + delta divergence + VWAP; Fabio = IVB / ORB when it sets up, momentum otherwise | Aggressor data | **No** |
| 4 | **ftJ9XuIaOXY**, Chris Kramer rules coded with Claude Code | **The most complete public rule set** (CL-137): value migration up → longs only; Fib 70.5–88.6 % pullback zone below the VAH; 5-min footprint absorption + ≥ 400 % stacked imbalances + higher-low retest; stop under the wick + 2 ticks; 1.5R capped; **2 losses → stop for the day**; 09:30–11:00 ET only | Aggressor-tagged trades (free on crypto exchanges; paid on CME) | **No** for the trigger. The value-migration filter and Fib zone are MT5-able |
| 5 | **zspMXJVbfAY** (The Rumers), "sneaky pivot" | **Pure price action** (CL-138): prior-day high/low plus the next swing levels; 15-min opening candle into a line → confirmation candle → enter on its break; stop beyond; target the opposite line | OHLC only | **Yes, fully** |
| 6 | **9IliXww64uM** (Andrea Cimi) | 10-day composite profile + prior RTH profile; open inside value → range day → fade the edges on absorbed big trades; breakouts only after acceptance outside (CL-139) | Profile + aggressor data | Profile part as a proxy; trigger **no** |
| 7 | **4L1qo7svEg4** (Lunar), Big Trades indicator | Big single executions failing at an HTF zone → absorption fade; settings: separated trades, min size (CL-140) | Aggressor data | **No** |
| 8 | **8eoTwrFXZo0** (The Orderflow Edge) | Big trades + delta footprint (DeepCharts "Deep Trades"), educational; notes big-trade bubbles are an old concept | Aggressor data | No |
| 9 | **JrHdpg7-1_U** (Amit Noriya) | MotiveWave set-up for Big Trades, delta profile, imbalance (200–300 %) | Aggressor data | No |
| 10 | **cVJs-Ndnh9s** (DejaBrew) | ATAS footprint / DOM settings | — | Platform tutorial |
| 11 | **ljk9BovCSqI** (TradingLab) | Footprint basics (per-candle VA, delta, imbalances). Claims imbalances "predict exactly where price reverses" (unverified) | Aggressor data | No |
| 12 | **Vinyl5fKDW8** | Futures and order-flow beginner course (spot vs futures, brackets) | — | Educational |
| 13 | **9eqDWJSvCx4** (Fractal Flow) | Volume-profile / VSA theory (balance ↔ imbalance, 70 % VA ≈ 1σ analogy) | — | Educational |
| 14 | **8peJK-8BSQA** (Mind Math Money) | Volume-profile course (VA 70 % defaults, settings) | — | Educational |
| 15 | **PBBSMSyU674** (Miles Deutscher), AI trading bot guide | **No transcript returned** (page and description only). Topic: building AI bots; "made USD 8k/week… lost tens of thousands building them wrong" | — | n/a |

**What the 15 add:**
- **Two genuinely new rule sets:**
  - **Kramer's** (complete, testable on CME data already owned);
  - **the sneaky pivot** (MT5-native, testable on Pepperstone data already owned).
- **One new Fabio model:** value migration (testable in proxy form).
- **The rest repeats the knowledge base:** absorption of opposing big trades at value edges; profile framing; strict daily risk stops.

---

## 3. What MT5 can and cannot do, and what NEXA could become

**MT5 / Pepperstone can:**
- anything built from price, time, spread, tick counts and volatility: opening-range rules, the sneaky pivot, intraday momentum, volatility scaling, session effects;
- volume profiles **as a proxy** (shape good; edges ±3–4 pips typical, ±17–19 pips at p90 on 6E; CL-109).

**MT5 / Pepperstone cannot:**
- aggressor side, true traded volume, footprints, delta, Big Trades, absorption, icebergs. Pepperstone ticks carry no buy/sell flag and volume = 0 (13.3M ticks checked).

**If a true order-flow strategy ever passes a test** (none has), NEXA would need a **multi-venue design**. The components:

| Layer | Option | Cost (published) | Fit |
|---|---|---|---|
| **Core** | Keep NEXA's research and risk logic **venue-agnostic** in Python: signals, the NEXA_Risk rules, the DNA journal, pre-registration and the DSR toolkit. Venues plug in as adapters | — | One risk engine everywhere |
| CFD / FX venue | **MT5 / Pepperstone** (existing EA + the `meta-trader-mcp` bridge, trading disabled) | Existing | Price/time strategies |
| CME order-flow data | **Databento live** (trades with aggressor + MBO) | From USD 32.65/month (non-professional) | Same data as the research; already integrated (python client, guard) |
| CME execution | **Interactive Brokers** (TWS API / `ib_async`, Python) for MNQ / M6E / MGC micros; or **Rithmic** through a futures broker (R\|API) | Commissions about USD 0.25–1 per micro side + exchange | IBKR = Python, no new platform; Rithmic = lower latency |
| Order-flow-native platforms (alternative) | **Sierra Chart** (ACSIL C++), **NinjaTrader 8** (NinjaScript C#, Order Flow+), **ATAS** (C# API), **Quantower** (C# API) | Licences + Rithmic or CQG data | Fast to prototype visually; locks logic into one platform |
| Crypto venue (cheapest order-flow lab) | Exchange WebSocket trade streams carry a **free aggressor flag** (CL-141); CCXT for execution | Free data; exchange fees | Good for **building and validating order-flow code**. Different market; custody / regulatory risk |

**Recommendation on venues:** decide this **only after** a strategy passes a pre-registered out-of-sample test. Until then, **MT5 stays the single live venue**, and order-flow work stays in research on the data already owned.

---

## 4. Everything NEXA has tested so far (from the first conversation to now)

| Line | Verdict | Lesson |
|---|---|---|
| V1 registry | REJECTED | — |
| **V2 (six families)** | **FROZEN, unopened; out-of-sample is prospective from 2027-01-04** | The most rigorous live candidate set; must not be touched without "OPEN V2" |
| 8E (8 engines; "+24.5 %/day") | REJECTED; +24.5 %/day contradicted (0 target days in 1,774 streams) | Unrealistic targets |
| Cap-neutral campaign (exposure cap) | No edge, −0.318 R/trade | — |
| T1 / T2 | Tick-volume proxy OK for XAU/EUR/JPY (not GBP); HAR/rough vol not better than ATR | Proxies have limits |
| OF-16 / 19 / 20 / 20b | No edge / rejected / inconclusive | Profile and IB rules fail on spot |
| C1 (Tokyo fix) | Real gross effect, **net negative** | **Costs kill small gross edges** |
| C2 (time-series momentum) | REJECTED | Swaps distort |
| **OFC1 / OFC1R** (the user's order-flow method on true CME data) | **REJECTED**, −0.21 R and −0.12 R; no better than random timing | Order-flow confirmation only cuts losses slightly |

**The common thread:** about ten pre-registered tests, and **nothing has survived realistic costs**.
- The one consistent gross effect (C1) died on commission.
- Tight-stop scalping is the most cost-sensitive style there is, and it is what most order-flow educators teach.

---

## 5. Advanced mathematics and "quantum physics": what actually helps

**Quantum computing and "quantum finance":**
- **No evidence of a trading edge at NEXA's scale.**
- Quantum annealing / QAOA portfolio optimisation is research-stage, and NEXA's problem sizes (a handful of instruments) are solved exactly and instantly by classical methods.
- "Quantum finance" path-integral formulations (e.g. Baaquie) re-express option pricing; they do not predict returns.
- Fabio mentions "spending money on quantum research" (YT-057): unverified, and no result shown.
- **Recommendation: do not spend on quantum.**

**Mathematics that does matter (most of it is already in NEXA):**

| Tool | What it does for NEXA | Status |
|---|---|---|
| Pre-registration, Deflated Sharpe, PBO/CSCV, BH-FDR | Stops overfitting from looking like an edge | **In use** (every test since OF-16) |
| Driftless two-barrier hit probability (H-HIT-PROB) | Explains "high win rate" claims: with no edge, P(hit TP before SL) = SL / (SL + TP) | Backlog; used as a null |
| Cost-to-move gate (H-COST-SHRINK) | Trades only when the expected move ≫ round-trip cost; the cost floor already blocks the worst | Partly in use |
| Optimal execution (Almgren–Chriss; limit vs market) | Reduces costs, the one thing that killed C1 | Not built; needs live fill logging (S14) |
| Volatility forecasting (HAR, rough vol) | Better stops and sizing | Tested: **not better than ATR** for NEXA |
| Kelly / fractional, drawdown-constrained sizing | Grows capital faster **only if an edge exists** | Backlog (H-MU-SIGMA2) |
| Regime models (HMM, Hurst, efficiency ratio) | Conditioning variables (trend vs chop); Fabio's and Kramer's main failure mode is chop | Backlog (H-HURST-GATE, H-THICKNESS-ER) |
| Information theory (entropy, transfer entropy) | Lead–lag detection between FX/XAU/indices | Backlog (H-LEADLAG-FX) |

**Bottom line:** the binding constraint is an **edge after costs**, not mathematical sophistication. Better maths makes NEXA *more honest and cheaper*, not *profitable by itself*.

---

## 6. Best next steps for NEXA (ranked; each needs approval + pre-registration; no new spending)

| Rank | Candidate | Why | Data | Venue |
|---|---|---|---|---|
| **1** | **Intraday momentum:** the first half-hour return predicts the last half-hour (Gao, Han, Li & Zhou 2018; Baltussen et al. 2021 JFE, 60+ futures **including currencies**, 1974–2020) | The only **peer-reviewed, cross-asset** effect in the whole programme. **Never tested in NEXA.** One trade per day, so turnover and cost per trade are low | Pepperstone M1 on hand (EUR, GBP, JPY, XAU, 2017–2026). Index CFDs would need an MT5 export (user approval) | **MT5-native** |
| 2 | **Sneaky pivot** (CL-138) | Fully specified price-action rule; cheap to test | Pepperstone M1 on hand | **MT5-native** |
| 3 | **Kramer order-flow rules** (CL-137) as a **new** pre-registered hypothesis (not an OFC1 re-tune) | The most complete public order-flow rule set, with a hard daily loss stop | **CME 6E already owned** (Oct 2022 → Sep 2026, 45 months); no purchase | Research only (CME); live would need §3 |
| 4 | **Fabio value-migration model** (CL-135), proxy version | New, simple, testable on per-candle VA from true volume | 6E owned | Research only |
| — | **V2** | Stays frozen; its prospective out-of-sample begins 2027-01-04 | — | — |

**Not recommended:**
- buying more order-flow data;
- quantum tools;
- building multi-venue infrastructure before any strategy passes;
- variants of OFC1 chosen from its results.
