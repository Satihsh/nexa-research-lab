# PRE-REGISTRATION FX1: daily FX fix reversals (Krohn, Mueller & Whelan 2024) on Pepperstone EURUSD, GBPUSD, USDJPY

**Status: BINDING.**
- Approved by the user 2026-10-11: "Approved, pre-register FX1".
- Written before any FX1 outcome is computed. Its SHA-256 goes into `PREREG_HASHES.txt` now.
- Code, tests and frozen calendars are hashed **before discovery opens**. Implementation and the run need a separate user approval.
- It inherits `PREREG_OF_COMMON.md` (data, clock NY+7, valid days §C4, costs §C7, statistics §C8) and the cost / stop / placebo conventions of `PREREG_IM1_INTRADAY_MOMENTUM.md`, **except where stated**.

## 1. Hypothesis, source and honest prior

**Source:** Krohn, Mueller & Whelan (2024, *Journal of Finance* 79:541–578; BoC SWP 2021-48), "Foreign Exchange Fixings and Returns around the Clock".
- The US dollar **appreciates before** the Tokyo (09:55 JST), ECB (14:15 Frankfurt) and WMR London (16:00 London) fixes and **depreciates after** them: a W-shape around the clock.
- G9 currencies, 1999–2019, t-statistics 4.5–11.7.
- Mechanism: dealers' inventory risk from an unconditional pre-fix USD demand.
- **The strategy returns in the paper ignore transaction costs.**

**Paper Table I** (RTH sample; bp per day; + = foreign currency appreciates vs USD):

| Window (paper, ET) | EUR | GBP | JPY |
|---|---|---|---|
| pre-Tokyo 17:00–20:55 | −1.80*** | −1.89*** | −1.61*** |
| **post-Tokyo** 20:55–02:00 | **+2.34*** | **+1.27*** | **+3.15*** |
| **pre-ECB** 02:00–08:15 | **−3.52*** | **−2.29*** | **−1.03** |
| ECB→London 08:15–11:00 | +0.63 | +0.42 | +0.62 |
| **post-London** 11:00–17:00 | **+2.73*** | **+2.65*** | **−1.16*** |

**Honest prior:**
- The gross effects are 1–3.5 bp per window per day (1999–2019 averages).
- NEXA's FX round trip is ≈ 0.9 bp (S0), ≈ 1.4 bp (S1).
- A net-positive result needs the effect to have **persisted at ≥ ≈ 50 % of the paper's size** in 2017–2026. The fix reforms (2015 WMR window widening) and the publicity (paper first posted 2020) may have eroded it.
- **2020-01 → 2026-09 is out-of-sample relative to the paper.**

**Disclosure (seen data):**
- The Pepperstone M1 files were used in T1/T2, OF-16/19/20/20b, C1, C2 and IM1. None computed these unconditional, fix-anchored window returns.
- **Overlaps:**
  - C1 measured USDJPY returns in a ± 5 min band around the Tokyo fix by gotobi class (post-fix fall: consistent with this paper);
  - IM1 measured EUR/GBP/JPY 14:30–15:00 ET returns conditional on r_ROD (inside the post-London window);
  - the OF tests measured session outcomes from London 08:00 / NY 08:30 anchors.

## 2. Data, clock, windows

**Data:**
- **Instruments:** EURUSD, GBPUSD, USDJPY. Pepperstone M1 canonical (bid OHLC + `spread`), 2017-07-03 → 2026-09-25.
- XAU is excluded (not a currency; not in the paper).

