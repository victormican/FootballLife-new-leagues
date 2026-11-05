# Mundo de prueba de Victor — estado y límites (2026-11-04)

Para **matozanato**. Esto es el mundo vivo de `D:\SP Football Life 2026 - copia - copia` tal
como quedó al final de la sesión del 4 de noviembre, con todo lo que se rompió y lo que sigue
abierto. Los ficheros del mundo están en `pesdb/`, el fichero de mundo en `fl26world.txt` y los
módulos de Sider que hacen falta en `modules/`.

## 1. Números del mundo (verificados con `check_world`)

```
equipos 3450 (239 selecciones)   jugadores 89488   asignaciones 83581
competiciones 293                regulaciones 488   entradas 4333
ligas 149 (slots 22..244)        copas (ccup) 168
0 errores, 1 aviso (competición 2, copa del juego con dos clubes en la posición 32)
```

## 2. Límites vigentes y cómo se subieron

| recurso | tope | módulo / mecanismo |
|---|---|---|
| slots de competición | **250** | `fl26slots250` (123 → 250, el 123 queda de centinela) |
| ids de competición | **1023** | `fl26cid16` con el censo de 16 bits |
| filas en Kick Off > Cup | **256** | `fl26cupgrow` (64 → 256; estaba en 13 de fábrica) |
| regulaciones | 1200 | `fl26regs1200` + `fl26caps` |
| regiones | 127 | `fl26reg128` |
| equipos | 4800 | `fl26caps` |
| jugadores | 262.143 | `fl26caps` / `fl26playercap` |
| clubes por liga | 38 | calendario (`BIG_LEAGUE_DAYS`) |

Paredes reales que quedan: **250 slots** (una liga por plaza), **38 clubes por liga** y
**127 regiones**. Los ids y las filas de copas ya no son pared.

## 3. El hallazgo gordo: el byte bajo del cid

El motor guarda el cid en 16 bits, pero **varias rutas lo leen como byte**:

- la **lista de clubes por slot** del censo de Select Team: una liga con cid 265 caía en el nodo
  de la competición 9 y su slot listaba los 20 clubes de la Premier League;
- el **emblema**: se pide `emb_<cid & 0xFF>`.

Lo primero está resuelto (`sider/experimental/fl26cid16.lua`, sección `map`): el censo usa un
`std::map<byte, fila*>` cuyo `insert` deduplica por ese byte, así que ensanchar los `cmp` nunca
podía funcionar (crash a los 25 s). Ahora las dos búsquedas se contestan desde una **tabla plana de
1024 punteros**:

```
0x1414f1d6a / 0x1414f1e5a   clave = byte[+8] | byte[+0xb] << 8
0x1414f1576                 insert: tabla[cid] = fila
0x1414f1d8b / 0x1414f1ea1   find:   &tabla[cid] - 0x28   (el llamante espera puntero al hueco)
```

Dos crashes medidos y documentados en `docs/cids-16-bit.md`: devolver la fila en vez del puntero
al hueco (`0xc0000005` en `0x1414f7ffc`) y devolver 0 para un cid sin fila (falta el fallback al
`find` original).

## 4. Las 168 copas

- **21 desbloqueadas del juego**: FA Cup, Coppa Italia, Copa del Rey, Coupe de France, KNVB, Taça,
  DFB Pokal, US Open Cup, Emperor's Cup, Copa Argentina, Copa Chile, Copa do Brasil, Copa
  Colombia, Croky Cup, Russian Cup, Greek Cup, Turkish Cup, Chinese FA Cup, Danish Cup, Scottish
  Cup, King's Cup.
- **101 nuevas `<País> Cup`**, una por país con liga en Select Team, eliminatoria directa con los
  8 primeros de su liga de primera (4 o 2 si es más corta).
- **27 estaduales brasileños** (7 que ya había + 20 nuevos; los 10 estados sin clubes en el juego
  tienen 2 clubes genéricos propios).
- **8 continentales nuevas**: UEFA Conference, CAF Champions, CAF Confederation, AFC Champions Two,
  AFC Challenge (16), Copa Caribeña CONCACAF (16), CFU Club Shield (16), Copa Intercontinental (2,
  campeón UCL vs campeón Libertadores).
