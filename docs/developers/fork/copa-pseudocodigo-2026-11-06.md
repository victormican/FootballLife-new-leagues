# Copa y menús: pseudo-código (2026-11-06)

Para nuestro uso. Cada bloque lleva la dirección real entre paréntesis, para poder volver al
desensamblado. Los nombres son inventados; lo que importa es el orden y los campos.

---

## 1. El sistema de menús (Copa, Liga, CompeSelect, ML, BL, Select Team)

Todos los modos son objetos con una vtable de la misma forma. Dos slots mandan:

```
# 0x140e43450 -- el "enter" COMUN de todos los modos (slot +0x58)
enter(self, a, b, c):
    ok = self.vt[0xd8](self, a, b, c)          # 1 = construir la lista de ESTA pantalla
    if not ok:
        return

    rows = self + 0x88                          # vector de filas, 0x50 B cada una
    for row in rows[0x70 .. 0x78]:
        if row[0x40]:
            0x140e4c240(row[0x40], 0, 4)        # prepara el objeto de la fila
    0x140e3f4c0(self)                           # monta la pantalla
    screen = 0x140e32980()
    if screen:
        0x140e32ad0(screen)
    if rows[0][0] == 0 and global_41:           # caso "sin contenido"
        0x140e52850()
```

```
# +0xd8 de cada clase = su constructor de lista
Copa             0x140b1c990
Liga             0x140b3be30
Liga Start       0x140ac32e0
Liga Category    0x140accce0
CompeSelect      0x140b08b70
CompeSelectBase  0x140c6bb50
ML TeamStatus    0x140b8acf0
ML PlayerMgmt    0x140b6eca0
ML Negociation   0x140b6c660
ML Coach         0x140b6b2b0
ML Journal       0x140b620a0
ML Training      0x140b385d0
SelectTeam       0x140c95420 / 0x140c9f520 / 0x140c985b0 (segun variante)
```

Consecuencia: **inyectar filas en cualquier pantalla = escribir en su lista** (`self+0x90..0x98`,
items de 12 B) **antes** de que corra su `+0xd8`, o enganchar ese `+0xd8`.

---

## 2. La lista de la Copa y su item

```
# 0x140b1c990 -- init de MenuModeCupSelect (el que el DLL sustituye)
init(self, a, b, c):
    0x140c6bb50(self, ...)          # init BASE (MenuModeCompeSelectBase): arma la lista cruda
    0x140b1cc60(self)               # decora cada item
    ui = 0x140e3dc90()
    ui[0x98] = "page"               # rotulo de la pagina
    return 1
```

```
# 0x140b1cc60 -- recorre la lista y resuelve cada competicion
decorate(self):
    items = self + 0x90             # begin
    end   = self + 0x98             # end
    for i in 0 .. (end - items) / 12:
        tmp = { cid: items[i].cid }             # copia en pila
        resolve_competition(&tmp)               # 0x140b1cda0
        add_to_mode(self + 0xd0, tmp)           # clubes / tiene_grupos / formato
```

```
# 0x140b1cda0 -- resolver por competicion (SIN comprobar nulos)
resolve_competition(item):                      # item: {cid, clubs, has_group, f6, f7, f8}
    block = owner()[0x48]                       # 0x14b6a60
    g = phkind(item.cid, 2)                     # fase de grupos (0xffff = no hay)
    k = phkind(item.cid, 3)                     # eliminatoria

    if k != 0xffff:
        rec = findrec(block, k)                 # 0x14bc860
        item.clubs     = rec[0x30c] & 0x7f      # <-- se desreferencia sin mirar null
        item.has_group = 0
        x = rec[0x300] >> 29
        item.f6 = (x == 1) ? 1 : (x == 2)
        item.f7 = (rec[0x300] & 0xe0000000) == 0x40000000
        item.f8 = (rec[0x304] >> 9) & 1

    if g != 0xffff:
        rec = findrec(block, g)
        item.has_group = 1
        item.clubs     = rec[0x30c] & 0x7f
```

**Item de 12 B** (lo que se escribe en la lista):

| +0 | cid de competición |
| +4 | nº de clubes |
| +5 | 1 = con fase de grupos, 0 = eliminatoria directa |
| +6,+7,+8 | bits de formato (`rec+0x300`, `rec+0x304`) |
| +9..+11 | sin usar por el resolver |

---

## 3. Cómo entra una competición en el juego (lo que hay que cumplir)

```
phkind(cid, 2) -> id de la fase de grupos   (una regulacion, o 0xffff)
phkind(cid, 3) -> id de la eliminatoria     (una regulacion, o 0xffff)

findrec(block, id) -> registro de 2352 B:
    +0x00  releg
    +0x02  id (u16)
    +0x08  cid (byte)
    +0x0a  group (255 = maestra)
    +0x0b  teams (6 bits bajos)
    +0x0c  formato
    +0x14  20 nombres de 115 B (idiomas)
    +0x30c clubes (7 bits)          +0x300/+0x304 formato/estado
```

