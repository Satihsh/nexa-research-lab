# NEXA pre-live engineering safety audit (2026-09-29)

**Scope.** Deterministic safety, execution, time, state, recovery, data-integrity and broker-interface defects in the live MQL5 tier, fixed only where no strategy, feature, parameter, hypothesis or V2 experiment element changes.

**Unchanged:**
- `NEXA_Risk.mqh` (`7fd5692a…`, the approved correlation fix only);
- schema v1.0 and f00–f47, including `PackFeatures`, which is byte-identical to the baseline;
- all inputs and defaults;
- V2: FROZEN and not opened.

**Changed:**

| File | Before | After |
|---|---|---|
| `NEXA_EA.mq5` | `97a3ff62…` | `d65090cca1654814…` |
| `NEXA_Intelligence.mqh` | `efa6db4e…` | `18e3b30c7de52234…` (news loop only) |
| `NEXA_Safety.mqh` | — | new, `843fc60674d4c3e7…` |

Backup: `NEXA_PRE_SAFETYAUDIT_BACKUP_20260929T092117Z/`.

## Findings and dispositions
| # | Area | Defect (evidence) | Disposition |
|---|---|---|---|
| S1 | Recovery | `OnInit` released the in-flight guard unconditionally. An order still pending at the broker after a restart could be duplicated. | **FIXED:** the guard is kept while `NexaOrderPending()`, and staged context is kept for it. |
| S2 | Execution / risk | Requote retries resent at the new price with lots sized for the old stop distance, so monetary risk could exceed the sized amount; the stop or target could also become invalid. | **FIXED:** every attempt re-validates stop side vs stops level, target room ≥ `InpMinTP_R`, and risk distance ≤ the sized distance. Otherwise it aborts, fail-closed. |
| S3 | Execution / state | Cross-instance race. Four EA instances decide on the same bar; each can pass `ExposureCapOK` / `CorrelationCapOK` / the daily trade limit before any position exists, then jointly exceed the caps. `IncrementTradeCount` was also a non-atomic read-modify-write. | **FIXED:** a terminal-global entry lock (`GlobalVariableSetOnCondition`, owner-checked release, stale reclaim after 2 × `InpInFlightTimeoutSec`) is held from the portfolio checks until the order resolves. The daily slot is reserved atomically before dispatch and given back only if nothing reached the server. The existing caps are enforced as written; the fix can only block. |
| S4 | Safety / recovery | A missing SL was re-applied at `open ± riskDist` even when price had already passed that level. The modify was rejected forever and the position stayed unprotected. | **FIXED:** if the intended stop is breached or inside the broker distance, the position is closed (de-duplicated). Otherwise the modify is re-applied, throttled. |
| S5 | Broker interface | The breakeven modify was re-sent every tick while `SL < open`, with no stops-level or freeze-level check (request spam, rejects). | **FIXED:** it is sent only when the stops/freeze distance allows it, throttled per `InpInFlightTimeoutSec`. |
| S6 | Broker interface | The time exit called `PositionClose` every tick until the position disappeared (duplicate close requests in async mode). | **FIXED:** uses the existing de-duplicated `CloseNexaPositionIfAny`. |
| S7 | Safety gate | The news filter skipped (**fail-open**) an event or country it could not resolve. | **FIXED:** an unresolvable event or country is treated as a risk window (fail-closed). The tester behaviour is unchanged (the calendar is unavailable there, as documented). |
| S8 | Data integrity | `row_id` restarted its sequence at 1 on every restart (the ingest flags `DUPLICATE_ROW_ID` as ERROR), and it was cast to int32. | **FIXED:** the sequence is run-seeded 64-bit (`TimeLocal()·10⁶`, `%I64d`). The column is unchanged and still an opaque string. |
| S9 | State integrity | `DEAL_ENTRY_OUT_BY` (close-by) was ignored: no CLOSE row, context never cleared, and the position was treated as partially closed forever. | **FIXED:** OUT_BY counts as an exit, both in the close handler and in the full-close test. |
| S10 | Data integrity / gate input | CLOSE `result_r` and the expectancy/survival statistics used only the **last** exit leg. After the default partial close at 1.5R, the banked R was lost. | **FIXED:** the result is volume-weighted over all exit legs. Verified in the tester: trades with a partial close were recorded as 0.0000R and −0.0091R, and are now +0.2620R and +0.2545R, matching the hand calculation. |
| S11 | Risk (`NEXA_Risk.mqh:326`) | `NetCurrencyExposure` skips a position whose symbol cannot be read, so the exposure cap under-counts (**fail-open**). | **NOT FIXED: needs your explicit approval** (frozen file; the approval covered only the correlation block). Proposed: an unreadable position → block the new entry. |
| S12 | Time (D-TZ) | `InpGMTOffset = 2` is fixed; the broker is New York + 7 h (UTC+2/+3). During US DST the session tags, Asia range, optional session filter and hard close are off by 1 h. | **NOT FIXED: human decision.** The session and Asia-range values feed frozen features (f00–f47). The FOMC gate was checked and is **not** affected: its 18:00 GMT anchor plus 1 h margin still covers the statement and press conference in both seasons. |
| S13 | Multi-symbol data | `UsdCompositeDirection` reads other symbols by shift via `iClose`, with no sync or time alignment. | **NOT FIXED:** it is a frozen `PackFeatures` feature slot. It is diagnostic and never scored as a gate. |
| S14 | Broker interface | `SetDeviationInPoints(20)` is fixed for every symbol (2 pips FX, $0.20 XAU). | **NOT CHANGED:** a parameter; human decision. |
| S15 | Deployment | The terminal's deployed `MQL5\Experts\Advisors\NEXA_EA.ex5` is the 2026-09-27 build: it predates the correlation fix and this audit. | **Not deployed (by design).** Deployment is your decision. |
| S16 | Tooling | Strategy Tester launches intermittently start no pass when the previous agent is still shutting down. | Worked around by waiting for agents and verifying journal size. The failed runs are disclosed in `tester_runs/safetyaudit_evidence/dna_regression.json`. |

