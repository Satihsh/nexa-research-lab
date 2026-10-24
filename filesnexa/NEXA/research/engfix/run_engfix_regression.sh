#!/bin/sh
# ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE (D-PARTIAL-AFTER-BE fix, 2026-10-03).
# Runs the PRE-fix build (copy of build/NEXA_EA.ex5, 91ee5e20) and the FIXED build (build/NEXA_EA_PMFIX.ex5)
# in the Strategy Tester with PRODUCTION inputs (no overrides; the ten NEXA_Risk inputs are written out at
# their production values so a cached tester setting cannot change them), $200 deposit, GBPUSD, the twelve
# campaign windows. Binaries are installed under MQL5\Experts\NEXA_EngFix\ -- never over a deployed EA.
# A tester run trades only its own simulated account; nothing here can place a live order.
#
#   ENGFIX_APPROVED=ENGINEERING-REGRESSION sh research/engfix/run_engfix_regression.sh
set -u
[ "${ENGFIX_APPROVED:-}" = "ENGINEERING-REGRESSION" ] || { echo "REFUSED: set ENGFIX_APPROVED" >&2; exit 2; }
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
PY="$ROOT/.venv-research/bin/python"
MT5="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5"
C="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/$USER/AppData/Roaming/MetaQuotes/Terminal/Common/Files"
DEST="$MT5/Experts/NEXA_EngFix"
OUT="$ROOT/research/engfix/regression"
SYM=GBPUSD
export WAIT_AGENT=1
PINS="InpMaxSameCurrencyNet=2 InpRiskPercent=0.30 InpHardRiskCeiling=1.00 InpMaxDailyLossPct=2.00 InpMaxDrawdownPct=10.00 InpMaxTradesPerDay=10 InpMaxSpreadATRRatio=0.15 InpMaxMarginUsagePct=50.0 InpMaxCorrelation=0.75 InpCorrelationBars=100"
sha() { shasum -a 256 "$1" | cut -d' ' -f1; }
die() { echo "STOP: $*" >&2; exit 1; }

[ "$(sha "$ROOT/NEXA_Risk.mqh")" = 7fd5692a2bd3aec7443185f914be320158cfe55bcddcf370db059a6da0d908d1 ] || die "NEXA_Risk.mqh changed"
[ "$(sha "$ROOT/build/NEXA_EA.ex5")" = 91ee5e20b0a21b75d72b169bfc1f7d079dd6542c7239bc280e05c6724609e5fb ] || die "pre-fix build changed"
cmp -s "$ROOT/NEXA_EA.mq5" "$ROOT/build/pmfix_src/NEXA_EA_PMFIX.mq5" || die "fixed build is not compiled from the current NEXA_EA.mq5"
ps -axo command | grep -v grep | grep -q terminal64.exe && die "MT5 terminal running"
DEPLOYED_BEFORE=$(sha "$MT5/Experts/Advisors/NEXA_EA.ex5")
mkdir -p "$DEST" "$OUT"
cp "$ROOT/build/NEXA_EA.ex5" "$DEST/NEXA_EA_PRE.ex5"
cp "$ROOT/build/NEXA_EA_PMFIX.ex5" "$DEST/NEXA_EA_PMFIX.ex5"
printf 'label=ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE\npre_ex5=%s\npost_ex5=%s\npost_source_NEXA_EA.mq5=%s\nNEXA_PositionMgmt.mqh=%s\n' \
  "$(sha "$DEST/NEXA_EA_PRE.ex5")" "$(sha "$DEST/NEXA_EA_PMFIX.ex5")" "$(sha "$ROOT/NEXA_EA.mq5")" "$(sha "$ROOT/NEXA_PositionMgmt.mqh")" > "$OUT/PROVENANCE.txt"

CHUNKS="A2024Q1:2024.01.01:2024.04.01:0 A2024Q2:2024.04.01:2024.07.01:0 A2024Q3:2024.07.01:2024.10.01:0 A2024Q4:2024.10.01:2025.01.01:0 A2025Q1:2025.01.01:2025.04.01:0 A2025Q2:2025.04.01:2025.07.01:0 A2025Q3:2025.07.01:2025.10.01:0 A2025Q4:2025.10.01:2026.01.01:0 A2026Q1:2026.01.01:2026.04.01:0 A2026Q2:2026.04.01:2026.07.01:0 A2026Q3:2026.07.01:2026.08.28:0 B:2026.08.28:2026.09.26:4"
for spec in $CHUNKS; do
  W=$(echo "$spec" | cut -d: -f1); FROM=$(echo "$spec" | cut -d: -f2); TO=$(echo "$spec" | cut -d: -f3); MODEL=$(echo "$spec" | cut -d: -f4)
  for BUILD in PRE PMFIX; do
    RUN="REG_${BUILD}_${SYM}_${W}"
    [ -f "$OUT/$RUN/VERIFIED" ] && { echo "skip $RUN"; continue; }
    FREE_KB=$(df -k "$ROOT" | awk 'NR==2{print $4}'); [ "$FREE_KB" -ge 3145728 ] || die "free disk < 3 GiB"
    ok=0
    for attempt in 1 2 3; do
      rm -f "$C/NEXA_TradeDNA_$SYM.csv"
      # shellcheck disable=SC2086
      "$ROOT/tools/run_tester.sh" "$RUN" "NEXA_EngFix\\NEXA_EA_$BUILD" "$SYM" M1 "$MODEL" "$FROM" "$TO" 200 200 250 $PINS >/dev/null
      rm -rf "$OUT/$RUN"; mv "$ROOT/research/tester_runs/$RUN" "$OUT/$RUN"
      [ -f "$C/NEXA_TradeDNA_$SYM.csv" ] && mv "$C/NEXA_TradeDNA_$SYM.csv" "$OUT/$RUN/dna.csv"
      if grep -q "Test passed" "$OUT/$RUN/tester.log" 2>/dev/null && [ -f "$OUT/$RUN/dna.csv" ]; then ok=1; break; fi
      echo "$(date '+%H:%M:%S') attempt $attempt $RUN failed (no Test passed / no DNA)"
    done
    [ $ok = 1 ] || die "$RUN failed 3 attempts"
    touch "$OUT/$RUN/VERIFIED"
    echo "$(date '+%H:%M:%S') ok $RUN rows=$(($(wc -l < "$OUT/$RUN/dna.csv") - 1))"
  done
done
[ "$(sha "$MT5/Experts/Advisors/NEXA_EA.ex5")" = "$DEPLOYED_BEFORE" ] || die "deployed EA changed"
echo REGRESSION_DONE
