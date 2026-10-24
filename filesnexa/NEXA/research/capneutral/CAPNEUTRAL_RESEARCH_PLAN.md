# CAP-NEUTRAL RESEARCH — NOT PRODUCTION CONFIGURATION

## NEXA cap-neutral tester campaign: run plan (DRAFT, 2026-10-02)

**Status:** A1, A2 and A3 done (2026-10-03; A3: 48/48 runs verified). A4 (analysis) approved 2026-10-03. Amendment 2 (§11) was recorded before any result was opened.

**Earlier status:** A1 and A2 done (2026-10-03). The research EA copy is installed and the smoke chunk USDJPY A2026Q1 passed every gate. The plan was amended once after the smoke run, before any full-campaign run (§11). The full campaign (A3) and the analysis (A4) still need approval.
**Decision it implements:** B-EXPOSURE-CAP option B (human-approved 2026-10-02): measure NEXA's own signal with the exposure cap neutralised **in the Strategy Tester only**, without editing `NEXA_Risk.mqh`.
**Files:**
- `NEXA_CAPNEUTRAL_RESEARCH.set`: the settings file (one override, nine pinned limits).
- `run_capneutral_batch.sh`: the batch runner. It refuses to start without `CAPN_APPROVED=CAP-NEUTRAL-RESEARCH-APPROVED`.
- this plan.

Every output of this campaign carries the label **CAP-NEUTRAL RESEARCH — NOT PRODUCTION CONFIGURATION**: file names, run folders, a `LABEL.txt` in every run and the report title.

---

## 1. Question

**Primary (strategy edge):** with the exposure cap made inert and every other frozen control unchanged, does NEXA's rule set produce a positive net expectancy per trade? The test window is 2024-01-01 → 2026-09-26, on EURUSD, GBPUSD, USDJPY and XAUUSD.

**Secondary (capital sizing, reported separately):** what daily-return profile do those trades produce under the frozen risk controls, and how does it compare with the user's capital objective (§7B)?

The two answers are kept apart. An edge verdict never depends on the capital objective, and the capital objective is never used to select, reject or tune anything.

## 2. What changes and what does not

| Item | Production | This campaign |
|---|---|---|
| `InpMaxSameCurrencyNet` | 2 (= 0.02 lots per currency) | **10000** (= 100 lots: inert, see below) |
| `InpRiskPercent` | 0.30 | 0.30 (pinned) |
| `InpHardRiskCeiling` | 1.00 | 1.00 (pinned) |
| `InpMaxDailyLossPct` | 2.00 | 2.00 (pinned) |
| `InpMaxDrawdownPct` | 10.00 | 10.00 (pinned) |
| `InpMaxTradesPerDay` | 10 | 10 (pinned) |
| `InpMaxSpreadATRRatio` | 0.15 | 0.15 (pinned) |
| `InpMaxMarginUsagePct` | 50.0 | 50.0 (pinned) |
| `InpMaxCorrelation` / `InpCorrelationBars` | 0.75 / 100 | 0.75 / 100 (pinned) |
| All other 54 EA inputs | source defaults | source defaults (verified per run, §5) |
| `NEXA_Risk.mqh` | approved `7fd5692a…` | **unchanged**, checked before and after |
| Deployed `Experts\Advisors\NEXA_EA.ex5` | stale 2026-09-27 build | **untouched**, hash checked before and after |

**Why 100 lots is inert:** the unchanged margin limit (50 % of free margin at $50,000 and 1:200) allows at most about 50 lots of USDJPY, 43 of EURUSD, 37 of GBPUSD and 11 of XAUUSD. The cap therefore never binds first.

**Why neutralising it in the tester is legitimate:** each tester run trades one symbol. The cap's purpose, limiting same-currency stacking across pairs, cannot act there, so the cap only clamps lot size. That clamp is what made the production campaign trade once in 3,927,131 decisions. Over 2.7 years it blocked 21,081 fully qualified decisions, about 4,400 distinct opportunities.

