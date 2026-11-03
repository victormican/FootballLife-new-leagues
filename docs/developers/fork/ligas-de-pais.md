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

## Cuarta tanda (2026-11-03): las últimas seis genéricas

`--wave4` usa `SPEC4` y cierra el mapa UEFA: Moldavia, Andorra, Malta, Gibraltar, Georgia y
Liechtenstein. Después de esta tanda **todos los países UEFA tienen liga** (Dinamarca, Turquía,
Países Bajos y Francia ya venían en el juego).

| país | reg | cid | slot | reales que entran de «Otros Europa» |
|---|---|---|---|---|
| Moldavia | 356 | 85 | 228 | Sheriff Tiraspol, Zimbru, Dacia, Speranta Nisporeni |
| Andorra | 357 | 87 | 229 | Santa Coloma, Inter Club d'Escaldes, UE Sant Julià |
| Malta | 358 | 88 | 230 | Valletta, Hibernians, Floriana, Birkirkara |
| Gibraltar | 359 | 89 | 231 | Lincoln Red Imps, St Joseph's |
| Georgia | 360 | 93 | 232 | Dinamo Tbilisi, Dinamo Batumi, Torpedo Kutaisi, Saburtalo, FC Telavi |
| Liechtenstein | 361 | 94 | 233 | Vaduz, Eschen/Mauren, Balzers, Ruggell, Schaan, Triesen, Triesenberg |

Dos capacidades nuevas del script:

- **`take_from`**: la liga toma sus clubes reales de una competición distinta de «Other European
  Leagues». Liechtenstein la usa con `take_from: 48` para llevarse sus siete clubes desde la vieja
  **Copa Argentina** (`cid 48`), que solo existía como contenedor de esos equipos.
- **`drop`**: la competición vieja desaparece. `drop: (375, 48)` borra la regulación 375, la fila de
  `Competition.bin` del cid 48, todas sus entradas y su línea `league` del mundo (el fichero pasa de
  502 a 501 líneas). Sin `drop` quedaría una copa fantasma sin clubes.

Detalles que costaron una pasada:

- Liechtenstein no es una liga: es la **copa**. El `cid` 48 lo conoce el ejecutable como «Copa
  Argentina» y no se lista bajo Liechtenstein, así que reutilizar la fila era la única forma de que
  apareciera; los siete clubes son de verdad y llevan la bandera 218.
- Sin refills: no queda ningún país UEFA sin liga al que mudar los donantes, así que los 25
  sobrantes se dejan fuera y «Other European Leagues» baja a **29** clubes (regulación y línea del
  mundo sincronizadas).
- «Sliema Wanderers» y «Europa FC» no existen en el mundo: el filtro `core()` los descarta como
  duplicados de sí mismos, así que entran como clubes nuevos (Sliema en Malta, Lions Gibraltar en
  Gibraltar).

## Liga desde cero (2026-11-03): Belice, Curazao, Surinam y Haití

Cuando se acaban las genéricas ya no hay fila que reciclar: `tools/new_league.py` construye cada liga
con `mkleague.add_league`, que **copia una competición nuestra como prototipo** (`FL_223_D1`, 10
clubes, división 1), le pone `cid`, código y nombre nuevos y escribe regulación y entradas. La
lista `LEAGUES` lleva una entrada por país y **se salta las que ya existen** (si el `cid` está en
`Competition.bin` no hace nada), así que se puede volver a ejecutar.

| país | cid | reg | región | slot |
|---|---|---|---|---|
| Belice (108) | 239 | 8457 | 106 | 234 |
| Curazao (140) | 240 | 8458 | 107 | 235 |
| Surinam (139) | 241 | 8459 | 108 | 236 |
| Haití (120) | 242 | 8460 | 109 | 237 |
| RD del Congo (55) | 243 | 8461 | 110 | 238 |
| Congo (98) | 244 | 8462 | 111 | 239 |
| Fiyi (164) | 245 | 8463 | 112 | 240 |

Y una liga que **ya existía llena de placeholders** se rellena en el sitio (`FILLS`), sin gastar
`cid` ni slot: «Liga Pro OFC» (Nueva Caledonia, cid 168, reg 198, slot 180) tenía 24 clubes
`Liga Pro OFC 01..24`; pasa a llamarse **Super Ligue** con 12 clubes reales y sus otras 12
entradas se retiran (sus filas quedan libres), sincronizando regulación y mundo.

Los diez clubes de cada una salen de filas que ninguna competición usa (`Generic League NN Club
0N`), renombradas y con la bandera de su país. Curazao, Surinam, Haití y los dos Congos no tenían
un solo club en el mundo, solo su selección. Las dos africanas van con lo que usan las ligas de CAF
(`conf=5`, `kickoff=70`) y sus regiones también son nuevas (110 y 111).

Dos trampas del prototipo:

- `add_league` escribe el código con **28 bytes** desde +0x08, así que borra el nombre de 16 bytes
  en +0x14: hay que reescribirlo después (`M.put(comp, fila + 0x14, nombre, 16)`).
- El `rid` de una regulación está en **+0x02**, no en +0x00 (+0x00 es el id de texto). Leerlo mal
  devuelve 0 y la línea del mundo no se sincroniza.

La primera pasada **retiró las ocho copias sudamericanas** que había dentro de «Other Latin American
Teams» (Los Chankas, Real Potosí, Universitario de Vinto, Zamora, Mushuc Runa, Técnico
Universitario, Guayaquil City, Montevideo City Torque): son clubes que ya juegan su liga, así que
se borran su fila de `Team.bin`, su entrada, sus 22 fichas de `PlayerAssignment.bin` y la plaza se
renumera; el grupo queda con **40** clubes y su regulación y su línea se sincronizan.

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

Tras la cuarta tanda `check_world` informa de **238 competiciones, 383 regulaciones y 3802
entradas** (28 menos: las de la copa retirada) y `sider.log` sirve en `fl26comptab` los slots
**228..233** (ids 356..361), sin `aborting` ni `no slot in the list`.
