# B1: Academic foundations for the 12 concepts (batch 1, 2026-10-11)

**Method:** web search (standard and extended) plus corpus notes S42/S44/S46/S49/S51/S52/S53.
- Findings are labelled **VERIFIED-LIT** only where the publication and its core result were confirmed from an abstract or full text.
- Secondary summaries are marked (sec.).
- No full-text verification was possible for paywalled items; they are flagged.

## 1. Volume profile, value area, POC, LVN

| Finding | Source | Class | Implication |
|---|---|---|---|
| **No peer-reviewed study tests volume-profile POC/VA/LVN levels on futures** with controls. The only volume-profile study found (WIG20 index, Poland) counts reactions to the prior POC without a significance/profitability test | Search 2026-10-11; ResearchGate "Use of the volume profile in making investment decisions on the stock market" (sec.) | VERIFIED-ABSENCE (search) | Every profile rule is **practitioner-only**; NEXA's own tests (T1, OF-16) are among the few controlled tests |
| Horizontal S/R levels predict trend *interruptions* better than chance, but fail to beat buy-and-hold (US stocks) | "Identifying and evaluating horizontal support and resistance levels" (ResearchGate 233852842) (sec.) | VERIFIED-LIT (abstract) | Reaction ≠ profit |
| Published S/R levels from FX firms predict intraday trend interruptions, with significance lasting up to 5 days | Osler (2000), "Support for resistance" (FRBNY) | VERIFIED-LIT | Mechanism for level reactions in FX |
| Prices re-bounce more often than they cross S/R levels vs shuffled series (memory effect) | Garzarelli et al., arXiv 2101.07410 | VERIFIED-LIT (preprint) | — |
| **VA algorithm and "70 % ≈ 1σ"**: Dalton two-bin greedy; Steidlmayer 68 %; the σ analogy holds only under normality; intraday profiles are often bimodal | S42 App. 1; S46; corpus note | VERIFIED-DOC (book) + critique | VA % is a convention (CL-071) |
| **Dalton's quantified MP studies**: 3-1 days 94 % / neutral-extreme 64 % next-session continuation | S42 (T-bonds 1986–87; n not stated; no base rate) | PRACTITIONER STAT (unverified) | HYP-008/009 untested |
| **"80 % rule" (Value-Area Rule):** no independent or peer-reviewed backtest. Dalton's wording is "a good possibility" (S42); "80 %" is a later rule-of-thumb label. A NexusFi sample: 75/120 = 62.5 % far-side completion (12 % setup rate); a replier could not reproduce it | S42; LuxAlgo library (sec.); futures.io thread (sec.) | UNVERIFIED-CLAIM | HYP-007 untested in NEXA |

## 2. Big trades, trade size and informed trading

| Finding | Source | Class | Implication |
|---|---|---|---|
| **Medium-size trades, not large ones, carry most cumulative price change** (stealth trading) | Barclay & Warner (1993, JFE); Chakravarty (2001, JFE): institutions' medium trades drive it | VERIFIED-LIT | A "big trade" filter targets the wrong bucket if the goal is informed flow. Big prints may be liquidity/hedging |
| Trade-count measures capture split-order pressure better than volume | Order-imbalance literature (sec.) | VERIFIED-LIT (sec.) | Aggregating child prints into parents (DeepCharts/ATAS "aggregate") is the relevant construct, not single prints |
| Order splitting creates **long memory in trade signs** (ACF ~ τ^−0.6); prices stay close to unpredictable because size and liquidity compensate | Lillo & Farmer (2004); Lillo, Mike & Farmer (2005); confirmed quantitatively by Sato & Kanazawa (2023, TSE) | VERIFIED-LIT | Aggressor flow persists, but its predictive value for price is largely neutralised |
| Pre-trade transparency lowers the price contribution of large trades | 2014 study (sec.) | VERIFIED-LIT (sec.) | Visible "big trades" are partly a transparency artefact |
| **CME large trades:** buys → permanent (information), sells → temporary (liquidity); flips with bull/bear state | Frino, Bjursell, Wang & Lepone (2008, JFM) | VERIFIED-LIT (abstract) | Mechanism for "big seller print then rebound" (CL-099) |
| E-mini blocks: buys more informed in bear markets, sells in bull markets | Frino, Mollica, Romano & Zhou (2017, JFM) | VERIFIED-LIT | Contradicts 2008 on the state direction (CL-100) |
| Futures: Berkman, Brailsford & Frino (2005, FTSE): small permanent impact, no size link; a 14-market index-futures study: block trades partly temporary, partly informed | (sec.) | VERIFIED-LIT (sec.) | Mixed |

## 3. Order flow, imbalance, delta

