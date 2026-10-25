# Estado del mundo `_FL26All` y sus límites, 2026-10-24

Lo que hay hoy en la copia de pruebas (`D:\SP Football Life 2026 - copia - copia`), con los ids y
los topes medidos. Complementa a [limits-2026-10-24.md](limits-2026-10-24.md).

## Totales

| cosa | valor | tope | libre |
|---|---|---|---|
| jugadores | **123.015** | 123.825 (array del bloque) | 810 |
| equipos | **3.910** | 4.800 (array) | 890 |
| selecciones | **211** | — (las de la FIFA) | 0 |
| clubes | **3.699** | 4.700 (tabla del Edit, DLL) | 1.001 |
| competiciones | **250** | 255 + 256..511 (con `fl26cid16`) | ~261 |
| regulaciones | **477** | 1.024 | 547 |
| slots de Select Team | **137** | 250 (`fl26slots250`) | 90 (23 del juego) |
| copas en Cup mode | **17** | 256 (`MAX_CCUP`) | 239 |
| lista de Cup mode | **13** | 13 (vector del menú) | **0** |

## Clubes

- **Ids**: los del juego van de 1 a ~71.577; los nuestros empiezan en **71.578** y el mayor es
  **74.738**. Las selecciones ocupan 71.676..71.742 y 1..1141.
- **Cómo se hicieron**: `add_generic_leagues.py` (las primeras), `grow_leagues.py` (más clubes por
  liga), `grow_squads.py` (más jugadores por club), `mk_other_africa.py` (los grupos). Todos clonan
  la fila de `Team.bin` de un club con plantilla y le dan id, alt id, nombre en los 20 slots, país y
  jugadores con ids de `playeredit.free_ids`.
- **Plantillas**: 30 jugadores en los clubes de liga (11 en los grupos, por presupuesto). Los
  porteros sobrantes se corrigieron con `fix_clone_positions.py` (máximo 5 por club).
- **Crestas**: `mkcrests.py --flags` generó 8.571 PNG (128/256/512) en
  `common/render/symbol/flag/e_<id>_r*.png`, la ruta que sirve el juego.
- **Ligas**: 127 a 20 clubes, 5 a 30, 5 a 40; nombres “Liga NN Clubes MM” por tamaño.

## Países

Los clubes nuevos y las ligas usan **8 combinaciones (region, country, conf)** ya probadas en el
mundo, rotando para no ser todos del mismo país:

| region | country | conf |
|---|---|---|
| 29 | 200 | 2 (UEFA) |
| 30 | 198 | 2 |
| 31 | 151 | 4 (CONMEBOL) |
| 32 | 149 | 4 |
| 33 | 58 | 5 (CAF) |
| 34 | 9 | 3 (AFC) |
| 35 | 112 | 6 (CONCACAF) |
| 36 | 164 | 7 (OFC) |

- `country` es la bandera (id de `Country.bin`, 9 bits en `Team.bin +0x46`, bit 2 en adelante).
- `conf` es la confederación que la fila de la competición dice (`Competition.bin +6`, 3 bits).
- Las **211 selecciones** salen de `Country.bin` por confederación: UEFA 55, CAF 54, AFC 46,
  CONCACAF 35, OFC 11, CONMEBOL 10. South Sudan y Chinese Taipei entraron por Mónaco y Palau.
- **Oceania**: liga de las 11 selecciones OFC, nombre propio, sale en Select Team.

## Grupos “Other …” y Classic Teams

| grupo | slot | qué lleva |
|---|---|---|
| Other Clubs (Africa) | 75 | **Wydad (9030)** y **Espérance (9033)**, los dos clubes sin competición |
| Other Clubs (CONCACAF) | 72 | 48 genéricos (nombre propio; el juego no tiene ese grupo) |
| Other European Leagues | 69 | 20 nuestros; el juego no tiene clubes en el pool en este mundo |
| Other Clubs (Asia) | 70 | 20 nuestros; ídem |
| Classic Teams | 5 | 20 nuestros, pero el juego ya llena los 48 y no caben |

`fl26clubs.dll` **suma** la lista del juego y la nuestra hasta 48 (`MERGE_MAX`); como en este mundo
casi todo club juega liga, los pools del juego están vacíos y solo se ven los nuestros.

## Límites: qué está roto y qué no

| límite | valor viejo | ahora | cómo |
|---|---|---|---|
| jugadores | 65.536 | **123.015** | `fl26playercap.lua`: tabla de 30.000 (`je`→`jae`) + stub del centinela 255 |
| competiciones | 255 | **511** | `fl26cid16.lua` (3 en sitio + 2 cuevas) + `cid16_migrate.py` (id en `+0x20`; **el `+4` NO era libre**) |
| copas en Cup mode | 16 | **256** | `MAX_CCUP`/`MAX_CCUP_FWD` en `fl26swiss.c` |
| clubes por regulación | 48 | **48** | estructural: lista en `+0x170` |
| lista de Cup mode | 13 | **13** | **pendiente**: el vector del menú; la DLL intenta ampliarlo si es array miembro |
| slots | 250 | 250 | `fl26slots250` (90 libres) |

## Herramientas de esta ronda

