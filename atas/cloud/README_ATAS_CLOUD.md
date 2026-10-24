# NEXA ATAS recorder VM (Google Cloud): built 2026-10-19 by the agent, with user approval

- **Approval:** the user asked to drop S14 and run ATAS X in the cloud ("Or we drop the S14 now, activate ATAS X" → "Can you do for me completely without any error?").
- **Purpose:** ATAS X + NEXA Monitor (recorder) running 24/7, so the user's Mac can be off or at work.

## As built
- **VM `nexa-atas`:** asia-southeast1-b (Singapore), e2-highmem-2 (16 GB; was e2-standard-2 until 2026-10-22) (2 vCPU / 8 GB), Windows Server 2022, 80 GB pd-balanced, shielded VM, external IP <redacted-ip>, tag `nexa-rdp`.
- **Auto-stop:** `--termination-time=2026-11-06T00:00:00Z`, action STOP (the end of the 14-day ATAS trial, plus 1 day). The disk is kept.
- **Cost (from the free credit):** about $0.18 per hour, ≈ RM540 per month, ≈ RM330 to the auto-stop.
- **Service account `nexa-atas-vm`:** objectAdmin on `gs://nexa-atas-<gcp-project>` only, plus logging.logWriter.
- **Software (signature-checked before running):**
  - ATAS X installer (2,561,592 B, sha256 BAD2FBB13CE7E638…, Authenticode Valid, signer ATAS LLC, Riga), silent install → `C:\Program Files\ATAS X`. Assemblies 8.0.15.656, the same as the Mac;
  - Google Chrome Enterprise MSI and the Chrome Remote Desktop host MSI (Valid, Google), exit 0.
- **Windows Update:** NoAutoUpdate=1.
- **Windows user `nexa`** (Remote Desktop Users). The user sets the password; the agent never sees it.
- **Tasks:**
  - `NEXA_ATAS_Sync` (SYSTEM, every 15 min + at start-up) runs `C:\nexa\atas_sync.ps1`. It rsyncs `C:\Users\nexa\Documents\NEXA_ATAS` → `gs://…/nexa_atas`, one-way, and writes the heartbeat log `nexa-atas-heartbeat`.
  - `NEXA_InstallAddon` (at `nexa` log-on) copies `C:\nexa\NexaMonitor.dll` (sha256 c4012e75…, the same build as the Mac) into the ATAS indicator folders.
- **Alert:** metric `atas_heartbeat_ok` + policy 10947394329638106228 ("heartbeat missing 45 min", e-mail to the user). Created **disabled**; enable once ATAS runs.
- **Access:** firewall `nexa-access-myip` (tcp 22/3389) from the user's current IPv4 only. The agent uses `gcloud compute ssh` (key auth, admin).
  - `gcloud compute scp` fails against this Windows SSH server, so files go through `gs://…/setup/`.

## Rules
- **ATAS runs from one place at a time.** ATAS allows two sessions only from the same IP, so close ATAS on the Mac while the VM runs it.
- **Never "Sign out" of Windows;** just close the remote window. Signing out closes ATAS.
- **No Topstep orders from this VM.** Topstep prohibits VPS order flow. The VM is for recording and ATAS demo (H-DISC1) only.

## Teardown
- Delete the VM, disk, bucket (after downloading), service account, metric and alert policy.
- Revert the firewall rule.

## Change 2026-10-19 ~01:55 +08: classic ATAS instead of ATAS X on the VM
- **Problem:** ATAS X failed with "WGL: The driver does not appear to support OpenGL". It renders with OpenGL/Vulkan (GLFW, Silk.NET), and the VM only has the Microsoft Remote Display Adapter (no GPU).
- **Fix:** installed **classic ATAS** (`https://atas.net/Setup/ATASPlatform.exe`, 2,318,224 B, sha256 2931BB01…, Authenticode Valid, ATAS LLC) silently.
  - It goes to `C:\Program Files (x86)\ATAS Platform`, with a desktop shortcut "ATAS Platform". Assemblies 8.0.15.304, net10.
  - ATAS X was uninstalled from the VM (exit 0); the Mac is unaffected.
- **NEXA for classic:** `atas/NexaMonitorClassic/NexaMonitorClassic.csproj` compiles the same `../NexaMonitor/*.cs` against `atas/refs_classic/`.
  - refs_classic holds the VM's 5 ATAS DLLs and is not committed.
  - Output NexaMonitor.dll sha256 fa173326…, installed in C:\nexa and the three Indicators folders.

## Incident 2026-10-19 04:35 +08: ATAS killed by low memory (fixed)
- **What happened:** ATAS (OFT.Platform.exe) grew from 3.4 GB to ~7 GB of virtual memory between 18:50 and 20:30 UTC on a Sunday, with futures closed.
  - Windows then raised "Out of Virtual Memory" (Resource-Exhaustion-Detector 20:20/20:26/20:31, popup 20:35) and ATAS was gone.
  - Heartbeat atas_running=False from 20:35 UTC; no live recording at the Monday open.
