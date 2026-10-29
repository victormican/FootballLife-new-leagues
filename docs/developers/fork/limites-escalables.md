# Como se escalan los topes (medido, 2026-10-27)

Este documento sustituye a la idea de "parchear a mano el exe". Los topes **ya estan subidos**,
pero no por codigo suelto: por un generador que verifica cada byte antes de escribir. Entender
esa cadena es lo que permite subir el siguiente tope sin romper el juego.

## 1. Estado medido (no estimado)

`python tools/limits.py` lee los topes de `patches/layout.json` y lo que hay de verdad en el
livecpk. Salida de hoy, con el livecpk `_FL26All` y el world vacio:

| tope | usado | limite | libre | fuente |
|---|---|---|---|---|
| jugadores | 120.666 | 123.825 | 3.159 | `layout.json` (`Player.bin`) |
| equipos | 3.802 | 4.800 | 998 | `layout.json` (`Team.bin`) |
| entrenadores | 1.078 | 6.800 | 5.722 | `layout.json` (`Coach.bin`) |
| regulaciones | 214 | 1.200 | 986 | `layout.json` |
| partidos del calendario | - | 65.000 | 65.000 | `layout.json` (rec596) |
| rondas (fixtures) | - | 8.000 | 8.000 | `layout.json` |
| clubes del Edit | 3.802 | 4.700 | **898** | `tools/native/fl26edit.c` |
| slots de Select Team | - | 250 | 250 | `fl26slots250.lua` |
| copas del menu | - | 512 | 512 | `fl26swiss.c` (`MAX_CCUP`) |
| ids de competicion | - | 511 | 511 | `fl26cid16.lua` |
| clubes por regulacion | - | **48** | - | estructural |

**El siguiente muro real es la lista de clubes del Edit (898)**, no los jugadores.

## 2. La cadena: de `layout.json` a `fl26caps.lua`

```
patches/layout.json          una sola fuente de verdad: donde vive cada array, su stride,
                             su cap viejo y su cap nuevo, y todas las direcciones que lo leen
        |
        v
tools/patchset.py <set>      desensambla cada direccion del exe, localiza el campo de 4 bytes
                             dentro de la instruccion y emite {va, old, new, why}
        |
        v
patches/<set>.json           el set completo, con el bloque nuevo y las bases nuevas
sider/fl26caps.<set>.lua     el aplicador (generado)
sider/fl26caps.lua           la copia que se instala
```

El aplicador es **todo o nada**: primero lee las ~3.500 direcciones y compara con los bytes que
el generador vio en el exe; si **una** no coincide, no escribe nada y el juego arranca sin
ningun tope. Eso es una red de seguridad, y a la vez el motivo de un fallo que costo dias:

> **Regla de oro.** Ningun otro modulo (ni DLL, ni otro Lua) puede escribir en una direccion que
> el set verifica. Si la pisa *antes*, el set aborta entero. Si la pisa *despues*, el set queda
> aplicado pero con una parte reescrita por el otro, y el resultado es un mundo a medias.

## 3. Por que el realojo de la tabla de jugadores rompia Edit (causa final)

El set **ya realoja** esa tabla: el bloque crece de `0x1877068` a `0x64D1D68` y la parte de
jugadores se sube de `+0xEE53D0` a `+0xFAD4D0` con **123.824 entradas** (`0x140af23b6`,
`0x140afd849`, `0x1412e67ff`, mas el contador `0xBA 30 75 00 00 -> BA B0 E3 01 00` en
`0x140af23cf`).

El experimento de `fl26swiss.c` escribia un `jmp` en `0xAF23B3`, que **pisa los bytes de
`0xAF23B6`** — la misma instruccion que el set mueve. Resultado: dos tablas de jugadores, una en
nuestro `VirtualAlloc` (la que veian las rutas que enganchamos) y otra en el bloque (la que veian
las otras diez). El juego saltaba a datos (`0x105EA0000 add [rax],al`), que es exactamente lo
que se veia en el depurador.

Conclusion: **no hay que realojar nada**. La tabla ya esta realojada, y por eso con la DLL del
commit (sin el experimento) el juego no se cierra.

## 3b. La cola baja: lo que el array de jugadores se comia (2026-10-27)

El array de jugadores empieza en `+0` y crece en sitio, asi que a partir de **66.918
jugadores** (`0x184c3bc / 0x17c`) empieza a escribir por encima de las estructuras que el
bloque guarda detras de el. Ese dia el cierre de Edit lo dejo claro:

```
0x1414d688b  mov eax, [rcx + rax*4]      ; c0000005, rax = 0x1324935
```

