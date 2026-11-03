# Divisiones de relleno: seis ligas nuevas con clubes genéricos (2026-11-03)

`tools/make_divisions.py` crea varias ligas de una vez reutilizando los clubes genéricos que ya
existen (no crea equipos ni jugadores), y borra las ligas de relleno de donde salen.

## Lo que hace

1. Coge todos los clubes de las ligas donantes (`DELETE_REGS`) y los reparte entre las ligas de
   `SPEC`.
2. Borra las donantes: su fila de `Competition.bin`, su regulación y todas sus entradas, y su
   línea del world file.
3. Para cada liga nueva: renombra sus clubes `<nombre> NN` (respetando los 24 B del slot 10 antes
   del código de `+0x372`), les pone el país en `+0x46` y crea competición + regulación + entradas
   con `mkleague.add_league`.
4. Escribe el world file con una línea por liga (`slot=-1`, así `fl26comptab` le da slot libre).

**Los cids son un byte.** `Competition.bin` guarda el id de competición en un solo byte, así que
solo hay 255; el mundo los tenía agotados y hubo que borrar cinco ligas de relleno para liberar
`95, 96, 98, 221, 254`. Antes de crear, el tool busca los ids libres y falla si no hay
suficientes.

**tier 4 no vale**: el juego lo lee como 0 sin `sider/experimental/fl26rank.lua`. Las ligas se
crean con tier 2 o 3.

## Las seis de 2026-11-03

| liga | cid | reg | país | tier | clubes |
|---|---|---|---|---|---|
| Primera B Metropolitana | 95 | 8451 | Argentina (144) | 3 | 22 |
| Federal A | 96 | 8452 | Argentina (144) | 3 | 38 |
| Primera C | 98 | 8453 | Argentina (144) | 3 | 28 |
| Torneo Federal | 99 | 8454 | Argentina (144) | 3 | 30 |
| Torneo Federal Brasil | 221 | 8455 | Brasil (146) | 3 | 30 |
| Segunda División Bolivia | 254 | 8456 | Bolivia (145) | 2 | 48 |

Los clubes son genéricos renombrados (`Primera B Metropolitana 01`…); se les puede poner el
nombre real después sin tocar nada más.

## «Otros Europa»

La liga `Other European Leagues` (cid 98, reg 364) duplicaba el grupo del juego: se borró, así que
el slot 69 vuelve a la lista del propio juego. Con ella cayeron `Other` (96), `Other Latin American
Teams` (95), `Otros Concacaf` (221) y `Other Clubs (Asia)` (254); `fl26clubs` pasó de servir 8
slots a 5 (`80<-76 72<-178 75<-181 77<-182 76<-196`).

Quedan **44 clubes genéricos sin competición** (240 donados, 196 usados): no rompen nada, no
aparecen en ninguna liga.

## Comprobado

`check_world` 0 errores, 0 abreviaturas rotas (3422 filas), 2 arranques con `FL 2026 start.exe`
vivos 55 s.
