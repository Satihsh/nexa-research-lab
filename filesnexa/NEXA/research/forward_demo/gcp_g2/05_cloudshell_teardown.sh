#!/usr/bin/env bash
# NEXA S14: tear-down after the forward check (target 2026-12-08; credit expires 2027-01-10).
# FIRST download the data (README step H). This script permanently deletes the VM, its disk and the bucket.
# Run in Google Cloud Shell:  bash 05_cloudshell_teardown.sh
set -euo pipefail
PROJECT="$(gcloud config get-value project 2>/dev/null)"
ZONE=us-east4-c; VM=nexa-s14; BUCKET="nexa-s14-${PROJECT}"; SA="nexa-s14-vm@${PROJECT}.iam.gserviceaccount.com"

echo "This PERMANENTLY deletes: VM $VM (+ boot disk), bucket gs://$BUCKET (all S14 data), firewall nexa-rdp-myip,"
echo "service account $SA, log metric s14_heartbeat_ok and the S14 alert policy."
read -r -p "Have you downloaded gs://$BUCKET/s14 to your Mac? Type DELETE to continue: " ok
[[ "$ok" == "DELETE" ]] || { echo "Aborted."; exit 1; }

gcloud compute instances delete "$VM" --zone="$ZONE" --delete-disks=all --quiet
gcloud storage rm --recursive "gs://$BUCKET"
gcloud compute firewall-rules delete nexa-rdp-myip --quiet || true
gcloud iam service-accounts delete "$SA" --quiet || true
gcloud logging metrics delete s14_heartbeat_ok --quiet || true
for p in $(gcloud alpha monitoring policies list --filter='displayName="NEXA S14 heartbeat missing (30 min)"' --format='value(name)'); do
  gcloud alpha monitoring policies delete "$p" --quiet
done
echo "Remaining billable resources (should be none):"
gcloud compute instances list; gcloud compute disks list; gcloud storage ls
echo "Also: remove the Claude connector, delete the OAuth client, remove the view-only account from IAM (README step I)."
