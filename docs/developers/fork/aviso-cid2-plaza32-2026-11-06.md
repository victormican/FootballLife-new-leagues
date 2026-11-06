# El aviso de la plaza 32: es del juego, no nuestro

2026-11-06. `check_world` venia diciendo:

```
WARN entry: competition 2 has two clubs at position 32 (a shipped cup with several stages)
```

## Diagnostico

La competicion 2 es una copa europea del juego. Sus entradas en el mundo (`CompetitionEntry.bin`)
tenian **33 filas**: plazas 1..31 con un club, **una fila con equipo 0 en la plaza 28** y **dos
clubes en la plaza 32** (Atalanta BC y Athletic Bilbao).

El defecto **no lo generamos nosotros**: esta en los datapacks originales. Leidos los cinco
`pesdb\pristine\data_s2526*\common\etc\pesdb\CompetitionEntry.bin`:

| datapack | filas cid 2 | plazas |
|---|---|---|
| data_s2526  | 32 | 1..32 |
| data_s25262 | 33 | 1..32 + 32 |
| data_s2526b | 33 | 1..32 + 32 |
| data_s2526c | 33 | 1..32 + 32 |
| data_s2526d | 33 | 1..32 + 32 |

Y en el datapack con 32 filas la plaza 28 es **equipo 0** igualmente. O sea: el juego trae un
hueco y un duplicado en esa copa, y el mundo los copio tal cual.

## Arreglo

`tools/fix_cid2_entries.py` (con copia de seguridad) quita la fila del equipo 0 y renumera las
32 filas validas a plazas 1..32 conservando el orden. Solo cambia el byte de la plaza (`+9`); el
cid alto de `+0x0b` no se toca.

```
python tools/fix_cid2_entries.py --pesdb "D:\...\_FL26MyWorld\common\etc\pesdb"
```

Resultado: 5.667 entradas, copa 2 con 32 clubes en plazas 1..32, y `check_world`:

```
teams 3648 (239 national), players 103722, assignments 93338, competitions 512, regulations 711, entries 5667
world file: 154 leagues, 152 slots 22..248, 286 ccup lines
0 error(s), 0 warning(s)
```

## Nota para el generador

Si el mundo se reconstruye desde los datapacks, el defecto vuelve. El paso que copia
`CompetitionEntry` del juego tiene que pasar por `fix_cid2_entries.py` (o por la misma logica:
fuera equipos 0 y plazas unicas) para que el aviso no reaparezca.
