# S05: Balayan (2026), "An algorithmic framework for sustainable marketing audit and prioritization in consulting engagements: The PRISM-Bridge Model"
**File:** `An_algorithmic_framework_for_sustainable_marketing.pdf`. 10 pp.
**Publication:** Economics, Management and Sustainability 11(1):136–145, doi:10.14254/jems.2026.11-1.7.
**Author affiliation:** "Private Group, US".

| Field | Value |
|---|---|
| **Source type** | External research. Journal article: open access; a peer-review history is listed (received, revised, accepted). |
| **Evidence status** | **Unverified claim / conceptual.** The author explicitly says "no primary field experiment". The demonstration uses 30 *synthesized* initiatives. |
| **Domain** | Management consulting and marketing prioritisation (multi-criteria decision analysis). **NOT a markets or trading paper.** |
| **Processing** | All 10 pages read. Figure 2 and Table 2 (p. 6) were inspected visually. Figures 1 and 3 are diagrams whose content duplicates Table 1 and the text. |

## 1. Content
The framework is called PRISM-Bridge: **P**riority, **R**eadiness, **I**mpact, **S**equencing, **M**easurability.

**The scoring rubric** (Table 1, p. 5). Each criterion is scored 1–5, with Risk and Dependency inverted so that higher is better.

| Criterion | Weight |
|---|---|
| Market Impact | 0.20 |
| Sustainability / ESG Alignment | 0.15 |
| Implementation Effort | 0.15 |
| Evidence Confidence | 0.15 |
| Measurement Readiness | 0.15 |
| Risk Exposure | 0.10 |
| Dependency Load | 0.10 |

**Aggregation**
- Implied form: Score = Σ_k w_k s_k with Σ w_k = 1. A linear additive value model.
- The weights come from a **simplified AHP**. The consistency-ratio / eigenvector step is *deliberately skipped* in favour of "heuristic consistency checks" (p. 5).

**Process**
1. Build an intervention register; each item needs a measurable anchor, an owner and a mechanism.
2. Score the items.
3. Build a 3-phase roadmap: foundation → acceleration → scale. Dependency-heavy and data-infrastructure items go to the foundation phase.
4. Select a quick-win portfolio. A quick win needs rapid time-to-value, low dependency and high measurement readiness; at least one must improve tracking capability.

**Results (illustrative only):** Tier 1: 10 items, average score 1.05; Tier 2: 12 items, 0.62; Tier 3: 8 items, 0.18 (Table 2).

## 2. Mathematical notes and critique
**AHP background** (standard knowledge, not derived in the paper):
- Weights are the principal eigenvector of a pairwise comparison matrix A.
- The consistency index is CI = (λ_max − n)/(n − 1); the consistency ratio is CR = CI/RI, conventionally required to be < 0.10.
- The paper omits this step. Its weights are therefore asserted, not elicited with checked consistency.

**INFERENCE: internal inconsistency.**
- A weighted sum of 1–5 scores with weights summing to 1.00 must lie in [1, 5].
- The reported tier averages (1.05, 0.62, 0.18) lie outside that range.
- The normalisation actually used is not stated. UNKNOWN, unless the scores were rescaled in some undisclosed way.

**Other issues**
- The Conflict-of-Interest statement says "Both authors", but there is a single author.
- The results are generated from synthetic data and so cannot validate anything.

## 3. Relevance to NEXA
**There is no market, price or trading content.** Transferable governance ideas, at the level of INFERENCE:
1. **"Measurement readiness" as a gate.**
   - NEXA already applies the same principle: do not promote anything that cannot be measured.
   - Examples: the D-EXEC defect, the minimum-spread artefacts, OFI not measurable.
   - The paper offers a vocabulary for prioritising the research backlog.
2. **Prioritising a research backlog with dependency-aware sequencing.** For example, NAS100 data acquisition must precede NAS100 research.
   - This is possibly useful for ordering `RESEARCH_HYPOTHESIS_BACKLOG.md`.
   - It is **not evidence about markets**.
3. **Warning example.** Weighted-sum scores without consistency checks are easily manipulated; the author admits this (p. 7). The same risk applies to hand-weighted multi-engine "confluence scores" in trading.

**Cross-references:** none in the market corpus. It shares the "multi-criteria scoring" pattern with the practitioner confluence systems (S07 BTMM, S08 guidebook) only in form.