`0x1414d6870(obj, i, j)` devuelve `obj[base[i] + j]`, con `base[10]` en `+0x1d4c0` y
`count[10]` en `+0x1d4e8`; el llamador hace `lea r12, [rbx + 0x184db1c]`. El indice salia de
`base[]`, y `base[]` estaba en `bloque + 0x186afdc` — dentro del array de jugadores. Los
valores del volcado (`0x6C502033`, `0x72657961`, `0x20455547`) son **texto de nombres de
jugador** de `Player.bin`, no punteros.

Lo que hay en esa franja, medido con `tools/tailscan.py --lo 0x184c3bc --hi 0x1877068`:

| offset | que es | sitios |
|---|---|---|
| `0x184c3bc` | registro dummy de jugador (todo lookup fuera de rango cae aqui) | 105 |
| `0x184c538` | tabla de 8 bytes por entrada, llenada por el constructor | 7 |
| `0x184db1c` | conjunto de 10 grupos: `base[10]` y `count[10]`, total en `+0x1d510` | 41 |
| `0x186b030` | objeto con constructor propio (`0x1464` bytes, memsets del ctor del bloque) | 11 |
| `0x186c494` | objeto con constructor (`0x140b15630`) y destructor | 9 |
| `0x186cec8..0x1877068` | resto de la cola, incluido el campo de 8 bytes final del bloque | 133 |

`layout.json` ahora la declara como `block.lower_tail` y `tools/lowertail.py` genera la lista
(`patches/lower-tail-sites.json`, **306 sitios**): decodifica cada funcion y solo cuenta
operandos reales, porque una busqueda de bytes en esa franja da cientos de coincidencias
contra ~300 esperadas por azar. Al comparar los operandos encontrados con las apariciones
literales de cada valor en `.trace` salen exactamente iguales para los 20 valores mas
frecuentes, que es la prueba de que no queda ninguno sin mover. Dos operandos de
`0x141854f10` son falsos positivos y estan excluidos con su razon en el propio generador:
una tabla de bytes de `.trace` alcanzada por la base de la imagen y una mascara
(`and eax, 0x1870f98`).

El generador la coloca **la primera**, justo donde acaba el array de jugadores, y mueve los
306 operandos por **un solo delta** (`+0x1493704` en este set): la franja se traslada entera y
su disposicion interna no cambia. `impscan.py` no encontro ninguna copia de esos offsets en
`.impdata` (si que encuentra las de los arrays), asi que no hay nada virtualizado que se
quede atras — el unico valor que aparece alli, `0x1877060`, es una coincidencia de tabla que
el escaneo descarta porque ninguna puerta de `.impdata` decodifica hasta ella.

Reglas que se derivan de esto:

- la cola se mueve **sola** en cuanto `cap_new * 0x17c` pasa de `0x184c3bc`; no hay flag que
  activar ni lista que mantener a mano;
- cualquier set que suba el cap de jugadores por encima de 66.918 tiene que regenerarse
  entero: mover el cap y no la cola es exactamente el cierre de arriba;
- `python tools/setcheck.py` hace sin arrancar el juego la misma verificacion que el
  aplicador (3839 parches, 0 discrepancias) y `python tools/lowertail.py --check` dice si la
  lista de sitios sigue coincidiendo con el exe.

## 4. Muros duros (y por que lo son)

| muro | valor | por que no se sube con un parche |
|---|---|---|
| clubes por regulacion | 48 | la lista esta literalmente en `+0x170` con 48 handles; los grupos "Other" pintan 48 como maximo |
| copas del menu | 13 utiles | es un `std::vector` de heap del constructor del menu: hay que enganchar `reserve`/`push_back`, no reemplazar un puntero |
| lista de ids de entrenador | 1.300 | `+0x1d4c0` con 1.300 entradas de 4 bytes y su contador en `+0x1e912`: `0x1d4c0 + 1300*4 == 0x1e910`, la tabla termina dos bytes antes de su propio contador. Subirla escribe ids encima del contador |
| tabla de `upper2` | 30.000 | busqueda lineal de 8 bytes por entrada dentro del bloque; no crece sin sitio detras, asi que los jugadores por encima de 30.000 simplemente no estan (y eso es seguro) |
| array de jugadores | 123.825 | empieza en `+0` (los accesos no llevan desplazamiento): **crece en sitio**, no se puede realojar. Su techo es el primer campo del bloque que no se mueve, `0x16705a8` (tabla de ranking de clubes) |
| tabla de textos | ~70.844 ids | se enumera entera al entrar en Edit; un nombre con id mayor no existe y el hash se sale |
| competiciones del mundo | **255** | lo dice el contador de *My world*; cuenta **todo** (liga, copa y supercopa). El modpack de la copia va por **210 / 255** |
| paises nuevos | **99** | mismo contador; el `Country.bin` del juego ya trae 222 |

