# What the NEXA recorder shows so far: NQ and ES, 21–22 October 2026 (exploratory decode)

**Status: exploratory, not a test.**
- Two complete US sessions only (09:30–16:00 ET, by exchange time; the feed is dxFeed 15-minute delayed).
- Nothing here is evidence of an edge, and no trial is counted. Any idea below would need its own pre-registration and far more days.
- **Not computed:** the iceberg / refill statistic (trades larger than the displayed size). That belongs to the pre-registered H-ICE-FEAS and stays sealed until its run (≈ 2026-11-04).
- Code: `recorder_explore.py`; numbers: `recorder_explore_2026-10-21_22.json`.

## 1. The two days
| | NQ 10-21 | NQ 10-22 | ES 10-21 | ES 10-22 |
|---|---|---|---|---|
| Open → close | 29,874 → 29,998 (+124) | 29,516 → 29,145 (−371) | 7,779 → 7,799 (+20) | 7,729 → 7,706 (−23) |
| Range | 342 pts | 562 pts | 61 pts | 66 pts |
| Low / high time (ET) | low 09:43, high 13:21 | high 10:03, low 15:47 | low 10:12, high 14:16 | high 10:03, low 15:02 |
| Close position in day range | 66 % | 20 % | 78 % | 45 % |
| First-hour range ÷ day range | 48 % | 44 % | 49 % | 70 % |
| Trades / contracts | 258k / 448k | 343k / 600k | 222k / 1.27M | 313k / 1.73M |
| Net aggressor delta | **−1,979** (price up) | **+2,838** (price down) | +11,023 | +15,852 (price down) |

**Reading:**
- 10-21: an early sell-off that bottomed in the first 15–45 minutes, then a steady climb into the afternoon. A "fake-out then reverse" open.
- 10-22: the high was set in the first 35 minutes, then a trend day down into the close, with the range more than double the first hour.
- **Day shape repeats a known fact:** both days extended far beyond the first-hour range. The first hour gave 44–49 % of the NQ range, so the open is not the whole story.

## 2. When the market moves (clearest pattern, and well known)
Average 1-minute volume and size of move, NQ, by half hour (ET):

| ET | 09:30 | 10:00 | 10:30 | 11:00 | 11:30 | 12:00 | 12:30 | 13:00 | 13:30 | 14:00 | 14:30 | 15:00 | 15:30 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Contracts / min | 2,712 | 2,009 | 1,834 | 1,468 | 1,193 | 789 | 1,234 | 858 | **640** | 801 | 940 | 1,299 | 1,728 |
| Avg 1-min move (pts) | **19.5** | 14.3 | 11.5 | 10.3 | 7.8 | 8.0 | 9.9 | 6.6 | **5.8** | 6.4 | 6.6 | 10.7 | 9.2 |

- **A "U" shape.** The first 30 minutes move NQ about **3.4× more per minute** than 13:30–14:00 (the quietest half hour). Activity picks up again into 15:00–16:00. ES shows the same shape.
- **What it means for you:** a fixed stop in points is far riskier at 09:30 than at 13:30. Size and stops have to follow the time of day. NEXA's tests already scale risk this way.

## 3. Does order flow predict the next move? (no, on these two days)
Correlation between each minute's net aggressor delta (buys − sells) and the price change:

| | Same minute | Next minute | Next 5 minutes |
|---|---|---|---|
| NQ delta | **0.71** | −0.04 | 0.02 |
| ES delta | **0.69** | 0.02 | 0.09 |
| NQ book imbalance (bids vs asks shown) | 0.22 | −0.06 | −0.14 |
| ES book imbalance | 0.19 | 0.00 | −0.02 |

- **Delta describes the move, it does not predict it.** Aggressive buying and rising price happen in the same minute (0.7). One minute later the link is gone (≈ 0).
- This is the same result as NEXA's H-FLOW-PRED and the creator who tested 25 order-flow signals on 279 days (next-minute 0.01). Now seen on your own recorder, with true aggressor sides from ATAS.
- **The visible book is weaker still.** The NQ next-5-minute value (−0.14) leans "more bids shown → price later lower". On 2 days it is within noise, and visible size is easy to pull or fake. Worth re-checking on 20+ days, not trading.

## 4. Things that look interesting (only 2 days: hypotheses, not findings)
1. **Net delta against the day's direction (NQ, both days).**
   - 10-21 NQ rose 124 points with net selling aggression (−1,979).
   - 10-22 NQ fell 371 points with net buying aggression (+2,838); ES the same on 10-22 (+15,852, price down).
   - The classic reading is "passive limit orders absorbed the aggressors": buyers hit the offer all day while a larger seller kept refilling it.
   - Two days cannot separate that from noise. A clean test needs many sessions, and it overlaps with what H-ICE-FEAS measures (refills).
2. **Big prints do not lead.** The top 0.1 % of trades by size (≥ ~32 NQ / ≥ ~100 ES contracts, 634 NQ and 605 ES prints) did **not** move price their way afterwards.
   - NQ: on average −1.8 points against the big trader after 1 minute, −2.2 after 15; only 43 % went their way.
   - ES: about flat.
   - "Follow the whale" did not work on these days. Many large aggressive prints are hedges, closing trades or stop-outs near short-term extremes. (Same finding as the 279-day test: following volume bubbles won 48 %.)
3. **NQ leads ES by about one second.** On 1-second returns, NQ now vs ES one second later correlates 0.06–0.07; the reverse is 0.02; same second 0.71–0.78.
   - The lead exists but lasts about 1 second. Not usable by hand, and on a delayed feed both arrive late.
4. **Most trades are tiny.** 72 % of NQ trades and 34 % of ES trades are 1 contract (median size 1 NQ / 3 ES). Large size is rare, so a "big trades" filter shows only the top few hundred prints a day.

## 5. What this means for the goal
- The recorder works and captures what ATAS shows: every trade with its side, the book every 5 seconds, the footprint and 1-minute bars.
- On your own data, the pattern NEXA keeps finding holds: **order flow explains the present minute, not the next one**, and big prints are not a signal by themselves.
- The robust things are about **risk, not direction**: when volatility is high (the open, the last hour), how far the day extends beyond the first hour, and where volume built value (POC / value area) for the next day.
- **Next useful steps:**
  - (a) let the recorder reach 10+ full sessions, then run the sealed H-ICE-FEAS (≈ 2026-11-04);
  - (b) re-run this decode at 20+ sessions to see whether the "delta against direction" and "visible bids lead lower" leans survive;
  - (c) any rule worth money still needs pre-registration and a long free-data test.
