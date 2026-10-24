# RESEARCH HYPOTHESIS BACKLOG (post-corpus study)

Built 2026-10-02, **after** all 39 corpus files (38 distinct works) were studied.

## Ground rules (binding)

**These are hypotheses, not strategies.** No item claims or implies profitability.

**Every test is research-only:**
- no change to NEXA production code, NEXA_Risk.mqh, V2, the frozen 8E campaign or frozen protocols;
- no deployment, no trading, no connection to live execution;
- no promotion;
- no flags passed to `freeze_*.py`.

**Any test requires a new, separately approved and frozen protocol.**
- Evaluate in-sample (IS) first, then **prospectively** out of sample (OOS).
- V2's 2027 OOS stays unopened.

**Each entry gives all 13 required fields:**
1. Sources
2. Principle
3. Mathematical basis
4. Mechanism
5. Required data
6. Expected effect *(the measurable direction if the hypothesis holds; not a P&L claim)*
7. Confounders
8. Failure conditions
9. Look-ahead risks
10. Overfitting risks
11. Validation
12. NEXA data availability: ✓ available / ◐ partial / ✗ not available
13. Evidence level

---

## 0. Summary and priority

**Priority** follows S05-style dependency-aware sequencing:
1. method-hygiene items first (they gate everything else);
2. then the volatility/risk layer (strongest evidence);
3. then execution realism (needs logging);
4. then regime and session descriptors;
5. then low-prior pattern items.

| ID | Layer | Priority | Data | Evidence level |
|---|---|---|---|---|
| H-DELAY-PARITY | Method | 1 | ✓ | Research principle (S22) / hypothesis for NEXA |
| H-COST-SHRINK | Method | 1 | ✓ | Research principle |
| H-SEARCH-DEFLATE | Method | 1 | ✓ | Established statistics; hypothesis for NEXA |
| H-NOISE-OBJ | Method | 1 | ✓ | Research finding (S04) |
| H-ABLATE | Method | 2 | ✓ | Strongly supported method (S26) |
| H-HIT-PROB | Payoff null | 1 | ✓ | Established maths; hypothesis as NEXA null |
| H-VOL-1 | Volatility | 2 | ✓ | Supported finding (equities) → hypothesis |
| H-VOL-2 | Volatility/sizing | 3 | ✓ | Supported → hypothesis |
| H-VOL-3 | Volatility | 3 | ✓ | Supported finding (equities) → hypothesis |
| H-VOL-4 | Volatility | 3 | ✓ | Supported finding (equities) → hypothesis |
| H-ROUGH-1 | Volatility | 3 | ✓ | Research finding (equities) → hypothesis |
| H-VR-SCALE | Volatility | 2 | ✓ | Theory + practitioner → hypothesis |
| H-VAR-TRIGGER | Risk gate | 3 | ✓ | Research finding → hypothesis |
| H-GAP-VOL | Volatility hygiene | 2 | ✓ | Supported (S15 simulation) |
| H-SPREAD-REGIME | Cost | 3 | ◐ | Hypothesis |
| H-VOLTARGET-CAP | Sizing | 4 | ✓ | Literature pointer → hypothesis |
| H-MU-SIGMA2 | Sizing | 6 | ◐ | Research finding (preliminary) |
| H-TAIL-SIM | Risk | 4 | ✓ | Hypothesis (tool) |
| H-NEWS-SLIP | Execution | 2 | ◐ | Strongly supported mechanism (CLOB) → hypothesis for OTC |
| H-STOP-SLIP | Execution | 2 | ◐ | Supported mechanism → hypothesis |
| H-LASTLOOK-REJECT | Execution | 3 | ◐ | Established theory → hypothesis |
| H-DEVIATION-OPT | Execution | 4 | ✗ (until logs) | Established (model) → hypothesis |
| H-HURST-GATE | Regime | 3 | ✓ | Hypothesis |
| H-THICKNESS-ER | Regime | 4 | ✓ | Hypothesis (practitioner origin) |
| H-TSMOM-TANH | Regime | 4 | ✓ | Hypothesis |
| H-SESSION-SPLIT | Session | 3 | ✓ | Strongly supported (equities) → hypothesis |
| H-FIX-FLOW | Session | 4 | ✓ | Unverified claim → hypothesis |
| H-GOTOBI / H-OPEN-CONT | Session | 5 | ✓ | Practitioner claim → hypothesis |
| H-NEWS-PTD | Event | 4 | ◐ | Unverified claim → hypothesis |
| H-LEADLAG-FX (incl. H-CROSS-LEAD) | Cross-asset | 5 | ◐ | Research finding (equities) / anecdote |
| H-PAIRS-OU | Relative value | 6 | ◐ | Hypothesis |
| H-ENVELOPE | Governance | 2 | ✓ | Practitioner consensus |
| H-PARTIAL-EXIT | Payoff | 5 | ✓ | Unverified claim → hypothesis |
| H-ROUND-NUM | Microstructure | 5 | ✓ | Textbook statement → hypothesis |
| H-SQUEEZE-VARIANTS | Pattern | 6 | ✓ | Unverified claim |
| H-TD-CANON | Pattern | 6 | ✓ | Unverified claim |
| H-PATTERN-LOWPRIOR | Pattern | 7 | ✓ | Unverified claim |
| H-RETURN-50 | Pattern | 8 | ✓ | Unverified, weakly falsifiable |
| H-CARRY-SWAP | Carry | 8 | ✗ | Established (literature) / data-limited |
| H-ENSEMBLE-META | Allocation | 8 | ✓ | Hypothesis (only if any engine shows edge) |

---

## 1. Method-hygiene hypotheses (gate all other work)

