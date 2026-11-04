# Ids de competición por encima de 255

2026-11-03. Estado del parche que abre el presupuesto de competiciones: **las copas ya pueden
usar `cid` 256..1023**; las ligas siguen limitadas a 255 porque el censo de Select Team indexa con
un byte. Prueba viva: la copa **Cupa Moldovei** (cid 256, reg 268) sale en Kick Off > Cup.

## Por qué hacía falta

Una copa gasta un `cid` y el mundo iba por 249 de 255. El `cid` es un byte en las tres tablas
(`Competition.bin` +5, `CompetitionEntry.bin` +8, `CompetitionRegulation.bin` +8) y la clave de las
entradas lo empaqueta con la plaza (`id << 8 | plaza-1`, 16 bits). En memoria, en cambio, el motor
lo guarda en 16 bits y el array tiene 600 huecos.

## Dónde vive el byte alto (medido, no supuesto)

| tabla | offset | qué había ahí |
|---|---|---|
| `Competition.bin` | **+0x07** | libre: cero en las 249 filas |
| `CompetitionEntry.bin` | **+0x0B** | libre: cero en las 3.896 filas |
| `CompetitionRegulation.bin` | **+0x492** | libre: el hueco de 32 ceros entre las dos tandas de nombres |

**Dos trampas que tumbaron los planes anteriores:**

1. **`+0x20` no es libre**: el nombre son 16 bytes desde +0x14, así que +0x20..+0x23 son su cola.
   En las tablas del juego quedan a cero porque los nombres son cortos ("GUE"), pero una liga
   nuestra ("Belize Premier") los llena. Poner ahí la palabra del id habría cambiado nombres.
2. **`+0x910` tampoco**: la ranura de nombre 19 empieza en 0x8BD y mide 0x73, o sea que acaba
   justo en 0x930: +0x910 cae **dentro** del nombre. Además `put_names` lo reescribe, así que la
   copa se quedó con `cid` 0 hasta que se movió a +0x492.

## El parche (`sider/experimental/fl26cid16.lua`)

Tres cuevas, verificando antes todos los bytes del ejecutable:

| sitio | qué hace |
|---|---|
| `0x1414f1609` (22 B) | empaqueta la entrada: `id = byte[+8] \| byte[+0xB] << 8`, clave `id << 6 \| (plaza-1)` (las plazas nunca llegan a 64) |
| `0x141eee27c` (6 B) | regulación buscada por `cid`: el byte alto sale de `+0x492` |
| `0x1414f1500` (7 B) | censo de Select Team: `id = byte[+5] \| byte[+7] << 8` (ver abajo) |

**Trampa medida (2026-11-03):** la cueva del empaquetado **no puede usar `edx`**. El bucle que la
llama lo tiene vivo como puntero de escritura del vector y el `movups [rdx], xmm0` de
`0x1414f174e` revienta: el selector de equipos del Mundial se cerraba al abrirlo. La versión buena
mete el byte alto en `ah` (`8a 67 02`) y desplaza `ax`: `(alto<<8|bajo) << 6 = alto<<14 | bajo<<6`,
sin tocar más registros que el `eax`/`ecx` originales.

Interruptores `ENABLE = { cmp, cid, pack, reg }` para biseccionar sin editar el código.

## El censo: resuelto el 2026-11-04 (tabla plana, no se toca el mapa)

El censo de Select Team guarda un **`std::map<byte, fila*>`** y sus dos bucles buscan la
competición de cada entrada por ese mapa. Ahí estaba la trampa: el `insert` (`0x1414e36f0`)
**deduplica por ese único byte**, así que dos competiciones que comparten byte bajo no pueden
coexistir en él. Por eso el intento anterior (ensanchar los `cmp` a dword) moría a los 25 s: la
clave de 16 bits nunca se guardaba en el nodo y el árbol comparaba basura.

La solución que funciona deja el mapa quieto y **puentea las búsquedas** a una tabla propia de
1024 punteros:

| sitio | qué hace ahora |
|---|---|
| `0x1414f1d6a`, `0x1414f1e5a` | la clave pasa a `byte[+8] \| byte[+0x0b] << 8` (mismo campo que el empaquetado) |
| `0x1414f1576` | al insertar, además `tabla[cid] = fila` |
| `0x1414f1d8b`, `0x1414f1ea1` | las búsquedas devuelven `&tabla[cid] - 0x28` |

Dos cosas medidas a base de crashes, que hay que respetar si se reescribe:

1. **Lo que el llamante espera es un puntero al hueco, no la fila.** Hace `r8 = iterador + 0x28`
   y luego `0x1414f7e80` ejecuta `mov rax,[r15]; mov ecx,[rax+4]`. Devolver la fila hace que lea
   su primer campo como puntero → `0xc0000005` en `0x1414f7ffc`.
2. **Un cid sin fila no puede devolver 0**: el hueco vacío se detecta con
   `cmp qword [tabla+cid*8], 0` y se cae al `find` original del mapa, que es el comportamiento de
   antes. Sin ese fallback, también `0xc0000005` en el mismo sitio.

La tabla vive en la cueva (`+0x1000`), el cid se enmascara a `0x3ff` y el módulo verifica los cinco
sitios antes de escribir nada. Con esto **desaparece el techo de los doce bytes bajos**: una liga o
una copa con `cid` 256..1023 tiene su lista de clubes propia. Probado en vivo el 2026-11-04
(`map=true`, sin crash).

Queda pendiente, si algún día molesta: el **emblema** se sigue pidiendo por el byte bajo
(`emb_<cid & 0xFF>`), que es otra ruta distinta de esta.

## Cómo se usa

`tools/mkccup.py` ya escribe el byte alto en los tres sitios (`M.set_comp_cid`, `M.R_CID_HI`,
`M.E_CID_HI`):

```
python tools/mkccup.py --base "<pesdb>" --out "<livecpk>" --cup \
  "Cupa Moldovei|FL_MD_CUP|256|268|268|0|356:1,...,356:8|2|29|23"
```

y en el mundo, con `cid=` para que salga en el menú:

```
ccup 268 ko=268 groups=0 entry=356:1,... cid=256 conf=2 region=29 national=1 like=23 name=Cupa Moldovei
```

`check_world` ya lee los ids como 16 bits (`M.comp_cid`, `M.R_CID_HI`, `M.E_CID_HI`) y el tope que
vigila es **1023**, el que aguanta la clave de las entradas.

## Prueba

```
python tools/check_world.py ...            0 errores (11 ccup)
sider.log   world file -- 11 cup(s) for Kick Off > Cup, 11 taken
sider.log   cup 268 from the world file: a single-match knockout of 8, shaped and dated as reg 23
sider.log   Cup mode: 11 competition(s) of the world to expose
2 de 2 arranques vivos 55 s, 0 aborting
```

Al abrir Kick Off > Cup aparece **Cupa Moldovei** al lado de las copas del juego.