## 3. Build under test

- **Binary:** `build/NEXA_EA.ex5`, sha `91ee5e20…`, compiled 2026-09-29 from the verified source `NEXA_EA.mq5` `d65090cc…` with the approved `NEXA_Risk.mqh` `7fd5692a…`. This is the build that would be deployed after the remaining decisions. It includes the S1–S10 safety fixes and the fail-closed correlation cap.
- **Installed as** `MQL5\Experts\NEXA_Research\NEXA_EA_CAPN.ex5`, a separate research copy. Its hash is checked to equal `91ee5e20…`. The deployed `Experts\Advisors\NEXA_EA.ex5` is never overwritten.
- **No exact comparison with the $50k production campaign is possible.** That campaign's binary (139,784 bytes, from source `9d1e6aaf…`) no longer exists anywhere on this machine, and the source has changed since (safety fixes). This campaign therefore stands on its own; it is not presented as "production campaign minus the cap".

## 4. Campaign design (same windows and tester settings as the production campaign)

- **Symbols:** GBPUSD, EURUSD, USDJPY, XAUUSD.
- **Windows (48 runs):** 11 calendar-quarter chunks A2024Q1 … A2026Q3 (2024-01-01 → 2026-08-28) plus window B (2026-08-28 → 2026-09-26), per symbol.
- **Tick model:** window A uses Model 0, every tick generated from M1 (Pepperstone has no real ticks before 2026-08-28; labelled). Window B uses Model 4, real ticks.
- **Account:** $50,000 USD, leverage 1:200, chart M1, execution delay 250 ms.
- **Chunk effects (as before, documented):**
  - the EA re-initialises at each chunk start;
  - the tester closes open positions at chunk end;
  - equity resets to $50,000 at every chunk start, so compounding runs within a chunk, not across chunks.
- **Bar exports** from the production campaign are reused (same tester data and windows), so no bar-export runs are repeated.
- **Run time:** about 1 minute per run plus about 2 minutes waiting for the agent log, so roughly 2.5–3 hours for 48 runs. Allow for about 25 % random early deaths and their retries.
- **Disk:** about 70 MB of Trade DNA per chunk (measured on the smoke run), so about 3.3 GB for the remaining 47 chunks. Free space was 7.6 GiB after the smoke run. macOS may also add 1 GB swap files under memory pressure, since this 8 GB Mac's swap was at 7.2 of 8 GB during the smoke run.
- **Disk and swap checks before every chunk:**
  - the runner stops if free disk is below **3 GiB**, or if macOS has added **2 or more swap files** since the batch started;
  - the campaign is resumable: verified chunks are skipped, including the smoke chunk, which counts as the USDJPY A2026Q1 run;
  - close memory-heavy apps before A3.

## 5. Gates (any failure = STOP and report; nothing is bypassed)

**Pre-run (every invocation):**
1. The approval token is set (§10).
2. `NEXA_Risk.mqh` = `7fd5692a…`, `NEXA_EA.mq5` = `d65090cc…`, `build/NEXA_EA.ex5` = `91ee5e20…`.
3. No MT5 terminal is running.
4. At least 3 GiB of disk is free. This is re-checked before every chunk, together with the swap-file count (see §4).
5. The settings file holds exactly 10 active lines, including `InpMaxSameCurrencyNet=10000`.
6. The research EA copy hash = `91ee5e20…`.

**Smoke run first:** USDJPY A2026Q1, the chunk where the production cap blocked the most decisions (718). `full` refuses to start until smoke passes all per-run gates and has produced at least one closed trade.

**Per run (all must hold):**
1. The tester log has "Test passed" for this symbol, inside this run's time window.
2. The Trade DNA's last decision is within 4 days of the window end.
3. **Every logged input equals its source default, except `InpMaxSameCurrencyNet=10000`.** No input may be missing or unexpected.
4. **Zero `NO_TRADE_PORTFOLIO_CURRENCY_EXPOSURE_CAP` decisions.**

