# Decision contract and reason-code audit (2026-09-27)

Source of the contract: research master §73–74 (`uploads/NEXA_COMPLETE_RESEARCH_MASTER.md`).
Compared against: `NEXA_EA.mq5`, `NEXA_Intelligence.mqh`, `NEXA_Risk.mqh`, `NEXA_FOMC.mqh`, and `nexa_schema_v1.json` (Trade DNA v1.0).
**No code or schema was changed by this audit.**

## 1. Decision contract fields

| Master §73 field | Where it lives in v1.0 | Status |
|---|---|---|
| symbol | `symbol` | PRESENT |
| direction | `direction` | PRESENT |
| trade_allowed | `event` (OPEN vs DECISION) + `reason` | PRESENT (implicit) |
| confidence | `composite_score`, `quality_score` | PRESENT (rule-based score, not a probability) |
| p_tp_before_sl | `ai_raw_p` (raw; `calibration_id=NONE`) | PARTIAL: raw model output, not calibrated. No model exists, so it is always −1 |
| expected_R | none (`target_r` is the target, not the expectation) | **MISSING** |
| entry / stop / target | `entry_intended`, `entry_actual`, `sl_price`, `tp_price` | PRESENT |
| risk | `lots`, `risk_dist` | PARTIAL: realised risk % of equity is not a column |
| regime | `regime_trend`, `regime_vol`, `regime_transitioning` | PRESENT |
| strategy | `strategy_id`, `liq_setup` | PRESENT |
| adversarial_result | only inside `reason` when it fails | **MISSING as a column** |
| execution_quality | `slippage_points` (post-fill only) | PARTIAL |
| news_risk | `f47 newsRiskActive` | PRESENT (flag only) |
| portfolio_risk | only inside `reason` when a cap blocks | **MISSING as a column** |
| reason_codes | `reason` (one code per row) | PRESENT (single code, not a list) |

## 2. Reason codes: spec vocabulary vs what the EA actually emits

| Master §74 code | EA equivalent (verified in source) |
|---|---|
| SPREAD_TOO_HIGH | `NO_TRADE_SPREAD_TAX_<pct>` |
| NEWS_TOO_CLOSE | `NO_TRADE_NEWS_RISK_WINDOW`, `FOMC_WINDOW_<date>_<kind>`, `FOMC_SCHEDULE_STALE_FAILCLOSED` |
| CORRELATION_EXCESS | `CORRELATION_BLOCK_*` |
| STRATEGY_HEALTH_LOW | `SURVIVAL_PAUSED_EXPECTANCY_<x>` |
| ADVERSARIAL_FAIL | `ADV_FAIL_{INVALID_STOP_DISTANCE, STRESSED_SPREAD_TOO_LARGE_VS_STOP, CONTRADICTORY_SIGNALS, HISTORICAL_BUCKET_POOR, STOP_TOO_TIGHT_VS_ATR}` |
| REGIME_UNCERTAIN | no single code; handled by the quality-score points and the HTF-conflict veto |
| EXPECTED_VALUE_NEGATIVE | not emitted (no EV estimate exists before a calibrated model) |
| LIQUIDITY_SWEEP / MSS_CONFIRMED / … (positive) | not emitted as codes; encoded in the features `f32..f45` |

Other codes the EA emits that the spec lacks: `MIN_LOT_EXCEEDS_HARD_RISK_CEILING`, `DRAWDOWN_THROTTLE_BELOW_MIN_LOT`, `EXPOSURE_CAP_*`, `PREFLIGHT_*` (9 variants), `NO_TRADE_AI_UNAVAILABLE_FAILCLOSED`, `NO_TRADE_AI_DISAGREES`, `NO_TRADE_INVALID_QUOTE`, `NO_TRADE_NO_QUALIFIED_LIQUIDITY_EVENT_*`.

**Decision:** keep the EA's codes as they are. Renaming them would change the meaning of the `reason` column mid-schema. A mapping layer belongs in research code if needed.

## 3. Required schema change (PROPOSED, NOT IMPLEMENTED)

Closing the MISSING rows needs Trade DNA **v1.1**, append-only (f00..f47 untouched, existing column order untouched):

| New column | Type | Written on | Meaning |
|---|---|---|---|
| `adversarial_result` | string | DECISION/OPEN | `ADV_PASS` or the `ADV_FAIL_*` code |
| `risk_pct_requested` | double | OPEN | InpRiskPercent after the drawdown throttle |
| `risk_pct_final` | double | OPEN | loss-at-stop / equity × 100 after lot normalisation |
| `portfolio_exposure_ccy_max` | int | OPEN | max same-currency net exposure after this trade (min-lot units) |
| `portfolio_corr_max` | double | OPEN | max absolute correlation vs open NEXA positions |
| `expected_r` | double | OPEN | calibrated EV in R (−999 until a calibrated model exists) |
| `reason_codes` | string | all | `|`-separated list of every gate outcome, not just the first failure |

Required with that bump: `SCHEMA_VERSION` and `SchemaHeader()` in MQL5, a new `nexa_schema_v1_1.json`, updates to `nexa_ingest`/`nexa_validate` (`SUPPORTED_SCHEMA_VERSIONS`), parity and ingest tests, MetaEditor compile, and a fresh tester run. **Needs human approval before implementation.**
