# NEXA 8-engine results: PRELIMINARY, DEV only (integrity gate, 2026-10-01)

> **Status of everything in this file: PRELIMINARY.**
> - **Data:** DEV 2018-01-01 → 2023-01-01, which is exploration data. No VAL query was run and no OOS data exists (prospective 2026-10-12 → 2027-04-12).
> - **No selection.** No engine, stack, threshold or configuration has been selected or promoted.
> - **Not run:** `run_8e.py val/select` and `analyze_8e.py info/stack/selected`, all of which read VAL.
> - **No trading:** no trading was enabled and nothing was deployed. V2 was not opened.
> - **Wording:** "improves" means relative to the Donchian base. It never means profitable.

## 0. Integrity gate
| Check | Result | Class |
|---|---|---|
| **V2** (`registry_v2`, anchor `6090be68…`) | **42/42** pinned files byte-identical; anchor recomputes exactly.<br>`verify` passes at checkpoint seq 6 `bbd9a28e…`.<br>Ledger: CAMPAIGN_FROZEN + 6× BUILDER_CERTIFIED and **no EVALUATION_OPENED**. Witness 7 = ledger 7.<br>6/6 protocol hashes OK; counts 1632 / 108 / 1740 / 17; **0 results, 0 OOS rows**. Re-verified at the end of this phase. | **PROVEN intact** |
| **8E** (`registry_8e`, anchor `6468fdea…`) | `verify` passes at seq 3 `1e84a047…`.<br>Ledger: FROZEN → 2× BUILDER_CERTIFIED → EVALUATION_OPENED.<br>**0 results** (0 VAL, 0 OOS rows).<br>Digests: code `efd149e4…`, data `0704932d…`, design `50fed18c…`. | **PROVEN** |
| **8E lineage** | `registry_8e_superseded_834473f0` was **never opened**. It was superseded only to pin `run_8e.py` / `analyze_8e.py` before opening (byte-identical tree `c1d7152f…`; reason in `.SUPERSEDED.txt`). | **PROVEN** |
| **Analyses added after the freeze** | Everything in §3–§8 (alternative orderings, leave-one-out, MI/CMI, incremental AUC, OFI deciles, the 99.9 percentile, 20-day scenarios, sensitivities) is **outside the frozen 2,160-trial universe**. It is exploratory and must **not** feed selection without a new freeze, which would also raise the DSR trial count. | Disclosed |
| **History base** | 25,113,780 KB → 25,180,036 KB. Growth came from the spec probe (it includes a NAS100 window sync) and the tick probes. No broad download. | Disclosed |

## 1. Harness findings that affect the evidence (new this phase)
1. **Entry-bar exit price defect in `nexa_execution.simulate_order` (DEFECT, pessimistic).**
   - **Mechanism:** a STOP order fills intrabar, and the SL is hit on the same bar. The exit is priced at `min(sl, bar_open)`. The bar open **precedes** the fill, so a bar that opened beyond the stop records an exit at a price that was no longer reachable.
   - **Measured effect, `stop_at_channel` mode** (`runs_8e/gate_dev/entry_bar_exit_defect.txt`):
     - 24 % of baseline trades are affected, with a mean excess loss of 0.60R;
     - baseline expectancy −0.645R as-is vs −0.492R corrected;
     - L5_ofi +0.112 vs +0.120.
   - **`close_next_open` mode:** unaffected (≤ 0.005R).
   - **Impact on conclusions:** every baseline config stays negative after correction (maximum −0.057R), and 20-day target days stay at 0 (`gate_dev/cv_corrected.txt`).
   - **Scope:** `nexa_execution.py` is pinned in **both** RESEARCH_8E_V1 and V2.
     - **V2:** `nexa_v2_trials.py` submits only MARKET and LIMIT orders. A MARKET fill happens at the open. A LIMIT fill comes either at an open between the level and the stop (then the exit is at the stop) or as a cancelled-invalid order (open beyond the stop). So **V2 results cannot be affected**.
     - **8E:** the `stop_at_channel` mode is affected.
     - **It was NOT modified.** A fix needs a human decision. Changing the file breaks verification of both campaigns, forcing a supersede and re-freeze of both (legal only because both have 0 results). For V2 that would be a re-freeze with no change in V2 behaviour.
     - **Alternative:** add a STOP-specific fix to the 8E harness only, which needs a re-freeze of 8E alone.
2. **Gap- and geometry-driven loss tails.**
   - Market orders anchor SL/TP at the signal close, but fill at the next open. After a gap, the realized risk can collapse: the worst case is GBPUSD M15, a 0.08-pip risk at the Sunday open, giving **−389R** net.
   - **Data gaps:** a few M1 gaps exist (GBPUSD 2018-07-17, 22 h; XAU 36 non-holiday gaps over 60 min in DEV; `runs_8e/m1_gap_audit.txt`). They produce time exits at gap prices.
   - **Sensitivity** (`gate_dev/tail_artifact_sensitivity.txt`): dropping delayed entries, dropping cost > 1R trades, and capping losses at −1.5R moves means by ≤ +0.06R. **No sign changes** in the share of positive configs.
