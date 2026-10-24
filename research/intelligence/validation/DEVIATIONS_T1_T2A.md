# DEVIATIONS / INTERPRETATIONS: T1 (H-STATE) and T2a (H-VAR)

Written 2026-10-18, BEFORE any data. Pre-registrations: PREREG_T1_STATE.md (3a162810), PREREG_T2A_VAR.md (b65cfc41).

| # | Interpretation | Why |
|---|---|---|
| I-1 | The 20-day IB-width history (T1 IBpct, secondary only) uses the previous 20 **complete** days, including days later excluded for a roll or a missing prior day. | The IB width does not depend on the prior-day profile; the roll exclusion exists to protect the value area. |
| I-2 | Prices are `BACKWARDS_RATIO`-adjusted, so they need not sit on the 0.25 grid. Volume-at-price bins are prices rounded to the nearest 0.25. "1 tick" and "2 ticks" (stop offset, minimum R) are 0.25 / 0.50 index points. | Consistent binning; the effect is below one tick. |
| I-3 | When a T2a signal is skipped (R < 2 ticks, or V-VA target not beyond the entry), that excursion is consumed. The next trade needs a new excursion whose first bar starts after the skipped signal bar. | The pre-registration only defines this after an exit (§3). Using the same rule after a skip avoids re-using one excursion. |
| I-4 | During an excursion, a 15-minute close on the **other** side of value (jumping across it) ends the excursion without a signal and starts a new excursion on that side. A close exactly at VAL or VAH neither starts an excursion nor signals. | PREREG §3 uses strict inequalities; the jump case is not described there. |
| I-5 | Instead of a full daily R series (log-size limit on the free QuantConnect node), each T2a variant logs the daily-R moments: n, mean, sd, skew, kurtosis, and the annualised Sharpe. These are enough for the local DSR. | PREREG_T2A §8 mentions "a compact daily R series"; the moments carry the information the DSR needs. |
| I-6 | The T1 IB tercile table uses IBpct ≤ 1/3, ≤ 2/3, > 2/3. | Secondary table only; boundaries fixed here. |
| I-7 | Weekend-dated sessions (none expected in RTH data) are treated as incomplete. | Guard only. |
