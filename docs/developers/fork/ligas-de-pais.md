# Liga de un país desde una liga genérica

Receta usada el 2026-11-03 para crear **Azerbaiyán, Irlanda, Gales, Islandia y Hungría** sin gastar
ningún `cid` nuevo, reutilizando cinco «Generic League» y sus clubes.

## Idea

Una liga genérica ya trae todo lo que cuesta crear: fila en `Competition.bin`, regulación, slot en
el Select Team y diez clubes en `CompetitionEntry.bin`. Convertirla en la liga de un país es
renombrar, no construir:

| qué | dónde | cómo |
|---|---|---|
| nombre de la liga | `CompetitionRegulation.bin` +0x14 (20 idiomas) | `mkleague.put_names` |
| nombre y código | `Competition.bin` +0x14 (16 B) y +0x08 (12 B) | escribir en su sitio |
| clubes | `Team.bin` slots de nombre desde 0x9E | `put_team_name` (como `rename.py`) |
| país del club | `Team.bin` +0x46 | `(v & 3) \| (flag_id << 2)` |
| liga de un club | `CompetitionEntry.bin` +0x08 | cambiar el byte `cid` |
| línea del mundo | `fl26world.txt` | `country=`, `name=`, `clubs=` |

**Trampa medida**: el campo de nombre de `Competition.bin` es de **16 bytes** desde `+0x14`. Una
asignación de rebanada más larga (`cc[20:20+48] = ...`) **alarga la fila** y descoloca las 239
competiciones: `check_world` suelta 998 errores «competition 238 is not in Competition.bin». Hay
que escribir `cc[20:36]`.

## Segunda tanda (2026-11-03): nueve países y la copa de Liechtenstein

`--wave2` usa `SPEC2` en vez de `SPEC` y hace tres cosas nuevas:

| país | reg | cid | slot | reales que entran de «Otros Europa» |
|---|---|---|---|---|
| Bielorrusia | 344 | 55 | 216 | BATE, Dinamo Minsk, Shakhtyor Soligorsk |
| Kazajistán | 345 | 57 | 217 | Kairat, Astana |
| Estonia | 346 | 58 | 218 | Flora Tallinn |
| Armenia | 347 | 59 | 219 | Ararat-Armenia, Pyunik |
| Letonia | 348 | 60 | 220 | Riga FC, FC RFS |
| Lituania | 349 | 61 | 221 | Žalgiris, Sūduva |
| Kosovo | 350 | 62 | 222 | Ballkani, Prishtina |
| Irlanda del Norte | 351 | 63 | 223 | — (diez clubes nuevos) |
| Finlandia | 352 | 64 | 224 | HJK, KuPS, Inter Turku, Ilves |
| Copa de Liechtenstein | 375 | 48 | -1 | Vaduz |

Cambios de diseño respecto de la primera tanda:

- **La copa de Liechtenstein ocupa el sitio de la Copa Argentina** (reg 375, cid 48). Los 48
  clubes de esa copa son clubes argentinos de verdad que **siguen en sus divisiones**: sus
  entradas de copa se borran y no se renombran, porque renombrar la fila del club lo cambiaría
  también en su liga. Los seis clubes que faltan salen de filas de equipo **sin competición**
  (`fresh`: genéricos sueltos), se renombran y se les añade su entrada en `CompetitionEntry.bin`
  con un `eid` nuevo.
- **Los donantes sobrantes** de cada liga (los que la liga no necesita porque entran reales) no se
  pierden: van a «Other European Leagues» renombrados a clubes reales de países que aún no tienen
  liga (Dinamarca, Escocia, Turquía, Rusia, Malta, Luxemburgo, Feroe, Gibraltar, Andorra, San
  Marino, Moldavia). El grupo queda con **47** clubes y su regulación y su línea del mundo se
  sincronizan con ese número.
- **Trampa del nombre**: el nombre canónico del club está en el slot **0x170**, no en el 0x9E (que
  viene vacío en las filas del juego). Leer 0x9E hace que `--take` no encuentre clubes como
  «FC RFS» y que el filtro de duplicados no vea los nombres reales.

## Tercera tanda (2026-11-03): Luxemburgo, Feroe y San Marino

`--wave3` usa `SPEC3`: las genéricas 353, 354 y 355 (cid 80, 81 y 83; slots 225, 226 y 227) pasan a
ser **National Division** (4 reales: F91 Dudelange, Jeunesse Esch, Progrès, Differdange),
**Betri deildin** (4 reales: Víkingur Gøta, HB Tórshavn, NSÍ Runavík, KÍ Klaksvík) y
**Campionato Sammarinese** (3 reales: Tre Fiori, Tre Penne, La Fiorita).

Es el mismo patrón: los reales se mueven desde «Other European Leagues» (cid 98) y los donantes
sobrantes vuelven a cid 98 renombrados a clubes reales de países sin liga, así que el grupo sigue
con 47 clubes.

## Clubes: mover, no duplicar

Los clubes reales del país que ya estaban en «Other European Leagues» (`cid 98`) se **mueven** a la
liga nueva cambiando el `cid` de su entrada. Para que el grupo siga con 48, el mismo número de
clubes donantes sale a `cid 98` renombrado a un club real de un país que aún no tiene liga
(Bielorrusia, Kazajistán, Kosovo, Georgia, Armenia...). Total: 5 donantes × 10 clubes = 50 = 40
renombrados + 10 movidos.

## Nombres que ya existen

Antes de renombrar hay que comprobar el mundo entero. La comparación por nombre exacto **no basta**:
`Emelec` choca con `Club Sport Emelec`, `Peñarol` con `CA Peñarol`. El filtro que funciona es la
**palabra más larga** del nombre candidato contra todos los nombres existentes (sin tildes):

```python
def core(name):  # 'Emelec' -> 'emelec', que aparece en 'Club Sport Emelec'
    ...
```

Con ese filtro, «Other Latin American Teams» quedó con 48 clubes reales de segunda fila (Perú,
Bolivia, Venezuela, Ecuador, Paraguay, Uruguay, Colombia) y cada uno con la bandera de su país.

## Gemelas vacías

Las «Generic League 66/67» (regs 382 y 383) compartían `cid` 50/51 y no tenían ni una entrada.
Se quitaron sus líneas del mundo: `check_world` deja de avisar de gemelas.

## Validación

```
fix_team_names --check     0 abreviaturas rotas
check_world                0 errores, 1 aviso (copa del juego con dos clubes en la misma plaza)
FL 2026 start.exe          2 de 2 arranques vivos 55 s
fl26clubs                 69<-364 y 73<-362 siguen sirviendo los dos grupos
```
