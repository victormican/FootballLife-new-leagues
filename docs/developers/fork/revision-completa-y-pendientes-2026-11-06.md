# Revisión completa del mundo y pendientes ordenados (2026-11-06)

Revisión del mundo vivo de `_FL26MyWorld` (154 ligas, 286 `ccup`) después de la sesión de
slots 750, Otros OFC y las 15 ligas ocultas. Aquí están las cifras medidas, los cuatro fallos
abiertos con su evidencia, y la lista de pendientes ordenada por impacto y riesgo.

Todo lo de abajo se midió sobre los ficheros desplegados:

```
D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\common\etc\pesdb\
D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26world.txt
```

## 1. Inventario verificado

`python tools/check_world.py --base <livecpk>\common\etc\pesdb --worldfile <modules>\fl26world.txt`

```
teams 3648 (239 nacionales), players 103722, assignments 93338,
competitions 512, regulations 711, entries 5668
world file: 154 leagues, 152 slots (22..248), 286 ccup
0 error(s), 1 warning(s)
```

El aviso es de una copa del juego con dos clubes en la misma plaza (UEFA Champions League,
fase + eliminatoria): es del juego, no nuestro.

- 512 competiciones = **91 del juego intactas** + 421 nuestras. Las 91 conservan `code`, `area`,
  `flags` y `parent` byte a byte (`hijack.py` / `areadiff.py`: 0 diferencias).
- 711 regulaciones con **711 ids únicos** (1..9000): no hay duplicados.
- 5668 entradas sobre **499 cids**; los 13 cids sin entradas son copas del juego por fases
  (`entry=0` en su `ccup`) y las de práctica.
- 20 slots servidos por el DLL: `75<-181 69<-364 71<-256 73<-362 248<-470 80<-76 209<-9000
  84<-111 72<-178 77<-182 200..208<-900..908 247<-250`.
- `clubs=` del world **coincide con el número de entradas en las 154 ligas**. Es la única
  fuente fiable para saber cuántos clubes tiene una liga sin contar las fases de una copa.

## 2. Hallazgo estructural: cómo se leen de verdad los ids

Hasta hoy `tools/pesdb.py` leía mal dos cosas. Corregido en esta revisión:

| campo | lectura vieja | lectura buena |
|---|---|---|
| id de regulación | `+0x02` **1 byte** → ids falsos repetidos | `+0x02` **u16** (`id \| hi<<8`) |
| cid de la regulación | `+0x08` **1 byte** | `+0x08 \| (+0x492 << 8)` |
| cid de la entrada | `+0x08` **1 byte** | `+0x08 \| (+0x0B << 8)` |
| plaza de la entrada | `u32(+8) >> 8` (arrastraba el byte alto) | `+0x09` |

Consecuencia: los "234 ids de regulación duplicados" y los recuentos de entradas por cid
(Serie A 34, Bélgica 34) eran **artefactos de leer solo el byte bajo**. Los valores reales son
Serie A 20, Bélgica 16, Brasileño 4.ª 63, Copa Sudamericana 32.

Esto también cierra una duda abierta: `+0x492` **es el byte alto del cid**, no del id de
regulación. Por eso `mkccup.py` lo escribe en `R_CID_HI` y por eso el `ccup` de la
Sudamericana dice `192`/`193`: son sus regulaciones (maestra y eliminatoria), que existen una
vez cada una.

## 3. Los cuatro fallos abiertos

### 3.1 Listas de clubes cruzadas en "Información de la Liga" (el defecto visible principal)

Evidencia: Serie A (20 clubes) pinta 34; Danish 1. Division (12) muestra 9 estonios; NIFL (10)
2 malteses; Copa BetPlay Dimayor mezcla clubes de Uzbekistán/Kazajistán/Turkmenistán/Irán y
suizos; Yokary (8) 2 brasileños.

Lo que **sí** está descartado:

- Las entradas no están cruzadas: las 154 ligas tienen `clubs=` == entradas, y los únicos
  clubes nuestros dentro de competiciones del juego son intencionados (selecciones en el
  Mundial, Charlotte/Colorado en MLS, rellenos de Copa Argentina/Copa do Brasil/UEL).
- `rebuild()` del DLL lee bien: `slot 84 <- reg 111: 16 clubs`, y `clubs=` de las 20 líneas
  servidas == entradas en 19 de 20 (la excepción es Bélgica, ver 3.2). Otros Concacaf declara
  58 y sirve 58, por eso **no** se puede volver a `MAX_CLUBS 48`.

Quedan dos mecanismos, y hay que medir cuál es antes de tocar nada:

1. **Censo de Select Team por byte bajo.** `fl26cid16.lua` se despliega con
   `ENABLE = { cmp=false, cid=false, pack=true, reg=true, build=true, map=true }`: el mapa de
   1024 punteros está puesto, pero **la clave sigue siendo el byte bajo**. En el mundo, 170 de
   los 256 bytes bajos están compartidos por más de un cid, y **257 de nuestras 421
   competiciones (>255) colisionan** con otra. Pares medidos: byte 10 = cid 10 (Serie A) y 266
   (FL_SUP_266); byte 1 = 1 (FIFA CWC), 257 y 513 (Sudamericana); byte 111 = 111 (Bélgica),
   367 (OFC CL), 623 y 879.
2. **El panel no lee la lista del slot sino otra fuente** (p. ej. el array de regulaciones
   vivo, stride `0x314`, donde el motor reutiliza el registro y no limpia los 48+ huecos de
   clubes). En ese caso el corte tiene que ser por contador declarado, no por terminador.

