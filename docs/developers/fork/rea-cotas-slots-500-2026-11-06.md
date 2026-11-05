# REA de las cotas de slots: por que 500 no es solo un inmediato (2026-11-06)

## Lo medido

`mkslots500.lua` tiene 35 parches. Los sitios de cota son, todos, **`cmp r32, imm8` con 123**:

```
0x1414d6290  cmp edx, 0x7b      (get)
0x1414d62c0  cmp edx, 0x7b      (count)
0x1414d6330  cmp edx, 0x7b      (set)
0x1414d6360  cmp edx, 0x7b      (setcount)
0x1414cb0f0  cmp r8d, 0x7b      (cid2slot)
0x1414f754e  cmp esi, 0x7b      (dos sitios)
0x1414f77da  cmp r14d, 0x7b
0x1412688e0  cmp eax, 0x7b
0x1412fac89  cmp ebp, 0x7b
0x1412fb24e  cmp r12d, 0x7b
0x1412fb6a5  cmp esi, 0x7b
0x1412640fc  cmp r15d, 0x7b
0x144acacec  cmp eax, 0x7b
```

Mas dos cotas de **datos** (`7b00 0000` -> `f401 0000`): 0x1414d62e5 y 0x1414f6e49.

El generador ya sustituye cada `cmp imm8` por un **salto a una cueva** (0x163400000) con la
comparacion a 32 bits y vuelve. O sea: no basta cambiar el inmediato (no cabe en 8 bits);
la cueva es la que lleva el valor.

## Por que 500 se cae

Con el modulo de 500 el juego **no arranca** (`0xc0000005`), y el volcado mini dice:

```
fault en ntdll+0x1a12d, escritura a 0x00000024
pila: sider.dll +0x1ae138 / +0x144ba9 ...
```

No es una cota del juego: la pila pasa por **sider.dll**, o sea que la cueva/trampolines
generados para 500 corrompen el flujo (o el propio modulo al aplicarse). Con 250 los mismos
35 parches funcionan.

## Siguiente

Depurar la cueva generada por `mkslots` para N>250 (offsets/trampolines de 32 bits) o escribir
a mano un modulo de 500 con comparaciones de 32 bits y saltos largos. Es un trabajo de RE
aparte; 250 sigue siendo el techo seguro (111 slots libres).


## Resuelto: la cueva no era, era el solape de tablas (2026-11-06)

El fallo de N>256 no estaba en las comparaciones: `mkslots` colocaba la tabla de **capacidades**
en `PAGE + 0xC00`, pero la de **offsets** empieza en `PAGE + 0x800` y para N=500 mide
`4*500 = 0x7D0`, o sea que acaba en `0xFD0` y **pisa la de capacidades**. Los accesores leian
offsets/capacidades corruptos y el juego se caia (pila por sider.dll, escritura a 0x24).

Arreglo en `tools/mkslots.py`:

1. `CAP_TAB = PAGE + 0x1000` (fuera de la tabla de offsets).
2. La pagina se reserva con **0x2000** cuando N > 256.
3. El assert de la cueva pasa a `PAGE+0x2000`.
4. Tope a **500** y `SIDER` por variable de entorno (antes `D:\dev\fl26\...`).

Resultado, comprobado:

```
fl26slots: applied all 35 patches -- competition slots 123 -> 500
           (slot 123 kept as sentinel), per-slot capacity 159, slots 79/80 1600
```

Juego arrancado con el modulo de 500. Capacidad por slot: **159 clubes** (la liga mas grande
del mundo tiene 87). Slots usados: 137; **363 libres** (hasta 499).
