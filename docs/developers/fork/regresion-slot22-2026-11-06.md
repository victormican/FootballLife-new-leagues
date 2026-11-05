# Regresion y leccion: el slot 22 de las copas rompia Select Team (2026-11-06)

Puse las filas de copa en el slot **22** para quitar el `memcpy(0xd70)` del menu de Copa.
Efecto colateral grave: `fl26comptab` detecta que **varias filas piden el mismo slot** y
aborta la construccion de la tabla entera:

```
fl26comptab: slot 22 asked for twice, by 439 and 413 -- aborting
```

Sin tabla, ninguna liga nuestra tiene fila ni slot en Select Team: el mundo se ve incompleto.
**Revertido a slot 123** (fila oculta por copa, sin conflicto). La tabla vuelve:

```
fl26comptab: 240 hidden row(s) for the world's cups
fl26comptab: table copied, 540 rows (165 shipped + 375 ours)
```

Regla: las filas de copa **no pueden compartir un slot real**; `comptab` lo rechaza y tumba
toda la tabla. El cierre del menu de Copa hay que resolverlo por el buffer (DLL), no por el slot.
