#!/bin/sh
# Re-run every tester run that research/nexa_tester_verify.py classifies FAILED, up to
# MAX_ATTEMPTS times, re-verifying from each run's own evidence after every attempt.
# Partial outputs of a failed run are renamed FAILEDRUN_* (never deleted, never reused).
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
PY="$ROOT/.venv-research/bin/python"
C="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/$USER/AppData/Roaming/MetaQuotes/Terminal/Common/Files"
D="$ROOT/data/pepperstone/tester"
V="$ROOT/research/reports/pepperstone/tester_verify.json"
MAX_ATTEMPTS=${MAX_ATTEMPTS:-3}
verify() { (cd "$ROOT/research" && "$PY" nexa_tester_verify.py tester_runs "$D" --out "$V" >/dev/null); }
failed() { "$PY" -c "import json;print('\n'.join(k for k,v in json.load(open('$V')).items() if v['status']=='FAILED' and 'SMOKE' not in k))"; }
attempt=1
verify
while [ $attempt -le "$MAX_ATTEMPTS" ]; do
  LIST=$(failed)
  [ -z "$LIST" ] && { echo "all runs verified PASSED"; break; }
  echo "attempt $attempt: $(echo "$LIST" | wc -l | tr -d ' ') failed runs"
  for RUN in $LIST; do
    KIND=$(echo "$RUN" | cut -d_ -f2); TAG=$(echo "$RUN" | cut -d_ -f3-); SYM=$(echo "$TAG" | cut -d_ -f1)
    W=$(echo "$TAG" | cut -d_ -f2)
    eval "$(grep -o '[a-z]*=[^ ]*' "$ROOT/research/tester_runs/$RUN/RUN.txt" | grep -E '^(model|from|to)=')"
    mv "$ROOT/research/tester_runs/$RUN" "$ROOT/research/tester_runs/FAILEDRUN_${RUN}_try$attempt"
    if [ "$KIND" = NEXA ]; then
      [ -f "$D/PEPPERSTONE_NEXA_TradeDNA_$TAG.csv" ] && mv "$D/PEPPERSTONE_NEXA_TradeDNA_$TAG.csv" "$D/FAILEDRUN_try${attempt}_PEPPERSTONE_NEXA_TradeDNA_$TAG.csv"
      rm -f "$C/NEXA_TradeDNA_$SYM.csv"
      "$ROOT/tools/run_tester.sh" "$RUN" 'Advisors\NEXA_EA' "$SYM" M1 "$model" "$from" "$to" 50000 200 250 >/dev/null
      [ -f "$C/NEXA_TradeDNA_$SYM.csv" ] && mv "$C/NEXA_TradeDNA_$SYM.csv" "$D/PEPPERSTONE_NEXA_TradeDNA_$TAG.csv"
      # a re-run NEXA chunk needs its own bar export too
      if [ ! -d "$ROOT/research/tester_runs/PS_BARS_$TAG" ]; then :; else
        mv "$ROOT/research/tester_runs/PS_BARS_$TAG" "$ROOT/research/tester_runs/SUPERSEDED_PS_BARS_${TAG}_try$attempt"; fi
      KIND=BARS; RUN="PS_BARS_$TAG"
    fi
    if [ "$KIND" = BARS ]; then
      for tf in M1 M5 M15 H1 D1; do
        [ -f "$D/PEPPERSTONE_${SYM}_${tf}_tester_$W.csv" ] && mv "$D/PEPPERSTONE_${SYM}_${tf}_tester_$W.csv" "$D/FAILEDRUN_try${attempt}_PEPPERSTONE_${SYM}_${tf}_tester_$W.csv"
        rm -f "$C/NEXA_Bars_${SYM}_$tf.csv"
      done
      [ -d "$ROOT/research/tester_runs/$RUN" ] && mv "$ROOT/research/tester_runs/$RUN" "$ROOT/research/tester_runs/FAILEDRUN_${RUN}_try$attempt"
      "$ROOT/tools/run_tester.sh" "$RUN" 'Advisors\NEXA_BarExport' "$SYM" M1 "$model" "$from" "$to" 50000 200 250 >/dev/null
      for tf in M1 M5 M15 H1 D1; do
        [ -f "$C/NEXA_Bars_${SYM}_$tf.csv" ] && mv "$C/NEXA_Bars_${SYM}_$tf.csv" "$D/PEPPERSTONE_${SYM}_${tf}_tester_$W.csv"
      done
    fi
    echo "$(date '+%H:%M:%S') re-ran $TAG"
  done
  verify
  attempt=$((attempt + 1))
done
echo "remaining failed:"; failed
(cd "$D" && shasum -a 256 PEPPERSTONE_*.csv > SHA256SUMS)
echo RERUN_DONE
