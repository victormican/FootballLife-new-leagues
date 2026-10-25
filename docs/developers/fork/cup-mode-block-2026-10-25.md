# Cup mode en blanco: bloque de trabajo abierto (2026-10-25)

## Sintoma

Con **una sola** linea `ccup` en el world, Kick Off > Cup sale **en blanco**. Sin ninguna `ccup`,
salen las copas del juego (8). Probado con 1, 9, 12, 17, 18 y 26 copas: todas en blanco salvo el
estado de las 22:00 del 24/10 (world `all-cid5`, tablas `all-cid5`, DLL `EB0681DA`, compcache
desactivado), que pinto 8 + 5.

## Lo que se descarto

| hipotesis | prueba | resultado |
|---|---|---|
| el tope de 13 del menu | `MAX_CCUP` 256 -> 512 (`BA241673`) | no es el tope: con 1 copa tambien falla |
| cids > 255 | 6 copas con cid 256..261 | se quitaron; el blanco sigue |
| competicion ausente en las tablas | `repair_cups.py`, cid 146 | las 18 cids existen como byte en `+0x05` |
| copas sin entradas | 6 copas con 0 entradas | se quitaron; el blanco sigue |
| tablas/world de momentos distintos | emparejados desde el mismo backup | el blanco sigue |
| la copa concreta | `Test Cup 16` nueva (cid 50, reg 256, 16 clubes, entradas) | el blanco sigue |

Conclusion: el fallo esta en el **hook de Cup mode de `fl26swiss`**, no en los datos. El log lo
delata: tras `Cup mode: N competition(s) of the world to expose` **no llega la linea de resultado**
(`N world cup(s) added`), o sea que el handler no escribe la lista.

## Datos del vector (para la sesion de Frida)

- El almacenamiento es un **`std::vector` de heap**, no un array miembro:
  `fl26swiss: Cup mode -- the list is a heap vector, left alone (room 0)`.
- El destructor libera su puntero: **no** se puede sustituir `self+0x90/0x98/0xa0` por memoria
  propia (doble free).
- Camino correcto: hookear el **`reserve`/`push_back`** del constructor del menu y forzar
  capacidad 64, o enganchar el punto donde el juego llena la lista (despues de nuestro handler).
- Diagnostico `CUPVEC` (log de `self/begin/end/cap/caller`) anadido a `fl26swiss.c` y **no llego a
  ejecutarse** en el arranque de prueba: el handler no corre, asi que el problema esta antes.

## Estado actual del mundo

```
world     : 138 ligas, 0 ccup   (juego usable: salen las copas del juego)
tablas    : all-cid5-20261024-155318
DLL       : fl26swiss EB0681DA, fl26edit, fl26clubs
compcache : desactivado en sider.ini (era lo que dejaba el menu en blanco con 0 copas)
backups   : all-cid5 (155318), all-groups-merge (162320), punto-20261024-cups512
```

## Herramientas de este bloque

- `tools/mkccup.py` -- ahora escribe el cid como **palabra** en el campo de competicion,
  regulacion maestra, knockout y entradas.
- `tools/repair_cups.py` -- crea la competicion de una linea `ccup` que falte (copia la del
  Libertadores). **Ojo: `Competition.bin` guarda el cid como byte en `+0x05`** (`M.CID_OFF`), no en
  `+0x20`; leerlo como palabra da basura.
- `tools/fix_cup_entries.py` -- reescribe las entradas de una copa sin ninguna, desde su
  `clubs=`/`entry=`.
- `tools/add_world_cups.py` -- Mundial, CWC 32, EURO, Copa America, Asian Cup y AFCON; hoy con
  cids 256..261 (no usar: rompen el menu).

## Reglas aprendidas

1. **Nunca borrar competiciones del juego** para hacer sitio: deja el menu en blanco.
2. El world que carga el juego es **`SiderAddons\modules\fl26world.txt`**; hay que sincronizar con
   `leaguebuilder.py on _FL26All` tras cada cambio.
3. **`fl26compcache`** puede dejar el menu en blanco: desactivado en este mundo.
4. `check_world` lee el cid como byte: los errores de las ligas TEST con cid 256+ son suyos, no del
   world.
