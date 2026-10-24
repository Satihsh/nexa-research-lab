#!/bin/sh
# Headless MetaEditor compile of a NEXA MQL5 unit on the macOS MetaTrader 5.app Wine bundle.
#
# Usage: tools/compile_mql5.sh <unit.mq5> [<unit2.mq5> ...]
#   Units are resolved relative to the NEXA root (the directory above tools/).
#
# Why not the meta-trader-mcp compile_ea tool: it stages the source under /tmp
# (Wine sees Z:\tmp\...) and MetaEditor then drops the drive letter when it
# resolves quoted includes ("NEXA_Common.mqh" not found). Staging INSIDE drive_c
# at a space-free path makes quoted includes resolve as C:\nexa_build\... .
#
# Recipe (same as the bridge): bundled-Wine libs on DYLD_FALLBACK_LIBRARY_PATH,
# exported inside /bin/sh because macOS SIP strips DYLD_* from direct children.
#
# The script never edits sources. It prints MetaEditor's own log verbatim and
# exits non-zero unless MetaEditor reports "0 errors". The log is the evidence.
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
PREFIX=${NEXA_WINEPREFIX:-"$HOME/Library/Application Support/net.metaquotes.wine.metatrader5"}
WINE=${NEXA_WINE:-"/Applications/MetaTrader 5.app/Contents/SharedSupport/wine/bin/wine"}
INSTALL="$PREFIX/drive_c/Program Files/MetaTrader 5"
STAGE="$PREFIX/drive_c/nexa_build"
OUT="$ROOT/build"
WINE_ROOT=$(cd "$(dirname "$WINE")/.." && pwd)

[ -x "$WINE" ] || { echo "Wine not found: $WINE" >&2; exit 2; }
[ -f "$INSTALL/metaeditor64.exe" ] || { echo "metaeditor64.exe not found in $INSTALL" >&2; exit 2; }
[ $# -ge 1 ] || { echo "usage: $0 <unit.mq5> ..." >&2; exit 2; }

mkdir -p "$OUT"
status=0
for unit in "$@"; do
  src="$ROOT/$unit"
  [ -f "$src" ] || { echo "missing: $src" >&2; status=1; continue; }
  name=$(basename "$unit" .mq5)
  rm -rf "$STAGE"; mkdir -p "$STAGE"
  cp "$src" "$STAGE/"
  cp "$(dirname "$src")"/*.mqh "$STAGE/" 2>/dev/null || true
  export DYLD_FALLBACK_LIBRARY_PATH="$WINE_ROOT/lib/external:$WINE_ROOT/lib:/usr/lib:/usr/local/lib"
  export WINEPREFIX="$PREFIX" WINEDEBUG=-all
  # No /inc: switch - MetaEditor's parser splits it on the space in "Program Files";
  # <Trade\Trade.mqh> resolves from the install's MQL5\Include by default.
  ( cd "$INSTALL" && "$WINE" metaeditor64.exe "/compile:C:\\nexa_build\\$name.mq5" \
        "/log:C:\\nexa_build\\$name.log" ) >/dev/null 2>&1 || true
  log="$STAGE/$name.log"
  if [ ! -f "$log" ]; then
    echo "[$name] NO LOG PRODUCED - compile did not run; no result can be claimed" >&2; status=1; continue
  fi
  python3 - "$log" "$OUT/$name.compile.log" <<'EOF'
import sys
b = open(sys.argv[1], 'rb').read()
t = b.decode('utf-16') if b[:2] in (b'\xff\xfe', b'\xfe\xff') else b.decode('utf-8', 'replace')
t = t.replace('\r\n', '\n')
open(sys.argv[2], 'w').write(t)
print(t)
EOF
  if grep -q "Result: 0 errors" "$OUT/$name.compile.log" && [ -f "$STAGE/$name.ex5" ]; then
    cp "$STAGE/$name.ex5" "$OUT/$name.ex5"
    shasum -a 256 "$src" "$OUT/$name.ex5" | sed "s|$ROOT/||" > "$OUT/$name.sha256"
    echo "[$name] OK -> build/$name.ex5"
  else
    echo "[$name] FAILED (see build/$name.compile.log)" >&2; status=1
  fi
done
exit $status