```
tools/grow_leagues.py          más clubes por liga (--clubs, --big, --limit, --skip, --squad)
tools/grow_squads.py           más jugadores por club
tools/fix_clone_positions.py   arregla los porteros clonados
tools/cid16_migrate.py         id de competición como palabra en +0x20
tools/cid16_test.py            mueve una competición a un id >255 (para pruebas)
tools/mk_other_africa.py       un grupo “Other …” con N clubes en un slot servido
tools/mk_conf_cup.py           copa continental a partir de las ligas de una confederación
sider/experimental/fl26cid16.lua    ids de competición >255
sider/experimental/fl26playercap.lua muro de jugadores
```

## Pendiente

1. **Lista de Cup mode (13)**: ampliarla (la DLL lo intenta; falta ver el log) o quitar copas del
   juego para hacer hueco.
2. **cid 256..511**: probado 256 y 320; 262/263/304 no salen — queda una lectura por byte.
3. **Grupos**: subir el tope de 48 si se quieren los genéricos detrás de los del juego en Classic.
4. **“Datos del usuario”** en el primer pintado de Select Team: es el placeholder del juego cuando
   aún no hay equipo resuelto; la sonda demostró que las listas ya vienen completas a la primera.

## Copas del mundo (26)

Las 20 que ya habia mas seis nuevas de `tools/add_world_cups.py`, que usa ids de competicion
`66..71` (filas del juego que ninguna liga de este mundo usaba; se borran su competicion,
regulaciones y entradas) y regulaciones `210..215`:

| copa | cid | reg | formato | quien juega |
|---|---|---|---|---|
| FIFA World Cup | 66 | 210 | eliminatoria de 32 | 13 UEFA, 5 CAF, 4 AFC, 4 CONMEBOL, 4 CONCACAF, 2 OFC |
| FIFA Club World Cup | 67 | 211 | eliminatoria de 32 | el 1.? de 14 ligas UEFA, 8 CONMEBOL, 6 AFC, 4 CAF |
| UEFA EURO | 68 | 212 | eliminatoria de 24 (como la FA Cup) | 24 selecciones UEFA |
| Copa America | 69 | 213 | eliminatoria de 16 | 10 CONMEBOL + 6 CONCACAF |
| AFC Asian Cup | 70 | 214 | eliminatoria de 24 | 24 selecciones AFC |
| CAF Africa Cup of Nations | 71 | 215 | eliminatoria de 24 | 24 selecciones CAF |

Mas la **CAF Confederation Cup** (cid 65, reg 206/ko 207, 4 grupos de 4, 16 clubes) que ya
estaba montada y ahora si se escribe: `mk_conf_cup.py` pasaba a `mkccup.py` un `--out`
una carpeta por encima y las tablas caian en `_FL26All\common\common\etc\pesdb`.

Las copas de naciones toman los equipos por id (`0:<teamid>`), no por puesto de liga: las
selecciones no tienen liga en este mundo. `nations.py` da los 211 por confederacion
(UEFA 55, CAF 54, AFC 46, CONCACAF 35, OFC 11, CONMEBOL 10).

Ojo: **Cup mode solo pinta 13** entradas de su vector; con 26 copas el menu seguira cortando.

## Liga de selecciones no FIFA (2026-10-24, pendiente de probar)

`Country.bin` viaja ahora **en el livecpk** (`_FL26All\common\etc\pesdb\Country.bin`): el juego
no lo traia ahi y sin filas nuevas no hay pais ni bandera para una seleccion no FIFA. Se anadieron
8 filas en ids de bandera libres y `tools/add_nonfifa.py` creo sus equipos (plantilla de 11 clonada
de Nueva Zelanda), 88 jugadores:

| pais | country/flag | conf | equipo |
|---|---|---|---|
| Martinica | 96 | CONCACAF | 74739 |
| Guadalupe | 97 | CONCACAF | 74740 |
| Guayana Francesa | 99 | CONCACAF | 74741 |
| San Martin | 100 | CONCACAF | 74742 |
| Sint Maarten | 101 | CONCACAF | 74743 |
| Bonaire | 102 | CONCACAF | 74744 |
| Cataluna | 118 | UEFA | 74745 |
| Padania | 123 | UEFA | 74746 |

Liga `Non-FIFA Nations` (reg 216, cid 110, conf 6, slot -1, 8 equipos) -> 141 ligas.

**Validado**: 222 filas en Country.bin, 219 selecciones = **211 FIFA + 8 no FIFA**; las tres filas
sin equipo siguen siendo Palau, Monaco y "Others"; ninguna copa (Mundial, CWC, EURO, Copa America,
Asian Cup, AFCON, resto) mete equipos no FIFA: el Mundial son 32 equipos FIFA, el CWC toma clubes.

Sin arte: las banderas `flag_<id>.png` no estan en la carpeta del juego (viven en un cpk), asi que
estos ocho salen sin bandera hasta que se suelten los PNG en `common/render/symbol/flag/`.

### Non-FIFA Nations: se queda bajo CONCACAF (C)

Decision del 2026-10-24: la liga no FIFA se queda **como esta**, tipo 4 y conf 6, o sea que en los
menus aparece bajo CONCACAF. Se descartaron `conf=0` (sin insignia) y dejarla sin slot (fuera de
Select Team). El tipo de la regulacion es lo que marca "esto no es liga": 4 liga (Select Team),
3 copa y 2 fase de grupos (Cup mode).

