# DEVIATIONS / INTERPRETATIONS — H-ORB30L-NQ and H-VAR-NQ

**Written 2026-10-15, BEFORE either run.**
- No statistic of either rule has been computed on NQ.
- The code, the tests and this file are hashed into `PREREG_HASHES.txt` before the run. The tests are `test_horb30l_hvar.py` (13/13, synthetic bars only); the older suite is still 16/16.
- Binding pre-registrations: `PREREG_HORB30L_NQ.md` (75fd92dd…) and `PREREG_HVAR_NQ.md` (687dbf38…).

## Shared trade engine (`horb30l_nq.run_trade`, used by both)

| # | Interpretation |
|---|---|
| I-1 | **Entry:** the open of the first *existing* 1-min bar at or after the entry minute, and before the exit bar. None → `no_entry_bar`. |
| I-2 | **R:** R = (entry − stop) × direction. R ≤ 0 → `invalid`; R < 10 points → `cost_floor`; both counted, no trade. |
| I-3 | **Stop:** a stop *touch* (low ≤ stop for longs) fills at the stop. After the entry bar, a bar that **opens** beyond the stop fills at its open (gap). |
| I-4 | **Target and same bar:** a target fills only on a 1-tick trade-through, at the target price. If stop and target are touched in the same bar → stop. The entry bar checks the stop only. |
| I-5 | **Time exit:** at the close of the exit bar (15:29 for H-ORB30L, 15:59 for H-VAR). Stop and target are checked first on that bar. |

## H-ORB30L-NQ (`horb30l_nq.py`)

| # | Interpretation |
|---|---|
| I-6 | **Deadline:** "closes by 11:30" = the 5-min candle [m, m+4] satisfies m + 5 ≤ 11:30; the last allowed candle is 11:25–11:29. Entry is at the 11:30 open at the latest. |
| I-7 | **Missing data:** any missing bar in 09:30–09:59, or a missing 15:29 bar → `missing`. A breakout candle whose last bar is missing is skipped. |
| I-8 | **Placebos:** the range bars of the anchor must all exist. The deadline is min(anchor + 2 h, 15:00). The time exit stays 15:29 for every anchor. |
| I-9 | **N2:** needs the same complete range and 15:29 bar. Entry at the first bar ≥ 10:00; stop B; 1R target; same cost floor. **Acceptance item 6 compares the means of the two series** (different trade sets, not paired). |
| I-10 | **Robustness:** "no deadline" = breakout candle closing by 15:25. "1-min closes" uses the same 11:30 deadline. The short mirror uses close < B, stop A. |
| I-11 | **User-goal report:** contracts = max(1, floor($100 ÷ (R points × $2))). The median *actual* risk and the share of trades risking more than $100 are reported, because 1 MNQ often risks more than $100 when R > 50 points. A "won day" is a trade day with net P&L > 0. Months are summed in $. The losing streak counts trades. |
| I-12 | **Statistics:** seed 20261014. DSR var_sr over the 22 own series (primary, 2R, 19 placebos, N2), n_trials = 116. Days come from `horb1_orb.eligible_days` with the latest NY date excluded. Data = volume CSV sha 35d1c3f5…. |

## H-VAR-NQ (`hvar_nq.py`)

| # | Interpretation |
|---|---|
| I-13 | **d−1:** the previous element of the eligible-days list, so holidays and weekends are skipped. Its value area needs all 390 RTH bars (09:30–15:59). Profile = `hivb1_nq.profile` (0.25-pt bins, uniform spread, 70 % `va_greedy`), identical to H-IVB1-NQ. |
| I-14 | **Setup:** the open of d's 09:30 bar. VAL ≤ open ≤ VAH → `inside_open`. Day d also needs its 09:30 and 15:59 bars. |
| I-15 | **Inside period:** computed over the existing bars of the 30-min period; a period with no bars → `missing`. The first period (09:30–09:59) counts if it traded inside. A run of two consecutive inside periods ending by 11:30 gives the signal; possible signals are 10:30, 11:00 and 11:30. |
| I-16 | **Stop:** the min low (long) / max high (short) of the RTH bars from 09:30 to the minute before the signal. |
| I-17 | **Target passed:** an entry already at or beyond the target → `target_passed`, no trade. Applies to the POC-target robustness too, when the POC is not beyond the entry. |
| I-18 | **Stale placebo:** lag k uses the value area of days[i − k], k = 2…20, with the same rules. |
| I-19 | **Dalton conditions (no lookahead):** <ul><li>**c1 (distance):** |open − nearest edge| ÷ width ≤ the median of the same value on the *setup* days (open outside value) among the previous 60 eligible days. Needs ≥ 10 values, else undefined.</li><li>**c2 (narrow value):** width(d−1) < the median width of the 20 sessions before d−1 (days[i−21] … days[i−2]). Needs ≥ 10, else undefined.</li><li>**c3 (direction):** sign(close(d−1) − close(days[i−21])) equals the trade direction; undefined if either session is incomplete.</li></ul> The subgroup "condition true" is the BH secondary; undefined days are excluded from it. |
| I-20 | **Robustness:** "no deadline" = signal by 15:30. "One inside period" = signal at the end of the first inside period. The quarter-width stop = VAL − 0.25 × width (long) / VAH + 0.25 × width (short). |
| I-21 | **Statistics:** DSR var_sr over the 25 own series (primary, long, short, c1, c2, c3, 19 stale lags), n_trials = 116. |

| # | Deviation | Why |
|---|---|---|
| D-1 | One test file `test_horb30l_hvar.py` covers both (§9 names separate files). | Naming only. It covers every §9 item plus end-to-end smoke tests of both `analyse()` functions. |
