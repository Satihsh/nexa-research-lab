# OF-20b: results (RETROSPECTIVE, semi-blind)

**Run:** 2026-10-11 (user approval: "Approved, implement and run OF-20b").

**Pre-registration:** `PREREG_OF20b_TREND_BALANCE_NORMALISED.md` (sha `fbd8f6bf…`, inherits `PREREG_OF_COMMON.md`).

**Code:**
- `of20b.py`, which reuses the OF-20 `cell`, `rd` and `rot_count`, unchanged.
- G1 tests: 10/10 PASS (new: `test_of20b_normalised_periods`).
- Code hashed 2026-10-10T22:24:35Z, before discovery was opened.

**Opening order:** diagnostics logged first, then discovery → validation → holdout, each once.

**No deviations.** No definition or threshold was changed. Outputs: `of20b_results{_disc,_val,}.json` and `of20b_run{_disc,_val,}.log`, hashed in `RESULTS_MANIFEST.txt`.

**Label:** RETROSPECTIVE (semi-blind). OF-20 had already shown outcome-adjacent rates on the same data (pre-registration §1).

---

## 1. Verdicts

| Item | Verdict |
|---|---|
| **CL-009 trend → balance (OF-20b, retrospective)** | **INCONCLUSIVE.** 0 SUPPORTED; 1 REJECTED (GBPUSD); 3 INSUFFICIENT-N (XAUUSD 71, EURUSD 80, USDJPY 97 trend days < 100) |
| **HYP-013 trend-day base rate** | **3.3–4.3 %** on all four symbols. Outside both S46 (10–20 %) and S42 (20–30 %); every CI is below 0.06 |
| **HYP-010 (≈ 0.9 sideways or reversal)** | UNDETERMINED on XAU/EUR/JPY (n < 100). GBPUSD 0.58 [0.48, 0.69], "refuted for the analogue" but not counted (profile proxy invalid). Every point estimate is ≈ the base rate (0.52–0.65 vs 0.58–0.62) |
| **Persistence (trend → trend)** | None. 0 of 4 symbols have a pooled CI above 0 |
| **CL-009 vs CL-031** | **Unresolved** (pre-stated table). GAP-K04 stays open |
| **Prospective confirmation (§6)** | **Not started.** It needs your approval to acquire new data, and data from 2027 onward needs separate approval |

## 2. Diagnostics (logged before any outcome)

**The normalisation did what it was designed to do:**
- On every symbol and anchor, the 13-period ROT has 5th / 25th / 50th / 75th / 95th percentiles of 1 / 2 / 3 / 4 / 6 (OF-20's 30-min ROT had a median of 8).
- 27–30 % of sessions satisfy ROT13 ≤ 2. This removes OF-20's degeneracy (≈ 0.1 %).
- Session validity: 1,252–1,426 discovery sessions per cell. Only XAU lost ≈ 40 sessions to the ≥ 11-usable-periods rule (short-session days).

**The binding constraint is now the conjunction of conditions:**
- close in the top or bottom 10 % (15–20 % of sessions);
- one-sided extension beyond IB_b (47–70 %);
- REX_b ≥ 1 (39–78 %);
- ROT13 ≤ 2 (28–30 %).

Together they fire on 3–4 % of sessions. That is still below the 10–30 % the Market Profile sources report for ES-type sessions.

**Variant A** (30-min periods, scaled allowance θ_A = 2 or 4) fires on only 0.7–3 % of sessions (n_TD = 10–42), so it is uninformative.

## 3. Primary results (13-period rule, primary anchor, BAL1b)

| Symbol | n(TDb) disc / val / hold | P(BAL1b \| TDb) | P(BAL1b \| not TDb) | θ20b disc / val / hold | **Pooled θ20b [95 % CI]** | p_perm | Disc p (BH) | Verdict |
|---|---|---|---|---|---|---|---|---|
| XAUUSD | 38 / 23 / 10 (71) | 0.44 | 0.38 | +0.03 / +0.07 / +0.13 | +0.053 [−0.052, +0.159] | 0.23 | 0.35 | INSUFFICIENT-N |
| EURUSD | 49 / 18 / 13 (80) | 0.45 | 0.35 | +0.10 / +0.09 / +0.12 | +0.100 [−0.008, +0.208] | 0.036 | 0.15 | INSUFFICIENT-N |
| GBPUSD | 55 / 29 / 17 (101) | 0.35 | 0.35 | +0.05 / −0.10 / −0.03 | −0.008 [−0.101, +0.081] | 0.57 | 0.29 | **REJECTED** (discovery and holdout signs opposite) |
| USDJPY | 41 / 35 / 21 (97) | 0.37 | 0.37 | +0.11 / −0.06 / −0.10 | +0.000 [−0.095, +0.116] | 0.48 | 0.15 | INSUFFICIENT-N |

**Reading**
- **EURUSD** is the only symbol consistent with CL-009:
  - positive in all three splits (≈ +0.10);
  - a permutation p of 0.036;
  - but its CI touches 0, it has 80 < 100 trend days, and its discovery BH p is 0.15.
- **XAUUSD** is positive in all splits but small and imprecise.
- **USDJPY** flips sign after discovery; **GBPUSD** shows nothing.
- **Pooled across the four symbols** (descriptive only, not a pre-registered statistic): about +0.04. The sequence effect, if it exists, is small (≈ 5–10 points over a 35–38 % base) and not robust across instruments.

**Robustness**
- Excluding Friday→Monday leaves the signs mostly unchanged.
- The up/down split is mixed and has no consistent direction.
- XAU, GBP and JPY carry a year-concentration flag.
- The σ̂-tercile pattern is inconsistent across symbols.
- **Secondary cells:** 2 of 28 have secondary-family BH < 0.10. Both are variant-A cells with n_TD = 10 and 33 (EURUSD BAL2 and USDJPY secondary-anchor BAL1). They are small-n and not interpretable.

## 4. What this means

1. **The day-type question is now well-posed for 24-hour FX/XAU**, which OF-20 was not. On it there is **no reliable evidence** that a trend day is followed by a balance day more often than other days. EURUSD's consistent +0.10 is the only lead, and it is not significant at the pre-registered standard.
2. **Trend days are rare under any faithful port of the codification (≈ 3–4 %).** Practitioner base rates (10–30 %) describe RTH index futures, not these instruments under this rule.
3. **The prospective route (§6) is slow.** At ≈ 3.5 % per session, the four symbols produce about 35 trend-day pairs a year, so the pre-registered trigger (≥ 100 pooled) would take **about 3 years**. Most of that data falls in 2027+, which needs your approval.
   - You may prefer to set an earlier evaluation date (allowed by §6), knowing it will probably be underpowered.
   - Or you may decide this line isn't worth continuing.
4. **Nothing is tradable here.** OF-20b is a base-rate study. No construct advances past G3, and nothing touches production.

## 5. KB effect
- **CL-009:** stays INCONCLUSIVE (OF-20 and OF-20b).
- **HYP-013:** measured at 3–4 % under the normalised codification.
- **GAP-K08:** partially closed (rotation degeneracy fixed; low base rate remains).
- **GAP-K04:** open.


## 6. Closure (2026-10-11)
User decision: "Close this line, don't start prospective confirmation." OF-20/OF-20b are CLOSED. CL-009 remains INCONCLUSIVE; GAP-K04 remains open but is not pursued. Re-opening would need a new ID, a new pre-registration and approval.
