# Por qué faltaban grupos de "Otros" y qué límite tocar (2026-11-06)

## No era un límite

Comprobado en el mundo vivo:

| recurso | usado | tope | libre |
|---|---|---|---|
| slots de Select Team | 134 | **250** | 116 |
| equipos | 3.574 | 4.800 | 1.226 |
| jugadores | 102.094 | 123.825 | 21.731 |
| entrenadores | ~1.078 | 6.800 | 5.700+ |
| competiciones | 496 | 1.023 | 527 |

Ninguno aprieta. **Los entrenadores no tienen nada que ver**: los grupos de "Otros" no usan
entrenadores, usan el **slot** y su lista.

## La causa de verdad

El juego dibuja los grupos 69 (Other European Leagues), 71 (Other/Asia), 73 (Other Latin
American) y 75 (Other Clubs Africa) **por slot**, y su relleno **no devuelve clubes extranjeros**:
los cuatro salían vacíos u ocultos aunque sus clubes existieran y tuvieran su nibble `+0x4f`.

África se arregló sirviendo la lista desde la regulación (línea `pool 75 181`). Los otros tres
estaban igual de vacíos y **no se habían servido**. Eso es todo lo que faltaba: ni slots, ni
equipos, ni jugadores.

## Lo que se hizo

1. Tres líneas nuevas en el world file, iguales a la de África:

```
pool 69 364      Other European Leagues      (reg 364, cid 98)
pool 71 256      Other Clubs (Asia)          (reg 256, cid 254)
pool 73 362      Other Latin American Teams   (reg 362, cid 95)
pool 75 181      Other Clubs (Africa)        (reg 181, cid 165)
```

2. Europeos y latinoamericanos subidos a **48 clubes** cada uno con `fill_group` (29 → 48 y
   40 → 48; 27 clubes nuevos, 594 jugadores), para que los cuatro grupos tengan el mismo tamaño.

```
grupo 69 Europa     48 clubes
grupo 71 Asia       48
grupo 73 Latinoam.  48
grupo 75 África     48
```

Concacaf no tiene slot propio en el juego (sus clubes llevan nibble 6, el de Latinoamérica); su
competición (cid 221, 58 clubes) sigue existiendo pero no se pinta como grupo aparte.

`check_world`: 0 errores. Equipos 3.574 · jugadores 102.094.

## Sobre "los equipos dañados en Select Team"

Auditoría después del remapeo de países (que guardaba el id de bandera en vez de la fila):

```
clubes en liga listada: 1.945
con país distinto al de su liga: 4   (71667-71670, galeses en la liga de Gales)
```

Solo esos cuatro, y ya estaban así antes. Lo que cambió y puede parecer "daño" es que, al
arreglar el país, **los clubes se agruparon en su confederación real**: equipos que el juego
enseñaba en Oceanía o en una sección equivocada pasaron a Europa, África o Sudamérica. Eso es la
corrección, no un daño.

## Cómo comprobarlo

Entra en Select Team y mira los cuatro grupos: deben salir con su cabecera y 48 clubes cada uno.
