import io
p = "docs/developers/fork/estado-copas-2026-11-04.md"
s = io.open(p, encoding="utf-8").read()
add = """
### Segunda medicion de la cadena (2026-11-04, 20:34)

Llamando por ffi a `0x1414b6a60()` (lo mismo que hace phkind) y leyendo `[rax+0x48]`:

    ctx=0x114643c0  block=0x7ff4df840010  count=65535  firstid=65535

O sea: la cadena del contexto **si** es la misma que la del global (`ctx+0x48` = el mismo bloque),
pero en ese bloque los offsets que tenemos apuntan a otra cosa: `+0xd0bcf4` no da la cuenta (sale
el centinela 0xffff) y `+0xc12e9c` no da registros con id razonable.

Conclusion: los offsets `0xc12e9c`/`0xd0bcf4` que se anotaron en su dia no son relativos a este
bloque, o el bloque correcto es otro campo de `ctx`.  Sin saberlo, escribir `+0x80` es a ciegas.

Lo que queda, entonces, es una pregunta de una linea para quien conozca el binario (o resolverlo con
depurador, que no se puede enganchar porque el juego corre elevado):

    en FL_2026.exe, phkind (0x14150af30) lee la cuenta en [block+0xd0bcf4] y los registros de
    0x314 bytes en [block+0xc12e9c], con block = [ctx+0x48] y ctx = 0x1414b6a60().
    Medido: block=0x7ff4df840010 da count=65535 y firstid=65535.
    ¿Cual es el bloque correcto, o que offsets usa de verdad el censo de Select Team?
"""
s = s.rstrip() + "\n" + add
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("doc actualizado")
