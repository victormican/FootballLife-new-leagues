# El cargador de sesión de Copa y por qué la 11ª no carga (2026-11-08)

Continuación de `copa-plaza-custom-2026-11-08.md`. Aquí queda localizado el punto exacto que
decide si una copa de Kick Off recibe fase y sorteo.

## Lo medido

- **Africa Cup** (copa del juego, funciona): al entrar, `mode=2` y la tabla de sesión
  (`block+0xc12e9c`, cuenta en `+0xd0bcf4`) queda con **1 registro**: `key=46, cid=36,
  estado=3`.
- **Nuestra 11ª** (cid 131, regulación 200): `mode=2` y la tabla queda **vacía** (cuenta 0).
- El objeto del menú tiene **dos vectores de 11** (`+0x90` visible y `+0xb8` copia), ambos con
  la 131; la lista interna que usa el cargador sale de otro vector (heap `0x6660c790`) con los
  **10 cids fijos**.
- El recuento de la tabla (`0x1414bc0a0`) lo llama **`0x1412671fa`**, dentro del **tick del
  modo** que empieza en `0x141267040`.

## El tick del modo

`0x141267040`:

```
call owner(); block = owner[0x48]
0x1414bc680(block, 1)
0x141264880(...); 0x1412687a0(...)
obj = [0x1435ee48]                 ; global (rip+0x2497c3d en 0x141267104)
switch (obj->0x78) {
  case 7:  0x14126be60(); 0x141269380(); 0x14126f000(); break;
  case 8:  0x14126e970(); 0x141269380(); 0x14126ff30(); break;
  case 9/10: ...; break;
  default: obj->0x2c = 1; ...;
}
if (!0x1415879f0(obj + 0x18)) {
    0x1414bc0a0(block);            ; recount: la tabla ya se llenó
    ...
}
```

Los `case 7/8/9/10` son las ramas que **cargan la copa** según el estado del modo. La copa
nuestra no llega a la rama que llena la tabla: por eso `count=0`.

## Siguiente paso (si se retoma)

1. Registrar `[obj+0x78]` en `0x141267104` al entrar a **Africa Cup** y a la 11ª (basta un
   `lfile` desde el DLL o una lectura de memoria con `tools/fl26inspect.py`).
2. Ver qué valor pone la copa buena y cuál la nuestra; forzar el bueno para la nuestra en el
   DLL (escribir `[obj+0x78]`) o llamar a la rama que llena la tabla.
3. El global `0x1435ee48` es `rip+0x2497c3d` en `0x141267104`; en reposo puede estar sin
   inicializar (se leyó basura una vez), así que hay que leerlo durante el tick.

## Intento de registrar el estado (descartado)

Se probó un segundo desvío en `0x141267104` para guardar `[obj+0x78]` en cada tick. **Crasheaba
al arrancar** (antes de construir el menú): el global `0x1435ee48` no siempre contiene un
puntero válido cuando el tick pasa por ahí, y el cave lo desreferenciaba a ciegas. Se quitó.
El estado hay que leerlo en un punto donde el objeto ya es válido (p. ej. el `r15` del tick en
la llamada al recuento) o desde `tools/fl26inspect.py` durante la entrada, no repitiendo la
desreferencia del global.

## Lectura del estado: descartada

Se corrigió la dirección del global (`0x1436fed48`, no `0x1435ee48`) y se leyó `[rcx+0x78]` en
`0x141267104` durante las tres entradas. Los valores no son un estado de copa
(`2009036240`, `67`, `11162048`): ese tick es un **recuento periódico**, no el cargador de la
sesión de Copa, y `+0x78` no es el campo que ramifica. El recuento capturado
(`0x1412671fa`) tampoco era el del llenado de la tabla de sesión.

Conclusión: el cargador real no es este tick. Para encontrarlo hace falta un **watchpoint de
escritura** sobre la tabla de sesión al entrar a una copa que funciona (CE o Frida estable),
no más lecturas estáticas.

## Herramienta

`tools/fl26inspect.py <pid>`: lee sin Frida (solo `ReadProcessMemory`, requiere elevación):
`owner` en `base+0x3705e10`, `block = owner+0x48`, `mode` en `block+0x183789c`, cuenta en
`block+0xd0bcf4` y los registros de la tabla que sean de la copa (200/1071/46/131).
