# La abreviatura del equipo (`Team.bin +0x372`)

El código de tres letras que el menú y el motor usan para un equipo vive en `+0x372`, pegado al
final de un campo de nombre.  Un nombre mal escrito ahí cierra el juego al cargar el mundo, así que
esta nota deja el layout medido, la firma de la caída y cómo repararlo.

## Layout de los nombres

`Team.bin` tiene filas de 1532 B.  Los nombres localizados van en una rejilla de 70 B por slot que
empieza en `0x90`; el texto de cada slot empieza 14 B más adentro (`0x9E + 70·k`):

| slot | base | texto | contenido |
|---|---|---|---|
| 0 | `0x90` | `0x9E` | nombre en el idioma 1 |
| 1 | `0xD6` | `0xE4` | idioma 2 |
| 2 | `0x11C` | `0x12A` | idioma 3 |
| 3 | `0x162` | `0x170` | **nombre canónico** (70 B, el que usa el motor) |
| … | | | |
| 10 | `0x34C` | `0x35A` | **24 B** de nombre corto + **código de 3** en `+0x26` (`0x372`) + nombre largo en `+0x30` (`0x37C`) |
| … | | | |
| 18 | `0x57C` | `0x58A` | último idioma, hasta `0x5D0` |

El slot 10 es el único con esa estructura partida: su texto solo tiene 24 B porque detrás van el
código y otro nombre.  Un club del juego (Ajax, 116) tiene el nombre en `+0x170` y el código en
`+0x372`, y el resto de la zona a cero; una selección (Irlanda, 1) usa varios slots de idioma y
lleva `IRL` en `0x372` más `Irlanda` en `0x37C`.

Los códigos reales pueden ser de una a tres letras (`OM` Marsella, `GS` Galatasaray, `AJA` Ajax).

## La caída

Al cargar el mundo el motor copia ese campo con `strcpy_s(dst, 4, src)` en `0x1414f5b0f`; `src` es
`r12+0x372` o `r12+0x566`.  Con una cadena de **cuatro o más caracteres** el CRT llama a
`invalid_parameter` y el proceso muere con `0xc0000409` (`FAST_FAIL_INVALID_ARG`).

```
ucrtbase!invoke_watson+0x18
  ucrtbase!invalid_parameter+0xc2
    ucrtbase!invalid_parameter_noinfo
      ucrtbase!strcpy_s+0x71
        FL_2026+0x14f5b0f      <- lea rcx,[r15+4Ah]; mov edx,4; lea r8,[r12+rax]
          FL_2026+0x14f6ccf
            FL_2026+0x1b3779c   (thread_start)
```

Es determinista cuando el dato está mal: con `_FL26MyWorld` caía a los ~28 s en 4 de 5 arranques (y
a los 16 s en el quinto).  Con `_FL26Test` y `_FL26All` —cuyos códigos están bien— no caía nunca por
esta firma.

## Cómo se rompía

Un escritor que vuelca el nombre en los veinte slots (`T_NAME = 0x9E`, `T_NAME_SLOTS = 20`) escribe
30 caracteres en un hueco de 70 B, pero en el slot 10 el nombre solo tiene 24 B antes del código.
El nombre «Other European Leagues Club 01» deja su cola `lub 01` justo encima de `0x372`.

## Reglas

1. **Nunca** escribir más de 24 B en el texto del slot 10 (`0x35A..0x371`).
2. Escribir **siempre** el código después del nombre, en `0x372` (3 B + NUL).  Escribir el nombre
   sin volver a poner el código es el fallo.
3. Comprobar el mundo antes de jugarlo:

```
python tools/fix_team_names.py --base <pesdb> --check
python tools/check_world.py --base <pesdb> --worldfile <fl26world.txt>
```

`fix_team_names.py` marca como rota una abreviatura vacía de NUL en sus 4 B, con caracteres no
imprimibles, o que sea la cola del propio nombre; la repara con el código del mismo id en un
`Team.bin` de referencia (`--ref`, se le pueden pasar varios) o, si no existe, con uno derivado del
nombre que no esté en uso.  No toca nada más de la fila.

`check_world.py` da **error** en los mismos dos casos, así que un mundo que pase la comprobación no
puede provocar esta caída.

## Resultado en `_FL26MyWorld` (2026-11-01)

- 65 filas rotas (42 «Other European Leagues Club NN», 23 «Other Clubs (Africa) Club NN») más 46
  con la cola de dos dígitos del nombre (`'01'`, `'36'`…), reparadas con los códigos del backup
  (`O61`…) y de `_FL26All`.
- `check_world`: 3404 equipos, **0 errores** (6 avisos preexistentes).
- Antes: 4/5 caídas a los 28 s. Después: 0/10 caídas con esa firma.  Queda ~1/5 de la inestabilidad
  de base del propio juego (`c0000005` en direcciones distintas: `0x195849c`, `0x118074f5`…), que
  también aparece **sin Sider** y sin mundo.
