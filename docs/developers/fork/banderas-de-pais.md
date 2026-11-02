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

## Formato del PNG

Medido sobre las banderas del juego (128, 256 y 512 comparten dibujo):

- lienzo **cuadrado blanco** `(255,255,255)`, sin canal alfa, PNG en paleta (`mode P`);
- marco gris `(222,222,222)` de `(2,40)` a `(253,215)` en la base de 256;
- la bandera ocupa `(10,48)-(245,207)`, es decir **236×160**, y se **estira** a esa caja (no se
  respeta la proporción original: Palau, 8:5, sale algo más ancha).

En 128 el marco es `(1,20)-(126,107)` y la bandera `118×80` en `(5,24)`; en 512, `(4,80)-(507,431)`
y `472×320` en `(20,96)`.

## Herramienta

```
python tools/mkcountryflag.py --root <livecpk del mundo> --from sider/flags --ids 96,97,99
python tools/mkcountryflag.py --root <livecpk del mundo> --check --game <carpeta del juego> [--also <otro root>]
```

`--from` es una carpeta con banderas planas `flag_<id>.png` (el id solo dice de qué país es; la
herramienta dibuja el marco y las tres tallas).  `--check` no escribe: lista los países del
`Country.bin` del mundo que no tienen textura ni en los roots ni en los CPK, y los ficheros mal
nombrados (sin relleno de tres dígitos).

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

- `mkcountryflag.py --check` sobre `_FL26MyWorld`: **222 países, 0 sin textura**.
- Los 57 `flag_*.png` que había en `_FL26All` están copiados en
  `SiderAddons\backup-flags-<fecha>` y borrados: ese root se queda solo con los `e_*.png`.
