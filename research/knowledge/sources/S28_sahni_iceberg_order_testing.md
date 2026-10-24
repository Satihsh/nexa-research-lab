# S28: Bhupinder Paul Singh Sahni, "Understanding and Testing Iceberg Algorithmic Trading Strategy" (Journal of Business and Strategic Management 9(4), 2024, pp. 40–49)

**File:** `2190-Article Text-5532-6567-10-20240811.pdf`. 11 pp. Published by CARI Journals.

| Field | Value |
|---|---|
| **Source type** | External research. Open-access, low-tier journal by a software-QA practitioner. |
| **Evidence status** | **Unverified claim / descriptive.** No data, no model, no empirical test. The examples are illustrative arithmetic. |
| **Processing** | All 11 pages read. Page 1 is a cover. Figure 1 (an iceberg picture) is decorative. Tables 1–2 were parsed from the text. |

## 1. Content (SOURCE)
- **Definition.** An iceberg order is a large order whose total size is hidden. Only a "block" (the displayed peak) is shown and replenished as fills occur. The parameters are Total Size, Block Size (fixed or random) and Price (limit or market).
- **Motive.** Large visible orders signal information. Others then adjust their order submission, which lowers fill probability and worsens price. Iceberg orders hide intent and reduce impact.
- **Detection.** A market-depth *snapshot* cannot reveal icebergs. They can only be detected from the *dynamics*: replenishment after fills at the same price.
- **Examples:**
  - **Equal blocks at market:** 5 × 20,000 at 162.25, 162.15, 162.10, 162.15, 162.20, giving a VWAP of **162.17** ✓ (810.85/5).
  - **Random blocks at limit 160:** blocks of 12k, 14k, 20k, 11k, 13k, 20k and 10k sum to 100k ✓. The table labels two rows "4th Block" (a typo).
- **Advantages claimed:** lower impact, anonymity, liquidity provision, less slippage, flexibility.
- **Risks claimed:** incomplete execution; extra fees; complexity; detection by others via a consistent block size, then adverse moves; not available everywhere.
- **QA testing checklist:**
  - environment with market simulators;
  - boundary cases (remaining size below the minimum tradable size; random-size bounds);
  - execution rate of the visible vs hidden part;
  - market impact vs a fully displayed order;
  - changing visibility; order size; timing; placement distance;
  - bull, bear and sideways regimes; risk management; regulatory compliance.

## 2. Critical assessment (INFERENCE)
- **Two distinct mechanisms are conflated:**
  - an exchange-native **iceberg / reserve order** (one order with a displayed peak and hidden reserve, keeping time priority only for the displayed part);
  - **order-slicing** algorithms that release child orders over time (TWAP/VWAP-like).
  - The Table 1 "equal blocks at market price" example is slicing, not an iceberg.
- **The benefits are asserted, not demonstrated.** "Iceberg orders contribute to maintaining liquidity" and "reduce slippage" are claims. S27 and S29 show the trade-off is non-trivial: a hidden order loses priority and fill probability, and detection risk is real.
- **The examples ignore costs** (stated) and have no counterfactual impact.
- **Value:** a sound software-QA checklist for testing *any* order-execution logic, including NEXA EA order handling. It is not market evidence.

## 3. NEXA relevance
- **Not applicable as strategy.** NEXA is a retail CFD trader with small size at an OTC dealer. There is no order book to hide in, and retail MT5 does not offer iceberg orders at Pepperstone (UNKNOWN for the broker's liquidity providers).
- **Transferable QA practice (aligned with the NEXA pre-live safety audit):**
  - boundary tests for minimum lot and step after rounding (cf. the 0.02-lot exposure cap memory);
  - partial-fill handling;
  - behaviour across simulated regimes;
  - regulatory/compliance checks.

**Cross-references:**
- S27 Esser–Mönch and S29 Cebiroğlu–Horst (optimal iceberg mathematics);
- S32 Harris (order types, hidden/reserve orders, order exposure);
- S06 (order size as a signal);
- S31 FX algo handbook (algo selection, TCA).
