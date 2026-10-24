# NEXA MASTER SPECIFICATION

## 1. PROJECT IDENTITY

Project: NEXA Autonomous Trading AI

Primary target:
Production-grade MetaTrader 5 Expert Advisor written in MQL5.

NEXA is an autonomous trading research and execution architecture designed
to analyze markets, generate trade hypotheses, validate them, manage risk,
execute trades, learn from outcomes, and continuously validate strategy
survival.

The AI development system is separate from the live MT5 execution system.

The development system consists of:

- GPT-6 Astra — Principal Architect / Builder
- Claude Opus 5.5 — Adversarial Auditor / Independent Co-Architect
- Deterministic verification — final authority

---

## 2. CORE PRINCIPLE

Evidence beats confidence.

Tests beat opinions.

Observed market data beats narrative.

Deterministic risk controls beat AI decisions.

No model may declare success merely because its reasoning sounds plausible.

---

## 3. DUAL-AGENT DEVELOPMENT MODEL

### Astra

Role:

- Principal architect
- Lead implementation agent
- System designer
- MQL5 builder
- Quantitative reasoning agent
- Integration owner

Astra proposes architecture, writes implementation changes, explains
technical decisions, and responds to valid objections.

### Opus

Role:

- Adversarial auditor
- Independent co-architect
- Quantitative reviewer
- MQL5 reviewer
- Risk auditor
- Leakage and validation auditor

Opus must actively attempt to break Astra's proposals.

Opus must not agree merely because Astra is confident.

### Final Authority

Neither Astra nor Opus has final authority.

Final acceptance requires deterministic evidence:

- Compiler result
- Automated tests
- Regression tests
- Schema validation
- Data-quality validation
- Risk-invariant tests
- MT5 Strategy Tester evidence
- Walk-forward validation
- Out-of-sample validation
- Execution validation where applicable

---

## 4. NEXA RESEARCH ENGINES

NEXA may incorporate the following analytical domains:

1. Market Data
2. Market Microstructure
3. Liquidity Events
4. Market Structure
5. Displacement
6. SMC / ICT / Price Action
7. BTMM / Market Cycle
8. Camarilla
9. Quantitative Analysis
10. Session / Killzone
11. Market Regime
12. Volatility / Tail Risk
13. Macro / News
14. Central Bank / Official Sector
15. Intermarket Analysis
16. Behavioral Analysis
17. Strategy Factory
18. AI / ML / Meta-labeling
19. Market Narrative Graph
20. Evidence vs Interpretation
21. Adversarial Analysis
22. Expectancy Analysis
23. Portfolio / Capital Allocation
24. Risk Management
25. Execution
26. Position Management
27. Trade DNA / Learning
28. Research / Validation
29. Strategy Survival / MLOps
30. MT5 Control / Observability

These engines must not be treated as independent voting systems when
their features represent overlapping measurements of the same market
phenomenon.

---

## 5. MARKET-LIQUIDITY FRAMEWORK

A central NEXA research hypothesis is:

Liquidity event → reaction.

A commonly observed cycle may include:

Accumulation
→ Liquidity build
→ Sweep / manipulation
→ Structure shift
→ Displacement
→ Distribution
→ Target liquidity

This is a research framework, not an assertion that a specific institution
is intentionally "hunting retail traders."

The implementation must use observable market behavior.

---

## 6. EXISTING NEXA ENGINEERING STATE

Existing validated work must NOT be discarded or unnecessarily rebuilt.

Stages 0–5 already contain engineering work.

The development agents must inspect the existing repository and build
manifest before modifying the architecture.

The current research state must be preserved.

The system must continue from the existing state rather than restarting
the project.

---

## 7. DATA PRINCIPLES

Historical market data must be real.

Never fabricate:

- OHLC
- tick data
- volume
- spread
- Trade DNA
- labels
- trades
- model predictions
- performance
- backtest results

Raw source data must be preserved.

Derived datasets must be reproducible.

Provider datasets must not be silently merged when their construction,
pricing, timezone, or market conventions differ.

All transformations must be documented.

---

## 8. MULTI-TIMEFRAME DATA

Where data permits, NEXA may derive:

- M1
- M5
- M15
- H1
- H4
- D1

from a consistent source.

Higher-timeframe aggregation must not introduce look-ahead information.

Timestamp conventions must be explicit.

Session boundaries and daily boundaries must be explicitly defined.

---

## 9. TRADE DNA

Trade DNA must represent actual observed trade or market episodes.

Trade DNA must contain only information that would have been available
at the relevant decision time.

No future information may leak into features.

Execution outcomes must not be used as decision-time features.

The distinction between:

- decision-time information
- execution information
- outcome information

must remain explicit.

---

## 10. LABELING

Labels must follow the validated NEXA labeling methodology.

Relevant concepts include:

- TP_WIN
- SL_LOSS
- BREAKEVEN_STOP
- TIME_EXIT
- TIMEOUT
- AMBIGUOUS
- UNLABELLED
- INVALID

The existing documented ambiguity and fill-bar policies must be preserved
unless a new change is explicitly justified and independently validated.

Partial-close behavior must not be silently misrepresented.

---

## 11. MACHINE LEARNING

ML models must be evaluated chronologically.

Avoid random train/test splits for time-series trading validation unless
there is a specific justified reason.

Required concepts include:

- Training
- Validation
- Out-of-sample testing
- Walk-forward validation
- Regime analysis
- Calibration
- Model health
- Drift monitoring
- Strategy survival

A high in-sample result is not evidence of a durable trading edge.

---

## 12. LEAKAGE PREVENTION

No feature may use information unavailable at the decision timestamp.

