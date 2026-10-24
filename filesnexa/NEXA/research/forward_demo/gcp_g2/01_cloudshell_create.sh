#!/usr/bin/env bash
# NEXA S14 demo forward check: Google Cloud set-up (G-2, Windows). Run in Google Cloud Shell.
# Creates: storage bucket, VM service account, Windows VM (us-east4), firewall rule for RDP from YOUR IP only,
# heartbeat log metric, email notification channel and a "heartbeat missing 30 min" alert.
# Creates nothing billable beyond the VM (~USD 100/month, paid from the free credit), the bucket (cents) and logs (free tier).
#
# Usage (Cloud Shell):
#   MYIP=<your current public IP> ALERT_EMAIL=<your email> bash 01_cloudshell_create.sh
set -euo pipefail

PROJECT="$(gcloud config get-value project 2>/dev/null)"
REGION=us-east4
ZONE=us-east4-c
VM=nexa-s14
SA_NAME=nexa-s14-vm
SA="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"
BUCKET="nexa-s14-${PROJECT}"
: "${MYIP:?set MYIP to your current public IP (e.g. from https://ifconfig.me)}"
: "${ALERT_EMAIL:?set ALERT_EMAIL to the address that should receive the alert}"

echo "Project: $PROJECT  Zone: $ZONE  Bucket: gs://$BUCKET"
read -r -p "Continue? [y/N] " ok; [[ "$ok" == "y" ]] || exit 1

gcloud services enable compute.googleapis.com storage.googleapis.com logging.googleapis.com monitoring.googleapis.com

# 1. Bucket (private, uniform access, same region as the VM)
gcloud storage buckets create "gs://$BUCKET" --location="$REGION" --uniform-bucket-level-access --public-access-prevention

# 2. VM service account: write to this bucket + write logs. Nothing else.
gcloud iam service-accounts create "$SA_NAME" --display-name="NEXA S14 VM"
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET" --member="serviceAccount:$SA" --role=roles/storage.objectAdmin
gcloud projects add-iam-policy-binding "$PROJECT" --member="serviceAccount:$SA" --role=roles/logging.logWriter --condition=None

# 3. Firewall: RDP only from your IP; disable the default open-to-the-internet RDP rule if it exists (reversible).
gcloud compute firewall-rules create nexa-rdp-myip --network=default --direction=INGRESS --action=ALLOW \
  --rules=tcp:3389 --source-ranges="${MYIP}/32" --target-tags=nexa-rdp
if gcloud compute firewall-rules describe default-allow-rdp >/dev/null 2>&1; then
  gcloud compute firewall-rules update default-allow-rdp --disabled
fi

# 4. Windows VM: e2-medium (2 vCPU, 4 GB), Windows Server 2022, 50 GB balanced disk
gcloud compute instances create "$VM" --zone="$ZONE" --machine-type=e2-medium \
  --image-family=windows-2022 --image-project=windows-cloud \
  --boot-disk-size=50GB --boot-disk-type=pd-balanced \
  --service-account="$SA" --scopes=cloud-platform --tags=nexa-rdp \
  --shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring

# 5. Heartbeat log metric + email channel + alert (fires if no "terminal running" heartbeat for 30 min)
gcloud logging metrics create s14_heartbeat_ok \
  --description="NEXA S14 heartbeat with terminal64 running" \
  --log-filter="logName=\"projects/${PROJECT}/logs/nexa-s14-heartbeat\" AND jsonPayload.terminal_running=true"
CHANNEL="$(gcloud beta monitoring channels create --display-name='NEXA S14 owner' --type=email \
  --channel-labels=email_address="$ALERT_EMAIL" --format='value(name)')"
cat > /tmp/s14_policy.json <<EOF
{
  "displayName": "NEXA S14 heartbeat missing (30 min)",
  "combiner": "OR",
  "conditions": [{
    "displayName": "No terminal-running heartbeat for 30 min",
    "conditionAbsent": {
      "filter": "metric.type=\"logging.googleapis.com/user/s14_heartbeat_ok\" AND resource.type=\"global\"",
      "duration": "1800s",
      "aggregations": [{"alignmentPeriod": "900s", "perSeriesAligner": "ALIGN_SUM"}]
    }
  }],
  "notificationChannels": ["${CHANNEL}"],
  "alertStrategy": {"autoClose": "86400s"}
}
EOF
gcloud alpha monitoring policies create --policy-from-file=/tmp/s14_policy.json

echo
echo "DONE. Next (README step C): set the Windows password yourself with:"
echo "  gcloud compute reset-windows-password $VM --zone=$ZONE --user=nexa"
echo "Then upload the 'upload' folder to gs://$BUCKET/upload/ (Cloud Storage page > Upload folder)."
