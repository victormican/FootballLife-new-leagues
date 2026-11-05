# "Información de la Liga": el censo es por byte bajo del cid

2026-11-06. P0.1 de `revision-completa-y-pendientes-2026-11-06.md`, medido y cerrado.

## Qué se preguntaba

El panel de la derecha de `Jugar > Liga > Nuevo` ("Información de la Liga", y el mismo listado que
usa Select Team) enseñaba clubes que no son de la competición: Serie A 20 pintaba 34, NIFL 10
pintaba 2 malteses, Danish 12 pintaba estonios, Yokary 8 pintaba 2 brasileños, la Copa
Sudamericana mezclaba clubes de medio continente. Había dos candidatas:

- (a) el censo de competiciones/entradas va por el **byte bajo** del cid y junta competiciones que
  lo comparten;
- (b) el panel lee el **array vivo de regulaciones** y el motor no limpia los huecos.

## Cómo se midió

Sin tocar el mundo ni el cableado:

1. `tools/livereg.py` (solo lectura, `ReadProcessMemory`) sobre el bloque de edición vivo.
2. Capturas del panel con las teclas de siempre (`Enter`/`Down`), una por competición.
3. Lectura de las tablas servidas (`_FL26MyWorld\common\etc\pesdb`) con `tools/pesdb.py` para
   saber qué entradas tiene cada cid y cuáles comparten byte bajo.

## Resultado del bloque vivo: no es el array

En esa pantalla el bloque de edición **no está cargado**:

```
pid 55100 dueno 0x4733fde0
bloque 0x7ff4e0050010
jugadores 0  equipos 0  entrenadores 0  regulaciones 65535
```

El array de regulaciones (`bloque + 0xc131b0`, paso 0x314) sigue con datos de arranque, no con las
711 regulaciones del mundo. El panel, por tanto, **no lee ese array**: lee las tablas pesdb que
sirve `livecpk`. La hipótesis (b) queda descartada para esta pantalla.

La sonda Lua `fl26diag` tampoco sirve aquí: al llamar a funciones del motor
(`0x1414bb000`, `0x1414cb030`) desde el callback `livecpk_make_key`, con el bloque a medio cargar,
**cerró el juego**. Se revirtió y se quedó apagada en `sider.ini`.

## Resultado en pantalla: las entradas ajenas van pegadas

**Copa Sudamericana** (cid 513, 32 entradas). El panel pinta 34 filas, en este orden:

| # | fila | origen |
|---|---|---|
| 1 | AF Elbasani | cid **257**, plaza 1 |
| 2 | FC Dinamo City | cid **257**, plaza 2 |
| 3..34 | los 32 clubes de la copa, en el orden de sus plazas 1..32 | cid **513** |

**Yokary Liga** (cid 359, 8 entradas). El panel pinta 10 filas:

| # | fila | origen |
|---|---|---|
| 1..8 | Yokary Liga Club 01..08 | cid **359**, plazas 1..8 |
| 9 | Clube de Regatas Brasil | cid **615**, plaza 1 |
| 10 | Centro Sportivo Alagoano | cid **615**, plaza 2 |

Capturas: `C:\Users\viarm\AppData\Local\Temp\opencode\shots\d7-panel1.png` (Sudamericana) y
`d8-pos9.png` (Yokary).

## El mismo patrón en las otras dos que se citaban

Salen de las tablas, sin necesidad de pantalla:

| liga | cid | entradas propias | cid que comparte byte bajo | entradas ajenas |
|---|---|---|---|---|
| NIFL Premiership | 63 | 10 (Linfield, Glentoran, ...) | **319** | 2 (Floriana FC, Birkirkara FC) |
| Danish 1. Division | 327 | 12 | **839** | 8 (Levadia Tallinn, Nomme Kalju, Paide, ...) |
| Yokary Liga | 359 | 8 | **615** | 2 (CRB, CSA) |
| Copa Sudamericana | 513 | 32 | **257** | 2 (AF Elbasani, FC Dinamo City) |

## Mecanismo

El censo (`0x1414f1480`) construye las dos colecciones que luego recorre el listado:

- la fila de competición se lee en `0x1414f1500` con `movzx ecx, byte ptr [rdi+5]`: **el cid como
  byte**;
- cada entrada se compara por su byte en `+8`, y su clave de orden es
  `cid << 6 | (plaza - 1)`, ya a 16 bits porque `fl26cid16.lua` tiene `pack = true`.

Por eso el panel enseña **todas** las entradas cuyo byte bajo coincide con el de la competición
seleccionada, concatenadas en el orden de la clave: las de cid menor salen antes (257 antes de
513) y las de cid mayor después (615 detrás de 359). No hay clubes "de más" ni en las entradas ni
en el array: es el censo el que junta competiciones.

## Lo que esto cambia del plan

- P0.2 es exactamente la prueba que toca: `cid = true` en `sider/experimental/fl26cid16.lua` para
  que ese censo lea el cid de 16 bits. La tabla plana (`map = true`, 2026-11-04) ya resuelve las
  búsquedas del censo; lo que queda en byte es la lectura de la fila de competición y el `cmp`
  del mapa, que se deja quieto (`cmp = false`, el intento anterior cascó).
- No hace falta tocar `clubs=` ni el DLL para esta pantalla: el panel no pregunta al motor por la
  lista viva, y las plazas servidas no influyen aquí.
- La aceptación de P0 sigue siendo la misma: Serie A 20, Danish 12, NIFL 10, Yokary 8, Copa
  BetPlay solo sus clubes; se comprobará en la misma pantalla tras el A/B.

## Herramientas

- `tools/livereg.py`: volcado de solo lectura del bloque vivo (estado, array de regulaciones y
  clubes por handle). Corre elevado, como el juego.
- `sider/experimental/fl26diag.lua`: se queda como estaba (sonda F9 del array); **no** llamar a
  funciones del motor desde `livecpk_make_key` con el bloque sin cargar.
