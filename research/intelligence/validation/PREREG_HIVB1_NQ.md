# PRE-REGISTRATION H-IVB1-NQ: Fabio Valentini's IVB Model 1 on Nasdaq-100 futures

**Status: BINDING.**
- Approved by the user 2026-10-13: "approved, pre-register H-IVB1-NQ and H-IM-NQ".
- Written **before** any IVB statistic has been computed on any data.
- The NQ 1-minute data on this machine (`NQ_v0_ohlcv1m_2023-02-18_2026-10-10_canonical.csv.gz`, sha `18d54a1c…`) was already used for H-ORB-1. **No IVB quantity (range profile, VA, POC, breakout, retrace) has been computed or looked at.**
- Its SHA-256 goes into `PREREG_HASHES.txt` now.
- **Implementation and the run each need a separate user approval.**
- Inherits the discipline of `PREREG_HORB1_NAS100_ORB.md` (hashing, stages opened once, day-block bootstrap, BH, DSR) except where stated.

## 1. Source and exact rules (as stated)

**Source:** Fabio Valentini, "The Simplest Orderflow Trading Model" (`cUTsoU-15Tc`, 2026-02-17; KB SRC-YT-031, claims CL-118 / CL-120 / CL-121). Transcript re-read 2026-10-13. Quotes:

| Element | Quote | Timestamp |
|---|---|---|
| Range | "a top… a bottom on the first 15 to 30 minutes"; in every example he waits "for the first 30 minutes of the session to be completed" | 4:23–4:42, 10:50–11:00, 16:27–16:55 |
| Profile | "we take this top, we drag down with the fixed profile… the PC [POC]" | 4:42–5:14 |
| Direction | after a breakout, "the price accept[s] this value"; "if they will break on the downside, we will consider short… upside… long" | 5:14–5:21, 20:51–21:06 |
| Location / entry | "the most sensitive level… is the level contained between the value area and the PC… when you retrace you can expect buyers to reload" | 5:21–5:36 |
| Invalidation | "a value area low that if it gets broken… If we close a candle here, the setup is invalidated" | 6:08–6:26 |
| Target | "from here to the first protection point… maybe 1 to 2, 1 to 2.5"; "better to take 1:2, 1:2.5 with a really consistent way of executing" | 6:26–6:42, 23:07–23:16 |
| Not codable | The "protection level" (TP1) is a proprietary DeepCharts algorithm (CL-120) | 8:16–9:10 |

**Track record cited by the source:** contest podiums (CL-125). It contains a confirmed selection effect (multiple accounts, keep the winner).

**Prior evidence:**
- **Third-party coding on NQ 5-min** (RoboQuant, CL-126): unprofitable as specified, about 9,900 optimisation runs, no out-of-sample test. Weak evidence either way.
- **H-ORB-1** (same data family, the opening-range breakout): INCONCLUSIVE, +0.063 R.

## 2. Instrument, data, clock, days

- **Data:** CME NQ, Databento `NQ.v.0` ohlcv-1m (trade prices + volume), 2023-02-18 → 2026-10-10, as frozen for H-ORB-1.
- **Clock:** America/New_York via the frozen calendar `IM1_US_CALENDAR.json`. Holidays and early closes are excluded.
- **Eligible days:** the latest NY date in the file is excluded.
- **Required bars:** every 1-min bar 09:30–09:59, and the 15:59 bar.

## 3. Rule (exact; design choices marked **DC**)

**1. Range.** Point A / point B = high / low of the 1-min bars 09:30–09:59. **DC-1:** 30 minutes (his examples); the 15-minute version is robustness only.

**2. Profile.**
- Fixed volume profile over 09:30–09:59, with bins of 0.25 point (one NQ tick).
- Each 1-min bar's volume is spread **uniformly** over the bins from its low to its high (**DC-2:** the trades-only data has no volume-at-price).
- POC = maximum bin. VA = 70 % via `of_common.va_greedy` (existing frozen function).
- VAH / VAL = the upper edge of the top VA bin / the lower edge of the bottom VA bin.

**3. Breakout.**
- From 10:00, the **first** 5-min candle (10:00–10:04, 10:05–10:09, …) that **closes** above A → **long**, or below B → **short**. Only the first breakout of the day counts.
- **DC-3:** 5-min candles. The breakout candle must close by 15:00.

**4. Entry (location).**
- After the breakout candle's close, a **limit order** at the near VA edge: **VAH for longs**, **VAL for shorts**. This is the first price reached on a retrace into the VA–POC zone (**DC-4**).
- **Fill:** a later 1-min bar trades at least 1 tick through the limit (low ≤ VAH − 0.25 / high ≥ VAL + 0.25), at the limit price (no improvement).
- **No fill by 15:00 → no trade.**
- If invalidation (rule 6) prints before the fill → no trade.

