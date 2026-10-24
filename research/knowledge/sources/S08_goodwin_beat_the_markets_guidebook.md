# S08: Jarrod Goodwin, "Beat the Markets Strategy Guidebook" (thetransparenttrader.com)
**File:** `Beat-the-Markets-Strategy-Guidebook.pdf`. 22 pp.

| Field | Value |
|---|---|
| **Source type** | Industry / practitioner. Retail education with course marketing; the author states he is "not regulated". |
| **Evidence status** | **Unverified claim.** Single-path MultiCharts backtests on Oanda data, **with no spread, commission or slippage** (stated explicitly on p. 14 for strategy 2). The filters were added after viewing the results. |
| **Processing** | All 22 pages read. The performance screenshots are images; pp. 6, 14, 16 and 21 were inspected visually. Pp. 5, 12, 13 and 15 hold equity curves; the caption text was read. |

## Strategy 1: EUR/USD outside daily bar (from Larry Williams, 1999)
**Rules** (daily bars, New York 17:00 close, 5 bars per week)
- **Setup:** an outside bar (High > previous High and Low < previous Low) whose Close < previous Low.
- **Entry:** long at the next open.
- **Stop:** 200 pips.
- **Exit:** at the first daily close in profit, exit at the next open; otherwise hold until the stop.

**Results** (p. 6, read visually; 1 lot fixed; 2010–2019)

| Metric | Value |
|---|---|
| Trades | 88, all long |
| Win rate | 87.5 % |
| Average win | $530.22 |
| Average loss | −$1,822.18 |
| **Win/loss ratio** | **0.29** |
| Average trade | **$236.17 ≈ 2.4 pips** |
| Largest loss | −$2,024 |
| Losing year | 2014: −$2,941 |
| 100 %-winning years | 2015, 2017, 2018, 2019 (5–9 trades each) |

**INFERENCE: this is a negatively-skewed, short-volatility payoff.**
- It takes small profits quickly and holds losers to a wide stop.
- A high hit rate is structurally guaranteed by the exit asymmetry, not by predictive skill.
- At 2.4 pips per trade gross, with **zero cost**, a ~1-pip round-trip cost would remove ~40 % of the edge.
- n = 88 over 10 years is too few for confidence. The evidence is weak.
- It links to S02's "win rate is meaningless" point (Potters & Bouchaud).

## Strategy 2: USD/JPY "Kangaroo Tail" breakout (adapted from Elder)
**Rules**
- **Pattern:** bar 2's Low < Low of bars 1 and 3 (a 3-bar fractal low).
- **Entry:** buy-stop at bar 3's High; stop at bar 3's Low. Shorts mirror this.
- **Exit:** end of day (< 24 h).

**Results (Oanda, 2008–2020, 1 lot)**
- **Base strategy:** average trade ¥4,430.81 ≈ 4.4 pips, *"does not include any commissions, spreads or slippage"* (p. 14).
- **Modified version:** skip if Close₃ moved > 0.5 % vs Close₂; skip Fridays (pp. 14–15).
  - 526 trades, 52.47 % win, P/L ratio 1.45, average trade ¥8,887 ≈ 8.9 pips (p. 16, visual).
  - 2 losing years (2015, 2010).
  - A 2009 profit of 63.33 % on the notional base dominates.
- **INFERENCE: the filters were chosen in-sample after seeing the results.** This is classic data snooping. There is no out-of-sample period for strategy 2.

## Strategy 3: USD/JPY 2-hour session breakout
**Rules**
- Trade window 21:30–23:30 New York.
- **Filter:** the previous daily candle's direction (white ⇒ longs only; black ⇒ shorts only).
- **Entry:** stop order at the session high (or low) of 17:00–21:30.
- **Stop:** 150 pips. **Exit:** about 16:50, before the session end.

**Results**
- Developed on 2008–2016, with "out of sample" 2016–2018. The ranges **overlap in 2016**.
- No losing years 2008–2018. Annual profit ¥158k–¥1,076k on 1 lot.
- 2008 was +534.8 % because the base was tiny (p. 21, visual).
- The cost treatment is not stated (UNKNOWN). It is presumably cost-free like strategy 2.

## Principles and critical assessment
- **Patterns as ideas:** outside-bar reversal (short-term mean reversion after an exhaustion bar), 3-bar fractal breakout, and a session-range breakout with a daily-direction filter.
- **Evidence weaknesses:**
  - no costs;
  - one data vendor;
  - optimisation by eye;
  - fixed-lot P&L (not risk-normalised);
  - no significance tests;
  - selection bias: these are "favourites of my students", chosen from a larger set.
- **Look-ahead risk:** Strategy 1 enters at the next open after the 17:00 close, which is fine. Strategy 3 uses the 17:00–21:30 range, known at 21:30, which is fine.

## NEXA relevance
- **Hypotheses (low prior):**
  - an outside-bar exhaustion reversal on the daily bar;
  - a fractal-low breakout;
  - an Asian-session-range breakout with a daily-candle direction filter (NY 21:30–23:30 = 01:30–03:30 UTC in summer).
- All are testable on NEXA's M1 data with real costs. NEXA's V2 already contains an "XAU session breakout" family and an "Asian MR" family.
- **Teaching value:** a concrete example of the win-rate illusion and of cost-free backtest inflation.

**Cross-references:** S02 (win rate), S07, S01 (sessions), S12 / S16 / S20 (other backtest papers with weak validation).