3. **The recorded M1 spread is the minute minimum**, so FX historical costs are understated (`spread_truth_audit.txt`). See the cost audit.

## 2. Baseline (E3 Donchian) and the empirical R envelope
- **Net expectancy:** negative in **72/72** bases (−0.059 … −0.769R).
- **Large R outcomes:** MFE ≥ 24.5R in 0 % of trades. The largest uncapped single-day aggregate was 29.14R (2 of 72 configs had any day ≥ 24.5R).
- **All 2,160 frozen trials on DEV:** 9.5 % have positive expectancy; 36 have ≥ 200 trades and positive expectancy.
  - A random-subset null and multiplicity (DSR 4,008 trials) are not yet applied. These are **not** findings of edge.

## 3. Each engine independently (filter on the Donchian base)
Means over 24 bases per symbol; the full table is in `gate_dev/summary.txt` §1.
- **p < .05** = the share of bases where the kept signals beat random subsets of the same size; about 0.05 is expected under the null.
- **ΔAUC** = drop-one incremental test AUC (fit 2018–20, test 2021–22).

| Engine | Kept | Exp (R) XAU / EUR / GBP | Improves base | p < .05 | ΔAUC | Class |
|---|---|---|---|---|---|---|
| E1 Squeeze | 23 % | −0.31 / −0.33 / −0.33 | 90 % | 51 % | −0.001 | UNPROVEN |
| E2 VEI ≥ 1.2 | 16 % | −0.30 / −0.29 / −0.25 | 93 % | 53 % | +0.004 | PROMISING (information) |
| E4 EMA200 side | 82 % | −0.36 / −0.38 / −0.34 | 90 % | 65 % | +0.001 | UNPROVEN |
| E5 EMA9 + MACD(5,13,4) | 70 % | −0.29 / −0.31 / −0.26 | 92 % | 79 % | **+0.006** | PROMISING (information) |
| E6 OFI proxy ≥ 3 | 6 % | −0.29 / −0.53 / −0.51 | 43 % | 25 % | +0.003 | CONTRADICTED (300 % hypothesis) |
| E7 Large quote/tick event ≥ p97.5 | 8 % | −0.27 / −0.33 / −0.20 | 85 % | 43 % | +0.002 | PROMISING (information) |
| E8 TD 8/9/13 veto | 81 % | −0.42 / −0.44 / −0.40 | 35 % | **0 %** | −0.0005 | CONTRADICTED |

**No single engine is net-positive on average for any symbol.**
- Several (VEI, MACD, EMA200, Squeeze, quote events) select better-than-random signals far more often than chance. They carry information but do not overcome the negative base.
- **Out-of-sample discrimination is weak:** the full logistic model has test AUC mean 0.556 (0.47–0.62).

## 4. Cumulative stacks and alternative orderings (non-overlapping trades; mean over 72 bases)
| Level | Frozen order (sq, vei, ema200, mom, ofi, qb, td) | n (median) | Exp (R) |
|---|---|---|---|
| 0 | base | 3,604 | −0.410 |
| 1 | + sq | 946 | −0.323 |
| 2 | + vei | 152 | −0.216 |
| 3 | + ema200 | 137 | −0.138 |
| 4 | + mom | 128 | −0.087 |
| 5 | + ofi | 23 | +0.052 (36 bases with n ≥ 30) |
| 6 | + qb | 6 | +0.046 (0 bases with n ≥ 30) |
| 7 | + td | 6 | +0.041 (**0 bases with n ≥ 30**) |

- **The full 8-engine stack produces about 5–6 trades in 5 years per base.** It is **NOT TESTABLE** at any useful power.
- **Level 5 is still small:** median n = 23, positive in 40 % of bases.
- **Ordering does not change the end point.** L7 is the logical AND of all filters; this was verified as an identity in code.
- **Ordering does change the attribution.** For example, TD's increment is −0.011 when added first but +0.077 after regime filters.
  - Order-independent leave-one-out on the full stack (signal-level marginal): OFI +0.29 and Squeeze +0.25. Both rest on about 5-trade samples, so they are **noise-level**.

## 5. Redundancy (DEV signal level)
**Pairwise flag correlation is low** (|ρ| < 0.1) except **VEI–quote events, ρ = 0.34** (MI 0.061 bits). Both measure activity or volatility expansion.

**Information about win/loss is tiny for every engine:**
- MI(flag; win) is between 0.0002 and 0.003 bits; MACD has the largest.
- Conditional MI given any other engine is about the same as the unconditional MI. The information is small and mostly **not shared**, except VEI given quote events (0.00125 → 0.00107).

