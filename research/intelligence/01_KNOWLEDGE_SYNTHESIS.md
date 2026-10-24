# 01: KNOWLEDGE SYNTHESIS (56-file NEXA Knowledge Base)

**Phase:** research only (directive "Knowledge + Intelligence Synthesis", 2026-10-04).
**Not changed:** the S14 forward test (live on demo <demo-account>), NEXA_Risk, execution logic, production inputs, schema v1, PackFeatures(), V2 and 8E.

**Tags used throughout:**
- **SOURCE:** stated in a corpus file.
- **EXTERNAL:** standard literature not in the 56 files, named so it can be checked; never presented as read from the corpus.
- **INFERENCE:** our reasoning.
- **MEASURED:** our own probe, with code and output in `evidence/`.
- **HYPOTHESIS:** untested.

---

## 1. Inventory: 56 files = 39 original + 17 new

| Set | Files | Content | Processing |
|---|---|---|---|
| **Original** (2026-10-01/02) | 39 PDFs, 92.37 MB | 38 distinct works, S01–S39 (S37 = duplicate of S06) | Fully processed in `research/knowledge/` (KB, 40-item backlog, contradictions, failed ideas, maths and statistics KBs, graph) |
| **New** (2026-10-04) | 17 files, about 60 MB: **15 PDFs + 2 `.bibtex` records** | S40–S54 below, plus B1 and B2 | Text-extracted with PDFKit (per page). All 15 PDFs read fully or in the sections listed in `sources/*.md` |

**The 17 new files**

| ID | File | Work | Type | Evidence status |
|---|---|---|---|---|
| S40 | Anna Coulling A complete Guide to Volume Price.pdf | **Cliff-notes by @HowLn_** of Coulling's VPA (not the book) | Practitioner, secondary | UNVERIFIED; secondary source |
| S41 | Anyone_Can_Learn_Market_Profile.pdf | "Dean Market Profile" (2019), AMT/MP, LCTR | Practitioner | OPINION |
| S42 | James Dalton - Mind over Markets.pdf | Dalton, Jones & Dalton (1993) | Practitioner classic | UNVERIFIED; the only quantified MP studies (n not stated, one market) |
| S43 | MarketProfile_v1.15.pdf | EarnForex MT4/MT5 TPO indicator manual | Tool documentation | n/a |
| S44 | Order-Flow-Trading-Setups-1.pdf | "Trader Dale", footprint/order-flow setups | Practitioner | UNVERIFIED; trades hypothetical |
| S45 | Profit with the Market Profile_….pdf | Keppler (2010) | Practitioner | UNVERIFIED |
| S46 | Steidlmayer on Markets_….pdf | Steidlmayer & Hawkins (2003, 2nd ed.) | Practitioner classic | UNVERIFIED |
| S47 | The Man Who Solved the Market PDF.pdf | **Bookey summary** of Zuckerman (2019) (not the book) | Journalism summary | NARRATIVE |
| S48 | Trading-Volatility.pdf | Bennett (2014), *Trading Volatility* | Sell-side textbook | ESTABLISHED (textbook option maths) |
| S49 | VOLUME-PROFILE-The-insiders-guide-to-trading.pdf | "Trader Dale", Volume Profile | Practitioner | UNVERIFIED; trades hypothetical |
| S50 | content.pdf | Serrano (2022), MSc thesis, GME gamma squeeze | Academic thesis | CASE STUDY (n = 1) |
| S51 | ssrn-2403000.pdf | Kozhan, Moore & Payne (2018), market vs limit order flow | Academic | RESEARCH FINDING (contemporaneous) |
| S52 | ssrn-3997109.pdf | Cont, Cucuringu, Glukhov & Prenzel (2021), client order flow | Academic (Oxford/JPM) | RESEARCH FINDING (descriptive) |
| S53 | ssrn-7098358.pdf | Sen (2026), GEX engine for gold and ES futures | Practitioner methodology | METHOD DISCLOSURE; no predictive test |
| S54 | ssrn-7131778.pdf | Chilingarian (2026), the sign of dealer gamma | Methodology standard | ESTABLISHED maths; no predictive test |
| B1 | Gamma_Exposure_Gex_for_0dte_Traders.bibtex | Citation only: Edet (2026), KDP | **Not content** | **NOT READABLE; never cite as read** |
| B2 | Options_Market_Microstructure.bibtex | Citation only: Schwartz & Whitemore (2026), KDP | **Not content** | **NOT READABLE; never cite as read** |

