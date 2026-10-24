# NEXA Agent Lab

**A pre-registered, AI-assisted research lab for testing intraday futures trading ideas honestly, including the ones that fail.**

NEXA asks one question: *is there a simple, mechanical rule for NQ / ES index futures that survives a fair out-of-sample test after costs?* It is built by one person working with Claude Code as a research partner. Every idea is written down and frozen **before** any data is touched, then tested once.

> **Current answer: not yet.** About 188 trials so far. Every intraday ES/NQ rule tested has failed or been inconclusive, and the negative results are kept, not hidden. This is research software, not financial advice, and not a signal service.

---

## Why this exists

Trading content online is full of strategies that "work" on the chart they were found on. NEXA is a guard rail against that:

- **Pre-registration.** Each hypothesis gets a `PREREG_*.md` with the rule, data, statistic and pass bar fixed in advance. Its sha256 is recorded before the first run.
- **One shot per test.** No re-runs, no parameter tuning on the test window. Deviations are logged in `DEVIATIONS_*.md`.
- **Frozen code.** Test code is hashed. Before every cloud backtest, the hash of the file in the QuantConnect editor is checked against the local frozen copy.
- **Controls and planted effects.** Random-direction and placebo controls are used where they apply. Synthetic tests with a planted effect check that the pipeline can detect a real edge before it is trusted to report "no edge".
- **Costs first.** Results are judged net of commissions and slippage, in R-multiples or basis points.
- **A public ledger of failure.** `research/intelligence/NEXA_RESEARCH_LEDGER_2026-10-18.md` lists every trial and its verdict, including the embarrassing ones.

## What is in the repo

| Area | Path | What it is |
|---|---|---|
| Validation suite | `research/intelligence/validation/` | 42 pre-registrations, 31 result reports, 28 synthetic test suites, frozen QuantConnect algorithms, and the sha256 of every run log |
| Research ledger | `research/intelligence/NEXA_RESEARCH_LEDGER_*.md` | Every hypothesis, what it tested, and the verdict |
| Knowledge base | `research/knowledge/` | Structured notes on 39 academic and practitioner sources, mapped to testable claims |
| ATAS monitor | `atas/NexaMonitor/` | Read-only C# (.NET) indicator for the ATAS order-flow platform: session clock, rule checks, trade journal, expected-range and risk panel, market-data recorder. 126 console tests. It never places orders. |
| Cloud recorder | `atas/cloud/` | Scripts for a Windows cloud VM that records ES/NQ trades, order-book snapshots and volume-at-price, with a watchdog and a heartbeat that checks that data is actually being written |
| MT5 expert advisor | `filesnexa/NEXA/` | The original MetaTrader 5 system (MQL5), its safety audit, defect fixes and tester campaigns |
| Platform roadmap | `research/platform/`, `nexa_platform/` | Work toward a platform-agnostic engine (NautilusTrader) |

## Selected results

| Hypothesis | Market / period | Result | Verdict |
|---|---|---|---|
| H-SK28-OOS: a published 12-model NQ system, frozen and ported | NQ 2010–2022 (outside its build window) | −0.021R per trade after costs, n = 3,708, below the random-direction control | Rejected |
| H-GEX-RANGE: does SPX dealer gamma improve the daily range forecast? | NQ / ES 2015–2025 walk-forward | Real in-sample pattern, but no out-of-sample gain on NQ (−0.06 %) | Rejected |
| H-ORB30L: 30-minute opening-range breakout | NQ 2009–2023 OOS | +0.058R in-sample became −0.071R out of sample | Closed |
| Tokyo fix / intraday momentum / fix reversals | FX, gold | The effects are real gross, but smaller than retail costs | Rejected (net) |
| H-SWING: 20-market time-series momentum | 20 CME futures 2011–2026 | +5.5 %/yr net, Sharpe 0.43, CI touches zero | Inconclusive (closest so far) |

The full list is in the ledger.

**Not in the public copy:** raw market data and backtest run logs (data-vendor licences), third-party transcripts and unlicensed code, and personal session notes. Reports cite the hashes of the withheld logs, and some notes point to files that are kept private.

## How a test runs

1. **Idea.** Taken from a paper, a video, a repo or the knowledge base, and recorded as a claim.
2. **Pre-registration.** Rule, data, primary statistic and verdict thresholds are written down, hashed and approved.
3. **Synthetic tests.** Formulas, look-ahead guards, the verdict logic and a planted-effect check.
4. **Probe.** A one-month cloud run checks data shape, timing and runtime. Its results are not looked at.
5. **Run.** QuantConnect's free cloud tier, one backtest per year chunk. Each log is saved and hash-checked.
6. **Report.** The local stats script produces the verdict. The report and the ledger are updated whatever the outcome.

## Tooling

Python 3.12 (NumPy, pandas, scikit-learn, LightGBM), QuantConnect LEAN (cloud, free tier), C# / .NET 10 for ATAS, MQL5 for MetaTrader 5, Google Cloud for the recorder VM. Development is done with **Claude Code** as a pair researcher: it drafts pre-registrations, writes and tests code, runs backtests through the browser, and keeps a long-term memory of decisions and results across sessions.

## Ground rules the project enforces

- No automated order placement. NEXA tools are read-only.
- No spending on data, evaluations or subscriptions until an edge passes a pre-registered test.
- No scraping of paid data feeds and no reverse engineering of trading platforms.
- Negative results are published, not deleted.

## Status

Active. The next candidate test is drafted and awaiting approval. Contributions, critique and replication attempts are welcome: open an issue if you see a flaw in a test design.

## Disclaimer

Nothing here is investment advice. Futures trading carries substantial risk of loss. The results describe historical tests only.
