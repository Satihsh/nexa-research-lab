# NEXA ATAS recorder VM: every 15 min, copy the NEXA journal + recorder folder to the private bucket and write a heartbeat.
# One-way (VM -> bucket); never deletes anything; never touches ATAS, orders or trading. Runs as SYSTEM.
param(
  [string]$Bucket,
  [string]$WinUser,
  [switch]$SelfTest
)
$ErrorActionPreference = 'Continue'

# Is CME Globex open at this Central-time moment? Sun 17:00 CT -> Fri 16:00 CT, daily halt 16:00-17:00 CT.
# Edges padded (15:54 / 17:15) so the halt boundaries don't raise false alarms.
# shortcut: CME holidays are not modelled, so holiday sessions may report stale; add a holiday list if alerts get noisy.
function Test-CmeOpen([datetime]$ct) {
  $t = $ct.TimeOfDay.TotalHours
  switch ($ct.DayOfWeek) {
    'Saturday' { $false } 'Sunday' { $t -ge 17.25 } 'Friday' { $t -lt 15.9 }
    default { $t -lt 15.9 -or $t -ge 17.25 } }
}
if ($SelfTest) {
  # 2026-10-19 is a Monday
  $cases = @(
    @('2026-10-17 12:00', $false), @('2026-10-18 17:00', $false), @('2026-10-18 17:30', $true),
    @('2026-10-19 10:00', $true), @('2026-10-19 15:50', $true), @('2026-10-19 16:30', $false),
    @('2026-10-19 17:30', $true), @('2026-10-20 02:00', $true), @('2026-10-23 15:00', $true),
    @('2026-10-23 16:30', $false), @('2026-10-23 20:00', $false))
  $bad = @($cases | Where-Object { (Test-CmeOpen ([datetime]$_[0])) -ne $_[1] })
  $bad | ForEach-Object { Write-Output "FAIL $($_[0]) expected $($_[1])" }
  Write-Output "$($cases.Count - $bad.Count)/$($cases.Count) market-hours cases pass"
  exit [int]($bad.Count -gt 0)
}
if (-not $Bucket -or -not $WinUser) { throw 'Bucket and WinUser are required' }
$errors = @()
$src = "C:\Users\$WinUser\Documents\NEXA_ATAS"
if (Test-Path $src) {
  & gcloud storage rsync $src "gs://$Bucket/nexa_atas" --recursive --quiet 2>&1 | Out-Null
  if ($LASTEXITCODE -ne 0) { $errors += "gcloud storage rsync exit $LASTEXITCODE" }
} else { $errors += "missing $src" }

# Newest recorder files per instrument folder (proves data is flowing)
$inst = @()
Get-ChildItem (Join-Path $src 'recorder') -Directory -ErrorAction SilentlyContinue | ForEach-Object {
  $newest = Get-ChildItem $_.FullName -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 3
  $inst += @{ folder = $_.Name; files = @($newest | ForEach-Object { @{ name = $_.Name; bytes = $_.Length; last_write_utc = $_.LastWriteTimeUtc.ToString('o') } }) }
}
# Exact main-process name (same as the NEXA_KeepATAS watchdog), so helper processes can't count as "running".
$atas = Get-Process -Name 'OFT.Platform' -ErrorAction SilentlyContinue | Select-Object -First 1
# Is data actually being recorded? (ATAS can be running but logged out.) Outside CME hours stale files are expected.
$marketOpen = Test-CmeOpen ([TimeZoneInfo]::ConvertTimeBySystemTimeZoneId((Get-Date).ToUniversalTime(), 'Central Standard Time'))
$newest = Get-ChildItem (Join-Path $src 'recorder') -Recurse -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
$ageMin = if ($newest) { [math]::Round(((Get-Date).ToUniversalTime() - $newest.LastWriteTimeUtc).TotalMinutes, 1) } else { 99999 }
$recordingOk = (-not $marketOpen) -or ($ageMin -le 20)
if (-not $recordingOk) { $errors += "recorder stale $ageMin min during market hours (ATAS logged out or frozen?)" }
$payload = @{
  atas_running = [bool]$atas
  atas_process = $(if ($atas) { $atas.ProcessName } else { '' })
  atas_private_mb = $(if ($atas) { [math]::Round($atas.PrivateMemorySize64 / 1MB) } else { 0 })
  market_open = $marketOpen
  recorder_age_min = $ageMin
  recording_ok = $recordingOk
  keep_last = "$(Get-Content 'C:\nexa\keep_atas.log' -Tail 1 -ErrorAction SilentlyContinue)"
  host = $env:COMPUTERNAME
  ts_utc = (Get-Date).ToUniversalTime().ToString('o')
  recorder = @($inst)
  errors = @($errors | Select-Object -First 10)
}
try {
  $md = @{ 'Metadata-Flavor' = 'Google' }
  $project = Invoke-RestMethod -Headers $md -Uri 'http://metadata.google.internal/computeMetadata/v1/project/project-id'
  $token = (Invoke-RestMethod -Headers $md -Uri 'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token').access_token
  $body = @{
    logName = "projects/$project/logs/nexa-atas-heartbeat"
    resource = @{ type = 'global' }
    entries = @(@{ severity = $(if ($errors.Count) { 'WARNING' } else { 'INFO' }); jsonPayload = $payload })
  } | ConvertTo-Json -Depth 8
  Invoke-RestMethod -Method Post -Uri 'https://logging.googleapis.com/v2/entries:write' `
    -Headers @{ Authorization = "Bearer $token" } -ContentType 'application/json' -Body $body | Out-Null
} catch {
  New-Item -ItemType Directory -Force -Path 'C:\nexa' | Out-Null
  Add-Content -Path 'C:\nexa\heartbeat_error.txt' -Value "$(Get-Date -Format o) $($_.Exception.Message)"
}
