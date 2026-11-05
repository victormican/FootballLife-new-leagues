# Los grupos "Otros" de Select Team (2026-11-05)

Los cinco grupos de Select Team que no son ligas son **competiciones con sus clubes** pero sin
línea en el world file, y el juego decide en qué grupo sale cada club por un **nibble** del
registro de equipo:

```
Team.bin +0x4f, nibble alto:  1 Classic Teams · 2 Other European · 3 Other Asia-Oceania
                              6 Other Latin American (Concacaf entra aquí) · 7 Other Africa
                              0 = fuera de los grupos
```

## Lo que había (medido)

| reg | cid | nombre | clubes | nibble |
|---|---|---|---|---|
| 181 | 165 | Other Clubs (Africa) | 48 | **0 en los 48** |
| 250 | 221 | Otros Concacaf | 48 | **0 en los 48** |
| 256 | 254 | Other Clubs (Asia) | 48 | 3 en 26 · **0 en 22** |
| 364 | 98 | Other European Leagues | 29 | 2 en 17 · **0 en 12** |
| 362 | 95 | Other Latin American Teams | 40 | 6 en 4 · **0 en 36** |

Por eso África y Concacaf salían con el **menú oculto** (ningún club con grupo) y Asia, Europa y
Latinoamérica **medio vacíos**: el juego solo pinta los clubes que llevan el nibble.

## Lo que se hizo (`tools/other_pools.py`)

1. Se pone el nibble de su grupo a los clubes de los cinco contenedores: **166 clubes**.
2. Se **quita** el grupo a los clubes que además juegan una liga listada (**32**): un club en liga
   no puede salir dos veces (HJK Helsinki, Zalgiris, Ferencváros… estaban en Europa y en su liga).
3. Se da grupo a **28 clubes sin competición** que sí pertenecen a uno, por nombre:
   Liga Pro OFC 13-24 → Asia-Oceania (12), USL (10) y Brazil State Pool (3) → Latinoamérica,
   y los tres placeholders africanos → África.

Resultado por grupo:

```
1 Classic Teams        48
2 Other European       29
3 Other Asia-Oceania   60   (48 + 12 OFC)
5 ML Default           48
6 Other Latin American 101  (48 Concacaf + 40 LatAm + 13)
7 Other Africa          51  (48 + 3)
0 fuera                2874 (los que juegan liga listada)
```

Comprobado: **0 clubes** con grupo y a la vez en una liga listada; **0** clubes de contenedor sin
grupo. `check_world`: 0 errores. Copia: `Team.bin.before-otherpools`.

## Los nombres de los latinoamericanos

Son correctos (los 40: Deportivo Llacuabamba, Sport Chavelines, Atlético Grau, Alianza
Universidad, Pirata FC, Juan Aurich, Universitario de Sucre, Aurora, Trujillanos, Orense,
Sportivo Ameliano, River Plate Montevideo, Rampla Juniors, Águilas Doradas…). Lo que fallaba no
era el nombre: era que **36 de los 40 no tenían grupo** y no salían.

## Lo que se dejó fuera a propósito

- **47 placeholders "Copa Argentina Club 02..48"**: son huecos de la copa, no clubes de un grupo.
- **The Old Boys**, **World Selection**, los **Generic League 01/43** sobrantes y los **ML Default**:
  huecos del juego, no plantillas reales.
- Los **4 clubes** de la Primera argentina que no existen en las tablas (ver `argentina-d1.md`).
