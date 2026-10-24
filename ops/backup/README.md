# NEXA backup to Google Cloud Storage

Two layers:
- **Code:** GitHub `Satihsh/nexa-agent-lab` (private), committed at each milestone.
- **Everything else** (data, logs, reports, PDFs, about 13 GB): the private bucket `gs://nexa-agent-lab-backup-<gcp-project>` (Singapore).

## Files

| File | What it does | When |
|---|---|---|
| `create_bucket.sh` | Creates the bucket: private, uniform access, public-access prevention, versioning (old copies kept 30 days, at most 3 per file) | Once, with approval |
| `gcs_backup.sh [--dry-run]` | Incremental one-way `gcloud storage rsync`. Text files are gzipped in flight only; the Mac stays awake while it runs; there is a lock against overlapping runs; output goes to `~/Library/Logs/nexa-gcs-backup.log`, with a macOS notification at the end. | By hand, or daily via launchd |
| `install_autosync.sh [--remove]` | launchd user agent: daily at 03:00. If the Mac was asleep at 03:00, the run starts at the next wake. | Once, with approval |

## Safety properties

- **Never deletes in the bucket.** There is no `--delete-unmatched-destination-objects`, so a file deleted or lost on the Mac stays in the backup.
- **Overwrites are versioned:** a corrupted file's previous copy survives for 30 days.
- **Never uploaded:** `.env*` (secrets), `.venv*`, `vendor/`, `__pycache__/`, `.git/`, `.DS_Store`, `*.pyc`. The exclude regex is tested on sample paths.
- **Bucket access:** owner only. The view-only account (`satihsh0903`) is **not** granted access to this bucket.

## Restore

- Everything: `gcloud storage rsync -r gs://nexa-agent-lab-backup-<gcp-project>/NEXA-Agent-Lab ~/NEXA-Agent-Lab-restore`
- One old version of a file: `gcloud storage ls -a gs://…/path` to list its versions, then `gcloud storage cp 'gs://…/path#<generation>' .`
