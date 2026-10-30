# Crear una selección, un club, una liga y una copa (método REA)

2026-10-29. Guía de campo: qué tablas hay que escribir, qué lee el motor de verdad y cómo se
comprueba con REA. Todo lo que aparece aquí está medido en este fork; las direcciones son RVA
(base del exe `0x140000000`, sin ASLR) y las herramientas son las del repo (`tools/`).

Léase con [re-arquitectura.md](re-arquitectura.md) (por qué el realojo de la tabla de jugadores
rompía Edit), [world-file.md](world-file.md) (gramática de `fl26world.txt`) y
[limites-escalables.md](limites-escalables.md) (topes y recetas para subirlos).

---

## 0. La idea en una frase

El juego **no tiene un editor de estructura**: una competición, un club y una selección son
filas en tablas binarias (`common/etc/pesdb/*.bin`, contenedor WESYS/zlib) más una línea de
texto en `fl26world.txt` que dice en qué hueco del menú se pinta. "Crear" = clonar una fila
válida, cambiar ids/nombres, añadir las filas dependientes (entradas, jugadores, entrenador) y
declararlo en el world file.

REA sirve para dos cosas:

1. **Descubrir** qué campo lee el motor y con qué límite (descompilar el lector, seguir xrefs).
2. **Verificar** que lo escrito es lo que el motor consume (volcar la tabla en runtime, mirar
   los readers, leer `sider.log`).

---

## 1. Las tablas y sus registros

Todas van en `livecpk/<mundo>/common/etc/pesdb/` y están comprimidas en WESYS
(`tools/pesdb.py`: `wesys_unpack` / `wesys_pack`).

| tabla | bytes/registro | campos (offset) |
|---|---|---|
| `Competition.bin` | 36 | `+0x00` 100/200 fijos, `+0x03` **región** (slot de país del menú), `+0x05` **cid**, `+0x06` flag, `+0x08` **código** (`ENGLAND_D1_LEAGUE`, `FL_XXXX`) |
| `CompetitionRegulation.bin` | 2352 | `+0x02` **id de regulación**, `+0x08` **cid**, `+0x09` **tipo** (4 liga, 3 eliminatoria, 2 grupos, 1 playoff), `+0x0b` **nº equipos** (6 bits bajos), `+0x0c` plantilla de formato (bits 12-17: 1 liga, 2 copa nacional), `+0x14` **nombre** 20 slots de `0x73` (10 + 10 desde `+0x4b2`) |
| `CompetitionEntry.bin` | 12 | `+0x00` **id de equipo**, `+0x04` id de entrada único, `+0x08` **cid**, `+0x09` **orden** (posición / siembra) |
| `Team.bin` | 1532 | `+0x00` **id de entrenador** (Coach.bin), `+0x08` **id de equipo**, `+0x46` **país** (9 bits desde bit 2), `+0x4f` nibble alto = grupo "Other…", `+0x53` bit alto = **selección**, `+0x170` **nombre** (70 B, 20 slots), `+0x372` **abreviatura** (3 B) |
| `Player.bin` | 312 | `+0x08` **id**, `+0x44` 4 slots de nombre de `0x3d`, nacionalidad en el bit 233 |
| `PlayerAssignment.bin` | 16 | `+0x00` id de entrada, `+0x04` **jugador**, `+0x08` **equipo**, `+0x0c` empaquetado: dorsal en los 10 bits bajos (`0x3ff`), orden de plantilla arriba |
| `Coach.bin` | 100 | `+0x00` **id**, `+0x04` nacionalidad (9 bits bajos), `+0x08` y `+0x36` nombre (46 B cada uno) |
| `Country.bin` | 1420 | primer dword: bits 10-18 = **id de bandera**; `+5` = **confederación** (2 UEFA, 3 AFC, 4 CONMEBOL, 5 CAF, 6 CONCACAF, 7 OFC); nombres 20 slots de 70 desde `+0x94`, inglés en `+0x120` |

Ids y topes vigentes en esta rama: equipo `< 81919` (NewLife usa 98304-114687), **4.800**
equipos, **123.825** jugadores, **6.800** entrenadores, **255** competiciones.

---

## 2. Cómo lo lee el motor (evidencia REA)

### 2.1 La tabla de competiciones del menú

El exe trae una tabla de **165 filas** en `0x1434FDF00`, stride `0x108`:

