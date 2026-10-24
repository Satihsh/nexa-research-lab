# SOURCE MAP: NEXA research corpus (39 files = 38 distinct works)

| Field | Value |
|---|---|
| **Built** | 2026-10-01 (batch 1: 26 files); **extended 2026-10-02 (batch 2: 13 files, S27–S39)**. Corpus deep-learning phase: knowledge acquisition only; no strategy work. |
| **Per-source detail** | `sources/S01…S39_*.md`. Every equation, page reference, critique and NEXA link is there. |
| **Machine-readable** | `CORPUS_MANIFEST.json` (sizes, hashes, page counts, extraction status, visual pages). |
| **Classification** | Two independent axes, as required. **Source type** = who produced it and how it was published. **Evidence status** = how strongly the *content* is supported. A peer-reviewed Oxford paper can still hold an untested hypothesis; a practitioner book can still state an established definition. |

**User research:** none of the 39 files is the user's own research, notes or experiments. All are external documents.

**Duplicate:** `ssrn-5080700.pdf` (S37) is the same paper as S06 (text identical; all 48 pages pixel-identical; only the PDF wrapper differs). It counts as **one** source in every evidence tally. Wherever a note mentions a NEXA finding (e.g. "8E DEV: Squeeze UNPROVEN"), that finding comes from prior NEXA project results, not from the corpus.

---

## 1. Master table

**Relevance key:** H = high, M = medium, L = low, — = none.

