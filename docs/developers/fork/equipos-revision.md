# Revisión de equipos: qué se ve mal y qué no (2026-11-05)

Auditoría de `Team.bin` (3.450 equipos, 239 selecciones) buscando lo que puede verse mal en
Select Team, fichas, calendario y marcador. Todo medido sobre el mundo vivo.

## Lo que está bien

| comprobación | resultado |
|---|---|
| equipos sin nombre | **0** |
| clubes nuestros (≥ 71578) sin escudo | **0** de 2.606 |
| clubes en más de una liga listada | **0** |
| clubes con grupo "Otros" y a la vez en una liga | **0** |
| clubs con país fuera de rango | **91, pero no es error** (ver abajo) |

Los 605 clubes del juego que no tienen PNG de escudo en el mundo no es un fallo: usan el escudo
de la base del juego.

### Los 91 "países raros"

Tienen ids 240, 241, 245, 303, 304, 311. `Country.bin` tiene 240 registros, así que parecían
inválidos, pero **el propio world file usa esos ids** para sus ligas: Uzbekistán 240, Gales 241,
Gibraltar 245, Montenegro 304, Kosovo 311. Son correctos y coinciden con su liga: no se toca nada.

## Lo que sí se ve mal

### 1. Copa Colombia: los mismos 24 clubes dos veces

`CompetitionEntry.bin`, competición 92, 48 entradas:

```
pos  1..24   73796..73819   "Copa Colombia Club 25" .. "Club 48"
pos 25..48   74101..74124   "Copa Colombia Club 25" .. "Club 48"   <-- el mismo juego otra vez
```

Los dos juegos existen como equipos distintos (22 jugadores cada uno) y con el mismo nombre: en
el cuadro salen duplicados. Es un relleno hecho dos veces.

### 2. Dos clubes huérfanos con el mismo nombre

```
73896  "Copa Argentina Club 48"   sin competición, 22 jugadores
74228  "Copa Argentina Club 48"   sin competición, 22 jugadores
```

No los usa nadie: son restos de un relleno anterior.

### 3. 72 clubes sin nombre corto

`Team.bin +0x372` (las tres letras que copian el marcador y las tablas) está vacío en 72 clubes,
todos placeholders de copas y de los grupos "Otros" ("Other Clubs (Africa) 01..24", "Copa
Argentina Club 02..", "Generic League…"). Ahí el marcador enseña un hueco.

### 4. Homónimos reales (no es error, pero confunde)

```
Al-Nasr (72229 y 72367)            dos clubes distintos con el mismo nombre
Alianza Universidad (5366, 71859)
CA Independiente (1240, 72467)
Club Nacional (1262, 71776)
```

## Herramientas dejadas para esto

- `tools/fix_club_country.py`: pone a cada club el país de su liga. Solo cambiaría 31 y **no se
  aplicó**: los ids 240+ son válidos aquí.
- `tools/fix_team_codes.py`: genera el nombre corto que falta. **No aplicado**: con nombres como
  "Other Clubs (Africa) 01..24" el código sale igual para todos (OCA) y no arregla nada.

## Lo que falta para rematarlo

Decidir qué se hace con los rellenos duplicados de la Copa Colombia (quitar el segundo juego de
24 y dejar la competición en 24 clubes, o renombrarlos) y con los dos huérfanos argentinos
(borrarlos). Las dos cosas cambian el tamaño de una competición, así que van con su copia y su
`check_world`; no se han tocado a ciegas.
