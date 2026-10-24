# S14 demo forward check on a Google Cloud Windows VM (G-2), with a view-only Claude connector

**Prepared 2026-10-11 for project `<gcp-project>` (full account, credit RM1,224.75 valid until 2027-01-10).**

**What this is:** the same S14 demo check (account <demo-account>, $200 demo), moved from the Mac to a Windows server in N. Virginia, about 5 ms from Pepperstone's New York servers.

**What it does not change:** the EA, its inputs, the risk settings or the stop rules in `../E_DEPLOYMENT.md`. Those all stay as they are.

**Rules that never change:**
- You do every sign-in and every password. Never paste a password into Claude.
- Only one machine runs S14 on <demo-account> at any time.
- Claude's connector is view-only and can never trade.

## Cost (from the free credit; you pay RM0 if you tear down on time)

| Item | Approx. | ~8 weeks |
|---|---|---|
| e2-medium VM (2 vCPU / 4 GB), us-east4 | ~$27/mo | |
| Windows Server licence ($0.046 per vCPU-hour, Google price list) | ~$67/mo | |
| 50 GB balanced disk, bucket, logs, alert | ~$6/mo | |
| **Total** | **~$100/mo ≈ RM410/mo** | **≈ RM760 of RM1,225** |

- **Budget:** RM100, credits deducted, thresholds 1 % / 50 / 90 / 100 / 150 %. The first email arrives at RM1 of real charges.
- **Tear-down target: 2026-12-08** (step I).

## Files in this folder

| File | Where it runs | What it does |
|---|---|---|
| `01_cloudshell_create.sh` | Cloud Shell | Creates the bucket, the VM service account (bucket write + log write only), the Windows VM, an RDP firewall rule open to **your IP only** (and disables `default-allow-rdp`), the heartbeat metric, the email channel and the "heartbeat missing 30 min" alert |
| `upload/` (2 × .ex5, .set, SHA256SUMS) | → bucket `upload/` | The exact approved files: S14 `ff30ac38…`, TickLogger `f1f847e8…`, production preset `1873bfe3…` |
| `02_install_and_verify.ps1` | VM (your user) | Copies the files into MT5 and **checks their SHA-256**. Stops if anything differs |
| `03_s14_sync.ps1` | VM (scheduled) | Every 15 min: copies `NEXA_*` outputs and the MT5 logs to the bucket (one-way, never deletes), and writes a heartbeat (terminal running? DNA rows / fills, tick-log sizes, errors) |
| `04_register_sync_task.ps1` | VM (administrator) | Registers the 15-minute task as SYSTEM |
| `05_cloudshell_teardown.sh` | Cloud Shell | Deletes everything after you have downloaded the data |

## A. Before you start (about 2 min)

1. In the Cloud console, open **Cloud Shell** (the `>_` icon, top right).
2. Use Cloud Shell's **⋮ → Upload** to upload `01_cloudshell_create.sh` and `05_cloudshell_teardown.sh`.
3. Find your current public IP at https://ifconfig.me.

## B. Create everything (Cloud Shell, about 5 min)

```bash
MYIP=<your IP> ALERT_EMAIL=<your email> bash 01_cloudshell_create.sh
```

- Answer `y` when asked.
- If a step says something "already exists", tell me before re-running.

## C. Windows password and files

1. Set the password **yourself** and keep it private:

   ```bash
   gcloud compute reset-windows-password nexa-s14 --zone=us-east4-c --user=nexa
   ```

2. Upload the files:
   - Go to **Cloud Storage → Buckets → `nexa-s14-<gcp-project>`**.
   - Use **Upload folder** to upload `upload/` (it lands as `upload/…`).
   - Also upload the three `.ps1` files into a folder named `scripts/`.

## D. Connect to the VM

1. Install Microsoft's **Windows App** (Mac App Store).
2. Add a PC using the VM's **External IP** (Compute Engine → VM instances). Sign in as `nexa` with your password.
3. **Travelling:** your IP will change. Update the rule from Cloud Shell, which works from a phone browser:

   ```bash
   gcloud compute firewall-rules update nexa-rdp-myip --source-ranges=<new IP>/32
   ```

4. **To leave, always just close the Remote Desktop window. Never "Sign out"**, because that closes MT5.

## E. Set up MT5 on the VM

1. **Windows updates:** run `sconfig`, choose *Update settings* → **Manual**, so the VM does not reboot itself during the check.
2. **Install MT5:**
   - Download Pepperstone's **MetaTrader 5 for Windows** from pepperstone.com and install it.
   - Start it, and log in to **<demo-account>, Pepperstone-Demo** with your password.
   - Check that the toolbar **Algo Trading** button is **OFF** for now.
3. Install and verify the files. In PowerShell, as the `nexa` user:

   ```powershell
   mkdir C:\nexa; gcloud storage cp "gs://nexa-s14-<project>/scripts/*" C:\nexa\
   powershell -ExecutionPolicy Bypass -File C:\nexa\02_install_and_verify.ps1 -Bucket nexa-s14-<project>
   ```

   - It must print **ALL PASS**.
   - Then **File → Exit** MT5 and start it again.
   - If `gcloud` is not found, install the *Google Cloud CLI for Windows* from cloud.google.com/sdk and re-run.
