# Strategy-candidate ranking from existing research (2026-10-11)

**Scope:** an audit of everything already in the repository, to find ideas that can become *precise entry, exit and risk rules* and be tested on data already on disk.
- **No experiment run.** No data collected. No frozen rule changed.
- **Sources audited:**
  - `research/NEXA_MASTER_PROJECT_STATUS.md`; `research/knowledge/` (39-PDF corpus KB, FAILED_IDEAS, 40-hypothesis backlog);
  - `research/intelligence/` (01–20, 14_HYPOTHESIS_REGISTRY, the 38-hypothesis priority matrix, T1/T2, OF-16/19/20/20b);
  - `research/intelligence/orderflow/kb/` (83 claims, OF-01…26);
  - `filesnexa/NEXA/research/` (V1/V2/8E registries, cap-neutral Gate 8, factory, 8E truth table);
  - the data inventory.

## 0. What the evidence already says (constraints on any candidate)

1. **NEXA's own rule set loses money:** −0.318R per trade net (n = 1,902), and −0.072R even before commission. Tight stops make commission ≈ 0.25R per trade.
   - ⇒ Any candidate must either have a gross edge clearly above about 1 bp, or trade horizons where cost/expected-move is small.
2. **Intraday pattern families on this data are exhausted or negative:**
   - factory 0/25;
   - 8E 2,160 trials (Donchian, TD, OFI proxy, Squeeze, EMA, MACD) with 0/11 replicated;
   - OF-16 / OF-19 / OF-20 / OF-20b no edge.
3. **Four V2 families are frozen and unopened** (macro event, XAU session breakout, FVG retracement, Asian mean reversion). Re-testing them here would contaminate V2's prospective out-of-sample test, so they are **excluded as duplicates**.
4. **No signed order flow, book or options OI** for spot FX/XAU. Everything order-flow or GEX based is **blocked** (CL-050, GAP-D01/D02/D08).
5. **Volatility is mostly persistence** (T2; FlashAlpha CL-075). Volatility-derived signals are risk tools, not entries.

⇒ The surviving class: **structural, scheduled flows** (calendar/fix effects) and **slow, low-turnover premia**. Their mechanisms do not depend on the data NEXA lacks.

## 1. Consolidated ranking (new candidates only; duplicates merged)

**Score** = E × T × I × V (each 1–5, max 625):
- **E** evidence quality (5 = peer-reviewed with mechanism and out-of-sample);
- **T** testability with data on disk;
- **I** implementation ease (5 = reuse existing code almost unchanged);
- **V** potential risk-adjusted value *net of NEXA's measured costs* (a prior, not a result).

