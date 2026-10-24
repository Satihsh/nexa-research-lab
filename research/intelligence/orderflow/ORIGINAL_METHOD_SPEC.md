# Your original order-flow method: complete reconstruction (v2, FOR YOUR APPROVAL)

**Date:** 2026-10-11. **v2** expands v1 (same day) to cover every concept you listed and how the concepts interact.

**Status: DRAFT FOR APPROVAL.** Nothing has been implemented or tested. Production NEXA, risk controls and MT5 are unchanged.

**Rules of this document:**
1. **No rule is invented.** Where your notes and the sources are silent, the element is **UNDEFINED → decision Dn**. Options are listed for you to choose from; they are not proposals.
2. **Concepts are not interchangeable.** Each has its own card. The links between them are stated only where a source states them.
3. **No profitability is claimed.** None of the setups has been tested.
4. **The original Big Trades strategy and any volume-only proxy are kept separate** (§5).

You listed "VAH", "VAL" and "Value Area High and Value Area Low". These are the same two levels, so they share one card (K3) with separate VAH and VAL rows.

## Evidence labels

| Label | Meaning | Location |
|---|---|---|
| **NOTE** | Your handwriting, quoted (spelling as written) | IMG_6395–6398; transcription in `NEXA_ORDERFLOW_FRAMEWORK_REPORT.md` §1 |
| **WB** | Vishaal Fx whiteboard (storyboard frames 320×180; detail unconfirmed) | `eLGVyu3utXE` 0:40–3:50 |
| **VERIFIED-DOC** | Official vendor documentation of what a tool *is* or *does* (not evidence of predictive value) | DeepCharts (DOC-001), NinjaTrader (DOC-005), Bookmap (DOC-002), MenthorQ (DOC-003), FlashAlpha (DOC-006) |
| **VERIFIED-LIT** | Peer-reviewed or corpus literature | `research/knowledge/`, KB SRC-LIT |
| **PRESENTER** | A claim made in a video, with KB claim ID and timestamp | `kb/CLAIMS.md` |
| **VENDOR-CLAIM** | Seller's performance/accuracy statement, unverified | `kb/CLAIMS.md` |
| **NEXA-RESULT** | NEXA's own pre-registered test | `validation/*_REPORT.md` |
| **HYPOTHESIS** | A testable statement NEXA derived (OF-xx) | `kb/HYPOTHESIS_QUEUE.md` |
| **INTERP** | My reading; never a rule | — |
| **UNRESOLVED** | Nobody defines it; it needs your decision or screenshots | — |

**Provenance finding:** your notes match the Vishaal Fx whiteboard (0:40–3:50) almost element for element, so they appear to be notes from that lesson.
- **Your notes contain:** the checklist, volume profile, VAH/VAL, big trades ("bubble"), LVN and ORB → IVB.
- **Your notes do not contain:** option flow, GEX, delta profile or stacked imbalances. Those come from the presenter's audio (delta profile, stacked imbalance) and from other DeepCharts/Bookmap/MenthorQ presenters (GEX, option flow).

---

# PART I: Concept cards

**Each card covers:**
- definition;
- role in the process (§3 stages: ① Context · ② Location · ③ Price response · ④ Order-flow confirmation · ⑤ Trade decision · ⑥ Risk checks · ⑦ Execution);
- setup conditions;
- entry/exit implications;
- required data;
- connections;
- NEXA status (REPRODUCIBLE / PROXY / NEEDS DATA / NOT REPRODUCIBLE / UNKNOWN);
- evidence;
- unresolved items.

## K1. Volume Profile

| Field | Content |
|---|---|
| **Definition** | VERIFIED-DOC: distribution of traded volume by price over a chosen period. DeepCharts "Volume By Price / Deep Profile Values" (POC = "the price level with the highest volume"; period Composite / Multiples / Visible / Personalized; session filter in U.S. time). NinjaTrader VP: POC = "the single largest data point"; minute resolution spreads each bar's volume evenly high→low (CL-071). VERIFIED-LIT: Market Profile / auction theory (S42, S46 in the corpus) |
| **In your notes** | Page 1: "Volume Profile ↓" diagram with VAH, VAL and a large bulge between them. Checklist title "market profile + Volume profile + Order flow" |
| **Role** | ① Context (balance vs imbalance) and ② Location (it produces VAH, VAL, POC, LVN) |
| **Setup conditions** | NOTE: price rotating inside the value of the profile ("ʌʌʌ"). PRESENTER (other): use RTH/cash-session profiles (CL-002, Axia); plan from the profile first, order flow last (CL-001) |
| **Entry/exit** | Not an entry signal by itself. It supplies the levels used by K3 and K4 |
| **Required data** | Traded volume at price per period. **TRUE** = exchange volume (CME futures). **PROXY** = broker tick volume (counts of quote changes, not traded volume) |
| **Connects to** | Produces **K3** (VAH/VAL) and **K4** (LVN). **K2** Delta Profile is the signed version. **K5** Big Trades are plotted on top of it |
| **NEXA status** | **PROXY: validated** for XAUUSD, EURUSD, USDJPY; **rejected for GBPUSD** (NEXA-RESULT T1: POC within 0.25σ on 67–75 % of days; failures on bimodal days). **TRUE** daily CME futures profiles cached 2024-10 → 2026-09 (2 y); CME 1-minute volume available via Massive (2 y rolling, not cached; collection needs approval) |
| **Evidence** | NEXA-RESULT OF-16: a value area from tick volume did no better than a range-based pseudo value area for predicting the day |
| **Unresolved** | D1 profile period/session; D2 VA % (shared with K3) |

