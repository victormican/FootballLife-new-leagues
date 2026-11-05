# El array de regulaciones en memoria (REA, 2026-11-05)

El pendiente del nombre de las copas necesitaba una cosa: dónde están **de verdad** las
regulaciones en memoria. Estaba mal anotado y por eso las sondas leían basura.

## Lo medido

`0x1414bc0a0` es el recuento que corre tras cada copia de modo. Descompilado con Ghidra, recorre
**cuatro** arrays y los cuenta en cuatro campos seguidos del mismo bloque (`param_1`):

| array | base en el bloque | stride | tope viejo | cuenta en |
|---|---|---|---|---|
| jugadores | `+0x2c` | `0x17c` | `0x7531` (30.001) | `+0xd0bce8` |
| equipos | `+0xadf4bc` | `0x690` | `0x2ee` (750) | `+0xd0bcec` |
| entrenadores | `+0xc4ca0c` | `0x258` (600) | `0x514` (1.300) | `+0xd0bcf0` |
| **regulaciones** | **`+0xc131b0`** | **`0x314`** | 300 (6 × 50) | **`+0xd0bcf4`** |

El de regulaciones va **seis registros por pasada** (`psVar6[-0x18a]`, `*psVar6`, `[0x18a]`,
`[0x314]`, `[0x49e]`, `[0x628]`, todos múltiplos de `0x314` en bytes) y avanza `0x93c` shorts =
`0x1278` bytes = `6 × 0x314`.

## El error que teníamos

Nuestras sondas leían `blk + 0xc12e9c`. El array de verdad empieza en **`blk + 0xc131b0`**:
exactamente **una regulación más allá** (`0xc131b0 - 0xc12e9c = 0x314`). Al leer desde una
regulación antes, el id que se tomaba en `+0x00` era en realidad un campo del registro anterior
—de ahí los `65535 65535 21582 …`— y el recuento salía mal.

La cuenta sí estaba bien: `+0xd0bcf4` es el mismo campo que lee `phkind` (`0x14150af30`).

## El cambio

`tools/native/fl26swiss.c`: `regcid_fix` pasa a recorrer `blk + 0xc131b0`. Con eso:

- las 101 supercopas y las copas de cid ≥ 256 se encontrarán por su id de regulación;
- se les podrá escribir el cid **completo** en `+0x80` (el campo que `phkind` compara como dword),
  que es lo que hace que el menú pinte el nombre bueno y abra el sorteo.

DLL compilado (380.416 B). **Pendiente de desplegar**: el juego estaba abierto con dos
instancias y corre elevado, así que el fichero está bloqueado y ni se puede matar sin UAC.

## Cómo probarlo

1. Cerrar las dos ventanas del juego.
2. Copiar `tools/native/fl26swiss_new.dll` a `SiderAddons\modules\fl26swiss.dll`.
3. Arrancar con **`FL 2026 start.exe`** (el exe directo casca: ver abajo).
4. Abrir Kick Off > Cup y mirar `C:\Users\viarm\AppData\Local\Temp\opencode\regcid.txt`.

Debe salir `N record(s) with an id, first ones: 1 2 3 4 …` y luego
`… ours seen, … got the full cid`. Si sale, los nombres deben cambiar.

## Nota de arranque

Lanzar `FL_2026.exe` a pelo **crashea** (`0xc0000005` en `0x32b92d`, dentro de `sub_14032b650`,
un `mov rcx,[rcx]` con `rcx` inválido) con el mundo activo o desactivado: no es cosa de los
datos. Con su lanzador `FL 2026 start.exe` arranca bien. Además el juego queda **elevado**, así
que Frida y Rizin no pueden engancharse sin un UAC: de ahí que el REA en vivo haya que hacerlo
desde el DLL de Sider (que ya corre dentro) o elevando la herramienta.