**Processing notes**
- **Text was extracted for all 15 PDFs.** S47's first extraction was truncated at page 24 by a NUL character and was re-extracted (186/186 pages).
- **Low-text pages** (figures and charts) occur in S42 (126), S44 (49), S45 (32) and others. They hold practitioner chart examples and were interpreted from captions and surrounding text.
- **Two binding provenance limits:**
  - **S40 and S47 are summaries by third parties.** Neither can stand in for the original book.
  - **B1 and B2 are bibliographic stubs.** The two most GEX-specific titles in the new set are **absent**.

## 2. Classification of the 56-file base by NEXA research tier

| Tier (directive §24) | Original 39 | New 17 | Net position |
|---|---|---|---|
| **T1** Microstructure, order flow, liquidity, volume, delta | S06, S10, S11, S13, S24–S29, S30–S32, S34 (LOB, last look, iceberg, adverse selection) | S51, S52 (academic order flow); S44 (practitioner footprint); S40 (VPA) | **Strong theory**, but **every quantitative result needs data NEXA lacks** (signs, depth, IDs) |
| **T2** Volume/delta profile, market structure, volatility, regimes | S04, S15, S18, S22, S23, S38, S39 (volatility); S01, S07–S09, S17, S19 (practitioner structure) | S41, S42, S43, S45, S46, S49 (Market/Volume Profile); S48 (volatility estimators) | **The volatility layer is strongly supported.** Profile/structure claims are **all unverified** but **mechanically codifiable** and **testable with data NEXA holds** |
| **T3** Options flow, GEX, walls, dealer positioning | S04, S18, S21 (option pricing only) | S48, S50, S53, S54 (B1, B2 absent) | **Measurement standard exists (S54); predictive evidence is absent** (S53 and S54 state it). Academic support only for a **volatility** effect (Ni et al., cited in S50/S53). **Data unavailable to NEXA** |
| **T4** Cross-asset, macro | S14 (lead–lag), S25, S36, S39 (IMF FX) | S51 (FX order flow ↔ returns, macro horizon) | Lead–lag decays within months (S14); order flow explains exchange rates *contemporaneously* (S51) |
| **T5** Advanced maths and physics | S04/S18 (rough volatility), S14 (signatures), S02/S03 (DL/RL), S34 (point processes) | S52 (signed measures, spectral clustering), S47 (HMM mention, second-hand) | Methods are well documented. Applicability is gated by T1/T2 evidence |

## 3. Consolidated knowledge map (what the 56 files jointly establish)

These are ranked by evidence. The original P-numbers are from EVIDENCE_MAP; N-numbers are new.

1. **P1, costs decide outcomes.** Strongly supported (original corpus).
   - **NEXA-specific confirmation (MEASURED, 2026-10-03):** NEXA's own rule set is −0.072R per trade *gross* and −0.318R *net* over 1,902 trades.
   - Commission alone costs −0.245R, **because stops are tiny** (EURUSD median 2.4 pips).
   - **Any new construct must widen the expected move relative to cost, or it cannot help.**
2. **P2/P5, volatility is forecastable; direction mostly is not.**
   - Unchanged.
   - **S48 adds** efficient OHLC variance estimators (Yang–Zhang up to 14× close-to-close efficiency) and the volatility-risk premium (implied above realised by 1–2 points, equities).
3. **N1, order flow and price are *jointly* determined (S51).**
   - Market *and* limit order flow explain same-interval returns: R² rises from under 10 % to over 50 % in equities.
   - The market-flow coefficient is biased about 13–25 % downward if limit flow is omitted.
   - **None of this is predictive.** The regressions are contemporaneous.
4. **N2, flow is heterogeneous by participant, and the types are stable (S52).**
   - **Four types:** quant, day-VWAP, signal, residual. They stay in their cluster about 80 % of the time.
   - **Their flows are near-independent.**
   - **This explains why time-of-day matters** (VWAP flow at the open, "signal" flow at the US open).
   - **But only agent IDs reveal the types.**
5. **N3, dealer gamma regime is a *volatility* concept, not a direction concept** (S53 §2.1; S54; Ni et al. via S50).
   - **Long dealer gamma:** dampening, mean-reverting hedge flow.
   - **Short dealer gamma:** amplifying flow.
   - **The sign of GEX is an inventory assumption** (S54, put–call parity). Signed volume is needed to measure it (S50).
6. **N4, hedging can pin only if hedge flow is large relative to underlying volume** (S48).
   - "Given the high trading volume of indices, it is difficult to pin a major index."
   - **This is the quantitative precondition every wall/pin claim must meet.**
