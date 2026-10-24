# 6E pilot: true CME order flow vs NEXA's Pepperstone EURUSD proxy (2026-10-11)

**Data**
- Databento `GLBX.MDP3` trades, `6E.v.0`, 2026-09-01 → 10-01.
- 636,982 trades; USD 0.80 from the free credit.
- Pepperstone EURUSD M1 (to 2026-09-25).

**Code:** `pilot_6e_analysis.py`. **Raw output:** `pilot_6e_results.json`.

**Nature:** descriptive measurement only.
- No trading rules, thresholds or returns were computed.
- n = 17 sessions in one month, so treat the figures as orders of magnitude, not estimates for other periods.
- Sep 2026 lies inside the OF campaign holdout window. That campaign is closed, and no strategy outcome was evaluated here.

**Sessions used:** 17 CME trading days = Pepperstone server days (17:00 NY start), 2026-09-02 → 09-25. Excluded:
- 09-01: partial; the file starts at 00:00 UTC.
- 09-11: the expiring September contract was thin, but `v.0` still pointed to it.

## Q1. Fills → aggressor orders ("Big Trades")

| Unit | Count | Median size | p99 | ≥ 25 lots (% events / % volume) | ≥ 50 lots | ≥ 100 lots |
|---|---|---|---|---|---|---|
| Single trade records | 636,982 | 2 | 48 | 3.24 % / 27.9 % | 0.94 % / 13.4 % | 0.17 % / 4.2 % |
| **Aggregated by matching-engine timestamp + aggressor side** | 611,821 | 2 | 50 | 3.43 % / 29.5 % | 1.01 % / 15.0 % | 0.21 % / 5.8 % |

- CME already reports one trade record per **price level** of an aggressor order. Aggregation therefore only merges multi-level sweeps:
  - 2.4 % of aggregated orders combine several records;
  - 0.6 % span more than one price.
- **The effect on "big trade" counts is small:** about +18 % more orders ≥ 100 lots.
- **`F_LAST` is not a usable order boundary in the trades schema.** It is set on only 26 of 636,982 records.
- **Not done:** grouping *separate* orders sent milliseconds apart (algo slicing, icebergs). That needs a time-window parameter that no source in the KB establishes, and it is what platform "aggregation" settings typically do. **Open: GAP-K11.**
- **Aggressor side:**
  - sell-aggressor 313,018, buy-aggressor 311,170, none 12,794 (2.0 %; implied/unspecified);
  - monthly volume was balanced: 1.64 M bought vs 1.65 M sold aggressively.

## Q2. Contract switch

- 6EU6 (instrument 10573) → 6EZ6 (instrument 5510) on **2026-09-14** (free symbology lookup).
- The `v.0` file holds one contract per day, so the switch appears as a **+40.8 pip jump** in the futures-minus-spot gap (basis): from about 0.8 pips (September contract, 1 day before expiry) to 41.6 pips (December contract).
- **Rule for any profile work:** build each session's profile from one contract only. Never mix contracts in one profile without a back-adjustment.

## Q3. Transferring futures levels to Pepperstone EURUSD

**Basis** = futures last trade − Pepperstone mid (bid + spread/2), per common minute. All values in pips.

| Measure | p50 | p90 | p95 | p99 |
|---|---|---|---|---|
| \|basis − **same-session** median\| (ideal: you know today's basis) | 0.2 | 0.5 | 0.6 | 0.8 |
| \|basis − **prior session's last-hour** basis\| (NEXA without a live futures feed; same contract) | 0.55 | 1.4 | 1.6 | 1.9 |

- **Within a session the basis is very stable.** The p50 of 0.2 pip includes the futures bid/ask bounce (half a 6E tick = 0.25 pip).
- **Day to day, the basis decays predictably as carry runs off.** The median change is −0.5 pip per session, ranging −1.6 to −0.07 (December contract: 41.6 → 37.4 over 9 sessions; the September contract converged to about 0 at expiry).
- **For context:**
  - the median true value-area width was **21 pips** (p5–p95: 13–39);
  - practitioner stops are "1–2 ticks beyond the aggressive print" = **0.5–1 pip** in 6E.
- **Consequence:** using yesterday's basis produces a transfer error (p95 1.6 pips) larger than the practitioner stop buffer. A precise tick-level entry on Pepperstone needs either a live futures price, or a carry-drift correction (untested; would need pre-registration).

**Value-area agreement** with the true futures profile (P1: real trade prices × real volume). Errors in pips, using the same-session median basis:

| Profile | \|VAL err\| p50 / p90 | \|VAH err\| p50 / p90 | \|POC err\| p50 / p90 |
|---|---|---|---|
| P2 futures M1 bars, real volume (M1-bar approximation only) | 1.0 / 6.0 | 1.0 / 5.2 | 1.0 / 18.0 |
| **P3 Pepperstone M1, tick volume** (the NEXA proxy, OF-03P) | **4.7 / 11.9** | **2.5 / 7.1** | **1.5 / 13.9** |

- **Profile-shape correlation P1 vs P3:** Spearman median 0.82 (p5 0.69).
- **No consistent sign bias** (VAL signed error p25 −4.4, p75 +4.7).
- **The proxy reproduces the shape and roughly the POC, but its value-area edges are typically several pips off:**
  - a VAL median error of 4.7 pips is about 22 % of the VA width;
  - and roughly 5–10× the stop buffer of a VAL "big trade" entry.
- **The M1-bar approximation alone (P2) costs about 1 pip.** Most of P3's error therefore comes from tick count ≠ traded volume, not from binning.
- **POC is fragile even with real data** (P2 p90 18 pips): two-peaked sessions flip the POC.

## What this means for NEXA (evidence class: NEXA, descriptive, n = 17)

1. **True Big Trades are measurable.**
   - The aggressor side is present on 98 % of 6E records.
   - Trader Dale's "≥ 25 lots" filter marks about 3.4 % of aggressor orders and about 30 % of volume, which is hardly "rare".
   - ≥ 100 lots is about 0.2 % of orders.
   - Any threshold must be chosen by the user or by a source, not here.
2. **OF-03P (proxy) and OF-03-ORIG (true) produce materially different VAH/VAL** at the precision the method needs. A result from the proxy cannot stand in for the original method.
3. **Execution on Pepperstone with futures-derived levels is feasible at the level-zone scale** (basis known to about 1–2 pips). It is **not feasible at the tick scale** without a live futures feed or a validated drift model.
4. **Costs to extend:** see `../kb/research_program/B5_DATA.md`. One year of 6E trades ≈ USD 11.5.
