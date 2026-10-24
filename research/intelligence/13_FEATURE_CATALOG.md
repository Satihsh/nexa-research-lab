# 13: FEATURE CATALOG (research features NF-xxx)

**These are not production features.** Schema v1.0 (f00–f47) and PackFeatures() are unchanged. NF-xxx are *research candidates* for a possible future schema v1.1, which needs separate approval.

**Hierarchy (directive §12):**

    RAW (R) → PRIMARY (P) → DERIVED (D) → NORMALIZED (N) → STATE (S) → INTERACTION (I) → PREDICTIVE (Y)

**Field order in each entry:**
1. **Formula**
2. **Units**
3. **Inputs**
4. **TS / look-ahead rule**
5. **Normalization**
6. **Interpretation**
7. **Expected direction**
8. **Failure mode**
9. **Data requirements**
10. **Test**

**Standing rules for every feature:**
- **TS** ("standard"): computed from bars or ticks closed **before** t+Δ (the decision bar's close). Never uses the decision bar's successor.
- **No feature uses future data.** Labels (§8) may.
- **"PROXY"** marks any feature whose economic concept is measured indirectly (03).

---

## R: RAW (as stored; no transformation)

| ID | Raw series | Source | Status |
|---|---|---|---|
| R-01 | M1 OHLC (bid), tick_volume, spread | MT5 Pepperstone | TRUE price; activity PROXY |
| R-02 | Quote ticks (time_msc, bid, ask) | MT5 / NEXA_TickLogger | TRUE quotes |
| R-03 | Futures 1-min OHLC, volume, transactions, dollar_volume | Massive (GC, 6E, 6B, 6J, ES) | TRUE |
| R-04 | GLD option 1-min / daily OHLCV per series; contract reference | Massive | TRUE (GLD) |
| R-05 | Daily Treasury yields | Massive | TRUE |
| R-06 | Trade DNA (decisions, fills, signed slippage, costs) | EA | TRUE |

## P: PRIMARY measurements

**NF-001: log return r** (EQ-001)
1. ln(c_t/c_{t−1}), 1-min.
2. Dimensionless.
3. R-01.
4. Standard.
5. → σ̂ units at the N level.
6. Price change.
7. n/a.
8. Gaps, rollover.
9. M1.
10. Basis for all tests.

**NF-002: realised variance RV_W** (EQ-001)
1. Σ r² over window W (session or 60 min).
2. Variance.
3. NF-001.
4. Standard; W ends at t.
5. ln transform.
6. Activity of price.
7. n/a.
8. Weekend gaps (H-GAP-VOL).
9. M1.
10. Variance-signature plot.

**NF-003: Yang–Zhang σ̂_YZ** (EQ-002)
1. Per S48 / YZ over n sessions (session anchors 06 §3).
2. Volatility.
3. R-01 aggregated.
4. Uses completed sessions only, plus the developing session's partial OHLC (flagged).
5. Annualise or leave per session.
6. Volatility level.
7. n/a.
8. Session anchor choice.
9. M1.
10. QLIKE vs ATR (HYP-001b).

**NF-004: HAR forecast σ̂_{t+1}** (EQ-004)
1. exp(HAR fitted value), coefficients rolling and causal.
2. Volatility.
3. NF-002.
4. Coefficients fitted on [t−W, t−1].
5. —
6. Next-session volatility.
7. n/a.
8. Breaks.
9. M1.
10. DM test vs ATR/GARCH (H-VOL-1).

**NF-005: spread state** (f28 exists as spread/ATR)
1. s_t / σ̂_t (σ̂ from NF-004, not ATR).
2. Ratio.
3. R-01/02.
4. Standard.
5. Seasonal percentile.
6. Cost of immediacy.
7. Higher → worse net expectancy.
8. The bar spread is a close snapshot.
9. M1/ticks.
10. M-09 quantile regression.

**NF-006: activity V (tick)**
1. Σ tick_volume over the window.
2. Count.
3. R-01.
4. Standard.
5. → NF-010.
6. Quote activity (PROXY).
7. n/a.
8. Feed changes.
9. M1.
10. Proxy probe (03).

**NF-007: exchange volume V^F, transactions N^F**
1. Σ over the window.
2. Contracts / count.
3. R-03.
4. A futures bar is usable only if window_start + 60 s ≤ t + Δ.
5. → NF-011.
6. True activity.
7. n/a.
8. Roll weeks.
9. Massive.
10. HYP-016.

## D: DERIVED variables

**NF-010: RVOL (spot)** (EQ-005)
1. V / Ê[V | how], K = 8 closed weeks, median.
2. Ratio.
3. NF-006.
4. Baseline from closed weeks only.
5. Seasonal ratio.
6. Unusual activity.
7. Higher → higher next RV (HYP-002).
8. DST: compute in UTC with explicit anchors.
9. M1.
10. ΔQLIKE over HAR.

**NF-011: RVOL (futures)** (EQ-005)
- As NF-010, on V^F.
- TRUE (2 y).
- HYP-016: incremental value over NF-010.

**NF-012: EVR effort–result residual** (EQ-006)
1. ln(|r|+ε) − fitted(ln V, how), rolling past fit.
2. Log ratio.
3. NF-001, NF-006/007.
4. Coefficients from [t−W, t−1].
5. Seasonal percentile.
6. Absorption (≪ 0) vs thin move (≫ 0).
7. At a level: absorption → reversal (practitioner claim).
8. ε choice; unstable fit.
9. M1 (+ futures).
10. HYP-003.

**NF-013: Amihud illiquidity** (EQ-007)
1. |r| / V (futures: / dollar_volume).
2. Price change per unit activity.
3. NF-001/006/007.
4. Standard.
5. Log + seasonal percentile.
6. Thin vs thick market.
7. Higher → larger next \|r\|.
8. Zero volume.
9. M1.
10. HYP-003 family.

**NF-014: average trade size V^F/N^F**
1. Ratio, seasonal percentile.
2. Contracts per trade.
3. R-03.
4. As NF-007.
5. Percentile.
6. Large-clip participation (S52 mechanism; agents unidentified).
7. Unknown.
8. Contract changes.
9. Massive.
10. Ablation within HYP-016.

**NF-015: compression ratio CR** (EQ-019)
1. σ̂_YZ(1 session) / σ̂_YZ(20 sessions).
2. Ratio.
3. NF-003.
4. Standard.
5. Percentile.
6. Compression → expansion.
7. Low CR → higher next RV; **direction unpredictable**.
8. Session definition.
9. M1.
10. HYP-019.

**NF-016: efficiency ratio ER_n** (EQ-020)
1. |Δp_n| / Σ|Δp|, n = 60 min.
2. [0,1].
3. NF-001.
4. Standard.
5. —
6. Trend vs chop.
7. —
8. —
9. M1.
10. HYP-020 state input.

**NF-017: variance ratio VR(q)** (EQ-021)
1. Rolling VR(5) on 1-min returns over 1 session.
2. Ratio.
3. NF-001.
4. Standard.
5. —
6. Persistence (> 1) vs reversion (< 1).
7. —
8. Bid-bounce bias at 1 min (S38).
9. M1.
10. H-VR-SCALE.

**NF-018: permutation entropy PE_m** (EQ-022)
1. m = 4, window 240 bars.
2. [0,1].
3. NF-001.
4. Standard.
5. —
6. Ordinal disorder.
7. Low PE → stronger \|autocorrelation\|.
8. Ties at round prices.
9. M1.
10. HYP-021.

**NF-020: BVC delta δ (futures)** (EQ-009) **PROXY**
1. V(2Φ(Δp/σ̂_Δp) − 1).
2. Contracts.
3. R-03.
4. **Predictive use only at lags ≥ 1.**
5. → NF-021.
6. Signed activity proxy.
7. Lagged β ≈ 0 expected.
8. **Same-bar circularity**; unvalidated.
9. Massive.
10. HYP-017.

**NF-022: tick-rule OBI (= f30), CVD (= f31)** (EQ-008) **PROXY**
1. Existing.
2. [−1,1] / count.
3. R-02.
4. Live only; parity-exempt.
5. CVD → within-session change ÷ seasonal \|ΔCVD\|.
6. Quote-revision direction.
7. Unknown.
8. Non-reproducible offline.
9. Ticks.
10. HYP-017b (demo data only).

## N: NORMALIZED features (what models consume)

| ID | Feature | Formula | Notes |
|---|---|---|---|
| NF-021 | δ̃, δ*, πδ | EQ-010 | PROXY. Lags ≥ 1 |
| NF-023 | Return in σ̂ units | r / σ̂_{t−1} | — |
| NF-024 | Distance to VAH / VAL / POC (prior session) | (p_t − level)/σ̂_day | POC fragile (06 §2). VA preferred |
| NF-025 | Seasonal percentiles of NF-005, NF-010–NF-014 | F̂_{same-how, K weeks}(q_t) | Robust to feed level shifts |

## S: STATE variables

**NF-030: liquidity density at the price** (EQ-012)
1. L(p_t, t) / max_p L.
2. [0,1].
3. M-02.
4. Field from closed bars only.
5. Density percentile.
6. Thick (HVN) vs thin (LVN) location.
7. Low → faster travel (HYP-004).
8. Bandwidth choice.
9. M1 or futures.
10. HYP-004.

**NF-031: futures-derived density at the spot price** (EQ-012 + EQ-026)
- As NF-030, on futures volume, mapped via the causal basis b̂_t.
- TRUE volume, basis-mapped.
- 2 years.
- HYP-016.

**NF-032: log-gradient g = ∂_p ln L** (EQ-013)
1. Kernel derivative at p_t, × σ̂.
2. Dimensionless.
3. M-02.
4. Closed bars.
5. ×σ̂ scaling.
6. "Pull" toward density.
7. sign(g) predicts sign of drift (HYP-005).
8. Multi-modal noise.
9. M1.
10. HYP-005.

**NF-033: curvature κ = h²∂²ln L** (EQ-013)
1. As above.
2. Dimensionless.
6. HVN (< 0) vs LVN (> 0).
7. HVN → reversion; LVN → continuation (HYP-006).
10. HYP-006.

**NF-034: profile concentration C** (EQ-015)
1. 1 − H/ln J, σ̂-scaled bins.
2. [0,1].
4. Completed session (prior day) or developing.
6. Balance (high C) vs trend (low C).
7. —
8. Depends on J/range.
10. HYP-014.

**NF-035: VA acceptance flag**
1. 1 if, after opening outside the prior VA, two consecutive 30-min closes are inside.
2. Binary.
4. Known at the second close.
6. S42 "Value-Area Rule" trigger.
10. HYP-007.

**NF-040: IB width IBR = IB / σ̂_day** (EQ-016)
1. First-60-minute range after the anchor ÷ σ̂.
2. Ratio.
4. Known 60 minutes after the anchor.
6. Base width.
7. Small IB → trend day / large extension (S46).
10. HYP-011.

**NF-041: developing range extension REX_dev** (EQ-016)
1. (H_so-far − L_so-far − IB)/IB.
4. **Developing only**; the final REX is a label.
6. OTF participation proxy (S46).
10. HYP-011.

**NF-042: open type (codified S42)**
- Categories:
  - **Drive:** the first 15 minutes move ≥ x·σ̂ one way with no return through the open.
  - **Test-drive:** probe beyond a reference level, then drive the opposite way.
  - **Rejection-reverse.**
  - **Auction.**
- Known at anchor + 30 minutes.
- Codification is NEW (S42 gives no thresholds). Thresholds are pre-registered.
- HYP-012.

**NF-043: prior-day type** (EQ-016–018)
- Nontrend / normal / normal-variation / trend / neutral(-extreme), from the completed prior session.
- HYP-008/009/010.

**NF-044: regime filtered probability P(z_t = k | x_{≤t})** (EQ-023)
- Forward-filter only.
- HYP-020.

**NF-045: hour-of-week / session phase**
- Categorical.
- Exists implicitly (session filters).
- Conditioning for all.

**NF-046: cross-asset context**
- ES 1-min RV percentile; XAU–USD-basket correlation (time-aligned); ΔUS10Y (daily, prior close).
- M-08.
- HYP-031/032.

**NF-047: execution state E[c | x^E]** (M-09)
- Spread percentile × quote intensity × session × news.
- Prospective (S14).
- HYP-035.

## I: INTERACTION features (only after main effects pass)

| ID | Interaction | Hypothesis |
|---|---|---|
| NF-050 | At-level indicator (\|NF-024\| ≤ 0.25 σ̂, or NF-033 HVN) × lagged πδ (NF-021) | WHERE × WHEN (HYP-022) |
| NF-051 | At-level × NF-012 (absorption) | HYP-003 at levels |
| NF-052 | NF-015 (compression) × NF-044 (regime) | HYP-019/020 |
| NF-053 | NF-040 (IB width) × NF-043 (prior day type) | HYP-011 extension |
| NF-054 | Level type × GEX regime × HPR | HYP-026/027. **BLOCKED** |

## Y: PREDICTIVE targets and forecasts (labels may use the future)

| ID | Object | Definition | Horizon |
|---|---|---|---|
| Y-01 | Next-session realised volatility | ln RV_{s+1} | 1 session |
| Y-02 | Barrier outcome | Target-before-stop indicator for a fixed (U, D) in σ̂ units, from fill to barrier or horizon (labels start at `fill_ts`) | ≤ H bars |
| Y-03 | Net R | EQ-025, cap-neutral definition | Trade |
| Y-04 | Level reaction | Reverse ≥ kσ̂ before extend ≥ kσ̂, given a touch of a level | ≤ H bars |
| Y-05 | Day type of the current session | Final REX/CL/ROT class | Session end |
| Y-06 | Slippage (signed, R) | From fills | Trade |

**Forecast features consumed by the decision layer:** P_U(x), E[R_net | x] (via EQ-034 + EQ-025), σ̂_{t+1}, E[c | x^E].
