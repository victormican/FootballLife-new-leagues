# Ghidra 12.1.4 + GhidraMCP en este equipo (2026-11-08)

Instalación de la vía libre de Ghidra para descompilar el exe del juego, ya que IDA Pro
no está instalado y el MCP de IDA no admite IDA Free.

## Instalado

- **Ghidra 12.1.4** (`ghidra_12.1.4_PUBLIC_20260921.zip`) en `D:\ghidra_12.1.4_PUBLIC`.
  Java 21 (Temurin) ya estaba.
- **GhidraMCP 2.0**:
  - Extensión en `D:\ghidra_12.1.4_PUBLIC\Ghidra\Extensions\GhidraMCP` (jar en `lib/`).
  - Servidor Python en un venv con PyGhidra:
    `C:\Users\viarm\.local\share\ghidra-mcp-venv\Scripts\ghidra-mcp.exe`
    (el `uv tool install` global choca con el proceso que lanza opencode; por eso el venv).
- **PE recortado** `D:\downloads\FL26-slices.exe` (465 KB), generado con
  `tools/mk_slices.py`: mismas direcciones que el exe real (base `0x140000000`), solo las
  regiones de menú, resolvedores, cargador de sesión, sorteo y fechas. Ghidra lo analiza en
  menos de un minuto.
- **Proyecto** `D:\ghidra_projects\FL26slices` (creado por el modo headless).

## Config de opencode

`C:\Users\viarm\.config\opencode\opencode.json`, servidor `ghidra`:

```
ghidra-mcp.exe --headless --binary D:\downloads\FL26-slices.exe
  --project D:\ghidra_projects --project-name FL26slices
  --ghidra-install-dir D:\ghidra_12.1.4_PUBLIC
  --extension-jar ...\GhidraMCP\lib\GhidraMCP.jar --transport stdio
```

Al arrancar opencode, el servidor importa/abre el proyecto y sirve las 28 herramientas
(`get_program_info`, `decompile_function_by_address`, `get_function_by_address`,
`disassemble_function`, `get_xrefs_to`, `read_memory`…).

## Problemas vistos

- **Dos instancias** del servidor lanzadas por opencode peleándose por el mismo proyecto:
  una crea `FL26slices.lock` y la otra falla con `Project is locked`. Se matan los dos
  procesos y se borran `D:\ghidra_projects\FL26slices.lock*` antes de reiniciar.
- La primera config apuntaba a la GUI (`--ghidra-server http://127.0.0.1:8080/`), que exige
  abrir Ghidra a mano; el modo headless no necesita GUI.

## Por qué no resuelve solo la copa nueva

Ghidra descompila el cargador y el menú, pero el bloqueo es de **ejecución**: la lista de
Copa son 10 cids fijos y el cargador de sesión solo rellena la tabla para esas plazas. Para
una plaza 11 hay que ver **qué función escribe** la tabla de sesión al entrar a una copa del
juego (watchpoint de escritura con Frida/CE) y replicarlo; Ghidra sirve para leer y parchear
esa función después.

## Uso

Con el servidor arriba, `get_program_info` debe devolver `FL26-slices.exe`. Las direcciones
son las del exe real, p. ej.:

- `0x140b1c990` constructor de MenuModeCupSelect.
- `0x140b1cda0` resolvedor por competición.
- `0x140c6bb50` init base de la lista.
- `0x1414b6a60` `owner()`; `0x1414bc860` `findrec`; `0x1414bc0a0` recuento de la tabla.
- `0x14150af30` `phkind`; `0x14150d2b0` gate del sorteo.
- `0x14157f810` función de fechas.
