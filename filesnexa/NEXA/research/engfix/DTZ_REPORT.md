# D48 / D-TZ: DST-aware server clock. Engineering report (2026-10-03)

**Scope:** human-approved option A. `NEXA_Common.mqh` changed, the EA source `NEXA_EA.mq5` (`3edcec11…`) and `NEXA_Risk.mqh` (`1f684cde…`) did not, and the parity oracle mirrors the change. **Not deployed:** `Experts\Advisors\NEXA_EA.ex5` is still `f0ae9618…`.

## Defect
- **Assumption:** the EA used a fixed `InpGMTOffset = 2`.
- **Reality:** the Pepperstone server runs at **New York + 7 h**, i.e. GMT+2 on US standard time and **GMT+3 during US DST** (evidence: `research/reports/TIME_CONVENTION_EVIDENCE.json`).
- **Effect:** from mid-March to early November, every "GMT" hour in the EA was real GMT + 1. That moved:
  - the Asia range, which feeds the liquidity levels and so frozen feature values;
  - the session tag and its **LATE veto** (21–24 GMT);
  - the optional session filter and hard close (both off in production);
  - the FOMC clock (the audit found its margin covered the error).
- **Scale:** 63 % of all server hours from 2000 to 2030, and 68 % of NEXA's journalled decisions, fall in US DST.
- **Research tier:** the Python side was already DST-correct (`nexa_time.py`).

## Fix (`NEXA_Common.mqh` `f4d0a7de…` → `bbf22ee9…`; pre-change copy at `build/dtz_pre_source/`)
- **Offset:** `NexaServerGMTOffsetHours(srv)` = `InpGMTOffset` + 1 h while New York (server − 7 h) is inside US DST. It uses the explicit US rule (2007+: second Sunday of March 02:00 → first Sunday of November 02:00; 1987–2006: first Sunday of April → last Sunday of October), the same as `nexa_time.us_dst_bounds_local`.
- **Single clock:** `NexaToGMT` and `NexaGMTNow` both go through it, so every session, Asia, LATE, FOMC, filter and hard-close decision uses the corrected clock.
- **Why not `TimeGMT()`:** it is not used, because it is unreliable in the Strategy Tester.
- **Inputs:** none added. `InpGMTOffset = 2` now means the standard-time offset. The broker assumption is the constant `NEXA_SERVER_FOLLOWS_US_DST = true`.
- **Oracle mirror:** `nexa_parity.server_gmt_offset_hours`, plus the new `ParityConfig.server_follows_us_dst` (default true) and `--fixed-gmt-offset` for the old clock.
- **Build:**
  - staged copies `build/dtz_src/` → `build/NEXA_EA_DTZ.ex5` (`53439394…`), `NEXA_ClockTest_DTZ.ex5` and `NEXA_CorrCapTest_DTZ.ex5`, **0 errors, 0 warnings** each;
  - the A3, D45, D46 and S11 binaries are untouched.

## Verification
| Check | Result |
|---|---|
| Compiled clock (`NEXA_ClockTest.mq5`, every server hour 2000-01-01 → 2031-01-01; `tester_runs/clock_dtz_20261003/`) | **271,690 / 271,690** well-defined hours equal `nexa_time.utc_offset_hours`. The 62 Sunday switch hours (market closed) all resolve to +3, the same as the Python mirror. |
| Journalled session tags, 12 GBPUSD windows (`engfix/dtz/`, `dtz_regression.py`) | **980,197** tags (668,982 in US DST): **0** mismatches against the true clock in the D-TZ build, and **0** against the old fixed clock in the S11 baseline. This is the runtime proof that the EA now runs on real GMT. |
| Where behaviour changes | The first divergence is inside US DST in **every** window. Winter-start windows are identical until the first trading hour after the March switch (2024-03-11, 2025-03-10, 2026-03-09). |
| LATE veto | 0 D-TZ trades open in real 21–24 GMT, against 2 in the baseline. |
| Behaviour change (expected, reported) | 169,149 keyed rows differ, 1,408 only in the baseline, 1,089 only in D-TZ. Trades 525 → 561. These are differences in a rule set with no edge; nothing here is an edge claim. |
| Window-B parity: D-TZ journals, all 4 symbols, DST-aware oracle (`reports/pepperstone/B_PARITY_DTZ_VERIFY_WINDOW_B.json`) | **PASS** on all 4 symbols. 0 mismatches. All 47 reviewed ties matched, 0 unused. |
| Full suite | **614 passed**; ruff clean |

**Note on the XAUUSD parity row count** (26,685 against 27,235 in the stored report): this regression trades with $200 under production inputs. On 2026-09-24 the 2 % daily-loss emergency stop fired, so the EA logs no decisions for the rest of that day (550 rows). The stored production journal had no trades. Every journalled row passes.

## Consequences
- **Earlier NEXA evidence describes the old clock:** the cap-neutral Gate 8 (NEGATIVE_EXPECTANCY), the D45, D46 and S11 regressions, and the stored window-B parity report. Their source pins (`NEXA_EA.mq5`, `NEXA_Risk.mqh`) are unchanged, so their tests still pass; the claims they back are about the rule set as it was run.
- **Stored report:** `PEPPERSTONE_PARITY_FULL_B.json` still reflects the old clock and the old oracle (`a4bf9f93…`); the oracle is now `728c4631…`. Replacing it with the D-TZ result needs approval.
- **Tests updated:** `test_nexa_parity.py`'s RC1 carry-over test now names its fixed clock explicitly (`us_dst=False`). It tests carry-over, not the clock.
- **Deployment:** still needs separate approval.