- **Causes:**
  1. The GCE Windows image page file was **fixed at 1 GB**, so the commit limit was about 9 GB.
  2. The synced ATAS workspace contains a **BTCUSDT (Binance futures) component with heatmap**. It streams 24/7 and was the only live feed while CME was closed.
- **Fixes (agent, 11:40 +08):**
  - Page file set to 16–24 GB and verified after restart (16,384 MB).
  - Task `NEXA_KeepATAS` (Interactive, nexa) runs `keep_atas.ps1`: starts ATAS 1 min after log-on, then every 10 min if OFT.Platform is not running; since 2026-10-21 also restarts ATAS above 9 GB private memory (14 GB since 2026-10-22) (log `C:\nexa\keep_atas.log`, last line in heartbeat `keep_last`).
  - 2026-10-21 (user chose A + C): the watchdog also (A) clicks **Connect** on the ATAS login window when "Remember data" is ticked (UI Automation ids `RememberCheckEdit`, `ConnectButton`), and (C) restarts ATAS once per weekday in the CME halt (16:05–16:48 CT ≈ 05:05 MYT) if it was started before that day's 16:00 CT.
  - Closing: ATAS asks "Save current workspace?" inside the main window; the watchdog closes the main window by UI Automation and presses **Save and close** (force-kill only after 90 s). Do NOT use Process.CloseMainWindow(): it hit a floating chart window and closed the chart (NQ chart lost 2026-10-21).
  - Verified 2026-10-20 17:59–18:01 UTC: Save and close → clean exit → start → auto Connect → ES recording again after ~1.5 min.
  - Helper: task `NEXA_Shot` runs `shot.ps1` (desktop screenshot to `C:\nexa\shot.png`).
  - Workspace backed up to `C:\nexa\Default_workspace_backup_*.ws`. VM restarted 03:42 UTC.
- **Still needed from the user:**
  - Log in once via Windows App, then log in to ATAS with "remember" ticked, so the watchdog can reconnect alone.
  - Close the BTCUSDT component and disable the Binance / Crypto Sim connections.
- **Access:** firewall `nexa-access-myip` allows only the user's current home IPv4 (/32). It changes often: check `curl -4 ifconfig.me` and update the rule before SSH.

## Incident 2026-10-19/20: second out-of-memory crash, and a blind heartbeat (fixed)
- **What happened:** ATAS memory grew through the 19-Oct US session. Recorder output stalled (tape ~16:50–17:00 UTC, bars by 20:02 UTC), and heartbeats became sparse, then absent from 14:56 UTC.
  - At ~21:01 UTC ATAS threw System.OutOfMemoryException (inside the still-active **Binance** connector) and crashed at 21:41 UTC.
  - `NEXA_KeepATAS` restarted it at 21:50 UTC, but at the **login window**: credentials were not saved.
  - From then on **nothing was recorded** (no 2026-10-20 files), while the heartbeat still said `atas_running=true`.
  - The alert fired at 16:00 UTC (heartbeat absent) and "recovered" at 21:52 UTC only because the process existed again.
- **Fix:** `atas_sync.ps1` now reports `recording_ok` = market closed (CME Globex hours, CT) OR newest recorder file ≤ 20 min old, plus `recorder_age_min`, `market_open` and `atas_private_mb`. A stale recorder during market hours is reported as an error.
  - Metric `atas_heartbeat_ok` now requires `atas_running=true AND recording_ok=true`, so the alert fires when data stops, not only when the process dies.
  - Verified 13:53 UTC 20-Oct: recording_ok=false, "recorder stale 1071.6 min".
- **Open:**
  - The user logs in with "remember me", removes Binance / Crypto Sim / the BTCUSDT heatmap / the AlphaX indicator, and saves the workspace.
  - Then consider a daily ATAS restart in the CME halt and/or 16 GB RAM.

## Change 2026-10-22: 16 GB
- 09:41–09:42 UTC: stopped, machine type e2-standard-2 → **e2-highmem-2** (2 vCPU, 16 GB), started (user-approved; paid from credit, ≈ +$21/month). The 2026-11-06 auto-stop was kept.
- **The external IP is ephemeral and changed** to <redacted-ip>. Every stop/start may change it: update Windows App.
- **Windows has no auto-logon**: after any VM restart the user must log in as `nexa` once (Windows App), then close the window without signing out. The watchdog then starts ATAS.
- After the user's log-on at 09:53 UTC, ATAS started and recorded again from ≈ 09:55 UTC (tape/DOM written 09:56:07). Recording gap ≈ 09:41–09:55 UTC (London session).
- **Watchdog limit raised to 14 GB** (`keep_atas.ps1` default `$LimitMB = 14336`, sha256 a3d71db8; backup of the old script on the VM: `C:\nexa\keep_atas_9216.ps1.bak`). User-approved 2026-10-22.
  - Test 10:00 UTC: parse check 0 errors; normal task run left ATAS alone (1.1 GB); a forced restart via a temporary task (`-ForceRestart`, removed afterwards) pressed "Save and close", restarted ATAS and clicked Connect in 42 s; NQ/ES tape and DOM written again by 10:02:53.
