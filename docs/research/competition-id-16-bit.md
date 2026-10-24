# The competition id, 8 bits on disk and 16 in memory

2026-10-23. Static reading of `FL_2026.exe` (sha256 `9ee0c306...836281`), no game running.
This is the map for the next wall: competition ids above 255.

## What is a byte and what is not

| place | width | evidence |
|---|---|---|
| `Competition.bin` row | **byte at +5** | 36-byte rows, +3 region, +5 id, +6 flag, code at +8 |
| `CompetitionEntry.bin` row | **byte at +8** | 12-byte rows, +0 club, +4 entry id, +8 id, +9 order |
| `CompetitionRegulation.bin` row | **byte at +8** | 2352-byte rows, +2 regulation id, +8 id, +9 type |
| live competition record, `+0` | **word** | `0x14158df9d  cmp word ptr [rax], di` |
| live competition array | 600 records | `0x1414fd476  mov edi, 0x258`, stride `0x187c`, base `+0x4650` |

So the engine's own record already holds the id in **16 bits**, and the array has room for 600
of them. The 255 is a property of the three text tables, not of the runtime.

## The resolver, and what it compares

`0x14158df30(rcx = u16 id, rdx = index list)`:

```
0x14158df3d  movzx edi, cx                  ; the id, 16 bits
0x14158df8a  imul rcx, rax, 0x187c          ; record = owner->+0x78, +0x4650 + index*0x187c
0x14158df9d  cmp word ptr [rax], di         ; the record's own id is a word
```

The array is cleared by `0x1414fd460`:

```
0x1414fd476  mov edi, 0x258                 ; 600 records
0x1414fd483  mov dword ptr [rbx], 0xffffffff
0x1414fd4b9  add rbx, 0x187c
```

## Where the byte becomes a key: the Select Team census

`0x1414f1480` reads the two tables and builds the containers the list builder walks.

**Competitions** (table id 5), `0x1414f1500`:

```
0x1414f1500  0fb64f05        movzx ecx, byte ptr [rdi + 5]   ; the id, as a byte
0x1414f1504  884d68          mov byte ptr [rbp + 0x68], cl
0x1414f1518  384820          cmp byte ptr [rax + 0x20], cl   ; std::map<unsigned char, row*>
0x1414f1576  48897b28        mov qword ptr [rbx + 0x28], rdi ; value: the 36-byte row
0x1414f157a  4883c724        add rdi, 0x24                   ; next row
```

The key is **one byte**, and the comparison is inlined into the tree walk at
`0x1414f1518` / `0x1414f1534`. A 16-bit id here means comparing words, which fits the node
(key at `+0x20`, value at `+0x28`) without moving anything.

**Entries** (table id 6), `0x1414f1609`:

```
0x1414f1609  0fb60f          movzx ecx, byte ptr [rdi]       ; +9, the order
0x1414f160c  66ffc9          dec cx
0x1414f160f  0fb647ff        movzx eax, byte ptr [rdi - 1]   ; +8, the id
0x1414f1613  66c1e008        shl ax, 8
0x1414f1617  660bc8          or cx, ax
0x1414f161a  66894c2448      mov word ptr [rsp + 0x48], cx   ; the sort key
0x1414f175c  4883c70c        add rdi, 0xc
```

The entry key is **one packed 16-bit word**: `id << 8 | (order - 1)`. Ids 0..255 and orders
0..255 share those 16 bits. This is the real reason 256 does not fit, not the table.

## What a 256..511 patch has to do

1. **Read the high byte.** `Competition` has +4 free (always 0) next to the id at +5; the
   cheapest shape is to move the id to a little-endian word at +4 (`movzx ecx, word ptr
   [rdi+4]`, four bytes, same length as the byte load) and write the tables that way.
   `CompetitionEntry` (+0xb) and `CompetitionRegulation` (+0x910) only have non-adjacent spare
   bytes, so those two need a load + shift + or, in a code cave.
2. **Widen the map key** at `0x1414f1518`/`0x1414f1534` and every lookup of the same map:
   byte compare → word compare.
3. **Repack the entry key** at `0x1414f1613` from `shl 8` to `shl 6`, and every unpack
   (`>> 8`, `and 0xff`) to `>> 6`, `and 0x3f`. Orders are positions in a league and never
   reach 64 (the longest shipped league is 48 clubs), so `id << 6 | order` still fits 16 bits
   up to id 1023 without widening the item.
4. `fl26join.c` keys two tables of 256 on the regulation id and has to grow with it.
5. The date stub already dates ids from 256 up (`datecave.py`, `id & 7` shift), so it is not
   part of this wall.

The five "loader hooks" of `docs/research/limits.md` are items 1–3 above: one high-byte read
per table, the map compare, the entry repack.

## A third byte read, found 2026-10-24

`0x141eee1c0` looks a regulation up **by competition id**: `rows(container, 8)`
(CompetitionRegulation) and then, per row, `movzx edx, byte [rax + 8]` (`0x141eee27c`) compared
with the dword in `[rbp + 0x77]`. It is the path the EDIT data and the competition set-up take.
A cid of 256 reads as 0 there and matches competition 0, so it needs the high byte from
`+0x910` and a code cave, like the entry read above. With the two census sites it makes three
of the five hooks known.

## Meanwhile: the slots do not need a new competition id

The Select Team slot is a field of the **parameter table row** (`0x1434fdf00`, 165 rows of
0x108: id at `+0`, slot at `+4`), keyed by **regulation id**, not by competition id.
`fl26comptab` appends a row per league and writes its slot there. So slots 183..187 can be
filled with *twin* regulations that copy an existing league's competition id and clubs:

