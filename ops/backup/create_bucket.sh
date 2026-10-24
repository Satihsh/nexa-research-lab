#!/bin/bash
# One-time: create the private backup bucket (owner gcloud on the Mac). Run only with the user's approval.
# Singapore, Standard class, private by construction, object versioning with 30-day retention of old versions.
set -euo pipefail
export CLOUDSDK_PYTHON=/Library/Frameworks/Python.framework/Versions/3.12/bin/python3
PROJECT=<gcp-project>
BUCKET=gs://nexa-agent-lab-backup-<gcp-project>

gcloud storage buckets create "$BUCKET" --project="$PROJECT" --location=asia-southeast1 \
  --default-storage-class=STANDARD --uniform-bucket-level-access --public-access-prevention

# Versioning: an overwritten or corrupted file keeps its previous copy...
gcloud storage buckets update "$BUCKET" --versioning
# ...for 30 days, and at most 3 old copies per file (keeps cost bounded).
LC=$(mktemp)
cat > "$LC" <<'JSON'
{"rule": [
  {"action": {"type": "Delete"}, "condition": {"daysSinceNoncurrentTime": 30}},
  {"action": {"type": "Delete"}, "condition": {"numNewerVersions": 3, "isLive": false}}
]}
JSON
gcloud storage buckets update "$BUCKET" --lifecycle-file="$LC"
rm -f "$LC"

gcloud storage buckets describe "$BUCKET" \
  --format="table(name,location,default_storage_class,public_access_prevention,uniform_bucket_level_access,versioning_enabled)"
