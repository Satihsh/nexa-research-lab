# NEXA Strategy Factory: research design for six new hypothesis families

**Phase 1 only.** Design, no strategy code, no results. Date 2026-09-27.
**Status of every claim below:** the families are **hypotheses**. None is assumed to exist, to be profitable, or to reflect any institutional mechanism.

Scope guards (unchanged): one NEXA system; research tier only; `NEXA_Risk.mqh`, schema v1.0 and f00–f47 untouched; no live trading; no Astra; nothing is optimised toward a win rate. Any family that survives would enter NEXA as a Strategy Factory family, which proposes; NEXA's deterministic gates and `NEXA_Risk.mqh` still authorise.

---

## 0. Evidence base: what data actually exists (measured today, not assumed)

| Source | What | Coverage | Resolution | Limits (measured) |
|---|---|---|---|---|
| Pepperstone ticks (`data/pepperstone/*_ticks_recent.csv.gz`) | bid, ask, ms timestamp, flags | **2026-08-28 → 2026-09-25 only (21 trading days)**, EURUSD 2.46M, GBPUSD 5.41M, USDJPY 3.45M, XAUUSD 10.84M, XAGUSD 4.18M ticks | ms (99.9% sub-second) | **Quote-only:** `volume=0` and `last=0` on 100% of ticks; no BUY/SELL aggressor flags; undocumented flag bits 128/1024. One market regime. |
| Pepperstone M1 (Strategy Tester export, `NEXA_BarExport`) | OHLC, tick volume, bar spread | 2024-01 → 2026-09 already exported for 4 core symbols; deeper history exists (tester: "history data begins 1993" for GBPUSD) and can be exported in chunks | 1 min | Bar spread = one spread value per bar, not intrabar. Pre-2026-08-28 tester ticks are generated, not real. |
| Pepperstone M1 (Python API) | same | last 99,998 bars only (≈ 2026-06-16/22 → 09-25) | 1 min | Capped by terminal `maxbars`. |
| Pepperstone H1 (tester export) | OHLC, spread | 2016-12-30 → 2026-09-25, 5 symbols | 1 h | – |
| Pepperstone D1 | OHLC | 2000 → 2026 (core), 91 FX pairs | 1 day | – |
| Pepperstone costs | spread + commission | measured | – | **Commission $3.50/lot/side** (tester). EURUSD tick spread ≈ 0 pts in session, **42 pts median at server 00 (rollover)**; XAUUSD ≈ 11 pts ($0.11) in session, 17 pts at 23/01. Latency to server ≈ 251 ms (terminal log). |
| NEXA Trade DNA (Pepperstone batch) | f00–f47 per closed M1 bar | 3,927,131 decisions, 4 symbols, 2024-01 → 2026-09 | 1 min | f13/f14 (FVG) are parity-verified (0 mismatches). The liquidity machine is 0.2–0.85% divergent. |
| MT5 economic calendar | event time, importance, actual/forecast/previous, revisions | via MQL5 `CalendarValueHistory()` in a **live** terminal | event timestamp in **trade-server time** | **Not yet exported.** Unavailable in the Strategy Tester (NEXA log: "economic calendar unavailable in Strategy Tester"). The bridge tool `get_economic_calendar` is a third-party Forex Factory weekly feed, **not** the MT5 calendar, and returned 0 events. |
| DOM (market depth) | book levels | – | – | Bridge `get_market_depth`: `available=false` for XAUUSD and EURUSD (checked on a weekend). XAUUSD contract reports `ticks_bookdepth=10`, so **re-check in open market**. Unproven. |
| Second feed | – | IC Markets / MetaQuotes: 2024 M1 FX only, MT5 `.hcc` binary, no ticks, no XAU; Axiory XAUUSD M1 to 2026-07-31 | 1 min at best | **No two tick feeds with a common clock exist.** |

**Time normalisation (applies to every family). CORRECTED in Phase 2:** Pepperstone server time is the **"New York close" convention: server = New York local time + 7 h**. That means UTC+2 while New York is on EST and UTC+3 while it is on EDT, switching on the **US** DST dates, not the EU dates this document originally stated.

Evidence (`reports/TIME_CONVENTION_EVIDENCE.json`): over 144 weeks × 4 symbols, the FX open is Monday 00:01 server time (Sunday 17:01 New York) and gold opens at Monday 01:01 (Sunday 18:01 New York), including every week between the US and EU switches.

NEXA's fixed `InpGMTOffset=2` is therefore 1 h wrong from the second Sunday of March to the first Sunday of November (open defect D-TZ). Research code converts **only** through `research/nexa_time.py`. The MT5 calendar is stamped in trade-server time and goes through the **same** conversion. All windows ("Asian session", "London open", event time) are defined in **UTC** and converted per bar. A session defined in fixed server hours is itself a DST bug.

