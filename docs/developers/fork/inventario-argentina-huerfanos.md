# Inventario: Argentina y los clubes sin competición (explicado)

Qué significa cada bloque de la auditoría que saca `probe_arg2.py`, qué es cada fila y qué se
hizo con ella. La foto es de antes de los arreglos del 4-5 de noviembre; al lado va el estado de
hoy.

## Bloque 1 — «competitions whose code or name mentions ARGENTINA»

Lista las filas de `Competition.bin` cuyo **código interno** (28 B desde `+0x08`) o **nombre de
menú** (16 B desde `+0x14`) contiene "ARGENT". El nombre sale truncado a 16 B — de ahí los
`_LEAGUE`, `_CUP`, `PER_CUP`: son trozos de nombres más largos guardados así en la tabla, no un
error de la herramienta.

| cid | código | región | conf | qué es |
|---|---|---|---|---|
| 22 | `ARGENTINA_D1_LEAGUE` | 17 | 4 | **Primera División**: la liga de Boca, River… |
| 49 | `ARGENTINA_D1_CUP` | 17 | 4 | **Copa Argentina**: la copa nacional |
| 79 | `ARGENTINA_SUPER_CUP` | 17 | 4 | **Supercopa Argentina**: campeón de liga vs campeón de copa |

- `region 17` es la región de fábrica que traía la fila; el mundo usa la **29** para Argentina.
- `conf 4` = CONMEBOL.

**Estado hoy**: la D1 (cid 22) estaba en las tablas pero **sin línea en el world file**, así que no
salía en Select Team. Se le puso línea propia (`reg 30`, slot 245, tier 1, 26 clubes). La copa
(cid 49) y la supercopa (cid 79) siguen como estaban: son competiciones de fábrica que el mundo
usa a través de sus `ccup`/copas.

## Bloque 2 — «regulations of Argentina's competitions»

Para esos tres cid, las filas de `CompetitionRegulation.bin` (2352 B cada una). Formato:
`reg | cid | type | teams | nombre`.

| reg | cid | type | equipos | nombre | qué es |
|---|---|---|---|---|---|
| 30 | 22 | 4 (liga) | 30 al leer, **26 hoy** | Liga Profesional de Fútbol | la primera división |
| 59 | 49 | 3 (eliminatoria) | 30 | Copa Argentina AXION | la copa nacional |
| 92 | 79 | 3 (eliminatoria) | 2 | Supercopa Argentina | la supercopa (2 clubes) |

- `type`: **4** liga · **3** eliminatoria · **2** grupos · **9** liga con split.
- `teams` son 6 bits (`+0x0B`): máximo **63**. La reg 30 declaraba 30 pero solo tenía **26
  entradas**: se bajó a 26 para que cuadre. La copa tiene 30 entradas y la supercopa 2.
- El nombre de la regulación es el que se ve en las fichas; el del menú de copas sale del cid (y
  ahí está el pendiente del byte bajo, ver `regulaciones-en-memoria.md`).

## Bloque 3 — «clubs in no competition at all: 178»

Equipos de `Team.bin` que **no tienen ninguna fila en `CompetitionEntry.bin`**: no juegan liga ni
copa. El juego los coloca en los grupos «Otros» por el nibble de `+0x4f`. Se agrupan por familias:

| familia | ids | qué es | qué se hizo |
|---|---|---|---|
| **ML Default** (3) | 140, 2469, 2696 | equipos plantilla de los modos de Master League (Europe/Latinamerica/Asia). No son clubes reales | se dejan |
| **Classics de fábrica** (10) | 900–909 | los equipos clásicos del juego (Rainmakers, Wildcats…) | se dejan; su grupo es el nibble 1 |
| **CLASSICS 01–24** (24) | 72203–72226 | los clásicos **nuestros**, creados para el modo Classic | se dejan; nibble 1 |
| **The Old Boys / World Selection** | 4971, 5129 | equipos conmemorativos del juego | se dejan |
| **Liga Pro OFC 13–24** (12) | 71622–71633 | relleno de la liga de Oceanía que nunca llegó a usarse | se les dio grupo **3** (Asia-Oceanía) |
| **USL Championship** (10) | 73703–73712 | clubes reales de la USL (Sacramento, Indy Eleven…) que no entraron en su liga | se les dio grupo **6** (Latinoamérica/Concacaf) |
| **Generic League 01/43** (4) | 73713, 73714, 73745, 73746 | sobrantes de una liga genérica borrada | candidatos a borrar (no los usa nadie) |
| **Other Clubs (Africa) Club 26** | 73771 | relleno del grupo de África | se le dio grupo **7** |
| **Copa Argentina Club 02–48** (47) | 73850–73896 | relleno de la Copa Argentina: son los clubes que el cuadro usa cuando no hay suficientes reales | se dejan: la copa los necesita |

### El `c40=` de esa salida no es el país

La herramienta imprimía el byte `+0x40` del registro de equipo y lo etiquetaba `c40`. **No es el
país**: el país son **9 bits desde el bit 562** (byte `0x46` bit 2). Aquel `c40` no significa nada
para el país y llevó a una conclusión falsa en su momento (Fiorentina "argentina"). El país de
verdad se lee con `bits(rec, 562, 9)`, y en este mundo sus valores eran **ids de bandera**, no
filas de `Country.bin` (ver `paises-id-bandera.md`).

## Qué queda de esta lista

- **Hecho**: D1 listada (slot 245, 26 clubes); los tres grupos «Otros» (OFC, USL, África) con su
  nibble; los ids de país de todo el mundo remapeados.
- **Pendiente y decidible**: los 4 `Generic League` sobrantes (borrar), y si la Copa Argentina
  quiere 30 reales en vez de 47 rellenos.
- **No se toca**: ML Default, Classics, Old Boys, World Selection, relleno de la copa.