**Fix times** (DST-aware, by each fix's own local clock; converted per day to UTC):
- Tokyo **09:55 Asia/Tokyo**;
- ECB **14:15 Europe/Berlin**;
- London **16:00 Europe/London**.

**Window anchors** (the paper's boundaries, expressed by their defining local clocks):

| Window | Start | End | Trade (fixed by the paper's sign) |
|---|---|---|---|
| **W1 post-Tokyo** | Tokyo fix (09:55 JST) | **08:00 Europe/Berlin** (the paper's "European open", 02:00 ET) | Foreign currency up: **long EURUSD, long GBPUSD, short USDJPY** |
| **W2 pre-ECB** | 08:00 Europe/Berlin | ECB fix (14:15 Europe/Berlin) | Foreign currency down: **short EURUSD, short GBPUSD, long USDJPY** |
| **W3 post-London** | London fix (16:00 Europe/London) | **16:55 America/New_York** | EUR/GBP up, JPY down: **long EURUSD, long GBPUSD, long USDJPY** |

**Excluded windows:**
- **pre-Tokyo**: it starts at the 17:00 NY rollover (widest spreads; swap boundary);
- **ECB→London**: not significant in the paper.

**W3 ends at 16:55 NY, not 17:00:** this avoids the rollover spread spike and the swap boundary. 17:00 is reported as robustness.

**Days:**
- A window is traded on day d (its start date in its anchor clock) only if:
  - its fix is published that day;
  - the server day is COMMON §C4-valid;
  - every required M1 bar exists.
- **Publication calendars** (frozen into `FX1_CALENDARS.json` before discovery):
  - Tokyo: Japanese business days (`C1_JP_HOLIDAYS.json`, frozen);
  - ECB: TARGET business days (excluding Jan 1, Good Friday, Easter Monday, May 1, Dec 25, Dec 26);
  - WMR London: weekdays except Dec 25 and Jan 1.

## 3. Rule (exact)

For each eligible (day, window, pair):
- **entry** at the open of the first M1 bar starting at the window start (bid; longs pay the spread);
- **exit** at the close of the M1 bar starting at end − 1 min;
- **direction** per §2;
- **one trade per window per pair per day.** Consecutive windows (W1→W2) are separate trades.

**Catastrophe stop** (no-missing-stop invariant):
- ± 4·σ̂_W from the entry, where σ̂_W = the sd of that window's log return for that pair over the **previous 60 eligible days** (causal).
- Checked on M1 bid high/low (shorts: high + spread); a gap fills at the bar open.

**No swap:** no window crosses the 17:00 NY rollover.

## 4. Costs (as IM1)

- **Commission:** USD 7/lot round trip (EUR/GBP 0.00007; JPY 0.00007 × P).
- **Spread:** s = trailing-20-valid-day median of the daily p90 M1 `spread` × point, **floor 0.2 pip**.
- **Stress:** S0 / **S1 (+0.25 bp per side; decides)** / S2 (+0.50 bp per side).
- **Cost floor:** skip if cost > 0.20 × the stop distance (counted).

## 5. Benchmarks and nulls

- **N0:** zero.
- **N1 (timing placebo):**
  - For each window W of length L, placebo windows [start + δ, start + δ + L) with the same direction, for **δ every 30 min from −12 h to +11.5 h, excluding |δ| ≤ 90 min**: 41 offsets.
  - A placebo trade is skipped (counted) if its window crosses or touches 16:55–17:05 NY.
  - Pooled placebo mean at offset δ = equal-weight mean over all windows and pairs.
  - p_tod = (1 + #{pooled placebo mean ≥ observed}) / 42.
- **N2 (gross replication):** the gross mean return per window × pair vs the paper's Table I sign and magnitude, reported.

## 6. Splits, samples, statistics

**Splits (COMMON §C8):**
- discovery 2017-07 → 2022-12;
- validation 2023 → 2024;
- holdout 2025-01 → 2026-09-25, opened once.

**Additionally reported:** the **post-paper period 2020-01 → 2026-09** (criterion 5).

**Expected trades:** ≈ 245 days × 3 windows × 3 pairs ≈ 2,200 per year, ≈ 20,000 in total (minus 60-day warm-ups).
- **Minimum:** holdout ≥ 1,000 pooled trades, else INSUFFICIENT-N.

**Uncertainty:** moving-block bootstrap over calendar days (block 20, B = 2,000, seed 20261011), with all trades of a day kept together; one-sided p.

**Multiplicity:**
- primary **P** = all 9 window × pair cells pooled, equal weight per trade, S1 net mean (bp);
- secondaries = the 3 windows (pairs pooled) and the 3 pairs (windows pooled): 6, BH q = 0.10;
- **DSR** n_trials = 1 + 6 + 41 = **48**.

**Power:** the discovery σ gives the MDE at 80 % per split (reported).

## 7. Acceptance criteria (all required for "research candidate", RESEARCH_GATE G4)

1. **Discovery:** P net (S1) mean > 0 with one-sided p < 0.05.
2. **Validation and holdout:** P net (S1) point estimates > 0.
3. **Pooled:** the 95 % CI lower bound of the P net (S1) mean > 0. S2 is reported.
4. **Placebo:** pooled p_tod ≤ 0.05.
5. **Post-paper persistence:** the 2020-01 → 2026-09 P net (S1) mean > 0, with its 95 % CI lower bound > 0.
6. **Stability:**
   - no calendar year > 40 % of pooled net P&L;
   - ≥ 6 of 10 years (2017 partial … 2026 partial) positive;
   - ≥ 2 of 3 windows and ≥ 2 of 3 pairs with a positive net mean.
7. **DSR** ≥ 0.95 at n_trials = 48.
8. **Cost feasibility:** the median stop distance ≥ 5 × the round-trip cost.

**Verdicts:**
- **REJECTED** if the pooled P net (S0) mean ≤ 0, or the discovery and holdout signs are opposite.
- **INSUFFICIENT-N** per §6.
- **INCONCLUSIVE** otherwise.
- The gross replication (N2) is reported separately.
- **No re-run with altered windows or signs under FX1.**

## 8. Robustness (reported only; never changes the verdict)

- W3 to 17:00 NY.
- Window boundaries at the paper's fixed ET clock times (20:55 / 02:00 / 08:15 / 11:00) instead of the local-clock fixes.
- FX spread floor 0.1 / 0.3 pip.
- Stop 3σ / 6σ.
- Each window × pair cell separately.
- Per year.
- Only W2 + W3 (excluding the overnight W1).
- Equal weight per day instead of per trade.

## 9. Code (thin; reused)

- `of_common.py`: load, valid days, splits, commission, bootstrap, BH, verdict.
- `im1_intraday_momentum.py`: Bars, trade mechanics (imported read-only; frozen sha b63698e4…).
- New `fx1_fix_reversals.py` and `test_fx1.py`. Tests cover:
  - fix-time conversion across the US/EU/UK DST mismatch weeks and Japan (no DST);
  - window construction and exclusions;
  - direction signs;
  - calendar rules;
  - placebo offsets / exclusions (41).
- Hashes recorded before discovery opens.
