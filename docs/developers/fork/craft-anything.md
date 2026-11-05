# Craft Anything 0.3.0 como motor de RE para FL_2026

Instalado el 2026-11-04 en `C:\Users\viarm\craft-anything\app\craft-anything-0.3.0-windows-x64-portable\`
(portable, 62,7 MB, SHA-256 verificado contra `SHA256SUMS.txt` del release `v0.3.0`).

Motivo: REA no sirve en esta máquina (Frida sin bindings, Rizin del proveedor bloqueado, `pdc`/`pdg`
de Cutter sin sleigh). Craft Anything trae motor propio en Rust (desensamblador y descompilador
propios), 301 herramientas, CLI y servidor MCP, y **sesiones de depuración vivas** (Rizin/GDB/Frida)
que es justo lo que nos faltaba.

## Qué hay conectado

| Pieza | Valor |
|---|---|
| CLI | `craft-anything-cli.exe` (herramienta por subcomando) |
| Servidor MCP | ya en `~/.config/opencode/opencode.json` como servidor `craft` |
| Modo | `--deep --allow-run`, proyecto `C:\Users\viarm\craft-anything\fl26.cany` |
| Ghidra | `C:/Users/viarm/ghidra_11.3.2_PUBLIC` (settings `engines.ghidra.install_dir` + `java_home`) |
| Rizin | `C:/Users/viarm/Cutter-v2.5.0/Cutter-v2.5.0-Windows-x86_64/rizin.exe` (`engines.tools.rizin`) |

Las herramientas se exponen por conjuntos: al arrancar solo los 37 de Essentials; el resto se
activa con `enable_toolset` (`native`, `runtime`, `frida`, `formats`, `setup`…).

## Comprobado en esta máquina

- `doctor` en verde, `capabilities` en `analysis_mode: deep`, Ghidra y Rizin detectados.
- `core_target_open` sobre `D:\SP Football Life 2026 - copia - copia\FL_2026.exe`
  (sha256 `9ee0c30651e5e3c37e3d308fb8224f5fea135cd8e929dee2cddca6e041836281`, 458.910.720 B).
- **Depurador vivo**: `native_rizin_session_begin` arranca un programa parado, `native_rizin_session_command_run`
  ejecuta `dr`, `dm`, `pd`, `db`, `dc`…, `native_rizin_session_end` lo cierra. Probado con
  `notepad.exe`: sesión creada, `.text` leída, cierre limpio. También acepta `pid` para **adjuntarse**.
- `FL_2026.exe` **no pide elevación** (sin `requireAdministrator` en el manifiesto), así que adjuntarse
  no debería necesitar permisos de administrador.

## Límites encontrados

- Las herramientas de barrido de bytes (`native_bytes_find`) **rechazan ficheros > 256 MB**;
  `FL_2026.exe` son 458 MB. Para escanear hay que pasar un recorte (por ejemplo la sección `.text`
  extraída como PE aparte) o usar Rizin directamente, que no tiene ese tope.
- El análisis propio ("builtin") **no reconoce** `0x14150af30` (`phkind`) como función: dice que puede
  ser código alcanzado solo por tabla de punteros. Para estático hay que dejar que use Ghidra
  (`--deep` + Ghidra configurado), que importa el PE entero en su propio proyecto (lento la primera vez).
- Las sesiones de depuración y de Frida viven **en memoria del servidor MCP**, no del CLI suelto.

## Para qué lo usamos en el bloque de copas

El agujero que queda es de **memoria viva del juego**, no de estático: no sabemos dónde está el array
de `CompetitionRegulation` ni quién escribe el cid en `+0x80` del registro. Con Rizin:

```text
native_rizin_session_begin { pid: <pid de FL_2026> }          # adjuntar
native_rizin_session_command_run { command: "db 0x14150af30+base; dc" }
native_rizin_session_command_run { command: "dr; px 0x340 @ <registro>" }
```

y al abrir *Kick Off > Cup* se lee el registro real: id, cid de `+0x80`, tipo de `+0x84` y la base
del array (caminando `-0x314`), sin más sondas a ciegas en el DLL. También permite romper en la
función que pinta la fila para ver de dónde sale el nombre.

## Frida

`doctor` no encuentra Frida. Si hace falta instrumentación scriptada (más cómoda que Rizin para
leer memoria en bucles), instalar con `pip install frida frida-tools` y apuntar
`engines.tools.frida` a `frida.exe`.
