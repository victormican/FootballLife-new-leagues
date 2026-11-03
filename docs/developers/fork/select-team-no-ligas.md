# Marcar un grupo como «no liga» en Select Team

Investigado el 2026-11-03 sobre el mundo vivo. Resumen: en Select Team **no existe un campo «esto
es liga / esto no»**. La lista es una lista de **slots**, y lo único que distingue una categoría de
una liga es que el slot tenga **rótulo propio**: el rótulo gana al nombre de la competición. Los
slots con rótulo son solo los del juego (0..6, 69, 70, 71, 73 y 75) y **no se puede pasar del 75**
sin parchear el interruptor.

## Cómo se pinta la lista

`0x140ea08e0` convierte un **slot** en el nombre que se ve. Es un `switch` cuyo índice sale de la
tabla de bytes `0x140ea0b3c` (**0x4c = 76 entradas**, una por slot 0..75); el valor elige uno de
doce casos. El caso 11 es el de por defecto, que deja la cadena vacía; el llamante, al verla vacía
(`0x140ea0a0e`), usa el **nombre de la competición**.

Traducido: **el rótulo del slot gana**, y si no hay rótulo se enseña la liga que haya en el slot.

| slot | rótulo del juego | texto |
|---|---|---|
| 0 | Europe | — |
| 1 | Africa | — |
| 2 | North & Central America | — |
| 3 | South America | — |
| 4 | **Asia-Oceania** | `0x660081` |
| 5, 6 | Classic Teams | `0x6600f7` |
| 69 | Other European Leagues | `0x6600d2` |
| 70 | Other Clubs (Asia) | — |
| 71 | Other | `0x660093` |
| 73 | Other Latin American Teams | `0x6600d3` |
| 75 | Other Clubs (Africa) | `0x66010f` |
| ≥ 76 | **ninguno** (`cmp eax, 0x4b` corta en 75) | — |

`fl26slotnames.lua` es el módulo que decide qué slots conservan el rótulo: recorre el mundo, y de
los siete (4, 5, 6, 69, 71, 73, 75) **libera** los que tienen una liga encima, apuntando su byte al
caso 11. Hoy libera 69, 73 y 75 (los tres que usamos para los «Other»). Con eso, esas filas enseñan
el nombre de la liga en vez del rótulo.

## Qué hay hoy en cada grupo

| grupo | cid | slot | rótulo del juego | en la lista ahora |
|---|---|---|---|---|
| Other European Leagues | 98 | 69 | sí | **liberado**: enseña el nombre de la liga |
| Other Clubs (Asia) | 254 | 70 | sí | conserva el rótulo |
| Other Latin American Teams | 95 | 73 | sí | **liberado** |
| Other Clubs (Africa) | 165 | 75 | sí | **liberado** |
| Oceania | 91 | 76 | **no existe** | enseña «Oceania» (nombre de la competición) |
| Otros Concacaf | 221 | 128 | **no existe** | enseña «Otros Concacaf» |
| Selecciones No FIFA | 255 | **-1** | no aplica | **no sale** (slot -1 = sin plaza) |

«No FIFA» ya está fuera del Select Team: su slot es `-1`, así que no es una liga jugable ni una
fila de la lista. Los tres «Other» sí están y son jugables.

## Cómo se marca, en la práctica

**A. Grupos en un slot con rótulo (69, 70, 71, 73, 75).** Es gratis: basta con **no liberar** el
slot. El rótulo del juego vuelve a ganar y la fila se lee como categoría, no como liga. Se hace en
`fl26slotnames.lua` quitando el slot de `SLOTS` (o dejando que `world_slots` no lo libere), y el
resultado se ve sin tocar el ejecutable.

**B. Slots sin rótulo (Oceania 76, Otros Concacaf 128).** No hay rótulo que conservar:
- **b1. Mover el grupo a un slot con rótulo libre.** El 71 («Other») está libre y conserva rótulo:
  mover ahí la competición (`slot=71`) la convierte en categoría sin tocar código. Es la vía
  barata, aunque el texto diga «Other» y no «Oceania».
- **b2. Darle rótulo propio.** Hay que **parchear el interruptor**: subir el corte `cmp eax, 0x4b`
  (igual que `fl26slots250.lua` sube otros topes de slot) y **mover la tabla de 76 bytes** a una
  copia más larga, porque la del ejecutable no tiene sitio para el slot 76 (los 4 bytes siguientes
  son otro dato). Después, su byte tiene que apuntar a un caso que cargue el texto; el texto
  «Oceania» no existe como id del juego, así que hay que **añadir una cadena** o reutilizar un id
  libre. Es la vía cara (una tarde de trabajo y una prueba por paso).
- **b3. Sacarlo de la lista.** `slot=-1` como «No FIFA»: deja de ser liga jugable y no aparece.
  Es lo correcto si no quieres ni categoría.

**C. Orden.** La lista va **por slot ascendente** y `fl26comptab` la reordena solo si el mundo trae
`kickorder <reg>:<place>` (hoy no hay ninguna): coloca la liga justo después del slot que diga
`place`, y lo aplica con un stub (`install_order`, `ORDER_FN 0x140ead990`). Para las categorías de
**país** dentro de Master League el orden es otro: `order <region>,...` (mundo) reordena las
regiones, y `fl26catlist` añade las nuestras al final porque la lista del ejecutable tiene 28
regiones fijas.

Para lo que pides —«Oceania después de Asia/Oceanía y luego los no FIFA»— el orden de slot ya lo
da si Oceania va en un slot **mayor que 4 y menor que 22**, y los no FIFA en el último rótulo
(71 o 75). Es decir:

```
4  Asia-Oceania   (rótulo del juego)
5  Classic Teams
6  Classic Teams
7  Oceania        (necesita rótulo: b2)  ó  71 «Other» (b1)
...
69 Other European Leagues
71 No FIFA / Other
73 Other Latin American Teams
75 Other Clubs (Africa)
```

## Recomendación

1. **Ya:** dejar de liberar 69, 73 y 75 → los tres «Other» vuelven a leerse como categorías (A).
   Es un cambio de una línea por slot en `fl26slotnames.lua` y no toca el ejecutable.
2. **Oceania:** moverla al slot 71 (libre, con rótulo «Other») o sacarla con `slot=-1`; su rótulo
   propio exige el parche de la tabla de casos (b2).
3. **No FIFA:** se queda con `slot=-1`, que es exactamente «no liga».
4. **Orden fino:** si hace falta, una línea `kickorder` por liga; las categorías ya se ordenan por
   slot.
