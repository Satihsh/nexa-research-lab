# NEXA PHASE3_SIX_FAMILIES_V2: final pre-opening audit and freeze (2026-09-29 UTC)

```
NEXA PHASE3_SIX_FAMILIES_V2
ANCHOR     = 6090be68184af7643f82b680d144a1b9e1622b3bbceebfb872729b97b9d9324c
LEDGER     = seq 6  bbd9a28ed6bc7e0b20f3fca9f9ba1fe437f4bd39dc9c1e99ed73fb7505be5b2b
STATUS     = FROZEN
EVALUATION = NOT OPENED (0 results, 0 OOS rows, no strategy run on market data)
OOS        = PROSPECTIVE [2027-01-04T00:00:00Z, 2028-01-03T00:00:00Z)
TRADING    = DISABLED (MTM_ENABLE_TRADING=false, MTM_ENABLE_EXEC=false; no order placed)
```

Companion files, all in `research/reports/`:
- `PHASE3_V2_MANIFEST.md`: the manifest.
- `V2_EXTERNAL_ANCHOR_VERIFICATION.md`: hashes and checkpoints.
- `V2_OPENING_CHECKLIST.md`
- `V2_OOS_DATE_CLARIFICATION_NOTE.md`: non-pinned.
- `V2_EXTERNAL_CHECKPOINT_PROCEDURE.md`: pinned.
- `adversarial_v2_final/`: attack evidence.
- `NEXA_COMMERCIAL_EA_PRIOR_ART_AUDIT_2026.md`
- `NEXA_ARCHITECTURE_GAP_AUDIT_2026.md`
- `NEXA_FUTURE_RESEARCH_BACKLOG.md`

## 1. Authoritative state (verified from files, not memory)
| Item | Result |
|---|---|
| `NEXA_Risk.mqh` | `e706d453d346100f`, byte-identical to `NEXA_BASELINE_BACKUP_20260919-124052/` |
| `NEXA_EA.mq5` | `97a3ff62cb2c4d36` (unchanged; no `.mq5`/`.mqh` modified since 2026-09-28) |
| `nexa_schema_v1.json` | `c24198b09b0e7192` (v1.0; matches the build manifest) |
| `NEXA_Intelligence.mqh` | `efa6db4e4abae2a9` (matches the build manifest); f00–f47 lines identical to the baseline |
| Baseline backup | `NEXA_BASELINE_BACKUP_20260919-124052_MANIFEST.sha256`: every file OK |
| Bridge | `MTM_ENABLE_TRADING=false`, `MTM_ENABLE_EXEC=false`; MT5 not running |
| Broker data | no MT5 history-base file modified since 2026-09-28; base 25,113,084 KB (see §20, which explains why this differs from the Phase-2 figure) |
| Prior V2 freeze at start of run | `f2dc4ffb…105e` verified intact (31 pins), then superseded (§5) |

## 2. OOS date discrepancy
**Record (non-pinned):** `V2_OOS_DATE_CLARIFICATION_NOTE.md` contains the exact required statement.

**Read-only verification.** Searched all of the following for `2026-10-05` / `2027-10-04`:
- the final registry and all four superseded archives with their notes;
- the external witness directory;
- `protocols_phase3_v2.py`;
- the pinned OOS design file;
- the checkpoint procedure.

**No match.** The strings occur only in the adversarial evidence. There, attack A06b tries to rewrite a protocol to that window and is rejected.

**What the protocols pin.** All six frozen protocols match their pins. F1, F2, F3 and F5 carry:
- `OOS = [2027-01-04Z, 2028-01-03Z)`
- `EXCLUDED = [2025-01-01Z, 2027-01-04Z)`

The anchor pins the campaign, and the campaign pins every protocol hash. No pinned artifact was edited to record the discrepancy.

## 3. Freeze integrity (final)
All values are in `V2_EXTERNAL_ANCHOR_VERIFICATION.md`.
- **Hashes.** Every hash below was recomputed and matches:
  - the anchor;
  - `ANCHOR.txt`;
  - the ledger chain (7 events);
  - the witness (7 entries, equal to the ledger);
  - 6 protocol hashes (unchanged across every V2 freeze);
  - the universe hash, whose universe is re-derived from the protocols;
  - 14 data pins (incl. `contracts.json`);
  - 23 code pins (incl. the builders, trial layer, driver and their tests);
  - 5 design pins (incl. the checkpoint procedure).