- `+0x00` id de competición, `+0x04` **slot**, `+0x30`/`+0x34` promote/demote.
- Se busca por id en `0x1414FDBDA`, por índice en `0x1414FDD71` y por rango en `0x1414FDE07`.
- `fl26comptab.lua` copia esa tabla, le añade nuestras filas del world file y **engancha las
  tres búsquedas**.

### 2.2 La lista de Select Team

- `count(slot)` = `0x1414D62C0`, `get(slot, i)` = `0x1414D6290`.
- Constructor de la lista: `0x1412FAC89` / `0x1412FB24E`, recorre **slots 0..249**.
- Un slot con lista no vacía y nombre se pinta.
- **El nombre que se ve sale de la regulación, no del world file.** (Por eso una liga con el
  nombre a medias sigue diciendo "Premier League".)

### 2.3 Los nombres de los grupos nacionales

Switch en `0x140EA08E0`, bytes de caso en `0x140EA0B3C`:

| caso | cabecera |
|---|---|
| 0 | Europe |
| 1 | Africa |
| 2 | North & Central America |
| 3 | South America |
| 4 | **Asia-Oceania** (AFC + OFC juntas) |
| 5, 6 | Classic Teams |
| 69, 71, 73, 75 | Other European / Other / Other Latin American / Other Clubs (Africa) |

**No hay sexta región nacional.** La agrupación es por slot, no por la confederación del país:
cambiar el nibble `+0x4f` de una selección no la mueve de grupo (medido 2026-10-24).

### 2.4 Copa vs liga en Select Team

Medido 2026-10-24: el motor solo rellena la lista de equipos de un slot si la regulación es
**liga** (`type` 4). Una copa (`type` 3) con slot es una competición con lista vacía y el
constructor la salta. Por eso "Oceania" se convirtió de copa a liga de selecciones
(`mk_oceania.py`).

### 2.5 Cup mode

`MenuModeCupSelect` (vtable `0x142692C40`), init `0xB1C990`, envuelto por `fl26swiss.dll`.
La lista está en `self+0x90` / `self+0x98`, items de 12 bytes con el cid en `+0`. El handler
quita las copas de más de 32 clubes en fase de grupos y **añade las copas del mundo** (líneas
`ccup`) mientras quede sitio en el vector.

### 2.6 El world file

```
league <reg> cid=<N> region=<R> country=<C> conf=<F> slot=<S> tier=1 promote=0 demote=0 clubs=<n> legs=<k> kickoff=<K> name=<texto>
ccup   <reg> ko=<reg> groups=<g> entry=... cid=<N> name=<texto>
```

- `slot` = hueco del menú; `-1` = que `fl26comptab` tome el primer slot libre 7..122.
- Un **abort** de `fl26comptab` (slot ocupado, dos regulaciones pidiendo el mismo slot) cancela
  **toda** la lista: síntoma "solo sale una liga".
- El fichero que lee el juego es `SiderAddons\modules\fl26world.txt`, no el del mundo.

---

## 3. Protocolo REA (cómo se descubrió todo esto)

1. **Abrir el binario** con REA (`open_binary`) sobre `FL_2026.exe`. Base `0x140000000`, sin
   ASLR: `RVA = VA - 0x140000000`.
2. **Buscar la cadena** que identifica el sistema (`search_strings`): códigos de competición,
   "Select Team", textos de cabecera. `xrefs` da las funciones que la usan.
3. **Descompilar** (`analyze_function`) esa función y leer los offsets que toca. Ahí salen los
   `+0x0b`, `+0x09`, `+0x46`… de las tablas.
4. **Confirmar el campo** de una de estas tres formas:
   - volcar dos registros de la tabla y comparar (el que cambia con el nombre es el nombre);
   - parchear un byte en una copia y ver el efecto en el menú;
   - breakpoint filtrado + `read_bytes` en runtime (REA/Frida) para ver qué valor pide.
5. **Medir el tope**: buscar el `cmp`/`mov` con la constante (`750`, `0x7530`, `4800`) y
   comprobar si es constante de código o campo de objeto (ver
   [limites-escalables.md](limites-escalables.md) §2 y §3).
6. **Verificar en juego barato**: `SiderAddons\sider.log` es el oráculo. Los módulos escriben
   ahí qué slot asignan, qué abortan y qué copas añaden.

