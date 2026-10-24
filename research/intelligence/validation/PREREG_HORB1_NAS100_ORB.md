# PRE-REGISTRATION H-ORB-1: 5-minute opening-range breakout on Pepperstone NAS100 (Zarattini & Aziz 2023 replication)

**Status: BINDING.**
- Approved by the user 2026-10-12: "Pre-register H-ORB-1".
- Written before any NAS100 data exists on this machine: NEXA has never loaded NAS100 history (master status item I3 BLOCKED), so **no NAS100 outcome has ever been seen**. Its SHA-256 goes into `PREREG_HASHES.txt` now.
- **Data acquisition, implementation and the run each need a separate user approval.**
- It inherits the discipline of `PREREG_OF_COMMON.md` / `PREREG_IM1_INTRADAY_MOMENTUM.md` (hashing, numbered deviations, stages opened once, day-block bootstrap, BH, DSR), **except where stated**.

## 1. Hypothesis, source, honest prior

**Source:** Zarattini, C. & Aziz, A. (2023), "Can Day Trading Really Be Profitable? Evidence of Sustainable Long-term Profits from Opening Range Breakout (ORB) Day Trading Strategy vs. Benchmark in the US Stock Market", SSRN 4416622 (rev. 2024-02).

**Exact rules, as stated by the source:**
- **Signal:** the first 5-minute candle of the cash session (09:30–09:35 ET) sets the direction: up → long, down → short.
- **No trade if that candle is a doji** (open = close).
- **Entry:** the open of the second 5-minute candle (09:35).
- **Stop:** the first candle's low (long) or high (short). R = |entry − stop|.
- **Exit:** a profit target at 10R, or the market close if the target is not reached. No partials.
- **Sizing:** 1 % risk per trade; max 4× leverage.

**Source sample and results:**
- QQQ, 2016-01-01 → 2023-02-17: 1,795 trades, win rate ≈ 24 %, total +675 % vs QQQ +169 %, annualised alpha 33 % (p = 0.0025), beta ≈ 0.
- **Costs assumed:** commission $0.0005/share; **no spread, no slippage** (CXO Advisory critique).

**Honest prior:**
- The paper's design is fixed in advance (no fitted parameters in the base rule), and an index CFD has no commission, so it is the most cost-plausible candidate in the 2026-10-12 video batch.
- **Risks:**
  - the source ignores spread and slippage;
  - the CFD tracks Nasdaq futures, not QQQ;
  - publication (April 2023) may have eroded the effect;
  - the stop is tight (often 20–60 index points), so a 1-point spread plus stop slippage is a material fraction of R.
- **The post-publication period (from 2023-02-18) is out of sample for the source.**

**Disclosure:**
- No NEXA test has used NAS100. IM1 used QQQ-like "last half hour" logic on FX/XAU only.
- The ATR-stop variant in the paper (5 % of 14-day ATR, EoD exit) was **selected by the authors after a parameter search**, so it is robustness only, never the primary.

## 2. Instrument, data, clock, days

**Instrument and costs:**
- Pepperstone MT5 **NAS100** CFD (spec probe 2026-10-01): point 0.1; $1 per point per lot; min / step 0.1 lot; **commission 0**; spread ≈ 1.0 point at 30,530; swap interest-based (avoided by the EoD exit).

**Data (to be acquired after approval):**
- Pepperstone NAS100 **M1** bid OHLC + spread, as far back as the server provides, through the last complete day.
- Exported with the canonical M1 pipeline conventions (server time NY + 7 h, DST-aware), using a terminal and account that **cannot disturb the live S14 demo** (decided in the implementation approval).
- The export is hashed and frozen before any statistic is computed.

**Clock and days:**
- **Clock:** 09:30 and 16:00 America/New_York, converted per day.
- **Days:** US exchange trading days only. Exclude NYSE holidays and **early-close days** (`IM1_US_CALENDAR.json` rule: MT5 US holidays + Good Friday + CME early closes), plus any day missing a required M1 bar.

## 3. Rule (exact)

For each eligible day d:
1. **First-candle values:**
   - **O₁** = open of the M1 bar starting 09:30;
   - **C₁** = close of the M1 bar starting 09:34;
   - **H₁ / L₁** = max high / min low of the five bars 09:30–09:34.
