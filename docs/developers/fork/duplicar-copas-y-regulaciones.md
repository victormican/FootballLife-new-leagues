# ¿Se pueden duplicar las regulaciones y las copas? (2026-11-06)

## Regulaciones: 691 de 1.200

| | |
|---|---|
| usadas | **691** |
| tope | **1.200** |
| libres | **659** |
| duplicar todas (691 × 2) | **1.382** → **no cabe** |

Duplicar *todas* las regulaciones no cabe en el tope actual. Para llegar a 1.382 habría que subir
el tope primero (`layout.json` → `patchset` → `fl26caps`, y `mkregs --stub` para el recuento);
2.000 es viable y está documentado en `limites-actuales-2026-11-05.md`. Coste: medio; riesgo: el
recuento y el reset de filas de la copia de modo.

Con lo que hay **sí** se pueden duplicar las copas (ver abajo): 271 copias más dejan las
regulaciones en **962**, dentro de 1.200.

## Copas: sí, y ya está probado

`tools/dup_cups.py` duplica las copas de eliminatoria directa (`groups=0`): por cada una copia la
fila de `Competition.bin`, la de `CompetitionRegulation.bin` (con su nombre y su tamaño de sorteo)
y sus entradas, y escribe una línea `ccup` nueva con el mismo cuadro, los mismos días y el nombre
con sufijo.

Probado en una copia del mundo con 2 copas:

```
AFC Challenge Cup   cid 367  reg 434  (16 entries)
Albania Cup         cid 368  reg 435  (8 entries)
check_world: 498 competiciones, 693 regulaciones, 273 ccup, 0 errores
```

### Lo que cuesta duplicar las 271

| recurso | antes | después | tope | ¿cabe? |
|---|---|---|---|---|
| regulaciones | 691 | **962** | 1.200 | sí |
| competiciones (cid) | 496 | **767** | 1.023 | sí |
| líneas `ccup` | 271 | **542** | — | — |
| filas del menú de copas | 271 | **542** | **512** | **no** → subir `fl26cupgrow` a 1.024 |
| clubes / jugadores / slots | — | igual | — | sí |

O sea: **duplicar las copas no necesita romper ningún tope de datos**; solo subir el menú de 512 a
1.024 filas (el mismo cambio que 256→512: `WANT` y el `lea rcx,[r11+0x1800]` → `0x3000`).

### Lo que no se duplica bien tal cual

- **Copas de grupos** (`groups>0`): tienen regulación maestra, una réplica por grupo y la
  eliminatoria; hay que duplicar las tres y renumerar las réplicas (`maestra + 1024*(g+1)`). El
  script las salta a propósito.
- **Fechas**: una copia conserva el `like=` de la original, así que se datea igual que ella. Dos
  copias el mismo día es legal, pero si se quiere otra fecha hay que poner `days=`.

## Recomendación

1. Subir `fl26cupgrow` a **1.024** (barato).
2. Duplicar las copas que interesen con `dup_cups.py --limit N` o `--only "Supercopa"`.
3. Dejar las regulaciones en 1.200 mientras no haga falta más; si algún día se duplican todas,
   subir el tope a 2.000 antes.
