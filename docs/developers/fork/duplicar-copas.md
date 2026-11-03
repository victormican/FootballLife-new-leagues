# Duplicar competiciones: qué funciona y qué no

2026-11-03. Pregunta: ¿se puede duplicar una copa para tener muchas sin gastar `cid`? Respuesta
corta: **duplicar funciona para ligas** (la lista de Select Team va por regulación y cada twin
tiene su slot) y **no para copas** (el menú de copas va por competición y una competición es una
copa). Aquí queda el porqué medido y lo que habría que enganchar para las copas.

## La duplicación que ya existe: twins de liga

`tools/add_twin_leagues.py` escribe una **regulación gemela**: una fila nueva en
`CompetitionRegulation.bin` que copia otra (mismo `cid`, mismos clubes) y solo cambia el `rid`, el
nombre y el slot. No añade competición, ni entradas, ni clubes, ni jugadores: el mundo sigue dentro
de los 255 ids.

Funciona porque **Select Team se construye por id de regulación**: `fl26comptab` añade una fila de
la tabla de parámetros por cada línea `league` del mundo, y su `id` es el `rid`. Dos regulaciones
con el mismo `cid` y slots distintos son dos entradas seleccionables, y `fl26clubs` responde con los
clubes que el mundo da a cada slot. En Master League comparten objeto de competición; eso es lo que
hay que vigilar.

## Por qué una copa no se puede duplicar así

El menú de copas es `MenuModeCupSelect` y lo engancha `fl26swiss.dll` (`cupsel_handler`). Su lista
son items de **12 bytes** con el **`cid` en +0**; al añadir una copa del mundo copia un item
existente para que el nombre y el escudo tengan plantilla y **sustituye el `cid`**:

```c
if (w > *pb) memcpy(w, *pb, 12); else memset(w, 0, 12);
*(uint32_t*)w = cid;          /* el id de la COMPETICIÓN */
```

Y antes de añadir, ya deduplica por `cid`:

```c
for (p = *pb; p + 12 <= w; p += 12) if (*(uint32_t*)p == cid) there = 1;
```

O sea: **la lista de copas está indexada por competición, no por regulación**. Dos copas con el
mismo `cid` son el mismo item (la segunda se descarta) y, al elegirla, el juego resuelve la
competición por ese id y toma la regulación de la temporada. Las regulaciones hermanas de una misma
`cid` que ya existen (reg 34, 1058, 2082… del Mundial) son **copias por temporada**, no copas
distintas.

## Lo que habría que enganchar para duplicar copas

1. **Llevar la regulación en el item.** Los 12 bytes son `cid` + 8 de plantilla (nombre/escudo).
   Hay que ver si el consumidor lee algo de esos 8; si no, se puede usar +4 como `rid` y
   rellenarlo en el handler.
2. **Cambiar la clave de la lista** de `cid` a `(cid, rid)`: al añadir, la deduplicación mira el par;
   al elegir, el juego debe cargar la regulación del item y no la de la temporada.
3. **Encontrar el consumidor**: la función que toma el item seleccionado y abre la competición
   (vtable de `MenuModeCupSelect`, `0x142692c40`; el init está en `0x141b1c990`). Hay que localizar
   dónde lee `+0` del item y de dónde saca la regulación.
4. **Probar con una copa duplicada de verdad**: mismo `cid`, otro `rid`, mismo cuadro, y ver si las
   dos salen y se juegan.

Coste realista: una sesión de RE (encontrar el consumidor) y una de módulo. Riesgo: el punto 2 toca
la ruta que ya nos dio guerra con el censo de ids de 16 bits.

## Alternativas mientras tanto

- **5 `cid` libres** (96, 250-253): cinco copas.
- **Copas de confederación** con `clubs=` invitados: una copa puede llevar clubes de muchas ligas,
  así que 5 copas cubren mucho terreno aunque no sean «la copa de cada país».
- **Liberar ids** retirando competiciones que no se usen (riesgo: el juego necesita las suyas).
