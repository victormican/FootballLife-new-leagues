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

## Patron completo de la tabla de jugadores (inventario 2026-10-27)

Volcado completo en `referencias-tabla-jugadores.txt` (Capstone sobre el exe, 437 MB).

### 12 rutas que leen la tabla

| offset | RVAs | para que |
|---|---|---|
| `0xEE53D0` (tabla inline) | `0xAF23B6`, `0xAFD849`, `0x12E67FF` | inicializar, otro consumidor, metadato de tamano |
| `0xEE53C8` (puntero) | `0xAF23BD`, `0xAF23D7` | guardar / leer |
| `0xE63DE4` (base de busqueda) | `0xC4F246`, `0x14B88CE`, `0x14BBC8F`, `0x14F365C`, `0x15106D3`, `0x20A9869`, `0x20A99DA` | buscar por id y comparar contenido |

`0xE63DE4` **es reescrita en runtime por `fl26caps`** (a `0x6475C08`), asi que la firma de bytes
debe ir por **opcode** y no por el desplazamiento exacto.

### Topes (offset exacto, no aproximado)

```
0xC4F255  cmp ecx, 0x7530      (antes lo escribi en 0xC4F253: 2 bytes desplazado)
0xAFD915  cmp edi, 0x7530
0xAE4C87  cmp eax, 0x7530
0xAE4C90  imul rcx, r9, 0x7530      (dimensionado de bloque)
0x8BDBCC  imul r8d, [rbx+0x18], 0x7530  (dimensionado de bloque)
```

### Por que el realojo fallo (causa completa)

1. Hay **12 rutas**, no 3: repuntar 2 deja las demas leyendo memoria vieja.
2. Los `cmp` se escribieron 2 bytes desplazados de su sitio real -> **corrupcion de instruccion**.
3. Consecuencia: salto a datos (`0x105EA0000`), incluso con la tabla bien construida.

### Decision de diseno

**(A) Ampliar in situ NO es viable**: la tabla esta dentro de un objeto grande y hay otros arrays
despues de ella (el offset 0xE63DE4 los indexa); no hay hueco contiguo garantizado.

**(B) Realojo con las 12 rutas**: viable pero exige los 12 puntos de enganche. Alternativa mas
barata y segura: **cambiar solo el campo de capacidad del objeto** si existe
(`0x12E67FF mov [rdi+0x180], 0xEE53D0` parece el metadato de tamano del objeto, NO de la tabla).

### Orden recomendado (ya con el inventario)

1. Leer los 2 metadatos del objeto (`0x12E67FF` y `0xAE4C87`/`0xAE4C90` y `0x8BDBCC`) para saber
   si el tamano se calcula de una constante o de un campo del objeto.
2. Si es campo del objeto: cambiar **el campo** (un entero) y reasignar el objeto entero, sin
   tocar las 12 rutas. Eso es un cambio de tamano, no de codigo.
3. Si es constante en codigo: realojo con las 12 rutas, una por una, validando cada 2.

