# NEXA Unified Auction-State Model (ASM): the "20 pillars" as one core (2026-10-17)

**Request (user, 2026-10-17):** combine the 20-pillar playbook (12 base and 8 expansion pillars) with all earlier NEXA sources, papers and videos into **one core strategy**, using advanced mathematics, psychology and physics. The stated goal is "**every day a green day**", not the highest win rate.

**Status:** DESIGN ONLY. No new data has been touched.
- Each claim below is marked **SOURCE** (cited), **EVIDENCE** (our own test result), or **INFERENCE** (my reasoning).
- Nothing here is tradable until it passes a pre-registered out-of-sample (OOS) test.

---

## 0. The answer in five lines

1. **Yes, the 20 pillars can be one core,** but as **one model with one hidden variable**, not as 20 conditions stacked on top of each other. Every pillar is either evidence about the market's *auction state* (initiative vs responsive), a *location*, a *trigger* or a *risk rule* (§3).
2. **No strategy can make every day green.** This is a mathematical fact, not a matter of skill (§1). "Almost every day green" exists only for exchange market makers at industrial scale (Virtu: 1 losing day in 1,238). For a directional trader, a high green-day share can only be bought with rare large losses, and those losses are exactly what breaks a prop account's trailing drawdown.
3. **Our own evidence already covers about half of the pillars, and none has shown an edge after costs yet** (§4). CFT on ES failed OOS today (−0.88 bp/day).
4. **About a quarter of the pillars cannot be tested at $0.** Spoofing, icebergs, DOM thickness and MOC imbalance need paid order-book or imbalance data.
5. **The honest "superpower"** is the method, not a pattern:
   - one hidden-state model;
   - few, pre-registered features;
   - one test at a time;
   - real money only after an OOS pass.
   
   §6 gives the test order.

---

## 1. Mathematics: why "every day green" is impossible, and what is possible

### 1.1 Streaks decay geometrically
If daily P&L has a probability p < 1 of being green, then:
- P(all N days green) = pᴺ (independent days);
- p = 0.95 gives P(21 of 21 green) = 0.34 and P(a full year green) = 0.95²⁵² ≈ 2·10⁻⁶;
- p = 0.99 gives a full year green with probability 0.08.

Dependence between days does not rescue this: any strategy whose daily P&L can be negative has a strictly positive chance of a red day.

### 1.2 Green-day share is set by the daily Sharpe ratio (symmetric P&L)
With daily mean μ and volatility σ, and roughly normal daily P&L:

  P(green day) ≈ Φ(μ/σ), so the required daily Sharpe for a green-day share q is Φ⁻¹(q).

| Target green-day share q | Daily μ/σ needed | Equivalent annual Sharpe (×√252) |
|---|---|---|
| 55 % | 0.13 | 2.0 (already elite) |
| 67 % (≈ 14 of 21 days) | 0.44 | 7.0 |
| 80 % (≈ 17 of 21) | 0.84 | 13.4 |
| 95 % (≈ 20 of 21) | 1.64 | 26.1 |

**INFERENCE:**
- An annual Sharpe of 13–26 does not exist for directional strategies at any public institution.
- The published CFT source paper reported 1.24 (Zarattini, Aziz & Barbon 2024). Our ES port measured −0.05 in sample and −0.70 OOS.

