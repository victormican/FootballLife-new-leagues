# Auditoría de ligas y banderas (2026-11-06)

Revisión de las **152 ligas** del mundo una a una: país, bandera que resuelve, clubes y
comparación con el release. Hecha después del susto de "las banderas se ven mal".

## Qué se tocó ayer (y por qué)

`country` (en `Team.bin` y en el world file) guardaba el **id de bandera**, y el juego lo lee como
**número de fila** de `Country.bin`. Consecuencia real, no teórica: Argentina (fila 129, bandera
144) se leía como **Nueva Caledonia** → los clubes argentinos salían en Oceanía.

Se remapearon 3.450 equipos y 152 valores del world file de bandera → fila. Eso es lo que cambió.
No se tocó ni un nombre de club ni una competición.

## Comprobación 1: clubes contra su liga

```
clubes en liga listada: 1.945
con país distinto al de su liga: 4   (71667-71670, galeses; ya estaban así)
```

Los clubes siguen en su liga y con el país de su liga.

## Comprobación 2: banderas

```
países (filas): 240 · ids de bandera distintos: 240 (sin repetir)
ids ≤ 214 (arte del juego): 206 · ids > 214 (arte propio): 34
flags propios en el mundo: 26 (ids 96..180), todos distintos entre sí
países sin textura (mkcountryflag --check): 0
```

Los 26 PNG propios son de los países nuevos (Martinica, Guadalupe, Cataluña, Padania, Zanzíbar,
Tuvalu, Vaticano…), y ninguno pisa una bandera de fábrica: **no hay ni un id repetido**. La
comprobación oficial (`mkcountryflag.py --check`) dice **0 países sin textura**.

## Comprobación 3: ligas contra el release

Las 152 ligas casan con una del release (152/152 por nombre). Ojo con una trampa: **el release
numera los países como el juego de fábrica** (allí Argentina es 144) y **nuestro `Country.bin` está
ampliado y reordenado** (aquí Argentina es la fila 129, con bandera 144). Comparar ambos id a id da
"distinto" en 100 ligas y **no significa nada**: la verdad para el juego es nuestra tabla.

Lo que sí vale es comparar **número de clubes**. 87 ligas están iguales o tienen más que el
release y **17 están cortas**, sumando **111 clubes**:

| liga | mundo | release |
|---|---|---|
| Brazilian National Fourth Division | 24 | 63 |
| Argentine Second Division | 24 | 36 |
| Argentine Torneo Federal A | 30 | 37 |
| Kazakhstan Premier League | 10 | 16 |
| J2 League | 16 | 20 |
| Zambia, Malta, Kuwait, Gales | 10 | 12 |
| Venezuela, Trinidad, Honduras, Gibraltar, Ecuador B | 10-13 | 11-14 |

Además hay ligas pequeñas **a propósito** (Yokary Liga 8, Scottish Championship 10, Swiss
Challenge 10, Andorra 10): no están cortas, son así.

## Lo que no cuadra y hay que mirar con un caso concreto

La auditoría estática no encuentra banderas mal: 240 filas, 240 ids, 0 sin textura y 26 propios sin
colisión. Si ves una bandera equivocada, hace falta **el país o la liga exacta** para comparar su
fila, su id de bandera y el PNG que carga. Con un ejemplo se cierra en un minuto; sin él, cualquier
cambio sería a ciegas y ya hemos roto cosas así.

## Lo que sí se puede hacer ya

Rellenar las 17 ligas cortas con `fill_group.py --reg <reg> --to <n>`: 111 clubes, 2.442
jugadores, cabe en los límites (equipos 3.574/4.800, jugadores 102.094/123.825).