Medida que decide: abrir la pantalla de una liga *no servida* (Serie A) y una *servida*
(Danish), y volcar con el DLL qué slot/reg y qué handles se leen en cada caso.

### 3.2 Bélgica sigue mostrando 1 equipo

El dato es correcto: 16 entradas, `slot 84 <- reg 111: 16 clubs`, handles que decodifican bien.
La regulación 111 es `type 9` (split) y declara **18** clubes (`teams & 0x3f`) frente a 16
entradas: es la única línea servida con esa discrepancia.

La lista se arregla al segundo intento (`select_team_retry.ps1`), así que el fallo está en la
**primera** respuesta del par count/get, no en `rebuild()`. Hipótesis: el censo pregunta antes
de que la regulación esté cargada, `rebuild` devuelve 0, el juego usa su lista guardada de ese
slot (1 club) y no vuelve a preguntar. Falta instrumentar `count_hook`/`get_hook` (slot, idx,
n, valor devuelto) en las primeras 20 llamadas del slot 84.

### 3.3 Copa Sudamericana: no pisa una copa del juego

Comprobado: `cid 513`, regulaciones **192** (grupos, 8 réplicas en `192 + 1024·k`) y **193**
(eliminatoria), 32 entradas. Las tres existen y son suyas. Lo que colisiona es el **byte bajo
1**: el emblema se pide como `emb_<cid & 0xFF>`, así que sale el trofeo del FIFA Club World
Cup (cid 1). No es un secuestro de fila; es la misma colisión de byte bajo del punto 3.1.

### 3.4 "Estructura de campeonato" no lista las ligas nuevas

Sin medir. No hay que suponer qué tabla lee: hay que abrir la pantalla con el mundo actual y
volcar qué registro se consulta (censo, `Competition.parent`, o una tabla fija de Liga Master).
Si solo lista competiciones del juego, se documenta como límite y no se fuerza.

## 4. Pendientes ordenados

### P0 — parar la contaminación (antes de tocar nada más)

1. ~~Medir qué lista pinta "Información de la Liga"~~ **HECHO (2026-11-06).** El panel no lee
   el array vivo (en esa pantalla el bloque está sin cargar: 0 jugadores, 0 equipos, 65535
   regulaciones) sino las tablas pesdb, y el censo junta las entradas de todo cid que comparte
   byte bajo, en el orden `cid << 6 | plaza-1`. Medición y evidencia en
   `informacion-de-la-liga-censo-2026-11-06.md` (Sudamericana 513←257, Yokary 359←615, NIFL
   63←319, Danish 327←839). Es la causa (a).
2. **Es el censo: probar `cid = true`** en `sider/experimental/fl26cid16.lua` (A/B con el
   juego cerrado, una sola pantalla) y, si casca, mover las ligas que importan con
   `tools/move_cids.py --free` (solo 12 bytes bajos libres: 1, 37, 45, 46, 47, 70, 71, 72, 86,
   97, 103, 227; 37 y 86 son la copa/liga personalizadas del juego).
3. **Si es el array vivo:** pasar `clubs=` del world al DLL y cortar `rebuild()` en
   `min(clubs, MAX_CLUBS)`; `MAX_CLUBS` se queda en 96 (Otros Concacaf necesita 58). Cambia el
   ABI `fl26_clubs_cfg_t` (añadir `uint16_t clubs`) y hay que recompilar con
   `zig cc -shared -target x86_64-windows-gnu -O2 -s`.
   Aceptación: Serie A 20, Danish 12, NIFL 10, Yokary 8, Copa BetPlay solo sus clubes.

### P1 — Select Team

4. **Bélgica a la primera.** Instrumentar el par count/get del slot 84 y precargar/invalidar la
   lista al cargar la regulación. Aceptación: entrar una vez y ver 16, sin reintento.
5. **Revisar los 20 servidos** con la misma sonda: que el primer `count` devuelva el número de
   `clubs=` en todos.

### P2 — cids ≥ 256 y copas

6. **Emblema de competiciones con cid ≥ 256.** O se parchea la búsqueda a 16 bits, o se eligen
   cids con byte bajo libre para las copas visibles (la Sudamericana es la primera).
   Aceptación: Sudamericana con su trofeo y una sola entrada en el menú.
7. **"Estructura de campeonato".** Medir la tabla que lee; si es fija, documentar el límite.

### P3 — datos y limpieza

8. **Nombres de "Otros latinoamericanos" (reg 362) y Dinamarca (reg 904 / cid 327)**; revisar
   también los 52 desajustes `teams & 0x3f` vs entradas (casi todos copas del juego por fases).
9. **Documentación:** este documento manda sobre `estado-y-escalado-2026-11-05.md` para el
   estado actual; `pendientes-2026-11-05.md` queda superado por la lista de arriba.

## 5. Cambios de esta revisión

- `tools/pesdb.py`: id de regulación y cid leídos a 16 bits; `slot` de la entrada sin el byte
  alto del cid. Añadidos `id_lo`, `id_hi`, `cid`.
- `tools/check_world.py`: el texto de ayuda decía "at most 255"; el límite real que vigila es
  1023.
- Verificado: `check_world` sigue en **0 errores** con el mundo actual; los recuentos por cid
  pasan a los valores reales (Serie A 20, Bélgica 16, cid 513 = 32).
