# El grupo "Other Clubs (Africa)" (slot 75) (2026-11-05)

## Lo que había

- **Cabecera**: slot 75 tiene su case propio en el switch de nombres (`0x140ea08e0`, case 10) y
  `fl26slotnames.lua:78` lo protege: como ninguna liga del mundo está en ese slot, no se libera y
  sigue diciendo **"Other Clubs (Africa)"**.
- **Clubes**: 48 clubes CAF con el nibble `+0x4f = 7` (ver `otros-grupos.md`).
- **Icono**: `emb_0165_*` (6 tamaños) existe en `common/render/symbol/emblemLc/`.

## Lo que fallaba

La **lista** del slot. El juego no la llena con clubes extranjeros (medido: el relleno de los
slots de pool nunca devuelve un club que no sea suyo), así que la cabecera existía pero el grupo
salía vacío u oculto. `fl26clubs.dll` ya sabe contestar una lista desde una regulación, pero solo
para los slots que el world file le nombra, y no había forma de nombrar el 75 sin poner una liga
en él (poner una liga ahí aborta toda la tabla de Select Team).

## El cambio

Nueva línea de mundo, `pool <slot> <regulación>`, leída por `fl26clubs.lua`:

```
pool 75 181
```

Significa: "la lista del slot 75 se contesta desde la regulación 181" (la competición 165,
"Other Clubs (Africa)", 48 clubes), sin pedirle a `fl26comptab` una fila de parámetros en ese
slot. No crea liga, no entra en ninguna temporada y no toca el switch de nombres.

Arranque medido:

```
fl26clubs: world file -- 150 leagues, 13 on slots the game fills itself, 2 on pool slots
fl26clubs: live -- 13 slots served from our own regulations: 75<-181 80<-76 72<-178 ...
```

El juego arranca sin cierre. El grupo debe salir en Select Team con su cabecera, sus 48 clubes y
el emblema de la competición 165.

## Si hubiera que quitarlo

Borrar la línea `pool 75 181` del world file (las dos copias) y reiniciar: el módulo vuelve a
dejar el slot al juego, como antes. El módulo entiende la línea aunque no exista (lista vacía).
