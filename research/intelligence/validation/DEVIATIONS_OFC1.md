# OFC1 deviations and implementation notes (fixed before discovery opened; hashed with the code)

Each item below covers something the pre-registration (`PREREG_OFC1_CORE_ORDERFLOW.md`, sha ede1bc8d…) did not specify, or specified inconsistently. **No OFC1 outcome had been computed when these were fixed.** The only engine output seen was the D9 smoke test: trade counts and exit kinds on warm-up sessions, outside every split.

| # | Item | Resolution | Reason |
|---|---|---|---|
| **D1** | Roll handling vs §2 / §11.8 | **Q-valid** session = not the first of the data, not thin, not touching a degraded date. History (big-trade thresholds, volume baselines) and the **prior profile** use Q-valid sessions. The prior profile = the most recent earlier Q-valid session. A **roll** (prior profile on a different instrument_id) skips **scoring only**. Roll sessions stay in history and can be a later session's prior profile | Excluding roll sessions from history and profiles, as §2 and §11.8 read literally, would cascade: after a roll, every session's prior profile would be on the old contract, so no session could ever be scored again |
| D2 | Re-entry timing | After an exit, setup tracking restarts from the minute after the exit minute | §4 "re-entry after exit" gives no timing |
| D3 | Price of levels | VAL = the first tick of the lowest VA row; VAH = the first tick above the highest VA row (`of_common` row boundaries). The LVN target = the row midpoint rounded to a whole tick **toward the entry** (short target below: ceil; long target above: floor) | Row midpoints are half-ticks for 2-tick rows |
| D4 | Pending after a non-trade | A cost-floor skip, or a stop on the wrong side, **ends** the pending (a triggered-but-skipped setup). "Target not beyond the entry" keeps the pending (§11.5). Setup B / B′ ends the pending in all cases (§4) | §5 / §11 are silent on the cost-floor case |
| D5 | Bootstrap units | Calendar session dates with ≥ 1 trade, pooled across instruments, in date order (moving block of 5 dates) | §6 says "sessions" |
| D6 | Placebo entry minutes | Minutes with trades in the session, excluding the session's last minute | §6 "trading-window minutes" |
| D7 | Trade order and orders | Sorted by (ts_event, side, sequence). An aggressor order = consecutive records with equal (instrument_id, ts_event, side) | Equivalent to `big_trades.py`'s group-by |
| D8 | Context test | Inside value means VAL ≤ close ≤ VAH, in ticks | — |
| D9 | Smoke test | Before hashing: GC and 6B engine runs on warm-up sessions (2025-09/11, not in any split) with temporary 25-session thresholds. Only trade counts and exit kinds were printed (6B 1 trade / 33 sessions; GC 24 / 32), **no R or P&L**. Peak memory 1.9 GB | Runtime check |
| D10 | Stage execution | A stage simulates only sessions ≤ that stage's end date (disc → 2026-04-30; val → 2026-07-31; full → 2026-09-30) | Opening each split once |
