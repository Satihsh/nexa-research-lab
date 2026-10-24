# 07: ORDER FLOW MODEL (Tier 1)

**The data reality governs everything here:**
- **True order flow** (aggressor-signed trades) is **UNAVAILABLE**:
  - Pepperstone ticks carry no trade side or size (MEASURED);
  - Massive trades and quotes are NOT_ENTITLED.
- Every NEXA order-flow quantity is a **PROXY** and is labelled as one.

## 1. What order flow is (definitions)

| Quantity | True definition | NEXA proxy | Proxy status |
|---|---|---|---|
| Market (aggressor) order flow mo_t | Σ sign(aggressor)·size over the interval (S51) | (a) quote-direction tick rule (f30/f31, EQ-008); (b) BVC on futures bars (EQ-009) | (a) quote revisions, not trades; parity-exempt. (b) unvalidated; same-bar circular |
| Limit order flow lo_t | Net new best-price limit orders minus cancellations (S51) | None | UNAVAILABLE |
| Order-flow imbalance (normalised) | mo_t / Σ \|size\| or / ADV (S52 eq. 18–19) | δ̃ = δ/V; δ* = δ/Ê[\|δ\| \| how] (EQ-010) | PROXY |
| Aggression | Share of volume initiated at market | None (no initiator) | UNAVAILABLE |
| Absorption | Large aggressor volume with little price change at a level (S44) | High volume, small range (ABS, EQ-039) or low EVR (EQ-006). **Unsigned** | PROXY (unsigned) |
| Exhaustion | Declining aggressor flow as price extends | Declining RVOL with continued extension; a proxy-δ trend | PROXY |
| Liquidity consumption | Aggressor volume relative to resting depth | None | UNAVAILABLE |

## 2. What the evidence says order flow does

1. **Explains same-interval returns** (S51; original S13, S26, S34): strongly. R² up to over 50 % with limit flow (equities, 30 min). λ_M > λ_L > 0.
2. **Predicts the next move:**
   - **At seconds/event scale with book data:** yes, but short-lived (S34 AUC 0.72; S29 3–30 s; S13 < 10 events).
   - **At NEXA's ≥ 1-minute decision clock with public bars:** no evidence in the corpus (original contradiction A6). S51 offers *no* predictive test.
3. **Heterogeneous and time-of-day structured** (S52).
4. **Practitioner use** (S44): delta / cumulative delta as *confirmation at pre-defined levels* ("WHEN"), divergences on 1-minute charts, imbalances ≥ 300 % (display default), unfinished business as a "magnet". **All hypothetical trades.**

## 3. Order-flow model for NEXA (proxy-honest)

**Model OF-1 (lagged proxy flow → next return).** HYP-017.

    r_{t+1:t+H} / σ̂_t = α + Σ_{ℓ=1}^{L} β_ℓ·δ̃_{t−ℓ+1} + γ'·x^P_t + ε

- δ̃ comes from futures BVC (2 y) or the tick-rule proxy (28 d + forward).
- **Expected result (prior): β ≈ 0 at ≥ 1-minute horizons.** Reported honestly either way.
- **Same-bar δ̃_t enters only for *explanation* diagnostics, never for prediction.**

**Model OF-2 (confirmation at a level: the "WHEN" claim).** HYP-018 / HYP-022.

    Y_react = 1[price reverses ≥ kσ̂ before extending ≥ kσ̂ | price at level ℓ]
    P(Y_react | level features, lagged flow proxy over the approach)

- Compare nested models: levels only vs levels plus flow (EQ-032).
- **Divergence version (S44):** price makes a new low into the level while proxy cumulative δ rises over the approach window. A binary feature.

**Model OF-3 (absorption at a level, unsigned).** HYP-003.

    P(reversal | ABS_t high at level)   vs   P(reversal | ABS_t high off-level)   vs   P(reversal | random level)

## 4. Why "Delta > 300 %" is replaced

- **Origin:** S44's footprint imbalance colour threshold (ask ≥ 3 × diagonal bid). It is a **display default with no stated justification**, and it needs bid×ask volume per price, which NEXA cannot obtain.
- **A ratio of two small counts is unstable** (2 vs 13 already qualifies in S44's example). Its distribution depends on the instrument's tick size and activity.
- **Replacement (if a proxy is used):**
  - δ̃ = δ/V (share, bounded);
  - its **seasonal percentile** πδ (same hour-of-week, trailing K weeks);
  - δ* = δ / Ê[|δ| | how] (magnitude relative to normal).
- **Thresholds on percentiles are pre-registered**, e.g. πδ ≥ 0.9, with sensitivity to 0.8 and 0.95 counted as extra tests.

## 5. Look-ahead traps specific to flow proxies

1. **Same-bar circularity:** BVC and tick-rule signs are functions of the same price change. Using δ_t to "predict" r_t is an identity.
2. **Cumulative delta resets:** f31 resets at server midnight (NY 17:00). A cross-session level is a mix of regimes, so normalise or use within-session changes only.
3. **Tick proxies are not reproducible offline** (f30/f31 are parity-exempt). Any model resting *only* on them is blocked by `sole_basis_guard()`. Keep that rule.
4. **Survivorship in examples:** S44/S49 examples are chosen after the fact. Tests must use *all* level touches, not curated ones.

## 6. Upgrade path

| Data | Unlocks |
|---|---|
| Futures **trades** with side (or quotes for Lee–Ready classification) | True δ, footprint, imbalances, unfinished business, BVC validation, OF-1/2/3 on true data |
| Futures **quotes (BBO)** | Spread/depth-at-top proxies, microprice (still no depth beyond the top) |
| XAU broker DOM logging (prospective) | Broker-book imbalance (not an exchange book) |
| Longer MT5 tick history (forward logging, now running for 4 symbols via NEXA_TickLogger) | Reproducible tick-rule proxies for future backtests. Hawkes features |
