# NEXA research ledger: everything tested since the start (as of 2026-10-18)

**Question from the user:** has any research found a strategy with 18 green days out of 20 (or 10 out of 10), at 1–2 trades a day?

**Short answer: no.**
- No strategy tested so far has passed a pre-registered test. None comes close to 18/20 green days.
- The best green-day share measured in any test was **about 45 %** of trading days (JJ Simon literal rule, NQ 2023–2026), and that rule *lost* money.
- H-SWING (daily trend-following, 20 CME futures) came closest of anything: +5.5 %/yr net, Sharpe 0.43, positive in all 4 time blocks, but the 95 % CI touches zero, so it is **INCONCLUSIVE**. It still had only 52.6 % green days and 50.3 % green months, and needs ≈ $1.7M to run as designed.

---

## 1. Everything tested, by phase

### Phase A: the NEXA MT5 expert advisor on Pepperstone (Sep 2026)
| Test | What it was | Result | Verdict |
|---|---|---|---|
| Production campaign | NEXA EA as configured, $50k tester | 1 trade in 3.93M decisions: the exposure cap blocked trading | Not testable as built |
| Cap-neutral campaign (option B) | Same EA, cap lifted in tester only, 1,902 trades | **−0.318R per trade** | **NO EDGE** |
| "+24.5 %/day" target (8E campaign) | 8-engine intraday design | 0 target days in 1,774 streams | **CONTRADICTED / REJECTED** |
| Phase-3 V2 (six families, 1,632 trials) | Pre-registered multi-family search | All trading claims negative on validation; 17 picks sealed | OOS scoring only after 2028-01-03 |
| H1 strategy factory (TrendLock etc.) | Hourly trend families | ≈ drift (no edge beyond holding) | No edge |
| Safety audit, defects | Partial-close-after-BE bug, exposure-cap fail-open, timezone | Fixed or recorded | Engineering, not edge |

### Phase B: research corpus and intelligence (Oct 1–5)
| Test | Result | Verdict |
|---|---|---|
| 39-PDF corpus, 40 hypotheses | Knowledge base only | No strategy by design |
| T1 tick-volume / profile proxy (FX/XAU) | Works for XAU, EUR, JPY; fails GBP | Data tool, not edge |
| T2 volatility models (YZ / HAR vs ATR) | YZ worse; HAR not separable | REJECTED |
| Futures–CFD basis map | OK for FX, fails gold | Data tool |