- **Registry tree.** The sha256 is unchanged before and after the attacks.

## 4. Feature builders: completed
All builders live in `nexa_v2_features.py`, which is pinned. Signals are enumerated **from the frozen protocol**, so no undeclared configuration can be produced.

| Family / claim | Builder | Information boundary |
|---|---|---|
| F1 H1b | `f1_event_table` → `attach_f1` → `f1_features` | Release score enters on the bar whose **open = release time**, i.e. decided at its close, after the release. Other inputs: eligibility = `f1_eligible`; score = mean of g·c·S over same-timestamp events of the instrument's currencies; S uses the **prior-only** surprise sd; clusters with another exact HIGH event within ±30 min at a different time are skipped. Signal at close = release + Δ. Stop per design 2.E. |
| F2 | `f2_features` (+ certified null `f2_null_random_range`) | UTC Asian range from bars before `asian_end`. The width filter uses the median of 60 **strictly earlier** valid days. The first break decides; the event filter uses scheduled times. |
| F3 H3a/H3b | `f3_features` | HTF bars from UTC bins, visible only when `open + tf ≤ decision_ts`. FVG uses t−2..t; ATR is SMA(14) (MT5 iATR); displacement on t−1. |
| F5 | `f5_features` | Anchor = session-to-date mean (inclusive); σ from the prior 60 price changes × √n; D1 regime from the last **completed** server day; rollover window on **server** time; spread and range medians from strictly earlier dates or sessions. |
| Calendar baselines | `calendar_prior_baselines` (event builder) | Prior-only columns certified by perturbing every later release. |

**Certification.** The registry itself runs `nexa_causality.certify` / `certify_events`; a caller-supplied certificate is refused. Six certificates are registered while FROZEN and are bound to source = function + defining module.

**A weakness was found and fixed before the freeze.** With fractional cuts alone, 3 of 5 deliberately leaky builders **passed**:
- release value 3 bars early;
- HTF visible 1 bar early;
- next-bar spread.

Certification now adds up to 16 **sensitive cuts** at sparse input events and sparse output signals. All leaky variants now fail, and the legitimate builders pass (tests in `test_nexa_v2_features.py`).

**Trial layer and driver.** Both are pinned:
- `nexa_v2_trials.py`: orders, costs, swap charges, three generic nulls plus the family nulls, the stationary bootstrap, the selection rule and the verdict logic.
- `nexa_v2_runner.py`: universe × period → registry records, with no free parameters.

**Unit-bug found and fixed.** Before freezing, F5 σ was in log-return units against a price deviation. It is now in price units.

**Pre-registered operational choices.** The choices made where the protocol and design were silent are listed in the module docstrings, which are pinned:
- the SIGN_MAP;
- same-timestamp clustering;
- the first-break rule;
- the matched-zone construction;
- the London null session;
- swap charges only;
- the warm-up rule.

**F4 and F6 remain BLOCKED.** No builder exists for them, `declared()` raises for both, and no data was approximated.

## 5. Freeze rule: supersession history
Every pre-opening change that touched pinned code produced a **new** freeze. The previous one was archived byte-for-byte, its witness was left unmodified, and a reason was recorded:

| # | Anchor | Why superseded |
|---|---|---|
| 1 | `27b3463f…` | registry defects (A6d / A10b / X1), 2026-09-27 UTC |
| 2 | `f2dc4ffb…` | builders, trial layer, execution hardening, sensitive-cut certification, R1 checkpoint |
| 3 | `faac4c86…` | final audit A30b: a raw `FileNotFoundError` on a missing protocol file; registry hardened |
| 4 | `88b7688b…` | evaluation driver pinned before opening (its audit was clean) |
| **final** | **`6090be68…`** | **authoritative** |

Protocols, periods, universe and counts are identical across all five freezes. Exactly one campaign is authoritative.

## 6. Adversarial registry audit (scratch copy only)
Evidence: `adversarial_v2_final/attack_results.txt` and the harness `attack_registry_v2_final.py.txt`.

