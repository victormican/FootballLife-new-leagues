# Instalación limpia, paso a paso (2026-11-06)

Para montar el mundo en un juego recién instalado, sin restos de pruebas. Cada paso dice cómo
saber que ha salido bien antes de pasar al siguiente.

## 0. Antes de empezar

- Windows 10/11 x64. `FL 2026 start.exe` (o `FL 2027 start.exe`) en su carpeta.
- Guarda una copia de `SiderAddons` y de `Documents\KONAMI\...\2026\save` si ya había algo.
- Herramientas que se usan aquí: **Sider 7.4.1**, **FL Mod Studio 0.3.0**, el **worldpack** y los
  módulos `fl26*.lua` + DLLs del repo (ver `inventario-herramientas-2026-11-06.md`).

## 1. Juego limpio

1. Instala el juego y **arráncalo una vez** hasta el menú. Eso crea las carpetas de guardado.
2. Ciérralo. No hace falta desinstalar nada si la carpeta está limpia (sin `SiderAddons` de pruebas).

**Comprobación:** existe `Documents\KONAMI\SP Football Life 2026\...\save` (o la de FL27).

## 2. Sider

1. Copia `SiderAddons` en la carpeta del juego (junto a `FL_2026.exe`).
2. En `SiderAddons\sider.ini`:
   - `luajit.ext.enabled = 1` (los módulos usan el `ffi` global y `memory`).
   - Los `cpk.root` de los packs que uses y el del mundo (paso 4).
3. Arranca el juego con `FL 2026 start.exe` (no `FL_2026.exe` a pelo: en FL27 el exe directo puede
   cerrarse al crear una Master League).

**Comprobación:** `SiderAddons\sider.log` termina en `Sider initialization complete`.

## 3. FL Mod Studio

1. Instala **FL Mod Studio 0.3.0** (antes FL26 Mod Studio; el ejecutable y la carpeta mantienen el
   nombre).
2. Settings → **Game folder**: la carpeta del juego. El programa detecta FL26 o FL27.
3. **Unpack the game's tables** (la primera vez tarda 1-2 min). FL26 en `%APPDATA%\FL26ModStudio\tables`,
   FL27 en `tables27`.

**Comprobación:** `%APPDATA%\FL26ModStudio\settings.json` apunta a tu carpeta y las tablas existen.

## 4. El mundo

**Por Mod Studio (recomendado):** My world → **+ Add...** → el zip del worldpack → **Install** →
**Activate**. Escribe `livecpk\_FL26MyWorld`, los módulos, las líneas de `sider.ini` y las tablas.

**A mano:** copia `livecpk\_FL26MyWorld` y añade en `sider.ini`:

```
cpk.root = ".\livecpk\_FL26MyWorld"
```

**Comprobación:** `_FL26MyWorld\common\etc\pesdb\` tiene `Competition.bin`, `CompetitionEntry.bin`,
`CompetitionRegulation.bin`, `Team.bin`, jugadores, etc.

## 5. Módulos y DLLs

1. Copia a `SiderAddons\modules\` los `fl26*.lua` y `fl26clubs.dll` / `fl26swiss.dll`.
2. Deja `modules\fl26world.txt` (lo escribe Mod Studio; a mano va con el mundo).
3. En `sider.ini`, el bloque de módulos (el orden importa):

```
lua.module = "fl26caps.lua"
lua.module = "fl26appcap.lua"
lua.module = "fl26regs1200.lua"
lua.module = "fl26slots750.lua"
lua.module = "fl26slot7.lua"
lua.module = "fl26guards.lua"
lua.module = "fl26regfast.lua"
lua.module = "fl26walk.lua"
lua.module = "fl26compcache.lua"
lua.module = "fl26joindll.lua"
lua.module = "fl26hdr255.lua"
lua.module = "fl26chain.lua"
lua.module = "fl26comptab.lua"
lua.module = "fl26slotnames.lua"
lua.module = "fl26cid16.lua"
lua.module = "fl26playercap.lua"
lua.module = "fl26embprobe.lua"
lua.module = "fl26clubs.lua"
lua.module = "fl26regen.lua"
lua.module = "fl26editlist.lua"
lua.module = "fl26edit.lua"
lua.module = "fl26rank.lua"
lua.module = "fl26deeprank.lua"
lua.module = "fl26regions.lua"
lua.module = "fl26reg128.lua"
lua.module = "fl26squadlist.lua"
lua.module = "fl26catlist.lua"
lua.module = "fl26swiss.lua"
lua.module = "fl26cupfree.lua"
lua.module = "fl26cupgrow.lua"
lua.module = "fl26augseason.lua"
lua.module = "fl26lateguards.lua"
lua.module = "fl26seasonend.lua"
```

**Comprobación:** en `sider.log`, `Active modules: NN` y cada `OK: Lua module initialized`.

## 6. Verificación de datos

```
python tools/check_world.py --base "<juego>\SiderAddons\livecpk\_FL26MyWorld\common\etc\pesdb" --worldfile "<juego>\SiderAddons\modules\fl26world.txt"
```

Debe dar `0 error(s), 0 warning(s)`. Recuentos de referencia: 512 competiciones, 711 regulaciones,
5.667 entradas, 154 ligas, 152 slots, 286 ccup.

## 7. Verificación en el juego

1. **Select Team** (Partido local): las ligas salen con sus clubs; con el cursor en una liga, la
   lista de la derecha muestra sus clubs (0.3.0).
2. **Liga > Nuevo**: el panel de la liga no debe mezclar clubs de otra competición.
3. **Kick Off > Cup**: las copas salen y se abren.
4. **Master League**: crear una carrera y mirar Team Info de una liga nuestra.

## 8. Problemas conocidos (y qué mirar)

| síntoma | causa / estado |
|---|---|
| Cierre `0x3fd2b2` al abrir Copa | buffer de la lista del menú de Copa; `fl26cupfree` lo mitiga |
| Copa con solo 8 filas la primera vez | la lista se llena al segundo acceso |
| Bélgica 1 equipo la primera vez | la regulación aún no estaba cargada en el primer `count`/`get` |
| Emblema de cid ≥ 256 | se pide por el byte bajo (`emb_<cid&0xFF>`) |
| Listas con clubs de otra competición | censo por byte bajo del cid; 78 de 154 ligas afectadas (`lista-ligas-2026-11-06.md`) |
| Copa 2 con plaza duplicada | venía de los datapacks; corregido con `fix_cid2_entries.py` |

## 9. Orden de arranque para no perder tiempo

1. Sider + juego limpio → menú.
2. Mod Studio → tablas.
3. Mundo → Activate.
4. Módulos/DLLs → sider.ini.
5. `check_world`.
6. Select Team → Liga → Copa → ML.
