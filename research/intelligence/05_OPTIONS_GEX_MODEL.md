# 05: OPTIONS / GEX MODEL (Tier 3)

**Bottom line first:**
- The mathematics of dealer gamma is well defined (S54, verified).
- A complete engine is disclosed (S53).
- **No source in the 56 files tests whether walls, flips or pins predict price.** S53 and S54 say so explicitly.
- **NEXA cannot compute GEX for any of its instruments with current data** (03):
  - no OI;
  - no greeks or IV snapshots;
  - no COMEX gold options;
  - and the sign is unidentifiable without signed flow (S50, S54).
- This document therefore specifies:
  - the model;
  - what it would predict;
  - the conditional (not hard-coded) wall hypotheses;
  - the data needed to test them.

## 1. Definitions (registry EQ-027–029, 031)

| Object | Definition | Source |
|---|---|---|
| Per-strike GEX | GEX_K = Γ_K·OI_K·M·S²·0.01·sgn(K) | S53, S54 |
| Sign | **Model A:** calls +, puts − (the "dealers long calls / short puts" proxy). **An assumption, not a fact** | S54 §3 |
| Net GEX / regime | N = Σ_K GEX_K. N > 0 is "long gamma" (dampening); N < 0 is "short gamma" (amplifying) | S53 §2.1, S54 |
| Gamma flip | Repriced root of N(S*) = 0, sign-resolved nearest (S53); local interpolation with the zero-straddle rule (S54) | S53, S54 |
| Call wall / put wall | Largest call-side (put-side) gamma strike at/above (below) spot, with a 1.5× dominance qualifier; strength = peak / median gross gamma | S53 §3.6 |
| Pins | Call-dominant strikes within ±5 % of spot; score = concentration / distance (distance in units of 0.5 % of spot); active only in positive gamma | S53 §3.7 |
| Vanna / charm overlays | Gated: vanna only on \|ΔIV\| ≥ 0.5 vol points since the open; charm only at ≤ about 5 DTE | S53 §3.9 |
| Hedge-pressure ratio | HPR = \|N\| / DV (dollar hedge per 1 % move ÷ daily dollar volume) | **NEW** (formalises S48 p. 42) |

## 2. Why a wall *could* matter (mechanism; conditional, not assumed)

**Delta-hedging feedback (S48, EQ-031)**
- A dealer long gamma at strike K rebalances *against* price near K: sell above, buy below. This creates mean-reverting pressure around K.
- **Short gamma reverses it.**
- The pressure is proportional to Γ_K·OI_K, which is concentrated near spot and near expiry.

**Under what conditions it should behave as …**

| Behaviour | Required conditions (all testable once data exists) |
|---|---|
| **Resistance / support (rejection)** | Dealers **long** gamma at the strike (correct sign); **HPR large**; positive net regime; calm volatility (S48: "pinning more likely in calm markets") |
| **Magnet / pin** | As above, plus proximity to expiry (charm), plus call-dominance per S53. Weakens as liquidity of the underlying rises (S48: hard to pin major indices) |
| **Breakout / acceleration zone** | Dealers **short** gamma (negative regime). Hedging chases the move. A wall "gives way" (S53 break-state machine) |
| **Liquidity target** | **No mechanism given in any source.** Practitioner usage only |
| **Dealer-hedging zone** | Definitionally any high \|Γ·OI\| strike. Behaviour depends on the sign |

**Therefore the hypotheses must be conditional probabilities, never "put wall = support":**

    P( reject at K | price reaches K, sgn, HPR, regime, τ_expiry, σ̂ )   vs   P( reject at K' | placebo level K' matched on distance and σ̂ )

## 3. Hypotheses (registered in 14; all BLOCKED by data except where noted)

