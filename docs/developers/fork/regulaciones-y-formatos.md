# Regulaciones, formatos y topes (investigación, 2026-11-04)

Cómo se define una competición en Football Life 2026, qué formas de liga y copa sabe jugar el
motor, qué topes hay de verdad y cómo se sube cada uno. Todo lo que aparece aquí está medido
sobre las tablas del juego o sobre el exe; lo que es hipótesis va marcado como tal.

Resumen en cinco líneas:

- Una competición son **tres filas**: `Competition.bin` (36 B), `CompetitionRegulation.bin`
  (2352 B) y `CompetitionEntry.bin` (12 B). Añadir una es **añadir filas al final** de cada tabla.
- El **formato** no es código: es un byte `type` (+0x09) más una plantilla `format` (+0x0C,
  bits 12-17) con 53 valores; el resto (grupos, rondas, prórroga, penaltis, ida/vuelta) son bits.
- El motor **no genera calendario** para una competición nueva: los partidos los pone el
  calendario grande (38 fechas) o el DLL (`fl26swiss`). Sin fechas, la liga se queda en "avanzar
  a la próxima temporada" con cero partidos.
- La **fase de liga tipo suizo** (Champions de 36) no es expresable en datos: hay que inyectar
  los emparejamientos.
- Los topes reales que quedan son **250 slots**, **38 clubes por liga**, **127 regiones** y
  **48 clubes por regulación**; jugadores, equipos, regulaciones, cid y filas de copa ya están
  subidos por módulos.

---

## 1. Las tres tablas

Las `.bin` no son crudas: son contenedores **WESYS** (3 bytes de cabecera, `WESYS`, u32 tamaño
comprimido, u32 tamaño real, zlib). Dentro, cada tabla es un array plano de registros de tamaño
fijo, **sin índice y sin contador**: el número de filas es `tamaño / registro`.

```python
def wesys_unpack(d):
    assert d[3:8] == b"WESYS"
    csz, usz = struct.unpack("<II", d[8:16])
    return zlib.decompress(d[16:16 + csz])
```

| tabla | registro | qué guarda |
|---|---|---|
| `Competition.bin` | 36 B | la competición: región, cid, banderas, código interno y nombre de menú |
| `CompetitionRegulation.bin` | 2352 B (0x930) | las **reglas** de una fase: tipo, formato, equipos, rondas, nombres |
| `CompetitionEntry.bin` | 12 B | qué club juega y **en qué posición** de esa competición |

`Competition.bin`

| offset | bits | significado |
|---|---|---|
| +0x00, +0x01 | — | 100 / 200 en todas las filas de fábrica |
| +0x03 | 3..7 | **región** (país) de la lista; se escribe `region << 3` (`mkleague.enc_region`) |
| +0x05 | 8 | cid, byte bajo |
| +0x06 | 0..2 | confederación (3 AFC, 4 CONMEBOL, 5 CAF, 6 CONCACAF, 7 OFC) y banderas de tipo |
| +0x07 | 8 | cid, byte alto (ampliación de `cid16_migrate`) |
| +0x08 | 28 B | código interno (`ENGLAND_D1_LEAGUE`); es lo que copian las herramientas |
| +0x14 | 16 B | **nombre de menú** (se trunca a 15) |

`CompetitionRegulation.bin`

| offset | bits | significado |
|---|---|---|
| +0x00 | u16 | regulación **a la que se desciende** (0 = nada debajo) |
| +0x02 | u16 | **id de regulación** |
| +0x04 | u16 | regulación **a la que se asciende** |
| +0x06 | u16 | padre: la maestra de grupos o la fase de la que cuelga (0 = ninguna) |
| +0x08 | 8 | cid, byte bajo |
| +0x09 | 8 | **tipo**: 1 playoff, 2 grupos, 3 eliminatoria, 4 liga, 5 estilo MLS, 9 liga con split |
| +0x0A | 8 | índice de grupo dentro de la fase (0 = maestra) |
| +0x0B | 6 | **número de equipos** (máx. 63) |
| +0x0C | 12..17 | **plantilla de formato** (53 valores, ver §3) |
| +0x0F | 8 | índice de escudo/colores (0 = sin activo propio) |
| +0x10 | 0..4 | **número de grupos** (máx. 31) |
| +0x10 | 12..14 | **rondas**: 1 ida, 2 ida y vuelta, 3 triple |
| +0x10 | 21..23 | plantilla de jornadas (qué días de la semana juega) |
| +0x10 | 24 | regla del gol visitante |
| +0x10 | 25 | prórroga |
| +0x10 | 27 | penaltis |
| +0x10 | 28 | partido por el tercer puesto |
| +0x10 | 29 | una o dos piernas |
| +0x10 | 30 | etiquetas de grupo con números en vez de letras |
| +0x14 | 20 × 115 B | **nombres**, 20 idiomas (0 = inglés); la segunda tirada de 10 empieza en +0x4B2 |
| +0x492 | 8 | cid, byte alto (ampliación de `cid16_migrate`) |

