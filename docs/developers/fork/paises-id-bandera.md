# Países: el id guardado era el de la bandera (2026-11-05)

## El fallo

El mundo guardaba en `country` el **id de la bandera** (bits 10-18 del primer dword de la fila de
`Country.bin`) donde el juego lee el **número de fila**. Son dos números distintos y no coinciden:

| país | fila | bandera | el mundo decía | el juego leía |
|---|---|---|---|---|
| Argentina | 129 | 144 | 144 | **Nueva Caledonia** (fila 144, OFC) |
| Brasil | 131 | 146 | 146 | **Papúa Nueva Guinea** (OFC) |
| Uruguay | 137 | 152 | 152 | **Guam** (OFC) |
| Francia | 173 | 208 | 208 | fila 208 = "Otros" |
| Sudán del Sur | 213 | 312 | 312 | **fuera de la tabla** (solo hay 240) |

De ahí los tres síntomas que viste:

- **Oceania llena**: media Sudamérica y Europa caían en filas de países de Oceanía.
- **Países en secciones que no son**: la sección es la confederación de la fila leída.
- **Sudán del Sur no existe**: 312 no es ninguna fila, así que el motor no lo coloca en ningún
  sitio. El registro estaba (equipo 73795) pero sin país válido.

## El arreglo (`tools/fix_country_ids.py`)

La correspondencia bandera → fila es uno a uno (240 filas, 240 banderas distintas), así que se
puede invertir sin pérdida: la bandera se sigue calculando sola desde la fila.

```
equipos remapeados: 3.450
valores country= del world file: 152
nombres de país en Mayúsculas Iniciales: 638
```

Después:

```
selecciones: 239, todas con país válido
por confederación: UEFA 61 · CAF 56 · AFC 47 · CONCACAF 45 · OFC 20 · CONMEBOL 10
países: 240 · sin selección: solo "Otros" (marcador de relleno)
Sudán del Sur -> equipo 73795, país 213 (CAF)
```

## Nombres en español y en Mayúsculas Iniciales

`Country.bin` tiene los nombres en 18 idiomas (70 B por ranura desde +148): la 0 y la 3 son
español, la 2 inglés. Se han puesto en Mayúsculas Iniciales las tres, respetando las partículas
("Sudán del Sur", "Costa de Marfil", "Estados Unidos"):

```
129  Argentina     131  Brasil      173  Francia
204  Uzbekistán    205  Gales       213  Sudán del Sur
```

Países con nombre duplicado: **0**.

## Banderas

`mkcountryflag.py --check`: **240 países, 0 sin textura**; 95 selecciones nuestras, 0 sin emblema.
Las 26 filas nuevas que añadimos tienen sus tres tamaños (`flag_XXX`, `_l`, `_ll`).

## Estado

`check_world`: 0 errores. Copias: `Team.bin.before-countryids`, `Country.bin.before-countryids`,
`fl26world.txt.before-countryids` (en `modules\` y en `livecpk\_FL26MyWorld\`).

> Nota para el futuro: `set_bits` sobre `teams[o:o+T_REC]` trabaja sobre una **copia** de la
> rebanada; hay que devolverla al array (`teams[o:o+T_REC] = rec`) o no se escribe nada. Fue el
> motivo de que el primer intento dijera "3.450 remapeados" sin cambiar ninguno.
