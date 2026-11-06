# Inventario del mundo: lo que logramos (2026-11-06)

Resumen de lo que tenía el mundo antes de empezar la instalación limpia, para reproducirlo. Los
números son del último `check_world` (0 errores, 0 avisos).

## 1. Números

| | handoff de Matozanato (base) | nuestro mundo |
|---|---|---|
| competiciones | 394 | **512** |
| regulaciones | 589 | **711** |
| entradas | 5.137 | **5.667** |
| equipos | 3.450 | **3.648** (239 selecciones) |
| jugadores | — | **103.722** |
| ligas en el world file | 149 | **154** |
| líneas `ccup` (copas) | 168 | **286** |

## 2. Ligas (154)

La tabla completa, con cid, slot, número de equipos y colisiones de byte, está en
`lista-ligas-2026-11-06.md`. Bloques que se trabajaron:

- **Sudamérica**: Argentine 1.ª y 2.ª, Brasileño 1.ª–4.ª (la 4.ª con 63 clubes), Uruguay, Paraguay,
  Venezuela, Bolivia, Chile, Perú, Ecuador, Colombia.
- **Europa**: las 5 grandes completas (Serie A 20, Bélgica 16, etc.), segundas y terceras
  (3. Liga, Serie C/A-B-C, Championship, League One...), nórdicas, balcánicas, Bálticas.
- **África y Asia**: ligas nacionales y segundas divisiones.
- **OFC**: `Otros OFC` (slot 248, cid 382, reg 470, **48 clubes**) más las ligas de Australia y
  Nueva Zelanda.
- **Concacaf**: `Otros Concacaf` (slot 247, cid 221, **58 clubes**), MLS, Liga MX, Costa Rica, etc.
- **Otros europeos / latinoamericanos**: grupos de relleno servidos por regulación propia.

Extras:
- **15 ligas ocultas** pasaron a slots visibles (128 y 182..196).
- **Slots 750**: el juego tiene 123 y el mundo usa **152** (22..248); `MAX_CFG 768`, `MAX_CLUBS 96`.

## 3. Copas (286 líneas `ccup`)

- **Del juego, intactas**: 91 competiciones originales (no se pisó ninguna).
- **Decisión (2026-11-06)**: las dos ligas **sin slot (-1)** se quitan:
  *Primera C Colombia* (cid **92**, 48 clubes) y *Primera C Especial Colombia* (cid **65**, 30
  clubes), no seleccionables. Se queda *Primera C Colombia* del cid **366** (87 clubes, slot 246).
  El mundo reconstruido tendrá **152 ligas**; al quitarlas se borran también sus regulaciones y
  entradas. La única copa metida en una línea `league` es *Liechtensteiner Cup* (94).
- **14 copas regionales nuevas** (creadas con `mk_regional_cups.py`, eliminatoria con byes):

| copa | cid | equipos | tipo |
|---|---|---|---|
| African Nations Championship | 368 | 16 | selecciones |
| Copa UNAF | 369 | 4 | clubes |
| WAFU B Club Championship | 370 | 3 | clubes |
| UNIFFAC Club Cup | 371 | 3 | clubes |
| CECAFA Kagame Cup | 372 | 2 | clubes |
| COSAFA Club Cup | 373 | 3 | clubes |
| ASEAN Club Championship | 374 | 4 | clubes |
| CAFA Club Championship | 375 | 4 | clubes |
| WAFF Club Championship | 376 | 7 | clubes |
| EAFF Club Championship | 377 | 2 | clubes |
| ASEAN Championship | 378 | 4 | selecciones |
| CAFA Nations Cup | 379 | 4 | selecciones |
| WAFF Championship | 380 | 7 | selecciones |
| EAFF E-1 Football Championship | 381 | 2 | selecciones |