| ID | Short name | File | Source type | Evidence status (primary) | Domain | NEXA relevance |
|---|---|---|---|---|---|---|
| S01 | Bland/Meisler/Archer, *Forex Essentials in 15 Trades* (Wiley 2009) | `(Wiley Trading)…Forex Essentials…pdf` | Industry/practitioner | Unverified claim (selected-sample anecdotes) | FX practice, money management, news, GSCS/ME TA | M |
| S02 | Lim, Zohren, Roberts, Deep Momentum Networks | `1904.04912v3.pdf` | Oxford/university (arXiv preprint) | Research finding | TSMOM + DL, volatility scaling, cost | M |
| S03 | Zhang, Zohren, Roberts, Deep RL for Trading | `1911.10107v1.pdf` | Oxford/university (arXiv preprint) | Research finding | RL, momentum, cost | L–M |
| S04 | C. Rough, rBergomi MSc (Imperial) | `212261203---Callum-Rough…pdf` | Academic thesis (other university) | Established (theory) / Research finding (replication) | Rough volatility, fBm, Monte Carlo calibration | M |
| S05 | Balayan, PRISM-Bridge marketing framework | `An_algorithmic_framework…pdf` | External research (peer-reviewed journal, non-market) | Unverified claim (conceptual, synthetic) | Multi-criteria decision analysis (MCDA) for consulting | — (governance vocabulary only) |
| S06 | Cartea, Chang, Graumans, Anonymity/Signalling/Collusion in LOBs | `Anonymity, Signaling…pdf` | Oxford/university + regulator (working paper) | Strongly supported (facts); model = hypothesis | Microstructure, sniping, collusion | M |
| S07 | BTMM strategy PDF | `Beat-The-Market-Maker…pdf` | Industry/practitioner (marketing) | Unverified claim | Retail TA, sessions, levels | L |
| S08 | Goodwin, Beat the Markets guidebook | `Beat-the-Markets-Strategy-Guidebook.pdf` | Industry/practitioner | Unverified claim (cost-free in-sample) | FX patterns, session breakout | L |
| S09 | Bollinger, Methods I–IV | `Bollinger On Bollinger Bands.pdf` | Industry/practitioner (originator) | Unverified claim; definitions established | Volatility bands, squeeze | M |
| S10 | Sánchez-Betancourt DPhil, Uncertain Execution | `DPhil_Thesis_L_Sanchez-Betancourt.pdf` | Oxford DPhil thesis (Ch. 3 published in SIFIN) | Established (maths) / Strongly supported (LMAX data) | Execution, latency, slippage, control | **H** |
| S11 | Cartea, Jaimungal, Walton, FX Last Look | `Foreign-Exchange-Markets-with-Last-Look…pdf` | Oxford/university, peer-reviewed (M&FE) | Established (theory); no empirics | Spread formation, last look | **H** |
| S12 | Lahanis et al., Online portfolio selection backtests | `Glucksman_Lahanis.pdf` | Other academic institution (student report) | Research finding (weak) | Online portfolio selection (OPS), Kelly growth, expert aggregation | L |
| S13 | Spears, Zohren, Roberts, Uncertainty sizing (Eurodollar) | `Investment-sizing-with-deep-learning…pdf` | Oxford/university (arXiv preprint) | Research finding (preliminary; fails at spread) | Sizing μ/σ², uncertainty, microprice | M |
| S14 | Jin DPhil, Statistical methods in market dynamics | `Jin_2025_Statistical_methods_in.pdf` | Oxford DPhil thesis | Research finding (Ch. 4, 6) / strongly supported statistics (Ch. 5) / weak (Ch. 7) | Lead-lag, overnight, clustering, analysts | M–H |
| S15 | Boeker PhD, Scaling and mean reversion in FX (UCL) | `Maria Elisabeth Boeker PhD Thesis.pdf` | Academic thesis (other university) | Established (scaling) / Research finding | FX scaling, OU, Hurst, gaps | **H** |
| S16 | Poudel & Paudel, NEPSE backtest | `Quantitative_Trading_Strategy…pdf` | Other academic (low-tier peer-reviewed) | Unverified claim / weak | Backtesting | L (negative example) |
| S17 | DeMark, TD Sequential (Currency Trader 2005) | `TD SEQUENTAIL.pdf` | Industry/practitioner (originator) | Unverified claim; canonical rule spec | Exhaustion, countertrend | M |
| S18 | Sánchez López, Rough Volatility BSc | `TFG2024ECOSanchez_Rough.pdf` | Academic thesis (undergraduate) | Supported (textbook facts) + formula errors | Rough volatility, option Monte Carlo | L–M |
| S19 | Carter & Senters, Gold volatility webinar | `Volatility_in_Gold_Markets_012110_UK.pdf` | Industry/practitioner (vendor) | Unverified claim | Gold volatility, TTM Squeeze | M |
| S20 | Zhang, Yu, Hu, QuantConnect BSc | `Zhang_Kun_Mei_Yu_Hu_Yiming.pdf` | Academic thesis (bachelor) | Unverified / descriptive | Platform, archetypes | L |
| S21 | Thorp & Kassouf, *Beat the Market* (1967) | `beatthemarket.pdf` | Other academic (academic authors, practitioner book) | Strongly supported principle (later BSM); performance self-reported | Warrant hedging, pyramiding maths, edge decay | L–M |
| S22 | Kakushadze & Serur, *151 Trading Strategies* | `ssrn-3247865.pdf` | Industry/practitioner–academic hybrid book | Established (maths) / Unverified (empirics, second-hand) | Strategy taxonomy, backtest hygiene | **H** |
| S23 | Zhang, Zhang, Cucuringu, Qian, Volatility forecasting with ML + commonality | `ssrn-4022147.pdf` | Oxford/university (later JFEC) | Supported finding (rigorous OOS) | Volatility forecasting, HAR, QLIKE | **H** |
| S24 | Cartea, Chang, Penalva, Algorithms and tick size | `ssrn-4105954.pdf` | Oxford/university (working paper) | Established (theory) + simulation | Algorithmic pricing, learning dynamics | L |
| S25 | Cartea, Drissi, Monga, Execution and stat-arb in AMMs | `ssrn-4388104.pdf` | Oxford/university (working paper) | Research finding (weak significance) | Optimal execution, OU, cointegration | L–M |
| S26 | Cartea et al., Statistical predictions of trading strategies | `ssrn-4442770.pdf` | Oxford/university, peer-reviewed (forthcoming JFEC) | Strongly supported | Algorithm behaviour, information ablation | M |
| S27 | Esser & Mönch, Optimal use of iceberg orders (2005) | `175-moench_paper.pdf` | Other academic institution + bank co-author (working paper → Springer LNEMS chapter) | Established (first-passage maths) / Research finding (one stock, XETRA 2002); β t-stat overstated | Iceberg/hidden orders, first-passage fill probability | L–M (H-HIT-PROB maths) |
| S28 | Sahni, Testing iceberg algorithmic strategy (2024) | `2190-Article Text-…pdf` | Other academic (low-tier peer-reviewed journal) | Unverified claim / descriptive QA checklist | Iceberg order testing (conflates iceberg with slicing) | L |
| S29 | Cebiroğlu & Horst, Optimal display of iceberg orders (2011) | `668476885.pdf` | Other academic (Humboldt SFB 649) + Deutsche Bank | Established within model (Prop 1 proof missing) / Research finding (INET 2009) | Order exposure vs priority, imbalance → short-horizon price | L–M |
| S30 | Lewis, *Flash Boys* (2014) | `Flash-Boys.pdf` | External: investigative journalism (trade non-fiction) | Unverified claims / anecdotal; mechanisms partly supported | HFT, latency arbitrage, Reg NMS/SIP, dark pools, IEX | M (execution-risk awareness) |
| S31 | *Algorithmic FX Trading Handbook 2021* (FXAlgoNews) | `TRADING-HANDBOOK-2021-SCREEN-1.pdf` | Industry / practitioner (vendor-sponsored) | Unverified claims / practitioner consensus | FX algo execution, TCA, liquidity, governance | M (governance, TCA) |
| S32 | Harris, *Trading and Exchanges* (draft 2002, OUP) — **sampler excerpt** | `Trading-Exchanges-…Draft Copy.pdf` | Oxford / university (OUP textbook, USC author) | Established (textbook microstructure); **file holds only chapter openings** | Microstructure principles: spreads, adverse selection, order anticipators, costs | M–H (conceptual) |
| S33 | Ibrahim, GenFX genetic EA generation (2014) | `iim_2014052015355914.pdf` | Other academic (peer-reviewed, SCIRP) | **Failed / invalid** (OOS used in selection; no P&L) | Genetic-algorithm MQL EA generation | L (negative example) |
| S34 | Zheng, Moulines & Abergel, Price-jump prediction in LOB (2013) | `jmf_2013052414582995.pdf` | Other academic + Natixis (peer-reviewed, SCIRP) | Research finding (AUC ≈ 0.72, one month) | LOB imbalance → trade sign / jumps | L (DATA-LIMITED) |
| S35 | Sonono & Mashele, GBM/VG prediction (2015) | `jmf_2015052215132554.pdf` | Other academic (peer-reviewed, SCIRP) | **Failed / negative** (hit ≈ 50 %; no naive benchmark) | Q-measure models used for P-forecasting | L (negative example) |
| S36 | Drakos, Stat-arb S&P 500 with Kalman (2016) | `jmf_2016022913315540.pdf` | Other academic (peer-reviewed, SCIRP) | **Unverified / flawed** (P&L accounting error; no costs; ADF multiple testing) | Pairs, cointegration, Kalman hedge ratio | L (negative example) |
| S37 | **Duplicate of S06** (SSRN 5080700) | `ssrn-5080700.pdf` | = S06 | = S06 (not independent) | = S06 | = S06 |
| S38 | Hong, HFT intervalling & portfolio volatility (2019) | `tel_2019092615201272.pdf` | Other academic (peer-reviewed, SCIRP) | Research finding / model-artefact (Prop 1 normalisation artefact; no data) | Sampling interval vs measured volatility (OU) | L–M (H-VR-SCALE) |
| S39 | Lafarguette & Veyrune, IMF FX intervention VaR rule (2021) | `wpiea2021032-print-pdf.pdf` | External research (IMF working paper) | Research finding (proof of concept; density OOS short) | EGARCH-X skew-t density, quantile triggers, PIT/log score | M (H-VAR-TRIGGER, density-evaluation toolkit) |

