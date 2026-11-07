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

## 9. Pseudo-código verificado con Ghidra 12.1.4 (2026-11-06, noche)

Salido de `rea decompile` sobre un **PE recortado** de 3,3 MB (0x140b1c000–0x140e45000) con la
misma base: así Ghidra analiza en minutos en vez de expirar con los 438 MB. Nombres `FUN_xxx` son
los de Ghidra; el resto es traducción nuestra.

### 9.1 Enter común — 0x140e43450 (slot +0x58)

```c
undefined1 enter(longlong *self)
{
  char ok = (*(*self + 0xd8))(self);          // construir la lista de ESTA pantalla
  if (ok == 0) return 0;                      // no hay lista -> no se entra

  rows = self[0x11];                          // objeto de filas (self+0x88)
  for (r = rows[0x70]; r != rows[0x78]; r += 0x50)
      if (r[0x40]) 0x141e4c240(r[0x40], 0, 4); // prepara el objeto de cada fila

  0x141e3f4c0(self);                          // monta la pantalla
  s = 0x141e32980();
  if (s) 0x141e32ad0(0x141e32980());

  if (*(int*)rows == 0 && global_1446f9a98) {  // caso "sin contenido"
      if (swap(global_1446f9a98[0x41], 0)) 0x141e52850();
  }
  return 1;
}
```

**No decide nada sobre sorteo ni calendario**: solo monta la pantalla y devuelve 1.

### 9.2 Init de Copa — 0x140b1c990 (slot +0xd8)

```c
undefined8 cup_init(longlong *self)
{
  0x141c6bb50();                              // init BASE (CompeSelectBase)
  decorate(self);                             // 0x141b1cc60
  ui = 0x141e3dc90(self);
  label = (vtable[ui+0x98][+8])(ui+0x98, "page");   // literal "page"
  0x141e4bba0(label, 0, 0, 2);
  0x141c6c540(self, 0x2bc01f5);
  0x141b1ca20(self, self + 0x17);
  (*(*self + 0x148))(self, 0, 0);             // otro slot propio
  0x141e51200(0x141e51150(), 0);
  return 1;                                   // SIEMPRE 1
}
```

### 9.3 Decorate — 0x140b1cc60

```c
void decorate(longlong self)
{
  for (i = 0; i < (self[0x98] - self[0x90]) / 12; i++) {
      if (i >= (self[0x98] - self[0x90]) / 12) {   // aserción si la lista cambia de tamaño
          (**_DAT_14352fa30)(0x1435a1fd8);          //   mientras se recorre
          __debugbreak();
          return;
      }
      item = { cid: *(u32*)(self[0x90] + i*12) };  // copia en pila
      item.flags = 0;
      resolve(&item);                              // 0x141b1cda0
      slot = map_find(self + 0xd0, item);          // 0x141b1c290
      map_insert(self + 0xd0, slot, item);         // 0x141b1c540
  }
}
```

`self+0xd0` es un **`std::map<cid, item>`** con lo que pinta la pantalla. La aserción de tamaño es
la que puede saltar si alguien toca la lista mientras se decora (crecer/recortar en el hook).

### 9.4 Resolver — 0x140b1cda0

```c
void resolve(item *it)                 // it = { cid, clubs, has_group, f6, f7, f8 }
{
  block = owner()[0x48];
  g = phkind(&it->cid, 2);             // grupos     (-1 = no hay)
  k = phkind(&it->cid, 3);             // eliminatoria
  if (k != -1) {
      rec = findrec(block, k);
      it->has_group = 0;
      it->clubs     = rec[0x30c] & 0x7f;
      it->f6 = (rec[0x300] >> 29 == 1) ? 1 : (rec[0x300] >> 29 == 2);
      it->f7 = (rec[0x300] & 0xe0000000) == 0x40000000;
      it->f8 = (rec[0x304] >> 9) & 1;
  }
  if (g != -1) {
      rec = findrec(block, g);
      it->has_group = 1;
      it->clubs     = rec[0x30c] & 0x7f;
  }
}
```

Confirma lo medido: **sin comprobación de nulos** (`findrec` se desreferencia directo) y la forma
del item.

## 10. Init base y montaje de la pantalla (2026-11-06)

### 10.1 Init base — 0x141c6bb50 (lo llama el de Copa)

