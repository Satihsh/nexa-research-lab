# H-ORB30L-REPL Part A-H report: HistData NSXUSD parity gate FAILED, so NOT EVALUABLE

**Date:** 2026-10-16.
- **Pre-registration:** `PREREG_HORB30L_REPL_HISTDATA.md` (3dcb7991), amending `PREREG_HORB30L_REPL_DUKA.md` (55fe9e68) and `PREREG_HORB30L_REPL.md` (758f8a31).
- **Code:** `horb30l_histdata_oos.py` (5189d197), frozen before download.
- **Data:** 14 HistData zips 2010–2023, `MANIFEST.json` committed in 59dc42a before parity.
- **Parity output:** `horb30l_histdata_parity.json` (opened once).

## Verdict

**NOT EVALUABLE.** The pre-registered parity gate failed on all four criteria, so **the OOS stage was not run and no day before 2023-02-18 was read.** The parity file says PASS = false, so `--stage oos` refuses to run. H-ORB30L keeps its in-sample status: **INCONCLUSIVE** (+0.058 R at S1, DSR fail).

## Parity: 2023-02-21 → 2023-12-29, in-sample, HistData bid vs NQ (Databento), same frozen engine

| Check | Result | Threshold | Pass |
|---|---|---|---|
| P1 same status | 0.757 (78 / 103 days) | ≥ 0.80 | ✗ |
| P2a same entry minute (days both trade) | 0.467 (21 / 45) | ≥ 0.75 | ✗ |
| P2b same exit kind | 0.733 | ≥ 0.75 | ✗ |
| P3 net-R correlation | 0.743 | ≥ 0.75 | ✗ |

**Descriptive (not decisive):**
- Same window, the rule earns **−0.113 R** on HistData (63 trades) against **+0.163 R** on NQ (52 trades).
- Of the trades, 18 days trade on HistData only and 7 on NQ only.
- Entry-minute differences on days both trade are multiples of 5 minutes (from −55 to +65). The 5-minute breakout close falls in a different candle in more than half the trades.
- The median level offset (bid − NQ at 10:00) is **−82.6 points**. This is consistent with HistData NSXUSD tracking the cash index rather than the future; it does not affect R.

**Data quality, 2023 window (descriptive):**

| Weekdays | Calendar | Range or 15:29 bar missing | Stale (≥ 20 % missing / flat) | Used |
|---|---|---|---|---|
| 223 | 10 | **74** (60 days with the whole 09:30–09:59 range absent) | **36** | 103 |

HistData's NSXUSD feed is incomplete around the US cash open in 2023. Only 48 % of eligible weekdays were usable.

## Interpretation, kept short

- A proxy where the rule's own signal (which 5-minute candle breaks out) agrees with NQ in under half of the trades cannot test the NQ result. The gate did exactly what it was written to do.
- **Nothing here says the rule fails out of sample. Nothing says it works.** The only evidence remains the in-sample INCONCLUSIVE and the forward log (Part B).
- **Not done, by pre-registration:** no clock shifts, no alternative day filters, no re-run with different thresholds. Any such change after seeing the parity result would be a new, separately pre-registered test, and the 2023 parity days are now spent.

## Remaining free routes to an OOS test (each needs the user's decision)

1. A JForex desktop export of Dukascopy USATECH M1 (the user declined installing it for now). Part A-D is frozen and ready.
2. QuantConnect after the user verifies the account with a card (the free tier says no charge). The code is hash-verified in project 37866267.
3. Otherwise only Part B (prospective): about 9–10 months to 100 forward trades.