### H-DELAY-PARITY: the timing illusion in NEXA backtests
1. **Sources:** S22 App. A (delay-0 "borderline in-sample"); S14 Ch. 4–5 (same-close execution); NEXA D-EXEC-ENTRYBAR (prior fact).
2. **Principle:** an edge that disappears when execution moves one bar later was a timing artefact.
3. **Math basis:** Δ = metric(delay-0) − metric(delay-1). With signal s_t from bar t's close, delay-1 P&L uses entry at open_{t+1} + spread.
4. **Mechanism:** same-bar fills use prices unavailable at decision time; bar-internal paths are unknown.
5. **Required data:** NEXA M1–D1 bid/ask bars; existing engine signal logs.
6. **Expected effect:** delay-1 metrics ≤ delay-0. The size of Δ ranks engines by timing fragility.
7. **Confounders:** spread regime at the next open (rollover, Sunday open); gaps.
8. **Failure conditions:** Δ ≈ 0 for all engines (then timing is not an issue), or bar data too coarse to separate.
9. **Look-ahead risks:** the test *targets* look-ahead; ensure delay-1 truly uses only information ≤ t.
10. **Overfitting risks:** low (no parameters).
11. **Validation:** re-run existing frozen engines in a **research copy** with an execution switch; no retuning; report both side by side.
12. **NEXA data:** ✓.
13. **Evidence level:** research principle (SOURCE) / hypothesis for NEXA.

### H-COST-SHRINK: expected-move-vs-cost gate
1. **Sources:** S22 eq. 551 (E_eff); S02 eq. 35; S03 eq. 4; S13; S14 Fig 4.6; S32 Ch. 21.
2. **Principle:** a signal whose expected move per trade does not exceed the round-trip cost should be zeroed.
3. **Math basis:** E_eff = sign(E)·max(|E| − (spread + commission + slippage), 0); cost curve SR(c).
4. **Mechanism:** costs are certain; signal edge is uncertain and small.
5. **Required data:** engine forecasts or expected R; per-symbol spread distribution by session; slippage assumptions.
6. **Expected effect:** fewer trades and lower gross turnover. Net metrics should not deteriorate if cost dominates (measurement, not a profit claim).
7. **Confounders:** E estimated in-sample (optimistic); spread regime shifts.
8. **Failure conditions:** expected-move estimates uncalibrated, so the gate removes random trades.
9. **Look-ahead risks:** the E estimate must come from past data only; spread at the decision time, not the realised fill.
10. **Overfitting risks:** the threshold choice. Pre-register it as "cost = realised median spread + fixed slippage".
11. **Validation:** cost curve per engine (SR vs cost multiple 0×–3×); IS then prospective.
12. **NEXA data:** ✓ (spread); ◐ (slippage).
13. **Evidence level:** research principle.

### H-SEARCH-DEFLATE: every sweep reports its search size
1. **Sources:** S33 (≈ 480k candidates; OOS in loop); S14 (cites DSR); S36 (~100 ADF tests/yr); S02 (random search); S32 Ch. 22 (selection bias).
2. **Principle:** the best of many backtests is biased upward.
3. **Math basis:** under no skill, E[max of K Sharpe estimates] ≈ σ_SR√(2 ln K). Deflated Sharpe (Bailey–López de Prado); PBO via combinatorial symmetric cross-validation.
4. **Mechanism:** selection on noise.
5. **Required data:** logs of all configurations evaluated (MT5 tester sweeps, Python research).
6. **Expected effect:** deflated metrics are materially below the raw best. Fewer candidates pass.
7. **Confounders:** correlated candidates (effective K < K). Estimate effective K by clustering candidate returns (EVIDENCE_MAP §6 families).
8. **Failure conditions:** candidate logs incomplete.
9. **Look-ahead risks:** none directly; the holdout must not be consulted during search (S33 lesson).
10. **Overfitting risks:** this *is* the countermeasure.
11. **Validation:** apply retrospectively to past sweeps (research only) and prospectively to all new ones.
12. **NEXA data:** ✓ (if sweep logs exist; otherwise start logging).
13. **Evidence level:** established statistics; hypothesis for NEXA application.

### H-NOISE-OBJ: measure objective noise before optimising
1. **Sources:** S04 (MC cost SD 9.53 % of mean; SRFG vs SLSQP); S02 (±2.08 block dispersion); S31 (single use "highly random").
2. **Principle:** if metric noise ≥ the parameter effect, the optimum is noise.
3. **Math basis:** bootstrap or block-bootstrap SE of the objective for each candidate; compare with between-candidate differences.
4. **Mechanism:** finite samples and path dependence.
5. **Required data:** trade lists per candidate.
6. **Expected effect:** most parameter differences in NEXA sweeps fall inside noise bands.
7. **Confounders:** autocorrelated trades (use a block bootstrap).
8. **Failure conditions:** too few trades for a bootstrap.
9. **Look-ahead risks:** none.
10. **Overfitting risks:** none (diagnostic).
11. **Validation:** report noise bands with every sweep.
12. **NEXA data:** ✓.
13. **Evidence level:** research finding (S04) / established statistics.

### H-ABLATE: where does an engine's information live?
1. **Sources:** S26 (70 % vs 54 % blinded); S23 (unseen-asset tests).
2. **Principle:** an edge relying on unavailable or proxy information is not real for NEXA.
3. **Math basis:** baseline-relative accuracy / metric difference between full and ablated feature sets; permutation importance.
4. **Mechanism:** proxies (tick_volume as volume; quote counts as OFI) may carry spurious information.
5. **Required data:** engine feature sets.
6. **Expected effect:** features based on tick_volume/OFI proxies add little once removed.
7. **Confounders:** correlated features; use grouped permutation.
8. **Failure conditions:** engines too simple to ablate.
9. **Look-ahead risks:** fit any scaling/PCA on the training window only (S26 practice).
10. **Overfitting risks:** low.
11. **Validation:** walk-forward ablation.
12. **NEXA data:** ✓.
13. **Evidence level:** strongly supported method.