El techo historico del array de jugadores merece numeros: `0x16705a8 / 0x17c = 61.918`, menos de
la mitad del cap actual. El set esta en **123.825** porque se genero sin `--player-cap` (el
guardia solo salta cuando se pasa el argumento): el bloque crece y lo que se recoloca **va
despues** del array. Lo que hacia falta para que eso fuese seguro esta en el apartado 3b: la
franja `0x184c3bc..0x1877068` (dummy de jugadores, conjunto de grupos y objetos del final del
bloque) se traslada con ellos, asi que el array puede pasar de largo sin pisar nada suyo.

## 4b. Lo que dice el contador de *My world* (medido en juego, 2026-10-28)

La pantalla de *My world* lleva arriba su propio contador, y es la fuente mas directa porque
cuenta lo que el juego acepta de verdad: **hasta 255 competiciones** y **hasta 99 paises
nuevos**. En competiciones entra **todo** — cada liga, cada copa y cada supercopa —, asi que
una supercopa nueva gasta una de las 255 igual que una liga de 20 clubes. El modpack instalado
en la copia va por **210 / 255**: quedan unas decenas antes de chocar, no cientos.

Eso encaja con lo medido por otro lado (el id de competicion es un word y Select Team tiene 255
filas) y deja el techo real del mundo en **255 competiciones y 99 paises**, no en los 750
equipos del `layout.json`: los clubes sobran, lo que se acaba es el numero de competiciones.

`python tools/limits.py` imprime esos dos contadores en la misma tabla que los topes de
`layout.json` (`competiciones (My world)` = ligas + copas del world, `paises nuevos` =
`Country.bin` menos los 214 de la base), asi que el "siguiente muro" que anuncia ya es el
bueno y no los 898 clubes del Edit.

## 4c. Regla: Oceania y Non-FIFA siempre presentes (2026-10-29)

En **todo** mundo se reservan 2 competiciones fijas:

- **Oceania** (conf 7, 12 equipos OFC) — liga aparte, no dentro de Asia.
- **Non-FIFA Nations** (conf 6, 8 equipos: Martínique, Guadalupe, Guayana Francesa, San Martín, Sint Maarten, Bonaire, Cataluña, Padania) — con sus banderas en `flag_96..123.png`.

Coste: **2 de las 255 competiciones**. Límite efectivo para ligas del usuario: **253**.

### conf=6 (CONCACAF) en _FL26MyWorld: 12 ligas

| # | Liga |
|---|---|
| 1 | Liga Dominicana de Fútbol |
| 2 | Jamaican Premier League |
| 3 | Primera División Nicaragüense |
| 4 | El Salvador Primera División |
| 5 | Liga Panameña de Fútbol |
| 6 | Liga Nacional de Guatemala |
| 7 | Liga Nacional de Honduras |
| 8 | Primera División de Costa Rica |
| 9 | Mexican First Division |
| 10 | United States Soccer Leagues Division One |
| 11 | OTROS CONCACAF |
| 12 | Non-FIFA Nations |

### Límites restantes (tras Oceania + Non-FIFA fijos)

| Recurso | Límite | Usado (_FL26MyWorld) | Libre |
|---|---|---|---|
| Competiciones | 255 | 159 | 96 |
| Efectivo para ligas de usuario | 253 | 159 | 94 |
| Países nuevos | 99 | 0 (base 214) | 99 |
| Jugadores | 123.825 | 120.666 | 3.159 |
| Equipos | 4.800 | 3.802 | 998 |
| Entrenadores | 6.800 | 1.078 | 5.722 |
| Regulaciones | 1.200 | 214 | 986 |
| Clubes del Edit | 4.700 | 3.802 | 898 |

## 4d. Regla de mundo: bloques obligatorios (2026-10-29)

En **todo** mundo (nuevo o existente) se deben incluir estos bloques, sin borrar los del juego:

| Bloque | Contenido | Clubs | Conf | Notas |
|---|---|---|---|---|
| **Oceania** | 11-12 selecciones OFC como liga aparte | 11-12 | 7 | Separado de Asia (no dentro de Asia-Oceania). Ya creado con `mk_oceania.py`. |
| **Non-FIFA Nations** | 8 selecciones no-FIFA (Martínique, Guadalupe, Guayana Francesa, San Martín, Sint Maarten, Bonaire, Cataluña, Padania) | 8 | 6 | Con banderas en `flag_96..123.png`. Creado con `add_nonfifa.py`. |
| **Otros África** | Clubes ocultos + genéricos hasta completar 48 | 48 | 5 | `Otros CAF`: clubes ocultos + genéricos. |
| **Otros Concacaf** | 48 equipos | 48 | 6 | `OTROS CONCACAF`. |
| **Otros Asia** | Clubes ocultos + genéricos | hasta 48 | 3 | Crear si no existe. |
| **Classics** | Completar hasta 48 | 48 | — | `Classic Teams` del juego (no borrar). |