---

## 2. By source type

| Source type | Sources | Count |
|---|---|---|
| **Oxford / university research** (Oxford-Man, Maths Institute, Oxford Statistics; incl. DPhil theses; Oxford University Press) | S02, S03, S06 (=S37), S10, S11, S13, S14, S23, S24, S25, S26, S32 (OUP textbook) | 12 (+1 duplicate file) |
| …of which peer-reviewed (as published or forthcoming; file may be a preprint) | S11 (M&FE), S26 (JFEC forthcoming), S10 Ch. 3 (SIFIN), S23 (later JFEC, not stated in file), S02 (later JFDS, not in file) | — |
| **Academic thesis, non-Oxford** | S04 (Imperial MSc), S15 (UCL PhD), S18 (BSc), S20 (Oulu BSc) | 4 |
| **Other academic institution** | S12 (NYU Stern student report), S16 (Nepal, low-tier journal), S21 (UC Irvine academics; practitioner book), S27 (Frankfurt/DekaBank), S28 (low-tier journal), S29 (Humboldt SFB), S33, S34, S35, S36, S38 (SCIRP open-access journals) | 11 |
| …of which peer-reviewed journal articles | S16, S28, S33, S34, S35, S36, S38 (S27 later a Springer chapter) | — |
| **External research** | S05 (outside markets), S39 (IMF working paper), S30 (investigative journalism) | 3 |
| **Industry / practitioner** | S01, S07, S08, S09, S17, S19, S22 (hybrid), S31 (vendor handbook) | 8 |
| **User research** | — | 0 |
| **Unknown / unverified provenance** | none fully. S07 and S08 lack dates and authors' credentials. | 0 |
| **Total distinct works** | 12 + 4 + 11 + 3 + 8 | **38** (39 files incl. duplicate S37) |

