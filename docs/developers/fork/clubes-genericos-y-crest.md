# Clubes genéricos, escudos y emblemas (2026-11-04)

Por qué las ocho ligas nuevas salieron con "escudos de copas" y clubes con nombre de club real,
y qué se hizo. Todo verificado sobre el mundo vivo de `D:\SP Football Life 2026 - copia - copia`.

## 1. Los escudos no eran de copas: no había escudo

El juego sirve el escudo de un club desde

    common/render/symbol/flag/e_<id de equipo, 6 dígitos>_r[_l|_ll].png

y el de una competición desde

    common/render/symbol/emblemLc/emb_<cid, 4 dígitos><variante>.png

En el mundo vivo faltaban **1120 escudos de club** (de los 2665 clubes nuestros: los 96 de las
ocho ligas, la Primera B Metropolitana entera, etc.) y **8 emblemas de competición** (cid
258..265). Con el fichero ausente el juego cae a un badge que no es el del club, y de ahí la
sensación de "escudos de copas". No era cosa de las `ccup`: quitarlas no habría cambiado nada.

Generado lo que falta, sin tocar nada existente:

    python tools/mkcrests_missing.py --team-bin <Team.bin del mundo> --flags <raíz livecpk>
    python tools/mkemblems.py --base <pesdb del mundo> --out <raíz livecpk> --only 258,...,266

`mkcrests_missing.py` es nuevo: escribe solo los ids que no tienen `e_<id>_r.png`, a los tres
tamaños y con el mismo color determinista de `mkcrests.py` (así un club no cambia de escudo al
repetir la herramienta).

## 2. `mkemblems.py` no veía los cid de 16 bits

`competitions()` leía `r[0x05]` a secas y el nombre de la regulación por el mismo byte. Con el
mundo de cid 16 bits eso da el byte bajo: cid 258 se leía como 2 (una competición del juego) y
`--only 258` no encontraba nada ("this pesdb folder adds no competition to the shipped 91").
Ahora lee `r[0x05] | (r[0x07] << 8)` y `r[0x08] | (r[0x492] << 8)`.

## 3. `fill_group.py` se llevó por delante la Serie A

Mismo byte bajo, pero con consecuencias: `cid = regs[ri + R_CID]` valía **10** para la liga de
Austria (cid 266 = 10 | 1<<8), así que `fill_group --reg 908 --reset` borró las **20 entradas de
la Serie A** (cid 10) y las sustituyó por los 16 clones nuevos. Reparado a mano desde
`CompetitionEntry.bin.before-usfix-20261104-092305` (backup de las 09:23, antes del destrozo) y
dejando `CompetitionEntry.bin.before-austriafix` como copia del estado roto.

Corregido en el código: lee `r[0x08] | (r[0x492] << 8)`, filtra por
`e[0x08] | (e[0x0b] << 8)` y escribe los dos bytes del cid al añadir la entrada.

Lección: **todo lo que lea o escriba un cid tiene que usar los 16 bits**. Los sitios ya
corregidos: `mkemblems.competitions`, `fill_group`, `generic_clubs`, `mkcrests_missing` (no usa
cid), `check_world` (ya lo hacía).

## 4. Los clubes ya son genéricos de verdad

Las ocho ligas se construyeron reciclando filas de `Team.bin` que nadie usaba
(`add_eight_leagues.py`) y luego renombrándolas con nombres de clubes reales. Las filas, las
plantillas y los ids eran nuestros, pero el menú leía Kocaelispor, AaB, St Johnstone... en un
mundo de clubes genéricos.

`tools/generic_clubs.py` reescribe **solo el nombre**: `<liga> Club NN` en las 20 ranuras del
club y `<club> Player NN` en los 22 jugadores, más la abreviatura `GNN`. No toca ids, entradas,
asignaciones ni escudos (el escudo va por id), así que es seguro sobre un mundo que ya se juega.

    python tools/generic_clubs.py --base <pesdb> --worldfile <fl26world.txt> --reg 900,...,907

## 5. La 2ª liga de Austria

`tools/add_league_generic.py` añade una liga **vacía** (competencia, regulación y línea del
mundo) y los clubes los crea después `fill_group.py`, que clona una plantilla por club. Es el
camino de todas las ligas genéricas del mundo: no recicla ninguna fila del juego.

    python tools/add_league_generic.py --base <pesdb> --worldfile <fl26world.txt> \
        --name "Austrian Second League" --cid 266 --reg 908 --region 123 \
        --country 194 --conf 2 --slot 208 --kickoff 25 --code FL_AT_D2
    python tools/fill_group.py --base <pesdb> --worldfile <fl26world.txt> \
        --reg 908 --reset --to 16