| Rank | ID | Candidate (executable form) | Merged duplicates | E | T | I | V | **Score** | Key evidence | Main risk |
|---|---|---|---|---|---|---|---|---|---|---|
| **1** | **C1** | **Tokyo-fix / gotobi USDJPY flow**: long USDJPY into the 09:55 JST (00:55 UTC) fix, short after, on gotobi and month-end days | H-GOTOBI, H-OPEN-CONT (fix part), S01 Ch. 25 | 4 | 5 | 5 | 2 | **200** | Ito & Yamada, *J. Int. Econ.* 109 (2017) 214–234: 15 y of EBS deals, long 5 min / short 5 min around 00:55 GMT = **+1.8 bp/day**, "slightly above" the interbank spread; **larger on 5th/10th days and month-end**; distinct from every other time of day (Fig. 6) | Edge ≈ retail cost (~0.8–1 bp per round trip); post-publication and post-2015 reform decay; M1 cannot see the seconds-long spike |
| 2 | C2 | **FX/XAU time-series momentum (daily)**: sign of the trailing 12-month (and 1/3-month) return, vol-scaled, weekly rebalance, ATR catastrophe stop | H-TSMOM-TANH | 4 | 3 | 4 | 3 | 144 | Moskowitz, Ooi & Pedersen (2012, JFE) include currencies; Menkhoff et al. (2012, JFE) on currency momentum (cross-sectional). D1 history 2000–2026 for ~95 Pepperstone FX pairs + XAU on disk | **No historical swaps**: carry is a confound of FX momentum (only the `contracts.json` snapshot convention used by V2). NEXA's factory found H1 trend ≈ drift |
| 3 | C3 | **London 4 pm WMR fix reversal** (EURUSD/GBPUSD): fade the pre-fix move after 16:00 London, month-end emphasis | H-FIX-FLOW | 3 | 4 | 4 | 2 | 96 | Evans (2014) and Melvin & Prins (2015) report return reversals at the London fix (cited in Ito & Yamada); S31 practitioner support | The WMR window widened to 5 min in Feb 2015 (Ito & Yamada fn. 7), likely shrinking the effect. The month-end equity-hedging signal needs equity data (not on disk) |
| 4 | C4 | **LBMA gold-price auction window** (XAU 10:30/15:00 London): pre-auction drift continuation/reversal | — | 2 | 4 | 4 | 2 | 64 | Mechanism plausible (scheduled benchmark flow). Literature recalled, **not verified this session** | XAU cost; 2015 auction reform |
| 5 | C5 | **Round-number order clustering** (Osler): fade the first touch of xx00/xx50, or continue after a break by k pips | H-ROUND-NUM, OF-06 (part), K-10 | 3 | 3 | 3 | 2 | 54 | Osler (2003, JF) (KB LIT; stop/take-profit clustering) | M1 resolution; quote-only data; overlaps NEXA's failed liquidity-sweep features (f32–f46) |
| 6 | C6 | **XAU–XAG ratio mean reversion** (causal OU z-score) | H-PAIRS-OU | 2 | 4 | 3 | 2 | 48 | Corpus mixed; cointegration unstable | XAG cost; regime shifts |
| 7 | C8 | **EURUSD "large-IB accepted break fails"** (fade) | OF-19x | 1 | 5 | 5 | 1 | 25 | One-symbol pattern found inside the OF-19 run (θ19a positive in all splits, p_N2 = 0.003) but **data-mined**; needs a new ID and a prospective holdout | Snooping |
| 8 | C7 | **Dalton 3-1 / neutral-extreme continuation** | HYP-008, HYP-009 | 1 | 4 | 3 | 1 | 12 | Practitioner statistics (94 %, 64 %) with no base rates; the profile family failed in OF-16/19/20 | Low prior |
| 9 | C9 | **USDJPY open-location lead** | OF-16 (USDJPY) | 1 | 2 | 5 | 1 | 10 | Positive in all splits but failed every gate; **prospective data only** | — |

**Enablers (risk layer, not entries):** these apply to whichever candidate passes and are not ranked as strategies.
- HYP-024 (wider stops cut cost-in-R), HYP-023 (stop rules), H-VOL-2 (vol-scaled size), HAR/ATR7 (T2: equivalent), H-COST-SHRINK (expected-move ≥ k·cost gate).

## 2. Excluded (preserved, not re-proposed)

| Group | Items | Status / reason |
|---|---|---|
| **Duplicates of frozen V2 families** | Macro-event / post-release drift (F1, H-NEWS-PTD); XAU session breakout, ORB/IVB (F2, OF-01/02); FVG (F3); Asian mean reversion (F5) | ⚫ FROZEN in V2 (OOS prospective 2027+). Testing here would contaminate V2 |
| **Data-blocked** | GEX/dealer gamma (OF-12/24/25, HYP-025–030); signed delta, absorption, footprint, stacked imbalance, big trades (OF-08/09/11/22, HYP-003/017/018, F6); cross-feed lead-lag (F4); carry (no swap history) | 🔴 BLOCKED (CL-050, CL-075, GAP-D01/D02/D08, B9) |
| **Failed / closed** | NEXA rule set (−0.318R, CI [−0.384, −0.250]); factory 0/25 (TrendLock = drift; MR and Camarilla negative); 8E 2,160 trials (Donchian contradicted 72/72; TD veto contradicted; OFI proxy failed; Squeeze/EMA200 unproven; MACD/VEI not replicated); +24.5 %/day (contradicted); 300 % OFI (failed); V1 six families (rejected); OF-16 (inconclusive; 70–80 % refuted); OF-19-P (rejected 4/4); OF-19-T (insufficient-n, net negative); OF-20/20b (closed); HYP-001b YZ/HAR beats ATR (rejected); TVPC fitted (failed); CL-031 ≈ 10 % (refuted) | ❌ Kept as evidence; never re-run under the same ID |

