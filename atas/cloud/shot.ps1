# Screenshot of the VM desktop to C:\nexa\shot.png. Run via task NEXA_Shot (Interactive, nexa) so it sees the user session.
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$b = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
$g = [System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen($b.Left, $b.Top, 0, 0, $bmp.Size)
$bmp.Save('C:\nexa\shot.png', [System.Drawing.Imaging.ImageFormat]::Png)
