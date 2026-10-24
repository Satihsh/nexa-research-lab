# NEXA core synthesis (2026-10-17): one core idea, two strategies

**Request (user, 2026-10-17):** combine the entire research into one core idea and build one or two new strategies with the highest possible win rate.

**Status:** DESIGN ONLY. No data has been touched for anything new here. Every number below is either cited from a source or labelled as a design choice. Nothing is tradable until it passes the pre-registered QuantConnect out-of-sample (OOS) tests in §6.

---

## 1. What ~25 tests taught us (the five laws of our own evidence)

| # | Law | Evidence in this repo |
|---|---|---|
| L1 | **Small gross edges die on costs.** An edge under ≈ 2× the round-trip cost is untradable. | C1 Tokyo fix (+2.17 bp gross, not tradable); FX1 (+0.70 bp gross, net −0.63); IM1 / H-IM-NQ (gross ≤ 0 or below cost); gate LC-2 |
| L2 | **Fixed-shape intraday rules have no stable edge.** The in-sample positives were regime luck. | H-ORB-1 (+0.063 R, p 0.15); H-IVB1 (+0.010 R); H-VAR (no evidence); **H-ORB30L +0.058 R in 2023–26 → −0.071 R over 2009–23 (1,604 trades, FAILED)** |
| L3 | **Order-flow *rules* on their own have no edge**, because predictable flow is already in the price. | OF-16/19/20/20b, OFC1, OFC1R REJECTED; gate LC-1; theory S55 (Muhle-Karbe / Rosenbaum 2026) and Lillo–Farmer: order *signs* are predictable, price *changes* are not |
| L4 | **Measurement tools work; predictors mostly do not.** | Tick-volume activity proxy, value-area proxy and basis map PASSED; Yang–Zhang / HAR do not beat ATR; TVPC fitted form FAILED, but the downstream gate PASSED |
| L5 | **The only multi-decade, after-cost intraday effect in our sources is trend continuation at the 30-minute-plus scale**, entered on abnormal moves and exited dynamically, never by a fixed target. | Zarattini, Aziz & Barbon 2024 (SPY 2007–24, net of costs, Sharpe 1.24 at 100 % size, 43 % hit rate, ≈ 1.8 trades a day); Gao et al. 2018 / Baltussen 2021 (decayed after 2018, which our H-IM-NQ confirms) |

**Combined core idea:**

