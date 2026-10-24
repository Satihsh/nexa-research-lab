# NEXA Order-Flow Trading Methodology: Master Document

**Version:** v0, 2026-10-11 (research programme batch 1 complete; batch 7, Fabio Valentini's primary videos, pending the transcript guard).

**Status:** research synthesis only. Nothing implemented, nothing purchased, production/MT5/risk unchanged.

**Persistent backing:** `kb/` (SOURCES, CLAIMS CL-001…098, CONCEPTS, GAPS, RESEARCH_PROGRAM, `research_program/B1…B5`), `ORIGINAL_METHOD_SPEC.md` (concept cards K1–K10), `CORE_STRATEGY_SPEC.md` (your notes' setups).

## Evidence classes used throughout

| Class | Meaning |
|---|---|
| **DEF** | Verified technical definition (platform docs, textbooks) |
| **LIT** | Published academic finding (peer-reviewed or established working paper) |
| **PRAC** | Practitioner explanation (books, courses, videos) |
| **LIVE** | Demonstrated live-trading example (n small, selected) |
| **PERF** | Independently verified performance (only: Robbins contest standings) |
| **UNV** | Unverified claim or statistic |
| **NEXA** | NEXA's own pre-registered test result |
| **HYP** | Hypothesis |
| **PENDING-PRIMARY** | Waiting for a primary source (video transcript) |

---

## 1. Bottom line of the research so far

1. **The definitions are solid; the edges are unproven.** Volume profile, value area, LVN, footprint, delta, imbalance, big trades and absorption are precise display constructs (DEF).
   - **No peer-reviewed or independently replicated study shows that trading them is profitable.**
   - Every published "win rate" (70–80 % stacked imbalances, the "80 % rule", "70–80 % daily bias") lacks a method (CL-096/097; B1).
2. **The academic literature explains why order flow *looks* predictive.**
   - It moves with price *contemporaneously* (Cont-Kukanov-Stoikov; Kozhan-Moore-Payne).
   - Trade signs persist, but prices stay near-unpredictable (Lillo-Farmer).
   - Informed traders prefer **medium** sizes, not big prints (Barclay-Warner).
   - So order flow is a **confirmation of what is happening now**, which is exactly how professionals use it: last, for timing.
3. **The base rate is brutal.** About 97 % of persistent discretionary futures day traders lose (Brazil mini-index, Chague et al.; Taiwan, Barber et al.).
4. **The one independently verifiable success in this exact methodology is contest-level.** Fabio Valentini (DeepCharts co-founder) has four Robbins quarterly futures-day-trading podiums (68.6–218.3 %; PERF). That proves real-money performance on those accounts, not a repeatable rule.
   - His published framework (market state → location → aggression) is the most complete process found.
   - It is known so far only from **secondary** write-ups; his own videos are queued.
5. **NEXA has already measured the main obstacle:** retail cost relative to a tight stop.
   - The C1 Tokyo-fix effect was real gross but not net.
   - ORB replications on index CFDs were the same: gross yes, net ≈ 0.
   - Order-flow scalps with stops "1–2 ticks beyond the aggressive print" are the **tightest-stop style there is**. Cost in R is the first feasibility question.
6. **The single most important missing input is CME trades with the aggressor side.** It is available (Databento, from USD 0.50/GB; a first window plausibly fits the USD 125 free credit; to be confirmed with the cost estimator). **Your approval is required.**

---

## 2. The 12 concepts: what is established

Details, sources and NEXA status per concept: `ORIGINAL_METHOD_SPEC.md` K1–K10.

| Concept | Verified definition (DEF) | What evidence exists | How professionals use it (PRAC) | Data | NEXA status |
|---|---|---|---|---|---|
| **Volume Profile** | Traded volume by price over a period; POC = max (DeepCharts, NinjaTrader, Dalton App. 1) | No controlled study of POC/VA levels in futures (search). General S/R: reactions yes, profits no (Osler 2000; S/R studies) | Context and levels first (all sources). **Profile period differs:** prior session (Dalton, Axia RTH), **impulse leg / reclaim leg** (Valentini), rotation cluster (Trader Dale) | Traded volume at price | Proxy validated XAU/EUR/JPY (T1) for **shape**. 6E, 13 months (CL-109): proxy VA edges are off by p50 ≈ 3–4 and p90 ≈ 17–19 pips vs the true CME profile. True CME data is on hand (Databento 6E 2025-09→2026-09) |
| **VAH / VAL** (value area) | Range around the POC holding 70 % (Dalton) / 68 % (Steidlmayer; NinjaTrader default) | Dalton's VA rule: "a good possibility", no statistic; "80 %" is folklore (CL-096). NEXA OF-16: open location vs VA has no predictive edge on FX/XAU | Balance edges; responsive trades back inside; acceptance outside = trend | As profile | Proxy ✓ |
| **LVN** | Thin area of the profile (DeepCharts "valleys"; NinjaTrader: between two HVNs) | **No controlled test** (CL-097) | **Contradictory roles:** pullback entry in a trend (Valentini A, Andrea Cimi); target traversed quickly (auction theory, NinjaTrader blog); support/"go up" (your note; CL-016) | As profile | Proxy (weaker) |
| **Order Flow** | Aggressive vs passive orders; delta = ask − bid aggressor volume (DeepCharts, Bookmap, NinjaTrader) | OFI explains price contemporaneously (LIT); trade-sign persistence (LIT); predictive tests at minutes+ are weak | Last step, for timing/confirmation (all) | Aggressor-flagged trades; book for absorption | **Needs data**; impossible on spot FX (CL-050) |
| **Big Trades** | Large aggressive orders as bubbles; side by colour; aggregation of split orders (DeepCharts, ATAS: algorithm undisclosed) | Medium, not large, trades carry informed impact (LIT). **CME large trades: sells → more temporary (liquidity) impact, buys → more permanent; flips with bull/bear state** (Frino et al. 2008, CL-099), **contradicted on the state direction by Frino et al. 2017** (CL-100) | Valentini: big prints **in the trade direction** at the location. Your notes: big **seller** prints that fail (absorbed/trapped). Trader Dale: ≥ 25 lots on 6E | CME trades with aggressor + size (+ MBO for Deep Trades) | **6E on hand** (Databento, 2025-09→2026-09). **Definition decided (E3):** top 1 % of aggressor orders per session block, prior 60 sessions (CL-111). 6J/6B/GC: data not bought |
| **Delta Profile** | Per-price ask−bid aggressor volume (3P; DeepCharts docs silent) | None (contemporaneous identity risk, S51) | Confirmation of who controls a level | Aggressor trades | Needs data |
| **Absorption** | Large passive orders absorbing aggression without price progress (Bookmap); "reloading" (Axia); no candle close beyond the cluster (Andrea Cimi). **≥ 4 competing definitions** | CME native icebergs are MBO-detectable (LIT, vendor-affiliated); detected icebergs attract market orders (WP) | Reversal confirmation at levels | MBO (true); trades (proxy) | Needs data; MBO prospective only |
| **Stacked imbalance** | Diagonal ask(p) vs bid(p−1) ratio; ratio 1.5 (NinjaTrader default) or 3:1 / 300 % (Trader Dale, LuxAlgo); stack ≥ 3. DeepCharts: undefined | **No controlled test** (CL-097) | S/R zone (Trader Dale); "super target" (Vishaal); aggression evidence (Valentini) | Per-price aggressor volume | Needs data |
| **ORB** | First-N-minute range break | Gross positive on equities (Zarattini et al., WP); **net ≈ 0 on 5 index CFDs** (independent replication); crude-oil ORB positive (Holmberg et al., abstract only) | Session-open momentum | OHLC | Reproducible (XAU overlaps V2-F2) |
| **IVB** | DeepCharts Deep-M IVB: proprietary ORB projection/protection/extension levels; secondary sources: ORB + volume confirmation | Unverified (one claimed "validation", PF 1.28, unknown author) | **Fabio "IVB Model 1 / Model 2" (video `cUTsoU-15Tc`): PENDING-PRIMARY** | Proprietary | Levels not reproducible |
| **GEX** | Γ·OI·mult·S²·0.01; regime boundary computed differently per vendor | Intraday momentum from gamma hedging, 60+ futures (Baltussen et al., LIT); GEX adds nothing beyond implied vol for SPY (vendor-published) | Context/targets (excluded from the core by you) | Options OI | Needs data |
| **Option Flow** | Signed option trades | Option volume predicts single stocks, not indices (Pan-Poteshman, LIT) | Context (excluded from the core) | Options trades | Needs data |

---

## 3. How the concepts fit together (documented relationships)

```
CONTEXT ─ Volume Profile → value area (VAH/VAL/POC) → state: BALANCE (inside, rotating) or IMBALANCE (displaced)
   │          (session/period choice is itself a methodology difference; §5)
LOCATION ─ VA edges · POC · LVN (in the prior profile, the impulse leg or the reclaim leg) · OR high/low
   │
PRICE RESPONSE ─ reaches the location; fails to break / reclaims / breaks and holds (candle-close based)
   │
ORDER-FLOW CONFIRMATION ─ Big Trades · delta / delta profile · footprint (stacked) imbalance · absorption
   │      two opposite readings:  (a) AGGRESSION WITH the trade   (b) AGGRESSION AGAINST the trade, absorbed
DECISION ─ entry on confirmation; stop just beyond the order-flow event / level; target = POC or the opposite edge
RISK ─ 0.25–0.5 % per trade; stop the day after N losses (Valentini); NEXA frozen controls
EXECUTION ─ futures (CME) or spot CFD with levels transferred from futures (Trader Dale)

ORB → IVB: a separate session-open breakout family (your decision); volume confirmation after the break
GEX / Option flow: context and targets in other presenters' chains (excluded from your core)
```

---

## 4. Strongest complete strategies identified

All rules are as **sourced**. Gaps are marked. **None is tested; none has published trade-level statistics.**

### S1. Valentini Mean-Reversion Model (failed breakout → back to balance)
**Sources:** WEB-002/003 (secondary); primary PENDING (CH-004). **Evidence:** PERF (trader-level contest placings), no strategy statistics.

| # | Element | Rule |
|---|---|---|
| 1 | Context and session | Market in balance or consolidation; London session or compressed (summer) conditions preferred |
| 2 | Profile | Previous day's profile = the balance reference; a separate profile of the **reclaim leg** |
| 3 | Levels | Balance edges (failed extreme), the reclaim-leg LVN, the balance POC |
| 4 | Order flow | Aggression in the snap-back direction (big buy prints after a downside failure) |
| 5 | Confirmation | Price must first **reclaim** inside balance; do not take the first move back; wait for the pullback |
| 6 | Entry | On the pullback into the reclaim-leg LVN with aggression |
| 7 | Stop / target | Stop beyond the aggressive print + 1–2 ticks (or beyond the failed extreme; sources differ); target = **balance POC** |
| 8 | LVN behaviour | LVN = pullback entry zone inside the reclaim leg |
| 9 | ORB/IVB | Unrelated |
| 10 | GEX/option flow | Not used |
| 11 | Risk | 0.25–0.5 % per trade; stop after 3 losses in a day; never widen the stop |
| 12 | Avoid | Choppy/compressed days produce more failed trades (also a stated weakness); entries without aggression |

### S2. Valentini Trend Model (out of balance → new balance)
Same sources and evidence as S1.

| # | Element | Rule |
|---|---|---|
| 1 | Context | Displacement away from prior value; **New York session**; avoid the London open (fake breakouts) |
| 2 | Profile | Profile of the **impulse leg** (start of impulse → extreme) |
| 3 | Levels | LVNs inside the impulse leg; the previous balance POC |
| 4 | Order flow | Aggression **in the trend direction** at the LVN (big bubbles / footprint imbalance / CVD) |
| 5 | Confirmation | Pullback reaches the LVN; alerts, not blind limits |
| 6 | Entry | At the LVN on aggression |
| 7 | Stop / target | Beyond the aggressive print + 1–2 ticks beyond the swing (one source: below the LVN); break-even early if CVD is strong; target = previous balance POC (trail only on strong trend days) |
| 8 | LVN | Continuation entry (price expected to *hold* the LVN in trend direction) |
| 11 | Risk | As S1 |
| 12 | Avoid | Rotation without displacement; London open |

### S3. "Big trade for sellers" absorbed at VAL (your notes / Vishaal Fx) and its break variant
Sources: NOTE-001, YT-001. Evidence: LIVE (1 trade). Full rule table in `CORE_STRATEGY_SPEC.md` (Setup A/B; E1–E12 open).

**Academic link (new):** large CME *sell* trades have a larger temporary (liquidity) impact than buys on average (Frino et al. 2008), a published mechanism for a rebound after big selling. The effect is condition-dependent, and two papers disagree on the direction (CL-099/100).

**Key differences from S1:**
- the trigger is **seller aggression that fails** (absorption/trapped sellers), not buyer aggression;
- the target is **VAH**, not the POC;
- the location is the prior-session VAL, not a reclaim-leg LVN;
- Setup B treats the LVN below VAL as a **target**, not an entry.

### S4. Dalton Value-Area Rule
Source: S42 (primary book). Evidence: none (UNV "80 %").

| Element | Rule |
|---|---|
| Context | Open outside the prior day's value area |
| Trigger | Re-entry into value with acceptance: two consecutive 30-min TPO periods ("double TPO prints") |
| Target | Traverse to the opposite VA edge |
| Stop | Not specified in the book (practitioners: back outside value) |
| Conditions | Better when the open is close to value and the VA is narrow |
| Order flow | None (pit era) |

### S5. Trader Dale volume-cluster setups with order-flow confirmation
Source: S44/S49 (primary books). Evidence: none (hypothetical trades).

| Element | Rule |
|---|---|
| Location | A volume cluster / accumulation POC from a rotation, or a volume-profile S/R zone |
| Confirmation | Order flow at the zone: absorption by limit orders, or aggressive orders with delta in the trade direction; imbalance 300 %, stacked ≥ 3; big trades ≥ 25 lots on 6E |
| Execution | **Analyse CME currency futures, execute spot FX**, levels transferred (inverse quotes for JPY/CHF/CAD) |
| Note | First touch "with no confirmation" in the volume-accumulation setup (S49) vs confirmation required in S44: two variants |

### S6. Axia "behind the elephant" (break-and-reclaim of a large resting order) and relative-IB breaks
Source: YT-006/011–014 (primary videos, partial). Evidence: none. **NEXA OF-19 rejected the relative-IB rule on spot FX/XAU.**

### S7. ORB → IVB (separate family)
- **Sources:** Zarattini et al. (equities); DeepCharts Deep-M IVB (proprietary levels); **Fabio "IVB Model 1/2" (PENDING-PRIMARY)**.
- **Evidence:** gross-positive equity ORB, net-zero CFD replication.
- **A crude-oil ORB working paper is positive** (abstract only).

---

## 5. Contradiction map (do not merge these)

| Topic | Alternative A | Alternative B | Alternative C | Resolution path |
|---|---|---|---|---|
| **Order-flow trigger direction** | Aggression **with** the trade at the level (Valentini; Trader Dale "aggressive orders"; DeepCharts blog CL-030) | Aggression **against** the trade that fails / is absorbed, then reclaim (your notes; Axia "behind the elephant"; Andrea Cimi CL-024; Trader Dale "limit absorption"; Faiz "inversion") | — | Treat as **two separate strategies**; test both with the same data |
| **Target from a VA-edge long** | POC (Valentini MR; Flow Zone first target) | Opposite VA edge = VAH (your notes; Dalton VA rule) | — | Separate cells; the driftless barrier law makes POC hits more frequent by geometry |
| **LVN role** | Pullback entry that holds (Valentini trend; Andrea demand zone) | Fast-traverse target (auction theory; your Setup B) | Support where price "will go up" (your note; CL-016) | Descriptive base-rate study first (OF-05 H-A vs H-B) |
| **Which profile** | Prior session/day (Dalton, Axia RTH, your notes inferred) | Impulse leg / reclaim leg (Valentini) | Rotation cluster (Trader Dale) | Part of each strategy's definition; not interchangeable |
| **Stop placement** | Beyond the aggressive print + 1–2 ticks (Valentini) | Beyond the level/LVN/failed extreme (secondary variants) | Below the bubble / around VAL (your notes) | Per strategy; **cost in R decides feasibility** |
| **Big-seller print: fade or follow?** | Fade: large sells are more temporary/liquidity-driven (CL-099 unconditional; your Setup A) | Follow: large sells are informed in bearish conditions (CL-099) or in bullish conditions (CL-100) | — | Condition on market state (balance vs trend, bull vs bear); test both with CME aggressor data |
| **Absorption definition** | Repeated reloading (Axia; MBO) | Large limit orders absorbing aggression (Bookmap) | No close beyond the cluster (Andrea Cimi) | Pick per strategy; MBO-based only prospectively |
| **Imbalance threshold** | 1.5 + min delta 10 (NinjaTrader) | 3:1 / 300 % (Trader Dale, LuxAlgo) | DeepCharts undefined | Your choice, or test both (counted) |

---

## 6. Data requirements and implementation feasibility

| Component | Faithful data | Available to NEXA | Cost (published) |
|---|---|---|---|
| Profile / VA / LVN | Traded volume at price | Proxy now (spot tick volume; XAU/EUR/JPY). True CME via Massive 1-min (2 y) or Databento | Included / per GB |
| **Big Trades, delta, footprint imbalance, stacked imbalance** | **CME trades with aggressor side** | **6E: 13 months on hand** (Databento `GLBX.MDP3` trades, bought 2026-10-11 from the free credit). 6J/6B/GC: none. Massive futures trades: aggressor field undocumented; current plan not entitled | Databento trades **USD 28/GB** (verified): ≈ USD 11.5/yr 6E, 9.4 6J, 5.1 6B, 36.5 GC; ≈ USD 112.6 free credit left |
| Absorption (true) / icebergs | MBO | Databento MBO from 2017 (historical, much larger volume); live Rithmic/dxFeed | Per GB (larger) |
| Live operation | Live CME feed | Databento live | from USD 32.65/month (non-pro) |
| Execution realism | Fills | S14 forward test (0 fills; MT5 down) | — |

**Execution venue question (project decision):**
- **(a) Trade CME futures directly.** NEXA is built on Pepperstone MT5; this would be a new broker/venue.
- **(b) Generate signals on CME data and execute spot/CFD at Pepperstone** (Trader Dale's approach). This needs a basis/level transfer; the T1 basis map passed for EUR/GBP/JPY and failed for XAU. **6E, 13 months (CL-108):** the basis is stable within a session (p95 0.6 pip). With yesterday's basis the error is p95 2.2 pips, which is fine at the zone scale and too coarse for tick-precise stops without a live futures price (GAP-M04).
- **Cost in R** under (b): a stop of 1–2 ticks beyond the print on 6E (tick = 0.5 pip) is often only 2–6 pips. NEXA's commission of ≈ 0.6–0.7 pip/round trip is then **10–35 % of R** before spread.

---

## 7. Questions research cannot settle (need your decision or new data)

1. **Which strategy family is "yours":** S3 (absorbed seller aggression → VAH) vs S1/S2 (Valentini, aggression with the trade → POC)?
   - They are different strategies.
   - Research can test both but cannot choose your intent.
2. **Venue:** CME futures vs spot CFD with transferred levels.
3. **Data approval:** Databento account plus the cost-estimator run (no spend without approval); window length.
4. **Thresholds no source fixes** (big-trade size per instrument, "near" tolerances, imbalance ratio). These either become your choices or counted test cells.
5. **Live-trading discretion:** Valentini's results include discretion (reading "strong" CVD, choosing days) that rules may not capture. A rule-based test can only falsify the rule version.

---

## 8. Prioritised plan (validation before implementation)

| Step | What | Data | Approval needed |
|---|---|---|---|
| **P0** | Finish primary-source decoding: Fabio channel (IVB models, signature model, risk protocol, entry zones, competition trades); remaining queue | Transcripts via the guard (free) | No |
| **P1** | Run the Databento cost estimator for CME trades (6E, 6J, 6B, GC; and NQ/ES as the native market of S1/S2) over 2 y and 7 y windows | — | **Yes** (account; no spend) |
| **P2** | Acquire the approved window of CME trades with the aggressor side | Databento | **Yes** (credits/spend) |
| **P3** | Build *research-only* measurement tools: aggregated big trades (by aggressor, same price/time window), footprint delta/imbalance, session and leg profiles, LVN detector. Parity with a platform screenshot set | P2 | No (research code) |
| **P4** | **Descriptive base rates first:** LVN traverse vs hold (OF-05); VA-edge reactions with and without big trades of each side; Dalton VA rule completion; with placebo levels and the driftless barrier law | P2–P3 | Pre-registration (your go-ahead) |
| **P5** | Pre-registered strategy tests of S1, S2, S3 (both trigger readings) on CME futures and in R net of costs. Instruments: the native market (NQ/ES) and NEXA's (6E/6J/GC) | P2–P4 | Your go-ahead per test |
| **P6** | Only for a strategy that passes out of sample: cost/venue design, Risk Engine review, demo forward test with real fills | live feed | **Yes** (separate approvals) |

**What NEXA can do today without approvals:** P0, plus proxy descriptive studies on spot tick-volume profiles (labelled `OF-03P`; never reported as Big Trades).


## Update 2026-10-11: first pre-registered test of the core method (OFC1)

**Result:** INSUFFICIENT-N (130 trades, minimum 150), with **every split negative**.
- Pooled −0.21 R/trade net on CME prices.
- Worse than random-timing entries with the same stops and targets.
- DSR 0.00.

**What it tested:**
- The user's fully specified core rules (E1–E12, E5b; `CORE_STRATEGY_SPEC.md`) on true aggressor data, 6E/6J/6B/GC, Dec 2025 → Sep 2026.
- Report: `../validation/OFC1_REPORT.md`; claim CL-116.

**Findings:**
- Order-flow confirmation reduced losses by +0.16 R vs the same levels without it (not significant).
- Setup B and its mirror almost never trigger under the chosen LVN rule.

**Status of the method in NEXA:** no evidence of an edge in its rule form.
- **Not:** re-tuning on these data.
- **Open:** a frozen-rule replication on unseen earlier history (purchase approval needed).

## Update 2026-10-11: final replication (OFC1R). The line is closed

**Verdict:** REJECTED. The frozen OFC1 rules on **unseen** 6E data, 2023-01 → 2025-08:
- 211 trades, −0.12 R/trade net;
- every calendar year negative;
- no better than random timing;
- DSR 0.0007.

**Together with OFC1:** the rule form of the core method has been tested in two independent periods and lost in both.

**Status:** the user closed the line (no further spending or variants). Report: `../validation/OFC1R_REPORT.md` (CL-117).
