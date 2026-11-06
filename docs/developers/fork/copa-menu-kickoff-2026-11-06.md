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
