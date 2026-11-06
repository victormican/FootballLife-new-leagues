# Copa propia jugable: receta y el último escalón (2026-11-06)

Probado en limpio (`D:\SP Football Life 2026 - copia`, sin Mod Studio) con el stack de módulos y
el DLL blindado.

## Lo que ya funciona

```
python tools/mkccup.py --base <pesdb del juego> --out <livecpk>_FL26CupsTest \
  --cup "Copa Test|FL_CTEST|50|300|300|0|17:1,17:2,17:3,17:4,19:1,19:2,19:3,19:4,18:1,18:2,18:3,18:4,20:1,20:2,20:3,20:4|4|0|23"
```

- Eliminación directa (`groups=0`), 16 equipos, **`like=23`** (el cuadro de la FA Cup).
- Línea para `modules\fl26world.txt` (sin BOM):

```
ccup 300 ko=300 groups=0 cid=50 like=23 entry=... name=Copa Test
```

Con eso, en el juego:
- Kick Off > Cup **lista la copa** (item 9, cid 50);
- la pantalla **muestra la cantidad de equipos y deja escoger** tamaño y equipos;
- el log confirma: `cup 300 ... a single-match knockout of 16, shaped and dated as reg 23`.

## El último escalón: el calendario

Después de elegir equipo **no deja avanzar el tiempo**: la copa no tiene fechas en el calendario.
El log lo dice:

```
[fl26swiss.lua] fl26swiss: date shift set for 0 cup(s)
[fl26caps.lua] fl26caps: [3788/3839] 0x163000000 ... fixture dates: the date-spread stub and its table
```

`fl26caps` instala un **stub de fechas** con una tabla por id de regulación
(`11:league+1, 49:league+2, ... 186:cup+0, 190..255:league+N`). Nuestro **reg 300 no está en esa
tabla** (se generó con el mundo viejo), así que el stub no le da fechas y el calendario se queda
sin partidos.

**Arreglo**: regenerar esa tabla (y el stub) con el id de nuestra copa. Es un paso del
constructor del mundo (`datecave.py` / `mkregs.py`), no algo que se pueda teclear en el juego.
Es decir: una copa hecha a mano en un mundo mínimo se configura y se sortea, pero para que tenga
calendario hay que pasar por el constructor que genera `fl26caps`.

## Alternativa (sin tocar el módulo)

Copiar la regulación **nativa** de una copa del juego (Champions 3/4 para clubes, Copa América
104/43 para selecciones) y ponerle nuestro cid y equipos: hereda formato y fechas nativas. Es el
camino más corto para una copa jugable de verdad.

## Blindajes del DLL ya hechos (para que cargue en limpio)

1. día (`0x19115e4`): solo se lee si la página es legible;
2. grupo: se lee del operando parcheado (`0x140af353e` → `0x2ce1220`);
3. volcado `CUPAFTER`: comprueba listas, filas y cadenas.
