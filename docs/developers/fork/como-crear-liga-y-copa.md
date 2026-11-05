# Cómo crear una liga, una copa y crecer el mundo (paso a paso)

Verificado el 2026-11-04 con una receta real: **una liga nueva de Andorra de 10 clubes a dos
vueltas, su copa nacional y su supercopa**. Tiempo del build: **45 s**. Resultado del
`check_world`: **0 errores**.

Este documento es el "cómo se hace"; los formatos, los campos y los topes están en
`regulaciones-y-formatos.md`.

## 0. Lo que produjo la prueba

```
world _FL26Tut: 1 new leagues, changes to 0 of the game's leagues and 0 of its clubs
  Lliga Tut                  reg  11  comp 130  region 29  slot  28  division 1  10 clubs x2
  Copa Tut: national cup of 10 clubs (copied from ENGLAND_D1_CUP)
  Supercopa Tut: super cup (copied from BELGIUM_SUPER_CUP)

built ...\livecpk\_FL26Tut: 1 leagues, 10 clubs
  time: clubs and tables 0 s, squads 0 s, players 35 s, cups and the world file 2 s,
        pictures and kits 8 s, regions and the swap 1 s

teams 759 (144 national), players 29792, assignments 21664,
competitions 95, regulations 220, entries 1389
world file: 1 leagues, 1 slots 28..28, 0 ccup lines
0 error(s), 4 warning(s)
```

Los 4 avisos son de datos de fábrica (la copa 24 y la 2 tienen dos clubes en la misma posición),
no de la liga nueva.

## 1. Requisitos

- Un **pesdb base** con las tablas del juego:
  `%APPDATA%\FL26ModStudio\tables\common\etc\pesdb` (o una copia limpia de `pesdb/_base`).
- Una **carpeta de juego** con `FL_2026.exe` (para leer las fechas de las copas) o una carpeta
  cualquiera con `SiderAddons\livecpk` dentro. Si no hay exe, el build avisa y las ligas solo se
  mantienen lejos de nuestras copas.
- Nada más: el builder escribe todo (tablas, plantillas, jugadores, kits, escudos, mundo).

## 2. La receta

`recipe.json`, sin BOM (si lo escribes con PowerShell 5.1 cuidado: `Set-Content -Encoding UTF8`
mete BOM y el builder lo rechaza).

```json
{
  "world": "_FL26Tut",
  "leagues": [
    {
      "name": "Lliga Tut",
      "country": "Andorra",
      "clubs": 10,
      "legs": 2,
      "cup": true,
      "cup_name": "Copa Tut",
      "supercup": true,
      "supercup_name": "Supercopa Tut"
    }
  ]
}
```

- `world` debe empezar por `_FL26`: es la carpeta de `livecpk`.
- `country` es un nombre de `Country.bin` (bandera, región, nombre en Competition Info).
- `clubs` 10..30 (probado hasta 24; 30 es nuevo), `legs` 1..4.
- `cup` / `supercup` solo en la primera división de un país nuevo.

Otras claves que se usan de verdad (todas en `recipe-keys.md`):

| clave | para qué |
|---|---|
| `above`, `exchange` | segunda división: liga de arriba y cuántos suben/bajan |
| `split {legs, groups, group_legs}` | split escocés (Ecuador: `[6,6,4]`) |
| `apertura` (`true` o `{"playoff": 8}`) | Apertura/Clausura, máx. 18 clubes |
| `season: "calendar"` | temporada febrero-diciembre (Brasil, Japón) |
| `exhibition: true` | solo Kick Off, nunca en Master League |
| `others: "europe"` | no es liga: clubes para el grupo "Other" del juego |
| `europe: [[1,0],[2,1]]` | plazas continentales por posición |
| `club_ids`, `club_names`, `club_crests` | ids, nombres y escudos propios |
| `game_clubs` | meter clubes que ya existen (con `swap` si juegan en otro sitio) |
| `real_calendar` | fechas reales de la liga (`rcal`) |

## 3. Plan (no escribe nada)

```
python tools/leaguebuilder.py plan recipe.json ^
  --base "%APPDATA%\FL26ModStudio\tables\common\etc\pesdb"
```

Devuelve los ids que va a gastar (regulación, competición, región, slot), los clubes, la copa y
la supercopa. **Mirar aquí primero**: si el slot o el cid chocan con el mundo que ya tienes, se ve
antes de escribir.

## 4. Build

```
python tools/leaguebuilder.py build recipe.json ^
  --base "%APPDATA%\FL26ModStudio\tables\common\etc\pesdb" ^
  --game "D:\SP Football Life 2026 - copia - copia"
```

Escribe en `<juego>\SiderAddons\livecpk\_FL26Tut\`:

- `common\etc\pesdb\` con `Competition.bin`, `CompetitionRegulation.bin`, `CompetitionEntry.bin`,
  `Team.bin`, `Player.bin`, `PlayerAssignment.bin`… ya parcheados;
- `fl26world.txt` con las líneas `league`, `dates`, `uefa`… que leen los módulos;
- `common\character0\...\uniform\team\` con los kits, y los escudos.

Coste medido: **35 s de los 45 son jugadores** (30 por club). Un mundo de 100 ligas son minutos,
no segundos.

## 5. Verificar

```
python tools/check_world.py ^
  --base  <juego>\SiderAddons\livecpk\_FL26Tut\common\etc\pesdb ^
  --worldfile <juego>\SiderAddons\livecpk\_FL26Tut\fl26world.txt