**Final run: 70 attacks, 70 EXPECTED_REJECTION, 4/4 LEGITIMATE_CONTROL_ACCEPTANCE, 0 DEFECT.** The real registry (tree `de0c101a…`) and witness (`05d4544b…`) were byte-identical before and after.

Coverage:
- **Protocol:** modification, hash substitution, deletion of a leakage rule.
- **Campaign:** modification; trial-count manipulation; a universe forgery verified with a forged anchor.
- **Dates:** OOS moved into the past, and moved to 2026-10-05.
- **Relabelling:** OOS as VAL, DEV or WF; VAL as OOS; DEV as VAL; EXCLUDED as DEV.
- **Budgets:** repeated OOS; repeated VAL; VAL budget reset; VAL after OOS.
- **Selection timing:** early OOS; partial OOS; selection after the OOS start or without VAL; in-sample after sealing; OOS of an unsealed trial.
- **Ledger and witness:** ledger truncation; ledger rewrite; witness rewrite, deletion and substitution.
- **R1:** consistent ledger + witness rollback, and a consistent forged append, both tested against the published checkpoint.
- **Pins:** data, code and design hash modification; results bound to an unpinned data or code set.
- **Universe membership:** sensitivity outside the grid; a hidden axis; an undeclared symbol; blocked F4 and F6.
- **Certificates and causality:**
  - a forged certificate dict;
  - a forged certificate injected into ledger + witness;
  - a future-data builder;
  - future calendar information (release value early; full-sample surprise sd);
  - an uncertified leaky builder used in a result;
  - source modified after certification;
  - registration after opening.
- **Timezone and timing:** offset timestamp; naive timestamp; unparseable timestamp; an offset disguised with "Z"; embargo and purge violations.
- **Malformed input:** invalid JSON; missing fields; a corrupt campaign; a missing protocol; a pinned file replaced by a directory; a malformed window.
- **Registry-level:** whole-registry rollback; inconsistent anchor (incl. a rewritten `ANCHOR.txt`); inconsistent ledger head (wrong sha, stale seq); open without a checkpoint or without an approval note; record while FROZEN; re-freeze; open after REJECTED.

Earlier runs found **genuine defects, all fixed and re-audited**:
- 2026-09-27: A6d, A10b, X1.
- This run: A30b (a raw exception on a missing protocol file), plus the proactively found raw-exception paths in `parse_utc`, pinned-path-as-directory and malformed `window_utc`.

One run reported A25 as a DEFECT because the harness called a function before defining it. That was a harness bug; it was fixed, and A25 is now rejected.

## 7. R1 trust boundary
**The limitation.** Hashes on this machine cannot stop a local actor from rewriting the ledger and witness consistently. This is not claimed otherwise.

**The control, now enforced in code.** Every mutating call requires the **externally published** ledger head (compare-and-swap):
- the checkpoint must exist in the ledger, otherwise the call is treated as a rollback or rewrite and refused;
- the ledger must have no entries beyond it, otherwise they are unpublished or forged and the call is refused.

`verify(anchor, checkpoint)` pins the local ledger to the published head. Attacks A17, A18, A32 and A35 show this rejects consistent rollbacks and forgeries. Control C2 documents that a local-only `verify` cannot see R1.

**The procedure** is in `V2_EXTERNAL_CHECKPOINT_PROCEDURE.md`, which is pinned. The current heads are recorded in this conversation, which is off-machine. **The residual gap is human:** there is no Git remote yet, so the checkpoint must also be written somewhere this machine cannot rewrite.

## 8. Statistical governance (verified)
- **Active trials: 1,632.** F1 216; F2 72; F3 H3a 48; F3 H3b 864; F5 432.
  - Sensitivity values are enumerated as trial dimensions: F2 `asian_end_utc_hour` 5/6/7, F3 `fill_rule` touch/through_1pt/through_2pt, F5 `session_start_utc_hour` 22/23/0.
- **DSR count:** 1,740 (1,632 + 108 legacy).
- **BH-FDR primary tests:** 17.
  - F1 × 4 symbols;
  - F2 × XAUUSD;
  - F3 H3a × 4 and F3 H3b × 4, which are separate claims;
  - F5 × 4.