Gates 3 and 4 are configuration gates: a failure there stops the whole batch and is not retried. Other failures are retried up to 3 times; failed attempts are renamed `FAILEDRUN_*`, never deleted or reused.

*Dry test of gates 3–4 (read-only, 2026-10-02) on production run `PS_NEXA_USDJPY_A2026Q1`:*
- gate 4 failed it with "exposure-cap blocks present";
- gate 3 alone failed it with `input mismatch ['InpMaxSameCurrencyNet']`;
- all other 63 inputs matched their source defaults.

**Post-batch:**
- The deployed EA hash and the `NEXA_Risk.mqh` hash are unchanged.
- A `SHA256SUMS` is written for all DNA files.
- **Balance reconciliation (before any analysis):** per run, rebuild the balance as
  - $50,000
  - plus price P&L from the agent-log deals (price × volume × contract size, converted to USD at the deal price),
  - plus the sum of **CLOSE-row** commission and swap.

  This must equal the tester's own "final balance" line to the cent. FILL-row commission is never added, because the CLOSE row already carries the full round trip (§7A). If a run doesn't reconcile, it is excluded and reported, never patched. *The smoke run reconciled exactly: price P&L +$2,730.67, CLOSE commission −$5,222.74, swap $0.00, giving $47,507.93, the tester's figure.*

## 6. Outputs and isolation

- **Runs:** `research/tester_runs_capneutral/CAPN_NEXA_<SYM>_<WINDOW>/`, with `tester.ini`, logs, `RUN.txt`, `LABEL.txt` and `VERIFIED_PASS`.
- **Trade DNA:** `data/pepperstone/tester_capneutral/CAPNEUTRAL_NEXA_TradeDNA_<SYM>_<WINDOW>.csv` plus `SHA256SUMS`.
- **Kept away from production tooling:** run ids do not start with `PS_`. `tools/rerun_failed.sh` and `nexa_tester_verify.py`, which are hard-wired to the production configuration, therefore never see or re-run these runs; a re-run through them would silently restore the production cap.
- **Report:** `research/reports/CAPNEUTRAL_RESEARCH_RESULTS.md`, titled with the label.
- **No registry write:** this is exploratory research on NEXA's own rules, not a frozen campaign. Nothing is written to V2 or 8E.

## 7. Pre-registered analysis (fixed before any result is seen)

### 7A. Strategy edge evidence (primary)

- **Unit:** resolved trades (OPEN → CLOSE pairs in the DNA), ordered by entry time. Partial closes are aggregated into their parent trade; the CLOSE row already gives the whole-position values.
- **Net R (pre-registered definition, amended 2026-10-03, §11):** each trade's realised dollar result divided by its initial dollar risk:

  `net_R = realised_pnl_usd / initial_risk_usd`

  - **`realised_pnl_usd`** = the sum over every exit leg of `direction × (exit price − actual fill price) × leg lots × contract value`, plus the CLOSE row's commission and swap.
    - Exit legs are the PARTIAL_CLOSE rows plus the CLOSE row's final leg. A row's `entry_actual` is that deal's price and its `lots` is that leg's volume.
    - The actual fill price is the FILL row's `entry_actual`.
    - The CLOSE row's commission and swap are totals over every deal of the position. FILL-row commission is never added; it would count the entry commission twice.
    - Contract value per 1.0 price move per lot, in USD: 100,000 for EURUSD and GBPUSD, 100 for XAUUSD, and 100,000 ÷ the leg's exit price for USDJPY (yen P&L converted at the exit rate, as the tester books it).
  - **`initial_risk_usd`** = the OPEN row's `lots × risk_dist ×` the same contract value. For USDJPY it is converted at the intended entry price, the risk NEXA sized against.
  - **Exactness check:** the sum of `realised_pnl_usd` over a run must equal that run's reconciled balance change to the cent. Any run that fails is excluded and reported (§5).
  - **Why not `result_r` directly:** the DNA's `result_r` is price-only R measured from the *intended* entry. It leaves out entry slippage, commission and swap (`NEXA_EA.mq5` close handler).
    - It is reported only as "gross R, from intended entry", and Gate 8 never receives it.
    - As a cross-check, `result_r` plus entry slippage plus commission and swap must agree with `net_R` to within the 4-decimal rounding of `result_r`.
  - **Validated on the smoke run:** the sum of `realised_pnl_usd` is −$2,492.07, exactly the tester's balance change. Mean `net_R` is −0.227R; mean `result_r` is +0.088R.
