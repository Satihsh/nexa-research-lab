# S48 & S50: volatility trading and the gamma squeeze (new corpus)

## S48: C. Bennett (2014), *Trading Volatility, Correlation, Term Structure and Skew*
**File:** `Trading-Volatility.pdf`, 317 pp.
**What was read:** the TOC; Ch. 1–2 (option basics; volatility trading, gamma scalping, pinning); Ch. 3.1 (implied above realized); App. A.2 (historical-volatility estimators). Other chapters were scanned via keyword search.
- Ch. 4–7 (volatility indices, exotics, correlation, skew/term structure) were **not studied in full**. They concern trading options, which NEXA does not do.

**Status:** practitioner reference by a sell-side head of derivatives strategy (Santander). **ESTABLISHED TEXTBOOK CONTENT**: standard Black–Scholes results, correctly stated.

**Statements used by NEXA (SOURCE; maths verified)**

**Delta-hedged P&L and the volatility premium**
- **Delta-hedged P&L** ≈ ½ Γ S² (r_t² − σ_impl² dt), where r_t is the return over the hedge interval.
  - "Dollar gamma" ≈ const/σ, so carry ∝ (σ_realized − σ_implied).
  - *Verified* (Taylor expansion plus Black–Scholes theta–gamma relation).
- **Implied volatility trades on average 1–2 vol points above subsequently realised volatility** (§3.1, equities). This is the volatility risk premium.

**Hedging behaviour**
- **Long-gamma hedgers** sell rallies and buy dips. They can hedge passively (sit on bid/offer).
- **Short-gamma hedgers** must cross the spread and trade *with* the move.
- **Pinning (SOURCE, p. 42):**
  - "the amount of buying and selling has to be **significant compared with the traded volume of the underlying**";
  - "pinning normally occurs for relatively illiquid stocks or where the position is particularly sizeable";
  - **"Given the high trading volume of indices, it is difficult to pin a major index"**;
  - "more likely in relatively calm markets".
  - **Examples:** Swisscom 2004–05 (a large convertible); AXA June 2005. Both snapped back after expiry.
- **Rules of thumb:**
  - σ_annual ≈ 16 × daily % move (√252);
  - an ATM premium ≈ 0.4 σ √T (exact: σ√T/√(2π)).

**Volatility estimators (App. A.2)**
- **Use zero drift** for close-to-close volatility; then variance is additive across periods.
- **Daily vs weekly volatility differ when returns are autocorrelated** (trend: weekly > daily; reversion: weekly < daily). This is the variance-ratio idea already in H-VR-SCALE.
- **Estimators and maximum efficiency vs close-to-close:**

| Estimator | Efficiency (max) | Handles drift | Handles overnight jumps |
|---|---|---|---|
| Parkinson (HL) | 5.2 | no | no |
| Garman–Klass | 7.4 | no | no |
| Rogers–Satchell | 8 | yes | no |
| GK–Yang–Zhang | 8 | no | yes |
| Yang–Zhang | 14 | yes | yes |

  - "For small samples Yang–Zhang is best overall."
  - Parkinson and Garman–Klass *underestimate* volatility when there are gaps.
- **Implication:** these estimators use only OHLC, which **NEXA has** (M1 back to 2017, plus Massive futures 1-min).

**INFERENCE for NEXA**
1. **Bennett's pinning condition is the measurable core of every "wall/pin" claim:** hedge flow must be large *relative to underlying volume*.
   - **Gold and major FX are among the most liquid markets in the world.** S53's claim that gold walls "cap rallies and floor sell-offs" therefore needs, at minimum, a demonstration that dealer hedge flow per 1 % move is a non-trivial fraction of COMEX/OTC volume.
   - This becomes construct **EQ-HPR (hedge-pressure ratio)** in 11_NEW_MATHEMATICAL_CONSTRUCTS.
   - **Contradiction recorded:** Bennett (2014: indices hard to pin) vs S53 (2026: walls/pins on ES and gold). 0DTE growth after 2014 is a possible reconciler for ES only. Gold has no 0DTE chain.