`CompetitionEntry.bin`

| offset | significado |
|---|---|
| +0x00 | id de equipo (`Team.bin`) |
| +0x04 | id de entrada, **único** (9100+ está libre) |
| +0x08 | cid, byte bajo |
| +0x09 | **posición** en la competición, base 1 (en copa, puesto de sorteo) |
| +0x0B | cid, byte alto |

Ascenso y descenso entre divisiones son **dos enteros**: el +0x00 de la de arriba apunta a la de
abajo y el +0x04 de la de abajo a la de arriba. No hay tabla de ligas ni código.

## 2. El registro vivo no es el del fichero

Al cargar, el motor copia las regulaciones a un bloque con **stride 0x314** (no 0x930) y
recalcula campos. Lo que se sabe medido:

- `ctx = 0x1414b6a60(&cid)` → `block = [ctx+0x48]`; cuenta en `[block+0xd0bcf4]`
  (vale 65535: el tope real lo pone el parche, 1200) y registros en `[block+0xc12e9c]`
  (**la base real sigue sin confirmarse**, ver §7.5).
- dentro del registro vivo: **cid en +0x80** (comparado como dword por `phkind` = `0x14150af30`,
  pero el campo solo lleva el byte bajo) y **tipo en +0x84**.
- **format** en +0x308 (`(dword >> 0x17) & 0x3f`); el parser rechaza `format >= 0x35` (53) en
  `0x1414f7fde`.

Consecuencia práctica: lo que se escribe en el fichero es `+0x0C`; lo que lee el menú y el
sorteo en caliente es `+0x308`/`+0x80` del registro vivo. Y el cid vivo solo guarda un byte:
**una competición con cid ≥ 256 se resuelve como la que tenga ese byte bajo** (nombre, emblema y
tamaño de sorteo). Es el único truncamiento que queda.

## 3. Tipos y plantillas

`type` (+0x09):

| valor | forma | ejemplo |
|---|---|---|
| 1 | playoff | play-off de ascenso |
| 2 | fase de grupos | Libertadores, Mundial, EURO |
| 3 | eliminatoria | FA Cup, Gold Cup, nuestras 145 copas |
| 4 | liga | Premier League |
| 5 | liga estilo MLS | MLS (conference + playoffs) |
| 9 | liga con split | Scottish Premiership (fila "total") |

`format` (+0x0C bits 12-17), valores vistos en uso:

| valor | forma |
|---|---|
| 1 | liga normal (round robin completo) |
| 2 | copa nacional a un partido por ronda (**con byes**: cualquier tamaño 2..44) |
| 11 | liga con split, fila **total** (sin fechas propias) |
| 12 | fase **regular** del split |
| 13 | fase **campeonato** (top) |
| 14 | fase **descenso** (second) |
| 15 | fase **inferior** |
| 20 / 22 | grupos / eliminatoria de la Champions |
| 28 / 30 | Europa League |
| 50 / 52 | grupos / eliminatoria a medida |

Grupos: la fase maestra lleva el total de equipos y una **réplica por grupo** con id
`maestra + 1024 * (g + 1)`, `+0x0A = g` y `+0x06` apuntando a la maestra. Es la regla del
Libertadores y del Mundial, y la que usan `mkccup.py` y `mk_cwc`.

## 4. Qué se puede construir hoy (probado)

