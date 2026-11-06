param([string]$hwndStr, [int]$vk = 0x79, [int]$scan = 0x44)
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class K1 {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, IntPtr p);
  [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint a, uint b, bool f);
  [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
  [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr e);
}
"@
$h = [IntPtr]([int64]$hwndStr)
[K1]::SetForegroundWindow($h) | Out-Null
$fg = [K1]::GetForegroundWindow()
$t1 = [K1]::GetWindowThreadProcessId($fg, [IntPtr]::Zero)
$t2 = [K1]::GetCurrentThreadId()
[K1]::AttachThreadInput($t2, $t1, $true) | Out-Null
[K1]::SetForegroundWindow($h) | Out-Null
[K1]::AttachThreadInput($t2, $t1, $false) | Out-Null
Start-Sleep -Milliseconds 400
[K1]::keybd_event([byte]$vk, [byte]$scan, 0, [UIntPtr]::Zero)
Start-Sleep -Milliseconds 150
[K1]::keybd_event([byte]$vk, [byte]$scan, 2, [UIntPtr]::Zero)
Start-Sleep -Milliseconds 1200
