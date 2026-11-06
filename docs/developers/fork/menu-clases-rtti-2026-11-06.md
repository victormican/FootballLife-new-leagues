# Menús por RTTI: Select Team, Copa y Editar (2026-11-06)

El ejecutable conserva **RTTI de MSVC**: 10.297 clases con nombre. Cada clase polimórfica tiene su
TypeDescriptor (`.?AVNombre@@`), un CompleteObjectLocator que lo apunta y una vtable cuyo slot -1
apunta al locator. Con eso se va de **nombre de clase a vtable y a sus métodos virtuales** sin
desensamblar el ejecutable entero:

```
python tools/rtti_vtables.py MenuModeCupSelect TeamSelectCommon MenuEditMenu
```

## Clases (RTTI)

**Copa**
- `menu::MenuModeCupSelect` — vt **0x142692c40**. Es el modo de la pantalla Kick Off > Copa:
  el DLL engancha su `+0xd8`.

**Select Team**
- `menu::TeamSelectCommon` — vt **0x14271c8c8** (base de la pantalla).
- `menu::TeamSelectMatchBase` — vt 0x14271fb68.
- `menu::TeamSelectExhibition` — vt 0x1426833e8.
- `menu::TeamSelectSingle`, `TeamSelectSingleSearch`, `TeamSelectDefaultTeamML`,
  `menu::MatchTeamSelectTraining`, `menu::OnlineMatchTeamSelect`... (una por modo).

**Editar** (237 clases con `Edit`), rama liga/copa:
- `menu::MenuEditMenu` — vt **0x1426f79f0** (menú raíz de Editar).
- `menu::MenuEditLgCpSelectCategory`, `MenuEditLgCpSelect`, `MenuEditLgCpMain` (vt 0x1426ef848),
  `MenuEditLgCpDetailSetting` (0x1427037b0), `MenuEditLgCpChangeName` (0x14270bed0),
  `MenuEditLgCpCardTypeSelect`, `MenuEditLgCpEmblemEditMain`, `MenuEditLgCpEmblemDefaultDialog`.
- Organizar liga: `MenuEditLeagueOrganizeMain/Base/TeamNum`, `EditLeagueOrganizeAreaSelect`.
- Equipos/jugadores/entrenadores: `MenuEditTm*` (nombre, emblema, equipación, entrenador),
  `MenuEditPl*`, `MenuEditCoach*`.
- Importar/exportar datos: `MenuEditCompeIm*`, `MenuEditExternalDataMain`, `MenuEditDataCreateDialog`.

## La vtable de la Copa, entera

`MenuModeCupSelect` (0x142692c40); los slots que importan:

| slot | dirección | qué es |
|---|---|---|
| +0x18 | 0x140b1c8c0 | junto al destructor 0x140b1c810 |
| +0x20 | 0x140e3f1e0 | (común a todos los menús) |
| +0x58 | **0x140e43450** | **enter**: llama al slot `+0xd8` y, si devuelve ≠0, recorre filas, `0x140e3f4c0`, y cambia de modo |
| +0xd8 | **0x140b1c990** | **init**: construye la lista (`+0x90` begin, `+0x98` end, `+0xa0` cap). Es el que el DLL sustituye |
| +0x120 | 0x140b1ce90 | |
| +0x128 | 0x140c6b310 | |
| +0x130 | 0x140b1cec0 | |

## Vtable base común

`MenuModeCupSelect`, `TeamSelectCommon`, `MenuEditMenu` y `MenuEditLgCpMain` comparten **los mismos
slots 0x00..0x50** (0x141fa0f90, 0x140e3bb90, 0x140e3eaa0, 0x140e3f1e0, 0x141fa15a0, 0x140e3ef10,
0x140e3eef0, 0x140e43530, 0x140e43780...): es la API genérica de un modo de menú. La primera
diferencia está en `+0x18` (0x140c93200 en TeamSelect, 0x140c26c30 en EditMenu, 0x140c18e90 en
LgCpMain), que es el método propio de cada pantalla.

## Ghidra

`rea decompile` con Ghidra 12.1.4 sobre `FL_2026.exe` **aborta**: el análisis del ejecutable de
438 MB no cabe en el plazo de 330 s del proveedor (`provider_timeout`,
`operation=procedure_pseudo_code`). Ghidra sí está sano (headless, decompilador x64, JDK 21).

Para usarlo hay que darle **solo la sección de código** (`.trace`, 38 MB, VA 0x140001000) como
`raw-binary` a 0x140001000 y descompilar funciones sueltas; o subir el plazo del proveedor.

## Lo que esto habilita

