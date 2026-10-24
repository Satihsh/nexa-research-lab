# S25: Cartea, Drissi & Monga, "Execution and Statistical Arbitrage with Signals in Multiple Automated Market Makers"
**File:** `ssrn-4388104.pdf`. 15 pp. SSRN 4388104 (≈2023). Oxford-Man Institute, Mathematical Institute Oxford, and Paris 1.

| Field | Value |
|---|---|
| **Source type** | Oxford / university research (working paper) |
| **Evidence status** | Research finding. The mathematical results are derivations; the empirical part is one backtest on crypto (Uniswap v3 + Binance, Jan–Jun 2022). |
| **Processing** | All 15 pages read. Equation pages 4, 9, 11 and 12 rendered and read; the text extraction had garbled the fractions. |

## 1. Market mechanism: constant function market makers (CFMMs)
**Pools and the LT condition**
- A pool holds x of the reference asset X and y of the asset Y.
- Trading function f(x, y): convex level sets, increasing in both arguments.
- The LT (liquidity taker) condition is f(x, y) = f(x + Δx, y − Δy) = κ², where κ is the **pool depth**.

**Rate and level function**
- Level function x = φ(y): convex and decreasing.
- Instantaneous rate Z = −φ′(y) (eq. 1).

**Constant product market maker (CPMM, Uniswap)**
- f = x·y and φ(y) = κ²/y, so Z = κ²/y² = x/y.

**Execution cost (Taylor expansion, p. 4):**

| Z − Z̃(Δy) | ≈ ½ φ″(y) |Δy| = (1/κ) Z^{3/2} |Δy|

**Price impact** ≈ φ″(y)|Δy| = (2 Z^{3/2}/κ) |Δy|.

**INFERENCE:** costs are linear in size, scale with Z^{3/2}, and are inverse in depth. This is analogous to a square-root/linear impact law in LOB markets.

**LP condition:** deposits change κ but not Z, so the trading function must be homothetic.

## 2. Stylised facts (SOURCE, data Jan–Jun 2022)
**Activity (Table 1)**

| Pair | Uniswap volume | Uniswap frequency | Binance volume | Binance frequency |
|---|---|---|---|---|
| ETH | $129.8 bn | 1 txn / 13 s | $267 bn | 1 / 0.13 s |
| BTC | $5.1 bn | 1 txn / 381 s | $358 bn | — |

Binance is where prices form.

**Lead-lag (Fig. 2):** Binance leads Uniswap. The pool rate tracks the "oracle" rate with a delay.

**Johansen trace test on R = (Z_ETH, Z_BTC, S_ETH, S_BTC)**
- Rank 2 is accepted at 99 %: r ≤ 0 has statistic 11,197 (critical value 54.68); r ≤ 1 4,822 (35.46); r ≤ 2 11.45 (19.93).
- Cointegration vectors ≈ (1, −0.022, −1.002, 0.022) and (1, 0.09, −1.004, −0.088). Essentially "pool ≈ oracle" for each coin.

## 3. Optimal-control model
**State dynamics**
- R = (pool rates Z, oracle rates S, signals I), with **multivariate Ornstein–Uhlenbeck** dynamics:

  dR_t = β(μ − R_t) dt + σᵀ dW_t (eq. 2)

  β is the mean-reversion matrix (it encodes cointegration *and* lead-lag); σᵀ is the Cholesky factor of Σ.
- Inventory: dỹ = −ν dt, where ν is the trading speed.
- Cash: dx̃ = (Z − D(η/κ ⊙ Z^{3/2}) ν)ᵀ ν dt (eq. 4). η depends on the trading frequency.

**Objective (eq. 6)**
- Maximise E[ x̃_T + R_Tᵀ X ᵀ ỹ_T − ỹ_Tᵀ α ỹ_T − ϕ ∫ ỹ_sᵀ Σ̃ ỹ_s ds ].
- Terms: terminal cash, plus marked-to-market inventory, minus a terminal liquidation penalty α, minus a running inventory risk penalty ϕ (urgency).

**HJB (eq. 7), verified visually**
- 0 = ∂_t w − ϕ ỹᵀ Σ̃ ỹ + (μ − R)ᵀ β ∂_R w + ½ Tr(Σ D_RR w) + sup_ν { −νᵀ ∂_ỹ w + (X R − D(η/κ ⊙ X R^{3/2}) ν)ᵀ ν ∂_x̃ w }.
- Ansatz: w = x̃ + Rᵀ X ᵀ ỹ + θ(t, ỹ, R).
- Optimal speed: ν* = −D( κ/(2η) ⊙ X R^{−3/2} ) ∂_ỹ θ (eq. 9).

