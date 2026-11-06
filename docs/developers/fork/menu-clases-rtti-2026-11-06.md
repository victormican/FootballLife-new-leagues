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
