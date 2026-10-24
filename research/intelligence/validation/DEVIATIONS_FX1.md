# FX1 deviations and implementation notes (fixed before discovery opened; hashed with the code)

**Context:**
- Pre-registration: `PREREG_FX1_FIX_REVERSALS.md` (sha 18207319…).
- **No FX1 outcome had been computed when these were fixed.**
- The only engine output seen is D10: counts, missing counts and stop rates, no P&L.

| # | Item | Resolution | Reason |
|---|---|---|---|
| D1 | Interpreter | System python3 (numpy / pandas / scipy), the same as IM1. The DSR is computed in-run (`nexa_robust.deflated_sharpe`) | — |
| **D2** | Day assignment (§2 "start date in its anchor clock") | Day d = the fix date. **All three windows of date d lie inside server day d** (NY + 7 h; unit-tested across DST and mismatch weeks): W1 starts 00:55 UTC d, W3 ends 16:55 NY d = 23:55 server d. Eligibility = weekday server day, ≥ FIRST_DAY, COMMON §C4 valid, fix published (D3), entry and exit bars present | One consistent day key; the day-block bootstrap keeps all trades of a server day together |
| **D3** | Publication calendars (§2) | `FX1_CALENDARS.json`: Tokyo closed = `C1_JP_HOLIDAYS.json` dates (205, including Dec 31–Jan 3); ECB closed = TARGET (Jan 1, Good Friday, Easter Monday, May 1, Dec 25, Dec 26; 2017–2026, 60); WMR closed = Jan 1, Dec 25 (20). **US holidays are not excluded** (§2 lists only the three fix calendars). Thin US-holiday server days still fall out through COMMON §C4 | As pre-registered |
| D4 | σ̂ warm-up (§3) | σ̂_W = sd of the cell's window log return (close of the exit bar / open of the entry bar) over the previous 60 eligible days **that have both bars** (causal, `shift(1)`). The first 60 such days per cell (≈ Jul–Sep 2017) have no σ̂ and count as missing | Same as IM1 D6 |
| D5 | Stress levels | The trade path (stop, exit) does not depend on stress. Each trade is simulated once; net_Sx = pnl − commission − 2 × stress × 10⁻⁴ × entry price. This is algebraically identical to IM1 | Speed |
| D6 | Spread for a trade | s = `Sym.sprd` of the **server day of the entry bar** (trailing-20-valid-day median of the daily p90, days ≤ d − 1), floored at 0.2 pip | As IM1 |
| **D7** | Placebo (§5) | For each real (day, window, pair): the same window shifted by δ ∈ {−720 … +690 min step 30, \|δ\| > 90} (41), same direction, same fix-calendar day set. **Excluded (counted)** if the closed interval [start, end] intersects 16:55–17:05 NY of any date. Each placebo cell has its own causal σ̂ (as IM1). The pooled placebo mean at δ = equal weight per trade over all 9 cells. p_tod = (1 + #{placebo mean ≥ observed}) / 42 | As §5 |
| D8 | REJECTED sign rule (§7) | "Discovery and holdout signs opposite" is evaluated on **S0** net, the same as the pooled-S0 rule (as IM1 code) | The S0 / S1 choice would otherwise be ambiguous; S0 is the less strict reject |
| **D9** | Criterion 8 | Evaluated per cell (median stop / (commission + spread) ≥ 5 in every cell). **Disclosure:** the cost-floor skip (cost > 0.20 × stop) makes every traded trade ≥ 5 by construction, so criterion 8 is mechanical. The skip count is reported | Transparency |
| D10 | Smoke test | Before hashing: EURUSD and USDJPY, 2017-07 → 2017-12 (inside discovery). Printed counts only: 129 server days; trades 63 / 68 / 66 (W1 / W2 / W3); missing 60 / 60 / 63 (warm-up); stop rate 0 to 0.015. **No P&L** | Runtime check |
| D11 | N2 gross replication (§5) | Per cell: the unconditional window return (bid close of the exit bar / bid open of the entry bar − 1, in bp), **in foreign-currency terms** (USDJPY sign flipped), on all fix-eligible days with both bars. No stop, no costs, no σ̂ requirement. Day-block bootstrap CI. Compared with the paper's Table I sign and size | §5 |
| D12 | Stage execution | A stage evaluates only days ≤ its end date (disc → 2022-12-31; val → 2024-12-31; full → 2026-09-25). σ̂ and spread use only earlier days | Opening each split once (as IM1 D9) |
| D13 | §8 "paper fixed ET boundaries" | W1 = 20:55 ET on the **previous NY calendar date** → 02:00 ET d; W2 = 02:00 → 08:15 ET; W3 = 11:00 → 16:55 ET (the 16:55 end kept, as primary) | The paper's 20:55 ET Tokyo fix falls on the previous NY date |
| D14 | §8 robustness definitions | "W3 to 17:00": exit bar 16:59 NY (still server day d). "Equal weight per day": the mean of day means, day-block bootstrap. "Only W2 + W3": the primary table without W1 | — |
| D15 | Criterion 6 "no year > 40 %" | Requires total pooled net > 0 and every year's share of the total ≤ 0.40 (signed share) | With a negative total, shares are not meaningful; the criterion fails |
| D16 | Secondaries (§6) | The 3 windows (pairs pooled) and the 3 pairs (windows pooled); BH on one-sided bootstrap p. DSR trials = P + 6 secondaries + 41 placebo-offset pooled series = 48; var_SR over those 48 | As §6 |
