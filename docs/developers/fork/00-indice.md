# Índice de la documentación del fork (revisado 2026-11-06)

Documentos del fork. Este índice dice **cuál manda hoy** en cada tema, cuál está superado y cuál
es histórico. Regla: si dos hablan de lo mismo, gana el más nuevo de la columna "vigente".

## Estado y pendientes

| documento | estado |
|---|---|
| **`revision-completa-y-pendientes-2026-11-06.md`** | **vigente** — cifras del mundo, los 4 fallos abiertos y los pendientes P0..P3 |
| **`estado-y-escalado-2026-11-05.md`** | histórico: qué estaba cerrado y abierto el 05; superado por el anterior |
| `pendientes-2026-11-05.md` | superado por la lista de `revision-completa-y-pendientes-2026-11-06.md` |
| `summary-2026-10-23.md`, `summary-2026-10-24.md`, `test-world-2026-10-23.md`, `world-state-2026-10-24.md`, `inventario-oculto-2026-10-26.md`, `reconstruccion-paso-a-paso.md` | histórico: sesiones pasadas |

## Límites y capacidad

| documento | estado |
|---|---|
| **`limites-actuales-2026-11-06.md`** | **vigente** — 500 slots, 159 por slot, y los topes de ligas/copas |
| **`sesion-2026-11-06.md`** | **vigente** — todo lo investigado y hecho en la sesión |
| **`rea-cotas-slots-500-2026-11-06.md`** | **vigente** — por qué 500 fallaba (solape de tablas) y el arreglo |
| **`limites-ligas-y-copas-2026-11-06.md`** | **vigente** — ligas solas y copas solas |
| **`regresion-slot22-2026-11-06.md`** | **vigente** — el slot 22 repetido abortaba comptab |
| **`belgica-slot84-y-limite-16.md`** | **vigente** — `MAX_CFG 16` del DLL (instalación fallida) y el id 111 de Bélgica |
| `limites-actuales-2026-11-05.md` | superado en números por el de 2026-11-06 |
| `limites-escalables.md` | vigente en el **mecanismo** (`layout.json` → `patchset` → `fl26caps`); sus números son de octubre |
| `walls.md` | vigente como mapa conceptual de paredes |
| `limits-and-formats.md`, `limits-2026-10-24.md` | superados en números |

## Competiciones, formato y tablas

| documento | estado |
|---|---|
| **`regulaciones-y-formatos.md`** | **vigente** — las tres tablas, campos, tipos y plantillas |
| **`como-crear-liga-y-copa.md`** | **vigente** — tutorial verificado (liga + copa + supercopa) |
| `world-file.md` | vigente — todas las clases de línea (incluye `pool`) |
| `recipe-keys.md` | vigente — claves de receta |
| `building.md`, `testing.md`, `modules.md` | vigentes — construir, probar y módulos |
| `code-map.md`, `re-arquitectura.md` | vigentes — mapa del ejecutable y del flujo de Select Team |
| `cids-16-bit.md` | vigente — cid por encima de 255 |
| **`regulaciones-en-memoria.md`** | **vigente** — el array vivo y el REA del nombre de copas |
| **`revision-completa-y-pendientes-2026-11-06.md`** §2 | **vigente** — id de regulación u16 en `+0x02`, cid alto en `+0x492` y en la entrada `+0x0B` |

## Copas

| documento | estado |
|---|---|
| **`supercopas-por-nacion.md`** | **vigente** — las 101 supercopas y el cupgrow a 512 |
| **`copas-regionales-2026-11-06.md`** | **vigente** — 14 copas regionales (CHAN, UNAF, WAFU B, UNIFFAC, CECAFA, COSAFA, ASEAN, CAFA, WAFF, EAFF) |
| **`copa-cierre-y-blanco.md`** | **vigente** — el cierre del menú de Copa: slot 123, buffer, cid |
| **`menus-y-automatizacion-2026-11-06.md`** | **vigente** — flujos de menú y automatización elevada |
| **`otros-ofc-y-slots-2026-11-06.md`** | **vigente** — Otros OFC (slot 248) y el techo de 250 que ahora es 500 |
| **`copas-grupos-duplicadas.md`** | **vigente** — las 9 copas que `dup_cups.py` dejaba fuera: 542 líneas `ccup` |
| **`copas-por-pais-y-del-juego.md`** | **vigente** — una copa y una supercopa por país; `showcup` para las del juego |
| **`selecciones-en-copa.md`** | **vigente** — Oceania y No FIFA en Copa |
| **`grupo-africa.md`** | **vigente** — slot 75 servido con `pool 75 181` |
| `estado-copas-2026-11-04.md` | histórico del bloque de copas (el nombre sigue abierto) |
| `cup-mode.md`, `copas-por-liga.md`, `cup-invites.md`, `duplicar-copas.md`, `super-cup-4.md`, `continental-cups-and-recopas.md`, `brazilian-state-cups.md`, `leagues-cup.md`, `club-world-cup-32.md`, `cup-mode-block-2026-10-25.md` | vigentes por tema; los dos últimos, históricos |

## Países, selecciones y grupos

| documento | estado |
|---|---|
| **`paises-id-bandera.md`** | **vigente** — el id de país era el de la bandera |
| **`revertido-paises-2026-11-06.md`** | **vigente** — el remapeo a filas de Country.bin se revirtió |
| **`nombres-corruptos-y-belgica.md`** | **vigente** — 35 nombres doble-codificados y la liga belga |
| **`otros-grupos.md`** | **vigente** — nibble `+0x4f` y los cinco grupos |
| `banderas-de-pais.md` | vigente — formato y nombres de las banderas |
| `national-teams-and-oceania.md` | vigente — modelo de slots de selecciones |
| `national-team-competitions.md`, `generic-national-teams.md`, `agregar-seleccion.md`, `select-team-no-ligas.md` | vigentes por tema |

## Equipos, escudos y NewLife

| documento | estado |
|---|---|
| **`newlife-aplicar.md`** | **vigente** — aplicar un release a un mundo ya hecho |
| **`escudos-reales-y-nombres.md`** | **vigente** — crests con el catálogo otro proyecto y nombres argentinos |
| **`equipos-vs-release.md`** | **vigente** — comparación de plantillas contra el release |
| **`equipos-revision.md`** | **vigente** — auditoría de equipos (duplicados, códigos) |
| `newlife-format.md` | vigente — formato del release |
| `newlife-limits-and-formats.md` | vigente — qué cabe del release |
| `clubes-genericos-y-crest.md`, `genericos-por-liga.md`, `inventory-real-clubs.md`, `abreviatura-de-equipo.md`, `ligas-de-pais.md`, `divisiones-genericas.md`, `genericas-a-paises.md`, `ligas-reales-2026-10-25.md`, `generic-leagues.md`, `afc-composition.md` | vigentes por tema |

## Herramientas

| documento | estado |
|---|---|
| **`craft-anything.md`** | **vigente** — motor de RE con MCP, Ghidra y Rizin |
| `inventario-argentina-huerfanos.md` | vigente — qué es cada fila de la auditoría de Argentina |
| `primera-c-colombia.md`, `mls-equipos.md`, `argentina-d1.md` | vigentes — las últimas altas |
