import io
p = "docs/developers/fork/estado-copas-2026-11-04.md"
s = io.open(p, encoding="utf-8").read()
add = """
## Estado del nombre al cerrar la sesion (2026-11-04, 20:2x)

- El menu **abre y lista las 175 filas** (`167 world cup(s) added, all in (list 175 of 256)`) con el
  stub de `fl26cupgrow` y sus guardas; las copas estan ordenadas alfabeticamente en el world file.
- El nombre **sale del byte bajo del cid**: una copa con `cid & 0xFF == 27` muestra "FIFA World Cup",
  otra con 88 muestra "Maltese Premier League", etc.  Las de cid < 256 (Gold Cup 96, OFC 250/251,
  Nations Leagues 252/253) salen bien.  Es el mismo truncamiento que ya se arreglo para la lista de
  clubes (censo) y que sigue vivo en la ruta del nombre y en el emblema.
- `phkind(cid, 3)` (0x14150af30) es el que convierte cid -> regulacion de una copa, y responde
  `0xffff` para cid >= 256: compara `dword [registro+0x80]` con el cid y ese campo solo lleva el
  byte bajo.
- `fl26regcid.lua` intenta rellenarlo, pero **la direccion del array no es la que usa el exe**:
  leyendo `[[0x143705e10]+0x48] + 0xc12e9c` sale `count=65535 firstid=65535`.  La cadena buena
  arranca en `0x1414b6a60()` (que usa phkind) y no en ese global; falta probarla desde Lua
  (ffi.cast de 0x1414b6a60) o conocerla de quien escribio el modulo.
- Con el campo `+0x80` correcto deberian caer **nombre y tamano de sorteo** a la vez: el menu abre
  la competicion 1 (que no tiene sorteo) cuando no encuentra la suya, y de ahi el cierre al entrar.
"""
s = s.rstrip() + "\n" + add
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("doc actualizado")