4. **Charts (8):**
   - Open **M1** charts for **EURUSD, GBPUSD, USDJPY and XAUUSD, two each**.
   - **First chart of each symbol:** drag **NEXA_EA_S14** onto it.
     - **Common** tab: tick *Allow Algo Trading*.
     - **Inputs** tab: leave the defaults, or **Load** `NEXA_EA_S14_DEMO_PRODUCTION.set`.
     - Confirm `InpEnableTrading=true` and `InpRequireDemoAccount=true`.
   - **Second chart of each symbol:** drag **NEXA_TickLogger** onto it.
   - **Tools → Options → Expert Advisors:** *Allow algorithmic trading* ON, *DLL imports* OFF.
   - **File → Profiles → Save As:** `NEXA_S14`.
5. **Sync task:** in PowerShell **Run as Administrator**:

   ```powershell
   powershell -ExecutionPolicy Bypass -File C:\nexa\04_register_sync_task.ps1 -Bucket nexa-s14-<project> -WinUser nexa
   ```

## F. Cut-over (the order matters)

1. **On the Mac:** quit MetaTrader 5 (Cmd-Q). This stops the Mac copy of S14.
2. **On the VM:** switch the **Algo Trading** button **ON**.
3. **Experts tab:** check for 4 × `NEXA init on <SYM> | … | AI=NONE | schema v1.0`, with no errors.
4. **Close the Remote Desktop window.** Do not sign out.
5. **About 15 minutes later, check:**
   - **Cloud Storage:** `s14/common_files/` exists.
   - **Logs Explorer:** `nexa-s14-heartbeat` shows `terminal_running: true`.
6. Tell me **"VPS live"**, and I will record the cut-over in `E_DEPLOYMENT.md` and check the first data.

**If the alert email arrives** ("heartbeat missing 30 min"): connect over RDP and check whether MT5 is open. If the VM is stopped, start it with `gcloud compute instances start nexa-s14 --zone=us-east4-c`.

## G. View-only Claude connector (optional; can be done later)

Google publishes official remote MCP servers:
- **Cloud CLI:** `https://cloudcli.googleapis.com/mcp` (Preview). Runs `gcloud` commands with the signed-in account's permissions.
- **Compute Engine:** `https://compute.googleapis.com/mcp`.

**Steps:**
1. **View-only identity:** use a **second Google account**. Never connect Claude with your owner account. In Cloud Shell:

   ```bash
   V=<<email>>; P=$(gcloud config get-value project); B=nexa-s14-$P
   gcloud projects add-iam-policy-binding $P --member=user:$V --role=roles/compute.viewer --condition=None
   gcloud projects add-iam-policy-binding $P --member=user:$V --role=roles/logging.viewer --condition=None
   gcloud storage buckets add-iam-policy-binding gs://$B --member=user:$V --role=roles/storage.objectViewer
   ```

   Also follow the **"Before you begin / Required roles"** sections of Google's pages *Use the Cloud CLI remote MCP server* and *Use the Compute Engine remote MCP server*. These enable the MCP endpoints and give any MCP-specific role. Their exact names may change, so use Google's page rather than guessing.
2. **OAuth client:**
   - Go to **APIs & Services → OAuth consent screen**: External, Testing, and add the viewer account as a test user.
   - Then **Credentials → Create OAuth client ID → Web application**:
     - Authorized JavaScript origin: `https://claude.ai`
     - Redirect URI: `https://claude.ai/api/mcp/auth_callback` (from Google's "Configure MCP in an AI application" page)
3. **Add the connector:**
   - Go to **claude.ai → Settings → Connectors → Add custom connector**: name `GCP S14 (view-only)`, URL `https://cloudcli.googleapis.com/mcp`, and under Advanced, the client ID and secret.
   - Connect and **sign in as the viewer account**.
   - Optionally add `https://compute.googleapis.com/mcp` the same way.
4. **Test:** ask Claude "check S14". I will read `gs://…/s14/` and the heartbeat log. I will never start, stop or change anything without asking you.

## H. Getting the data

- **Any time:** use the Cloud Storage page to download files from `s14/`.
- **At the end** (Cloud Shell):

  ```bash
  gcloud storage cp -r gs://nexa-s14-$(gcloud config get-value project)/s14 . && zip -qr s14_final.zip s14
  ```

  Then use Cloud Shell's **⋮ → Download** to fetch `s14_final.zip`, and put it in `research/forward_demo/` on the Mac.

## I. Tear-down (by 2026-12-08; the credit expires 2027-01-10)

1. Finish step H first.
2. In Cloud Shell, run `bash 05_cloudshell_teardown.sh` and type `DELETE` when asked.
3. Remove the Claude connector, delete the OAuth client, and remove the viewer account from IAM.
4. **Billing → Reports:** confirm the net cost is RM0 and nothing is still running.

**Cheaper fallback:** a Linux VM with Wine costs about RM230 for 8 weeks instead of about RM760. Ask me for the G-1 pack if the credit gets tight.
