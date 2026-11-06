# Copa propia en Kick Off > Copa: listada, pero no abre (2026-11-06)

Nota final de la tarde. La copa del constructor (`ccup 317`, competicion 131, regulacion 317,
16 clubes, eliminatoria) **aparece en la lista** de Kick Off > Copa, pero **al elegirla el juego
se cierra**. Probado con la fila de parametros en tres slots distintos; los tres cierran, y el
punto de cierre dice mucho.

## Lo medido

| fila de parametros | que pasa |
|---|---|
| slot **123** (centinela "sin slot") | la lista se construye (`CUPAFTER list=9`, item 8 `cid=131`) y el juego se cierra **al elegir la copa**: salto a `0x161efa600` (direccion fuera de modulo: llamada por un puntero nulo) |
| slot **22** (real, libre) | se cierra **durante la construccion de la lista**, antes de `CUPAFTER`: mismo `0xc0000005` en `0x161efa600` |
| slot **128** (rango de `fl26slots750`) | la lista ni se construye: `0xc0000005` en `0x141ae48ae` |

`0x141ae48ae` es, desensamblado, el interior de un recorrido de arbol (`cmp byte ptr [r10+0x19],0`
con `r10 = [[global]+8]`), es decir una busqueda en un `std::map<std::wstring, ...>` del propio
juego con un nodo nulo: el mapa que resuelve la competicion del slot.

`CUPRES cid=131 group=65535 rec=0 vols: k1=65535 k2=65535 k3=317 k4..k6=65535` dice que el
resolutor del juego da la regulacion de la copa **en `kind 3`** (fase eliminatoria) y no tiene
fase de grupos (normal: la Copa Chile da igual, `k2=65535`). O sea: la fila de parametros no es
lo que falta; lo que falta es **el objeto por slot** que el juego construye al arrancar para las
competiciones suyas.

## Conclusion

Kick Off > Copa no abre competiciones nuevas. La pantalla resuelve cada entrada por su cid contra
las estructuras que el juego crea en el arranque para sus copas; una copa nuestra, por muy
completa que este en `Competition`/`CompetitionRegulation`/`CompetitionEntry`, no las tiene, y el
menu cae al resolverla.

- La fila de parametros sigue en el **slot 123** (es lo unico que deja que la lista se construya).
- `ccup`/`showcup` dejan la copa **listada**; abrirla necesita el objeto del slot, que no
  escribimos nosotros.
- En temporada (Liga/Master League) la copa del mundo **si** se juega: ahi el objeto lo construye
  `fl26swiss.dll` con el plan del mundo (`ccup`, `dates`, sorteo).

## Caminos que quedan

1. **Copas de nuestro mundo en temporada** (funciona hoy): la copa nacional de la liga de prueba,
   con su tabla, calendario y partido.
2. **Copa de la casa del juego** (cid 37, *Custom Cup*): existe, es jugable y es la via del juego
   para "montar una copa"; no es una copa de nuestro mundo.
3. **Abrir el menu a un cid nuevo**: hay que construir la estructura por slot que el juego arma al
   arrancar (o enganchar su resolutor y devolver un objeto nuestro). Es trabajo de RE dentro de
   `fl26swiss.dll`, no de datos.

## Estado dejado

- `fl26comptab.lua`: filas de copa en el 123, con la maquinaria para compartir un slot real
  (`CUPROWS`) ya escrita y probada (no aborta la tabla con 286 copas), por si se retoma la via 3.
- El mundo `_FL26CupTest` queda con `ccup 317` y `showcup 131`: la copa se ve en la lista.
- `Competition.bin` de la copa devuelto a lo que escribio el constructor (area 29, flags 0x02).

---

# Sesión 2 (tarde): el cierre no era el menú, era un `call` a memoria libre

## El fallo del stub de `fl26cupgrow`

`fl26cupgrow.lua` envuelve el slot de la vtable y **parchea el destructor** del menú
(`0x140b1c810`) con un stub de 61 bytes que anula la lista y salta a `0x140b1c824`. El parche
estaba mal:

```lua
-- antes (mal)
d = d:sub(1, 56) .. u32(DTOR_NEXT - (dstub + 60)) .. d:sub(61)
-- despues (bien)
d = d:sub(1, 57) .. u32(DTOR_NEXT - (dstub + 61)) .. d:sub(62)
```

Con `sub(1,56)` se perdía el opcode `e9` del `jmp`: en `dstub+0x38` quedaban los bytes
`e8 c3 a1 df 00`, es decir **`call 0x161efa600`** — memoria libre. Ese era el
`CRASH #1 code c0000005 rip 161efa600 ... info 8` (fallo de *ejecución*) y el cierre exacto al
elegir la copa. Verificado con capstone: el stub corregido hace `jmp 0x140b1c824`.

## El volcado que lo demostró

`tools/native/fl26swiss.c` lleva desde hoy un grabador de excepciones propio
(`AddVectoredExceptionHandler`, escribe `fl26swiss-crash.log` junto al DLL y al log del DLL):

```
CRASH #1 code c0000005 rip 161efa600 (base+21efa600) touched 161efa600 info 8
  rip page state 10000 protect 1 type 0     -> MEM_FREE
  rax 142692c40 (vtable MenuModeCupSelect)   rcx/rdi = objeto del menu
  rsp+00 16110043d                           -> retorno dentro del stub de cupgrow
```

Sin ese volcado no se veía que el `call` salía de nuestro propio stub.

## Trazas del handler (`CUPTRACE`)

Con el stub arreglado, el handler **completa**:

```
CUPTRACE enter self=... +90=... +98=... +a0=... +88=... +00=142692C40
CUPTRACE regcid_fix done
CUPTRACE filter done gone=2 items=8
CUPTRACE add begin have=8 room=1024 ncupcid=1
CUPTRACE add end added=1 short=0 items=9
CUPTRACE init call begin
CUPTRACE init call returned 1
```

