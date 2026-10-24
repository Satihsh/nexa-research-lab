# S33: Alaa Eldin M. Ibrahim, "Evolutionary Approach to Forex Expert Advisor Generation" (Intelligent Information Management 6, 2014, 129–141)

**File:** `iim_2014052015355914.pdf`. 13 pp. University of Sharjah. doi:10.4236/iim.2014.63014.

| Field | Value |
|---|---|
| **Source type** | Other academic institution. Peer-reviewed, open-access journal (SCIRP; low tier). |
| **Evidence status** | **Unverified claim** (about trading performance). The only results are GA fitness curves: an undisclosed 0–100 "special formula" score. **No P&L, no trade statistics, no costs, no out-of-sample performance reported.** The engineering description is a source fact. |
| **Processing** | All 13 pages read, including the appendix (data, metric definitions). **Rendered:** p. 8 (Fig 5) and p. 10 (Figs 9–10). Figs 1–4 and 6–8 (diagrams, similar fitness plots) were interpreted from their captions. |

## 1. System (SOURCE)
- **What it is:** GenFx, a genetic algorithm that breeds MetaTrader 5 Expert Advisors (MQL5).
  - **Genome:** a directed acyclic graph of "boxes" (MQL functions, indicators, constants), built with the author's EATree tool.
  - **Phenome:** generated MQL5 source code, compiled and backtested in the MT5 tester. This takes 95 % of CPU time.
- **Mechanisms:**
  - steady-state, **multiple-generation population** (size 200–300, sorted insertion);
  - **output pool** of the best EAs;
  - **aging:** the score decays exponentially after 10 generations;
  - **"gender" selection:** one parent from the Net-Profit pool, the other from the Profit-Factor pool;
  - Gaussian rank selection, alternating small and large SD across generations;
  - subtree-swap crossover, with subtree depth chosen uniformly or Gaussian, and smaller swaps for high scorers;
  - mutation (rate 0.05) of leaf values or node types (e.g. MACD → MA);
  - restart on stagnation (> 5 generations);
  - elitism (best 3);
  - 12 parallel processes over pool pairs (Net Profit, PF, MaxDD %, Stability, Sharpe), plus 2 random-diversity processes.
- **Fitness:** each criterion is converted to 0–100 "using a special formula" (not given) and combined 1:1.
- **"Robustness testing" (§2.10, Fig 9):**
  - EAs must be "retested on unknown data or out-of-sample data" before insertion;
  - plus changes to data range, trade elimination and parameter changes.
- **Data (Appendix):** EURUSD H1. In-sample 2004–2010; OOS 2010–2014.
- **Results (Figs 5–8, 10):**
  - mean output-pool fitness over 200 generations, rising from ≈ 0 to ≈ 60–85;
  - the standard GA stagnates at ≈ 40;
  - gender + aging is best (≈ 75);
  - 12-process mode reaches ≈ 85 and avoids stagnation.

## 2. Critical assessment (INFERENCE)
1. **The OOS data is used inside selection, so it is no longer out of sample.**
   - Fig 9 shows "IS & OOS Price Data → Evaluation → Robustness Testing → Multiple-Generation Population".
   - EAs that fail on the 2010–2014 data are filtered out. After 200 generations × 200 children × 12 processes, the "OOS" period is fully fitted.
   - This is the classic search-across-many-strategies data-snooping problem. There is no third, untouched holdout.
2. **Massive multiple testing.** Up to about 480k compiled backtests (200 × 200 × 12). Some EAs will look excellent by chance. No deflation or PBO.
3. **Fitness ≠ tradability.** No costs or spread model is specified (MT5 tester settings unknown). There is no live or forward result; the "future improvements" list live testing as not yet done.
4. **Internal contradiction:**
   - Abstract: "multi-processor… outperformed all single runs".
   - Conclusion: the multiple-process extension "been outperformed by using a single processor".
5. **The Sharpe definition in the appendix is loose and incorrect** ("Sharpe 0.6 means… lose 10 dollars per a profit of 6").
6. **"Near-duplicate successful strategies can only be detected manually"** (SOURCE). A diversity metric is missing. Variants of one strategy inflate apparent breadth.

## 3. Principles
- **SOURCE:** GA design trade-off between selection pressure and diversity; stagnation remedies (restarts, aging, multi-population).
- **INFERENCE (key lesson for NEXA):**
  - Automated strategy generation turns *every* evaluation dataset into a training set.
  - Credible evaluation requires a frozen, never-consulted holdout. NEXA's V2 prospective 2027 OOS and its frozen protocols already enforce this.
  - Also required: a count of all candidates evaluated (for deflated Sharpe / PBO).

## 4. NEXA relevance
- **Directly relevant as a cautionary design pattern.** NEXA itself generates MT5 EAs and runs MT5 tester sweeps (memory: NEXA MT5 tooling).
- **Rule (consistent with existing NEXA governance):**
  - log every configuration tried;
  - never let a holdout influence selection;
  - prefer prospective OOS.
- **H-SEARCH-DEFLATE:** for any NEXA parameter sweep, report the number of variants and a deflated Sharpe or PBO alongside the best result (STATISTICAL_KNOWLEDGE_BASE §3).
- **Not usable:** any GenFx-like output as evidence.

**Cross-references:**
- S01 (Archer's JOSTAN FX: 100+ indicators, 5,000+ parameter sets; same risk);
- S12 (best-Sharpe grid selection);
- S02 (random hyperparameter search per block);
- S04 (noisy objective);
- S22 (alpha combos from many faint signals);
- S16 (trade-resampling MC).
