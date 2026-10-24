#!/bin/sh
# ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE (stale-bar guard, 2026-10-03, approved option C).
# Runs the STALE-GUARD build (build/NEXA_EA_STALE.ex5) in the Strategy Tester with exactly the setup of
# run_engfix_regression.sh (PRODUCTION inputs pinned, $200, GBPUSD, the twelve campaign windows), so its
# Trade DNA can be compared row by row with the D45 baseline (regression/REG_PMFIX_GBPUSD_<W>/dna.csv.gz).
# Binary installed under MQL5\Experts\NEXA_EngFix\ -- never over a deployed EA. Tester only: no live order.
#
#   STALEGUARD_APPROVED=ENGINEERING-REGRESSION sh research/engfix/run_staleguard_regression.sh
set -u
[ "${STALEGUARD_APPROVED:-}" = "ENGINEERING-REGRESSION" ] || { echo "REFUSED: set STALEGUARD_APPROVED" >&2; exit 2; }
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
MT5="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5"
C="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/$USER/AppData/Roaming/MetaQuotes/Terminal/Common/Files"
DEST="$MT5/Experts/NEXA_EngFix"
OUT="$ROOT/research/engfix/staleguard"
SYM=GBPUSD
export WAIT_AGENT=1
PINS="InpMaxSameCurrencyNet=2 InpRiskPercent=0.30 InpHardRiskCeiling=1.00 InpMaxDailyLossPct=2.00 InpMaxDrawdownPct=10.00 InpMaxTradesPerDay=10 InpMaxSpreadATRRatio=0.15 InpMaxMarginUsagePct=50.0 InpMaxCorrelation=0.75 InpCorrelationBars=100"
sha() { shasum -a 256 "$1" | cut -d' ' -f1; }
die() { echo "STOP: $*" >&2; exit 1; }

[ "$(sha "$ROOT/NEXA_Risk.mqh")" = 7fd5692a2bd3aec7443185f914be320158cfe55bcddcf370db059a6da0d908d1 ] || die "NEXA_Risk.mqh changed"
cmp -s "$ROOT/NEXA_EA.mq5" "$ROOT/build/stale_src/NEXA_EA_STALE.mq5" || die "STALE build is not compiled from the current NEXA_EA.mq5"
ps -axo command | grep -v grep | grep -q terminal64.exe && die "MT5 terminal running"
DEPLOYED_BEFORE=$(sha "$MT5/Experts/Advisors/NEXA_EA.ex5")
mkdir -p "$DEST" "$OUT"
cp "$ROOT/build/NEXA_EA_STALE.ex5" "$DEST/NEXA_EA_STALE.ex5"
printf 'label=ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE\nstale_ex5=%s\nsource_NEXA_EA.mq5=%s\nbaseline=regression/REG_PMFIX_GBPUSD_<W> (D45 build 28e8d925, source 10b62623)\n' \
  "$(sha "$DEST/NEXA_EA_STALE.ex5")" "$(sha "$ROOT/NEXA_EA.mq5")" > "$OUT/PROVENANCE.txt"

CHUNKS="A2024Q1:2024.01.01:2024.04.01:0 A2024Q2:2024.04.01:2024.07.01:0 A2024Q3:2024.07.01:2024.10.01:0 A2024Q4:2024.10.01:2025.01.01:0 A2025Q1:2025.01.01:2025.04.01:0 A2025Q2:2025.04.01:2025.07.01:0 A2025Q3:2025.07.01:2025.10.01:0 A2025Q4:2025.10.01:2026.01.01:0 A2026Q1:2026.01.01:2026.04.01:0 A2026Q2:2026.04.01:2026.07.01:0 A2026Q3:2026.07.01:2026.08.28:0 B:2026.08.28:2026.09.26:4"
for spec in $CHUNKS; do
  W=$(echo "$spec" | cut -d: -f1); FROM=$(echo "$spec" | cut -d: -f2); TO=$(echo "$spec" | cut -d: -f3); MODEL=$(echo "$spec" | cut -d: -f4)
  RUN="REG_STALE_${SYM}_${W}"
  [ -f "$OUT/$RUN/VERIFIED" ] && { echo "skip $RUN"; continue; }
  FREE_KB=$(df -k "$ROOT" | awk 'NR==2{print $4}'); [ "$FREE_KB" -ge 3145728 ] || die "free disk < 3 GiB"
  ok=0
  for attempt in 1 2 3; do
    rm -f "$C/NEXA_TradeDNA_$SYM.csv"
    # shellcheck disable=SC2086
    "$ROOT/tools/run_tester.sh" "$RUN" "NEXA_EngFix\\NEXA_EA_STALE" "$SYM" M1 "$MODEL" "$FROM" "$TO" 200 200 250 $PINS >/dev/null
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
