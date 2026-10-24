#!/bin/sh
# Launch one MT5 Strategy Tester run headlessly (same mechanism as meta-trader-mcp's
# trigger_backtest, but with the modelling mode and execution delay exposed).
#
# Usage: tools/run_tester.sh <run_id> <Expert rel. to MQL5\Experts, no .ex5> <SYMBOL> <PERIOD>
#                            <MODEL> <FROM yyyy.mm.dd> <TO yyyy.mm.dd> <DEPOSIT> <LEVERAGE>
#                            <EXEC_DELAY> [Key=Value input overrides ...]
#   MODEL: 0 every tick (generated), 1 1-minute OHLC, 2 open prices, 4 every tick based on REAL ticks
#   EXEC_DELAY: 0 = ideal (no delay; label results "idealized"), -1 = random, N>0 = fixed N ms
#
# The user's MT5 window must be CLOSED (one terminal per install). The run blocks until
# the tester terminal exits (ShutdownTerminal=1) and then copies the tester + agent logs
# for this run into research/tester_runs/<run_id>/. Nothing here can place live orders:
# a Strategy Tester run trades only its own simulated account.
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
PREFIX="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5"
WINE_ROOT="/Applications/MetaTrader 5.app/Contents/SharedSupport/wine"
INSTALL="$PREFIX/drive_c/Program Files/MetaTrader 5"
RUN=$1 EXPERT=$2 SYM=$3 PER=$4 MODEL=$5 FROM=$6 TO=$7 DEP=$8 LEV=$9; shift 9
DELAY=$1; shift
STAGE="$PREFIX/drive_c/nexa_tester/$RUN"
OUT="$ROOT/research/tester_runs/$RUN"
mkdir -p "$STAGE" "$OUT"

if ps -axo command | grep -v grep | grep -q 'terminal64.exe'; then
  echo "ABORT: a terminal64.exe is already running (close MT5 first)" >&2; exit 3
fi

{
  printf '[Tester]\r\nExpert=%s\r\nSymbol=%s\r\nPeriod=%s\r\nModel=%s\r\n' "$EXPERT" "$SYM" "$PER" "$MODEL"
  printf 'FromDate=%s\r\nToDate=%s\r\nForwardMode=0\r\nDeposit=%s\r\nCurrency=USD\r\n' "$FROM" "$TO" "$DEP"
  printf 'Leverage=%s\r\nExecutionMode=%s\r\nOptimization=0\r\nVisual=0\r\n' "$LEV" "$DELAY"
  printf 'Report=C:\\nexa_tester\\%s\\report\r\nReplaceReport=1\r\nShutdownTerminal=1\r\n' "$RUN"
  if [ $# -gt 0 ]; then printf '[TesterInputs]\r\n'; for kv in "$@"; do printf '%s\r\n' "$kv"; done; fi
} > "$STAGE/tester.ini"
cp "$STAGE/tester.ini" "$OUT/tester.ini"

START=$(date '+%Y-%m-%d %H:%M:%S')
export DYLD_FALLBACK_LIBRARY_PATH="$WINE_ROOT/lib/external:$WINE_ROOT/lib:/usr/lib:/usr/local/lib"
export WINEPREFIX="$PREFIX" WINEDEBUG=-all
( cd "$INSTALL" && "$WINE_ROOT/bin/wine" terminal64.exe "/config:C:\\nexa_tester\\$RUN\\tester.ini" ) >/dev/null 2>&1 &
sleep 5
while ps -axo command | grep -v grep | grep -q 'terminal64.exe'; do sleep 10; done
END=$(date '+%Y-%m-%d %H:%M:%S')

day=$(date +%Y%m%d)
# Agents flush their own log only when they stop (~2 min idle). The pass/fail summary is
# also in the tester log, so waiting is optional: WAIT_AGENT=1 to wait for agent logs.
if [ "${WAIT_AGENT:-0}" = 1 ]; then
  while ps -axo command | grep -v grep | grep -q 'metatester64.exe'; do sleep 5; done
fi
for f in "$INSTALL/Tester/logs/$day.log" "$INSTALL"/Tester/Agent-*/logs/$day.log "$INSTALL/logs/$day.log"; do
  [ -f "$f" ] || continue
  n=$(echo "$f" | sed 's|.*/Tester/\(Agent[^/]*\)/logs/.*|\1|; s|.*/Tester/logs/.*|tester|; s|.*/logs/.*|terminal|')
  python3 - "$f" "$OUT/$n.log" <<'EOF'
import sys
b = open(sys.argv[1], 'rb').read()
t = b.decode('utf-16') if b[:2] in (b'\xff\xfe', b'\xfe\xff') else b.decode('utf-8', 'replace')
open(sys.argv[2], 'w').write(t.replace('\r\n', '\n'))
EOF
done
cp "$STAGE"/report* "$OUT/" 2>/dev/null
printf 'run=%s\nstart=%s\nend=%s\nexpert=%s symbol=%s period=%s model=%s from=%s to=%s deposit=%s leverage=%s delay=%s\n' \
  "$RUN" "$START" "$END" "$EXPERT" "$SYM" "$PER" "$MODEL" "$FROM" "$TO" "$DEP" "$LEV" "$DELAY" > "$OUT/RUN.txt"
echo "done $RUN ($START -> $END)"
