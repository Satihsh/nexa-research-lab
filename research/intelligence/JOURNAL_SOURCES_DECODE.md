# What experienced traders in our sources say about journaling → NEXA Monitor v2 fields (2026-10-18)

- **Method:** searched every decoded transcript, book note and web source in `research/` for "journal" (sponsor reads for TradeZella / "Market Journal" newsletter and academic "Journal of …" hits excluded).
- **Only statements by traders in the user's own sources are used.** Each becomes a journal field or a panel line. Nothing here is an entry rule; NEXA has no tested entry edge (ledger 2026-10-18).

| # | Source (ID) | What they said (paraphrased) | NEXA Monitor v2 field |
|---|---|---|---|
| J1 | Fabio Valentini, Chart Fanatics live (`DyS79Eb92Ug`, SRC-YT-056) | Keeps statistics on everything; reviews metrics at weekends. Found that days starting with 3–5 stop-losses end in big losses, so now cuts the day early. Removed a weekday (Wednesday) after the data showed it. "If you don't have data, you can't improve." | `losses_in_row_today`, `losses_today`, weekday on every row; panel warns after consecutive losses |
| J2 | Fabio Valentini (`tvERE-Beu2U`, SRC-YT-058) | Jumped in on aggression before his model was complete; "when you journal, you understand the error… when your mind is cold". Using AI on the journal "can really step up the game"; with 2,500 trades, small risk-management changes reshape the equity curve. | `setup_tag` + `followed_plan` flags; Claude reviews the CSVs after the session (cold mind) |
| J3 | Dhesi, Words of Rizdom (`G9itT05pGvc`, SRC-YT-122) | Journal starts with: how am I feeling, did I sleep enough, how is life outside the markets. Only then trade. Logs what times work; weekly / bi-weekly review of what losses have in common. Cut the NY afternoon after seeing he gave back morning gains. Max 2 losses a day. Screen-records trades. | `ready_check` (sleep/feeling, ticked by the user before trading), `time_ct`, entry hour bucket; panel: losses today vs 2 |
| J4 | Kevin McCormick, Robbins Cup 2021 champion (`a0nQKIl5o4M`, SRC-YT-104) | Learned from Larry Williams to go back through the journal "to reinforce the correct behaviours": a winning trade can still be wrong for your plan. | `rule_flags` on every trade (no stop, 3rd trade, late entry, risk > cap), kept even on winners |
| J5 | Omar "MBB Trader", Chart Fanatics (`IB-fyWI5j8w`, SRC-YT-121) | People who complain about break-even stops should journal: when the break-even stop was hit, how often would the original stop or original target have been hit? | `followup.csv`: after each exit, which came first, the **original target or the original stop** (until flat-by time) |
| J6 | TG Capital, Chart Fanatics (`ADnslyKOwFE`, SRC-YT-085) | Handwritten journal of "what the candles have done"; grades setups (A++). | Entry/exit **candle record**: OHLC, body/wick shape, volume, delta, bar POC; user `setup_grade` |
| J7 | Daryl Martin, Apex founder (`8oMl5xJhu1U`, SRC-YT-123) | "Every bad habit you have will come out in trading"; journaling is how you reflect; he even tape-recorded himself while trading. | `notes` field; suggest macOS screen recording (⌘⇧5) during sessions |
| J8 | Day Trade Professor live (`lsOa2AKb994`, SRC-YT-124) | Post-trade review: candles, levels, multiple timeframes, "where was the real battle". | Context record: distance to VWAP, session high/low, prior-day high/low/close, overnight high/low, initial balance |
| J9 | Marci Silfrain, Robbins Cup 2nd (`Dt9vzMmf__o`, `eiAe4i-epxQ`) | Plan to lose the next 20 in a row (if you can't, you're over-levered); exit plan fixed before entry; one direction per day, no flip-flopping. | Longest losing streak in the review; panel shows what 20 losses in a row would do to the MLL; `direction_flip` flag when the day's 2nd trade is the opposite side |
| J10 | Praveen (`4BKMDB0dMXc`, decoded by the user) | Journal every trade; one instrument; no revenge trading; risk ≤ max loss ÷ 4. | `minutes_since_last_loss` on each entry (revenge-trade check); risk cap shown in planner |
| J11 | Larry Williams (via J4 and SRC-YT notes) | The most profitable strategies have the lowest accuracy. | Panel reports R-multiple, not just win/loss |

