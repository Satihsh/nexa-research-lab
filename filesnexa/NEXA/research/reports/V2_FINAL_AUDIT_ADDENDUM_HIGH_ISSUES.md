# Final audit addendum: two HIGH issues (NON-PINNED, read-only investigation, 2026-09-29)

This addendum is **not** a pinned artifact.
- **No file was modified** in `NEXA_Risk.mqh`, the V2 campaign, its protocols, universe, dates or anchor.
- **No evaluation was run.** There was no V2 evaluation, no F1 evaluation, and no strategy or OOS result.
- **Data read:** real data was read for two things only. For issue 1, M1 bar **timestamps** (no prices). For issue 2, calendar **metadata and actual/forecast/prev values** (no prices, no returns).
- **Evidence script:** `addendum_evidence/corr_cap_sim.py.txt` (synthetic data only).

---

## Issue 1: `NEXA_Risk.mqh` correlation cap fails OPEN

**Classification: LIVE-TRADING SAFETY DEFECT, severity HIGH.** It does not affect V2, which is research-only and never executes the EA.

### 1.1 Exact mechanism
The code is `NEXA_Risk.mqh` lines 174–219 (hash `e706d453d346100f`, unchanged).
- **Call:** `CorrelationCapOK(newSymbol)` loops over **all** open positions. For each other symbol it calls `PearsonCorrelation(newSymbol, psym, InpCorrelationBars=100)` and blocks only if `|corr| >= InpMaxCorrelation (0.75)`.
- **Series construction.** `PearsonCorrelation` reads both series with `iClose(sym, PERIOD_CURRENT, i+1 / i+2)`. It pairs bars **by shift index, not by bar time**, and never checks `SERIES_SYNCHRONIZED`, `Bars()`, `CopyRates` counts or `GetLastError()`.
- **Error value.** `iClose` returns **0 on error**, per the MQL5 documentation. The function turns any pair with a zero price into a zero return pair, and it can return **0** from three places:
  - fewer than 3 valid pairs (`valid < 3`);
  - zero variance;
  - a non-finite result.
- **Fail-open.** A return of 0 means "uncorrelated" to the caller, so **every data failure passes the cap**.
- **Unreadable position.** `PositionGetSymbol(i) == ""` is skipped (`continue`), which also passes.

### 1.2 Affected execution paths
There is exactly one call site: `NEXA_EA.mq5:481` in `ExecuteSignal`, the **only new-entry path**. The gate order there is:

1. `AdversarialCheck`
2. `StrategySurvivalOK`
3. AI veto
4. TP
5. lot sizing
6. `ExposureCapOK` (line 479)
7. **`CorrelationCapOK`** (line 481)
8. `PreflightExecutionCheck` (line 484; checks only the traded symbol)
9. `trade.Buy` / `trade.Sell`

No later gate re-checks cross-symbol correlation. Exits and position management do not call it.

### 1.3 Can missing or misaligned history actually bypass the cap? Yes
Reproduced with a line-by-line Python transliteration on **synthetic** correlated series (true shift-aligned correlation 0.872, which BLOCKS):

| Condition | Computed corr | Cap |
|---|---|---|
| aligned, full history | 0.872 | BLOCK |
| other symbol's history absent (`iClose`=0) | 0.000 | **PASS** |
| 10–30 % isolated missing bars | 0.877–0.899 | BLOCK (refuted: zero pairs are removed on both sides) |
| other symbol offset by 1 / 3 / 12 / 60 bars | 0.10 / −0.08 / −0.04 / 0.04 | **PASS** |
| only the oldest 21 of 101 pairs offset by a 60-bar gap | 0.708 | **PASS** |
| oldest 41 / 61 / 81 pairs offset | 0.54 / 0.13 / 0.02 | **PASS** |

**How often shift-alignment breaks in real Pepperstone data.** Measured on 2024 bar **timestamps**: the share of decisions whose last 101 bars do **not** have identical open times in both symbols.

| TF | EURUSD~GBPUSD | EURUSD~USDJPY | EURUSD~XAUUSD |
|---|---|---|---|
| M1 | 1.4 % | 1.4 % | 11.0 % |
| M5 | 0.1 % | 0.5 % | 39.6 % |
| M15 | 0.0 % | 0.0 % | **100 %** |
| H1 | 0.0 % | 0.0 % | **100 %** |

XAUUSD has a daily trading break that FX does not, so any window spanning it is misaligned by shift. At M15 and above, every 101-bar window spans a break.

