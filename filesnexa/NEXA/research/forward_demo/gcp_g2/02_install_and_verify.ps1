# NEXA S14: copy the approved EA files from the bucket into the MT5 data folder and verify their SHA-256.
# Run in PowerShell on the VM AFTER MT5 has been installed and started once (so the data folder exists).
#   powershell -ExecutionPolicy Bypass -File 02_install_and_verify.ps1 -Bucket nexa-s14-<project>
param([Parameter(Mandatory = $true)][string]$Bucket)
$ErrorActionPreference = 'Stop'

$Expected = @{
  'NEXA_EA_S14.ex5'                 = 'ff30ac3868bd6af9001a9fe8f40b212aef6b81675c2764080a34b310b401ed99'
  'NEXA_TickLogger.ex5'             = 'f1f847e86f364b0c02e660c4eb5d5aedd6dc1f861556cb2085c2c8bb1a120e9d'
  'NEXA_EA_S14_DEMO_PRODUCTION.set' = '1873bfe3f137af99e1b756eb6117543298d0bef0d0390cc6889d329c038ad4c9'
}

$root = Join-Path $env:APPDATA 'MetaQuotes\Terminal'
$data = Get-ChildItem $root -Directory | Where-Object { $_.Name -match '^[0-9A-F]{32}$' } |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $data) { throw "No MT5 data folder under $root. Start MT5 once, then re-run." }
$adv = Join-Path $data.FullName 'MQL5\Experts\Advisors'
$pre = Join-Path $data.FullName 'MQL5\Presets'
New-Item -ItemType Directory -Force -Path $adv, $pre | Out-Null

$stage = Join-Path $env:TEMP 'nexa_upload'
New-Item -ItemType Directory -Force -Path $stage | Out-Null
$ErrorActionPreference = 'Continue'   # gcloud writes progress to stderr
& gcloud storage cp "gs://$Bucket/upload/*" $stage *> $null
$rc = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($rc -ne 0) { throw "gcloud storage cp failed ($rc)" }

$ok = $true
foreach ($f in $Expected.Keys) {
  $h = (Get-FileHash -Algorithm SHA256 (Join-Path $stage $f)).Hash.ToLower()
  if ($h -ne $Expected[$f]) { Write-Host "FAIL $f $h" -ForegroundColor Red; $ok = $false; continue }
  $dest = if ($f -like '*.set') { $pre } else { $adv }
  Copy-Item (Join-Path $stage $f) $dest -Force
  $h2 = (Get-FileHash -Algorithm SHA256 (Join-Path $dest $f)).Hash.ToLower()
  if ($h2 -eq $Expected[$f]) { Write-Host "PASS $f -> $dest" -ForegroundColor Green } else { Write-Host "FAIL after copy $f" -ForegroundColor Red; $ok = $false }
}
Write-Host "MT5 data folder: $($data.FullName)"
Write-Host "Common\Files:    $(Join-Path $root 'Common\Files')"
if (-not $ok) { throw 'Hash verification FAILED - do not attach the EA.' }
Write-Host 'ALL PASS. Restart MT5 (File > Exit, start again) so the Navigator shows the EAs.'