| Finding | Source | Class | Implication |
|---|---|---|---|
| **Order-flow imbalance at the best quotes explains most short-horizon price variation, contemporaneously**; slope ∝ 1/depth | Cont, Kukanov & Stoikov (2014, J. Fin. Econometrics 12:47–88) | VERIFIED-LIT | Explains *current* price change (seconds–minutes); not a forecast |
| Market and limit order flows jointly explain returns; all regressions are contemporaneous | Kozhan, Moore & Payne (2018) = corpus S51 | VERIFIED-LIT | Same-bar delta "confirming" a move is partly an identity (look-ahead trap) |
| Equity order imbalance: negatively related to short-horizon, positively to longer-horizon returns | Chordia, Goyal & Jegadeesh (sec.) | VERIFIED-LIT (sec.) | Mixed |
| Futures (Chinese ags): lagged imbalance positively predicts same-day returns | Zhao (AUT) (sec.) | VERIFIED-LIT (sec.) | One market; not CME |
| **No study found of footprint "stacked imbalance" or "delta divergence" as a signal** | search | VERIFIED-ABSENCE | Practitioner-only |

## 4. Absorption and icebergs

| Finding | Source | Class | Implication |
|---|---|---|---|
| **CME native icebergs** keep one order ID across refills, so they are detectable from MBO. Synthetic icebergs look like independent orders. Icebergs are ≈ 3–8 % of volume | Exegy (sec.); arXiv 1909.09495 "CME Iceberg Order Detection and Prediction" (ESU19, 1 week, out of sample; **author affiliated with dxFeed, a vendor of iceberg detection**) | VERIFIED-LIT (preprint, conflict noted) | "Absorption by a reloading passive order" (Axia CL-020) is measurable **only with MBO**; no historical MBO for NEXA |
| Detected icebergs attract market orders; latent liquidity determines price impact | CFR Cologne WP 09-06 | VERIFIED-LIT (WP) | Absorption has a microstructural basis; its trading value is untested |
| Optimal iceberg display / testing | Esser & Mönch (S27), Sahni (S28), Cebiroglu & Horst (S29), in the corpus | VERIFIED-LIT | — |

## 5. ORB and intraday momentum

| Finding | Source | Class | Implication |
|---|---|---|---|
| 5-min ORB on QQQ: hit rate 24 %, +0.13R/trade, 4× leverage ≈ 33 %/yr (gross of spread/slippage; no OOS) | Zarattini & Aziz (2023), SSRN 4416622 (sec.) | VERIFIED-LIT (sec.) | — |
| ORB on "Stocks in Play" (7,000+ US stocks, 2016–23); a QuantConnect recreation reports Sharpe 2.4 | Zarattini, Barbon & Aziz (2024), SSRN 4729284 (sec.) | VERIFIED-LIT (sec.) + 3rd-party replication | Stock-selection driven; not FX |
| **Independent replication on NQ, SPX, Dow, DAX, FTSE CFDs 2015–2026: gross reproduced (NQ +0.131R, 23.2 %), net ≈ 0, 4 of 5 negative** | MQL5 blog post 776235 (sec.) | INDEPENDENT REPLICATION (non-peer) | Matches NEXA C1: gross edges die at retail cost |
| **Intraday momentum** (first part of the day predicts the last 30 min) in 60+ futures incl. currencies, 1974–2020; reverses over the following days; driven by gamma hedging of option dealers and leveraged ETFs | Baltussen, Da, Lammers & Martens (2021, JFE 142:377–403) | VERIFIED-LIT | The **only peer-reviewed bridge between GEX and intraday futures returns**; mechanism-level, not a level-trading rule |

## 6. Option flow and GEX (excluded from the core by the user; kept for completeness)

| Finding | Source | Class |
|---|---|---|
| Buyer-initiated open-position put/call volume predicts next-day (≈ 40 bp) and next-week (≈ 1 %) stock returns, 1990–2001; non-public information; **none for index options** | Pan & Poteshman (2006, RFS) | VERIFIED-LIT |
| GEX tracks next-day RV raw but adds nothing beyond VIX + ATM IV (SPY 2018–2026) | FlashAlpha (CL-075) | VENDOR-PUBLISHED (method disclosed) |
| Pinning at strikes near expiry | Ni, Pearson & Poteshman (2005) | VERIFIED-LIT (KB) |
| "Gamma Fragility" (Barbon & Buraschi) | St. Gallen repository | EXISTS; findings not retrieved |

## 7. Stops and round numbers (supports VA-edge / bubble-stop mechanics)
- **Osler (2003, JF 58:1791–1819):** take-profit orders cluster at round numbers, so rates reverse there. Stop-loss orders cluster just beyond them, so rates accelerate after crossing ("price cascades", FRBNY SR 125/150).
  - Effects last hours, not days. Data: about 9,700 orders at one dealing bank, 1999–2000.
  - **Class:** VERIFIED-LIT.
  - **Implication:** the only peer-reviewed mechanism behind "break of a level accelerates; reaction at levels". It concerns *order clustering at prices*, not volume nodes.

