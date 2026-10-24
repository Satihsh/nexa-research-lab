#!/bin/bash
# Run one V2 group using the last PUBLISHED checkpoint (= last log line, published before this call), then regenerate the page.
set -e
G=$1; R=~/NEXA-Agent-Lab/filesnexa/NEXA/research; S=/private/tmp/claude-501/-Users-<user>-NEXA-Agent-Lab/b7761295-0bbc-412a-840f-c599b9bfa132/scratchpad/registry_checkpoints
read SEQ HEAD < <(tail -1 $R/reports/V2_INSAMPLE_RUN_LOG.jsonl | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print(d['seq'], d['head'])")
cd $R && caffeinate -i ../.venv-research/bin/python run_v2_inSample.py --group $G --seq $SEQ --head $HEAD 2>&1 | grep -v "^\s*$" | tail -12
python3 $S/gen.py $S $R/reports/V2_INSAMPLE_RUN_LOG.jsonl
