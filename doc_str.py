import io
p = "docs/developers/fork/estado-copas-2026-11-04.md"
s = io.open(p, encoding="utf-8").read()
add = """
## El nombre sale de la tabla de textos del juego (medido 2026-11-04, 17:xx)

Los nombres de competición que pinta el menú **no están en las tablas del mundo**: están en

    <idioma>/string/all.str      (data_s2526a.cpk; WESYS + zlib, 1,3 MB al descomprimir)

que es un fichero suelto y por tanto se puede servir por livecpk. Formato:

    u32 208                        numero de entradas
    208 x 3 u32                    indice (offset de la clave + dos campos)
    pool UTF-8 con NUL             desde el offset 2504 (las claves van ordenadas)

Las claves del indice son cortas y alfabeticas ("All1C", "Chg1C", "Cmt1T", "E10W"...).  Dentro
del pool hay ademas un bloque de **nombres de competicion**, que es el que se pinta:

    League | Eredivisie | Spanish League | Africa | Asia-Oceania | Italian Cup | Spanish Cup |
    Netherlands Cup | England Cup | French Cup | Germany Cup | Europe | Other | South America |
    League | Other European Leagues | Other Latin American Teams | na | nb | FIFA Club World Cup |
    European Qualifiers | African Regional Qualifiers | ...

`FIFA Club World Cup` aparece ahi como una entrada mas, y eso es lo que salia en todas nuestras
filas: no hay entrada para `FL_C700` y se cae a esa.

Lo que falta para escribir nombres: identificar los dos campos que acompañan al offset en el
indice (para saber si la clave es un id numerico, un hash o la propia cadena) y ver si el bloque
de nombres se indexa por posicion o por hash.  Con eso se añaden las 168 cadenas al pool, sus
entradas al indice, y se apunta a ellas el `+0x38` de la fila de cada copa (o se deja que el juego
las resuelva por codigo).  No se toca el ejecutable: basta el fichero por livecpk.
"""
s = s.rstrip() + "\n" + add
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("doc actualizado")