## 7b. Base rates for discretionary intraday trading (the prior any order-flow method must overcome)
| Finding | Source | Class |
|---|---|---|
| 19,646 individuals who began day trading Brazilian mini-index futures in 2013–15: **97 % of those who persisted > 300 days lost money**; 1.1 % earned more than the minimum wage; no evidence of learning | Chague, De-Losso & Giovannetti, "Day Trading for a Living?" (SSRN 3423101; FGV) | VERIFIED-LIT |
| Taiwan day traders: **97 % likely to lose** in future day trading; fewer than 3 % predictably profit net of costs; losers keep trading (overconfidence) | Barber, Lee, Liu, Odean & Zhang, *Review of Asset Pricing Studies* 10(1) 2020 | VERIFIED-LIT |
| ORB intraday rule on crude-oil (keyword) futures: returns significantly > 0 and success rate above a fair game (costs not stated in the abstract) | Holmberg, Lönnbark & Lundström (2012), Umeå WP 845 | VERIFIED-LIT (abstract only) |
| No academic test of a London-open breakout on EURUSD or gold was found | search 2026-10-11 | VERIFIED-ABSENCE |
| **No published controlled test of LVN reactions, stacked imbalances or delta divergence** was found; vendor/blog win rates (70–80 %) have no methodology | search 2026-10-11 | VERIFIED-ABSENCE |

## 8. B1 conclusions
1. **Definitions are solid; edges are not.** The profile, value area, footprint, delta and big trades are well-defined display constructs. **No peer-reviewed evidence shows that trading VAH/VAL/POC/LVN reactions, big trades, stacked imbalances or delta divergence is profitable.**
2. **The microstructure literature explains *why* order flow and price co-move (contemporaneously)**, which is why order flow works as a *confirmation of what is happening now*. It also warns that large single prints are not where informed flow concentrates.
3. **The two peer-reviewed tradable effects found (ORB, intraday momentum) are gross effects whose net survival at retail cost is doubtful.** One independent replication failed net; NEXA C1 shows the same pattern.
4. **Base rate:** about 97 % of persistent discretionary futures day traders lose (two large administrative datasets). Any claimed edge in this field starts from that prior.
5. **The strongest *evidence-type* available for this specific methodology is practitioner live performance** (B3: audited contest placings), not academic tests.

## 9. FX fix effects (added 2026-10-11, for the post-IM1 roadmap)

| Finding | Source | Class | Implication for NEXA |
|---|---|---|---|
| **Daily USD reversal around the three fixes:** USD appreciates before the Tokyo (9:55 JST), ECB (14:15 CET) and London (16:00) fixes and depreciates after (W-shape).<br>Per-window bp per day (foreign currency vs USD), 1999–2019, G9: **pre-ECB 02:00–08:15 ET** EUR −3.52, GBP −2.29; **post-London 11:00–17:00 ET** EUR +2.73, GBP +2.65, JPY −1.16 (opposite); **post-Tokyo 20:55–02:00 ET** EUR +2.34, JPY +3.15; pre-Tokyo 17:00–20:55 EUR −1.80.<br>t-stats 4.5–11.7; strategy returns **ignore costs** | Krohn, Mueller & Whelan (2024, *J. Finance* 79:541–578); BoC SWP 2021-48 | VERIFIED-LIT | 2–3.5 bp gross per window per day, 4–10× IM1's 0.35 bp. Uses FX prices only (on disk). 2020–2026 is out-of-sample relative to the paper |
| **Month-end hedging flow:** a country's equity outperformance over the month predicts currency depreciation in the hour before the **end-of-month** 4 pm fix (10 % equity → ≈ 14 bp), partly reverting next day; 2004–2012 | Melvin & Prins (2015, *J. Fin. Markets* 22:50–72) | VERIFIED-LIT (abstract + WP) | Conditional and small (≈ 4–7 bp per month-end at typical equity moves). Needs monthly equity-index returns (not on disk) |
| Excess volatility and negative serial correlation around the WMR fix in 21 pairs, every year; strongest at month-end | Evans (2018, *J. Banking & Finance* 87:233–247) | VERIFIED-LIT (abstract) | Supports fix-centred reversal timing |
| Pepperstone costs (published): MT5 Razor USD 7/lot round trip (cTrader USD 6). Active Trader rebate USD 1/lot (official, from 200 lots/month); third-party reviews: up to USD 3/lot above 1,500 lots/month → EURUSD all-in ≈ 0.26–0.8 pip | pepperstone.com Active Trader page; forexbrokers.com, dailyforex.com reviews (sec.) | VERIFIED-DOC (+ sec.) | Best-case cost floor ≈ 0.3–0.5 bp. IM1 (≈ 0.5 bp gross FX) stays ≈ 0 even at the top tier |