```
python tools/add_twin_leagues.py --base <pesdb> --worldfile <fl26world.txt>
```

which is what the test copy has (regulations 379..383, slots 183..187, five cids reused).
That fills the grid to 158 leagues without breaking the 255-id budget; a genuinely new
competition still needs the patch above.
## The exact sites, and how far each one can be patched in place

Read at the addresses below on 2026-10-23 (file offset = VA - 0x140000a00).

| site | bytes now | what it does | what 256..511 needs | in place? |
|---|---|---|---|---|
| `0x1414f1500` | `0f b6 4f 05` | `movzx ecx, byte [rdi+5]` | `0f b7 4f 04` -- the id as a word at +4 | **yes**, same 4 bytes |
| `0x1414f1504` | `88 4d 68` | `mov [rbp+0x68], cl` | `89 4d 68` -- store the dword (the slot is 8 bytes) | **yes**, same 3 |
| `0x1414f1518` | `38 48 20` | `cmp byte [rax+0x20], cl` | `39 48 20` -- compare **dwords**; the key is zero-extended, so the order is the same and no jump moves | **yes**, same 3 |
| `0x1414f1534` | `3a 4b 20` | `cmp cl, byte [rbx+0x20]` | `39 4b 20` -- `cmp dword [rbx+0x20], ecx` | **yes**, same 3 |
| `0x1414f1613` | `66 c1 e0 08` | `shl ax, 8` (entry key = id<<8\|order-1) | `66 c1 e0 06` (id<<6\|order-1; orders never reach 64) | **yes**, same 4 |
| `0x1414f160f` | `0f b6 47 ff` | `movzx eax, byte [rdi-1]` (the entry's id) | needs id = `byte[+8] \| byte[+0xb]<<8` -- four instructions | **no**, code cave |
| `0x141eee27c` | `0f b6 50 08` | `movzx edx, byte [rax+8]` -- **the regulation's id looked up by competition id** (`0x141eee1c0`: `rows(container, 8)`, then `cmp [rbp+0x77], edx`) | the high byte from `+0x910`; the compare is already a dword | **no**, code cave |

The entry read is the one that does not fit. The bytes from `0x1414f1609` to `0x1414f161e` are
the whole pack (`movzx ecx,[rdi]`, `dec cx`, `movzx eax,[rdi-1]`, `shl ax,8`, `or cx,ax`,
`mov [rsp+0x48],cx`); a `jmp rel32` at `0x1414f1609` can replace their start and the stub can
do the pack with the two-byte id and land back on `0x1414f161f` (`lea rax,[rsp+0x40]`), which
is a clean instruction boundary. The loop re-enters at `0x1414f1600`, before the jump, so the
row pointer is stored first and the pack is the only part moved.

Two things this table does **not** cover: where the same packed key is built or read outside
`0x1414f1480` (a second lookup would have to agree on the shift), and the `fl26join.c` tables
of 256 keyed on the regulation id. Both have to be found before a patch is worth playing.

The `Competition` row change also has a writer side: putting the id at `+4` as a word means
`Competition.bin` rows must be written little-endian there (`+4` low, `+5` high), and every
other reader of `+5` in the code becomes wrong. Grepping the decoded code for `movzx ..., byte
ptr [reg+5]` and `add reg, 0x24` in the same function finds `0x1414f1480` only, which is
encouraging but not proof.

## Correcci?n medida el 2026-10-24: +4 NO est? libre

El plan de arriba pone el id como palabra en `Competition.bin` `+4` (con el byte bajo en `+5`).
Medido en el mundo `_FL26All`: **cinco filas usan `+4`** -- las competiciones 23..27 llevan `27`
ah? (`+4 = 0x1b`, `+5 = 28..32`). Leer una palabra en `+4` las convierte en 6940..6944 y deja
sin casa a las regulaciones que las nombran (4.323 errores en `check_world`). El campo no es
libre: es la competici?n **padre/fase** de esos cinco.

Columnas que s? est?n a cero en **todas** las filas (medido):

| tabla | filas | columnas a cero |
|---|---|---|
| Competition.bin | 249 | `+0x02`, `+0x07`, `+0x20`..`+0x23` |
| CompetitionEntry.bin | 4.501 | `+0x03`, `+0x0b` |
| CompetitionRegulation.bin | 473 | `+0x01`, `+0x05`, `+0x3b`.. (y `+0x910`) |

Plan corregido, que hay que escribir antes de tocar el ejecutable:

1. **Competition**: mover el id a la **palabra en `+0x20`** (cuatro bytes libres y contiguos), y
   rellenar esa palabra en **todas** las filas con su id actual. El parche en sitio sigue siendo
   de la misma longitud: `movzx ecx, word [rdi+0x20]` (`0f b7 4f 20`).
2. **Entry**: byte bajo en `+8`, alto en `+0x0b` (libre), cueva como ya dec?a el documento.
3. **Regulation**: byte bajo en `+8`, alto en `+0x910` (libre y cero en las 473 filas), cueva.
4. `fl26join.c`, sus dos tablas de 256 por id de regulaci?n.

`fl26cid16.lua` ya lleva los tres parches en sitio del mapa y las dos cuevas (entrada y
regulaci?n) con verificaci?n de bytes; el de la competici?n queda pendiente de la migraci?n de
`+0x20`, porque sin rellenar esa palabra todas las competiciones leer?an id 0.