- Saber qué pantalla es cuál y qué método la construye, sin adivinar por cadenas.
- Enlazar el editor del juego (`MenuEditLgCp*`) con las tablas que escribe: si el juego deja
  editar nombre/emblema/equipos de una competición, esa es la vía para que lo insertado quede
  "como lo suyo" (y para ver qué campos mira antes de listarlo).

## Constructores y el mito del fichero de menú (2026-11-06, tarde)

Con `tools/vtable_xrefs.py` (busca el `lea`/`mov imm64` que guarda cada vtable) salen los
constructores:

| clase | vtable | constructor |
|---|---|---|
| `MenuModeCupSelect` | 0x142692c40 | 0x140b1c6xx (destructor 0x140b1c810 al lado) |
| `MenuEditMenu` | 0x1426f79f0 | 0x140c26ac0 |
| `MenuEditLgCpMain` | 0x1426ef848 | **0x140c18dd0** |
| `TeamSelectCommon` | 0x14271c8c8 | 0x140c92eex |

`MenuEditLgCpMain` (0x140c18dd0): llama a la base (0x140e38940), guarda sus vtable en `[this]` y
`[this+0x70]`, pone `[this+0x90]=0`, y **solo carga dos assets**:

```
lea rax, "cpk_data/common/menu/mode/editSettingList.bin"
lea rax, "editSettingList"
call 0x140e3ef30 / 0x140e3f0e0
```

Ese `.bin` **no es la lista de ítems**: extraído de `dt11_x64.cpk` (`tools/cpkread.py`) y
descomprimido (WESYS) es un paquete de texturas `TXP2` (`afp_editSettingList.apk`). Lo mismo pasa
con `modeMainMenu.bin`, `editTeamInfo.bin` y `editLeagueOrganizeMenu.bin`: todos son `afp_*.apk`
(atlas de texturas).

Conclusión: los ítems de los menús **no están en datos**: se construyen en código, y los `.bin` de
`common/menu/mode` son solo su arte. Así que "de arriba abajo" hay que sacarlo de los métodos
virtuales de cada clase (init/enter), no de un fichero.

## Cómo seguir con el menú Editar
1. Localizar en cada `MenuEdit*` su slot de inicialización (el que añade ítems: en la Copa es
   `+0xd8`; en las demás clases hay que mirar los slots propios, los que no son la base común
   `+0x00..+0x50`).
2. Desensamblar ese método con capstone (rápido) o con Ghidra sobre la **sección `.trace` sola**
   (38 MB) como `raw-binary`, que evita el timeout de los 438 MB.
3. Los ítems se añaden con llamadas que llevan un id de texto; el id se resuelve contra la tabla de
   textos del juego, que es la que da el rótulo ("Nombre", "Emblema", "Organizar"...).

## El menú Liga: la misma máquina que la Copa (2026-11-06)

| clase | vtable | `+0x18` | `+0x58` | `+0xd8` |
|---|---|---|---|---|
| `MenuModeCupSelect` | 0x142692c40 | 0x140b1c8c0 | **0x140e43450** | **0x140b1c990** |
| `MenuModeLeagueSelect` | 0x1426745e8 | 0x140ac3050 | **0x140e43450** | **0x140b3be30** |
| `MenuModeLeagueSelectStart` | 0x142674860 | 0x140ac30a0 | **0x140e43450** | 0x140ac32e0 |
| `MenuModeLeagueSelectCategory` | 0x142677860 | 0x140accc00 | **0x140e43450** | 0x140accce0 |
| `MenuModeCompeSelect` | 0x14268cd40 | 0x140b08a50 | **0x140e43450** | 0x140b08b70 |
| `MenuModeCompeSelectBase` | 0x142716088 | 0x140c6b2d0 | **0x140e43450** | 0x140c6bb50 |

Lo importante: **`+0x58` es el mismo enter para todos** (0x140e43450) y **`+0xd8` es el que
construye la lista** de cada modo. O sea:

- el hook del DLL en `+0xd8` no es "de la copa": es el mismo punto que usa el menú Liga (y los
  CompeSelect de Master League). Sirve igual para inyectar filas en Liga.
- el enter (0x140e43450) es común: llama al `+0xd8` y, si devuelve ≠0, recorre filas
  (`[this+0x88]`, 0x50 B cada una), llama a 0x140e3f4c0 y cambia de modo. Por eso el
  comportamiento raro al entrar (volver al menú, morir) es el mismo en Copa y en Liga.
- `+0x120/0x128/0x130` son los otros métodos propios (transición, teardown, etc.).

## Menú Copa a fondo: init, item y resolver por cid (2026-11-06)

