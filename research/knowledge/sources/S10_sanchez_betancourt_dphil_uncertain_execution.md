# S10: Leandro Sánchez-Betancourt, *Uncertain Execution in Order-Driven Markets* (DPhil Mathematics, Oxford, Trinity 2021)

**File:** `DPhil_Thesis_L_Sanchez-Betancourt.pdf`, 162 pp.
**Supervisor:** Á. Cartea. Funded partly by LMAX Exchange.
**Chapters are papers:** Cartea & S-B, *SIAM J. Financial Math.* 2021 ("shadow price of latency"); Cartea, Jaimungal & S-B 2019; Cartea & S-B 2021 (stochastic delay).

| Field | Value |
|---|---|
| **Source type** | Oxford DPhil. Ch. 3 is published in a peer-reviewed journal (SIFIN). Industry data partner: LMAX. |
| **Evidence status** | **Mathematics:** established within the stated model assumptions. Proofs are given: verification theorem, FBSDE existence/uniqueness under a short-horizon condition, viscosity solutions. **Empirics:** strongly supported **for an exchange (LMAX) central limit order book (CLOB) with firm quotes**, using proprietary trader-level FX data: Ch. 3, USD/JPY Dec 2016–Mar 2017, two traders; Ch. 5, 10 pairs Sep 2019–Feb 2020. |
| **Processing** | Full text read: pp. 1–162 (10,200 extracted lines). Includes App. A (ODE system, verification proof, robustness), B (Gâteaux derivatives, forward/backward FBSDE existence, Lemma 8) and C (DPP, HJBQVI, viscosity proof; deterministic and zero-latency cases). Low-text pages 1–4, 6, 8, 12 and 23 are title/blank. **Rendered:** p. 92 (Fig 5.2, SPI histograms; verified visually that the distribution is left-skewed). Other figures were read from captions and text. |

## 1. Definitions (SOURCE)
- **Latency:** the full loop from the exchange streaming data (t0) to the trader receiving the outcome (t5), measured on the trader's clock.
- **Marketable limit order (MLO):** a limit order with IoC or FoK time-in-force. **"Discretion" δ** is the allowance to walk the book beyond the observed best quote.
- **Slack / SPI** = (limit − execution-equivalent price) × side.
  - Negative SPI means the order missed.
  - Positive SPI means it filled with room to spare or with price improvement.
- **Flickers:** sub-second deviations of the best quotes, caused by post-and-cancel activity and liquidity that is consumed and then replenished. Bid flickers are mostly negative and ask flickers mostly positive, i.e. a transient widening of the spread.

## 2. Ch. 3: Shadow price of latency (closed-form control)
### Model
- **Micro-price volatility:** dv = κ(v̄ − v)dt + σ_v v dW.
- **Fill ratio with discretion:**
  - dF = [λ(F̄ − F) + aδ − b(v − v̄)]dt + σ_F dW^F;
  - higher volatility lowers fills (b > 0); discretion raises them (a > 0).
- **Robustness to model misspecification:** entropy penalty with ambiguity aversion ϕ (Hansen–Sargent).
- **Objective:** sup_δ inf_Q E^Q[−φ_δ∫(δ − δ̂)² − φ_F∫(F − F̂)² + H(Q|P)].

### Solution (Prop 1 / Thm 1; verified structure)
- **Linear–quadratic (LQ) form:**
  - ansatz V = h0 + h1·f + h2·f² + h3·v + h4·v² + h5·fv;
  - h2 solves a Riccati equation in tanh form when ϕ < a²/(2σ_F²φ_δ);
  - verification proof via Novikov's condition and localisation.
- **Optimal discretion:** δ*_t = δ̂ + (a/2φ_δ)[g1(t) + g2(t)(F̂ − F_t) + g3(t)(v_t − v̄)], with g2, g3 > 0.
  - Discretion increases when the fill ratio is below target **and when volatility is above its mean**.
- **Our check:** σ_v enters only the ODE for h4, which does not appear in δ*. That explains why the Table A.7/A.8 sensitivity rows are identical in pairs.
  - Typo: "v̄_d = 1.2v̄" should read 0.8 (§3.5.3).

