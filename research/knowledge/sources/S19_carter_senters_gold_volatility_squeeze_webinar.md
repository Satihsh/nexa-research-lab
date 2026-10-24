# S19: John Carter & Hubert Senters (TradeTheMarkets.com), "How to Take Advantage of Volatility in the Gold Market"
**File:** `Volatility_in_Gold_Markets_012110_UK.pdf`. 41 slides. An Interactive Brokers / CME Group webinar; the file name dates it 21 Jan 2010.

| Field | Value |
|---|---|
| **Source type** | Industry / practitioner. Webinar slides with a vendor promotion (TTM indicators, trading room). |
| **Evidence status** | **Unverified claim.** Illustrative intraday charts (YM, GC 5-minute; ES / GC 60-minute and daily). No statistics. |
| **Processing** | Text of all 41 slides read. **21 of the 41 pages are image-dominant.** Rendered and inspected: pp. 7, 12, 21, 22, 27, 29, 30, 32.<br>Pp. 5–6 and 17–20 are CME product and contract-spec screenshots or logos (text read); pp. 34 and 37–40 are promotional. |

## Content (SOURCE)
1. **Cross-asset volatility (p. 7 chart):**
   - 20-day historical volatility of gold, crude oil, S&P 500 and DJIA, Dec-2004 to Dec-2009.
   - Gold mostly ~10–40 %; it spiked in the autumn-2008 crisis but much less than crude (~130 %) or equities (~80 %).
   - "Volatility travels from market to market… follow the volatility" (p. 11).
2. **Contract economics (pp. 21–23)**, COMEX GC full contract, $100 per $1/oz:
   - H1 ATR(14) ≈ 4.29 points ≈ $429 per contract (Jan 2010, price ≈ $1,130), vs ES ≈ 4 points ≈ $200;
   - Mar-2009 → Jan-2010 GC range 282 points = $28,200 per contract.
   - **INFERENCE:** gold's H1 ATR was ≈ 0.38 % of price then. NEXA's 2025–26 XAU H1 ATR median of $18.88 at ~$4,000+ is ≈ 0.4–0.5 %, a similar relative scale.
3. **The Squeeze (TTM Squeeze), the source of the BB-inside-KC definition (pp. 25–32)**
   - **Squeeze ON:** the Bollinger Bands are *inside* the Keltner Channels, signalling low volatility.
   - **Fire:** the BBs come back outside the KCs; "volatility is increasing and it's time to place a trade".
   - **Parameters, read from the indicator label on the rendered p. 30 / p. 32:**
     - `TTM Squeeze(Close, 1, "Futures=1 Stocks=2 FX=3", 20, 1.5, 2, …)`, i.e. length 20, KC 1.5 × ATR and BB 2σ.
     - This matches NEXA 8E's BB(20, 2σ) inside KC(20, 1.5·ATR).
   - **Direction:** taken from a **momentum histogram** (blue above zero = long, red below = short). The chart on p. 29 also shows Momentum(Close, 12).
   - Squeeze state is shown as red dots (on) and green dots (off). Slide p. 30: "One red dot can be just as powerful as 20 red dots" (an assertion).
   - **Time frames:** 5-minute (day trading), 60-minute and daily (swing), weekly (position).
4. **Exits (pp. 31–33):** close one-third of the position on each of three signals, and move the stop to breakeven after the first.
   1. Loss of momentum: 2 darker histogram bars.
   2. TTM trend change: 2 bars of the opposite colour.
   3. 8/21 EMA cross.

   Stated reason: "trailing stops often get hit BEFORE the trend has run its course" (assertion).
5. **Psychology (pp. 35–37):**
   - avoid greed and euphoria;
   - do not double up; this is likened to blackjack, where it "only has to not work once" (a risk-of-ruin intuition);
   - use limit orders. "Limit orders = planned; market orders = impulse."

## Critical assessment
- **Mechanism:** the same as S09 (volatility compression → expansion). It is a stylised-fact basis for **volatility** forecasting, not direction.
- The direction comes from a short momentum oscillator. **INFERENCE:** it is therefore a momentum-breakout system with a volatility-regime precondition.
- **No backtest, no base rates, hand-picked examples.**
- The claim that futures have "no gap risk" in near-24-hour markets is **incorrect as stated**: futures gap at session breaks and weekends.
- **The "limit orders" advice ignores adverse selection.** INFERENCE grounded in S06 / S10: limit orders fill preferentially when price moves against you.

## NEXA relevance
- **Provenance:** this is the origin of 8E's E1 Squeeze definition.
  - NEXA DEV: E1 is **UNPROVEN** (selects better than random in 51 % of bases; expectancy −0.31R; incremental AUC −0.001).
  - The 8E implementation used "fired within 5 bars" and **no momentum-histogram direction**. Direction came from the Donchian breakout.
  - **Backlog hypothesis:** the Carter-style fire with momentum-histogram direction, which was not tested in 8E.
- **Gold volatility is lower than crude and equities in crises (2008)**, a single-episode observation. It is relevant to XAU stop sizing and regime modelling.
- **The scaled-exit (1/3) idea is testable.** Partial exits change the payoff distribution. NEXA's simulator currently uses a single exit.

**Cross-references:** S09 Bollinger (BandWidth squeeze); S04 / S18 (volatility clustering and roughness); S02 / S03 (momentum); S01 (FX practitioner); S22 (151 Strategies).
