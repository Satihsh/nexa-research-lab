#!/bin/sh
# =====================================================================
# CAP-NEUTRAL RESEARCH — NOT PRODUCTION CONFIGURATION
# DRAFT 2026-10-02, amended 2026-10-03 (disk/swap gates). smoke: approved and PASSED.
# full: NOT YET APPROVED TO RUN.
# Plan: research/capneutral/CAPNEUTRAL_RESEARCH_PLAN.md
# =====================================================================
# Runs NEXA in the MT5 Strategy Tester with the single override in
# NEXA_CAPNEUTRAL_RESEARCH.set (InpMaxSameCurrencyNet=10000). It never edits
# NEXA_Risk.mqh, never overwrites the deployed Experts\Advisors\NEXA_EA.ex5,
# never places live orders (a tester run trades only its own simulated
# account), and keeps every output apart from the production campaign:
#   runs  -> research/tester_runs_capneutral/CAPN_NEXA_<SYM>_<WINDOW>/
#   DNA   -> data/pepperstone/tester_capneutral/CAPNEUTRAL_NEXA_TradeDNA_<SYM>_<WINDOW>.csv
# Run ids deliberately do NOT start with "PS_", so tools/rerun_failed.sh and
# nexa_tester_verify.py (both hard-wired to the production configuration) can
# never pick them up and silently re-run them with the production cap.
#
# Usage (only after explicit human approval):
#   CAPN_APPROVED=CAP-NEUTRAL-RESEARCH-APPROVED sh research/capneutral/run_capneutral_batch.sh smoke
#   CAPN_APPROVED=CAP-NEUTRAL-RESEARCH-APPROVED sh research/capneutral/run_capneutral_batch.sh full
# "full" refuses to start unless "smoke" has passed every gate.
set -u
LABEL="CAP-NEUTRAL RESEARCH — NOT PRODUCTION CONFIGURATION"
[ "${CAPN_APPROVED:-}" = "CAP-NEUTRAL-RESEARCH-APPROVED" ] || {
  echo "REFUSED: draft not approved to run (see CAPNEUTRAL_RESEARCH_PLAN.md)" >&2; exit 2; }
MODE=${1:-}
[ "$MODE" = smoke ] || [ "$MODE" = full ] || { echo "usage: $0 smoke|full" >&2; exit 2; }

ROOT=$(cd "$(dirname "$0")/../.." && pwd)
HERE="$ROOT/research/capneutral"
PY="$ROOT/.venv-research/bin/python"
SET="$HERE/NEXA_CAPNEUTRAL_RESEARCH.set"
MT5="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5"
C="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/$USER/AppData/Roaming/MetaQuotes/Terminal/Common/Files"
D="$ROOT/data/pepperstone/tester_capneutral"
RUNS="$ROOT/research/tester_runs_capneutral"
EXPERT='NEXA_Research\NEXA_EA_CAPN'
RESEARCH_EX5="$MT5/Experts/NEXA_Research/NEXA_EA_CAPN.ex5"
DEPLOYED_EX5="$MT5/Experts/Advisors/NEXA_EA.ex5"
MAX_ATTEMPTS=${MAX_ATTEMPTS:-3}
# agents flush their log (which lists every input value) only when they go idle;
# the input gate needs that log, so wait for it (adds ~2 min per run)
export WAIT_AGENT=1

# ---- pinned identities (any mismatch = STOP) ----------------------------
RISK_SHA=7fd5692a2bd3aec7443185f914be320158cfe55bcddcf370db059a6da0d908d1   # approved NEXA_Risk.mqh
SRC_SHA=d65090cca1654814b1be6e6b50cb6c2570c2ba4a3a9c7790bae5ba7121716c62    # NEXA_EA.mq5 (verified source)
EX5_SHA=91ee5e20b0a21b75d72b169bfc1f7d079dd6542c7239bc280e05c6724609e5fb    # build/NEXA_EA.ex5 compiled from it
sha() { shasum -a 256 "$1" | cut -d' ' -f1; }
die() { echo "STOP: $*" >&2; exit 1; }