- **Test:** `nexa_stats.evaluate` (Gate 8, unchanged code) with `StatsConfig(min_trades=200, block=10)`, all other settings default (cost shock +0.05R, seed 20260927).
  - `min_trades=200` is the project's validation requirement.
  - `block=10` allows for serial dependence of trades in time.
  - The iid bootstrap (`block=1`) is reported as a secondary view.
- **Scope:** pooled across symbols (primary) and per symbol (secondary, Benjamini–Hochberg across the 4 symbols).
- **Extra stress:** +0.15R per trade, reported, not used for the verdict.
- **Verdict:** the Gate 8 enum, exactly as the code returns it: `INSUFFICIENT_SAMPLE`, `NEGATIVE_EXPECTANCY`, `EDGE_NOT_DEMONSTRATED` or `EDGE_SUPPORTED_IN_SAMPLE`.
- **Labelling:** every verdict is labelled **PRELIMINARY**. The window is not out-of-sample (the EA was developed and hardened during it), so even `EDGE_SUPPORTED_IN_SAMPLE` would only justify a prospective forward test, never a profitability claim.
- **Also reported:**
  - trade count per symbol and year;
  - win rate, average win and loss in R, profit factor;
  - expectancy, gross and net;
  - cost breakdown (spread, commission, slippage, swap in R, and cost share of gross);
  - maximum drawdown in R;
  - Monte Carlo ruin probability at the 10 % drawdown limit;
  - DSR at the honest trial count (1 pre-specified rule), plus sensitivity at larger counts.

### 7B. Capital-sizing feasibility (secondary, separate)

**The user's objective, verbatim:**
> PRIMARY CAPITAL OBJECTIVE: +24.5% net equity growth per trading day, compounded over the trading period, with the intended 20-day cycle and monthly profit extraction/reset described in the NEXA System Blueprint.

**Guardrails (binding on this campaign):**
- The objective is the user's target, not a guaranteed or expected outcome.
- No frozen hard-risk control is altered to pursue it.
- The experiment is not shaped or optimised to produce it.
- It is not a prerequisite for selecting or rejecting any hypothesis.
- The finding is reported objectively as SUPPORTED, CONTRADICTED or UNRESOLVED for the tested configuration.

**Source note:** a document named "NEXA System Blueprint" is **not present in this repository**. The 20-day cycle parameters used here are the ones already recorded in `research/reports/NEXA_24_5_DAILY_FEASIBILITY_AUDIT.md` §1: start balance, 20 trading days compounded, profit extracted and balance reset to the start at cycle end. A 20-day run at +24.5 %/day ends at 80.05 × the start balance. If the Blueprint defines the cycle differently, that document must be supplied before analysis, and this section is amended before results are opened.