Regla de oro: **no dar un campo por bueno sin verlo en una ejecución**. Un offset mal leído
cuesta una ronda entera de "no aparece" (pasó con `+0x4f` y con `0xAF23B3`).

---

## 4. Receta: un club

**Dependencias**: `Team.bin`, `Coach.bin`, `Player.bin`, `PlayerAssignment.bin`,
`CompetitionEntry.bin`, arte (kit/escudo) y, opcional, `UniformParameter.bin`.

1. **Elegir id**. Libre, ascendente, `< 81919`. Los ids del juego acaban en 71577 (Selangor FC);
   `mkteams.py` empieza en 71578. **La fila debe existir en el `Team.bin` base**, no solo en el
   bloque vivo: el guardado de Edit es un delta sobre el base y un club sin fila base no tiene
   de qué ser delta (por eso el realojo se perdía al recargar).
2. **Clonar la fila** con `tools/mkteams.py`: nuevo id en `+0x08`, nuevo "alt"/entrenador en
   `+0x00`, nombre en `+0x170` (20 slots) y abreviatura en `+0x372`.
3. **Entrenador propio**: `+0x00` es un id de `Coach.bin`. Si no existe, el juego muestra una
   copia del primer entrenador ("Jorge Jesus"). `tools/mkcoaches.py` añade un registro de 100 B
   por club con ese id, nacionalidad y nombre.
4. **Plantilla**: `tools/mkplayers.py` (o `grow_squads.py`) clona una plantilla real y escribe
   `Player.bin` + `PlayerAssignment.bin`. Sin jugadores el partido se pierde por incomparecencia.
5. **Kit y escudo**: `UniformParameter.bin` para los colores, texturas de kit y el escudo
   (`mkcrests.py` / `mkkits.py` / `kitpics.py`). Sin arte, el club sale con el kit del prototipo.
6. **Meterlo en una competición**: una fila de `CompetitionEntry.bin` con `cid`, `order` 1..n y
   un id de entrada único.
7. **Opcional**: nibble alto de `+0x4f` para el grupo "Other…" y línea `fans` en el world.

```powershell
python tools/mkteams.py --in <Team.bin> --out <livecpk\mundo> --count 2 --name "FL Club %02d" --abbr "F%02d"
python tools/mkcoaches.py <pesdb del mundo> --coach <Coach.bin shipped>
python tools/mkplayers.py --base <pesdb> --out <livecpk\mundo>
```

---

## 5. Receta: una selección

**Dependencias**: `Team.bin`, `Country.bin`, arte de bandera, `Player.bin`,
`PlayerAssignment.bin`, y una **liga** que la coloque en el menú.

1. **Fila de equipo con el bit nacional**: `Team.bin` `+0x53` bit alto a 1 (nunca en un club),
   país en `+0x46` (9 bits desde el bit 2), nombre y abreviatura.
2. **País**: `Country.bin` con id de bandera (bits 10-18 del primer dword), nombre en los 20
   slots y confederación en `+5`. Si el juego no tiene fila libre, se **añade** en un id de
   bandera libre (`add_nonfifa.py` lo hace).
3. **Bandera**: `common/render/symbol/flag/flag_<id>.png` a 128, `_l` a 256 y `_ll` a 512.
   Las que ya pinta el juego no necesitan arte. Si un PNG del livecpk no se ve, la hipótesis
   abierta es que para ese id manda el cpk base; la alternativa es inyectarlo en el cpk
   (no verificado todavía).
4. **Plantilla**: 23 jugadores clonados con nacionalidad = país (`add_nations.py`).
5. **Colocarla en Select Team**: una **liga** (`type` 4) cuyas entradas sean las selecciones, en
   un slot libre. Una copa no rellena el slot (§2.4).
6. **Grupo**: no se puede abrir una sexta región nacional; lo que se hace es una liga aparte
   ("Oceania") en un slot libre con `conf=7`, separada de Asia-Oceania.

```powershell
python tools/add_nations.py --base <pesdb> --countries <pesdb con Country.bin> --oceania
python tools/mk_oceania.py --base <pesdb> --worldfile <fl26world.txt> --countries <pesdb>
```

Ejemplo ya aplicado: `league 196 cid=91 region=25 country=200 conf=7 slot=<libre> clubs=12 legs=1 name=Oceania`.

