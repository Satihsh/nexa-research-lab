#!/bin/sh
# Phase-2 historical M1 export from ALREADY-LOCAL Pepperstone history (no broad download).
# NEXA_BarExport on an M1 chart, Model 2 (open prices: bars only, no tick generation),
# half-year chunks. Each chunk is accepted only on its own "Test passed" line (timestamped
# after its start) and retried up to 3x. Outputs are gzipped with SHA-256 recorded.
# The local history base size is logged before and after as download evidence.
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
C="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/$USER/AppData/Roaming/MetaQuotes/Terminal/Common/Files"
BASE="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/bases/Pepperstone-Demo"
D="$ROOT/data/pepperstone/m1_history"
mkdir -p "$D"
LOG="$D/export_log.tsv"
[ -f "$LOG" ] || printf 'utc\tsymbol\tchunk\tstatus\ttries\tbase_bytes\n' > "$LOG"
base_bytes() { du -sk "$BASE" | cut -f1; }
echo "base_kb_before=$(base_bytes)"
for SYM in ${SYMS:-EURUSD GBPUSD USDJPY XAUUSD XAGUSD}; do
  for spec in ${CHUNKS:-2017.07.01:2018.01.01 2018.01.01:2018.07.01 2018.07.01:2019.01.01 2019.01.01:2019.07.01 2019.07.01:2020.01.01 2020.01.01:2020.07.01 2020.07.01:2021.01.01 2021.01.01:2021.07.01 2021.07.01:2022.01.01 2022.01.01:2022.07.01 2022.07.01:2023.01.01 2023.01.01:2023.07.01 2023.07.01:2024.01.01}; do
    FROM=${spec%%:*}; TO=${spec##*:}; TAG="${SYM}_$(echo "$FROM" | tr -d .)"
    [ -f "$D/PEPPERSTONE_${TAG}_M1.csv.gz" ] && { echo "skip $TAG"; continue; }
    ok=0; try=0
    while [ $try -lt 3 ] && [ $ok -eq 0 ]; do
      try=$((try + 1)); RUN="PS_M1H_${TAG}_t$try"
      for tf in M1 M5 M15 H1 D1; do rm -f "$C/NEXA_Bars_${SYM}_$tf.csv"; done
      "$ROOT/tools/run_tester.sh" "$RUN" 'Advisors\NEXA_BarExport' "$SYM" M1 2 "$FROM" "$TO" 50000 200 0 \
         InpExportIntraday=true InpWarmupM1=60 InpWarmupM5=320 InpWarmupM15=320 InpWarmupH1=320 InpWarmupD1=30 >/dev/null
      S=$(grep start= "$ROOT/research/tester_runs/$RUN/RUN.txt" | awk '{print $2}')
      if awk -F'\t' -v s="$S" '$3>=s' "$ROOT/research/tester_runs/$RUN/tester.log" | grep -q "Test passed" \
         && [ -s "$C/NEXA_Bars_${SYM}_M1.csv" ]; then
        for tf in M1 M5 M15 H1 D1; do
          gzip -c "$C/NEXA_Bars_${SYM}_$tf.csv" > "$D/PEPPERSTONE_${TAG}_$tf.csv.gz" && rm -f "$C/NEXA_Bars_${SYM}_$tf.csv"
        done
        ok=1
      fi
    done
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$SYM" "$FROM-$TO" "$([ $ok = 1 ] && echo PASSED || echo FAILED)" "$try" "$(base_bytes)" >> "$LOG"
    echo "$(date '+%H:%M:%S') $TAG ok=$ok tries=$try"
  done
done
echo "base_kb_after=$(base_bytes)"
(cd "$D" && shasum -a 256 *.csv.gz > SHA256SUMS)
echo M1H_DONE