## 3. By evidence strength (content), strongest first

| Evidence status | Sources (and what specifically) |
|---|---|
| **Established evidence** | Mathematical results with proofs: S11 Props 1–12; S24 Props 1–6; S10 Thms 1–13 within the model; S25 HJB/Riccati.<br>Textbook theory: S04 fBm/rBergomi; S22 option/bond algebra; S21 hedge bound (later BSM).<br>The FX scaling law ⟨\|Δx\|⟩ ∝ Δt^{0.56–0.58}, replicated in S15.<br>GBM first-passage law and inverse-Gaussian hitting density (S27, verified).<br>Market-microstructure textbook principles: spread = transitory + adverse-selection components; limit order = free option; zero-sum game (S32). |
| **Strongly supported** | S06 sniping/size-signalling facts (regulator IDs).<br>S26 70 % vs 54 % ablation (walk-forward).<br>S10 LMAX fill and slippage facts.<br>S14 Ch. 5 volume-shock → overnight statistics (t > 20).<br>Volatility clustering/forecastability (S23 + S04 + S18 + S09/S19 stylised; S39 EGARCH β ≈ 0.99, ν ≈ 8.5 on daily MXN).<br>Adverse selection of resting/limit orders (S06, S10, S11, S29, S32; practitioner corroboration S31, S30). |
| **Supported finding** | S23 HAR/NN volatility forecasting results (DM tests, unseen-stock test, utility with costs).<br>S39 GARCH-family density beats unconditional/quantile-regression densities (Diks log-score test; short window). |
| **Research finding** | S02, S03 (single dataset, OOS, cost-free or cost-fragile); S13 (preliminary); S14 Ch. 4/6; S15 OU-bias simulations; S25 stat-arb; S12 (weak); S27 MAN iceberg statistics; S29 INET imbalance → price (seconds); S34 AUC ≈ 0.72 (one month); S38 (model only); S39 (proof of concept). |
| **Unverified claim** | S01, S07, S08, S09 (profitability), S16, S17 (predictive value), S19, S20, S05 (non-market); S22's second-hand "empirical studies suggest…"; S28 (descriptive); S30 magnitudes (HFT profit, "tax" extrapolations); S31 vendor numbers. |
| **Contradicted / failed (specific claims)** | See `FAILED_IDEAS.md` and `CONTRADICTIONS.md`. Examples: S14 "Lévy area captures nonlinear lead-lag" (not established by its own theorem); S18 "exponential ACF" (contradicted by S04); S16 "MC rules out overfitting" (invalid); **S33** GA "out-of-sample" (OOS used in selection); **S35** direction from Q-measure GBM/VG (≈ 50 % hit, worse than naive on MAPE); **S36** Kalman stat-arb P&L (accounting error, no costs). |
| **Data-limited (for NEXA)** | Microprice/LOB imbalance (S13, S26, S06, S29, S34), cross-feed lead-lag (S25), historical swap/carry (S22), order-level IDs (S06, S26), multi-venue/SIP latency structure (S30), iceberg/hidden depth (S27–S29), broker fill/requote logs (S10, S11, S30, S31: not yet logged). |

## 4. By domain (where to look)