```
CompetitionEntry (12 B por fila):
    u32 team
    u32 rowid
    u16 key = (cid << 8) | (orden - 1)      # 16 bits: cid 0..255 y orden 0..255
```

Checklist para una copa propia:

1. fila de `Competition` con el cid (flags/area de copa, código y nombre);
2. una regulación **maestra** (parent 0) con el cid, `group=255`, `teams=n`;
3. si hay grupos, réplicas `master + (g+1)*1024` con `parent=master`, `group=g`;
4. entradas por cid (orden 1..n);
5. el cid debe resolver en `phkind` (`k2` y/o `k3`);
6. `ccup`/`dates` en `fl26world.txt` para temporada;
7. y, para Kick Off, que la regulación tenga **calendario de copa** (ver §5).

---

## 4. La primera pantalla: qué construye las filas

```
rows(self)                      # [self+0x88] -> vector de 0x50 B
    fila: +0x40 puntero a objeto de fila
          0x140e4c240(obj, 0, 4) al entrar
```

Si al entrar "vuelve al menú" o muere, el orden de sospecha es:

```
1. +0xd8 devolvio 0            -> la lista no se construyo
2. rows[0][0] == 0             -> lista vacia; 0x140e52850 (transicion rara)
3. excepcion dentro del enter  -> fila/objeto mal formado
4. exit limpio (ExitProcess)   -> alguien de mas arriba decide salir (calendario/sorteo)
```

---

## 5. Fechas: el stub (donde esta el muro de los 255)

```
# tools/datecave.py, pagina 0x163000000 (119 B de codigo + 256 B de tabla)
date_for(reg_id):
    if reg_id < 256:
        b = table[reg_id]
        if b == 0xff: return []                  # sin calendario
        if b & 0x10:  return cup_calendar()    + (b & 7)   # 10 fechas de copa
        else:         return league_calendar() + (b & 7)   # 38 fechas de liga
    else:
        return league_calendar() + (reg_id & 7)  # <-- TODO id >= 256 acaba aqui
```

Para romperlo (copa con id > 255):

```
date_for(reg_id):
    idx = reg_id
    if reg_id >= 256:
        idx = reg_id - 256
        if idx >= 256: return league_calendar() + (reg_id & 7)
        b = table2[idx]                          # segunda tabla de 256 B
    else:
        b = table[reg_id]
    ... mismo tratamiento del byte ...
```

Y `patchset --cup-keys` tendría que aceptar ids hasta 511 y escribir en `table2`.

---

## 6. Sorteo (lo que sabemos)

```
# 0x1415485c0 -- sorteo de grupos nativo  (id_regulacion, vector de clubes, flag)
draw(reg, clubs, flag):
    reparte clubs en los grupos de la regulacion
    (el DLL lo engancha para el formato suizo de 36: tools/native/fl26swiss.c, gdraw_handler)
```

El cuadro de eliminatoria no se sortea: se llena con los ganadores de la fase anterior.

---

## 8. Lo medido en juego (2026-11-06, noche)

- **Copa propia** (cid 50, reg 200, 16 equipos): entra en el menú y **no muere**, pero el juego
  **no pregunta fechas** (`DATESTUB id=200`: 0 llamadas) y **no llama al sorteo** (`DRAW`: 0).
  O sea: se pinta la pantalla, pero el flujo no genera cuadro ni calendario para un cid nuevo.
- **Clon de la 36** (cid nativo, nuestros 16 equipos y nuestro nombre): con el stack de módulos
  **apagado**, hace **sorteo, genera partidos y avanza**. Con el stack encendido **no arranca**.
- Conclusión provisional: el flujo de Kick Off construye cuadro/calendario **solo para cids que el
  juego ya conoce al arrancar**; y algo de nuestro stack rompe incluso el cid nativo.
- Sospechoso nº1 del stack: el handler que reescribe la lista de copas (`+0xd8`, fl26swiss) al
  quitar las copas de grupos >32; después, `fl26caps` (fechas) y los módulos de paridad.
- Siguiente: bisect del stack módulo a módulo, y el pseudo-código de Ghidra del enter/sorteo.

## 7. Nuestro uso

```
Para listar una copa en Kick Off:
    escribir en la lista (self+0x90..0x98) un item { cid, 0,0, ... }
    antes de que corra +0xd8   ->  sale con clubes y formato del resolver

Para que se pueda JUGAR:
    regulacion con id <= 255 y byte de fecha 0x10  (o extender el stub, §5)
    + entradas y formato validos
```

Lo que **no** hay que hacer: meter un cid cuyo `phkind` devuelva un id sin registro (el resolver
no comprueba nulos y peta en `[rec+0x30c]`).