Resultado: cid 266, regulación 908, `slot=208`, 16 clubes `Austrian Second League Club 01..16`,
352 jugadores nuevos, emblema `emb_0266` y 48 escudos.

## 6. Los slots 200..208

`fl26comptab` reparte los slots libres y le tocaron 200..207 a las ocho ligas (208 a Austria).
Como son slots que **crea** `fl26slots250` (el exe solo tiene 123), el juego no tiene lista
propia de clubes ahí: `fl26clubs.lua` los sirve desde la regulación de cada liga, y para eso hay
que tener el slot en `SERVED` y el `slot=` explícito en la línea del mundo. Sin las dos cosas la
liga no se dibuja.

## 7. El byte bajo del cid: la lista de clubes también

Medido el 2026-11-04 con el mundo en marcha: **el censo de Select Team busca la lista de clubes
por el byte bajo del cid**, no por el cid. Yokary (cid 265) caía en el nodo de la competición 9
y su slot listaba los 20 clubes de la Premier League; Austria (266) los 20 de la Serie A;
Russian First (261) los 17 de la Libertadores; TT Premier (258) los 33 de la Champions. No era
un club movido ni duplicado: era la lista equivocada, con los nuestros detrás.

Las nueve ligas se movieron con `tools/move_cids.py` a los únicos bytes bajos que no tienen
clubes de ninguna competición (12 en todo el mundo):

| liga | cid viejo | cid nuevo | byte |
|---|---|---|---|
| TT Premier | 258 | 301 | 45 |
| TFF 1. Lig | 259 | 302 | 46 |
| Aruba | 260 | 303 | 47 |
| Russian First | 261 | 326 | 70 |
| Danish 1. Division | 262 | 327 | 71 |
| Scottish Championship | 263 | 328 | 72 |
| Swiss Challenge | 264 | 353 | 97 |
| Yokary Liga | 265 | 359 | 103 |
| Austrian Second League | 266 | 483 | 227 |

`move_cids.py --free` imprime los doce (1, 37, 45, 46, 47, 70, 71, 72, 86, 97, 103, 227); el 1
choca con la Sudamericana (513) y el 37/86 son la Copa y la Liga personalizadas del juego, así
que quedan **tres libres**.

**Consecuencia para la planificación:** de este tipo de liga (cid ≥ 256) solo caben **12**, no
115. Los slots dan para 115, pero el juego identifica estas ligas por el byte bajo. Para pasar de
12 hay que parchear el censo (es el `cmp`/`cid` de `fl26cid16`, que ya mató el juego a los 25 s
cuando se activó).

## 8. Emblemas de todo el mundo

`mkemblems.py` gana tres opciones: `--missing` (solo lo que aún no tiene fichero), `--shipped`
(el `pesdb` de base con el que comparar, para no necesitar `modscan`) y `--bytes` (escribe en
`emb_<cid & 0xFF>`, que es la ruta que el exe pide de verdad para un cid > 255).

    python tools/mkemblems.py --base <pesdb> --out <raíz livecpk> \
        --shipped C:\Users\viarm\test-carpeta\pesdb\_base --missing
    python tools/mkemblems.py --base <pesdb> --out <raíz livecpk> \
        --bytes --only 301,302,303,326,327,328,353,359,483

Resultado: 181 de las 265 competiciones del mundo tienen emblema propio por livecpk. Las 84
restantes son competiciones del juego (cid ≤ 145 y la Sudamericana 513) y conservan el suyo del
CPK; no se pisan. Ocho de las nueve ligas quedan claveadas en un byte que una competición del
juego también usa (45/46/47 partido amistoso, entrenamiento y retirada; 70/71/72 play-offs de
segunda; 97 retirada; 103 World Selection), así que esos badges de partido muestran el de nuestra
liga: es el precio de que la fila tenga escudo.

## Comprobación

`check_world.py` sobre el mundo vivo: **0 errores**, 1 aviso preexistente (competición 2, copa
del juego con dos clubes en la posición 32), 4111 entradas, 265 competiciones, 419 regulaciones,
3430 equipos, 89048 jugadores.