- **The universe is closed.** It is re-derived from the pinned protocols on every call. Any config, symbol, axis or blocked-family trial outside it is rejected (A22–A23c), and so is any silently added trial (A01, A05).
- **One OOS per (experiment, claim, symbol).** It is sealed before the OOS start and scored only after the OOS end. The VAL budget is 1 and cannot be reset (A12, A13, A17). OOS cannot be relabelled, and DEV cannot become VAL (A07–A10c). Selection cannot see OOS (A13b, A13e).
- **Selection rule (pinned):** the highest VAL one-sided 95 % stationary-bootstrap lower bound among trials with ≥ 30 VAL observations; ties go to fewer parameters, then to `trial_id`.
- **Verdict (pinned):** PASS_CANDIDATE only if **all** of these hold:
  - n ≥ 200;
  - IUT p ≤ 0.05 (bootstrap and every null);
  - BH-FDR q = 0.10 across all 17;
  - DSR ≥ 0.95 at N = 1,740;
  - PBO ≤ 0.5.

  Anything else is NOT_DEMONSTRATED.
- No parameter was optimised, no strategy was run on market data, and no result was inspected.

## 9. Clean OOS
- **Periods.**
  - EXCLUDED: `[2025-01-01Z, 2027-01-04Z)`
  - Prospective OOS: `[2027-01-04Z, 2028-01-03Z)`
- **No historical use is possible.** The latest bar in the repository is 2026-09-25 20:53 UTC, and today is 2026-09-29, so no OOS data exists yet.
- **No overlap.** DEV `[2018, 2023)`, VAL `[2023, 2025)` and WF 2020–2024 all end on or before 2025-01-01, before both the EXCLUDED period and the OOS.
- **Early access is blocked.** The registry refuses OOS before its end, a partial OOS window, and OOS relabelled as any other period (A13c, A13d, A07–A10b).
- **Warm-up for OOS (pre-registered in the driver).** Up to 100 days of trailing bars from the end of EXCLUDED are read as trailing inputs only, at OOS evaluation time after the OOS has ended. They produce no signal, order or result.

## 10. Macro / calendar (F1)
- **Provenance.** MT5 `CalendarValueHistory` export, 2026-09-27, Pepperstone-Demo, with a pinned raw export and provenance. Times use the **export-time offset**, never the bar clock.
- **Independent recount: 4,524 of 8,586 HIGH rows are eligible**, with an identical row set on recomputation.
  - HIGH first print: 6,776 CONFIRMED, 1,809 UNDETERMINED, 1 REVISED_VALUE.
  - HIGH time_mode: 8,306 DATETIME, 201 DATE, 79 TENTATIVE. Date-only and tentative rows are excluded.
  - Eligible rows have 0 missing forecast or actual values, 0 non-exact timestamps and 0 non-indicator rows.
- **NFP clock.** 115 of 116 releases at 08:30 New York. The 2025-11-20 release (07:30 local, prior mode 08:30) is `local_clock_off_prior = True`, so it is **excluded**.
- **Causality.** Baselines are prior-only and certified. The full-sample variant fails certification.
- **Selection effect (disclosed).** `first_print` is a *provenance* label that uses the **next** release's `prev`. Excluding UNDETERMINED rows therefore conditions the historical sample on later information about revisions. It is not a feature and it is protocol-mandated. It can bias DEV/VAL, and it does not affect the prospective OOS, where first prints must be logged live.
- **Pre-registered currency-sign map.** Unemployment and claims indicators get −1. EIA crude stocks and BoJ L money stock get 0 and are excluded, as having no conventional currency sign. Unlisted codes are excluded. The map rests on economic convention, not outcomes; only event metadata was inspected.

## 11. Timezone / execution
- **Time convention** (checked on real EURUSD M1 timestamps only):
  - 490 weekly opens fall at New York Sunday 17:00–17:02 (server Monday 00:00–00:02).
  - Server−UTC offsets are exactly {+2 h: 1,146,361 bars; +3 h: 2,285,118 bars}.
  - This confirms server = New York + 7 h with US DST.
