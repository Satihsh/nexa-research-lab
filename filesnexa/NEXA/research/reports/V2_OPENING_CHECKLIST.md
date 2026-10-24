# PHASE3_SIX_FAMILIES_V2: OPENING CHECKLIST

**DO NOT OPEN THIS CAMPAIGN UNTIL HUMAN APPROVAL IS PROVIDED.**

State at 2026-09-29: **FROZEN**, not opened, not evaluated.
- Anchor `6090be68184af7643f82b680d144a1b9e1622b3bbceebfb872729b97b9d9324c`
- Published head seq 6 `bbd9a28ed6bc7e0b20f3fca9f9ba1fe437f4bd39dc9c1e99ed73fb7505be5b2b`

## A. Before any opening (human)
- [ ] An explicit human instruction "OPEN V2" is given, with a written approval note (≥ 20 characters) stating who approves and why.
- [ ] The anchor and seq-6 head are recorded **off this machine** (Git remote tag, email or printed note), and the checkpoint used below is copied **from that record**.
- [ ] Human decisions acknowledged. None blocks research, but each blocks live trading:
  - B-EXPOSURE-CAP;
  - D-TZ;
  - M1 (the correlation cap fails open);
  - F1 versus the news veto and FOMC gate.
- [ ] Trading flags confirmed `MTM_ENABLE_TRADING=false` and `MTM_ENABLE_EXEC=false`. Opening V2 is research; it never enables trading.

## B. Verification immediately before opening
```bash
cd research && ../.venv-research/bin/python -m pytest -q
```
```bash
cd research && ../.venv-research/bin/python -m ruff check .
```
```bash
cd research && ../.venv-research/bin/python -c "import nexa_registry2 as r2; reg=r2.RegistryV2('registry_v2'); print(reg.checkpoint_line('6090be68184af7643f82b680d144a1b9e1622b3bbceebfb872729b97b9d9324c', {'seq': 6, 'entry_sha256': 'bbd9a28ed6bc7e0b20f3fca9f9ba1fe437f4bd39dc9c1e99ed73fb7505be5b2b'}))"
```
- [ ] All tests pass; ruff is clean; the verify line prints `seq=6 … state=FROZEN`.
- [ ] `NEXA_Risk.mqh` = `e706d453d346100f`. Schema, f00–f47 and the baseline are unchanged.

## C. Opening (only after A and B)
- [ ] `reg.open_evaluation(anchor, approval_note, checkpoint={"seq": 6, "entry_sha256": "bbd9a28e…5b2b"})`
- [ ] Publish the returned `(seq 7, entry_sha256)` off-machine **before** any further call.

## D. After opening (rules the registry enforces; listed so nobody tries to bypass them)
- DEV and WF are free for development. **VAL is one query per trial.**
- Results come only from `nexa_v2_runner.run_group` → `record_all` (pinned, no free parameters). Publish the head after every call.
- Selection is the pinned rule: one sealed trial per (experiment, claim, symbol), **before 2027-01-04T00:00:00Z**.
- The EXCLUDED period `[2025-01-01Z, 2027-01-04Z)` is never used for anything.
- **OOS:** collect 2027 data after the freeze. Score **once**, after 2028-01-03T00:00:00Z, on the full window.
- The final verdict is `nexa_v2_trials.primary_verdicts`. Anything short of PASS_CANDIDATE is NOT_DEMONSTRATED; no re-tuning is allowed.
- A PASS_CANDIDATE still needs, before any live use:
  - an MT5 Strategy Tester replica;
  - shadow mode;
  - the promotion gate;
  - `NEXA_Risk.mqh` limits unchanged.

## E. Never
- Never open a superseded freeze (27b3463f, f2dc4ffb, faac4c86, 88b7688b) or V1.
- Never edit pinned files after opening. That breaks verification and invalidates the campaign.
- Never add trials, change dates, relabel periods, or re-query VAL or OOS.
- Never treat zero trades or NOT_DEMONSTRATED as a failure to be fixed. They are valid outcomes.
