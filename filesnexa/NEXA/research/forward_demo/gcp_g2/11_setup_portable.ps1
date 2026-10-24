# NEXA S14 VM: build the portable MT5 at C:\MT5 with the approved EA files and the 8-chart profile, verify every
# hash, write the first-start config, create desktop shortcuts, and set Windows Update to manual (user approved
# 2026-10-11: "Yes 1 and 2"). Run over SSH as an administrator. Algo Trading stays OFF until the user's cut-over.
param([Parameter(Mandatory = $true)][string]$Bucket)
$ErrorActionPreference = 'Stop'
$src = 'C:\Program Files\Pepperstone MetaTrader 5'
$mt5 = 'C:\MT5'
$Expected = @{
  'NEXA_EA_S14.ex5'                 = 'ff30ac3868bd6af9001a9fe8f40b212aef6b81675c2764080a34b310b401ed99'
  'NEXA_TickLogger.ex5'             = 'f1f847e86f364b0c02e660c4eb5d5aedd6dc1f861556cb2085c2c8bb1a120e9d'
  'NEXA_EA_S14_DEMO_PRODUCTION.set' = '1873bfe3f137af99e1b756eb6117543298d0bef0d0390cc6889d329c038ad4c9'
}

# 1. Portable copy
if (-not (Test-Path "$mt5\terminal64.exe")) {
  robocopy $src $mt5 /E /NFL /NDL /NJH /NJS /NP | Out-Null
  if ($LASTEXITCODE -ge 8) { throw "robocopy failed ($LASTEXITCODE)" }
}
$adv = "$mt5\MQL5\Experts\Advisors"; $pre = "$mt5\MQL5\Presets"; $prof = "$mt5\MQL5\Profiles\Charts\NEXA_S14"
New-Item -ItemType Directory -Force $adv, $pre, $prof | Out-Null

# 2. Files from the bucket, hash-verified
$stage = 'C:\nexa\upload'
New-Item -ItemType Directory -Force $stage | Out-Null
$ErrorActionPreference = 'Continue'   # gcloud writes progress to stderr
& gcloud storage cp -r "gs://$Bucket/upload/*" $stage *> $null
$rc = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($rc -ne 0) { throw "gcloud storage cp failed ($rc)" }
foreach ($f in $Expected.Keys) {
  $h = (Get-FileHash "$stage\$f" -Algorithm SHA256).Hash.ToLower()
  if ($h -ne $Expected[$f]) { throw "HASH MISMATCH $f $h" }
  $dest = if ($f -like '*.set') { $pre } else { $adv }
  Copy-Item "$stage\$f" $dest -Force
  if ((Get-FileHash "$dest\$f" -Algorithm SHA256).Hash.ToLower() -ne $Expected[$f]) { throw "HASH MISMATCH after copy $f" }
  Write-Output "PASS $f"
}
$sums = Get-Content "$stage\profile_NEXA_S14\SHA256SUMS" | ForEach-Object { $p = $_ -split '\s+'; @{ h = $p[0]; f = $p[1] } }
foreach ($s in $sums) {
  Copy-Item "$stage\profile_NEXA_S14\$($s.f)" $prof -Force
  if ((Get-FileHash "$prof\$($s.f)" -Algorithm SHA256).Hash.ToLower() -ne $s.h) { throw "HASH MISMATCH $($s.f)" }
}
Write-Output "PASS profile NEXA_S14 ($($sums.Count) charts)"

# 3. First-start config: account + server + profile; Algo Trading OFF (switched on by the user at cut-over)
@"
[Common]
Login=<demo-account>
Server=Pepperstone-Demo
[Charts]
ProfileLast=NEXA_S14
[Experts]
AllowLiveTrading=1
AllowDllImport=0
Enabled=0
"@ | Set-Content "$mt5\nexa_first.ini" -Encoding Unicode

# 4. Desktop shortcuts (all users)
$ws = New-Object -ComObject WScript.Shell
foreach ($sc in @(@{ n = '1 MT5 FIRST START (NEXA)'; a = "/portable /config:$mt5\nexa_first.ini" }, @{ n = '2 MT5 NEXA'; a = '/portable' })) {
  $l = $ws.CreateShortcut("C:\Users\Public\Desktop\$($sc.n).lnk")
  $l.TargetPath = "$mt5\terminal64.exe"; $l.Arguments = $sc.a; $l.WorkingDirectory = $mt5; $l.Save()
}
Write-Output 'Shortcuts created on the Public desktop'

# 5. Windows Update: manual (no automatic install / reboot) until tear-down
$au = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU'
New-Item -Path $au -Force | Out-Null
Set-ItemProperty -Path $au -Name NoAutoUpdate -Value 1 -Type DWord
Set-ItemProperty -Path $au -Name NoAutoRebootWithLoggedOnUsers -Value 1 -Type DWord
Write-Output "WindowsUpdate NoAutoUpdate=$((Get-ItemProperty $au).NoAutoUpdate)"
Write-Output 'SETUP OK'
