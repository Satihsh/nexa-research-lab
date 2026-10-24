# 19: DATA REQUIREMENTS

## Cost rules

- **Prices are not estimated here.** The only figures quoted are those stated in a corpus source:
  - S53 §5: CME and COMEX non-professional top-of-book options data at $2/month each via Sierra Chart's Denali feed, plus a $36.00/month platform package and a $2.80/month surcharge, as of July 2026.
- **Everything else is "quote required".**
- **No subscription, purchase or account change is made or implied.** Each requires explicit approval.

## 1. Already sufficient (no new data needed)

| Need | Source | For |
|---|---|---|
| Spot price and volatility, 9 years | MT5 M1 canonical | HYP-001b, 002, 004–015, 019–021, 023, 024, 031 |
| Exchange futures volume, 2 years, 1 minute | Massive (current plan) | HYP-001, 016, 034; true-volume profiles |
| GLD option bars and contract lists, 2 years | Massive (current plan) | HYP-028, 030 (weak proxies) |
| Treasury yields | Massive | HYP-031 |
| Own execution data | S14 demo + NEXA_TickLogger (running since 2026-10-04) | HYP-033, 035, 017b |

## 2. Requirements by blocked hypothesis

| Priority | Data | Unblocks | Candidate source (verify) | Notes |
|---|---|---|---|---|
| **D1** | **Longer forward tick history** for the 4 symbols (quotes) | Reproducible tick features; Hawkes (HYP-033); spread regimes | **Already running** (NEXA_TickLogger, S14 demo) | Note: the logger's timestamps are whole seconds. A ms-resolution logger would be a separate approved change |
| **D2** | **Futures trades with aggressor side (or BBO quotes for Lee–Ready)** for GC, 6E, 6B, 6J | True delta, footprint, imbalance; BVC validation; HYP-017/018/022 on true data | Massive futures trades/quotes (NOT_ENTITLED on the current plan; check plan tiers). CME DataMine. Exchange-licensed vendors | Largest analytical upgrade for T1 |
| **D3** | **COMEX gold options (OG): daily per-strike OI + settlement/IV, ≥ 2 years history** | GEX, flip, walls, HPR (HYP-025–027, 029) | CME DataMine (historical). Or *prospective* daily collection via a licensed feed (S53's Sierra/Denali route) | Without history, start prospective collection and wait ≥ 250 sessions |
| **D4** | **Signed option volume** (customer vs market-maker, open/close) for gold options | GEX **sign** identification (CN1; S50 used ISE Open/Close for equities) | Exchange open/close datasets (availability for COMEX: unknown, verify) | Without it, report both sign models (S54) |
| **D5** | **XAU broker DOM (depth 10) logging**, prospective | First resting-liquidity measure (broker book) | MT5 `MarketBookAdd`, a new logger (needs approval; must not touch the S14 EA) | Broker-specific, not an exchange book |
| **D6** | **Massive options snapshot / OI** (GLD) | Proxy positioning (still not COMEX) | Massive higher tier (NOT_ENTITLED now; verify whether historical OI is offered at all) | Low value for gold; S53 rejects ETF proxies |
| **D7** | **VIX / index levels** | Cross-asset risk context (HYP-031/032 extension) | Massive indices tier (NOT_ENTITLED); or VX futures via the futures API (not probed) | Low priority |
| **D8** | **Corrected-offset news calendar with consensus/actual** | H-NEWS-PTD, news gates | Existing MT5 calendar (offset fix per memory) | Small |

## 3. Data-engineering requirements (no purchase; research tier)

1. **Roll calendar** for each futures product: pre-declared rule (15 §6 N4).
2. **Causal basis series** b̂_t per instrument (EQ-026), with roll resets.
3. **Session-anchor tables** in UTC with DST rules (06 §3).
4. **Entitlement-window registry:**
   - Massive history starts about 2 years before "today" and moves forward daily;
   - **store pulled data locally with hashes** so that analyses remain reproducible after the rolling window advances.
   - Massive workspace tables expire after 1 hour.
5. **Proxy tags** carried in every derived dataset (TRUE/PROXY; source F/T/MFX/OPT).
6. **Disk:** about 3.6–5 GiB free (memory). Two years of 1-min futures for 4–5 products is about 0.5M rows each; store as gzip CSV or Parquet.

## 4. Minimum viable data plan (recommended order)

1. **D0 (no cost):**
   - pull and archive 2 years of Massive 1-min futures (GC, 6E, 6B, 6J, ES) plus FX aggregates, with hashes;
   - run candidates 1–2 (17).
2. **D1 (running):** let S14 demo fills and tick logs accumulate.
3. **Decide D2 vs D3 on evidence:**
   - if the proxy-based WHERE/WHEN study (HYP-022) shows any conditional value, **D2** (true flow) is the higher-value upgrade;
   - **D3** (gold options OI) is justified only to test the *volatility channel* (HYP-025) first, because that is the only academically supported GEX claim.
