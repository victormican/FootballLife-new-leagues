# STATUS (2026-11-05, cierre de sesión)

## El mundo

```
D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld
equipos 3.547 (239 selecciones, 3.308 clubes) · jugadores 101.500
competiciones 496 · regulaciones 691 · entradas 5.446
151 ligas (slots 22..246) · 271 copas (102 supercopas) · 240 países
check_world: 0 errores (1 aviso de fábrica)
```

World file idéntico en `livecpk\_FL26MyWorld\fl26world.txt` y `modules\fl26world.txt`.
Copia de seguridad: `livecpk\_FL26MyWorld.bak*` y los `.before-*` de cada tabla.

## Infraestructura desplegada

| pieza | estado |
|---|---|
| `fl26swiss.dll` | 380.416 B, `7BC998A8…`, con `regcid_fix` sobre `block+0xc131b0` |
| `fl26cupgrow.lua` | **512** filas (stub `0x1800`) |
| `fl26clubs.lua` | sirve `pool 75 181` (África) |
| `fl26cid16.lua`, `fl26slots250`, `fl26caps`, `fl26regs1200` | en su sitio |
| Craft Anything | MCP con Ghidra 11.3.2 y Rizin (REA) |

## Hecho (sesión 4-5 de noviembre)

1. **Copas**: 168 → **271** (101 supercopas por nación, Oceania y No FIFA como copas, menú a 512
   filas).
2. **Países**: arreglado el `country` (guardaba el id de bandera): 3.450 equipos y 152 líneas
   remapeados; nombres en español con mayúsculas iniciales; Sudán del Sur ya sale (CAF).
   239 selecciones válidas: UEFA 61 · CAF 56 · AFC 47 · CONCACAF 45 · OFC 20 · CONMEBOL 10.
3. **Grupos "Otros"**: nibble `+0x4f` repuesto (África 51, Concacaf/LatAm 101, Asia 60, Europa 29);
   el grupo de África servido con `pool 75 181`.
4. **Argentina**: Primera listada (cid 22, slot 245, 26 clubes); 117 nombres reales en las
   divisiones bajas.
5. **NewLife 1.6b4**: 1.812 clubes con plantilla nueva (9.878 jugadores nuevos, 38.114
   actualizados).
6. **Escudos**: 510 reales desde el catálogo de footylogos.
7. **MLS**: 10 clubes creados y en Otros Concacaf (58); cid 40 preparado con 30 entradas.
8. **Colombia**: Primera C creada (cid 366, 87 clubes con nombre real).
9. **REA**: array de regulaciones localizado (`block+0xc131b0`); `phkind` solo se referencia desde
   una tabla; la entrada sintética no llega al juego.
10. **Documentación**: índice de 72 documentos, estado/escalado y una doc por bloque.

## Semáforo por área

| área | estado |
|---|---|
| Tablas y mundo (check_world) | 🟢 0 errores |
| Ligas y copas | 🟢 creadas y listadas |
| Países, banderas y nombres | 🟢 arreglados |
| Grupos "Otros" | 🟢 los cinco con clubes |
| Escudos de clubes nuestros | 🟢 2.606 con escudo (510 reales) |
| NewLife (plantillas) | 🟢 aplicado |
| Nombre y sorteo de copas (cid ≥ 256) | 🟡 **esperando una prueba de 5 min** |
| 17 copas no aceptadas por el DLL | 🟡 identificadas, sin decidir |
| Emblemas por byte bajo | 🟡 depende de lo anterior |
| MLS en su slot | 🟡 datos listos, falta formato/calendario |
| Oceania/No FIFA como grupos de selecciones | 🟡 hoy son copas |
| Escudos de ~2.100 clubes y logos de competición | 🔴 sin fuente mapeada |
| 4 clubes argentinos de la Primera | 🔴 no existen en las tablas |
| Primera C Colombia (87) | 🟡 se ve, no se jugará (172 jornadas) |

## El bloqueo principal (5 minutos)

Abrir **Kick Off > Cup** una vez. El DLL escribirá
`C:\Users\viarm\AppData\Local\Temp\opencode\regcid.txt` y con eso se cierra (o se reabre con
datos) el nombre y el sorteo de las 271 copas y, de paso, los emblemas.

## Pendientes priorizados

1. **Abrir el menú de copas** y leer `regcid.txt` (5 min).
2. 17 copas no aceptadas (1 h).
3. Emblema por byte bajo (2 h).
4. Duplicados de Copa Colombia + 4 `Generic League` (30 min).
5. Escudos con emparejador difuso (2 h + red).
6. MLS con su formato (`type 5`, conferencias, calendario) (3 h).
7. 111 clubes de las 17 ligas cortas (2 h).
8. 4 clubes argentinos (3 h).
9. Oceania/No FIFA como grupos de selecciones (4 h).
10. Capacidad barata: regulaciones a 2.000 y copas a 1.024 (2 h).

## Reglas que no se rompen

Arrancar con **`FL 2026 start.exe`** · world file idéntico en las dos copias · `fl26cupgrow` en
**512** · cerrar el juego (UAC) antes de escribir tablas · copia `.before-*` y `check_world` al
final · país = 9 bits desde el bit 562 y **fila**, no bandera · `set_bits` devolviendo la rebanada.

## Verificar en un minuto

```
python tools/check_world.py --base <mundo>\common\etc\pesdb --worldfile <modules>\fl26world.txt
python tools/limits.py
```