| Domain | Primary sources | Secondary |
|---|---|---|
| Execution, slippage, fills, latency | S10, S11, S32 (costs, benchmarks) | S06, S25, S01 (news fills), S22 App. A (cost model), S27/S29 (passive fill probability), S30 (latency arbitrage), S31 (TCA practice) |
| Market microstructure and market-maker (MM) behaviour | S06, S26, S24, S32 | S11, S13 (microprice), S29, S34 (imbalance), S27/S28 (icebergs), S30 (HFT narrative), S07 (narrative only) |
| Volatility modelling and forecasting | S23, S04, S39 (density) | S18, S15 (scaling), S38 (sampling interval), S09/S19 (squeeze heuristics), S02 (vol scaling), S35 (VG tails) |
| Momentum and trend following | S02, S03, S22 §10.4 | S01 (major trend = first-to-last close), S21 (Kassouf trend term), S19 |
| Mean reversion and stat-arb | S15, S14 Ch. 6, S25 | S12 (OPS), S22 §3.8–3.10, S16, S17 (countertrend), S09 III, S36 (Kalman pairs, flawed), S38 (OU sampling) |
| Lead-lag and cross-asset | S14 Ch. 4, S25 | S01 (Shanghai BC cross-lead claims), S23 (commonality) |
| Sessions, time of day, overnight | S14 Ch. 5 | S01 (opens, Tokyo fix, App. D), S08 (session breakout), S23 (diurnal) |
| Position sizing and growth | S13 (μ/σ²), S02/S03 (1/σ), S21 (avalanche, log growth) | S12 (Kelly/CRP), S01 (fixed-$ risk), S22 §15.3.1 (vol target) |
| Validation and statistics | S23 (QLIKE/DM), S26 (walk-forward, ablation), S14 (cost curves, DSR/HAC), S22 (delay-d, OOS definitions), S39 (PIT, log score, Diks) | S04 (noisy objective), S15 (estimator bias), S32 (skill vs luck, selection bias), S31 (operational envelope), S16/S08/S12/S33/S35/S36 (negative examples) |
| Machine learning | S02, S03, S13, S23, S26 | S14 Ch. 5 (TabNet), S22 §18 (ANN, naive Bayes), S20, S34 (LASSO logit), S33 (GA) |
| Indicators and technical analysis definitions | S09, S17, S19, S22 §3.11–3.17 | S01 (RSI, Dagger, GSCS, ME), S07, S08 |
| Market design and game theory | S24, S06, S11 | S30 (IEX speed bump, Reg NMS), S32 (market structure chapters) |
| Option pricing / derivatives | S04, S18, S21, S22 Ch. 2 | S35 (LSMC, VG under Q) |
| FX market structure and central banks | S31, S39 | S01, S11, S22 Ch. 8 |
| Barrier / first-passage probabilities | S27 | S21 (barrier maths), S04 (simulation) |
| Governance and prioritisation | S05 | — |

## 5. Lineage and authorship clusters (for dependence between sources)

| Cluster | Sources | Note |
|---|---|---|
| **Cartea group (Oxford-Man / Maths Institute)** | S06, S10 (supervised by Cartea), S11, S14 (co-supervised), S24, S25, S26 | Shared methods (stochastic control, AFM data) and shared viewpoints. They are **not independent replications** of one another. |
| **Zohren–Roberts group (Oxford-Man)** | S02, S03, S13 | Same features (Baz MACD, vol-scaling), same data vendor (Pinnacle CLC for S02/S03). |
| **Cucuringu (Oxford Stats/Turing)** | S14 (co-supervisor), S23 | — |
| **Rough-volatility pair** | S04 and S18 | Both restate Gatheral–Jaisson–Rosenbaum and Bayer–Friz–Gatheral. S04 is the more rigorous; S18 contains errors. |
| **Practitioner squeeze lineage** | S09 → S19 | Bollinger BandWidth squeeze → Carter TTM squeeze, which is NEXA 8E E1's definition. |
| **Global-View / FXPraxis** | S01 | Single author group; anecdotal. |
| **Iceberg-order lineage** | S27 → S29 (S28 descriptive) | S29 cites the Esser–Mönch line. Model-based; not independent replications. |
| **SCIRP *J. Mathematical Finance* / similar open-access** | S33, S34, S35, S36, S38 | Same venue family; quality varies widely (S34 credible, S33/S35/S36 flawed). |
| **Microstructure-for-practitioners trio** | S32 (Harris) ↔ S30 (Lewis) ↔ S31 (handbook) | Different authors and eras; S30/S31 interested parties. Agreement on mechanisms (order anticipation, last look, TCA benchmarks) is cross-cluster but S30/S31 are not independent of industry interests. |
| **Duplicate** | S06 = S37 | Same paper; count once. |

