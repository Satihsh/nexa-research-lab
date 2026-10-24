# PRE-REGISTRATION OF-COMMON: shared definitions for OF-16, OF-19 and OF-20

**Written 2026-10-11, before any OF-16 / OF-19 / OF-20 outcome is computed.** The SHA-256 of this file and of the three hypothesis files is recorded in `PREREG_HASHES.txt`. Every hypothesis file inherits this document. Any later deviation is reported as a numbered deviation. **No definition, threshold or decision rule here is changed after outcomes are seen.**

**Approval:** user, 2026-10-11, "Approved, pre-register OF-16, OF-19 and OF-20".

**Scope:** research only.
- No production code, S14, NEXA_Risk, schema v1, MT5 or deployment is touched.
- No new market data is collected. Every input is already on disk.
- Passing any test makes an item a *research candidate* only (RESEARCH_GATE). Nothing is promoted automatically.

---

## C1. Disclosures (what was seen before writing)

- **No OF-16/19/20 outcome has been computed by anyone in this project.**
  - The only profile work already done is T1, which measured *proxy agreement* on 2024-10 → 2026-09: tick-volume VA vs futures VA, and the inside-VA flag at 08:00/14:00 UTC (F-b). It did not measure next-day direction, range extension or day-type sequences.
- **T2** measured realised-volatility forecasts on the same M1 data. Here that data is used only for σ̂ (§C5).
- **V2 campaign overlap:** the V2 strategy campaign used 2017–2024 for its own features and *excludes* 2025–2026, but that exclusion applies to V2 only. These OF tests are a separate programme; the overlap is stated rather than hidden.
- **Prior knowledge of the author:** the author knows the general price history of these instruments (e.g. gold's 2018–2026 rise). The drift-controlled nulls (§C8) exist for this reason.
- **Source claims are priors to falsify, not facts:**
  - CL-005 "70–80 %" (YT-005);
  - CL-009 "trend → balance" (YT-013);
  - CL-031 "rebalance ≈ 10 %" (YT-002);
  - CL-003/004 (YT-006).
  - No source published data or method behind its statistic.
  - All sources trade ES/NQ/stocks with an exchange cash open; NEXA tests a spot FX/XAU *analogue*. A negative result here refutes the analogue for these instruments, not necessarily the original claim on its original instrument.
- **Stage note:** RESEARCH_GATE G2 requires G1 (a reference implementation with a synthetic unit test). This document is the G2 artefact filed *ahead of* the code. The items become G2 only when the reference implementation and its synthetic unit test exist. If writing the code reveals an ambiguity, it is resolved by a disclosed deviation, never by a silent choice.

## C2. Data

**Source:** Pepperstone M1 canonical, `filesnexa/NEXA/data/pepperstone/m1_canonical/PEPPERSTONE_<SYM>_M1_canonical.csv.gz`.
- Columns used: `time_server`, `open`, `high`, `low`, `close` (bid), `tick_volume`, `spread` (points), `time_status`, `time_utc`.

**Symbols and first server day evaluated:**

| Symbol | First server day | Point size |
|---|---|---|
| EURUSD | 2017-07-03 | 0.00001 |
| GBPUSD | 2017-07-03 | 0.00001 |
| USDJPY | 2017-07-03 | 0.001 |
| XAUUSD | 2018-01-02 | 0.01 |

- **Last server day:** 2026-09-25, for all symbols. **No 2027 data is used.** 2027 is reserved as V2 OOS and needs user approval.
- **Rows:**
  - rows with `time_status ≠ OK` are excluded, and the count is reported;
  - duplicate `time_server` stamps keep the first row, and the count is reported;
  - a bar's timestamp is its **open** time;
  - a bar belongs to a window [a, b) iff a ≤ t < b.
- **Cached CME futures profiles** (`validation/data/*_fut_profile.csv`, 2024-10 → 2026-09) are used **only** for the proxy-swap robustness check named in OF-16. They are never used for any verdict.

## C3. Clocks

- **Server day (A0):** the date of `time_server` (Pepperstone, NY+7). Server midnight = 17:00 New York. Weekdays only; any Saturday/Sunday server-day bar is dropped and counted.
- **Conversion:**
  - New York local time = `time_server` − 7 h, exactly;
  - UTC is obtained by localising New York local time with `America/New_York` (zoneinfo);
  - London local time comes from UTC via `Europe/London`.
- **Check:** the conversion is checked against the file's `time_utc` wherever that column is non-empty. Mismatches are counted and reported. A mismatch rate > 0.1 % halts the run until it is explained as a deviation.
- **Anchors (from `06_LIQUIDITY_MODEL.md` §3, already pre-registered):**
  - A1 London open = 08:00 Europe/London;
  - A2 New York open = 08:20 America/New_York for XAUUSD (COMEX gold day session), 08:30 America/New_York for FX (US data time);
  - session end E = 17:00 America/New_York (= the end of server day d).
  - Each anchor is taken on the calendar date equal to the server date d. Both anchors then fall inside server day d.
- **Primary and secondary anchor per symbol** (fixed here, with the 06 §3 rationale):

| Symbol | Primary anchor | Secondary anchor (counted trial) |
|---|---|---|
| EURUSD, GBPUSD, USDJPY | A1 (London 08:00; highest-volume FX session start) | A2 (08:30 ET) |
| XAUUSD | A2 (08:20 ET; COMEX gold day session, the closest gold analogue of an exchange cash open) | A1 |

- **Anchored session of day d:** S_d = [a_d, E_d). Anchor bar = the first bar with t ≥ a_d and t < a_d + 5 min. If no such bar exists, the session is invalid (counted).
- **Initial balance:** IB_d = [a_d, a_d + 60 min). Valid only if ≥ 54 of its 60 minutes have a bar.

## C4. Valid days

- **Thin day:** a server day whose bar count is < 80 % of that symbol's median weekday bar count over the full sample (the T1/T2 rule).
- **Valid server day:** not thin, all OHLC finite, and high ≥ low on every bar.
- **Next session / prior session:** d+1 (d−1) is the next (previous) weekday server day present in the data.
  - A test that needs both d and d±1 is evaluated only if both are valid. Skipped pairs are counted.
  - Friday→Monday pairs are included. Their exclusion is reported as a sensitivity check.

## C5. Scale σ̂ (causal)

- σ̂_d = C_{d−1} × sd(ln C_k − ln C_{k−1}, over the 20 valid server days ending at d−1), with sample sd (ddof = 1). C_k is the close of the last bar of server day k.
- Days with fewer than 20 prior valid returns are not evaluated.

## C6. Volume profile and value area (used by OF-16 and OF-20 BAL2)

**Construction**
- Each M1 bar's `tick_volume` is assigned to the bin containing its typical price (h + l + c)/3.
- **Bin widths (spot price units):** XAUUSD 1.00, EURUSD 0.0001, GBPUSD 0.0001, USDJPY 0.01. These are the spot equivalents of the T1-validated futures bins.
- **POC** = the argmax bin; ties go to the lowest-price bin.
- **VA** at α = 0.70 by the EQ-014 two-bin greedy rule, with ties going to the upper side first. This is identical to `va_greedy` in `t1_tickvol_proxy.py`.
- VAH = the upper edge of the top VA bin; VAL = the lower edge of the bottom VA bin.

**Proxy status (T1)**
- The tick-volume profile is a validated proxy for XAUUSD, EURUSD and USDJPY.
- It is **REJECTED for GBPUSD**. GBPUSD profile-based results are reported but **excluded from verdict counts**.
- **Robustness (not a verdict input):** the same analysis with σ-scaled bins (bin = σ̂_d / 50).

## C7. Costs (used where a trade translation is pre-registered)

- **Commission:** USD 7.00 per lot round trip, NEXA's documented Pepperstone rate. To be re-verified from the first S14 CLOSE row when fills exist. In price units:
  - EURUSD / GBPUSD 0.00007;
  - USDJPY 0.00007 × P (P = entry price);
  - XAUUSD 0.07 (100 oz lot).
- **Spread:** s_d = the median, over the 20 valid server days ending at d−1, of each day's 90th-percentile M1 `spread` × point size.
  - Longs: buy at bid + s_d, sell at bid.
  - Shorts: sell at bid, buy at bid + s_d.
  - Note that the MT5 M1 `spread` field is the bar minimum, so this understates real costs. Hence the stress below.
- **Slippage stress:** +0.05R (decision) and +0.10R (reported) per trade.
- **Swap:** none. Every pre-registered trade is flat by E (17:00 NY, before rollover).
- **Cost floor (ex ante):** a trade is not taken if the round-trip cost (commission + s_d) exceeds 0.20 × D, where D is the initial risk distance in price units. Excluded setups are counted.

## C8. Statistics (common)

**Splits:**
- **Discovery:** first day → 2022-12-31.
- **Validation:** 2023-01-01 → 2024-12-31.
- **Holdout:** 2025-01-01 → 2026-09-25.
- **Prospective:** 2026-10 onward, accumulated unseen.

**Order of opening:** discovery first, then validation, then holdout, **once**. Results are reported per split and pooled.

**Fitted objects:** nothing in OF-16/19/20 is fitted to outcomes. The only quantities estimated from data are:
- tercile and quintile cut-points;
- the intraday variance-share curve (§OF-19).

Both are estimated on **discovery only** and frozen.

**Uncertainty:** moving day-block bootstrap.
- Block length 20 valid server days; B = 2,000 resamples; seed 20261011.
- One-sided bootstrap p = (1 + #{θ*_b ≤ 0}) / (B + 1) for a hypothesised positive effect θ.
- 95 % CIs are percentile CIs.

**Drift control:** every directional statistic is compared with a drift-matched base rate (defined per hypothesis). Raw 50 % comparisons are reported but **never** decide.

**Per-symbol rule** (applies to each primary effect θ of each hypothesis):

| Verdict | Condition |
|---|---|
| **SUPPORTED** | (1) Discovery θ > 0 with BH-adjusted p < 0.10 (BH within that hypothesis's primary family). **And** (2) validation and holdout point estimates > 0. **And** (3) pooled (all splits) 95 % CI lower bound > 0. **And** (4) every additional requirement named in the hypothesis file |
| **REJECTED** | Pooled point estimate ≤ 0, **or** discovery and holdout point estimates have opposite signs |
| **INCONCLUSIVE** | Anything else |

**Multiple testing:**
- BH at q = 0.10 within each hypothesis's primary family (symbols × primary cell).
- BH is also reported across all 15 primary tests jointly, plus the OF-19 trade test. Joint failure is disclosed.
  - OF-16: 3 (GBPUSD excluded, proxy-invalid).
  - OF-19: 8 (two effects × 4 symbols).
  - OF-20: 4.
- Secondary cells are counted trials, reported with BH within their own family, and **never** override a primary verdict.

**Year stability:** reported for every primary effect: the share contributed by each calendar year. A year > 50 % of the pooled effect is flagged.

**Outputs:** `of16_results.json`, `of19_results.json`, `of20_results.json` plus `*_run.log` under `research/intelligence/validation/`, hashed into `RESULTS_MANIFEST.txt`.
