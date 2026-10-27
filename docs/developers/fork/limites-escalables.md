# Como se escalan los topes (medido, 2026-10-27)

Este documento sustituye a la idea de "parchear a mano el exe". Los topes **ya estan subidos**,
pero no por codigo suelto: por un generador que verifica cada byte antes de escribir. Entender
esa cadena es lo que permite subir el siguiente tope sin romper el juego.

## 1. Estado medido (no estimado)

`python tools/limits.py` lee los topes de `patches/layout.json` y lo que hay de verdad en el
livecpk. Salida de hoy, con el livecpk `_FL26All` y el world vacio:

| tope | usado | limite | libre | fuente |
|---|---|---|---|---|
| jugadores | 120.666 | 123.825 | 3.159 | `layout.json` (`Player.bin`) |
| equipos | 3.802 | 4.800 | 998 | `layout.json` (`Team.bin`) |
| entrenadores | 1.078 | 6.800 | 5.722 | `layout.json` (`Coach.bin`) |
| regulaciones | 214 | 1.200 | 986 | `layout.json` |
| partidos del calendario | - | 65.000 | 65.000 | `layout.json` (rec596) |
| rondas (fixtures) | - | 8.000 | 8.000 | `layout.json` |
| clubes del Edit | 3.802 | 4.700 | **898** | `tools/native/fl26edit.c` |
| slots de Select Team | - | 250 | 250 | `fl26slots250.lua` |
| copas del menu | - | 512 | 512 | `fl26swiss.c` (`MAX_CCUP`) |
| ids de competicion | - | 511 | 511 | `fl26cid16.lua` |
| clubes por regulacion | - | **48** | - | estructural |

**El siguiente muro real es la lista de clubes del Edit (898)**, no los jugadores.

## 2. La cadena: de `layout.json` a `fl26caps.lua`

```
patches/layout.json          una sola fuente de verdad: donde vive cada array, su stride,
                             su cap viejo y su cap nuevo, y todas las direcciones que lo leen
        |
        v
tools/patchset.py <set>      desensambla cada direccion del exe, localiza el campo de 4 bytes
                             dentro de la instruccion y emite {va, old, new, why}
        |
        v
patches/<set>.json           el set completo, con el bloque nuevo y las bases nuevas
sider/fl26caps.<set>.lua     el aplicador (generado)
sider/fl26caps.lua           la copia que se instala
```

El aplicador es **todo o nada**: primero lee las ~3.500 direcciones y compara con los bytes que
el generador vio en el exe; si **una** no coincide, no escribe nada y el juego arranca sin
ningun tope. Eso es una red de seguridad, y a la vez el motivo de un fallo que costo dias:

> **Regla de oro.** Ningun otro modulo (ni DLL, ni otro Lua) puede escribir en una direccion que
> el set verifica. Si la pisa *antes*, el set aborta entero. Si la pisa *despues*, el set queda
> aplicado pero con una parte reescrita por el otro, y el resultado es un mundo a medias.

## 3. Por que el realojo de la tabla de jugadores rompia Edit (causa final)

El set **ya realoja** esa tabla: el bloque crece de `0x1877068` a `0x64D1D68` y la parte de
jugadores se sube de `+0xEE53D0` a `+0xFAD4D0` con **123.824 entradas** (`0x140af23b6`,
`0x140afd849`, `0x1412e67ff`, mas el contador `0xBA 30 75 00 00 -> BA B0 E3 01 00` en
`0x140af23cf`).

El experimento de `fl26swiss.c` escribia un `jmp` en `0xAF23B3`, que **pisa los bytes de
`0xAF23B6`** — la misma instruccion que el set mueve. Resultado: dos tablas de jugadores, una en
nuestro `VirtualAlloc` (la que veian las rutas que enganchamos) y otra en el bloque (la que veian
las otras diez). El juego saltaba a datos (`0x105EA0000 add [rax],al`), que es exactamente lo
que se veia en el depurador.

Conclusion: **no hay que realojar nada**. La tabla ya esta realojada, y por eso con la DLL del
commit (sin el experimento) el juego no se cierra.

## 4. Muros duros (y por que lo son)

