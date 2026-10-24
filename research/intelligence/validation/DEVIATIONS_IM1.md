# IM1 deviations and implementation notes (fixed before discovery opened; hashed with the code)

**Context:**
- Pre-registration: `PREREG_IM1_INTRADAY_MOMENTUM.md` (sha aee2e870…).
- **No IM1 outcome had been computed when these were fixed.**
- The only engine output seen is D7: counts and a stop rate, no P&L.

| # | Item | Resolution | Reason |
|---|---|---|---|
| **D1** | Calendar (§2) | `IM1_US_CALENDAR.json` (149 dates) = MT5 US type-2 holidays 2017–2026 (110; federal list, including Columbus / Veterans Day and Juneteenth) **∪ Good Friday** (10, computed) **∪ CME early closes** (Fri after Thanksgiving; Dec 24, Dec 31 and Jul 3 when weekdays; 32) | §2 intends "US exchange holidays". Good Friday is an exchange holiday missing from the MT5 federal list. Columbus / Veterans Day are kept because the MT5 list is the stated source (conservative exclusion) |
| **D2** | Placebo count (§5) | The stated rule (every 15 min, 06:00–16:45 ET, excluding \|t − C\| ≤ 75 min) yields **33** times per instrument, not 37. **DSR n_trials = 1 + 4 + 33 = 38** (not 42) | The pre-registration contains an arithmetic error. The rule governs |
| D3 | Interpreter | System python3 (numpy 2.1.3, pandas 2.2.3, scipy 1.15.2), the same as C1 / C2. The DSR is computed in-run | — |
| D4 | "Valid previous close day" (§2) | The previous **eligible** day (weekday, not in the calendar, COMMON §C4 valid), at most 4 calendar days earlier. Otherwise the day is skipped and counted as missing | Spans weekends and single holidays |
| D5 | r_ROD = 0 | No trade, not counted (§3 "no trade if = 0") | — |
| D6 | σ̂₃₀ warm-up | The first 60 eligible days per instrument and close time have no σ̂ and count as missing (≈ the first quarter of each series) | Causal 60-day window (§3) |
| D7 | Smoke test | Before hashing: EURUSD 2017-07 → 2017-12 and XAUUSD 2018-01 → 2018-06 (inside discovery). Only trade counts, missing / skip counts and the stop rate were printed (61 / 61 / 0 / 0.0 and 65 / 60 / 0 / 0.0), **no P&L** | Runtime check |
| D8 | Pooled placebo (§5) | The k-th placebo time of each instrument is pooled with the k-th of the others (equal weight per trade). p_tod = (1 + #{pooled placebo mean ≥ observed}) / 34 | As §5 ("same C′ offset rank") |
| D9 | Stage execution | A stage evaluates only days ≤ its end date (disc → 2022-12-31; val → 2024-12-31; full → 2026-09-25). σ̂ uses only earlier days (causal) | Opening each split once |
