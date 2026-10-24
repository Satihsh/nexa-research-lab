# PRE-REGISTRATION CFT / CFT-P: Core-Flow Trend on CME index futures (QuantConnect)

**Status: BINDING.**
- User approval 2026-10-17: "Ok we test the CFT and CFT-P".
- Design source: `../NEXA_CORE_SYNTHESIS_2026-10-17.md` (commit d75fd1d).
- **Written before any data was read for this hypothesis.** No CFT, H-NOISE or gate statistic has been computed on any data.
- **Not tuned.** Every parameter is either taken from the source paper or fixed here from theory. Nothing may change after results.
- Data: QuantConnect AlgoSeek US Futures (free node). **No orders are placed; the algorithm only reads data and logs results.**

## 1. Instruments, clock, sessions

- **Primary instrument:** ES (E-mini S&P 500) continuous contract.
  - Front month by open interest (`DataMappingMode.OPEN_INTEREST`).
  - **`DataNormalizationMode.BACKWARDS_RATIO`**, so the noise band and returns are not distorted by rolls.
  - Regular hours only.
  - Clock: America/New_York.
- **Transfer test:** NQ, with the same settings.
- **Session:** 09:30–16:00 ET.
  - Decision times τ ∈ {10:00, 10:30, …, 15:30} (12 decisions).
  - Bar convention: P_t(τ) = close of the 1-minute bar *ending* at τ.
- **A day is used** if all 390 RTH minute bars 09:30–15:59 exist and 14 prior valid days exist. Otherwise it is skipped and counted.

## 2. Trend layer (Zarattini, Aziz & Barbon 2024, SSRN 4824172: rules as published)

- **Normal move:** σ_t(τ) = mean over the previous 14 valid days d of |P_d(τ) / O_d − 1|, where O_d is the 09:30 bar open.
- **Bands:**
  - UB_t(τ) = max(O_t, C_{t−1}) · (1 + σ_t(τ));
  - LB_t(τ) = min(O_t, C_{t−1}) · (1 − σ_t(τ));
  - C_{t−1} is the prior day's 15:59 bar close (adjusted series). Volatility multiplier = 1, as in the paper's base case.
- **VWAP:** cumulative Σ((H+L+C)/3 · V) / ΣV over the day's 1-minute bars from 09:30.
- **Signal at τ:** D = +1 if P(τ) > UB(τ); −1 if P(τ) < LB(τ); else 0.
- **Positions:** at most one at a time. One contract unit at 1× notional for the statistics (§5).
- **Entry:** at the **open of the next 1-minute bar** after τ (no same-bar fill).
- **Trailing stop**, checked only at decision times τ:
  - long exits if P(τ) < max(UB(τ), VWAP(τ));
  - short exits if P(τ) > min(LB(τ), VWAP(τ)).
  - The exit fills at the next bar's open.
- **Reversal:** if at τ the position is exited **and** the opposite signal holds (and, in Stage B, the gate passes in the new direction), a new position opens at the same next-bar open.
- **Time exit:** the 15:59 bar close. No entries after 15:30.

## 3. Core-flow gate (NEXA contribution; Stage B only)

**Signed volume per second.** For each RTH second s with trade volume v_s > 0, the trade close p_s is compared with the bid b_s and ask a_s of the quote bar for that second:
- +v_s if p_s ≥ a_s;
- −v_s if p_s ≤ b_s;
- otherwise by mid: + if p_s > (a_s + b_s)/2, − if below;
- if exactly at mid, the sign of the last differing trade price (tick rule); 0 if none.

**Minute flow:** x_i = sum of the signed seconds in minute i from 09:30.

**Statistic at τ:** Z(τ) = Σ_{i<τ} x_i / √(Σ_{i<τ} x_i²).
- Null (reaction flow only, martingale differences; S55 Thm 3.6): Z → N(0,1).
- **Gate:** take or keep a *new entry* only if **D · Z(τ) > 1.96**. The threshold is the 5 % two-sided normal critical value, fixed by theory.
- **The gate affects entries only.** Exits are the trend layer's.

**Pre-flight F1 (classifier check, before any OOS day).**
- On **2024-01-02 … 2024-01-05** (4 days, *before* the OOS window), the second-bar classifier is compared with a tick-level quote-rule classifier (`History<Tick>`).
- **Pass:** Pearson correlation of the minute x_i ≥ 0.80 and sign agreement ≥ 0.80.
- **If it fails, the gate uses the pure tick rule on the second-bar trade close**, declared here as the only fallback. F1 is reported either way.

## 4. Costs (round trip, per contract, in index points)

- **ES:** S0 = 0.30, **S1 = 0.60** (1 tick of slippage plus about $5 commission), S2 = 1.20.
- **NQ:** S0 = 1, **S1 = 2**, S2 = 3 (as in all earlier NQ tests).
- Costs are charged per round trip. A reversal counts as two round trips' worth of fills: one exit and one entry.