**Arithmetic ceiling under the tested configuration (pre-registered, from the frozen inputs):**
- **Largest possible gain per trade:** 50 % closed at 1.5R plus 50 % at the 4.0R take-profit maximum, so 2.75R.
- **Risk per trade:** ≤ 0.30 % of equity (rounded down at $50k).
- **Trades per day:** ≤ 10, account-wide (shared `TradesToday` counter).
- **Highest possible day, before costs:** (1 + 0.0030 × 2.75)^10 − 1 ≈ **+8.6 %**. *(Superseded by amendment 2, §11: the implemented EA cannot partial-close, so the correct figure is ≈ +12.67 %.)*
- **Formal upper bound:** +31 %, but only if all 10 trades took the minimum-lot path up to the 1 % ceiling. At $50k that path needs gold stops wider than about $150 (≈ 3 % of price), so it is not a practical route.
- **Pre-registered expectation:** **zero days at or above +24.5 %.** Any such day is treated as a probable simulation or accounting defect and investigated before anything is reported.
- **What this implies:** under the frozen controls, the objective cannot be reached on any day regardless of edge. The campaign measures how far below it the realised profile sits; it cannot show the objective is feasible.

**Measured and reported (per symbol; each tester run is its own account):**
- **Daily net return:** realised closed balance by Pepperstone server day. Days with no trade count as 0 %.
  - Reported as a distribution: mean, median, standard deviation, quantiles 1/5/25/75/95/99 %.
  - Maximum daily return and the best 10 days.
- **Losing days:** count and share of losing days, the largest daily loss, and the number of days halted at −2 %.
- **Drawdown:** maximum drawdown and the longest drawdown duration.
- **Activity:** trade count per day (mean and maximum) and the share of days with ≥ 1 trade.
- **Expectancy and cost impact:** from §7A.
- **Days at target:** frequency and share of days at or above +24.5 %, with a 95 % Clopper–Pearson upper bound when the count is 0.
- **20-trading-day cycles:** non-overlapping cycles chained within chunks (a cycle never spans a chunk reset).
  - Compounded cycle return distribution.
  - Count of cycles reaching ×80.05.
  - Share of cycles ending below their start (before extraction).
- **$200 replay (labelled as a replay, not a tester run):**
  - The same trade sequence (entry time, R, costs) is replayed at the 0.30 % risk setting on a $200 start, with 20-day cycles and extraction/reset, using the existing capital-velocity simulator (`nexa_8e_capital.simulate`) and the real broker spec.
  - Reports the share of trades skipped below the minimum lot, cycle outcomes and extracted profit.
  - It reads no data beyond the campaign's own DNA.
- **Not done:** portfolio-summed returns across the four separate runs. They would break the account-wide 10-trades and 2 % daily-loss limits that a real single account enforces.

**Verdict rule for the objective (tested configuration only):**
- **CONTRADICTED:** the campaign completes and no day reaches +24.5 %, consistent with the arithmetic ceiling.
- **UNRESOLVED:** the campaign does not complete, or balance reconciliation fails.
- **SUPPORTED:** a target frequency high enough for the 20-day cycle to complete. This is not attainable under the frozen controls.

**Keeping the two answers apart:** the report states the edge verdict (§7A) and the capital-sizing verdict (§7B) in separate sections. A NO-EDGE result does not by itself answer the sizing question, and the sizing ceiling does not by itself answer the edge question.

## 8. Known limitations (disclosed up front)

- **Not out-of-sample;** results are PRELIMINARY (§7A).
- **Generated ticks** (Model 0) in window A; real ticks only in window B.
- **Single-symbol runs:** cross-pair correlation and exposure interaction are not exercised; that is exactly why the cap is inert here.
- **Chunk resets** of equity and positions at quarter boundaries.
- **The production configuration is not what is tested.** This campaign says nothing about how NEXA behaves under the 0.02-lot cap. If an edge appears, the live cap still needs its own decision (option C, a risk-counted cap, as a separately approved change).
- **D-TZ:** the fixed GMT+2 offset is wrong during US daylight time. Inherited; it shifts session tags and FOMC windows by an hour in summer. Disclosed, not corrected.
- **No V2 or 8E interaction:** `NEXA_Risk.mqh` is not pinned by either campaign, and nothing is written to their registries.

## 9. Stop rules