### Data (SOURCE)
- **Fill rates:** T1 (FoK) and T2 (IoC) filled about 91 % and 87 % of USD/JPY MLOs at zero discretion.
- **Misses concentrate in high volatility:** 36.5 % / 40 % of misses occur in the top volatility quartile.
- **Retrying a miss is expensive:** 2.3–3.3 ticks if retried 20–100 ms later (tick = 10⁻³ JPY). The miss is adversely selected.
- **Optimal-strategy result:** the fill rate rises to about 99 % at an average cost of 1.76 ticks (T1) and 1.24 ticks (T2), below the retry cost (+14 % to +128 %).

### Implied latency and shadow price
- **Implied latency** (mapping fill rates through cloned traders): T1 averages 20 ms (std 11). The optimal strategy is equivalent to about 2.3 ms.
- **Shadow price of latency:** about ¥3M (≈ $30k) over 4 months for T1. The author states this is below what co-location costs.

## 3. Ch. 4: Trade-off between costs and misses (FBSDE)
### Model
- **Fill rule:** shocks Z arrive with marked-point-process (MPP) trade attempts. A FoK fills iff δ ≥ Z.
- **Cost of walking the book:** C = ∫∫ z·1{δ ≥ z} p(dz, dt).
- **Misses:** D counts missed trades. The miss cost is αD + γD².

### Results
- **Theorem 2:** δ*_t = 2γ E_{t−}[D_T] + γ + α.
  - Theorem 3 gives existence/uniqueness via contraction if kTλ̄(max{1, 2γ})² < 1.
  - Theorems 4–7 give global optimality using a Tikhonov-regularised coercive functional (assuming weak lower semicontinuity).
- **Key closed form:** for a linear miss cost (γ = 0), **δ* = α. The optimal slippage tolerance is a constant equal to the per-miss cost.**
  - Intuition: accept any adverse shock smaller than what missing the trade would cost.
  - Real LMAX traders use a constant discretion (10 ticks for four months, then 5 ticks), consistent with γ = 0.
- **Lemma 2:** negative discretion is suboptimal **when misses are penalised**.
- **Lemma 5:** among cost-neutral strategies (E[C] = 0), a fixed discretion minimises E[misses]. Variable discretion can nonetheless give better tail control, e.g. P(misses < 10 %): 99.997 % vs 98.706 %.
- **Simulation:** Z ~ N(0.1, 1) with intensity λ = 100/day.
  - Zero discretion misses about 54 % (= P(Z > 0)).
  - The cost-neutral α* = 1.79 gives E[misses] = 4.32 per day.

## 4. Ch. 5: Optimal execution with stochastic delay (impulse control)
### Data (SOURCE, LMAX Sep 2019 – Feb 2020)
- **MLOs dominate volume:** 52–73 % of volume, against 3–26 % for market orders.
- **EUR/USD MLOs:** 41 % filled, 1.9 % partially filled, **57.1 % rejected**. Rejected limits were on average about 3 ticks from the best quote.
- **Order size vs best-level depth:** only 0.1–8.8 % of taker orders exceed the depth at the best quote. Typical size is €50k–500k, against mode depth of €500k at best.
- **SPI distribution is left-skewed** (rendered Fig 5.2), even for MLOs aimed exactly at the decision rate.

### Model
- **Price:** Ŝ = S (fundamental) + F (flicker at processing time).
- **Delay:** exponential.
- **Flicker law:** ν = p0·δ0 + p+·η+·e^{−η+ z} (improvement) + p−·η−·e^{η− z} (slippage).
- **Impulse control** with at most one pending order:
  - HJB quasi-variational inequality (C.11);
  - v1 expressed through v0 (C.6);
  - v0 is a viscosity solution (Theorem 13).

### Estimates (Table 5.11)

| Window | p− | p0 | p+ | Mean slippage size | Mean improvement size |
|---|---|---|---|---|---|
| 09:00 | 0.057 | 0.901 | 0.042 | 2.7e−5 | 1.9e−5 |
| 1 min around news | **0.229** | — | 0.056 | **1.6e−4** | 2.5e−5 |