- FIFA World Cup (cid 27) expuesta con sus 32 selecciones, 8 grupos + KO.
- Más las 17 de siempre (Sudamericana, Gold Cup, OFC, Nations Leagues, Leagues Cup, Moldovei,
  Carabao, Supercopa, estaduales viejas).

Todas caben: `Cup mode -- 167 world cup(s) added, all in (list 175 of 256)`.

## 5. Lo que queda abierto (y por qué)

**El menú de copas no resuelve nuestras competiciones.** Síntoma doble, misma causa:

- la fila muestra *FIFA Club World Cup* (cid 1) en vez de su nombre;
- al entrar en una copa nuestra, el juego se cierra por "sin tamaño de sorteo" (abre la cid 1).

Medido, no supuesto:

- la lista trae **8 filas del juego** con cids 33, 5, 8, 27, 36, 34, 35, 37, y **esas 8 muestran su
  nombre bien**; a partir de la novena, todas enseñan el nombre de la cid 1;
- el item de la lista son **12 bytes**: `{cid:4, ffff:2, 0000:2, 0:4}` — no lleva el nombre, el
  menú lo busca por el cid;
- **descartado** el tope de 300 del resolutor `0x14150af30` (`fl26caps` ya lo sube a 1200 en
  `0x14150afb0` y `0x14150b00e`);
- **descartado** `phkind` para esto: devuelve `0xffff` en todas nuestras copas porque son
  eliminatorias sin fase de grupos, y eso es correcto;
- los datos están bien: los 168 nombres están en `Competition.bin +0x14` (16 B, truncado a 15) y
  en las 20 ranuras de 70 B de su regulación.

Hipótesis principal: el constructor de filas del menú (`0x140b1c990` y sus ayudantes
`0x140e4bba0`, `0x140b1cc60`, y el bucle de `0x140e43450` que recorre filas de 0x50 B llamando a
`0x140e4c240`) resuelve el nombre por una tabla que solo cubre las 8 copas de fábrica; lo que cae
fuera se va al registro 0 (cid 1 = FIFA Club World Cup), que además no tiene sorteo → cierre.

Siguiente paso propuesto: instrumentar `0x140e4bba0` y `0x140b1cc60` (o buscar la tabla con un
depurador; el juego corre elevado y no se puede enganchar) para ver qué cid consultan por fila, y
con eso o ensanchar la tabla en tiempo de ejecución (tabla propia de 1024 entradas, como se hizo
con el censo) o parchear el constructor.

### Medido después (sonda `CUPAFTER`, 2026-11-04 16:13)

El handler ya no salta en cola al init: lo llama y vuelca el estado al volver. Resultado:

- la lista **conserva** nuestros cids después del init (`item 8 cid=513`, `item 9 cid=96`,
  `item 10 cid=250`…), así que el menú no los reescribe;
- `self+0x88` **no** es un array de filas: apunta a la cadena `"compeSelect"` (el nombre de la
  pantalla), así que el bucle de `0x140e43450` recorre otra cosa;
- la lista queda con `list=175 cap=0x5F40C00` (los 256 huecos del stub de `fl26cupgrow`).

Conclusión: el nombre se resuelve **al dibujar**, no al construir la lista, y la resolución por
cid falla para las nuestras. Eso ya necesita un depurador (el juego corre elevado y REA/rizin no
se pueden enganchar) o alguien que conozca el código del menú: es el punto exacto que hay que
preguntar a Matozanato.

## 6. Otras cosas pendientes, menores

- **Emblemas**: se piden por `emb_<cid & 0xFF>`, así que una competición con cid ≥ 256 comparte
  emblema con la que tenga ese byte bajo (la fila muestra el escudo de otra). Generados los de
  nuestras 8 continentales y las 20 estaduales; el Mundial conserva el del juego.
- **Plantillas clonadas**: los 112 clubes de las ligas nuevas y los 17 de los estaduales son
  clones del mismo once (mismas 22 notas). Falta diversificarlos por nivel de liga.
- **3 clubes de relleno** (`74284..74286`, "Brazil State Pool Club 18..20") quedaron sin
  competición al borrar la liga temporal.
- **Kits**: los clubes nuevos heredan la equipación del prototipo.

## 7. Cómo ponerlo en marcha