| forma | cómo | herramienta / clave | estado |
|---|---|---|---|
| liga a una/dos/tres vueltas | `type 4`, `format 1`, rondas 1-3 | `mkleague`, receta `clubs`/`legs` | jugada |
| liga de 30-38 clubes | 38 fechas del calendario grande | `clubs: 38` (una vuelta) / 20 (dos) | construida, sin jugar |
| split escocés | fila total `type 9` + fases `type 4` format 12/13/14/15 | `mksplit.py`, receta `split` | jugada (Ecuador) |
| Apertura/Clausura | dos fases con `carry=0` | receta `apertura` | construida |
| copa KO con byes | `type 3`, `format 2`, bracket 2..44 | `mkcup`, `like=23`, bracket | jugada (168 copas) |
| copa de grupos + KO | maestra `type 2` + réplicas + KO `type 3` | `mkccup.py`, línea `ccup ... groups=N` | jugada (Libertadores, Mundial) |
| supercopa | KO de 2 con `entry=<copa>:0` | `scup`, `ccup` de 2 | jugada |
| copa de selecciones | igual que clubs, con ids de selección | `add_world_cups.py`, `mk_cwc` | jugada (Mundial 32) |
| liga de 36 tipo suizo | **no** en datos: 8 rivales de 35 | `mkswiss.py` genera 144 partidos y el DLL los instala | construida, no nativa |

Ejemplo mínimo de liga (medido y probado en el juego): clonar una liga que funcione (Süper Lig),
cambiar en `Competition.bin` región, cid, flags y código; en la regulación el id, el cid, el
número de equipos y los 20 nombres; y añadir una entrada por club con posición 1..N. Eso es todo:
**no hace falta tocar el exe para añadir una liga.** Lo que falta después es el **calendario**
(§6.4), que es donde el motor se queda corto.

## 5. Lo que el motor no expresa

| forma real | por qué no | camino |
|---|---|---|
| Colombia: 20 → 8 en dos grupos de 4 → final | el split no **corta** (mete a todos); el KO es KO, no grupos | copa de 8 con `groups=2` alimentada por posiciones 1..8, en fechas libres |
| Argentina: 2 zonas de 15 + interzonales + KO de 16 | una zona es una regulación propia (dos regulaciones en el mismo cid) y los interzonales tocan los dos calendarios | dos regulaciones de 15 en el mismo cid + `ccup` de 16 con `entry=<reg>:<pos>` |
| Uruguay: Intermedio entre Apertura y Clausura | los días del `ccup` son fijos (finales de noviembre a febrero) | `days=` en la línea `ccup` (ya mueve las rondas de un KO) |
| descenso por promedio | no hay campo de promedio; solo ascenso/descenso directo | no soportado |
| fase de liga suiza | la regulación siempre juega un round robin completo | inyectar emparejamientos (lo hace `fl26swiss`) |

Nada de esto necesita un formato nuevo de registro: son **una segunda regulación en el mismo
cid** y/o **una copa con días propios**.

## 6. Topes (medidos con `python tools/limits.py`)

### 6.1 Tabla

| recurso | tope | dónde se sube |
|---|---|---|
| jugadores | **123.825** | `layout.json` (`cap_new`) → `patchset` → `fl26caps.lua` |
| equipos | **4.800** | idem |
| entrenadores | **6.800** | idem |
| regulaciones | **1.200** | idem (+ `fl26regs1200` para el recount) |
| partidos de calendario (rec596) | **65.000** | idem |
| fixtures | **8.000** | idem |
| clubes del Edit | **4.700** | `tools/native/fl26edit.c` |
| slots de Select Team | **250** | `fl26slots250.lua` |
| copas del menú (filas) | **256** | `fl26cupgrow.lua` (de 13 de fábrica) |
| copas aceptadas por el DLL | **512** | `fl26swiss.c` (`MAX_CCUP`) |
| ids de competición | **1.023** | `fl26cid16.lua` (tabla de 1024, máscara `0x3ff`; `limits.py` aún imprime 511) |
| regiones | **127** | `fl26reg128.lua` |
| clubes por regulación (campo) | **63** | 6 bits en +0x0B |
| clubes por regulación (lista del censo) | **48** | estructural, `fl26clubs.c` |
| clubes por liga (calendario) | **38** | `BIG_LEAGUE_DAYS` |

Uso del mundo vivo (`_FL26MyWorld`, 2026-11-04): 3.450 equipos, 89.488 jugadores, 293
competiciones, 488 regulaciones, 4.333 entradas, 149 ligas, 168 copas.

### 6.2 Cómo se sube un tope de tabla (la cadena)

```
patches/layout.json      stride, cap_old, cap_new y TODAS las direcciones que leen el array
tools/patchset.py <set>  desensambla cada dirección, localiza el campo de 4 bytes y emite {va, old, new}
patches/<set>.json       el set completo
sider/fl26caps.<set>.lua el aplicador generado  ->  modules/fl26caps.lua
```

