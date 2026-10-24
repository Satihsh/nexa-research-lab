#!/bin/sh
# Engineering fix D-PARTIAL-AFTER-BE (2026-10-03): run a position-management test harness in the
# Strategy Tester. Places NO orders (the harness only evaluates NexaManageStep). Installs the
# binary under MQL5\Experts\NEXA_EngFix\ -- never under Advisors\ and never over a deployed EA.
#
# Usage: sh research/engfix/run_pmgmt_harness.sh <unit name in build/, no .ex5> <run id> <mqh used>
#   e.g. sh research/engfix/run_pmgmt_harness.sh NEXA_PositionMgmtTest pmgmt_harness NEXA_PositionMgmt.mqh
set -eu
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
UNIT=$1 RUN=$2 MQH=$3
MT5="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5"
C="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/$USER/AppData/Roaming/MetaQuotes/Terminal/Common/Files"
DEST="$MT5/Experts/NEXA_EngFix"
OUT="$ROOT/research/engfix/runs/$RUN"
RES=nexa_pmgmt_mql5_results.csv
[ -f "$ROOT/build/$UNIT.ex5" ] || { echo "missing build/$UNIT.ex5" >&2; exit 2; }
mkdir -p "$DEST" "$ROOT/research/engfix/runs"
cp "$ROOT/build/$UNIT.ex5" "$DEST/$UNIT.ex5"
rm -f "$C/$RES"
"$ROOT/tools/run_tester.sh" "ENGFIX_$RUN" "NEXA_EngFix\\$UNIT" EURUSD M1 2 2024.01.08 2024.01.12 50000 200 0 >/dev/null
rm -rf "$OUT"; mv "$ROOT/research/tester_runs/ENGFIX_$RUN" "$OUT"
[ -f "$C/$RES" ] && mv "$C/$RES" "$OUT/mql5_results.csv"
{
  echo "label=ENGINEERING REGRESSION -- not research evidence"
  echo "unit=$UNIT"
  echo "mqh=$MQH"
  echo "mqh_sha256=$(shasum -a 256 "$ROOT/$MQH" 2>/dev/null | cut -d' ' -f1)"
  echo "harness_ex5_sha256=$(shasum -a 256 "$ROOT/build/$UNIT.ex5" | cut -d' ' -f1)"
} > "$OUT/PROVENANCE.txt"
if [ -f "$OUT/mql5_results.csv" ]; then
  echo "$RUN: $(tr -d '\r' < "$OUT/mql5_results.csv" | grep -c ',PASS$') PASS, $(tr -d '\r' < "$OUT/mql5_results.csv" | grep -c ',FAIL$') FAIL"
else
  echo "$RUN: NO RESULTS FILE (harness did not run)"; exit 1
fi