7. **N5, auction/profile concepts are consistent across all practitioner sources** (S41, S42, S45, S46, S49):
   - value area of 68–70 %;
   - POC;
   - initial balance;
   - range extension;
   - day types;
   - open types;
   - "volume slows price".
   - **None are tested beyond Dalton's one-market, about one-year 1986–87 T-bond tallies** (no n, no base rate).
8. **N6, CFD tick volume is a usable but partial proxy for exchange volume** (MEASURED, 2026-10-04, `evidence/`):
   - **Hourly level:** log-correlation with COMEX GCZ6 volume is 0.82, and with CME 6EZ6 is 0.88.
   - **After removing hour-of-week seasonality:** 0.67 and 0.57 (R² ≈ 0.45 / 0.32).
   - **Daily volume profile:** the POC is within $2 of the COMEX POC on 13 of 20 days. **On bimodal days the POC jumps $12–68.** The value-area Jaccard median is **0.82**.
   - **Value areas are a robust proxy; the POC is a fragile one.**

## 4. Duplicate and overlapping concepts (count families, not names)

| Concept family | Appears as | Single underlying statistic |
|---|---|---|
| **Volume-at-price density** | VA, POC, HVN/LVN (S42, S45, S46, S49, S43); "volume clusters" and "multiple HVN" (S44); "accumulation zone" (S49) | One object: the **volume-at-price distribution** L(p) (06_LIQUIDITY_MODEL) |
| **TPO density** | TPO profile (S42, S43, S45) | A time-at-price distribution; with tick volume as weight it becomes a volume profile |
| **Signed flow** | Delta, cumulative delta, divergence (S44); "effort vs result" (S40); OBI/CVD proxies (NEXA f30/f31); market order flow (S51); OFI (S52) | One object: **signed aggressor volume**. NEXA has only quote-direction proxies |
| **Imbalance** | 300 % diagonal imbalance, stacked imbalances (S44); depth imbalance (S13, S26) | Ratios of the signed-flow components |
| **Range expansion vs base** | IB and range extension, day types (S42, S46); squeeze (S09, S19); "thin profile" (S49) | Range/volatility state (the original corpus "range/volatility" family) |
| **Level reaction** | Walls (S53), VA edges (S42), HVN S/R (S44, S49), round numbers (S32 H-ROUND-NUM), liquidity sweeps (NEXA f11/f12, f32–f46) | **One hypothesis family:** "price behaves differently near a defined level". It must be tested as a family, with an FDR correction across level definitions |
| **Regime** | Day types (S42, S46), gamma regime (S53), HMM (S47), trend frequency claims | Discrete latent state. One family |

**Rule carried forward (from the original KB §5):** a test of many level definitions is one hypothesis tested many times. Multiple-testing correction counts families.

## 5. Contradictions, new set (both sides preserved)

| ID | Side A | Side B | Status |
|---|---|---|---|
| **CN1** | **S53, S54 (Model A):** call OI → *positive* dealer gamma (dealers long calls, i.e. customers overwrite) | **S50:** customers *buy* calls → dealers *short* calls → *negative* gamma | **The sign is market- and period-specific (S54 §3.1).** Unresolvable without signed volume. S53's own sentence "dealers are long the calls … that customers have bought" is self-contradictory |
| **CN2** | **S48:** "difficult to pin a major index"; pinning needs hedge flow that is large relative to volume | **S53:** walls "cap rallies and floor sell-offs", pins strengthen into expiry, on ES *and gold* | Testable via the hedge-pressure ratio (EQ-HPR). The 0DTE growth after 2014 may reconcile it for ES only; gold has no 0DTE chain |
| **CN3** | **S46:** value area = 68 % ("first standard deviation") | **S42, S45, S41:** 70 % | A convention, not a finding. NEXA must fix one parameter and pre-register it |
| **CN4** | **S46:** markets trend 10–20 % of the time | **S42:** 20–30 % | Both unsourced. Measurable once "trend day" is defined (HYP-MP-04) |
| **CN5** | **S46:** after a trend day, 90 % sideways or reverse next day | **S42:** after 3-1 or neutral-extreme days, continuation (94 % / 64 % trade beyond the prior VA in the first 90 minutes) | Different structures. Both testable on the same data (HYP-MP-01/03) |
| **CN6** | **S44 text:** "Delta shows a **sum** of Bid and Ask" | **S44 usage, S51, all literature:** delta is a **difference** | A formula error in S44 (logged) |
| **CN7** | **S41:** "stop relying on statistical patterns as they are not applicable" | **NEXA governance and the original corpus:** statistical validation is mandatory | Philosophical. NEXA keeps its evidence standard |
| **CN8** | **S44:** delta and order flow used *predictively* for entry timing | **S51:** the evidence is *contemporaneous* (explanatory) | The directive's "order flow = WHEN" is **untested** in the corpus (HYP-ARCH-01) |
| **CN9** | **S40 (Coulling notes):** high-volume sell-off bottom = "buying climax" | **Standard Wyckoff usage:** "selling climax" at the bottom | Terminology only. Define by observable conditions, never by label |
| **CN10** | **S44:** transfer futures levels to spot FX "visually" (≈ 100 % correlation) | **MEASURED:** 6EZ6 − EURUSD ≈ +0.0047; GCZ6 − XAUUSD ≈ +$35–50, falling from 49.7 to 35.1 over 2026-08-31 → 09-25, about −$0.6/day, as the contract approaches expiry (carry) | A level mapping must use an explicit, time-varying basis (EQ-BASIS) |
| **CN11** | **S53:** max pain is "empirically negligible" beyond 5 DTE (asserted) | **No source** gives evidence either way | Unknown. Not a NEXA priority |

