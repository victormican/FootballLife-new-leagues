# Copa Sudamericana propia (cid 132 / clon cid 5) — estado final (2026-11-12)

## Objetivo

Una copa internacional propia (tipo Sudamericana, 32 clubes, 8 grupos + eliminación) jugable en
Kick Off > Copa. Sin depender de Master League.

## Resultado

- **Se lista directa en el menú** (vía A, cid 132): nombre, 32 equipos, grupos, ida/vuelta, final
  única; pasa por Opciones generales y Seleccionar equipo.
- **No es jugable**: el cid 132 se queda cargando (deadlock del cargador de archivos) y el clon
  (cid 5) crashea por el stack de `fl26swiss` en Kick Off.
- **El clon nativo sí construye su sorteo** (`loader count=8 key=1033`: los 8 grupos de la
  Libertadores), antes de que el stack crashee.

## Vía A: cid nuevo directo (132)

Lo que hay (world `_FL26Sud`, receta `out/recipe-sud.json`):

```
ccup 318 ko=319 groups=8 entry=11:1,29:7,30:7,67:3,168:3,... cid=132 name=Copa Sudamericana
```

Piezas que se necesitaron (y están):

1. `fl26comptab.lua` añade fila de parámetros para **318 (grupos) y 319 (KO)** (copia privada de la
   tabla + subir los 4 contadores; el límite 165/177 queda roto).
2. Tabla de fases `0x1434eecc4` (indexada por **slot**): entrada **slot 84 → reg 318**.
3. `fl26swiss.lua` con `EXPOSE=-1` para listar el cid 132.
4. `fl26cup.dll` encadenado tras el handler de `fl26swiss` (slot de la vtable ocupado): busca la
   reg 318, fecha **318→9** y vigila el cargador de sesión.

Muro: al confirmar el equipo, el hilo principal entra en un busy-wait sobre el contador de la
cola de carga (`_DAT_143747e98 + 0xc0`); dos hilos del juego quedan en `NtReadFile` y el hilo de
Sider espera. Es un **deadlock del lector de archivos CPK + Sider** para una competición nueva.
Forzar el contador a 0 no destraba la pantalla. No es un dato ni un hook simple.

## Vía B: clon nativo (cid 5, la Libertadores)

```powershell
python tools/clone_shipped_cup.py --base <mundo>\common\etc\pesdb --out <mundo> `
  --cid 5 --reg 9 --code FL_SUDAM --name "Copa Sudamericana" --teams 318:1,318:2,...,318:32
```

- Conserva id/slot/fechas/reglas nativos; cambia entradas (nuestras 32) y el nombre de la
  regulación 9.
- `EXPOSE=0` para no duplicar con el cid 132.
- Construye el sorteo (`count=8 key=1033`), pero el **stack de `fl26swiss` crashea en Kick Off**.

## El muro común: fl26swiss en Kick Off

`fl26swiss` corre su calendario/pool de temporada en cada tick del día (`daychk_handler`). En
Kick Off no hay temporada y crashea en varios puntos:

1. `cal_dedupe` recorría el calendario (365 días × 792 ids) sin comprobar que esté comprometido
   → guard `cal_mapped` (añadido).
2. `table_pool_old_slots` llamaba a `SLOTFREE 0x158f870` con slot nulo (`rip 0x14158f86e`,
   `rcx=2`) → guard `span_committed` sobre el pool (añadido).
3. Tras el guard, aún crashea en otro punto del DLL (rip dentro de `fl26swiss.dll`), al cargar el
   sorteo del clon.

Conclusión: **con el stack fl26swiss encendido, Kick Off > Copa crashea para cualquier copa
(nativa incluida)**. El clon se jugó de punta a punta con el stack **apagado** (verificado
2026-11-07); con el stack encendido no pasa del sorteo.

## Lo que queda

- **Para jugar el clon**: apagar los módulos fl26 que tocan calendario/pool en Kick Off
  (`fl26swiss` sobre todo), o aislar su `daychk_handler` para que no corra en Cup mode.
- **Para el cid 132 directo**: destrabar el deadlock del lector CPK/Sider (RE del cargador del
  motor), y después registrar la competición en el plan (fases/draw).
- El análisis completo del exe (`FL26full`) sigue corriendo en Ghidra (proyecto `D:\ghidra_projects`).

## Archivos y commits

- `out/recipe-sud.json`, `tools/clone_shipped_cup.py`, `docs/developers/fork/copa-sudamericana-2026-11-09.md`
- `tools/native/fl26cup.c/.dll` (cadena, find 318, fecha 318→9, gate +0x84), `fl26swiss.c/.dll`
  (guardas `cal_mapped`/`span_committed`), `sider/experimental/fl26comptab.lua`
  (fila KO + fase slot 84), `sider/experimental/fl26swiss.lua` (EXPOSE).
- Commits: `017854b`, `772a2a9`, `cae130c`, `1c5c469`, `961ceda`, `950f6fd`, `68eaff8`, `fd92872`.