### H-HIT-PROB: driftless two-barrier null for TP/SL rules
1. **Sources:** S27 (first-passage maths, verified); MATH M1/M1b; S01 G5 (break-even p* = 1/(1 + R)); S08 (win-rate illusion).
2. **Principle:** without drift, P(target first) = L/(U + L) = break-even win rate, so exits cannot create edge.
3. **Math basis:** P(U first) = (1 − e^{θL})/(e^{−θU} − e^{θL}), θ = 2µ/σ²; µ = 0 ⇒ L/(U + L).
4. **Mechanism:** martingale property of driftless prices.
5. **Required data:** NEXA trade lists (entry, SL, TP, outcome); bar paths.
6. **Expected effect:** realised hit rates cluster near L/(U + L) unless entries carry drift. Deviations measure entry skill **or** path effects (bounce, gaps, fills through stops).
7. **Confounders:** spread asymmetry (stop on bid/ask); bar-level monitoring; volatility clustering; time stops.
8. **Failure conditions:** heavy jumps make the continuous null inappropriate (use an empirical bootstrap null instead).
9. **Look-ahead risks:** none if SL/TP are fixed at entry.
10. **Overfitting risks:** none (null model).
11. **Validation:** compare each engine's hit rate and expectancy with the analytic null and a random-entry null with identical exits.
12. **NEXA data:** ✓.
13. **Evidence level:** established mathematics; hypothesis as a NEXA null.

### H-ENVELOPE: operational-envelope monitoring
1. **Sources:** S31 (Modular FX: operational envelope, no live parameter changes, deviation kill switch, calibration vs choice data); S30 (normal accidents); NEXA_Safety.mqh (prior fact).
2. **Principle:** an engine should only act inside the market states it was tested in.
3. **Math basis:** envelope = joint ranges/quantiles of state variables (spread/ATR, volatility percentile, session, news flag) from the test period. Out-of-envelope flag = any variable outside its tested quantiles.
4. **Mechanism:** performance is regime-conditional (EVIDENCE_MAP P12).
5. **Required data:** state variables at each historical decision.
6. **Expected effect:** out-of-envelope trades show different (typically worse or more variable) outcomes than in-envelope trades.
7. **Confounders:** small out-of-envelope samples.
8. **Failure conditions:** envelope too wide (no information) or too narrow (no trades).
9. **Look-ahead risks:** quantiles must come from the test period, not the evaluation period.
10. **Overfitting risks:** the choice of variables; pre-register them.
11. **Validation:** descriptive, then prospective monitoring (research only).
12. **NEXA data:** ✓.
13. **Evidence level:** practitioner consensus.

---

## 2. Volatility and risk layer

### H-VOL-1: HAR-D log-RV forecasts beat ATR for XAU/FX volatility
1. **Sources:** S23 (HAR-D, QLIKE, DM, unseen stocks); S04/S18 (roughness); S39 (GARCH baseline).
2. **Principle:** volatility is forecastable; long-memory log-variance models beat naive range averages.
3. **Math basis:** RV = log Σr²; HAR: RV_{t+1} = α + β_dRV_d + β_wRV_w + β_mRV_m (+ diurnal term D); QLIKE = mean[e^{RV}/e^{R̂V} − (RV − R̂V) − 1]; DM test.
4. **Mechanism:** volatility clustering with multiscale persistence.
5. **Required data:** M1 bid (mid ≈ bid + spread/2) for XAU and FX symbols; session calendar (server = NY+7).
6. **Expected effect:** lower QLIKE than ATR14/ATR50 scaled forecasts at next-hour / next-session horizons.
7. **Confounders:** weekend/rollover gaps (H-GAP-VOL); diurnal seasonality; spread spikes inflating RV.
8. **Failure conditions:** DM test not significant; gains vanish after diurnal adjustment.
9. **Look-ahead risks:** RV only from closed bars before the forecast time; the diurnal profile from past days only.
10. **Overfitting risks:** low (few parameters); avoid choosing horizons after seeing results.
11. **Validation:** rolling annual retraining; QLIKE + DM; then prospective.
12. **NEXA data:** ✓.
13. **Evidence level:** supported finding (equities) → hypothesis for XAU/FX.

### H-VOL-2: volatility-forecast-scaled stops/size reduce drawdown at similar return (within the fixed 1 % cap)
1. **Sources:** S02 (1/σ), S03, S13 (μ/σ²), S22 §15.3.1 (vol-managed), S23.
2. **Principle:** equal ex-ante risk per trade stabilises outcomes.
3. **Math basis:** size ∝ min(1, σ*/σ̂) (scale **down only** from the fixed cap); stop distance ∝ σ̂.
4. **Mechanism:** better σ̂ means more uniform realised risk.
5. **Required data:** H-VOL-1 forecasts; engine trade lists.
6. **Expected effect:** lower drawdown dispersion and loss-streak depth; return per unit risk unchanged or modestly changed.
7. **Confounders:** stop distance changes the hit rate (H-HIT-PROB); costs relative to smaller stops (S13: tiny costs kill).
8. **Failure conditions:** forecast errors in jumps (the ex-ante σ is too low exactly when it matters).
9. **Look-ahead risks:** σ̂ from data before entry only.
10. **Overfitting risks:** choice of σ*; fix it ex ante.
11. **Validation:** research simulation only. **NEXA_Risk caps unchanged**; compare drawdown statistics IS, then prospective.
12. **NEXA data:** ✓.
13. **Evidence level:** supported (literature) → hypothesis.

### H-VOL-3: last-hour-of-session RV carries extra information on next-day volatility
1. **Sources:** S23 §7 (last half hour has the largest coefficient).
2. **Principle:** late-session volatility reflects information arrival and positioning.
3. **Math basis:** daily RV regressed on intraday RV buckets (Intraday2Daily).
4. **Mechanism:** closing flows and information timing.
5. **Required data:** M1 bars; NY-close (17:00 NY = server 00:00) session map.
6. **Expected effect:** a significant positive coefficient on the last NY hour beyond daily lags.
7. **Confounders:** rollover spread spikes at the NY close for XAU (NEXA tick audit); FX trades 24 h, so "session end" is a convention.
8. **Failure conditions:** the effect is driven by rollover spread artefacts.
9. **Look-ahead risks:** align buckets in UTC with DST.
10. **Overfitting risks:** bucket choice; pre-register buckets.
11. **Validation:** OOS QLIKE/DM.
12. **NEXA data:** ✓.
13. **Evidence level:** supported (equities) → hypothesis.

