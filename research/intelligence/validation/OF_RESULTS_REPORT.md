# OF-16 / OF-19 / OF-20: results of the pre-registered tests

**Run:** 2026-10-11 (user approval: "Approved, implement and run OF-16, OF-19, OF-20").

**Pre-registration:** `PREREG_OF_COMMON.md`, `PREREG_OF16_OPEN_LOCATION.md`, `PREREG_OF19_RELATIVE_IB.md`, `PREREG_OF20_TREND_BALANCE.md`. Hashed 2026-10-10T19:54:33Z, read-only.

**Code:**
- `of_common.py`, `of16.py`, `of19.py`, `of20.py` and `of_joint.py`.
- G1 synthetic tests (`test_of_common.py`): 9/9 PASS.
- Code hashed 2026-10-10T20:08:10Z, before discovery was opened.

**Opening order:** discovery → validation → holdout, each opened once (`*_results_disc.json`, `*_results_val.json`, final `*_results.json`). No definition, threshold or rule was changed after any outcome was seen. All hashes are in `RESULTS_MANIFEST.txt`.

**Scope:** research only. No production code, S14, NEXA_Risk, schema, MT5 or market-data collection was touched. Only data already on disk was used.

---

## 1. Verdicts (pre-registered rules)

| Test | Verdict | One-line reason |
|---|---|---|
| **OF-16** open location vs prior VA (CL-005) | **INCONCLUSIVE** (0 SUPPORTED, 1 REJECTED of 3 proxy-valid symbols) | No symbol beats the drift-matched base rate. EURUSD REJECTED; XAUUSD and USDJPY have pooled CIs spanning 0 |
| **CL-005 "70–80 % accurate"** | **REFUTED for the XAU/FX analogue: 4/4 symbols** | Directional hit rate H = 0.48–0.53. Every 95 % CI upper bound is < 0.56 |
| **OF-19-P** relative IB width (CL-003) | **REJECTED (4/4 symbols)** | Accepted small-IB breaks do not beat the driftless law, and do not beat large-IB breaks, consistently across splits |
| **OF-19-T** trade translation (CL-003/004) | **INSUFFICIENT-N** (holdout n = 47 < 200) | Net E[R] is negative in every split. It does not beat the geometry-matched random-entry null (p = 0.37) |
| **OF-20 / CL-009** trend → balance | **INCONCLUSIVE: INSUFFICIENT-N on 4/4 symbols** | The pre-registered trend-day codification almost never fires on FX/XAU anchored sessions: n(TD) = 33 / 2 / 2 / 0 |
| **CL-031 "rebalance ≈ 10 %"** | **REFUTED for the XAU/FX analogue: 4/4 symbols** | P(balance day \| expansion day) = 0.45–0.52 (CIs ≈ 0.40–0.57) |
| **CL-009 vs CL-031 contradiction** | **Unresolved** (per the pre-stated table) | CL-009 cannot be evaluated. CL-031's figure fails. No trend persistence on any symbol |
| **Joint BH, 15 primary tests + OF-19-T** | 3 tests with q < 0.10 | Two are EURUSD OF-19 discovery p-values whose symbol later failed. One is a degenerate OF-20 EURUSD p (n_TD = 2), blocked by the n ≥ 100 rule. See `of_joint_bh.json` |

**Bottom line:**
- **No tradable or predictive edge was found** for any of the three source claims on NEXA's instruments.
- The two quantitative practitioner statistics that could be tested (70–80 % and ≈ 10 %) **do not hold for the spot XAU/FX analogue.**
- Nothing advances past G3/G4. Nothing is proposed for production.

---

## 2. OF-16: opening location vs prior-session value

**Setup**
- **Primary cell:** A0 (full server day) tick-volume VA of day d−1 at α = 0.70. The open is taken at the primary anchor: London 08:00 for FX, 08:20 ET for gold.
- **Effect θ16:** directional hit on outside opens minus the drift-matched base rate.

| Symbol | Days | Outside share | θ16 discovery | Validation | Holdout | **Pooled θ16 [95 % CI]** | p_N3 placebo | Hit rate H [CI] | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| XAUUSD | 2,234 | 0.59 | −0.009 | +0.053 | −0.013 | +0.004 [−0.023, +0.031] | 0.64 | 0.506 [0.479, 0.533] | INCONCLUSIVE |
| EURUSD | 2,374 | 0.58 | −0.032 | +0.013 | −0.007 | −0.018 [−0.045, +0.008] | 0.88 | 0.483 [0.456, 0.508] | **REJECTED** |
| USDJPY | 2,374 | 0.62 | +0.017 | +0.003 | +0.055 | +0.021 [−0.004, +0.045] | 0.23 | 0.527 [0.502, 0.551] | INCONCLUSIVE |
| GBPUSD (proxy-invalid) | 2,371 | 0.57 | −0.007 | +0.005 | +0.010 | −0.001 [−0.028, +0.027] | 0.22 | 0.499 [0.472, 0.527] | REJECTED (not counted) |

