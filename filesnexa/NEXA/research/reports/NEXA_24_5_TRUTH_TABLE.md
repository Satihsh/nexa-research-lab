# NEXA +24.5 %/day: truth table (integrity gate, 2026-10-01)

**Scope.**
- Research only. No trading was enabled, nothing was deployed, V2 was not opened, and no VAL or OOS row of RESEARCH_8E_V1 was read.
- Empirical evidence = DEV 2018-01-01 → 2023-01-01 only: exploration, in-sample-like, **PRELIMINARY**.
- No engine, stack or configuration was selected.

**Status scale.**

| Status | Meaning |
|---|---|
| PROVEN | Exact mathematics, or a direct measurement of the broker or data. |
| SUPPORTED | Consistent DEV evidence; not yet confirmed out of sample. |
| PROMISING | Weak but repeated DEV signal. Not a profitable edge. |
| UNPROVEN | No evidence either way that survives costs. |
| CONTRADICTED | The evidence goes against the claim. |
| DATA-LIMITED | The data needed does not exist locally. |
| NOT TESTABLE | The quantity is not observable at this broker. |

**Notation.**
- R = the 1 % risk unit, including costs.
- Engine statistics are means over 24 bases per symbol (72 in total). The bases are 2 timeframes × 2 channel lengths × 2 entry modes × 3 targets on the same underlying data. They are **not** independent samples.
- p-values compare the engine's kept signals against random subsets of the same size (`random_subset_p`). Under the null, about 5 % of bases would show p < 0.05.

