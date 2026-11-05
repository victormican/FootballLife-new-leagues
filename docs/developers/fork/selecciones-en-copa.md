# Selecciones en la Copa: Oceania y No FIFA (2026-11-05)

## Lo que estaba mal

Dos competiciones de selecciones tenían sus entradas y su regulación pero **ninguna línea de
copa**, así que no salían en Kick Off > Cup:

| cid | regulación | forma | equipos | nombre |
|---|---|---|---|---|
| 91 | 196 | eliminatoria (tipo 3) | 12 selecciones | Oceania |
| 255 | 255 | eliminatoria (tipo 3) | 8 selecciones | Selecciones No FIFA |

Y no son ligas: el mundo no las lista como liga (`league ... cid=91` / `cid=255` no existen), y
la herramienta **se niega a escribir** si aparecen como tal.

## Lo que se escribió

```
ccup 196 ko=196 groups=0 entry=0:<12 selecciones> cid=91  fill=12 national=1 days=20,27,34,41 like=23 name=Oceania
ccup 255 ko=255 groups=0 entry=0:<8 selecciones>  cid=255 fill=8  national=1 days=20,27,34,41 like=23 name=Selecciones No FIFA
```

- `entry=0:<id>` mete selecciones concretas, igual que la línea del Mundial.
- `like=23` es la forma de la FA Cup: un partido por ronda y byes para cualquier tamaño (12 y 8
  caen en la lista que el cuadro sabe dibujar).
- Los dos cid son **menores que 256**, así que su nombre se resuelve bien en el menú.

Resultado: **271 copas** en el mundo, `check_world` con **0 errores**.

## Los "Others" no son ligas

Comprobado: **ninguna** de las cinco competiciones de grupos "Otros" (cid 165 África, 221
Concacaf, 254 Asia, 98 Europa, 95 Latinoamérica) tiene línea `league`. Solo existen como
competiciones con sus clubes, y el juego las pinta por el nibble de `Team.bin +0x4f` (ver
`otros-grupos.md`), nunca como una liga.

## Lo que queda de la misma familia (no tocado)

Estas competiciones de selecciones tampoco tienen línea de copa:

| cid | competición | forma |
|---|---|---|
| 28-32 | clasificatorios del Mundial (Europa, N/C América, Sudamérica, Asia, África) | grupos |
| 33 | UEFA EURO | 6 grupos + KO de 16 |
| 34 | Copa América | 3 grupos + KO de 8 |
| 35 | AFC Asian Cup | 4 grupos + KO de 8 |
| 36 | Africa Cup of Nations | KO de 14 |

Se pueden añadir con la misma herramienta (`mk_natcups.py`) cuando se quiera: las de grupos
necesitan `groups=<n> ko=<reg del KO>`, y el clasificatorio puro no tiene cuadro final.

Copias: `fl26world.txt.before-natcups` en `modules\` y en `livecpk\_FL26MyWorld\`.
