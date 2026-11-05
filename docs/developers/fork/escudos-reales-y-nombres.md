# Escudos reales y nombres argentinos (2026-11-05)

## 1. Escudos reales con tu herramienta

Tu proyecto `newlife-classics` ya tiene lo necesario y se ha reutilizado tal cual:

| pieza | qué hace |
|---|---|
| `nlc/images/fuentes.py` | catálogo de footylogos por país (JSON-LD) y `https://www.footylogos.com/dls/logo/<slug>.png` |
| `nlc/images/catalog.py` | validar, recortar y normalizar (256×256 RGBA, margen) |
| `data/cache/footylogos_<pais>.json` | **120 catálogos ya descargados, 3.635 nombres** |

`tools/fetch_world_crests.py` indexa todos esos catálogos por nombre normalizado y, para cada club
del mundo cuyo nombre aparece **una sola vez**, descarga el PNG y escribe los tres tamaños que lee
el juego:

```
e_<id6>_r.png      128×128 RGBA
e_<id6>_r_l.png    256×256 RGBA
e_<id6>_r_ll.png   512×512 RGBA
```

Recorte al alfa, margen del 4 %, LANCZOS — la misma forma que `mkcrests.py`.

Resultado: **510 escudos reales escritos, 0 fallos** (solo clubes nuestros, id ≥ 71578; los del
juego no se tocan porque ya traen el suyo en la CPK). Ejemplo: Celtic pasó de un escudo generado
de 5,6 KB a uno real de 286 KB a 128 y 262 KB a 512.

Lo que falta: el emparejamiento es exacto, así que variantes como "Club Almagro" contra "Almagro"
del catálogo se quedan fuera. `fuentes.mejor_slug()` (el emparejador difuso de tu proyecto, por
país) es el siguiente paso; con él se pueden recuperar bastantes de los ~2.000 clubes restantes.

## 2. Los nombres argentinos: no los cambié yo

Comprobado contra **todos** los backups de `Team.bin` (desde el 2/11):

```
clubes en competiciones argentinas: 168
con nombre distinto en cualquier backup: 0
```

Los nombres de la **Primera División** (Boca, River, Racing, Independiente, San Lorenzo, Vélez,
Estudiantes, Gimnasia, Rosario Central, Newell's, Talleres, Belgrano, Lanús, Banfield, Huracán,
Defensa y Justicia, Tigre, Platense, Argentinos, Instituto, Barracas, Central Córdoba, Unión,
Aldosivi, Independiente Rivadavia, Atlético Tucumán) y de la **Primera Nacional** (Almagro,
Almirante Brown, All Boys, Atlanta…) ya eran los oficiales.

Lo que sí estaba mal eran las **divisiones de abajo**, rellenas de placeholders desde antes
("Primera B Metropolitana 01", "Federal A 01"…). Ahora se les ha puesto el nombre real del release
NewLife 1.6b4 (`tools/rename_arg_lower.py`):

| competición | cid | clubes | renombrados |
|---|---|---|---|
| Primera B Metropolitana | 25 | 22 | 22 |
| Torneo Federal A | 26 | 38 | 37 (el release trae 37) |
| Primera C | 38 | 28 | 28 |
| Torneo Federal | 99 | 30 | 30 |

Total **117 clubes** con su nombre real; el que sobra en Federal A mantiene su número porque el
release no trae un 38.º.

Copia: `Team.bin.before-argnames`. `check_world`: 0 errores.
