# Limites: ligas solas y copas solas (2026-11-06)

Estado del mundo: **153 ligas**, **286 ccup**, 511 competiciones, 710 regulaciones,
5.620 entradas, 3.648 equipos, 103.722 jugadores.

## Ligas solas

Cada liga necesita **1 competicion (cid)**, **1 regulacion** y **1 slot** de Select Team.

| recurso | ahora | tope | libre |
|---|---|---|---|
| slots de Select Team | 140 (136 ligas + 4 pools) | **250** (`fl26slots250`) | **110** |
| competiciones (cid) | 511 | 1.023 (`fl26cid16`) | 512 |
| regulaciones | 710 | 1.200 (`fl26regs1200`) | 490 |

**El que manda son los slots: quedan 110 ligas mas** (hasta 250). Las competiciones y
regulaciones no son el limite para ligas.

## Copas solas

Las copas **no gastan slots de Select Team**; gastan 1 competicion, 1 regulacion por
eliminatoria (10 por copa de grupos: maestra + 8 replicas + KO) y **1 fila** en Kick Off > Cup.

| recurso | ahora | tope | libre |
|---|---|---|---|
| filas del menu de copas | 294 (8 del juego + 286) | **1.024** (`fl26cupgrow`) | 730 |
| competiciones (cid) | 511 | 1.023 | 512 |
| regulaciones | 710 | 1.200 | 490 |

**Tope por datos: ~490 copas de eliminatoria** (la regulacion es lo que antes se agota) o
**~49 copas de grupos** (10 regulaciones cada una). El menu aguanta 730 filas mas, asi que no
es el limite.

**En la practica** el limite hoy no son los numeros: es el defecto de la primera entrada y el
cierre `0x3fd2b2` al abrir Copa (ver `copa-cierre-y-blanco.md`).

## Cierre comprobado

El juego (pid 41284) se cerro a las **11:17:28** con `0x3fd2b2` (pool free) al abrir Copa, con
el DLL 378.880 restaurado: el cierre no era del build nuevo.
