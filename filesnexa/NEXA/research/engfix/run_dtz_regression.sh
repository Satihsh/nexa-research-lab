#!/bin/sh
# ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE (D-TZ DST-aware server clock, 2026-10-03, approved option A).
# Runs the D-TZ build (build/NEXA_EA_DTZ.ex5) in the Strategy Tester with exactly the setup of
# run_s11_regression.sh (PRODUCTION inputs pinned, $200, the twelve campaign windows) for GBPUSD, so its
# Trade DNA can be compared with the S11 baseline (s11/REG_S11_GBPUSD_<W>/dna.csv.gz), plus window B for
# EURUSD / USDJPY / XAUUSD so the parity oracle can be re-run on all four window-B symbols.
# Binary installed under MQL5\Experts\NEXA_EngFix\ -- never over a deployed EA. Tester only: no live order.
#
#   DTZ_APPROVED=ENGINEERING-REGRESSION sh research/engfix/run_dtz_regression.sh
set -u
[ "${DTZ_APPROVED:-}" = "ENGINEERING-REGRESSION" ] || { echo "REFUSED: set DTZ_APPROVED" >&2; exit 2; }
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
MT5="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5"
C="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/$USER/AppData/Roaming/MetaQuotes/Terminal/Common/Files"
DEST="$MT5/Experts/NEXA_EngFix"
OUT="$ROOT/research/engfix/dtz"
export WAIT_AGENT=1
PINS="InpMaxSameCurrencyNet=2 InpRiskPercent=0.30 InpHardRiskCeiling=1.00 InpMaxDailyLossPct=2.00 InpMaxDrawdownPct=10.00 InpMaxTradesPerDay=10 InpMaxSpreadATRRatio=0.15 InpMaxMarginUsagePct=50.0 InpMaxCorrelation=0.75 InpCorrelationBars=100"
sha() { shasum -a 256 "$1" | cut -d' ' -f1; }
die() { echo "STOP: $*" >&2; exit 1; }

[ "$(sha "$ROOT/NEXA_Risk.mqh")" = 1f684cdef889757ae1b5cbf6c6d72378891d8e9f65bf951f964658ff9fa5897b ] || die "NEXA_Risk.mqh changed"
cmp -s "$ROOT/NEXA_EA.mq5" "$ROOT/build/dtz_src/NEXA_EA_DTZ.mq5" || die "DTZ build is not compiled from the current NEXA_EA.mq5"
cmp -s "$ROOT/NEXA_Common.mqh" "$ROOT/build/dtz_src/NEXA_Common.mqh" || die "DTZ build is not compiled from the current NEXA_Common.mqh"
ps -axo command | grep -v grep | grep -q terminal64.exe && die "MT5 terminal running"
DEPLOYED_BEFORE=$(sha "$MT5/Experts/Advisors/NEXA_EA.ex5")
mkdir -p "$DEST" "$OUT"
cp "$ROOT/build/NEXA_EA_DTZ.ex5" "$DEST/NEXA_EA_DTZ.ex5"
printf 'label=ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE\ndtz_ex5=%s\nsource_NEXA_EA.mq5=%s\nsource_NEXA_Common.mqh=%s\nbaseline=s11/REG_S11_GBPUSD_<W> (S11 build 7d37dc7d, fixed GMT+2 clock)\n' \
  "$(sha "$DEST/NEXA_EA_DTZ.ex5")" "$(sha "$ROOT/NEXA_EA.mq5")" "$(sha "$ROOT/NEXA_Common.mqh")" > "$OUT/PROVENANCE.txt"

CHUNKS="GBPUSD:A2024Q1:2024.01.01:2024.04.01:0 GBPUSD:A2024Q2:2024.04.01:2024.07.01:0 GBPUSD:A2024Q3:2024.07.01:2024.10.01:0 GBPUSD:A2024Q4:2024.10.01:2025.01.01:0 GBPUSD:A2025Q1:2025.01.01:2025.04.01:0 GBPUSD:A2025Q2:2025.04.01:2025.07.01:0 GBPUSD:A2025Q3:2025.07.01:2025.10.01:0 GBPUSD:A2025Q4:2025.10.01:2026.01.01:0 GBPUSD:A2026Q1:2026.01.01:2026.04.01:0 GBPUSD:A2026Q2:2026.04.01:2026.07.01:0 GBPUSD:A2026Q3:2026.07.01:2026.08.28:0 GBPUSD:B:2026.08.28:2026.09.26:4 EURUSD:B:2026.08.28:2026.09.26:4 USDJPY:B:2026.08.28:2026.09.26:4 XAUUSD:B:2026.08.28:2026.09.26:4"
for spec in $CHUNKS; do
  SYM=$(echo "$spec" | cut -d: -f1); W=$(echo "$spec" | cut -d: -f2); FROM=$(echo "$spec" | cut -d: -f3); TO=$(echo "$spec" | cut -d: -f4); MODEL=$(echo "$spec" | cut -d: -f5)
  RUN="REG_DTZ_${SYM}_${W}"
  [ -f "$OUT/$RUN/VERIFIED" ] && { echo "skip $RUN"; continue; }
  FREE_KB=$(df -k "$ROOT" | awk 'NR==2{print $4}'); [ "$FREE_KB" -ge 3145728 ] || die "free disk < 3 GiB"
  ok=0
  for attempt in 1 2 3; do
    rm -f "$C/NEXA_TradeDNA_$SYM.csv"
    # shellcheck disable=SC2086
    "$ROOT/tools/run_tester.sh" "$RUN" "NEXA_EngFix\\NEXA_EA_DTZ" "$SYM" M1 "$MODEL" "$FROM" "$TO" 200 200 250 $PINS >/dev/null
    rm -rf "$OUT/$RUN"; mv "$ROOT/research/tester_runs/$RUN" "$OUT/$RUN"
    [ -f "$C/NEXA_TradeDNA_$SYM.csv" ] && mv "$C/NEXA_TradeDNA_$SYM.csv" "$OUT/$RUN/dna.csv"
    if grep -q "Test passed" "$OUT/$RUN/tester.log" 2>/dev/null && [ -f "$OUT/$RUN/dna.csv" ]; then ok=1; break; fi
    echo "$(date '+%H:%M:%S') attempt $attempt $RUN failed (no Test passed / no DNA)"
  done
  [ $ok = 1 ] || die "$RUN failed 3 attempts"
  gzip -9 "$OUT/$RUN/dna.csv"
  touch "$OUT/$RUN/VERIFIED"
  echo "$(date '+%H:%M:%S') ok $RUN"
done
[ "$(sha "$MT5/Experts/Advisors/NEXA_EA.ex5")" = "$DEPLOYED_BEFORE" ] || die "deployed EA changed"
echo REGRESSION_DONE
