# Liga de un país desde una liga genérica

Receta usada el 2026-11-03 para crear **Azerbaiyán, Irlanda, Gales, Islandia y Hungría** sin gastar
ningún `cid` nuevo, reutilizando cinco «Generic League» y sus clubes.

## Idea

Una liga genérica ya trae todo lo que cuesta crear: fila en `Competition.bin`, regulación, slot en
el Select Team y diez clubes en `CompetitionEntry.bin`. Convertirla en la liga de un país es
renombrar, no construir:

| qué | dónde | cómo |
|---|---|---|
| nombre de la liga | `CompetitionRegulation.bin` +0x14 (20 idiomas) | `mkleague.put_names` |
| nombre y código | `Competition.bin` +0x14 (16 B) y +0x08 (12 B) | escribir en su sitio |
| clubes | `Team.bin` slots de nombre desde 0x9E | `put_team_name` (como `rename.py`) |
| país del club | `Team.bin` +0x46 | `(v & 3) \| (flag_id << 2)` |
| liga de un club | `CompetitionEntry.bin` +0x08 | cambiar el byte `cid` |
| línea del mundo | `fl26world.txt` | `country=`, `name=`, `clubs=` |

**Trampa medida**: el campo de nombre de `Competition.bin` es de **16 bytes** desde `+0x14`. Una
asignación de rebanada más larga (`cc[20:20+48] = ...`) **alarga la fila** y descoloca las 239
competiciones: `check_world` suelta 998 errores «competition 238 is not in Competition.bin». Hay
que escribir `cc[20:36]`.

## Clubes: mover, no duplicar

Los clubes reales del país que ya estaban en «Other European Leagues» (`cid 98`) se **mueven** a la
liga nueva cambiando el `cid` de su entrada. Para que el grupo siga con 48, el mismo número de
clubes donantes sale a `cid 98` renombrado a un club real de un país que aún no tiene liga
(Bielorrusia, Kazajistán, Kosovo, Georgia, Armenia...). Total: 5 donantes × 10 clubes = 50 = 40
renombrados + 10 movidos.

## Nombres que ya existen

Antes de renombrar hay que comprobar el mundo entero. La comparación por nombre exacto **no basta**:
`Emelec` choca con `Club Sport Emelec`, `Peñarol` con `CA Peñarol`. El filtro que funciona es la
**palabra más larga** del nombre candidato contra todos los nombres existentes (sin tildes):

```python
def core(name):  # 'Emelec' -> 'emelec', que aparece en 'Club Sport Emelec'
    ...
```

Con ese filtro, «Other Latin American Teams» quedó con 48 clubes reales de segunda fila (Perú,
Bolivia, Venezuela, Ecuador, Paraguay, Uruguay, Colombia) y cada uno con la bandera de su país.

## Gemelas vacías

Las «Generic League 66/67» (regs 382 y 383) compartían `cid` 50/51 y no tenían ni una entrada.
Se quitaron sus líneas del mundo: `check_world` deja de avisar de gemelas.

## Validación

```
fix_team_names --check     0 abreviaturas rotas
check_world                0 errores, 1 aviso (copa del juego con dos clubes en la misma plaza)
FL 2026 start.exe          2 de 2 arranques vivos 55 s
fl26clubs                 69<-364 y 73<-362 siguen sirviendo los dos grupos
```
