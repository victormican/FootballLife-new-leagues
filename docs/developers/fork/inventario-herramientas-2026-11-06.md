# Inventario de herramientas (2026-11-06)

Qué hay en el repo, para qué sirve cada bloque y qué se necesita en una instalación limpia. Las
herramientas de desarrollo no van al juego; solo los módulos, el world file y las dos DLL.

## 1. Construir el mundo (Python, `tools/`)

| herramienta | qué hace |
|---|---|
| `pesdb.py` | Lee y escribe las tablas WESYS (`Competition`, `Entry`, `Regulation`, `Team`...). Ya lee el cid a 16 bits (`+0x08 \| +0x0B<<8`) y la regulación a 16 bits (`+0x02`). |
| `leaguebuilder.py` | Convierte un plan JSON en mundo: ligas, copas, entradas, regulaciones, calendario. Aquí viven `cwc_champs` (nuestro) y `assoc_rank`/`place_rank` (ranking UEFA del upstream). |
| `mkworld.py` / `build_leagues.py` | Empaqueta el mundo (tablas + world file + módulos). |
| `add_world_cups.py`, `mk_conf_cups.py`, `dup_cups*.py`, `add_twin_leagues.py` | Copas continentales, copias de copa, ligas gemelas. |
| `mkslots.py`, `mkregs.py`, `cid16_migrate.py`, `move_cids.py` | Slots, regulaciones, migración de cids a 16 bits, bytes bajos libres. |
| `newlife.py`, `playeredit.py`, `lbfaces.py`, `mkcrests.py`, `mkflags.py`, `mkemblems.py`, `mkkits.py`, `kitpics.py` | NewLife (clubs/jugadores), caras, escudos, banderas, emblemas, equipaciones. |
| `countries.py`, `crestmatch.py`, `fetch_world_crests.py` | Países, emparejar escudos, descargarlos. |
| **`check_world.py`** | Validador: equipos, jugadores, asignaciones, competiciones, regulaciones y entradas. **Debe dar 0 errores / 0 avisos.** |
| **`fix_cid2_entries.py`** | Quita el equipo 0 y la plaza duplicada de la copa 2 (defecto de los datapacks). |

## 2. Ver el juego por dentro (solo lectura)

| herramienta | qué hace |
|---|---|
| **`livereg.py`** | Bloque de edición vivo: dueño, bloque, regulaciones, clubs por handle. |
| `livedump.py` | Volcado del bloque vivo (equipos, jugadores, slots). |
| **`fl26dis.py`** | Desensambla `.text` (39 MB) y deja un SQLite: 158.648 funciones, 906.162 llamadas, 314.061 referencias, 55.381 cadenas. |
| `callindex.py`, `impscan.py`, `boundscan.py`, `hdrverify.py` | Índices de llamadas, imports, límites y cabeceras del exe. |
| `checkratings.py`, `calaudit.py`, `buildcheck.py` | Comprobaciones de datos del mundo. |

## 3. Automatizar el juego (PowerShell)

| herramienta | qué hace |
|---|---|
| `send_keys.ps1`, `press_key.ps1` | Teclas al juego (ventana enfocada, `keybd_event` + `AttachThreadInput`). |
| `liga_probe.ps1`, `scroll_shot.ps1` | Ir a `Jugar > Liga > Nuevo` y capturar la lista con scroll. |
| `select_team_retry.ps1` | Repetir el flujo de Select Team para el fallo del primer `count`. |
| `cup_nav.ps1` | Navegar el menú de copas. |

(En `%TEMP%\opencode` quedaron además `driver.ps1` —teclas por cola, sin robar el foco en cada
llamada— y los monitores de Frida `frida_arm.py`, `frida_range.py`, `frida_scan.py`.)

## 4. Módulos que van al juego (`sider/experimental/*.lua`)

