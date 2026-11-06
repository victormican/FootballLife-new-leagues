# Pendientes (condensado, 2026-11-06 noche)

Estado del árbol: `cwc-next`, últimos commits `b202d8d` (menús), `5b1d51e` (id de copa ≤255),
`6f52445` (resolver de la copa). Vault al día (Historial, Estado actual).

## 1. Copa Test en juego (en curso)

- Desplegado en `D:\SP Football Life 2026 - copia`: mundo `_FL26CupsTest` con
  `ccup 200 ko=200 groups=0 cid=50 like=23 entry=17:1..20:4`, 86 módulos (los 40 fl26 + DLL) y
  `fl26zcupdates` que pone el byte de fechas 200 a `0x10`.
- **Reproducir**: entrar en Kick Off > Copa, elegir equipo y ver si muere.
- **Captura**: la traza de `ExitProcess` se escribe en
  `C:\Users\viarm\AppData\Local\Temp\opencode\exit-trace.txt` (sobrevive al cierre; el agente
  duerme el hilo 1 s para que se escriba).

## 2. Diagnóstico del cierre (lo que falta)

- Con el backtrace del `EXIT`, identificar la función que apaga el juego tras elegir equipo.
  Sospechosos: el generador de calendario (no encuentra día de copa) o el sorteo (se queda sin
  campo).
- Si es el calendario: revisar `dates 200 like=23`, el byte `0x10` y `--cup-keys 200` del patchset.
- Si es el sorteo: `0x1415485c0` (`id, lista, flag`) y el llenado desde las entradas.

## 3. Ghidra

- Import de `FL_2026.exe` (438 MB) en marcha con `REA_GHIDRA_STARTUP_TIMEOUT_MS=10800000` y
  snapshot `...\fl26-ghidra.gpr`. Al terminar, descompilar en el mismo snapshot:
  `0x140e43450` (enter común), `0x140b1c990` (init copa), `0x140b3be30` (liga),
  `0x1415485c0` (sorteo), `0x150af30` (phkind), `0x140c18dd0` (EditLgCpMain).

## 4. Menú Editar

- Los ítems **no** están en los `.bin` de `common/menu` (son texturas TXP2); se construyen en
  código. Falta el init de cada `MenuEdit*` (los slots propios, no la base `0x00..0x50`).
- `MenuEditLgCpMain` ctor 0x140c18dd0; los demás: nombre 0x14270bed0, detalle 0x1427037b0,
  organizar (`MenuEditLeagueOrganizeMain`).

## 5. Herramientas / entorno

- **REA MCP**: sigue sin cargarse como herramienta en esta sesión (catálogo viejo). El CLI
  (`rea ...`) funciona y Frida ya tiene su binding. Requiere reinicio de OpenCode para las tools.
- `rea decompile` sobre el exe solo es viable con el plazo subido (env) o con la sección `.trace`
  (38 MB) como `raw-binary`.

## 6. Decisiones abiertas

- Copa definitiva: **reg 200 + cid 131** con la Liga Test (build del mundo) o **clon nativo**
  (cid 36) como atajo jugable.
- Copa en temporada: verificar que la 200 se juega en Master League (el DLL ya la fecha).
- Limpieza: 5 carpetas `_uninstall_modstudio_*` en la raíz del juego (backups de Mod Studio) y los
  `.bak-*` que he ido dejando; decidir si se borran.
- Punto limpio intacto en `G:\Backups\SPFL26-limpia-20261106\Game` (restauración dirigida en ~2 min).

## 7. Repo

- Sin commitear (del usuario, no tocar): `fl26clubs.lua`, `fl26swiss.lua`, `fl26clubs.c/.dll`,
  `fl26swiss.lib`, `pesdb.py` y varios `*.py` sueltos en la raíz.
