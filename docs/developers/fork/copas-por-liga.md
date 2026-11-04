# Copas para las ligas, y cómo aparecen en Kick Off > Cup

Investigado el 2026-11-03 sobre el mundo vivo (249 competiciones, 10 copas). Resumen: **la copa se
construye sin programa nuevo** (`tools/mkccup.py` copia la forma de una copa del juego) y **aparece
sola en el menú de copas** porque `fl26swiss` añade a la lista los `cid=` de las líneas `ccup`. El
límite no es el menú: es que **cada copa gasta un `cid` y solo quedan 6**.

## Qué es una copa en los datos

Una copa son cuatro cosas, exactamente como una liga:

| pieza | dónde | qué lleva |
|---|---|---|
| competición | `Competition.bin` (36 B) | `cid` en +5, región en +3, código en +8, nombre en +0x14 |
| fase | `CompetitionRegulation.bin` (2352 B) | `rid` en +2, `cid` en +8, **tipo** en +9 (2 grupos, 3 eliminatoria), `clubes` en +0x0B |
| clubes | `CompetitionEntry.bin` (12 B) | club en +0, `cid` en +8, plaza en +9 |
| calendario y forma | `fl26world.txt` | una línea `ccup` por copa |

La línea que lo une todo (la del Campeonato Paulista, que ya funciona):

```
ccup 260 ko=260 groups=0 entry=0:1247,0:137,... cid=229 fill=15 national=1 days=20,27,34
     clubs=1247,137,... like=23 name=Campeonato Paulista
```

- `ccup <reg>` = regulación de la fase de grupos (o la única si no hay grupos);
- `ko=<reg>` = regulación de la eliminatoria; `groups=<n>` = cuántos grupos de cuatro (0 = solo
  eliminatoria);
- `entry=<reg>:<plaza>` = de qué liga y qué puesto sale cada club (`reg 0` = plaza literal por
  `clubs=`);
- `clubs=<team id>,...` = invitaciones fijas (mismo número que el cuadro, o se descartan);
- `cid=<cid>` = **la competición que se ofrece en Kick Off > Cup**;
- `like=<reg>` = la copa del juego cuya forma y fechas se copian (23 = FA Cup: un partido por
  ronda, con byes);
- `days=`, `fill=`, `national=1`, `alt=` los usan `fl26swiss` y `fl26comptab`.

## Cómo llega al menú de copas

`Kick Off > Cup` es `MenuModeCupSelect`. Antes de que el menú cuente sus opciones, `fl26swiss.dll`
hace dos cosas (`tools/native/fl26swiss.c`, `cupsel_handler`):

1. **Quita** las competiciones cuya fase de grupos pasa de **32 clubes** (`rec[0x30c] & 0x7f > 32`):
   por eso la Champions de 36 no se puede jugar en modo copa.
2. **Añade** las copas del mundo, un item de 12 bytes por `cid`, copiando uno existente para que el
   nombre y el escudo tengan plantilla. Si la lista no tiene sitio, la **agranda** con
   `VirtualAlloc` (solo si el vector vive dentro del objeto, que es el caso): `Cup mode -- list
   enlarged from N to M entries`.

Los ids salen de los `cid=` de las líneas `ccup`: `fl26swiss.lua` los recoge y llama a
`fl26_swiss_cup_cids`. En el arranque se ve en `sider.log`:

```
fl26swiss: world file -- 10 cup(s) for Kick Off > Cup, 10 taken
fl26swiss: Cup mode: 10 competition(s) of the world to expose
fl26swiss: Cup mode -- N world cup(s) added, all in (list X of Y)
```

El campo que juega el modo copa son las **entradas** de `CompetitionEntry.bin` (por eso `mkccup`
las escribe): no hace falta una temporada de Master League. En una carrera, las mismas líneas
`ccup` hacen que `fl26swiss` llene la copa desde las tablas de las ligas, sortee los grupos y date
la eliminatoria.

## Receta: una copa de país

Con la liga ya hecha (por ejemplo Moldavia, `cid 85`, `reg 356`, 10 clubes):

```
python tools/mkccup.py --base "<pesdb>" --out "<livecpk>" --cup \
  "Cupa Moldovei|FL_MD_CUP|250|8468|8468|0|356:1,356:2,356:3,356:4,356:5,356:6,356:7,356:8|2|29|23"
```

Campos (`NAME|CODE|cid|reg|ko|groups|entry|conf|region|like`):

- `groups=0` y `reg=ko` → eliminatoria directa; `entry` con **8** plazas (el cuadro de la FA Cup
  admite 2, 4, 8, 16 o 32 y pone byes si no es potencia de dos);