## 3. Why C1 is the strongest *testable* candidate

| Criterion | C1 Tokyo fix | C2 TSMOM (runner-up) |
|---|---|---|
| Mechanism | Scheduled, structural customer flow (importers' USD settlement at the fix); peer-reviewed | Behavioural/risk premium; peer-reviewed but contested post-2009 |
| Free parameters | **None** in the primary claim: the time is fixed by the institution (00:55 UTC); days are fixed by the calendar | Look-back, rebalance, vol-target, stop (a grid) |
| Data on disk | USDJPY M1 2017-07 → 2026-09 (UTC-verified clock); JP holidays in the MT5 calendar (2017+) | D1 2000–2026; **swaps missing** |
| Clean null | Yes: the same rule at every other 5-min switch time (time-of-day placebo, as in the paper's Fig. 6) and on non-gotobi days | Random-sign / drift nulls; carry confound unresolved |
| Overlap with frozen or failed work | None by signal. Shares the Asian time window with V2 F5 (different signal; disclosed) | None |
| Cost exposure | High relative to the edge (that is the test) | Low per trade; swap unknown |
| Time to a decisive answer | ~1–2 h compute with existing code | Needs a swap decision first |

**Value expectation (stated before any data, to be falsified):**
- If the post-2017 retail-CFD effect on gotobi days is about +1 bp net per event, that is ≈ 60 events/yr.
- With a 4σ catastrophe stop (≈ 15–20 bp), that is ≈ 0.05–0.07R per event ≈ +3–4R/yr at 1 % risk: modest, but uncorrelated with everything NEXA has.
- If the effect is ≤ cost, C1 fails fast and cheaply, and C2 is next.

Sources (literature checked 2026-10-11):
- [Ito & Yamada, NBER w22820](https://www.nber.org/papers/w22820)
- [Columbia WP 352](https://business.columbia.edu/sites/default/files-efs/imce-uploads/Research/Research_Papers/WP_352.Ito-Yamada.Tokyo_Fixing_Puzzles.pdf)
- Published version: J. Int. Econ. 109, 214–234 (2017), doi:10.1016/j.jinteco.2017.09.005.

## 4. Results log
- **2026-10-11, C1 tested** (`C1_REPORT.md`):
  - INCONCLUSIVE by rule; not tradable at retail cost.
  - The structural effect is confirmed gross (+2.17 bp/event) but net −0.58 bp at S1.
  - **Next:** C2 (needs the swap-history decision).
- **2026-10-11, C2 pre-registered** (`PREREG_C2_TSMOM.md`, hashed):
  - Swaps use option (a), the V2/8E snapshot convention: charges only, ×3 Wednesday.
  - Primary cell: 12-month lookback, monthly rebalance, 8 instruments.
  - Not implemented or run yet.
- **2026-10-11, C2 tested** (`C2_REPORT.md`):
  - REJECTED.
  - The swap snapshot dominates the formal result, and ex-swap is not significant either (Sharpe 0.25).
  - **Lesson:** never apply points-denominated swaps across decades.
- **2026-10-11:** C3 and further unrelated strategy research **PAUSED by user**. Priority moved to reconstructing the user's original order-flow method (`orderflow/ORIGINAL_METHOD_SPEC.md`, awaiting approval).

