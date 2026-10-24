# S14 demo forward check: final report (closed 2026-10-19 00:5x +08, early, by user decision)

- **Decision:** the user, in chat on 2026-10-19: "Or we drop the S14 now, activate ATAS X", then "Can you do for me completely without any error?"
- **Why early:** the project moved to futures only (ATAS X + Topstep). This MT5 forex/gold EA has no role in that plan, and its cloud credit is re-used for an ATAS recording machine.
- **The planned minimum** (4 weeks or 100 fills, from 2026-10-12) was **not reached.** This is a partial record, not a verdict on execution quality over a full sample.

## What ran
- **EA:** NEXA_EA_S14 (ff30ac38) + NEXA_TickLogger (f1f847e8), production preset 1873bfe3.
- **Account:** Pepperstone demo <demo-account> ($200), on GCP VM `nexa-s14` (us-east4-c).
- **Live window:** 2026-10-12 open → 2026-10-16 close (one trading week; the weekend added no trades).

## Close-out steps (all verified)
1. MT5 closed **gracefully** inside the `nexa` session: a one-off Interactive scheduled task called CloseMainWindow (a plain taskkill was refused cross-session), and the task was removed after.
2. The tick logs, held open for the whole run, were released: EURUSD 61.0 MB, GBPUSD 116.1 MB, USDJPY 70.1 MB, XAUUSD 221.5 MB.
3. Final `NEXA_S14_Sync`: result 0. The bucket `gs://nexa-s14-<gcp-project>/s14/common_files/` holds 12 objects (468.31 MiB), sizes equal to the VM's.
4. Heartbeat alert policy 5663138342355737928 **disabled** (no false "missing" email).
5. VM `nexa-s14` **stopped** (TERMINATED). Its disk and the 5 daily snapshots (10-14…10-18) are kept until the 2026-12-08 teardown.
6. Local copy: `s14_final/` (DNA, MT5 logs; tick logs downloading separately).

## Result (19 closed trades)
- Source: `s14_final/common_files/NEXA_TradeDNA_*.csv`; per-trade list in `s14_final/s14_trades_summary.txt`.
- **Net R** = result_r − (round-trip commission − swap) / $ risk to the initial stop. result_r excludes costs (see memory nexa-dna-result-r-semantics).

| | Value |
|---|---|
| Trades | 19 (EURUSD 8, XAUUSD 7, GBPUSD 3, USDJPY 1) |
| Gross mean | **−0.235 R** (sum −4.46 R) |
| Net mean | **−0.387 R** (sum −7.34 R) |
| Wins / break-even / losses | 2 / 7 / 10 (one GBPUSD +3.38 R) |
| Slippage | **0 points on all 19 fills** (Pepperstone demo, market execution) |
| Commission as a share of risk | **0.15 R per trade on average** (EURUSD 0.17–0.35 R) |

## Reading
- **Consistent with every earlier verdict on this strategy** (Phase-3 V2 VAL negative, 8E rejected, exposure-cap no edge). A small sample, but nothing here contradicts them.
- **The cost lesson carries over to futures:**
  - with $0.30–$1.80 of risk per trade at 0.01 lot, a fixed commission eats 5–35 % of R;
  - stops that are very tight relative to costs cannot be profitable unless the win rate is high.
  - The same arithmetic is built into NEXA Monitor's what-if panel (break-even win rate) for MNQ/ES.
- **Demo fills had zero slippage.** That says nothing about live slippage; demo market execution fills at the quote.

## Remaining teardown (by 2026-12-08)
- Delete VM `nexa-s14` + disk, snapshot policy `nexa-s14-daily` and its snapshots.
- Bucket `nexa-s14-…`: keep or delete after the local copy is verified.
- Remove the viewer IAM bindings, OAuth client and the "GCP S14 (View Only)" connector.
- Script: `gcp_g2/05_cloudshell_teardown.sh`.