# ---- pre-run gates ------------------------------------------------------
[ "$(sha "$ROOT/NEXA_Risk.mqh")" = "$RISK_SHA" ] || die "NEXA_Risk.mqh is not the approved 7fd5692a build"
[ "$(sha "$ROOT/NEXA_EA.mq5")" = "$SRC_SHA" ]    || die "NEXA_EA.mq5 differs from verified source d65090cc"
[ "$(sha "$ROOT/build/NEXA_EA.ex5")" = "$EX5_SHA" ] || die "build/NEXA_EA.ex5 differs from 91ee5e20"
ps -axo command | grep -v grep | grep -q 'terminal64.exe' && die "an MT5 terminal is running; close it first"
# disk floor and swap growth (plan §4/§9, amended 2026-10-03): checked here and before EVERY chunk
MIN_FREE_KB=3145728                      # 3 GiB
swapfiles() { ls /System/Volumes/VM/swapfile* 2>/dev/null | wc -l | tr -d ' '; }
SWAP0=$(swapfiles)
resources_ok() {
  FREE_KB=$(df -k "$ROOT" | awk 'NR==2{print $4}')
  [ "$FREE_KB" -ge "$MIN_FREE_KB" ] || die "free disk $((FREE_KB / 1048576)) GiB < 3 GiB"
  NOW=$(swapfiles)
  [ $((NOW - SWAP0)) -lt 2 ] || die "macOS added $((NOW - SWAP0)) swap files since the batch started (memory pressure)"
}
resources_ok
[ -f "$DEPLOYED_EX5" ] && DEPLOYED_BEFORE=$(sha "$DEPLOYED_EX5") || DEPLOYED_BEFORE=absent
OVR=$(grep -v '^[[:space:]]*;' "$SET" | grep '=' | tr -d '\r')
echo "$OVR" | grep -qx 'InpMaxSameCurrencyNet=10000' || die "settings file lacks the expected override"
[ "$(echo "$OVR" | wc -l | tr -d ' ')" = 10 ] || die "settings file must hold exactly 10 active lines"

# install the research copy beside, never over, the deployed EA
mkdir -p "$(dirname "$RESEARCH_EX5")" "$D" "$RUNS"
[ -f "$RESEARCH_EX5" ] || cp "$ROOT/build/NEXA_EA.ex5" "$RESEARCH_EX5"
[ "$(sha "$RESEARCH_EX5")" = "$EX5_SHA" ] || die "research EA copy hash mismatch"

# ---- per-run verification (all gates must hold) -------------------------
# 1 tester log has "Test passed" for this symbol at/after this run's start
# 2 the DNA's last decision is within 4 days of the window end (EA saw the window)
# 3 every logged input equals its source default, except InpMaxSameCurrencyNet=10000
# 4 zero NO_TRADE_PORTFOLIO_CURRENCY_EXPOSURE_CAP decisions (cap really inert)
verify_run() {  # $1 run dir, $2 DNA csv -> prints PASS or FAIL:<reason>
  "$PY" - "$1" "$2" "$ROOT" <<'EOF'
import glob, os, re, sys
import pandas as pd
run, dna, root = sys.argv[1:4]
meta = dict(re.findall(r"(\w+)=(\S+)", open(os.path.join(run, "RUN.txt")).read()))
start = re.search(r"start=\S+ (\S+)", open(os.path.join(run, "RUN.txt")).read()).group(1)
end = re.search(r"end=\S+ (\S+)", open(os.path.join(run, "RUN.txt")).read()).group(1)
def fail(why): print("FAIL:" + why); sys.exit(0)
def lines(pattern):
    out = []
    for f in glob.glob(os.path.join(run, "*.log")):
        for ln in open(f, errors="replace"):
            p = ln.rstrip("\n").split("\t")
            if len(p) >= 4 and start <= p[2][:8] <= end and re.search(pattern, ln):
                out.append(p[-1])
    return out
if not any(f"{meta['symbol']}," in l and "Test passed" in l for l in lines("Test passed")):
    fail("no Test passed line for this run")
if not os.path.exists(dna):
    fail("no DNA file")
d = pd.read_csv(dna, dtype=str, usecols=["decision_ts", "event"])
last = pd.to_datetime(d.decision_ts, format="%Y.%m.%d %H:%M:%S", errors="coerce").max()
if not (pd.notna(last) and last >= pd.to_datetime(meta["to"], format="%Y.%m.%d") - pd.Timedelta(days=4)):
    fail(f"DNA does not cover the window (last decision {last})")
if open(dna).read().count("PORTFOLIO_CURRENCY_EXPOSURE_CAP"):
    fail("exposure-cap blocks present: override did not take effect")
expected = {}
src = open(os.path.join(root, "NEXA_EA.mq5"), errors="replace").read()
for f in ["NEXA_EA.mq5"] + re.findall(r'^#include "([^"]+)"', src, re.M):   # exactly what the EA compiles
    path = os.path.join(root, f)
    for m in re.finditer(r"^\s*s?input\s+\w+\s+(\w+)\s*=\s*([^;]+);", open(path, errors="replace").read(), re.M):
        expected[m.group(1)] = m.group(2).strip().strip('"')
expected["InpMaxSameCurrencyNet"] = "10000"
logged = dict(re.findall(r"^\s*(Inp\w+)=(.*)$", "\n".join(lines(r"\tTester\t\s+Inp\w+=")), re.M))
if not logged:
    fail("no input values logged for this run")
def same(a, b):
    try: return abs(float(a) - float(b)) < 1e-9
    except ValueError: return a.strip().lower() == b.strip().lower()
bad = sorted(k for k in expected if k in logged and not same(logged[k], expected[k]))
missing = sorted(k for k in expected if k not in logged)
extra = sorted(k for k in logged if k not in expected)   # would mean a different binary
if bad or missing or extra:
    fail(f"input mismatch {bad} missing {missing} unexpected {extra}")
print("PASS")
EOF
}

