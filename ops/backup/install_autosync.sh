#!/bin/bash
# Install / remove the daily auto-sync (launchd user agent). Persistent config: install only with approval.
#   install_autosync.sh            install (daily 03:00 local; if the Mac slept through it, runs on wake)
#   install_autosync.sh --remove   uninstall
set -euo pipefail
LABEL=com.nexa.gcsbackup
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
SCRIPT="$HOME/NEXA-Agent-Lab/ops/backup/gcs_backup.sh"
DOMAIN="gui/$(id -u)"

if [ "${1:-}" = "--remove" ]; then
  launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
  rm -f "$PLIST"
  echo "auto-sync removed"; exit 0
fi

chmod +x "$SCRIPT"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array><string>/bin/bash</string><string>$SCRIPT</string></array>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>3</integer><key>Minute</key><integer>0</integer></dict>
  <key>RunAtLoad</key><false/>
  <key>LowPriorityIO</key><true/>
  <key>Nice</key><integer>10</integer>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/nexa-gcs-backup.launchd.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/nexa-gcs-backup.launchd.log</string>
</dict></plist>
EOF
plutil -lint "$PLIST"
launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
launchctl bootstrap "$DOMAIN" "$PLIST"
launchctl print "$DOMAIN/$LABEL" | grep -E "state|path" | head -3
echo "auto-sync installed: daily 03:00 -> $(grep -o 'gs://[^"}]*' "$SCRIPT" | head -1)"