- La lista del menú **no crece**: `cap - begin = 0x3000` = 1024 entradas. `room=1024`, así que
  `fl_pool_alloc` no llega a usarse. El item se escribe en su sitio (`begin+96`).
- `init` (0x140b1c990) devuelve **1** con nuestros 9 items y la lista queda
  `33,5,8,27,36,34,35,37,131`.
- El fallo de `0x141ae48ae` que apareció después es un recorrido de `std::map<wstring,...>` con
  nodo nulo (`[[global]+8]=0x7`). Ese global (`0x1437ce9c8`) es el mapa de **rutas de procesos**
  que el juego consulta en un hilo de fondo (`conhost.exe`, `explorer.exe`, `FL_2026.exe`...), no
  el de la copa: el volcado se produce cuando el proceso ya está muriendo.

## El resolver del juego, medido desde dentro (`tools/native/frida/cid_probe.js`)

`phkind(cid, kind)` (RVA `0x150af30`), `owner()` (`0x14b6a60`) y `findrec` (`0x14bc860`) son las
mismas funciones que usa el filtro del handler:

| cid | k1 | k2 (grupos) | k3 (eliminatoria) | registro |
|---|---|---|---|---|
| 33 | 65535 | 41 | 42 | si |
| 5 | 65535 | 9 | 10 | si |
| 8 | 65535 | 15 | 16 | si |
| 27 | 65535 | 34 | 35 | si |
| 36 | 65535 | **65535** | 46 | **no** |
| 34 | 65535 | 104 | 43 | si |
| 35 | 65535 | 44 | 45 | si |
| 37 | 65535 | 47 | 48 | si |
| **131** | 65535 | **65535** | **317** | **no** |

Nuestra copa tiene **la misma forma que la 36** (el Mundial de Clubes): sin fase de grupos y con
la regulación en `kind 3`. O sea: el resolutor no la rechaza por rara; la 36 se lista igual.

## Herramientas nuevas

- `tools/native/frida/cupmenu_probe.js` — INIT, items, excepciones, y `rpc.exports.setcups()` para
  añadir o no la copa sin reiniciar.
- `tools/native/frida/cupmenu_rea.js` — lo mismo más los pasos del modo copa (`0x140e43450` es el
  "enter" del menú, que llama al slot `+0xd8` y sigue si devuelve 1) y hooks de
  `ExitProcess`/`TerminateProcess`/`RtlExitUserProcess`/`abort` con backtrace.
- `tools/native/frida/cid_probe.js` — la tabla de arriba.
- `tools/native/frida/run_probe.cjs` — engancha sin límite de 60 s (REA corta a 60 s por llamada).

## Frida, desbloqueado

El fallo `capability_unavailable: Could not locate the bindings file` era el binding nativo de
`frida` sin compilar en la caché de npx. Se arregla con:

```
cd %LOCALAPPDATA%\npm-cache\_npx\ad9a3fdbcad992c6\node_modules\frida
node ..\prebuild-install\bin.js      # baja frida_binding.node (135 MB)
```

El servidor MCP que ya estaba en marcha cachea el `import("frida")` fallido (mapa de módulos ESM),
así que **hay que reiniciar OpenCode** para que REA lo vea; el CLI (`rea list-frida-devices`,
`rea instrument-with-frida attach <pid> --script-file ...`) funciona ya con el binding nuevo.

## Lo que queda abierto

- Con el stub corregido, entrar en Kick Off > Copa **devuelve al menú principal** (pantalla de
  carga y vuelta) en las pruebas de esta sesión; el driver de teclas no es fiable (el juego tarda
  ~2 min desde que aparece la ventana hasta que acepta input, y las pulsaciones caían en el título),
  así que ese extremo hay que confirmarlo a mano antes de sacar conclusiones.
- El camino de la vía 3 sigue siendo el mismo: enganchar el resolutor y devolver un objeto propio
  para el cid nuevo, o clonar el objeto de la 36 (misma forma) al arrancar.

## El id de la regulacion: por que no arranca (2026-11-06, tarde)

Los equipos **no** son el problema. Leidos en caliente con `rec_probe.js` (mismas funciones que usa
el filtro del handler: `owner()` 0x14b6a60, `findrec` 0x14bc860) el campo `+0x30c & 0x7f` da el
numero de clubes:

| regulacion | copa | clubes |
|---|---|---|
| 46 | 36 (Mundial de Clubes) | 14 |
| 42 | 33 | 16 |
| 48 | 37 | 16 |
| 41 | 33 (grupos) | 24 |
| 47 | 37 (grupos) | 32 |
| **317** | **131 (la nuestra)** | **16** |

La nuestra tiene 16 clubes, igual que las del juego. El problema es **el id**:

- `tools/datecave.py` genera el stub de fechas con `cmp eax, 256 ; jae big`: los ids **256 o
  mayores** caen en `big`, que da el **calendario de liga** (38 fechas), nunca el de copa.
- `tools/patchset.py --cup-keys` solo admite **1..255** (`datecave` aborta con "regulation id %d is
  outside the stub's table (1..255)"; `cup_patches` acepta 1..175 para el byte de caso).
- Nuestra copa es la **regulacion 317**: por definicion no puede llevar calendario de copa. En
  temporada el DLL le pasa las fechas a mano (`dates 317 like=122`), pero en Kick Off ese
  hand-over no corre.

Arreglo: nacer con una regulacion **<= 255** (banda libre 176..255; la doc ya probo la 200 con el
byte `0x10`) y regenerar `fl26caps` con `--cup-keys 200`, o clonar una copa nativa (la 36), que es
lo unico que hoy llega a iniciar partido.