## K2. Delta Profile

| Field | Content |
|---|---|
| **Definition** | **Not defined in DeepCharts' official help articles** (DOC study §1.5). Partner/3P descriptions: per-price accumulation of aggressive buy volume minus aggressive sell volume ("directional conviction at each level"). Delta itself is VERIFIED-DOC: "Difference between Ask and Bid" (DeepCharts Deep Print); NinjaTrader: trades at ≥ ask = buy, ≤ bid = sell, in-between = previous tick's side (CL-049) |
| **In your notes** | **No** |
| **Role** | ④ Order-flow confirmation (presenter usage) |
| **Setup conditions** | PRESENTER (YT-001 6:03 "Delta profile"; 6:50 "this trade is purely based on P and Delta and big confirmations"). INTERP: "P" = profile. **No condition is stated** |
| **Entry/exit** | UNRESOLVED: the presenter gives no rule. 3P reading (not a rule): strong positive delta at a level where price stalls = passive sellers absorbing |
| **Required data** | Exchange trades **with aggressor side**, aggregated by price |
| **Connects to** | Signed counterpart of **K1**; per-price view of **K6** order flow; the same raw data as **K5** Big Trades |
| **NEXA status** | **NEEDS DATA.** Spot FX/XAU has no traded "last", so bid/ask delta is impossible (VERIFIED-DOC NinjaTrader, CL-050). Any delta from Pepperstone quotes = quote pressure, not order flow (OF-26) |
| **Evidence** | None for predictive value. CL-026 (Axia): CVD divergence is "a warning, not a trade" |
| **Unresolved** | D25 whether the delta profile is part of your method at all; if yes, D27 what delta condition confirms an entry |

## K3. Value Area: VAH (Value Area High) and VAL (Value Area Low)

| Field | Content |
|---|---|
| **Definition** | VERIFIED-LIT/DOC: the price range around the POC holding a chosen share of volume. EQ-014 algorithm (S42): start at the POC, add the larger two-bin neighbour until α of volume is included. **VAH** = top edge, **VAL** = bottom edge. α: 70 % (DeepCharts example; NEXA pre-registered), 68 % (NinjaTrader default; S46) |
| **In your notes** | Page 1: VAH and VAL drawn, "The middle part where the market runs ʌʌʌ". Page 2: bubble near VAL. Page 3: "Stop loss → Below the bubble and also around VAL", "Take Profit → at VAH", "break the VAL" |
| **Role — VAH** | ② Location, and **⑤ target** in Setup A (NOTE: "Take Profit → at VAH") |
| **Role — VAL** | ② Location (where the bubble forms), **stop reference** in Setup A, and **break level** that triggers Setup B (NOTE) |
| **Setup conditions** | NOTE: price balancing between VAH and VAL. PRESENTER (other): VAH resistance / VAL support, rotate to POC/opposite edge (CL-006); do not fade edges blindly, wait for a reclaim (CL-007); HTF trend filter (CL-008); open location vs VA sets bias (CL-005) |
| **Entry/exit** | NOTE only: TP at VAH (long), SL around VAL, a VAL break flips to short. Everything else is presenter material (CL-006/007) |
| **Required data** | Same as K1 |
| **Connects to** | Derived from **K1**. **K5** bubbles are located relative to VAL. **K4** LVN lies below VAL (NOTE). **K9/K10** ORB/IVB are an independent level system (no source in your notes links them to VAH/VAL) |
| **NEXA status** | **PROXY: validated** (XAU/EUR/JPY; VA overlap with futures ≥ 0.70 median); **TRUE** 2 y futures |
| **Evidence** | NEXA-RESULT OF-16: open above VAH / below VAL did not predict direction (hit rate 0.48–0.53; the "70–80 %" claim was refuted for spot FX/XAU). **The VAL→VAH rotation (Setups A/B) is untested** |
| **Unresolved** | D1, D2, D3 (what "balancing" means), D4 ("near VAL") |

