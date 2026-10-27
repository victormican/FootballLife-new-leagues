# RE: como se crea una liga en Select Team (mapa para escalar limites)

## 1. Las cuatro piezas de una competicion

| pieza | fichero | campos |
|---|---|---|
| **competicion** | `Competition.bin` | `+0x05` cid (byte) ? `+0x20` codigo (FL_XXXX) ? `+0x00` region |
| **regulacion** | `CompetitionRegulation.bin` | `+0x02` id ? `+0x08` cid ? `+0x09` tipo (4 liga, 3 copa) ? `+0x0b` equipos (6 bits) ? `+0x14` nombre en 20 slots |
| **entradas** | `CompetitionEntry.bin` | 16 B por club: `+0x00` eid ? `+0x04` equipo ? `+0x08` cid ? `+0x0c` orden |
| **world** | `fl26world.txt` | `league <reg> cid=<N> slot=<S> clubs=<N> ...` |

`slot` es el sitio del menu; `serve=` sirve ese slot sin ocuparlo (merge con el pool del juego).

## 2. Como el menu construye la lista

1. El juego tiene una tabla de **165 filas** (`0x1434FDF00`, stride `0x108`), con `id` en `+0x00`,
   `slot` en `+0x04` y `promote/demote` en `+0x30/+0x34`.
2. `fl26comptab` la copia y le a?ade nuestras filas, enganchando las tres busquedas
   (por id `0x1414FDBDA`, por indice `0x1414FDD71`, rango `0x1414FDE07`).
3. `fl26clubs` reemplaza los lectores (`count@0x1414D62C0`, `get@0x1414D6290`) y sirve
   nuestras regulaciones por slot (`slot 75 <- reg 197`, etc.).
4. `fl26slotnames` nombra la cabecera; `fl26catlist` pone pais/bandera; `fl26regnames` da
   los nombres de las regulaciones.

**El nombre que se pinta sale de la REGULACION**, no del world.

## 3. Topes encontrados (con direccion)

| tope | RVA | forma |
|---|---|---|
| clubes del Edit: 750 | `0x1EF21D0` | `mov eax,0x2EE ; ret` ? ya elevado a 4.700 por `fl26edit` |
| equipos: 4.800 | `0x235E55B` | `mov eax,0x12C0 ; ret` ? parcheado a 12.600 |
| tabla de jugadores: 30.000 | inicializador `0xAF23B3` | `lea rax,[rcx+0xEE53D0]` y puntero en `[rcx+0xEE53C8]` |
| busqueda por id | `0xC4F242` | `lea rax,[rax*8+disp]` (disp movido en runtime por `fl26caps`) |
| busqueda hash de texto | `0x14D688B` | `mov eax,[rcx+rax*4]` tras `add eax,0x410001D4` |
| lista de copas | vector de heap | 13 entradas, `reserve` a localizar |

## 4. Por que el realojo rompe el juego

- La tabla de jugadores esta **inline en un objeto**; su inicializacion usa `[rcx+0xEE53D0]` y
  guarda el puntero en `[rcx+0xEE53C8]`.
- Moverla con una cueva **funciona en si misma** (`PT relocated`), pero la referencia es global:
  otras rutas del juego siguen leyendo la zona vieja (`lea [rbx+0xE63DE4]` o el equivalente).
- Con la tabla nueva, esas otras rutas leen memoria invalida y el juego salta a datos
  (dump: `0x105EA0000 add [rax],al`).
- Con la tabla antigua + la cueva, el resultado es el mismo cierre.

Conclusion: **no hay un unico sitio que apunte a la tabla**. Hay que localizar **todas** las rutas
que la leen antes de realojar (un inventario completo de referencias, no solo 3).

## 5. Como se puede escalar de forma segura (orden)

1. **Inventario de referencias** (con Capstone): todas las instrucciones que usan los offsets
   `0xEE53D0`, `0xEE53C8`, `0x7530` y `0xE63DE4`. Eso dice cuantas rutas hay que repuntar.
2. Topes con accesor (750, 4.800, regulaciones, cids): seguros, ya hechos o casi.
3. Tabla de jugadores: realojo solo cuando (1) este completo el inventario.
4. Slots 250 -> 500: tabla del menu, copia + repunte (no hay realojo de datos, es menos riesgo).
5. Copas: vector de heap -> hook del `reserve`.

## 6. Hallazgos de este estudio

- El crash de Edit es una **busqueda hash de id de texto** (no la tabla de jugadores): el juego
  enumera ids 0..0x114BB (70.843) y se sale al pedir el siguiente.
- El rotulo **Datos del usuario** tiene el mismo origen (nombre/id de texto inexistente).
- Con la DLL estable (sin experimentos), el juego **no se cierra**: los cierres eran nuestros.