---

## 1. Shared methodology (applies to all six families; family sections list only deviations)

### 1.1 Outcome unit and metrics
- Every trade is measured in **R = realised P/L ÷ initial risk**, net of spread, commission and slippage, from the **actual** simulated entry (`nexa_factory.simulate` conventions: next-bar/next-tick entry, bid bars, stop wins an ambiguous bar, gaps fill at the open).
- **Reported for every configuration, IS and OOS separately:**
  - win rate and loss rate;
  - expectancy E[R] with block-bootstrap 95% CI;
  - median R, profit factor, max drawdown (R);
  - MAE and MFE (R): mean and median;
  - Sharpe and Sortino per trade (only when n ≥ 100 and trades are non-overlapping; otherwise marked N/A);
  - trade frequency (per week), exposure (% of time in market);
  - spread, commission and slippage cost, each as R and as % of gross;
  - modelled execution latency and fill probability (limit-order families);
  - regime stability (E[R] by vol regime × trend regime × session × year);
  - parameter stability (sensitivity surface, §1.7);
  - OOS performance, and **degradation D = E[R]_OOS ÷ E[R]_IS** (flagged if D < 0.5 or the sign flips).
- **Win rate is never a selection criterion.** A configuration with 80% wins and E[R] ≤ 0 is a failure.

### 1.2 Cost model (defaults; each family can only make it harsher)
| Component | FX majors | XAUUSD | Source |
|---|---|---|---|
| Spread | per-bar recorded spread (M1), or per-tick ask−bid when ticks exist | same | measured |
| Commission | $7.00/lot round trip ($3.50/side), i.e. 0.7 pip EURUSD | $7.00/lot RT = $0.07/oz | tester-observed |
| Slippage | adverse 0.5 × spread + 0.1 pip base; ×3 inside ±2 min of a high-impact event | adverse 0.5 × spread + $0.05; ×3 at events | assumption, stressed in §1.6 |
| Latency | signal at bar/tick close → fill at first quote ≥ 250 ms later | same | measured ping 251 ms |
| Swap | applied on positions crossing server 00:00 at `swap_long/short` from `contracts.json` | same | measured spec |

### 1.3 Null hypotheses and baselines (every family has at least these three)
1. **Timing null:** same number of trades, the same signal timestamps, **random direction**. This tests whether the rule's direction adds anything.
2. **Direction null:** same directions, entries at **random times** drawn from the same session/hour-of-week distribution. This tests whether the rule's timing adds anything.
3. **Circular-shift null:** the signal series shifted by a random offset of ≥ 1 week within each year. This preserves autocorrelation and frequency and destroys the alignment.

A family must beat **all three** after costs. The random-entry result on XAUUSD (a coin flip beat the trend rule, twice, on two feeds) is the reason null 1 is mandatory.

