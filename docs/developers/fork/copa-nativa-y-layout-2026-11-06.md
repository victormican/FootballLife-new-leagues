# Copa nativa vs copa nuestra, y el layout que bloquea el módulo (2026-11-06)

## 1. Champions League nativa (cid 2, clubes)

Fila de `Competition.bin` (36 B):

```
64 c8 00 08 00 02 22 00 "UEFA_CHAMPIONS_LEAGUE"
 ^area  ^id=2 ^flags=0x22   ^parent=0
```

19 regulaciones, todas con el mismo nombre:

| reg | tipo | teams | group | parent | para qué |
|---|---|---|---|---|---|
| 2 | 1 (playoff) | 16 | 255 | 0 | ronda previa |
| 3 | 2 (grupos) | 96 → 36 | 255 | 0 | fase de liga (maestra) |
| 4 | 3 (eliminatoria) | 16 | 255 | 0 | cuadro final |
| 1026, 2050, ... 8194 | 1 | 16 | 0..7 | 2 | una copia de la previa por grupo |
| 1027, 2051, ... 8195 | 2 | 96 | 0..7 | 3 | una copia de la fase de liga por grupo |

La clave: **cada fase real es una regulación maestra (parent 0) y cada grupo es una réplica con
`parent` = la maestra y `group` = índice**. El `+0x0a` es el grupo; el `+0x0b` los equipos (6 bits
bajos); el dword de formato en `+0x0c` (`57 41 09 c1` en la fase de liga, `57 61 01 02` en la
eliminatoria) es lo que la pantalla del sorteo lee para "tamaño del sorteo" y "formato".

## 2. Copa América nativa (cid 34, selecciones)

```
64 c8 00 c8 00 22 2c 00 "COPA_AMERICA"
                 ^flags=0x2c
```

5 regulaciones:

| reg | tipo | teams | group | parent |
|---|---|---|---|---|
| 43 | 3 (eliminatoria) | 8 | 255 | 0 |
| 104 | 2 (grupos) | 76 → 12 | 255 | 0 |
| 1128, 2152, 3176 | 2 | 76 | 0,1,2 | 104 |

Mismo patrón: maestra + una réplica por grupo, y una eliminatoria aparte.

## 3. Nuestra copa (`mkccup`, cid 50)

- Fila de competición **copiada de la Libertadores** (`flags 0x24`, `area 1`), no de una copa de
  clubes europea.
- `reg 300` tipo 2 grupos + réplicas `1324, 2348, 3372, 4396` (parent 300, group 0..3).
- `reg 301` tipo 3 eliminatoria (8 clubes de los 16).
- 16 entradas.

Diferencias con la nativa que explican que **no salga "tamaño del sorteo" ni el formato**:

1. La fila de competición no es la de una copa de clubes del juego (flags/area copiados de la
   Libertadores). La pantalla usa flags/area para decidir qué enseñar.
2. Las regulaciones no llevan el dword de formato nativo (`+0x0c`): `mkccup` copia la forma de la
   Libertadores/Europa, no la de la Champions.
3. `teams` de la fase de grupos: la nativa declara 96 (36 clubes, 6 bits) y las réplicas 76/96; la
   nuestra declara el número justo. El sorteo pide el tamaño de la nativa.

**Arreglo**: `mkccup --like` sobre la **Champions** (clubes) y sobre la **Copa América**
(selecciones): copiar la fila y las regulaciones maestras nativas y solo cambiar cid, nombre,
equipos y entradas. Así el sorteo y el formato salen solos.

## 4. El bloqueo real del módulo (por qué casca)

`fl26swiss.dll` lleva **offsets del bloque escritos a mano** (`0x2cfe6e0` = grupo, `0x2d1bbf0` =
su cuenta, `0x19115e4` = día). Esos offsets son de **otro build de `fl26caps`**. En esta
instalación:

- `fl26caps` aplica 45 parches y deja las tablas de fase en `0x4650 → 0xb34c`;
- `fl26slots750` deja 750 slots con counts en **+0x59b8c**, capacidades en `0x1634013c0` y listas
  en `0x163400800` (log de `fl26clubs`);
- el grupo y su cuenta no caen en `0x2cfe6e0/0x2d1bbf0`, así que el DLL lee fuera del bloque.

Arreglado ya el del día (`today_at` + `VirtualQuery`, commit `9b7d1e1`). Falta lo mismo para el
grupo y la cuenta: o se leen del **operando parcheado** del exe (la instrucción que nombra el
grupo ya lleva el desplazamiento bueno), o `fl26caps` publica el offset en una dirección fija que
el DLL lea al arrancar.

## 5. Plan 1-2-3

1. **Sacar el layout**: leer del exe parcheado los desplazamientos reales (grupo, cuenta, día,
   slots) con una firma por sitio, en vez de constantes.
2. **`fl26layout.h`**: generarlo con `tools/mklayout.py` desde `patches/layout.json` + las firmas,
   y compilar `fl26swiss.c` con esos valores.
3. **Recompilar y probar**: cargar, abrir Copa, ver sorteo con tamaño y formato, jugar un partido.
