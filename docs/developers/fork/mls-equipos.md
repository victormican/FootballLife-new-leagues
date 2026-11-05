# MLS: los 10 clubes que faltaban y el paso al slot (2026-11-05)

## Lo que había

La MLS **no está listada** en el mundo (no hay línea `league` para ella). Su competición de
fábrica sigue en las tablas:

| cid | código | regulaciones | equipos | entradas |
|---|---|---|---|---|
| 40 | `US_D1_LEAGUE` | reg 51 `type 5` "MLS", reg 166 y 167 `type 4` "MLS First/Second Round" | 24 | **20** |

Los 20 clubes que había eran los de siempre (Chicago, Columbus, FC Dallas, Galaxy, Montréal,
New England, New York RB, Portland, San Jose, Seattle, Kansas, Vancouver, NYC, Orlando, Atlanta,
Cincinnati, Miami, Nashville, Austin, LAFC).

## Los 10 que faltaban (creados)

Del release NewLife 1.6b4, la MLS tiene 30 clubes; comparando **por id** faltaban 10. Se han
creado como clubes nuevos (clon de plantilla, 22 jugadores cada uno) con
`tools/fill_group.py --reg 250 --to 58` y se han renombrado:

| id | club | país |
|---|---|---|
| 74287 | Charlotte FC | EE. UU. |
| 74288 | Colorado Rapids | EE. UU. |
| 74289 | D.C. United | EE. UU. |
| 74290 | Houston Dynamo FC | EE. UU. |
| 74291 | Minnesota United FC | EE. UU. |
| 74292 | Philadelphia Union | EE. UU. |
| 74293 | Real Salt Lake | EE. UU. |
| 74294 | San Diego FC | EE. UU. |
| 74295 | St. Louis City SC | EE. UU. |
| 74296 | Toronto FC | Canadá |

**Se quedan en "Otros Concacaf"** (cid 221, regulación 250), que pasa de 48 a **58 entradas**.
Los 220 jugadores nuevos salen de los 24.459 huecos que había.

## El paso al slot de la MLS (investigado y preparado)

`cid 40` ya tiene **30 entradas** (las 20 de antes + los 10 nuevos) y sus tres regulaciones
(51, 166, 167) se han subido de 24 a **30 equipos**. Eso deja la competición lista en datos.

Lo que falta para que salga en Select Team y se juegue es **listarla**, y ahí está el problema:

```
league 51 cid=40 region=81 country=124 conf=6 slot=<libre> tier=1 clubs=30 legs=2 name=Major League Soccer
```

- **Formato**: la MLS es `type 5` con dos rondas (reg 166/167) y conferencias; **no es un round
  robin de 30**. Una línea normal con `clubs=30 legs=2` serían 58 jornadas y el calendario grande
  tiene 38: `fl26swiss` la rechazaría o la dejaría sin fechas.
- **Fechas**: no hay `dates` para ella en el mundo (la MLS de fábrica no está). Haría falta su
  calendario propio (el de la MLS original) o un `rcal` a mano.
- **Conferencias**: si el motor espera las dos rondas, hay que decidir si se listan las tres
  regulaciones o solo la maestra.

Por eso **no la he listado**: los datos están preparados y el paso es reversible, pero poner una
línea normal la dejaría sin partidos. El camino correcto es darle su calendario y su formato de
conferencias, y eso es un trabajo aparte (el siguiente paso natural).

## Estado

`check_world`: 0 errores (58 entradas en Concacaf, 30 en MLS, 30 equipos en las tres
regulaciones). Copias: las de `fill_group` y `Team.bin.before-codes` si se tocaron los códigos.