```c
undefined8 base_init(longlong *self)
{
  (*(*self + 0x250))(self);                     // preparación base
  0x141c6bc30(self);
  0x141e41fe0(self, 0, (self[0x13] - self[0x12]) / 12, 1, 0);   // <-- construye las FILAS
  ui = 0x141e3dc90(self);
  label = (vtable[ui+0x98][+8])(ui+0x98, 0x143715e70);
  if (label) 0x141e54900(label, 0x190250);
  return 1;
}
```

`self[0x12]/[0x13]` son `+0x90/+0x98`: **la lista**. O sea, las filas se construyen a partir de
los items de 12 B, con `0x141e41fe0(self, 0, nº_items, 1, 0)`.

### 10.2 Montar la pantalla — 0x141e3f4c0

```c
void mount(longlong *self)
{
  rows = self[0x11];                            // objeto de filas (self+0x88)
  if ((rows[0x0a] != 0 || rows[0x0b] != 0) &&
      (rows[0x3d0] != rows[0x3d8])) {           // <-- exige filas NO vacías
      obj = 0x1424bea50();                      // "competición seleccionada"
      if (obj) {
          (self->vt[0x120])(self, obj[0x148] & 0xffffffff, obj[0x148] >> 32);
          return;
      }
  }
  /* si no, no se monta nada */
}
```

**Esta es la condición del "no arranca"**: si `rows[0x3d0] == rows[0x3d8]` (vector de filas
vacío) o `0x1424bea50()` devuelve 0, la pantalla no se monta y el menú se queda donde estaba.

### 10.3 Estado de la descompilación

- Hecho: enter, init de Copa, decorate, resolver, init base, mount.
- `0x141e41fe0` (constructor de las filas) sale con *bad instruction data* en el recorte: es un
  constructor de widget con vtables (`0x142b391f8`, `0x142b39220`, `0x142b39240`) y el decompilador
  no sigue el flujo. Habría que recortar su región exacta o depurarlo en vivo.

## 11. Resultado en juego (2026-11-07): el clon sí se juega

Probado de punta a punta **con el stack de módulos fl26 apagado** y el clon de la 36 (cid nativo,
nuestros 16 equipos) desplegado en `_FL26CupsTest`:

1. Kick Off > Copa → lista.
2. Pantalla de formato.
3. Selección de equipo.
4. **Sorteo** (cuadro).
5. **Menú del torneo**.
6. **El partido se juega**.

O sea: el motor hace todo cuando la competición es un cid que él conoce. Con el stack encendido, en
cambio, no pasa de la selección (y a veces el juego crashea).

### Lo que NO era
- `0x141e3f4c0` (el `mount` que decompilamos) **nunca se llamó** en este flujo: la pantalla se monta
  por otro camino. Su condición (`rows[0x3d0] != rows[0x3d8]`) no es la del "no arranca".
- El `ENTER` compartido (0x140e43450) se dispara en **muchas** pantallas y en casi todas llega con
  `+0x90` vacío (`items=-1`), así que no sirve como señal de la lista de copas.
- La lista de copas en vivo son **10 items** (`33, 2, 3, 5, 8, 27, 36, 34, 35, 37`) sin el DLL.

### Conclusión práctica

| vía | resultado |
|---|---|
| **Clon de copa nativa** (cid 36, nuestro nombre y equipos) | **jugable de punta a punta** con el stack apagado |
| **Cid nuevo** (cid 50, reg 200 ≤255, byte de fechas `0x10`) | se lista y abre; el juego **no sortea ni fecha** (0 llamadas a `DRAW` y `DATESTUB`) |
| Stack fl26 encendido | rompe el clon (no pasa de la selección) |

Siguiente trabajo, por orden:
1. **Bisect del stack** (mitades) para saber qué módulo rompe el clon; el sospechoso nº1 es el
   handler del `+0xd8` que reescribe la lista.
2. Con el stack arreglado, decidir: quedarse con el **clon** (hoy lo único jugable) o seguir con
   cid nuevo (falta el objeto por competición que el juego crea al arrancar).

## 12. El interruptor del sorteo (2026-11-07)

El sorteo (`0x1415485c0`) solo se llama desde `0x141344920` (y otras tres funciones) cuando un
**predicado** devuelve exactamente **2**:

```c
/* 0x141344920 */
FUN_141346030(param_1, 2, &list);       // lista de clubes de la fase
0x141522b50(reg, &list, 1);
if (0x14150d2b0(&reg) == 2)             // <-- el interruptor
    0x1415485c0(reg, &list, 1);         // sorteo
```

