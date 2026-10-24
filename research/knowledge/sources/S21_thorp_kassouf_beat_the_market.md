# S21 — Thorp & Kassouf, *Beat the Market: A Scientific Stock Market System* (Random House, 1967)
File: `beatthemarket.pdf` · 229 pp (PDF) · book pp. i–211 + index

| Field | Value |
|---|---|
| Source type | Academic authors (UC Irvine maths/economics professors) writing a **practitioner book**; not peer-reviewed. Builds on Kassouf's Columbia PhD (1965, econometric warrant model) [ref 10]. |
| Evidence status | **Strongly supported (historically) / later established**: the warrant-hedge mispricing principle was subsequently formalised by Black–Scholes–Merton (1973) and Thorp's own later fund (Princeton-Newport). Within this book: author track record (5 yrs, no losses, ~25 %/yr — self-reported, unaudited) + a 1946–66 historical simulation (in-sample rule construction). Regime-specific (1946–66 US listed warrants, Reg T margin). |
| Processing | Full text read (pp. 1–229, 1306 extracted lines). 30 low-text pages: all are figures/tables/blank. **Rendered and visually read**: p. 85 (Fig 6.3 normal price curves), p. 102 (basic-system growth chart 1946–66), p. 108 (Table 7.2, 1929 warrants), pp. 206–211 (Appendices A–D — **image-only, no text layer**; read visually in full), p. 213 (Fig E.1). Remaining figure pages (Fig E.2–E.4 hedge-mix scatter plots, Fig 14.1, Tables 14.1–14.2, misc. diagrams) interpreted from captions + surrounding text only. |

## 1. Core objects and rules (SOURCE)
- Warrant = long-dated call issued by the company; **adjusted warrant** = price of the right to buy 1 share; **adjusted exercise price** E.
- Two price rules (Ch. 2): (1) W ≤ S (warrant never above common); (2) W ≥ S − E (otherwise arbitrage: buy W, exercise, sell S). In the S/E–W/E diagram these are the *maximum value line* (W/E = S/E) and *minimum value line* (W/E = S/E − 1).
- **Normal price curves** (Ch. 6, Fig 6.3, rendered p. 85): empirical average W/E vs S/E for 24, 18, 12, 6, 1.5 months to expiry, 1946–66. Read-off: at S/E = 1, 24 months → W/E ≈ 0.43; at S/E = 0.5 → W/E ≈ 0.14. Curves collapse onto the minimum value line as T→0 ⇒ **time decay of option premium**.
- **Basic system** (Ch. 4–7): short "overpriced" warrants (actual above normal curve), expiring < ~2–4 yrs, with 0.3 ≤ S/E ≤ 1.2; buy common at mix ≈ 3 warrants short : 1 share long (Fig 6.3 annotation: "Use a 3 to 1 mix when stock is between 0.3 and 1.2 times adjusted exercise price"; below 0.3: short warrants only).
- **Profit profile / zero-profit lines** (Ch. 4): with mix m short warrants per share long, P&L at expiry is piecewise linear in final S; the two zero-profit prices bracket a wide "safe" interval. Upside zero-profit line slope = 1/mix in the warrant–stock diagram.

## 2. Mathematics (verified)
### 2.1 Avalanche effect (App. A, image p. 206–207, verified)
Short at W₀, price falls continuously to W_f, margin a constant fraction m of current price, all new buying power re-shorted:
  **P = V₀[(W₀/W_f)^{1/m} − 1]**
Derivation sketch (INFERENCE, ours): position value dynamics dV = −(V/(mW)) dW ⇒ ln V ∝ −(1/m) ln W.
Check (book): W₀=13, W_f=10, m=½, V₀=$6,500 ⇒ (1.3)² − 1 = 0.69 ⇒ P=$4,485 ✓ (table with discrete 1-pt reinvestment: $3,841).
Long pyramiding analogue: P = V₀[(W_f/W₀)^{1/m} − 1].
Constant $k per-share margin: **P = V₀(exp[(W₀−W_f)/k] − 1)**; check: V₀=$10,340, 10→5, k=5 ⇒ $10,340(e−1)=$17,767 (book rounds $17,800) ✓; discrete table $15,755.
- Intuition: under proportional margin, a short in a falling instrument **compounds geometrically** (released margin → more shorts). This is pyramiding / anti-martingale sizing; symmetric risk on reversal (losses also compound).
- Failure conditions: price jumps (no continuous reinvestment), buy-ins/short squeezes, margin changes, reversal → the pyramided position takes maximum size exactly at the worst point.

