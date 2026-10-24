# S06: Cartea, Chang & Graumans, "Anonymity, Signaling, and Collusion in Limit Order Books"
**File:** `Anonymity, Signaling, and Collusion in Limit Order Books.pdf`. 48 pp. Preprint (SSRN); this version 30 Jun 2025, first version 3 Jan 2025.
**Affiliations:** Oxford-Man Institute, Mathematical Institute Oxford, Autoriteit Financiële Markten (AFM).

| Field | Value |
|---|---|
| **Source type** | Oxford / university research, co-authored with the Dutch regulator (AFM). Working paper. |
| **Evidence status** | **Strongly supported finding (empirical facts)**: proprietary regulator data with **trader identity and dealing capacity**, nanosecond timestamps, all Euronext Amsterdam messages for January 2022. The **model interpretation (collusion) is a hypothesis consistent with the data**, as the authors say. |
| **Processing** | All 48 pages read. Equilibrium conditions (p. 29) rendered and checked. The figures (box plots, the parameter-region plots on pp. 41–42, and the trailing-digit histogram on p. 44) were read from captions and text. |

## 1. Empirical facts (SOURCE)
**Market:** Euronext Amsterdam ETFs.
- January 2022: 425 M order entries and 390,628 trades, an order-to-trade ratio > 1000. 70 % of trades involve retail.
- Shares: ratio ≈ 32; retail in 10 % of trades.

**Order size signalling**
- Market makers' (MM) median limit order is **€116,144**, against €515 for retail and a €709 median transaction: **226× retail and 164× the transaction**.
- In shares the MM median is €5,919 vs retail €3,999, so there is no such separation.

**Sniping of spread-improving orders** (filled within 1 ms by an IOC aggressor; Table 6)
- Retail orders that nearly cross the spread (improvement 0.9–1.0) are sniped **62.58 %** of the time; MM orders **0.08 %**.
- Odds ratio ≈ **2,068×**.
- Snipe probability for retail rises monotonically with improvement: 0.59 % → 62.58 %.

**Who snipes, and how fast**
- MMs do **82.24 %** of the sniping and win **90.68 %** of the races.
- Median reaction time **91 µs** (min 24 µs).

**Trades between MMs:** only **1.37 %** of ETF trades (≈ 0.61 per ETF per day), against 24.02 % in shares (Tables 9–10).

**Concentration:** about 3 dominant MMs per ETF.

**Explanations rejected:** public information / latency arbitrage, inventory skewing, flickering quotes, queue priority (most ETFs are small-tick) and quoting obligations (which are cumulative) cannot explain the behaviour.

**Trailing-digit patterns:** MM order quantities show non-uniform trailing digits (Fig. 6), similar to FCC-auction "code bidding".

## 2. Model (SOURCE)
**Setup**
- An infinitely repeated 4-period game, generalising Budish, Lee & Shim (2024).
- Fundamental y follows jumps with size distribution J.
- **Agents:**
  - impatient investors (marketable orders, probability p_LT);
  - patient investors (limit orders at y ± δ inside the spread, probability p_LO);
  - N ≥ 3 risk-neutral HFTs with discount factor ρ.
- **Information:** public jumps (p_public) and short-lived private jumps to one HFT (p_private). This comes from fragmentation: HFTs connect to different venues.

**Arbitrage payoff functions**
- L(x) = P(J > x) E[J − x | J > x].
- L̃(x) = P(J < x) E[x − J | J < x].
- L_δ(x): the same, conditional on J > δ.

**Equilibrium half-spreads (verified p. 29)**
- (3a) adverse-selection side: ½ p_LO p_LT s_a/2 = ½ p_LO p_public L(s_a/2) + ((N−1)/N) p_private L(s_a/2).
- (3b) other side: ½ p_LO p_LT s_na/2 = ½ p_LO p_public L(s_na/2).
- s_a ≥ s_na, with equality iff p_private = 0.
- These are indifference conditions between being the market maker and being a latency arbitrageur (the Budish logic).

**Snipe or wait (Lemma 1)**
- Don't snipe (D0) if the expected value of latency-arbitraging patient orders later exceeds sniping now net of the toxic-order risk.
- Snipe (D1) if p_LO δ/N > p_private L(δ)/N.

**Competitive equilibrium:** informed HFTs **pretend to be patient investors** (toxic limit orders), and HFTs **do not provide excess liquidity**. The data contradict this second prediction.

**Collusive equilibrium (Green–Porter trigger strategy)**
- HFTs signal with quantity Q ≫ 1, take turns as market maker, avoid sniping each other, and snipe only unsignalled (retail) orders.
- Punishment for T periods after a trigger.
- **Incentive constraints (ICC):** ρ[c(q_C − q_D)(1−ρ^T) + g q_C + ρ^T(1−q_C) g] ≥ g, and likewise for k.
  - Deviation gains: g = (p_private/N) L(δ) (pretending to be a patient investor) and k = Q L(s_a/2) (latency arbitrage).
- **Informativeness** of the trigger: q_C − q_D = p_private P(J > δ)/N.
- **Corollaries:**
  - collusion is harder with more HFTs (N↑);
  - collusion is harder with less private information. Policy implication: frequent batch auctions reduce short-lived private information.
- **Outcome:** wider effective spreads, and impatient investors are prevented from trading with patient (retail) limit orders.

## 3. Principles (SOURCE → INFERENCE)
- **Anonymity is not guaranteed in practice.** Order size and trailing digits can act as identity signals.
- **Retail limit orders that improve the spread toward or through the fair value are systematically picked off within ~100 µs** by faster agents. Adverse selection of slow limit orders is severe.
- **Market makers fight on speed, but co-operate on who to trade with.** Strategic microstructure, not random noise, determines who fills a limit order.

## 4. NEXA relevance
**NEXA is a retail CFD trader at Pepperstone (OTC, a broker-dealer model).** It does not trade on a lit LOB like Euronext. Transferable lessons (INFERENCE):
1. **Passive and limit entries by a slow retail participant are adversely selected.**
   - NEXA's MARKET entries pay the spread.
   - Any future LIMIT-entry family (e.g. FVG retracement in V2) must model the fill-conditional drift: fills happen when price moves against you.
   - This matches S11 (last-look rejections).
2. **Pepperstone's quote stream is a dealer quote, not an exchange LOB.** "OFI" in the sense of order flow cannot be inferred. This supports NEXA's existing finding: OFI is **NOT TESTABLE** on this feed.
3. **Order-size signalling is visible only with order-level IDs.** NEXA has no such data. **DATA-LIMITED.**

**Cross-references:** S24 (algorithmic collusion and tick size, same authors), S11 (FX last look, latency arbitrage), S10 / S26 (Sánchez-Betancourt execution and trader-ID data), S07 BTMM (practitioner "market-maker manipulation", unrelated in evidence quality).
