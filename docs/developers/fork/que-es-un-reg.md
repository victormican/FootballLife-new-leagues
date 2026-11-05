# Qué es un `reg` (regulación): definición, tabla y qué hace

## 1. Definición

Una **regulación** (`reg`) es **una fase de una competición con sus reglas**: cuántos equipos
entran, de qué forma se enfrentan (liga, eliminatoria, grupos…), cuántas vueltas, si hay prórroga o
penaltis, y cómo se llama esa fase.

No es la competición. Una competición **es dueña de una lista de clubes** (`CompetitionEntry.bin`)
y puede tener **varias regulaciones**: la liga regular, la fase de campeonato, el descenso, cada
grupo de una fase de grupos, la eliminatoria final… Todas comparten la misma lista de clubes.

```
Competition (cid)  ─┬─ Regulation (reg)  ── la liga regular
                    ├─ Regulation (reg)  ── el grupo A      (réplica)
                    ├─ Regulation (reg)  ── el grupo B      (réplica)
                    └─ Regulation (reg)  ── la eliminatoria
CompetitionEntry   ── los clubes, una sola vez para toda la competición
```

## 2. Las tres tablas

| tabla | registro | qué guarda |
|---|---|---|
| `Competition.bin` | 36 B | la competición: cid, región, confederación, código y nombre de menú |
| **`CompetitionRegulation.bin`** | **2352 B (0x930)** | **la fase: tipo, formato, equipos, rondas, reglas y 20 nombres** |
| `CompetitionEntry.bin` | 12 B | club + posición en la competición |

Las tres son arrays planos dentro de un contenedor WESYS (zlib): el número de filas es
`tamaño / registro`. Añadir una regulación = **añadir 2352 bytes al final** (clonando una que
funcione).

## 3. Campos del registro

| offset | bits | qué es |
|---|---|---|
| +0x00 | u16 | regulación **a la que se desciende** (0 = nada debajo) |
| +0x02 | u16 | **id de la regulación** (el `reg`) |
| +0x04 | u16 | regulación **a la que se asciende** |
| +0x06 | u16 | **padre**: la maestra de grupos o la fase de la que cuelga |
| +0x08 | 8 | cid, byte bajo |
| +0x09 | 8 | **tipo** (ver abajo) |
| +0x0A | 8 | índice de **grupo** dentro de la fase |
| +0x0B | 6 | **número de equipos** (máx. 63) |
| +0x0C | 12-17 | **plantilla de formato** (53 valores) |
| +0x0F | 8 | índice de escudo/colores |
| +0x10 | 0-4 | **número de grupos** (máx. 31) |
| +0x10 | 12-14 | **rondas**: 1 ida, 2 ida y vuelta, 3 triple |
| +0x10 | 21-23 | plantilla de jornadas (qué días se juega) |
| +0x10 | 24 | gol visitante · 25 prórroga · 27 penaltis · 28 tercer puesto · 29 una/dos piernas · 30 etiquetas con número |
| +0x14 | 20 × 115 | **nombres** de la fase, 20 idiomas (el 0 es español; la segunda tirada de 10 empieza en **+0x4B2**, con 0x20 de hueco) |
| +0x492 | 8 | cid, byte alto (ampliación a 16 bits) |

## 4. Tipos y formatos

**Tipo** (`+0x09`), con lo que hay hoy en el mundo:

| type | forma | juego de fábrica | mundo vivo |
|---|---|---|---|
| 1 | playoff | 14 | 32 |
| 2 | fase de grupos | 93 | 145 |
| 3 | eliminatoria | 56 | **306** |
| 4 | liga | 42 | 191 |
| 5 | liga estilo MLS | 2 | 4 |
| 8 | «otra liga» (grupos de Otros) | 4 | 9 |
| 9 | liga con split | 3 | 4 |

**Formato** (`+0x0C` bits 12-17): 1 liga · 2 copa a un partido con byes · 11 total del split ·
12 regular · 13 campeonato · 14 descenso · 15 inferior · 20/22 Champions · 28/30 Europa ·
50/52 a medida.

## 5. Réplicas de grupo: `maestra + 1024 · (g+1)`

Una fase de grupos es **una regulación maestra** (el total de equipos) y **una réplica por grupo**
cuyo id es `maestra + 1024·(g+1)`, con `+0x0A = g` y `+0x06` apuntando a la maestra. Por eso hay
ids como 1026, 2050, 3074… y por eso el mundo tiene **167 regulaciones con id > 1023**.

