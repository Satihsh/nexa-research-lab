# Audit: PHASE3_SIX_FAMILIES_V1 (2026-09-28)

**Scope:** leakage, look-ahead, accidental OOS reuse, duplicate trial definitions, and whether parameters can change after opening.
**No strategy was evaluated.** Enforcement probes ran on a scratch copy of the registry with dummy metrics (no market data, no strategy code). The real registry remains **FROZEN**, with no `results.jsonl`.

## CRITICAL

**C1. The "untouched" OOS window has already been used.**
- The campaign OOS is 2025-01-01 → 2026-08-27 and DEV/VAL are 2018–22 / 2023–24.
- Six earlier factory runs used the **identical DEV/VAL** and evaluated a **holdout of 2025-01-01 → end of data** on the same symbols (EURUSD, GBPUSD, USDJPY, XAUUSD, XAGUSD, plus Axiory XAUUSD).
- Those runs covered families directly related to F2 (breakout, trend breakout on gold) and F5 (z-score mean reversion).
- The design document cites those holdout results as "prior evidence" (lines 208, 338), so the protocols were designed with knowledge of the OOS period.
- The walk-forward years 2020–24 used for the primary BH tests are the same DEV/VAL window those runs already studied.
- **Impact:** OOS is not independent for F2 and F5, and only partly independent for F1 and F3. Only post-freeze data (FORWARD) is truly unseen.

**C2. Frozen parameters can be changed after opening.**
- PoC: after `open_evaluation`, I edited F3's protocol file (added `target_r=5`, moved the OOS start), re-hashed it in place, and a result for the new value was **accepted**.
- `record_result` → `load_protocol` checks the file against the hash **stored inside that same file**, never against the hash pinned in the frozen campaign.
- `verify_ledger()` still returned True, because the ledger chain does not cover file contents.

**C3. OOS can be used for selection.**
- "One-shot OOS" is enforced per (experiment, **config**, symbol), not per (experiment, symbol).
- PoC: OOS results for **36 of 36** F5 configurations on EURUSD were accepted.
- **Impact:** best-of-OOS selection is possible. Nothing binds OOS to the single config chosen by the pre-declared walk-forward rule.

## HIGH

**H1. The campaign manifest can be edited without detection.**
- PoC: I lowered `dsr_trial_count` from 915 to 807 and `legacy_trials` from 108 to 0 after opening; recording continued.
- `record_result` and `open_evaluation` never recompute the campaign hash, and never cross-check against the ledger's CAMPAIGN_CREATED and CAMPAIGN_FROZEN payloads.
- There is also no external anchor: the repository is not under version control, so the whole registry (protocols, campaign and ledger) could be regenerated with a self-consistent chain.

**H2. Results are not bound to periods, data or code.**
- The `period` label is supplied by the caller. Labelling an OOS computation "DEV" bypasses the one-shot rule.
- Data hashes (M1, calendar, ticks) and the execution-module hash are pinned in each protocol but **never verified** at recording time.
- `metrics` is free-form.

**H3. Causal-estimation rules are outside the frozen protocol.**
These rules exist only in the design document, which is referenced **by path, not by hash**, so they can be edited after the freeze:
- F1: surprise σ from **prior** releases only;
- F2: range-width filter from the **prior** 60 days;
- F5: σ from prior bars;
- F6: signal quantiles from **DEV only**;
- all families: purge and embargo, the walk-forward selection metric, minimum trades, the ±30 min event-exclusion window.

A leaky implementation (for example full-sample quantiles) would not violate any frozen hash.

**H4. VAL can be re-queried without limit.**
- PoC: the same configuration was recorded five times on VAL.
- VAL drives selection, so unlimited re-queries allow overfitting to VAL.

## MEDIUM

**M1. Period boundaries are under-specified.**
- There is no timezone for any period date. Bars are server-clock (NY+7) and research is UTC, a 2–3 h ambiguity at every boundary.
- There is **no purge or embargo** at DEV|VAL or VAL|OOS in the protocols. Label spans reach about 10 h (F2) and about 12 h (F3: M15 × 48), so trades opened on 2024-12-31 can resolve inside OOS.

**M2. Sensitivity axes are uncounted trials.**
- F2 `asian_end_utc` ×3, F3 `fill_rule` ×3 and F5 `session_start_utc` ×3 are not grid axes, so the registry cannot record them.
- If they are ever used to choose settings, the real variant counts are 72 / 864 / 432 against 24 / 288 / 144 declared. DSR and FDR would be understated, and the runs would be off-registry.

**M3. Primary tests are undercounted.**
- F3 makes two separate claims (H3a revisit rate, H3b trade expectancy), but only one test per symbol is counted.
- The BH family of 18 should be at least 22.

**M4. The F1 event filter uses future information.**
- `local_clock_off_mode` compares each row with the event's **modal clock over the full 2017–2026 sample**, OOS included.
- The effect is small and structural, but the exclusion set is informed by future data. The filter itself was also added after inspecting the data.

**M5. Calendar data caveats.**
- `actual` is the **first print** in 6,597 of 6,606 high-importance releases (clean).
- 1 row equals a later revision and 8 match neither; they are not yet excluded.
- Whether `forecast` is the pre-release consensus cannot be verified.
- 20% (actual) and 38% (forecast) of high-importance values are missing, which is selection by availability.

**M6. F6 tick data is not ready.**
- Tick `time_msc` is **server time**: the weekly first tick is Monday 00:01. There is no canonical, UTC-labelled tick file yet.
- The entire 21-day sample, including its OOS week (2026-09-21 → 25), was already inspected (spread by hour, flags, parity) and used to set cost assumptions.
- The same window doubles as the bar families' REAL_TICK_EXECUTION_CHECK.

## LOW

- **L1:** `config_id` is type-sensitive (`1` ≠ `1.0`). It causes false rejections, not duplicates.
- **L2:** F3's NEXA-DNA inputs (f13/f14) exist only for 2024–26 (VAL + OOS), not DEV. Only counts were inspected, no outcomes.

## Checked and clean

- **Duplicate trials:** 0 within any grid and 0 across experiments. The 807 declared active trials match the grids (F4's 32 excluded as BLOCKED).
- **Canonical M1:** 0 overlap conflicts. Rebuilt M5/M15/H1 match the broker's bars (≤ 2.8e-5 mismatch).
- **Time convention:** NY+7 verified. Calendar export-offset basis verified (NFP 115/116).
- **State machine:** the real registry refuses evaluation while FROZEN; BLOCKED F4 cannot be evaluated; the ledger is intact.

## Implication
As frozen, V1 **must not be opened**: C2, C3 and H1 let parameters, selection and trial counts change after opening, and C1 means its OOS is not untouched. A V2 would need all of the following:
- protocol hashes verified against the campaign at every call;
- a campaign hash plus ledger cross-check;
- OOS one-shot per experiment × symbol, restricted to the walk-forward-selected config;
- a VAL query budget;
- results bound to period dates and data/code hashes;
- causal rules, purge/embargo, timezones and sensitivity axes inside the protocol;
- the design document hash-pinned;
- an external anchor (git tag or published hash);
- a fresh untouched OOS (FORWARD data only) or an explicitly downgraded OOS status.