```

Comprueba ids únicos, nombres, códigos de 3 letras, jugadores por club, once inicial, portero,
que cada regulación apunte a una competición existente y que el world file cuadre. **Criterio de
"hecho": 0 errores.**

## 6. Instalar en el juego

1. `leaguebuilder.py on _FL26Tut --game "<juego>"` (o añadir `cpk.root = ".\livecpk\_FL26Tut"` a
   `sider.ini`).
2. Copiar `fl26world.txt` **a `livecpk\_FL26Tut\` y a `SiderAddons\modules\`** (idénticos).
3. Los módulos que el mundo necesite, en orden: `fl26caps` → `fl26regs1200` → `fl26cid16`;
   `fl26swiss` → `fl26cupgrow`.
4. Arrancar y mirar Select Team: la liga debe salir en su país y, si es Master League, tener
   calendario.

## 7. Variantes que ya funcionan

| quiero | cómo |
|---|---|
| dos divisiones | segunda entrada con `"above": "Lliga Tut", "exchange": 2` |
| split (top/bottom) | `"split": {"legs": 2, "groups": [6, 6], "group_legs": 2}` |
| Apertura/Clausura | `"apertura": {"playoff": 8}` (máx. 18 clubes) |
| liga de 30-38 clubes | `clubs: 30` a una vuelta (38 es el techo del calendario) |
| copa KO con byes | `mkcup.py --like 23 --bracket 44` |
| copa de grupos + KO | `mkccup.py --cup "Nombre|CODE|cid|reg|ko|4|191:1,..."` |
| copa de selecciones | `add_world_cups.py` (Mundial 32, EURO 24, Copa América 16…) |
| liga solo para Kick Off | `"exhibition": true` |

## 8. A mano: las tres filas

Cuando no haya builder que te sirva, una competición son tres filas (WESYS + zlib):

```python
# Competition.bin (36 B): region<<3, cid, flags, codigo, nombre de menu
c[3]  = region * 8
c[5]  = cid & 0xFF
c[7]  = cid >> 8          # ampliacion 16 bits
c[8:36] = b"MI_LIGA".ljust(28, b"\0")
c[0x14:0x24] = b"Mi Liga".ljust(16, b"\0")

# CompetitionRegulation.bin (2352 B)
r[0x02:0x04] = reg.to_bytes(2, "little")
r[0x08]      = cid & 0xFF
r[0x09]      = 4          # 3 copa, 4 liga, 2 grupos, 9 split
r[0x0B]      = (r[0x0B] & 0xC0) | clubs        # 6 bits
r[0x0C]      = (r[0x0C] & ~0x3F000) | (1 << 12)  # format 1 = liga
r[0x10]      = (r[0x10] & ~0xF000) | (legs << 12)  # rondas 1..3
# nombres: 20 ranuras de 115 B desde 0x14 (la 2a tirada de 10 empieza en 0x4B2)

# CompetitionEntry.bin (12 B por club)
e[0:4] = team_id
e[4:8] = entry_id        # unico, 9100+ esta libre
e[8]   = cid & 0xFF
e[9]   = position        # base 1; en copa, puesto de sorteo
```

Copiar una fila que funcione y cambiar ids/nombres es más seguro que construir desde cero: así
heredas rondas, prórroga, penaltis y plantilla de jornadas.

## 9. Cuánto puede crecer el juego

Por orden de lo que se agota primero:

| recurso | tope | cuántas ligas de 10 dan |
|---|---|---|
| **slots de Select Team** | 250 | **250 visibles** (slot 123 = ocultas) |
| **clubes por liga (calendario)** | 38 | — (límite de tamaño, no de número) |
| **regiones** | 127 | 127 países; más países comparten región |
| **regulaciones** | 1.200 | ~120 ligas con copa y supercopa |
| **competiciones (cid)** | 1.023 | de sobra |
| equipos | 4.800 | 480 ligas de 10 |
| jugadores | 123.825 | 412 ligas de 30×10 |
| clubes del Edit | 4.700 | ~470 ligas |

Con el mundo vivo (149 ligas, 168 copas) quedan ~100 slots y ~700 regulaciones. El crecimiento
sano es **por países**: una liga nueva + su copa + su supercopa gastan 3 competiciones, 3
regulaciones y 1 slot.

## 10. Desbloquear todo (recetario)

1. **Copas del juego que no salen en el menú** (21): no se crean, se exponen.
   ```
   ccup 49 ko=49 groups=0 entry=0:1236,0:2719,... clubs=1236,2719,... cid=49 fill=20 national=1 days=20,27,34,41 name=Argentina Cup
   ```
   `entry=0:<team>` = club explícito; `entry=<reg>:<pos>` = por posición. **No les pongas
   `like=23`**: tienen `type` 4/8/9 y se bloquean.
2. **Ligas ocultas**: `slot=123` en la línea `league` (juega, no se lista).
3. **cid ≥ 256**: `fl26cid16` (tabla plana de 1024). Sin él solo hay 12 bytes bajos libres.
4. **Filas del menú de copas**: `fl26cupgrow` (256) + `fl26comptab` (una fila oculta por copa).
5. **Pendiente para "todo"**: nombre y sorteo de las copas con cid ≥ 256 (el cid vivo va en un
   byte en `+0x80`), 17 copas no aceptadas por el DLL y los emblemas por byte bajo.

## 11. Errores típicos

| síntoma | causa |
|---|---|
| `Unexpected UTF-8 BOM` | receta guardada con `Set-Content -Encoding UTF8` en PS 5.1; guarda sin BOM |
| `the game's cup dates could not be read` | `--game` sin `FL_2026.exe`; usa el juego real |
| la liga existe pero no juega | sin calendario: revisa `rcal`/`july` o el dword copiado |
| la liga no sale en Select Team | slot 123, o región sin fila en `Competition.bin` |
| el juego se cierra al arrancar | `serve=` en un slot que el exe también llena |
| la copa del juego no entra al menú | `like=` en una copa con `type` 4/8/9 |
