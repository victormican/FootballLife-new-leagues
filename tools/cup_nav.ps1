param([string]$hwndStr)
$log = "C:\Users\viarm\AppData\Local\Temp\opencode\nav.log"
function L($m) { Add-Content -Path $log -Value ("{0:HH:mm:ss} {1}" -f (Get-Date), $m) }
Set-Content -Path $log -Value "start"
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class N {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint dx, uint dy, uint d, UIntPtr e);
  [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr e);
  public struct RECT { public int L,T,R,B; }
}
"@
$h = [IntPtr]([int64]$hwndStr)
[K]::SetForegroundWindow($h) 2>$null
[N]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 600
function Tap([byte]$vk,[byte]$sc,[uint32]$ex) {
  [N]::keybd_event($vk,$sc,($ex), [UIntPtr]::Zero)
  Start-Sleep -Milliseconds 120
  [N]::keybd_event($vk,$sc,($ex -bor 2), [UIntPtr]::Zero)
  Start-Sleep -Milliseconds 450
}
$r = New-Object N+RECT
[N]::GetWindowRect($h, [ref]$r) | Out-Null
$cx = [int](($r.L+$r.R)/2); $cy=[int](($r.T+$r.B)/2)
[N]::SetCursorPos($cx,$cy) | Out-Null
Start-Sleep -Milliseconds 200
[N]::mouse_event(0x0002,0,0,0,[UIntPtr]::Zero)
Start-Sleep -Milliseconds 80
[N]::mouse_event(0x0004,0,0,0,[UIntPtr]::Zero)
[N]::SetCursorPos(20,900) | Out-Null
L "click title"
Start-Sleep -Milliseconds 800
Tap 0x0D 0x1C 0
L "enter title"
Start-Sleep -Seconds 30
Tap 0x0D 0x1C 0
L "enter jugar"
Start-Sleep -Seconds 2
for ($i=0; $i -lt 6; $i++) { Tap 0x28 0x50 1; L "down $i" }
Start-Sleep -Milliseconds 500
Tap 0x0D 0x1C 0
L "enter copa"
Start-Sleep -Seconds 6
Tap 0x0D 0x1C 0
L "enter nuevo"
L "done"