**INFERENCE:** agreement within a cluster counts as roughly one line of evidence. Cross-cluster agreement (e.g. volatility forecastability: S23 + S04 + S15 + practitioner S09/S19) is stronger.

## 6. Page and section reference index for key items

| Item | Reference |
|---|---|
| TSMOM vol-scaling eq. (1); turnover-cost loss eq. (35) | S02 pp. 4–5, 12 (rendered) |
| DRL reward with cost eq. (4) | S03 p. 4 |
| fBm ACF ~ H(2H−1)n^{2H−2}; Hurst table | S04 Ch. 4, Table 5.1 p. 37 |
| ATM skew eq. 9.1.1 (mislabelled "volatility") | S04 p. 64 |
| Sniping odds ratio about 2,068× | S06 Table 6 |
| Equilibrium half-spreads (3a), (3b) | S06 p. 29 |
| Optimal discretion δ* = α (linear miss cost) | S10 Ch. 4, Thm 2 |
| News flicker law, Table 5.11 | S10 Ch. 5 (p. 92 Fig 5.2 rendered) |
| Last-look Props 1, 4–7, 9 | S11 pp. 11–14 |
| μ/σ² sizing derivation | S13 App. A.1, p. 13 |
| Lévy area / lead-lag Thm 1; cost curve Fig 4.6 | S14 App. A.3; p. 56 |
| Overnight return eq. 5.2 (index typo) | S14 p. 75 |
| OU mean absolute return; business-time σ bias; DMA artefact | S15 eq. 4.3; Tables 5.x; Ch. 6 (pp. 77, 116 rendered) |
| Canonical TD rules vs NEXA code (6 discrepancies) | S17 pp. 1–6 |
| rBergomi eq. 3.6 missing exp; eq. 4.7 error | S18 pp. 14, 17 |
| TTM Squeeze parameters (20, 1.5, 2) | S19 pp. 30, 32 |
| Avalanche formula; App. C bound; Kassouf model | S21 App. A, C, D (pp. 206–211, image-only) |
| delay-0 "borderline in-sample"; E_eff cost shrink | S22 App. A, pp. 125–129 |
| KNN look-ahead; HP-filter look-ahead; TSMOM tanh | S22 §3.17, §8.1, §10.4 |
| 1+κ error; non-exp "softmax" | S22 pp. 103–104 and 119 (PDF 104 and 120 rendered) |
| QLIKE, DM test, realised utility | S23 pp. 17, 19 |
| Replicator / Q-learning ODEs; tick-size bounds L*, U* | S24 §1, Prop 4 |
| HJB/Riccati, optimal speed = AC + signal | S25 pp. 9–12 |
| Blinded-ID ablation 54 % | S26 §3 |
| Fig 6.1 trading record; DM/V example error; equilibrium formula error; VB code bug | S01 pp. 108, 278–279, 245, 291–292 |
| First-passage P(τ<∞) = exp(−2a\|ν\|/σ²); inverse-Gaussian density; MAN calibration | S27 p. 17 (rendered), Tables III–IV |
| Zero-inflated exponential flows; E[V^Δ] closed form; exposure decomposition | S29 eqs 2.6–2.16, Prop 1; Figs 1–2 p. 21, Fig 8 p. 36 (rendered) |
| Flash Boys facts: Spread Networks 13 ms; Thor 350 µs; IEX 350 µs coil; Gates dark-pool test | S30 Ch. 1, 2, 4, 6 |
| JPM algo share; HSBC Fig 4 short/long-vol ratio March 2020; operational envelope | S31 pp. 4, 10 (rendered), Modular FX article |
| Spread components; Estimated Cost = Size × Sign × (Price − Benchmark); zero-sum; sampler limitation | S32 Ch. 14, Ch. 21 (p. 84), Ch. 1 |
| GA selection uses OOS; abstract/conclusion contradiction | S33 pp. 8, 10 (rendered) |
| W(i) = log(Σexp V_b / Σexp V_a); AUC table | S34 p. 4 (rendered), Table 3 |
| Q-measure GBM/VG direction ≈ 50 %; table mislabels | S35 Tables 1–17 |
| Kalman γ_{t+h} used at exit (P&L error) | S36 pp. 3, 5, 6 (rendered) |
| Prop 1 normalisation artefact; eq. 6 approximation | S38 pp. 3, 4, 7 (rendered) |
| EGARCH-X skew-t; PIT; Diks log-score table; counterfactual 15 days | S39 Table 1, App. II |
