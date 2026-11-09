# La copa jugable: la plaza Custom Cup (2026-11-08)

Resumen de lo que se probó y de lo que quedó funcionando. El objetivo era una copa
propia (competición 131, 16 clubes) que sortease, fechara y se jugase en Kick Off > Copa.
Lo que funciona hoy: **la copa ocupa la plaza que el juego llama Custom Cup** (cid 37,
regulación 1071) y hace todo el flujo. El usuario lo confirmó en juego: sorteo, cuadro y
partidos.

## 1. Lo que el menú hace de verdad

Medido en vivo (Frida) sobre `FL_2026.exe`:

- `MenuModeCupSelect` recibe una lista de **10 ítems de 12 bytes** con los cids
  `[33, 2, 8, 3, 27, 36, 34, 35, 37, 5]`. Es una lista **fija del juego**, no sale de
  `Competition.bin` ni se puede ampliar cambiando datos.
- El constructor base (`0x140c6bb50`) copia esos 10 ítems a un vector temporal y llama a
  `0x140eae260`, que produce la **lista de claves de regulación**:
  `[1027, 6, 1039, 10, 1058, 1065, 1128, 1068, 46, 1071]`.
- El decorador (`0x140b1cc60` → `0x140b1cda0`) resuelve cada cid con `phkind(cid, 2/3)` y
  rellena los campos del ítem (clubes, tiene grupos, formato). Nuestro ítem se decoró bien:
  `cid 131 → 16 clubes, eliminatoria`.
- Al **entrar** a una copa el juego pasa a `mode=2` y **vacía la tabla de sesión**
  (`block+0xc12e9c`, cuenta en `+0xd0bcf4`). Para África Cup la rellena (2 registros); para
  un ítem 11 nuestro se queda **a 0**: el paso selección→sesión está cableado a las 10 cids
  fijas. Ahí se corta la plaza nueva.
- El cargador de sesión termina en el recuento `0x1414bc0a0`; sus llamadores son el punto
  donde habría que enganchar un ítem 11.

Corolario: **la lista sí acepta un ítem extra** (se probó añadiendo cid 131 al vector
temporal: `KEYLIST [...46,2095,200]`, y el resolvedor encontró la 200), pero el cargador de
sesión no lo usa. Una plaza completamente nueva exige parchear ese cargador, no los datos.

## 2. La plaza que sí funciona: Custom Cup (1071)

Custom Cup es una de las 10 cids fijas (la 37) y su regulación es la **1071**. Si se pone
ahí la copa propia, el juego la trata como una copa suya y hace todo el flujo.

Receta aplicada en `_FL26W1`:

1. `CompetitionRegulation.bin`: la fila de la regulación **1071** se sustituye por una copia
   de la fila de la 200 (la copa propia): `cid = 131`, `type = 3` (eliminatoria),
   `group = 0xff`, `teams = 16`, nombre `Copa Nueva`. El id de regulación se deja en **1071**
   para que siga siendo la plaza del juego.
2. `CompetitionEntry.bin`: las 16 entradas de la competición **131** (ya las pone el
   constructor del mundo).
3. Fechas: la función de fechas del juego (`0x14157f810`) solo fecha regulaciones **2..175**;
   la 1071 devuelve 0. `fl26cup.dll` instala un desvío en `0x14157f81e`: si la regulación es
   **1071**, llama a la función original con **122** (copa de 16, 8 fechas). Es un salto
   relativo a una cueva asignada **dentro de ±2 GB del exe** (una cueva lejana desborda el
   rel32 y crashea).
4. `fl26cup.lua` carga el DLL; no añade nada a la lista (el `showcup` del mundo está
   desactivado). Solo aporta el desvío de fechas.

Con esto: la copa aparece en la plaza Custom Cup, sortea, muestra el cuadro y juega.

## 3. El nombre

La etiqueta de la plaza no sale de `Competition.bin` (renombrar el código de la cid 37 a
`COPA_NUEVA` no cambió el rótulo) ni de una cadena UTF-16 simple en memoria (se buscó y no
está). Es un texto localizado por plaza; queda pendiente localizar su tabla/ID si se quiere
que diga "Copa Nueva" en la lista.

## 4. Herramientas

- `tools/native/fl26cup.c` — DLL mínima: desvío de fechas 1071→122 (y, opcionalmente, el
  gancho del constructor de Copa, hoy sin uso).
- `sider/experimental/fl26cup.lua` — cargador mínimo.
- `tools/native/frida/` — sondas usadas: `regscan`, `regscan2`, `regwatch`, `codefull`,
  `phwatch`, `abtrace`, `ab2`, `appendcup`, `finaltrace`, `slotlinks`, `dateprobe`,
  `keysrc`, `findlist`, `nameprobe`, `findtext`.

## 5. Reproducir

```
# mundo con la fila 1071 = copa propia (cid 131, 16 clubes, eliminatoria)
# fl26world.txt: sin showcup
# sider.ini: lua.module = "fl26cup.lua"
# SiderAddons/modules: fl26cup.dll + fl26cup.lua
```

Entrar a Kick Off > Copa > Custom Cup: debe sortear y jugar con los 16 clubes.
