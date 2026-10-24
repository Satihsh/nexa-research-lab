# User links checked 2026-10-15: strategy marketplaces, research DBs, MCP trading tools

**Constraints applied:** $0 budget, Mac, ATAS, the user clicks orders; the frozen H-ORB30L research path.

| Link | What it is (from its own pages, 2026-10-15) | Cost | Use for NEXA |
|---|---|---|---|
| **collective2.com/build-with-c2** + agents.md | Strategy marketplace with an HTTP API built for AI agents: search and screen strategies, subscribe, autotrade on/off. The human approves price, broker agreement and identity. `SearchHistoricalStrategies` with `Graveyard:true` includes **dead / killed strategies (survivorship-bias-free)**. Publishing a strategy needs a paid manager plan. | Free key; subscriptions and manager plan paid | **Research only, $0:** count how many futures strategies survive and profit over time (a reality check on "top traders"). **Not** for subscribing or publishing now. |
| **quantpedia.com** | An encyclopedia of strategies extracted from academic papers. ~70 free strategies; 900+ in paid Premium; Pro / API paid. | Free tier (sign-up) | **Idea source** in the Matteo Conti / SSRN style. Free entries only. |
| **trendfollowing.com** (Michael Covel) | Trend-following education, books, podcast and paid systems. Explicitly "no day trading, no 1-hour bars". | Products paid; podcast free | **Low fit:** long-horizon, multi-market, deep drawdowns; NEXA already closed G10 trend+carry (LC-3). Not an income-per-evening fit. |
| **ionanalytics.com/barclayhedge** | Hedge-fund / CTA databases and 50+ indices (Barclay CTA Index, BTOP50…). Free registration for some views. | Databases paid; index pages viewable | **Benchmark realism:** what professional CTAs actually earn year to year. |
| **autumngold.com** | Independent CTA / managed-futures rankings since 1994, plus World Cup Advisor (live copy-trading of contest traders). | $295/yr; WCA $300 subscriptions | **Reality check only.** Even the featured contest traders show deep drawdowns (e.g. 211 % return with a −35.7 % drawdown; another −36.7 % YTD). |
| **crosstrade.io MCP guide** | A hosted MCP bridge to **NinjaTrader 8** (Windows) + Tradovate. Read scope and trade scope; MCP only on the Elite tier. It notes Apex prohibits automation. | Elite tier paid | **Not usable:** NT8 is Windows, we use ATAS on Mac, and it is paid. Its safety pattern (read state → restate → human confirms → verify) matches NEXA's rules. |
| **github …/servers/issues/3904 (BotSpot)** | A request to list BotSpot (Lumibot-based AI strategy generation + backtest + live deploy, 10+ brokers). **Closed by the MCP maintainers:** the repo is not a registry. | Free tier: 2 generations + 30 min backtesting per month | Unverified data source for futures; AI-generated strategies = the overfitting anti-pattern NEXA avoids. **Not recommended.** |
| **mcpservers.org … tv-pinescript-backtest-engine-mcp** | Remote MCP running Pine Script backtests. **Binance Futures tickers only, max 1,440 candles.** | API key; beta | **Not usable** for NQ / MNQ (crypto only; 1,440 candles is about 1 day of M1). |

**Net:**
- None of these gives free historical NQ data or a free way to run the H-ORB30L out-of-sample test.
- The two useful free items are research aids: Collective2's graveyard-inclusive statistics and Quantpedia's free entries.

## Batch 2 (same day): backtesting research + 3 Algovibes videos

