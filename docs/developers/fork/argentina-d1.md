# Argentina: la Primera estaba sin listar (2026-11-04)

## El síntoma

En Select Team los clubes de la Primera División argentina no aparecían bajo Argentina. Los que
el juego enseña en los grupos de "otros clubes" son los de competiciones **sin slot**: la
Primera tenía sus filas y sus 26 clubes, pero **no tenía línea en `fl26world.txt`**, así que no
tenía plaza en Select Team ni fechas.

## Lo medido

```
Competition.bin         cid 22  ARGENTINA_D1_LEAGUE   (region 17, conf 4)
CompetitionRegulation   reg 30  type 4, decía 30 equipos, "Liga Profesional de Fútbol"
CompetitionEntry        26 clubes, posiciones 1..26:
    CA Aldosivi, Argentinos Juniors, Atl. Tucumán, CA Banfield, CA Barracas Central,
    Belgrano, CA Boca Juniors, Central Córdoba SDE, Defensa y Justicia, Estudiantes LP,
    Gimnasia LP, CA Huracán, CA Independiente, Independiente Rivadavia, Instituto AC,
    CA Lanús, Newell's Old Boys, CA Platense, Racing Club, CA River Plate, Rosario Central,
    CA San Lorenzo, Talleres, CA Tigre, CA Unión, CA Vélez Sarsfield
fl26world.txt           0 líneas con cid=22, 0 con reg 30
reg 11 (cid 130)        "Argentine Second Division" con tier=1 (era Primera Nacional)
```

El grupo `cid 95 FL_OTHERLATINAM` ("Other Latin American Teams") tiene **40 clubes de Perú,
Bolivia, Venezuela, Ecuador, Paraguay, Uruguay y Colombia; ninguno argentino**. Es decir: los
clubes argentinos no estaban ahí por datos, sino porque su competición no se listaba.

## El arreglo (`tools/arg_d1.py`)

1. reg 30: el número de equipos pasa de 30 (declarado) a **26** (los que hay de verdad).
2. Línea nueva en el world file, en la **primera plaza libre por encima de las 123 del juego**
   (slot 245; el máximo válido es 249 porque `fl26slots250` deja el 123 como centinela):

   ```
   league 30 cid=22 region=29 country=144 conf=4 slot=245 tier=1 promote=0 demote=2 \
       clubs=26 legs=2 kickoff=99 name=Liga Profesional de Fútbol
   ```

3. La Primera Nacional pasa a `tier=2`, con `promote=2 demote=2` (antes decía tier 1).
4. Se escriben **las dos copias** del world file (`livecpk\_FL26MyWorld\` y `modules\`) idénticas.

Verificación: `check_world` → **150 ligas, 133 slots, 0 errores** (el único aviso es de fábrica,
la copa 2 con dos clubes en la posición 32).

## Lo que falta de la Primera real

El release NewLife 1.6b4 tiene 30 clubes en su "Argentine Premier Division"; al mundo le faltan
cuatro porque **no existen como equipos** en estas tablas:

| club | id en el release | en el mundo |
|---|---|---|
| Atlético Sarmiento de Junín | 2730 | el 2730 es **Atlético Grau** (Perú) |
| Deportivo Riestra | 5366 | el 5366 es **Alianza Universidad** (Perú) |
| Gimnasia y Esgrima de Mendoza | 4997 | no existe |
| Estudiantes de Río Cuarto | 5659 | no existe |

Ojo con esto: **los ids de equipo del mundo no son los del juego en todos los casos** (se
reutilizaron al crear clubes). Cualquier importación por id tiene que comprobar el nombre antes
de tocar nada. Es la razón de que `newlife_apply.py` busque primero por nombre.

Crear esos cuatro clubes es un trabajo aparte (equipos nuevos con plantilla, escudo y kit); con
el release delante es hacerlo con `leaguebuilder`/NewLife y no a mano.