## K4. Low Volume Node (LVN)

| Field | Content |
|---|---|
| **Definition** | VERIFIED-DOC (closest): DeepCharts "Peaks and Valleys" ("highest and lowest volume traded"; sensitivity undocumented). The term "LVN" itself is not in DeepCharts' docs. VERIFIED-LIT: a thin area of the profile (S42/S46) |
| **In your notes** | Page 3: "at below got LVN", "LOW Volume NOTE [sic]", "Unfinish Auction", "Automatically market go down will reach LVN, once reach LVN, market will go up" |
| **Role** | ② Location and **⑤ target** in Setup B (NOTE) |
| **Setup conditions** | NOTE: an LVN below VAL, reached after a VAL break |
| **Entry/exit** | NOTE: exit the short at the LVN. "market will go up" = UNRESOLVED (D18: exit only, or also a new long?) |
| **Conflicting sources** | PRESENTER: LVN = fast traverse / rejection (CL-017); an LVN below VAL holds on a bullish day (CL-016); balance fills LVN "caves" (CL-010); prior VAH → nearest LVN = demand zone (CL-015, Andrea Cimi); an "empty profile" = regime change (CL-018). Your "unfinished auction" ≠ the Market Profile meaning (a poor high/low). **Sources disagree on whether an LVN attracts, repels or supports price** |
| **Required data** | Same as K1, plus a node-detection rule |
| **Connects to** | From **K1**. Below **K3** VAL. In Andrea Cimi's chain (§2) the VAH → LVN zone is where **K6/K5** absorption is sought |
| **NEXA status** | **PROXY** (LVN location is less reliable on tick volume than VA edges; T1 bimodality failures) |
| **Evidence** | **Untested** (OF-05 queued, competing hypotheses H-A traverse vs H-B reaction) |
| **Unresolved** | D5 LVN definition; D18 |

## K5. Big Trades (the core of your original setup)

| Field | Content |
|---|---|
| **Definition** | VERIFIED-DOC (DeepCharts): "visualize large, aggressive market orders in real time" as **bubbles**.<br>• **Ask colour = aggressive buyers; Bid colour = aggressive sellers.**<br>• Manual Min/Max size filter, or the automatic "Big Trades Analysis" (undocumented thresholds).<br>• Inputs: Volume (raw prints; a split order is missed), Aggregate (parent order inferred from the aggressor ID), Order (MBO).<br>• The **Deep Trades** variant uses MBO to show the passive orders hit; **historical MBO cannot be backfilled**. |
| **In your notes** | Page 2: "**BIG TRADES** … Wait until we get big trades !!! What is big trades ? — A particular point (a lot of transaction happened → it will represent like bubble. !!! When the market move above the bubble … we should buy !!!" Diagram label: "**Big trade for Sellers**" |
| **Role** | **④ Order-flow confirmation, and the anchor of entry and stop** in Setups A/B |
| **Setup conditions** | NOTE: a bubble near VAL at the end of a down-swing, labelled for sellers. INTERP: a **bid-coloured** (aggressive-seller) bubble. Two readings that predict the same "up" but fail differently: (a) sellers trapped below; (b) a passive buyer absorbing. **Indistinguishable without aggressor and book data** |
| **Entry/exit** | NOTE: buy when price moves above the bubble; SL below the bubble (and around VAL). Setup B: a break of the bubble **and** VAL → short |
| **Required data** | **Exchange trade prints with aggressor side and size** (CME GC/6E/6B/6J), ideally the aggressor-ID aggregation; MBO for the Deep Trades variant |
| **Connects to** | Located on **K1/K3** (near VAL). Same data as **K2** delta. Breakout-continuation reading with **K9** (CL-030: large buyers above resistance) |
| **NEXA status** | **NEEDS DATA.** Massive trades NOT_ENTITLED; Pepperstone quote-only. Candidate source: **DataBento `GLBX.MDP3` trades with aggressor side** (CL-079; purchase/credits need approval). MBO history does not exist anywhere (prospective only) |
| **Evidence** | None for the setup. VERIFIED-LIT caveat: large prints ≠ informed (Barclay & Warner 1993; split orders) |
| **Unresolved** | D7 bubble threshold/aggregation; D10 must it be seller-coloured; D6 "move above" |

## K6. Order Flow (umbrella concept)