1. Copiar `pesdb/*` a `<juego>\SiderAddons\livecpk\_FL26MyWorld\common\etc\pesdb\`.
2. Copiar `fl26world.txt` a `<juego>\SiderAddons\livecpk\_FL26MyWorld\` **y** a
   `<juego>\SiderAddons\modules\` (los dos tienen que ser iguales).
3. Copiar los módulos de `modules/` a `<juego>\SiderAddons\modules\` y usar el `sider.ini` de
   ejemplo: `fl26cid16.lua` **después** de `fl26regs1200.lua`, y `fl26cupgrow.lua` **después** de
   `fl26swiss.lua`.
4. `fl26swiss.dll`: el de fábrica del mod. La versión con sondas está en el repo
   (`tools/native/fl26swiss.c`, commit `1a8e7fc`) si quieres ver los 12 bytes de cada fila.

## 8. Commits de la sesión (repo `pes-2021`, rama `cwc-next`)

```
1a8e7fc chore(fork): fuera el modulo de los 300 (fl26caps ya lo parcheaba) y sonda CUPRES
06ba3d7 fix(fork): el resolutor de copas solo recorria 300 regulaciones
de51c21 feat(fork): el buffer de copas pasa de 64 a 256 filas y quedan las cuentas
15caba5 fix(fork): las 19 copas del mundo entran en Kick Off > Cup (fl26cupgrow)
200f021 fix(tools): mkccup writes the 16-byte menu name at Competition.bin +0x14
fff5a7f feat(fork): el censo de Select Team usa cid de 16 bits (tabla plana, mapa intacto)
e4db1bc feat(tools): move_cids.py -- el juego busca la lista por el byte bajo del cid
6ab6e33 feat(tools): emblemas para todo el mundo y la clave real del byte bajo
```

Herramientas nuevas o tocadas: `tools/move_cids.py`, `tools/generic_clubs.py`,
`tools/add_league_generic.py`, `tools/mkcrests_missing.py`, `tools/mkemblems.py` (cid de 16 bits,
`--missing`, `--shipped`, `--bytes`), `tools/fill_group.py` (cid de 16 bits), `tools/mkccup.py`
(nombre en `+0x14`).

## El nombre sale de la tabla de textos del juego (medido 2026-11-04, 17:xx)

Los nombres de competición que pinta el menú **no están en las tablas del mundo**: están en

    <idioma>/string/all.str      (data_s2526a.cpk; WESYS + zlib, 1,3 MB al descomprimir)

que es un fichero suelto y por tanto se puede servir por livecpk. Formato:

    u32 208                        numero de entradas
    208 x 3 u32                    indice (offset de la clave + dos campos)
    pool UTF-8 con NUL             desde el offset 2504 (las claves van ordenadas)

Las claves del indice son cortas y alfabeticas ("All1C", "Chg1C", "Cmt1T", "E10W"...).  Dentro
del pool hay ademas un bloque de **nombres de competicion**, que es el que se pinta:

    League | Eredivisie | Spanish League | Africa | Asia-Oceania | Italian Cup | Spanish Cup |
    Netherlands Cup | England Cup | French Cup | Germany Cup | Europe | Other | South America |
    League | Other European Leagues | Other Latin American Teams | na | nb | FIFA Club World Cup |
    European Qualifiers | African Regional Qualifiers | ...

`FIFA Club World Cup` aparece ahi como una entrada mas, y eso es lo que salia en todas nuestras
filas: no hay entrada para `FL_C700` y se cae a esa.

Lo que falta para escribir nombres: identificar los dos campos que acompañan al offset en el
indice (para saber si la clave es un id numerico, un hash o la propia cadena) y ver si el bloque
de nombres se indexa por posicion o por hash.  Con eso se añaden las 168 cadenas al pool, sus
entradas al indice, y se apunta a ellas el `+0x38` de la fila de cada copa (o se deja que el juego
las resuelva por codigo).  No se toca el ejecutable: basta el fichero por livecpk.

## Estado del nombre al cerrar la sesion (2026-11-04, 20:2x)

- El menu **abre y lista las 175 filas** (`167 world cup(s) added, all in (list 175 of 256)`) con el
  stub de `fl26cupgrow` y sus guardas; las copas estan ordenadas alfabeticamente en el world file.
- El nombre **sale del byte bajo del cid**: una copa con `cid & 0xFF == 27` muestra "FIFA World Cup",
  otra con 88 muestra "Maltese Premier League", etc.  Las de cid < 256 (Gold Cup 96, OFC 250/251,
  Nations Leagues 252/253) salen bien.  Es el mismo truncamiento que ya se arreglo para la lista de
  clubes (censo) y que sigue vivo en la ruta del nombre y en el emblema.
- `phkind(cid, 3)` (0x14150af30) es el que convierte cid -> regulacion de una copa, y responde
  `0xffff` para cid >= 256: compara `dword [registro+0x80]` con el cid y ese campo solo lleva el
  byte bajo.
- `fl26regcid.lua` intenta rellenarlo, pero **la direccion del array no es la que usa el exe**:
  leyendo `[[0x143705e10]+0x48] + 0xc12e9c` sale `count=65535 firstid=65535`.  La cadena buena
  arranca en `0x1414b6a60()` (que usa phkind) y no en ese global; falta probarla desde Lua
  (ffi.cast de 0x1414b6a60) o conocerla de quien escribio el modulo.
- Con el campo `+0x80` correcto deberian caer **nombre y tamano de sorteo** a la vez: el menu abre
  la competicion 1 (que no tiene sorteo) cuando no encuentra la suya, y de ahi el cierre al entrar.

### Segunda medicion de la cadena (2026-11-04, 20:34)

Llamando por ffi a `0x1414b6a60()` (lo mismo que hace phkind) y leyendo `[rax+0x48]`:

    ctx=0x114643c0  block=0x7ff4df840010  count=65535  firstid=65535

O sea: la cadena del contexto **si** es la misma que la del global (`ctx+0x48` = el mismo bloque),
pero en ese bloque los offsets que tenemos apuntan a otra cosa: `+0xd0bcf4` no da la cuenta (sale
el centinela 0xffff) y `+0xc12e9c` no da registros con id razonable.

Conclusion: los offsets `0xc12e9c`/`0xd0bcf4` que se anotaron en su dia no son relativos a este
bloque, o el bloque correcto es otro campo de `ctx`.  Sin saberlo, escribir `+0x80` es a ciegas.

Lo que queda, entonces, es una pregunta de una linea para quien conozca el binario (o resolverlo con
depurador, que no se puede enganchar porque el juego corre elevado):

    en FL_2026.exe, phkind (0x14150af30) lee la cuenta en [block+0xd0bcf4] y los registros de
    0x314 bytes en [block+0xc12e9c], con block = [ctx+0x48] y ctx = 0x1414b6a60().
    Medido: block=0x7ff4df840010 da count=65535 y firstid=65535.
    ¿Cual es el bloque correcto, o que offsets usa de verdad el censo de Select Team?

## Como esta construida una copa de selecciones de las del juego (UEFA EURO)

Medido de las tablas del mundo:

| competicion | entradas | regulaciones | forma |
|---|---|---|---|
| UEFA EURO (cid 33) | 24 | maestra 41 `type 2` 24 equipos + 6 replicas (grupo 0..5) + KO 42 `type 3` 16 | 6 grupos de 4 -> eliminatoria de 16 |
| Copa America (34) | 16 | maestra 104 `type 2` 12 + 3 replicas + KO 43 `type 3` 8 | 3 grupos de 4 -> KO de 8 |
| FIFA World Cup (27) | 32 | maestra 34 `type 2` 32 + 8 replicas + KO 35 `type 3` 16 | 8 grupos de 4 -> KO de 16 |
| CONCACAF Gold Cup (96) | 16 | una sola reg 179 `type 3` 16 | eliminatoria directa |
| OFC Nations Cup (250) | 8 | una sola reg 183 `type 3` 8 | eliminatoria directa |

Reglas: `type 2` = fase de grupos (la maestra lleva el total y una replica por grupo con id
maestra + 1024*k, `group` = k); `type 3` = eliminatoria.  El dword de `+0x10` lleva la division y
la forma.  Nuestras 145 copas son `type 3` con el tamano exacto de sus entradas: igual que la Gold
Cup, correctas.

Las 21 copas del juego que desbloqueamos tienen regulaciones suyas con `type` 4, 8 o 9 en varios
casos (Spain Cup 4, Chile 8, Russia 9): ponerles `like=23` en la linea (forma de FA Cup) no casa
con su forma y las bloquea, asi que se ha quitado el `like=` de esas 22 lineas (2026-11-04).