- **Execution engine** (`nexa_execution.py`):
  - Market orders fill at the next bar open ≥ decision + 250 ms (bar mode).
  - A LIMIT fills only on trade-through; `through_points` is 0, 1 or 2 per `fill_rule`, so "touch" appears only as a declared sensitivity.
  - A STOP entry fills at max(level, ask) + slippage.
  - When both stop and target are hit in one bar, the stop wins. Gaps fill at the open.
  - Commission is $3.50 per lot per side. Slippage is 0.5 × spread (× 3 for F1 events). Swaps are only ever charged.
- **Execution hardening in this run:**
  - After an intrabar LIMIT/STOP fill, the fill bar can no longer hit the target or add MFE (previously optimistic).
  - `max_hold` is measured from the fill.
  - Pending orders are cancelled when a bar closes beyond the invalidation level.
- **Known limits.** Bar spread is MT5's recorded M1 spread and may understate release-second spreads. Intrabar path is unknown before 2026-08-28. Swaps are a 2026-09 snapshot, so only charges are applied. All stressed per the protocol (cost, latency and missed-fill shocks).

## 12. MQL5 systems audit (read-only; no MQL5 file modified)
| ID | Area | Finding | Severity | Fix path |
|---|---|---|---|---|
| M1 | Multi-symbol sync / risk | `PearsonCorrelation` (`NEXA_Risk.mqh`) aligns symbols **by shift, not time**. An unsynchronised symbol (`iClose` = 0) sets returns to 0, and fewer than 3 valid bars return **0 correlation**, so the correlation cap **fails open** on missing history. | **HIGH** | `NEXA_Risk.mqh` is frozen, so this is a human decision. Proposed: time-aligned reads plus `SERIES_SYNCHRONIZED` checks, with fail-closed (block) on insufficient data. The AlgoBook prior art uses same-time checks across symbols. |
| M2 | Time (D-TZ) | `InpGMTOffset = 2` is fixed, but the broker is NY+7 (UTC+2/+3). Session filter, hard close and GMT tags are 1 h off during US DST. | MEDIUM (open defect D-TZ) | human decision; `NEXA_Common.mqh` |
| M3 | Tester reporting | No `OnTester()` / custom criterion. The tester result is not machine-readable beyond the Trade DNA CSV. | LOW | add an R-expectancy `OnTester` (engineering; the EA is outside V2) |
| M4 | Tester multi-symbol | Cross-instance risk state lives in terminal GlobalVariables. A single-symbol tester run cannot exercise portfolio caps, and cross-symbol `iClose` triggers history sync. This is the earlier tester stall. | MEDIUM | multi-symbol tester harness, or document as untestable in the tester |
| M5 | Order validation | No `OrderCheck()` before send. Lot sizing uses `OrderCalcProfit`, and the margin cap exists. | LOW | optional pre-send `OrderCheck` |
| M6 | Freeze level | `SYMBOL_TRADE_FREEZE_LEVEL` is not checked before modify/close (stops level is checked). Pepperstone freeze level is 0 today. | LOW | check before `PositionModify` |
| M7 | Partial fills | Risk is sized on the requested volume, so a partial fill means **lower** actual risk (safe direction). Partial OUT deals are handled via deal history. | OK | — |
| M8 | Duplicate prevention / recovery | In-flight GlobalVariable guard with timeout; ambiguous retcodes never retried; async rejection path; stops re-applied if missing; stops only ratchet one way. | OK (strength) | — |
| M9 | Normalisation | Volume step/min/max handled with a hard ceiling. Stops-level check on setup. Deviation fixed at 20 points for every symbol (2 pips FX, $0.20 XAU). | LOW | per-symbol deviation |
| M10 | Hedging vs netting | `ACCOUNT_MARGIN_MODE` is read; the account is hedging. The magic-filtered single position per symbol is compatible with both. | OK | — |
| M11 | Exposure cap | `InpMaxSameCurrencyNet = 2` × min-lot makes NEXA untradeable above about $1.3k equity (B-EXPOSURE-CAP). | BLOCKER (live) | human decision; hard risk parameter, **not changed** |

**Compilation:** no MQL5 source was modified in this run, so no compile was required and none is claimed. The last compile results (0/0) are from earlier sessions.

