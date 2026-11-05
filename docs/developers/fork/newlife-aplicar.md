# Aplicar un release NewLife a un mundo ya construido (2026-11-05)

`tools/newlife_apply.py` mete las plantillas de un release NewLife en un mundo **ya construido**,
sin reconstruirlo: toca `Player.bin` y `PlayerAssignment.bin` y nada más. Las ligas, las copas,
los ids de club, los nombres y los escudos se quedan como están.

Para qué: el mundo vivo (`_FL26MyWorld`) se hizo con herramientas sueltas, no con una receta, así
que el camino normal de Mod Studio (*Bring the game's leagues to this season* → receta → Build) lo
habría reconstruido desde cero y se habría llevado por delante las 150 ligas y las 168 copas.

## Uso

```
python tools/newlife_apply.py --release "C:\Users\viarm\Downloads\Database Newlife" ^
    --world "<juego>\SiderAddons\livecpk\_FL26MyWorld\common\etc\pesdb" [--go] [--dry]
    [--only "River Plate"] [--debug] [--limit N]
```

- Sin `--go` es un **simulacro**: cuenta y no escribe.
- Con `--go` copia antes las dos tablas a `Player.bin.before-nl<version>` y
  `PlayerAssignment.bin.before-nl<version>`.
- `--only` filtra por nombre de club del release; `--debug` imprime club a club
  `old / keep / join / add / out`.

## Cómo empareja

**Un id de equipo no basta.** Este mundo ha reutilizado ids: el 2730 es *Atlético Grau* (Perú)
aquí y *Sarmiento de Junín* en el release; el 5366 es *Alianza Universidad* y en el release
*Deportivo Riestra*. Emparejar solo por id renombraría y desarmaría clubes que no son.

Orden:

1. **id**, y solo si los nombres se parecen (uno contenido en el otro por palabras: "River Plate"
   ⊂ "CA River Plate"). Esto resuelve los clubes del juego con nombre corto.
2. **nombre exacto normalizado**, cuando es único en el mundo.
3. **nombre + país** cuando el nombre se repite (p. ej. dos "Sportivo San Lorenzo").
4. si no hay nada de eso, el club **no se toca**.

Nacionales fuera: el release no trae selecciones.

## Qué jugador se queda con qué

1. por `game_id`, luego por `newlife_id`, si ese id es un jugador del mundo;
2. por nombre, primero entre los del propio club, luego en todo el mundo si el nombre es único;
3. si no, es jugador nuevo (`lbplayers.apply` le da un id libre).

Un jugador del release que está en otro club del mundo **se mueve** a este (`join`). El que sobra
del club sale como agente libre, salvo que el club se quedase por debajo de 18: entonces se queda
de banquillo.

## Lo aplicado al mundo vivo (2026-11-05)

```
NewLife Database 1.6b4: 13.481 clubes, 13.395 con plantilla
clubes actualizados: 1.812  (id con nombre parecido: 424, nombre: 1.388)
jugadores: 38.114 siguen con su id, 3.240 se mueven, 9.878 nuevos,
           7.301 dejan su club, 502 mayores se quedan de banquillo
tabla de jugadores: 89.488 -> 99.366 (tope 123.825)
lbplayers.apply: 61.773 cambios · 1.075 clubes con el 1 para su portero
59 clubes cortos rellenados con 99 agentes libres · mejor once elegido en 1.812 clubes
check_world: 0 errores (1 aviso de fábrica)
```

Copias: `Player.bin.before-nlNewLifeDatabase1.6b4` y `PlayerAssignment.bin.before-...`.

## Trampas que costaron una pasada

- **Sin ids libres**: el mundo tiene ids de jugador densos hasta 260.545, y `lbplayers` solo
  busca por encima del máximo. `newlife_apply.py` pone `FL26_FREE_PLAYER_IDS=1` antes de
  importarlo para que use los huecos de abajo (171.057 huecos, 0 jugadores borrados).
- **`join` con enteros**: `lbplayers.apply` compara `key in join` con cadenas; con enteros no
  casaba, el jugador no se actualizaba y el club se quedaba corto. Va como `str(pid)`.
- **Un jugador en dos clubes**: el release repite algún jugador en dos plantillas; se reclama una
  vez (`claimed`) y el segundo club recibe uno nuevo.
- **Clubes cortos**: los traspasos pueden dejar un club con 3 jugadores (CSKA). Se arregla con
  `lbplayers.sign_keepers`, que ficha agentes libres del propio mundo.

## Lo que sigue sin hacerse

- **Escudos y equipaciones** del release: no se tocan (cada club conserva los suyos).
- **Nombres de club**: no se renombran; el nombre del mundo manda.
- Los cuatro clubes de la Primera argentina que no existen en las tablas (ver
  `argentina-d1.md`) siguen sin crearse.
- Ligas del release que el mundo no tiene: no se añaden; esto es solo plantillas.
