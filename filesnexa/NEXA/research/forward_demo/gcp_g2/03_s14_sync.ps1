# NEXA S14: every 15 min, copy the forward-check outputs and MT5 logs to the private bucket and write a heartbeat.
# One-way (VM -> bucket); never deletes anything; never touches MT5 or trading.
# Registered by 04_register_sync_task.ps1 to run as SYSTEM, using the VM service account.
param(
  [Parameter(Mandatory = $true)][string]$Bucket,
  [Parameter(Mandatory = $true)][string]$WinUser,
  [string]$Mt5Dir = 'C:\MT5'          # portable MT5 (data folder = install folder)
)
$ErrorActionPreference = 'Continue'
$errors = @()
$locked = @()
$root = "C:\Users\$WinUser\AppData\Roaming\MetaQuotes\Terminal"
$common = Join-Path $root 'Common\Files'
$stage = 'C:\nexa_sync_stage'

# Copy with read-sharing into a staging folder (MT5 may hold the files open), then upload the staging copy.
function Stage-Copy([string]$src, [string]$dst, [string]$filter) {
  New-Item -ItemType Directory -Force -Path $dst | Out-Null
  Get-ChildItem $src -File -Filter $filter -ErrorAction SilentlyContinue | ForEach-Object {
    $f = $_
    try {
      $in = [System.IO.File]::Open($f.FullName, 'Open', 'Read', 'ReadWrite')
      $out = [System.IO.File]::Create((Join-Path $dst $f.Name))
      $in.CopyTo($out); $out.Close(); $in.Close()
    } catch {
      # The tick logger holds today's file open without read-sharing; it is released at day change (expected).
      if ($f.Name -like 'NEXA_TickLog_*') { $script:locked += $f.Name }
      else { $script:errors += "copy $($f.FullName): $($_.Exception.Message)" }
    }
  }
}

Stage-Copy $common (Join-Path $stage 'common_files') 'NEXA_*'
Stage-Copy (Join-Path $Mt5Dir 'logs') (Join-Path $stage 'terminal_logs\portable') '*.log'
Stage-Copy (Join-Path $Mt5Dir 'MQL5\Logs') (Join-Path $stage 'mql5_logs\portable') '*.log'
Get-ChildItem $root -Directory | Where-Object { $_.Name -match '^[0-9A-F]{32}$' } | ForEach-Object {
  Stage-Copy (Join-Path $_.FullName 'logs') (Join-Path $stage "terminal_logs\$($_.Name)") '*.log'
  Stage-Copy (Join-Path $_.FullName 'MQL5\Logs') (Join-Path $stage "mql5_logs\$($_.Name)") '*.log'
}

& gcloud storage rsync $stage "gs://$Bucket/s14" --recursive --quiet 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { $errors += "gcloud storage rsync exit $LASTEXITCODE" }

# Heartbeat (Cloud Logging, via the VM service account token from the metadata server)
$dna = @{}
Get-ChildItem (Join-Path $stage 'common_files') -Filter 'NEXA_TradeDNA_*.csv' -ErrorAction SilentlyContinue | ForEach-Object {
  $rows = Import-Csv $_.FullName -ErrorAction SilentlyContinue
  $dna[$_.BaseName] = @{
    rows = @($rows).Count
    fills = @($rows | Where-Object { $_.event -eq 'FILL' }).Count
    last_write_utc = $_.LastWriteTimeUtc.ToString('o')
  }
}
$tick = Get-ChildItem (Join-Path $stage 'common_files') -Filter 'NEXA_TickLog_*.csv' -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 4 |
        ForEach-Object { @{ name = $_.Name; bytes = $_.Length; last_write_utc = $_.LastWriteTimeUtc.ToString('o') } }
$payload = @{
  terminal_running = [bool](Get-Process terminal64 -ErrorAction SilentlyContinue)
  host = $env:COMPUTERNAME
  ts_utc = (Get-Date).ToUniversalTime().ToString('o')
  dna = $dna
  ticklogs = @($tick)
  tick_locked_active = @($locked)
  errors = @($errors | Select-Object -First 10)
}
try {
  $md = @{ 'Metadata-Flavor' = 'Google' }
  $project = Invoke-RestMethod -Headers $md -Uri 'http://metadata.google.internal/computeMetadata/v1/project/project-id'
  $token = (Invoke-RestMethod -Headers $md -Uri 'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token').access_token
  $body = @{
    logName = "projects/$project/logs/nexa-s14-heartbeat"
    resource = @{ type = 'global' }
    entries = @(@{ severity = $(if ($errors.Count) { 'WARNING' } else { 'INFO' }); jsonPayload = $payload })
  } | ConvertTo-Json -Depth 8
  Invoke-RestMethod -Method Post -Uri 'https://logging.googleapis.com/v2/entries:write' `
    -Headers @{ Authorization = "Bearer $token" } -ContentType 'application/json' -Body $body | Out-Null
} catch {
  Add-Content -Path 'C:\nexa_sync_stage\heartbeat_error.txt' -Value "$(Get-Date -Format o) $($_.Exception.Message)"
}
