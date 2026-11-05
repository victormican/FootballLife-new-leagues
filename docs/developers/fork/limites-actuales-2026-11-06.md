# Límites actuales del mundo (2026-11-06)

Sustituye a `limites-actuales-2026-11-05.md` en los números. Estado del mundo hoy:

```
154 ligas · 137 slots · 286 ccup · 511 competiciones · 710 regulaciones
5.620 entradas · 3.648 equipos · 103.722 jugadores
```

| recurso | usado | tope | libre | quién lo pone |
|---|---|---|---|---|
| **slots de Select Team** | **137** | **500** (`fl26slots500`) | **363** | `mkslots.py` |
| competiciones (cid) | 511 | 1.023 | 512 | `fl26cid16` (tabla plana) |
| regulaciones | 710 | 1.200 | 490 | `fl26caps` + `fl26regs1200` |
| filas Kick Off > Cup | 294 | 1.024 | 730 | `fl26cupgrow` |
| equipos | 3.648 | 4.800 | 1.152 | `fl26caps` |
| jugadores | 103.722 | 123.825 | 20.103 | `fl26caps` |
| entrenadores | ~1.078 | 6.800 | 5.700 | `fl26caps` |

## Slots: 500 (antes 250)

`tools/fl26slots500.lua` (generado con `mkslots.py 500`) deja:

- **500 slots** (123 sigue siendo el centinela "ninguno"; válidos 0..122 y 124..499).
- **159 clubes por slot** ordinario (antes 324 con 250); slots 79/80 (los agregados del
  juego) conservan 1.600; 0..5 y 69..78 conservan 750.
- 159 basta: la liga más grande del mundo tiene 87 clubes.

El fallo al subir de 250 no eran las 15 comparaciones de cota (`cmp r32, imm8`): era que la
tabla de offsets (`PAGE+0x800`, `4*N` bytes) **se solapaba con la de capacidades**
(`PAGE+0xC00`) a partir de N>256. Ver `rea-cotas-slots-500-2026-11-06.md`.

## Ligas solas

Cada liga gasta 1 slot, 1 competición y 1 regulación. **El slot manda: caben 363 ligas más**
(hasta 500). Comps (512 libres) y regulaciones (490) no son el límite para ligas.

Ojo: una liga por slot; no se comparten slots (y `fl26comptab` aborta la tabla si dos filas
piden el mismo — lección del slot 22, ver `regresion-slot22-2026-11-06.md`).

## Copas solas

Las copas no gastan slot de Select Team. Grastan 1 competición, **1 regulación por eliminatoria**
(10 por copa de grupos: maestra + 8 réplicas + KO) y 1 fila de menú.

- **~490 copas de eliminatoria** (la regulación es lo primero que se agota).
- **~49 copas de grupos** (10 regulaciones cada una).
- Filas de menú: 730 libres, no es el límite.

En la práctica el techo hoy es el **cierre `0x3fd2b2` al abrir Copa** (buffer de la lista,
ver `copa-cierre-y-blanco.md`), no los números.

## Reglas aprendidas

1. `country` = **id de bandera** (no la fila de `Country.bin`).
2. Las filas de copa **no pueden compartir un slot real**: comptab aborta la tabla entera.
3. El world file solo se toca con Python UTF-8 (`io.open`), nunca con `Get-Content -Raw` (ANSI).
4. Una liga nueva: `league <reg> cid=... slot=...` con slot libre y `country` de bandera.
5. Una copa nueva: 1 competición + 1 regulación (o 10 si es de grupos) + línea `ccup`.