### 1.4 Statistical tests
- **Primary:** H0: E[R_net] ≤ 0. One-sided **stationary block bootstrap** CI (block ≈ max holding time), plus a **permutation p-value versus each null** (≥ 5,000 draws, seeded).
- **Multiple testing:** every (family × configuration × symbol) tried is registered before any result. The total trial count feeds **Benjamini–Hochberg (q = 0.10)** across all six families, and the **Deflated Sharpe Ratio** with that count. **PBO via CSCV** runs across each family's configuration grid. The existing XAUUSD and Pepperstone factory trials (108) count toward the running total.
- **Dependence:** overlapping labels are purged; a HAC (Newey–West) SE is reported alongside the bootstrap for regression-style tests.
- **Minimum sample:** 30 trades to report, **200 trades** to be eligible for promotion (matches NEXA's validate gate).

### 1.5 Walk-forward and untouched OOS (bar-based families 1, 2, 3, 5)
- **Protocol frozen and hashed before the first run** (as `nexa_factory_run.PROTOCOL`).
- **DEV:** 2018-01-01 → 2022-12-31 (needs a chunked M1 export 2017-07 → 2022-12; H1 already exists).
- **VAL:** 2023-01-01 → 2024-12-31.
- **Walk-forward:** anchored, yearly re-selection on all prior years; purge = max holding time; embargo = 1 day.
- **Untouched OOS:** 2025-01-01 → 2026-08-27 (generated-tick era), evaluated **once**.
- **Real-tick execution check:** 2026-08-28 → 2026-09-25 re-runs the frozen OOS configuration with real ticks to measure the M1-vs-tick fill discrepancy. It is **not** a second OOS.
- **Forward holdout:** data collected after the protocol hash (via `NEXA_TickLogger`) is the only truly unseen period.

Tick-based families (4, 6) cannot use this calendar; see §6.M and §4.M.

### 1.6 Monte Carlo and robustness
- trade-order bootstrap (drawdown, P(hit NEXA 10% max DD) at 0.30% risk per R);
- block bootstrap of returns;
- cost shocks: spread ×1.5, ×2, ×3; commission ×1.5; slippage +1 spread;
- latency shocks: 250 → 500 → 1,000 ms;
- missed fills: randomly drop 10% / 25% of entries;
- regime holdouts: leave-one-year-out, leave-one-symbol-out.

### 1.7 Parameter sensitivity
- Each parameter gets a **pre-declared grid** of 3–5 values.
- Report the E[R] surface. A result counts as **stable** only if ≥ 70% of neighbouring grid cells keep E[R] > 0 and the CI sign.
- An isolated peak is classified as overfit, whatever its OOS number.

### 1.8 Common failure criteria (any one fails the family)
- E[R]_OOS CI includes 0, or doesn't beat any one of the three nulls after BH-FDR.
- E[R] < 0 at spread ×2 or latency 500 ms.
- PBO ≥ 0.5, DSR < 0.95, or parameter surface unstable.
- D = E[R]_OOS / E[R]_IS < 0.5 or sign flip.
- Result driven by one year or one symbol (leave-one-out flips the sign).
- Fewer than 200 OOS-eligible trades.

---

## 2. Family 1: MACRO EVENT VOLATILITY

**Hypothesis.** After a scheduled high-impact macro release, two separate claims are tested:
- **(H1a)** post-release absolute returns exceed a matched baseline (a volatility claim; expected true and **not tradable by itself**);
- **(H1b)** the sign of the post-release move, **after the initial spike**, follows the sign of the standardised surprise more often than chance and **after costs**.

"News always causes continuation" is **not** assumed; reversal is an equally admissible outcome.

**A. Measurable definition.** For event e at UTC time τ_e with actual A, forecast F and historical surprise std σ_k of that indicator:
- S_e = (A − F) ÷ σ_k (σ_k estimated only from **prior** releases of the same indicator).
- Currency sign c_e = +1 if a positive surprise is conventionally positive for the event currency (−1 for unemployment-type indicators; the map is fixed in advance).
- Instrument sign g = +1 if the event currency is the base currency, −1 if it is the quote.
- Post-release return r_e(Δ,H) = ln(P(τ_e+Δ+H) ÷ P(τ_e+Δ)).
- H1a: E[|r_e(0,H)|] ÷ E[|r_base(0,H)|] > 1, against the same weekday and time in non-event weeks.
- H1b: E[g·c_e·sign(S_e)·r_e(Δ,H)] > 0, with Δ ≥ 1 min so the spread spike is excluded.

**B. Inputs.**
- MT5 calendar: `event_id`, `time`, importance, `actual_value`, `forecast_value`, `prev_value`, `revised_prev_value`, `currency`. These come from a **new read-only MQL5 export script** (`CalendarValueHistory` over 2018–2026) run in the live terminal. Timestamps are server time, converted with §0.
- Pepperstone M1 with per-bar spread; ticks only for 2026-08-28 onward.

**C. Entry.** Only HIGH-importance events of USD/EUR/GBP/JPY with |S_e| ≥ z* (z* ∈ {0.5, 1.0, 1.5}), and no other high-impact event within ±30 min. Enter at the open of the M1 bar at τ_e + Δ (Δ ∈ {1, 2, 5} min), direction g·c_e·sign(S_e). Skip if the recorded bar spread > 3× that hour's median.

**D. Exit.** First of: stop (E), target k·R (k ∈ {1, 2}), or time exit at τ_e + Δ + H (H ∈ {15, 30, 60} min).

**E. Stop.** max(1.5 × pre-event ATR(M1,14) measured at τ_e − 1 min, the range of the bars between τ_e and τ_e + Δ), placed beyond the post-release extreme.

**F/G. Costs, spread, slippage.** §1.2 with **event slippage ×3**, and the entry-bar spread used as-is (never the hour median). Pre-2026-08 there are no real ticks at releases, so the M1 bar spread **understates** the release-second spread. Every event trade is also stress-tested at spread ×5.

**H. Max hold.** 60 min.

**I. Invalidation.**
- The event is rescheduled or revised (calendar `change_id`); `actual` is missing at τ_e + Δ.
- Multiple same-currency events coincide.
- The FOMC gate or NEXA's news veto would block (see Data limitations: conflicts with NEXA's own vetoes).

**J. Expected failure mode.** The spike reverses within minutes (whipsaw). Spread and slippage consume the move. The consensus forecast is stale or mis-specified. A timezone error shifts τ_e by 1 h (D-TZ), giving a silent look-ahead or look-behind.

**K. Nulls.** §1.3, plus a **surprise-shuffled null**: permute S_e across events of the same indicator.

