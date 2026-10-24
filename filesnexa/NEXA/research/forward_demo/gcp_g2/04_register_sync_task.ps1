# NEXA S14: register 03_s14_sync.ps1 to run every 15 minutes (and at start-up) as SYSTEM.
# Run once in an elevated PowerShell on the VM:
#   powershell -ExecutionPolicy Bypass -File 04_register_sync_task.ps1 -Bucket nexa-s14-<project> -WinUser nexa
param(
  [Parameter(Mandatory = $true)][string]$Bucket,
  [Parameter(Mandatory = $true)][string]$WinUser
)
$ErrorActionPreference = 'Stop'
$dir = 'C:\nexa'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
Copy-Item (Join-Path $PSScriptRoot '03_s14_sync.ps1') $dir -Force
$arg = "-NoProfile -ExecutionPolicy Bypass -File `"$dir\03_s14_sync.ps1`" -Bucket $Bucket -WinUser $WinUser"
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arg
$every = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 15)
$boot = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -MultipleInstances IgnoreNew -StartWhenAvailable
Register-ScheduledTask -TaskName 'NEXA_S14_Sync' -Action $action -Trigger @($every, $boot) -Settings $settings `
  -User 'SYSTEM' -RunLevel Highest -Force | Out-Null
Start-ScheduledTask -TaskName 'NEXA_S14_Sync'
Write-Host 'Registered NEXA_S14_Sync (every 15 min). First run started; check gs://' $Bucket '/s14/ in ~2 min.'
