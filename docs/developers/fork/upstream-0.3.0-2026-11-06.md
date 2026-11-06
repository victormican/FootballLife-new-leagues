# Lo que trajo el upstream (FL Mod Studio 0.3.0) y qué aporta

2026-11-06. `git fetch upstream` y merge de `upstream/main` (`5fb1ea5`) sobre `cwc-next`.

- 127 commits del upstream (0.2.5.1, 0.2.5.2, 0.3.0) sobre la base `f2e2937`.
- 20 ficheros tocados por los dos lados; **7 conflictos**, resueltos así:
  - `tools/native/fl26clubs.dll`, `fl26swiss.dll`, `sider/experimental/fl26swiss.dll` → **los nuestros**
    (nuestras builds; hay que recompilar desde el `.c` mergeado).
  - `tools/native/fl26swiss.c` → el log de **1 MB con contador de líneas perdidas** del upstream
    + nuestra sonda de `player table probe`.
  - `sider/experimental/fl26clubs.lua` → **nuestra** lista `SERVED` (con 200..208, 247..249, 84,
    209) + la función `own_remap`/`pick` del upstream (0.3.0).
  - `tools/fl26world.py` → `KEYS` con **`pick`**.
  - `tools/leaguebuilder.py` → se quedan **las dos**: `cwc_champs` (nuestra) y `assoc_rank`/`place_rank`
    (upstream, ranking UEFA B250).
- Merge: `60ddf18`. `python -m compileall tools` pasa.

## Lo que aporta de verdad

| cambio | por qué nos importa |
|---|---|
| **Select Team lista los clubs de la liga** (`fl26squadlist.lua` nuevo) | Es justo el panel que llevábamos días peleando: con el cursor en una liga, la lista de la derecha ya no sale vacía; sale "Team List" con los clubs y sus escudos. Es la solución del upstream, no la nuestra. |
| **B312 / B308: cierre en la ronda de clasificación** (`fl26swiss.c`) | `0x141333485`: una eliminatoria se quedaba con un club que ya se había movido de plaza y el juego cerraba en el día del partido (agosto). Afecta a mundos como el nuestro. |
| **B313: plazas europeas en cascada** | Una plaza libre va al siguiente club y los demás suben; antes el 8.º jugaba Europa y el 7.º no. |
| **B314 / B320: liga debajo de la liga del juego (y de las de split)** | NewLife/ nuestras ligas de un país del juego entran como división inferior; con Escocia, Dinamarca y Bélgica (fase regular + grupos) también. |
| **B315 / B318: enero-diciembre** | Ascenso/descenso entre ligas de un país nuestro con calendario natural, y su copa nacional se juega. |
| **B307: tablas propias de FL26 y FL27** | No se pisan las tablas al cambiar de juego. |
| **B317: instalar zip con `livecpk` vacío** | Un pack con carpeta vacía ya no rompe la instalación. |
| **Nombres de regens tras cargar** y retratos FL27 | Estabilidad de carrera. |
| **Colores en las tablas** y **elegir qué grupo "Other" sustituye una liga** (`pick=1`) | Presentación y colocación en Select Team. |
| **FL27** | El programa pasa a llamarse FL Mod Studio y sirve para los dos juegos. |

## Lo que seguimos poniendo nosotros

- El **mundo** (154 ligas, 152 slots, 286 ccup, tablas en `_FL26MyWorld`).
- **Slots 750** y `MAX_CFG 768` (`fl26slots750`, DLL).
- Los parches de **cid 16 bits** (`fl26cid16`: `pack`, `reg`, `build`, `map`; `list` sigue apagado).
- `fl26clubs.lua` con nuestra lista `SERVED` y el DLL de 750 slots.
- Nuestros docs de `docs/developers/fork/` y la herramienta de desensamblado.

## Pendiente al terminar el merge

1. **Recompilar** `fl26clubs.dll` y `fl26swiss.dll` desde el `.c` mergeado (el `.c` de swiss ya lleva
   el fix de log del upstream; el de clubs se automergeó) y desplegarlos.
2. Probar en limpio: Select Team (lista de clubs nueva), Liga, Copa, y el aviso de la copa 2.
3. Decidir si el parche `ENABLE.list` se retira: con `fl26squadlist` del upstream la lista ya sale
   de otra ruta; hay que medir si sigue haciendo falta.
