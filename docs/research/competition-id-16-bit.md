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
