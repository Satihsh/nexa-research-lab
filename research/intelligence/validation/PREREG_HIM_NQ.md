# PRE-REGISTRATION H-IM-NQ: market intraday momentum on Nasdaq-100 futures

**Status: BINDING.**
- Approved by the user 2026-10-13: "approved, pre-register H-IVB1-NQ and H-IM-NQ".
- Written **before** any intraday-momentum statistic has been computed on NQ.
- The NQ 1-minute data (`NQ_v0_ohlcv1m_2023-02-18_2026-10-10_canonical.csv.gz`, sha `18d54a1c…`) was used for H-ORB-1, which never computed rest-of-day or last-half-hour returns.
- Its SHA-256 goes into `PREREG_HASHES.txt` now.
- **Implementation and the run each need a separate user approval.**
- Inherits the discipline of `PREREG_IM1_INTRADAY_MOMENTUM.md` / `PREREG_HORB1_NAS100_ORB.md` except where stated.

## 1. Hypothesis, sources, honest prior

**Sources:**
- Gao, Han, Li & Zhou (2018, JFE), "Market intraday momentum": SPY; the first half-hour return predicts the last half-hour return.
- **Baltussen, Da, Lammers & Martens (2021, JFE), "Hedging demand and market intraday momentum":** 60+ futures including equity indices. The rest-of-day return (previous close → 30 minutes before the close) predicts the last 30 minutes.
- **Mechanism (Baltussen et al.):** hedging by short-gamma intermediaries (option market makers, leveraged ETFs) trades in the direction of the day's move into the close. The effect is stronger when gamma is negative. This is the mechanism behind GEX tools.

**NEXA history:** IM1 tested the same rule on EUR / GBP / JPY / XAU CFDs. It was **REJECTED on costs** (net −1.08 bp per trade; FX costs are large relative to a 30-minute move).
- **This is a new market, not a re-run:** equity-index futures are the papers' own domain.
- NEXA's 2026-10-12 audit found cost ÷ daily range ≈ 0.2–0.3 % for Nasdaq vs ≈ 1.5–2.5 % for EURUSD.

**Honest prior:**
- Published, cross-market, with a mechanism, and no parameter to tune.
- But the effect may have weakened after publication.
- The 2023–2026 sample is short (one trade per day, ≈ 890 trades).

## 2. Data, clock, days

- **Data:** CME NQ, Databento `NQ.v.0` ohlcv-1m, 2023-02-18 → 2026-10-10 (frozen, sha `18d54a1c…`).
- **Clock and calendar:** as H-IVB1-NQ (America/New_York; frozen US calendar; holidays and early closes excluded; the latest NY date excluded).
- **Previous close** = the close of the 15:59 bar on the previous eligible day. If that day is not eligible, the signal is undefined → no trade.

## 3. Rule (exact)

For each eligible day d:

1. **Signal (primary, Baltussen ROD):** r = close(15:29 bar, d) / close(15:59 bar, previous eligible day) − 1.
2. **Direction:** long if r > 0, short if r < 0, no trade if r = 0.
3. **Entry** at the open of the 15:30 bar. **Exit** at the close of the 15:59 bar. No stop and no target (the papers' design).
4. **Outcome** = (exit − entry) × direction − cost, in NQ points and in bp of the entry price.

## 4. Costs (per round trip, NQ points)

| Level | Cost |
|---|---|
| S0 | 1.0 |
| **S1 (decides)** | 2.0 |
| S2 | 3.0 |

These are the same conservative levels as H-IVB1-NQ (a real round trip ≈ 0.5–0.75 point).

## 5. Nulls

- **N1 timing placebo:** the identical rule (signal = previous close → t − 30; trade t − 30 → t) for window ends t every 15 min from 10:30 to 15:15 ET → **20 placebos**.
  - p_tod = (1 + #{placebo mean ≥ observed}) / (1 + 20), on mean net bp at S1.
- **N0:** zero.
- **N3:** unconditional long 15:30 → 15:59 (reported).

## 6. Period and statistics

- **One stage:** the full period, **opened once**.
- **Primary:** mean net bp per trade at S1. Moving-block bootstrap over days (block 20, B = 2,000, seed 20261013), one-sided p.
- **Secondaries (BH q = 0.10):**
  - **Gao FH signal** (previous close → 09:59 bar close; same 15:30 → 15:59 trade);
  - long-only and short-only;
  - per year.
- **DSR family:** 69 trials, shared with H-IVB1-NQ (H-ORB-1 23 + H-IVB1-NQ 22 + H-IM-NQ 24 = 1 primary + 1 Gao + 2 long/short + 20 placebos). The trial-Sharpe variance is computed over this hypothesis's own series.
- **Minimum sample:** ≥ 600 trades, else INSUFFICIENT-N.

## 7. Acceptance (all required for "research candidate")

1. Mean net S1 bp > 0 **and** the 95 % CI lower bound > 0.
2. p_tod ≤ 0.05.
3. **Stability:**
   - no calendar year > 40 % of the total net;
   - ≥ 60 % of years positive;
   - long and short each ≥ 0.
4. DSR ≥ 0.95 (69 trials).
5. **Gross edge:** mean gross points per trade ≥ 2 × the S1 cost (LC-2 rule).

**Verdict order:** INSUFFICIENT-N → REJECTED (S0 mean ≤ 0) → RESEARCH CANDIDATE → otherwise INCONCLUSIVE. No re-run with altered windows under H-IM-NQ.

## 8. Robustness (reported only)

- Excluding FOMC / CPI / NFP days.
- Only days with |r| above the median (a "strong move" proxy for negative-gamma days; GEX history is not available).
- Entry at the 15:30 bar close.
- The S0 / S2 cost levels.

## 9. Code (after approval)

- `him_nq.py` and `test_him.py`, with synthetic tests for:
  - the signal sign and the previous-close lookup across a holiday;
  - the entry / exit bars across DST;
  - the placebo count (20).
- Reuses `horb1_orb` loader / calendar / clock and `of_common` statistics, read-only.
- Hashed before the run.

**If it passes:** it becomes an ATAS alert ("15:30 ET: momentum long / short into the close"), after a parity test and a forward demo.
