# Inventario de lo oculto (base limpia, 2026-10-26)

## Equipos

- Equipos en Team.bin: **3802** (selecciones: 211, clubes: 3591)
- Clubes **ocultos** (sin competicion): **3046**

| country | clubes ocultos |
|---|---|
| CROATIA (200) | 839 |
| EGYPT (58) | 470 |
| BOSNIA AND HERZEGOVINA (198) | 458 |
| ECUADOR (149) | 432 |
| INDIA (9) | 430 |
| PERU (151) | 362 |
| ENGLAND (204) | 13 |
| POLAND (227) | 5 |
| MEXICO (124) | 4 |
| UKRAINE (239) | 2 |
| VENEZUELA (153) | 2 |
| CYPRUS (201) | 2 |
| BOLIVIA (145) | 2 |
| CZECH REPUBLIC (202) | 1 |
| LITHUANIA (219) | 1 |

## Sitios del menu

- Slots de Select Team: 250 (23 del juego) -> **227 libres**
- Grupos servidos por `serve=`: 5, 6, 69, 70, 71, 72, 73, 75 (PARK)
- Copas: 26 posibles; `MAX_CCUP` ya en 512
- Regulaciones: 1.024 (libres ~545)

## Hallazgo del bug 'Datos del usuario'

- Con el livecpk `_FL26All` desactivado el rotulo desaparece; con el activo aparece.
- Todos los equipos tienen entre 8 y 10 de los 20 slots de nombre llenos (normal, tambien los del juego).
- Por tanto el rotulo no viene de un nombre vacio aislado: viene del conjunto de datos del livecpk
  (falta por aislar si es `Team.bin`, `Player.bin` o el `Country.bin`). Prueba pendiente: livecpk con solo
  `Competition*.bin` y despues anadir `Team.bin`.

## Causa raiz del rotulo "Datos del usuario" (biseccion completa)

Pruebas, una variable cada vez, con competiciones originales del juego y world vacio:

| livecpk contiene | rotulo |
|---|---|
| nada (livecpk desactivado) | **no** |
| Team.bin nuestro + Player/Assignment del juego | **no** |
| Team.bin nuestro + Player.bin nuestro + Assignment del juego | **si** |
| Team.bin + Player + Assignment nuestros | **si** |

Conclusion: lo dispara **Player.bin nuestro** (120.666 jugadores; el del juego tiene ~30.000).
Es el mismo muro ya documentado: la tabla de 30.000 entradas del bloque de edicion
(`cmp ecx, 0x7530`); los jugadores por encima no estan en la tabla y Select Team cae al rotulo.

### Arreglo

- Realojo de la tabla a 123.015 entradas (reserva + copia + repunte + los cinco `cmp`).
- Requiere capturar el bloque de edicion: la sonda `block_poll_thread` ya consulta
  `owner_fn()` cada 500 ms y escribe en `%TEMP%\opencode\arrays.txt`; el bloque aparece al
  entrar en **Master League** (no al menu ni al abrir Edit).
- Mientras no se realoje: **el rotulo es el precio de tener mas de 30.000 jugadores**.

### Otro defecto encontrado por el camino

- 1.949 jugadores estaban en **dos o mas plantillas**. Corregido: `PlayerAssignment` de 112.538 a
  110.589 filas (una por jugador).

## Crash de Edit: causa encontrada con depurador en vivo (2026-10-26)

### Herramienta

`cdb` (Windows Kits) **elevado**, adjuntando al proceso (el juego corre elevado: sin elevacion da
`Acceso denegado`). Script de comandos en fichero (`-cf`), no `-c` (el `-c` se parte).

```
sxd av                  ; ignora las excepciones de primera oportunidad
sxd 80000003
bp 0x140000000+0x14d688b ".echo ID:; r eax; gc"
g
```

La base del exe es siempre **0x140000000** (confirmado en los dumps).

### Lo que se ve

- La instruccion del fallo es `0x14D688B  mov eax,[rcx+rax*4]`, dentro de una **busqueda hash**:
  `0x14D6883 add eax,0x410001D4` / `0x14D6889 add eax,eax` / `0x14D688B mov eax,[rcx+rax*4]` / `ret`.
- La llama `0x1F0C158 call 0x14D6870`, que devuelve un **id de texto** en `eax`.
- Con el breakpoint puesto, se capturan **70.844 ids consecutivos**: 0, 1, 2, ... hasta
  **0x114BB (70.843)**. El juego **enumera la tabla de textos** y se sale al pasar del ultimo id.

Conclusion: **falta un id de texto** (se pide ~0x114BC). No es la tabla de jugadores.

### Descartado por el camino (con pruebas)

| hipotesis | prueba | resultado |
|---|---|---|
| tabla de 30.000 jugadores | realojo a 123.015 + busqueda + topes | `PT relocated` y `topes OK`, **el crash sigue** |
| entrenadores ausentes | `mkcoaches`: 3.053/3.053 con manager valido | **el crash sigue** |
| tacticas ausentes | `mktactics`: "club 71578 already has tactics" | descartado |
| `.fl26x` no cargado | reetiquetado con el tag del EDIT + restaurado el EDIT de dataSP | sigue `749 clubs, 0 from .fl26x` |
| `EDIT00000000` | renombrado y restaurado | sin efecto |

### Pista del rotulo "Datos del usuario"

Mismo origen: un **nombre/id de texto que no existe**. Por eso aparecen juntos el rotulo en
Select Team y el cierre al entrar en Edit.

### Siguiente paso (barato)

Desactivar **solo** `fl26regnames.lua` y `fl26slotnames.lua` (los que a?aden nombres/cabeceras
nuevas) y entrar a Edit. Si deja de cerrarse, el fallo es el rango de ids que escriben; si sigue,
filtrar el breakpoint a ids >= 0x11400 para ver quien pide el que falta.

### Vuelta atras aplicada

`tools/native/fl26swiss.c` revertido a HEAD y DLL estable reinstalada (`AE768947`): el realojo y
las cuevas quedan **documentados aqui** pero **fuera del juego**, que vuelve a estar estable.

