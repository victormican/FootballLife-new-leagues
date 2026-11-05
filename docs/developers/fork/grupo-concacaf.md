# El grupo "Otros Concacaf" con su slot (2026-11-06)

## Lo que había

La competición **cid 221 / reg 250** ("Otros Concacaf") tenía **58 clubes** (48 + los 10 de la MLS)
pero **ningún slot**: el juego no trae una sección de clubes de Concacaf (las de fábrica son
Europa 69, Asia 70, «Other» 71, Latinoamérica 73 y África 75), así que sus clubes solo se veían
por el nibble `+0x4f` en el grupo latinoamericano.

## Lo que se hizo

1. `fl26clubs.lua`: los slots **247, 248 y 249** pasan a la lista de slots servidos (antes solo
   hasta 208). Un slot servido contesta su lista desde la regulación del mundo que lo pide.
2. Línea nueva en el world file, con `exhibition=1` (Kick Off sí, temporada no):

```
league 250 cid=221 region=81 country=124 conf=6 slot=247 tier=3 promote=0 demote=0 \
       clubs=58 legs=2 kickoff=17 exhibition=1 name=Otros Concacaf
```

3. `fl26comptab` crea la fila del slot **247** con ese nombre y `fl26clubs` contesta sus **58
   clubes** desde la regulación 250.

Arranque medido:

```
fl26clubs: world file -- 152 leagues, 17 on slots the game fills itself, 2 on pool slots
world file: 152 leagues, 135 slots 22..247, 271 ccup lines
check_world: 0 errores
```

## Los cinco grupos

| slot | grupo | clubes | cómo |
|---|---|---|---|
| 69 | Other European Leagues | 48 | `pool 69 364` |
| 71 | Other (Asia) | 48 | `pool 71 256` |
| 73 | Other Latin American Teams | 48 | `pool 73 362` |
| 75 | Other Clubs (Africa) | 48 | `pool 75 181` |
| **247** | **Otros Concacaf** | **58** | línea `league 250 … slot=247 exhibition=1` |

El nombre de los cuatro primeros viene del interruptor de nombres del juego; el del 247 viene de
la propia línea (`Otros Concacaf`), porque el juego no tiene un caso para ese slot y cae al nombre
de la competición.

## Dónde sale

El slot 247 va con `region=81` / `country=124` (Estados Unidos, el mismo país que la USL), así que
la fila aparece **dentro de la sección de EE. UU.**, no como grupo suelto. Si se quiere como
sección internacional, hay que probar `region=25` (la de selecciones); no se ha hecho para no
tocar los grupos de selecciones.

## Si hay que dejarlo en 48

El grupo tiene **58** porque incluye los 10 clubes de la MLS que se crearon ayer (siguen también
en la competición 40). Para dejarlo en 48 exactos habría que sacar 10 de la regulación 250; no se
ha hecho porque esos 10 son los que pediste mantener en Concacaf.
