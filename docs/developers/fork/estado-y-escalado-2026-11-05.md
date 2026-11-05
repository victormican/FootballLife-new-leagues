# Estado y escalado (2026-11-05)

Lo que ya no hay que volver a investigar, lo que sigue abierto y lo que habría que romper para
seguir creciendo. Los números son del mundo vivo `_FL26MyWorld` medidos hoy.

## 1. El mundo hoy

```
equipos 3.460 (239 selecciones) · jugadores 101.280 · asignaciones 90.000+
competiciones 496 · regulaciones 692 · entradas 5.4xx
151 ligas (slots 22..246) · 271 copas (102 supercopas) · 240 países
check_world: 0 errores
```

## 2. Preguntas cerradas (no volver a investigarlas)

| pregunta | respuesta | dónde está |
|---|---|---|
| ¿Se pueden añadir ligas y copas? | Sí: tres filas (Competition, Regulation, Entry) y una línea de mundo | `regulaciones-y-formatos.md` |
| ¿Cuáles son los topes y cómo se suben? | `layout.json` → `patchset` → `fl26caps`; todo o nada | `limites-actuales-2026-11-05.md` |
| ¿Se puede pasar de 255 competiciones? | Sí, con la tabla plana de 1024 (`fl26cid16`) | `cids-16-bit.md` |
| ¿Por qué Oceanía salía llena y los países en secciones raras? | el `country` guardaba el **id de bandera**, no la fila de `Country.bin` | `paises-id-bandera.md` |
| ¿Por qué no aparecía Sudán del Sur? | su país era la bandera 312, fuera de las 240 filas | `paises-id-bandera.md` |
| ¿Por qué la Primera de Argentina no salía? | estaba en las tablas y **sin línea** en el world file | `argentina-d1.md` |
| ¿Por qué África salía oculto? | el juego no llena los slots de pool: hizo falta `pool 75 181` | `grupo-africa.md` |
| ¿Se puede aplicar NewLife a un mundo ya hecho? | Sí, `newlife_apply.py`, con cuidado con los ids reutilizados | `newlife-aplicar.md` |
| ¿Cómo se crean las supercopas? | 101 copias de la Pro League Supercup con `entry=liga:1,copa:0` | `supercopas-por-nacion.md` |
| ¿Dónde está el array de regulaciones en memoria? | `block + 0xc131b0`, stride `0x314`, cuenta en `+0xd0bcf4` | `regulaciones-en-memoria.md` |
| ¿Cómo se arranca el juego? | con **`FL 2026 start.exe`**; el exe directo casca en `0x32b92d` | `regulaciones-en-memoria.md` |
| ¿Se puede depurar el juego con Frida/Rizin? | corre **elevado**: sin UAC no; el DLL de Sider sí (va dentro) | `craft-anything.md` |
| ¿Qué motor de RE tenemos? | Craft Anything por MCP con Ghidra 11.3.2 y Rizin | `craft-anything.md` |

## 3. Preguntas abiertas

| # | pregunta | qué falta | esfuerzo |
|---|---|---|---|
| 1 | **¿El cid completo en `+0x80` arregla el nombre y el sorteo de las copas?** | abrir **Kick Off > Cup** una vez y leer `regcid.txt` (el DLL ya recorre `+0xc131b0`) | 5 min |
| 2 | ¿Por qué el DLL acepta 254 de 271 copas? | listar las 17 rechazadas (las del juego con `type` 4/8/9) y decidir | 1 h |
| 3 | ¿Se puede arreglar el **emblema** por byte bajo? | depende de (1); si no, ensanchar la ruta `emb_<cid>` | 2 h |
| 4 | ¿Cómo se lista la **MLS** con 30 clubes y su formato? | `type 5` con dos rondas y conferencias; necesita calendario propio | 3 h |
| 5 | ¿Oceania y No FIFA como **grupos de selecciones** en vez de copas? | prestar el slot 5/6 de Classic Teams y servir la lista | 4 h |
| 6 | ¿Se juegan las **supercopas** en su fecha? | comprobar `like=128` en juego; si no, `days=` | 1 h |
| 7 | ¿Se pueden poner **escudos reales** a los ~2.100 clubes que faltan? | emparejador difuso `fuentes.mejor_slug()` por país (footylogos ya cacheado) | 2 h + red |
| 8 | ¿Logos de **competición** reales? | mapear con `logos/` del release y `Downloads\Logos` a `emb_<cid>` | 2 h |
| 9 | ¿Se crean los **4 clubes** que faltan en la Primera argentina? | NewLife los tiene; hay que crear club + plantilla | 3 h |
| 10 | ¿Qué hacemos con los duplicados de **Copa Colombia** y los 4 `Generic League`? | decidir borrar/renombrar | 30 min |
| 11 | ¿La **Primera C Colombia** (87) debe jugarse? | partirla en grupos o dejarla en 20 a dos vueltas | 2 h |
| 12 | ¿Se rellenan las **17 ligas cortas** (111 clubes)? | `fill_group` por liga; cabe sin romper nada | 2 h |

