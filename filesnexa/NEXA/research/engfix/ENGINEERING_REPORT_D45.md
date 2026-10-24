# D-PARTIAL-AFTER-BE (D45): engineering correction report (2026-10-03)

**Scope:** engineering correction only. No strategy parameter, entry logic, risk limit, exposure cap, survival-pause threshold, V2 or 8E artefact was changed. Nothing was deployed: the deployed `Experts\Advisors\NEXA_EA.ex5` is untouched (`f0ae9618…`).

## 1. Root cause

`NEXA_EA.mq5` `ManageOpenPosition()` (source `d65090cc…`) recomputed the R denominator from the **current** stop on every tick:

```
double risk = MathAbs(open - sl);
if(risk <= 0 || !NexaFinite(risk)) return;
```

- At `InpBreakevenAtR` = 1.0 the EA moves the stop to exactly `open`. From then on `risk = 0` and the routine returns before the **1.5R partial close** and the **48-bar time exit**.
- The partial could fire only if price jumped from below 1.0R to at least 1.5R within one management pass.
- **Evidence:** in A3, 1,902 trades each had exactly 2 deals and there were 0 partial closes. The pre-fix build in this regression: 0 partials in 495 trades.
- **Why the 2026-09-29 safety audit missed it:** it forced partials with `InpPartialCloseAtR=0.5`, so they fired before breakeven.

## 2. Exact fix

1. **New include `NEXA_PositionMgmt.mqh`** (`b98a49b5…`). It holds pure decision functions (`NexaInitialRiskRef`, `NexaMgmtR`, `NexaPartialCloseVolume`, `NexaPartialHandled`, `NexaManageStep`), contains no policy and introduces no parameter. The EA passes its existing inputs in and executes the returned actions with its existing guards.
2. **R reference** = the **original initial risk**, i.e. the existing authoritative `RiskDist_<posId>`.
   - It is staged at sizing, migrated at fill, and is the same R the Trade DNA `result_r` and the survival statistics already use.
   - Without that context it falls back to the stop distance **only while the stop is still on the loss side**. At or beyond breakeven, R is unknown and R-based management is skipped with a one-time warning; that case did not occur in the regression.
3. **Partial close exactly once:**
   - "Already executed" is decided by the position's **deal history**: any exit deal while the position is open.
   - A partial is also treated as in flight if a **NEXA close order for the position is pending** at the broker, at any age.
   - `PartialDone_<posId>` now stores the **time of the last send attempt**, which blocks a re-send within `InpInFlightTimeoutSec`. A failed send retries after that window.
   - Unreadable history **blocks** the send (fail-closed, logged once).
   - The legacy flag value 1 and a flag reset by restart adoption are harmless, because history is authoritative.
4. **Time exit:** evaluated whenever R is known, including after breakeven (unchanged rule: ≥ 48 bars and r < 0.3).
5. **Keys:** context keys are read by `POSITION_IDENTIFIER`, the key every writer and deleter uses (reviewer S1).
6. **Unchanged:**
   - breakeven guards (`StopDistanceAllowed` / `FreezeLevelAllowsChange` / `ModifyThrottled`);
   - the partial-volume rule;
   - all 64 inputs and their defaults;
   - `NEXA_Risk.mqh` (`7fd5692a…`);
   - every other function, which is byte-identical to the pre-fix source (test-enforced).
7. **Build:** compiled as a byte-identical staged copy `build/NEXA_EA_PMFIX.ex5` (`28e8d925…`, source `10b62623…`): **MetaEditor 0 errors, 0 warnings**. The A3 binary `build/NEXA_EA.ex5` (`91ee5e20…`) was not overwritten.

**Disclosed behaviour change before breakeven:** the R denominator moves from |actual fill − placed stop| to the sized initial risk. On the A3 trades, the new r ÷ the old r has median **1.000**, is within ±3 % for **92 %** of trades, and spans 0.947–1.052 at the 1st/99th percentiles. The only source is tick rounding of very tight stops. Breakeven and partial thresholds now use the same R as the journal.

## 3. Tests added

| Requirement | Evidence |
|---|---|
| 1 below 1R · 2 BE at 1R (management stays active) · 3 1.5R after BE · 4 exactly once · 5 remainder state · 6 no retrigger · 7 48-bar time exit after BE · 8 SL/TP after partial · 11 restart / lost flag / legacy flag · 12 failed send, in-flight window, async late execution, unreadable history | `NEXA_PositionMgmtTest.mq5`: 47 scenario checks driving the exact `NexaManageStep` in the Strategy Tester → **47 / 47 PASS** (`runs/pmgmt_harness/`) |
| Mutation testing | 6 deliberate regressions of the include (current-stop denominator, ignore deal history, ignore in-flight window, no time exit after BE, whole-position close, ignore pending order) → **6 / 6 killed** (`runs/mutation_summary.json`) |
| 9 Trade DNA records the partial · 10 result_r / net-R accounting · end-to-end behaviour | Pre-fix vs fixed EA, GBPUSD, 12 windows, **production inputs** (no override; `InpMaxSameCurrencyNet=2`), $200 deposit, 24 tester runs (`regression/regression_evidence.json`) |
| Static source contract | `research/test_nexa_position_mgmt_fix.py` (9 tests, evidence pinned to current source hashes) |