### 2.2 "Scientific proof that hedging can offer high expected return" (App. C, p. 207–208, verified)
Assume P(X_f ≥ x₀ + t) ≥ P(X_f ≤ x₀ − t) ∀t ≥ 0 ("weak symmetry"; implies E X_f ≥ x₀). Buy 100 common at 0.5E, short 100 warrants at 0.2E:
  G_f = X_f − 0.3E if X_f ≤ E;  G_f = 0.7E if X_f > E  ⇒ G_f = min(X_f, E) − 0.3E.
  ⇒ **E(G_f) ≥ 0.2E**. Returns: 100 % margin → ≥ 28 %; 70 % margin on common → ≥ 36 %; 70 % on both → ≥ 40 %.
- **Our verification:** with x₀ = 0.5E, E = 2x₀, and support ⊂ [0,∞): min(X,2x₀) − x₀ is symmetric-dominated (upper tail truncated at x₀ above, lower tail cannot exceed x₀ below), so E[min(X,E)] ≥ x₀ ⇒ bound holds ✓.
- Pacific Petroleums example (27 Sep 1966): common 0.53E, warrant 0.19E, 18 months. Book claims E(G) ≥ 0.16E. **Our check:** truncation at E < 2x₀ = 1.06E costs at most 0.06E·P(X > E) ≤ 0.06E·½ = 0.03E ⇒ E(G) ≥ 0.53 − 0.03 − 0.53 + 0.19 = **0.16E ✓**. With 5 % commissions ≥ 0.15E on 0.56E invested ⇒ > 26.7 % per 18 months (≈ 18 %/yr).
- Principle: **the edge is the option premium (time value) that the short collects, made robust to direction by the long hedge**; the only distributional assumption is weak symmetry. It is a *risk-premium/mispricing harvest*, not a forecast.
- Limits: assumes hold to expiry, no early squeeze/buy-in, no dilution/term changes, no extension of warrant life (Ch. 11 risk), borrow availability.

### 2.3 Kassouf warrant-price model (App. D, p. 211, verified numerically)
  **y = (x^z + 1)^{1/z} − 1**,
  z = 1.307 + 5.355/T + 14.257R + 0.298D + 1.015 ln(X/X̄) + 0.405x
  y = adjusted warrant / adjusted exercise price; x = X/E_adj; X̄ = mean of previous 11 months' high-low average; T = months to expiry; R = dividend yield; D = dilution ratio.
- Sperry Rand 15 Nov 1966: x = 1.04, X̄ = 23.49, T = 10, R = 0, D = 0.12 ⇒ z: 1.307+0.5355+0+0.0358+0.1414+0.4212 = **2.441 ✓**; y = (1.04^2.44+1)^{1/2.44} − 1 = **0.355 ✓** ⇒ predicted 1.08×25.93×0.36 = $9.98 vs actual $8.125 (actual *below* model ⇒ not a short candidate).
- Structure: a one-parameter family of curves interpolating between the minimum-value line (z→∞: y → max(x−1,0)) and the maximum-value line (z→1: y → x). Larger z ⇒ cheaper warrant. Short T increases z (time decay); **momentum term ln(X/X̄)** — warrants on stocks above their 11-month average are *relatively cheaper* per this fit (SOURCE: "trend effect").
- Limits: in-sample OLS-type econometric fit (Kassouf 1965) on 1945–64 data; no volatility input except implicitly; predates Black–Scholes.

### 2.4 Volatility/expectation (Ch. 9)
- Volatility proxy: yearly range ÷ midpoint price (crude range estimator); "square-root law" index entry: price dispersion grows ∝ √t (SOURCE).
- Expected value E(X_f); trend = (E(X_f) − x₀)/t; the hedge needs only weak symmetry, not a trend forecast.

