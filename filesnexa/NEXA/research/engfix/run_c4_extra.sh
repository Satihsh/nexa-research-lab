#!/bin/sh
# ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE (C4 daily-loss budget, 2026-10-03). Tester only.
#  1. NEXA_DailyBudgetTest (compiled C4 NEXA_Risk.mqh): boundary + fail-closed cases -> tester_runs/dailybudget_c4_20261003
#  2. NEXA_CorrCapTest re-run (its evidence pins the NEXA_Risk.mqh hash)    -> tester_runs/corrcap_parity_20261003_c4
#  3. Research configuration ($50k, InpMaxSameCurrencyNet=10000, other inputs at defaults) on the six windows that
#     had days beyond -2 % in the cap-neutral campaign, D-TZ build vs C4 build -> c4/capn_<BUILD>_<SYM>_<W>
#   C4_APPROVED=ENGINEERING-REGRESSION sh research/engfix/run_c4_extra.sh
set -u
[ "${C4_APPROVED:-}" = "ENGINEERING-REGRESSION" ] || { echo "REFUSED: set C4_APPROVED" >&2; exit 2; }
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
MT5="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5"
C="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/$USER/AppData/Roaming/MetaQuotes/Terminal/Common/Files"
DEST="$MT5/Experts/NEXA_EngFix"; OUT="$ROOT/research/engfix/c4"; TR="$ROOT/research/tester_runs"
export WAIT_AGENT=1
sha() { shasum -a 256 "$1" | cut -d' ' -f1; }
die() { echo "STOP: $*" >&2; exit 1; }
cmp -s "$ROOT/NEXA_Risk.mqh" "$ROOT/build/c4_src/NEXA_Risk.mqh" || die "C4 build not from current NEXA_Risk.mqh"
ps -axo command | grep -v grep | grep -q terminal64.exe && die "MT5 terminal running"
DEPLOYED_BEFORE=$(sha "$MT5/Experts/Advisors/NEXA_EA.ex5")
mkdir -p "$DEST" "$OUT"
cp "$ROOT/build/NEXA_DailyBudgetTest_C4.ex5" "$ROOT/build/NEXA_CorrCapTest_C4.ex5" "$ROOT/build/NEXA_EA_C4.ex5" "$ROOT/build/NEXA_EA_DTZ.ex5" "$DEST/"

harness() { # run_id expert results_file
  for a in 1 2 3; do
    rm -f "$C/$3"
    "$ROOT/tools/run_tester.sh" "$1" "NEXA_EngFix\\$2" EURUSD M1 2 2024.01.08 2024.01.12 50000 200 0 >/dev/null
    [ -f "$C/$3" ] && return 0; echo "attempt $a $1: no results"
  done; die "$1 failed"
}
harness dailybudget_c4_20261003 NEXA_DailyBudgetTest_C4 nexa_dailybudget_mql5_results.csv
cp "$C/nexa_dailybudget_mql5_results.csv" "$TR/dailybudget_c4_20261003/mql5_results.csv"
printf 'nexa_risk_sha256=%s\nharness_ex5_sha256=%s\n' "$(sha "$ROOT/NEXA_Risk.mqh")" "$(sha "$ROOT/build/NEXA_DailyBudgetTest_C4.ex5")" > "$TR/dailybudget_c4_20261003/PROVENANCE.txt"

(cd "$ROOT/research" && "$ROOT/.venv-research/bin/python" -c "import nexa_corr_oracle as o; o.write_fixtures('$C/nexa_corrcap_fixtures.csv')")
harness corrcap_parity_20261003_c4 NEXA_CorrCapTest_C4 nexa_corrcap_mql5_results.csv
cp "$C/nexa_corrcap_mql5_results.csv" "$TR/corrcap_parity_20261003_c4/mql5_results.csv"; cp "$C/nexa_corrcap_fixtures.csv" "$TR/corrcap_parity_20261003_c4/fixtures.csv"
printf 'nexa_risk_sha256=%s\nharness_ex5_sha256=%s\nfixtures_sha256=%s\nnote=re-run after the human-approved C4 change to NEXA_Risk.mqh (2026-10-03)\n' "$(sha "$ROOT/NEXA_Risk.mqh")" "$(sha "$ROOT/build/NEXA_CorrCapTest_C4.ex5")" "$(sha "$TR/corrcap_parity_20261003_c4/fixtures.csv")" > "$TR/corrcap_parity_20261003_c4/PROVENANCE.txt"

PINS="InpMaxSameCurrencyNet=10000 InpRiskPercent=0.30 InpHardRiskCeiling=1.00 InpMaxDailyLossPct=2.00 InpMaxDrawdownPct=10.00 InpMaxTradesPerDay=10 InpMaxSpreadATRRatio=0.15 InpMaxMarginUsagePct=50.0 InpMaxCorrelation=0.75 InpCorrelationBars=100"
for spec in GBPUSD:A2024Q1:2024.01.01:2024.04.01 GBPUSD:A2024Q2:2024.04.01:2024.07.01 GBPUSD:A2026Q1:2026.01.01:2026.04.01 EURUSD:A2025Q1:2025.01.01:2025.04.01 USDJPY:A2024Q1:2024.01.01:2024.04.01 USDJPY:A2025Q1:2025.01.01:2025.04.01; do
  SYM=$(echo "$spec" | cut -d: -f1); W=$(echo "$spec" | cut -d: -f2); FROM=$(echo "$spec" | cut -d: -f3); TO=$(echo "$spec" | cut -d: -f4)
  for BUILD in DTZ C4; do
    RUN="capn_${BUILD}_${SYM}_${W}"
    [ -f "$OUT/$RUN/VERIFIED" ] && { echo "skip $RUN"; continue; }
    ok=0
    for attempt in 1 2 3; do
      rm -f "$C/NEXA_TradeDNA_$SYM.csv"
      # shellcheck disable=SC2086
      "$ROOT/tools/run_tester.sh" "$RUN" "NEXA_EngFix\\NEXA_EA_$BUILD" "$SYM" M1 0 "$FROM" "$TO" 50000 200 250 $PINS >/dev/null
      rm -rf "$OUT/$RUN"; mv "$TR/$RUN" "$OUT/$RUN"
      [ -f "$C/NEXA_TradeDNA_$SYM.csv" ] && mv "$C/NEXA_TradeDNA_$SYM.csv" "$OUT/$RUN/dna.csv"
      if grep -q "Test passed" "$OUT/$RUN/tester.log" 2>/dev/null && [ -f "$OUT/$RUN/dna.csv" ]; then ok=1; break; fi
      echo "$(date '+%H:%M:%S') attempt $attempt $RUN failed"
    done
    [ $ok = 1 ] || die "$RUN failed 3 attempts"
    gzip -9 "$OUT/$RUN/dna.csv"; touch "$OUT/$RUN/VERIFIED"; echo "$(date '+%H:%M:%S') ok $RUN"
  done
done
[ "$(sha "$MT5/Experts/Advisors/NEXA_EA.ex5")" = "$DEPLOYED_BEFORE" ] || die "deployed EA changed"
echo EXTRA_DONE