### H-VOL-4: a cross-symbol "market RV" factor improves single-symbol forecasts
1. **Sources:** S23 (commonality; augmented training).
2. **Principle:** volatility has common components.
3. **Math basis:** add the equal-weighted mean of log RV across symbols to HAR.
4. **Mechanism:** shared macro/USD shocks.
5. **Required data:** synchronised M1 bars for XAU, EURUSD, GBPUSD, USDJPY, etc.
6. **Expected effect:** QLIKE improvement for most symbols.
7. **Confounders:** USD-leg mechanical commonality across pairs.
8. **Failure conditions:** gains only from mechanical USD overlap.
9. **Look-ahead risks:** the market factor from the same closed bars only.
10. **Overfitting risks:** symbol set selection.
11. **Validation:** OOS with DM; leave-one-symbol-out test (S23 unseen-asset analogue).
12. **NEXA data:** ✓ (symbols already held; no broad downloads).
13. **Evidence level:** supported (equities) → hypothesis.

### H-ROUGH-1: XAU/FX log-volatility is rough (H ≈ 0.1)
1. **Sources:** S04 Ch. 5 (GJR estimator; H 0.066–0.140 for indices); S18.
2. **Principle:** power-law volatility kernels.
3. **Math basis:** m(q, Δ) = mean|log σ_{t+Δ} − log σ_t|^q ∝ Δ^{ζ_q}; slope of ζ_q vs q ≈ H.
4. **Mechanism:** multiscale order flow and information.
5. **Required data:** daily (or sub-daily) RV from M1.
6. **Expected effect:** H̃ well below 0.5 for XAU/FX.
7. **Confounders:** daily integration biases H upward (S04); microstructure noise in RV.
8. **Failure conditions:** estimates unstable across windows.
9. **Look-ahead risks:** none for estimation; forecasts must be causal.
10. **Overfitting risks:** low.
11. **Validation:** stability across subperiods; compare with a simulated RFSV/fBm null.
12. **NEXA data:** ✓.
13. **Evidence level:** research finding (equities) → hypothesis.

### H-VR-SCALE: variance ratios across bar sizes
1. **Sources:** S38 (intervalling kernel); S15 (scaling); S31 (HSBC March 2020 chart); S32 Ch. 14 (bounce).
2. **Principle:** measured volatility depends on sampling interval when returns are autocorrelated.
3. **Math basis:** VR(k) = Var(r_k)/(k·Var(r_1)); OU: VR = (1 − e^{−θh})/(θh).
4. **Mechanism:** bid/ask bounce (VR < 1 at short k); trending (VR > 1).
5. **Required data:** closed bars M1→H4 for XAU/FX.
6. **Expected effect:** VR(k) < 1 at short k on bid-based bars; regime variation (lower in stress).
7. **Confounders:** bid-only bars embed spread changes; overlapping-return estimators need corrections (Lo–MacKinlay).
8. **Failure conditions:** VR ≈ 1 everywhere (then cross-frame ATR transfer is fine).
9. **Look-ahead risks:** none for description.
10. **Overfitting risks:** low.
11. **Validation:** heteroskedasticity-robust VR tests; per session/regime.
12. **NEXA data:** ✓.
13. **Evidence level:** theory + practitioner chart → hypothesis.

