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

## Ultimo hallazgo: la vtable no es el camino (25/10 09:00)

Con 1 copa en el world y la sonda `CUPIN` en la entrada de `cupsel_handler`, el log de ese arranque
trae `Cup mode list live` y `Cup mode: 1 competition(s) of the world to expose` y **ninguna linea
`CUPIN` ni `CUPVEC`**: el handler parcheado en `CUPSEL_VT_RVA` **no se ejecuta**.

Consecuencia: el menu de Cup de este build no pasa por esa vtable. Cuando el handler si corria
(estado de las 22:00) la lista salia; cuando no, el juego se queda con una lista vacia y pinta
blanco. El siguiente probe no va a la vtable sino al **constructor del vector**: enganchar
`VirtualAlloc`/`operator new` durante el primer pintado, ver quien reserva el bloque de 13 items de
12 bytes y parchear la capacidad.

## Backlog ordenado (facil -> dificil)

1. **Documentacion y vault al dia** (este documento, entradas 287-289).
2. **Banderas reales de las 8 no FIFA** (hoy hay placeholder con el id; basta poner PNG encima).
3. **Quitar/renombrar "Liga NN Clubes MM"** en el world: nombres reales por liga.
4. **Copas del juego sin equipos** (Gold Cup 156, OFC Nations 157, Nations Leagues 159/160): darles
   entradas con selecciones reales, como ASEAN/Caribe.
5. **Other Europe (69) y Other Asia (70)**: pasar de `serve=` a slot directo y subir de 20 a 48.
6. **check_world: duplicados 128/192/255** del juego (decidir si se limpian o se toleran).
7. **`Country.bin` nuevo en el livecpk**: confirmar que el motor acepta filas; si no, dejar las 8
   selecciones sin bandera desde el juego.
8. **Hook de Cup mode** (el bloque de arriba): probe de `VirtualAlloc`, constructor, capacidad 64.
9. **cid 262/263/304**: lectura por byte sin localizar en Select Team.
10. **"Datos del usuario"**: falta saber si la fila sale arriba o dentro de un grupo.
11. **48 clubes por regulacion / arrays de jugadores y equipos**: mudanza de offsets, fuera de PR.

