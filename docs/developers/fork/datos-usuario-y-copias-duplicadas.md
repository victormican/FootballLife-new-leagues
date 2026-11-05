# Datos de usuario y copas duplicadas (2026-11-06)

## 1. "Datos de usuario" al arrancar (caso conocido)

Tras añadir 74 clubes y renombrar 135, el juego volvió a quejarse de los **datos de usuario**. Es
el caso que ya está documentado en el vault (entrada 269): **`EDIT00000000` del mundo viejo tiene
prioridad sobre las tablas**.

El módulo `fl26edit` reparte el trabajo así: los **primeros 749 clubes** van al
`EDIT00000000` normal y **los nuestros** (los que pasan de 749) a `EDIT00000000.fl26x`. Cuando el
mundo cambia mucho, ese `.fl26x` queda desfasado y el juego canta el error.

**Arreglo aplicado** (el mismo de la vez anterior): apartar los ficheros para que se regeneren.

```
Documents\KONAMI\eFootball PES 2021 SEASON UPDATE\2026\save\EDIT00000000       -> .before-rebuild-20261106
Documents\...\2026\save\EDIT00000000.fl26x                                     -> .before-rebuild-20261106
D:\SP Football Life 2026 - copia - copia\dataSP\EDIT00000000                   -> .before-rebuild-20261106
```

Al arrancar, el juego crea unos nuevos; el mundo (clubes, ligas, copas) vive en las tablas y no se
pierde. Lo que se pierde son las ediciones hechas **desde el modo Edit** que solo estaban en ese
fichero.

Comprobado: arranca y `fl26edit` reconstruye sus tablas.

## 2. Copas duplicadas: 271 → 533

Con `tools/dup_cups.py` (duplica las copas de eliminatoria directa: competición, regulación,
entradas y línea `ccup` con sufijo):

```
straight-knockout cups to duplicate: 263
planned: 262   (Copa Intercontinental se salta: no tiene entradas)
written: 262 cups duplicated
```

| | antes | ahora | tope |
|---|---|---|---|
| competiciones | 496 | **758** | 1.023 |
| regulaciones | 691 | **953** | 1.200 |
| líneas `ccup` | 271 | **533** | — |
| filas del menú | 271 | **533** | **1.024** |
| entradas | 5.547 | **7.280** | — |

Para que quepan se subieron los dos topes de menú:

- `fl26cupgrow.lua`: `WANT` 512 → **1024** y el stub `lea rcx,[r11+0x1800]` → **`0x3000`**
  (12.288 B = 1.024 filas por buffer; 16 buffers).
- `fl26swiss.c`: `MAX_CCUP` y `MAX_CCUP_FWD` 512 → **1024**.

Arranque:

```
fl26swiss: world file -- 533 cup(s) for Kick Off > Cup, 533 taken
fl26cupgrow: 16 buffers of 1024 items; vtable wrapped ... destructor neutralised
check_world: 0 errores (3.648 equipos, 103.722 jugadores)
```

Las copias conservan el `like=` y las entradas de la original, así que se datean igual y llevan su
mismo cuadro; el nombre lleva el sufijo ` II`.

## 3. Lo que queda

- **Copas de grupos** (8 de las 271): no se duplican con este método (maestra + réplicas + KO).
- **Nombres**: la copia hereda el problema del cid ≥ 256 en el menú (nombre y sorteo) mientras no
  se cierre el `+0x80`. El DLL desplegado es la build A/B **sin escritura**.