Stop and report immediately (no workaround) on:
- any configuration gate (inputs or exposure-cap blocks);
- a hash mismatch (risk file, source, binary or deployed EA);
- free disk below 3 GiB, or 2 or more new macOS swap files since the batch started (checked before every chunk);
- a chunk failing 3 attempts;
- balance reconciliation failing on more than 10 % of runs;
- any day at or above +24.5 % (investigate first);
- the MT5 terminal dying repeatedly (B-TERMINAL).

## 10. Approvals requested before anything runs

- [x] **A1.** *(done 2026-10-03)* Install the research copy `Experts\NEXA_Research\NEXA_EA_CAPN.ex5` (= `build/NEXA_EA.ex5` `91ee5e20…`) beside, not over, the deployed EA.
- [x] **A2.** *(done 2026-10-03, PASSED)* Run the **smoke** chunk (USDJPY A2026Q1) with `InpMaxSameCurrencyNet=10000`, labelled CAP-NEUTRAL RESEARCH — NOT PRODUCTION CONFIGURATION.
- [x] **A3.** *(done 2026-10-03, 48/48 verified)* After reviewing the smoke result, run the **full** 48-run campaign.
- [x] **A4.** *(approved 2026-10-03)* Write the analysis code for §7 (new research files only; Gate 8 code unchanged) and the results report.

Each approval is separate. Nothing above is started by approving this plan's text alone.

## 11. Amendments

**2026-10-03, after the smoke run and before any full-campaign run (human-approved):**

1. **Net-R definition (§7A) and balance reconciliation (§5).** The smoke run showed that the DNA's `result_r` is price-only R measured from the intended entry: it excludes **entry slippage, commission and swap**. It also showed that the CLOSE row carries the full round-trip commission while the FILL row repeats the entry half. Both facts are confirmed in the EA source and by an exact balance reconciliation.
   - Net R is therefore defined from each trade's realised dollar result, which reproduces the tester's balance to the cent.
   - A first version of this amendment, using `result_r` plus commission and swap, missed entry slippage; it was off by $3.09 on the smoke run. It was corrected the same day, before any full-campaign run.
   - The definition follows the EA's own accounting, so that Gate 8 receives costs as the broker charged them. It was not chosen to favour any result.
   - **Disclosure:** the smoke chunk's own outcome was seen before this amendment: +0.088R per trade gross of commission, −0.226R net, with commission averaging 0.315R per trade at $7.00 per lot round trip. It is one symbol for one quarter. The chunk stays in the campaign unchanged.
2. **Disk and swap gates (§4, §5, §9).** The 6 GiB floor could not accommodate the remaining 47 chunks (about 3.3 GB against 7.6 GiB free), and the free-space check ran only once. It is now a 3 GiB floor plus a swap-file-growth stop, both checked before every chunk.

Nothing else in the plan changed. The settings file, windows, tester settings, gates 1–4, the Gate 8 configuration and the capital-objective analysis (§7B) are unchanged.

**2026-10-03, after A3 and BEFORE any campaign result was opened (A4 approved; amendment 2):**

1. **Engineering defect D-PARTIAL-AFTER-BE (disclosed, not repaired).**
   - **Where:** `NEXA_EA.mq5` `ManageOpenPosition` (source `d65090cc…`).
   - **Mechanism:**
     - At `InpBreakevenAtR` = 1.0 the EA moves the stop to exactly the entry price (`SafeModifySL(ticket, open, …)`).
     - From then on `risk = MathAbs(open − sl)` is 0, and the routine returns early (`if(risk <= 0 …) return;`).
     - So the partial close at `InpPartialCloseAtR` = 1.5 (50 %) can fire only if price moves from below 1.0R to at least 1.5R within a single management pass.
     - The 48-bar time exit (`InpTimeExitBars` = 48, applies when r < 0.3) is never evaluated once a position is at breakeven.
   - **Evidence:** the 48 runs contain 0 PARTIAL_CLOSE rows, and in every run the tester deal count is exactly 2 × the CLOSE rows (3,804 deals, 1,902 trades).
   - **Implemented behaviour actually tested:** each trade exits in full, at the stop-loss (−1R before costs), at breakeven (≈ 0R) once 1.0R was reached, at the take-profit (`target_r` between 1.5R and 4.0R), by the time exit (only if breakeven was never reached), at the Friday close, or by the tester at chunk end.
   - **Intended (specification) behaviour, NOT tested:** 50 % closed at 1.5R, the rest managed to the take-profit or breakeven, and the time exit available for the whole life of the trade.
   - **The campaign remains valid** as a measurement of the implemented EA. All results are labelled "implemented EA (D-PARTIAL-AFTER-BE present)". No result is re-scored as if the specification had been implemented, and no alternative EA is simulated and presented as campaign evidence.

