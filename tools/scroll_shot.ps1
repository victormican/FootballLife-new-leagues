param([string]$hwndStr, [int]$steps = 20, [string]$shot = "")
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class SC {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, IntPtr p);
  [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint a, uint b, bool f);
  [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint dx, uint dy, uint d, UIntPtr e);
  [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr e);
  public struct RECT { public int L,T,R,B; }
}
"@
$h = [IntPtr]([int64]$hwndStr)
[SC]::SetForegroundWindow($h) | Out-Null
$fg = [SC]::GetForegroundWindow()
$t1 = [SC]::GetWindowThreadProcessId($fg, [IntPtr]::Zero)
$t2 = [SC]::GetCurrentThreadId()
[SC]::AttachThreadInput($t2, $t1, $true) | Out-Null
[SC]::SetForegroundWindow($h) | Out-Null
[SC]::AttachThreadInput($t2, $t1, $false) | Out-Null
Start-Sleep -Milliseconds 400
$r = New-Object SC+RECT
[SC]::GetWindowRect($h, [ref]$r) | Out-Null
[SC]::SetCursorPos($r.L + 300, $r.T + 20) | Out-Null
Start-Sleep -Milliseconds 100
[SC]::mouse_event(0x0002,0,0,0,[UIntPtr]::Zero); Start-Sleep -Milliseconds 60
[SC]::mouse_event(0x0004,0,0,0,[UIntPtr]::Zero)
[SC]::SetCursorPos(20, 900) | Out-Null
Start-Sleep -Milliseconds 400
function Tap([byte]$vk,[byte]$sc,[uint32]$ex) {
  [SC]::keybd_event($vk,$sc,$ex,[UIntPtr]::Zero); Start-Sleep -Milliseconds 120
  [SC]::keybd_event($vk,$sc,($ex -bor 2),[UIntPtr]::Zero); Start-Sleep -Milliseconds 620
}
1..$steps | ForEach-Object { Tap 0x28 0x50 1 }
Start-Sleep -Milliseconds 500
if ($shot) {
  Add-Type -AssemblyName System.Windows.Forms,System.Drawing
  $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
  $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)
  $bmp.Save($shot, [System.Drawing.Imaging.ImageFormat]::Png)
  $g.Dispose(); $bmp.Dispose()
}