### 1.3 The only way to a high green-day share without that Sharpe is negative skew
For a driftless price with profit target +a and stop −b (gambler's ruin):

  P(target first) = b/(a+b),  E[P&L] = 0 − costs.

- **Example:** target $200, stop $1,800 gives 90 % green days and an expectation of exactly $0 before costs, so it is negative after costs. One red day erases nine green days.
- **Topstep 50K:** the trailing MLL is $2,000, so a single −$1,800 day nearly ends the account.
- **This is why CFT-P overlays measured "no improvement" today (EVIDENCE).** On ES OOS:
  - every overlay × size cell had negative monthly $;
  - P(pass the 50K Combine in 60 days) ≤ 3 %;
  - P(breach) was up to 87 %.
- **Optional stopping theorem:** no stopping rule changes the expectation of a martingale.

### 1.4 What *is* achievable, and the correct objective
The objective that survives the mathematics is **maximise P(pass and keep a prop account) subject to positive expectancy**. That is CFT-P's choice rule (PREREG_CFT §7). It needs a base strategy with μ > 0 first; no overlay can supply that.

---

## 2. Physics and psychology (why the "superpower" framing is dangerous)

### 2.1 Physics (INFERENCE, analogies made precise)
- **Markets are near-martingales.** Price changes are close to white noise at intraday scale, and predictable order *signs* are already priced (S55; Lillo–Farmer).
- **Maxwell's demon.** A demon that sorts thermal noise into useful work must acquire and erase information, and Landauer's principle charges for that. Extracting profit from price noise likewise requires an *information or service advantage* that someone pays for: speed, inventory provision, risk bearing.
  - Charts, footprints and profiles are public. Their information is shared by everyone looking at the same screen.
- **No conservation laws, plus adaptation.** Published patterns decay because traders exploit them: anomaly returns fall by roughly a third to a half after publication (McLean & Pontiff 2016, *J. Finance*). CFT's source paper was published in May 2024, and our OOS began on that date.

### 2.2 Psychology (SOURCE: behavioural finance)
- **Day-trading outcomes.**
  - Taiwan: fewer than 1 % of day traders are predictably profitable after fees (Barber, Lee, Liu & Odean 2014).
  - Brazil: 97 % of people who day-traded futures for more than 300 days lost money (Chague, De-Losso & Giovannetti 2019).
- **A "never a red day" rule produces the disposition effect** (Shefrin & Statman 1985; Odean 1998): losers are held to avoid realising them, which turns small red days into account-ending ones. The break-even effect (Thaler & Johnson 1990) makes it worse after losses.
- **"I decide when I lose; I predict the market"** is the textbook *illusion of control* (Langer 1975). No participant, including Virtu or Renaissance, chooses its losing days.

---

## 3. The one core: the Auction-State Model (ASM)

### 3.1 The hidden variable
Auction market theory (Steidlmayer, S46; Dalton, S42) describes one thing: at any time the market is either
- **I⁺ / I⁻ (Initiative):** other-timeframe money moves price to new value; trend, range extension, one-sided flow; or
- **R (Responsive / balance):** price rotates around accepted value; extremes are faded and value edges hold.

Every pillar is a noisy *observation* of this state, or an *action* that is only valid in one state.

### 3.2 Formal model (INFERENCE: design, not tested)
- **State:** Sₜ ∈ {I⁺, I⁻, R}, updated at 30-minute decision times τ (as in CFT). It follows a Markov chain with transition matrix A, which has a high diagonal (states persist).
- **Observations at τ** (all computable from free QuantConnect futures data):
  - x₁ = displacement relative to the noise band, (P/O − 1)/σₜ(τ) (CFT trend layer);
  - x₂ = self-normalised signed flow Z(τ) (CFT gate; tick-rule estimate, corr ≈ 0.68 to true flow per F1);
  - x₃ = location relative to the prior RTH value area: above VAH / inside / below VAL;
  - x₄ = structure flags: open type (drive / test / reject / auction), initial-balance width percentile, range extension, single-print tails, poor (flat) extremes, P/b profile shape;
  - x₅ = event flag: sweep beyond the prior-day high or low followed by a close back inside within k minutes (stop run / trapped traders).
- **Filter (Bayes forward recursion):** πₜ(s) ∝ L(oₜ | s) · Σₛ′ πₜ₋₁(s′) A(s′, s).
- **Policy (one rule set, three branches):**
  - π(I⁺) ≥ θ → trend long (CFT trend branch: band entry, VWAP/band trail, flat at 15:59); I⁻ is the mirror.
  - π(R) ≥ θ **and** x₅ fired at a value-area edge → responsive fade toward the POC, stop beyond the sweep extreme.
  - Otherwise → **no trade.** This is the most important branch.
- **Risk engine:** fixed-$R sizing from the stop; a daily loss cap of 1R; a CFT-P overlay only if μ > 0 is proven.

### 3.3 Overfitting guard (non-negotiable)
- A full HMM with 5 feature groups and 3 states has dozens of parameters.
- To stay testable:
  - discrete features;
  - **≤ 4 features**;
  - likelihoods estimated **only** on 2009–2019;
  - validation on 2020 – 2024-05;
  - one OOS look.
- The ES 2024-05 → 2026-07 window has **already been used once** (CFT). A new family tested there must count all earlier CFT stages in its DSR trials.

### 3.4 The 20 pillars inside ASM

| # | Pillar | Role in ASM | Data needed | Status of evidence (NEXA) |
|---|---|---|---|---|
| 1 | CFT | Trend branch (I±) | Free | **ES OOS FAILED today** (−0.88 bp/day; gate added nothing). NQ pending |
| 2 | CFT-P as "value-edge location" | x₃ | Free | OF-16 (open location vs prior VA): INCONCLUSIVE; no symbol beat the base rate (FX/XAU proxies) |
| 3 | Passive absorption | Evidence for R | **MBO / ladder** | BLOCKED-DATA (CL-020, CL-022); only an unsigned proxy (OF-09/22) |
| 4 | Imbalance & trend-riding | Evidence for I (x₂) | Free (estimate) / tick | CFT gate = signed-flow persistence: no value on ES OOS |
| 5 | Stop hunts / stop-run reversals | x₅ trigger (R branch) | Free | **Untested** (OF-06/13); best free candidate |
| 6 | HVN pullbacks | Location for R fades | Free | Untested (OF-22, proxy) |
| 7 | Trapped-trader exhaustion | Same event as 5 | Free (price), tick (footprint) | Untested; merged with 5 |
| 8 | Spoofing / liquidity flipping | Evidence for R/I | **MBO** (paid) | BLOCKED; no public edge evidence |
| 9 | Iceberg tracking | Evidence for R | **MBO** (paid) | BLOCKED |
| 10 | Delta divergence | Evidence for R (at extremes) | Tick-rule estimate | Untested on futures (OF-11 was low-prior on FX); F1 caveat |
| 11 | MOC / last-30-min profiles | Separate time-of-day effect | Imbalance feed is paid | Intraday momentum into the close: **H-IM-NQ REJECTED** (−3.1 bp; the close reverses) |
| 12 | Global risk engine | Risk layer | — | Sizing changes variance, not the sign of edge (optional stopping) |
| 13 | Auction tails | x₄ flag | Free (30-min TPO) | Dalton 3-1 day stats: one market, 1986–87, n not reported; untested |
| 14 | Failed auctions / poor highs "must revisit" | x₄ flag / target | Free | Untested; needs a distance-matched placebo (nearby levels are revisited often anyway) |
| 15 | Open drive | x₄ open type → I | Free | ORB family: H-ORB-1 inconclusive, **H-ORB30L FAILED** 2009–23 OOS; OF-17 untested |
| 16 | Responsive vs initiative | **The hidden state itself** | — | This is the unifying variable |
| 17 | CVD sweep with flat price | Evidence for R (absorption estimate) | Tick-rule estimate | Untested; same measurement caveat as 10 |
| 18 | LVN vacuum | Evidence for I / target | Free (profile); DOM part paid | OF-05 untested |
| 19 | P/b liquidation profiles | x₄ shape → state | Free | OF-21 untested (CL-013) |
| 20 | Anomalous volume node | Location / anchor | Free (volume per price) | Untested (OF-22 family) |

### 3.5 False or untestable statements in the 20-pillar text
- "Guarantees institutional rejection" (13).
- "The market **must** revisit" (14).
- "An absolute anchor for the rest of the day" (20).
- "Secure the 20-day streak" (the B-pillars).

No source in the NEXA corpus shows any of these with statistics. Dalton's own quantified studies come with the caveat that they are one market over a limited period (S42).

---

## 4. Evidence ledger: what ~30 NEXA tests imply for ASM
- **L1 (costs):** small gross edges die on costs. This favours few trades with large moves, i.e. the trend branch, which just failed on ES.
- **L2 (fixed shapes):** ORB family failed OOS. This argues against hard-coded open-drive rules.
- **L3 (order flow):** order-flow rules alone have no edge (OF-16/19/20, OFC1/OFC1R). This argues against a gate made only of flow.
- **New today:** a self-normalised flow-persistence gate did **not** improve trend trades on ES OOS (B − A = −0.14 bp/day).
- **Not yet tested on futures with exchange volume:**
  - the responsive branch (stop-run reversal at value edges);
  - the auction-state classifier itself.
  
  These are the open questions.

---

## 5. What would change my mind (falsifiable)
- **ASM is worth building only if Test T1 passes.** T1 asks whether the state is predictable at all: by 11:00 ET, do pre-registered x₃ + x₄ features classify the rest of the day (trend vs balance) better than the base rate, OOS, on ES and NQ? If they do not, every pillar that relies on "context" has no foundation.
- **The responsive branch has an edge only if T2 passes:** net of 1-tick slippage + commission, mean > 0, CI lower bound > 0, ≥ 300 trades.

---

## 6. Test ladder ($0, QuantConnect free node, ES primary / NQ transfer, one at a time)

| Step | Test | Pillars covered | Why this order |
|---|---|---|---|
| **T1** | **Auction-state predictability** (no trading): open type, IB-width percentile, open location vs prior VA, tails → P(trend day) and P(balance day) vs base rate | 2, 13, 15, 16, 19 | Cheapest, most decisive. If the state is unpredictable, ASM stops here |
| **T2** | **Stop-run reversal** at the prior-day high/low or a VA edge: sweep ≥ k ticks, close back inside within m minutes; stop beyond the extreme; target POC; exit by time | 5, 7, 14, 6 | Best free candidate; mechanically defined |
| T3 | T2 conditioned on the T1 state (only in predicted-R days) | 16 + 5 | Tests whether the context adds value (paired difference, like CFT B − A) |
| T4 | Delta divergence / CVD sweep add-on to T2 (tick-rule estimate, measurement caveat) | 10, 17 | Only if T2 or T3 shows μ > 0 |
| T5 | CFT-P overlay on the surviving rule | 12 | Only if μ > 0 OOS |
| Blocked | Spoofing, icebergs, DOM sizing, MOC imbalance | 3, 8, 9, 11, 18 (DOM part) | Needs paid MBO / imbalance data; out of scope while spending is $0 |

Each step:
- `PREREG_*.md` hashed before any data;
- a frozen code hash, verified in the QuantConnect editor;
- one OOS run;
- the result is preserved whatever it is.

---

## 7. What the user can usefully find (offered 2026-10-17)
1. **The NQ CFT log** ("Virtual Red Wolf" → Logs → Download Logs). It finishes the CFT test.
2. **For T1 and T2:** any source with **exact numbers** for:
   - a stop-run reversal (sweep distance, reclaim time, stop, target);
   - poor-high / poor-low definitions.
   
   Video timestamps work; we will cite them the way the CL-xxx claims are cited.
3. **Optional:** Dalton, *Markets in Profile* (2007), or any study with base rates for open types and day types on ES/NQ.

There is no need to search for a "superpower" strategy. A source claiming 20 green days a month without audited statements is evidence against itself.