## 5. Statistics

**Unit:** the **day**. Daily net P&L = Σ over the day's trades of (exit − entry) · direction − cost, expressed in **basis points of the day's 09:30 open**. This is "100 % size", as in the paper. Days with no trade count as 0.

**Primary for each stage:** the mean net daily bp at S1.
- Moving-block bootstrap over days: block 20, B = 2,000, **seed 20261017**, one-sided p.

**Also reported:**
- trades and trades per day;
- hit rate and payoff;
- S0 / S2;
- per-half-year table;
- long vs short;
- the daily-return Sharpe (annualised √252);
- max drawdown;
- **green-day share**;
- the descriptive DSR (deflated Sharpe ratio) with all CFT stages counted as trials.

## 6. Stages, periods, acceptance (each OOS stage runs ONCE; results files are never overwritten)

The **OOS window is 2024-05-10 → the last complete day in QuantConnect data at run time**. The paper was posted on SSRN 2024-05-10, so the authors never saw it.

| Stage | Rule | Data | Pass criteria |
|---|---|---|---|
| **F1** | Classifier check (§3) | ES 2024-01-02…05 | Corr and sign agreement ≥ 0.80, otherwise the declared fallback |
| **A-chk** | Trend layer only (no gate) | ES **2009-05 → 2024-05-09** (authors' era; port check, not evidence) | Reported only. A clearly negative full-sample result would indicate a porting error and is investigated **on this window only** before any OOS run |
| **A** | Trend layer only | **ES OOS** | Mean > 0, CI lower bound > 0, ≥ 3 of 4 equal time blocks positive, ≥ 300 trades |
| **B (primary)** | **CFT = A + gate** | **ES OOS** | B mean > 0 **and** CI lower bound > 0; **and** paired daily difference B − A > 0 with one-sided bootstrap p ≤ 0.10; ≥ 150 trades |
| B-EVE | CFT, **evening-only**: entries 10:00–12:00 ET, forced exit at the 12:29 bar close | ES OOS | Declared secondary. Mean > 0 and CI lower bound > 0 |
| A-NQ / B-NQ | Stages A and B on NQ | NQ OOS | Declared transfer tests, same criteria |

**Verdicts:**
- **CFT VALIDATED (G4)** if B passes.
- **TREND-ONLY** if A passes and B does not beat A (the gate adds nothing).
- **REJECTED** if B's mean ≤ 0.
- Otherwise **INCONCLUSIVE**.
- If fewer than 150 B trades: INSUFFICIENT-N.

## 7. CFT-P (prop overlay), computed only from the Stage B (or B-NQ) OOS trade list

**Overlays (declared now):**
- **V0:** none;
- **V1:** after the first trade of the day closes with positive net P&L, take no more trades that day;
- **V2:** stop for the day once the day's net P&L ≤ −1 R, where R is the absolute P&L of the first trade's initial stop distance;
- **V1+V2:** both.

**Prop model (Topstep 50K, verified 2026-10-16):**
- +$3,000 target;
- trailing end-of-day $2,000 Maximum Loss Limit, with intraday breach including unrealised P&L approximated by the trade path's worst decision-time mark;
- best day < 55 % of the target.

**Sizing:** fixed **k ∈ {2, 4, 8} MES** (ES S1 points × $5 × k). For NQ, the same k in MNQ ($2 / point).

**Estimates** by block bootstrap of OOS days (10,000 paths, seed 20261017):
- (a) mean monthly $;
- (b) P(green day), P(≥ 20 green days in a 21-day month);
- (c) **P(pass the Combine within 60 trading days)**;
- (d) P(MLL breach within 60 days).

**Choice rule:** pick the (overlay, k) with the highest (c) among those with (a) > 0. If none has (a) > 0, **no overlay is recommended.**

**No overlay can create edge** (optional stopping theorem). CFT-P is used only if Stage B passes.

## 8. Code and freeze

- **QuantConnect algorithm:** `qc_cft/main.py`. One file, with MODE ∈ {F1, ACHK, A, B, BEVE, ANQ, BNQ}; only the MODE line differs between runs.
- **Local:** `cft_local.py` (the CFT-P bootstrap on trade lists exported via the result log) and `test_cft.py` (synthetic tests for the bands, VWAP, the second-bar classifier, Z, and the entry / exit / reversal logic).
- The code is ported to the QuantConnect editor as plain source and **hash-verified in the editor** before every run (procedure D-9).
- **Before any run**, this file, the code and the tests are hashed into `PREREG_HASHES.txt`.
- Output: one `NEXA_RESULT` JSON line per run (≤ 10 KB log). The trade list goes to QuantConnect ObjectStore if available on the free tier; otherwise compact per-day lines are logged in chunks.
