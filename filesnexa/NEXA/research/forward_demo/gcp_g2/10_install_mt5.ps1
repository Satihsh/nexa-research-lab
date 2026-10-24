# NEXA S14 VM: download Pepperstone's MT5 installer, verify the MetaQuotes signature, install silently, stop the
# auto-started terminal. Run over SSH as an administrator. (User approval 2026-10-11: "Yes 1 and 2".)
$ErrorActionPreference = 'Stop'
$url = 'https://download.terminal.free/cdn/web/pepperstone.group.limited/mt5/pepperstone5setup.exe'
New-Item -ItemType Directory -Force C:\nexa | Out-Null
$exe = 'C:\nexa\pepperstone5setup.exe'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest $url -OutFile $exe -UseBasicParsing
$sig = Get-AuthenticodeSignature $exe
Write-Output "size=$((Get-Item $exe).Length) sha256=$((Get-FileHash $exe -Algorithm SHA256).Hash)"
Write-Output "signature=$($sig.Status) signer=$($sig.SignerCertificate.Subject)"
if ($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notmatch 'MetaQuotes') { throw 'Installer signature check FAILED - not installing.' }

$p = Start-Process $exe -ArgumentList '/auto' -PassThru
$deadline = (Get-Date).AddMinutes(15)
$t = $null
do {
  Start-Sleep 10
  $t = Get-ChildItem 'C:\Program Files' -Directory -ErrorAction SilentlyContinue |
       ForEach-Object { Join-Path $_.FullName 'terminal64.exe' } | Where-Object { Test-Path $_ } | Select-Object -First 1
} until (($t -and $p.HasExited) -or (Get-Date) -gt $deadline)
if (-not $t) { throw 'terminal64.exe not found after install' }
Start-Sleep 20
Get-Process terminal64, metaeditor64 -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Output "installer_exited=$($p.HasExited) installed=$t"