```c
/* 0x14150d2b0 -- gate(short *reg) */
undefined4 gate(short *reg)
{
  block = owner()[0x48];
  for (i = 0; i < *(u32*)(block + 0xd0bcf4); i++)
      if (*(u16*)(block + 0xc12e9c + i * 0x314) == *reg)
          return *(u32*)(findrec(block, *reg) + 0x84);
  return 7;                             // sin registro -> nunca sortea
}
```

- La tabla es la de **registros de 0x314 B** (la misma que usa `regcid_fix` del DLL): cuenta en
  `block+0xd0bcf4`, base `block+0xc12e9c`, y por registro un estado en `+0x84`.
- **2** = "toca sortear"; **7** = "no encontrado".
- Nuestra copa (reg 200) **no tiene registro** en esa tabla → devuelve 7 → no hay sorteo, ni cuadro,
  ni fechas. El clon (reg 46) sí lo tiene porque es una competición del juego.

**Siguiente paso de la vía 1**: encontrar quién crea esos registros al arrancar (la tabla se lee en
~550 sitios; el que la escribe es el "constructor del mundo") y añadir uno para la regulación
nueva con `+0x84 = 2`. Mientras no exista ese registro, ningún cid nuevo puede sortear.

### El planificador: `0x141348210` (2026-11-07)

La cadena del sorteo no arranca sola: la llama el planificador por fase. Su raíz:

```c
void root(param_1, short reg, param_3, param_4)       /* 0x141348210 */
{
  block = owner()[0x48];
  rec = findrec(block, reg);
  if (rec && phfin(reg)) {                            /* 0x141546c70 */
      /* tabla de 0x70 entradas {reg, ...} en 0x1434eecc4: rellena hasta 4 plazas
         de un array en rec+0x430 con 0x1415561c0(...) */
      if (FUN_141345cc0(param_1, reg, lista, param_4)) {   /* fase -> gate -> draw */
          FUN_141343bf0(param_1, lista);
          ...
      }
  }
}
```

Y `phfin` (`0x141546c70`) es el "¿está lista/terminada esta fase?": mira
`FUN_141546860(reg)` y recorre fases dependientes con `entry(otra_reg)`; también mira el campo
`rec[0x84]` (el mismo que el gate) contra 6.

**Registrar una competición, por tanto, es conseguir que el planificador llame a
`0x141348210(param_1, reg, …)` para su regulación** con `phfin(reg) == true`. Eso lo hace el
calendario del mundo (los partidos con fecha), no una tabla de alta.

Sonda lista para comprobarlo en vivo: `injectcup.js` engancha `0x141348210` (`ROOT`) y
`0x141546c70` (`PHFIN`) y avisa si se llaman con nuestra regulación (200) o con la del clon (46).

### Lo medido al intentarlo (2026-11-07)

Se inyectó la copa (cid 50) en la lista con Frida y se puso `reg 200[0x84] = 2` en vivo:

- La copa **se lista y deja avanzar** (formato), pero **`GATE` y `DRAW` no se llaman nunca**.
- La regulación 200 **sí existe** en la tabla de 0x314 (slot 123) y su `+0x84` pasó de **3 a 2**.
- La cadena del sorteo es:

```
0x141348340  (sin llamadores estáticos: es virtual/callback del planificador)
   -> 0x141345cc0  (fase)
      -> 0x141344920  (lista de la fase kind 2, kind 3, 0x141522b50)
         -> gate 0x14150d2b0 == 2 ?
            -> draw 0x1415485c0
```

Conclusión: **el muro no es el estado `+0x84`**; es que el juego nunca invoca esa cadena para una
competición que no sea suya: `0x141348340` no tiene llamadores estáticos, lo llama el planificador
del mundo, que solo conoce sus competiciones. Para la vía 1 hay que **registrar la competición en
ese planificador** (el "constructor del mundo"), no basta con la tabla ni con el campo.

**Confirmado a la última (2026-11-07)**: con `reg 200[0x84]=2`, la copa inyectada en la lista y
`phfin(200)` **forzado a `true`** con Frida, el juego **sigue sin llamar a `ROOT`** (ni `GATE` ni
`DRAW`). O sea: no es cuestión de satisfacer condiciones en runtime; el planificador simplemente no
tiene a esa competición en su plan. La única vía completa es que nazca del **constructor del mundo**
(con su calendario), como las del juego — o quedarse con el clon nativo, que sí está en el plan.

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
