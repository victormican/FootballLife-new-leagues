# Otros OFC y el techo de 250 slots (2026-11-06)

## Otros OFC

Creado con `tools/mk_otros_ofc.py`, copiando "Otros Concacaf" (cid 221, reg 250, type 8):

```
league 470 cid=382 region=25 country=166 conf=7 slot=248 tier=3 ... exhibition=1
       clubs=48 name=Otros OFC
```

48 clubes de las cuatro ligas OFC del mundo (New Zealand Northern, NZ Central, Super Ligue,
Fiji Premier). `fl26clubs` lo sirve en el slot **248** (`248<-470`): 20 slots servidos.

"Otros Concacaf" ya existía en el slot **247** (58 clubes, `247<-250`), con el mismo mecanismo
que un pool: la línea le dice a fl26clubs de qué regulación sale la lista.

```
check_world: 154 ligas, 137 slots 22..248, 286 ccup, 0 errores
```

## Slots a 500: por qué no

`mkslots.py` corta en 250 (`N must be 124..250`). Le quité el tope y generó
`fl26slots500.lua` (capacidad 159 por slot), pero **el juego se cae al arrancar**:
`0xc0000005` en `0x1a12d`, con escritura a `0x03712e43`.

Esa escritura viene de un **inmediato de 8 bits**: las comparaciones de cota del juego son
`cmp r32, imm8` (0..255). 250 entra (0xFA), **500 (0x1F4) no**: el generador escribe el byte
truncado (0xF4 = 244) y el flujo se corrompe.

Para 500 de verdad hay que reescribir esas comparaciones a 32 bits (cuevas de código), no basta
regenerar el módulo. Con 250: **111 slots libres** (137 usados).
