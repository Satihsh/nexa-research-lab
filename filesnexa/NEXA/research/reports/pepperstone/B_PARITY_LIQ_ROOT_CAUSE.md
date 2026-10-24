# Feature parity: B-PARITY-LIQ, B-PARITY-EDGE and B-PARITY-TOL — RESOLVED, window-B contract PASS (2026-10-03)

**Scope:** parity oracle only (`research/nexa_parity.py`). The EA, `NEXA_Liquidity.mqh`, `NEXA_Features.mqh`, NEXA_Risk (`7fd5692a…`), schema v1.0, V2 and 8E are unchanged. None of the changed files is pinned by V2 or 8E.

**Before:** `PEPPERSTONE_FINAL_AUDIT.md` §M recorded that the liquidity state machine diverged on 0.2–0.85 % of 112,688 rows. Every other categorical feature matched, apart from a few trend and displacement edge cases.

**Method:** one mismatching episode per symbol was replayed bar by bar, comparing the oracle's level trackers with the MQL5 Trade DNA. Each candidate fix was tested first on a scratch copy of the oracle over the whole of window B for all four symbols, and applied to the repository only after human approval.

## Root causes

| | Cause | Class | Example | Resolution |
|---|---|---|---|---|
| **RC1** | The EA keeps the Asia range until the next bar at GMT hour 0 (`UpdateSessionLevels`). The oracle used the same GMT calendar day only. On Monday 00:00–01:59 server time the oracle therefore had an Asia level of 0, so `advance()` returned early and the tracker stayed frozen in its Friday state, while the EA aged and expired it. | Oracle definition gap | GBPUSD 2026-09-14 00:09–01:59 (111 rows): the oracle stays RECLAIMED on Friday's Asia high 1.35268; the EA expires at 00:09 | **Fixed:** `_asia_range_as_of` copies the EA's carry-over |
| **RC2** | The tester D1 exports omit each window's final, still-forming day, and `prev_day_levels` took `iloc[-2]`. On the last day of every window the oracle used the levels from two days before. | Oracle input defect | GBPUSD 2026-09-25: the oracle uses the 09-23 PDH/PDL (1.33458 / 1.32234); the EA uses 09-24 (1.32561 / 1.32041) | **Fixed:** use the latest D1 bar dated before the decision's day, as the EA's `GetPreviousDayLevelsAsOf` does |
| **RC3** | Exact floating-point tie at the 2.5-ATR acceptance limit: (1.33647 − 1.33607) / 0.00016 = 2.5 at 2026-09-22 00:15. The oracle does not reset there; the EA is inferred to reset. The result is a one-bar shift in `liqBarsBeyond` and `liqWickBodyRatio`. `liqState` is unaffected. | Floating-point tie | GBPUSD 2026-09-22 00:34–00:51, 18 rows | **Accepted as a tie** (human decision 2026-10-03); recorded under B-PARITY-TOL; no code change |

The EA computes its Asia range differently at start-up: it seeds it from the current day's bars only. That falls inside the 7,200 warm-up bars, which both sides skip, so it does not affect parity.

## Verification: full chronological parity, window B, repository oracle with RC1 + RC2

The output is identical, symbol by symbol, to the scratch-oracle run done before approval. Evidence: `B_PARITY_LIQ_VERIFY_WINDOW_B.json` (sha256 `e668f728…`).

| Symbol | Rows | liqState before → after | liqBarsBeyond before → after | Liquidity values beyond journal precision, before → after |
|---|---|---|---|---|
| GBPUSD | 28,527 | 0.782 % → **0** | 0.845 % → 0.063 % (RC3) | 464 → 18 (RC3) |
| EURUSD | 28,563 | 0.844 % → **0** | 0.844 % → **0** | 467 → **0** |
| USDJPY | 28,363 | 0.508 % → **0** | 0.508 % → **0** | 258 → **0** |
| XAUUSD | 27,235 | 0.521 % → **0** | 0.540 % → **0** | 285 → **0** |

