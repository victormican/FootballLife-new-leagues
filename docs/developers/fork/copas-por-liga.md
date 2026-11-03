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
| `cid` | **1 byte**, 249 usados de 255 → **6 libres** (48, 96, 250-253) | 6 copas más, ni una más |
| fase de grupos | > 32 clubes | esa copa **no** sale en Kick Off > Cup |
| `fl26chain` | `MAX_CUPS = 128` | tope de copas encadenadas a ligas |
| entradas | obligatorias | sin `CompetitionEntry` la copa se abre vacía |
| lista del menú | se agranda sola | no es el cuello de botella |

El `cid` de 255 no es del ejecutable (en memoria es un word y el array tiene 600 registros): es de
las tres tablas, que lo guardan en un byte, y de la clave de las entradas
(`id << 8 | plaza-1`). El parche a 16 bits está mapeado en
[docs/research/competition-id-16-bit.md](../../research/competition-id-16-bit.md) pero no hecho.

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
