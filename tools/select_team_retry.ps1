param([string]$hwndStr, [int]$scroll = 0, [string]$shot = "")
# Reintento del flujo de Select Team: menu principal -> Jugar -> Liga -> Nuevo -> lista.
# El operador mira la captura: si la lista trae un solo equipo (el fallo de la primera
# lectura), se vuelve al menu y se repite; a la segunda entrada sale completa.
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class ST {
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
[ST]::SetForegroundWindow($h) | Out-Null
$fg = [ST]::GetForegroundWindow()
$t1 = [ST]::GetWindowThreadProcessId($fg, [IntPtr]::Zero)
$t2 = [ST]::GetCurrentThreadId()
[ST]::AttachThreadInput($t2, $t1, $true) | Out-Null
[ST]::SetForegroundWindow($h) | Out-Null
[ST]::AttachThreadInput($t2, $t1, $false) | Out-Null
Start-Sleep -Milliseconds 500
$r = New-Object ST+RECT
[ST]::GetWindowRect($h, [ref]$r) | Out-Null
[ST]::SetCursorPos($r.L + 300, $r.T + 20) | Out-Null
Start-Sleep -Milliseconds 100
[ST]::mouse_event(0x0002,0,0,0,[UIntPtr]::Zero); Start-Sleep -Milliseconds 60
[ST]::mouse_event(0x0004,0,0,0,[UIntPtr]::Zero)
[ST]::SetCursorPos(20, 900) | Out-Null
Start-Sleep -Milliseconds 400

function Tap([byte]$vk,[byte]$sc,[uint32]$ex) {
  [ST]::keybd_event($vk,$sc,$ex,[UIntPtr]::Zero); Start-Sleep -Milliseconds 110
  [ST]::keybd_event($vk,$sc,($ex -bor 2),[UIntPtr]::Zero); Start-Sleep -Milliseconds 380
}
# volver al menu principal (por si estamos en un submenu)
Tap 0x1B 0x01 0; Tap 0x1B 0x01 0; Tap 0x1B 0x01 0
# Jugar (bola): subir 6, entrar
1..6 | ForEach-Object { Tap 0x26 0x48 1 }
Tap 0x0D 0x1C 0
# Liga: 5 abajo desde Partido local
1..5 | ForEach-Object { Tap 0x28 0x50 1 }
Tap 0x0D 0x1C 0
Start-Sleep -Seconds 2
# Nuevo
Tap 0x0D 0x1C 0
Start-Sleep -Seconds 6
# desplazamiento opcional por la lista de competiciones
1..$scroll | ForEach-Object { Tap 0x28 0x50 1 }
if ($shot) {
  Add-Type -AssemblyName System.Windows.Forms,System.Drawing
  $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
  $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)
  $bmp.Save($shot, [System.Drawing.Imaging.ImageFormat]::Png)
  $g.Dispose(); $bmp.Dispose()
}
