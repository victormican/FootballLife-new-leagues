# Copas de grupos duplicadas: 533 → 542 líneas `ccup` (2026-11-06)

## 1. Primero: la Russia Cup había desaparecido

Al arrancar había **532** líneas `ccup`, no 533. Faltaba una: la **Russia Cup**.

- `tools/fix_world_names.py` reescribía **todo** `name=` que no coincidiera con el nombre de su
  regulación. La regulación 115 guarda el registro de Bélgica (`Jupiler Pro League`), así que
  renombró la línea de la Russia Cup a "Jupiler Pro League".
- Después, al quitar la cup belga mal formada, esa línea se borró con ella.

Arreglo: el script ahora **solo reescribe texto corrupto** (mojibake, controles C1, caracteres
> U+2FFF); un nombre distinto pero legible se deja como está. La línea se restauró desde
`fl26world.txt.before-names` (`tools/restore_missing_cups.py`):

```
ccup 115 ko=115 groups=0 entry=0:5196,... cid=115 fill=20 national=1 days=20,27,34,41 \
     clubs=5196,... name=Russia Cup
```

## 2. Las 9 copas que `dup_cups.py` dejaba fuera

`dup_cups.py` solo duplica eliminatorias directas (`groups=0`). Quedaban 9:

- **8 copas de grupos** (`groups>0`): CAF Champions League, CAF Confederation Cup, AFC Champions
  League Two, Copa Caribena CONCACAF, Copa Sudamericana, FIFA World Cup, Leagues Cup, UEFA
  Conference League.
- **Copa Intercontinental**: no tiene entradas propias (se llena con los campeones de las copas
  `entry=2:0,8:0`).

Cada copa de grupos son **diez filas**: la regulación maestra (`type 2`), una réplica por grupo en
`maestra + 1024 * (g + 1)`, y la eliminatoria (`type 3`). `fl26swiss` reconoce un grupo por
`id & 0x3ff`, así que **la maestra y la eliminatoria tienen que quedar por debajo de 1024**; una
maestra mayor rompería la aritmética de las réplicas.

`tools/dup_cups_groups.py` (nuevo) hace las cuatro cosas:

| qué | cómo |
|---|---|
| competición | fila copiada, cid nuevo, código `FL_DUP_<cid>` |
| regulaciones | maestra + réplicas + eliminatoria, ids nuevos < 1024, cid nuevo |
| entradas | todas las de la copa original, con cid y eid nuevos |
| línea `ccup` | `ccup <maestra nueva> ko=<ko nuevo> cid=<cid nuevo> … name=<nombre> II` |

Las copias llevan **`national=1`**: si no, entrarían en `ccup_taken` y se llevarían los clubes que
la copa original ya tiene (la CAF Champions League II robaría los de la Confederation Cup, que se
llena después). Con `national=1` la copia juega con **los mismos clubes** que su original, igual
que las 262 copias de eliminatoria que ya había.

## 3. Resultado

```
cups for this pass: 9
  AFC Champions League Two   cid 424  master 537  ko 779  groups 8 (32 entries)
  CAF Champions League       cid 661  master 780  ko 781  groups 8 (32 entries)
  CAF Confederation Cup      cid 662  master 782  ko 783  groups 8 (32 entries)
  Copa Caribena CONCACAF     cid 663  master 784  ko 785  groups 4 (16 entries)
  Copa Intercontinental      cid 664  master 786  ko 786  groups 0 (0 entries)
  Copa Sudamericana          cid 665  master 787  ko 788  groups 8 (32 entries)
  FIFA World Cup             cid 666  master 789  ko 790  groups 8 (32 entries)
  Leagues Cup                cid 667  master 791  ko 792  groups 8 (32 entries)
  UEFA Conference League     cid 668  master 793  ko 794  groups 8 (32 entries)
planned: 9 cups, 77 regulations, 240 entries
```

```
check_world: 767 competiciones, 1.031 regulaciones, 7.520 entradas
             153 ligas, 136 slots, **542 líneas ccup**, 0 errores
sider.log:   world file -- 542 cup(s) for Kick Off > Cup, 542 taken
             fl26cupgrow: 16 buffers of 1024 items
```

Las 9 copias están en la lista del DLL (`cup 537 (knockout 779) from the world file: 8 groups,
32 entries`, …), no entre las rechazadas.

## 4. Pendiente

- Ver en **Kick Off > Cup** que aparecen las 542 (las copias llevan el sufijo ` II`).
- El llenado de las copas de grupos ocurre a finales de agosto, no al arrancar: hasta que no se
  juegue una temporada no se verá el cuadro. Los avisos a mirar en `sider.log` son
  `cup N -- only X of Y clubs found; not started` y `its rows are not all in this world`.
- El menú ya está en 1.024 filas (`fl26cupgrow` WANT 1024, stub `0x3000`) y el DLL en
  `MAX_CCUP 1024`; 542 cabe de sobra.
