# Recursos de ingenieria inversa

## REA (oficial)

| que | donde |
|---|---|
| Repositorio oficial | <https://github.com/morluto/rea> |
| Sitio web oficial | <https://rea.tools> |
| Instalacion y configuracion de agentes | <https://github.com/morluto/rea/blob/main/docs/installation.md> |
| Primera investigacion | <https://rea.tools/first-investigation> |
| Guias | <https://rea.tools/guides> |
| Prompts guiados de MCP | <https://github.com/morluto/rea/blob/main/docs/mcp-prompts.md> |

Instalacion:

```
npx rea-agents@latest setup
```

## Repositorios de GitHub

| repo | para que |
|---|---|
| <https://github.com/morluto/rea> | REA: un MCP para RE de binarios, apps y runtime |
| <https://github.com/awesome-reverse-engineering> | lista curada de material de RE |
| <https://github.com/sqwu/rea-gems> | gems (recetas) para REA |
| <https://github.com/alexgaoth/awesome-reverse-engineered> |ejemplos de binarios analizados |
| <https://github.com/nationalsecurityagency/ghidra> | Ghidra: descompilador (analisis estatico del exe) |
| <https://github.com/skylot/jadx> | JADX: dex a Java (APK) |
| <https://github.com/frida/frida> | Frida: instrumentacion en runtime (procesos y scripts) |
| <https://github.com/icsharpcode/ILSpy> | ILSpy: .NET a C# |
| <https://github.com/x64dbg/x64dbg> | x64dbg: depurador de Windows |

## Como se usa en este fork

Los muros del mundo (jugadores 123.825, clubes 750, equipos 4.800, lista de copas 13 entradas,
48 clubes por regulacion, 250 slots) son **constantes en el codigo del ejecutable**: se localiza
la funcion que las usa con el flujo de REA (instrucciones -> caller -> constantes -> C) y se
escribe el parche en una DLL propia (`tools/native/`), sin tocar el ejecutable.

Un volcado de memoria a mano no es un informe: la pregunta se formula como pregunta de RE y se
responde con evidencia.
