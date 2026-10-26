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

