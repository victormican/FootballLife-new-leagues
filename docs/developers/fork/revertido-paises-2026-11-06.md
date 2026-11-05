# Revertido el remapeo de países (2026-11-06)

## Me equivoqué: el juego quiere el id de bandera

Ayer cambié `country` de **id de bandera** a **fila de `Country.bin`**, convencido de que el juego
leía la fila. La evidencia de hoy dice lo contrario:

- Antes del cambio las banderas se veían bien.
- Después del cambio, las banderas de las ligas creadas salen mal y la liga belga desapareció.

Con el valor como id de bandera el juego resuelve la bandera por `flag_%03d.png`; con la fila,
resuelve la bandera de **otro** país (o ninguna).

## Lo revertido

`tools/revert_country_ids.py`:

- **Equipos**: los **3.450** que ya existían antes del remapeo recuperan **su valor de entonces**
  (del backup `Team.bin.before-countryids`). Los **198 nuevos** (Copa, MLS, Concacaf, rellenos) se
  convierten de fila a bandera con la tabla de `Country.bin`.
- **World file**: los **152** valores `country=` de las líneas viejas vuelven a su valor anterior;
  las líneas nuevas se convierten igual.
- **Línea belga quitada**: la que añadí para listar la Primera real (cid 111) era parte del
  empeoramiento; fuera hasta entenderlo.

Comprobado:

```
equipos: 3450 viejos restaurados, 198 nuevos mapeados
world: 152 valores de pais cambiados, linea belga quitada: 1
check_world: 152 ligas, 135 slots, 533 copas, 0 errores
```

Ejemplos del estado restaurado:

```
league 368  cid=106  country=197  name=Bélgica CPL        (197 = bandera de Bélgica)
league 30   cid=22   country=144  name=Liga Profesional   (144 = bandera de Argentina)
```

## Qué queda pendiente y qué NO se debe volver a hacer

1. **No volver a remapear países**: el valor correcto es el **id de bandera**.
2. El síntoma de "Oceanía llena" y "países en secciones que no son" hay que atacarlo por el
   **nibble `+0x4f` y los slots de pool** (que ya se arreglaron), no por el país.
3. **Bélgica**: la Primera real (cid 111, reg 115, 16 clubes) sigue sin listar, y la genérica
   `Bélgica CPL` (cid 106) sigue oculta (`slot=-1`). Para listarla hay que usar un slot que el
   juego acepte (probablemente uno de los 22..122 de fábrica, no 248) y `country` = **197**.
4. Las banderas de las ligas creadas ya deberían volver a verse como antes del cambio.

## Lección

Cada vez que un cambio de datos "arregla" una cosa y rompe otra, la prioridad es **volver al
último estado bueno** y atacar el síntoma por su causa real. El remapeo no era la causa: el país
estaba bien; lo que faltaba era servir los slots de pool.