> *Prices are martingales almost all the time (L3). Intraday trends persist only when slow "core" money (institutional metaorders) is actually executing (S55's core-flow layer). So: trade intraday trends **only** on the days and moments when signed order flow shows statistically significant persistence in the trend's direction, size each trade to its stop, and never use fixed targets.*

This combines:
- L5: what works;
- L3 plus S55: why it usually doesn't, and when it might;
- L1: few trades, large moves, so the gross edge is large relative to costs;
- L2: adaptive bands and dynamic exits instead of fixed shapes.

**Novelty check (2026-10-17, Exa + OpenAlex):**
- Gating trend trades on *price* Hurst exponents has been published (e.g. Marton & Cakir 2022, SSRN 4290787; student reports).
- Order-flow persistence has been *measured* (Borsa Istanbul study; S55).
- **No published test was found that gates intraday trend trades on a real-time self-normalised test of signed order-flow persistence.** We cannot prove "first in the world", only "not found in our search".

---

## 2. Strategy 1: CFT (Core-Flow Trend)

**Market:** CME index futures, **ES / MES** (primary) and NQ / MNQ (declared second test). Regular hours, flat every day.

**Notation:** day t; decision times τ ∈ {10:00, 10:30, …, 15:30} ET; O_t = 09:30 open; C_{t−1} = prior 16:00 close.

### 2.1 Trend layer (published; Zarattini, Aziz & Barbon 2024)
- **Normal move at time-of-day τ:** σ_t(τ) = mean over the previous 14 days d of |P_d(τ)/O_d − 1|.
- **Bands:**
  - UB_t(τ) = max(O_t, C_{t−1}) · (1 + σ_t(τ));
  - LB_t(τ) = min(O_t, C_{t−1}) · (1 − σ_t(τ)).
- **Trend signal:** D_t(τ) = +1 if P_t(τ) > UB_t(τ), −1 if P_t(τ) < LB_t(τ), else 0.
- **Trailing stop**, checked only at decision times:
  - long: max(UB_t(τ), VWAP_t(τ));
  - short: min(LB_t(τ), VWAP_t(τ)).
- **Flat at 16:00.**

### 2.2 Core-flow gate (new: the NEXA contribution)
Let x_i be the **aggressor-signed volume** of minute i since 09:30. A trade at the ask counts +, at the bid −; between the quotes it takes the side of the previous trade (CL-049).

The trend is accepted only if the cumulative flow is *significantly persistent* in the trend's direction, using the self-normalised statistic

  **Z_t(τ) = (Σ_{i≤τ} x_i) / √(Σ_{i≤τ} x_i²)**

- **Null hypothesis (no core flow, reaction flow only):** x_i is a martingale-difference sequence (S55 Thm 3.6, reaction component). Under that null, Z → N(0,1) by the martingale CLT. The self-normalisation makes this robust to the rough, heavy-tailed volume (S55 Fig. 5).
- **Alternative (core flow present):** the fractional part with H0 > ½ makes Σx grow like n^{H0} while √Σx² grows like n^{½}, so |Z| grows like n^{H0−½}.
- **Entry rule:** enter in direction D only if **D · Z_t(τ) > 1.96**. This is the 5 % two-sided null critical value. It is **fixed by theory, not tuned on data.**
- **Interpretation:** "price has left its normal range **and** the money that moved it is statistically persistent, not noise."

### 2.3 Sizing (prop-compatible)
- **Risk per trade:** fixed $R (for example $100).
- **Contracts:** n = floor($R / (|entry − trailing stop| × $/point)), with a minimum of 1 MES / MNQ. Skip the trade if n = 0 would be needed, so $R is never exceeded.
- This is the volatility-targeted sizing of Moreira & Muir (2017), as Matteo Conti (YT-081) recommends.

### 2.4 Why it might work, and why it might not (stated before any data)
- **For:**
  - Metaorder execution produces drift while it lasts (impact grows like t^{2−2H0}, S55 Thm 4.1).
  - Requiring both a price displacement and flow persistence should remove the "noise breakouts" that sank the ORB family.
- **Against:**
  - Efficiency (S55 eq. 2) says expected future flow is already priced, so a persistence gate may select days that are *already* repriced.
  - The paper's edge may have decayed after publication (May 2024).
- **The OOS test decides.**

---

## 3. Strategy 2: CFT-P (CFT plus a prop "green-day" overlay)

The user's goal is **about 20 winning days and 3–5 losing days a month**, which is ≈ 80 % green days. That is a statement about the **daily** win rate.

### 3.1 The mathematics that must be faced (no shortcuts)
- **Per-trade identity:** expectancy E = p·W − (1−p)·L. Win rate p can be raised arbitrarily by taking smaller targets and wider stops, but **E does not improve**. High-win-rate shapes are negatively skewed (many small wins, rare large losses), which is exactly what breaks a **trailing** loss limit (Topstep: $2,000 on 50K, intraday breach liquidates).
- **Optional stopping theorem:** if the trade P&L is a martingale (no edge), **no stopping rule** (for example "stop after the first win") changes the expected P&L. With a positive edge, stopping early **raises the share of green days but lowers the expected P&L**. Overlays only *reshape* days; they never *create* edge.
- **Trend strategies have low hit rates by nature** (paper: 43 %). They earn through a few large days. An honest target for CFT alone is a modest green-day share with positive months, **not** 80 % green days.

### 3.2 Overlay design (pre-registered as declared variants, not tuned)
- **V1 "first green, stop":** after the first trade of the day closes positive, take no more trades that day.
- **V2 "daily loss cap":** stop for the day after a −1 $R day.
- **V1 + V2 combined.**
- **Objective (computed, not optimised):** for each variant, from the **OOS trade list**, estimate by block bootstrap:
  - (a) the expected monthly P&L;
  - (b) P(green day) and P(≥ 20 green days in a month);
  - (c) **P(pass the 50K Combine)** = P(hit +$3,000 before the trailing $2,000 loss limit, with best day < 55 % of the target);
  - (d) P(breach) within 60 trading days.
- **Choice rule (fixed now):** use the variant with the highest (c) among those with (a) > 0. If none has (a) > 0, **no variant is used.**

---

## 4. "Highest win rate in the world" and "quantum mathematics": honest answers

- **No one can promise the highest win rate in the world.** Win rate is a design choice traded against payoff (§3.1). What matters is positive expectancy after costs, plus the probability of passing and surviving prop rules. That is what §3 measures.
- **Quantum mathematics:** no published, verified trading edge comes from quantum methods. "Quantum" in trading products is mostly marketing.
- **The mathematics actually used here is graduate-level stochastic processes:**
  - mixed fractional Brownian motion and Hawkes scaling limits (S55);
  - the martingale CLT for self-normalised sums (§2.2);
  - the optional stopping theorem (§3.1);
  - first-passage (barrier) probabilities for a trailing drawdown (§3.2);
  - block bootstrap and DSR (deflated Sharpe ratio) for multiple testing.

---

## 5. Data and feasibility ($0)

- **QuantConnect AlgoSeek US Futures:** May 2009 → now; tick / second / minute; trades + quotes.
- **Trend layer:** minute bars.
- **Gate:** signed volume needs ticks.
  - To stay within the free node, minute bars drive the algorithm, and at each decision time it requests `History<Tick>` for the elapsed 30-minute block only, then classifies those trades against the prevailing quotes.
  - A smoke test checks that quote ticks are present. If they are not, the tick rule is used as a fallback, **declared before any result.**
- **No depth / DOM data** is needed.

---

## 6. Test plan (each needs the user's approval; pre-registered and hashed before any data)

| Stage | What | Period (QuantConnect) | Passes if |
|---|---|---|---|
| A | Trend layer only (H-NOISE), ES | **2024-05-10 → latest** (after publication) | Mean net R > 0, CI lower bound > 0, ≥ 60 % of years / halves positive, ≥ 300 trades |
| A-chk | Same, ES 2009 → 2024-04 | in-sample for the authors | Broadly reproduces the paper (port check only) |
| **B** | **CFT = A + core-flow gate**, ES | same OOS window | B's mean net R > 0 **and** B − A > 0 on paired days (the gate must *add* value) |
| B-NQ | CFT on NQ / MNQ | same window | Declared transfer test |
| C | CFT-P overlays V1 / V2 / V1+V2 | from B's OOS trade list | Choice rule §3.2; reports P(pass the 50K Combine) |

**Costs:**
- ES S1 = 1 tick per side + commission (S0 / S2 = ½× / 2×).
- NQ as before: S0 / S1 / S2 = 1 / 2 / 3 pts round trip.

**Multiple testing:** every stage counts toward DSR trials (the NQ family is already at 116).

**Evening-window fit:**
- Entries run 10:00–15:30 ET, which is 22:00–03:30 MYT (23:00–04:30 after 1 Nov). That needs automation (MyFundedFutures or the Topstep API both allow the trader's own bot) or the user staying up.
- A declared "entries only until 00:00 MYT" variant can be added at pre-registration, never afterwards.
