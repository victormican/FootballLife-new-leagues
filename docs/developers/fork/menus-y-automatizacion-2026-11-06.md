# Menus, automatizacion y hallazgos (2026-11-06)

## Automatizacion

- **Teclas**: PowerShell **elevado** (`-Verb RunAs`) con `keybd_event` y scancode
  (enter 0x0D/0x1C, flechas con flag extendido 1/3). Desde un proceso normal Windows las
  bloquea (UIPI: el juego corre elevado).
- **Foco**: `AttachThreadInput` + `SetForegroundWindow` y un clic en la **barra de titulo**
  (no en el contenido) para que el juego quede delante sin activar nada.
- **Capturas**: `System.Drawing` + `CopyFromScreen` (el juego va en ventana).
- Script: `tools/send_keys.ps1` (`<hwnd> enter down up esc f10 ...`). El hwnd se saca con
  `Get-Process FL_2026 | MainWindowHandle`; `FindWindow` por titulo devolvia 0.

## Flujo de los menus

```
titulo (INGRESAR) -> menu principal (iconos)
  Jugar (bola) -> Partido local | Partido local (EURO) | Cooperativo |
                  Partido de seleccion | Versus | Liga | Copa
  Liga Master (campo)
  Ser una Leyenda (jugador)
  Controles de audio (sliders)
  Configuracion (engranaje)
```

- **Partido local**: elegir mando (Local/Visitante) -> Datos del usuario -> OK -> Cargar datos
  del equipo local -> seleccion de equipo.
- **Copa**: Continuar (si hay partida) | Nuevo | Cargar. **Nuevo** abre "Seleccionar
  competencia" con las reglas a la derecha (tamano del sorteo, fase de grupos, formato...).
- **Liga**: la misma pantalla con la lista de ligas.

El menu recuerda el ultimo icono: al volver del titulo hay que subir 6 veces para caer en la
bola (Jugar), si no se entra en Configuracion o Audio.

## El defecto

En **Copa > Nuevo**, la primera vez la lista solo trae las 8 del juego (UEFA EURO,
Libertadores, AFC Champions League, Africa Cup, FIFA World Cup...). Al salir al menu y volver a
entrar, salen **todas** (286). Es el orden de construccion: `cupsel_handler` anade los cids al
vector despues de que la pantalla se construya; al segundo acceso el vector ya los tiene.

## Copa: lo arreglado y lo que queda

| fallo | estado |
|---|---|
| filas de copa en slot 123 -> `memcpy(src=0xd70)` al abrir | **arreglado** (slot 22) |
| cierre al salir `0x161efa600` (cid no encontrado -> competicion 1) | la escritura del cid esta en el fuente; build 434.176 probado, sigue el otro cierre |
| cierre `0x3fd2b2` al liberar el buffer de la lista | **abierto**; probado pool 2 -> pool 0 y sin cupgrow, sigue |
| lista vacia en la primera entrada | **abierto** (orden del vector) |

Se volvio al DLL desplegado (378.880 B) y a `cupgrow`/`compcache` activos para dejar el juego
como estaba.

## Copas regionales

14 creadas (CHAN, UNAF, WAFU B, UNIFFAC, CECAFA, COSAFA, ASEAN Club, CAFA Club, WAFF Club,
EAFF Club, ASEAN Championship, CAFA Nations, WAFF Championship, EAFF E-1). `check_world`: 286
ccup, 0 errores.
