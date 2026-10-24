# NEXA ATAS recorder VM: one-time setup, run over SSH as the administrator.
# Downloads only from official sources and refuses any file whose Authenticode signature is not Valid.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
New-Item -ItemType Directory -Force -Path 'C:\nexa\dl' | Out-Null

# 1. Windows Update: manual (no surprise reboots during recording)
New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU' -Force | Out-Null
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU' -Name NoAutoUpdate -Value 1 -Type DWord
'windows update: manual'

function Get-Signed([string]$url, [string]$file, [string]$signer) {
  $path = Join-Path 'C:\nexa\dl' $file
  Invoke-WebRequest -Uri $url -OutFile $path -UseBasicParsing
  $sig = Get-AuthenticodeSignature $path
  $hash = (Get-FileHash $path -Algorithm SHA256).Hash
  Write-Host ("{0}: {1:N0} bytes, sha256 {2}, signature {3}, signer {4}" -f $file, (Get-Item $path).Length, $hash.Substring(0,16), $sig.Status, $sig.SignerCertificate.Subject)   # Write-Host: keep the return value = path only
  if ($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notmatch $signer) { throw "REFUSED $file : signature not valid for $signer" }
  return $path
}

# 2. Google Chrome (for Chrome Remote Desktop set-up) + Chrome Remote Desktop host
$chrome = Get-Signed 'https://dl.google.com/chrome/install/googlechromestandaloneenterprise64.msi' 'chrome.msi' 'Google'
$crd = Get-Signed 'https://dl.google.com/edgedl/chrome-remote-desktop/chromeremotedesktophost.msi' 'crdhost.msi' 'Google'
foreach ($m in $chrome, $crd) {
  $p = Start-Process msiexec.exe -ArgumentList "/i `"$m`" /qn /norestart" -Wait -PassThru
  if ($p.ExitCode -ne 0) { throw "msiexec $m exit $($p.ExitCode)" }
}
if (-not (Test-Path 'C:\Program Files\Google\Chrome\Application\chrome.exe')) { throw 'Chrome not installed' }
'chrome + chrome remote desktop host installed (verified)'

# 3. ATAS X installer (official link from atas.net/atas-download)
$atas = Get-Signed 'https://updates.orderflowtrading.net/v2/ATAS%20X.exe' 'ATAS_X_setup.exe' '.'
'ATAS X installer downloaded and signature-checked: ' + $atas