Original contradictions A1–A17, B and C remain in force (`research/knowledge/CONTRADICTIONS.md`). The most relevant here:
- **A6:** does public order-book data predict the next move?
- **A5:** is trend following alive?
- **A4:** is MA mean reversion an artefact?

## 6. Agreements across independent lines

**Evidence classes:**
- **(a)** academic or empirical;
- **(b)** textbook theory;
- **(c)** practitioner consensus.

| Statement | Lines of support | Strength |
|---|---|---|
| Dealer/market-maker inventory hedging produces price-dependent flows | S48 (b), S50 (a, case), S53 (c), S54 (b); original S11, S10 (b) | **Strong mechanism. Weak NEXA-applicable evidence** |
| Volume concentrates at accepted prices; price "slows" in high-volume areas | S42, S45, S46, S49, S44 (all c) | **Practitioner consensus only.** It is a clean HYPOTHESIS (HYP-LIQ-01) |
| Signed aggressor flow is the strongest same-interval price-change correlate | S51 (a), S52 (a); original S13, S26, S34 (a) | **Strong**, but contemporaneous and data-limited |
| Session/time-of-day structures flow and volatility | S52 (a, agent timing), S42/S46 (c, IB/opens); original S23 (a), S14 (a) | **Supported** |
| Costs and validation failures dominate published "edges" | Original P1, P6–P8; NEXA's own measured results | **Strong** |

## 7. NEXA's own history: constraints on this research (not reinterpreted)

| Prior result | Constraint it imposes |
|---|---|
| **8E campaign REJECTED** (terminal, seq 2170); V2 FROZEN, OOS 2027 prospective | Do not open, modify or reinterpret. New work cannot use 2027 data |
| **Cap-neutral A4 (2026-10-03):** −0.318R net per trade, CI [−0.384, −0.250], n = 1,902; −0.072R gross; every symbol negative | The current SMC-style rule set (f00–f27, f32–f46) has **no edge**. New intelligence must be tested **as an addition with ablation**, not assumed to rescue it |
| **The +24.5 %/day objective is CONTRADICTED** (arithmetic ceiling +12.67 %; best day +3.15 %) | No framework in this package targets it. Expected value is in R, net of costs |
| **Commission ≈ 0.245R at a 2.4-pip median stop** | **The stop-distance distribution is a first-order design variable.** Any stop rule (§9 of the directive) must be compared in *net* R |
| **Parity regime:** 44/48 features match the research oracle; f30/f31 (tick proxies), f46 and f47 are exempt | New tick-dependent features inherit the same non-reproducibility. **Bar-reproducible definitions are preferred** |
| **Original backlog priority:** method gates → volatility layer → execution logging → regime descriptors → patterns | Kept. The new T1–T5 order is merged into it (02, 14) |

## 8. What the new 17 files add, net

1. **A precise, testable vocabulary for auction/profile structure:** IB, range extension, day types, open types, VA rule, 3-1 days. Previously the corpus had none of this. Every item is a HYPOTHESIS.
2. **A measurement standard for dealer gamma** (S54) and a full disclosed engine (S53) for the day OI/IV data exist.
3. **Academic grounding** that order flow is informative *about the same interval* (S51) and heterogeneous (S52).
4. **Volatility-estimation upgrades** (S48 App. A.2) usable immediately with NEXA's OHLC.
5. **Clarity about data:** the new corpus repeatedly assumes centralised futures data (S44, S53) that a spot-CFD trader does not have. **The Massive probe confirms NEXA has exchange futures *aggregates* (real volume) but no signed trades, quotes or option OI.**
