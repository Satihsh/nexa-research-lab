# PRE-REGISTRATION H-ICE-FEAS: can the NEXA recorder tape see iceberg-like refills? (data-quality / feasibility only)

**Status: BINDING.**
- User approval 2026-10-21: "all four, do it" (proposal P4 in `../INSTITUTIONAL_PATTERNS_REVIEW_2026-10-21.md`).
- **Written before any of the qualifying sessions exist.** No tape statistic for this question has been computed.
- **No price-direction statistic is computed in this test.** Any "follow the iceberg" rule needs its own pre-registration (the literature predicts iceberg size, not direction: Zotikov & Antonov 2019; Frey & Sandås 2017).

## 1. Data
- NEXA recorder files from the cloud VM (`gs://…/nexa_atas/recorder/{ES_M1,NQ_M1}/tape_<session>.csv`), header
  `received_utc,trade_time,side,volume,first_price,last_price,prev_bid,prev_bid_size,prev_ask,prev_ask_size,prints`.
- Feed: dxFeed 15-minute delayed (free), aggregated trades (ATAS cumulative trades).
- **Qualifying session:** a Topstep session file whose RTH part (09:30–15:59 ET by `trade_time`) has ≥ 1 trade row in ≥ 95 % of RTH minutes, for that instrument.
- **Run when:** the first 10 qualifying sessions per instrument exist, counting sessions that start on or after 2026-10-21. Expected ≈ 2026-11-04 (VM auto-stop 2026-11-06). If fewer than 10 exist by the stop, run on what exists and label it INSUFFICIENT.

## 2. Definitions (RTH rows only)
- Aggressor rows: side ∈ {BUY, SELL}.
- **Quote-valid row:** prev_bid > 0, prev_ask > prev_bid, prev_bid_size > 0, prev_ask_size > 0.
- **Iceberg candidate (refill proxy):** a quote-valid aggressor row that did not move price through the level and traded more than was shown:
  - BUY: first_price = last_price = prev_ask and volume > prev_ask_size;
  - SELL: first_price = last_price = prev_bid and volume > prev_bid_size.
- Delay = received_utc − trade_time (seconds).

## 3. Measures (per instrument, per session, and pooled)
- Rows, aggressor share, quote-valid share, rows with received_utc going backwards, delay median / p95.
- Candidates per session; candidates as a share of aggressor rows; median excess (volume − displayed size); share of candidates that are the same price and side as the previous candidate within 10 s (repeat refills).

## 4. Verdict (per instrument)
- **FEASIBLE:** quote-valid share ≥ 99 % **and** median ≥ 20 candidates per qualifying session.
- **NOT FEASIBLE:** otherwise (the free delayed tape cannot support iceberg work; MBO data would be required).
- **INSUFFICIENT:** fewer than 10 qualifying sessions.

## 5. Code, freeze
- `iceberg_feas.py` (reads local copies of the tape files; standard library + numpy). Unit tests `test_iceberg_feas.py` on synthetic rows: RTH filter by trade_time (ET, DST-aware), quote validity, candidate definition both sides, qualifying-session rule, repeat-refill rule, verdict thresholds. Hash before the run.
