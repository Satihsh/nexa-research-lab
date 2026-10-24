#!/bin/sh
# Run the research pipeline on one REAL Trade DNA export:
#   Stage 2 ingest -> Stage 3 parity -> Stage 4 labels -> Stage 5 validate -> Gate 8 stats
#
# Usage: tools/run_dna_pipeline.sh <NEXA_TradeDNA_SYM.csv> <SYM> <bars_M1.csv> <bars_D1.csv> <run_dir>
#                                  [<bars_M5.csv> <bars_M15.csv> <bars_H1.csv>]
#   With the optional MTF bars, step 3b also runs the parity oracle on DECISION rows
#   (a zero-trade window has no OPEN/FILL rows, but DECISION rows journal f00..f47 too).
#   bars come from NEXA_BarExport run in the SAME tester configuration.
#
# Every stage's stdout and exit code are kept in <run_dir>. A failing stage is
# recorded, not hidden; later stages still run where their input exists so the
# full picture is visible, but nothing downstream of a FAILED gate may be
# treated as trainable.
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
PY="$ROOT/.venv-research/bin/python"
R="$ROOT/research"
abspath() { (cd "$(dirname "$1")" && printf '%s/%s\n' "$(pwd)" "$(basename "$1")"); }
DNA=$(abspath "$1"); SYM=$2; M1=$(abspath "$3"); D1=$(abspath "$4")
mkdir -p "$5" && OUT=$(cd "$5" && pwd)   # absolute: the stages run from research/
M5=${6:+$(abspath "$6")}; M15=${7:+$(abspath "$7")}; H1=${8:+$(abspath "$8")}
POINT=$("$ROOT/.venv-research/bin/python" -c "import json; c=json.load(open('$ROOT/data/pepperstone/contracts.json')); print(c.get('$SYM',{}).get('point',1e-5))" 2>/dev/null || echo 1e-5)
cp "$DNA" "$OUT/trade_dna_raw.csv"
shasum -a 256 "$DNA" "$M1" "$D1" > "$OUT/inputs.sha256"

# MT5 writes "YYYY.MM.DD HH:MM:SS"; convert to ISO so no stage guesses the format.
"$PY" - "$M1" "$OUT/m1.csv" "$D1" "$OUT/d1.csv" ${M5:+"$M5" "$OUT/m5.csv"} ${M15:+"$M15" "$OUT/m15.csv"} ${H1:+"$H1" "$OUT/h1.csv"} <<'EOF'
import sys, pandas as pd
a = sys.argv[1:]
for src, dst in zip(a[0::2], a[1::2]):
    b = pd.read_csv(src)
    b["time"] = pd.to_datetime(b["time"], format="%Y.%m.%d %H:%M:%S").dt.strftime("%Y-%m-%d %H:%M:%S")
    b.to_csv(dst, index=False)
EOF

run() { name=$1; shift; "$@" > "$OUT/$name.log" 2>&1; rc=$?; echo "$name exit=$rc" | tee -a "$OUT/STATUS"; return 0; }
cd "$R" || exit 2
run 2_ingest   "$PY" nexa_ingest.py "$OUT/trade_dna_raw.csv" --schema "$ROOT/nexa_schema_v1.json" -o "$OUT/canonical.csv" --allow-errors
run 3_parity   "$PY" nexa_parity.py "$OUT/canonical.csv" --m1 "$OUT/m1.csv" --d1 "$OUT/d1.csv" --point "$POINT" \
                   --mql5-source "$ROOT/NEXA_Intelligence.mqh" --out "$OUT/parity_mismatches.csv"
if [ -n "$H1" ]; then
run 3b_parity_decisions "$PY" - "$OUT" "$POINT" "$ROOT/NEXA_Intelligence.mqh" <<'EOF'
import sys, pandas as pd, nexa_parity as p
out, point, src = sys.argv[1], float(sys.argv[2]), sys.argv[3]
f = pd.read_csv(f"{out}/canonical.csv")
for c in ("decision_ts", "decision_ts_effective"):
    if c in f.columns:
        f[c] = pd.to_datetime(f[c], errors="coerce")
paths = {tf: f"{out}/{tf.lower()}.csv" for tf in ("M1", "M5", "M15", "H1", "D1")}
res = p.run_parity(f, p.load_market_data(paths, point=point), p.ParityConfig(gmt_offset=2),
                   mql5_source=src, events=("DECISION",))
print(res.report())
if res.mismatches:
    res.mismatch_frame().to_csv(f"{out}/parity_decisions_mismatches.csv", index=False)
sys.exit(0 if res.passed else 1)
EOF
fi
run 4_labels   "$PY" nexa_labels.py "$OUT/canonical.csv" --m1 "$SYM=$OUT/m1.csv" -o "$OUT/labelled.csv" \
                   --training-view "$OUT/training_view.csv"
run 5_validate "$PY" nexa_validate.py "$OUT/labelled.csv" --out "$OUT/validate_report.txt"
run 8_stats    "$PY" - "$OUT/canonical.csv" "$OUT/gate8.json" <<'EOF'
import json, sys, pandas as pd, numpy as np
import nexa_stats as st
df = pd.read_csv(sys.argv[1])
closes = df[df["event"] == "CLOSE"]
r = pd.to_numeric(closes["result_r"], errors="coerce").dropna().values
rep = st.evaluate(r).to_dict()
rep["source"] = "broker result_r on CLOSE rows (net of costs as the tester realised them)"
rep["events"] = df["event"].value_counts().to_dict()
rep["reasons_top"] = df["reason"].astype(str).value_counts().head(25).to_dict()
json.dump(rep, open(sys.argv[2], "w"), indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
print(json.dumps({"n_closed": int(len(r)), "verdict": rep["verdict"], "events": rep["events"]}, indent=1))
EOF
cat "$OUT/STATUS"