**L. Test.**
- H1a: ratio test with bootstrap.
- H1b: permutation test of E[R_net]. Also regress r_e on S_e with HAC SE (reported, not used for selection).

**M/N. WF/OOS.** §1.5. Unit = event. An estimated ~8–15 qualifying high-impact USD/EUR/GBP events per month gives roughly 200–400 per year across four symbols (to be counted from the export, not assumed).

**O/P.** §1.6 plus a timestamp-jitter test (τ_e ± 1 min; a result that flips is fragile). Grid: z* × Δ × H × k = 3×3×3×2 = 54 configs per symbol.

**Target labels.** Triple-barrier (stop / k·R / H) from τ_e + Δ. MFE/MAE in R.

**Execution model.** Market order at the next quote ≥ 250 ms after the τ_e + Δ bar open, filled at ask/bid + event slippage.

**Implementation complexity: MEDIUM-HIGH.** A new MQL5 calendar export script, a DST-aware time normaliser, a per-indicator surprise-σ table built causally, and event-level simulation.

**Data limitations.**
1. The calendar isn't exported yet.
2. No historical release-second ticks (M1 only before 2026-08-28).
3. Forecast values are the provider's consensus, with unknown revision history.
4. **Architecture conflict:** NEXA deliberately vetoes trading around news (Tier-3 news veto, FOMC hard gate). A validated macro family would require an explicit, human-approved design for how it coexists with those gates. It can **never** bypass them silently.

---

## 3. Family 2: XAUUSD SESSION BREAKOUT

**Hypothesis.** A close beyond the XAUUSD Asian-session range during the early London window is followed by further movement in the break direction more often than for matched random breaks, after costs. "Breakouts continue" is **not** assumed. NEXA's own liquidity engine treats the Asia high/low as a sweep-and-reclaim (reversal) level, so this family and NEXA's core logic predict **opposite** outcomes at the same level. Both are tested on the same data, and only evidence decides.

**A. Definition.**
- Asian range on day d: R_d = [L_d, H_d] = min low / max high of XAUUSD M1 bars with UTC time in [00:00, 06:00).
- W_d = H_d − L_d. Breakout-window bars t ∈ [06:00, 10:00) UTC.
- Long break: close_t > H_d + b·W_d. Short break: close_t < L_d − b·W_d.
- Continuation label: the price reaches entry + k·(risk) before the stop.

**B. Inputs.** Pepperstone XAUUSD M1 (chunked tester export 2017-07 → 2026-09) with bar spread. ATR(M1,14) and D1 ATR(14) from prior days only.

**C. Entry.** First qualifying break of day d only, b ∈ {0, 0.1, 0.25}. Skip if W_d is outside [0.3, 2.0] × median(W over prior 60 days), which excludes dead and extreme Asian sessions. Skip if a high-impact USD event falls within ±30 min (§2 calendar). Enter at the next bar open.

**D. Exit.** Stop, target k·R (k ∈ {1, 1.5, 2, 3}), or a time exit at 16:00 UTC (London/NY overlap end).

**E. Stop.** At the opposite side of the range midpoint, (H_d + L_d)/2. Variant: 1.0 × ATR(M1 at entry) × 10. Both are pre-declared.

**F/G.** §1.2 with XAU costs: tick spread ≈ $0.11 (measured), commission $0.07/oz RT, slippage $0.05 + 0.5 spread.

**H. Max hold.** Until 16:00 UTC (≤ 10 h).

**I. Invalidation.** Price re-enters the range and closes inside for 3 consecutive M1 bars (optional exit variant, pre-declared). The day is a holiday (no Asian session bars). A weekend or Monday gap distorts the range.

