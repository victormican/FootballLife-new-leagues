# Automatizar la interacción con el juego (2026-11-06)

El juego corre **elevado**, así que un proceso normal no puede mandarle teclas (UIPI). Lo que
funciona, comprobado:

1. **Capturas**: `System.Drawing` + `CopyFromScreen` (el juego está en ventana, no exclusivo).
2. **Teclas**: un PowerShell **elevado** (`Start-Process -Verb RunAs`) con `keybd_event` y el
   **scancode** correcto (`enter` = VK 0x0D, scan 0x1C), y `SetForegroundWindow` sobre el hwnd.
3. El hwnd se saca con `Get-Process FL_2026 | MainWindowHandle`; **`FindWindow` por título
   devolvía 0** aunque el título fuera "SP Football Life 2026" (usar el hwnd del proceso).

`tools/send_keys.ps1` manda teclas: `powershell -Verb RunAs -File send_keys.ps1 <hwnd> enter down ...`

## Camino hasta el fallo

```
título (clic + Enter) -> menú -> Jugar (Enter) -> bajar 6 -> Copa (Enter) -> Nuevo (Enter)
```

Ahí se cierra. El volcado (LocalDumps) da:

```
EXCEPTION_ACCESS_VIOLATION 0x1403fef5f  memcpy(dst=0xb70010, src=0x00000d70, 0x20)
```

El `src=0xd70` es un puntero basura: la lista de Copa construye una fila por competición y
copia datos de su **slot**.

## Causa

`fl26comptab` da a las copas del mundo una **fila oculta en el slot 123** ("none"). De las 64
primeras copas, **62 están en 123 o sin fila**. El slot 123 no tiene lista de clubes ni sorteo:
el modo Copa lee de ahí y revienta.

Las ligas sí reciben slots reales (la tabla `APPEND` del módulo). Las copas no.

## Siguiente

Dar a las filas de las copas un **slot real**, compartido por forma (las copas del mismo tamaño
pueden compartir slot; el dato ya comparte 24 slots entre competiciones), en vez de 123.
Es un cambio en `fl26comptab.lua` (asignación de slots), no en los datos.
