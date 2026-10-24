# H-ML1 clarifications (recorded 2026-10-18, before any code was written or data read)

## C-1: feature count
- §3 says "19" features. The enumerated list has **20**:
  - `tod`, `dow`, `r5`, `r15`, `r30`, `r60`, `r_open`, `gap`, `prev_ret`, `pos_prev`, `pos_today`, `vwap_dist`, `or_hi`, `or_lo`, `vol_ratio`, `rv_ratio`, `range_ratio`, `sd_regime`, `x_ropen`, `x_r30`.
- **The enumerated list is binding.** "19" is a counting error. No feature is added or removed.

## C-2: exact definitions used by the code (all implied by §2–§3, stated here so the code has no freedom)
- Bar index k = minutes since 09:30 − 1. Decision times 10:00 … 15:00 ⇒ k = 29, 44, …, 329.
- **σ60** = population std (ddof = 0) of log(c[min(k+60, 389)] / c[k]) over the 21 decision k of each of the previous 20 kept days.
- **σd** = std (ddof = 0) of the previous 20 kept days' close-to-close log returns. Close = c[389]. The first kept day has no prior close; its return is not used.
- **r_n** = log(c[k] / c[k−n]); if k − n < 0, the base is the 09:30 open o[0]. The same applies to the other instrument's r30.
- **r_open** = log(c[k] / o[0]).
- **Opening range** = max h / min l over bars 0–29.
- **VWAP** = Σ(typical × v) / Σ v over bars 0..k, typical = (h + l + c)/3. If Σ v = 0, vwap_dist = 0.
- **vol_ratio**: denominator = the mean over the previous 20 days of their cumulative volume over bars 0..k. If 0, NaN.
- **rv_ratio**: today's std (ddof = 0) of 1-minute log returns over bars 1..k (c[j]/c[j−1]) ÷ the mean over the previous 20 days of their full-day std of 1-minute log returns (bars 1..389).
- **range_ratio**: (max h − min l over bars 0..k) ÷ the mean full-day range (max h − min l) of the previous 20 days.
- **sd_regime**: σd ÷ the mean σd of the previous up-to-250 kept days. Requires ≥ 60 previous σd values, otherwise NaN.
- **Prior day**: H, L, C of the previous kept day (if a non-kept day lies between, the previous *kept* day is used, as §1 says).
- **dow** from the calendar date.
- **Placebo:** applies to **both** targets (§5's verdict structure is "the same" for ES). Permutation within each training day uses `numpy.random.default_rng(seed)` with seed 1–20 and a stable day ordering.
- **Fold "years"** for δ calibration are calendar years present in the training window.
  - With training years y1 < … < yn: the calibration fit uses y1..y(n−2) and calibration predictions use y(n−1), yn.
  - If n < 3, no calibration is possible. This cannot happen: the first test year 2013 has 2010–2012.

## D-1: placebo design corrected (recorded 2026-10-18, after synthetic G1 testing, BEFORE any market data was read)
- **Found by the synthetic end-to-end test.** With a planted signal that moves a whole day one way, the §5 placebo ("labels permuted **within each training day**") scored exactly the real model's mean (0.880 vs 0.880).
  - Labels on the same day are strongly correlated (trend days), so a within-day shuffle keeps each day's direction mix, and the placebo still learns day-level direction.
  - That is not a placebo for "the features carry no information".
- **Corrected placebo (binding):** a **circular day-shift**.
  - The training days are sorted by date (n days).
  - For placebo seed s, draw a shift m = `default_rng(s).integers(n // 10, n − n // 10)`.
  - Each row (day i, decision k) receives the label of (day (i + m) mod n, same k).
  - Label = 1 if that row's long outcome > 0, else 0. Rows whose source day lacks that k are dropped.
  - This keeps the label series' own structure (trend days, time-of-day patterns) but breaks its link to the features.
  - The same δ procedure follows.
- **Unchanged:** 20 placebos, seeds 1–20, P-rank definition and the verdict rule.
- `permute_within_day` is kept only as a helper (unused for the verdict). G1 test 7 now checks the day-shift placebo.
