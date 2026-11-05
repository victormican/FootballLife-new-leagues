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

## 6. Revisión de los secuestros (2026-11-06, segunda pasada)

Se revisaron todas las líneas cuyo `cid` es una copa de otro país. Resultado:

| línea | cid | era | ahora |
|---|---|---|---|
| Coppa Italia | 16 | 24 (Brasil) | **16 ITALY_D1_CUP** |
| Copa BetPlay Dimayor | 123 | 126 (China) | **123 COLOMBIA_CUP** |
| Russian Supercup | 116 | 129 (Dinamarca) | **116 RUSSIA_SUPER_CUP** |
| Russia Cup | 115 | — | 115 RUSSIA_CUP (ya estaba bien) |
| Supercopa de España | 74 | — | 74 SPAIN_SUPER_CUP (ya estaba bien) |

Y se quitaron 7 líneas que eran copias de copas que el juego ya muestra en su lista de 8, o que
no son copas:

```
AFC Asian Cup          (el juego ya la tiene, cid 35)
AFC Champions League   (dos líneas; el juego ya la tiene, cid 8)
Copa America           (el juego ya la tiene, cid 34)
UEFA EURO              (el juego ya la tiene, cid 33)
Russian Cup            (duplicado de Russia Cup)
국제 친선 경기            (amistosos, no es copa)
```

`check_world`: **254 líneas `ccup`, 0 errores**. Ya no queda ninguna línea usando el `cid` de la
copa de otro país.

## 7. Las copas del juego (`showcup`) se retiraron

La prueba de listarlas en Kick Off > Cup **no llegó a abrir el menú**: el juego se cerró en
`FL_2026+0x3fd2b2`, la caída de heap conocida de `copas-por-liga.md` (la misma que aparece a veces
sin abrir Copas). Las 33 líneas `showcup` se quitaron para dejar el menú como estaba; el soporte
en `fl26swiss.lua` queda, sin datos.

Siguiente intento, si se quiere: listar **una sola** copa del juego (p. ej. `showcup 73`, la
Community Shield) y comprobar que el menú abre antes de añadir el resto.

