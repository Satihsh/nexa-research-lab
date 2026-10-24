# NEXA_KeepATAS watchdog (scheduled task, Interactive as the ATAS user, every 10 min).
# - starts classic ATAS if it is not running;
# - restarts it if its memory passes the limit (it grows inside ATAS until the VM runs out: incidents 2026-10-19/20);
# - restarts it once per weekday in the CME halt (16:00-17:00 CT), so memory resets when no data is missed;
# - clicks "Connect" on the ATAS login window when "Remember data" is shown (user-approved 2026-10-21; uses ATAS's own
#   saved login, never reads or types the password).
# Never touches orders or workspaces.
param([int]$LimitMB = 14336, [switch]$ForceRestart)  # 14 GB since the 2026-10-22 upgrade to 16 GB RAM (was 9216 on 8 GB)
$exe = 'C:\Program Files (x86)\ATAS Platform\OFT.Platform.exe'
$log = 'C:\nexa\keep_atas.log'
function Log($m) { Add-Content -Path $log -Value "$((Get-Date).ToUniversalTime().ToString('o')) $m" }

function Stop-Atas($p, $why) {
  Log "restart: $why"
  # Close the MAIN window by UI Automation: Process.CloseMainWindow() can hit a floating chart window instead,
  # which closes that chart and leaves ATAS running (lost the charts on 2026-10-21).
  try {
    Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
    $A = [System.Windows.Automation.AutomationElement]
    $main = $null
    foreach ($w in $A::RootElement.FindAll([System.Windows.Automation.TreeScope]::Children,
        (New-Object System.Windows.Automation.PropertyCondition ($A::ProcessIdProperty, $p.Id)))) {
      if ($w.Current.Name -like 'ATAS - `[*') { $main = $w }
    }
    if ($main) {
      $main.GetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern).Close()
      # ATAS then asks "Save current workspace?" (Close without saving / Don't close / Save and close) inside the main window.
      $walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
      for ($i = 0; $i -lt 10 -and -not $p.HasExited; $i++) {
        Start-Sleep -Seconds 2
        $hit = $main.FindFirst([System.Windows.Automation.TreeScope]::Descendants,
          (New-Object System.Windows.Automation.PropertyCondition ($A::NameProperty, 'Save and close')))
        while ($hit -and $hit.Current.ControlType -ne [System.Windows.Automation.ControlType]::Button) { $hit = $walker.GetParent($hit) }
        if ($hit) { $hit.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke(); Log 'pressed "Save and close"'; break }
      }
    }
    else { Log 'ATAS main window not found' }
  } catch { Log "main-window close failed: $($_.Exception.Message)" }
  if (-not $p.WaitForExit(90000)) { Log 'graceful close timed out after 90 s: killing'; Stop-Process -Id $p.Id -Force }
  Start-Sleep -Seconds 10
}

# Click Connect on the ATAS login window ("Authorization"), only when its "Remember data" box is ticked.
# Element ids from the classic ATAS 8.0.15 UI Automation tree (2026-10-21): RememberCheckEdit, ConnectButton.
function Connect-Atas([int]$Tries) {
  Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
  $A = [System.Windows.Automation.AutomationElement]
  $T = [System.Windows.Automation.TreeScope]
  $C = [System.Windows.Automation.PropertyCondition]
  for ($i = 0; $i -lt $Tries; $i++) {                               # 18 tries = up to 3 min for the login window
    $p = Get-Process -Name 'OFT.Platform' -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $p) { return }
    $wins = $A::RootElement.FindAll($T::Children, (New-Object $C ($A::ProcessIdProperty, $p.Id)))
    foreach ($w in $wins) {
      if ($w.Current.Name -ne 'Authorization') { continue }
      $chk = $w.FindFirst($T::Descendants, (New-Object $C ($A::AutomationIdProperty, 'RememberCheckEdit')))
      if (-not $chk -or $chk.GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern).Current.ToggleState -ne 'On') {
        Log 'login window open but "Remember data" is not ticked: not clicking Connect'; return }
      $btn = $w.FindFirst($T::Descendants, (New-Object $C ($A::AutomationIdProperty, 'ConnectButton')))
      if ($btn) {
        $btn.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
        Log 'clicked Connect on the ATAS login window'
        return
      }
    }
    Start-Sleep -Seconds 10
  }
}

$p = Get-Process -Name 'OFT.Platform' -ErrorAction SilentlyContinue | Select-Object -First 1
if ($p) {
  $mb = [math]::Round($p.PrivateMemorySize64 / 1MB)
  $ct = [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId((Get-Date).ToUniversalTime(), 'Central Standard Time')
  $startCt = [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId($p.StartTime.ToUniversalTime(), 'Central Standard Time')
  $inHalt = "$($ct.DayOfWeek)" -notin 'Saturday', 'Sunday' -and $ct.TimeOfDay.TotalHours -ge 16.05 -and $ct.TimeOfDay.TotalHours -lt 16.8
  if ($ForceRestart) { Stop-Atas $p 'forced (test)'; $p = $null }
  elseif ($mb -gt $LimitMB) { Stop-Atas $p "ATAS private $mb MB > limit $LimitMB MB"; $p = $null }
  elseif ($inHalt -and $startCt -lt $ct.Date.AddHours(16)) { Stop-Atas $p "daily CME-halt restart ($mb MB)"; $p = $null }
}
$tries = 1
if (-not $p) { Log 'start ATAS'; Start-Process $exe; Start-Sleep -Seconds 20; $tries = 18 }
try { Connect-Atas $tries } catch { Log "Connect click failed: $($_.Exception.Message)" }
