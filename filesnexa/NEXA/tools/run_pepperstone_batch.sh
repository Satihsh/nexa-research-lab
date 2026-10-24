#!/bin/sh
# Pepperstone NEXA batch, CHUNKED. A single 2.7-year tester run kills the terminal during
# data preparation on this 8 GB machine (no MT5 log line; process disappears); a 3-month
# run passes in ~35 s. So window A runs as calendar-quarter chunks.
#
# Per chunk: NEXA_EA, then NEXA_BarExport with IDENTICAL settings; outputs moved to
# data/pepperstone/tester/ with explicit PEPPERSTONE_ names. Default NEXA inputs.
#   Window A chunks: Model 0 (every tick GENERATED from M1 - Pepperstone has no real
#                    ticks before 2026-08-28; labelled, not hidden)
#   Window B:        2026.08.28-2026.09.26, Model 4 (every tick based on REAL ticks)
# Chunk effects (documented): the EA re-initialises at each chunk start (liquidity
# events rebuilt by causal replay are tagged RECONSTRUCTED), and any open position is
# closed by the tester at chunk end.
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
C="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/$USER/AppData/Roaming/MetaQuotes/Terminal/Common/Files"
D="$ROOT/data/pepperstone/tester"
mkdir -p "$D"
SYMS=${SYMS:-"GBPUSD EURUSD USDJPY XAUUSD"}
CHUNKS=${CHUNKS:-"A2024Q1:2024.01.01:2024.04.01:0 A2024Q2:2024.04.01:2024.07.01:0 A2024Q3:2024.07.01:2024.10.01:0 A2024Q4:2024.10.01:2025.01.01:0 A2025Q1:2025.01.01:2025.04.01:0 A2025Q2:2025.04.01:2025.07.01:0 A2025Q3:2025.07.01:2025.10.01:0 A2025Q4:2025.10.01:2026.01.01:0 A2026Q1:2026.01.01:2026.04.01:0 A2026Q2:2026.04.01:2026.07.01:0 A2026Q3:2026.07.01:2026.08.28:0 B:2026.08.28:2026.09.26:4"}
for SYM in $SYMS; do
  for spec in $CHUNKS; do
    W=$(echo "$spec" | cut -d: -f1); FROM=$(echo "$spec" | cut -d: -f2)
    TO=$(echo "$spec" | cut -d: -f3); MODEL=$(echo "$spec" | cut -d: -f4)
    TAG="${SYM}_${W}"
    if [ -f "$D/PEPPERSTONE_NEXA_TradeDNA_$TAG.csv" ]; then echo "skip $TAG (exists)"; continue; fi
    rm -f "$C/NEXA_TradeDNA_$SYM.csv"
    "$ROOT/tools/run_tester.sh" "PS_NEXA_$TAG" 'Advisors\NEXA_EA' "$SYM" M1 "$MODEL" "$FROM" "$TO" 50000 200 250 >/dev/null
    if grep -q "Test passed" "$ROOT/research/tester_runs/PS_NEXA_$TAG/tester.log" 2>/dev/null && [ -f "$C/NEXA_TradeDNA_$SYM.csv" ]; then
      mv "$C/NEXA_TradeDNA_$SYM.csv" "$D/PEPPERSTONE_NEXA_TradeDNA_$TAG.csv"
    else
      echo "$(date '+%H:%M:%S') FAILED $TAG (no 'Test passed' or no DNA)"; continue
    fi
    "$ROOT/tools/run_tester.sh" "PS_BARS_$TAG" 'Advisors\NEXA_BarExport' "$SYM" M1 "$MODEL" "$FROM" "$TO" 50000 200 250 >/dev/null
    for tf in M1 M5 M15 H1 D1; do
      [ -f "$C/NEXA_Bars_${SYM}_$tf.csv" ] && mv "$C/NEXA_Bars_${SYM}_$tf.csv" "$D/PEPPERSTONE_${SYM}_${tf}_tester_$W.csv"
    done
    echo "$(date '+%H:%M:%S') ok $TAG rows=$(($(wc -l < "$D/PEPPERSTONE_NEXA_TradeDNA_$TAG.csv") - 1))"
  done
done
(cd "$D" && shasum -a 256 *.csv > SHA256SUMS)
echo BATCH_DONE
