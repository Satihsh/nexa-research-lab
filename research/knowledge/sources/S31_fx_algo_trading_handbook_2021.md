# S31: *Algorithmic FX Trading Handbook 2021* (FXAlgoNews; "A guide to more efficient automated FX trade execution for buyside firms")

**File:** `TRADING-HANDBOOK-2021-SCREEN-1.pdf`. 50 PDF pages, each a **two-page spread**, so about 98 printed pages.

**Structure:**
- About 20 contributed articles: bank algo desks (JPM, HSBC, Credit Suisse, UBS, BofA), independent TCA providers (BestX, Cürex, NCFX/Raidne), consultants (Modular FX, Aoraki, Afett) and academics (Sancetta).
- A vendor directory (about 30 bank and technology providers).
- Advertisements.

| Field | Value |
|---|---|
| **Source type** | **Industry / practitioner.** Vendor-sponsored trade publication. Most articles are written by firms selling the algos or TCA they describe. Not peer-reviewed. |
| **Evidence status** | **Unverified claims / practitioner consensus.** No methods sections. Charts carry proprietary data with no sample definitions. Useful as a **description of institutional FX execution practice** and as qualitative principles. Its numbers are **single-firm, self-reported**. |
| **Processing** | All 50 PDF pages (all spreads) read in full text: 6,177 lines, about 250k characters, including the whole vendor directory. **Contact sheet rendered** (all 50 pages) to locate figures. **High-resolution renders inspected:** p. 4 (JPM volume and algo-type charts), p. 10 (HSBC Fig. 3 IOC round-trip box plots; Fig. 4 short-term volatility vs long/short volatility ratio, 2020), p. 11 (BestX/FX HedgePool "Real Cost of Risk Transfer" chart), p. 21 (FX Global Code Principle 19 box). Remaining charts are vendor illustrations or stock imagery. No equations of substance. |

## 1. Market structure facts (SOURCE: practitioner claims, mostly single-firm)
- **JPM (A. Cole, pp. 6–7; chart V):**
  - share of JPM-client spot eFX in sizes > $10M executed via algo: < 35 % (2016) → ≈ 60 % (2020);
  - click-to-trade share: ≈ 60 % → 22 %;
  - algo ADV during **Mar 9–20 2020** was 556 % of 2016 ADV, against 418 % on the Brexit day. So algos were used *more*, not less, in the volatility spike;
  - **algo-type mix shifted** from limit-based (≈ 55–60 % at the US election 2016 and Brexit) to adaptive (≈ 55 %) in Mar 2020;
  - 21 % of 2020 algo clients were first-time users.
- **HSBC (Barzykin / Nanji, "Liquidity management"):**
  - liquidity should be curated by fill rate, round-trip time (IOC) and post-trade market impact;
  - **last look** and geographically delocalised matching engines create *liquidity mirage* (displayed but not executable);
  - "orthogonal" (uncorrelated) liquidity sources reduce aggregated impact;
  - Fig. 3 (V): IOC round-trip distributions differ by venue by orders of magnitude, with wide dispersion.
  - **Fig. 4 (V):**
    - in March 2020, 30-second volatility spiked about 2.5× the January level;
    - the ratio of long-term (2 h) to short-term volatility **dropped** (≈ 1.35 → ≈ 1.15), and short-term volatility rose relatively more.
    - SOURCE interpretation: "the risk of waiting was overshadowed by the cost of crossing".
- **FX HedgePool (J. Moore; chart V):**
  - FX swaps are about half of FX turnover ($3.2tn/day, BIS 2019);
  - **passive hedge rolls are scheduled (month/quarter end), so they are predictable in timing, size and direction, and can be gamed**;
  - BestX expected spreads for > $1B 1M swaps peaked in Mar 2020 at several times normal.
- **Credit Suisse (algo selection):**
  - choose by benchmark: TWAP/VWAP for schedule; arrival / implementation shortfall for urgency; spread capture for passive;
  - "Sniper"-type opportunistic algos in fast markets;
  - fix algos (WMR 4 pm, BFIX, LBMA gold/silver) for benchmark orders.
- **UBS (C. Gressel):**
  - a core set of algos (Orca, Tap, Float, TWAP/VWAP) covers most needs;
  - **"a single use of a strategy is highly random"**: evaluate on samples, not anecdotes.
- **Mouat (TWAP/VWAP/passive guide):**
  - a simple aggressive TWAP pays about half the spread per child;
  - participation caps of about 15–20 % of volume;
  - VWAP needs a **volume-distribution forecast** (London 4 pm fix, day of week, month end);
  - **passive-algo P&L is asymmetric**: fills come when the market trades through you, and misses come when it runs away (adverse selection).
- **BofA (Vince):**
  - on average, slower algo execution beats the bank's immediate risk-transfer price;
  - the trade-off is variance (time risk).
- **Vendor directory:** XAU/XAG are executed by several bank algos (CS: XAU/XAG/XPD/XPT; UBS: "select precious metals"); fix algos are offered for LBMA bullion. Commerzbank reports TCA impact at 10, 30 and 60 s.

## 2. TCA and benchmarking principles (SOURCE)
- **Sancetta (academic contributor):**
  - FX TCA is **noisy because time (market) risk dominates spread cost**. Execution-quality estimates need many orders;
  - prefer an **arrival mid** (primary-venue mid, e.g. EBS/Reuters) to the dealer's risk-transfer price;
  - real-time TCA via reinforcement learning is "likely".