## 13–16. Prior art and backlog
See `NEXA_COMMERCIAL_EA_PRIOR_ART_AUDIT_2026.md` and `NEXA_FUTURE_RESEARCH_BACKLOG.md`.
- 14 sources were reviewed. The Scribd body is behind a login and XenClarity is not independently verified.
- The Apex Drawdown Zero primary and secondary sources conflict.
- No performance claim was verified.
- The AlgoBook example itself scales lots after losses. It is rejected as martingale-type, and only its architecture is taken.
- **V2 is unchanged by the prior art.**

## 17. Architecture gap audit
See `NEXA_ARCHITECTURE_GAP_AUDIT_2026.md`.

## 18. Regression
- `cd research && python -m pytest -q`: **446 passed**, 1 pre-existing warning (from an intentional infinite-value test in `test_nexa_validate.py`).
- `python -m ruff check .`: **All checks passed.**
- No test was weakened, skipped or deleted.
- One vacuous assertion I had written (`or True`) was replaced by a real bound before the freeze.

## 19. Final integrity check
1. **No V2 evaluation performed.** ✔ No builder, trial or driver was run on market data. Only synthetic data was used; the real-data reads were timestamp and calendar-metadata audits.
2. **No V2 result recorded.** ✔ 0 rows.
3. **No OOS result exists.** ✔
4. **No broker data newly downloaded.** ✔ No history-base file modified since 2026-09-28. See §20 for the size difference.
5. **No trade placed.** ✔ No trading tool was called; MT5 is not running.
6. **`MTM_ENABLE_TRADING=false`.** ✔
7. **`MTM_ENABLE_EXEC=false`.** ✔
8. **`NEXA_Risk` hard invariants unchanged.** ✔ Byte-identical to the baseline.
9. **Schema v1.0 unchanged.** ✔
10. **f00–f47 unchanged.** ✔
11. **F4 BLOCKED.** ✔
12. **F6 BLOCKED.** ✔
13. **OOS = [2027-01-04T00:00:00Z, 2028-01-03T00:00:00Z).** ✔
14. **EXCLUDED = [2025-01-01T00:00:00Z, 2027-01-04T00:00:00Z).** ✔
15. **Exactly one authoritative anchor.** ✔ `6090be68…`; four superseded archives are labelled.
16. **Witness agrees with the registry.** ✔
17. **Scratch attacks cannot mutate the real registry.** ✔ Byte-identical before and after.
18. **Builders pass causality checks.** ✔ Six registered, and leaky variants fail.
19. **Full regression passes.** ✔ 446 passed.
20. **Ready for a future human "OPEN V2" instruction.** ✔ V2 remains **closed**.

## 20. Remaining blockers and open items (exact)
1. **Human approval to open.** `open_evaluation` requires an explicit approval note plus checkpoint seq 6 `bbd9a28e…5b2b`.
2. **Off-machine checkpoint (R1).** Record the anchor and seq-6 head somewhere this machine cannot rewrite. There is no Git remote yet, so creating one and pushing is a human action.
3. **Timeline.** No V2 claim can be promoted before 2028-01-03 plus scoring. The OOS must still be *collected*: Pepperstone M1 and spreads for 2027, logged after the freeze.
4. **F1 OOS first prints must be captured live.** The calendar logger is not yet deployed.
5. **F4 BLOCKED** (no second synchronous tick feed). **F6 BLOCKED** (needs sufficient post-freeze tick data).
6. **M1 (HIGH):** the correlation cap fails open on missing or unsynchronised history (`NEXA_Risk.mqh`, frozen). This needs a human decision; it does not affect V2, which is research-only.
7. **Live-trading blockers outside V2 (human decisions):** B-EXPOSURE-CAP, D-TZ, and coexistence of F1 with NEXA's news veto and FOMC gate.
8. **Disclosed limitations (not blockers):**
   - the first-print selection effect;
   - swap snapshot only (charges only);
   - bar-mode fill realism;
   - bar spread may understate event spreads.
9. **History-base size.** It was 24,891,040 KB in the Phase-2 report and is 25,113,084 KB now. The newest base files are dated 2026-09-27 23:36 local, the calendar-export session. Nothing has been modified since 2026-09-28, so the growth predates this run.

```
READY FOR HUMAN OPENING APPROVAL = YES
(conditions: items 1-2 are human actions; V2 is NOT opened; nothing was evaluated)
```