**Findings**
- **USDJPY** is the only symbol positive in all three splits. It fails every gate:
  - discovery is not significant (p = 0.16; BH 0.49);
  - the pooled CI includes 0;
  - it does not beat the placebo value area (p_N3 = 0.23).

  It is also the only symbol whose futures-VA proxy swap agrees in sign (+0.069 vs +0.070 on 2024-10 → 2026-09). It is recorded as the weakest kind of lead, not a finding.
- **Volume adds nothing.** The volume-free pseudo-VA (central 70 % of the prior range) performs the same: VA minus N2 = −0.004 / +0.002 / +0.002 for XAU / EUR / JPY, with all CIs spanning 0.
- **The "inside open ⇒ neutral / rotate" reading (Y3) fails.** P(close inside the prior VA | inside open) is not above the geometry-matched placebo VA on any symbol (p = 0.14 / 0.995 / 0.87 / 0.80).
- **Magnitude:** the mean signed move on outside days is −0.01 to +0.04 σ̂. The median round-trip cost is 0.014–0.017 σ̂. Even XAU's point estimate would be mostly consumed by costs.
- **Barrier outcome Y2** (±0.5σ̂ from the open): below the drift base on every symbol in discovery (−0.04 to −0.08, with unresolved days counted as 0).
- **Robustness** changes nothing:
  - above-only vs below-only;
  - excluding Friday→Monday;
  - σ-scaled bins;
  - anchored-session profile;
  - secondary anchor.

  All 12 secondary cells have BH q ≥ 0.73. XAUUSD and GBPUSD carry a year-concentration flag (one year > 50 % of a near-zero pooled effect).

---

## 3. OF-19: relative initial-balance width

**Setup:** primary cell = primary anchor, N = 20, m = 30 min.
- **θ19a** = excess directional-close rate (vs the driftless law) of SMALL minus LARGE RIB terciles.
- **θ19b** = the SMALL excess alone.

| Symbol | Accepted breaks S / M / L | θ19a disc / val / hold | Pooled θ19a [CI] | θ19b disc / val / hold | Pooled θ19b [CI] | p_N2 | Verdict |
|---|---|---|---|---|---|---|---|
| XAUUSD | 71 / 68 / 84 | −0.10 / −0.31 / +0.26 | −0.08 [−0.21, +0.05] | −0.04 / −0.22 / +0.25 | −0.03 [−0.14, +0.08] | 0.90 | REJECTED |
| EURUSD | 124 / 115 / 123 | +0.15 / +0.13 / +0.30 | **+0.19 [+0.08, +0.30]** | +0.12 / −0.05 / −0.00 | +0.06 [−0.02, +0.15] | 0.003 | REJECTED (θ19a SUPPORTED, θ19b REJECTED) |
| GBPUSD | 98 / 100 / 100 | −0.13 / +0.29 / +0.28 | +0.01 [−0.13, +0.15] | −0.07 / +0.09 / +0.04 | −0.02 [−0.12, +0.08] | 0.45 | REJECTED |
| USDJPY | 106 / 114 / 106 | +0.01 / −0.19 / −0.21 | −0.06 [−0.20, +0.07] | +0.00 / −0.02 / −0.04 | −0.01 [−0.11, +0.09] | 0.82 | REJECTED |

**Findings**
- **CL-003 is not supported.** After an accepted break, the session closes beyond the IB about as often as a driftless random walk predicts, whatever the IB's width relative to recent days.
- **Extension (Y2):** small-IB breaks travel *less*, not more, than large-IB breaks on XAU (−0.45σ_rem, CI [−0.75, −0.14]) and JPY (−0.26, CI [−0.51, −0.03]). Mean MFE for SMALL is 0.72–0.87σ_rem, against a driftless benchmark of 0.80.
- **Most first breaks fail:** 85–90 % of first IB breaks trade back inside within 30 minutes (strict "by a tick" acceptance).
- **"Large IBs stay inside" (Y3):** P(no accepted break) is about 0.85–0.91 in every class. There is no gradient by relative width or by absolute IB/σ̂.
- **EURUSD θ19a** is the one consistent pattern. It is positive in all three splits and has a permutation p of 0.003, but **it comes from LARGE-IB breaks underperforming** (E1 = −0.12), not from SMALL-IB breaks outperforming (E1 = +0.06, and negative or flat in validation and holdout). It is single-symbol and fails the pre-registered rule.

  Recorded as an exploratory observation. Pursuing it would need a new ID and a new pre-registration. 7 of 18 EURUSD secondary cells have a pooled θ19a CI > 0; 0 of 18 on every other symbol.