**Coste fijo**: Oceania (1) + Non-FIFA (1) = **2 competiciones** descontadas del total de 255.
Límite efectivo para ligas de usuario: **253**.

### Estado actual (_FL26MyWorld)

| Bloque | Estado | Clubs |
|---|---|---|
| Oceania | ✅ Creado (cid 91, slot 23) | 12 |
| Non-FIFA Nations | ✅ Creado (cid 255, slot 24) | 8 |
| Otros África (Otros CAF) | ✅ Existe (cid 165, slot 76) | 24 (falta completar a 48) |
| Otros Concacaf (OTROS CONCACAF) | ✅ Existe (cid 221, slot 158) | 24 (falta completar a 48) |
| Otros Asia | ❌ No existe | — |
| Classics | ✅ Del juego (no borrar) | — |

### Pendiente
- Completar Otros África y Otros Concacaf a 48 clubes (requiere rebuild con `mkleague clubs=48`).
- Crear Otros Asia.
- Completar Classics a 48.
- Verificar en juego que Oceania y Non-FIFA aparecen en Select Team.

## 5. Como se sube cada tope (receta)

Todos los de `layout.json`:

```powershell
# 1. editar patches/layout.json: arrays.<nombre>.cap_new (y cap_old si el de partida cambia)
# 2. regenerar el set completo (tarda unos minutos: desensambla el exe entero)
python tools/patchset.py teams-coaches-regs-players-dates-matches-upper-mlcopy-fixtures-calendar
# 3. comprobar el diff y que el tamano del bloque es el esperado
git diff --stat patches sider
python tools/setcheck.py          # la misma verificacion que hace el aplicador, sin arrancar
# 4. instalar y arrancar: el log dice "applied all N patches" o "MISMATCH ... nothing written"
copy sider\fl26caps.lua "<juego>\SiderAddons\modules\fl26caps.lua"
```

Reglas que el generador hace cumplir y que hay que respetar al elegir el numero:

- el bloque solo puede crecer en multiplos de `0x80` (el `memcpy` de la copia de seguridad es un
  bucle desenrollado con cola fija de `0x68`);
- las bases de los arrays se alinean a 16;
- el cap de jugadores tiene que ser **17 mod 32** (las colas de `memcpy` de la tabla empaquetada
  de la copia de modo: `0x9c` por jugador);
- el array de equipos que crece mueve **todo** lo que tiene encima en la copia A (y su tamano
  de objeto), y ademas su array lateral de `0x10` bytes por equipo.

Los que **no** estan en `layout.json`:

| tope | donde | como |
|---|---|---|
| clubes del Edit 4.700 | `fl26edit.c` (`TEAMS`), accesor en `0x1EF21D0` (`mov eax,0x2EE;ret`) | constante del modulo + el accesor se parchea desde el propio modulo |
| slots 250 | `fl26slots250.lua` | tabla del menu copiada y repuntada (`fl26comptab`), sin tocar el bloque |
| copas 512 | `fl26swiss.c` (`MAX_CCUP`) | constante nuestra; el limite real es el vector del menu |
| cids 511 | `fl26cid16.lua` | 3 sitios en sitio + 2 cuevas; ids en `Competition.bin +0x20` como palabra |
| clubes por regulacion 48 | `fl26clubs.c` (`MAX_CLUBS`) | estructural, no se sube con datos |

## 6. Que NO hacer (aprendido a base de cierres)

1. **No** parchear a mano una direccion del set desde otro modulo (rompe el todo o nada o deja
   dos copias de la estructura).
2. **No** subir un `cmp` de capacidad sin mover el array: se lee el array siguiente.
3. **No** fiarse de un offset "que funciona hoy": `0xE63DE4` se reescribe en runtime por
   `fl26caps` a `0x6475C08`; la firma tiene que ir por **opcode**, nunca por el desplazamiento.
4. **No** borrar competiciones del juego para hacer sitio: el menu se queda en blanco (ya paso).
5. **No** dar por bueno un arranque sin leer `sider.log`: si el set aborta, todo lo demas sigue
   arrancando y el fallo aparece mucho despues, lejos de la causa.
