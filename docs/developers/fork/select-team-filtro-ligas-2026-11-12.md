# Seleccionar equipo en Copa: el filtro de ligas (2026-11-12)

## Qué se vio

En Kick Off > Copa, tras elegir la competición y las Opciones generales, la pantalla
**"Seleccionar equipo"** es el Select Team del juego: a la izquierda una **columna de ligas**
(el filtro) y a la derecha los clubes de la liga elegida. La copa lista sus participantes
agrupados por su liga.

- **Clon nativo (cid 5 = nuestra Sudamericana)**: el filtro muestra las ligas de los 32
  participantes (Brasil, Argentina, Chile, Colombia y la Liga Nueva en "Otros
  latinoamericanos"). Así es como debe comportarse la réplica.
- **Cid nuevo directo (cid 132)**: el filtro salía con **todas** las ligas del juego, no las
  de la copa. La competición nueva no ata su field al Select Team.

## Por qué

El filtro de ligas del Select Team sale de la **lista de entradas de la competición**
(`CompetitionEntry.bin`): los clubes y sus ligas. Una competición **nativa** (cuyo cid el motor
conoce) ata esa lista al Select Team; una competición **nueva** (cid 132) tiene las entradas
pero el motor no las enlaza al menú (el mismo muro del plan/sorteo).

## Cómo hacerlo (la receta de una réplica jugable)

1. Construir la copa desde el mundo: receta con `ccup` (regulación maestra + KO, 32 clubes,
   8 grupos), como `out/recipe-sud.json` -> `ccup 318 ko=319 groups=8 ... cid=132`.
2. **Clonar una plaza nativa** que ya está en el plan del motor (formato idéntico): la
   Libertadores (**cid 5**, 32 clubes / 8 grupos):

   ```
   python tools/clone_shipped_cup.py --base <mundo>\common\etc\pesdb --out <mundo> \
     --cid 5 --reg 9 --code FL_SUDAM --name "Copa Sudamericana" --teams 318:1,318:2,...,318:32
   ```

3. `fl26swiss.lua` con `EXPOSE = 0`: la copa del mundo (cid 132) no se lista (cerraría el
   juego); el clon (cid 5) es el que se juega.

Resultado: Kick Off > Copa > último item = Copa Sudamericana con **sorteo, cuadro y partidos**,
y el Select Team con el **filtro de ligas correcto** (los 32 participantes por su liga).

## Nota

El cid nuevo directo (132) queda a un paso (menú, opciones, selección de equipo), pero se
atasca en el cargador de archivos del motor; para jugar ya, la vía es el clon nativo.