### OF-19-T: trade translation

| Split | SMALL-class trades | Net E[R] | After +0.05R stress [95 % CI] | Per symbol (stress) |
|---|---|---|---|---|
| Discovery | 208 | −0.017 | −0.067 [−0.278, +0.171] | XAU +0.10, EUR −0.08, GBP −0.05, JPY −0.23 |
| Validation | 67 | −0.326 | −0.376 [−0.880, −0.042] | — |
| Holdout | 47 | −0.095 | −0.145 [−0.547, +0.256] | XAU −0.30, EUR −0.17, GBP +0.14, JPY −0.21 |

- **Verdict:** **INSUFFICIENT-N** (pre-registered: fewer than 200 holdout trades ⇒ no verdict).
- **Every split is negative net of costs.** The LARGE class is worse: −0.18 / −0.40 / −0.42R.
- **Geometry-matched random entries** average −0.113R (holdout). The rule's −0.095R is indistinguishable (p_null = 0.37).
- **Cost floor:** it excluded 14 / 62 / 30 / 92 setups (XAU / EUR / GBP / JPY) where cost > 0.20·D. The median D was 9.6 pips on EURUSD and 8.7 pips on USDJPY, which is the same tight-stop cost problem documented for NEXA's campaign.

---

## 4. OF-20: trend day → balance day

### 4.1 The pre-registered trend-day rule almost never fires

| Symbol | Primary session | P(TD) | n(TD) in pairs | P(TD), secondary anchor | P(TD-lite) | P(BAL1) |
|---|---|---|---|---|---|---|
| XAUUSD | 08:20 ET → 17:00 NY (8 h 40 m) | 1.46 % | 33 | 0.0 % (London → 17:00 NY) | 3.1 % | 46 % |
| EURUSD | London 08:00 → 17:00 NY (≈ 14 h) | 0.08 % | 2 | 1.75 % (08:30 ET →) | 0.13 % | 45 % |
| GBPUSD | same | 0.08 % | 2 | 1.76 % | 0.08 % | 46 % |
| USDJPY | same | 0.04 % | 0 | 1.46 % | 0.13 % | 49 % |

**Cause (verified, not a bug):**
- On a 14-hour session there are about 28 half-hour periods. The median EQ-018 rotation count is 8 (5th–95th percentile 5–12).
- "≤ 2 rotations" was codified for pit sessions of about 13 periods (S46). On 24-hour FX/XAU it is satisfied by 0.14 % of sessions.
- The close-location (20 % of sessions) and range-extension (87 %) conditions are not the bottleneck.
- A manual recount reproduced the stored ROT. The A0 full-day robustness session gives P(TD) = 0 on all symbols.

**Consequences:**
- **CL-009 is INSUFFICIENT-N on every symbol** (pre-registered n(TD) ≥ 100).
- **HYP-013's measured base rate** under the registry codification is 0–1.5 %, far below S46's 10–20 % and S42's 20–30 %. This says the *codification does not transfer to 24-hour sessions*. It does not show that trend days don't exist.

The only symbol with any trend days (XAUUSD, n = 33) shows P(BAL1 | TD) = 0.52 vs 0.46 otherwise: risk difference +0.05, CI [−0.13, +0.25]. No information.

### 4.2 CL-031 analogue (expansion day = top-quintile range/σ̂)

| Symbol | P(BAL1 next \| XD) [95 % CI] | P(BAL1 next \| not XD) | Against "≈ 10 %" |
|---|---|---|---|
| XAUUSD | 0.52 [0.47, 0.57] | 0.45 | **REFUTED** |
| EURUSD | 0.45 [0.40, 0.49] | 0.45 | **REFUTED** |
| GBPUSD | 0.46 [0.42, 0.51] | 0.46 | **REFUTED** |
| USDJPY | 0.52 [0.46, 0.56] | 0.49 | **REFUTED** |

- After an expansion day, a balance (rotational, mid-range-close) session follows about half the time, essentially the unconditional rate.
- XAUUSD is slightly *above* its base rate: +0.066, CI [+0.018, +0.122]. This is a secondary cell, and the secondary-family BH was not significant.
- BAL2 (the HYP-010 "sideways or reversal" operationalisation) gives 0.58–0.64. The 10 % figure fails under both outcome definitions.

