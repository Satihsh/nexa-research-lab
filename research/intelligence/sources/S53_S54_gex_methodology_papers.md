# S53 & S54: GEX methodology papers (new corpus, 2026)

## S53: N. Sen (July 2026), "Gamma Exposure (GEX) Without the Paywall"
**File and status**
- **File:** `ssrn-7098358.pdf`, 14 pp., full text read.
- **Type:** independent practitioner working paper (SSRN). Not peer-reviewed.
- **Evidence status:** METHODOLOGY DISCLOSURE. **No empirical test of any level's predictive value, and no P&L** (stated by the author, §6).

**What it specifies (SOURCE)**

**Pricing and inputs**
- **Black-76 on futures options**, with per-strike IV solved from live premiums, so the skew is captured (§3.2).
- **Inputs:** per-strike open interest, and live bid/ask/last for COMEX GC and CME ES options (Sierra Chart Denali feed).
- **Proxies are explicitly rejected:** the author argues that GLD ETF options have different strikes, expiries and holder populations, so levels derived from them land at the wrong prices (§3.1).

**Exposure and sign**
- **Per-strike exposure:** GEX(K) = Γ(K)·OI(K)·M·S·(0.01·S), in dollars of dealer delta per 1 % move.
- **Sign:** put gamma × (−1) before summation.

**Flip and walls**
- **Zero-gamma (flip):** the *repriced root* of net gamma over a band of hypothetical spots. Gamma is recomputed at each hypothetical spot.
  - If net gamma at spot is > 0, the scan runs downward; otherwise upward ("sign-resolved nearest").
- **Walls:** the largest side-gamma strike above (call) or below (put) spot.
  - **Dominance qualifier:** side gamma ≥ 1.5× the other side; otherwise tagged "(mixed)".
  - **Strength:** peak / median strike gross gamma; "(weak)" tag below a threshold.

**Pins and secondary levels**
- **Pins:**
  - call-dominant strikes within ±5 % of spot;
  - score = concentration / distance, with distance in units of 0.5 % of spot;
  - active only in positive gamma;
  - "puts never pin" is asserted, not tested.
- **Max pain:** shown but marked inactive beyond about 5 DTE ("empirically negligible", **uncited**).

**Overlays and horizons**
- **Vanna overlay:** gated on |ΔIV since open| ≥ 0.5 vol points. Falling IV means dealers buy, rising IV means they sell.
- **Charm overlay:** gated on ≤ about 5 DTE.
- **Three horizons:** monthly, weekly and 0DTE. **Gold has no 0DTE chain.**
- **Conviction** = |net Γ| / Σ|per-strike net Γ|.

**Decision layer and data cost**
- **Stance matrix** (regime × location, 4 × 2):
  - "at" a level means within 1·ATR(14);
  - a wall break is confirmed by a completed bar closing beyond it by 0.25·ATR.
- **Wall quality score (0–100):** "deliberately not a probability"; *uncalibrated*. Episodes are logged for future calibration.
- **Data cost:** CME and COMEX options top-of-book at $2/month each (non-professional).

**Limitations the author states (SOURCE §6)**
1. **The dealer-sign assumption is untestable** with OI data.
2. **OI is a prior-session figure** and is stale intraday.
3. **It is a "map, not a prediction engine"**; walls break, most readily in negative gamma.
4. **The quality score is uncalibrated.**
5. **No backtested P&L.**

**Internal inconsistency found (INFERENCE)**
- §3.3 says the engine "assumes dealers are long the calls and short the puts *that customers have bought*".
- If customers *bought* the calls, dealers are short them. The sentence contradicts itself.
- The arithmetic (+call, −put) matches S54's Model A, which instead frames it as customers *selling* calls (overwriting) and *buying* puts (protection).
- **Conclusion:** the economic story behind the sign is stated inconsistently even by a careful practitioner.

