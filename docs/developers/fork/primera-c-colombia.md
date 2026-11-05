# Primera C Colombia (2026-11-05)

## Creada

| | |
|---|---|
| competición | **cid 366** (`FL_COL_D3`) |
| regulación | **433** (type 4, liga) |
| slot | **246** (el primero libre por encima de las 123 del juego) |
| región / país / confederación | 38 / 133 (Colombia) / 4 (CONMEBOL) |
| clubes | **87** |
| nombre | Primera C Colombia |

Se hizo con `add_league_generic.py` (competición + regulación + línea) y
`fill_group.py --reg 433 --to 87` (los clubes, con plantilla clonada de 22 jugadores: **1.914
jugadores** nuevos).

## Los nombres

Salen del release **NewLife 1.6b4**, liga **"Colombian Third Division"**, que trae **87 clubes**
reales. Se han puesto en orden alfabético:

- los **30 primeros** (el tamaño de la Primera C de Wikipedia que pediste),
- y **el resto hasta 87**, que es lo que da el release y lo que cabe de sobra en los límites
  (equipos 3.308 / 4.800, jugadores 101.280 / 123.825).

Todos con país 133 y sus tres letras.

## Escudos: no hay fuente

- El catálogo de **footylogos de Colombia** (`footylogos_colombia.json`) solo tiene **25 clubes**,
  y son de Primera A.
- El **release no trae** `crests/` para estos clubes (`rel.crest()` devuelve vacío para los 30
  primeros).
- **Wikimedia Commons** (`fuentes.buscar_commons`) devuelve 0 resultados para ellos.

Así que, como dijiste, quedan **los nombres**. Si aparece una fuente de escudos de la Primera C
colombiana, `fetch_world_crests.py` los mete en un minuto.

## Aviso de formato

87 clubes a dos vueltas son **172 jornadas**: el calendario grande tiene 38 (46 con split). La
liga se verá y tendrá sus clubes, pero **no se jugará**: es una lista, como las otras divisiones
bajas del mundo (Federal A con 38×2, Segunda de Bolivia con 48×2). Para que juegue habría que
partirla en grupos o bajar el número.

## Otras competiciones colombianas que ya había

- `Colombian Second Division` (cid 150, reg 112, 16 clubes, slot 85).
- `Copa Colombia` (cid 92, reg 378, 48 clubes, oculta).
- `Copa Especial Colombia` (cid 65, reg 376, 30 clubes, oculta).

`check_world`: 0 errores (151 ligas, 134 slots).