run_chunk() {  # $1 SYM, $2 window spec W:FROM:TO:MODEL
  SYM=$1; W=$(echo "$2" | cut -d: -f1); FROM=$(echo "$2" | cut -d: -f2)
  TO=$(echo "$2" | cut -d: -f3); MODEL=$(echo "$2" | cut -d: -f4)
  TAG="${SYM}_${W}"; RUN="CAPN_NEXA_$TAG"; OUT="$D/CAPNEUTRAL_NEXA_TradeDNA_$TAG.csv"
  [ -f "$RUNS/$RUN/VERIFIED_PASS" ] && { echo "skip $TAG (verified)"; return 0; }
  attempt=1
  while [ $attempt -le "$MAX_ATTEMPTS" ]; do
    resources_ok
    rm -f "$C/NEXA_TradeDNA_$SYM.csv"
    # shellcheck disable=SC2086
    "$ROOT/tools/run_tester.sh" "$RUN" "$EXPERT" "$SYM" M1 "$MODEL" "$FROM" "$TO" 50000 200 250 $OVR >/dev/null
    mv "$ROOT/research/tester_runs/$RUN" "$RUNS/$RUN"
    [ -f "$C/NEXA_TradeDNA_$SYM.csv" ] && mv "$C/NEXA_TradeDNA_$SYM.csv" "$OUT"
    printf '%s\noverrides:\n%s\nexpert=%s sha256=%s\n' "$LABEL" "$OVR" "$EXPERT" "$EX5_SHA" > "$RUNS/$RUN/LABEL.txt"
    V=$(verify_run "$RUNS/$RUN" "$OUT")
    if [ "$V" = PASS ]; then
      touch "$RUNS/$RUN/VERIFIED_PASS"
      echo "$(date '+%H:%M:%S') ok $TAG rows=$(($(wc -l < "$OUT") - 1))"; return 0
    fi
    echo "$(date '+%H:%M:%S') attempt $attempt $TAG $V"
    case "$V" in *"override did not take effect"*|*"input mismatch"*) die "$TAG: $V (configuration gate; not retried)";; esac
    mv "$RUNS/$RUN" "$RUNS/FAILEDRUN_${RUN}_try$attempt"
    [ -f "$OUT" ] && mv "$OUT" "$D/FAILEDRUN_try${attempt}_CAPNEUTRAL_NEXA_TradeDNA_$TAG.csv"
    attempt=$((attempt + 1))
  done
  echo "$(date '+%H:%M:%S') GAVE UP $TAG after $MAX_ATTEMPTS attempts"; return 1
}

CHUNKS="A2024Q1:2024.01.01:2024.04.01:0 A2024Q2:2024.04.01:2024.07.01:0 A2024Q3:2024.07.01:2024.10.01:0 A2024Q4:2024.10.01:2025.01.01:0 A2025Q1:2025.01.01:2025.04.01:0 A2025Q2:2025.04.01:2025.07.01:0 A2025Q3:2025.07.01:2025.10.01:0 A2025Q4:2025.10.01:2026.01.01:0 A2026Q1:2026.01.01:2026.04.01:0 A2026Q2:2026.04.01:2026.07.01:0 A2026Q3:2026.07.01:2026.08.28:0 B:2026.08.28:2026.09.26:4"
echo "$LABEL"
if [ "$MODE" = smoke ]; then
  # highest-cap-block chunk of the production campaign (718 blocked decisions)
  run_chunk USDJPY "A2026Q1:2026.01.01:2026.04.01:0" || die "smoke run failed"
  CLOSES=$(grep -c ',CLOSE,' "$D/CAPNEUTRAL_NEXA_TradeDNA_USDJPY_A2026Q1.csv")
  [ "$CLOSES" -ge 1 ] || die "smoke run produced no closed trade"
  printf 'smoke passed %s closes=%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$CLOSES" > "$RUNS/SMOKE_PASSED"
else
  [ -f "$RUNS/SMOKE_PASSED" ] || die "smoke has not passed"
  FAILED=0
  for SYM in GBPUSD EURUSD USDJPY XAUUSD; do
    for spec in $CHUNKS; do run_chunk "$SYM" "$spec" || FAILED=$((FAILED + 1)); done
  done
  (cd "$D" && shasum -a 256 CAPNEUTRAL_*.csv > SHA256SUMS)
  echo "chunks given up: $FAILED"
fi
[ -f "$DEPLOYED_EX5" ] && DEPLOYED_AFTER=$(sha "$DEPLOYED_EX5") || DEPLOYED_AFTER=absent
[ "$DEPLOYED_BEFORE" = "$DEPLOYED_AFTER" ] || die "deployed NEXA_EA.ex5 changed during the batch"
[ "$(sha "$ROOT/NEXA_Risk.mqh")" = "$RISK_SHA" ] || die "NEXA_Risk.mqh changed during the batch"
echo "BATCH_DONE $MODE"
