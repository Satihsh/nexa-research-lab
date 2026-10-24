# PRE-REGISTRATION H-LVN-SPEED (HYP-004): does price move faster through yesterday's low-volume zones? (descriptive; NQ primary, ES report)

**Status: BINDING.**
- User approval 2026-10-21: "all four, do it" (proposal P3 in `../INSTITUTIONAL_PATTERNS_REVIEW_2026-10-21.md`).
- **Written before any data was read for this hypothesis.** HYP-004 ("volume slows price") is listed untested in `../06_LIQUIDITY_MODEL.md`.
- **This is not a trading rule.** A positive result would only justify a context feature; any strategy built on it needs its own pre-registration.

## 1. Data
- As PREREG_SWEEP §1, with minute **volume** kept. Period 2010-01-04 → end; valid days as PREREG_SWEEP §1 (≥ 20 prior valid days; previous valid day ≤ 4 calendar days earlier).

## 2. Prior-day volume profile (proxy from minute bars)
- Bin width w(d) = max(0.02 · RNG20(d), 1 tick), rounded down to a whole number of ticks (RNG20 as PREREG_SWEEP §2).
- Bins tile [PDL, PDH] of the previous valid day from PDL upward.
- Each of the previous day's 390 RTH minute bars spreads its volume **uniformly over its own [low, high]** into the bins it overlaps (by overlap length; a zero-range bar puts all volume in its bin).
- Density ρ(bin) = bin volume / total. **Thin** bins = the lowest 20 % of bins by ρ (ties broken toward thin by lower ρ, then lower price); **thick** = the highest 20 %. Days with fewer than 10 bins are skipped (counted).
- Shortcut (declared): minute-bar spreading is a proxy for true volume-at-price; the recorder's footprint can confirm later.

## 3. Speed measure
- σ(d) = mean |c[k+1] − c[k]| over all RTH minutes of the 20 prior valid days.
- For each minute k = 0 … 388 of day d with PDL ≤ c[k] ≤ PDH: m = |c[k+1] − c[k]| / σ(d), tagged thin / thick / middle by the bin containing c[k].
- **Primary statistic:** S = mean m over all thin minutes ÷ mean m over all thick minutes (pooled over days).

## 4. Mirror placebo
- Same computation with the prior-day profile **flipped around (PDH + PDL)/2** (bin i ↔ bin n−1−i). This keeps the shape and the share of thin bins but breaks their location.
- D = S_real − S_mirror.

## 5. Inference and verdict (NQ; ES reported the same way)
- Moving-block bootstrap over chronological valid days (block 20, B = 2,000, seed 20261021), recomputing S_real, S_mirror and D on each replicate; 95 % percentile CIs. 4 equal blocks of valid days.
- **CONFIRMED:** S ≥ 1.10, CI(S) lower > 1, ≥ 3/4 blocks with S > 1, and CI(D) lower > 0.
- **REFUTED:** S ≤ 1.00. **INCONCLUSIVE:** otherwise.
- Reported: number of thin / thick / middle minutes, mean m per group, S by year, S restricted to 09:30–10:30 and 10:30–15:59, skipped-day counts.

## 6. Multiple testing
- 2 descriptive trials (NQ, ES); they do not enter the trading-rule DSR count but are listed in the ledger.

## 7. Code, freeze
- `qc_lvn/main.py` (MODE ∈ {NQ, ES}). Unit tests `test_lvn.py`: bin construction, uniform volume spreading by overlap, thin/thick selection and ties, σ warm-up, minute tagging inside [PDL, PDH] only, mirror flip, ratio and bootstrap smoke. Hash before the run; QC editor hash check; output `NEXA_LVN_RESULT`.
