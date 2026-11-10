import io
p = "docs/developers/fork/estado-copas-2026-11-04.md"
s = io.open(p, encoding="utf-8").read()
add = """
## Como esta construida una copa de selecciones de las del juego (UEFA EURO)

Medido de las tablas del mundo:

| competicion | entradas | regulaciones | forma |
|---|---|---|---|
| UEFA EURO (cid 33) | 24 | maestra 41 `type 2` 24 equipos + 6 replicas (grupo 0..5) + KO 42 `type 3` 16 | 6 grupos de 4 -> eliminatoria de 16 |
| Copa America (34) | 16 | maestra 104 `type 2` 12 + 3 replicas + KO 43 `type 3` 8 | 3 grupos de 4 -> KO de 8 |
| FIFA World Cup (27) | 32 | maestra 34 `type 2` 32 + 8 replicas + KO 35 `type 3` 16 | 8 grupos de 4 -> KO de 16 |
| CONCACAF Gold Cup (96) | 16 | una sola reg 179 `type 3` 16 | eliminatoria directa |
| OFC Nations Cup (250) | 8 | una sola reg 183 `type 3` 8 | eliminatoria directa |

Reglas: `type 2` = fase de grupos (la maestra lleva el total y una replica por grupo con id
maestra + 1024*k, `group` = k); `type 3` = eliminatoria.  El dword de `+0x10` lleva la division y
la forma.  Nuestras 145 copas son `type 3` con el tamano exacto de sus entradas: igual que la Gold
Cup, correctas.

Las 21 copas del juego que desbloqueamos tienen regulaciones suyas con `type` 4, 8 o 9 en varios
casos (Spain Cup 4, Chile 8, Russia 9): ponerles `like=23` en la linea (forma de FA Cup) no casa
con su forma y las bloquea, asi que se ha quitado el `like=` de esas 22 lineas (2026-11-04).
"""
s = s.rstrip() + "\n" + add
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("doc actualizado")