## 4. Para escalar: qué romper y hasta dónde

### 4.1 Se puede subir sin tocar el ejecutable

| recurso | hoy | siguiente | cómo | coste |
|---|---|---|---|---|
| regulaciones | 692 / 1.200 | 2.000 | `layout.json` + `mkregs --stub` | bajo |
| filas de copa | 271 / 512 | 1.024 | `fl26cupgrow` (mismo cambio que 256→512) | bajo |
| clubes del Edit | 3.308 / 4.700 | 6.000 | `fl26edit.c` | medio |
| equipos | 3.460 / 4.800 | 6.000 | `layout.json` (después del Edit) | medio |
| competiciones (cid) | 496 / 1.023 | 4.096 | tabla plana de 4.096 + máscara `0xfff` | medio |
| jugadores | 101.280 / 123.825 | ~262.000 | `layout.json` + regenerar set y cola baja | alto |

### 4.2 Paredes de formato (no se suben con un `cap_new`)

| pared | límite | por qué |
|---|---|---|
| id de jugador | **262.143** | 18 bits del formato; a 22 por club el techo son **~11.900 clubes** |
| equipos por regulación | **63** | campo de 6 bits (`+0x0B`) |
| clubes por liga jugable | **38** | el calendario grande tiene 38 fechas (46 con split) |
| regiones | **127** | slot de liga en 7 bits (`+0x41c & 0x7f`) |
| slots de Select Team | **250** | espacio del bloque de slots, no un `cmp` |
| nombre/emblema por cid | byte bajo | mientras no se cierre (1), cid ≥ 256 muestra el de otra |

### 4.3 El techo real del mundo

Con el id de 18 bits y 22 jugadores por club: **~11.900 clubes**. El release NewLife tiene
**13.481**: no cabe entero ni rompiendo las capacidades. Para acercarse hay que subir jugadores
(lo caro) y aceptar que las divisiones amateur del release (Federal C 720, Regional Amateur 250…)
nunca entrarán completas.

## 5. Reglas de operativa (las que nos han costado un mundo)

1. Arrancar con **`FL 2026 start.exe`**.
2. El world file **idéntico** en `livecpk\_FL26MyWorld\` y `modules\`.
3. `fl26cupgrow` en **512** (con 256 se pierden 15 copas).
4. `set_bits` sobre una rebanada de `bytearray`: devolverla al array o no escribe.
5. Emparejar clubes **por nombre antes que por id** (los ids se reutilizaron).
6. El país son 9 bits desde el bit 562 y **fila**, no bandera.
7. Antes de escribir tablas con el juego abierto: cerrarlo (UAC).
8. Copia `.before-*` de todo lo que se toca y `check_world` al terminar.

## 6. Cómo verificar

```
python tools/check_world.py --base <mundo>\common\etc\pesdb --worldfile <modules>\fl26world.txt
python tools/limits.py
python tools/setcheck.py
```

Criterio de "hecho": `check_world` con **0 errores** y el juego arrancando con el lanzador.