**Núcleo del mundo**
- `fl26comptab.lua` — filas de parámetros para nuestras ligas (slot y nombre).
- `fl26slots750.lua` / `fl26slots250.lua` / `fl26slots128.lua` — plazas.
- `fl26regs1200.lua`, `fl26regs600.lua`, `fl26reg64.lua`, `fl26reg128.lua` — regulaciones y regiones.
- `fl26cid16.lua` — cids ≥ 256: `pack`, `reg`, `build`, `map` encendidos; **`cid` y `list` apagados**.
- `fl26clubs.lua` + `fl26clubs.dll` — sirve la lista de clubs de cada liga desde su regulación (slots `SERVED`, `own_remap`/`pick` de 0.3.0).
- `fl26swiss.lua` + `fl26swiss.dll` — copas de grupos y fases suizas.
- `fl26squadlist.lua` — **nuevo de 0.3.0**: lista de clubs de la liga en Select Team / Team Info.

**Menús y nombres**
- `fl26slotnames.lua`, `fl26regions.lua`, `fl26regnames.lua`, `fl26catlist.lua`.
- `fl26cupgrow.lua`, `fl26cupfree.lua` — menú de copas (más de 13 y sin el cierre `0x3fd2b2`).

**Guardas y extras**
- `fl26guards.lua`, `fl26lateguards.lua`, `fl26boardguard.lua`, `fl26ctlguard.lua`, `fl26kitguard.lua`, `fl26resultsguard.lua`, `fl26superguard.lua`.
- `fl26seasonend.lua`, `fl26augseason.lua`, `fl26regen.lua`, `fl26playercap.lua`, `fl26rank.lua`, `fl26deeprank.lua`, `fl26edit.lua`, `fl26editlist.lua`, `fl26chain.lua`, `fl26walk.lua`, `fl26compcache.lua`, `fl26hdr192.lua`, `fl26hdr255.lua`, `fl26appcap.lua`, `fl26caps.lua`, `fl26joindll.lua`.

**Sondas (no van en una instalación limpia)**: `fl26diag.lua`, `fl26strprobe.lua`, `fl26embprobe.lua`, `fl26deep4.lua`.

## 5. DLL nativas (`tools/native/`)

| fichero | qué hace |
|---|---|
| `fl26clubs.c` / `fl26clubs.dll` | Hooks `count`/`get` del motor; responde la lista de clubs de los slots servidos. `MAX_CFG 768`, `MAX_CLUBS 96`. |
| `fl26swiss.c` / `fl26swiss.dll` | Fases de grupos/suizas y calendario; log de 1 MB con contador de líneas perdidas (upstream). |
| `fl26edit.c`, `fl26swiss.lib` | Soporte de edición y enlace. |

Compilar (no está en PATH): `C:\Users\viarm\test-carpeta\tools\zig-x86_64-windows-0.16.0\zig.exe cc -shared -target x86_64-windows-gnu -O2 -s`.

## 6. Documentación viva (`docs/developers/fork/`)

- `exe-mapa-2026-11-06.md` — mapa del ejecutable y cómo usar el SQLite.
- `instalacion-limpia-2026-11-06.md` — este paso a paso.
- `lista-ligas-2026-11-06.md` — las 154 ligas con sus equipos y colisiones de byte.
- `informacion-de-la-liga-censo-2026-11-06.md`, `p02-cid-true-ab-2026-11-06.md` — el fallo de las listas.
- `upstream-0.3.0-2026-11-06.md` — qué trajo el merge y qué aporta.
- `aviso-cid2-plaza32-2026-11-06.md` — el aviso resuelto.
- `revision-completa-y-pendientes-2026-11-06.md` — el plan P0..P3.

## 7. Qué se copia a una instalación limpia

**Sí:** `sider/experimental/fl26*.lua` (menos las sondas), `fl26clubs.dll`, `fl26swiss.dll`,
`modules/fl26world.txt`, `livecpk/_FL26MyWorld`, las líneas de `sider.ini` del paso 5 de la guía.

**No:** `tools/`, `docs/`, `patches/`, los scripts sueltos de la raíz y las sondas.
