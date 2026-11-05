# Supercopas por nación (2026-11-05)

Creadas **101 supercopas**, una por país con primera división y copa nacional: el campeón de la
liga contra el campeón de la copa, a un partido, antes de la temporada.

## Cómo está construida una

Cada una es una eliminatoria de dos clubes copiada de la **Pro League Supercup** del juego
(regulación 128, competición 113, código `BELGIUM_SUPER_CUP`):

- fila en `Competition.bin`: cid nuevo, región del país, código `FL_SUP_<cid>`, nombre de menú;
- fila en `CompetitionRegulation.bin`: tipo 3 (eliminatoria), **2 equipos**, formato 2, los 20
  nombres (`Supercopa <país>`);
- dos filas en `CompetitionEntry.bin` (posiciones 1 y 2) con los dos primeros clubes de la liga
  como relleno: el motor los sustituye en juego;
- línea en el world file:

```
ccup <reg> ko=<reg> groups=0 entry=<liga>:1,<copa>:0 cid=<cid> fill=2 national=1 like=128 \
     name=Supercopa <país>
```

`entry=<liga>:1` es el **campeón de la liga** y `entry=<copa>:0` el **campeón de la copa** — el
mismo par que usa la Supercopa de España del juego. `like=128` hace que `fl26swiss` la datee como
la supercopa belga.

## Ids gastados

| | antes | después |
|---|---|---|
| competiciones | 394 | **495** |
| regulaciones | 589 | **690** |
| entradas | 5137 | **5339** |
| líneas `ccup` | 168 | **269** |

Los cids van de 257 en adelante, **saltando los que tienen byte bajo 0** (256, 512, 768): ese
byte bajo es el que usan el menú y el emblema, y con 0 se rompe la búsqueda.

## El menú de copas: de 256 a 512 filas

Con 269 copas, el stub de `fl26cupgrow` (256 filas) se quedaba corto. Se subió a **512**:

- `local WANT, RING = 512, 16` (el buffer de cada anillo: 512 × 12 = 6.144 B);
- en el stub, `lea rcx,[r11+0xC00]` (3.072 B = 256 filas) → `0x1800` (6.144 B = 512 filas).

La guarda de espacio libre (`cmp r11, 0x400`) sigue valiendo. Copia del módulo anterior:
`fl26cupgrow.lua.before-512`.

## Verificación

`check_world`: **495 competiciones, 690 regulaciones, 5339 entradas, 269 copas, 0 errores**.

Ejemplo medido:

```
reg 12  cid 257  FL_SUP_257  Supercopa Albania  tipo 3  2 equipos  2 entradas
reg 65  cid 264  FL_SUP_264  Supercopa Austria   tipo 3  2 equipos  2 entradas
```

Copias: `Competition.bin.before-supercups`, `CompetitionRegulation.bin.before-supercups`,
`CompetitionEntry.bin.before-supercups`, `fl26world.txt.before-supercups`.

## Lo que sigue pendiente (el nombre)

Las 101 supercopas entran en Kick Off > Cup y se juegan, pero el menú sigue resolviendo el nombre
por el **byte bajo del cid** (el campo `+0x80` del registro vivo solo guarda un byte). Con cid
257..357 mostrarán el nombre de la competición que tenga ese byte bajo, igual que las otras copas
del mundo. Es el mismo bloqueo de siempre: falta la base real del array de regulaciones o rellenar
ese `+0x80` con el cid completo.
