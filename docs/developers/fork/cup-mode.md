# Cup mode: play the cups a world builds

Kick Off > Cup lists the competitions the game ships. A world's own competitions — the
continental cups of `mkccup.py` (`ccup` lines), the Copa Centroamericana, the league and
pre-season cups — are in the live competition table, but the Cup-select menu builds its list from
the shipped categories, so they were not offered. Since 2026-10-23 they are added to that list.

## How the list works

- The Cup-select menu is `MenuModeCupSelect` (vtable `0x142692c40`); the only Cup flow enters it.
  Master League uses `MenuModeCompeSelect`, a different menu.
- Its init is wrapped by `fl26swiss.dll` (`CUPSEL_VT_RVA 0x2692d18`,
  `CUPSEL_INIT_RVA 0xb1c990`). The list is at `self+0x90` (begin) and `self+0x98` (end), 12-byte
  items with the competition id at `+0`. `self+0xa0` is the end of the storage.
- Before the menu counts its choices, the handler:
  1. removes every competition whose group phase holds more than 32 clubs (GitHub #100: the 36-club
     Champions/Europa/Conference league phases cannot be drawn by Cup mode);
  2. **appends the world's own cups**, one 12-byte item per competition id, copied from an existing
     item so the name/logo lookup has a template. It only appends while the vector has room; the
     log says `Cup mode -- N world cup(s) added, all in` or `no room for the rest`.
- The ids come from the `ccup` lines: `leaguebuilder.ccup_options` writes `cid=<competition id>`
  on every cup line, `fl26swiss.lua` collects them and calls `fl26_swiss_cup_cids`.

## The field Cup mode plays

`mkccup.py` writes `CompetitionEntry` rows: the clubs at the entry positions, a fixed field taken
from the world's leagues at Build time. Cup mode uses those entries and the competition's own
shape (groups of four + knockout, or a straight knockout), so the cup is playable without the
Master League season.

The **Club World Cup** is not in this list yet: `mkcwc.py` writes no entries on purpose (its field
is chosen from league tables by `fl26swiss` in a Master League season), so Cup mode would open an
empty cup. Adding a fixed 32-club entry list for Cup mode is the next step if it is wanted.

## Master League

The same cups are already in a Master League season: the world file's `ccup` lines make
`fl26swiss` fill them from the league tables when the Champions League play-off progresses, draw
the groups, start the knockout and date both. Competition Info and the schedule show them by
their competition id. They are not in Select Team (they are cups, not leagues); a career does not
start in one.

## Test

1. Build a small world with one of the cups, for example the CAF/OFC/CONCACAF recipe of
   [limits-and-formats.md](limits-and-formats.md), into the test copy.
2. Switch the copy to that world (`python tools/leaguebuilder.py on <world> --game <copy>` or Mod
   Studio), start the game, and open **Kick Off > Cup**.
3. The cup should be in the list next to the shipped ones. Pick it, pick a club, and play the
   first match.
4. The `sider.log` lines to check:
   - `fl26swiss: world file -- N cup(s) for Kick Off > Cup, M taken`
   - `fl26swiss: Cup mode -- N world cup(s) added, all in (list X of Y)`
   - if it says `no room for the rest`, the Cup vector is full and the remaining cups are not
     offered; the log gives the size.

## Más de 13 copas: `fl26cupgrow.lua`

La lista del menú es un vector con sitio para 13 items (156 bytes), y con las dos competiciones
que se quitan por grupos de 36/34 clubes solo quedaban **5 huecos** para las nuestras: de las 19
del mundo entraban 5 y el log decía `no room for the rest (list 13 of 13)`.

`fl26cupgrow.lua` (activo desde 2026-11-04) envuelve el slot de la vtable donde `fl26swiss` dejó
su handler: antes de llamarlo, copia los items que ya hay a un buffer de **64 items** (de un anillo
de 16 buffers de 768 B), repunta `begin/end/cap` (`self+0x90/+0x98/+0xa0`) y salta al handler
anterior. Así el handler encuentra sitio y añade todas. El destructor (`0x140b1c810`) se neutraliza
para que no libere un buffer ajeno.

Dos fallos del stub, medidos a base de crashes del 2026-11-04 y ya corregidos:

1. `begin` se guardaba en `rax` y luego `rax` se reutilizaba como índice del anillo: el
   `rep movsb` copiaba desde la dirección 0 (crash `0x16110026f`). Ahora `begin` va en `rdx`, con
   su `push`/`pop`.
2. El SIB de `mov r11,[r10+rax*8]` llevaba REX.X y leía `[r10+r8*8]`.

Resultado en vivo: `Cup mode -- 19 world cup(s) added, all in (list 27 of 64)`.

Y la línea de log final usaba `%#x`, que el `format` de LuaJIT no acepta: el módulo se quedaba en
"NOT activated" con el parche ya escrito. Ahora concatena con `string.format("%x", …)`.

## Cuántas copas caben (2026-11-04)

El buffer del stub es lo que manda: estaba en 64 items de 12 bytes (768 B) y ahora está en **256**
(3072 B, `cmp r11, 0xc00` y `lea rcx,[r11+0xc00]`, con `WANT = 256`). El anillo son 16 buffers.

| recurso | usado | tope | margen |
|---|---|---|---|
| filas en Kick Off > Cup | 46 | **256** | 210 |
| regulaciones | 488 | 1200 | 712 |
| ids de competición | 293 | 1023 | 730 |
| slots | 132 | 250 | — las copas no gastan slot |
| clubes / jugadores | 3450 / 89.488 | 4800 / 262.143 | las copas reutilizan clubes |

El coste en regulaciones es lo único que hay que mirar al planificar:

- copa de eliminatoria (estadual, nacional): **1** regulación → caben ~700 más;
- copa con fase de grupos de 8: **10** (maestra + 8 réplicas + eliminatoria) → caben ~70 más.

Con eso: **duplicar (92) y triplicar (138) entran sin tocar nada más**; el límite realista de
mezcla es unas 70 copas con grupos + 68 de eliminatoria = 138, y si todas son de eliminatoria se
llega a las 256 filas del menú.

## Lo que sigue mal: el nombre

Con el `cid` de 16 bits resuelto, el nombre de la copa en esa lista **no** sale de
`Competition.bin +0x14` ni de las ranuras de la regulación: los dos están escritos y verificados, y
la lista sigue mostrando el nombre del item que copió como plantilla (`FIFA Club World Cup`, la
primera copa del juego). Es un trabajo dentro de `fl26swiss.dll`: al añadir cada item hay que
volver a resolver su nombre (o copiarlo del sitio correcto) en vez de heredar el de la plantilla.
