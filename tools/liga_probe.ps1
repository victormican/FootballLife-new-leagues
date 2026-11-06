param([string]$hwndStr, [string]$prefix = "liga")
# Jugar -> Liga -> Nuevo, luego capturas: lista inicial y tras varios scrolls.
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class LP {
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
[LP]::SetForegroundWindow($h) | Out-Null
$fg = [LP]::GetForegroundWindow()
$t1 = [LP]::GetWindowThreadProcessId($fg, [IntPtr]::Zero)
$t2 = [LP]::GetCurrentThreadId()
[LP]::AttachThreadInput($t2, $t1, $true) | Out-Null
[LP]::SetForegroundWindow($h) | Out-Null
[LP]::AttachThreadInput($t2, $t1, $false) | Out-Null
Start-Sleep -Milliseconds 500
$r = New-Object LP+RECT
[LP]::GetWindowRect($h, [ref]$r) | Out-Null
[LP]::SetCursorPos($r.L + 300, $r.T + 20) | Out-Null
Start-Sleep -Milliseconds 100
[LP]::mouse_event(0x0002,0,0,0,[UIntPtr]::Zero); Start-Sleep -Milliseconds 60
[LP]::mouse_event(0x0004,0,0,0,[UIntPtr]::Zero)
[LP]::SetCursorPos(20, 900) | Out-Null
Start-Sleep -Milliseconds 400

function Tap([byte]$vk,[byte]$sc,[uint32]$ex) {
  [LP]::keybd_event($vk,$sc,$ex,[UIntPtr]::Zero); Start-Sleep -Milliseconds 140
  [LP]::keybd_event($vk,$sc,($ex -bor 2),[UIntPtr]::Zero); Start-Sleep -Milliseconds 650
}
function Shot([string]$name) {
  Add-Type -AssemblyName System.Windows.Forms,System.Drawing
  $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
  $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)
  $bmp.Save($name, [System.Drawing.Imaging.ImageFormat]::Png)
  $g.Dispose(); $bmp.Dispose()
}
$dir = "C:\Users\viarm\AppData\Local\Temp\opencode\shots"
# menu principal -> Jugar (bola)
1..6 | ForEach-Object { Tap 0x26 0x48 1 }
Tap 0x0D 0x1C 0
Start-Sleep -Milliseconds 800
# Liga (5 abajo desde Partido local)
1..5 | ForEach-Object { Tap 0x28 0x50 1 }
Tap 0x0D 0x1C 0
Start-Sleep -Seconds 2
# Nuevo
Tap 0x0D 0x1C 0
Start-Sleep -Seconds 7
Shot "$dir\$prefix-00.png"
# foco en la lista
Tap 0x0D 0x1C 0
Start-Sleep -Milliseconds 500
$marks = @(8, 16, 24, 32, 40)
foreach ($m in $marks) {
  if ($m -gt 8) { 1..8 | ForEach-Object { Tap 0x28 0x50 1 } }
  else { 1..8 | ForEach-Object { Tap 0x28 0x50 1 } }
  Start-Sleep -Milliseconds 600
  Shot ("$dir\\" + $prefix + "-" + $m.ToString("00") + ".png")
}
