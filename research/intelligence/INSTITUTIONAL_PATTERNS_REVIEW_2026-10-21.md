# Six "reverse-engineer the institutions" ideas: evidence review (2026-10-21)

User request: research 6 ideas (time-based sweeps / ORB, TPO value area and volume vacuums, volatility squeeze, icebergs, stop runs, spoofing) "with all skills, tools and connectors". Sources used: NEXA ledger and KB, OpenAlex, Firecrawl paper index, Exa web search, arXiv, SSRN, CFTC.

## 0. One correction first: what "REA" can and cannot do
- **REA is a software reverse-engineering tool** (Ghidra, Kuna, jadx, Hopper). It takes apart programs (binaries, apps). It does **not** analyse prices, volume or order books, and it cannot discover a trading algorithm from market data.
- **Using REA on ATAS, dxFeed or Topstep software is forbidden** (ATAS licence §6; standing NEXA rule).
- What the six ideas actually need is **statistics on market data** (Python, QuantConnect, our recorder files), which NEXA already does. In this note, "reverse engineer" means "measure the pattern and test whether it pays after costs".

## 1. Verdict table

| # | Idea | What is true (evidence) | What is overstated | NEXA status | Data at $0? | Verdict |
|---|---|---|---|---|---|---|
| 1 | Opening-range "institutional" breakout | Volume and volatility are U-shaped (high at open and close; Gerety & Mulherin 1992, Gao et al. 2018). Execution algos follow that curve (VWAP literature). The first 30 min weakly predicts the last 30 min (Gao et al. 2018, R² 1.6 %) | "Institutions sweep retail at exact times"; "mathematical threshold confirming an institutional trend" | 3 tests: H-ORB-1 +0.063R p 0.15 (inconclusive), H-ORB30L-NQ OOS −0.071R (failed), H-IM-NQ −3.1 bp (rejected) | Yes (QC NQ minute 2009–2026) | **Weak, cost- and regime-dependent.** See §2 |
| 2 | TPO / value area / "volume vacuum" | Support/resistance levels coincide with real resting depth (Kavajecz & Odders-White 2004, RFS). Thin books give bigger moves (order-book models; Cont et al. 2013: price impact ∝ 1/depth) | "Ride a burst to $600 in minutes" | VA rules: H-VAR-NQ inconclusive, T2a 80 % rule rejected (≈1,450 trades each, ES/NQ), OF-16 inconclusive. **LVN speed (HYP-004/006) untested** | Yes (QC minute volume-at-price proxy; our recorder footprint going forward) | **Value-area trading rejected; LVN "speed" is a free descriptive test** |
| 3 | Volatility squeeze | Volatility clusters and mean-reverts (Engle 1982) | "Squeeze predicts a violent move"; direction | Squeeze as a direction signal rejected inside 8E (2,160 trials); HYP-019 (compression → expansion) untested | Yes | **Evidence negative:** Girgin 2026 (SSRN 7600800, 36 definitions, S&P 500 2006–25): squeezes do *not* precede volatility bursts; the squeeze breakout lost money. EdgeTools: 0 significant results from 7.2M squeeze tests. Not worth a NEXA trial |
| 4 | Iceberg absorption | CME native icebergs can be detected (trade size > displayed size, refills; Zotikov & Antonov 2019/2020). When icebergs are detected, the other side trades into them more aggressively (Pardo & Pascual 2011; Frey & Sandås 2017) | "Marker the exact millisecond", "ride as shorts get squeezed" | Blocked so far (needed MBO) | **Partly, now:** the VM recorder logs every trade with the best bid/ask size just before it, so "trade bigger than the displayed size" can be counted. Refill/cancel detection needs MBO (paid; ATAS gets MBO only via Rithmic) | **Detection literature is about size, not price direction.** No study shows a profitable "follow the iceberg" rule. Feasibility study only |
| 5 | Stop runs / liquidity sweeps | Stop orders cluster beyond round numbers and cause **cascades: faster moves in the breakout direction**, lasting hours; take-profit clusters at round numbers cause short reversals (<30 min) (Osler 2005, NY Fed SR150; FX data) | "Flag the sweep, fade it with almost zero drawdown" (Osler's evidence points to *continuation* after stops trigger, not reversal) | **Untested** (T2 / H-SWEEP); marked "best free candidate" | Yes (QC NQ/ES minute, prior-day high/low) | **Best free test.** Pre-register both directions (continuation vs reclaim-reversal) |
| 6 | HFT spoofing | Spoofing in ES/NQ happens and is prosecuted: CFTC v. Falloon (2025, 400+ events, spoof:genuine 5:1, 6 % of spoof orders partly filled), Cox (2019), Belvedere ($1.1M, 2019; spoof orders opposite a genuine iceberg). Detection papers exist (mostly crypto L3 data) | "Filter out fake heat, keep only real walls" with screen data | Blocked (MBO) | **No.** Needs order-by-order adds/cancels with IDs. Snapshots every few seconds cannot separate a cancel from a fill | **Not testable at $0.** Practical takeaway: resting size can vanish, so trade executed volume, not displayed size (already NEXA policy) |

## 2. Idea 1 in detail: the 5-minute ORB (Zarattini & Aziz 2023, SSRN 4416622)
- **Rule:** direction of the first 5-min candle, enter 09:35 ET, stop at the other side of that candle, target 10R or exit at the close.
- **Paper:** QQQ 2016–2023, 24 % winners, +0.13R/trade, commission only (no spread/slippage), no out-of-sample period.
- **Independent replications (2026):**

| Replication | Market, period | Gross | Net / control | Verdict |
|---|---|---|---|---|
| KruegerAlgorithms | Index CFDs 2015–2026 | NQ +0.131R (paper reproduced) | NQ +0.002R net; 2015–17 negative everywhere | Net ≈ 0 |
| ripbacktest.com | **NQ futures** 2020–2026, $15.76 RT | +0.107R | +0.079R net, **but random-direction trades also made money** (rule at 79th percentile); ~10 trend days carry the result; 2026 losing | Buried |
| giovannibrusco (GitHub) | QQQ 2016–2023 | Sharpe 1.06 | ~2.2 ¢/share of slippage → zero; 2022 = 76 % of profit | Fragile |
| Mesfin, arXiv 2605.04004 | MNQ 2021–2025, 14 signal families | — | ORB long T = 0.88, year-unstable; **0 of 14 families passed** | Failed |

- **Reading:** the first candle carries a little directional information (~+0.1R vs random in several markets), but most of the profit is "big trend days pay a 10R target", which random directions also catch. It is regime-dependent (works in high-volatility years such as 2020 and 2022). This matches NEXA's own results.
- **Time-zone fact:** NY 09:30 = **21:30 MYT now** (US daylight time) and **22:30 MYT from 2026-11-02** (US clocks change 2026-11-01).

## 3. What can actually be done (proposals; each needs the user's approval and a pre-registration before any data is looked at)

| Priority | Test | Why | Data / cost | Pass bar |
|---|---|---|---|---|
| P1 | **H-SWEEP-NQ/ES**: prior-day high/low sweep ≥ k ticks; arm A = continuation (Osler), arm B = close back inside within m min, then fade (the video claim) | Untested, free, has a real mechanism (stop clusters) and a published direction | QC free, NQ + ES minute 2009–2026; hold-out 2023–2026 | Net ≥ +0.025R/trade (H-PROP-EV bar), beats a distance-matched placebo, stable by block |
| P2 | **H-ORB5-NQ**: the exact Zarattini 5-min rule on NQ 2009–2019 (a period no replication above covers) + random-direction placebo | Settles whether the first candle adds anything beyond "volatility pays 10R targets" | QC free | Beats ≥ 95 % of random-direction placebos *and* net ≥ +0.025R |
| P3 | **HYP-004 LVN speed** (descriptive, no trading): does price cross low-volume nodes faster than high-volume nodes, per σ? | Tests the core claim of idea 2 cheaply | QC minute volume-at-price proxy now; recorder footprint later | Pre-registered effect size; even a pass is only a context feature |
| P4 | **Iceberg feasibility** (descriptive): count trades larger than the displayed best size at an unchanged price, per session, on the VM recorder data | Shows whether delayed dxFeed tape is good enough for any iceberg work | Our recorder (free), after ≥ 10 sessions | Data-quality question only; no trading claim |
| — | Squeeze (idea 3) | Strong negative external evidence + 8E | — | Not proposed |
| — | Spoofing (idea 6) | Needs MBO; emulating it is illegal | — | Not proposed |

## 4. About the C# indicators in the request
- NEXA already shows several of these as **facts**: developing value area / POC, TTM squeeze state, footprint imbalance stacks, big trades, CVD (NEXA v3), plus the full recorder (v4).
- An opening-range box, LVN lines or an "iceberg candidate" dot can be added to NEXA in a few hours each. **They would be displays, not edges.** Building a "signal" before a test passes repeats the pattern behind every failure in the ledger ("looks good in examples, fails when made exact").

## 5. Claims in the request that the evidence does not support
- "Hit a $600 daily target in minutes" / "almost zero drawdown": no tested intraday rule in NEXA, the replications above or the MNQ study shows this. The ORB's real shape is ~24 % winners and long losing streaks.
- "The exact millisecond an iceberg absorbs retail": the delayed (15-min) feed and few-second DOM snapshots cannot do this; even with MBO the literature predicts iceberg *size*, not direction.
- "Institutions trade at exact times to capture retail liquidity": institutions trade at the open and close because liquidity and benchmark prices are there (closing prices for fund NAVs, VWAP benchmarks), not to target retail traders.

## Sources
- Zarattini & Aziz (2023), "Can Day Trading Really Be Profitable?", SSRN 4416622; Zarattini, Barbon & Aziz, SSRN 4729284 (stocks in play).
- KruegerAlgorithms (2026), ORB replication on five indices (PDF); ripbacktest.com (2026-10-17), 5-min ORB on NQ futures; github.com/giovannibrusco/zarattini-2023-orb-qqq.
- Mesfin (2026), arXiv 2605.04004, OHLCV intraday momentum in MNQ.
- Gao, Han, Li & Zhou (2018), "Market intraday momentum", JFE 129(2).
- Gerety & Mulherin (1992), JF, volume at the open and the close.
- Kavajecz & Odders-White (2004), "Technical analysis and liquidity provision", RFS 17(4).
- Cont, Kukanov & Stoikov (2013), "The price impact of order book events", JFEC.
- Girgin (2026), SSRN 7600800, Bollinger/TTM squeezes and volatility, S&P 500 2006–2025.
- Pardo & Pascual (2011), "On the hidden side of liquidity", EJF; Frey & Sandås (2017), "The impact of iceberg orders in limit order books", QJF; Zotikov & Antonov (2019), arXiv 1909.09495, CME iceberg detection.
- Osler (2005), "Stop-loss orders and price cascades in currency markets", JIMF 24(2) (NY Fed SR150).
- CFTC: Falloon/Flatiron order 25-07 (2025), Cox (2019), Belvedere (2019).

## 6. Test results (added 2026-10-21, same day; `validation/SWEEP_ORB5_LVN_REPORT.md`)
- **P1 H-SWEEP: REJECTED** on NQ and ES, both arms. Fading the sweep is the worst (−0.39R NQ, −0.31R ES).
- **P2 H-ORB5: REJECTED** on NQ (−0.20R) and ES (−0.18R) outside the paper's window.
- **P3 H-LVN-SPEED: INCONCLUSIVE.** Real but tiny: 2–3.5 % faster in thin zones.
- **P4 H-ICE-FEAS:** frozen; runs after 10 recorded sessions (≈ 2026-11-04).
- Common cause: small stops, so a fixed round-trip cost is 0.2–0.4R per trade, larger than any gross edge found (≤ +0.09R).