**Bandera y selección no-FIFA**: `add_nonfifa.py` añade país + equipo + plantilla y deja las
filas listas; el PNG de bandera se mete a mano en `_FL26All/.../flag/`.

---

## 6. Receta: una liga

**Dependencias**: tres filas (`Competition`, `CompetitionRegulation`, `CompetitionEntry`) y una
línea `league`.

1. **cid libre** (`<= 255`; hoy es el recurso escaso) y **reg id libre** (por encima de la tabla
   de fechas si se quiere calendario propio).
2. **Competition.bin**: región del país (las del juego van de 8 en 8: 16 Inglaterra, 24 Francia,
   32 España, 40 Italia, 128 Brasil, 192 Japón; las nuevas, 29..127), cid, flag y código único.
3. **CompetitionRegulation.bin**: `type` 4, `nº equipos` en los 6 bits bajos de `+0x0b`, y el
   **nombre en los 20 slots** (si solo escribes el primero, se sigue viendo el nombre del
   prototipo). Los bits 12-17 de `+0x0c` son la plantilla de formato (1 liga).
4. **CompetitionEntry.bin**: una fila por club con `order` 1..n.
5. **World file**: `league <reg> cid=<N> ... clubs=<n> legs=<k> kickoff=<K> name=<texto>`,
   con `slot` libre (o `-1`).
6. **Calendario**: la liga necesita la plantilla de fechas de una liga que ya juega; se copia la
   regulación de un prototipo shipped (lo hace `mkleague.add_league`) en vez de inventar dwords.

```powershell
python tools/mkleague.py --base <pesdb> --out <livecpk\mundo> ^
    --cid 254 --reg 256 --region 160 --like "CHINA_D1_LEAGUE" ^
    --name "Otros Asia" --code FL_OTROS_ASIA_LEAGUE ^
    --teams 73723,73724,73725,...
python tools/check_world.py --worldfile <fl26world.txt> --base <pesdb>
```

`mkleague.py` **no inventa clubes**: recibe los ids con `--teams` (uno por entrada) y el
`clubs=` del world debe coincidir con esas entradas. Para generar clubes nuevos antes hay que
usar `add_generic_leagues.py` (clona un club con plantilla) o `mkteams.py` + `mkplayers.py`.

---

## 7. Receta: una copa

**Dependencias**: las mismas tres filas, pero con forma de copa, y (para jugarla) una línea
`ccup`.

1. **Clonar una regulación de copa shipped**, no inventarla: `BELGIUM_CUP` (cid 112, reg 122,
   bracket 16, 16 entradas), `CHINA_CUP` (cid 126, reg 127), `CUSTOM_CUP` (cid 37, reg 48, 16
   huecos y 0 participantes).
2. **`type` 3** y plantilla de formato bits 12-17 de `+0x0c` = **2** (copa nacional). Eso es lo
   que la distingue de una liga; el resto de la fila se copia entera.
3. **Bracket ≠ entradas**: el nº de equipos de la regulación es el tamaño del cuadro (p. ej.
   Coppa Italia = bracket 20 con 40 entradas porque las divisiones bajas entran después).
   `--bracket` lo fija aparte.
4. **Entradas**: el `order` es **siembra** ("dónde empieza en el cuadro"), no la posición liguera.
5. **World file**:
   - Para Master League: `ccup <reg> ko=<reg> groups=<g> entry=<cid:pos,...> cid=<N> name=...`
     y `fl26swiss` la rellena desde las tablas de las ligas.
   - Para **Kick Off > Cup**: la línea `ccup` con `cid=` basta; `fl26swiss` añade la copa al
     vector del menú (`Cup mode -- N world cup(s) added, all in`). Si el vector está lleno:
     `no room for the rest`.
6. **Calendario**: `mkcup.py` **no** pone la copa en el calendario (documentado sin probar). El
   camino probado es copiar la copa entera de un país que ya la juega, dword de calendario
   incluido.

```powershell
python tools/mkcup.py --base <pesdb> --out <livecpk\mundo> ^
    --name "FL Cup 01" --code FL_CUP_01 --region 2 ^
    --teams 72318,72319,... --bracket 16
```

---

## 8. Verificación