### Phase C: published structural effects, FX/gold CFDs (Oct 11)
| Test | Gross effect | Net of retail costs | Verdict |
|---|---|---|---|
| C1 Tokyo fix (gotobi, USDJPY) | **Real** (beats 44/44 placebos) | −0.58 bp | INCONCLUSIVE (not tradable) |
| IM1 intraday momentum | **Real** | negative | REJECTED |
| FX1 fix reversals | **Real** (9/9 signs, ~¼ of the paper's size) | −0.13 | REJECTED |
| C2 time-series momentum (8 FX + gold, monthly) | — | ≤ 0 | REJECTED |
| Gate closures LC-1/2/3 | Intraday FX edges < 2.6 bp, below cost | — | Closed |

### Phase D: order-flow and auction ideas from the video batches (Oct 11–18)
| Test | Source idea | Result | Verdict |
|---|---|---|---|
| OF-16 open location vs prior value area | Dalton / videos | No symbol beats the drift base rate | INCONCLUSIVE |
| OF-19 relative initial balance | Videos | 4/4 rejected | REJECTED |
| OF-20 / 20b trend → balance | Videos | — | INCONCLUSIVE |
| OFC1 / OFC1R core order-flow (Fabio model) | Fabio Valentini | −0.21R / −0.16R | REJECTED |
| H-ORB-1 opening range (NAS100) | ORB videos | +0.063R, p 0.15 | INCONCLUSIVE |
| H-ORB30L-NQ 30-min ORB | ORB videos | in-sample +0.058R → OOS 2009–23 **−0.071R** | FAILED |
| H-IVB1-NQ (Fabio IVB model 1) | Fabio | +0.010R | INCONCLUSIVE (no edge) |
| H-IM-NQ last-half-hour momentum | Papers | −3.1 bp | REJECTED |
| H-VAR-NQ value-area rule | Dalton | reached other side 40 % | INCONCLUSIVE (no edge) |
| CFT trend + order-flow gate (ES/NQ) | Zarattini + order flow | ES −0.88 bp/day, NQ +0.13; gate hurt | NOT VALIDATED |
| T1 auction state at 11:00 (user's ASM) | User's 20-pillar model | ES +0.09 bp, NQ −1.99 bp | NOT PREDICTABLE |
| T2a value-area re-entry "80 % rule" | Dalton / Data Trader / $1M-payout trader | ES −0.046R, NQ −0.045R (≈1,450 trades each) | REJECTED |
| **H-FPT-REV** JJ Simon fair-pricing (NQ/ES) | Batch 10 | NQ −0.456R, ES −0.403R; literal 25/38 in 2023–26 −0.147R; negative before costs | **REJECTED** |
| **H-SWEEP** prior-day high/low stop runs, 2026-10-21 (`validation/SWEEP_ORB5_LVN_REPORT.md`) | Osler 2005 + user's idea 5 | Continuation NQ −0.223R / ES −0.152R; reclaim fade NQ −0.386R / ES −0.314R; gross +0.05…+0.09R eaten by 0.24–0.44R cost | **REJECTED** (4 trials) |
| **H-ORB5** Zarattini 5-min ORB outside the paper's window, 2026-10-21 | SSRN 4416622 + user's idea 1 | NQ −0.201R, ES −0.178R; paper window NQ +0.035, post-paper NQ +0.065 (CI incl. 0); break-even cost ≤ 0.52 NQ pt | **REJECTED** (2 trials) |
| H-LVN-SPEED (descriptive) thin vs thick prior-day volume zones, 2026-10-21 | HYP-004, user's idea 2 | Price 2 % (NQ) / 3.5 % (ES) faster in thin zones; bar was 10 % | INCONCLUSIVE (tiny, real on ES) |
| **H-FLOW-PRED** "Market Predicted" 29-feature order-flow model, 4 horizons, 2026-10-21 (`validation/FLOW_PRED_REPORT.md`) | User's 20-component spec | NQ: 30 s −0.203R, **5 min +0.073R (CI −0.037…+0.192; ≈ always-long +0.067)**, 10 min −0.048, 15 min −0.113; Brier skill < 0 everywhere; no family adds information; 1-s tick-rule flow (rung 3). ES: all 4 horizons negative (5 min −0.108R, CI < 0) | **INCONCLUSIVE** (NQ binding) / ES REJECTED (8 trials) |
| **H-HOUGAARD** Tom Hougaard pre-open (08:30–09:29 ET) range breakout, stop/target 9/6 Dow points scaled, 2026-10-22 (`validation/HOUGAARD_REPORT.md`) | User's saved reel IG-01 | NQ −2.16R, ES −1.69R, YM −1.34R net (YM literal 9/6 −0.97R); 1-min bars cannot resolve the 3–11 pt bracket (stop-first tie rule decides), and costs alone need 64–85 % winners | **REJECTED** (6 trials) |
| **H-CE50** "CE 50 % Model" (08:30–09:30 range midline + first 3-min close, trailing 15-min swing stop), 2026-10-23 (`validation/CE50_REPORT.md`) | Instagram @cemarketsolutions | NQ 2010–15 (outside creator's sample) −0.173R; NQ 2016–26 +0.072R (creator's window only); ES −0.196R / −0.019R; direction beats random but structure loses | **REJECTED** (2 trials) |
| **H-SK28-OOS** frozen s-k-28 12-model NQ day-trading system (commit 0ee4392d), 2026-10-23 (`validation/SK28_OOS_REPORT.md`) | GitHub S73 | Port gate PASS (94.3 % of reference trades matched); NQ 2010–2022 S1 −0.021R (CI −0.057…+0.013, n 3,708, 0/4 blocks, below random-direction control); P-late 2018–22 −0.012R; only build window 2023–25 positive (+0.054R); gross +0.14R eaten by 2-pt costs | **REJECTED** (1 trial) |
| **H-GEX-RANGE** SPX dealer net gamma (prior-close OI, QC free index options) → NQ/ES RTH range forecast vs 10-day panel baseline, 2026-10-24 (`validation/GEX_RANGE_REPORT.md`) | Repo review S85–S97 / CL-032, CL-038 | Walk-forward OOS 2015–2025: NQ −0.06 % error (p 0.52), ES +1.7 % (p 0.13); right sign in-sample (high gamma ⇒ smaller range) but no added OOS value; secondary ES+VIX +3.0 % (p 0.003) noted only | **REJECTED** (NQ binding; ES INCONCLUSIVE; 2 trials) |

### Phase E: prop-firm maths (Oct 18)
| Test | Result |
|---|---|
| H-PROP-EV (Apex 50K, published rules) | At list prices an evaluation loses money unless the strategy makes **≥ +0.025R per trade net**. With coupons even random trading is slightly positive, but only **~1 in 28 evaluations pays** (a lottery), and it breaches Apex's "stockpiling evaluations" rule. |

| H-PROP-EV-TS (Topstep 50K, user's firm) | Zero-edge average is slightly positive (+$35/Combine) only via lottery sizing ($750 risk, 1-in-28 Combines pay, 69 % chance of nothing after 10) that Topstep's "Account Stacking" rule prohibits. Sensible sizing at zero edge = break-even at best. **Real-edge target ≈ +0.10R net** (54 % of Combines pay, +$935 each) |

| **H-ML1** machine-learning direction model (gradient boosting, 20 features, walk-forward 2013–22, hold-out 2023–26) | NQ hold-out −0.007R/trade net (CI [−0.070, +0.045]), gross +0.025R eaten by costs; 5 of 20 placebos as good; ES −0.026R; 0.4–0.7 trades/day; green days 45–48 % | **REJECTED** (both) |

### Phase F: daily swing / trend (Oct 18), see `validation/SWING_REPORT.md`
| Test | Result | Verdict |
|---|---|---|
| **H-SWING P** (12-month TSMOM, 20 CME futures, 2011–2026) | +5.5 %/yr net, Sharpe 0.43, 4/4 blocks positive, CI [−0.02, +4.65] bp/day, p 0.027; not better than holding long (p 0.31); DSR 0.16 at ~161 trials | **INCONCLUSIVE** (closest yet) |
| V-DON Turtle 55/20 | −0.2 %/yr | REJECTED |
| V-MA 50/200 | +0.5 %/yr | INCONCLUSIVE |
| V-IDX (ES + NQ only) | +18.9 %/yr at 40 % vol, drawdown > 100 % at that sizing; secondary, fails multiple-testing, no ES+NQ drift control | Not a result |
| H-SWING-FWD Part A: V-IDX vs always-long ES+NQ | Trend timing cost −4.5 bp/day vs holding long at the same size; Sharpe 0.47 vs 0.74 (always long) vs 0.80 (buy-and-hold) | **DRIFT ONLY** (ES+NQ variant closed) |
| H-SWING-FWD Part B: forward test of P, 2026-07-22 → 2027-12-31 | Pre-registered; binding look on/after 2028-01-03 | Pending |

---

## 2. Why "18 green days out of 20" has not been found, and is not realistic

With 1–2 trades a day, a green day is roughly a winning trade. Assuming each day is independent:

| Daily win probability | P(≥ 18 green of 20 days) | P(10 green of 10 days) |
|---|---|---|
| 50 % | 0.0 % | 0.1 % |
| 60 % | 0.4 % | 0.6 % |
| 70 % | 3.5 % | 2.8 % |
| 80 % | 21 % | 11 % |
| **90 %** | **68 %** | **35 %** |
| 95 % | 93 % | 60 % |

1. **Even a 90 % winner fails the user's target in about 1 month out of 3** (18/20), and fails "10 out of 10" in about 2 months out of 3.
2. **A 90 % win rate with positive expectancy almost always means small wins and rare big losses** (negative skew). One stop wipes out many green days:
   - the "10-point target, 20-point stop" systems (SRC-YT-103/112) need about 67–70 % just to break even;
   - Apex explicitly bans "small targets with disproportionate risk".
3. **The highest green-day share measured in any NEXA test was about 45 %** (all intraday tests 25–45 %), and those rules lost money.
4. **The verified traders say the same.** The Robbins Cup 2nd place wins at most 50 % of her trades and plans for 20 losses in a row. Larry Williams: the strategies that earn the most have the lowest accuracy.
5. **"1 long + 1 short every day"** is close to a coin flip on direction. Holding both at once is hedging, which Apex bans.

## 3. What failed, and why (pattern)
| Pattern | Seen in | Lesson |
|---|---|---|
| Real effect, but smaller than costs | C1, IM1, FX1 | Retail spread and commission eat small intraday edges |
| Looks good in examples, fails when made exact | T2a, OFC1, FPT-REV, ORB30L | Videos show hand-picked winners; fixed rules over 10–16 years lose |
| Positive in-sample, negative out-of-sample | H-ORB30L | In-sample gains were period luck (NEXA law L2) |
| Context / state models not predictive | T1, OF-16, OF-20 | "What kind of day it is" was not knowable by a fixed rule at decision time |
| "Big payouts" come from prop fee economics, not edge | JJ Simon, Dhesi, Apex founder | Payouts ≠ market edge; ~2 % of funded traders reach live |

## 4. Corrective actions (already taken / proposed)
| # | Action | Status |
|---|---|---|
| 1 | Pre-registration, frozen code with hashes, one run, negatives kept | In place since Sep |
| 2 | Stop testing new intraday YouTube rules unless the source gives exact rules **and** a long verified record | Proposed |
| 3 | Test the style verified traders actually use: daily swing / trend, longer holds, lower cost per move | Done: H-SWING INCONCLUSIVE (positive but not significant; ≈ $1.7M needed) |
| 4 | Replace the "green days" goal with **positive expectancy and green months** as the target metric; report green days for information only | Proposed |
| 5 | Any rule that passes: forward paper / demo first, then a capital review. No prop purchase below +0.025R net | Rule set by H-PROP-EV |
| 6 | Outcome autocorrelation check on existing logs (decides whether "size up on A+ setups" is ever justified) | Not started, free |
| 7 | Keep income independent of trading while research continues | Advice from verified traders (Silfrain, McCormick) |

## 5. Exploratory note (not pre-registered, not a trial): "Praveen" evaluation method (YouTube 4BKMDB0dMXc, transcript decoded by the user)
- **Method as stated:** risk $1,000 to make $1,500 (1.5R), one trade a day, pass in about 2 days or fail; "risk = max loss ÷ 4" afterwards.
- **Run through the frozen H-PROP-EV-TS engine** (`prop_ev_ts.cell('STD', 1.5, 1000, 1, mu, n=10000)`), Topstep 50K Standard path:

| Edge per trade | P(pass Combine) | P(any payout) per Combine | Cash per Combine | Cost per Combine | Net per Combine | P(no payout in 10 Combines) |
|---|---|---|---|---|---|---|
| −0.08R | 22.0 % | 4.0 % | $117 | $82 | +$35 | 66 % |
| 0 | 27.0 % | 5.9 % | $229 | $89 | +$140 | 55 % |
| +0.05R | 30.7 % | 7.5 % | $372 | $95 | +$277 | 46 % |
| +0.10R | 33.8 % | 9.2 % | $606 | $99 | +$507 | 38 % |

- **Reading:** the method is fee-convexity (lottery) sizing. It shows a positive average even with *negative* skill, because a Combine costs ~$90 and a lucky streak pays thousands. That is the same pattern Topstep's "Account Stacking" rule prohibits (PROP_EV_TS_REPORT.md). It is not evidence of skill, his or ours.