| Link | Content (own words, 2026-10-15) | Use for NEXA |
|---|---|---|
| IBKR Campus / ORATS "180 million options backtests" (2024) | **Options** backtest practice: use quotes 14 minutes before the close (not the closing print); slippage 75 % of the bid-ask width for single legs, 56 % for 4-leg spreads; avoid overfitting (look for neighbourhoods of good results, not the single best); path dependency; notional vs margin return. | Principles agree with NEXA's discipline. **Options are not our path** (no options data, small account). |
| paperswithbacktest.com/strategies | ~4,300 backtests of published-paper strategies. **Median Sharpe 0.32; 33 % above 0.5.** A "Still working?" view shows post-publication decay. Search and filters need a subscription. | **Free research aid:** base rates for published edges and their decay. Relevant entries: "Overnight-Intraday Return Gap and the Retail Ebb and Flow" (Ahn et al. 2025); "Intraday time series reversal" (2025, 80 % max DD). |
| sentimentrader.com/trading-tools | Paid no-code backtester on 30,000+ sentiment / trend series; daily / weekly / monthly only. | **Not usable:** paid; no intraday futures. |
| SRC-YT-088 `XFocx6K4Ers` Algovibes "I Tested 100,000 Trading Strategies" (2026-05-19) | 131,441 walk-forward backtests (62 strategies × 31 assets, daily bars). 917 promising in-sample → 358 survived walk-forward → **65 after 6 filters**. Mean reversion and volume strategies survived most (~38 %); trend following least (18 %). Realistic out-of-sample Sharpe for a real edge on daily bars: 0.5–1.5. | Independent confirmation of NEXA's experience: most edges die out of sample. |
| SRC-YT-089 `o0INvuabn7I` Algovibes "133,461 Backtests" (2026-07-13) | The same 65 re-checked: the expected maximum Sharpe from luck alone ≈ 2.32, and none beat it. **Deflated Sharpe ≥ 0.95: 0 of 133,461** (best 12.5 %). Stop-loss / trailing stops cut the average max drawdown from 30 % to 21 % but the Sharpe fell from +0.04 to −0.06: **"stops change how you lose, not whether you have an edge."** | Same DSR test NEXA uses. Explains why H-ORB30L's DSR failure matters. |
| SRC-YT-090 `6B3ibD1T0KQ` Algovibes "6.7 Million Trading Strategies" (2026-08-29) | 6,720,225 backtests over 11 studies (stocks, crypto, FX; MAs, RSI, breakouts, candles, ML, AI-generated, regime switching). After costs + luck correction: 2 survivors out of 4,092,971 in five rigorous studies (one stock, a 3 % dip buy on 5-min, about 2.5 days of out-of-sample evidence). **Buy-and-hold (beta) beat everything.** Trend following was the "best of the rest" (2/3 of profitable portfolio pieces) but 0 of 2,400 trend setups passed formally. A day-trading strategy built exactly as its creator describes: 0 of 640 beat holding the currency. | Strongest external confirmation of NEXA's "beta control" check (N2) and of the deflated-Sharpe gate. |

**Net:** the user's 6 links contain no new free data or tool for the H-ORB30L out-of-sample test. The 3 videos are independent large-scale evidence that agrees with NEXA's own results: almost nothing survives proper out-of-sample + luck correction; beating buy-and-hold is rare; risk management is not an edge.

## Batch 3: atilaahmettaner/tradingview-mcp (mcpservers.org listing, v0.9.0, 5.1k GitHub stars)

- **What it is:** open source (MIT), free if self-hosted (`pip install tradingview-mcp-server`); a hosted version is $9–29/month.
- **Not affiliated with TradingView.** It uses public endpoints (Yahoo Finance, the TradingView screener / TA ratings) and needs no account.
- **Tools (39):** screeners, technical "BUY/SELL" ratings, Reddit sentiment, RSS news, and a backtester limited to **9 fixed indicator strategies (RSI, Bollinger, MACD, EMA cross, Supertrend, Donchian, …) on daily / 1-hour bars**, plus a simple train/test walk-forward.
- **Its own README examples report "100 % win rate | 2 trades"** — statistically meaningless; the overfitting pattern the Algovibes studies and NEXA's DSR gate reject.
- **Security warning in its README:** malicious copies on npm (MAL-2026-16390); only the PyPI package / the original repo are official.
- TradingView's own official MCP (public beta since 2026-09-16) requires a paid TradingView plan (Essential+).

