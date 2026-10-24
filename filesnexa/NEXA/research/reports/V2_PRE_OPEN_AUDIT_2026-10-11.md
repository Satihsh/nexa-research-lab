# PHASE3_SIX_FAMILIES_V2: pre-open audit (read-only), 2026-10-11

**Requested by the user:** "V2 pre-open audit".

**Constraints honoured:**
- No registry mutation, no `open_evaluation`, no pinned file edited, no `freeze_*.py` call.
- No trading flag changed; MT5 not touched (the S14 forward check runs on the GCP VM).

**Verdict: TECHNICALLY READY TO OPEN.** All integrity checks pass. Three items need a human decision before or soon after opening (§3).

## 1. Integrity (checklist §B)

| Check | Result |
|---|---|
| Off-machine record (claude.ai artifact 6o1hnw9d…, recorded 2026-10-02) | anchor `6090be68…9324c`, head seq 6 `bbd9a28e…5b2b`, FROZEN · NOT OPENED |
| `RegistryV2.verify(anchor, checkpoint = off-machine seq 6)` | **PASS**: `state=FROZEN`, 7 ledger events, 1,632 trials |
| Pins re-hashed by `verify` | **14 data + 23 code + 5 design = 42, all unchanged**; 6 protocols and the trial universe match their pins; results chain empty |
| Witness `~/.nexa_registry_witness/6090be68….jsonl` | last line seq 6 `bbd9a28e…` (matches) |
| `pytest -q` (research) | **634 passed** (628 at the freeze; 6 tests added since) |
| `ruff check .` | All checks passed |
| Re-verify after the test run | PASS (the tests did not touch `registry_v2`) |
| Trading flags (Claude Desktop meta-trader-mcp config) | `MTM_ENABLE_TRADING=false`, `MTM_ENABLE_EXEC=false` |

## 2. Stale lines in `V2_OPENING_CHECKLIST.md` (not pinned; documentation only)

| Checklist line | Current fact | Effect on V2 |
|---|---|---|
| "`NEXA_Risk.mqh` = `e706d453d346100f`" | It is now `a43d8328…`, after the human-approved S11 fail-closed exposure cap and the C4 pre-trade daily-loss budget (2026-10-03). | **None.** `NEXA_Risk.mqh` is **not** in the 42 V2 pins (verified programmatically): V2 is Python research only. Before opening, acknowledge `a43d8328` as the approved hash. |
| Human decisions B-EXPOSURE-CAP, D-TZ, M1 (correlation cap fail-open) | All decided or fixed: cap unchanged (2026-10-03); D-TZ fixed (D48); correlation cap fail-closed (2026-09-29). | None for research. |
| F1 versus news veto / FOMC gate | Still open (protocol `architecture_note`). | Production design only; it does not block research. |

## 3. Items needing a human decision

1. **F1 OOS live first-print capture: NOT BUILT.**
   - **Requirement:** protocol F1 (pinned) says "OOS: first prints must be captured live at release (calendar logger)".
   - **Current state:** no calendar logger exists; NEXA has only `NEXA_TickLogger`.
   - **What it needs:**
     - a small data-only MQL5 logger that records MT5 calendar `actual`/`forecast`/`prev` at release time (new code: approval required; no trading);
     - running continuously **2027-01-04 → 2028-01-03** on an always-on terminal, live before 2027-01-04.
   - **Without it:** F1 OOS first-print status can only be reconstructed historically, which the protocol declares insufficient. F1's 216 trials would face a contested or NOT_DEMONSTRATED OOS.
   - **Alternative:** accept that F1 will likely be NOT_DEMONSTRATED. F2, F3 and F5 (1,416 trials) do not need it.
2. **2027 always-on infrastructure.**
   - The S14 VM is scheduled for tear-down by 2026-12-08, and the GCP credit expires 2027-01-10.
   - A 2027-long logger needs a host: Linux + Wine on GCP ≈ RM110–125/month ≈ RM1,400–1,500 for 2027 (real money after the credit ends), or another always-on machine.
3. **OOS price data.**
   - After 2028-01-03, export Pepperstone M1 for 2027 for the 4 core symbols with the existing canonical pipeline (`tools/pepperstone_*.py`). This needs an MT5 terminal (approval) and should avoid the D1-download trap.
   - Score once with `nexa_v2_trials.primary_verdicts`.

## 4. Schedule if opened

| Milestone | Deadline |
|---|---|
| "OPEN V2" + approval note (≥ 20 chars, who/why) + checkpoint from the off-machine record; publish seq 7 off-machine immediately | any time; practical latest ≈ 2026-12-01 |
| DEV (free) / walk-forward + VAL (one query per trial / trial-year) via `nexa_v2_runner.run_group → record_all`; republish the head after every call | ≈ 2–4 weeks (compute: local, no data purchase) |
| OOS_SELECTED sealed per (experiment, claim, symbol) | **before 2027-01-04T00:00Z** (registry-enforced) |
| F1 calendar logger live (if F1 is kept) | before 2027-01-04 |
| OOS year | 2027-01-04 → 2028-01-03 |
| Single OOS scoring | after 2028-01-03 |

## 5. Honest prior (unchanged by this audit)

This audit checks readiness, **not** expected edge. Evidence gathered after the freeze points against intraday retail-cost edges:
- C1, IM1 and FX1 were gross-positive but net-negative;
- the NEXA rule set returned −0.318R per trade;
- 8E had no DSR pass.

The most plausible V2 claim is **F3 H3b (limit entry at FVG zones)**, because limit entries avoid the entry spread. The expected outcome remains NOT_DEMONSTRATED for most claims.

## 6. Outcome: OPENED 2026-10-11 15:57:24 UTC

- **Approval:** the user's explicit instruction "OPEN V2 with option B" (no F1 live logger).
- **Immediately before opening:** pytest 634 passed; ruff clean; verify with the off-machine seq 6 checkpoint passed.
- **Event:** `open_evaluation` appended seq 7 EVALUATION_OPENED `df1f54cd847a7b08f4ab8b4f108a9306b651af77ae487f47d0b744d2561a2906`. The witness matches; re-verify with the seq 7 checkpoint passes (state OPEN).
- **Off-machine record:** updated (claude.ai artifact 6o1hnw9d…, version 2) before any further registry call.
