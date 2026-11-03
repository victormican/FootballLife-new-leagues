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

Interruptores `ENABLE = { cmp, cid, pack, reg }` para biseccionar sin editar el código.

## Lo que falta: las ligas

El censo de Select Team guarda la clave del mapa en un nodo con un **byte** (`cmp byte [rax+0x20],
cl`). El plan original lo cambiaba a dword igual que el almacén (`89 4d 68`); con esos dos parches
el juego **muere a los 25 s** siempre: la cola del nodo no es cero y las comparaciones se vuelven
basura. Por eso `cmp` y `cid` quedan **apagados** y una liga con `cid > 255` no aparecería en
Select Team: los datos se escribirían bien, pero el censo la agruparía por el byte bajo.

Para cerrarlo hace falta rehacer ese mapa (clave de 16 bits de verdad: nodo más ancho o un mapa
auxiliar), y comprobar si algún otro lector del id de `Competition.bin` sigue leyendo +5 a pelo.
Con las copas no hace falta: no pasan por Select Team.

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