**Verdict for NEXA:**
- It cannot run the frozen H-ORB30L rule: there is no custom rule logic and no 1-minute NQ history. Yahoo's 1-minute history covers only ~7 days.
- Installing it would need user approval (package install).
- Not recommended for strategy decisions. At most an optional quick market-snapshot tool.

## Batch 4: paperswithbacktest.com/strategies/dataset + github.com/cloudquantai

**Papers With Backtest dataset card (recounted hourly; read 2026-10-15):**
- 4,312 papers, each re-run as Python on common data from 1990, with a split at the publication date.
- **Median Sharpe 0.32** (quartiles 0.04 / 0.57). Only 101 of 4,312 have Sharpe > 1 (**97.7 % below 1**).
- Median annual return 1.8 % at 9.1 % volatility. Median max drawdown 37 %; 29 % go deeper than −50 %.
- **Publication decay / regression to the mean:**
  - the top in-sample decile goes from 0.95 to 0.85 out of sample;
  - the in-sample vs out-of-sample rank correlation is only 0.52;
  - their reconstruction of McLean & Pontiff (2016) goes from 0.47 before publication to −0.08 after.
- **Diversification:**
  - an equal-weight book of all ~5,200 strategies has Sharpe 0.83 at 3.6 % volatility (no costs);
  - 680 strategies behave like only ~12 independent bets (participation ratio 11.9; PC1 = 28 % ≈ market beta).
- **Caveats they publish themselves:** costs are each paper's own assumption (often gross); today's universes (survivorship); overlapping out-of-sample windows.
- **Free access:** search / API filter free; one credit per record. The open repo github.com/paperswithbacktest/papers holds ~3,846 papers as README + strategy.py + paper.pdf. Nearly all use **daily or slower** data.
- **NEXA use:** base rates and an idea source (daily / monthly strategies; equities 87 %). It contains no intraday NQ data for the H-ORB30L out-of-sample test.

**CloudQuant (github.com/cloudquantai):**
- CloudQuant LLC, Chicago: "free cloud-based strategy backtesting engine… you create it, we back it" (an incubator / capital-allocation model).
- Its public repos are small samples (TA-Lib, breakout, mean reversion, sentiment, ZigZag) for **US stocks** on app.cloudquant.com; 67 followers; the repos look dated. Current platform status and futures coverage are not verified.
- **NEXA use:** none now. It is not a source of NQ futures data, and the incubator terms would need reading before any strategy were shared.

## QuantConnect Strategies marketplace (quantconnect.com/strategies), checked 2026-10-15 via the in-app browser (signed in)

- **What it is:** community-published algorithms you can clone into your account. They are ranked on a leaderboard by **"OOS 3M return / OOS 3M Sharpe"**, meaning only about 3 months of live-style tracking since publication. The top 10 are mostly large-cap stock momentum, risk parity and crypto, with 3-month Sharpe 4–8. Three months is far too short to mean anything (Sharpe standard error ≈ 2 over 3 months). **This is not evidence of an edge.** The backtests shown are in-sample, run by each author.
- **Searching "opening range" finds 3 strategies:**
  - **#374 "MNQ Opening Range Breakout Trend-Following" (Arbaz Rana, Mar 2026).**
    - Rules: 9:30–9:45 opening range; long/short on a close beyond it, filtered by the 20-day EMA; entries 9:50–15:30, up to 3 a day; range-size filter; stop = min(0.5×ATR14, range); 2R target; trail after +1.5R; flat before the close.
    - Results: **5-year CAGR 0.57%, 1-year Sharpe −7.95, 3-month return −0.51%**, equity roughly flat 2022–2026.
    - So the closest public relative of our rule (MNQ ORB with a bracket) shows **no edge** on QuantConnect's own data. This agrees with our H-ORB30L "INCONCLUSIVE, small" result. 1,679 clones.
  - **#551 "TQQQ Opening Momentum Breakout" (Jun 2026).**
    - Rules: first 5-minute candle sets the direction; stop at the range midpoint; 10R target; move to breakeven at 6R; risk 0.6% per trade; leverage up to 4×.
    - Results: in-sample 2022–26 CAGR 30%, drawdown 35%; 3-month OOS +11.6%; 1-year Sharpe 0.31.
    - It is a variant of the Zarattini-style 5-minute ORB (our H-ORB-1 family, INCONCLUSIVE).
    - **Red flag:** the page's traded-asset panel lists **TSLA**, not TQQQ, so the published code may not match the description.
  - **"MNQ Opening Range Breakout Momentum":** no statistics published.
