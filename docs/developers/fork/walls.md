# The walls, with numbers

2026-10-24. `python tools/walls.py --base <world pesdb> --worldfile <world>` prints this table
for any world. What it says for the test copy, and what each wall needs next.

```
player id max in the engine: 262144 (18 bits)
players      76972 / cap 123825  highest id 260545  ids left 1598
teams         2886 / cap 4800    national 211
competitions   255 / 255 (a one-byte id)  free 0
regulations     403 / 1024 (the ids the module names)
slots          158 of 250 used by the world file
```

## Players: the array is not the wall any more, the id is

The array cap (123,825) is far away; the **18-bit player id** is not. The engine keeps a player
handle as `id << 14 | n` in 32 bits, so an id of 262,144 or more has no handle and the season
set-up dereferences nothing (measured 2026-10-14, `0x140f325a4`). The copy's highest id is
**260,545**, so 1,598 ids are left.

The id space is not really 262,144 used: **the game's own table is sparse**. The shipped
`Player.bin` has 29,492 players using 29,492 of the 184,461 ids below its highest -- **150,776
free ids** below it, plus every gap the world's own players leave. The builder has always
allocated *above* the game's highest (first free above 179,672, then above the base's max), so
all that room went unused and the copy walked into the wall.

What is done about it:

- `playeredit.free_ids(players, n)` returns the first n ids no record holds, from 1 up;
- `add_nations.py` and `add_generic_leagues.py` take `--ids free` (default) and allocate from
  them: a world of 29,492 players that gets 67 national teams keeps its highest id at 184,461
  instead of climbing;
- `lbplayers` takes `FL26_FREE_PLAYER_IDS=1` for the same in a Build (the `FreeIds` start and
  the `new_id` floor), and `new_face_lines` now tells the world's players apart by "not in the
  shipped table" instead of "above its highest", which is what makes low ids work with the
  face lists.

What is left: the Build's *own* new-player allocator still starts above the game's highest
(the ids 179,673+ in a fresh build), so a world built with the flag still has to be checked
against the copy's 1,598 ids; the next step is to start it from the gaps too (`mkplayers`'
cursor), then a 123,825-player world lives at ids 1..~154,000, far from 262,144.

**Above 262,143** is a different job: the handle's id field is 18 bits. Widening it means
finding the packing (`id << 14`) and every `>> 14` that reads an id back, and shrinking the
14-bit half -- deep, and the game has to be in the loop.

## Competitions: 255 of 255, and the third site

Every competition id is used (the game's 91 and the world's 164). The one-byte id is read in
more places than the census of Select Team (`0x1414f1480`, documented in
`competition-id-16-bit.md`):

| site | reads | note |
|---|---|---|
| `0x1414f1500` | `Competition.bin +5`, byte | the Select Team census, map keyed by a byte |
| `0x1414f160f` | `CompetitionEntry.bin +8`, byte | the entry key `id << 8 | order-1` |
| `0x141eee27c` | **`CompetitionRegulation.bin +8`, byte** | a lookup of a regulation **by cid** in `0x141eee1c0`: `rows(container, 8)`, then `movzx edx, byte [rax+8]; cmp [rbp+0x77], edx` |

The third one is new (2026-10-24): it is the path the EDIT data and the competition set-up use
to find a regulation by its competition id. It compares the **byte** with a **dword**, so a cid
of 256 (byte 0) matches competition 0. Any cid above 255 needs this site widened as well -- and
unlike the two census sites, its read is four bytes (`0f b6 50 08`) and the high byte is not
next to it (+9 is the type), so it needs a cave.

Nothing has changed in the conclusion: ids above 255 need the three high-byte reads, the census
key widened, and the entry key repacked. The list of exact byte patches is in
`competition-id-16-bit.md`.

## The modules are not installed by `leaguebuilder.py on`

2026-10-24, measured on the test copy: a world looked like "one league instead of 134" for two
whole rounds because the module that does the work was not the one being run. `tools/leaguebuilder.py
on <world>` switches the world (cpk root, `modules\fl26world.txt`, the per-world region modules)
but it does **not** copy `sider/` or `sider/experimental/*.lua` into `SiderAddons\modules`. That
is the Studio's **Install the modules** button (`leaguebuilder.install_modules`), and it copies
from the module pack (`tools/lbpack.py` -> `out/lbpack`), not from the source tree.

So after changing a module of ours, check the copy the game runs:

```
python - <<'EOF'
import hashlib, os
repo = r"...\pes-2021\sider"
game = r"...\SiderAddons\modules"
...
EOF
```

and copy the file by hand (or build the pack and run `install_modules`). The log of a stale
`fl26comptab.lua` said `too many rows -- aborting` while the repository copy already had the 400
cap: the module that aborted was 181 bytes shorter than the one in `sider/experimental`.

## The competition parameter table: 255 rows

`fl26comptab` used to abort the whole list when the copy of the competition parameter table
would pass **255 rows** (`too many rows -- aborting`): the game ships **165** rows and the
module could append **90** of ours. That was the module's own safety, not the game's: the count
is patched through `COUNT_SITES` as a **dword**, so 2026-10-24 it was raised to **400** and a
world with **134 leagues** (165 + 129) installs. A league whose regulation id is one of the
shipped 165 reuses that row (moves it) and does not count.

The world `_FL26All` hit it with 134 leagues (8 on shipped rows, 126 new): the copy was 291
rows. Dropping 36 left 98 leagues = 8 + 90, exactly 255. A world with 158 leagues (the old
copy) kept 68 of them on shipped rows to stay inside the cap. More than 90 new rows needs the
game's count widened (it is a byte), the same kind of job as the competition ids above 255.

## Leagues: the slot table, not the ids

A league needs a **Select Team slot** and a competition. The slot table has 250 entries
(`fl26slots250`) and the world file already uses 158 of them; the game's own leagues use theirs.
The competition ids are full.

Two levers, in order of cost:

1. **Share a competition id between leagues** (the "twins" of the test world, regulations 379..383
   on the cids of 336..340). The league's table and its clubs come from the *regulation* and the
   clubs' slots, not from the competition row, so a shared cid may cost nothing in Master
   League. That is the thing the first career with the twins will tell us.
2. **More slots**: the slot field of a club is a byte (`fl26slot7`), so 250 is near its end. A
   slot above 255 needs a 16-bit slot -- the same kind of job as the 18-bit player id.

## Teams

4,800 of a 4,800 cap, 2,886 used: the loosest wall. The block grows with the caps set, and the
allocation immediates are 32-bit, so this one has room for years.

## The order to work in

1. Finish the player id allocator in Build (gaps, not above the game's) -- no exe patch, no game
   needed to check the ids; it buys ~75,000 players of headroom.
2. Play the twins in a career: if two regulations on one cid work, leagues are no longer limited
   by competition ids.
3. Then the competition id high byte, with the three sites above.
