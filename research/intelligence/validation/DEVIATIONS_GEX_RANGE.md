# H-GEX-RANGE deviations and gate notes (PREREG_GEX_RANGE.md)

## Probe (2026-10-23, before any yearly run)
- QC backtest 6dd7d567, January 2015, `main.py` YEAR = 0 (editor hash be086980…). Log sha256 e55652c3….
- **Checks (only these were read; the probe's ranges and gamma values were not looked at):**
  - **Columns:** QC's flattened chain has `openinterest`, `gamma`, `right`, `underlyinglastprice` (plus delta, IV, strike, expiry…). The code reads the first four.
  - **Timing:** at 09:25 ET on 2015-01-05 the chain's underlying price is 2058.2, the SPX close of **2015-01-02** (the prior trading day). The same holds on 01-06 (2020.58 = 01-05 close) and for NDX. ⇒ features are prior-close only; no look-ahead.
  - **Chain size:** SPX + SPXW ≈ 3,200–3,600 contracts a day (mean 3,641); NDX + NDXP ≈ 1,700.
  - **Runtime:** 40 s for the month (35 s inside the option reads) ⇒ about 8 minutes per year on the free node.
  - **Flags:** 19 of 21 days complete. One day had no option chain and fewer than 300 RTH bars (a market holiday), and one other day had no option chain. VIX was missing on 2 days, among them the first day of the run, because a daily-resolution index has no price before its first bar.
- **Consequence:**
  - the first trading day of each year chunk has no VIX. This affects only the secondary B2/M2 models (those days drop out of them);
  - the primary model uses the chain's own `underlyinglastprice` and is unaffected.
- **No code change; no deviation.**
