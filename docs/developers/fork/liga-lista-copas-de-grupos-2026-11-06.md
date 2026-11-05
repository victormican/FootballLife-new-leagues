# Liga lista copas de grupos (2026-11-06)

Verificado en pantalla: "Liga > Seleccionar la liga a competir" muestra:

```
Copa Sudamericana
Austrian Second League
FL Conference League
UEFA Champions League
UEFA Europa League
```

Las copas que salen son las de **fase de grupos** (Copa Sudamericana y Conference nuestras; UEFA CL/EL
del juego). Las eliminatorias directas no salen. O sea: el criterio del menu "Liga" es el
**formato de la competicion** (tiene fase de liga/grupos), no la forma de la fila.

Se probo a copiar la fila de copa desde la Libertadores (`CUP_TEMPLATE_ID = 5`) en vez de la
plantilla de liga (61): la lista **no cambio**. El filtro no esta en la fila de parametros.

Siguiente: mirar el campo de formato/tipo de `Competition.bin` (o el `+0xa` de la regulacion)
para las copas de grupos nuestras, y decidir si se les quita la fase de grupos (cambiaria el
formato de la copa) o se acepta que el juego las liste tambien en Liga, como hace con las UEFA.