- **Other categorical liquidity fields** went to 0 on every symbol: level, sweep direction, resolution, setup, event active, bars since reclaim, and displacement / MSS / FVG after.
- **Continuous fields:** the remaining `liqExcursionATR` / `liqWickBodyRatio` differences are at most 5.0e-07, i.e. within 6-decimal journal rounding. They belong to B-PARITY-TOL.
- **Effect of each fix:** RC2 alone took USDJPY and XAUUSD to 0. GBPUSD and EURUSD then still failed only on Monday 2026-09-14 00:00–01:59 (111 and 109 rows), which RC1 fixed.
- **No side effects:** every non-liquidity mismatch rate is identical to the stored reports, and the number of compared rows is unchanged.

## Tests

- 3 new tests in `test_nexa_parity.py`:
  - D1 series without the forming day;
  - unchanged behaviour on a complete D1 series, including Monday → Friday;
  - weekend Asia carry-over and restart at GMT hour 0.

  The RC1 and RC2 tests fail on the pre-fix oracle.
- Full research suite: **590 passed**; ruff clean.
- `nexa_parity.py`: `1cd3d231…` → `6c58f6aa266b340adcc8713e3a7a41ea33218491c5f1eeffdace2bbc82212f3c`.
- `README_PARITY.md`: the PDH/PDL and Asia-range paragraphs now describe the new semantics.

## Follow-up: trend / displacement / MSS edge cases (B-PARITY-EDGE, 2026-10-03)

After the RC1 + RC2 fix, 42 decision rows in window B still had categorical mismatches outside the liquidity machine (GBPUSD 15, EURUSD 15, USDJPY 9, XAUUSD 3). They split into two causes.

| | Cause | Class | Rows | Resolution |
|---|---|---|---|---|
| **EDGE-1** | The EA evaluates a closed bar at the **first tick of the next M1 bar** and reads M5/M15/H1 with `CopyRates(tf, 1, …)` at that moment (`RefreshMTFCache`). The oracle assumed that tick arrives at decision_ts + 1 min. After a tick gap the EA sees more closed higher-timeframe bars. | Oracle timing defect | 34 trend / htfAlignment rows, every one after a gap: 23 at the daily break (23:58 → +3–8 min), 6 at the weekend (Friday 23:54 → Monday), 5 intraday or XAU tick gaps (+2–63 min) | **Fixed:** `MarketData.window` uses the later of decision_ts + 1 min and the next M1 bar's open as the decision clock, for M5/M15/H1 only |
| **EDGE-2** | Exact floating-point tie at the 1.20 displacement threshold: body / ATR is exactly 1.2, e.g. GBPUSD 2026-09-11 07:22, body 0.00015 / ATR 0.000125. The two sides' float results land about 1e-12 apart, on opposite sides of 1.2, so `≥ 1.20` flips; MSS flips with it. The journal records `displacementATR` = 1.2 for all 8. | Floating-point tie | 8 rows (GBPUSD 4; EURUSD 4, 3 of them with MSS) | **Accepted as a tie** (human decision 2026-10-03); filed under B-PARITY-TOL; no code change |

Example of EDGE-1: GBPUSD 2026-08-31 23:58. The next bar is 00:01, so the EA's last closed M5 bar is 23:55 while the pre-fix oracle used 23:50; trendM5 came out 1 vs 2.

**Verification, window B, repository oracle** (`nexa_parity.py` `590c977e3eafa33a2542aa55ec5ee1a0f96b2ef6e823b2e680fe532e8ecd7844`):
- trendM5, trendM15, trendH1 and htfAlignment go to **0** on all four symbols.
- Every other feature's mismatch rate and the compared-row counts are unchanged.
- The output is identical, symbol by symbol, to the scratch run done before approval.
- Evidence: `B_PARITY_EDGE_VERIFY_WINDOW_B.json` (sha256 `6dd8803d…`).
- **Remaining categorical mismatches in window B are ties only:**
  - EDGE-2: 8 rows (GBPUSD 4, EURUSD 4 + 3 MSS);
  - RC3: 18 GBPUSD `liqBarsBeyond` rows.

  USDJPY and XAUUSD have none.
