# Copa: ya abre; queda la lista de la primera entrada (2026-11-06)

Con el slot 22 en las filas de copa, **Jugar > Copa > Nuevo ya abre** y pinta "Seleccionar
competencia" con las reglas a la derecha. Ya no hay cierre al entrar.

## El defecto que queda

En la **primera** entrada la lista solo trae las 8 copas del juego (UEFA EURO, Libertadores,
AFC Champions League, Africa Cup, FIFA World Cup...). Si sales al menu y vuelves a entrar,
aparecen **todas** (las 286).

Es el orden de construccion del menu: el vector de la lista se rellena con nuestros cids en
`cupsel_handler` (fl26swiss.dll), y la primera vez la pantalla ya se ha construido con las 8
del juego; al volver a entrar, el vector conserva lo anadido y salen todas.

## Siguiente

Anadir los cids al vector **antes** de que la pantalla lo materialice (en el arranque del modo,
no en el callback de filas), o forzar un rebuild de la lista en la primera entrada. Es de
`fl26swiss.dll`; el fuente esta en `tools/native/fl26swiss.c`.

## Copas regionales

Creadas 14 (ver `copas-regionales-2026-11-06.md`): CHAN, Copa UNAF, WAFU B, UNIFFAC, CECAFA,
COSAFA, ASEAN Club, CAFA Club, WAFF Club, EAFF Club, ASEAN Championship, CAFA Nations, WAFF
Championship, EAFF E-1. `check_world`: 286 ccup, 0 errores.

## Select Team

Los datos estan servidos (19 slots, cuatro pools "Otros" y Concacaf). El mismo defecto de
primera entrada puede verse ahi (la lista se rellena al segundo acceso).