- **Use for NEXA:** none as a signal source; it is cross-check only. Cloning does not get around the card-verification gate on backtests (D-10). No new hypothesis is registered from it.

## Oxford Capital Strategies (oxfordstrat.com), checked 2026-10-16

- **Products:** ALPHA20 (fractals, "self-adaptive") and DELTA20 (volatility / signal-to-noise patterns) are proprietary paid systems, plus paid research services. **Not considered:** the user has a no-spending rule, the systems are closed, and there is no verifiable track record.
- **Resources (free):** about 100 "public-domain" strategy reviews (Crabel ORB / NR7, Turtle Soup, Hikkake, Smash Day, Livermore, Wyckoff, MACD / RSI / Bollinger and others), plus a few data notes (global correlations 1995–2014, volatility clustering).
  - Static fetchers hit reCAPTCHA; the pages are readable in the in-app browser.
- **Method** (identical on every page):
  - 42 US futures, all sectors, **daily bars**, 1980 → 2011–2015, MATLAB;
  - 1 % fixed-fractional sizing, ATR(20)×6 stop;
  - 2-parameter sensitivity heat maps shown at $0 and at $50 round-turn costs.
  - Results appear only as charts (no numbers in the text). **No out-of-sample split.** The rating A–D is the authors' judgement.
- **Ratings:** no strategy is rated **A**. Only 6 are rated **B**: Gap Pattern Type A, Ross Hook with filter ×2, Smash Day Type B ×2.
  - Most are C or D. **Crabel's Opening Range Breakout is rated D**; the weekly ORB and the counter-trend ORBP are also D.
  - The B entries share one feature: **a trend / channel filter plus multi-day holding**. The setups are daily momentum, effectively trend-following.
- **Use for NEXA:**
  - Independent corroboration that **ORB-type rules do not survive costs**, which agrees with H-ORB30L FAILED OOS on 2026-10-16.
  - The B-rated ideas are **daily, multi-day-hold, diversified futures trend-following**. That conflicts with the user's constraints (evening-only, no overnight holds for prop accounts), and the gate already closed G10 trend+carry for FX (LC-3).
  - **No new hypothesis registered.** If the user ever accepts overnight multi-day holds, "diversified daily trend-following with a channel filter" is the family with the most external support. It would need its own pre-registration plus a QuantConnect OOS test.

## Google AI Mode shares from the user, checked 2026-10-16

- **"scalping meaning"** (share yRsGQj4…): Google returned a bot-check CAPTCHA, so it was **not read** (Claude does not solve CAPTCHAs).
- **"topstep prop firm"** (share h0Z602h7…): read in full. Key claims were **verified against Topstep's own help center** (help.topstep.com, 2026):
  - **Pricing:**
    - Trading Combine $50K / $100K / $150K at **$49 / $99 / $199 a month (Standard) plus a $149 activation fee on passing**, or **$95 / $149 / $229 a month with no activation fee**.
    - A Reset costs one month's fee.
    - Back2Funded costs $599 / $699 / $829.
    - Live Funded data fees are about $133 per exchange per month.
  - **Rules:**
    - Profit target $3K / $6K / $9K. **Trailing end-of-day Maximum Loss Limit $2K / $3K / $4.5K**, with intraday breach including unrealised P&L = instant liquidation.
    - Consistency: best day < 55 % of the target (Combine).
    - **All positions flat by 3:10 PM CT.**
    - Max 5 minis / 50 micros (50K).
  - **Payouts (XFA):** Standard = 5 winning days ≥ $150, up to 50 % of the balance, capped at $5K. Consistency = 3+ days at 40 %, capped at $6K. 90/10 split. The XFA is **simulated**; Live is at the firm's discretion.
  - **Automation:** **custom bots are allowed** through the TopstepX / ProjectX API (**billed separately**; not on Live accounts). **HFT is banned**, and so is "scalping algorithms designed to exploit unrealistic SIM fills" and tight brackets or auto-breakeven used to exploit SIM fills.
  - **Topstep's own statistic:** "Over 63 % of traders have lost an account in a single day."