- `conf=2` (UEFA) y `region=29` (la de Europa) para que no herede la confederación de la copa que
  se copia;
- `like=23` copia la forma de la FA Cup; sin `like` se copia la eliminatoria de la Europa League.

Con grupos, en cambio: `groups=4` y `entry` con 16 plazas (`reg` = grupos, `ko` = eliminatoria).

Después hay que **pegar la línea `ccup` que imprime** en `modules\fl26world.txt` y en
`_FL26MyWorld\fl26world.txt`, y validar:

```
python tools/fix_team_names.py --base "<pesdb>" --check
python tools/check_world.py --base "<pesdb>" --worldfile "<world>"
```

`check_world` comprueba que el `cid` y las regulaciones de la línea existen y que el número de
clubes coincide con las entradas: es la puerta que detecta una copa a medio hacer.

## Límites (medidos hoy)

| límite | valor | consecuencia |
|---|---|---|
| `cid` | **1 byte**, 250 usados de 255 → **5 libres** (96, 250-253) | 5 copas más |
| **lista del menú** | **13 items** (8 del juego + **5** nuestras) | las demás no se ven |
| fase de grupos | > 32 clubes | esa copa **no** sale en Kick Off > Cup |
| entradas | obligatorias | sin `CompetitionEntry` la copa se abre vacía |

### La lista del menú: 13 huecos (medido con Frida)

Capturado en vivo, el vector contiene items de 12 bytes `{cid, 0xffff, 0}`:

```
21 05 08 1b 24 22 23 25   (8 copas del juego)
e4 e5 e7 e8 e9            (nuestras: las 5 primeras líneas ccup)
```

`fl26swiss` añade las del mundo **en el orden del archivo** y se para al llenar:
`5 world cup(s) added, no room for the rest (list 13 of 13)`. El ensanche que trae el
módulo (`VirtualAlloc`) no actúa: el vector está en el heap y el código solo agranda si está
dentro del objeto (`the list is a heap vector, left alone`).

**Intentos de agrandarlo (2026-11-03), los dos tumban el juego:** envolver el `init` del menú
(`0x140b1c990`) con un stub que mueve la lista a un buffer de 64 items revienta al llamar a
cualquier asignador desde ese contexto — con el del ejecutable (`0x140227930`) cae en
`FL_2026.exe+0x3fd394`, con `ucrtbase!malloc` en `ucrtbase.dll+0xd50c`. La reserva de los 13
items ocurre **al arrancar** (la captura de `malloc` estando dentro del menú no ve ninguna), así
que el camino correcto es localizar en el constructor la constante `13` del `reserve` y subirla,
no asignar desde nuestro código.

**Dónde se construyen los items (encontrado el 2026-11-03):** hay un único sitio en todo el
ejecutable que escribe el centinela `0xffff` del item:

```
0x140b1c27c  mov qword [r9+4], 0xffff     (r9 = nodo de 0x1c bytes, cid en +0, byte 0 en +0xc)
```

junto a dos ayudantes (`0x140b1c240` y `0x140b1c290`) que crean el nodo con el cid leído de la
tabla. Es la estructura `{cid, 0xffff, 0}` que devuelve el menú.

**La lista nace vacía en el constructor base** (`0x140c6a540`):

```
0x140c6a5cc  lea rdi, [r13 + 0x90]
0x140c6a5d7  mov [rdi], r15                ; begin = 0
0x140c6a5da  mov [rdi+8], r15              ; end   = 0
0x140c6a5de  mov [rdi+0x10], r15           ; cap   = 0
```

No hay `reserve(13)`: la capacidad aparece entre ese constructor y el momento en que `fl26swiss`
añade las copas, y los 8 items iniciales los decide antes de que corra el `init`. Los dos
`mov edx, 0xd` de `0x140b1a955` son **búsquedas de un id 13**, no una reserva.

**Intentos de agrandarla (2026-11-03), todo medido en juego:**

| intento | resultado |
|---|---|
| Enganchar el `init` y ensanchar en un tick | no se ejecuta: el hook ya corre dentro del `init` |
| Stub en el `init` que mueve la lista antes de `fl26swiss` | revienta al asignar (`FL_2026+0x3fd394`) |
| Stub en el `init` con `ucrtbase!malloc` | revienta (`ucrtbase+0xd50c`) |
| Stub en el **constructor** (`0x140b1c6f0`) con buffer de `ucrtbase` | **se ven todas las copas**, cae al cerrar: el destructor libera el buffer con su asignador (`FL_2026+0x3fd5db`), heap distinto |
| Stub en el constructor con el asignador del juego | **cuelga el arranque**: no está listo cuando carga Sider |
| Frida, hooks de asignación (attach y spawn) | dispara (62 MB al arrancar) pero **ninguna reserva de 156 B**; `spawn` de `FL_2026.exe` pelado muere a los 10 s; spawn gating no existe en Windows |

