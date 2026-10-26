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

