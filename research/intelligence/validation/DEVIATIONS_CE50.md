# Deviations and clarifications: H-CE50 (logged before any market data)

| # | When (UTC) | What | Effect on results |
|---|---|---|---|
| C-1 | 2026-10-23 (code build, pre-data) | Synthetic G1: 12/12 PASS (`run_tests.py test_ce50.py`, `.venv-ml`). Planted directional drift → VALIDATED; pure noise → not validated. Swing trailing applies only from the 15-minute block after confirmation (tested). The ES file differs only in the MODE line. | None |
| R-1 | 2026-10-22T16:20Z | **NQ run launched once** (user: "approve H-CE50 … run it on QuantConnect (NQ, ES)"). QC project **NEXA/CE50 38292473**; editor file read back = **9a1ae51e** (11,538 chars); compile BuildSuccess; backtest "CE50 NQ 9a1ae51e" **cb463b32…**. The ES in-page copy also hash-matched (20e3b454) before upload. | — |
| R-2 | 2026-10-22T16:24Z | NQ completed (215.2 s); log sha a843c0f7 = saved file. ES launched: editor hash **20e3b454**, backtest "CE50 ES 20e3b454" **75787582…**. | — |
| R-3 | 2026-10-22T16:29Z | ES completed (244.3 s); log sha b5388156 = saved file. NQ and ES REJECTED (CE50_REPORT.md). | — |
