# Equipos del mundo contra el release NewLife 1.6b4 (2026-11-05)

## Totales

| | clubes | selecciones | equipos |
|---|---|---|---|
| mundo vivo | **3.221** | 239 | 3.460 |
| release 1.6b4 | **13.481** (1.095 ligas) | — | — |

El release incluye divisiones amateur enormes (Torneo Federal C 720 clubes, Regional Amateur
250…), así que la diferencia de 10.260 clubes **no** es un fallo del mundo.

## Comparación liga a liga

Las **150 ligas del mundo** casan con una liga del release (89 por nombre exacto, 61 por nombre
parecido). Comparando el número de clubes:

- **87 ligas están iguales o tienen más** que el release.
- **17 están cortas**, y suman **111 clubes** de diferencia.

| liga | mundo | release | faltan |
|---|---|---|---|
| Brazilian National Fourth Division | 24 | 63 | **+39** |
| Argentine Second Division | 24 | 36 | **+12** |
| Argentine Torneo Federal A | 30 | 37 | **+7** |
| Kazakhstan Premier League | 10 | 16 | **+6** |
| J2 League | 16 | 20 | +4 |
| Zambian Premier League | 18 | 20 | +2 |
| Maltese Premier League | 10 | 12 | +2 |
| Kuwaiti Premier League | 10 | 12 | +2 |
| JD Cymru Premier | 10 | 12 | +2 |
| Venezuelan Premier Division | 13 | 14 | +1 |
| TT Premier Football League Tier 1 | 10 | 11 | +1 |
| Liga Nacional de Honduras | 11 | 12 | +1 |
| Gibraltar Football League | 10 | 11 | +1 |
| Ecuadorian Serie B | 10 | 11 | +1 |

(Las tres filas «Premier League 10 vs 20» del listado completo son emparejamientos dudosos del
nombre: hay varias "Premier League" en el release y no se pueden dar por buenas sin mirar el
país.)

## ¿Hay que romper límites?

**Para esos 111 clubes, no.** Margen actual:

| recurso | usado | tope | libre |
|---|---|---|---|
| equipos | 3.221 | 4.800 | **1.579** |
| clubes del Edit | 3.221 | 4.700 | 1.479 |
| jugadores | 99.366 | 123.825 | **24.459** |
| ids de club | 74.296 | 81.919 | 7.623 |
| competiciones | 495 | 1.023 | 528 |
| regulaciones | 690 | 1.200 | 510 |

111 clubes × 22 jugadores = **2.442 jugadores**: caben de sobra.

## Si se quisiera el release entero (13.481 clubes)

Ahí sí habría que romper, y aun así **no llegaría**:

- 13.481 clubes × 22 jugadores = **296.582 jugadores**. El formato empaqueta el id de jugador en
  **18 bits (262.143)**: es pared de dato, no de array. A 22 por club el techo real es **~11.900
  clubes**; a 30 por club, **~8.700**.
- Subir para acercarse exigiría: `players` en `layout.json` (hoy 123.825), `clubs del Edit`
  (`fl26edit.c`, 4.700), `teams` (4.800) y regenerar el set entero (mover la cola baja).
- Coste: alto y con riesgo; y el resultado seguiría sin cubrir las 1.095 ligas del release.

## Lo que yo haría

1. **Rellenar las 14 ligas claras** (los 111 clubes) con `fill_group.py --reg <reg> --to <n>`:
   crea los clones con plantilla y actualiza las entradas y el contador. Cabe sin tocar límites.
2. Revisar a mano las tres «Premier League» dudosas antes de tocarlas.
3. Si se quiere crecer más allá, subir **Edit y teams** primero (baratos) y **jugadores** después
   (caro), sabiendo el techo de ~11.900 clubes por los 18 bits del id.