2. **The volatility risk premium means implied volatility is a biased forecast of realised volatility.** If an IV series is ever obtained, regress σ_realized on σ_implied with a *bias* term rather than using IV as is.
3. **OHLC estimators (Yang–Zhang) are a cheap, strong upgrade over ATR** for NEXA's volatility layer. They complement H-VOL-1 (HAR on realised volatility).

---

## S50: P. Serrano (2022), "Dissecting the Gamma Squeeze: the Case of GameStop" (MSc thesis, ISEG Lisbon)
**File:** `content.pdf`, 38 pp. Full text read, through §4.3.
**Status:** master's thesis. **Single-event case study (n = 1)**; descriptive, no statistical test. Evidence level: **CASE STUDY**.

**Content (SOURCE)**

**Proposed mechanism and conditions**
- **Mechanism:** customers buy short-dated OTM calls and sell puts, leaving dealers short calls. Dealers buy stock to hedge; delta rises, so they buy more. Short covering amplifies this.
- **Conditions argued:**
  - small float;
  - high short interest (at least 140 % of shares outstanding);
  - concentrated blocks (Schedule 13 filings totalling 81 % of shares);
  - coordinated retail buying (85 % of option volume was retail).

**Data and the net-gamma calculation**
- **Data:** OptionMetrics volumes; **ISE Open/Close signed option volume** (open-buy, open-sell, close-buy and close-sell, by investor type); Markit securities lending.
- **Net dealer gamma follows Ni et al. (2020):**
  - netOI_{j,t} = −(OI^{Buy,Public} − OI^{Sell,Public}), with OI updated from open/close signed volumes;
  - netΓ_t = 100 (S_t/N_t) Σ_j netOI_{j,t} Γ_j(t, S_t);
  - Black–Scholes gamma, σ = 60-day historical volatility, r = 30-day LIBOR.
- **Finding:** "days with major changes in GME prices were systematically preceded by days in which the OMMs had negative net gamma." This rests on visual inspection only; there is no test.
- **Literature cited:** Ni et al. (2020/21) find a significant **negative relation between dealer net gamma and subsequent stock volatility**, and a higher probability of large moves when gamma is negative.
- **American vs European:** gamma differences between Barone-Adesi–Whaley and Black–Scholes–Merton are small for short-dated puts. Delta differences can be large for long-dated puts.

**INFERENCE for NEXA**

1. **This is the only source in the 56-file corpus that computes dealer gamma from *signed* (open/close, customer vs market maker) volume** rather than assuming a sign.
   - It shows that the *correct* GEX sign needs **trade-initiator data**, which neither MT5 nor NEXA's Massive plan provides.
2. **Sign convention contradiction (important):**
   - In this thesis, customers buying calls means **dealers short calls, so negative gamma** (calls add *negative* dealer gamma).
   - S53/S54 Model A says call OI adds **positive** dealer gamma.
   - Both cannot be true in general. Which is right depends on who actually holds the calls, an **empirical inventory question** (S54 §3.1).
   - For meme-stock call buying, S50's sign is the economically plausible one. For index overwriting, Model A is.
   - **Conclusion:** the sign is market- and period-specific. It cannot be fixed by convention for gold or FX without signed-flow data.
3. **The academically supported claim** (Ni et al., via S50 and S53) is a **volatility** effect: negative dealer gamma → higher subsequent volatility and fatter tails. It is *not* a directional effect, which is consistent with S53 §2.1. **This is the only GEX hypothesis NEXA should ever test first.**
4. **The squeeze conditions are equity-specific** (float, short interest, share recalls, blockholders). **None maps to spot gold or FX CFDs. Gamma-squeeze mechanics are REJECTED as directly applicable to NEXA's instruments** (see 18_REJECTED_CONCEPTS).
