# Ligas cortas rellenadas al nivel del release (2026-11-06)

## Lo que se hizo

Se compararon las **152 ligas** del mundo con el release NewLife 1.6b4 por nombre y se rellenaron
las que tenían menos clubes. Solo se aceptaron emparejamientos **seguros** (nombre exacto, o el
nuestro contenido en el del release); los nombres ambiguos se dejaron fuera.

| reg | liga | antes | ahora | nuevos |
|---|---|---|---|---|
| 11 | Argentine Second Division | 24 | **36** | 12 |
| 60 | Brazilian National Fourth Division | 24 | **63** | 39 |
| 93 | Venezuelan Premier Division | 13 | **14** | 1 |
| 111 | Ecuadorian Serie B | 10 | **11** | 1 |
| 121 | Zambian Premier League | 18 | **20** | 2 |
| 201 | Kuwaiti Premier League | 10 | **12** | 2 |
| 221 | Liga Nacional de Honduras | 11 | **12** | 1 |
| 341 | Cymru Premier | 10 | **12** | 2 |
| 345 | Kazakhstan Premier League | 10 | **16** | 6 |
| 358 | Maltese Premier League | 10 | **12** | 2 |
| 359 | Gibraltar Football League | 10 | **11** | 1 |
| 8467 | J2 League | 16 | **20** | 4 |
| 900 | TT Premier Football League | 10 | **11** | 1 |

**74 clubes nuevos** (1.628 jugadores) con `fill_group.py`, y después **135 nombres reales**
puestos desde el release con `tools/rename_filled.py` (los clones salen con nombre genérico; se les
asigna el nombre del release que faltaba en esa liga, y su abreviatura).

## Estado

```
equipos 3.648 (239 selecciones) · jugadores 103.722 · competiciones 496
regulaciones 691 · entradas 5.547 · 152 ligas · 271 copas
check_world: 0 errores
```

## Lo que quedó fuera (y por qué)

- **National Division**, **Primera Divisio**, **Federal A**, **Primera C**, **Torneo Federal**:
  el nombre coincide con varias ligas del release y no se puede elegir sin mirar el país. Nuestras
  divisiones argentinas se resolvieron a mano en su día.
- Las ligas pequeñas **a propósito** (Yokary Liga 8, Scottish Championship 10, Swiss Challenge 10,
  Andorra 10…) no se tocan: no están cortas.

## Nota sobre el DLL

El `fl26swiss.dll` desplegado es la build **A/B sin escritura** (para aislar el cierre al salir del
menú de copas). El arreglo del nombre/cid no está activo hasta volver a compilarlo con la
asignación.
