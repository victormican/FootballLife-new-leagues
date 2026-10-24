# National teams and a separate Oceania group

Written 2026-10-23. What the game actually has, why there is no Oceania region, and what it would
take to add one and to reach 211 national teams. Read with
[limits-and-formats.md](limits-and-formats.md) (Select Team slots) and
[world-file.md](world-file.md).

## What the game has

`Team.bin` holds clubs and national teams in one table. A national team is a row with the top
bit of byte `+0x53` set; its name is at `+0x170`, its short name at `+0x372` and its country id
in the 9 bits at `+0x46` (bit 2 on). The country's confederation is `Country.bin +5`
(2 UEFA, 3 AFC, 4 CONMEBOL, 5 CAF, 6 CONCACAF, 7 OFC).

The FL 2026 world in the test copy has **144 national teams**:

| confederation | teams |
|---|---|
| UEFA | 55 |
| AFC | 38 |
| CONCACAF | 12 |
| CONMEBOL | 10 |
| CAF | 28 |
| OFC | **1** |
| total | **144** |

The OFC one is **New Zealand, team 1141, country 166**. `Country.bin` has twelve OFC country ids
(161, 163-172, 184), but none of the other eleven has a national team. **211 is FIFA's member
count, not this game's**; the gap is 67 teams.

`tools/nations.py` prints this table and the OFC list from any world:

```
python tools/nations.py --base <world pesdb> --countries <pesdb with Country.bin> [--json]
```

## How the menus group them

The Select Team / Kick Off list is built from **competition slots** (see
[limits-and-formats.md](limits-and-formats.md)). The first five slots are the national-team
regions, hard-coded in the game:

| slot | heading | teams |
|---|---|---|
| 0 | Europe | UEFA |
| 1 | Africa | CAF |
| 2 | North & Central America | CONCACAF |
| 3 | South America | CONMEBOL |
| 4 | **Asia-Oceania** | AFC + OFC |
| 5, 6 | Classic Teams | the two shipped Classic groups |
| 69, 71, 73, 75 | Other European / Other / Other Latin American / Other Clubs (Africa) | clubs in no league |

The slot name comes from the switch at `0x140ea08e0` (case bytes at `0x140ea0b3c`, cases 0-3
Europe/Africa/NC America/South America, 4 Asia-Oceania, 5-6 Classic Teams, 69/71/73/75 the other
groups). `sider/experimental/fl26slotnames.lua` patches the case byte to blank a borrowed heading.

The list itself is read through **two readers**, count `0x1414d62c0(this, slot)` and get
`0x1414d6290(this, slot, i)`. `sider/experimental/fl26clubs.dll` replaces both: for the slots a
world file configures it answers from the league's own regulation record, and for every other slot
it falls through to the game. The list builder is `0x1412fac89` / `0x1412fb24e` and walks slots
`0..249` (`fl26slots250`). A slot with a non-empty list and a name is shown.

There is **no sixth national-team region**: the game merges AFC and OFC into slot 4. Nothing in
`Country.bin` opens a new slot; the grouping is by the hard-coded slot, not by the country's
confederation alone.

## Adding Oceania: the options

### A. A new slot 189 (clean, needs the list builder to accept a sixth nation region)

1. `fl26slots250` already allows slot 189 (capacity 324). Create a competition row on slot 189
   named **Oceania** (`fl26comptab` appends rows; a small module can do it without a league).
2. Serve the slot's list from `fl26clubs.dll`: a new export `fl26_clubs_nations(handles, n)` that
   stores the national-team handles (New Zealand, and any new OFC teams) for slot 189, and
   `fl26_clubs_keep_out` (already there) to remove team 1141 from slot 4.