| muro | valor | por que no se sube con un parche |
|---|---|---|
| clubes por regulacion | 48 | la lista esta literalmente en `+0x170` con 48 handles; los grupos "Other" pintan 48 como maximo |
| copas del menu | 13 utiles | es un `std::vector` de heap del constructor del menu: hay que enganchar `reserve`/`push_back`, no reemplazar un puntero |
| lista de ids de entrenador | 1.300 | `+0x1d4c0` con 1.300 entradas de 4 bytes y su contador en `+0x1e912`: `0x1d4c0 + 1300*4 == 0x1e910`, la tabla termina dos bytes antes de su propio contador. Subirla escribe ids encima del contador |
| tabla de `upper2` | 30.000 | busqueda lineal de 8 bytes por entrada dentro del bloque; no crece sin sitio detras, asi que los jugadores por encima de 30.000 simplemente no estan (y eso es seguro) |
| array de jugadores | 123.825 | empieza en `+0` (los accesos no llevan desplazamiento): **crece en sitio**, no se puede realojar. Su techo es el primer campo del bloque que no se mueve, `0x16705a8` (tabla de ranking de clubes) |
| tabla de textos | ~70.844 ids | se enumera entera al entrar en Edit; un nombre con id mayor no existe y el hash se sale |

El techo del array de jugadores merece numeros: `0x16705a8 / 0x17c = 61.918`, menos de la mitad
del cap actual. El set esta en **123.825** porque se genero sin `--player-cap` (el guardia solo
salta cuando se pasa el argumento): el bloque crece y lo que se recoloca **va despues** del
array, de modo que el array puede pasar de largo por encima de esos campos. Funciona, pero es una
zona donde el generador ya no avisa: si algun dia se sube mas, hay que mirar a mano que no quede
nada sin recolocar en `0x16038a8..0x1877068`.

## 5. Como se sube cada tope (receta)

Todos los de `layout.json`:

```powershell
# 1. editar patches/layout.json: arrays.<nombre>.cap_new (y cap_old si el de partida cambia)
# 2. regenerar el set completo (tarda unos minutos: desensambla el exe entero)
python tools/patchset.py teams-coaches-regs-players-dates-matches-upper-mlcopy-fixtures-calendar
# 3. comprobar el diff y que el tamano del bloque es el esperado
git diff --stat patches sider
# 4. instalar y arrancar: el log dice "applied all N patches" o "MISMATCH ... nothing written"
copy sider\fl26caps.lua "<juego>\SiderAddons\modules\fl26caps.lua"
```

Reglas que el generador hace cumplir y que hay que respetar al elegir el numero:

- el bloque solo puede crecer en multiplos de `0x80` (el `memcpy` de la copia de seguridad es un
  bucle desenrollado con cola fija de `0x68`);
- las bases de los arrays se alinean a 16;
- el cap de jugadores tiene que ser **17 mod 32** (las colas de `memcpy` de la tabla empaquetada
  de la copia de modo: `0x9c` por jugador);
- el array de equipos que crece mueve **todo** lo que tiene encima en la copia A (y su tamano
  de objeto), y ademas su array lateral de `0x10` bytes por equipo.

Los que **no** estan en `layout.json`:

| tope | donde | como |
|---|---|---|
| clubes del Edit 4.700 | `fl26edit.c` (`TEAMS`), accesor en `0x1EF21D0` (`mov eax,0x2EE;ret`) | constante del modulo + el accesor se parchea desde el propio modulo |
| slots 250 | `fl26slots250.lua` | tabla del menu copiada y repuntada (`fl26comptab`), sin tocar el bloque |
| copas 512 | `fl26swiss.c` (`MAX_CCUP`) | constante nuestra; el limite real es el vector del menu |
| cids 511 | `fl26cid16.lua` | 3 sitios en sitio + 2 cuevas; ids en `Competition.bin +0x20` como palabra |
| clubes por regulacion 48 | `fl26clubs.c` (`MAX_CLUBS`) | estructural, no se sube con datos |

## 6. Que NO hacer (aprendido a base de cierres)

1. **No** parchear a mano una direccion del set desde otro modulo (rompe el todo o nada o deja
   dos copias de la estructura).
2. **No** subir un `cmp` de capacidad sin mover el array: se lee el array siguiente.
3. **No** fiarse de un offset "que funciona hoy": `0xE63DE4` se reescribe en runtime por
   `fl26caps` a `0x6475C08`; la firma tiene que ir por **opcode**, nunca por el desplazamiento.
4. **No** borrar competiciones del juego para hacer sitio: el menu se queda en blanco (ya paso).
5. **No** dar por bueno un arranque sin leer `sider.log`: si el set aborta, todo lo demas sigue
   arrancando y el fallo aparece mucho despues, lejos de la causa.