## 3. Empirical record (SOURCE; quality notes)
- **Basic system 1946–66** (Ch. 7, Table 7.1, growth chart p. 102 rendered): simplified mechanical rules; $1,000 → ≈$50k before tax / ≈$22k after 25 % tax (Table 7.1 last entry implied $22,289 via Ch. 13 "$10,000 → $222,890"). Book: > 25 %/yr for 17 years after commissions before tax. **Rendered chart shows a ~4-year flat gap 1956–60 ("no listed warrant satisfied the five rules")** and a large share of terminal wealth from 1962–66 ⇒ opportunity-limited, lumpy.
- 1929–30 crash: basic system could have doubled (Table 7.2, 23 listed warrants June 1929, rendered p. 108).
- Author cash record: 5 years, no losses, ~25 %/yr; one author >2× $100k in 4 years. **Unaudited self-report.**
- App. E (Fig E.1, rendered): average 1-month % gain from shorting a warrant vs months-to-expiry (1946–66, 100 % margin, **no costs**): fitted line ≈ +17 %/mo at T≈0 falling to ≈ −9 % at T=24; huge outlier (~+64 %) at T≈1. Figs E.2–E.4 (1:1, 2:1, 3:1 hedges) captioned similarly (not visually inspected). ⇒ **Premium decay accelerates near expiry** (theta convexity) — SOURCE, cost-free.
- Capacity (Ch. 14, Tables 14.1–14.2): on 14 Oct 1966 the three best situations supported ≈ $4.6 M (existing short interest) up to ≈ $15 M (half of warrant issue short) before exchange short-sale bans. **Capacity-constrained edge.**

## 4. Principles (SOURCE → INFERENCE)
1. **Relative-value hedging beats directional forecasting** when a derivative is mispriced relative to its underlying; the hedge converts a priced-in premium into an expected return with bounded directional risk. (SOURCE; later established by BSM.)
2. **Edge decay through rediscovery** (Ch. 13–14): "when enough money is finally invested in the basic system it will be ruined"; academics (Samuelson, Cootner) and newsletter readers were converging on it. (SOURCE) → explicit early statement of **alpha crowding/capacity**.
3. **Institutional frictions are the binding risk**: short-sale bans, buy-ins, squeezes, warrant-term extensions, margin changes (Reg T), borrow availability. (SOURCE)
4. **Mechanical rules + historical simulation + small live record** — the authors acknowledge the system was "rediscoverable" and derived from observing the same period it is tested on (INFERENCE: in-sample rule construction; no OOS separation in the modern sense).
5. Kelly/diversification: the book's portfolio chapter cites Markowitz [14] (the summary's earlier note "Kelly ref [14]" is corrected here: **ref [14] is Markowitz, *Portfolio Selection* (1959)**; Kelly is not cited anywhere in the book; Thorp's Kelly work appears elsewhere). The Ch. 12 claim (p. 184–185): with two equally favourable alternatives, the investor who splits equally "will tend to far surpass" the one who concentrates, citing [14]. That is a log-growth (geometric mean) diversification argument; it is stated without proof.

## 5. Critical assessment
- Strong: correct theoretical insight; math in App. A/C/D verified by us; candid about frictions, capacity and decay.
- Weak: self-reported returns; cost-free App. E; normal price curves fitted to the same sample used to evaluate; survivorship of listed warrants unclear; tax-dependent conclusions; 1960s US equity-warrant microstructure.
- Look-ahead: normal price curves estimated on 1946–66 data then used to select 1946–66 trades (**in-sample**).

## 6. NEXA relevance
- **Direct strategy relevance: none** (NEXA trades spot-FX/metal CFDs at Pepperstone; no warrants/options, no shorting-borrow mechanics).
- Transferable knowledge:
  - **Capacity/crowding/decay** principle → supports NEXA's insistence on prospective OOS (V2 2027) and on treating published patterns (S08, S09, S17, S19, S22) as likely decayed.
  - **Avalanche/pyramiding math** → formal model for any NEXA position-add logic: under proportional margin, adding to winners compounds as (W₀/W_f)^{1/m}; risk on reversal is maximal at peak size. Relevant only as a caution; NEXA's 1 %/trade & exposure caps forbid it (NEXA_Risk unchanged).
  - **Hedge-vs-forecast** principle → relative-value constructs (XAU–XAG cointegration, S25/S22) are the closest NEXA analogue; DATA-LIMITED/hypothesis only.
  - **Theta convexity near expiry** (Fig E.1) → no NEXA instrument has expiry; not applicable.
  - **Momentum term in warrant pricing (ln X/X̄, 11-month window)** → historical evidence of ~1-year trend effect in prices, cf. S02/S03/S22 TSMOM 12-month lookback. Weak cross-support.

Cross-refs: S22 (151 Strategies: convertible arbitrage, warrant/option strategies, Kelly), S12 (online portfolio / log-optimal growth), S13 (μ/σ² sizing ≈ Kelly), S25 (stat-arb hedging), S08/S09/S17/S19 (practitioner pattern decay).