### H-VAR-TRIGGER: conditional-quantile risk gates have stable trigger frequency
1. **Sources:** S39 (EGARCH-X skew-t ERaR; PIT, log score, Diks); S23.
2. **Principle:** quantile-of-density thresholds adapt to volatility while fixing trigger frequency.
3. **Math basis:** gate if r_t ∉ [Q(θ | F_{t−1}), Q(1 − θ | F_{t−1})]; GARCH-t/EGARCH-t density; Kupiec/Christoffersen coverage.
4. **Mechanism:** volatility clustering; fixed ATR multiples trigger more in high volatility.
5. **Required data:** XAU/FX bars at D1–H1.
6. **Expected effect:** gate frequency close to nominal across regimes (coverage tests pass), unlike fixed-multiple gates.
7. **Confounders:** fat tails and skew (use skew-t); event days.
8. **Failure conditions:** coverage tests reject; the PIT is non-uniform.
9. **Look-ahead risks:** **only lagged regressors** (S39's same-day regressor issue).
10. **Overfitting risks:** model-family choice; compare with GARCH(1,1)-t as baseline.
11. **Validation:** PIT, log score, Diks test, coverage tests OOS.
12. **NEXA data:** ✓.
13. **Evidence level:** research finding → hypothesis (a risk-layer tool, not an entry signal).

### H-GAP-VOL: weekend/rollover gap conventions bias NEXA volatility
1. **Sources:** S15 Ch. 5 (interpolation −20 %, business time +25 % in σ̂); S01 (Sunday open); NEXA time conventions (server = NY+7; D-TZ open item).
2. **Principle:** gap handling materially changes volatility estimates.
3. **Math basis:** σ̂² inflation 168/108 in business time; interpolation dilutes.
4. **Mechanism:** non-trading periods.
5. **Required data:** M1 bars with gaps flagged.
6. **Expected effect:** ATR/RV differ by up to ≈ 20–25 % across conventions, most on Monday bars.
7. **Confounders:** genuine Monday volatility.
8. **Failure conditions:** negligible differences on H1+ bars.
9. **Look-ahead risks:** none.
10. **Overfitting risks:** none.
11. **Validation:** document the NEXA convention; sensitivity table.
12. **NEXA data:** ✓.
13. **Evidence level:** supported (simulation) → hypothesis for NEXA.

### H-SPREAD-REGIME: XAU spreads follow a few discrete states
1. **Sources:** S24 (grid discreteness; supracompetitive equilibria); S11 (spread ∝ σ); NEXA tick audit (modal 12, jumps to 17 at rollover).
2. **Principle:** spreads are endogenous and discrete.
3. **Math basis:** hidden-Markov chain over spread states; transition matrix by session.
4. **Mechanism:** dealer pricing with a tick grid; risk at rollover/news.
5. **Required data:** tick data (only ~21 days now; must be recorded going forward).
6. **Expected effect:** 3–5 states with session-dependent occupancy.
7. **Confounders:** broker configuration changes.
8. **Failure conditions:** insufficient tick history.
9. **Look-ahead risks:** state estimation must be filtered, not smoothed, if used in decisions.
10. **Overfitting risks:** number of states.
11. **Validation:** descriptive, then prospective stability.
12. **NEXA data:** ◐.
13. **Evidence level:** hypothesis.

### H-VOLTARGET-CAP: σ_target/σ exposure scaling (≤ 1)
1. **Sources:** S22 §6.5, §15.3.1 (vol-managed portfolios; momentum crashes); S02.
2. **Principle:** de-risk after volatility spikes.
3. **Math basis:** w = min(1, σ_target/σ̂).
4. **Mechanism:** volatility clustering and negative skew after high-volatility downturns.
5. **Required data:** bars; engine trade lists.
6. **Expected effect:** reduced clustering of losses in high-volatility periods.
7. **Confounders:** fewer trades in high volatility may also cut gains.
8. **Failure conditions:** volatility forecasts lag jumps.
9. **Look-ahead risks:** σ̂ ex ante.
10. **Overfitting risks:** σ_target choice; fix it ex ante.
11. **Validation:** research simulation; **caps unchanged**.
12. **NEXA data:** ✓.
13. **Evidence level:** literature pointer (S22, second-hand) → hypothesis.

### H-MU-SIGMA2: Kelly-like μ/σ² down-scaling
1. **Sources:** S13 App. A.1; S22 eq. 373; S21 (fractional-Kelly caution); S12.
2. **Principle:** size ∝ expected return ÷ variance.
3. **Math basis:** α* = μ/σ² (scale-free), capped at the fixed 1 % risk and scaled down only.
4. **Mechanism:** mean–variance optimality.
5. **Required data:** calibrated per-signal μ and σ (**not available**).
6. **Expected effect:** small risk-adjusted improvement if μ is calibrated; harm if not.
7. **Confounders:** plug-in error amplifies (μ/σ² is sensitive).
8. **Failure conditions:** μ estimates noisy (likely).
9. **Look-ahead risks:** μ from past only.
10. **Overfitting risks:** high.
11. **Validation:** only after a calibration study shows reliable μ.
12. **NEXA data:** ◐.
13. **Evidence level:** research finding (preliminary).

### H-TAIL-SIM: heavy-tailed simulation of loss streaks within caps
1. **Sources:** S35 (VG tails); S39 (ν ≈ 8.5); S21 (avalanche risk); S01 (single large loss).
2. **Principle:** risk caps should be stress-tested under fat tails, not Gaussian paths.
3. **Math basis:** Student-t/VG/GARCH-t bootstraps; block bootstrap of trade outcomes.
4. **Mechanism:** fat tails and clustering produce longer loss streaks than i.i.d. normals.
5. **Required data:** engine trade outcomes; return distributions.
6. **Expected effect:** P(drawdown > X) higher than Gaussian estimates.
7. **Confounders:** dependence between trades.
8. **Failure conditions:** a model misfit in tails.
9. **Look-ahead risks:** none (risk tool).
10. **Overfitting risks:** low.
11. **Validation:** backtest coverage of predicted drawdown quantiles.
12. **NEXA data:** ✓.
13. **Evidence level:** hypothesis (tool, not edge).

---

## 3. Execution realism (mostly needs live/demo logging, only when separately approved)

### H-NEWS-SLIP: time-varying asymmetric slippage around news and sessions
1. **Sources:** S10 Ch. 5 (flicker law; news p− 0.229 vs 0.057, size ×6); S01 (NFP fill 45 pips away); S11; S31.
2. **Principle:** slippage is regime-dependent and asymmetric.
3. **Math basis:** ν = p₀δ₀ + p₊η₊e^{−η₊z} + p₋η₋e^{η₋z}, estimated per session and news window.
4. **Mechanism:** liquidity withdrawal and flickers.
5. **Required data:** requested vs filled prices with timestamps; MT5 calendar (corrected for the export-time offset).
6. **Expected effect:** larger p₋ and mean slippage around releases and opens.
7. **Confounders:** broker execution model changes; order size.
8. **Failure conditions:** too few news-window fills.
9. **Look-ahead risks:** use scheduled release times, not detected moves.
10. **Overfitting risks:** few parameters.
11. **Validation:** fit on one period, check calibration on the next.
12. **NEXA data:** ◐ (calendar ✓; fills ✗ until logged).
13. **Evidence level:** strongly supported mechanism (CLOB) → hypothesis for OTC CFD.

### H-STOP-SLIP: stop-loss fills deteriorate non-linearly with short-horizon volatility
1. **Sources:** S30 (liquidity withdrawal; flash crash); S32 Ch. 28 (stop cascades); S01 (gaps, no gap insurance); S10.
2. **Principle:** stops fill through the level when liquidity withdraws.
3. **Math basis:** slippage_stop = side × (fill − stop) regressed on pre-fill RV (1–5 min), spread and session; quantile regression for tails.
4. **Mechanism:** gap/jump risk and quote withdrawal.
5. **Required data:** live/demo stop fills (tester has no real slippage).
6. **Expected effect:** convex relation, with heavy upper tails in news and opens.
7. **Confounders:** stop placement at round numbers (H-ROUND-NUM).
8. **Failure conditions:** small sample.
9. **Look-ahead risks:** RV computed before the fill.
10. **Overfitting risks:** low.
11. **Validation:** prospective logging; then stress scenarios in backtests (k × spread, k × ATR_1m).
12. **NEXA data:** ◐.
13. **Evidence level:** supported mechanism → hypothesis.

### H-LASTLOOK-REJECT: requotes/rejections cluster when price has just moved in NEXA's favour
1. **Sources:** S11 (rejection asymmetry; Prop 9); S31 (Cürex: rejections leak information); S30.
2. **Principle:** last-look options are exercised against the trader.
3. **Math basis:** P(reject | Δp_favourable) vs P(reject | Δp_adverse); logit on the pre-request micro-move.
4. **Mechanism:** the broker/LP rejects losing trades for itself.
5. **Required data:** MT5 retcodes (requote/off quotes) with tick context.
6. **Expected effect:** rejection probability is higher after favourable micro-moves.
7. **Confounders:** volatility (rejections rise with volatility both ways).
8. **Failure conditions:** rejections are too rare.
9. **Look-ahead risks:** micro-move measured strictly before the request.
10. **Overfitting risks:** low.
11. **Validation:** prospective logs.
12. **NEXA data:** ◐.
13. **Evidence level:** established theory → hypothesis.

### H-DEVIATION-OPT: MT5 `deviation` should equal the marginal cost of a miss
1. **Sources:** S10 Ch. 3–4 (δ* = α; widen with volatility and shortfall).
2. **Principle:** accept slippage up to what missing the trade costs.
3. **Math basis:** δ* = 2γE[D_T] + γ + α (γ = 0 ⇒ δ* = α); LQ discretion with volatility term.
4. **Mechanism:** misses are adversely selected.
5. **Required data:** fill/miss logs with deviation settings (none yet).
6. **Expected effect:** the optimal deviation is positive and rises with volatility, bounded by stop/ATR economics.
7. **Confounders:** OTC vs CLOB execution differences.
8. **Failure conditions:** no misses observed (then deviation is irrelevant).
9. **Look-ahead risks:** none.
10. **Overfitting risks:** low.
11. **Validation:** only after logs exist; research only.
12. **NEXA data:** ✗.
13. **Evidence level:** established (model) / strongly supported (LMAX) → hypothesis for OTC.

---

## 4. Regime and session descriptors (conditioning variables, not engines)

### H-HURST-GATE: MA-reversion only where H < ½, trend only where H > ½
1. **Sources:** S15 (MA artefact; scaling); S38; S04 (do not confuse volatility-H with price-H).
2. **Principle:** an MA-relative signal needs genuine anti-persistence at the trading horizon.
3. **Math basis:** H(2) by DMA: σ²(τ) ∝ τ^{2H}; H(1) by mean-absolute-return scaling; rolling windows.
4. **Mechanism:** persistence vs anti-persistence at the horizon.
5. **Required data:** M5–D1 closed bars; NY+7 session boundaries.
6. **Expected effect:** engine outcome differences across H terciles, in the predicted directions.
7. **Confounders:** H estimates noisy and biased; spread bounce at short horizons.
8. **Failure conditions:** no monotone relationship.
9. **Look-ahead risks:** rolling H from past data only.
10. **Overfitting risks:** horizon × symbol multiplicity (count as tests).
11. **Validation:** IS descriptive split of **existing frozen engines' trades** (no retuning), then prospective.
12. **NEXA data:** ✓.
13. **Evidence level:** hypothesis.

### H-THICKNESS-ER: efficiency ratio and bar overlap as regime variables
1. **Sources:** S01 (DM/V ≡ Kaufman ER; thickness, verbal definition); S22 (TSMOM).
2. **Principle:** path efficiency distinguishes trend from chop.
3. **Math basis:** ER = |C_t − C_{t−N}|/Σ|ΔC|; overlap = |[L_{t−1}, H_{t−1}] ∩ [L_t, H_t]| / |union|.
4. **Mechanism:** trending paths are efficient and non-overlapping.
5. **Required data:** closed bars.
6. **Expected effect:** trend-engine outcomes are better in high-ER terciles; reversion engines in low-ER.
7. **Confounders:** overlap with H-HURST-GATE and H-TSMOM-TANH (same family).
8. **Failure conditions:** no difference.
9. **Look-ahead risks:** causal windows only.
10. **Overfitting risks:** N choices.
11. **Validation:** as H-HURST-GATE.
12. **NEXA data:** ✓.
13. **Evidence level:** hypothesis (practitioner origin).

### H-TSMOM-TANH: continuous vol-scaled momentum descriptor
1. **Sources:** S22 §10.4 (tanh fix for sign instability); S02 (φ(y) non-monotone).
2. **Principle:** continuous trend strength is more stable than a sign.
3. **Math basis:** η = tanh(R_T/κ)/σ; φ(y) = y e^{−y²/4}/0.89.
4. **Mechanism:** time-series momentum.
5. **Required data:** bars.
6. **Expected effect:** covariance with trend-engine outcomes; possibly "momentum in disguise" (S22 §3.21).
7. **Confounders:** family overlap with ER/H.
8. **Failure conditions:** no relation.
9. **Look-ahead risks:** causal returns only.
10. **Overfitting risks:** T and κ.
11. **Validation:** conditioning study only.
12. **NEXA data:** ✓.
13. **Evidence level:** hypothesis.

### H-SESSION-SPLIT: signals carry different premia by session
1. **Sources:** S14 Ch. 5 (overnight vs intraday opposite premia); S23 (diurnal); S01 App. D.
2. **Principle:** decompose P&L by Asia / London / NY / rollover.
3. **Math basis:** P&L_total = Σ_s P&L_s; Fama–MacBeth-style per-session means with HAC SE.
4. **Mechanism:** different participants and liquidity by session.
5. **Required data:** trade timestamps; server = NY+7 → UTC with DST.
6. **Expected effect:** heterogeneous, possibly opposite-sign session contributions.
7. **Confounders:** DST misalignment (D-TZ open item); rollover spread.
8. **Failure conditions:** homogeneous contributions.
9. **Look-ahead risks:** session assignment by entry time.
10. **Overfitting risks:** post-hoc session filters. **Description only**, no filter adoption without prospective test.
11. **Validation:** IS description → prospective.
12. **NEXA data:** ✓.
13. **Evidence level:** strongly supported (equities) → hypothesis.

### H-FIX-FLOW: London 4 pm WMR / LBMA fix and month-end windows behave differently
1. **Sources:** S31 (fix algos; predictable month/quarter-end hedge rolls; VWAP volume curve); S01 (Tokyo fix); S32 Ch. 11.
2. **Principle:** scheduled, predictable flows create distinct price/volatility/reversal patterns.
3. **Math basis:** event-window averages of returns, RV and spread around fix times; placebo windows.
4. **Mechanism:** benchmark execution concentrated in the fix window.
5. **Required data:** M1 bars; fix times in UTC (DST shifts).
6. **Expected effect:** elevated volatility/spread around fixes; possible post-fix reversal.
7. **Confounders:** London close overlap; data releases.
8. **Failure conditions:** no difference from placebo windows.
9. **Look-ahead risks:** fix times known ex ante (fine); DST handling.
10. **Overfitting risks:** window width choices.
11. **Validation:** pre-registered windows; placebo comparison.
12. **NEXA data:** ✓.
13. **Evidence level:** unverified claim (practitioner) → hypothesis.

### H-GOTOBI / H-OPEN-CONT: Tokyo fix/gotobi USD/JPY drift; session-open continuation
1. **Sources:** S01 (Shanghai BC; Ch. 25).
2. **Principle:** importer settlement demand into the 10:00 JST fix; open-hour moves persist.
3. **Math basis:** day-of-month (5/10/15/20/25/30) × pre-fix window return; open-hour return autocorrelation.
4. **Mechanism:** predictable corporate flow.
5. **Required data:** USDJPY M1; JST mapping.
6. **Expected effect:** positive USD/JPY drift pre-fix on gotobi days; open-hour continuation.
7. **Confounders:** holidays; month-end.
8. **Failure conditions:** null.
9. **Look-ahead risks:** calendar-only (fine).
10. **Overfitting risks:** many window variants.
11. **Validation:** pre-registered windows; prospective.
12. **NEXA data:** ✓ (if USDJPY is in NEXA's symbol set).
13. **Evidence level:** practitioner claim (academic literature exists but is not in the corpus).

### H-NEWS-PTD: post-release drift reverses or continues the shock
1. **Sources:** S01 (PTD claim); S10 (news flickers).
2. **Principle:** measure the post-release path.
3. **Math basis:** cumulative return from t₀ + k to t₀ + K conditional on the shock sign.
4. **Mechanism:** overreaction and liquidity return.
5. **Required data:** MT5 calendar (correct the export-time offset), M1 bars.
6. **Expected effect:** UNKNOWN sign; primarily a **no-trade-window** risk question.
7. **Confounders:** multiple releases; surprise measurement.
8. **Failure conditions:** null.
9. **Look-ahead risks:** use scheduled release times.
10. **Overfitting risks:** k/K choices.
11. **Validation:** pre-registered windows.
12. **NEXA data:** ◐ (consensus/surprise values may be missing).
13. **Evidence level:** unverified claim → hypothesis.

---

## 5. Cross-asset and relative value

### H-LEADLAG-FX (includes S01's H-CROSS-LEAD)
1. **Sources:** S14 Ch. 4 (Lévy area ≡ antisymmetric lag-1 cross-covariance); S01 (EUR/GBP, GBP/CHF lead; JPY crosses lead USD/JPY; gold mirrors USD); S25.
2. **Principle:** short-horizon cross-asset information diffusion.
3. **Math basis:** A_ij = ½Σ(X^j_a X^i_{a−1} − X^i_a X^j_{a−1}); lagged cross-correlations at lag ≥ 1 bar.
4. **Mechanism:** slow diffusion across instruments.
5. **Required data:** synchronous closed bars for NEXA symbols (no broad downloads).
6. **Expected effect:** weak, decaying lead-lag at the shortest bar horizon; likely below spread.
7. **Confounders:** asynchronous quote timing; USD-leg mechanics.
8. **Failure conditions:** below cost; unstable identity.
9. **Look-ahead risks:** next-bar-open execution (L2).
10. **Overfitting risks:** pair × horizon multiplicity.
11. **Validation:** rolling identity stability; cost curve.
12. **NEXA data:** ◐ (earlier study was DATA-LIMITED).
13. **Evidence level:** research finding (equities) / anecdote (FX).

### H-PAIRS-OU: XAU–XAG (or FX crosses) cointegration with causal OU signals
1. **Sources:** S25 (OU/VAR, Johansen); S22 §3.8; S20; S36 (lessons: fixed-at-entry P&L, causal innovations, multiple testing); S15 (OU bias).
2. **Principle:** relative value rather than direction.
3. **Math basis:** Johansen rank test; ΔR = a + ΠR_{t−1} + ε; Kalman *filter* innovations; half-life bias corrections.
4. **Mechanism:** common drivers.
5. **Required data:** synchronous XAU/XAG bars (if both are in NEXA's symbol set).
6. **Expected effect:** UNKNOWN; spreads may be non-stationary across regimes.
7. **Confounders:** regime shifts; the α̂ bias (S15).
8. **Failure conditions:** cointegration unstable.
9. **Look-ahead risks:** S36 errors (re-fitted γ in P&L; smoothed residuals).
10. **Overfitting risks:** pair selection.
11. **Validation:** OOS cointegration stability before any signal study.
12. **NEXA data:** ◐.
13. **Evidence level:** hypothesis.

### H-CARRY-SWAP
1. **Sources:** S22 §8.2 (UIRP failure, carry crash risk); S01 (carry unwinds).
2. **Principle:** the forward-premium puzzle.
3. **Math basis:** CIRP F = S(1 + r_d)/(1 + r_f); HML carry by forward discount.
4. **Mechanism:** risk premium with crash risk.
5. **Required data:** historical swap/rate series (**not held**).
6. **Expected effect:** N/A until data exist; only current swap cost can be estimated.
7. **Confounders:** broker swap mark-ups.
8. **Failure conditions:** data unavailable.
9. **Look-ahead risks:** using today's swap for history.
10. **Overfitting risks:** —.
11. **Validation:** deferred.
12. **NEXA data:** ✗.
13. **Evidence level:** established in literature (second-hand) / data-limited.

---

## 6. Payoff and microstructure items

### H-PARTIAL-EXIT: scaled exits reshape the payoff without creating edge
1. **Sources:** S19 (thirds); S01 (partial profit at +20–25 pips); MATH M1b.
2. **Principle:** exits change the distribution, not the mean, absent drift.
3. **Math basis:** a mixture of two-barrier exits; driftless null expectancy = 0 before costs.
4. **Mechanism:** payoff shaping.
5. **Required data:** trade paths.
6. **Expected effect:** lower variance, unchanged or lower mean (costs).
7. **Confounders:** extra commissions per partial.
8. **Failure conditions:** —.
9. **Look-ahead risks:** exit rules fixed at entry.
10. **Overfitting risks:** split choices.
11. **Validation:** compare with the H-HIT-PROB null.
12. **NEXA data:** ✓.
13. **Evidence level:** unverified claim → hypothesis.

### H-ROUND-NUM: price clustering at round levels affects fills and short-horizon reversal
1. **Sources:** S32 Ch. 5 (price clustering; limits placed just inside round numbers); S01 (stops at round numbers get run; Osler via S22); S32 Ch. 28 (stop cascades).
2. **Principle:** liquidity and stops cluster at round prices.
3. **Math basis:** frequency of swing extremes and quotes at x00/x50 (XAU) and 00/50 pips (FX) vs uniform; conditional reversal/continuation after touches.
4. **Mechanism:** human order placement; stop clustering.
5. **Required data:** M1/tick data.
6. **Expected effect:** excess clustering; different short-horizon behaviour at touches.
7. **Confounders:** price-level drift; tick size.
8. **Failure conditions:** uniform distribution.
9. **Look-ahead risks:** "touch" defined causally.
10. **Overfitting risks:** level definitions.
11. **Validation:** descriptive with a placebo level grid.
12. **NEXA data:** ✓.
13. **Evidence level:** textbook statement (equities) → hypothesis for XAU/FX.

---

## 7. Low-prior pattern hypotheses (only after the method gates above)

### H-SQUEEZE-VARIANTS
1. **Sources:** S09 (BandWidth 6-month low; Method IV), S19 (fire + momentum histogram direction).
2. **Principle:** volatility compression precedes expansion; direction needs confirmation.
3. **Math basis:** BandWidth percentile; BB inside KC; momentum histogram sign.
4. **Mechanism:** volatility clustering.
5. **Required data:** bars.
6. **Expected effect:** expansion is predictable (volatility); direction weakly (if at all).
7. **Confounders:** same family as 8E E1 (UNPROVEN).
8. **Failure conditions:** no gain over base rates net of costs.
9. **Look-ahead risks:** band look-back causal.
10. **Overfitting risks:** many variants (count them).
11. **Validation:** new frozen protocol; deflated metrics.
12. **NEXA data:** ✓.
13. **Evidence level:** unverified claim.

### H-TD-CANON
1. **Sources:** S17 (canonical rules; 6 discrepancies vs 8E).
2. **Principle:** canonical TD as a countertrend **entry** (not a veto).
3. **Math basis:** setup/countdown/qualifier/cancellation/recycle rules.
4. **Mechanism:** exhaustion.
5. **Required data:** D1/H4 bars.
6. **Expected effect:** reversal/sideways base rate after perfected 9s / qualified 13s above random bars.
7. **Confounders:** trend regime.
8. **Failure conditions:** base rate ≈ random.
9. **Look-ahead risks:** perfection and qualifier evaluated only when known.
10. **Overfitting risks:** time-frame choice.
11. **Validation:** new frozen protocol; **frozen 8E code untouched**.
12. **NEXA data:** ✓.
13. **Evidence level:** unverified claim.

### H-PATTERN-LOWPRIOR (grouped)
1. **Sources:** S07 (previous-day high/low, ADR exhaustion, 3-day cycle); S08 (outside bar, fractal breakout, Asian range + daily filter); S20 (ORB, gap fade); S16 (z + RSI reversion with long-MA filter).
2. **Principle:** practitioner archetypes.
3. **Math basis:** rule definitions in the notes.
4. **Mechanism:** asserted only.
5. **Required data:** bars.
6. **Expected effect:** most fail net of costs (prior).
7. **Confounders:** overlap with existing V2 families (session breakout, Asian MR).
8. **Failure conditions:** expected.
9. **Look-ahead risks:** session-range timing; swing confirmation.
10. **Overfitting risks:** high (many variants).
11. **Validation:** only within a deflated multi-test protocol.
12. **NEXA data:** ✓.
13. **Evidence level:** unverified claim.

### H-RETURN-50 (GSCS)
1. **Sources:** S01 Ch. 27.
2. **Principle:** 4th swing ends near 50 % of the 1-2-3 matrix.
3. **Math basis:** causal zig-zag; compare with a random-walk swing null.
4. **Mechanism:** asserted.
5. **Required data:** bars.
6. **Expected effect:** likely null.
7. **Confounders:** zig-zag threshold choice.
8. **Failure conditions:** null.
9. **Look-ahead risks:** **swing confirmation lag** (classic trap).
10. **Overfitting risks:** thresholds.
11. **Validation:** null comparison.
12. **NEXA data:** ✓.
13. **Evidence level:** unverified, weakly falsifiable (3C rule). Lowest priority.

### H-ENSEMBLE-META
1. **Sources:** S12 (Aggregating Algorithm, EG); S24 (EXP3/Hedge converge; naive Q-learning can lock in).
2. **Principle:** regret-bounded allocation across engines.
3. **Math basis:** w_i ∝ w_i e^{−ηℓ_i}.
4. **Mechanism:** adapts to the better expert.
5. **Required data:** engine return streams.
6. **Expected effect:** only meaningful if some engine shows edge (none does now).
7. **Confounders:** costs of switching.
8. **Failure conditions:** no positive engine.
9. **Look-ahead risks:** losses ℓ_t known only after t.
10. **Overfitting risks:** η.
11. **Validation:** deferred.
12. **NEXA data:** ✓.
13. **Evidence level:** hypothesis.

---

## 8. Notes

- **Removed/merged from earlier source notes:**
  - H-EXEC-LL (S11) → merged into H-LASTLOOK-REJECT;
  - H-CROSS-LEAD (S01) → merged into H-LEADLAG-FX;
  - H-OPEN-CONT and H-GOTOBI → one entry;
  - H-VOL-2 is the volatility-forecast version of H-VOLTARGET-CAP; they are kept separate because their sources and inputs differ.
- **Family counting:** for multiple-testing correction, count EVIDENCE_MAP §6 families (e.g. ER/overlap/H/TSMOM-tanh are one "trendiness" family).
- **DATA-LIMITED items are kept** so they are not forgotten. They are not runnable until data exist.
