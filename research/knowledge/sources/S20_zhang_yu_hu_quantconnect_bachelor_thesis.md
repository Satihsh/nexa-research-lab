# S20: Kun Zhang, Mei Yu & Yiming Hu, "Research and Implementation of Quantitative Trading Strategies Based on QuantConnect Platform"
**File:** `Zhang_Kun_Mei_Yu_Hu_Yiming.pdf`. 65 pp. Bachelor's thesis, Oulu University of Applied Sciences (IT), Spring 2025. Supervisor: Teemu Korpela.

| Field | Value |
|---|---|
| **Source type** | Academic thesis (bachelor's, applied sciences) |
| **Evidence status** | **Descriptive / no evidence of edge.** Mostly platform documentation and code screenshots. The few results shown are QuantConnect "Strategy Explorer" pages (authored by QuantConnect), or no-trade runs. |
| **Processing** | All 65 pages read. Rendered: pp. 22 (ORB result), 52 (all-weather result) and 57 (FX SVM-wavelet result). The other image pages (code screenshots, pp. 14–33; dataset examples, pp. 38–48; explorer dashboards, pp. 50–58) are covered by their captions. |

## Content (SOURCE)
- **Platform:** the QuantConnect / LEAN architecture, Python API, brokers (IB, FXCM, Oanda), dataset market (alternative data categories), Strategy Explorer.
- **Strategy illustrations (code only)**
  - FX buy rule: EURUSD > 1.18.
  - Trailing stop at 90 % of the peak (SPY).
  - **Tactical momentum:** MOMP = (P_t − P_{t−n})/P_{t−n} × 100 with n = 10 days; 100 % SPY if positive, else 100 % BND; weekly rebalance (Tuesday).
  - **Opening Range Breakout:** a 30-minute range; enter on a >1 % penetration; close at 13:30 EST.
    - **The authors' own backtest produced no trades** ("due to insufficient backtesting data"; p. 22: equity $100,000, 0 trades).
  - **Gap fading** on TSLA: trade against gaps > 3σ.
  - Liquidity universe: top decile by dollar volume; 2 % position caps; exclude σ > 50 %.
  - **EMA 50/200 crossover** (golden / death cross) on a liquid universe, equal-weight, monthly rebalance.
  - **Pairs** SPY–TLT: spread z-score from a 60-day SMA and standard deviation.
  - Earnings-yield long/short quintiles (value factor).
- **Strategy Explorer examples (authored by QuantConnect):**
  - Quiver crowd sentiment; FAANG news sentiment; all-weather risk parity; P/B "Buffett bargain"; inverse-volatility futures; ML tech-stock forecasting;
  - **EURJPY SVM + wavelet daily forecast:** the rendered p. 57 shows return 0.11 %, PSR 0 %, net profit −$553, over a short live window;
  - Nasdaq-100 6-month momentum top decile.

## Critical assessment
- **There are no systematic results:**
  - no performance tables for the authors' own strategies;
  - no out-of-sample design;
  - no cost model, beyond mentions.
- **Several claims are unsupported or uncited:**
  - "reduce transaction costs by 18–22 %" (footnote to an Investopedia landing page);
  - "a 10-day MOMP replicating Jegadeesh (1993)". Jegadeesh–Titman used 3–12-**month** formation periods, so this is **incorrect**.
- **Reference anomalies:** the Chan, Jegadeesh & Lakonishok "2019" citation points to a 1996 J. Finance DOI; the numbering is disordered.
- **Value:** a catalogue of commonly implemented retail/quant strategy archetypes and of data categories. It is **not evidence**.

## NEXA relevance
- **Archetypes for the backlog** (all need NEXA's own testing):
  - opening-range breakout (FX: London-open range; XAU: COMEX open);
  - gap fading (FX/XAU Sunday-open gaps);
  - pairs / cointegration spread (XAU–XAG, EUR–GBP);
  - long-MA crossover regime filters.
- **The SVM-wavelet FX example is a cautionary data point:** the screenshot shows a flat-to-negative result. Note too that wavelet decomposition can leak the future if it is applied over the full series rather than causally (INFERENCE). Causal-transform discipline is required (NEXA causality certifier).
- **The Strategy Explorer "Likely Not Overfit" badges** (p. 22) are heuristics, not validation.

**Cross-references:** S22 (151 Strategies: formal definitions of the same archetypes), S12 / S16 (other student backtests), S08 (session breakout), S25 (cointegration), S02 (momentum).