| ID | Statement | Falsification | Data status |
|---|---|---|---|
| **HYP-025** | **Volatility channel (academic prior: Ni et al., via S50 and S53):** next-day realised volatility of XAU is lower after positive dealer net gamma than after negative, controlling for HAR σ̂ | Coefficient on regime ≈ 0, or the wrong sign, after HAR controls, in a frozen holdout | **BLOCKED** (no OI/sign) |
| **HYP-026** | **Wall rejection is conditional:** rejection probability at walls exceeds matched placebo levels **only** in positive regime with HPR above its median | No difference vs placebo, or no dependence on regime/HPR | BLOCKED |
| **HYP-027** | **Dose–response on HPR:** the wall/pin effect size increases monotonically in HPR (Bennett's condition) | Flat or non-monotone (isotonic regression test) | BLOCKED |
| **HYP-028** | **Proxy:** GLD option *volume* concentration (unsigned, Σ_K Γ_K·Vol_K, S53's "volume toggle") marks XAU prices with abnormal reaction | No difference vs placebo levels. **Low prior:** volume ≠ positioning; GLD ≠ COMEX | APPROXIMABLE (Massive GLD options aggregates + BS-inverted IV) |
| **HYP-029** | **Charm drift into monthly GLD expiry** (S53 "charm bid") | No drift difference in the last 5 sessions vs other weeks | BLOCKED for the sign; the GLD proxy is weak |
| **HYP-030** | **IV–RV spread:** GLD-implied minus XAU realised volatility (VRP) predicts XAU realised volatility (mean reversion of the spread) | No gain over HAR | APPROXIMABLE (BS inversion of GLD option closes) |

## 4. Why NEXA should not build GEX now (INFERENCE, evidence-based)

1. **Data:** OI and quotes are not entitled. COMEX gold options are not on Massive.
   - S53's stack (Sierra Chart plus Denali) is a *different* vendor: about $4/month non-professional exchange fees plus about $38.80/month platform cost, per S53 §5.
   - **Even S53 provides no backtest of its levels.**
2. **Sign identification:** OI does not reveal who is long (S54 §3.3).
   - S50 shows the *opposite* sign convention is economically right when customers buy calls (meme stocks).
   - For gold, the customer mix (miners' hedges, ETF holders, macro funds) is unknown. A Model-A-only analysis would carry an untestable assumption into every level.
3. **Scale:** S48 states that major indices are hard to pin. Gold and major FX are among the most liquid markets.
   - Without HPR there is no reason to expect wall effects in XAUUSD at the size of dealer books.
   - **HPR is the first quantity to measure** when OI is ever acquired.
4. **Instrument mismatch:**
   - FX options are mostly OTC (no public OI).
   - CME FX futures options exist but are not in the Massive futures API.
   - ETF options (FXE/FXB/FXY) are thin.
   - **For EURUSD, GBPUSD and USDJPY a GEX model is effectively UNAVAILABLE at any reasonable cost.**
5. **Priority:** the directive itself ranks GEX as Tier 3, after T1/T2 foundations. **T1/T2 are testable now; T3 is not.**

## 5. Minimum data to unblock Tier 3 (gold only) (detail in 19)

1. **Daily per-strike OI and settlement for COMEX gold options (OG), ≥ 2 years history.** Sources: CME DataMine (historical) or a vendor feed. Without history, only *prospective* collection is possible.
2. **Option quotes or settlement IV** per strike, to compute Γ.
3. **Signed volume**, to estimate the sign. Otherwise run *both* sign models and report the sensitivity (S54's isolation experiment as a mandatory robustness check).
4. **Futures/spot basis** (EQ-026), to map strikes to XAUUSD.

**If only prospective collection is feasible:** collect a daily OI snapshot from now, freeze the hypotheses above, and evaluate after ≥ 250 sessions. No result before then.

## 6. Rules if GEX is ever implemented (adopted from S53/S54 as method, not signal)

- **Ratify the sign contract in writing, and test at the production operating point** (S54 "masking test").
- **Repriced-root flip; zero-straddle rule;** "no flip" when there is no genuine sign change.
- **Dominance-qualified walls, with strength tags;** never a naked "wall = S/R".
- **Log every wall-test episode** (entry score, outcome: bounce, fade or break) **before** any calibration. S53 does this but has not calibrated.
- **Map with an explicit basis.**
- **OI is prior-session:** usable intraday only as yesterday's positioning (03 §3).
