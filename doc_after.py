import io
p = "docs/developers/fork/estado-copas-2026-11-04.md"
s = io.open(p, encoding="utf-8").read()
old = "Siguiente paso propuesto: instrumentar `0x140e4bba0` y `0x140b1cc60` (o buscar la tabla con un\ndepurador; el juego corre elevado y no se puede enganchar) para ver qué cid consultan por fila, y\ncon eso o ensanchar la tabla en tiempo de ejecución (tabla propia de 1024 entradas, como se hizo\ncon el censo) o parchear el constructor."
new = """Siguiente paso propuesto: instrumentar `0x140e4bba0` y `0x140b1cc60` (o buscar la tabla con un
depurador; el juego corre elevado y no se puede enganchar) para ver qué cid consultan por fila, y
con eso o ensanchar la tabla en tiempo de ejecución (tabla propia de 1024 entradas, como se hizo
con el censo) o parchear el constructor.

### Medido después (sonda `CUPAFTER`, 2026-11-04 16:13)

El handler ya no salta en cola al init: lo llama y vuelca el estado al volver. Resultado:

- la lista **conserva** nuestros cids después del init (`item 8 cid=513`, `item 9 cid=96`,
  `item 10 cid=250`…), así que el menú no los reescribe;
- `self+0x88` **no** es un array de filas: apunta a la cadena `"compeSelect"` (el nombre de la
  pantalla), así que el bucle de `0x140e43450` recorre otra cosa;
- la lista queda con `list=175 cap=0x5F40C00` (los 256 huecos del stub de `fl26cupgrow`).

Conclusión: el nombre se resuelve **al dibujar**, no al construir la lista, y la resolución por
cid falla para las nuestras. Eso ya necesita un depurador (el juego corre elevado y REA/rizin no
se pueden enganchar) o alguien que conozca el código del menú: es el punto exacto que hay que
preguntar a Matozanato."""
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("doc actualizado")
