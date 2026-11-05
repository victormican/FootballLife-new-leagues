# Todos los slots de liga servidos (2026-11-06)

Sintoma del usuario: en Select Team hay slots con **1 o 2 equipos** (las listas del juego, no
las nuestras). El log lo confirmaba: `fl26clubs` servia solo **19 slots**; las otras ~118 ligas
del mundo dependian de la lista del juego, que en slots de competiciones no usadas trae 1-2.

## Cambios

- `tools/native/fl26clubs.c`: `MAX_CFG` 32 -> **192**.
- `sider/experimental/fl26clubs.lua`: `from_world` sirve **todo slot de liga** del mundo desde su
  regulacion; solo se dejan fuera los que el juego llena con listas propias:
  `0..6` (selecciones/clasicos), `69..80` (pools y agregados) y `123` (centinela).

## Resultado

```
fl26clubs: live -- 137 slots served from our own regulations: 75<-181 69<-364 ... 28<-11 ...
           245<-30 49<-49 ... 209<-9000 84<-111 ... (137 pares)
```

Juego arrancado. Ahora cada liga del mundo sirve su lista desde su regulacion.

## Limite de clubes en una liga

La lista de una regulacion (y por tanto el slot) lleva **48 clubes como maximo**: es el tope
del propio juego (`+0x170`). Hay tres ligas por encima y se quedan en 48:

| clubes | liga | slot |
|---|---|---|
| 87 | Primera C Colombia | 246 |
| 63 | Brazilian National Fourth Division | 40 |
| 58 | Otros Concacaf | 247 |

Para verlas completas habria que partirlas o recortarlas (48 es el techo del dato).
