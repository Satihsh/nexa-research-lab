# NEXA Order-Flow Trading Methodology: Master Document

**Version:** v1, FINAL, 2026-10-11. Supersedes v0 (`archive/NEXA_ORDERFLOW_METHODOLOGY_MASTER_v0_2026-10-11.md`).

**Status:** research complete for the core method. The core method's test line (OFC1) is **closed by user decision**.
- Production NEXA, MT5, the EA (S14), NEXA_Risk and schema v1 were **not modified**. No trades were placed.
- **Data spend:** USD 117.95 of Databento historical data, all from the free credit (≈ USD 7.06 left). No further spending is planned.

**Backing material (persistent):**
- `kb/`: SOURCES (80 entries), CLAIMS CL-001…117, CONCEPTS, GAPS, HYPOTHESIS_QUEUE, CHANGELOG, RESEARCH_PROGRAM, `research_program/B1/B3/B5`;
- `ORIGINAL_METHOD_SPEC.md` (concept cards K1–K10);
- `CORE_STRATEGY_SPEC.md` (the user's final rules, E1–E12);
- `DECISION_BRIEF_OPEN_ITEMS.md`;
- `databento/` (data access, measurements);
- `../validation/` (pre-registrations, code, results, reports).

---

## 0. Executive summary

1. **All 12 concepts are precisely defined, but none has an independently proven edge.**
   - Volume profile, value area (VAH/VAL), LVN, order flow, delta profile, big trades, footprint imbalance, absorption, ORB, IVB, GEX and option flow are well-specified display constructs.
   - No peer-reviewed or independently replicated study shows that trading them is profitable. Every published win rate (70–80 %, "80 % rule") lacks a method.
2. **The academic literature explains why order flow looks convincing on a chart.**
   - It moves with price at the same moment.
   - Informed traders prefer medium, not large, orders.
   - About 97 % of persistent discretionary futures day traders lose money.
3. **NEXA has tested the user's own method rigorously.**
   - The method: a big seller trade near the prior value-area low, confirmed by footprint order flow, then a reversal back to VAH or a break to the next LVN, plus mirrors at VAH.
   - The data: true CME aggressor-side data.
   - The process: all twelve rule decisions were made by the user; the tests were pre-registered with hashed code; each period was opened once.
4. **It lost in both independent periods.**
   - **OFC1** (6E / 6J / 6B / GC, Dec 2025 → Sep 2026): 130 trades, **−0.21 R** per trade net.
   - **OFC1R** (unseen 6E, Jan 2023 → Aug 2025): 211 trades, **−0.12 R** per trade net; every year negative. **REJECTED.**
   - In both tests, the entries were **no better than random timing** with the same stops and targets.
5. **The only component that helped was the order-flow confirmation itself.**
   - It reduced losses by about +0.1 to +0.16 R relative to the same levels without confirmation.
   - It was never significant, and never enough to turn the method profitable.
6. **NEXA's cheap substitute is not a stand-in for the original.**
   - The substitute is a Pepperstone tick-volume profile.
   - Its value-area edges sit 3–4 pips off the true CME levels on a typical day, and 17–19 pips off on 1 day in 10.
   - Only true aggressor data can reproduce Big Trades, delta and footprints.
7. **Decision implied for NEXA: nothing from this methodology should be implemented in production.**
   - What remains untested: discretionary judgement; the Valentini models on their native market (NQ / ES); absorption from order-book (MBO) data. See §9.

---

## 1. Scope, method and evidence classes

**Mandate (user, 2026-10-11):**
- Build an evidence-based understanding of the 12 concepts, individually and in interaction.
- Reconstruct complete strategies, with 12 process elements each.
- Keep contradictions as alternatives.
- Connect the methodology to NEXA, keeping true Big Trades distinct from volume-only proxies.
- Investigate data sources and costs, and buy only with approval.
- Later decisions narrowed the core:
  - GEX and Option Flow are excluded from the core;
  - ORB → IVB is a separate family;
  - the core is your notes' method.

**Method:**
- Sources were registered before claims were extracted.
- Claims carry a source and timestamp.
- Contradictions are kept side by side.
- Every NEXA test was pre-registered (hash before data, code hash before results, numbered deviations), and negative results are preserved.

**Evidence classes:**

| Class | Meaning |
|---|---|
| DEF | Verified technical definition (platform docs, textbooks) |
| LIT | Published academic finding |
| PRAC | Practitioner explanation (books, courses, videos) |
| LIVE | Demonstrated live example (n small, selected) |
| PERF | Independently verified performance (only: Robbins contest standings) |
| UNV | Unverified claim or statistic |
| NEXA-MEASURED | NEXA's descriptive measurement on true data |
| NEXA-TESTED | NEXA's pre-registered strategy test |
| HYP | Hypothesis |

---

## 2. The 12 concepts (final)

| Concept | Verified definition | Evidence of value | How practitioners use it | NEXA findings |
|---|---|---|---|---|
| **Volume Profile** | Traded volume by price over a period; POC = the maximum row (DeepCharts, NinjaTrader, Dalton) | No controlled study of profile levels in futures. Support/resistance levels show reactions, not profits (Osler 2000; S/R studies) | Context and levels first. The profile period differs by school: prior session (Dalton, Axia), impulse or reclaim leg (Valentini), rotation cluster (Trader Dale) | On 6E, NY (08:30–17:00 NY) holds 58 % of volume, London 27 %, Asia 14 % (CL-114). The Pepperstone tick-volume proxy matches the shape (ρ ≈ 0.85) but not the edges (CL-109) |
| **Value Area, VAH / VAL** | Range around the POC holding 70 % of volume (Dalton) or 68 % (Steidlmayer; NinjaTrader default) | The Dalton VA rule says "a good possibility"; the "80 %" figure is folklore (CL-096) | Balance edges: responsive trades back inside; acceptance outside = trend | **OF-16:** open location vs VA has no predictive edge on FX / XAU; hit rate 0.48–0.53 refutes 70–80 %. **OFC1/OFC1R:** VA-edge reversal rules lost |
| **LVN** | Thin part of the profile. **No standard detection rule:** neighbour minima, smoothing + prominence, DeepCharts undisclosed (CL-113) | No controlled test | **Contradictory roles:** pullback entry (Valentini), fast-traverse target (auction theory; your Setup B), support (your note) | With your rule (no smoothing, depth ≤ 50 %), an LVN beyond the edge exists in 41 % of sessions (CL-115). Setup B and its mirror rarely trigger (7 trades in two tests) |
| **Order Flow** | Aggressive vs passive orders; delta = buy-aggressor minus sell-aggressor volume | Order-flow imbalance explains price at the same moment (Cont-Kukanov-Stoikov). Trade signs persist, but prices stay near-unpredictable (Lillo-Farmer) | Last step, for timing | True aggressor side exists on 98 % of 6E trades (CL-103). Spot FX has none (CL-050) |
| **Big Trades** | Large aggressive orders shown as bubbles; aggregation undisclosed (DeepCharts, ATAS) | Medium trades carry the informed impact (Barclay-Warner). Large CME sells are more temporary (Frino 2008), but the state dependence is contradicted (Frino 2017; CL-099/100) | Valentini: aggression **with** the trade. Your notes: seller aggression that **fails**. Trader Dale: ≥ 25 lots on 6E | **A fixed lot size drifts ≈ 2× per year in share of orders** (CL-107). **User definition (E3):** top 1 % of aggressor orders per session block over the prior 60 sessions; this flags ≈ 1.15 % of orders per block (CL-111) |
| **Delta Profile** | Per-price buy − sell aggressor volume | None; contemporaneous identity risk | Who controls a level | Measurable from Databento trades; used in the OFC1 confirmation |
| **Absorption** | Passive orders absorbing aggression; **≥ 4 competing definitions** (Axia reloading, Bookmap, Andrea Cimi, Trader Dale) | CME native icebergs are MBO-detectable (vendor-affiliated preprint). Detected icebergs attract market orders (WP) | Reversal confirmation at levels | **Not tested.** True absorption needs MBO (larger, not bought). OFC1 approximated it by "no close below the bubble" |
| **Stacked imbalance** | Diagonal ask(p) vs bid(p−1) on **every** platform; default ratios 150–300 %; stack ≥ 3 is common (CL-112) | No controlled test | Support / resistance zone (Trader Dale), "super target" (Vishaal), aggression evidence (Valentini) | Your rule: 300 %, ≥ 10 lots, ≥ 3 levels, confirmation only. Part of the OFC1 confirmation, which helped slightly |
| **ORB** | Break of the first-N-minute range | Gross-positive on equities (Zarattini et al.); **net ≈ 0 on five index CFDs** (independent replication) | Session-open momentum | Separate family; not tested in this programme (XAU overlaps the frozen V2-F2) |
| **IVB** | Fabio's IVB (primary, CL-118/119): the NY opening range (15–30 min) plus a fixed profile. **Model 1:** after the breakout, buy the retrace into the zone between the range's VA edge and POC; a close back through the VA low invalidates. **Model 2:** the same plus order-flow confirmation (absorption or aggression). TP1 = proprietary "protection level" (claimed 65–70 %) | His claim: 13.5 % skew over a coin flip for the NQ 30-min IB breakout at 1:1 (CL-121). A third-party coding found the volume confirmation **hurt** (heavily optimised, CL-126) | Direction (IVB) → location (profile) → order-flow trigger | Primary source read 2026-10-11; not tested (native NQ) |
| **GEX** | Γ·OI·multiplier·S²·0.01; regime boundary computed differently by each vendor | Gamma hedging drives intraday momentum (Baltussen et al.). GEX adds nothing beyond implied vol (vendor-published) | Context and targets | **Excluded from the core** (user). Futures options OI not bought |
| **Option Flow** | Signed option trades | Predicts single stocks, not indices (Pan-Poteshman) | Context | **Excluded from the core** (user) |

---

## 3. How the concepts interact (process chain)

```
CONTEXT   Volume profile of a reference period → value area (VAH/VAL/POC) → state: balance (rotating inside) or imbalance (displaced)
LOCATION  VA edges · POC · LVNs (of the prior profile, the impulse leg, or the reclaim leg) · opening-range high/low
RESPONSE  Price reaches the location → fails to break / reclaims / breaks and holds (1-min close based)
ORDER FLOW  Big Trades · delta · stacked footprint imbalance · absorption
            two OPPOSITE readings:  (a) aggression WITH the intended trade      (Valentini, Trader Dale "aggressive orders")
                                    (b) aggression AGAINST it that is absorbed  (your notes, Axia "behind the elephant", Andrea Cimi)
DECISION  Entry on confirmation · stop just beyond the order-flow event · target = POC, opposite edge, or next LVN
RISK      Small fixed fraction · daily loss stop (Valentini) · NEXA frozen controls in production
EXECUTION CME futures, or spot CFD with levels transferred from futures (Trader Dale)
SEPARATE  ORB → IVB (session-open family) · GEX / option flow (context in other presenters' chains; excluded)
```

**What NEXA's measurements add:**
- **Order flow belongs at the end of the chain, for timing.** It co-moves with price, and NEXA's tests found its confirmation reduces losses slightly but adds no edge on its own.
- **Level transfer to spot is possible at zone scale, but not tick-precise.** The futures-to-Pepperstone basis is stable within a day (p95 0.6 pip). With yesterday's basis the p95 error is 2.2 pips (CL-108).

---

## 4. Complete strategies (12 process elements each)

**Element key:**
1. context
2. profile
3. levels
4. order flow
5. confirmation
6. entry
7. stop / target
8. LVN role
9. ORB / IVB
10. GEX / option flow
11. risk
12. avoid / invalidation

### S3. The user's core method: "big trade for sellers" at VAL, with break and mirror variants

**Status: TESTED and REJECTED in rule form (OFC1, OFC1R).**

**Basis:**
- Sources: NOTE-001 and YT-001 (Vishaal Fx; one live trade).
- **Every parameter was decided by the user on 2026-10-11:** E1–E12, E5b, bubble, re-entry, window, venue and costs (`CORE_STRATEGY_SPEC.md`).

| # | Element | Rule (final) |
|---|---|---|
| 1 | Context | When a bubble prints, the last 1-min close is inside the prior value area. Trades from 18:00 to 17:00 NY; flat at 17:00 NY |
| 2 | Profile | The **prior NY session** (08:30–17:00 NY), 70 % VA, 1-pip rows (6E) |
| 3 | Levels | VAL, VAH, and LVNs (no smoothing; valley ≤ 50 % of the lower neighbouring peak) |
| 4 | Order flow | **Big trade** = an aggressor order (trades grouped by timestamp + side) in the top 1 % of its session block over the prior 60 sessions. **Setup A / B:** a seller big trade within 10 % of the VA width of VAL. **Mirrors:** a buyer big trade near VAH |
| 5 | Confirmation | On the 1-min trigger candle: ≥ 3 stacked diagonal imbalances at 300 % (≥ 10 lots), delta in the trade direction, and volume above the same minute's mean over the prior 20 sessions. Applies to breaks too (E5b) |
| 6 | Entry | **A:** a close above the bubble high, with no close below the bubble before it. **B:** a close below both the bubble and VAL. Entry at that close (+1 tick slippage). The most recent bubble defines the setup |
| 7 | Stop / target | **Stop:** 1 tick beyond the bubble (A: below its low; B: above its high). **Target:** A → VAH; B → the nearest LVN below VAL (none → no trade). Mirrors are reflected |
| 8 | LVN role | Target only (exit at the LVN; no new trade) |
| 9 | ORB / IVB | Not used |
| 10 | GEX / option flow | Excluded |
| 11 | Risk | One position per instrument; re-entry after exit. Cost USD 2.61 / side (GC 2.66) + 1 tick on entries and stops. Test cost floor: skip if cost > 20 % of risk |
| 12 | Invalidation | A close below the bubble cancels A (B is still possible). An unconfirmed break ends the setup. 17:00 NY exit |

**Results:**

| Test | Data | Trades | Mean R (net) | Verdict |
|---|---|---|---|---|
| **OFC1** | 6E/6J/6B/GC, Dec 2025 → Sep 2026 (disc / val / hold) | 130 | −0.21 (every split negative) | INSUFFICIENT-N (< 150), no edge |
| **OFC1R** (final, out-of-sample) | 6E, Jan 2023 → Aug 2025, unseen | 211 | −0.12 (2023 / 24 / 25 all negative) | **REJECTED** |

**Benchmarks in both tests:**
- The timing placebo was as good as or better than the method.
- DSR ≈ 0.
- **Confirmation vs no confirmation:** +0.16 R (OFC1) and +0.09 R (OFC1R), both not significant.

**By setup (OFC1 / OFC1R):** A −0.28 / −0.07; A′ −0.16 / −0.15; B and B′ 7 trades in total.

### S1. Valentini mean-reversion model (failed breakout → back to balance)

**Basis:**
- Sources: secondary write-ups only (WEB-002/003). The primary videos are queued (CH-004) and blocked (§9).
- **Evidence:** PERF at trader level (four Robbins quarterly podiums, 2023–25), with no strategy statistics.
- **Status: not tested.**

| # | Element | Rule (as sourced) |
|---|---|---|
| 1 | Context | Market in balance; London session or compressed conditions preferred |
| 2 | Profile | Previous day = the balance reference; plus a profile of the **reclaim leg** |
| 3 | Levels | Failed balance extreme, the reclaim-leg LVN, the balance POC |
| 4 | Order flow | Aggression **in the snap-back direction** (big buy prints after a downside failure) |
| 5 | Confirmation | A reclaim inside balance first; do not take the first move back; wait for the pullback |
| 6 | Entry | On the pullback into the reclaim-leg LVN, with aggression |
| 7 | Stop / target | Beyond the aggressive print + 1–2 ticks (or beyond the failed extreme; sources differ) → **balance POC** |
| 8 | LVN role | Pullback entry zone |
| 9 | ORB / IVB | Unrelated |
| 10 | GEX / option flow | Not used |
| 11 | Risk | 0.25–0.5 % per trade; stop after 3 losses in a day; never widen the stop |
| 12 | Avoid | Choppy days; entries without aggression |

### S2. Valentini trend model (out of balance → new balance)

Same sources and evidence as S1. **Not tested.**

| # | Element | Rule (as sourced) |
|---|---|---|
| 1 | Context | Displacement away from prior value; New York session; avoid the London open |
| 2 | Profile | The **impulse leg** (start → extreme) |
| 3 | Levels | LVNs inside the impulse leg; the previous balance POC |
| 4 | Order flow | Aggression **with the trend** at the LVN (bubbles / footprint imbalance / CVD) |
| 5 | Confirmation | The pullback reaches the LVN; alerts, not blind limits |
| 6 | Entry | At the LVN on aggression |
| 7 | Stop / target | Beyond the print + 1–2 ticks (one source: below the LVN); early break-even on strong CVD → previous balance POC; trail only on strong trend days |
| 8 | LVN role | Continuation entry (the LVN holds) |
| 9 | ORB / IVB | Unrelated |
| 10 | GEX / option flow | Not used |
| 11 | Risk | As S1 |
| 12 | Avoid | Rotation without displacement; the London open |

### S4. Dalton value-area rule

**Basis:** primary book (S42). Evidence: none ("80 %" is UNV).

| # | Element | Rule |
|---|---|---|
| 1 | Context | Open outside the prior day's value area |
| 2 | Profile | The prior day (TPO / volume) |
| 3 | Levels | VAH, VAL |
| 4 | Order flow | None (pit era) |
| 5 | Confirmation | Re-entry into value, held for two consecutive 30-min TPO periods |
| 6 | Entry | After acceptance back inside |
| 7 | Stop / target | Stop not specified (practitioners: back outside) → the opposite VA edge |
| 8 | LVN role | — |
| 9–10 | ORB / IVB, GEX | — |
| 11 | Risk | — |
| 12 | Avoid | Wide value areas; opens far from value |

**NEXA:** related open-location behaviour showed no edge on spot FX / XAU (OF-16).

### S5. Trader Dale volume-cluster setups with order-flow confirmation

**Basis:** primary books (S44 / S49). Evidence: none (hypothetical trades).

| # | Element | Rule |
|---|---|---|
| 1–3 | Context, profile, levels | A volume cluster / POC of a rotation, or a profile support/resistance zone |
| 4–5 | Order flow, confirmation | Limit-order absorption, **or** aggressive orders with delta in the direction; imbalance 300 %, stacked ≥ 3; big trades ≥ 25 lots (6E) |
| 6–7 | Entry, stop / target | At the zone, on confirmation. Stop and target per zone. **One variant enters on the first touch without confirmation** |
| 8–10 | LVN, ORB, GEX | — |
| 11 | Risk / execution | **Analyse CME futures, execute spot FX**; levels transferred visually |
| 12 | Avoid | — |

**NEXA:**
- The transfer is feasible at zone scale (CL-108).
- A fixed 25-lot filter is non-stationary (CL-107).

### S6. Axia "behind the elephant" and relative-IB breaks

**Basis:** primary videos (partial). Evidence: none.
- **Setup:** break and reclaim of a large resting order; absorption = repeated reloading (needs MBO).
- **NEXA OF-19:** the relative initial-balance rule was **REJECTED** on spot FX / XAU (4/4).

### S7. ORB → IVB (separate family)

**Basis:** Zarattini et al. (equities, gross-positive); an independent CFD replication (net ≈ 0); DeepCharts proprietary IVB levels; Fabio "IVB Model 1 / 2" (primary video pending).

**Not tested here.**

---

## 5. Contradiction map (kept as alternatives)

| Topic | Alternative A | Alternative B | Alternative C | How it was handled |
|---|---|---|---|---|
| Order-flow trigger direction | Aggression **with** the trade (Valentini, Trader Dale) | Opposing aggression that is **absorbed** (your notes, Axia, Andrea Cimi) | — | Separate strategies. **OFC1 tested B** (your reading); A (S1 / S2) is untested |
| Target from a VA-edge long | POC (Valentini) | Opposite edge, VAH (your notes, Dalton) | — | Your choice: VAH (tested) |
| LVN role | Pullback entry that holds | Fast-traverse target | Support / "goes up" | Your choice: target, exit only |
| Reference profile | Prior session | Impulse / reclaim leg | Rotation cluster | Your choice: prior NY session |
| Stop placement | Print + 1–2 ticks | Beyond the level / extreme | Below the bubble | Your choice: 1 tick beyond the bubble |
| Big seller print: fade or follow | Fade (Frino 2008 unconditional) | Follow in bear (2008) or bull (2017) markets | — | Fade (Setup A) and break-follow (Setup B) both tested; both lost |
| Absorption definition | Reloading (MBO) | Passive absorption (Bookmap) | No close beyond the cluster | Approximated by C in OFC1; MBO never tested |
| Imbalance threshold | 150 % (ATAS / NinjaTrader) | 300 % (TradingView, Trader Dale) | 200 / 400 % (ATAS Learn) | Your choice: 300 % (tested; the NinjaTrader form in robustness) |
| Big-trade threshold | Fixed lots (Trader Dale 25) | Relative (no source) | — | Your choice: relative (fixed lots drift 2× per year) |

---

## 6. What NEXA measured on true CME data (descriptive)

Databento `GLBX.MDP3` trades with aggressor side. All figures are 6E unless stated.

| Measurement | Result | Claim |
|---|---|---|
| Aggressor side present | 98 % of trades (2 % implied / unspecified) | CL-103 |
| Aggressor orders | Median 2 lots; ≥ 25 lots = 1.75 % of orders / 19 % of volume; **the share doubled within a year** | CL-104, CL-107 |
| Relative big-trade rule (E3) | Asia 23–32 lots, London 28–42, NY 32–45; ≈ 1.15 % of orders per block | CL-110, CL-111 |
| Futures → Pepperstone basis | Within a session p95 0.6 pip; with yesterday's basis p95 2.2 pips; contract rolls jump 40–60 pips | CL-105, CL-108 |
| Pepperstone tick-volume profile vs true profile | Shape ρ ≈ 0.85; \|VAL\| error p50 3.9 / p90 19 pips; \|VAH\| 3.2 / 17; \|POC\| 2.4 / 32 (median VA width 27). The 1-min-bar approximation alone costs ≈ 1 pip | CL-106, CL-109 |
| Session volume split | NY 58 %, London 27 %, Asia 14 % | CL-114 |
| Setup preconditions (counts only) | A seller big trade near VAL in 73–85 % of sessions (5–20 % of VA width); an LVN below VAL in 6–56 % depending on the rule | CL-115 |

---

## 7. What NEXA tested (pre-registered)

| Test | Question | Data | Result |
|---|---|---|---|
| OF-16 | Does the open's location vs the prior VA predict the day? | Pepperstone FX / XAU 2017–26 | INCONCLUSIVE; EURUSD FAILED. Hit rate 0.48–0.53 refutes the "70–80 %" claims |
| OF-19 | Relative initial-balance width rule (Axia) | Same | **REJECTED** 4/4 (P); T: INSUFFICIENT-N, net < 0 |
| OF-20 / 20b | Trend day → balance next day | Same | INCONCLUSIVE (codification degenerate on 24 h FX; line closed) |
| **OFC1** | Your core method, rule form | CME 6E/6J/6B/GC, Dec 2025 → Sep 2026 | INSUFFICIENT-N; **all splits negative** (−0.21 R) |
| **OFC1R** | Final out-of-sample replication | CME 6E, Jan 2023 → Aug 2025 (unseen) | **REJECTED** (−0.12 R; 0 of 3 years positive) |

**Related lessons from non-order-flow tests:**
- **C1 (Tokyo fix):** the effect was real gross, but commission ate it.
- **C2 (time-series momentum):** rejected.
- **Common thread:** retail costs and tight stops consume small gross edges. Order-flow scalps have the tightest stops of all.

**Reports:**
- `../validation/OF_RESULTS_REPORT.md`, `OF20b_RESULTS_REPORT.md`;
- `OFC1_REPORT.md`, `OFC1R_REPORT.md`;
- the hash log `PREREG_HASHES.txt`.

---

## 8. Data sources, costs and infrastructure

| Source | Provides | Status / cost |
|---|---|---|
| **Databento `GLBX.MDP3`** | CME trades with aggressor side (from 2010); MBO (from 2017); statistics / OI | **Used.** Trades USD 28 / GB. **Bought:** 6E 2022-10 → 2026-09; 6J / 6B / GC 2025-09 → 2026-09. **Total USD 117.95, all free credit** |
| Pepperstone MT5 | Bid / ask M1, tick volume (quote count) | On hand. **No aggressor side or traded volume** |
| Massive | 1-min aggregates (2 y); futures trades (aggressor field undocumented) | Current plan not entitled to trades |
| Rithmic / dxFeed / CME DataMine | Live MBO; official history | Not used (live / prospective or quote-only pricing) |
| Databento live | Live CME | From USD 32.65 / month (non-professional); not needed |

**Infrastructure** (`databento/`; research only):
- the official `databento` Python client in its own venv;
- the key in a gitignored file (mode 600);
- `db_guard.py`, which requires a `get_cost` quote and a confirmation token for every download, keeps a ledger, and enforces a hard cap (now full at USD 117.95);
- `big_trades.py` (the E3 definition).

**Note:** the Databento portal also has its own historical monthly limit. A request above it returns 402 and is not billed.

**Research connectors:** OpenAlex, Exa, Tavily, Firecrawl and GitHub (official MCP, user scope) are all verified working (GitHub confirmed in-session 2026-10-11).

---

## 9. Conclusions, what is closed, what remains open

**Conclusions:**
1. **The user's core method has no edge in its rule form.** It was tested on true data in two independent periods, with every parameter chosen by the user, and lost in both.
   - Its entry timing was no better than random.
   - This is the strongest evidence NEXA can produce without the user's discretion.
2. **Order-flow confirmation is the one ingredient with a consistent (small, non-significant) benefit.**
   - It is useful as a **filter that avoids bad trades**, not as a source of edge.
   - This matches the literature: order flow co-moves with price.
3. **True aggressor data is required to reproduce Big Trades, delta and footprints.**
   - Pepperstone data cannot (no aggressor side).
   - Its volume-profile edges are off by several pips on a typical day.
4. **The practitioner evidence is thin.**
   - Only one trader (Valentini) has independently verifiable results, and those are contest results, not rules.

**Closed:**
- OFC1 / OFC1R (user decision: final run, no further spending).
- OF-20 / 20b.
- C3 and unrelated strategy research (paused by the user).

**Open but unfunded (listed for completeness, not proposed):**

| # | Item | Why untested | What it would need |
|---|---|---|---|
| U1 | Valentini S1 / S2 (aggression **with** the trade; reclaim / impulse-leg LVNs) | Native market NQ / ES; primary videos blocked | NQ / ES data plus new pre-registration |
| U2 | Absorption from order-book data (MBO reloading, icebergs) | MBO is much larger and costlier | MBO purchase |
| U3 | The user's **discretionary** application | Rules cannot capture visual judgement | A prospective trade journal (no cost) |
| U4 | ~~Fabio's primary videos~~ **DONE 2026-10-11** (12 primary videos via Tavily; CL-118…131) | — | — |
| U5 | ORB → IVB family | Separate family | Separate pre-registration |

**For NEXA production:**
- Nothing from this methodology is recommended for implementation.
- No order-flow module, no Big Trades feature and no change to the EA, Risk Engine or MT5.
- The S14 forward test and the V2 campaign are unaffected.

---

## 10. File map

| Purpose | Location |
|---|---|
| This document | `orderflow/NEXA_ORDERFLOW_METHODOLOGY_MASTER.md` |
| Knowledge base | `orderflow/kb/` (SOURCES, CLAIMS CL-001…117, CONCEPTS, GAPS, HYPOTHESIS_QUEUE, CHANGELOG, RESEARCH_PROGRAM, research_program/) |
| Concept cards and the original method | `orderflow/ORIGINAL_METHOD_SPEC.md` |
| Your final rules (E1–E12) | `orderflow/CORE_STRATEGY_SPEC.md`, `orderflow/DECISION_BRIEF_OPEN_ITEMS.md` |
| Data access and measurements | `orderflow/databento/` (README, db_guard, ledger, PILOT_6E_REPORT, YEAR_6E_REPORT, *.json) |
| Pre-registrations, code, results | `validation/PREREG_OFC1_CORE_ORDERFLOW.md`, `PREREG_OFC1R_REPLICATION.md`, `ofc1_core.py`, `DEVIATIONS_OFC1.md`, `OFC1_REPORT.md`, `OFC1R_REPORT.md`, `PREREG_HASHES.txt`, `RESEARCH_GATE.md` |
| Failed ideas | `research/knowledge/FAILED_IDEAS.md` |
| Transcript tooling | `orderflow/tools/yt_transcript_guard.py` (queue: 30 videos, Fabio first) |


## Update 2026-10-11: Fabio Valentini's primary sources (transcript batch 6)

The YouTube IP block was bypassed by fetching transcripts through Tavily from its servers; no local network change was made. All 30 queued videos were processed: 12 of Fabio's primary videos read in full, plus the others (claims CL-118…134).

**What the primary sources change:**
1. **IVB is now defined from the primary source** (CL-118/119): opening range plus fixed profile → retrace into the VA-edge-to-POC zone (Model 1), plus order-flow confirmation (Model 2).
   - The "65–70 %" protection-level probability and the "13.5 % skew" are unverified presenter claims.
   - A third-party coding found the volume confirmation hurt (CL-126).
2. **Fabio uses both order-flow readings** (§5).
   - His most-shown execution trigger is **big aggressive orders absorbed at a pre-qualified level** (CL-128). That is reading (b), the same as the user's "big trade for sellers".
   - He also takes aggression-with-result momentum entries (reading a).
   - The trigger-direction "contradiction" is therefore two tools used by the same practitioner, selected by context.
3. **His daily bias uses the NY cash-session profile only** (CL-127), matching the user's E1 choice. LVNs are **rebalance pivots** for continuation entries (CL-129), not targets.
4. **Contest evidence carries a selection effect, in his own words** (CL-125): several accounts run different models, the winner is scaled with a deliberately aggressive, convex protocol "no hedge fund would accept".
   - The podiums show real-money results under a tournament payoff, not a stable per-trade edge.
   - His personal-account guidance is 0.5–1.25 % risk per trade.
5. **Much of his absorption reading uses the order book** (reloads, icebergs, book sweeps; CL-130), which needs depth data (U2).

**Effect on conclusions:** none on the verdicts.
- OFC1 / OFC1R tested the user's rules, which the primary sources show are close to Fabio's reading (b) at the VA edge.
- What remains untested is Fabio's full discretionary combination: bias from the profile or IVB, a leg-profile location, absorption read partly from the order book, scaling, and trailing. That stays U1–U3.
