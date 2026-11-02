# Añadir una selección que el juego no trae

`tools/add_nation.py` mete una nación nueva entera: la fila de `Country.bin`, la selección en
`Team.bin` y su plantilla en `Player.bin` + `PlayerAssignment.bin`.  Sirve para las federaciones que
existen y el juego no tiene (no-FIFA, territorios, asociados).

## Qué escribe

| tabla | qué |
|---|---|
| `Country.bin` | fila nueva: id de bandera en los bits 10-18 del primer dword, confederación en `+0x05`, nombre en las 18 columnas de 70 B desde `148` y el inglés en `288` |
| `Team.bin` | fila clonada de una selección de la misma confederación: id nuevo, id alt nuevo, nombre en los 20 slots, código de 3, país en `+0x46`, bit nacional de `+0x53` |
| `Player.bin` | la plantilla del modelo clonada (23 por defecto) con ids nuevos, nombre genérico y nacionalidad |
| `PlayerAssignment.bin` | una fila por jugador nuevo apuntando al equipo nuevo |

Confederaciones (`+0x05`): 2 UEFA, 3 AFC, 4 CONMEBOL, 5 CAF, 6 CONCACAF, 7 OFC.  El grupo del menú
sale de aquí: UEFA → Europe, CAF → Africa, CONCACAF → North & Central America, CONMEBOL → South
America, y AFC + OFC comparten «Asia-Oceania» (son el mismo slot del juego); Oceania es la liga
`cid 91` de `national-teams-and-oceania.md`.

**El nombre no puede comerse el código.**  El slot 10 de la fila (`0x35A`) solo tiene 24 B antes de
la abreviatura en `0x372`; la herramienta escribe ahí como mucho 24 y el resto de slots completos
(ver [abreviatura-de-equipo](abreviatura-de-equipo.md)).

## Uso

```
python tools/add_nation.py --base <pesdb del mundo> \
  --nation "<id de bandera>,<conf>,<NOMBRE>,<ENGLISH>,<ABBR>" \
  [--nation ...] [--squad 23] [--dry]
```

Comprueba antes de escribir: que el id de bandera esté libre y que el nombre no exista.  Con `--dry`
enseña el plan y no toca nada.  Los ids de equipo salen del máximo de la tabla + 1 (van a 74233 en
adelante desde 2026-11-02).

Después hay que darle arte, que es aparte:

```
python tools/mkcountryflag.py --root <livecpk del mundo> --from sider/flags --ids <ids>
python tools/mkcountryflag.py --root <livecpk del mundo> --base <pesdb> --from sider/flags --game <juego> --emblems
python tools/mkcountryflag.py --root <livecpk del mundo> --check --also <otro root> --game <juego>
python tools/check_world.py --base <pesdb> --worldfile <fl26world.txt>
python tools/fix_team_names.py --base <pesdb> --check
```

## Las nueve de 2026-11-02

Faltaban en el mundo (222 países) y se añadieron con 23 jugadores cada una:

| bandera | conf | nombre | id de equipo |
|---|---|---|---|
| 126 | AFC | ISLAS MARIANAS DEL NORTE | 74233 |
| 138 | CAF | ZANZIBAR | 74234 |
| 141 | CAF | REUNION | 74235 |
| 142 | CONCACAF | SAN BARTOLOME | 74236 |
| 143 | CONCACAF | SABA | 74237 |
| 154 | CONCACAF | SAN EUSTAQUIO | 74238 |
| 155 | CONCACAF | SAN PEDRO Y MIQUELON | 74239 |
| 156 | OFC | TUVALU | 74240 |
| 157 | OFC | KIRIBATI | 74241 |

Las banderas planas están en `sider/flags/flag_<id>.png` (Wikimedia Commons, 768 px de ancho; el
`_ll` se genera de ahí).  Resultado de las comprobaciones: 231 países sin textura pendiente, 86
selecciones nuestras sin escudo pendiente, `check_world` 0 errores, 0 abreviaturas rotas.

## Los nombres, en caja normal

El juego guarda el nombre del equipo en la columna que enseña en Select Team y los suyos van en caja
normal («Irlanda», «Tahití»), mientras que las altas por script salían en mayúsculas («ISLAS
MARIANAS DEL NORTE»), que es lo que se veía feo.  `tools/title_case_names.py` las pone en caja
normal:

```
python tools/title_case_names.py --base <pesdb del mundo> [--dry]
python tools/title_case_names.py --base <pesdb> --all-teams     # también los clubes
```

- **Selecciones** (bit nacional de `+0x53`) y **filas de `Country.bin`** desde la 214: nombre en los
  20 slots y en el largo de `0x37C`, más las 18 columnas y el inglés del país.  Las partículas
  («de», «del», «y», «la»…) quedan en minúscula y los guiones se capitalizan («Saint-Pierre»).
- **Clubes**: no se tocan por defecto, porque sus nombres ya venían bien y hay siglas que se
  romperían («Países Bajos KKD Club 09» → «Kkd»).  `--all-teams` los incluye.
- El código de tres letras de `0x372` no se toca, y el slot 10 sigue limitado a 24 B.

Guayana Francesa, Guadalupe, Martinica, San Martín, Sint Maarten y Bonaire ya estaban desde el alta
de las no-FIFA (ids 96-123); no se duplican: el tool aborta si el nombre o el id ya existen.

## Los nueve territorios de 2026-11-03

Segunda tanda, los no FIFA de Europa y Oceanía que no son miembros de confederación (o lo son con
estatus discutido):

| bandera | conf | nombre | id de equipo |
|---|---|---|---|
| 158 | UEFA | Groenlandia | 74242 |
| 160 | UEFA | Ciudad del Vaticano | 74243 |
| 173 | UEFA | Chipre del Norte | 74244 |
| 174 | OFC | Micronesia | 74245 |
| 175 | OFC | Islas Marshall | 74246 |
| 177 | OFC | Nauru | 74247 |
| 178 | OFC | Niue | 74248 |
| 179 | OFC | Tokelau | 74249 |
| 180 | OFC | Wallis y Futuna | 74250 |

Palaos (184) y Mónaco (250) ya tenían país y selección; no se duplican.  El mundo queda en **240
países** y **95 selecciones nuestras**, todas con bandera y escudo.