- **BestX (Eggleston):**
  - OTC FX has **no universal mid**; arrival-price definitions vary between providers (timestamp, source);
  - comparisons need a consolidated, independent reference.
- **NCFX:**
  - impact must be measured against **a rate not sourced from the platform providing the algo**, otherwise market-impact cost is mis-measured;
  - this is an *independent-benchmark* principle (and a sales pitch).
- **Raidne:** "Pure Decay" post-trade reversion as an impact and information-leakage metric. Proprietary; no definition given.
- **Afett (algo wheel):** randomised algo allocation removes trader selection bias, but **small samples limit significance**.
- **Cürex (Singleton):** market impact comes from (a) disclosure/signalling of child orders, (b) **last-look rejections** (rejected fills leak information and cause re-trading at worse prices) and (c) child-order concentration on few venues.

## 3. Governance and validation principles (SOURCE: Modular FX, Grubb / von Massenbach; Mouat)
- Separate **calibration data from choice/validation data** (resampling, partitioning).
- Define each algorithm's **"operational envelope"**: the market conditions it was designed and tested for.
  - **No live parameter changes.** Pre-calibrated regime parameter sets selected by a rule act as a meta-algorithm, tested as a whole.
- Test failure modes explicitly: **missing data, crossed prices, timestamp errors, stale feeds**; kill switch; **stop when behaviour deviates from the envelope**.
- Demand enough data to beat a **null / simple alternative** before deploying.
- **FX Global Code Principle 19 (V, p. 21):** order books, axes and benchmark-fix orders are confidential information. Algo and fix desks should be segregated from principal trading.

## 4. Critical assessment (INFERENCE)
1. **Conflict of interest everywhere.**
   - Bank authors promote their own algos; TCA vendors argue that bank TCA is biased.
   - Numbers (volume shares, cost savings, "studies suggest clients could have reduced costs") are **unverifiable marketing**.
2. **No methods.**
   - JPM charts are % of the *2016 ADV* of JPM clients only.
   - HSBC Fig. 4 has unlabelled venues, an unspecified instrument ("some instruments") and no confidence bands.
3. Still **consistent with academic sources**:
   - adverse selection of passive fills (S06, S10, S11, S29);
   - last-look information leakage (S30 Flash Boys analogue);
   - the variance-ratio change in stress (S38, S15);
   - multiple testing / small samples (S14, S22);
   - TCA noise dominated by time risk (S25 Almgren–Chriss variance term).
4. **Institutional-scale relevance only.** Retail CFD trading at Pepperstone is principal/market-maker or ECN-bridged. NEXA has no algo, wheel or venue choice.

## 5. Principles extracted
- **SOURCE + S25:** execution cost = spread/impact (deterministic) + timing risk (stochastic). In FX the stochastic part dominates single-order outcomes.
  - **INFERENCE:** per-trade slippage comparisons need large n; NEXA's slippage audits must be distributional, not anecdotal.
- **SOURCE:** benchmark choice (arrival mid vs risk-transfer price vs fix) changes measured cost. Independent references are required.
  - **INFERENCE:** NEXA cost models should benchmark fills against an *independent* mid (e.g. bid/ask midpoint at the signal timestamp from broker ticks, with known limitations), not against the order's own requested price.
- **SOURCE:** stress regimes raise short-horizon volatility *more* than long-horizon volatility (March 2020), so the cost of waiting vs crossing changes regime by regime. Links to H-VR-SCALE (S38).
- **SOURCE:** predictable flows (fix, month/quarter-end hedge rolls) are gameable. **INFERENCE:** they are also a known source of calendar-timed price pressure (S01 H-GOTOBI / month-end analogues), which NEXA could *study* but which is not established here.
- **SOURCE:** operational envelope + no live parameter changes + kill switch on deviation = good algo governance. It matches NEXA's frozen-protocol philosophy.

## 6. NEXA relevance
- **Governance (directly transferable, no data needed):**
  - formalise an *operational envelope* per engine (spread, volatility, session, news states tested);
  - a deviation monitor that halts the engine outside its envelope;
  - failure-mode tests for stale, missing or crossed ticks and timestamp errors (NEXA_Safety.mqh already covers part of this).
- **H-VR-SCALE support** (S38): measure the ratio of long-horizon to short-horizon realised variance (e.g. M1 vs H1 scaled) on XAU/FX across regimes. Data: available (M1).
- **H-FIX-FLOW (new, hypothesis):** London 4 pm WMR fix / LBMA gold fix and month-end windows show distinct volatility, spread and reversal patterns.
  - Data: broker M1 with spread, available.
  - Look-ahead: fix times shift with UK/US DST (cf. memory note on server = NY+7).
- **Cost measurement:**
  - NEXA slippage studies should use the arrival mid at signal time;
  - report distributions with n;
  - expect high noise (Sancetta).
- **Not applicable:** algo wheels, venue curation, last-look management, segregated desks.

**Cross-references:**
- S25 (Almgren–Chriss time-risk/impact trade-off);
- S06, S10, S11, S29 (passive-fill adverse selection);
- S38 (variance ratio vs sampling interval);
- S15 (FX scaling laws);
- S30 Flash Boys (information leakage, latency);
- S32 Harris (benchmarks, order exposure, dealers);
- S14, S22 (multiple testing; small samples);
- S39 (FX intervention/fix as a market mechanism);
- S01 (Gotobi/fix calendar effects).
