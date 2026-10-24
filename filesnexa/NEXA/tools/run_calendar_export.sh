#!/bin/sh
# Run NEXA_CalendarExport (read-only MQL5 script) once in a LIVE terminal via MT5's
# [StartUp] config, then shut the terminal down. Uses the terminal's saved login; no
# credentials are passed or changed. Outputs are moved into data/pepperstone/calendar/<utc>/.
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
PREFIX="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5"
WINE_ROOT="/Applications/MetaTrader 5.app/Contents/SharedSupport/wine"
INSTALL="$PREFIX/drive_c/Program Files/MetaTrader 5"
C="$PREFIX/drive_c/users/$USER/AppData/Roaming/MetaQuotes/Terminal/Common/Files"
STAGE="$PREFIX/drive_c/nexa_tester/calendar_export"
STAMP=$(date -u '+%Y%m%dT%H%M%SZ')
OUT="$ROOT/data/pepperstone/calendar/$STAMP"
if ps -axo command | grep -v grep | grep -q 'terminal64.exe'; then echo "ABORT: terminal running" >&2; exit 3; fi
cp "$ROOT/build/NEXA_CalendarExport.ex5" "$INSTALL/MQL5/Scripts/NEXA_CalendarExport.ex5"
rm -f "$C"/NEXA_Cal_*.csv "$C"/NEXA_Cal_provenance.txt
mkdir -p "$STAGE" "$OUT"
printf '[StartUp]\r\nScript=NEXA_CalendarExport\r\nSymbol=EURUSD\r\nPeriod=H1\r\nShutdownTerminal=1\r\n' > "$STAGE/startup.ini"
export DYLD_FALLBACK_LIBRARY_PATH="$WINE_ROOT/lib/external:$WINE_ROOT/lib:/usr/lib:/usr/local/lib"
export WINEPREFIX="$PREFIX" WINEDEBUG=-all
( cd "$INSTALL" && "$WINE_ROOT/bin/wine" terminal64.exe "/config:C:\\nexa_tester\\calendar_export\\startup.ini" ) >/dev/null 2>&1 &
sleep 5
i=0
while ps -axo command | grep -v grep | grep -q 'terminal64.exe' && [ $i -lt 180 ]; do sleep 5; i=$((i+1)); done
if [ -f "$C/NEXA_Cal_provenance.txt" ]; then
  mv "$C"/NEXA_Cal_*.csv "$C/NEXA_Cal_provenance.txt" "$OUT/"
  (cd "$OUT" && shasum -a 256 * > SHA256SUMS)
  echo "CALENDAR_OK $OUT"
else
  echo "CALENDAR_FAILED (no provenance file; see terminal log)"
fi
