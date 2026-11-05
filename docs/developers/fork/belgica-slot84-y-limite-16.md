# Por qué "desaparecieron" los equipos: el DLL se negaba a instalarse, y Bélgica estaba en el slot de Ecuador (2026-11-06)

## 1. La causa de fondo: `MAX_CFG 16`

`fl26clubs.dll` acepta como máximo **16 slots** servidos (`MAX_CFG` en `tools/native/fl26clubs.c`).
El mundo le manda **19**:

```
14 ligas en slots que el juego rellena + 5 líneas pool = 19
```

`fl26_clubs_install` valida `ncfg > MAX_CFG` y devuelve **9**. En `sider.log`:

```
[fl26clubs.lua] fl26clubs: install FAILED (status 9) -- bad slot list. The game is unmodified.
```

Es decir: **no se servía ningún grupo**. Los 48 clubes de "Otros" (Europa, Asia, Latinoamérica,
África), Concacaf y las ligas en slots 200-208 estaban todos muertos; el juego usaba sus listas
de fábrica. Eso explica los grupos vacíos y las listas raras.

Arreglo: `MAX_CFG` 16 → **32** y una línea de log por slot servido:

```
fl26clubs: slot 84 <- reg 111: 16 clubs
```

## 2. Bélgica: el id 111 es el de Bélgica, y estaba ocupado por Ecuador

`fl26comptab` dice, al arrancar:

```
fl26comptab:   id 111 -> row 167 slot  84
```

La fila de fábrica del **id 111** apunta al **slot 84**, que es el de `BELGIUM_D1_LEAGUE`
(cid 111, 16 clubes: Anderlecht, Brujas, Amberes…). Pero en el mundo:

```
league 111 cid=149 ... slot=84 name=Ecuadorian Serie B
```

El id 111 (Ecuador, cid 149, 11 clubes) se había quedado con la fila y el slot de Bélgica.
Resultado: el menú pintaba el **nombre del slot** ("Jupiler Pro League") con **la lista de
Ecuador**, y los 16 belgas no aparecían.

### Arreglo

- **Bélgica** ocupa su id de fábrica:

  ```
  league 111 cid=111 region=8 country=197 conf=2 slot=84 tier=1 \
         promote=0 demote=0 clubs=16 legs=2 kickoff=99 name=Jupiler Pro League
  ```

- **Ecuador** se muda a una regulación **nueva** (id 9000, copia de la 111) en un slot libre:

  ```
  league 9000 cid=149 region=37 country=149 conf=4 slot=209 tier=1 \
         promote=0 demote=0 clubs=11 legs=2 kickoff=99 name=Ecuadorian Serie B
  ```

  Un id > 177 no tiene fila de fábrica: `fl26comptab` le crea la suya en el slot 209.

- `[209] = true` en `SERVED` de `fl26clubs.lua` (el slot 209 es nuestro: hay que servirlo).
- Quitada la línea `pool 84 115` (el slot 84 no es un pool: es una liga con fila propia).
- `CompetitionRegulation.bin`: el registro 111 pasa a ser el de Bélgica (copia del 115) y se
  **añade** el registro 9000 con los datos de Ecuador. Backup: `.before-belg-fix`.

## 3. Comprobado

```
check_world: teams 3648, competitions 758, regulations 954, entries 7280
             153 ligas, 136 slots, 532 lineas ccup, 0 errores
sider.log:   fl26clubs: live -- 19 slots served from our own regulations:
             75<-181 69<-364 71<-256 73<-362 80<-76 209<-9000 84<-111 ...
             104 club(s) of the game kept out of the pools,
             followers class and share for 1450 new club(s)
```

## 4. Pendiente de ver en juego

1. Select Team → **Jupiler Pro League** debe listar los 16 belgas (Anderlecht, Brujas…).
2. Los cinco grupos "Otros" deben listar 48 clubes cada uno.
3. Ecuadorian Serie B debe seguir en su sitio, con 11 clubes.
4. Al abrir Select Team, `sider.log` escribirá `fl26clubs: slot N <- reg R: K clubs` por cada
   slot servido: ahí se ve el número exacto de cada grupo.

## 5. Lo que NO era

- No era el límite de slots (135 usados de 250).
- No era el límite de equipos (3.648 de 4.800) ni de jugadores (103.722 de 123.825).
- No tenían nada que ver los entrenadores.
- Ni el país (`country` es el id de bandera, y sigue siéndolo).
