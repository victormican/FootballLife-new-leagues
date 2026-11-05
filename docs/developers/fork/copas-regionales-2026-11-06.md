# Copas regionales: 14 nuevas (2026-11-06)

Creadas con `tools/mk_regional_cups.py` como eliminatoria directa de un partido con byes
(`like=23`, la forma de la FA Cup): fila de competicion, una regulacion, sus entradas y linea
`ccup`.

| copa | cid | equipos | tipo |
|---|---|---|---|
| African Nations Championship | 368 | 16 | selecciones |
| Copa UNAF | 369 | 4 | clubes |
| WAFU B Club Championship | 370 | 3 | clubes |
| UNIFFAC Club Cup | 371 | 3 | clubes |
| CECAFA Kagame Cup | 372 | 2 | clubes |
| COSAFA Club Cup | 373 | 3 | clubes |
| ASEAN Club Championship | 374 | 4 | clubes |
| CAFA Club Championship | 375 | 4 | clubes |
| WAFF Club Championship | 376 | 7 | clubes |
| EAFF Club Championship | 377 | 2 | clubes |
| ASEAN Championship | 378 | 4 | selecciones |
| CAFA Nations Cup | 379 | 4 | selecciones |
| WAFF Championship | 380 | 7 | selecciones |
| EAFF E-1 Football Championship | 381 | 2 | selecciones |

**No creadas** (en este mundo solo hay 1 equipo de esa region): WAFU A Club Championship,
SAFF Club Championship, SAFF Championship.

Los equipos salen de lo que hay en el mundo: para clubes, el campeon de cada liga de la region;
para selecciones, las selecciones de esos paises. **AFC Champions League Two Clubes ya existe**
(cid 603).

```
check_world: 286 lineas ccup, 0 errores
sider.log:   286 cup(s) for Kick Off > Cup, 286 taken
```

Backups: `Competition*.bin.before-regional` y `fl26world.txt.before-regional`.