- During news, the slippage tail is about 6× larger.

### Results
- **RLOS performance:** the random-latency-optimal strategy (RLOS) beats TWAP by $3.80 per €M at 30 ms latency, which is about the size of fees ($2–5/€M).
  - Around news: $7–29/€M.
  - Faster traders gain more (10 ms: $5.14; 90 ms: $2.65).
- **Source of the gain:** about 97 % of a patient trader's MLOs are *speculative* (limit better than the current quote). Only 2.4 % fill, but those fills plus price protection generate the gain.
- **Urgency removes the edge:** with high urgency (φ = 10⁻³), the strategy collapses to TWAP-like behaviour, outperforming by only $0.79/€M.
- **Random vs deterministic latency:** RLOS ≈ DLOS (the deterministic-latency version), so knowing the mean latency suffices.
- **Robustness:** results hold under the fundamental-price spread filter υ (7–∞ ticks) and σ ∈ {1, 2, 3} × 10⁻⁴.

## 5. Principles
1. **SOURCE:** fill probability falls with volatility, and **misses are adversely selected.** A missed fill retried later costs more than accepting a small slippage allowance up front.
2. **SOURCE:** the optimal slippage tolerance equals the marginal cost of a miss (δ* = α). It should widen when volatility is high or when the fill shortfall is large (Ch. 3).
3. **SOURCE:** news windows change the flicker distribution asymmetrically: more and larger adverse moves.
4. **INFERENCE:** speculative limit orders capture micro-flickers *only* for a patient, fast trader on a firm CLOB, and the value is about 0.4 bp. It is irrelevant at retail CFD scale.

## 6. Critical assessment
- **Strong points:** rigorous mathematics; unique trader-level data; out-of-sample parameter estimation (previous-day / August estimates).
- **Limitations:**
  - **Firm-quote CLOB** (LMAX), whereas Pepperstone is an OTC dealer with possible last look (S11).
  - The fill-ratio SDE (3.9) is not bounded in [0, 1]; about 0.5 % of simulated paths leave the interval.
  - The Ch. 5 backtest uses historical book data **with no permanent impact** (κ = 0) and assumes sizes that do not walk the book.
  - Benchmarks are relatively weak (TWAP, zero-latency strategy ZLOS).
  - The Heston SDE (3.8) is written with v instead of √v (likely a typo/extraction issue).

## 7. NEXA relevance (execution realism; high)
- **The MT5 `deviation` parameter is exactly "discretion".**
  - **Hypothesis H-DEVIATION-OPT:** NEXA should set deviation ≈ the marginal cost of missing the trade, i.e. the expected edge forgone, bounded by the risk cap.
  - Deviation should also scale with current volatility relative to normal, but it must **never** breach the stop/ATR economics.
  - **Data needed:** live/demo fill logs (requotes, rejections, slippage) with timestamps. NEXA has none yet; this must be logged when forward testing is approved.
  - Evidence: strongly supported mechanism on a CLOB; transfer to OTC is a hypothesis.
- **Backtest realism (H-NEWS-SLIP):**
  - NEXA's cost model should use a **time-varying, asymmetric slippage distribution**, e.g. the S10 three-part law (point mass + two exponentials).
  - Parameters should be per session and per news window, with p− and the slippage size inflated around news (Table 5.11: ×4 probability, ×6 size).
  - This directly addresses the optimistic "100 % fill at stale-safe price" assumption already flagged in S11.
  - It complements the D-EXEC-ENTRYBAR audit finding, which is currently *pessimistic* for STOP fills.
- **Adverse selection of misses:** if NEXA ever uses LIMIT/MLO entries (V2 FVG retracement), model fill-conditional drift: fills happen when price moves against you; misses happen when it runs away.
- **Not usable:** speculative-MLO execution gains (~0.4 bp) are below Pepperstone spread granularity.

**Cross-references:**
- S11 (last look: rejection correlated with favourable moves);
- S06 (sniping of retail limit orders, ~91 µs);
- S26 (algorithm-level behaviour, same group);
- S13 (microprice);
- S25 (Almgren–Chriss/HJB execution);
- S22 (execution-sensitive strategies).