Reviewed and not defects:
- FOMC gate DST coverage.
- Async rejection path.
- Ambiguous retcodes never retried.
- The weekend close uses the broker's own server clock.
- The partial fill leaves risk ≤ sized.
- The emergency-stop daily reset: the max-drawdown check re-fires on the next bar because the equity peak persists.
- Every `Copy*` / `CopyBuffer` count is checked.
- The daily loss uses equity at the server-day roll.

## Verification
| Check | Result |
|---|---|
| MetaEditor compile | `NEXA_EA.mq5`, `NEXA_SafetyTest.mq5`, `NEXA_CorrCapTest.mq5`: **0 errors, 0 warnings** each |
| Safety primitives, runtime (Strategy Tester, `NEXA_Safety.mqh` itself) | **29/29 PASS**: stops/freeze boundaries, NaN/zero inputs, lock (exclusive acquire, owner-only release, stale reclaim, an old holder cannot free a reclaimed lock), slot reservation (exactly 10, release, never negative) |
| Behavioural regression: pre-audit vs fixed EA, same data (EURUSD M1 2024-Q1, every tick, 250 ms) | $50k: 89,645 rows, **0 differing**. $1k (4 trades): 89,657 rows, **0 differing**. Forced partial closes (test override `InpPartialCloseAtR=0.5`): **exactly 2 CLOSE rows differ** (`result_r`, `reason`), the intended S10 correction. `row_id` is unique in every post run. |
| Mutation test of the new static tests | 12 of 12 reverted fixes detected |
| Python regression | **502 passed** (1 pre-existing warning); ruff clean |
| V2 adversarial suite (scratch copy) | **70/70 rejected, 4/4 controls, 0 defects**; real registry `de0c101a…` and witness `05d4544b…` byte-identical |

**Not verifiable in the tester (disclosed).**
- The live 4-instance contention path. The Strategy Tester runs one symbol, so the lock is never contended there. It is covered by the primitive tests and static checks.
- Requote and freeze-level rejections. The tester does not requote.

A multi-chart demo forward check before live trading is recommended; it is a human decision.

## Invariants and state
- `NEXA_Risk.mqh`: `7fd5692a…`, unchanged in this audit.
- Schema v1.0: `c24198b0…`.
- f00–f47 / `PackFeatures`: identical to the baseline.
- `NEXA_BASELINE_BACKUP_20260919-124052`: intact.
- Trading flags: `MTM_ENABLE_TRADING=false`, `MTM_ENABLE_EXEC=false`; MT5 not running.
- Tester launches: every launch synchronised the demo account with **0 positions, 0 orders**; the test builds were removed from `Experts` afterwards.
- MT5 history base: 25,113,084 KB → 25,118,284 KB (+5.2 MB) across this session's tester runs. This is tester cache for EURUSD 2024-Q1, not a broad download.
- **V2:** anchor `6090be68184af7643f82b680d144a1b9e1622b3bbceebfb872729b97b9d9324c`, seq 6 `bbd9a28e…5b2b`, FROZEN, 0 results, 0 OOS rows. No MQL5 file is in the V2 pinned universe, so no re-freeze was needed. **Not opened.**