**5. R.** R = |entry − invalidation level| = VAH − VAL for longs, the same for shorts (the full value-area width).

**6. Exits** (checked after the fill; the first of these wins):
- **(a) Invalidation (source):** a 5-min candle **closes** below VAL (long) / above VAH (short). Exit at that candle's close.
- **(b) Hard stop (DC-5):** the range's opposite extreme, B for longs / A for shorts, intrabar on 1-min bars. A gap fills at the bar open. The source: "you don't need to wait till here" (the range edge is the outer limit).
- **(c) Target (source, DC-6):** entry ± **2R** (the low end of his "1:2–1:2.5", since TP1 is not reproducible). The limit fills when a 1-min bar trades at least 1 tick through it.
- **(d) Time exit:** the close of the 15:59 bar.
- **Priority:** if (b) and (c) touch in the same 1-min bar → stop.

**7. One trade per day** (the first setup). Re-entries ("break and reload… 1:2, 1:2, 1:2") are robustness only.

**8. Outcome** = net P&L ÷ R.

## 4. Costs and stress (per round trip, NQ points)

| Level | Cost |
|---|---|
| S0 | 1.0 point |
| **S1 (decides)** | 2.0 points |
| S2 | 3.0 points |

- These are deliberately above a typical real round trip (1 tick spread ≈ 0.25 + commission and fees ≈ 0.3–0.5 point).
- **Cost floor:** skip if the S1 cost > 20 % of R (i.e. R < 10 points), counted.

## 5. Nulls

- **N1 timing placebo:** the identical rule with the 30-min range anchored at other times. Every 30 min from 02:30 to 08:00 and from 11:00 to 14:00 ET → **19 anchors**. Breakout and fill windows are shifted equally; the time exit is still 15:59.
  - p_tod = (1 + #{placebo mean R ≥ observed}) / (1 + 19).
- **N2 direction placebo:** fade the breakout (opposite direction, same entry level, same R, same target multiple). Reported.
- **N3:** H-ORB-1's result on the same days (reported for comparison; not re-run).

## 6. Period and statistics

- **One stage:** the full period 2023-02-20 → last complete day, **opened once**.
- **Primary statistic:** mean net R per trade at S1. Moving-block bootstrap over days (block 20, B = 2,000, seed 20261013), one-sided p.
- **Secondaries (BH q = 0.10):** long-only, short-only, per year.
- **DSR family:** every series tested on this NQ dataset = H-ORB-1 (23) + H-IVB1-NQ (1 + 2 + 19 = 22) + H-IM-NQ (1 + 1 + 2 + 20 = 24) = **69 trials** (conservative, shared with H-IM-NQ). The trial-Sharpe variance is computed over this hypothesis's own series.
- **Minimum sample:** ≥ 200 trades at S1, else INSUFFICIENT-N.

## 7. Acceptance (all required for "research candidate", RESEARCH_GATE G4)

1. Mean net S1 R > 0 **and** 95 % CI lower bound > 0.
2. p_tod ≤ 0.05.
3. **Stability:**
   - no calendar year > 40 % of total net R;
   - ≥ 60 % of years positive;
   - long and short each ≥ 0.
4. DSR ≥ 0.95 (69 trials).
5. Median R ≥ 10 × the S1 cost (≥ 20 points).

**Verdict order:** INSUFFICIENT-N → REJECTED (S0 mean ≤ 0) → RESEARCH CANDIDATE (all pass) → otherwise INCONCLUSIVE. No re-run with altered parameters under H-IVB1-NQ.

## 8. Robustness (reported only; never selected)

- 15-minute range.
- Target 2.5R.
- Entry at the POC instead of the VA edge.
- Invalidation on a 1-min close.
- No hard stop.
- Re-entries allowed (up to 3 per day).
- Excluding FOMC / CPI / NFP days.

## 9. Code (after approval)

- `hivb1_nq.py` and `test_hivb1.py`, with unit tests on synthetic bars for:
  - the uniform volume spread, POC / VA against a hand calculation;
  - 5-min breakout detection;
  - limit fill with a 1-tick penetration;
  - invalidation on a 5-min close;
  - the hard stop vs target same-bar priority;
  - the cost floor;
  - the placebo count (19).
- Reuses `horb1_orb` loader / calendar / clock and `of_common` (`va_greedy`, bootstrap, BH), read-only.
- Code and tests are hashed before the run.

**If it passes:** it becomes an ATAS alert indicator. ATAS natively has the fixed-range volume profile with VA / POC. Only after a parity test and a forward demo.
