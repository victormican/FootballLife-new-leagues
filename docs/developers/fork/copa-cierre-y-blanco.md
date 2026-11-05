# Copa: del memcpy(0xd70) al free del buffer (2026-11-06)

## Lo que se arreglo

`fl26comptab.lua` daba a cada copa del mundo una fila en el **slot 123** ("none"). Con eso,
Jugar > Copa > Nuevo cerraba en `memcpy(dst, src=0x00000d70, 0x20)` (`0x1403fef5f`).

Cambiado `CUP_SLOT = 22` (un slot real de la lista de libres del propio modulo). El `memcpy`
desaparece: ahora la lista se construye.

## Lo que queda

El siguiente cierre es `0x3fd2b2` (pool free) al liberar **el buffer de la lista**. Nuestro
handler (`cupsel_handler`, en `fl26swiss.dll`) sustituye el vector del menu por:

- con `fl26cupgrow`: un anillo de `VirtualAlloc` (1024 items), y
- sin `fl26cupgrow`: el ensanche del DLL (tambien `VirtualAlloc` en el binario desplegado).

El destructor del modo Copa libera ese vector con `operator delete` (pool 0), y un bloque de
`VirtualAlloc` no es del pool: revienta al desenlazarlo del arbol rojo-negro.

Probado con `fl26cupgrow` **dentro y fuera**: mismo `0x3fd2b2`. El `fl26cupfree` tapa el free de
`+0x90` del destructor del menu, pero el del modo Copa va por otra ruta.

## Siguiente

El buffer tiene que venir del **mismo asignador que usa el vector** (`operator new` del juego),
o no sustituirlo y dejar que el vector crezca solo. Eso es recompilar `fl26swiss.dll` desde
`tools/native/fl26swiss.c` (el fuente usa `fl_pool_alloc` del pool 2, que es el del destructor
del menu, no el del modo Copa). Antes de desplegar hay que confirmar que el fuente genera un
binario equivalente al que corre (378.880 B).

## Automatizacion (para no molestar al usuario)

`tools/send_keys.ps1 <hwnd> enter down ...` elevado; capturas con `CopyFromScreen`.
Camino: titulo -> Jugar -> 6 abajo -> Copa -> Nuevo.