### 4.3 Persistence and HYP-010
- **Persistence:** P(TD tomorrow | TD today) is not above P(TD) on any symbol. XAU 3.0 % vs 1.5 % (n = 33, CI includes 0). There is no evidence for the "expansion continues" reading either.
- **HYP-010 (≈ 0.9 "sideways or reversal" after a trend day):**
  - XAUUSD P(BAL2 | TD) = 0.76, CI [0.61, 0.90], vs 0.62 on other days (difference +0.14, CI [−0.01, +0.28]). The CI touches the claimed band only because it is wide.
  - EURUSD and GBPUSD (n = 2) and USDJPY (n = 0) are **uninformative**.
  - *Reporting correction RC-1:* the JSON labels HYP-010 "CONSISTENT" for EUR/GBP (CI [0, 1] from n = 2) and "ABOVE RANGE" for JPY (n = 0). Both labels are artefacts of the label code, which had no sample-size guard. They should read **UNDETERMINED (n < 100)**. The numbers themselves are unaffected.

### 4.4 Resolution (pre-stated table)
- CL-009 cannot be evaluated, and no trend persistence was found, so the table gives **"Unresolved."** GAP-K04 stays open.
- What *is* established for the analogue: **the ≈ 10 % rebalance statistic (CL-031) is wrong for XAU/FX sessions.** Day types under these definitions look close to independent of the prior day.

---

## 5. Deviations, implementation notes and caveats

**Deviation OF-D1 (disclosed, hashed in `PREREG_HASHES.txt`)**
- `of20.py`'s report-only A0 full-day robustness path crashed in the first discovery run. XAUUSD has no bars at 17:00 NY (gold opens 18:00 NY).
- The A0 IB now starts at the server day's first bar.
- Fixed before any OF-20 output existed. It does not touch any verdict path.

**Implementation notes** (recorded in the JSON `implementation_notes`):
- **(a)** OF-19 break eligibility requires t + m ≤ 16:59 NY, so that P_a exists.
- **(b)** The OF-19-T geometry null applies no cost floor.
- **(c)** OF-20 BAL2 on non-trend days uses sign(C_d − O_d) as the "direction of d". The pre-registration does not define a direction for non-trend days.

**Reporting correction RC-1:** see §4.3.

**Data audit**
- 0 of 13.4 M rows have a non-OK status or a duplicate stamp.
- 487–492 weekend-server-day rows were dropped per FX symbol.
- The clock conversion matches the file's `time_utc` on 100 % of rows.
- Thin days: 0 on XAU/EUR/JPY; 2 on GBP.

**Caveats that limit what these results mean**
1. These are the **spot XAU/FX analogues** of claims made for ES/NQ cash sessions. They refute the transfer, not necessarily the original claims on their own instruments.
2. The OF-16 profiles are tick-volume proxies. GBPUSD was excluded per T1, and only 2 years of futures profiles exist for the swap.
3. The MT5 M1 spread field is the bar minimum, so costs are understated. That is why the stress tests exist, and the conclusions are negative anyway.
4. The V2 campaign's 2025–2026 exclusion applies to V2 only. The holdout here is this programme's own. No 2027 data was used.

---

## 6. What this changes (and what it does not)

- **No construct advances.**
  - **RESEARCH_GATE:** OF-16 is INCONCLUSIVE@G3/G4 (EURUSD FAILED@G4).
  - OF-19-P is **FAILED@G4**.
  - OF-19-T has no verdict and is negative.
  - OF-20 is INCONCLUSIVE (codification degenerate).
- **KB claim statuses** (from these tests only):
  - CL-005 "70–80 %": CONTRADICTED; the edge is INCONCLUSIVE.
  - CL-003: CONTRADICTED.
  - CL-004: INCONCLUSIVE (exit rule used only in OF-19-T).
  - CL-009: INCONCLUSIVE.
  - CL-031: CONTRADICTED.
- **Not concluded:**
  - that profile context is useless in general;
  - that ES/NQ practitioners are wrong on ES/NQ;
  - that a different, *newly pre-registered* trend-day codification for 24-hour sessions would fail.
- **Possible follow-ups (each needs your approval, a new ID and a new pre-registration; none started):**
  - **OF-20b:** a trend-day codification normalised for session length, e.g. rotation rate per period, or rotations on 60-min periods. It would be counted as a new trial.
  - **OF-19x:** EURUSD "LARGE-IB accepted breaks underperform". This is a single-symbol observation and low priority.
  - **USDJPY OF-16:** only via the prospective holdout (2026-10 →), with no re-test on the data already used.
