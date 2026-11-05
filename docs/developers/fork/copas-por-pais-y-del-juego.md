# Una copa y una supercopa por país; las del juego, a la lista (2026-11-06)

## 1. El menú volvía a repetir "FIFA Club World Cup"

Con 542 líneas la lista pasaba de 550 filas, y a partir de cierto punto el menú dejaba de
resolver el nombre y caía a la **competición 1** (`FIFA Club World Cup`), que se repetía.
El tope realista del menú es el de siempre; 542 copias lo desbordaban.

## 2. Fuera las copias: 542 → 279

`tools/drop_cup_copies.py` quita las 271 líneas `… II` (las tablas quedan; solo dejan de
listarse). Resultado: **279 líneas**, una copa y una supercopa por país, como pediste.

## 3. Y 10 líneas que eran ligas, no copas: 279 → 261

El world file tenía ligas escritas como eliminatoria directa, ocupando el `cid` de la copa de
otro país:

| línea `ccup` | usaba el cid de | y debería ser |
|---|---|---|
| Premier League | España (17) | liga |
| LaLiga | Países Bajos (19) | liga |
| Serie A TIM | Francia (18) | liga |
| Ligue 1 | Portugal (20) | liga |
| Trendyol Süper Lig | Grecia (118) | liga |
| CFA Super League | Turquía (120) | liga |
| Tanzanian Mainland Premier Division | Escocia (138) | liga |
| Ivorian Ligue 1 | Arabia Saudí (140) | liga |
| Brazilian National Third Division | Argentina (49) | liga |
| Colombian Second Division | Bélgica (112) | liga |

Quitadas (`tools/show_game_cups.py`). Eso libera esos `cid` para la copa de verdad.

## 4. Las copas del juego, a la lista: `showcup`

Las copas nacionales de los países grandes (FA Cup, Copa del Rey, Coppa Italia, DFB-Pokal,
Coupe de France, Taca de Portugal, KNVB Beker, Copa Argentina, Copa do Brasil…) **ya están en
los datos del juego**: no hay que crearlas, solo listarlas.

Nueva línea del world file:

```
showcup <cid>
```

`fl26swiss.lua` la lee (`SHOWCUPS`) y añade esos ids a la lista de Kick Off > Cup
(`fl26_swiss_cup_cids`), sin tocar el juego: la competición la juega él. Se añadieron 33:
copas y supercopas de Inglaterra, España, Italia, Francia, Alemania, Países Bajos, Portugal,
Argentina, Brasil, Bélgica, Dinamarca, Escocia, Grecia, Turquía, Arabia Saudí, Japón, China,
Colombia, EE. UU., Rusia y Chile.

## 5. Estado

```
check_world: 153 ligas, 136 slots, 261 ccup, 0 errores
sider.log:   285 cup(s) for Kick Off > Cup, 285 taken (8 del juego + 261 nuestras + 16 nuevas)
```

Juego arrancado. En Kick Off > Cup deberían salir ~293 filas (las 8 del juego + las nuestras +
las suyas listadas) y **acabar en la última, sin repetir FIFA Club World Cup**.

## 6. Lo que queda (cid secuestrados)

Todavía hay líneas nuestras que usan el `cid` de una copa del juego y por eso su nombre no
aparece:

| cid | lo usa | debería ser |
|---|---|---|
| 16 | AFC Champions League (nuestra) | Coppa Italia (Italia) |
| 42 | UEFA EURO (nuestra) | DFB-Pokal (Alemania) |
| 43 | Copa America (nuestra) | US Open Cup (EE. UU.) |
| 44 | AFC Asian Cup (nuestra) | Copa de Japón |
| 56 | 국제 친선 경기 | (no es copa) |
| 123 | Russian Cup (nuestra) | Copa Colombia |
| 126 | Copa BetPlay Dimayor | Copa de China |
| 129 | Russian Supercup | Copa de Dinamarca |

La siguiente pasada: remapear esas líneas a su cid real (o quitarlas si son duplicados de las
8 del juego) y volver a listar. Así cada `showcup` cae en su sitio.