**Realistic triggers for total absence**
- a position on a symbol that is not charted or not loaded, such as a manual trade;
- history still loading after a restart or reconnect (`iClose` may block or return 0 on first access);
- a symbol missing from Market Watch.

**Why the current exposure cap does not fully mask it.** All four NEXA symbols contain USD, and `ExposureCapOK` (2 × min-lot net per currency) runs first. Two minimum-lot positions in the **same** USD direction therefore pass the exposure cap: for example long EURUSD 0.01 plus long GBPUSD 0.01 gives USD −0.02, which equals the cap. For that pair the correlation cap is the only guard against stacking. If the pending B-EXPOSURE-CAP decision loosens the exposure cap, the correlation cap becomes the primary cross-symbol guard.

**Also untested in the Strategy Tester.** A single-symbol tester run never holds another symbol's position, so this gate has never been exercised by any NEXA tester run.

### 1.4 Recommended fail-closed remediation
This is a future engineering change. It requires explicit human approval to edit the frozen `NEXA_Risk.mqh`, then recompile, tests and tester verification. **Do not change `InpMaxCorrelation` (0.75) or `InpCorrelationBars` (100).**

1. **Tri-state result.** Replace the `double` return with `OK / BLOCK / INSUFFICIENT_DATA`. **INSUFFICIENT_DATA blocks**, with Trade DNA reason `NO_TRADE_CORRELATION_DATA_INSUFFICIENT`.
2. **Time-aligned pairs.** `CopyRates` both symbols over the same closed-bar time window and join on bar **open time**. Compute returns only from consecutive bars present in **both** series; never zero-fill.
3. **Data sufficiency.** Require at least `max(30, 0.8 × InpCorrelationBars)` aligned return pairs. Check `CopyRates` return counts, `SeriesInfoInteger(sym, tf, SERIES_SYNCHRONIZED)` and `GetLastError()`, and call `SymbolSelect(psym, true)` for every position symbol. Any failure → INSUFFICIENT_DATA → block.
4. **No silent zeros.** Zero variance or a non-finite result → INSUFFICIENT_DATA, never 0. `PositionGetSymbol` failure → block.
5. **Stable timeframe (optional).** Compute on a fixed, documented timeframe independent of the chart (e.g. M15, time-aligned) so the cap's meaning does not change with `PERIOD_CURRENT`.
6. **Verification.** Before deployment:
   - a Python parity oracle for the new algorithm;
   - an MQL5 test with an unsynchronised or custom symbol, which must BLOCK;
   - a multi-symbol tester or shadow scenario that actually exercises the gate.

---

## Issue 2: F1 historical first-print selection

**Classification: no look-ahead in any feature VALUE. The event INCLUSION rule conditions on post-decision information.** That is a non-causal selection, independent of prices by construction and empirically tiny in DEV/VAL, but not zero. It is protocol-mandated and left unchanged.

### 2.1 Exactly how later revision information is used
1. `nexa_calendar.first_print_status`:
   - sorts each `event_id` by release time;
   - reads the **next** release's `prev` and `revised_prev` (published about a period later);
   - labels the row CONFIRMED if `actual == next.prev`, REVISED_VALUE if `actual == next.revised_prev ≠ next.prev`, and UNDETERMINED otherwise (including when there is no later release in the export).
2. `nexa_calendar.f1_eligible` requires the row's **own** `first_print == CONFIRMED`. `nexa_v2_features.f1_event_table` uses only eligible rows.
3. `nexa_calendar.prior_only_baselines` builds `prior_surprise_sd` from **earlier** CONFIRMED releases. The confirmation of release e−1 uses release e's `prev`, which is published **together with** release e's actual, so it is available at e's decision time. The certified event builder confirms these baseline columns are causal.
4. The surprise itself, `S = (actual − forecast) / prior_surprise_sd`, uses the row's `actual`. For CONFIRMED rows that is the verified first print.

### 2.2 Legitimate reconstruction versus unavailable information
| Element | Available at decision time (release + Δ)? | Verdict |
|---|---|---|
| `actual` value of a CONFIRMED row | **Yes.** It equals the value later reported as the unrevised `prev`, i.e. the first print a live trader saw | legitimate: later data only *verifies* provenance |
| `forecast`, `prior_surprise_sd`, prior modal clock, schedule | yes (prior-only, certified) | causal |
| **Inclusion flag** (`first_print == CONFIRMED`) | **No.** It needs the next release, weeks later | **non-causal selection** |
| REVISED_VALUE rows (stored actual = a later revision) | the stored value was **not** available at decision time | correctly **excluded**; including them would be true look-ahead |