2. **Daily-return ceiling (§7B) corrected.** The earlier figure assumed the specified 2.75R best case, which the implemented EA cannot produce. Derivation from the frozen inputs, before costs:

   | Input | Source | Value |
   |---|---|---|
   | Risk per trade | `InpRiskPercent`, rounded DOWN to the volume step | r ≤ 0.30 % of current equity |
   | Best exit per trade | full take-profit, `targetR = MathMin(anchorR, InpMaxTP_R)` | ≤ 4.0R |
   | Trades per day | `InpMaxTradesPerDay`, account-wide `TradesToday` counter | ≤ 10 |
   | Commission and swap | — | ≥ 0 cost, so they only lower the bound |

   - **Best trade:** a +4.0R win at 0.30 % risk multiplies equity by at most (1 + 0.0030 × 4.0) = 1.012. Sizing uses current equity, so ten wins compound.
   - **Implemented ceiling:** 1.012^10 − 1 = **+12.6692 %** per day, the corrected figure.
   - **Intended specification (not tested), for reference:** (1 + 0.0030 × 2.75)^10 − 1 = +8.5631 %.
   - **Formal upper bound:** if every trade took the minimum-lot path up to the 1 % hard ceiling, 1.04^10 − 1 = +48.02 %. At $50,000 that path requires stops wider than about $150 per 0.01 lot of risk (about 3 % of the gold price) and is not a practical route.
   - **Trades needed for +24.5 % at the 0.30 % × 4R maximum:** ln(1.245) / ln(1.012) = 18.37 consecutive full-target wins. That exceeds the 10-trade cap, so +24.5 % is **unreachable on any day** under the frozen controls, whatever the edge.
   - **Pre-registered expectation unchanged:** zero days at or above +24.5 %; any such day is investigated as a probable defect.
3. **$200 replay (§7B) aligned with the tested risk architecture (disclosed deviation).**
   - **Why:** the pre-registered simulator (`nexa_8e_capital.simulate`) sizes with costs included and skips any trade below the minimum lot. NEXA's own rule (`NEXA_Risk.mqh` `CalcLotSizeHardened`) sizes on price risk only, rounds down, and if the result is below the minimum lot **executes the minimum lot only if its risk is within the 1 % hard ceiling**; otherwise no trade.
   - **Replays reported:**
     - (a) the pre-registered simulator at 0.30 % risk, as written;
     - (b) a replay applying NEXA's own sizing rule.

     Both use real broker minimum lots and steps and are labelled as replays (theoretical sizing of tested trades), not as broker-executed results.
   - **How:** each 20-trading-day cycle starts at $200, and profit is extracted (or a loss realised) at cycle end.
4. **Specification gaps filled with library defaults (stated before results):**
   - **Per-symbol Benjamini–Hochberg:** uses the repository's one-sided expectancy p-value (`nexa_robust.expectancy_pvalue`) at `q = 0.10`, the library default.
   - **DSR at the honest trial count of 1:** equals PSR against 0.
   - **Larger-trial-count DSR sensitivity:** borrows the 8E VAL Sharpe variance and is labelled EXPLORATORY.
