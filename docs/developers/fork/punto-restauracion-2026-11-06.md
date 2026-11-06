# Punto de restauración limpio (2026-11-06)

Instalación **sin nada nuestro**: juego base + Sider + los packs que ya traía, después de quitar
todo lo de FL Mod Studio. Es el punto al que volver antes de reconstruir.

## Dónde

| | |
|---|---|
| origen | `D:\SP Football Life 2026 - copia` |
| copia | `G:\Backups\SPFL26-limpia-20261106\Game` |
| listado | `G:\Backups\SPFL26-limpia-20261106\LISTADO.txt` |
| notas | `G:\Backups\SPFL26-limpia-20261106\LEEME.txt` |
| tamaño | 76,5 GB (sin la carpeta `_uninstall_modstudio_*`, que se quedó en D:) |

## Qué se quitó (herramienta `tools/uninstall_modstudio.py`)

- Mundos `livecpk\_FL26MyWorld` y `_FL26MyWorld.building`.
- 40 módulos `fl26*.lua/.dll` + `fl26world.txt` + `fl26regen_faces.bin` + `fl26compcache.log`.
- `SiderAddons\ModStudio` (perfiles y copias).
- `%APPDATA%\FL26ModStudio` (tablas, recetas, packs, caché).
- 32 líneas de `sider.ini` (30 de módulos/`cpk.root` + 2 marcadores), con copia `.bak`.

Todo se **movió** a `D:\SP Football Life 2026 - copia\_uninstall_modstudio_20261106-101151`
(0,45 GB), no se borró. No se metió en el backup.

## Qué queda (lo que se respalda)

- `FL_2026.exe` 26.2.0.3, 458.910.720 B, sha256 `9ee0c30651e5e3c37e3d308fb8224f5fea135cd8e929dee2cddca6e041836281`.
- Sider DLL 7.3.3; `sider.ini` con **17 módulos base** (CommonLib, nesalib, stadiums, scoreboards,
  cinematics, referee, audio, omb, kits, SleeveBadge, Fans-Server, env, camera, matchset, nets,
  movieintro) y **1 cpk.root** (`.\livecpk\FL26 Regen Faces`).
- `livecpk`: `FL26 Regen Faces`, `root`.
- `modules`: MenuServer, ScoreboardServer, SubBoard, WeatherConditions, camera, common, env, kserv,
  lib, matchset, movieintro, nets, stadswitch, tracer.
- `Data` 23,2 GB, `download` 42,2 GB, `dataSP` 0,01 GB.
- Partidas dentro del juego: `KONAMI\eFootball PES 2021 SEASON UPDATE\2026\save`.

## Comprobación hecha

Con el juego arrancado desde esa carpeta: `Sider initialization complete`, **Active modules: 17**
y Select Team con **sus** ligas y equipos (Jupiler con sus clubes, Brasileirão, Liga BetPlay,
MLS, CFA). Las tablas que carga son las del juego (`CompetitionEntry.bin` 15.972 B,
`CompetitionRegulation.bin` 503.328 B).

## Cómo restaurar

1. Cierra juego y Sider.
2. Renombra la carpeta actual y copia `Game\` a `D:\SP Football Life 2026 - copia`.
3. Arranca con `FL 2026 start.exe`.
4. En `sider.log`: `Sider initialization complete` y `Active modules: 17`.

## Nota

`D:\SP Football Life 2026` (la otra carpeta) **no se tocó**: sigue con su mundo de 91 ligas si se
quiere mirar. Para limpiarla igual: `python tools/uninstall_modstudio.py --game "D:\SP Football Life 2026"`.
