> **Superado en numeros por limites-actuales-2026-11-06.md.** Se deja como historico.

# Límites del mundo: estado y hasta dónde se puede subir (2026-11-05)

Foto de los topes con el mundo vivo (`_FL26MyWorld`) medido hoy, y para cada uno: cuánto queda,
si se puede subir, cómo y qué cuesta. Sustituye a las tablas sueltas de `limits-and-formats.md`
(23/10) y `limites-escalables.md` (27/10).

> `python tools/limits.py` mide por defecto el livecpk `_FL26All`, no el mundo vivo: sus columnas
> "usado" no son las de esta tabla. Los números de abajo salen de `check_world` y de leer las
> tablas del mundo vivo.

## 1. Lo que hay hoy

| recurso | usado | tope | libre | se sube con | ¿se puede más? |
|---|---|---|---|---|---|
| jugadores | 99.366 | **123.825** | 24.459 | `layout.json` → `patchset` → `fl26caps` | **sí**, hasta ~262.000 (ver 3.2) |
| equipos | 3.450 | **4.800** | 1.350 | idem | sí, pero antes el Edit (4.700) |
| entrenadores | 1.078 | **6.800** | 5.722 | idem | sí |
| regulaciones | 690 | **1.200** | 510 | idem + `fl26regs1200` | **sí**, 1.500-2.000 con el stub de recuento |
| competiciones (cid) | 495 | **1.023** | 528 | `fl26cid16` (tabla plana de 1.024) | sí, con tabla más grande (3.1) |
| entradas | 5.339 | 4.700 por club / sin tope global | — | — | sí |
| fixtures | — | **8.000** | 8.000 | `layout.json` | sí |
| partidos de calendario | — | **65.000** | 65.000 | `layout.json` | sí |
| clubes del Edit | 3.450 | **4.700** | 1.250 | `tools/native/fl26edit.c` | sí, es el siguiente muro real |
| slots de Select Team | 133 | **250** (0..249) | 117 | `fl26slots250` | **difícil** (ver 4.1) |
| regiones | ~101 | **127** | 26 | `fl26reg128` | **no** (campo de 7 bits) |
| filas de Kick Off > Cup | 271 | **512** | 241 | `fl26cupgrow` (hoy 512) | sí, a 1.024 con el mismo método |
| copas aceptadas por el DLL | 271 | **512** | 241 | `fl26swiss.c` (`MAX_CCUP`) | sí, es una constante |
| clubes por regulación (lista del censo) | 48 | **48** | 0 | `fl26clubs.c` | sí, es una lista del código |
| clubes por regulación (campo) | 48 | **63** | 15 | 6 bits en `+0x0B` | **no** sin ensanchar el campo |
| clubes por liga (calendario) | 38 | **38** | 0 | `BIG_LEAGUE_DAYS` | **no** sin fechas nuevas |
| clubes por liga con split | 20 | **46** | 26 | `SPLIT_MAX_ROUNDS` | sí, hasta 46 |
| id de club | 74.286 | **81.919** | 7.641 | `CLUB_ID_MAX` | sí, pero el handle da 16.381 |
| id de jugador | 260.545 | **262.143** | 1.598 | 18 bits del formato | **no**, es pared de formato |
| países (`Country.bin`) | 240 | 240 + 99 | 99 | `add_nation.py` | sí, +99 |

## 2. Cómo se sube una tabla (la cadena)

```
patches/layout.json      stride, cap_old, cap_new y TODAS las direcciones que leen el array
tools/patchset.py <set>  desensambla cada dirección y emite {va, old, new}
patches/<set>.json       el set completo
sider/fl26caps.<set>.lua el aplicador  ->  modules/fl26caps.lua
```

Reglas que ya nos costaron un mundo:

1. **Todo o nada**: si un byte no coincide, no se escribe nada.
2. **Ningún otro módulo puede tocar esas direcciones** (ni antes ni después).
3. Subir jugadores obliga a **regenerar el set entero** (la cola baja, 306 operandos).
4. Verificación sin arrancar: `python tools/setcheck.py` (3.839 parches) y
   `python tools/lowertail.py --check`.

## 3. Lo que sí se puede subir todavía

### 3.1 Competiciones (cid): 1.023 → 4.095 (o más)

La tabla plana de `fl26cid16` tiene 1.024 entradas y enmascara a `0x3ff`. El id cabe en 16 bits
tres veces (`Competition +7`, `Entry +0x0B`, `Regulation +0x492`), así que el límite no es el
dato: es la tabla y el **orden de entradas**, que hoy corta en 1.023. Subir a 4.096 = tabla de
4.096 punteros (32 KB, cabe en la cueva) + máscara `0xfff` + revisar el orden. Coste: medio.
Con 528 libres hoy no urge.