| Requirement | Mathematical Requirement | Empirical Evidence | Status |
|---|---|---|---|
| **+24.5 % NET per day** | **Required aggregate per day:** ≥ 24.5R (start-equity basis), or ≥ 22.16R with compounding over 10 trades.<br>**Per-trade R:** with ≤ 10 trades at 1 % risk, every trade must be at least 2.2156R; 10/10 winners at 2R give only +21.90 %.<br>**Zero-edge bound:** for any strategy with non-positive expected value per trade, P(target hit on a day) ≤ (1−0.9702)/(1.245−0.9702) = **10.84 %** (optional stopping; no independence needed). This bounds a probability, not a return.<br>**20 consecutive days at zero edge:** ≤ 0.1084²⁰ ≈ 5·10⁻²⁰. | **DEV, 1,774 trade streams** (every frozen variant with ≥ 30 trades, no selection): **0 target-hit days** in every scenario (B empirical, C conservative / ×2 / ×3 / ×2 + 10 % missed days + 5 % execution failures), at both $200 and a $10,000 reference. Longest run of target days: 0.<br>**Uncapped baseline:** the largest aggregate single day was 29.14R; 2 of 72 configs had any day ≥ 24.5R. | **CONTRADICTED** for the tested engine set (DEV).<br>Mathematically **not impossible**, but it requires a large positive edge that has not been shown. |
| **1 % max trade risk** | Lots = floor(1 % · equity / loss-per-lot, step), where loss-per-lot = (stop + spread + 2·slippage)·value + commission. A size below the minimum lot ⇒ SKIP; never rounded up. | Implemented in `nexa_8e_costs.size_trade` and `nexa_8e_capital.simulate`; tests pass (546). **Gaps can exceed 1 %:** stop-through gap fills are modelled in `nexa_execution`, and a gap loss is larger than the planned 1R. | **PROVEN** as an enforceable sizing rule (gap risk excepted) |
| **2 % max daily loss** | The halt **triggers** at equity ≤ 0.98·E₀. With 1 % trades: 2 losses = −1.99 % (no halt); a 3rd loss gives **−2.97 %**. A true 2 % cap needs a pre-trade check that the remaining daily budget is at least the trade risk. | The live `NEXA_Risk.mqh:41-49` has the same trigger semantics: halt at loss ≥ 2 %. In the DEV streams the halt was hit on 1.5 % ($200) to 8.7 % ($10k) of traded days. | **PROVEN** as a halt trigger.<br>**CONTRADICTED** as a hard 2 % cap (realized loss up to ≈ 3 % + gap). Human decision needed. |
| **Minimum trades** | **Minimum winners:** 1R 23 · 2R 12 · 3R 8 · 4R 6 · 5R 5 · 10R 3 · 20R 2 · 25R 1.<br>**1 trade/day:** needs 24.5R.<br>**10 trades/day:** needs an average of 2.45R (start-equity basis) or 2.216R (compounding) on **every** trade. | **DEV baseline:** MFE ≥ 24.5R in 0 % of trades; net R per trade is capped by the target grid (k ≤ 5).<br>**Win rates:** 20–31 % in the filtered stacks. | **PROVEN** (math); the empirical requirement is **CONTRADICTED** |
| **Minimum broker cost** | Cost per R = (spread + 2·slip)/stop + commission/(risk cash). It falls as the stop rises, but min-lot risk then exceeds 1 % at $200. | **XAUUSD:**<br>• true tick spread: median 12 pts, p99 18 pts; rollover 17–20 pts;<br>• all-in cost: $1.68 stop 18.8 % of R; M5 ATR 6.3 %; M15 ATR 3.5 %.<br>**Commission:** $3.50/lot/side, i.e. $0.08 round trip at 0.01 lot.<br>**FX:** the recorded M1 spread is the minute-**minimum** and understates the true cost. DEV mean expectancy runs from recorded to ×3 conservative: EUR −0.359 → −0.417, GBP −0.296 → −0.409. | **PROVEN** (spec and tick measurements).<br>FX historical cost: **DATA-LIMITED**. |
| **$200 starting capital** | Max stop at 1 % for a min lot, all-in: XAU **$1.684**; NAS100 **18 pts**; EUR 19.1 pips; GBP 18.8 pips. | **XAU:** only 0.3 % of M5 ATR values are ≤ $1.75. Min-lot risk at the M5 / M15 / H1 ATR median = 2.66 % / 4.71 % / 9.60 % of $200.<br>**DEV streams at $200:** 2.34 M signals skipped (below min lot) vs 0.52 M executed. | **CONTRADICTED** for XAUUSD and NAS100 at realistic stops.<br>**SUPPORTED** (technically sizeable) for EURUSD and GBPUSD. |
| **XAUUSD viability** | Needs stop ≤ $1.684 at $200 (broker stops level 0, so this is technically accepted). | **Random-entry first passage** on the last 12 months of M1, $1.68 stop:<br>• P(2R target first) 0.327 vs the driftless 0.333;<br>• expectancy −0.207R after 18.8 % cost.<br>**DEV baseline Donchian:** net negative in all 24 XAU bases (−0.118 … −0.716R). | **CONTRADICTED** at $200 (cost, statistically).<br>Technically **VALID** order size only with micro-stops. |
| **NAS100 viability** | Min lot 0.1 × $1/pt per lot = $0.10 per point; 1 % of $200 ⇒ stop ≤ 18 pts. | **No local NAS100 M1 or tick history:** the tester returned 1 tick, the spread is from one probe quote (1 pt), and there is no ATR distribution.<br>Not in the research universe (E8_NAS100 BLOCKED). | **DATA-LIMITED** |
| **10-pip TP** | Pip = 0.0001 (FX), $0.10 (XAU), 1 pt (NAS100). TP ≥ 2.2156R net is needed with ≤ 10 trades. | **XAU** (10 pips = $1.00): **unreachable at any stop**. The maximum with 10/10 winners is +21.86 % (costs = 30.6 % of TP).<br>**EUR / GBP:** stop ≤ 2.96 / 2.51 pips is needed even with 10/10 winners. Driftless P(10/10) is 3.8·10⁻⁷ / 1.1·10⁻⁷.<br>**NAS100:** stop ≤ 1.33 pts (data-limited spread). | **CONTRADICTED** (XAU).<br>**UNPROVEN** (FX; it needs an extreme win rate).<br>**DATA-LIMITED** (NAS100). |
| **300 % OFI** | OFI needs a signed trade or depth flow. Pepperstone supplies only BID/ASK change bits (0 LAST/VOLUME/BUY/SELL bits in 10.8 M XAU ticks). | **Tick-level quote imbalance:** median 1.004, p95 1.122; **never ≥ 3**.<br>**Bar tick-rule proxy:** ≥ 3 in 6.1 % of DEV signals; ρ(proxy, r_net) mean +0.088.<br>**Top decile (ratio > 2.3):** −0.19 … −0.32R.<br>**A_ofi (≥ 3):** mean −0.446R, improves 43 % of bases, p < 0.05 in 25 %. | **NOT TESTABLE** as true OFI.<br>As a proxy hypothesis: **CONTRADICTED** (recorded as failed). |
| **Big Trade detection** | Needs trade size or volume, and none exists (OTC CFD quote feed). Renamed **LARGE QUOTE/TICK EVENT ENGINE**: quote-count percentile (classification D/E). | **Percentiles 95 / 97.5 / 99 / 99.5 / 99.9** (99.9 exploratory): every expectancy is negative (−0.19 … −0.39R).<br>The filter raises the signal mean in 46–100 % of bases. GBP is strongest: p < 0.05 in 54–75 % of bases at 95–99. | **NOT TESTABLE** (big trades).<br>Quote-event proxy: **PROMISING** as information, **UNPROVEN** as edge. |
| **TD 8/9/13** | Exhaustion veto: setup ≥ 8, or a 9/13 within the last 3 bars. | Removes ≈ 19 % of DEV signals (kept 77–85 %).<br>p < 0.05 in **0 %** of bases; improves 35 %; incremental AUC −0.0005; LOO marginal +0.003. | **CONTRADICTED** (adds no information on DEV) |
| **Squeeze** | BB(20, 2) inside KC(20, 1.5·ATR); fired within 5 bars. | Exp −0.32R; improves 90 %; p < 0.05 in 51 %; incremental AUC −0.001. | **UNPROVEN** (selects better than random; not net-positive; no out-of-sample AUC gain) |
| **VEI** | ATR14/ATR50 ≥ 1.2 | Exp −0.28R; improves 93 %; p < 0.05 in 53 %; incremental AUC +0.0036 (> 0.01 in 32 % of bases). | **PROMISING** (information).<br>**UNPROVEN** (profit). |
| **Donchian** | N-bar breakout, N ∈ {20, 55}, prior bars only | Net negative in **all 72** bases (−0.059 … −0.769R); 0 % positive.<br>This still holds after correcting the entry-bar exit defect (max −0.057R; see `NEXA_8_ENGINE_RESULTS.md` §1). | **CONTRADICTED** (standalone) |
| **EMA200** | Trade side = EMA200 side | Exp −0.36R; improves 90 %; p < 0.05 in 65 %; incremental AUC +0.001. | **UNPROVEN** |
| **MACD (EMA9 + MACD 5,13,4)** | Momentum alignment score ≥ 4 | Exp −0.29R; improves 92 %; p < 0.05 in 79 %; incremental AUC **+0.0063** (> 0.01 in 39 % of bases; the largest of the 7). | **PROMISING** (information).<br>**UNPROVEN** (profit). |