### 2.3 Survivorship, selection bias, outcome-dependent inclusion
Diagnostics use calendar values only.
- **Candidate pool.** 4,451 releases (USD/EUR/GBP/JPY) pass **every** other F1 filter. 4,403 are CONFIRMED; 48 are excluded by the first-print rule:
  - 39 are the last release of an event in the export (no successor; all after 2024, outside DEV/VAL);
  - 6 have `actual ≠ next.prev`;
  - 1 has no `next.prev`;
  - 1 is REVISED_VALUE;
  - 1 has `actual` missing.
- **Mismatch cause.** All 6 mismatches (Core PCE 2019 ×4, JOLTS 2025 ×2) are **release-ordering artifacts**: US government-shutdown catch-up releases, where the next release by time was not the next reference period. The time-keyed rule mislabels them UNDETERMINED, which is a conservative exclusion.
- **No revision survivorship.** 1,487 of the 4,403 CONFIRMED releases were **later revised** (`next.revised_prev ≠ next.prev`) and are still included. Whether a number was revised is **not** the exclusion criterion.
- **DEV+VAL (2018–2024).** 6 of 3,562 candidates are excluded (**0.17 %**).
  - Surprise magnitude |S|, CONFIRMED vs excluded: Mann-Whitney p = 0.79. The power is low with n = 6.
  - Median |S| over the whole pool is 0.39 for CONFIRMED and 0.23 for excluded.
- **Outcome dependence.** Eligibility uses **no price data**, so inclusion cannot depend directly on the post-release price move.
  - Indirect channel: an erroneous or out-of-sequence release is atypical, so excluding it could make a history slightly cleaner than a live trader's experience.
  - Bound: at most 0.17 % of DEV/VAL releases.
  - The effect on F1 results was **not** measured, because that would require an F1 evaluation.
- **OOS edge effect.** The final 2027 release of each event is UNDETERMINED unless the OOS calendar export is taken **after** every event's next release. That would exclude about one release per event.

### 2.4 Recommendations (no protocol change)
- Keep the frozen rule. In OOS, the protocol already requires **live-logged first prints**, which make the value causal by construction.
- Before OOS scoring, record the reconciliation between live-logged first prints and the exported CONFIRMED set as an operational step. Export the calendar only after every OOS event has a successor release, so the edge effect vanishes.
- When F1 is evaluated after human opening, report alongside it:
  - the count of excluded candidates per period;
  - a sensitivity line that includes the 6 DEV/VAL ordering-artifact releases, reported as a **disclosure, not a selection input**.
- A future campaign (not V2) should key confirmation by **reference period** rather than release order.

---

## Read-only integrity verification (performed after this investigation)
| Check | Result |
|---|---|
| anchor | `6090be68184af7643f82b680d144a1b9e1622b3bbceebfb872729b97b9d9324c`; sha256(campaign.json) equals it ✔ |
| ledger head | seq 6 `bbd9a28ed6bc7e0b20f3fca9f9ba1fe437f4bd39dc9c1e99ed73fb7505be5b2b`; `verify(anchor, checkpoint)` PASS ✔ |
| witness | 7 entries equal to the ledger; sha256 `05d4544b4c86340d…` (unchanged) ✔ |
| registry directory | tree sha256 `de0c101accf58655…` (unchanged); no registry or witness file modified ✔ |
| state | FROZEN (1 CAMPAIGN_FROZEN + 6 BUILDER_CERTIFIED) ✔ |
| results / OOS rows | 0 / 0 (`results.jsonl` does not exist) ✔ |
| trading / execution | `MTM_ENABLE_TRADING=false`, `MTM_ENABLE_EXEC=false`; MT5 not running ✔ |
| `NEXA_Risk.mqh` | `e706d453d346100f` (unchanged) ✔ |
| V2 evaluation | none occurred ✔ |

No frozen artifact was modified, so **no new freeze was created**.

```
V2 STATUS = FROZEN
V2 EVALUATION = NOT OPENED
HUMAN OPENING APPROVAL = NOT YET GRANTED
```

---
**Update 2026-09-29.** Issue 1 was fixed under explicit human approval. See `NEXA_RISK_CORRELATION_CAP_SAFETY_FIX.md`: `NEXA_Risk.mqh` is now `7fd5692a…`, the cap is fail-closed and time-aligned, compiled 0/0, and MQL5 parity was verified. V2 is unaffected, remains FROZEN and has not been re-frozen.
