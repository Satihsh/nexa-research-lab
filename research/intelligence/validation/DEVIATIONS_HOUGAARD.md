# Deviations and clarifications: H-HOUGAARD (logged before any market data)

| # | When (UTC) | What | Effect on results |
|---|---|---|---|
| C-1 | 2026-10-22 (code build, pre-data) | Synthetic G1: 13/13 PASS (`run_tests.py test_hougaard.py`, `.venv-ml`). A synthetic market winning 62 % at +6/−9 earns +0.015R gross and −0.32R net at YM S1 → REJECTED, as the pre-registered break-even arithmetic predicts. The ES/YM files differ from main.py only in the MODE line. | None |
| R-1 | 2026-10-22T10:31Z | **NQ run launched once** (user: "Upload, verify the hash and run H-HOUGAARD (NQ, ES, YM)"). QC project **NEXA/HOUGAARD 38279481**; editor file read back via /api/v2/files/read = **230660be** (12,407 chars); compile BuildSuccess; backtest "HOUGAARD NQ 230660be" **7906f2ba…**. ES (27afa20d) and YM (003df236) in-page copies also hash-matched before upload. | — |
| R-2 | 2026-10-22T10:35Z | NQ completed (185.6 s); log sha f273f431 = saved file. ES launched: editor hash **27afa20d**, backtest "HOUGAARD ES 27afa20d" **26a4b172…**. | — |
| R-3 | 2026-10-22T10:39Z | ES completed (172.4 s); log sha ae9b52a3 = saved file. YM launched: editor hash **003df236**, backtest "HOUGAARD YM 003df236" **54c24b66…**. | — |
| R-4 | 2026-10-22T10:44Z | YM completed (205.7 s); log sha 286f1222 = saved file. All six cells REJECTED (HOUGAARD_REPORT.md). | — |
| N-1 | 2026-10-22 (after the results; no rerun) | **Interpretation note, not a rule change.** The percentage-scaled stops (NQ ≈ 2–5 pts, ES 3–6 ticks, YM 5–11 pts) are smaller than typical 1-minute ranges at the open, so the pre-registered stop-first tie rule decides most trades (win rates 2–9 %). The gross R is a pessimistic bound; the true win rate is unknown from minute bars. The verdict stands (costs alone need a 64–85 % win rate after 2021). Any tick-data re-test would be a new hypothesis. | Interpretation only |