## Precise restatement of the "10.8 %" figure
**What it is.**
- Take any strategy whose every trade has a conditional expected value ≤ 0 (zero or negative edge).
- Risk ≤ 1 % of current equity per trade.
- Stop for the day at +24.5 % or at the 2 % halt, with a bounded number of trades.
- Then the probability of reaching +24.5 % **on a given day** is at most **10.84 %**.

**What it is not.**
- It is **not** a cap on daily return.
- It is **not** an estimate for any NEXA engine.

**Where the earlier wording needs correcting.** `NEXA_24_5_DAILY_FEASIBILITY_AUDIT.md` is a pinned 8E design artifact and is left unedited. Where it reads as a return ceiling, this restatement supersedes it.

## Sources
- `research/runs_8e/`:
  - `gate_dev/*.csv` and `gate_dev/summary.txt`
  - `dev_empirical_R.txt`
  - `capital_200_feasibility.txt`
  - `tp10pip_feasibility.txt`
  - `tick_data_audit.json`
  - `spread_truth_audit.txt`
  - `cost_sensitivity_dev.txt`
  - `xau_spread_profile.txt`
  - `xau_spread_by_hour.txt`
- Spec probe: `data/pepperstone/spec_probe/spec_probe_20261001.csv`.
- Independent math reproduction: exact `Fraction` enumeration, matching the DP to ≤ 2·10⁻¹⁶.