## "Backstage" (order flow and book) recorded at entry and exit
- Each is a **fact at that moment**, not a signal. OFC1/OFC1R/T2a showed fixed order-flow rules failed on 10+ years of data. The journal records them so *your* trades can be studied later (H-DISC1 report-only breakdowns).
- **Fields:**
  - best bid / ask and spread;
  - cumulative DOM bid and ask volume, plus the top-10-level bid/ask imbalance (ATAS `MarketDepthInfo`);
  - last 60 s of tape: aggressive buy and sell volume, trade count, largest single print;
  - bar delta, max/min delta, and bar ask/bid volume (ATAS candle).

## "What if" (on the chart panel)
- **When flat:** "If you enter now" with your planned stop/target ticks:
  - contracts for your risk cap;
  - $ lost if the stop is hit, $ won if the target is hit;
  - day P&L and the Topstep MLL buffer after each outcome;
  - break-even win rate.
- **When in a position:** reads your **working stop and target orders** (ATAS SL/TP) and shows:
  - **A: stop hit →** trade $, R, day P&L, MLL buffer, trades and losses left;
  - **B: target hit →** the same.
  - If no stop order is working, the panel shows a violation.

## Indicators (NEXA Monitor v3, added 2026-10-18 at the user's request)
- **Scope:** ATAS X ships 296 indicator classes (256 in `ATAS.Indicators.Technical.dll`, 40 in `ATAS.Indicators.Other.dll`). The user sees about 281 in the menu.
- **No API reads another indicator's values off the chart** (`IChart` exposes no indicator list). NEXA therefore computes its own set with the same formulas.
- **Recording all 281 is not done, on purpose:**
  - most are re-mixes of the same OHLCV, delta and volume inputs;
  - NEXA already tested this class of signal: 8E (2,160 trials covering Donchian, TD Sequential, Squeeze/EMA200 and MACD, all REJECTED or not net-positive) and H-ML1 (REJECTED);
  - a "gold mine" search across hundreds of columns on ≤ 200 trades finds patterns by chance (ledger ≈ 163 trials).
- **The set below is limited to indicators that traders in the user's sources use, with their stated settings.**

| Field (indicators.csv) | Setting | Source |
|---|---|---|
| EMA 5 / 9 / 13 and stack order | 5, 9, 13 on chart bars | TG Capital (`ADnslyKOwFE` [5:31]); EMA 5/13 BTMM (S07) |
| MACD | (5, 13, 4) | NEXA 8E momentum engine / BTMM S07 (8E: not net-positive) |
| Bollinger %B, width | (20, 2σ) on closes | Silfrain (outer band); Straight Kim (`-FCNwoQ_ARs`); Carter S19 |
| Double-Bollinger touch | BB(4, 4σ, opens) + BB(20, 2σ) | Straight Kim (`-FCNwoQ_ARs`, claims unverified) |
| Squeeze on/off | BB(20, 2σ) inside KC(20, 1.5 × ATR20), 20-bar mean as midline | Carter TTM (S19); 8E (UNPROVEN) |
| RSI | 14, Wilder | ATAS default (no source gives an intraday RSI setting) |
| CVD | Since 17:00 CT and since 08:30 CT | ATAS CVD; order-flow sources (Fabio) |
| Developing and prior-day POC / VAL / VAH | 70 % greedy, two ticks per step, ties upward (= `of_common.va_greedy`, EQ-014) on footprint volumes | Fabio Valentini (`DyS79Eb92Ug`, `tvERE-Beu2U`) |
| Footprint imbalances and stacks in the bar | Diagonal 3×, ≥ 10 contracts, stack ≥ 3 ticks (OFC1 E4) | Fabio / OFC1 (REJECTED as an entry rule) |
| Big trades (last 60 s) | ATAS aggregated trades ≥ setting (default 30 = Fabio's NQ filter; set your own for MNQ/ES) | Fabio (`tvERE-Beu2U`) |

- **How the data is used:** H-DISC1 report-only breakdowns (PREREG_DISC1.md §3).
  - A pattern found there becomes a **new** pre-registered hypothesis, tested on later trades.
  - It never becomes a filter applied back to the trades it was found in.