No label may leak into features.

No future OHLC information may influence a historical decision.

No future spread, execution result, or trade outcome may be used
incorrectly as a decision-time feature.

All temporal joins must be audited.

---

## 13. RISK INVARIANTS

These controls are hard constraints.

AI agents may NOT override them.

Current baseline constraints include:

- Initial risk target: 0.30%
- Hard risk ceiling: 1.00%
- Maximum daily loss: 2%
- Maximum drawdown: 10%
- Maximum trades per day: 10
- No martingale
- No grid recovery
- Margin protection
- Exposure protection
- Correlation protection
- Spread / volatility protection
- Emergency stop
- Fail-closed behavior

These values must not be increased simply to improve simulated returns.

Any proposed change requires explicit engineering justification,
tests, and review.

---

## 14. EXECUTION

Execution logic must account for real broker constraints including:

- Digits
- Tick size
- Tick value
- Volume minimum
- Volume maximum
- Volume step
- Stop distance
- Freeze level
- Spread
- Slippage
- Margin
- Filling mode
- Execution mode
- Asynchronous execution
- Partial fills
- Partial closes
- Restart recovery

NormalizeDouble alone must not be treated as sufficient broker
constraint validation.

---

## 15. MQL5 ENGINEERING

All MQL5 changes must be compatible with the actual target MetaEditor
environment.

The compiler is authoritative for compilation validity.

Agents must consider:

- MQL5 type semantics
- Arrays
- Handles
- Indicator lifecycle
- Event handlers
- Position state
- Order state
- Deal state
- Async trade transactions
- Restart behavior
- State recovery
- Symbol properties
- Broker constraints

No code is accepted merely because it looks correct.

---

## 16. ADVERSARIAL REVIEW

For every significant Astra proposal, Opus should attempt to identify:

1. Logical defects
2. Mathematical defects
3. Data defects
4. Leakage
5. Overfitting
6. Execution defects
7. Risk defects
8. MQL5 defects
9. Recovery defects
10. Regression risks
11. Hidden assumptions
12. Unsupported claims

Findings must be classified:

CRITICAL
HIGH
MEDIUM
LOW
INFORMATIONAL

CRITICAL and HIGH findings require:

- Finding
- Evidence
- Failure mechanism
- Impact
- Required correction
- Verification test

---

## 17. DEBATE PROTOCOL

The development loop is:

1. Astra proposes.
2. Opus independently attacks the proposal.
3. Astra responds to each material objection.
4. Astra proposes corrections where warranted.
5. Opus re-audits the correction.
6. Deterministic tests execute.
7. Compiler executes where applicable.
8. Failed gates return the issue to the agents.
9. Successful gates permit integration.
10. The accepted change is recorded.

Neither agent wins because it argues better.

The evidence determines acceptance.

---

## 18. NO MAJORITY VOTE

Three models agreeing does not make something true.

Two models disagreeing does not make something false.

The decision hierarchy is:

1. Hard safety constraints
2. Deterministic verification
3. Reproducible evidence
4. Validated data
5. Quantitative analysis
6. Engineering reasoning
7. Model judgment

---

## 19. NO FABRICATION

Agents must explicitly state:

UNKNOWN

NOT AVAILABLE

NOT VERIFIED

or

BLOCKED

when evidence is missing.

Never manufacture a plausible answer to make the project appear complete.

---

## 20. PERFORMANCE CLAIMS

NEXA must not claim:

- Guaranteed profitability
- Guaranteed win rate
- Guaranteed return
- Guaranteed AI superiority
- Guaranteed market prediction

Performance claims require documented evidence from the appropriate
validation procedure.

Win rate alone is insufficient.

Relevant measures may include:

- Expectancy
- Profit factor
- Drawdown
- Risk-adjusted return
- MFE
- MAE
- Calibration
- Stability across regimes
- Out-of-sample performance
- Execution sensitivity
- Strategy survival

---

## 21. RESEARCH STATE

If a required dataset, validation result, model, or execution result
does not exist, the system remains in research-only status.

Engineering completion does not equal trading validation.

---

## 22. CHANGE MANAGEMENT

Every significant change must identify:

- What changed
- Why it changed
- Files affected
- Expected behavior
- Risks
- Tests required
- Test results
- Regression impact

Do not silently modify unrelated systems.

Do not rewrite validated components without justification.

---

## 23. REPOSITORY SAFETY

Before modifying existing NEXA code:

1. Inspect the current repository.
2. Inspect the build manifest.
3. Inspect the relevant tests.
4. Identify immutable or protected files.
5. Create a reversible change.
6. Run the relevant tests.
7. Compile where applicable.

Never delete validated work simply to simplify implementation.

---

## 24. CURRENT DEVELOPMENT OBJECTIVE

The immediate objective is NOT to create a hypothetical profitable
trading system.

The immediate objective is to build a rigorous autonomous NEXA
engineering and research system that can:

- inspect the existing NEXA repository
- continue from the current research state
- ingest validated market data
- construct Trade DNA
- validate features and labels
- develop models
- perform walk-forward and OOS validation
- identify defects
- debate architectural decisions
- test MQL5 implementation
- preserve hard risk controls
- produce reproducible evidence

Only evidence can determine whether a strategy deserves promotion.

---

## 25. FINAL PRINCIPLE

NEXA should optimize for:

ROBUSTNESS

REPRODUCIBILITY

SURVIVABILITY

RISK CONTROL

EVIDENCE

rather than optimizing solely for:

WIN RATE

BACKTEST PROFIT

SHORT-TERM RETURNS

or

MODEL CONFIDENCE.
