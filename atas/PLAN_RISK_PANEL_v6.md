# Plan: NEXA v6 "Risk & Range" panel (approved and BUILT 2026-10-23)

**Goal:** show only things the research shows *are* predictable (how much and when the market moves, the known event risk, the right size), never a buy/sell call. Read-only; never places orders (Apex / Topstep automation rules; NEXA rule).

## What NEXA Monitor already has (reuse, no rewrite)
- Risk cap per trade and contracts for a planned stop (`WhatIf.Contracts`, `RiskPerTradeUsd`).
- Max-loss / daily-loss tracking (`MllState`, `RuleCheck`), what-if exits, the journal.
- Profile POC / VAH / VAL (`NexaIndicators.Profile`), big trades, multi-timeframe, the recorder.

## New (small additions to the same panel)
| # | Line on the panel | How it is computed | Evidence it is real |
|---|---|---|---|
| 1 | **Expected range today** and **% already used** | Mean RTH high–low of the previous 10 sessions (from the chart's bars); used = today's range so far ÷ expected | Volatility clusters (IG-04; standard; recorder: day ranges 342 / 562 NQ) |
| 2 | **Time-of-day regime**: OPEN SURGE / MORNING / LUNCH LULL / CLOSE | Fixed ET windows, with the typical 1-minute move for that window from the last 10 sessions | Recorder U-shape: 19.5 pts/min at 09:30 vs 5.8 at 13:30 (NQ) |
| 3 | **Volatility-based stop and size** | Suggested stop = 1.5 × the mean 5-minute range for the current window (last 10 sessions); contracts = risk cap ÷ (stop × tick value), via the existing `WhatIf.Contracts` | Fixed-point stops fail at the open (H-HOUGAARD, H-ORB5) |
| 4 | **First-hour extension warning** | After 10:30 ET: first-hour range and "days usually extend ≈ 2× the first hour; don't treat it as the day's range" | Recorder: first hour = 44–49 % of the NQ range on both days |
| 5 | **Next scheduled news** (countdown) | Reads `news_calendar.csv` (date, ET time, event, impact) that Claude prepares weekly from free official calendars; panel turns amber 15 min before / red 2 min before a high-impact event | Known event times (CPI, NFP, FOMC) |
| 6 | **Daily stop-trading line** | Existing daily-loss guard, set to ≈ 1/5 of the drawdown, plus "max N trades" | Prop studies (IG-45), H-PROP-EV-TS |

**Not included (on purpose):** any direction arrow, "Market Predicted" probability, or big-trade "follow" signal. NEXA's own tests and the recorder show they do not predict.

## Work and checks
- Code: one small static class in `NexaContext.cs` (range/regime/stop maths) and new lines in `NexaMonitor.cs`; the same change in `NexaMonitorClassic` (VM).
- Tests: unit tests in `NexaMonitor.Tests` for the range, the regime windows (DST-aware ET), the stop/size maths and the calendar parser. Run with `dotnet run --project atas/NexaMonitor.Tests`.
- Deploy: rebuild both variants. Install on the Mac (ATAS X) and the VM (classic), keeping backups of the current DLLs (Mac `732c3f87`, VM `498023f4`).
- Calendar: Claude writes `news_calendar.csv` each weekend from official sources (BLS, Fed, BEA). No scraping of paid feeds.
- Estimated effort: one session. Nothing is purchased.

## Status (2026-10-23)
- Approved by the user ("build the v6 Risk & Range panel as planned, test it, and deploy it to the Mac and the VM").
- Code: `NexaMonitor/NexaRange.cs` (RangeGuide, NewsCalendar) + `RangeLines` in `NexaMonitor.cs`; panel title v6; settings group "Risk & Range" (show, lookback 10, stop multiple 1.5, news file).
- Tests: 126/126 pass (22 new, incl. a parse check of the shipped `atas/news_calendar.csv`).
- Builds: Mac ATAS X `e8698eb6`, VM classic `caaf0b76`.
- Deployed:
  - **Mac:** `~/Library/Application Support/ATAS/Indicators/NexaMonitor.dll` (backup `NexaMonitor_732c3f87.dll.bak` next to the folder); ATAS X was closed, so it loads on next start.
  - **VM:** `C:\nexa` + 3 Indicators folders (backup `C:\nexa\NexaMonitor_498023f4.dll.bak`); ATAS restarted 11:01 UTC with the watchdog's force-restart (Save and close → start → Connect in 59 s); recorder writing again 11:03:24.
- News calendar: `news_calendar.csv` copied to both journal folders (Mac `~/Documents/NEXA_ATAS`, VM `C:\Users\nexa\Documents\NEXA_ATAS`); refresh weekly from the Fed, BLS and BEA.
- The v6 lines show in **Full** panel mode; news warnings also show in One-line mode.