Reglas que se derivan de haber roto el juego varias veces:

1. **Todo o nada**: el aplicador compara ~3.500 direcciones con los bytes del exe; si una no
   coincide, no escribe nada.
2. **Nadie más puede tocar esas direcciones**: un módulo que las pise antes hace abortar el set
   entero; si las pisa después, deja el mundo a medias.
3. Subir el cap de jugadores obliga a **regenerar el set entero**: el array de jugadores se mueve
   en sitio y a partir de 66.918 jugadores se come la "cola baja" (306 operandos que
   `tools/lowertail.py` mantiene).
4. Verificación sin arrancar: `python tools/setcheck.py` (hoy 3.839 parches, 0 discrepancias) y
   `python tools/lowertail.py --check`.

### 6.3 Topes que no son de tabla

- **Slots** (`fl26slots250`): una liga visible = un slot. El slot 123 es el centinela oculto
  (la liga se juega pero no se lista): es lo que usa Select Team para esconder grupos.
- **cid** (`fl26cid16`): el censo de Select Team es un `std::map<byte, fila*>` que deduplica por
  byte, así que ensanchar los `cmp` nunca podía funcionar; se contesta desde una **tabla plana de
  1024 punteros** (clave `byte[+8] | byte[+0xb] << 8`). ids > 1023 no caben en el orden de
  entradas.
- **Filas del menú de copas** (`fl26cupgrow`): stub de vtable de 256 filas; el DLL no sabe
  ampliar la lista solo (crashea en `0x1403fef5f`).
- **Filas ocultas** (`fl26comptab`): una fila oculta por copa y tope de filas 400 → 1200.
- **Emblema**: se pide `emb_<cid & 0xFF>`; con cid ≥ 256 comparte escudo con quien tenga ese
  byte. Es la única ruta que sigue truncando además del nombre.

### 6.4 La pared del calendario

Una liga nueva **no recibe fechas** por existir. El motor datea por id de regulación con un
`switch` sobre los ids de fábrica (2..175); una liga de id 176+ se queda sin fechas y la
temporada no arranca (cero partidos, solo "avanzar"). Las soluciones que hay en el proyecto:

- copiar el **dword de calendario** de una liga que funcione (lo hace `leaguebuilder`), y
- dar fechas propias desde el DLL: `rcal` (temporada real, día a día), `july` (adelanto),
  `dates <copa> like=<copa del juego>` (copas), `split_dates` (fases del split).

Un partido cabe en un registro de 16 huecos: por eso una jornada de 36 clubes (18 partidos) se
parte en dos jornadas de 9 en la fase suiza.

## 7. Desbloquear todo

### 7.1 Copas del juego que el menú no lista

El juego trae 21 copas con sus regulaciones y no las enseña. **No hay que crearlas: hay que
exponerlas**. En el world file basta una línea `ccup` con su cid y sus clubes:

```
ccup 49 ko=49 groups=0 entry=0:1236,0:2719,... clubs=1236,2719,... cid=49 fill=20 national=1 days=20,27,34,41 name=Argentina Cup
```

- `entry=0:<team>` = club explícito; `entry=<reg>:<pos>` = el que acabe en esa posición.
- `clubs=` es la lista que el sorteo usa cuando no hay tabla.
- **Cuidado con `like=`**: las 21 del juego tienen `type` 4, 8 o 9 (Spain Cup 4, Chile 8,
  Russia 9); ponerles `like=23` (forma de FA Cup) las bloquea. Por eso se quitó de esas líneas.

### 7.2 Ligas y competiciones ocultas

`slot=123` en la línea `league` deja la competición jugable pero **fuera de Select Team**; es el
mecanismo para tener ligas que alimentan copas sin llenar la lista. `serve=<slot>` intenta
prestarle un grupo del juego a una liga nuestra: **crashea el arranque** (`0x14d6aa0`, el insert
ordenado de la lista de clubes) si el slot lo llena también el exe.

### 7.3 cid por encima de 255

Con `fl26cid16` (tabla plana) una liga o copa con cid 256..1023 tiene lista de clubes propia.
Sin él, solo hay **12 bytes bajos libres** (1, 37, 45, 46, 47, 70, 71, 72, 86, 97, 103, 227), o
sea techo de 12 ligas de cid propio. El **emblema** sigue yendo por byte bajo.

### 7.4 Menú de copas