El tope de 1.200 es de **registros**, no de ids: el id es de 16 bits y las réplicas lo gastan a
saltos.

## 6. La regulación viva (memoria)

Al cargar, el motor copia las regulaciones a un array con **stride `0x314`**:

- `+0x00` es una **clave**: los 10 bits bajos son el id y los altos, el grupo (`id >> 10`).
- `+0x80` es el **cid** (comparado como dword por `phkind`); con cid ≥ 256 muchas rutas solo leen
  el byte bajo (nombre y emblema).
- `+0x84` es el tipo.
- El array está en **`block + 0xc131b0`** y la cuenta en `+0xd0bcf4` (ver
  `regulaciones-en-memoria.md`).

## 7. Cuántas hay

| | filas | type 1 | 2 | 3 | 4 | 5 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|
| **juego de fábrica** | **214** | 14 | 93 | 56 | 42 | 2 | 4 | 3 |
| **mundo vivo** | **691** | 32 | 145 | 306 | 191 | 4 | 9 | 4 |

| dato | valor |
|---|---|
| tope actual | **1.200** registros (`layout.json` → `fl26caps`) |
| tope de fábrica | 300 (el motor contaba solo 300; `fl26regs1200` sube el recuento) |
| libres | 509 registros |
| equipos por regulación | campo de 6 bits: **63** máximo real |
| lista de clubes del censo | **48** por regulación (`fl26clubs.c`, es código nuestro) |
| grupos | hasta 31 (campo de 5 bits) |

## 8. Qué hace una regulación en el juego

- **Fechas**: el calendario delige qué días juega según el id y la plantilla de jornadas.
- **Sorteo/calendario**: genera los enfrentamientos (round robin, eliminatoria, grupos).
- **Tablas**: una tabla de posiciones por regulación con grupos.
- **Ascenso/descenso**: `+0x00` y `+0x04` enlazan divisiones.
- **Copas**: `type 3` da el tamaño del **cuadro** (`teams`), que es lo que el menú llama «tamaño de
  sorteo»; sin regulación encontrada, la copa no abre.
- **Split**: la fila `type 9` (formato 11) es el «total» y las fases 12/13/14/15 las partes.
- **Grupos continentales**: maestra + réplicas + eliminatoria.

## 9. Ejemplos reales

| reg | cid | type | equipos | qué es |
|---|---|---|---|---|
| 30 | 22 | 4 | 26 | Liga Profesional (Argentina) |
| 34 | 27 | 2 | 32 | Mundial: fase de grupos (maestra) |
| 35 | 27 | 3 | 16 | Mundial: eliminatoria |
| 51 | 40 | 5 | 30 | MLS (estilo MLS) |
| 128 | 113 | 3 | 2 | Pro League Supercup (prototipo de las 101 supercopas) |
| 196 | 91 | 3 | 12 | Oceania |
| 250 | 221 | 8 | 58 | Otros Concacaf |
| 433 | 366 | 4 | 87 | Primera C Colombia |

## 10. Cómo se crea o se edita

- **Clonar una que funcione** y cambiar id, cid, tipo, equipos, rondas y nombres. Herramientas:
  `mkleague.py` (liga), `mkcup.py` (copa KO), `mkccup.py` (grupos + KO), `mksplit.py` (split),
  `fill_group.py` (más clubes), `dup_cups.py` (duplicar copas).
- **Nombres**: escribir las 20 ranuras con el hueco de 0x20 entre las dos tiradas
  (`pesdb.reg_set_name` las escribe seguidas y pisa el cid en `+0x492`; usar el helper de
  `mk_supercups.py`).
- **Equipos**: el campo `teams` debe cuadrar con las entradas reales (`check_world` avisa).
- **Ids**: libres de 1 a 1.200 para registros normales; 1024+ reservados a las réplicas de grupo.

## 11. Trampas conocidas

1. `teams` (6 bits) no puede pasar de **63**.
2. Una liga nueva **no juega** si no tiene fechas (calendario o `rcal`/`dates`).
3. El **cid** de la regulación se guarda también en `+0x492` (byte alto) y en el registro vivo solo
   llega el byte bajo a nombre/emblema.
4. El array vivo se ordena por **clave**, no por id: comparar la clave entera contra un id es un
   error (nos costó un cierre).
5. `check_world` es el juez: 0 errores antes de decir que una regulación está bien.
