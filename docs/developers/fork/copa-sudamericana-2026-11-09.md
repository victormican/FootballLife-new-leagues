# Copa Sudamericana propia: del constructor del mundo a Kick Off (2026-11-09)

## Lo que se buscaba

Una copa internacional propia (tipo Sudamericana) **jugable en Kick Off > Copa**, sin depender de
Master League. La copa nueva (cid 132) no puede jugarse en Kick Off: el planificador solo conoce
las competiciones que trae el juego y el modo cierra al elegirla.

## 1. Copa desde el constructor del mundo

Receta `out/recipe-sud.json`:

```json
{
  "world": "_FL26Sud",
  "leagues": [
    { "name": "Liga Nueva", "country": "Bolivia", "clubs": 16, "legs": 2,
      "cup": true, "cup_name": "Copa Nueva",
      "europe": [[1, 9], [2, 9], [3, 9], [4, 9]] }
  ]
}
```

`europe` con la competición 9 (Sudamericana) da a la liga nueva sus cuatro plazas. El constructor
planifica la copa con las plazas del mundo y las del juego:

```
Copa Sudamericana: competition 132, 32 clubs, groups 318, knockout 319
```

y escribe en `fl26world.txt`:

```
ccup 318 ko=319 groups=8 entry=11:1,29:7,30:7,67:3,168:3,11:2,... cid=132 name=Copa Sudamericana
```

Es una copa de temporada: `fl26swiss` la rellena de las tablas de las ligas, la sortea, la fecha y
la avanza. En Kick Off no se puede jugar (cid nuevo, sin plan).

## 2. El bug del constructor

`leaguebuilder.ccup_options` asumía que toda copa tenía `opts` (relleno/fechas). Una copa
continental no los tiene y el build caía con `TypeError: 'NoneType' object is not subscriptable`.
La guarda deja la línea tal cual, conservando el `cid=` que necesita `fl26swiss`:

```python
if not o:
    if cup.get("cid") and " cid=" not in line:
        head, sep, name = line.partition(" name=")
        return "%s cid=%d%s%s" % (head, cup["cid"], sep, name)
    return line
```

## 3. Exponerla en Kick Off: clon de una plaza nativa

La única plaza que el motor conoce y que tiene el formato de la Sudamericana (32 clubes, 8 grupos)
es la **Copa Libertadores (cid 5)**. `tools/clone_shipped_cup.py` conserva id, slot, fechas y
reglas, y cambia entradas y nombre:

```powershell
python tools/clone_shipped_cup.py `
  --base <mundo>\common\etc\pesdb --out <mundo> `
  --cid 5 --reg 9 --code FL_SUDAM --name "Copa Sudamericana" `
  --teams 318:1,318:2,...,318:32
```

- `--reg 9`: la regulación maestra de la Libertadores (grupo 255, 32 equipos, 8 grupos).
- `--teams`: las 32 entradas de la Sudamericana del mundo (regulación 318), resueltas a ids.
- Resultado: cid 5 con 32 entradas nuestras y la regulación 9 renombrada `Copa Sudamericana`.

En Kick Off > Copa es el **último item** de la lista (el orden nativo termina en cid 5).

## 4. `EXPOSE = 0`

`fl26swiss.lua` expone en Kick Off > Cup las copas del mundo (`ccup`). Una copa de cid nuevo
(cid 132) cierra el juego al listarse, así que se deja en 0: Kick Off solo lista las 10 del juego;
la Sudamericana del mundo vive en la temporada y la jugable de Kick Off es el clon del cid 5.

## Archivos

- `out/recipe-sud.json` (receta)
- `tools/leaguebuilder.py` (`ccup_options`)
- `tools/clone_shipped_cup.py` (clon)
- `sider/experimental/fl26swiss.lua` (`EXPOSE = 0`)
- `tools/native/fl26swiss.c` (guarda del calendario en `cal_dedupe`)