| Field | Content |
|---|---|
| **Definition** | VERIFIED-DOC: aggressive buying = "large orders lift the ask"; aggressive selling = "large orders hit the bid" (DeepCharts blog); delta = ask − bid volume. VERIFIED-DOC (Bookmap glossary): aggressor vs passive orders, absorption = large limit orders absorbing aggressive volume (CL-053), sweeps, pulled liquidity, spoofing. Footprint/imbalance: NinjaTrader imbalance ratio 1.5, minimum delta 10; **no standard "stacked imbalance"** (CL-048/051) |
| **In your notes** | The checklist "④ What does order flow show ?"; Big Trades (K5) is the only order-flow tool you wrote down |
| **Role** | ④ confirmation. PRESENTER consensus: context and profile first, order flow last, for timing (CL-001, CL-025, K-11) |
| **Setup conditions** | PRESENTER only: absorption definitions conflict (CL-020 reloading; CL-022 candle position; CL-024 no close below a sellers' cluster; CL-053 Bookmap). Stacked imbalance as a "super target" (CL-029, YT-001) |
| **Entry/exit** | PRESENTER: entry after absorption plus a close beyond ("inversion", CL-023); CVD divergence = warning only (CL-026) |
| **Required data** | Aggressor-flagged trades; for absorption/icebergs, the order book (MBO/MBP) |
| **Connects to** | Contains **K5** and **K2**; confirms locations from **K3/K4**; confirms **K9** breakouts (CL-030) |
| **NEXA status** | **NEEDS DATA** (aggressor trades); **NOT REPRODUCIBLE on spot FX/XAU** (no central tape or book; CL-050, K-12). Unsigned effort-vs-result proxy only (OF-09) |
| **Evidence** | VERIFIED-LIT: order-flow imbalance predicts price only over seconds–minutes (Cont, Kukanov & Stoikov 2014). Practitioner claims are untested |
| **Unresolved** | D25 which order-flow confirmations (beyond big trades) are in your method |

## K7. Option Flow

| Field | Content |
|---|---|
| **Definition** | Traded options volume and premium, classified by side (customer buys vs sells), strike and expiry; "sweeps" and "blocks". VERIFIED-DOC (FlashAlpha flow-signed GEX, CL-076): trades classified against NBBO; dealer_pos = customer sells − customer buys. PRESENTER: Bookmap/SpotGamma "HIRO" = real-time hedging impact of options trades (CL-038, YT-003) |
| **In your notes** | **No** |
| **Role (presenter usage)** | ① Context (intraday dealer-hedging pressure) and ⑤ targets (option "walls") |
| **Setup conditions** | PRESENTER: positive-gamma days mean-revert; follow HIRO direction (CL-038; SPX/NDX only) |
| **Entry/exit** | PRESENTER: option walls as the final target (CL-044) |
| **Required data** | Options trades with side (OPRA for equities; **CME options-on-futures trades** for gold/FX: OG, EUU etc.) |
| **Connects to** | Feeds **K8** (flow-signed GEX); turns static GEX into an intraday signal |
| **NEXA status** | **NEEDS DATA** (none on hand; CME options trades possibly via DataBento, unverified, approval needed). All presenter examples are SPX/NDX |
| **Evidence** | None for XAU/FX. Vendor flow tools state no backtests (CL-081) |
| **Unresolved** | D28 whether option flow is part of your method |

## K8. Gamma Exposure (GEX)

| Field | Content |
|---|---|
| **Definition** | VERIFIED-DOC (FlashAlpha, CL-072): GEX per strike = Γ × OI × multiplier × S² × 0.01 (USD per 1 % move); calls +, puts − under the *assumption* that dealers are long calls and short puts; "the formula is exact; the positioning interpretation is a model". Gamma flip / zero gamma / HVL / volatility trigger = the regime boundary, **computed differently by each vendor** (CL-033, CL-060, CL-073). Call Resistance / Put Support = the max net call/put gamma strike (CL-061, CL-067) |
| **In your notes** | **No** |
| **Role (presenter usage)** | ① Context (regime: positive gamma = mean reversion/pinning; negative = expansion, CL-032) and ⑤ targets/walls (CL-034, CL-044) |
| **Setup conditions** | PRESENTER: a "no-trade cage" between two large positive-GEX strikes; trade only after the cage breaks, IVB-like (CL-034); include expiring "carry" in 0DTE GEX (CL-037, one example) |
| **Entry/exit** | PRESENTER: walls as targets; regime decides fade vs breakout. VENDOR-CLAIM: CL-035 "≈13 % skew" (unpublished) |
| **Required data** | Options OI by strike and expiry, plus IV/greeks, for the underlying. Gold/FX = CME options-on-futures (GC/OG, 6E/6B/6J) |
| **Connects to** | Context for **K3/K4** locations and **K9/K10** breakouts; targets alongside IVB levels (CL-044); built from **K7** if flow-signed |
| **NEXA status** | **NEEDS DATA** (GAP-D08: historical CME options OI by strike; paid; approval). MenthorQ claims GC and 6E/6B/6J levels, but they are EOD-only, the method is undisclosed, it contradicts its own GLD advice (CL-057/058/064), and there is no history, so they are **not testable** |
| **Evidence** | VERIFIED (vendor-published with method, CL-075): on 8 years of SPY, GEX tracks next-day volatility raw (ρ −0.36) but **adds nothing beyond VIX + ATM IV** (ρ −0.03, p 0.18); DEX no return signal. VERIFIED-LIT: index-level gamma effects (Baltussen et al. 2021; Ni-Pearson-Poteshman 2005). **No evidence for XAU/FX** |
| **Unresolved** | D29 whether GEX is part of your method; D30 its role (context filter vs target) |

## K9. ORB (Opening Range Breakout)

| Field | Content |
|---|---|
| **Definition** | VERIFIED-LIT: the high/low of the first N minutes after a session open; trade the break (Zarattini & Aziz, equities; KB LIT). PRESENTER (SMB, CL-040/042): the trigger is a candle **close** above the range; size from the stop |
| **In your notes** | Page 4: "ORB Open Range Breakout ↓ Initial Volume Breakout" |
| **Role** | ② Location (range high/low) → ③ response (the break) → ⑤ entry |
| **Setup conditions** | WB 3:00–3:50: oscillation inside the range, an upward break, "E" and "SL" marks (positions unconfirmed). DOC (Deep-M IVB): RTH opening range of 15/**30 (recommended)**/60 min |
| **Entry/exit** | UNRESOLVED (D21/D22/D23). CL-004 (Axia, IB analogue): exit fast if price returns inside |
| **Required data** | OHLC from a defined session open. FX/XAU need an anchor choice (no RTH) |
| **Connects to** | Refined by **K10** IVB. Volume confirmation via **K5/K6** (CL-030) or volume (RVOL). GEX cage (CL-034) as a filter |
| **NEXA status** | **REPRODUCIBLE** (M1 2017–2026). ⚠ On XAU it **overlaps the frozen V2 family F2** (XAU session breakout); a new test would contaminate V2 unless restricted or approved |
| **Evidence** | NEXA-RESULT OF-19: breaks of a small initial balance did **not** continue (rejected 4/4). 8E Donchian breakout contradicted. No ORB test with your rules yet |
| **Unresolved** | D19–D24 |

## K10. IVB (DeepCharts Deep-M IVB; proprietary)

| Field | Content |
|---|---|
| **Definition** | VERIFIED-DOC: "an algorithmic indicator … to simplify trading the Opening Range Breakout (ORB) structure"; "analyzes years of historical data"; plots **projection, protection and exit** levels: RTH OR High/Mid/Low, then **Protection** ("highest-probability target of the day"), **Ext. Avg**, **Ext. Std-1**, reaction **Zones**, and a Neutral/Positive/Negative bias panel. **The acronym is never expanded; there are no formulas, instruments or years.** VENDOR-CLAIM: "high-probability" (no statistics) |
| **In your notes** | Page 4 ("Initial Volume Breakout": your expansion; not confirmed by DeepCharts) |
| **Role** | ⑤ targets/exits after an ORB break (presenter usage: CL-044 "IVB protection level used as first target") |
| **Setup conditions** | PRESENTER: "OB or B open range breakout … world famous" (2:53), "initial volume" (3:03) |
| **Entry/exit** | Targets only (Protection → Ext. Avg → Ext. Std-1); partial exits "may be considered" at Zones (DOC) |
| **Required data** | DeepCharts' proprietary model |
| **Connects to** | Built on **K9**. Used with GEX walls as the final target (CL-044). "IVB-like" cage logic for GEX (CL-034) |
| **NEXA status** | **NOT REPRODUCIBLE.** NEXA can only pre-register **its own** ORB extension levels, which must never be called IVB |
| **Unresolved** | D23 (your own target definition) |

---

# PART II: How the concepts interact (only as sources state)

## 1. Your notes (NOTE): the only interactions you wrote down

```
Volume Profile ──► VAH / VAL (value) ──► price rotates inside value ("ʌʌʌ")      ① Context
                        │
                        ▼
          Big Trades bubble "for Sellers" near VAL                              ② Location + ④ Order flow
                        │
      ┌─────────────────┴──────────────────┐
      ▼                                    ▼
price moves ABOVE the bubble        price breaks the bubble AND VAL             ③ Price response
      │                                    │
 LONG: SL below bubble/~VAL,        SHORT: SL "at the top",                      ⑤ Trade decision
       TP at VAH                           TP below VAL at the LVN
                                           ("market will go up" at the LVN: D18)

ORB ──► IVB   (separate page; no stated link to VAH/VAL or Big Trades)
```

## 2. Interactions stated by presenters (PRESENTER; not in your notes; single examples)

| Chain | Steps | Source |
|---|---|---|
| **Andrea Cimi** (DeepCharts team): the most complete chain using every listed concept | GEX context (0DTE incl. carry, CL-037) → location = prior VAH down to the nearest **LVN** ("demand zone", CL-015) → **order flow**: sellers cluster with no candle closing below = passive buyers, trigger when buyers take control (CL-024) → first target **IVB Protection**, final target **option walls** (CL-044) | YT-007 (7:34; one live trade; DeepGamma 18 % discount) |
| **Vishaal Fx** (your notes' source) | Profile context → ORB/IVB → **delta profile** + "big confirmations" (6:50) → **stacked imbalance** as "super target" (8:53) → switch to 1-min (10:36) → added a contract (12:48) → closed; "$960 … $3,000", "170 pips" | YT-001 (audio sparse; live trade not decoded) |
| **DeepCharts GEX course** | GEX regime → "no-trade cage" between positive-GEX strikes → trade after the cage breaks, "IVB-like" (CL-034); expansion rarely rebalances (CL-031, **refuted for XAU/FX by NEXA OF-20**) | YT-002 |
| **Faiz SMC** (MenthorQ + DeepCharts affiliate) | Open location vs VA = bias (CL-005, **"70–80 %" refuted by NEXA OF-16**) → absorption "inversion" entry (CL-023) → targets at overnight POC/VA | YT-005 |
| **Bookmap / Doug Pless** | SpotGamma levels (call/put walls, volatility trigger) + HIRO option flow → Bookmap heatmap/order flow for entries (SPX/NDX/equities) | YT-003, YT-015–017 |

**INTERP:** all these chains share the order **context (profile and/or GEX) → location (VA edge/LVN/OR) → order-flow trigger → target (VA edge/IVB/wall)**. They differ in which concept fills each slot. **None of them publishes a sample of trades.**

---

# PART III: The complete process map

Each stage lists what your method says (NOTE), what the presenters add (PRESENTER), NEXA's standing controls (NEXA, not part of your method), and reproducibility.

| Stage | NOTE (your method) | PRESENTER additions (optional; D25–D30) | Concepts | NEXA can do today |
|---|---|---|---|---|
| **① Market context** | Balance: price rotating inside VAH–VAL ("ʌʌʌ") | GEX regime (CL-032/033/034); HTF trend (CL-008); session choice (CL-002) | K1, K3, (K8) | Profile **PROXY** ✓ (XAU/EUR/JPY); GEX ✗ |
| **② Location** | Near VAL (bubble); VAL; LVN below VAL; ORB range (page 4) | VAH → LVN demand zone (CL-015); VA edges (CL-006) | K3, K4, K5, K9 | Levels **PROXY** ✓; OR levels ✓ |
| **③ Price response** | Price moves above the bubble (A); breaks bubble + VAL (B); breaks the OR (C) | Wait for a reclaim, not a blind fade (CL-007); close-based trigger (CL-040); 1-min confirmation (YT-001 10:36) | K5, K3, K9 | Price ✓ (once D6/D11 are fixed) |
| **④ Order-flow confirmation** | **Big trades bubble, "for Sellers"** | Delta profile (YT-001); absorption (CL-020–024); stacked imbalance (CL-029); large aggressors through levels (CL-030); option flow/HIRO (CL-038) | K5, K2, K6, K7 | **✗ TRUE** (no aggressor data). **Volume-only proxy ≠ your rule** (§5) |
| **⑤ Trade decision** | A: long, SL below bubble/~VAL, TP VAH. B: short, SL "at the top", TP the LVN. C: ORB → IVB (rules not written) | IVB Protection as T1, walls final (CL-044); stacked imbalance target (CL-029); "1 to 2" (YT-001 13:41, unclear) | K3, K4, K5, K9, K10, (K8) | Geometry ✓ after D12–D18; IVB levels ✗ |
| **⑥ Risk checks** | **None written** (no sizing, no daily limit) | Scaling in (YT-001 12:48); "$960 vs $3,000" (n = 1) | — | **NEXA standing controls** (frozen, not part of your method; would apply to any implementation): 1 % risk per trade to the stop; 2 % daily pre-trade loss budget (C4); currency-exposure and correlation caps (fail-closed); no trade without a stop; news/FOMC veto; stale-bar guard. **Scaling in conflicts with fixed-risk sizing** (needs a separate risk-policy approval) |
| **⑦ Execution** | **None written** (order type, slippage) | Presenter trades CME futures on DeepCharts; market/limit not stated | — | NEXA EA execution is frozen. Costs measured: USD 7/lot commission (≈ 0.25R at 2.4-pip stops). **Real fills: 0** (S14 forward test down since 2026-10-05) |

---

# PART IV: Setups (from your notes; unchanged from v1 except cross-references)

## Setup A: big trade for sellers near VAL, then break above the bubble: LONG

| Element | As written (NOTE) | Undefined → decision |
|---|---|---|
| Context | Price rotating inside value | D1, D2, D3 |
| Location | Bubble at the end of the last down-swing near VAL | D4 |
| Order flow | A big-trades bubble labelled "Big trade for Sellers" (K5) | D7, D10 |
| **Entry** | "When the market move above the bubble … we should buy" | D6, D11 |
| **Stop** | "Below the bubble and also around VAL" | D12 |
| **Target** | "at VAH" | D13 |
| **Invalidation** | Implied: a bubble + VAL break turns the idea into Setup B | D14 |
| Mirror (near VAH, short) | Not in the notes | D15 |

## Setup B: bubble AND VAL broken: SHORT to the LVN

| Element | As written (NOTE) | Undefined → decision |
|---|---|---|
| Trigger | "If market breaks the bubble and break the VAL" | D6, D16 |
| **Entry** | "from here" | D6, D11 |
| **Stop** | "SL at the top" | **D17** |
| **Target** | "TP at below VAL … at below got LVN" | D5 |
| At the LVN | "Unfinish Auction"; "once reach LVN, market will go up" | **D18** |
| Mirror | Not in the notes | D15 |

## Setup C: ORB → IVB

| Element | Known | Undefined → decision |
|---|---|---|
| Opening range | DOC: 15/30/60 min (30 "recommended") | D19, D20 |
| Entry | WB: "E" after an upward break (unconfirmed) | D21 |
| Stop | WB: "SL" (position unreadable) | D22 |
| Targets | IVB levels are proprietary (K10) | D23 |
| Volume condition ("Initial Volume") | No formula anywhere | D24 |

---

# PART V: Big Trades original vs volume-only proxy (kept separate)

| | **Original (your Setup A/B)** | **Volume-only proxy (if ever approved)** |
|---|---|---|
| What the bubble is | A large **aggressive** market order (or aggregated parent order), **side-coloured**; yours is **seller-coloured** | A minute (or cluster of minutes) with abnormally high volume/transactions; **no side** |
| Data | CME trades with aggressor side and size (± MBO) | Pepperstone tick volume (spot) or CME 1-min volume/transactions (Massive) |
| Can express "for Sellers"? | **Yes** | **No** |
| Can separate "trapped sellers" from "absorbing buyer"? | Partly (side known; book unknown without MBO) | **No** |
| What a test would answer | Whether **your rule** works | Whether "**volume cluster near VAL + reclaim → VAH**" works, which is a different hypothesis |
| Naming rule | `OF-03-ORIG` | **`OF-03P` (proxy). Never reported as "Big Trades" or as a test of your method** |

---

# PART VI: Reproducibility summary

| Concept | Status | What is missing |
|---|---|---|
| K1 Volume Profile | **PROXY ✓** (XAU/EUR/JPY); TRUE 2 y daily | 1-min futures volume (collectable via Massive; approval) for intraday true profiles |
| K3 VAH/VAL | **PROXY ✓** | — |
| K4 LVN | **PROXY (weaker)** | Detection rule (D5) |
| K9 ORB | **REPRODUCIBLE ✓** | Rules D19–D24; V2-F2 overlap on XAU |
| K5 Big Trades | **NEEDS DATA** | CME aggressor trades (DataBento candidate; approval/cost); MBO = prospective only |
| K6 Order Flow (absorption, footprint, stacked imbalance) | **NEEDS DATA / NOT REPRODUCIBLE on spot** | Aggressor trades + book |
| K2 Delta Profile | **NEEDS DATA** | Aggressor trades |
| K7 Option Flow | **NEEDS DATA** | CME options trades with side (unverified source) |
| K8 GEX | **NEEDS DATA** | CME options OI by strike, history (GAP-D08) |
| K10 IVB | **NOT REPRODUCIBLE** | Proprietary model |
| Presenter live-trade details | **UNKNOWN** | 1080p screenshots (§VIII) |

---

# PART VII: Decisions needed from you (nothing assumed)

D1–D26 are unchanged from v1.

| # | Question | Options (source-backed) |
|---|---|---|
| D1 | Which profile defines value? | prior full day · prior session (London/NY) · developing · composite |
| D2 | VA % | 70 % (DeepCharts example) · 68 % (NinjaTrader) |
| D3 | "Balancing (ʌʌʌ)" = ? | by eye · n rotations VAH↔VAL · inside value ≥ X time |
| D4 | "Near VAL" = ? | X pips · X·ATR · lower third of value |
| D5 | LVN = ? | DeepCharts valley · local minimum of a smoothed profile · other |
| D6 | "Move above / break" = ? | touch · candle close · close + retest |
| D7 | Bubble = ? | single print ≥ N contracts · aggregated parent order · vendor auto |
| D8 | Minimum R:R / cost rule | none · ≥ 2R · cost ≤ 20 % of stop |
| D9 | Checklist gate | all five must pass · judgement |
| D10 | Must the bubble be seller-coloured? | yes (as labelled) · either side |
| D11 | Trigger timeframe | 1-min (presenter) · 5-min · other |
| D12 | Setup A stop | below bubble · below VAL · lower of the two; buffer? |
| D13 | Setup A target | VAH only · POC then VAH |
| D14 | Other invalidation | none · time limit · end of session |
| D15 | Mirror setups? | yes · no |
| D16 | Setup B event order/window | — |
| D17 | Setup B "SL at the top" | bubble high · VAL · VAH · session high |
| D18 | At the LVN | exit only · exit + long |
| D19 | OR length | 15 / 30 / 60 min |
| D20 | OR session anchor (FX/XAU) | London 08:00 · NY 08:20/08:30 ET · Tokyo · other |
| D21 | ORB entry | close beyond range · + volume condition |
| D22 | ORB stop | opposite side · mid · other |
| D23 | ORB targets (IVB proprietary) | range multiples · VA edges · your choice |
| D24 | "Initial volume" confirmation | RVOL ≥ k · big trades at the break · none |
| D25 | Presenter confirmations (delta, absorption, stacked imbalance, scaling in)? | exclude · include (blocked by data) |
| D26 | Instruments | XAUUSD, EURUSD, USDJPY (proxy-valid) · + GBPUSD only with true futures volume |
| **D27** | *(new)* If the delta profile is included: what delta condition confirms? | none given by any source; your definition |
| **D28** | *(new)* Is option flow part of your method? | no (not in notes) · yes (needs data) |
| **D29** | *(new)* Is GEX part of your method? | no (not in notes) · yes (needs data; SPY evidence says it adds nothing beyond implied vol) |
| **D30** | *(new)* If GEX is included, its role | context/regime filter · targets (walls) · both |
| **D31** | *(new)* Do ORB/IVB (page 4) and the VA/Big-Trades setups (pages 1–3) combine, or are they separate methods? | separate (as written on separate pages) · combined (how?) |
| **D32** | *(new)* Which presenter chain (Part II) is closest to what you actually trade, if any? | Vishaal · Andrea Cimi · none (notes only) |

---

# PART VIII: What would close the remaining gaps

- **Screenshots** of `eLGVyu3utXE` at 1080p:
  - 10:30–10:50, 11:20–12:00, 17:10–18:20 (live chart: levels, entry/stop/target prices, bubbles);
  - 3:00–3:50 and 1:30–2:20 (whiteboards).
  - These would settle D6, D12, D17 and D19–D23 from the presenter's own drawing.
- **Your own marked trade examples**, if you have traded this. They would define D4–D7 directly.
- **The Andrea Cimi video transcript** is already in the KB (YT-007). Its chain (Part II) is the only source that combines GEX, VA, LVN, order flow, IVB and walls. Watching it and confirming whether it matches your intent would settle D29–D32.

# PART IX: Path after approval (research only)

1. You answer D1–D32, or mark items "exclude".
2. A pre-registration from your answers only: **OF-03-ORIG** (true Big Trades; needs data) and, if you want, **OF-03P** (proxy, clearly labelled), plus an ORB test with your own levels if D31 asks for it.
3. **Data approvals only where needed:**
   - CME aggressor-side trades (Big Trades, delta);
   - CME 1-min volume (true intraday profile);
   - CME options OI/trades (GEX, option flow) only if D28/D29 = yes.
4. The same validation discipline as before: driftless-barrier and placebo-level nulls, NEXA costs, holdout opened once. Production, the Risk Engine and MT5 stay unchanged until a separately approved proposal.