3. The world file gets a line `nations oceania 1141 ...`; `fl26swiss.lua` passes it to the export.
4. Patch the slot-name switch for 189 (case byte -> a text id, or the row's own name).

The risk is step 1/2: the UI decides "national team" from the slot number. A slot above 4 may be
drawn as a club group, and a national team inside a club group can open the wrong panel. This is
the part that must be measured in a running game before it is promised.

### B. Reuse a Classic Teams slot (quick, loses one Classic group)

Rename slot 5 from "Classic Teams" to "Oceania", serve New Zealand there, and remove it from slot
4. Slots 5/6 are already in the region range the UI treats as national/classic groups. The cost is
one of the two shipped Classic Teams entries (the other stays on slot 6). This is the smallest
patch and the best first test.

### C. Split slot 4 into "Asia" and "Oceania" (no new slot, needs a range patch)

Keep slot 4 for AFC, and move the OFC team to a new slot. The UI's national-region range is
`0..4`; extending it to `0..5` means changing every compare on that range (the list builder, the
name switch, the team-select panels) and moving Classic Teams. Larger than B, but it keeps every
shipped group.

**Recommendation:** test B first (one module, no new competition, reversible), then decide
whether A/C is worth the UI work.

## Reaching 211 national teams

Creating the 67 missing teams is a data job and a capacity problem:

- **Team records**: clone a `Team.bin` row, set the national bit, name, short name, country, kit
  and colours. 67 rows fit: the table has 2,400 slots and 2,199 are used.
- **Squads**: each national team needs players. `PlayerAssignment.bin`/`Player.bin` hold them.
  The world uses **61,791** player records; `fl26caps` caps the runtime at **61,905**. 67 teams at
  23 players need **1,541** more records, so the cap is the wall. Freeing/compacting players or
  raising the cap (another array move) is required first.
- **Country/flag**: a new `Country.bin` row (or reusing an existing OFC country id) and a flag
  picture; the menu group follows the country's confederation.
- **Names**: the twenty language slots of the Team record; Mod Studio's name slots.

So **211 national teams is not possible in this world yet**; the player cap leaves about 114
players, not 1,541. The Oceania group with the existing New Zealand needs no new players and can
be done now.

## Measured 2026-10-24: the group is not a Team.bin nibble

An earlier reading of `+0x4f` was wrong and cost a round of "Oceania does not show". Dumped on
the test world's shipped 144 national teams, the **low** nibble of `+0x4f` is scattered across
0..9 with no relation to the confederation (India 0, Morocco 2, Ireland 4, Portugal 6, Belgium
8, Saudi Arabia 9), and the **high** nibble -- the one `leaguebuilder.T_POOL` uses for a club's
"Other ..." group -- is 0 for all of them. So neither half of that byte files a national team
into a Select Team region; the shipped grouping is built by the game, not read from the row.

Consequence: moving the OFC sides' `+0x4f` (to 4, then to 8) changed nothing, and the world is
back to the shipped value (high nibble 0) for every national team. Whatever groups the 211 is
code, and the boot log / the menu is the way to find out where the 67 added teams landed.

## The Oceania competition and slot 9

2026-10-24: `tools/add_nations_cups.py --preset oceania` builds a real OFC competition named
**Oceania** (cid 91, regulation 196, the 8 OFC sides it picks), on the pattern of the OFC
Nations Cup. The world file also carries a league-shaped row for it:

```
league 196 cid=91 region=25 country=200 conf=7 slot=9 tier=1 promote=0 demote=0 clubs=8 legs=1 kickoff=166 name=Oceania
```

`fl26comptab` appends a parameter row for it, and `0x140ea08e0` has no case for
slot 9 (its jump table stops at 0x4b and slots 7, 8 and 9 fall to the default), so the caller
falls back to the name of the competition on that slot -- "Oceania".

**The number cannot be written in the world file.** The first attempt asked for slot 9 and the
game answered, in sider.log:

```
fl26comptab: slot 9 is already competition 18, not free -- aborting
```

-- and one abort at that step means *nothing* of the list is applied (that is the "one league
shows" symptom again). Which slots the exe fills is a fact of the running game, so since
2026-10-24 a `league` line may say **`slot=-1`**: `fl26comptab` looks at the rows the exe
built, skips our own and the hidden 123, and takes the first free slot from 7 to 122, logging
which one it got ("id 196 asked for a free slot -- it gets slot N"). `check_world` accepts -1
(the line is not range-checked and does not take part in the one-league-per-slot check).


The cid is the scarce resource: `add_nations_cups.free_ids` used to look for 130..255, which the
test world has filled, so it now searches from 88 (free: 91, 92, 0, 6, 7, 48, 55, 57, 58, 64, 65).

## Test plan

1. `python tools/nations.py` on the test world: expect 144, OFC 1 (New Zealand 1141).
2. Build the B prototype (or A) as a Sider module in the copy; start the game and open Select
   Team / Kick Off. Check:
   - the heading "Oceania" appears where Classic Teams was (B) or on the new slot (A);
   - New Zealand is under it and no longer under "Asia-Oceania";
   - the other Classic Teams entry is still there (B);
   - a national-team match can still be started with New Zealand.
3. If the panel opens as a club group, fall back to C and measure the range compares.

No new players, no new Team.bin rows and no world rebuild are needed for the Oceania group.
