#!/bin/sh
# Pepperstone H1 history for the Strategy Factory, via the Strategy Tester (the GUI
# terminal is unstable here; tester runs are not). NEXA_BarExport with
# InpExportIntraday=false writes only H1 + D1. Model 2 (open prices): bars only, no tick
# generation. Chunks of ~3 years (a 16-year run dies during data preparation). Each chunk
# is accepted only on its own "Test passed" line (timestamped after its start) and
# retried up to 3 times. Chunks are concatenated later with duplicate bars dropped.
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
C="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/$USER/AppData/Roaming/MetaQuotes/Terminal/Common/Files"
D="$ROOT/data/pepperstone/factory_h1"
mkdir -p "$D"
for SYM in ${SYMS:-EURUSD GBPUSD USDJPY XAUUSD XAGUSD}; do
  for spec in 2017.01.01:2020.01.01 2020.01.01:2023.01.01 2023.01.01:2026.09.26; do
    FROM=${spec%%:*}; TO=${spec##*:}; TAG="${SYM}_${FROM%%.*}"
    [ -f "$D/PEPPERSTONE_${TAG}_H1.csv" ] && { echo "skip $TAG"; continue; }
    ok=0
    for try in 1 2 3; do
      RUN="PS_FH1_${TAG}_t$try"
      rm -f "$C/NEXA_Bars_${SYM}_H1.csv" "$C/NEXA_Bars_${SYM}_D1.csv"
      "$ROOT/tools/run_tester.sh" "$RUN" 'Advisors\NEXA_BarExport' "$SYM" H1 2 "$FROM" "$TO" 50000 200 0 \
         InpExportIntraday=false InpWarmupH1=10 InpWarmupD1=10 >/dev/null
      S=$(grep start= "$ROOT/research/tester_runs/$RUN/RUN.txt" | awk '{print $2}')
      if awk -F'\t' -v s="$S" '$3>=s' "$ROOT/research/tester_runs/$RUN/tester.log" | grep -q "Test passed" \
         && [ -f "$C/NEXA_Bars_${SYM}_H1.csv" ]; then
        mv "$C/NEXA_Bars_${SYM}_H1.csv" "$D/PEPPERSTONE_${TAG}_H1.csv"; ok=1; break
      fi
    done
    echo "$(date '+%H:%M:%S') $TAG ok=$ok"
  done
done
(cd "$D" && shasum -a 256 *.csv > SHA256SUMS)
echo FH1_DONE
