# S09: John Bollinger, "Bollinger On Bollinger Bands": Methods I–IV (web excerpt, bbands.com)
**File:** `Bollinger On Bollinger Bands.pdf`. 14 pp. It excerpts chapters 16, 19 and 20 of the 2001 book, plus the website's "Method IV".

| Field | Value |
|---|---|
| **Source type** | Industry / practitioner (the originator of Bollinger Bands) |
| **Evidence status** | **Unverified claim** for profitability: no statistics, only illustrative charts. The definitions are established. |
| **Processing** | All 14 pages read. The charts (Figs 16.1–20.4) are illustrations; pp. 5 and 8 inspected visually. They show a price panel with %b, MFI and band panels and no quantitative results. |

## Definitions (standard; implied in the text)
- **Bands:** middle = SMA_n(close); upper/lower = SMA_n ± k·σ_n. Defaults n = 20, k = 2. Short-term variant n = 15, k = 1.5 (p. 3).
- **%b** = (close − lower) / (upper − lower). %b = 1 at the upper band and 0 at the lower band (p. 8).
- **BandWidth** = (upper − lower) / middle. The formula is not printed in this excerpt; it is the standard BB definition.
- **The Squeeze:** BandWidth at a low over a look-back, **default 6 months** (p. 3). A longer look-back gives "more explosive" but fewer setups.

## Method I: volatility breakout (Ch. 16)
- **Precondition:** a Squeeze.
- **Entry:** with the first breakout beyond a band.
- **Exit:** Wilder's Parabolic SAR, starting below the breakout formation, or a tag of the opposite band (longer trades).
- **"Head fake":**
  - after a Squeeze, price often feints in the wrong direction first (a band tag), then makes the real move;
  - the discretionary variant trades half a position against the feint and adds on the breakout.
- **Volume-indicator confirmation:** Intraday Intensity, Accumulation/Distribution, MFI.
- **SOURCE (anecdote):** Bruce Babcock, after reviewing many systems, preferred volatility breakout. No data.

## Method II: trend following (Ch. 19)
- **Buy** if %b > 0.8 **and** MFI(10) > 80; **sell** symmetrically.
- **Parameter rule of thumb:** indicator length ≈ half the band period (an adaptation of cycle analysis).
- **Variants:** substitute VW-MACD for MFI; buy the first pullback after the alert to reduce late entry.
- The "Rational Analysis" fundamental pre-screen is out of scope.

## Method III: reversals (Ch. 20)
**Classic background**
- DJIA within its 21-day MA ± 4 % envelopes.
- Sell on an upper-envelope tag with a negative breadth oscillator (A−D or up-volume − down-volume); buy on the reverse.

**Bollinger's modification**
- Oscillator = a "departure graph" (21-period average minus 100-period average) of A−D and of up-volume − down-volume. Equivalent to MACD(21, 100, 9) on breadth.
- This normalises for long-term bias.

**Patterns**
- **W-bottom:** the retest has higher %b than the first low (a relative W4), confirmed by MFI or VWMACD. Buy the first strong up day.
- **Tops:** three or more pushes, with %b and A/D lower on each push.

## Method IV: confirmed breakouts (website)
- **Day 1:** close inside the band, with BandWidth within 25 % of its 6-month low.
- **Day 2:** close outside the band.
- **Day 3:** close beyond the Day-2 close = a confirmed signal.

## Principles and critical assessment
- **Mechanism, SOURCE + INFERENCE:** volatility clustering and mean reversion of volatility.
  - Low BandWidth ⇒ volatility tends to expand later. This is a well-known stylised fact (cf. the GARCH and rough-volatility sources S04 and S18).
  - Expansion **does not predict direction**. Bollinger himself requires a breakout and confirmation for direction.
- **Self-acknowledged problems:** head fakes (false first breakouts) and late entry.
- **SOURCE: no backtests are given.** Bollinger repeatedly urges parameter customisation, which raises overfitting risk if done on the same data used to evaluate.
- **The volume indicators assume real volume.** NEXA has **only quote counts** (`tick_volume`), so MFI, A/D and Intraday Intensity become quote-activity proxies. The same caveat applies as for the OFI proxy (NEXA tick audit).

## NEXA relevance
- **The 8E "Squeeze" engine is a different definition:** BB(20, 2) inside KC(20, 1.5·ATR) (the Carter-style TTM squeeze), with a fired-within-5-bars filter.
  - Bollinger's own definition is BandWidth at a 6-month low.
  - NEXA DEV result: Squeeze **UNPROVEN** (it selects better than random in 51 % of bases; it is not net-positive).
- **Untested variants for the backlog:**
  - BandWidth-percentile squeeze (6-month look-back);
  - the Method IV 3-day confirmed breakout;
  - the head-fake (first-tag reversal) entry.
- **Information content:** volatility state is well supported as a *volatility* predictor, weak as a *direction* predictor.

**Cross-references:** S04 / S18 (volatility persistence), S22 (151 Strategies: channel/breakout definitions), S17 TD (exhaustion), S02 (MACD), S07 (TDI uses volatility bands).