### End-to-end regression results (ENGINEERING REGRESSION, not research evidence)

| Check | Result |
|---|---|
| Runs: Test passed / inputs exactly production | 24 / 24 / 24 |
| Partial closes: pre-fix → fixed | **0 → 52** (in 495 → 525 trades) |
| Partials sent (EA log) = partials executed | 52 = 52 in every window; **no duplicate send** |
| Trigger R (EA log) | all ≥ **1.50R** vs initial risk |
| Max one partial per trade; deals = legs | yes / yes |
| Balance reconciliation (deals and DNA incl. partial legs) | **24 / 24 to the cent** |
| CLOSE `result_r` = volume-weighted over both legs | max relative error 1.8 % (5-dp journal rounding) |
| `nexa_ingest`: no errors, episodes OPEN → … → CLOSE | yes / yes |
| Send failures / missing-reference / unreadable-history warnings | 0 / 0 / 0 |
| 0.01-lot positions (not splittable, logged once) | 101 |
| First pre/post divergence | always at an exit row: a fixed-EA PARTIAL_CLOSE or an earlier CLOSE, i.e. the time exit after BE (journaled R ≈ 0.28–0.31) |

**Deal price vs trigger:** one partial filled at 1.43R although it triggered at 1.505R. The broker's real ticks show the ask moved 2 points during the tester's 250 ms execution delay on a 2.7-pip stop. This is exit slippage, not logic.

## 4. Tests passed

- Harness: 47 / 47.
- Mutants: 6 / 6 killed.
- Fix tests: 9 / 9.
- Full research suite: **587 passed** (578 before + 9 new).
- **ruff:** clean.
- **Two pre-existing safety tests updated (legitimate):** the missing-stop slice anchor, and the 2026-09-29 audit evidence, now pinned to its own source `d65090cc…`.

## 5. Independent review

A general-purpose read-only agent reviewed the change. The named "You should know" side-agent was not available.

- **Verdict:** no blocker.
- **Applied:**
  - S1: keys by `POSITION_IDENTIFIER`;
  - S3: pending-order guard against a partial that executes after the 20 s window;
  - observability: one-time logs for unsplittable volume and unreadable history; history not re-read once a partial is confirmed.
- **Remaining uncertainty (pre-existing, documented, not changed here):**
  - **Partial-volume rule:** floors to the 0.01 grid, so 0.01-lot positions never partial and binary rounding can close slightly under 50 %.
  - **Take-profit collision:** a take-profit at exactly 1.5R (the TP floor) closes before the partial can fire.
  - **Netting accounts:** `PositionClosePartial` refuses on netting accounts (Pepperstone runs are hedging).
  - **Partial fill of the partial order:** treated as done.
  - **Time-exit bar count:** `iBarShift(PERIOD_CURRENT)` depends on the chart timeframe.
  - **Missing-stop recovery path** (`sl <= 0`) still reads `RiskDist_` by ticket. It is outside this defect; note.
  - **Rejected async partials** are retried but not journaled.
  - **Duplicate residual:** a sync-mode TIMEOUT followed by a late execution that is visible neither as a pending order nor in history.
  - **Outcomes diverge from previous research runs:** this is expected, because exits now differ.

## 6. Production deployment status

**NOT deployed.**
- `Experts\Advisors\NEXA_EA.ex5` = `f0ae9618…` (stale 2026-09-27 build) is unchanged.
- Test binaries live only under `Experts\NEXA_EngFix\`.
- Deployment still needs the open decisions (S11, D-TZ, stale build) and separate approval.

## 7. Frozen and research artefacts

- **Unchanged:**
  - V2 (seq 6 `bbd9a28e…`) and 8E (seq 2170 `9f7249a2…`), verified including all pins;
  - the A3 binary and research copy (`91ee5e20…`);
  - all `research/capneutral/` files.
- **Pre-fix source** is preserved at `build/pmfix_pre_source/NEXA_EA.mq5` (`d65090cc…`).
- **Expected consequences of the source change** (the frozen files themselves were not edited):
  - `run_capneutral_batch.sh` now refuses to run;
  - `capn_analysis.py`'s integrity block would report `NEXA_EA.mq5` as changed.
- The master status files still cite the pre-fix EA hash `d65090cc…`.