**Fixed-cost subproblem (ζ fixed)**
- Use the quadratic ansatz (eq. 12).
- This yields **Riccati ODEs** (p. 11) for A, B, C. D = E = F = 0.
- Closed form for A:
  - A_ζ(t) = η D(ζ)^{½} (Ψ + ξ(t)^{−1}) D(ζ)^{½};
  - Ψ = (ϕ/η)^{½} D(ζ)^{−½} Σ̃ D(ζ)^{−½};
  - ξ(t) = −(Ψ^{−1}/2)(I − e^{−2Ψ(T−t)}) − e^{−Ψ(T−t)} (Φ + Ψ)^{−1} e^{−Ψ(T−t)};
  - Φ = (1/η) D(ζ)^{−½} A(T) D(ζ)^{−½}.
- B is given via a time-ordered exponential, with C = −μᵀ Bᵀ.

**Optimal speed (eq. 13):** ν^{ζ*} = (1/(2η)) D(ζ)^{−1} ( B_ζ(t)ᵀ (μ − R) − 2 A_ζ(t) ỹ ).

**Closed-form approximation (eq. 14):** set ζ = κ^{−1} ⊙ Z^{3/2} using the observed rates.
- **First term:** *speculative*. It trades on the deviation of rates and signals from their long-run mean through β (statistical arbitrage, lead-lag).
- **Second term:** classical **Almgren–Chriss** inventory liquidation.
- With β = 0, the strategy reduces to AC.

## 4. Empirics (SOURCE)
**Estimation**
- Discretise the OU as a VAR(1): ΔR_t = a + Π R_{t−1} + ε_t.
- Least squares on 24 h of minute data, then trade over the next 12 h.
- ϕ = 1e-6 and α = diag(10, 10). The window rolls by 12 h: 357 runs, buying or selling 1000 ETH and 100 BTC.

**Results (Table 3)**

| Strategy | Average P&L | Std dev |
|---|---|---|
| Optimal | **$2,328** | $54,805 |
| Optimal stat-arb (zero initial inventory) | $2,658 | $5,819 |
| AC | −$343 | $54,823 |
| TWAP | −$3,705 | $99,946 |

## 5. Critical assessment
- **Statistical weakness:** the mean advantage over AC (≈ $2.7k) is tiny relative to the standard deviation ($55k). No significance test is reported.
  - INFERENCE: for 357 runs, the standard error ≈ 54,805/√357 ≈ $2.9k, so optimal vs AC is **not statistically distinguishable** on liquidation.
  - The stat-arb mean ($2,658, sd $5,819, SE ≈ $308) is more convincing but small.
- **Cointegration within the same asset across venues** (pool vs oracle) is near-mechanical arbitrage linkage, not a deep inefficiency.
- **The multi-OU assumes stationarity of spreads.** The 24-hour estimation windows are short and regime shifts are likely (INFERENCE).
- **Blockchain costs** (gas fees, MEV, block latency) are not modelled. UNKNOWN effect.

## 6. NEXA relevance
- **The general toolkit is transferable:**
  - OU / VAR(1) for spreads and lead-lag;
  - Johansen cointegration test;
  - the HJB + quadratic-ansatz → Riccati pattern;
  - the decomposition **optimal speed = AC inventory term + signal term**.
- **NEXA-relevant hypotheses (data permitting):**
  - (a) Lead-lag between the XAUUSD CFD (Pepperstone) and a price-forming venue (COMEX GC futures).
    - NEXA does **not** have a second synchronous feed. "Cross-feed latency" was already BLOCKED in V2 for this reason. **DATA-LIMITED.**
  - (b) Cointegration-based pairs (XAU / XAG; EUR / GBP vs USD) with OU mean reversion.
- **Execution:** NEXA trades small retail size at a fixed spread. Impact-optimal scheduling (AC) is **irrelevant at NEXA's size**. The value lies in the *signal* term, which needs evidence.

**Cross-references:** S10 / S26 (Sánchez-Betancourt execution), S11 (FX last look, latency arbitrage), S24 (algorithmic market makers), S15 Boeker (OU mean reversion in FX), S14 Jin (lead-lag).