### 3.2 Jugadores: 123.825 → ~262.000

El tope de 123.825 es una elección de `layout.json`, no del formato. El formato empaqueta el id
en **18 bits** (262.143) y el array se indexa por id: con un id por jugador caben ~262.000
registros. Subir implica `cap_new` más alto + regenerar el set entero (mover la cola baja) +
vigilar memoria (cada jugador son 0x17c = 380 B: 262k son ~100 MB de bloque). Coste: alto.

### 3.3 Regulaciones: 1.200 → 2.000

`fl26caps` realoja el array (stride 0x314) y `fl26regs1200` arregla el recuento. El recuento se
escribe en sitio solo si `N` es múltiplo de 6 y `N/6` cabe en disp8 (N ≤ 762); por encima,
`mkregs.py --stub` pone un bucle plano propio. Con el stub, 2.000 es solo un número: coste bajo.
Ojo con `fl26caps` y el reset de filas (`N` filas se limpian al copiar de modo).

### 3.4 Equipos: 4.800 → 4.700 (Edit) y luego más

El tope que muerde antes es **el Edit** (`fl26edit.c`, 4.700), no `Team.bin` (4.800). El handle
del equipo aguanta 16.381. Subir el Edit es tocar su módulo; después, `Team.bin` a 6.000+ con el
set. Coste: medio.

### 3.5 Filas de copa: 512 → 1.024

`fl26cupgrow` ya pasó de 256 a 512 (WANT y el `lea rcx,[r11+0xC00]` → `0x1800`). El mismo cambio
a `0x3000` (1.024 filas) es mecánico; el ring tiene 16 buffers de `WANT*12` B (12 KB cada uno).
La guarda de espacio libre (`cmp r11,0x400`) sigue valiendo. Coste: bajo.

### 3.6 Slots de Select Team: 250 → más

El módulo reparte 324 clubes por slot dentro del bloque; el número de slots está limitado por el
espacio de ese bloque, no por un `cmp`. Subir a 300 exige mover/ampliar la zona (como se hizo con
la cola de jugadores). Coste: alto y con riesgo de romper listas.

## 4. Lo que no se puede sin ingeniería nueva

### 4.1 Regiones: 127

El slot de liga de un equipo vive en **7 bits** (`+0x41c & 0x7f`). 127 es el máximo del campo. Un
país nuevo tiene que compartir región con otro (hoy: 101 usadas de 127).

### 4.2 Clubes por regulación: 63

El número de equipos de una regulación son **6 bits** (`+0x0B`). El censo además tiene una lista
de **48** en `fl26clubs.c` (esa sí se puede subir: es código nuestro). El campo de 63 no.

### 4.3 Clubes por liga y calendario: 38

El calendario grande tiene **38 fechas** (`BIG_LEAGUE_DAYS`): una liga a una vuelta admite 38
clubes y a dos vueltas 20. Con split hay 46 fechas. Una liga de 40+ clubes necesita fechas
nuevas (y que el motor las acepte), no un `cap_new`.

### 4.4 Id de jugador: 262.143

18 bits del formato de `Player.bin` y del `PlayerAssignment`. No es un array: es el dato. Lo único
que se puede hacer es reutilizar huecos (lo hace `FL26_FREE_PLAYER_IDS=1`) y no desperdiciar ids.

### 4.5 El byte bajo del cid (nombre y emblema)

No es un tope de cantidad: el menú de copas y el emblema leen **un byte** del cid. Con cid ≥ 256
salen con el nombre/escudo de otra competición. Se está cerrando por el lado de la memoria: el
array de regulaciones está en `block+0xc131b0` y el cid completo va en `+0x80`
(`docs/developers/fork/regulaciones-en-memoria.md`).

## 5. Orden recomendado si hay que crecer

1. **Regulaciones a 2.000** (barato, y con 271 copas ya vamos por 690).
2. **Filas de copa a 1.024** (mecánico).
3. **Edit de clubes** de 4.700 a lo que pida el mundo.
4. **cid a 4.096** solo si el mundo pasa de 1.000 competiciones.
5. **Jugadores** solo si el mundo pasa de ~400 ligas de 30: es el cambio caro y con más riesgo.
6. **Slots** el último: es el que más se rompe y el que menos aprieta hoy (117 libres).