| qué | cómo |
|---|---|
| tablas coherentes | `python tools/check_world.py --worldfile <txt> --base <pesdb>` (compara `clubs=` con las entradas, ids repetidos, slots) |
| recuentos | `python tools/limits.py` / `newlife_limits.py` |
| slots y módulos | `Select-String sider.log -Pattern 'fl26comptab|fl26swiss|fl26clubs'` |
| parches aplicados | `applied all N patches` y `setcheck` 0 en `sider.log` |
| campo concreto | REA: volcar el registro antes/después, o `read_bytes` en runtime |
| en juego | Select Team (ligas), Kick Off > Cup (copas), Edit (clubes), ML (calendario) |

Lecturas típicas de `sider.log`:

```
fl26comptab: world file -- N leagues, M with a slot of their own
fl26comptab: slot 23 is already competition 4, not free -- aborting
fl26comptab: slot 124 asked for twice, by 254 and 256 -- aborting
fl26comptab: id 196 asked for a free slot -- it gets slot N
fl26swiss: Cup mode -- N world cup(s) added, all in (list X of Y)
```

Un `aborting` invalida **todo** el lote: hay que dejar el slot libre o usar `slot=-1`.

---

## 9. Límites y trampas

| trampa | efecto | arreglo |
|---|---|---|
| cid repetido o > 255 | la competición no entra | liberar un cid (borrar fila en las 3 tablas + línea del world) |
| slot ocupado o pedido dos veces | `aborting`: no se aplica ninguna línea | slot libre verificado o `slot=-1` |
| nombre solo en el primer slot de la regulación | se ve el nombre del prototipo | escribir los 20 slots |
| copa (`type` 3) con slot | slot vacío en Select Team | convertirla en liga (`type` 4) |
| región inventada | la liga carga pero no sale en ningún menú | usar una región shipped o 29..127 |
| fila solo en el bloque vivo | se pierde al recargar Edit | escribir siempre el `Team.bin` base |
| club sin `Coach.bin` | todos con el mismo entrenador | `mkcoaches.py` |
| club sin jugadores | derrota por incomparecencia | `mkplayers.py` / `grow_squads.py` |
| copa sin línea `ccup` | no aparece en Kick Off > Cup | añadir `ccup ... cid=<N>` |
| selección esperando grupo propio | no hay sexta región nacional | liga aparte en slot libre (Oceania) |
| mundo editado y no activado | el juego lee `modules\fl26world.txt` | copiar el world a `modules\` |

Topes vigentes: 255 competiciones (253 efectivas con Oceania + Non-FIFA fijos), 4.800 equipos,
123.825 jugadores, 6.800 entrenadores, 4.700 clubes en Edit. Los muros que quedan (1.300 ids de
entrenador, `TODAY_OFF`, `fl26edit`/`.fl26x`, ML en la pantalla de entrenador) están en
[limites-escalables.md](limites-escalables.md) §4.

---

## 10. Instalación real de un bloque (lo que faltaba el 2026-10-30)

Crear las filas no basta. Para que el bloque se vea:

1. **Activar el mundo**: en `SiderAddons\sider.ini`, `cpk.root = ".\livecpk\_FL26MyWorld"` **sin
   comentar**. Si está `#`, el juego corre datos vanilla y ninguna de tus filas existe. (Estaba
   comentado desde el bisect de "Datos del usuario".)
2. **world en `modules\`**: copiar `livecpk\<mundo>\fl26world.txt` a `SiderAddons\modules\`.
3. **`slot=-1`** en las líneas nuevas: `fl26comptab` les da un slot libre en runtime.
4. **`fl26comptab` corregido** (`6c3909c`): el pool de slots libres no debe incluir los slots que
   el propio world ya reclama (`APPEND`) ni los de `RESHAPE`, ni los "Other…" del exe
   (5/6/69/70/71/72/73/75) ni el 123. Sin eso, la petición de slot libre cae en el slot de otra
   liga y **aborta el lote completo**.
5. **Reiniciar Sider** (no solo el juego) al cambiar un `.lua` de `modules\`: Sider carga los
   módulos al arrancar.

Prueba en `sider.log`:

```
fl26comptab: id 196 asked for a free slot -- it gets slot 206
fl26comptab: table copied to 0x15c000000, 305 rows (165 shipped + 140 ours)
fl26clubs: world file -- 158 leagues, ...
```

Si en vez de eso sale `slot N asked for twice ... aborting`, arregla los slots antes de mirar el
menú: con un abort no se aplica **ninguna** línea del world.