**Claims about walls (SOURCE):**
- "empirically tend to cap rallies and floor selloffs … most reliably while the market is in positive gamma";
- "puts never pin".
- **No data, test or citation** supports either claim beyond the general pinning literature (Ni–Pearson–Poteshman 2005; Avellaneda–Lipkin 2003).
- **Status: UNVERIFIED CLAIM.**

---

## S54: A. Chilingarian (July 2026), "The Sign of Dealer Gamma"
**File and status**
- **File:** `ssrn-7131778.pdf`, 12 pp., full text read.
- **Type:** independent working paper (SSRN). Not peer-reviewed.
- **Evidence status:**
  - **MEASUREMENT STANDARD.** Mathematics correct and verified (below).
  - The "institutional validation" checks agreement of sign, geometry and scale with vendors. It does **not** check predictive value.
  - The author states: "not a trading signal".

**Key mathematics (SOURCE, verified)**
- **Put–call parity:** C − P = S e^{−qT} − K e^{−rT}.
  - Therefore Δ_C − Δ_P = e^{−qT}, and Γ_C = Γ_P ≥ 0.
  - *Verified:* differentiate twice; the right-hand side is linear in S.
  - **Corollary:** the call/put sign in GEX is an **inventory assumption, not a property of the Greek**.
- **Three coherent sign models:**
  - **A** (+call, −put; SqueezeMetrics);
  - **B** (all negative; destroys bipolarity);
  - **C** (−call, +put; the exact negation of A).
- **Per contract:** GEX = |Γ|·OI·S²·m·sign, with m = 0.01.
  - The author omits the ×100 multiplier internally, giving a 1/100 scale.
  - The normalized form GEX/(S²m) is scale-free.
- **Flip:**
  - **Canonical:** the portfolio repriced root.
  - **Local:** linear interpolation between adjacent strikes with opposite net GEX within ±10 % of spot, S* = K⁻ + (K⁺−K⁻)|n(K⁻)|/(|n(K⁻)|+|n(K⁺)|).
  - **Zero-straddle rule:** a zero strike is a flip only if its neighbours have opposite signs.
- **Isolation experiment** (real 10,223-contract SPX snapshot): switching A↔C negates net GEX exactly; vanna, charm and the flip level are unchanged.
- **Software lesson ("masking test"):** a sign test run at a non-production scalar passes while production is inverted. Test at the operating point you ship.

**Semantics asserted (SOURCE, untested in the paper)**
- A positive-GEX strike below spot is *support*; above spot it is *resistance*.
- Negative-GEX strikes are *acceleration zones*.
- Long gamma means expect range; short gamma means expect move.
- **Status: PRACTITIONER CONVENTION.** Directional value is not claimed.

---

## Joint implications for NEXA (INFERENCE)

1. **True GEX needs per-strike OI plus option quotes (or IV) on the instrument NEXA trades or its futures.**
   - NEXA's Massive plan returns **NOT_ENTITLED** for option snapshots, quotes, trades and OI (probe 2026-10-04, see 03_DATA_AVAILABILITY_MATRIX).
   - MT5/Pepperstone has no options at all.
   - **GEX for XAUUSD/FX is UNAVAILABLE to NEXA today.**
2. **Even with OI, the sign is an assumption.** Every GEX-based hypothesis must carry "sign model A, unverified" and test the regime label against realized volatility *before* using it for direction.
3. **The economically testable core** is a *volatility* claim, not a direction claim: positive net dealer gamma is followed by lower realized volatility and more mean-reversion. That claim is falsifiable with OI history plus intraday prices.
4. **Proxy chains (GLD for gold; FXE/FXB/FXY for FX) are explicitly argued against by S53.**
   - The CFD–futures basis must also be mapped: about +$35–50 for GCZ6 vs XAUUSD in September 2026 (measured; see evidence/profile_proxy_check_results.csv).
5. **What can be adopted now (method, not signal):**
   - the sign contract;
   - the zero-straddle rule;
   - testing at the production operating point;
   - logging wall-test episodes for calibration;
   - "a quality score is not a probability".
