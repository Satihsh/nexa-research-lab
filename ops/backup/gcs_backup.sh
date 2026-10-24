#!/bin/bash
# NEXA-Agent-Lab (+ Mac MT5 Wine prefix) -> Google Cloud Storage backup (incremental, one-way, never deletes in the bucket).
#   gcs_backup.sh            real run
#   gcs_backup.sh --dry-run  list what would be uploaded, upload nothing
# Run by hand or by the launchd agent installed with install_autosync.sh.
# Secrets (.env*), virtualenvs, vendor clones, caches and .git never leave the Mac.
set -u
export CLOUDSDK_PYTHON=/Library/Frameworks/Python.framework/Versions/3.12/bin/python3  # gcloud breaks on Python 3.14
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

SRC="$HOME/NEXA-Agent-Lab"
BUCKET="${NEXA_BACKUP_BUCKET:-gs://nexa-agent-lab-backup-<gcp-project>}"
DEST="$BUCKET/NEXA-Agent-Lab"
# Second source (user approval 2026-10-14 "+ MT5 folder"): the Mac MT5 Wine prefix.
MT5_SRC="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5"
MT5_DEST="$BUCKET/MT5-wine"
# Wine drive links (dosdevices: c: z:=/ d::) never leave the Mac; saved MT5 logins (accounts.dat) stay local too.
MT5_EXCLUDE='^dosdevices/.*|^(.*/)?config/accounts\.dat$|^(.*/)?\.DS_Store$'

LOG="$HOME/Library/Logs/nexa-gcs-backup.log"
LOCKDIR="${TMPDIR:-/tmp}/nexa-gcs-backup.lock"
# Python regexes on the path RELATIVE to $SRC.
EXCLUDE='^(.*/)?\.venv[^/]*/.*|^vendor/.*|^(.*/)?__pycache__/.*|^\.git/.*|^(.*/)?\.env(\..*)?$|^(.*/)?\.DS_Store$|^.*\.pyc$'
# Text compresses well on the wire; objects are stored uncompressed (restore = plain files).
GZIP_EXT='csv,tsv,log,txt,json,jsonl,md,py,mq5,mqh,set,ini,html,sh,ps1'

DRY=""
[ "${1:-}" = "--dry-run" ] && DRY="--dry-run"

mkdir -p "$(dirname "$LOG")"
log() { echo "$(date '+%Y-%m-%d %H:%M:%S %z') $*" >> "$LOG"; }
notify() { osascript -e "display notification \"$1\" with title \"NEXA backup\"" >/dev/null 2>&1 || true; }

if ! mkdir "$LOCKDIR" 2>/dev/null; then log "SKIP another backup is running"; exit 0; fi
trap 'rmdir "$LOCKDIR" 2>/dev/null' EXIT

# Keep the Mac awake while this process runs (released automatically when it exits).
caffeinate -i -w $$ &

start=$(date +%s)
log "START ${DRY:-real} $SRC -> $DEST"
gcloud storage rsync "$SRC" "$DEST" --recursive --exclude="$EXCLUDE" \
    --gzip-in-flight="$GZIP_EXT" $DRY >> "$LOG" 2>&1
rc=$?
if [ -d "$MT5_SRC" ]; then
  log "START ${DRY:-real} $MT5_SRC -> $MT5_DEST"
  gcloud storage rsync "$MT5_SRC" "$MT5_DEST" --recursive --exclude="$MT5_EXCLUDE" \
      --gzip-in-flight="$GZIP_EXT" $DRY >> "$LOG" 2>&1
  rc2=$?
  [ $rc -eq 0 ] && rc=$rc2
fi
mins=$(( ($(date +%s) - start) / 60 ))
if [ $rc -eq 0 ]; then
  log "OK ${DRY:-real} in ${mins} min"
  [ -z "$DRY" ] && notify "Backup OK (${mins} min)"
else
  log "FAIL rc=$rc after ${mins} min (rerun resumes; nothing is deleted)"
  notify "Backup FAILED rc=$rc - see ~/Library/Logs/nexa-gcs-backup.log"
fi
exit $rc
