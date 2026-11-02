# La bandera de un país (`common/render/symbol/flag/flag_%03d.png`)

Un país no tiene campo de textura: el juego **construye la ruta a partir del id de bandera**, que es
el valor de los bits 10-18 del primer dword de su fila de `Country.bin`.  Si el id no tiene
textura en ninguna parte, ese país sale sin imagen.

## Cómo resuelve la textura

El exe lleva las piezas de la ruta juntas en `0x027c0a70`
(`cpk_dat/common/render/`, `symbol/flag/`, `flag_`, `e_`, `_l`, `_ll`, `_w_l`, `_b_l`, `_e_l`,
`_s1_l`, …) y las tres tallas son:

| fichero | tamaño | uso |
|---|---|---|
| `flag_%03d.png` | 128×128 | listas y rótulos pequeños |
| `flag_%03d_l.png` | 256×256 | la imagen normal |
| `flag_%03d_ll.png` | 512×512 | la grande |

Se leen de los `cpk.root` de Sider (por fichero) y después del CPK del juego
(`Data/dt15_x64.cpk` trae 214 ids, del 1 al 312).  Los equipos usan el mismo cajón con otro
prefijo: `e_<id6>_r.png`.

**El relleno a tres dígitos no es cosmético.**  El juego pide `flag_096.png`, nunca `flag_96.png`:
un país con id &lt; 100 guardado sin rellenar no se encuentra y queda en blanco.  (Esto ya se había
visto en `tools/mkcatflags.py`: el propio juego nombra `flag_012_l.png`.)

**Y hay dos dibujos distintos para lo que el usuario llama «bandera»:**

| qué se ve | fichero | qué es |
|---|---|---|
| el país en listas de nacionalidad, ligas, Edit | `flag_%03d[_l\|_ll].png` | la bandera del país |
| la **selección** en Select Team (la fila con su escudo) | `e_<id de equipo6>_r[_l\|_ll].png` | la bandera del país otra vez |

Una selección **no** dibuja `flag_<id>`: dibuja su escudo, y el de una selección del juego es la
bandera con el mismo marco (comparado: `e_001141_r.png` de Nueva Zelanda es la bandera de Nueva
Zelanda).  Por eso dar de alta el país no basta: el equipo nacional necesita su `e_`.  Nuestras
selecciones nuevas tenían el escudo de relleno de `tools/mkcrests.py` (el círculo con `G00`), y eso
es lo que salía en su hueco.

## Formato del PNG

Medido sobre las banderas del juego (128, 256 y 512 comparten dibujo):

- lienzo **cuadrado transparente**, PNG en paleta (`mode P`) con tabla alfa;
- marco gris `(222,222,222)` de `(2,40)` a `(253,215)` en la base de 256;
- la bandera ocupa `(10,48)-(245,207)`, es decir **236×160**, y se **estira** a esa caja (no se
  respeta la proporción original: Palau, 8:5, sale algo más ancha).

Lo de fuera del marco es **alfa 0**, no blanco: las banderas del juego tienen el marco recortado en
transparente (medido: `flag_170_l.png`, alfa 0 en `y<40` y `y>215`, y en `x<2` / `x>253`).  Si se
pinta blanco opaco, en el menú se ve una franja blanca por arriba y por abajo.

El PNG del juego lleva **tabla alfa** (`tRNS` de 256 entradas, 0 y 255) y un `sBIT` `(8,8,8)`.  Un
PNG en paleta *sin* `tRNS` no tiene canal alfa y el cargador de texturas no lo levanta: el fichero
está, el hueco sale vacío.  La herramienta escribe el PNG con la misma forma que el del juego,
`IHDR / sBIT / PLTE(256) / tRNS(256) / IDAT / IEND`.

En 128 el marco es `(1,20)-(126,107)` y la bandera `118×80` en `(5,24)`; en 512, `(4,80)-(507,431)`
y `472×320` en `(20,96)`.

## Herramienta

```
python tools/mkcountryflag.py --root <livecpk del mundo> --from sider/flags --ids 96,97,99
python tools/mkcountryflag.py --root <livecpk del mundo> --game <carpeta del juego> --emblems \
       [--from <carpeta de banderas>] [--min-team 71578]
python tools/mkcountryflag.py --root <livecpk del mundo> --check --game <carpeta del juego> [--also <otro root>]
```