2. **Direction:** up if C₁ > O₁; down if C₁ < O₁; **no trade if C₁ = O₁** (at the instrument's 0.1-point precision).
3. **Entry** at the open of the bar starting 09:35:
   - long pays the ask (bid open + that day's spread);
   - short sells the bid.
4. **Stop:**
   - long: L₁ (bid low ≤ stop triggers);
   - short: H₁ (ask high = bid high + spread ≥ stop triggers);
   - a gap through the stop fills at the bar open.
   - R = |entry − stop| in price.
5. **Target:** entry ± 10R (bid for long exits, ask for short exits), as a limit.
6. **Time exit** at the close of the bar starting 15:59 (long sells the bid; short buys the ask).
7. **Same-bar rule:** if one bar touches both stop and target, assume **the stop** (conservative).
8. **Outcome** per trade = net P&L ÷ R.

## 4. Costs and stress

| Level | Spread | Extra per side | Notes |
|---|---|---|---|
| **S0** | Recorded M1 spread at entry and exit bars (floor 1.0 point) | — | Commission 0 |
| **S1 (decides)** | as S0 | **+0.5 point** | Also applied to stop fills |
| **S2** | as S0 | +1.0 point | — |

- **Cost floor:** skip if (spread + 2 × stress) > 20 % of R (counted).
- **Swap:** none (flat by 16:00 ET, before the 17:00 ET rollover).

## 5. Benchmarks and nulls

- **N0:** zero.
- **N1 (timing placebo):**
  - The identical rule anchored at other session times: start t ∈ {every 30 min from 03:00 to 15:00 ET, excluding 08:30–10:30}, with the 5-min candle at t and the EoD exit at 15:59.
  - p_tod = (1 + #{placebo mean R ≥ observed}) / (1 + #placebos).
- **N2 (direction placebo):** trade **opposite** to the first candle (same stop distance and target). Reported.
- **N3:** buy-and-hold NAS100 over the same days (open 09:35 → close 15:59), reported.

## 6. Periods, statistics

**Periods:**
- **Replication (P):** first available day → 2023-02-17 (the paper's end date).
- **Post-paper holdout (H):** 2023-02-18 → last complete day. **Opened once.**
- If fewer than 2 calendar years exist before 2023-02-18, P is INSUFFICIENT and only H is judged.

**Statistics:**
- **Primary:** mean net R per trade at S1, pooled long + short.
- **Uncertainty:** moving-block bootstrap over days (block 20, B = 2,000, seed 20261012); one-sided p.
- **Secondaries (BH q = 0.10):** long-only; short-only; per year.
- **DSR:** n_trials = 1 + 2 + number of placebo times (computed from the rule; recorded as a deviation if the count differs from the design).
- **Minimum sample:** H ≥ 300 trades, else INSUFFICIENT-N.

## 7. Acceptance (all required for "research candidate", RESEARCH_GATE G4)

1. **P (if sufficient):** net S1 mean R > 0 with one-sided p < 0.05.
2. **H:** net S1 mean R > 0 **and** the 95 % CI lower bound > 0.
3. **Timing:** p_tod ≤ 0.05.
4. **Stability:**
   - no calendar year > 40 % of total net R;
   - ≥ 60 % of years positive;
   - long and short each with net S1 mean ≥ 0.
5. **DSR** ≥ 0.95.
6. **Costs:** median R ≥ 10 × (spread + 2 × S1 stress).

**Verdicts:**
- **REJECTED** if H net S0 mean ≤ 0, or P and H have opposite signs.
- **INSUFFICIENT-N** per §6.
- **INCONCLUSIVE** otherwise.
- No re-run with altered times, stops or targets under H-ORB-1.

**Not a pass criterion, but reported for any deployment decision:**
- The share of trades whose **minimum-lot risk** (0.1 lot × R points × $1) is ≤ 1 % of a $200 account (i.e. R ≤ 20 points).
- The account size needed for 1 % risk at the median R.

The production NEXA_Risk limits (1 % per trade / 2 % daily / 10 % DD) are unchanged and binding.

## 8. Robustness (reported only)

- Paper variant: stop = 5 % of 14-day ATR, no target, EoD exit (author-selected; **not** a candidate).
- Target 5R / no target.
- Entry at 09:35 bar close instead of open.
- Spread floor 0.5 / 2.0 points.
- Excluding FOMC / CPI / NFP days (MT5 calendar).
- 2020 excluded.

## 9. Code (to be written after approval)

- **New:** `horb1_orb.py`, `test_horb1.py`. Tests cover:
  - 09:30 / 16:00 ET mapping across DST and the US/EU mismatch weeks;
  - doji;
  - stop / target / time exits with bid/ask;
  - the same-bar stop priority;
  - the calendar;
  - the placebo count.
- Reuse `of_common` statistics and the `im1_intraday_momentum` calendar builder (read-only).
- Code, tests, data export and calendar are hashed before P is opened.