- **OFC Champions League** (cid 367) y su copa de selecciones.
- **Copa Sudamericana** (cid 513): 32 clubes, 8 grupos (regs 192 + 1024k) y eliminatoria (193).
- **AFC Champions League Two Clubes** (cid 603).
- **Una copa y una supercopa por país** (`copas-por-pais-y-del-juego.md`), con los campeones de
  cada liga; las copas de grupos del juego se conservan.
- **Copas de grupos duplicadas** para llenar el menú (286 en total), sin pisar ids del juego.

## 4. Equipos y jugadores

- **3.648 equipos** (239 selecciones; el resto clubes), con nombre, código de 3 letras y país.
- **103.722 jugadores** y **93.338 asignaciones**; cada club con 11 + portero.
- Escudos y kits: PNG 256×256 RGBA en `crests/` y `logos/`; caras para los ids nuevos.

## 5. Parches y piezas que sostienen el mundo

| pieza | qué hace |
|---|---|
| `fl26slots750` + DLL | 750 slots, `MAX_CFG 768`, `MAX_CLUBS 96` |
| `fl26cid16` | cids hasta 1023 (`pack`, `reg`, `build`, `map`; `cid` y `list` apagados) |
| `fl26clubs` + DLL | sirve la lista de clubs de la liga desde su regulación (20 slots `SERVED`) |
| `fl26swiss` + DLL | copas de grupos y fases |
| `fl26comptab` | filas de parámetros de nuestras ligas |
| `fl26catlist`, `fl26slotnames`, `fl26regions` | países, nombres y regiones en los menús |
| `fl26cupgrow` / `fl26cupfree` | menú de copas (más de 13, sin el cierre `0x3fd2b2`) |
| `fl26squadlist` (0.3.0) | lista de clubs de la liga en Select Team / Team Info |

Slots servidos (20): `75←181, 69←364, 71←256, 73←362, 248←470, 80←76, 209←9000, 84←111,
72←178, 77←182, 200..208←900..908, 247←250`.

## 6. Estado: el build estaba en la carpeta borrada

El mundo vivo estaba en `D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld`.
Esa carpeta **ya no existe** (la instalación nueva está en `D:\SP Football Life 2026`, con un mundo
de 91 ligas y 0 copas). En el disco no queda copia de nuestras tablas (la mayor es el handoff).

**Lo que sí sobrevive (en el repo):**
- La lista de las 154 ligas con sus equipos (`lista-ligas-2026-11-06.md`).
- Los documentos de cada bloque: copas regionales, copas por país, Otros OFC/Concacaf, Sudamericana,
  slots, límites, menús.
- Las herramientas que lo construyen (`tools/mk_*.py`, `leaguebuilder.py`, `add_world_cups.py`,
  `mk_regional_cups.py`, `dup_cups*.py`, `mkslots.py`, `mkregs.py`...) y el validador
  `check_world.py`.
- Los módulos y las DLL.

## 7. Reconstrucción en la instalación limpia (orden)

1. Base: instalar el **handoff de Matozanato** (`handoff-matozanato-20261104`) → 149 ligas, 168 copas.
2. Quitar las dos ligas sin slot (cid 92 y 65) y añadir las 5 nuestras con `add_*`/`leaguebuilder`
   → **152 ligas** (149 del handoff − 2 + 5).
3. Copas: `mk_conf_cups.py` (continentales), `mk_regional_cups.py` (las 14), `dup_cups_groups.py`
   (menú de copas), una copa + supercopa por país.
4. `mkslots.py` (750), `cid16_migrate.py` (cids altos), `fix_cid2_entries.py` (copa 2).
5. Escudos/kits/caras (`fetch_world_crests.py`, `mkcrests.py`, `mkkits.py`, `lbfaces.py`).
6. `check_world.py` hasta **0 errores / 0 avisos**.
7. Módulos + DLL + `sider.ini` (ver `instalacion-limpia-2026-11-06.md`).

Con esto se reproduce el mundo; lo que no se puede recuperar es el *arbol exacto* de decisiones
de cada copa, pero está documentado bloque a bloque.
