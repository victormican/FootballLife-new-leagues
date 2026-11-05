# La lista de Liga/Copa necesita Enter antes de navegar (2026-11-06)

En "Seleccionar la liga a competir" el foco no esta en la lista: **hay que pulsar Enter**
una vez para que la lista lo coja y entonces las flechas recorren arriba/abajo. Sin ese
Enter, los `down` no mueven la seleccion.

`tools/select_team_retry.ps1` ya lo hace: Enter (foco), luego `scroll` posiciones.

## Copa Sudamericana

`ccup 192 ko=193 groups=8 ... cid=513 name=Copa Sudamericana` usa las regulaciones **192/193**
(que son las del juego) con un competition id propio (513, `FL_SUDAMER`). No hay otra
competicion `SUDAM` en `Competition.bin`: el mundo sustituyo la copa del juego por esta.

Para conservar la del juego y tener la nuestra encima hace falta:

1. El registro original del juego (cid/regulacion) desde los datos base (cpk), que no estan
   en nuestros backups (vienen de NewLife).
2. La nuestra con id/regulaciones nuevos (>177) y un slot libre.

Mientras, la nuestra "pisa" la del juego.