**Queda:** buffers de `VirtualAlloc` (seguros) + **anular el `free`** de la lista en el destructor.
Los `call` a la IAT del CRT (free `0x15b9601a8`, malloc `0x15b9601b0`, calloc `0x15b9601a0`,
realloc `0x15b9601b8`) **no son `FF15`/`FF25` directos**: van por thunk, así que hay que seguir el
`jmp` del thunk hasta el sitio que llama al `free`. Con eso: capacidad 64 y las 19 copas sin caídas.

Mientras no se haga, **las 6 primeras líneas `ccup` del mundo son las que se ven**: hoy Copa
Sudamericana, Gold Cup, OFC Nations, OFC World Cup Qualifying, UEFA Nations League y CONCACAF
Nations League.

**Pila capturada (2026-11-03, attach + breakpoint en los ayudantes):**

```
0x140b1cd2d   dentro de 0x140b1cc60   (recorre la lista y mete cada item en el mapa)
0x140b1c9a6   init del menú 0x140b1c990 + 0x16
0x7ffe72ec55a6  handler de fl26swiss.dll
0x140e43462 · 0x1401fa111d · 0x140149fdf2 ...
```

`0x140b1cc60` **no reserva**: recorre `[self+0x90]..[self+0x98]` y por cada item (divide por 12 con
la magia `0x2AAAAAAAAAAAAAAB`) llama a `0x140b1cda0` y `0x140b1c290`/`0x140b1c540` para insertarlo
en el contenedor de `+0xd0`. La lista ya tenía los 8 items antes de que corra el init, así que quien
la llena y reserva **no está en esta pila**: es el código que prepara el menú antes de llamar a su
vtable (o el propio constructor del objeto, que no toca `+0x90`).

**Siguiente paso exacto:** breakpoint en el **constructor del menú** (`0x140b1c6f0`, el que escribe
la vtable en `[rdi]`) y, desde ahí, en el primer escritor de `[self+0x90]`; o buscar la tabla de
cids de las 8 copas del juego (no es un array de dwords consecutivos: no aparece en `.rdata`) para
llegar a su lector. Con eso se ve el `reserve` y basta cambiar su constante.

Mientras no se haga, **las 5 primeras líneas `ccup` del mundo son las que se ven**: hoy
Leagues Cup, Cupa Moldovei, Oceania, Selecciones No FIFA y Carabao Cup.

## «Una copa para cada liga»: el presupuesto

Hay **146 ligas** en el mundo y **6 `cid` libres**. Una copa por liga no cabe, y no hay truco:
dos copas no pueden compartir `cid` (compartirían competición, entradas y nombre; serían fases de
la misma copa). Las salidas, por orden de coste:

1. **6 copas ahora** con los `cid` libres (48, 96 y 250-253): elegir los seis países que más se
   jueguen. Es lo único que no toca nada existente.
2. **Reciclar una competición que no se use** para liberar su `cid`: se borran fila, regulaciones,
   entradas y línea del mundo (como se hizo con la Copa Argentina, `cid 48`). Las 12 competiciones
   sin clubes son del motor (`_MATCH`, `YOFF`, `RLD_CUP`…), no se pueden tocar.
3. **Una copa por confederación** alimentada con `clubs=` (invitaciones): una sola competición puede
   llevar clubes de muchas ligas, así que 6 copas cubren las 146 ligas aunque no sean «la copa de
   cada país».
4. **Terminar el parche de `cid` a 16 bits**: entonces el presupuesto pasa a 1023 competiciones
   (clave de entrada con `id << 6`) y el límite real sería el array de 600 registros.

Ojo con la forma: una copa de 48 clubes con **fase de grupos de 4** se puede jugar en el modo copa,
pero una con grupos de 36 (el formato suizo nuevo) queda fuera del menú.

## Prueba

1. Crear la copa con `mkccup.py`, pegar la línea `ccup` en los dos `fl26world.txt` y validar.
2. Arrancar con `FL 2026 start.exe`.
3. En `sider.log`: `world file -- N cup(s) for Kick Off > Cup, N taken` y
   `Cup mode -- 1 world cup(s) added, all in`.
4. **Kick Off > Cup** → la copa aparece por su nombre al lado de las del juego; elegir club y jugar
   la primera ronda.
