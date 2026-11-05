# Pendientes y qué se puede abordar (2026-11-05)

Lista viva al cerrar la sesión. Ordenada por lo que desbloquea más con menos trabajo.

## A. A un paso (una prueba o una línea)

| # | pendiente | estado | qué falta | esfuerzo |
|---|---|---|---|---|
| 1 | **Nombre y sorteo de las copas con cid ≥ 256** | `regcid_fix` ya recorre el array bueno (`block+0xc131b0`) y está desplegado | **abrir Kick Off > Cup una vez** y leer `regcid.txt` | 5 min |
| 2 | **17 copas que el DLL no acepta** (`271 ... 254 accepted`) | identificadas como las del juego con `type` 4/8/9 | mirar cuáles son y darles la forma que el DLL acepta (o dejarlas como están, van al menú igual) | 1 h |
| 3 | **Emblema por byte bajo** (cid ≥ 256 comparte escudo) | conocido; las 101 supercopas y las copas nuevas lo sufren | depende de (1): con el cid completo, o bien se pide `emb_<cid>` o se ensancha la ruta | 2 h |
| 4 | **Duplicados de Copa Colombia** (comp 92: los mismos 24 clubes dos veces) y 2 huérfanos "Copa Argentina Club 48" | medido, sin tocar | decidir: quitar el segundo juego (dejar la copa en 24) o renombrarlo; borrar los huérfanos | 30 min |
| 5 | **72 clubes sin nombre corto** (`+0x372`) | herramienta hecha, no aplicada (los placeholders darían el mismo código) | esquema que incluya el número (OC1..OC9) o dejarlos | 1 h |

## B. Trabajo medio

| # | pendiente | estado | qué falta | esfuerzo |
|---|---|---|---|---|
| 6 | **4 clubes de la Primera argentina que no existen** (Sarmiento, Riestra, Gimnasia Mendoza, Estudiantes Río Cuarto) | el release los tiene; los ids 2730/5366 están ocupados por peruanos | crearlos con plantilla, escudo y kit (NewLife → build parcial) | 3 h |
| 7 | **~2.100 clubes sin escudo real** | 510 ya traídos con el catálogo exacto de footylogos | emparejador difuso `fuentes.mejor_slug()` por país, en lotes | 2 h + descargas |
| 8 | **Logos de competición reales** | hay `logos/` en el release y 53 en `Downloads\Logos` | mapear competición → logo y escribirlos como `emb_<cid>` | 2 h |
| 9 | **Supercopas: fechas** | creadas con `like=128` (copia de la belga) | comprobar en juego que se juegan en la fecha correcta; si no, `days=` | 1 h |
| 10 | **Oceania y No FIFA como grupos de selecciones** (hoy son copas) | existen como competiciones (cid 91 y 255) con sus selecciones | opción B de `national-teams-and-oceania.md`: prestar el slot 5/6 de Classic Teams y servir la lista | 4 h |

## C. Capacidad (cuando el mundo apriete)

| # | pendiente | margen hoy | qué falta | esfuerzo |
|---|---|---|---|---|
| 11 | ids de jugador | 1.598 libres (de 262.143) | compactar ids o política de reutilización antes de añadir ligas grandes | 3 h |
| 12 | regulaciones a 2.000 | 510 libres de 1.200 | `layout.json` + `mkregs --stub` | 2 h |
| 13 | filas de copa a 1.024 | 241 libres de 512 | el mismo cambio que 256→512 | 30 min |
| 14 | Edit de clubes (4.700) | 1.250 libres | `fl26edit.c` | 4 h |
| 15 | slots de Select Team (250) | 117 libres | mover la zona de slots | alto, riesgo |

## D. Paredes que no se abordan (documentadas)

- **Regiones 127** (campo de 7 bits), **equipos por regulación 63** (6 bits), **clubes por liga 38**
  (calendario de 38 fechas), **id de jugador 18 bits** (262.143) y el **byte bajo del cid** mientras
  no se cierre (1).

## E. Operativa que hay que respetar

- El juego se arranca con **`FL 2026 start.exe`**; el exe directo casca en `0x32b92d` (no es de los
  datos).
- El world file va **idéntico** en `livecpk\_FL26MyWorld\` y en `modules\`.
- El juego corre **elevado**: para copiar el DLL o matarlo hace falta un UAC.
- `fl26cupgrow` tiene que quedar en **512** filas (con 271 copas, 256 deja 15 fuera).

## Lo que yo abordaría ahora, en este orden

1. **(1) abrir el menú de copas**: es una prueba de 5 minutos y cierra el bloque más grande
   (nombres, sorteo y, de paso, los emblemas).
2. **(4) duplicados de Copa Colombia**: son visibles y el arreglo es corto.
3. **(7) escudos con el matcher difuso**: se nota mucho y es mecánico.
4. **(6) los cuatro clubes argentinos**: deja la Primera completa.
5. **(12 y 13) capacidad barata**: regulaciones a 2.000 y copas a 1.024.