**J. Failure mode.** False breaks that are liquidity sweeps (NEXA's own thesis). Gold's secular drift makes long breaks look good while shorts fail. (Seen twice already: split all results by direction and report the drift-matched null.)

**K. Nulls.** §1.3, plus a **random-range null**: a range of the same width W_d placed at random offsets around the actual Asian mid, with the same break rule.

**L. Test.** Permutation vs the three nulls. The direction split (long versus short, each must be > 0) is mandatory because of gold drift.

**M/N.** §1.5, one trade/day at most, so ≈ 1,500 trading days in DEV+VAL and ≈ 420 in OOS.

**O/P.** §1.6. Grid: b × k × stop-variant = 3×4×2 = 24 configs. Also test sensitivity to the session boundary (Asian end 05:00/06:00/07:00 UTC). If the result depends on the exact boundary, it is overfit.

**Labels.** Triple-barrier from entry, MFE/MAE.

**Execution.** Market order at the next bar open + latency. Real-tick check on 2026-08-28 → 09-25.

**Complexity: LOW-MEDIUM.** It reuses `nexa_factory.simulate`; the M1 export is the main cost.

**Data limitations.** Only XAUUSD is required, but M1 before 2024 needs a chunked tester export (no massive new download: the history is already in the local Pepperstone base). Bar spread is a single value per bar at the London open. Relationship to prior evidence: the factory's Donchian/TrendLock breakouts on Pepperstone XAUUSD H1 did **not** beat the random-entry baseline. This is a narrower, session-conditioned variant, so its trials add to the multiple-testing count.

---

## 4. Family 3: IMBALANCE / FVG RETRACEMENT

**Hypothesis.** Split into two claims so the base-rate trap can't hide:
- **(H3a)** Price revisits a fair-value-gap zone **more often than it revisits matched non-FVG zones** of equal size and distance. "FVGs must fill" is **not** assumed; small nearby zones get revisited by ordinary noise.
- **(H3b)** A limit entry at the zone, **conditional on being filled**, earns E[R_net] > 0 and beats the same entry at matched random zones.

**A. Definition.** On closed bars (M5 and M15 primary; M1 secondary), using NEXA's own definition (f13/f14):
- Bullish FVG at t: low_t > high_{t−2}, with zone Z = [high_{t−2}, low_t] and size s = low_t − high_{t−2}.
- Bearish FVG is the mirror.
- Qualifying: s ≥ m·ATR_t (m ∈ {0.1, 0.25, 0.5}) and bar t−1 is a displacement bar (|body| ≥ 1.2·ATR, NEXA's f08/f09 threshold).
- H3a label: the zone is touched within N bars (N ∈ {12, 48}).
- H3b: a limit order at the zone edge nearest price (variant: zone midpoint).

**B. Inputs.** Pepperstone M5/M15/M1 bars (tester export) with spread. NEXA's journaled f13/f14 (FVG active) and f08–f10 (displacement) in the 3.93M-row Pepperstone Trade DNA are **parity-verified**, so H3a can first be tested on NEXA's own features without re-implementation, then re-derived in Python for M5/M15.

**C. Entry.** Pending limit order placed at the close of bar t, valid for N bars. **Fill rule:** a buy limit fills only if ask ≤ limit − 1 point (a touch is not a fill). On bars this approximates to bar low + spread < limit, and it's validated against real ticks for 2026-08-28 → 09-25.

**D. Exit.** Stop, target k·R (k ∈ {1, 2, 3}), or time exit at N_hold bars.

**E. Stop.** Beyond the far edge of the zone + 0.25·ATR (the gap is "invalidated" if fully traded through).

**F/G.** §1.2. Limit orders pay no entry spread in the book sense, but the fill condition above already requires the ask/bid to trade through. Commission is unchanged. Slippage is 0 on limit entry and applies on stop exit.

**H. Max hold.** 48 bars of the entry timeframe.

**I. Invalidation.** Price closes beyond the far edge before the fill (cancel the order). A new opposite FVG forms. A high-impact event within the validity window.

**J. Failure mode.** **Adverse selection:** limit orders fill preferentially when price is running through the zone, so fills are conditionally bad. Fills at bars are over-counted relative to real ticks. Size and displacement thresholds get data-snooped.

**K. Nulls.** §1.3, plus the **matched-zone null** (the core null for this family): for every real FVG, a zone of identical size at the same distance from price at the same time, but with no gap structure. Its touch rate is the H3a baseline, and its limit-entry outcome is the H3b baseline.

**L. Test.**
- H3a: difference of touch proportions (FVG versus matched zone), cluster bootstrap by day.
- H3b: permutation vs the matched-zone null on E[R_net] **of filled trades**. Also report the **fill probability** and the **E[R] of all placed orders** (unfilled = 0R), so a high filled-trade win rate can't mask a low fill rate.

**M/N.** §1.5. The event count is large (thousands per year per symbol on M5), so identifiability is high.

**O/P.** §1.6 plus fill-rule sensitivity (touch versus 1-point through versus 2-point through). A result that only exists under "touch = fill" is rejected. Grid: m × N × k × entry-point = 3×2×3×2 = 36 per timeframe.

**Labels.** H3a: touched-within-N (binary). H3b: triple-barrier on filled orders.

**Execution.** Limit order with the trade-through fill rule and 250 ms latency on placement (the order is live only from bar close + 250 ms).

**Complexity: LOW-MEDIUM.** The definition already exists in NEXA (parity-verified); a pending-order simulator is new.

**Data limitations.** Intrabar path is unknown before 2026-08-28, so fill realism rests on the 21-day tick validation. The zone definition overlaps NEXA's existing f13/f14. If H3 is validated it becomes a **feature-conditioned rule inside NEXA's existing schema**, needing no schema change.

---

## 5. Family 4: CROSS-FEED LATENCY / LEAD-LAG

**Hypothesis (three separate claims, never merged):**
- **(L1) Observed feed lead.** Price changes in feed A predict price changes in feed B at lag ℓ > 0.
- **(L2) Executable lead.** After our own latency (≈ 250 ms to Pepperstone), feed-B quote staleness is still exploitable: B's executable price at t + ℓ_exec differs from A's signal-implied price by more than B's spread.
- **(L3) Post-cost realised edge.** L2 survives commission, slippage, rejects and requotes.

L1 does **not** imply L2, and L2 does not imply L3. **No arbitrage is claimed from L1.**

**A. Definition.**
- Mid returns on a common clock: r_A(t), r_B(t) sampled every δ (δ ∈ {50, 100, 250, 1000} ms).
- L1: the cross-correlation ρ(ℓ) = corr(r_A(t), r_B(t+ℓ)); the lead is ℓ* = argmax_ℓ>0 ρ(ℓ), with Hayashi–Yoshida for asynchronous ticks.
- L2: at each A-signal (|Σ r_A over window| > threshold), compare B's ask/bid at t + 250 ms against B's value at t + 250 ms + holding h.
- L3: L2 net of all costs.

**B. Inputs required.** Two tick feeds for the **same instrument over the same period**, stamped by **one common local clock** (receive time, not each broker's server time).

**Available: none.** Pepperstone ticks are Pepperstone-server-stamped. The other brokers' data is 2024 M1 bars in a binary format with no ticks, and no second login. Alpha Vantage intraday FX is premium-only on this key.

**C–I.** Specified, but **not executable** until data exists. Entry: A-signal and B stale by > spread + commission. Exit: fixed h (≤ 5 s). Stop: h-time stop only. Costs: §1.2 plus a **reject/requote probability** (unknown, and must be measured). Max hold 5 s. Invalidation: clock drift > ℓ*/2, or the feed-A gap.

**J. Failure mode.** The lead is a clock artefact: different server clocks, network jitter, or batching by the broker's price engine. Plus last-look rejects and ToS risk: latency-exploitation is commonly restricted in retail broker terms (**verify Pepperstone's terms before any work; flagged, not assumed either way**).

**K. Nulls.** Time-shift null (ρ at negative lags must be symmetric under no-lead); a clock-jitter null (add ±ℓ* noise).

**L. Test.** Bootstrap CI of ρ(ℓ*) − ρ(−ℓ*); L2/L3 permutation vs a random-time-signal null.

**M/N.** It cannot follow §1.5: weeks-long parallel recordings are needed, split into disjoint weeks, with the final week untouched.

**O/P.** Latency shocks are the whole test (100 → 250 → 500 ms). The grid is δ × threshold × h.

**Complexity: HIGH.** Parallel logging on two terminals/brokers with a shared microsecond clock (`GetMicrosecondCount` / local receive time via `NEXA_TickLogger`), plus clock-sync validation.

**Data limitations: BLOCKING.** No second synchronous tick feed exists. The only honest current statement is **"untestable"**. The minimum viable dataset is ≥ 4 weeks of simultaneous tick logging from two brokers on one machine (a second broker login is needed, which is a human action).

---

## 6. Family 5: ASIAN SESSION MEAN REVERSION

**Hypothesis.** During the Asian session, a short-horizon deviation of price from its session anchor reverts, E[future return | stretched] opposite the stretch, more often than matched nulls, **after costs**. "Asian markets revert 80% of the time" is **not** assumed; the claim is only about conditional mean returns net of costs.

**A. Definition.**
- Session S_d = UTC [23:00, 06:00), avoiding server-00:00 rollover bars **explicitly** (measured EURUSD spread 42 pts median at server hour 00).
- Anchor μ_t = session-to-date mean of M1 closes (typical-price variant pre-declared); σ_t = std of M1 returns over the prior 60 bars × √(bars since session start). z_t = (close_t − μ_t)/σ_t.
- Signal: z_t ≤ −z* → long; z_t ≥ z* → short (z* ∈ {1.5, 2.0, 2.5}).
- Label: return to μ before the stop, within H bars.

**B. Inputs.** Pepperstone M1 (FX majors and XAUUSD) with bar spread; D1 for regime (prior-day ATR, trend).

**C. Entry.** Next-bar open after the signal, only if the bar spread ≤ 1.5 × that UTC hour's median spread. No entry in the rollover window (server 23:55–01:05). No entry within ±30 min of a high-impact event (JPY/AUD/CNY data, BoJ). One position at a time.

**D. Exit.** Price touches μ_t (dynamic target), or the stop, or the time exit at H bars (H ∈ {30, 60, 120}), or the session end (06:00 UTC).

**E. Stop.** k·σ beyond the entry z (k ∈ {1, 1.5}), i.e. z_stop = z* + k.

**F/G.** §1.2. Asian spreads are measured per hour; that's decisive here because targets are small (≈ 1–2 σ of a quiet session).

**H. Max hold.** 120 min or session end.

**I. Invalidation.** D1 regime is trending (|prior-day return| > 1.5 × ATR_D1). A session-range expansion > 2 × median. A high-impact event.

**J. Failure mode.** Costs exceed the small reversion. Trend days start in Asia (JPY, gold). The rollover spread spike creates fake stretches. The z-normalisation is look-ahead-prone: σ must use only **prior** bars.

**K. Nulls.** §1.3, plus a **same-rule-other-session null** (London hours), which tests whether "Asian" matters or it's generic reversion.

**L. Test.** Permutation vs nulls; per-symbol BH within the family plus the global BH.

**M/N.** §1.5. Many signals per night, so they're autocorrelated: cluster bootstrap by session/day, and count effective n as the number of sessions.

**O/P.** §1.6. Grid z* × k × H × anchor = 3×2×3×2 = 36 per symbol. Session-boundary sensitivity (start 22:00/23:00/00:00 UTC).

**Labels.** Triple-barrier with a dynamic target; MFE/MAE.

**Execution.** Market order at the next bar + 250 ms; real-tick check for the last 21 days.

**Complexity: LOW.** Bars only.

**Data limitations.** M1 before 2024 needs the chunked export. Prior evidence against: the factory's z-score mean-reversion (H1, ADX filter) was **negative on all five Pepperstone symbols** (CI below 0 on most). This family is a session- and timeframe-conditioned variant, so its trials count toward FDR, and the prior result is reported alongside.

---

## 7. Family 6: TICK MICROSTRUCTURE / ORDER-FLOW IMBALANCE

**Terminology (binding).**
- **Tick data:** here, Pepperstone **quote updates** (bid/ask).
- **Tick volume:** the count of quote updates per bar. It is **not** traded volume.
- **Signed tick proxy:** the sign of the mid change between consecutive quotes.
- **DOM:** book depth; currently `available=false`, **unproven**.
- **Transaction / order-flow data:** trades with size and aggressor side, which **Pepperstone's feed does not provide here** (volume=0, last=0, no BUY/SELL flags).

**Nothing in this family is institutional order flow.** At most it measures the **statistical behaviour of one broker's quote stream**.

**Hypothesis.** A quote-update imbalance over a short window predicts the sign of the next mid-price change over a horizon h **beyond a shuffled-sign null**, and that prediction survives spread, commission and 250 ms latency.

**A. Definition.**
- Mid m_i = (bid_i + ask_i)/2; signed proxy s_i = sign(m_i − m_{i−1}) (zero changes are dropped).
- Imbalance I_t(W) = Σ_{i∈(t−W, t]} s_i ÷ #{i}, with W ∈ {50, 200, 1000} quote updates.
- **Bid/ask-update asymmetry** (OFI-lite, sizes unavailable): A_t = (#bid-up − #bid-down) − (#ask-down − #ask-up) over W. This is the Cont–Kukanov–Stoikov OFI with unit sizes, and **labelled as a degraded proxy**.
- Target: sign(m(t + 250 ms + h) − ask/bid-side entry) for h ∈ {1, 5, 30} s.

**B. Inputs.** Pepperstone ticks, 2026-08-28 → 09-25 (the only data). Forward collection via `NEXA_TickLogger` for OOS.

**C. Entry.** |I_t| ≥ q-quantile (q ∈ {0.9, 0.95, 0.99}, quantiles from DEV only), direction sign(I_t). Execute at the first quote ≥ 250 ms later at ask (long) or bid (short).

**D. Exit.** Time exit at h, at the bid (long) or ask (short). Stop variant: a fixed 2 × median spread.

**E. Stop.** The time stop is primary. The price stop is secondary and pre-declared.

**F/G.** §1.2 using **actual tick-level bid/ask** (real spreads) plus commission (0.7 pip EURUSD RT is **large** relative to second-scale moves), plus 250 ms latency. Slippage is embedded because the fill is the actual quote after latency.

**H. Max hold.** 30 s.

**I. Invalidation.** Server rollover window; quote gaps > 2 s (a feed stall); spread > 3 × median.

**J. Failure mode.** Predictability exists in **mid** but is smaller than spread + commission (the classic outcome). Quote-update batching by the broker's price engine creates spurious autocorrelation. 250 ms latency erases second-scale signals. A single 21-day regime.

**K. Nulls.** **Sign-shuffled null** (permute s_i within 1-minute blocks); a **time-shifted null** (I_t paired with the target at t + random offset); §1.3 timing and direction nulls.

**L. Test.**
- Directional accuracy and E[R_net] vs nulls by permutation.
- Predictive regression of future mid change on I_t with HAC SE, reported for the **mid**, then separately for **executable** P/L.

The mid result alone is **never** reported as an edge.

**M/N.** It can't use §1.5. With 21 days: DEV = weeks 1–2, VAL = week 3, untouched OOS = week 4 (a single look), and **forward OOS** = ≥ 4 weeks of new logging after the protocol hash.

**O/P.** §1.6 with latency 100/250/500 ms. Grid W × q × h = 3×3×3 = 27 per symbol.

**Labels.** Executable P/L sign at h; MFE/MAE in spread units.

**Execution.** Quote-level: the fill is the first available quote after latency, with no partial fills modelled (size unknown). This is a limitation: it assumes infinite size at the touch, which is optimistic.

**Complexity: MEDIUM.** A tick-level event simulator exists partially (`nexa_marketdata`). The heavy memory load (10.8M XAU ticks) must run with nothing else on the machine.

**Data limitations.** 21 days; quote-only; no sizes; no DOM (recheck in open market); no aggressor side; one regime. Identifiability is high for the **mid** statistic (millions of observations), but executable-edge identifiability is modest, and generalisation is untested until forward data exists.

---

## 8. Cross-family governance

- **Registration:** one frozen protocol (periods, grids, nulls, costs, metrics) is hashed **before** any family is run. The global trial count = Σ grid sizes × symbols + the 108 prior factory trials.
- **Selection bias:** no family can be re-parameterised after seeing OOS. A failed family is recorded as failed, not tuned.
- **Integration path if anything survives:** a Strategy Factory candidate → MT5 Strategy Tester replica → shadow mode → promotion gate. It still passes through NEXA's deterministic gates and `NEXA_Risk.mqh`. **Also note:** under the current `InpMaxSameCurrencyNet` (0.02 lots) cap, NEXA cannot execute any family at a $50k account size (open blocker B-EXPOSURE-CAP).

---

## 9. Ranking (by research-design criteria only; **not** by expected profitability)

Scores 1 (worst) – 5 (best). "Overfitting resistance" is the inverse of susceptibility (5 = least susceptible).

| Family | Evidence testability | Data availability | Execution realism | Statistical identifiability | Overfitting resistance | Total |
|---|---|---|---|---|---|---|
| **3. FVG retracement** | 5: definition exists in NEXA, parity-verified | 5: bars + 3.9M journaled rows | 3: limit-fill uncertainty before real ticks | 4: thousands of events/yr; matched-zone null available | 3: size/displacement thresholds | **20** |
| **5. Asian mean reversion** | 4 | 4: M1 exportable locally; spreads per hour measured | 3: small targets vs costs; rollover handled explicitly | 4: many signals, effective n = sessions (~1,900) | 2: anchor, z, session-boundary choices | **17** |
| **2. XAUUSD session breakout** | 4 | 4 | 3 | 3: ≤ 1 trade/day (~1,900 days) | 2: boundary, buffer, stop variants | **16** |
| **6. Tick microstructure** | 3: 21 days, one regime | 2: quote-only, no size/DOM/aggressor | 1: second-scale edge vs 250 ms latency + 0.7-pip commission | 4: millions of observations (for the mid statistic) | 3: small grid, but a single regime | **13** |
| **1. Macro event volatility** | 3: needs a calendar export and a DST-exact time map | 2: calendar not exported; no release-second ticks before 2026-08 | 2: release spreads/slippage unobserved historically | 2: ~200–400 heterogeneous events/yr; surprise σ per indicator | 3 | **12** |
| **4. Cross-feed latency** | 1 | 1: no second synchronous tick feed exists | 1: latency, last-look, ToS unknown | 1: clock artefacts dominate | – (not assessable) | **4** |

**Order:** 3 → 5 → 2 → 6 → 1 → 4.

Families 2 and 5 score close together. Family 5 ranks higher only on identifiability, because it has more independent sessions per unit of history. Neither ranking claims anything about profitability. Families 2 and 5 also carry documented prior evidence against related variants (breakout ≈ random on gold; mean reversion negative on all five symbols), and that evidence will be reported alongside.

---

## 10. What Phase 2 would need (not started, pending approval)

1. A frozen protocol hash for all six families.
2. A chunked Pepperstone M1 tester export for 2017-07 → 2023-12 (local history only; no new broker download).
3. A read-only MQL5 calendar export script (Family 1).
4. A DST-aware server→UTC converter with tests (also fixes research-side D-TZ).
5. A pending-order simulator with the trade-through fill rule (Family 3).
6. Tick-event simulator hardening (Family 6).
7. Family 4 stays blocked until a second broker login and parallel logging exist.