```
MenuModeCupSelect +0xd8 = 0x140b1c990   (init)
    call 0x140c6bb50        base: el MISMO init de MenuModeCompeSelectBase
    call 0x140b1cc60        recorre la lista [this+0x90..0x98] de items de 12 B
         para cada item: 0x140b1cda0(&item)   <-- resolver por competicion
    call 0x140e3dc90        objeto de UI de la pagina
    lea rdx, "page"         y lo asigna en el objeto +0x98
```

`0x140b1cda0(item)` es el que decide si una competicion puede pintarse:

```
owner() -> bloque
g = phkind(cid, 2)      ; fase de grupos (0xffff = ninguna)
k = phkind(cid, 3)      ; eliminatoria
if k != 0xffff:
    rec = findrec(bloque, k)
    item[+4] = rec[0x30c] & 0x7f          ; CLUBES
    item[+5] = 0                          ; sin grupos
    item[+6] = (rec[0x300] >> 29 == 1) ? 1 : (== 2)
    item[+7] = (rec[0x300] & 0xe0000000) == 0x40000000
    item[+8] = (rec[0x304] >> 9) & 1
if g != 0xffff:
    rec = findrec(bloque, g)
    item[+5] = 1
    item[+4] = rec[0x30c] & 0x7f          ; CLUBES (de la fase de grupos)
```

**El item de la lista es, entonces:**

| offset | campo |
|---|---|
| +0 | cid de competición (lo que se escribe al añadir) |
| +4 | nº de clubes |
| +5 | 1 = tiene fase de grupos, 0 = eliminatoria directa |
| +6, +7, +8 | bits de formato leídos de `rec+0x300` / `rec+0x304` |

Detalles que importan para lo insertado:

- **No hay comprobación de nulo**: `findrec` se desreferencia directo (`[rax+0x30c]`). Si `phkind`
  devuelve un id cuya regulación no está en el bloque, el juego peta ahí mismo. Es la clase de
  fallo que hay que evitar al meter una copa nueva.
- La copa nuestra (200, cid 131) da `k2=0xffff, k3=200`: entra por la rama de eliminatoria, con
  **16 clubes** y `has_group=0` — la misma forma que la 36 (Mundial de Clubes).
- El init **no** construye las filas de la pantalla: esas salen del enter común (`+0x58`,
  0x140e43450) y de `[this+0x88]`, que es donde hay que mirar cuando "entra y vuelve".

## Liga Master: mismos slots en todas las pantallas ML (2026-11-06)

| clase | vtable | `+0x18` | `+0x58` | `+0xd8` | `+0x120` |
|---|---|---|---|---|---|
| `MenuModeMLTeamStatus` | 0x1426aff58 | 0x140b8ab20 | 0x140e43450 | 0x140b8acf0 | 0x140e3f520 |
| `MenuModeMLPlayerManagement` | 0x1426a8c40 | 0x140b6e9c0 | 0x140e43450 | 0x140b6eca0 | 0x140e3f520 |
| `MenuModeMLNegociationMenu` | 0x1426a8050 | 0x140b6c5b0 | 0x140e43450 | 0x140b6c660 | 0x140e3f520 |
| `MenuModeMLCoachMenu` | 0x1426a7830 | 0x140b6b200 | 0x140e43450 | 0x140b6b2b0 | 0x140e3f520 |
| `MenuModeMLJournalList` | 0x1426a5b30 | 0x140b61fc0 | 0x140e43450 | 0x140b620a0 | 0x140e3f520 |
| `MenuModeMLTrainingSelect` | 0x14269cc78 | 0x140b37dd0 | 0x140e43450 | 0x140b385d0 | 0x140e3f520 |

**Regla general del sistema de menús** (Copa, Liga, CompeSelect, ML y BL):

- `+0x58` → **0x140e43450**, el enter común: llama al `+0xd8`, y si devuelve ≠0 recorre las filas
  de `[this+0x88]` (0x50 B por fila), llama a 0x140e3f4c0 y cambia de modo.
- `+0xd8` → constructor de la lista **de cada pantalla** (Copa 0x140b1c990, Liga 0x140b3be30,
  MLTeamStatus 0x140b8acf0...). Es el punto de inyección universal.
- `+0x120` → 0x140e3f520 en casi todas (base), y `+0x18` es el montaje propio de cada pantalla.

Consecuencia práctica: lo aprendido de la lista de la Copa (items de 12 B, resolver 0x140b1cda0,
filas en `+0x88`) se aplica **igual** a Liga y a Liga Master, cambiando solo el `+0xd8` de la
clase que se quiera tocar.

## Cómo seguir con el menú Editar