- **Tests:** 1 new test in `test_nexa_parity.py` (higher-timeframe window across the daily break; unchanged without a gap; the M1 window still ends at the decision bar). It fails on the pre-fix oracle. Full suite: **591 passed**; ruff clean.

**Observation for a human, not a parity defect:** EDGE-1 shows the EA takes **Friday's last-bar decision at Monday's first tick**, on Friday's data. The bars before each daily break are likewise decided 3–8 minutes late. Whether the EA's weekend and session filters block entries in that situation has not been checked.

## B-PARITY-TOL: decided 2026-10-03 (human, option A) — window-B contract PASS

**Contract** (`nexa_parity.py` `a4bf9f9309a60031…`; `README_PARITY.md` §Tolerance):
- **Continuous values:** `abs ≤ 1e-9` OR `rel ≤ 1e-6` OR `abs ≤ 0.5e-6 + abs(mql5)·2⁻²³`. The third term is the journal's own quantisation: the EA packs each value to float32 and prints it with `DoubleToString(f, 6)`.
- **Categorical values:** exact, except entries in the reviewed register `research/parity_accepted_ties.json` (`e92a8866…`, 47 entries):
  - RC3: 18 `liqBarsBeyond` + 18 `liqWickBodyRatio`, GBPUSD;
  - EDGE-2: 8 displacement + 3 MSS, GBPUSD and EURUSD.
- **How an entry is accepted:** only on the same symbol, decision bar and feature with the same MQL5 and Python values. Anything else on that row still fails, and accepted ties are always listed in the report.

**Rejected alternatives:**
- **B, automatic tie rule:** more code, and it could hide a real logic bug.
- **C, journal more decimals:** an EA change that still needs a tolerance and leaves the ties.
- **D, keep 1e-9:** parity could never pass on real data.

**Result** (`B_PARITY_TOL_VERIFY_WINDOW_B.json`, sha256 `f02aa017…`):

| Symbol | Rows | Mismatches | Accepted ties | Status |
|---|---|---|---|---|
| GBPUSD | 28,527 | 0 | 40 | **PASS** |
| EURUSD | 28,563 | 0 | 7 | **PASS** |
| USDJPY | 28,363 | 0 | 0 | **PASS** |
| XAUUSD | 27,235 | 0 | 0 | **PASS** |

- **Coverage:** 43 of 48 features are compared (5 are exempt by design) and no rows were skipped.
- **Register use:** all 47 entries matched with exact values, none went unused, and the report has no notes.
- **Tests:** 5 new tests (tolerance bound; a rounding-sized drift passes while a real drift fails; a tie is accepted and reported; a tie with a different value, feature or symbol still fails; the register holds exactly the reviewed set). Full suite: **596 passed**; ruff clean.

## What remains for feature parity

1. **Stored parity reports: replaced 2026-10-03** (human-approved). `PEPPERSTONE_PARITY_FULL_B.json` is now the PASS result (`f02aa017…`, identical to `B_PARITY_TOL_VERIFY_WINDOW_B.json`), with per-symbol logs and `PEPPERSTONE_PARITY_FULL_B.provenance.txt`. The pre-fix FAIL reports are archived byte-identical as `SUPERSEDED_*_pre_parity_fixes_2026-10-03.*`. Window B is the only window with a full real-tick parity run.
2. **New windows:** any window added later needs its own ties reviewed before they go on the register.
3. **EA observation** (not parity): Friday's last bar is decided at Monday's first tick; see the B-PARITY-EDGE section above.
