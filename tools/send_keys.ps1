param([string]$hwndStr)
$log = "C:\Users\viarm\AppData\Local\Temp\opencode\keys.log"
function L($m) { Add-Content -Path $log -Value ("{0:HH:mm:ss.fff} {1}" -f (Get-Date), $m) }
Set-Content -Path $log -Value "start"
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class F3 {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr e);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint dx, uint dy, uint d, UIntPtr e);
  public struct RECT { public int L,T,R,B; }
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
}
"@
$h = [IntPtr]([int64]$hwndStr)
[F3]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 500
L ("fg=" + [F3]::GetForegroundWindow())
$keys = $args
foreach ($k in $keys) {
  switch ($k) {
    "enter" { [F3]::keybd_event(0x0D, 0x1C, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 130; [F3]::keybd_event(0x0D, 0x1C, 2, [UIntPtr]::Zero) }
    "space" { [F3]::keybd_event(0x20, 0x39, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 130; [F3]::keybd_event(0x20, 0x39, 2, [UIntPtr]::Zero) }
    "down"  { [F3]::keybd_event(0x28, 0x50, 1, [UIntPtr]::Zero); Start-Sleep -Milliseconds 130; [F3]::keybd_event(0x28, 0x50, 3, [UIntPtr]::Zero) }
    "up"    { [F3]::keybd_event(0x26, 0x48, 1, [UIntPtr]::Zero); Start-Sleep -Milliseconds 130; [F3]::keybd_event(0x26, 0x48, 3, [UIntPtr]::Zero) }
    "right" { [F3]::keybd_event(0x27, 0x4D, 1, [UIntPtr]::Zero); Start-Sleep -Milliseconds 130; [F3]::keybd_event(0x27, 0x4D, 3, [UIntPtr]::Zero) }
    "left"  { [F3]::keybd_event(0x25, 0x4B, 1, [UIntPtr]::Zero); Start-Sleep -Milliseconds 130; [F3]::keybd_event(0x25, 0x4B, 3, [UIntPtr]::Zero) }
    "esc"   { [F3]::keybd_event(0x1B, 0x01, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 130; [F3]::keybd_event(0x1B, 0x01, 2, [UIntPtr]::Zero) }
  }
  L "key $k"
  Start-Sleep -Milliseconds 600
}
L "done"