**Incremental predictive power:** see the ΔAUC column above. MACD and VEI are the only features with ΔAUC > 0.01 in more than 30 % of bases.

## 6. OFI (redefined) and the 300 % hypothesis
**What OFI needs.** Order Flow Imbalance (Cont–Kukanov–Stoikov) needs signed depth or trade flow.

**What Pepperstone supplies.** Only BID/ASK change bits. In 10.8 M XAU ticks there are 0 LAST, VOLUME, BUY or SELL bits; BOOKDEPTH is 10 for XAU and 0 for EUR, and a live DOM is unverified.

**Proxies that are computable:**

| Proxy | Formula | Data | Limit |
|---|---|---|---|
| (a) Tick quote imbalance | count(bid↑ or ask↑) / count(bid↓ or ask↓) per window | 21 days of ticks | Quote revisions, not orders |
| (b) Bar tick-rule proxy (**implemented**) | (up_tv + 1) / (dn_tv + 1) from 1-minute close-direction quote counts | 2017–2026 M1 | ρ = 0.25 with (a) |
| (c) Signed price-change pressure | Σ sign(Δmid)·\|Δmid\| | Ticks | Same limitation as (a) |

**Can any of these be called OFI? No.** They are quote-activity imbalance proxies.

**The 300 % hypothesis.**
- Under (a), the condition **never occurs** (median 1.004, p95 1.122).
- Under (b) it occurs in 6.1 % of DEV signals, with a mean of −0.45R.
- **Continuous test:** expectancy rises monotonically across deciles (ρ = +0.088; positive in 83 % of bases). Even the top decile (ratio > 2.3) is negative: −0.19 (XAU), −0.32 (EUR), −0.19 (GBP).
- **Recorded: HYPOTHESIS FAILED (CONTRADICTED)** as an edge threshold. As true OFI it is **NOT TESTABLE**.

## 7. "Big Trades" → LARGE QUOTE/TICK EVENT ENGINE
**Classification: D/E.** There are no trade sizes, so the detector is a quote-intensity / tick-burst proxy. It is renamed accordingly.

Detector: trailing 500-bar percentile rank of the bar quote count.

| Percentile | Signals (median per base) | Exp (R) XAU / EUR / GBP | Improves base | p < .05 |
|---|---|---|---|---|
| 95 | 980 / 1,092 / 1,029 | −0.28 / −0.31 / −0.21 | 75–100 % | 38–75 % |
| 97.5 | 582 / 630 / 593 | −0.27 / −0.33 / −0.20 | 75–100 % | 25–67 % |
| 99 | 343 / 346 / 329 | −0.24 / −0.35 / −0.19 | 67–96 % | 25–54 % |
| 99.5 | 198 / 189 / 173 | −0.32 / −0.36 / −0.25 | 54–75 % | 13–21 % |
| 99.9 (exploratory; not a frozen threshold) | 76 / 68 / 54 | −0.39 / −0.32 / −0.34 | 46–67 % | 0–17 % |

The information is concentrated at p95–p99 and **fades at the extreme tail**. Every expectancy is negative.

## 8. 20-day capital-velocity scenarios (from $200; real spec; lock +24.5 %, halt −2 %, cap 10, round-down sizing)
| Scenario | Definition | Result |
|---|---|---|
| **A ideal** | Every day exactly +24.5 % | $200 → **$16,010.95** at day 20 (arithmetic only) |
| **B empirical** | All 1,774 DEV streams with ≥ 30 trades (no selection) | **0 target days** in any stream, at $200 and at $10,000. At $200, 2.34 M signals were skipped below min lot vs 0.52 M executed. 6 % of streams end above start. Median max drawdown 33 % ($200) and 80 % ($10k). |
| **C stress** | Conservative true spread, ×2, ×3, ×2 + 10 % missed days + 5 % execution failures (−1R − cost) | **0 target days** in every variant |
| **B/C with the corrected entry-bar exit** | Defect §1.1 removed | **0 target days**. The largest single day was +12.7 % ($200) / +20.2 % ($10k). |

**P(20/20 target days):** 0 in every bootstrap. The zero-edge analytic bound is ≤ 0.1084²⁰.

## 9. What remains (all DEV-independent, needing approval)
1. **VAL (2023-01 → 2026-09; seen data, one query per frozen trial) and the pinned selection rule.** This needs explicit human approval, and must come after a decision on defect §1.1. If `nexa_execution` is fixed, 8E must be superseded and re-frozen first, while it still has 0 results.
2. **NAS100 history acquisition** (data decision), then E8_NAS100.
3. **True tick-level microstructure research.** It needs a feed with trade sizes or depth; this is NOT available at Pepperstone.
4. **Prospective OOS** (2026-10-12 → 2027-04-12): only after selection is sealed.