- **NEXA fit:** the intraday, flat-by-close format and the NY-open evening window (MYT) fit the user's constraints, and Topstep, unlike Apex, allows bots.
  - **But no NEXA rule has survived out-of-sample testing** (H-ORB30L FAILED 2026-10-16; IVB1, IM and OFC1 failed or had no edge). Paying fees now would mean paying to trade a rule with negative expectancy.
  - **Hold** until a rule passes a pre-registered QuantConnect OOS test. Then estimate P(pass the Combine) by bootstrap from the OOS trade list against the trailing-MLL rules before spending anything.

## User PDF "ATAS_Trading_Chat_History.pdf" (an AI chat: scalping, ATAS, prop firms, IBKR), fact-checked 2026-10-16

| Claim in the chat | Check against official sources (2026) | Status |
|---|---|---|
| ATAS is software and does not provide prop accounts | ATAS connects to prop firms' feeds | ✓ |
| **Topstep "100 % allowed", supports ATAS via Rithmic** | Topstep moved new Combines and Resets to its own **ProjectX / TopstepX** feed from **Aug 2025**, dropping Rithmic, Tradovate and CQG (ATAS feedback board; atas.net/atasfortopsteptrader). ATAS promised a ProjectX connection "Autumn 2025"; **Topstep's help center in 2026 documents Quantower via ProjectX, not ATAS**. Bots are allowed only through the paid TopstepX / ProjectX API (not on Live). | **Outdated / unverified** |
| **TradeDay permits ATS, compatible via Rithmic** | TradeDay supports ATAS for *manual* trading, but **automated systems must run on NinjaTrader, Tradovate, TradingView, Jigsaw or Quantower — not ATAS**. No platform APIs are given to traders. Third-party bots are forbidden; > 200 trades a day is forbidden; "software, AI … unfair advantage" is prohibited. | **Wrong for an ATAS C# bot** |
| MyFundedFutures allows automation, bans HFT | The MFFU Fair Play page allows the trader's *own* automated strategies, provided they do not exploit sim fills. No HFT, no copy trading, tier-1 news trading restricted, tight-bracket sim exploits banned. Third-party summaries add "active supervision required, ≤ 200 trades / day". The ATAS connection is reported by third parties (Rithmic). | ✓ with conditions |
| Apex bans fully automated trading | Matches the March 2026 finding (sabrtrader-due-diligence) | ✓ |
| "Busha Capital" permits automation | No evidence found | **Unverified (likely invented)** |
| Topstep is not a broker; clears via Dorman / Phillip | It is a prop firm; the funded XFA is simulated, Live is at the firm's discretion | ✓ (clearing names unverified) |
| IBKR: 100–250 ms snapshot data, so slow for scalping | Generally true of IBKR aggregated market data | ✓ broadly; **IBKR is NOT a Topstep platform** (Topstep's "not supported" list) |
| Micro futures: "start with $100–500" | At NQ ORB-type stops (median R ≈ 119 pts ≈ $238 per MNQ), a few losses wipe out $500 | **Misleading** |
| An LLM in the loop is too slow for scalping → day / swing trading instead | Latency point correct; the VWAP / VAH / POC suggestions were tested: H-VAR found **no evidence**, ORB family FAILED OOS | Untested advice |

**NEXA stance:**
- No automated or live trading until a rule passes a pre-registered OOS test.
- The user's chat line "I connected Claude with ATAS using C#" has **not been verified or built by NEXA**. Any such bridge must sit behind the frozen NEXA risk gate and run on demo first.