`--from` es una carpeta con banderas planas `flag_<id>.png` (el id solo dice de qué país es; la
herramienta dibuja el marco y las tres tallas).  `--emblems` recorre las selecciones de `Team.bin`
desde `--min-team` (por defecto 71578, las nuestras) y le escribe a cada una el escudo con la
bandera de su país; la bandera la toma de `--from` o, si no está, del CPK del juego (`--game`),
recortando el dibujo que ya trae marco.  `--check` no escribe: lista los países sin textura, los
ficheros mal nombrados y las selecciones sin escudo propio.

### Receta, de principio a fin

1. **El país existe** en `Country.bin` y su primer dword lleva el id de bandera en los bits 10-18.
2. **La bandera del país**: una imagen plana en `sider/flags/flag_<id3>.png` (el `_ll` sale de
   aquí; cuanto más grande el original, menos blando queda el 512) y
   `--from sider/flags --ids <ids>` escribe `flag_%03d`, `_l`, `_ll` en el mundo.
3. **La selección**: está en `Team.bin` con el bit nacional (`+0x53` & 0x80) y su país en `+0x46`
   (el id de bandera, 9 bits desde el bit 2).  `--emblems --game <juego>` escribe su
   `e_<id6>_r.png` con la bandera de ese país, quitando el marco del original si viene del CPK.
4. **Comprobar**: `--check` debe decir 0 países sin textura y 0 selecciones sin escudo.
5. **Arrancar** y mirar Select Team; si un equipo sale con imagen y otro no, el que falla es el que
   no tiene `e_` en ningún root.

Los ficheros van al `common/render/symbol/flag/` del mundo (`_FL26MyWorld`), que es el primer
`cpk.root`; el juego lee por fichero, así que lo que haya ahí gana a lo de `_FL26All` y a lo del CPK.

Las banderas de los países nuestros viven en `sider/flags/` (fuente) y se escriben en el
`common/render/symbol/flag/` del mundo.

## Estado en `_FL26MyWorld` (2026-11-01)

- El juego **ya trae** las banderas de Oceanía (`flag_161` Samoa Americana, `163` Islas Cook, `164`
  Fiyi, `165` Nueva Caledonia, `167` Papúa, `168` Samoa, `169` Salomón, `170` Tahití, `171` Tonga,
  `172` Vanuatu, `184` Palau) y son correctas.  Los 11 PNG que había en `_FL26All` para esos ids
  **sobrescribían** las del juego con un recorte mal escalado (la de Samoa Americana salía como un
  zoom del águila): se retiraron.
- Los países realmente nuevos son los **8 no-FIFA**, y el juego no tiene textura para ninguno:

  | id | país | antes | ahora |
  |---|---|---|---|
  | 96 | Martinica | `flag_96.png` (nunca se pide) | `flag_096.png` |
  | 97 | Guadalupe | `flag_97.png` | `flag_097.png` |
  | 99 | Guayana Francesa | `flag_99.png` | `flag_099.png` |
  | 100 | San Martín | `flag_100.png` sin marco | con marco |
  | 101 | Sint Maarten | `flag_101.png` sin marco | con marco |
  | 102 | Bonaire | `flag_102.png` sin marco | con marco |
  | 118 | Cataluña | `flag_118.png` sin marco | con marco |
  | 123 | Padania | `flag_123.png` sin marco | con marco |

- `mkcountryflag.py --check` sobre `_FL26MyWorld`: **222 países, 0 sin textura** y **77 selecciones
  nuestras, 0 sin escudo**.
- Los 57 `flag_*.png` que había en `_FL26All` están copiados en
  `SiderAddons\backup-flags-<fecha>` y borrados: ese root se queda solo con los `e_*.png`.
- Los escudos de relleno (`G00`) de nuestras 77 selecciones estaban en `_FL26All` y **ganaban** al
  mundo en cuanto a prioridad de carpeta no, pero sí eran lo único que había: ahora el mundo escribe
  su `e_<tid>_r.png` con la bandera (231 ficheros) y los de relleno de esas 1527 filas se retiraron
  a `SiderAddons\backup-emblems-<fecha>`.