`fl26swiss` entrega al DLL las líneas `ccup` (hoy 168, 151 aceptadas), `fl26cupgrow` da 256
filas al desplegable y `fl26comptab` crea una fila oculta por copa y sube el tope de filas a 1200.
Resultado actual: **`167 world cup(s) added, all in (list 175 of 256)`**, menú abre y lista.

### 7.5 Lo que falta para "todo" (estado real)

1. **Nombre y sorteo de las copas con cid ≥ 256.** El menú resuelve por `phkind` (`0x14150af30`),
   que busca `dword[registro+0x80] == cid` y ese campo solo tiene el byte bajo; cuando no
   encuentra, cae a la competición 1 (FIFA Club World Cup), que no tiene sorteo → cierre al
   entrar. Falta localizar **la base real del array vivo** (los offsets `0xc12e9c`/`0xd0bcf4`
   dan un bloque con ids basura) o rellenar `+0x80` con el cid completo. Con eso caen nombre y
   sorteo a la vez.
2. **17 de 168 copas no las acepta el DLL** (`168 ... 151 accepted`): son las del juego con
   `type` 4/8/9.
3. **Emblemas** de cid ≥ 256: hoy comparten el del byte bajo.
4. Los nombres viven en `<idioma>/string/all.str` (WESYS + zlib, 208 entradas + pool UTF-8):
   añadir las 168 cadenas es el otro camino para el nombre, sin tocar el exe.

## 8. Receta para crecer el mundo (orden que funciona)

1. **Ids y sitios**: elegir cid (≤ 1023), regulación (≤ 1200), slot (≤ 250) y región (≤ 127)
   libres; comprobar con `python tools/limits.py`.
2. **Ligas**: `mkleague`/`leaguebuilder` (clonar prototipo, escribir las 3 filas).
3. **Copas**: `mkcup` (KO), `mkccup` (grupos + KO), `add_world_cups` (selecciones).
4. **Entradas**: posición 1..N por club; en copa, orden de sorteo.
5. **Calendario**: `rcal`/`july`/`dates` o el dword copiado; sin esto no hay partidos.
6. **Activos**: `mkcrests_missing`, `mkemblems`, `mkkits`, `mkflags` (256×256 RGBA para crests).
7. **Mundo**: escribir `fl26world.txt` en `livecpk\<mundo>\` **y** en `modules\` (idénticos).
8. **Verificar**: `check_world` (0 errores), `limits.py`, `setcheck.py`.
9. **Módulos en orden**: `fl26caps` → `fl26regs1200` → `fl26cid16`; `fl26swiss` → `fl26cupgrow`.

## 9. Herramientas por tarea

| tarea | herramienta |
|---|---|
| liga nueva | `mkleague.py`, `leaguebuilder.py`, `new_league.py` |
| copa KO | `mkcup.py`, `mkccup.py`, `make_carabao.py` |
| copa de grupos / continental | `mkccup.py`, `mk_conf_cup.py`, `mk_cwc.py` |
| split / apertura | `mksplit.py`, `mkphases.py` |
| fase suiza | `mkswiss.py` + `fl26swiss` |
| selecciones | `add_nation.py`, `add_nations.py`, `add_world_cups.py` |
| clubes genéricos | `generic_clubs.py`, `add_league_generic.py` |
| audit del mundo | `check_world.py`, `limits.py`, `calaudit.py` |
| topes | `limits.py`, `patchset.py`, `setcheck.py`, `lowertail.py` |
| escudos / emblemas / kits | `mkcrests*.py`, `mkemblems.py`, `mkkits.py` |

## 10. De dónde sale cada dato

- Offsets y bits de la regulación: parser `0x1414f7e80`–`0x1414f841f`, correlado con las 214
  filas de fábrica (`docs/research/research-findings.md` §2).
- Tipos y plantillas en uso: filas reales de `CompetitionRegulation.bin` (Escocia 133-136,
  Libertadores 9, Mundial 34/35).
- Formato suizo no expresable: `docs/research/league-phase-swiss-decode.md`.
- Topes: `python tools/limits.py` + `patches/layout.json` (medidos hoy).
- Estado del mundo y de las copas: `docs/developers/fork/estado-copas-2026-11-04.md`.
- Registro vivo (`+0x80`, `+0x84`, `+0x308`, stride `0x314`): `phkind` descompilado
  (`phkind.txt`) y sondas del DLL `fl26swiss`.
